# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Read a validated SEAG source bundle for deterministic transformations."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .validate import validate


def load_bundle(manifest_path: Path) -> tuple[dict, list[tuple[dict, dict]], str]:
    manifest_path = manifest_path.resolve()
    errors = validate(manifest_path)
    if errors:
        raise ValueError("invalid SEAG bundle:\n" + "\n".join(errors))
    raw = manifest_path.read_bytes()
    manifest = json.loads(raw)
    records: list[tuple[dict, dict]] = []
    for item in manifest["fragments"]:
        fragment = json.loads((manifest_path.parent / item["path"]).read_text(encoding="utf-8"))
        records.extend((fragment, record) for record in fragment["records"])
    return manifest, records, hashlib.sha256(raw).hexdigest()


def package_version() -> str:
    return (Path(__file__).resolve().parents[1] / "VERSION").read_text().strip()
