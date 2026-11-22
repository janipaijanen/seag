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
import sys
import unicodedata

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from seag.cxl import export, parse_bytes
from seag.validation import (
    absolute_iri,
    ipv4_address,
    ipv6_address,
    iso_timestamp,
    language_tag,
    port_number,
    strict_json_loads,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "standards.json"
WHEN = "2026-11-22T00:00:00Z"
CLASSES = {"core", "conditional", "mapping", "export-profile", "publication-gate"}
EXPECTED = {
    "rfc2119-rfc8174": "core",
    "bcp47": "core",
    "uri-iri": "core",
    "ip-address-literals": "core",
    "internet-port-range": "core",
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
COMMON_FIELDS = {"id", "title", "class"}
ENTRY_FIELDS = {
    "rfc2119-rfc8174": COMMON_FIELDS | {"versions", "applies_to"},
    "bcp47": COMMON_FIELDS | {
        "versions", "registry", "registry_version_field", "registry_version", "applies_to"
    },
    "uri-iri": COMMON_FIELDS | {"versions", "applies_to"},
    "ip-address-literals": COMMON_FIELDS | {"versions", "applies_to"},
    "internet-port-range": COMMON_FIELDS | {"versions", "claim", "applies_to"},
    "uuid": COMMON_FIELDS | {"versions", "condition"},
    "json": COMMON_FIELDS | {"versions", "applies_to"},
    "json-schema": COMMON_FIELDS | {"versions", "applies_to"},
    "json-pointer": COMMON_FIELDS | {"versions", "applies_to"},
    "timestamp": COMMON_FIELDS | {"versions", "applies_to"},
    "unicode-normalization": COMMON_FIELDS | {
        "versions", "normalization_form", "version_evidence",
        "runtime_version_recorded_in_transformation_provenance", "validated_versions",
    },
    "json-canonicalization": COMMON_FIELDS | {"versions", "condition"},
    "w3c-prov": COMMON_FIELDS | {"versions", "claim", "serialization_required"},
    "w3c-skos": COMMON_FIELDS | {"versions", "claim", "serialization_required"},
    "spdx": COMMON_FIELDS | {"versions", "license_list_version"},
    "cmaptools-cxl": COMMON_FIELDS | {
        "version", "claim", "compatible_parser", "limitations"
    },
    "semantic-web-exports": COMMON_FIELDS | {"version", "claim"},
}


def check_register() -> list[str]:
    try:
        register = strict_json_loads(REGISTER.read_bytes())
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        return [f"cannot parse standards.json as strict UTF-8 JSON: {error}"]
    if not isinstance(register, dict):
        return ["standards.json: top-level value must be an object"]

    errors: list[str] = []
    required_top = {"seag_standards_register", "status", "conformance_classes", "standards"}
    if set(register) != required_top:
        errors.append("standards.json: top-level fields do not match the closed register contract")
    if register.get("seag_standards_register") != "0.1":
        errors.append("standards.json: unsupported register version")
    if register.get("status") != "pinned-for-0.1":
        errors.append("standards.json: status must remain pinned-for-0.1")
    if register.get("conformance_classes") != [
        "core", "conditional", "mapping", "export-profile", "publication-gate"
    ]:
        errors.append("standards.json: conformance classes or their canonical order changed")

    raw_entries = register.get("standards")
    if not isinstance(raw_entries, list):
        return errors + ["standards.json: standards must be an array"]
    entries: dict[str, dict[str, object]] = {}
    for index, entry in enumerate(raw_entries):
        if not isinstance(entry, dict):
            errors.append(f"standards.json: standards/{index} must be an object")
            continue
        identifier = entry.get("id")
        if not isinstance(identifier, str):
            errors.append(f"standards.json: standards/{index}/id must be a string")
            continue
        if identifier in entries:
            errors.append(f"standards.json: duplicate standard id {identifier}")
            continue
        entries[identifier] = entry
        expected_fields = ENTRY_FIELDS.get(identifier)
        if expected_fields is not None and set(entry) != expected_fields:
            errors.append(f"{identifier}: fields do not match its closed register contract")
        if not isinstance(entry.get("title"), str) or not entry["title"]:
            errors.append(f"{identifier}: title must be a nonempty string")
        versions = entry.get("versions")
        version = entry.get("version")
        if not (
            isinstance(version, str) and version
            or isinstance(versions, list) and versions
            and all(isinstance(item, str) and item for item in versions)
        ):
            errors.append(f"{identifier}: version or versions must identify a nonempty pin")

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
    if entries.get("internet-port-range", {}).get("claim") != "numeric-range-only":
        errors.append("internet-port-range must not claim assignment or service suitability")
    if entries.get("bcp47", {}).get("registry_version") != "2026-11-18":
        errors.append("bcp47: pinned IANA registry File-Date is missing")
    if entries.get("cmaptools-cxl", {}).get("version") != (
        "IHMC public cmap.xsd sha256:"
        "aa8ffda7d51ce4864e76186a349240cb6f01e086fab9cbc34e9c816bd778802a"
    ):
        errors.append("cmaptools-cxl: pinned cmap.xsd digest is missing")
    compatible_parser = entries.get("cmaptools-cxl", {}).get("compatible_parser")
    if not isinstance(compatible_parser, dict) or set(compatible_parser) != {
        "implementation", "ci_image", "linux_amd64_manifest"
    } or not all(isinstance(value, str) and value for value in compatible_parser.values()):
        errors.append("cmaptools-cxl: compatible parser evidence is malformed")
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
    require(not any(absolute_iri(value) for value in ("relative/path", "https://", "https://example.invalid/%GG", "https://example.invalid:65536/", "https://256.1.1.1/", "https://[2001:db8:::1]/")),
            "uri-iri: malformed IRI rejection probe failed")
    require(port_number(0) and port_number(65535) and not port_number(-1) and not port_number(65536),
            "network values: port range probe failed")
    require(ipv4_address("192.0.2.1") and not ipv4_address("256.0.2.1"),
            "network values: IPv4 octet probe failed")
    require(ipv6_address("2001:db8::1") and not ipv6_address("2001:db8:::1"),
            "network values: IPv6 syntax probe failed")
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
