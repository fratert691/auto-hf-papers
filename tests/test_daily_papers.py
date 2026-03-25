from __future__ import annotations

import unittest

from app.clients import _parse_api_response, normalize_github_repo_url
from app.logic import qualify_paper
from app.models import PaperCandidate


class ParseApiResponseTests(unittest.TestCase):
    def _make_entry(self, **overrides) -> dict:
        paper = {
            "id": "2603.12345",
            "title": "Sample Paper",
            "upvotes": 42,
            "summary": "A long abstract.",
            "ai_summary": "Short summary.",
            "githubRepo": "https://github.com/org/repo",
            "projectPage": "https://example.com/project",
            "publishedAt": "2026-03-25T00:00:00.000Z",
            "authors": [{"name": "Alice"}, {"name": "Bob"}],
        }
        paper.update(overrides)
        return {"paper": paper, "numComments": 0}

    def test_parses_basic_entry(self) -> None:
        entries = [self._make_entry()]
        papers = _parse_api_response(entries)

        self.assertEqual(len(papers), 1)
        p = papers[0]
        self.assertEqual(p.paper_id, "2603.12345")
        self.assertEqual(p.title, "Sample Paper")
        self.assertEqual(p.upvotes, 42)
        self.assertEqual(p.ai_summary, "Short summary.")
        self.assertEqual(p.github_repo, "https://github.com/org/repo")
        self.assertEqual(p.project_page, "https://example.com/project")
        self.assertEqual(p.authors, ["Alice", "Bob"])
        self.assertEqual(p.hf_url, "https://huggingface.co/papers/2603.12345")

    def test_skips_entry_without_id(self) -> None:
        entries = [self._make_entry(id="")]
        papers = _parse_api_response(entries)
        self.assertEqual(len(papers), 0)

    def test_handles_missing_optional_fields(self) -> None:
        entry = {"paper": {"id": "2603.99999", "title": "Minimal", "upvotes": 5}}
        papers = _parse_api_response([entry])
        self.assertEqual(len(papers), 1)
        p = papers[0]
        self.assertIsNone(p.github_repo)
        self.assertIsNone(p.project_page)
        self.assertIsNone(p.ai_summary)
        self.assertEqual(p.authors, [])

    def test_ignores_non_github_repo_urls(self) -> None:
        entries = [self._make_entry(githubRepo="https://gitlab.com/org/repo")]
        papers = _parse_api_response(entries)
        self.assertIsNone(papers[0].github_repo)


class GithubUrlTests(unittest.TestCase):
    def test_normalize_strips_subpath_and_query(self) -> None:
        value = normalize_github_repo_url("https://github.com/openai/codex/tree/main?tab=readme")
        self.assertEqual(value, "https://github.com/openai/codex")

    def test_normalize_strips_dot_git(self) -> None:
        value = normalize_github_repo_url("https://github.com/org/repo.git")
        self.assertEqual(value, "https://github.com/org/repo")

    def test_normalize_returns_none_for_non_github(self) -> None:
        self.assertIsNone(normalize_github_repo_url("https://gitlab.com/org/repo"))

    def test_normalize_returns_none_for_none(self) -> None:
        self.assertIsNone(normalize_github_repo_url(None))


class QualificationTests(unittest.TestCase):
    def _make_paper(self, **overrides) -> PaperCandidate:
        defaults = dict(
            paper_id="2603.99999",
            title="Interesting Paper",
            hf_url="https://huggingface.co/papers/2603.99999",
            published_at=None,
            upvotes=21,
            summary="A summary.",
            ai_summary="Short summary.",
            github_repo=None,
            project_page=None,
            authors=["Alice"],
        )
        defaults.update(overrides)
        return PaperCandidate(**defaults)

    def test_qualify_by_upvotes_only(self) -> None:
        paper = self._make_paper(upvotes=21)
        result = qualify_paper(paper, upvote_threshold=20, stars_threshold=100, github_stars=None)
        self.assertIsNotNone(result)
        self.assertEqual(result.qualified_by, "upvotes")
        self.assertIn("HF upvotes 21", result.brief_zh)

    def test_qualify_by_stars_only(self) -> None:
        paper = self._make_paper(upvotes=5, github_repo="https://github.com/org/repo")
        result = qualify_paper(paper, upvote_threshold=20, stars_threshold=100, github_stars=150)
        self.assertIsNotNone(result)
        self.assertEqual(result.qualified_by, "github_stars")
        self.assertIn("GitHub stars 150", result.brief_zh)

    def test_qualify_by_both(self) -> None:
        paper = self._make_paper(upvotes=25, github_repo="https://github.com/org/repo")
        result = qualify_paper(paper, upvote_threshold=20, stars_threshold=100, github_stars=120)
        self.assertIsNotNone(result)
        self.assertEqual(result.qualified_by, "both")

    def test_does_not_qualify_below_thresholds(self) -> None:
        paper = self._make_paper(upvotes=10)
        result = qualify_paper(paper, upvote_threshold=20, stars_threshold=100, github_stars=50)
        self.assertIsNone(result)

    def test_brief_zh_has_no_mixed_chinese_english_sentence(self) -> None:
        """English summary and Chinese reason should be on separate lines, not spliced together."""
        paper = self._make_paper(upvotes=21, ai_summary="This is an English summary.")
        result = qualify_paper(paper, upvote_threshold=20, stars_threshold=100, github_stars=None)
        # English summary should appear standalone, not inside a Chinese sentence
        self.assertIn("This is an English summary.", result.brief_zh)
        self.assertIn("入选原因", result.brief_zh)
        # No more "因为它Hugging" style splice
        self.assertNotIn("是因为它", result.brief_zh)


if __name__ == "__main__":
    unittest.main()
