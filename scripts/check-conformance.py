#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Check SEAG's pinned, machine-verifiable conformance profiles.

This is deliberately not a general standards-certification tool.  It checks
the claims SEAG actually makes, against the pinned register and local evidence.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from seag.cxl import export, parse_bytes
from seag.validate import absolute_iri, iso_timestamp, language_tag, strict_json_loads


ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "standards.yaml"
WHEN = "2026-11-22T00:00:00Z"
CLASSES = {"core", "conditional", "mapping", "export-profile", "publication-gate"}
EXPECTED = {
    "rfc2119-rfc8174": "core",
    "bcp47": "core",
    "uri-iri": "core",
    "uuid": "conditional",
    "json": "core",
    "json-schema": "core",
    "json-pointer": "core",
    "timestamp": "core",
    "unicode-normalization": "core",
    "json-canonicalization": "conditional",
    "w3c-prov": "mapping",
    "w3c-skos": "mapping",
    "spdx": "publication-gate",
    "cmaptools-cxl": "export-profile",
    "semantic-web-exports": "export-profile",
}


def register_entries(raw: str) -> tuple[dict[str, dict[str, str]], list[str]]:
    """Read the deliberately small top-level entry subset used by this gate."""

    entries: dict[str, dict[str, str]] = {}
    errors: list[str] = []
    current: dict[str, str] | None = None
    for line_number, line in enumerate(raw.splitlines(), 1):
        match = re.fullmatch(r"  - id: ([a-z0-9][a-z0-9-]*)", line)
        if match:
            identifier = match.group(1)
            if identifier in entries:
                errors.append(f"standards.yaml:{line_number}: duplicate standard id {identifier}")
            current = {"id": identifier}
            entries.setdefault(identifier, current)
            continue
        if current is not None:
            scalar = re.fullmatch(r"    ([a-z][a-z0-9_]*): (.+)", line)
            if scalar:
                current[scalar.group(1)] = scalar.group(2).strip('"')
    return entries, errors


def check_register() -> list[str]:
    try:
        raw = REGISTER.read_bytes().decode("utf-8")
    except (OSError, UnicodeError) as error:
        return [f"cannot read standards.yaml as UTF-8: {error}"]
    entries, errors = register_entries(raw)
    missing = sorted(set(EXPECTED) - set(entries))
    extra = sorted(set(entries) - set(EXPECTED))
    if missing:
        errors.append("missing registered standards: " + ", ".join(missing))
    if extra:
        errors.append("unclassified registered standards: " + ", ".join(extra))
    for identifier, expected_class in EXPECTED.items():
        entry = entries.get(identifier)
        if not entry:
            continue
        actual_class = entry.get("class")
        if actual_class not in CLASSES:
            errors.append(f"{identifier}: missing or unknown conformance class")
        elif actual_class != expected_class:
            errors.append(f"{identifier}: class is {actual_class}, expected {expected_class}")
    if entries.get("semantic-web-exports", {}).get("claim") != "not-yet-conformant":
        errors.append("semantic-web-exports must remain not-yet-conformant until tested profiles exist")
    if entries.get("cmaptools-cxl", {}).get("claim") != "compatible-parser-round-trip":
        errors.append("cmaptools-cxl claim must be limited to compatible-parser-round-trip")
    if 'registry_version: "2026-11-18"' not in raw:
        errors.append("bcp47: pinned IANA registry File-Date is missing")
    if "sha256:aa8ffda7d51ce4864e76186a349240cb6f01e086fab9cbc34e9c816bd778802a" not in raw:
        errors.append("cmaptools-cxl: pinned cmap.xsd digest is missing")
    return errors


def check_behavior() -> list[str]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require(all(language_tag(value) for value in ("en", "en-GB", "zh-Hant-TW", "x-seag", "i-klingon")),
            "bcp47: supported well-formed tag probe failed")
    require(not any(language_tag(value) for value in ("en_US", "not a tag", "en-a-x-a-y", "sl-rozaj-rozaj")),
            "bcp47: malformed tag rejection probe failed")
    require(all(absolute_iri(value) for value in ("https://example.invalid/id", "urn:uuid:12345678-1234-4234-8234-123456789abc", "https://example.invalid/ä")),
            "uri-iri: absolute IRI acceptance probe failed")
    require(not any(absolute_iri(value) for value in ("relative/path", "https://", "https://example.invalid/%GG")),
            "uri-iri: malformed IRI rejection probe failed")
    require(iso_timestamp("2026-11-22T12:34:56Z") and iso_timestamp("2026-11-22T14:34:56+02:00"),
            "timestamp: RFC 3339 acceptance probe failed")
    require(not iso_timestamp("2026-11-22T12:34:56"), "timestamp: timezone-less value was accepted")

    try:
        strict_json_loads('{"value":1,"text":"UTF-8: ä"}'.encode("utf-8"))
        for invalid in (b'{"value":1,"value":2}', b'{"value":NaN}', '{"value":1}'.encode("utf-16")):
            try:
                strict_json_loads(invalid)
            except (UnicodeError, ValueError, json.JSONDecodeError):
                continue
            errors.append("json: a forbidden JSON representation was accepted")
    except (UnicodeError, ValueError, json.JSONDecodeError) as error:
        errors.append(f"json: valid UTF-8 probe failed: {error}")

    for schema_path in sorted((ROOT / "schema").glob("*.schema.json")):
        try:
            schema = strict_json_loads(schema_path.read_bytes())
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
            errors.append(f"json-schema: {schema_path.relative_to(ROOT)} is invalid strict JSON: {error}")
            continue
        require(isinstance(schema, dict) and schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema",
                f"json-schema: {schema_path.relative_to(ROOT)} does not declare Draft 2020-12")

    require(unicodedata.unidata_version in {"15.0.0", "16.0.0"},
            f"unicode-normalization: unvalidated runtime Unicode data {unicodedata.unidata_version}")
    require(unicodedata.normalize("NFC", "A\N{COMBINING RING ABOVE}") == "Å",
            "unicode-normalization: NFC probe failed")

    mapping = (ROOT / "docs/semantic-mappings.md").read_text(encoding="utf-8")
    for marker in ("prov:Entity", "prov:Activity", "prov:Agent", "skos:Concept", "skos:prefLabel", "skos:broader"):
        require(marker in mapping, f"semantic mapping: required documented correspondence {marker} is missing")

    try:
        cxl, provenance, expected = export(ROOT / "fixtures/valid/manifest.json", WHEN)
        require(parse_bytes(cxl) == expected, "cmaptools-cxl: compatible-parser round trip changed the graph")
        require(hashlib.sha256(cxl).hexdigest() == provenance.get("output_sha256"),
                "cmaptools-cxl: output digest provenance does not match")
        require(cxl == (ROOT / "fixtures/expected/concept-map.cxl").read_bytes(),
                "cmaptools-cxl: pinned expected output is stale")
    except (OSError, UnicodeError, ValueError) as error:
        errors.append(f"cmaptools-cxl: profile probe failed: {error}")
    return errors


def main() -> int:
    errors = check_register() + check_behavior()
    if errors:
        print("standards conformance check: FAILED", file=sys.stderr)
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("standards conformance check: machine-verifiable profiles passed")
    print("documented mappings present: W3C PROV, W3C SKOS")
    print("conditional profiles inactive: UUID generation, RFC 8785 canonical semantic JSON")
    print("not claimed: JSON-LD, RDF, OWL, and PROV-O serialization")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
