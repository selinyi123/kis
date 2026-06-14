"""Minimal, zero-dependency JSON-Schema validator for KnowledgeCard.

Honors the subset of draft-07 the KnowledgeCard schema actually uses:
type, required, enum, properties, items, additionalProperties:false.

Why hand-rolled instead of `jsonschema`: ClipVault's desktop discipline is zero
third-party runtime deps. PPE's contract rule "reject unknown fields by default"
is the property we most need, and additionalProperties:false gives us exactly
that. If you later want full draft-07, swap this for the `jsonschema` package —
the schema file is standard and portable.
"""

from __future__ import annotations

import json
import os
from typing import Any

_SCHEMA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "schema",
    "knowledge-card.schema.json",
)

_TYPE_MAP = {
    "object": dict,
    "array": list,
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "null": type(None),
}


class ValidationError(Exception):
    pass


def load_schema(path: str | None = None) -> dict[str, Any]:
    with open(path or _SCHEMA_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _check(node: Any, schema: dict[str, Any], path: str, errors: list[str]) -> None:
    expected = schema.get("type")
    if expected:
        py = _TYPE_MAP.get(expected)
        # bool is a subclass of int — guard so True does not satisfy "integer".
        if expected == "integer" and isinstance(node, bool):
            errors.append(f"{path}: expected integer, got boolean")
            return
        if py is not None and not isinstance(node, py):
            errors.append(f"{path}: expected {expected}, got {type(node).__name__}")
            return

    if "enum" in schema and node not in schema["enum"]:
        errors.append(f"{path}: value {node!r} not in enum {schema['enum']}")

    if expected == "object" and isinstance(node, dict):
        props = schema.get("properties", {})
        for req in schema.get("required", []):
            if req not in node:
                errors.append(f"{path}: missing required field '{req}'")
        if schema.get("additionalProperties") is False:
            for key in node:
                if key not in props:
                    errors.append(f"{path}: unknown field '{key}' (additionalProperties:false)")
        for key, sub in props.items():
            if key in node:
                _check(node[key], sub, f"{path}.{key}", errors)

    if expected == "array" and isinstance(node, list):
        item_schema = schema.get("items")
        if item_schema:
            for i, item in enumerate(node):
                _check(item, item_schema, f"{path}[{i}]", errors)


def validate_card(card: dict[str, Any], schema: dict[str, Any] | None = None) -> list[str]:
    """Return a list of human-readable errors. Empty list == valid."""
    schema = schema or load_schema()
    errors: list[str] = []
    _check(card, schema, "card", errors)
    return errors


def assert_valid(card: dict[str, Any], schema: dict[str, Any] | None = None) -> None:
    errors = validate_card(card, schema)
    if errors:
        raise ValidationError("KnowledgeCard invalid:\n  - " + "\n  - ".join(errors))
