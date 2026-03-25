from __future__ import annotations

from datetime import datetime, timezone

from app.models import QualifiedPaper


def render_markdown(
    date_str: str,
    qualified_papers: list[QualifiedPaper],
    total_papers: int,
    upvote_threshold: int,
    stars_threshold: int,
) -> str:
    lines: list[str] = []
    lines.append(f"# Hugging Face Papers Digest - {date_str}")
    lines.append("")
    lines.append(f"- Generated at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("- Source: Hugging Face Daily Papers page plus GitHub repository API")
    lines.append(
        f"- Rule: include papers with `upvotes > {upvote_threshold}` or `GitHub stars > {stars_threshold}`"
    )
    lines.append(f"- Result: {len(qualified_papers)} selected from {total_papers} papers")
    lines.append("")

    if not qualified_papers:
        lines.append("今天没有满足筛选条件的论文。")
        return "\n".join(lines).strip() + "\n"

    for index, paper in enumerate(qualified_papers, start=1):
        lines.append(f"## {index}. {paper.title}")
        lines.append("")
        lines.append(f"- Qualified By: {describe_qualified_by(paper.qualified_by)}")
        lines.append(f"- Hugging Face Upvotes: {paper.upvotes}")
        lines.append(f"- GitHub Stars: {paper.github_stars if paper.github_stars is not None else 'N/A'}")
        if paper.authors:
            lines.append(f"- Authors: {', '.join(paper.authors)}")
        lines.append(f"- Hugging Face: {paper.hf_url}")
        if paper.github_repo:
            lines.append(f"- GitHub: {paper.github_repo}")
        if paper.project_page:
            lines.append(f"- Project Page: {paper.project_page}")
        lines.append("")
        lines.append("简介：")
        lines.append("")
        lines.append(paper.brief_zh)
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def describe_qualified_by(value: str) -> str:
    mapping = {
        "upvotes": "HF upvotes",
        "github_stars": "GitHub stars",
        "both": "HF upvotes + GitHub stars",
    }
    return mapping.get(value, value)
