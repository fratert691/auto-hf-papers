from __future__ import annotations

from app.models import PaperCandidate, QualifiedPaper


def qualify_paper(
    paper: PaperCandidate,
    upvote_threshold: int,
    stars_threshold: int,
    github_stars: int | None,
) -> QualifiedPaper | None:
    meets_upvotes = paper.upvotes > upvote_threshold
    meets_stars = github_stars is not None and github_stars > stars_threshold

    if not meets_upvotes and not meets_stars:
        return None

    qualified_by = "both"
    if meets_upvotes and not meets_stars:
        qualified_by = "upvotes"
    elif meets_stars and not meets_upvotes:
        qualified_by = "github_stars"

    return QualifiedPaper(
        paper_id=paper.paper_id,
        title=paper.title,
        hf_url=paper.hf_url,
        published_at=paper.published_at,
        upvotes=paper.upvotes,
        summary=paper.summary,
        ai_summary=paper.ai_summary,
        github_repo=paper.github_repo,
        project_page=paper.project_page,
        authors=paper.authors,
        github_stars=github_stars,
        qualified_by=qualified_by,
        brief_zh=build_brief_zh(paper, github_stars, qualified_by, upvote_threshold, stars_threshold),
    )


def build_brief_zh(
    paper: PaperCandidate,
    github_stars: int | None,
    qualified_by: str,
    upvote_threshold: int,
    stars_threshold: int,
) -> str:
    # English summary (ai_summary is one sentence; fall back to full abstract)
    base_summary = paper.ai_summary or paper.summary or ""
    base_summary = _ensure_terminal_punctuation(base_summary) if base_summary else ""

    # Chinese metadata: why this paper was selected
    reason_parts: list[str] = []
    if qualified_by in {"upvotes", "both"}:
        reason_parts.append(f"HF upvotes {paper.upvotes}（阈值 > {upvote_threshold}）")
    if qualified_by in {"github_stars", "both"} and github_stars is not None:
        reason_parts.append(f"GitHub stars {github_stars}（阈值 > {stars_threshold}）")
    reason_text = "，".join(reason_parts) if reason_parts else "满足筛选条件"

    if paper.github_repo and paper.project_page:
        link_hint = "附有 GitHub 仓库和项目页"
    elif paper.github_repo:
        link_hint = "附有 GitHub 仓库"
    elif paper.project_page:
        link_hint = "附有项目页"
    else:
        link_hint = ""

    lines: list[str] = []
    if base_summary:
        lines.append(base_summary)
        lines.append("")
    entry = f"入选原因：{reason_text}。"
    if link_hint:
        entry += link_hint + "。"
    lines.append(entry)

    return "\n".join(lines)


def _ensure_terminal_punctuation(text: str) -> str:
    text = " ".join(text.split()).strip()
    if not text:
        return text
    if text[-1] in ".!?。！？":
        return text
    return text + "."
