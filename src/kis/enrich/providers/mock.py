"""Deterministic mock provider — default for tests, zero network."""

from __future__ import annotations

from ..prompt_contract import output_hash
from .base import EnrichmentRequest, EnrichmentResult


class MockProvider:
    name = "mock"

    def enrich(self, request: EnrichmentRequest) -> EnrichmentResult:
        summary = f"[mock] {request.title}".strip()
        tags = ["mock_generated"]
        return EnrichmentResult(
            summary=summary,
            reason_tags=tags,
            provider="mock",
            model="mock-1",
            output_hash=output_hash(summary, tags),
        )
