from __future__ import annotations

import json
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from app.models import PaperCandidate

HF_API_URL = "https://huggingface.co/api/daily_papers?date={date}"
DEFAULT_TIMEOUT = 20
USER_AGENT = "auto-hf-papers/0.1 (+https://github.com)"


class FetchError(RuntimeError):
    """Raised when a remote resource cannot be fetched or parsed."""


class GithubRateLimitError(FetchError):
    """Raised when the GitHub API rate limit has been exceeded."""


def fetch_text(url: str, headers: dict[str, str] | None = None, timeout: int = DEFAULT_TIMEOUT) -> str:
    request_headers = {"User-Agent": USER_AGENT, **(headers or {})}
    request = Request(url, headers=request_headers)
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, "replace")


def fetch_json(url: str, headers: dict[str, str] | None = None, timeout: int = DEFAULT_TIMEOUT) -> Any:
    return json.loads(fetch_text(url, headers=headers, timeout=timeout))


def fetch_daily_papers(date: str) -> list[PaperCandidate]:
    """Fetch papers from the HuggingFace daily papers JSON API."""
    url = HF_API_URL.format(date=date)
    try:
        data = fetch_json(url)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise FetchError(f"Failed to decode HuggingFace API response: {exc}") from exc

    if not isinstance(data, list):
        raise FetchError(
            f"Unexpected HuggingFace API response format: expected a list, got {type(data).__name__}"
        )

    return _parse_api_response(data)


def _parse_api_response(data: list[Any]) -> list[PaperCandidate]:
    """Parse the HuggingFace daily papers API JSON array into PaperCandidate objects."""
    papers: list[PaperCandidate] = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        paper = entry.get("paper") or {}
        if not isinstance(paper, dict):
            continue

        paper_id = str(paper.get("id") or "").strip()
        if not paper_id:
            continue

        authors = [
            str(a.get("name") or "").strip()
            for a in paper.get("authors") or []
            if isinstance(a, dict) and a.get("name")
        ]

        papers.append(
            PaperCandidate(
                paper_id=paper_id,
                title=str(paper.get("title") or paper_id).strip(),
                hf_url=f"https://huggingface.co/papers/{paper_id}",
                published_at=paper.get("publishedAt"),
                upvotes=int(paper.get("upvotes") or 0),
                summary=_clean_text(paper.get("summary")),
                ai_summary=_clean_text(paper.get("ai_summary")),
                github_repo=normalize_github_repo_url(paper.get("githubRepo")),
                project_page=_clean_url(paper.get("projectPage")),
                authors=authors,
            )
        )

    return papers


def normalize_github_repo_url(repo_url: str | None) -> str | None:
    if not repo_url:
        return None
    try:
        parsed = urlparse(str(repo_url).strip())
    except ValueError:
        return None

    if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        return None

    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2:
        return None

    owner, repo = parts[0], parts[1]
    repo = repo.removesuffix(".git")
    return f"https://github.com/{owner}/{repo}"


def fetch_github_stars(repo_url: str, token: str | None = None, retries: int = 2) -> int:
    normalized_url = normalize_github_repo_url(repo_url)
    if not normalized_url:
        raise FetchError(f"Unsupported GitHub repository URL: {repo_url}")

    parsed = urlparse(normalized_url)
    owner, repo = [part for part in parsed.path.split("/") if part][:2]
    api_url = f"https://api.github.com/repos/{owner}/{repo}"

    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            payload = fetch_json(api_url, headers=headers)
            stars = payload.get("stargazers_count")
            if not isinstance(stars, int):
                raise FetchError(f"GitHub API returned an invalid stars value for {normalized_url}")
            return stars
        except HTTPError as exc:
            if exc.code == 403:
                raise GithubRateLimitError(f"GitHub API rate limit exceeded for {normalized_url}") from exc
            last_error = exc
            if attempt == retries:
                break
            time.sleep(0.6 * (attempt + 1))
        except (FetchError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt == retries:
                break
            time.sleep(0.6 * (attempt + 1))

    raise FetchError(f"Failed to fetch GitHub stars for {normalized_url}: {last_error}")


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).split()).strip()
    return text or None


def _clean_url(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
