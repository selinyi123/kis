"""KIS-008 single-URL web clip tests (10 cases).

No real network: fetch is mocked, extraction/validation are pure. Temp dirs are
cleaned up (no ResourceWarning, no temp pollution).
"""

import os
import shutil
import sys
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

from kis.card import normalize_url  # noqa: E402
from kis.connectors.web_url import (  # noqa: E402
    UrlSafetyError, WebPageRaw, extract_web_page, validate_url, web_page_to_card,
)
from kis.store import Store  # noqa: E402
from kis.validate import load_schema, validate_card  # noqa: E402
from ingest_url import ingest_url  # noqa: E402

with open(os.path.join(_ROOT, "examples", "web-url.sample.html"), encoding="utf-8") as _fh:
    SAMPLE_HTML = _fh.read()


def _raw(url="https://example.com/blog/knowledge-runtime"):
    return WebPageRaw(url=url, final_url=url, status=200,
                      content_type="text/html; charset=utf-8", html=SAMPLE_HTML, error=None)


class TestUrlSafety(unittest.TestCase):
    # 1
    def test_validate_url_allows_https(self):
        self.assertEqual(validate_url("https://example.com/path"), "https://example.com/path")

    # 2
    def test_validate_url_blocks_file_scheme(self):
        for bad in ("file:///etc/passwd", "ftp://x/y", "javascript:alert(1)", "data:text/html,x", "about:blank"):
            with self.assertRaises(UrlSafetyError):
                validate_url(bad)

    # 3
    def test_validate_url_blocks_localhost(self):
        for bad in ("http://localhost:8080/", "https://app.localhost/", "http://0.0.0.0/"):
            with self.assertRaises(UrlSafetyError):
                validate_url(bad)

    # 4
    def test_validate_url_blocks_private_ip(self):
        for bad in ("http://10.0.0.1/", "http://192.168.1.1/", "http://127.0.0.1/",
                    "http://169.254.169.254/", "http://[::1]/"):
            with self.assertRaises(UrlSafetyError):
                validate_url(bad)

    # 5
    def test_normalize_url_strips_tracking_params(self):
        out = normalize_url("https://example.com/p?utm_source=x&id=5&gclid=z")
        self.assertNotIn("utm_source", out)
        self.assertNotIn("gclid", out)
        self.assertIn("id=5", out)


class TestExtraction(unittest.TestCase):
    def setUp(self):
        self.page = extract_web_page(_raw())

    # 6
    def test_extract_title_from_html(self):
        self.assertEqual(self.page.title, "Building a Knowledge Runtime")

    # 7
    def test_extract_meta_description(self):
        self.assertTrue(self.page.description.startswith("How to turn scattered"))
        self.assertNotIn("tracking pixel", self.page.text_preview)  # script stripped
        self.assertEqual(self.page.lang, "en")

    # 8
    def test_web_clip_to_card_schema_valid(self):
        card = web_page_to_card(self.page)
        self.assertEqual(validate_card(card, load_schema()), [])
        self.assertEqual(card["source"]["source_type"], "web_clip")


class TestIngest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.db = os.path.join(self.tmp, "k.db")
        self.vault = os.path.join(self.tmp, "vault")

    # 9
    def test_blocked_url_not_written_to_store_or_vault(self):
        def _must_not_fetch(_url):
            raise AssertionError("blocked URL must not be fetched")
        res = ingest_url("https://www.mostlogin.com/zh", self.db, self.vault, fetcher=_must_not_fetch)
        self.assertEqual(res.status, "blocked")
        self.assertEqual(Store(self.db).count("web_clip"), 0)
        self.assertFalse(os.path.isdir(os.path.join(self.vault, "Web-Clips")))
        self.assertTrue(os.path.isdir(os.path.join(self.vault, "_blocked")))

    # 10
    def test_ingest_url_end_to_end_with_mock_fetch(self):
        res = ingest_url("https://example.com/blog/knowledge-runtime", self.db, self.vault,
                         fetcher=lambda u: _raw(u))
        self.assertEqual(res.status, "inserted")
        self.assertEqual(Store(self.db).count("web_clip"), 1)
        clips = [f for _r, _d, fs in os.walk(os.path.join(self.vault, "Web-Clips")) for f in fs]
        self.assertTrue(clips, "expected a Web-Clips markdown note")
        # re-run is idempotent
        res2 = ingest_url("https://example.com/blog/knowledge-runtime", self.db, self.vault,
                          fetcher=lambda u: _raw(u))
        self.assertEqual(res2.status, "unchanged")


if __name__ == "__main__":
    unittest.main()
