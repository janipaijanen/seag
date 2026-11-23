# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Read a validated SEAG source bundle for deterministic transformations."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .validate import validate
from .validation import read_confined_regular, strict_json_loads


def load_snapshot(manifest_path: Path) -> tuple[dict, list[tuple[dict, dict, bytes]], str]:
    """Read and validate one immutable manifest-plus-fragments snapshot."""
    manifest_path = manifest_path.resolve()
    try:
        raw = manifest_path.read_bytes()
        manifest = strict_json_loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError(f"invalid SEAG bundle: cannot read manifest: {error}") from error
    fragment_raws: dict[str, bytes] = {}
    inventory = manifest.get("fragments", []) if isinstance(manifest, dict) else []
    if isinstance(inventory, list):
        for item in inventory:
            if isinstance(item, dict) and isinstance(item.get("path"), str):
                try:
                    fragment_raws[item["path"]] = read_confined_regular(
                        manifest_path.parent, item["path"]
                    )
                except (OSError, ValueError):
                    # The validator reports the path as unreadable from this immutable snapshot.
                    pass
    errors = validate(manifest_path, manifest_raw=raw, fragment_raws=fragment_raws)
    if errors:
        raise ValueError("invalid SEAG bundle:\n" + "\n".join(errors))
    fragments: list[tuple[dict, dict, bytes]] = []
    for item in manifest["fragments"]:
        fragment = strict_json_loads(fragment_raws[item["path"]])
        fragments.append((item, fragment, fragment_raws[item["path"]]))
    return manifest, fragments, hashlib.sha256(raw).hexdigest()


def load_bundle(manifest_path: Path) -> tuple[dict, list[tuple[dict, dict]], str]:
    manifest, fragments, digest = load_snapshot(manifest_path)
    records: list[tuple[dict, dict]] = []
    for _item, fragment, _raw in fragments:
        records.extend((fragment, record) for record in fragment["records"])
    return manifest, records, digest


def package_version() -> str:
    return (Path(__file__).resolve().parents[1] / "VERSION").read_text().strip()
