# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Read a validated SEAG source bundle for deterministic transformations."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat

from .validate import validate
from .validation import strict_json_loads


def _read_confined(root: Path, relative: str) -> bytes:
    """Read one regular file without following any path-component symlink."""
    path = Path(relative)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise ValueError(f"unsafe fragment path: {relative!r}")
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    directory = os.open(root, directory_flags)
    try:
        for component in path.parts[:-1]:
            child = os.open(component, directory_flags | nofollow, dir_fd=directory)
            os.close(directory)
            directory = child
        descriptor = os.open(path.parts[-1], os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0), dir_fd=directory)
        try:
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise ValueError(f"fragment is not a regular file: {relative!r}")
            with os.fdopen(descriptor, "rb", closefd=False) as handle:
                return handle.read()
        finally:
            os.close(descriptor)
    finally:
        os.close(directory)


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
                    fragment_raws[item["path"]] = _read_confined(manifest_path.parent, item["path"])
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
