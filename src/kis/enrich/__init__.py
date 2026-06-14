"""KIS-013 AI enrichment — the derived layer.

Strict boundary (see docs/KIS-013_PROMPT_INJECTION_BOUNDARY.md):
  * writes ONLY card["derived"], never source/content/enrichment/provenance;
  * LLM output is an opinion, never a fact source;
  * every result carries reproducible generator metadata
    (mode/provider/model/prompt_hash/input_hash/output_hash/generated_at);
  * blocked cards are never enriched;
  * heuristic baseline runs fully offline; LLM providers are optional.
"""

from .heuristic import build_derived, enrich_card

__all__ = ["build_derived", "enrich_card"]
