"""Safe-export the Obsidian vault into a filtered snapshot (KIS-016).

GBrain only ever reads the EXPORT, never the raw vault. The exporter is
read-only w.r.t. the source vault — it only copies allowed files out.
"""

from __future__ import annotations

import os
import shutil
from typing import Any

from .filters import classify_file
from .manifest import build_manifest, content_hash


def export_vault(vault_dir: str, out_dir: str, dry_run: bool = False) -> dict[str, Any]:
    """Walk vault_dir, copy allowed files into out_dir/exported_vault, write
    manifests. Returns the manifest dict. dry_run=True computes but writes nothing."""
    export_dir = os.path.join(out_dir, "exported_vault")
    manifests_dir = os.path.join(out_dir, "manifests")
    included: list[dict[str, Any]] = []
    denied: list[dict[str, Any]] = []

    for root, _dirs, files in os.walk(vault_dir):
        for name in files:
            abs_path = os.path.join(root, name)
            rel = os.path.relpath(abs_path, vault_dir).replace("\\", "/")
            try:
                size = os.path.getsize(abs_path)
                with open(abs_path, "rb") as fh:
                    head = fh.read(4096)
            except OSError as e:
                denied.append({"source_path": rel, "reason": f"read error: {e}"})
                continue
            verdict = classify_file(rel, size, head)
            if not verdict.allowed:
                denied.append({"source_path": rel, "reason": verdict.reason})
                continue
            with open(abs_path, "rb") as fh:
                data = fh.read()
            entry = {
                "source_path": rel,
                "export_path": f"exported_vault/{rel}",
                "content_hash": content_hash(data),
                "size_bytes": size,
                "sensitivity": verdict.sensitivity,
                "reason": verdict.reason,
            }
            included.append(entry)
            if not dry_run:
                dest = os.path.join(export_dir, *rel.split("/"))
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copyfile(abs_path, dest)

    manifest = build_manifest(vault_dir, export_dir, included, denied)
    if not dry_run:
        os.makedirs(manifests_dir, exist_ok=True)
        _write_json(os.path.join(manifests_dir, "export_manifest.json"), manifest)
        _write_json(os.path.join(manifests_dir, "denied_files.json"), denied)
        _write_json(os.path.join(manifests_dir, "content_hashes.json"),
                    {e["source_path"]: e["content_hash"] for e in included})
    return manifest


def _write_json(path: str, obj: Any) -> None:
    import json
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)
