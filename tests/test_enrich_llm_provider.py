"""KIS-013b provider tests — optional, lazy, no network."""

import os
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from kis.card import github_star_card  # noqa: E402
from kis.enrich.heuristic import build_derived  # noqa: E402
from kis.enrich.providers import MockProvider, ProviderUnavailable  # noqa: E402

_REPO = {"full_name": "x/y", "html_url": "https://github.com/x/y", "description": "d",
         "language": "Python", "stargazers_count": 1, "topics": []}


class TestProviders(unittest.TestCase):
    def test_openai_provider_import_is_lazy(self):
        import kis.enrich.providers.openai_provider  # noqa: F401
        self.assertNotIn("openai", sys.modules)  # SDK not imported at module load

    def test_llm_mode_requires_provider_or_env(self):
        with self.assertRaises(ProviderUnavailable):
            build_derived(github_star_card(_REPO), mode="llm", provider=None)

    def test_auto_mode_falls_back_to_heuristic_without_provider(self):
        d = build_derived(github_star_card(_REPO), mode="auto", provider=None)
        self.assertEqual(d["processing_status"], "heuristic")

    def test_mock_provider_no_network(self):
        # Mock provider must not import any SDK or touch the network.
        d = build_derived(github_star_card(_REPO), mode="llm", provider=MockProvider())
        self.assertEqual(d["processing_status"], "llm_generated")
        self.assertNotIn("openai", sys.modules)


if __name__ == "__main__":
    unittest.main()
