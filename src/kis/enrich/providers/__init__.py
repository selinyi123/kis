"""Enrichment providers (KIS-013b). External SDKs are imported lazily inside the
provider's enrich() — importing this package never requires openai etc.
"""

from .base import EnrichmentProvider, EnrichmentRequest, EnrichmentResult, ProviderUnavailable
from .mock import MockProvider

__all__ = [
    "EnrichmentProvider", "EnrichmentRequest", "EnrichmentResult",
    "ProviderUnavailable", "MockProvider", "get_provider",
]


def get_provider(name: str | None):
    """Resolve a provider by name. 'none'/None -> None (heuristic only)."""
    if name in (None, "none"):
        return None
    if name == "mock":
        return MockProvider()
    if name == "openai":
        from .openai_provider import OpenAIProvider  # lazy
        return OpenAIProvider()
    raise ProviderUnavailable(f"unknown provider: {name}")
