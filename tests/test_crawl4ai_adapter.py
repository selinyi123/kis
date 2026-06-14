"""KIS-009 Crawl4AI adapter tests — optional, lazy, mocked (no network/browser)."""

import importlib.util
import os
import shutil
import sys
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

from kis.connectors.web_url import WebPageRaw  # noqa: E402
from kis.extractors.base import OptionalDependencyMissing  # noqa: E402
from kis.extractors.crawl4ai_adapter import Crawl4AIExtractor, _run_crawl4ai  # noqa: E402
from kis.store import Store  # noqa: E402
from ingest_url import ingest_url  # noqa: E402

with open(os.path.join(_ROOT, "examples", "web-url.sample.html"), encoding="utf-8") as _fh:
    SAMPLE_HTML = _fh.read()


def _canned(url="https://example.com/blog/x"):
    return WebPageRaw(url=url, final_url=url, status=200,
                      content_type="text/html; charset=utf-8", html=SAMPLE_HTML, error=None)


def _good_runner(url):
    return {"title": "T", "description": "d", "markdown": "# Hello\n\nWorld",
            "text": "Hello World", "structured": {"author": "x"}, "http_status": 200,
            "site_name": "example.com", "lang": "en", "error": None}


def _raising_runner(url):
    raise RuntimeError("boom")


def _must_not_call(url):
    raise AssertionError("crawl4ai/fetch must not be called for this URL")


class TestCrawl4AILazy(unittest.TestCase):
    def test_crawl4ai_import_is_lazy(self):
        # Importing the adapter must NOT import crawl4ai.
        self.assertNotIn("crawl4ai", sys.modules)

    def test_missing_crawl4ai_dependency_returns_controlled_error(self):
        if importlib.util.find_spec("crawl4ai") is not None:
            self.skipTest("crawl4ai is installed in this environment")
        with self.assertRaises(OptionalDependencyMissing):
            Crawl4AIExtractor(_run_crawl4ai).extract("https://example.com/")


class TestCrawl4AIMapping(unittest.TestCase):
    def test_crawl4ai_adapter_maps_markdown(self):
        page = Crawl4AIExtractor(_good_runner).extract("https://example.com/x")
        self.assertEqual(page.extraction_engine, "crawl4ai")
        self.assertTrue(page.clean_markdown.startswith("# Hello"))

    def test_crawl4ai_adapter_maps_structured_data(self):
        page = Crawl4AIExtractor(_good_runner).extract("https://example.com/x")
        self.assertEqual(page.structured_data, {"author": "x"})

    def test_crawl4ai_failure_raises_in_forced_mode(self):
        # Adapter-level: failure surfaces, never silently faked as success.
        with self.assertRaises(RuntimeError):
            Crawl4AIExtractor(_raising_runner).extract("https://example.com/x")


class TestCrawl4AIIngest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.db = os.path.join(self.tmp, "k.db")
        self.vault = os.path.join(self.tmp, "v")

    def test_crawl4ai_failure_falls_back_in_auto_mode(self):
        res = ingest_url("https://example.com/blog/x", self.db, self.vault, mode="auto",
                         fetcher=lambda u: _canned(u), crawl4ai_runner=_raising_runner)
        self.assertEqual(res.status, "inserted")
        self.assertEqual(res.card["source"]["extraction_engine"], "stdlib")
        self.assertEqual(res.card["source"]["extraction_status"], "fallback")

    def test_crawl4ai_failure_raises_in_forced_mode_ingest(self):
        res = ingest_url("https://example.com/blog/x", self.db, self.vault, mode="crawl4ai",
                         fetcher=lambda u: _canned(u), crawl4ai_runner=_raising_runner)
        self.assertEqual(res.status, "failed")  # explicit, not silent success
        self.assertEqual(Store(self.db).count("web_clip"), 0)

    def test_blocked_url_never_calls_crawl4ai(self):
        res = ingest_url("https://www.mostlogin.com/zh", self.db, self.vault, mode="crawl4ai",
                         fetcher=_must_not_call, crawl4ai_runner=_must_not_call)
        self.assertEqual(res.status, "blocked")
        self.assertEqual(Store(self.db).count("web_clip"), 0)

    def test_ssrf_url_never_calls_crawl4ai(self):
        for bad in ("file:///etc/passwd", "http://169.254.169.254/", "http://localhost/"):
            res = ingest_url(bad, self.db, self.vault, mode="crawl4ai",
                             fetcher=_must_not_call, crawl4ai_runner=_must_not_call)
            self.assertEqual(res.status, "refused", bad)


if __name__ == "__main__":
    unittest.main()
