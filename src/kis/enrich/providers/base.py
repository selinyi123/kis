"""Enrichment provider interface (KIS-013b). No external SDK imported here."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


class ProviderUnavailable(RuntimeError):
    """Raised when a provider cannot run (missing SDK, missing API key, etc.)."""


@dataclass
class EnrichmentRequest:
    card_id: str
    title: str
    prompt: str           # inert, injection-guarded prompt (prompt_contract)
    input_hash: str


@dataclass
class EnrichmentResult:
    summary: str
    reason_tags: list[str] = field(default_factory=list)
    provider: str | None = None
    model: str | None = None
    output_hash: str | None = None
    error: str | None = None


@runtime_checkable
class EnrichmentProvider(Protocol):
    name: str

    def enrich(self, request: EnrichmentRequest) -> EnrichmentResult:
        ...
