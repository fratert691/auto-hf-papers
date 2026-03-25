from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PaperCandidate:
    paper_id: str
    title: str
    hf_url: str
    published_at: str | None
    upvotes: int
    summary: str | None
    ai_summary: str | None
    github_repo: str | None
    project_page: str | None
    authors: list[str]


@dataclass
class QualifiedPaper(PaperCandidate):
    github_stars: int | None
    qualified_by: str
    brief_zh: str
