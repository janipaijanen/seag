# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Export the bounded SEAG source model to deterministic Cmap CXL."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path
import sys
import unicodedata
import xml.etree.ElementTree as ET

from .source import load_bundle, package_version
from .transform import json_bytes, timestamp


CXL = "http://cmap.ihmc.us/xml/cmap/"
DC = "http://purl.org/dc/elements/1.1/"
ET.register_namespace("", CXL)
ET.register_namespace("dc", DC)


def xml_text(value: str) -> str:
    if any(
        character not in "\t\n\r"
        and not "\x20" <= character <= "\ud7ff"
        and not "\ue000" <= character <= "\ufffd"
        and not "\U00010000" <= character <= "\U0010ffff"
        for character in value
    ):
        raise ValueError("CXL text contains an XML-forbidden character")
    return value


def expected_graph(manifest_path: Path) -> tuple[dict, dict, str]:
    manifest, records, digest = load_bundle(manifest_path)
    namespace = manifest["namespace"]
    concepts = {namespace + r["id"]: r["label"] for _, r in records if r["kind"] != "proposition"}
    links = {}
    connections = []
    provenance = {}
    for _, record in records:
        expanded = namespace + record["id"]
        provenance[expanded] = record["provenance"]
        if record["kind"] == "proposition":
            links[expanded] = record.get("name", record["predicate"])
            connections.extend(((namespace + record["source"], expanded), (expanded, namespace + record["target"])))
    return {"concepts": concepts, "linking_phrases": links, "connections": sorted(connections)}, provenance, digest


def export(manifest_path: Path, generated_at: str) -> tuple[bytes, dict, dict]:
    manifest, _, _ = load_bundle(manifest_path)
    graph, record_provenance, source_digest = expected_graph(manifest_path)
    root = ET.Element(f"{{{CXL}}}cmap")
    meta = ET.SubElement(root, f"{{{CXL}}}res-meta")
    ET.SubElement(meta, f"{{{DC}}}title").text = xml_text(manifest["title"])
    ET.SubElement(meta, f"{{{DC}}}identifier").text = xml_text(manifest["bundle_id"])
    ET.SubElement(meta, f"{{{DC}}}language").text = xml_text(manifest["default_language"])
    map_node = ET.SubElement(root, f"{{{CXL}}}map")
    concept_list = ET.SubElement(map_node, f"{{{CXL}}}concept-list")
    for ident, label in sorted(graph["concepts"].items()):
        ET.SubElement(concept_list, f"{{{CXL}}}concept", {"id": xml_text(ident), "label": xml_text(label)})
    link_list = ET.SubElement(map_node, f"{{{CXL}}}linking-phrase-list")
    for ident, label in sorted(graph["linking_phrases"].items()):
        ET.SubElement(link_list, f"{{{CXL}}}linking-phrase", {"id": xml_text(ident), "label": xml_text(label)})
    connection_list = ET.SubElement(map_node, f"{{{CXL}}}connection-list")
    for source, target in graph["connections"]:
        ET.SubElement(connection_list, f"{{{CXL}}}connection", {"from-id": xml_text(source), "to-id": xml_text(target)})
    ET.indent(root, space="  ")
    data = ET.tostring(root, encoding="utf-8", xml_declaration=True, short_empty_elements=True) + b"\n"
    sidecar = {
        "schema": "seag/transformation-provenance/v1",
        "transformation": "cmaptools-cxl-export",
        "profile": "seag/cxl/0.1",
        "generator": f"seag/{package_version()}",
        "generated_at": generated_at,
        "source_bundle_id": manifest["bundle_id"],
        "source_manifest_sha256": source_digest,
        "output_sha256": hashlib.sha256(data).hexdigest(),
        "lossless": False,
        "omissions": [
            "confirmation metadata",
            "definitions",
            "external reference IRIs",
            "bundle licence",
            "bundle draft status",
            "controlled-predicate versus named-association distinction",
            "fragment identity and revision",
            "fragment inventory paths and digests",
            "fragment role",
            "grammatical number",
            "implementation alignment",
            "per-record language",
            "record kind distinctions",
            "record-to-fragment membership",
            "replacement or deprecation rationale",
            "semantic status",
            "source contract identity",
            "source namespace",
            "source record provenance from CXL (retained in the sidecar)",
            "source and target cardinalities",
            "visual layout",
        ],
        "record_provenance": record_provenance,
        "compatible_parser": {
            "implementation": "CPython xml.etree.ElementTree",
            "python_version": platform.python_version(),
            "elementtree_version": ET.VERSION,
        },
        "unicode_data_version": unicodedata.unidata_version,
    }
    return data, sidecar, graph


def parse_bytes(raw: bytes) -> dict:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("CXL verification accepts UTF-8 only") from error
    upper = text.upper()
    if "<!DOCTYPE" in upper or "<!ENTITY" in upper:
        raise ValueError("DTD and entity declarations are forbidden in CXL verification")
    root = ET.fromstring(text)
    ns = {"c": CXL}
    concepts = {e.attrib["id"]: e.attrib["label"] for e in root.findall(".//c:concept-list/c:concept", ns)}
    links = {e.attrib["id"]: e.attrib["label"] for e in root.findall(".//c:linking-phrase-list/c:linking-phrase", ns)}
    connections = sorted((e.attrib["from-id"], e.attrib["to-id"]) for e in root.findall(".//c:connection-list/c:connection", ns))
    return {"concepts": concepts, "linking_phrases": links, "connections": connections}


def parse(path: Path) -> dict:
    return parse_bytes(path.read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--provenance-output", type=Path)
    parser.add_argument("--generated-at")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    try:
        data, sidecar, expected = export(args.manifest, timestamp(args.generated_at))
        if args.verify and parse_bytes(data) != expected:
            raise ValueError("compatible-parser round trip changed identifiers, labels, or connections")
        args.output.write_bytes(data)
        provenance_path = args.provenance_output or args.output.with_name(args.output.name + ".provenance.json")
        provenance_path.write_bytes(json_bytes(sidecar))
    except (ET.ParseError, OSError, ValueError) as error:
        print(f"CXL export failed: {error}", file=sys.stderr)
        return 1
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
