from __future__ import annotations

import unittest

from app.clients import normalize_github_repo_url, parse_daily_papers
from app.logic import qualify_paper
from app.models import PaperCandidate


class ParseDailyPapersTests(unittest.TestCase):
    def test_parse_daily_papers_payload(self) -> None:
        html_text = """
        <div data-target="DailyPapers" data-props="{&quot;dailyPapers&quot;:[{&quot;paper&quot;:{&quot;id&quot;:&quot;2603.12345&quot;,&quot;title&quot;:&quot;Sample Paper&quot;,&quot;upvotes&quot;:42,&quot;ai_summary&quot;:&quot;Short summary&quot;,&quot;githubRepo&quot;:&quot;https://github.com/org/repo&quot;,&quot;projectPage&quot;:&quot;https://example.com/project&quot;,&quot;authors&quot;:[{&quot;name&quot;:&quot;Alice&quot;},{&quot;name&quot;:&quot;Bob&quot;}]},&quot;title&quot;:&quot;Sample Paper&quot;}]}"></div>
        """
        papers = parse_daily_papers(html_text)

        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0].paper_id, "2603.12345")
        self.assertEqual(papers[0].title, "Sample Paper")
        self.assertEqual(papers[0].upvotes, 42)
        self.assertEqual(papers[0].github_repo, "https://github.com/org/repo")
        self.assertEqual(papers[0].project_page, "https://example.com/project")
        self.assertEqual(papers[0].authors, ["Alice", "Bob"])


class GithubUrlTests(unittest.TestCase):
    def test_normalize_github_repo_url(self) -> None:
        value = normalize_github_repo_url("https://github.com/openai/codex/tree/main?tab=readme")
        self.assertEqual(value, "https://github.com/openai/codex")


class QualificationTests(unittest.TestCase):
    def test_qualify_by_upvotes_only(self) -> None:
        paper = PaperCandidate(
            paper_id="2603.99999",
            title="Interesting Paper",
            hf_url="https://huggingface.co/papers/2603.99999",
            published_at=None,
            upvotes=21,
            summary="A summary",
            ai_summary="Short summary",
            github_repo=None,
            project_page=None,
            authors=["Alice"],
        )

        qualified = qualify_paper(paper, upvote_threshold=20, stars_threshold=100, github_stars=None)
        self.assertIsNotNone(qualified)
        self.assertEqual(qualified.qualified_by, "upvotes")
        self.assertIn("21 个 upvotes", qualified.brief_zh)


if __name__ == "__main__":
    unittest.main()
