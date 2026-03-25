from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.clients import (
    FetchError,
    GithubRateLimitError,
    fetch_daily_papers_html,
    fetch_github_stars,
    parse_daily_papers,
)
from app.logic import qualify_paper
from app.render import render_markdown


@dataclass
class RunStats:
    total_papers: int
    github_checked: int
    github_failed: int
    selected: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a daily Markdown digest from Hugging Face Daily Papers."
    )
    parser.add_argument("--date", help="Date in YYYY-MM-DD format. Defaults to local today.")
    parser.add_argument(
        "--upvotes",
        type=int,
        default=20,
        help="Include papers with HF upvotes strictly greater than this value.",
    )
    parser.add_argument(
        "--stars",
        type=int,
        default=100,
        help="Include papers with GitHub stars strictly greater than this value.",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs",
        help="Directory where the Markdown digest will be written.",
    )
    parser.add_argument(
        "--github-token",
        default=os.environ.get("GITHUB_TOKEN"),
        help="Optional GitHub token to raise API limits. Defaults to GITHUB_TOKEN env var.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    date_str = args.date or datetime.now().astimezone().date().isoformat()

    try:
        html_text = fetch_daily_papers_html(date_str)
        candidates = parse_daily_papers(html_text)
    except FetchError as exc:
        print(f"[error] {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - defensive main guard
        print(f"[error] Failed to fetch Hugging Face papers: {exc}")
        return 1

    qualified = []
    github_checked = 0
    github_failed = 0
    github_rate_limited = False

    for candidate in candidates:
        github_stars = None
        if candidate.github_repo and not github_rate_limited:
            github_checked += 1
            try:
                github_stars = fetch_github_stars(candidate.github_repo, token=args.github_token)
            except GithubRateLimitError as exc:
                github_failed += 1
                github_rate_limited = True
                print(f"[warn] {exc}")
                print("[warn] Skipping remaining GitHub lookups for this run.")
            except FetchError as exc:
                github_failed += 1
                print(f"[warn] {exc}")

        qualified_paper = qualify_paper(
            candidate,
            upvote_threshold=args.upvotes,
            stars_threshold=args.stars,
            github_stars=github_stars,
        )
        if qualified_paper is not None:
            qualified.append(qualified_paper)

    qualified.sort(key=lambda paper: (paper.upvotes, paper.github_stars or -1, paper.title), reverse=True)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{date_str}.md"
    markdown = render_markdown(
        date_str=date_str,
        qualified_papers=qualified,
        total_papers=len(candidates),
        upvote_threshold=args.upvotes,
        stars_threshold=args.stars,
    )
    output_path.write_text(markdown, encoding="utf-8")

    stats = RunStats(
        total_papers=len(candidates),
        github_checked=github_checked,
        github_failed=github_failed,
        selected=len(qualified),
    )
    print(f"[info] Date: {date_str}")
    print(f"[info] Total papers: {stats.total_papers}")
    print(f"[info] GitHub repos checked: {stats.github_checked}")
    print(f"[info] GitHub lookups failed: {stats.github_failed}")
    print(f"[info] Selected papers: {stats.selected}")
    print(f"[info] Wrote digest: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
