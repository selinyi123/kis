"""Enrichment orchestrator (KIS-013).

build_derived(card, mode, provider) -> the derived dict (does not mutate card).
enrich_card(card, mode, provider)   -> a NEW card with card['derived'] set, or
                                       None if the card is blocked.

Boundary enforcement: enrich_card snapshots all locked (source/provenance) fields
and asserts only `derived` changed (prompt_contract.assert_only_derived).
"""

from __future__ import annotations

import copy
from typing import Any

from ..card import now_iso
from .project_relevance import compute_project_relevance
from .prompt_contract import (
    assert_only_derived, build_enrichment_prompt, input_hash, output_hash, prompt_hash, snapshot_locked,
)
from .providers.base import EnrichmentRequest, ProviderUnavailable
from .scoring import compute_value_score, next_action, review_flags, value_level
from .summary import heuristic_summary


def _heuristic_payload(card: dict[str, Any], base: dict[str, Any], mode: str, ihash: str,
                       extra_tags: list[str], error: str | None = None) -> dict[str, Any]:
    summary = heuristic_summary(card)
    gen: dict[str, Any] = {"mode": mode, "input_hash": ihash,
                           "output_hash": output_hash(summary, base["reason_tags"])}
    if error:
        gen["error"] = error
    base.update(ai_summary=summary, processing_status="heuristic", generator=gen)
    return base


def build_derived(card: dict[str, Any], mode: str = "heuristic", provider: Any = None) -> dict[str, Any]:
    if mode == "llm" and provider is None:
        raise ProviderUnavailable("llm mode requires a provider (or set --provider)")

    relevance = compute_project_relevance(card)
    score, tags = compute_value_score(card, relevance)
    ihash = input_hash(card)
    base: dict[str, Any] = {
        "value_score": score,
        "value_level": value_level(score),
        "reason_tags": tags,
        "project_relevance": relevance,
        "next_action": next_action(card, relevance),
        "review_flags": review_flags(card, score),
        "generated_at": now_iso(),
    }

    if mode == "heuristic" or (mode == "auto" and provider is None):
        return _heuristic_payload(card, base, mode, ihash, tags)

    # llm / auto-with-provider
    request = EnrichmentRequest(card_id=card["id"], title=card["content"]["title"],
                                prompt=build_enrichment_prompt(card), input_hash=ihash)
    try:
        result = provider.enrich(request)
        if result.error:
            raise RuntimeError(result.error)
    except Exception as e:
        if mode == "llm":
            raise
        return _heuristic_payload(card, base, "auto", ihash, tags, error=f"llm_failed: {e}")

    summary = result.summary or heuristic_summary(card)
    rtags = tags + [t for t in (result.reason_tags or []) if t not in tags]
    base.update(
        ai_summary=summary,
        reason_tags=rtags,
        processing_status="llm_generated",
        generator={
            "mode": mode, "input_hash": ihash, "prompt_hash": prompt_hash(),
            "provider": result.provider or getattr(provider, "name", "unknown"),
            "model": result.model, "output_hash": result.output_hash or output_hash(summary, rtags),
        },
    )
    return base


def enrich_card(card: dict[str, Any], mode: str = "heuristic", provider: Any = None) -> dict[str, Any] | None:
    """Return a new enriched card, or None if the card is blocked (never enriched)."""
    if card["safety"].get("sensitivity") == "blocked":
        return None
    locked = snapshot_locked(card)
    out = copy.deepcopy(card)
    out["derived"] = build_derived(out, mode, provider)
    assert_only_derived(locked, out)  # source/provenance immutability
    return out
