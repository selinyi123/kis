import importlib.util
import pathlib
import sys
import unittest

SCRIPT = pathlib.Path(__file__).parents[1] / "scripts" / "sync_github_stars_to_notion.py"
spec = importlib.util.spec_from_file_location("star_sync", SCRIPT)
star_sync = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = star_sync
spec.loader.exec_module(star_sync)


class StarSyncPureTests(unittest.TestCase):
    def test_parse_star_wrapper(self):
        star = star_sync.parse_star({
            "starred_at": "2026-08-30T09:00:00Z",
            "repo": {
                "full_name": "owner/repo",
                "html_url": "https://github.com/owner/repo",
                "description": "A useful tool",
                "stargazers_count": 42,
                "owner": {"login": "owner"},
                "default_branch": "main",
            },
        })
        self.assertEqual(star.full_name, "owner/repo")
        self.assertEqual(star.starred_at, "2026-08-30T09:00:00Z")
        self.assertEqual(star.stars, 42)

    def test_canonical_url(self):
        self.assertEqual(
            star_sync.canonical_github_url("https://github.com/Owner/Repo.git/"),
            "https://github.com/owner/repo",
        )
        self.assertEqual(
            star_sync.canonical_github_url("https://github.com/Owner/Repo.git"),
            "https://github.com/owner/repo",
        )

    def test_readme_purpose_skips_badges_and_headings(self):
        md = """# Project

[![build](https://example.com/badge.svg)](https://example.com)

This tool synchronizes GitHub stars into a personal knowledge database
without requiring an LLM in the write path.

## Install
"""
        text = star_sync.extract_readme_purpose(md)
        self.assertIn("synchronizes GitHub stars", text)
        self.assertNotIn("build", text)

    def test_build_purpose_prefers_description(self):
        star = star_sync.Star(
            starred_at="2026-08-30T09:00:00Z",
            full_name="owner/repo",
            html_url="https://github.com/owner/repo",
            description="Syncs GitHub stars into Notion",
            stars=10,
            owner="owner",
            default_branch="main",
        )
        self.assertEqual(
            star_sync.build_purpose(star, "ignored README"),
            "该仓库主要用于：Syncs GitHub stars into Notion。",
        )

    def test_owner_mapping(self):
        star = star_sync.Star(
            starred_at="2026-08-30T09:00:00Z",
            full_name="selinyi123/repo",
            html_url="https://github.com/selinyi123/repo",
            description="x",
            stars=1,
            owner="selinyi123",
            default_branch="main",
        )
        props = star_sync.notion_properties(star, "用途", "selinyi123")
        self.assertEqual(props["归属"]["select"]["name"], "本人")
        self.assertEqual(props["标星时间"]["date"]["start"], star.starred_at)


if __name__ == "__main__":
    unittest.main()
