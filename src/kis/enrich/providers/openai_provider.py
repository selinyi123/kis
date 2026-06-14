"""Optional OpenAI provider (KIS-013b).

The openai SDK is imported LAZILY inside enrich() — importing this module never
requires openai. Requires OPENAI_API_KEY. Never exercised by the offline test
suite (the mock provider is used there).
"""

from __future__ import annotations

import json
import os

from ..prompt_contract import output_hash
from .base import EnrichmentRequest, EnrichmentResult, ProviderUnavailable


class OpenAIProvider:
    name = "openai"

    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")

    def enrich(self, request: EnrichmentRequest) -> EnrichmentResult:
        if not self.api_key:
            raise ProviderUnavailable("OPENAI_API_KEY is not set")
        try:
            from openai import OpenAI  # lazy import
        except ImportError as e:
            raise ProviderUnavailable("openai SDK not installed (`pip install openai`)") from e

        client = OpenAI(api_key=self.api_key)
        resp = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": request.prompt}],
            response_format={"type": "json_object"},
            temperature=0,
        )
        text = resp.choices[0].message.content or "{}"
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = {"summary": text.strip(), "reason_tags": []}
        summary = (data.get("summary") or "").strip()
        tags = list(data.get("reason_tags") or [])
        return EnrichmentResult(
            summary=summary,
            reason_tags=tags,
            provider="openai",
            model=self.model,
            output_hash=output_hash(summary, tags),
        )
