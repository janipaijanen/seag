# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Extract a provenance-preserving glossary from a SEAG source bundle."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import unicodedata

from .source import load_bundle, package_version
from .transform import timestamp, write_with_provenance


NAMED_KINDS = {"concept", "lifecycle_state", "rule_reference", "external_reference"}


def extract(manifest_path: Path, language: str, generated_at: str) -> tuple[dict, dict]:
    manifest, records, source_digest = load_bundle(manifest_path)
    selected = [(fragment, record) for fragment, record in records if fragment["language"] == language and record["kind"] in NAMED_KINDS]
    if not selected:
        raise ValueError(f"no named records for exact language {language!r}; fallback policy is none")
    namespace = manifest["namespace"]
    entries = []
    for fragment, record in selected:
        entry = {
            "id": namespace + record["id"],
            "local_id": record["id"],
            "kind": record["kind"],
            "label": record["label"],
            "definition": record["definition"],
            "language": fragment["language"],
            "source_fragment_id": fragment["fragment_id"],
            "source_fragment_revision": fragment["revision"],
            "status": record["status"],
            "implementation_alignment": record["implementation_alignment"],
            "source_provenance": record["provenance"],
        }
        if "iri" in record:
            entry["external_iri"] = record["iri"]
        entries.append(entry)
    entries.sort(key=lambda item: item["id"])
    result = {
        "schema": "seag/glossary/v1",
        "bundle_id": manifest["bundle_id"],
        "title": manifest["title"],
        "language": language,
        "licence": manifest["licence"],
        "entries": entries,
    }
    provenance = {
        "schema": "seag/transformation-provenance/v1",
        "transformation": "glossary-extraction",
        "generator": f"seag/{package_version()}",
        "generated_at": generated_at,
        "source_bundle_id": manifest["bundle_id"],
        "source_manifest_sha256": source_digest,
        "requested_language": language,
        "language_selection": "exact",
        "fallback_policy": "none",
        "entry_count": len(entries),
        "source_fragment_ids": sorted({fragment["fragment_id"] for fragment, _ in selected}),
        "unicode_data_version": unicodedata.unidata_version,
    }
    return result, provenance


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--language", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--provenance-output", type=Path)
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    try:
        result, provenance = extract(args.manifest, args.language, timestamp(args.generated_at))
        write_with_provenance(args.output, result, provenance, args.provenance_output)
    except (OSError, ValueError) as error:
        print(f"glossary extraction failed: {error}", file=sys.stderr)
        return 1
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
