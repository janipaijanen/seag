# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Render or check a deterministic canonical SEAG source bundle."""

from __future__ import annotations

import argparse
import copy
import hashlib
import os
from pathlib import Path
import shutil
import sys
import tempfile

from .source import load_snapshot
from .transform import json_bytes
from .validate import validate


def render(manifest_path: Path) -> tuple[str, bytes, dict[str, bytes], dict[str, bytes], str]:
    """Return canonical bytes and the validated original bytes without writing."""
    manifest, fragments, manifest_digest = load_snapshot(manifest_path)
    canonical_fragments: dict[str, bytes] = {}
    original_fragments: dict[str, bytes] = {}
    inventory: list[dict] = []
    for item, fragment, raw in fragments:
        canonical_fragment = copy.deepcopy(fragment)
        canonical_fragment["records"] = sorted(canonical_fragment["records"], key=lambda record: record["id"])
        data = json_bytes(canonical_fragment)
        relative = item["path"]
        canonical_fragments[relative] = data
        original_fragments[relative] = raw
        canonical_item = copy.deepcopy(item)
        canonical_item["sha256"] = hashlib.sha256(data).hexdigest()
        inventory.append(canonical_item)
    canonical_manifest = copy.deepcopy(manifest)
    canonical_manifest["fragments"] = sorted(inventory, key=lambda item: (item["fragment_id"], item["path"]))
    return manifest_path.name, json_bytes(canonical_manifest), canonical_fragments, original_fragments, manifest_digest


def is_canonical(manifest_path: Path) -> bool:
    _name, manifest_data, fragments, originals, manifest_digest = render(manifest_path)
    return hashlib.sha256(manifest_data).hexdigest() == manifest_digest and all(
        originals[path] == data for path, data in fragments.items()
    )


def write(manifest_path: Path, output_dir: Path) -> Path:
    """Create a staged, validated canonical bundle directory; never overwrite."""
    name, manifest_data, fragments, _originals, _manifest_digest = render(manifest_path)
    output_dir = output_dir.resolve()
    if output_dir.exists():
        raise ValueError(f"output directory already exists: {output_dir}")
    parent = output_dir.parent
    if not parent.is_dir():
        raise ValueError(f"output parent is not a directory: {parent}")
    temporary = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.", dir=parent))
    try:
        for relative, data in fragments.items():
            target = temporary / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        output_manifest = temporary / name
        output_manifest.write_bytes(manifest_data)
        errors = validate(output_manifest)
        if errors:
            raise ValueError("canonical output failed validation:\n" + "\n".join(errors))
        # mkdir is the no-overwrite publication boundary. The validated staging
        # tree is then moved into the directory we exclusively created.
        output_dir.mkdir()
        try:
            for child in temporary.iterdir():
                os.rename(child, output_dir / child.name)
        except Exception:
            shutil.rmtree(output_dir, ignore_errors=True)
            raise
        temporary.rmdir()
        return output_dir / name
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true", help="exit 1 when source bytes are not canonical")
    action.add_argument("--output-dir", type=Path, help="create a canonical copy in a new directory")
    args = parser.parse_args(argv)
    try:
        if args.check:
            canonical = is_canonical(args.manifest)
            print("SEAG source bundle is canonical" if canonical else "SEAG source bundle is not canonical")
            return 0 if canonical else 1
        output_manifest = write(args.manifest, args.output_dir)
        print(f"Canonical SEAG source written to {output_manifest}")
        return 0
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
