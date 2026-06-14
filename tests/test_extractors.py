"""KIS-009 extractor abstraction tests (stdlib baseline + card/obsidian fields).

No network: stdlib extractor is driven by a canned fetcher.
"""

import os
import shutil
import sys
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

from kis.classify import classify_bookmark  # noqa: E402
from kis.connectors.web_url import WebPageRaw  # noqa: E402
from kis.extractors.base import ExtractedPage, extracted_to_card  # noqa: E402
from kis.extractors.stdlib_html import StdlibExtractor  # noqa: E402
from kis.obsidian import render_webclip_md  # noqa: E402
from kis.validate import load_schema, validate_card  # noqa: E402
from ingest_url import ingest_url  # noqa: E402

with open(os.path.join(_ROOT, "examples", "web-url.sample.html"), encoding="utf-8") as _fh:
    SAMPLE_HTML = _fh.read()


def _canned(url="https://example.com/blog/knowledge-runtime"):
    return WebPageRaw(url=url, final_url=url, status=200,
                      content_type="text/html; charset=utf-8", html=SAMPLE_HTML, error=None)


def _crawl4ai_page(url="https://example.com/x"):
    return ExtractedPage(
        url=url, normalized_url=url, title="Crawled Title", description="d",
        text_preview="preview text", clean_markdown="# Heading\n\nbody",
        structured_data={"k": "v"}, extraction_engine="crawl4ai",
        extraction_status="success", extraction_error=None,
        site_name="example.com", lang="en", http_status=200, fetched_at="2026-06-14T00:00:00Z",
    )


class TestExtractors(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_stdlib_extractor_remains_default(self):
        res = ingest_url("https://example.com/blog/knowledge-runtime",
                         os.path.join(self.tmp, "k.db"), os.path.join(self.tmp, "v"),
                         fetcher=lambda u: _canned(u))  # mode defaults to stdlib
        self.assertEqual(res.status, "inserted")
        self.assertEqual(res.card["source"]["extraction_engine"], "stdlib")

    def test_schema_valid_with_crawl4ai_fields(self):
        cls = classify_bookmark("Crawled Title", "https://example.com/x", "example.com")
        card = extracted_to_card(_crawl4ai_page(), cls)
        self.assertEqual(validate_card(card, load_schema()), [])
        self.assertEqual(card["content"]["clean_markdown"], "# Heading\n\nbody")
        self.assertEqual(card["content"]["structured_data"], {"k": "v"})
        self.assertEqual(card["source"]["extraction_engine"], "crawl4ai")

    def test_obsidian_renders_extraction_metadata(self):
        cls = classify_bookmark("Crawled Title", "https://example.com/x", "example.com")
        md = render_webclip_md(extracted_to_card(_crawl4ai_page(), cls))
        self.assertIn("## Extraction", md)
        self.assertIn("Engine: crawl4ai", md)
        self.assertIn("extraction_engine: crawl4ai", md)  # frontmatter
        self.assertIn("## Clean Markdown", md)

    def test_tests_do_not_require_network(self):
        # stdlib extraction is fully driven by a canned fetcher — proves offline path.
        page = StdlibExtractor(fetcher=lambda u: _canned(u)).extract("https://example.com/x")
        self.assertEqual(page.extraction_engine, "stdlib")
        self.assertEqual(page.title, "Building a Knowledge Runtime")
        self.assertIsNone(page.clean_markdown)


if __name__ == "__main__":
    unittest.main()
