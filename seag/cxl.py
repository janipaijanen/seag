# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Export the bounded SEAG source model to deterministic Cmap CXL."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET

from .source import load_bundle, package_version
from .transform import json_bytes, timestamp
from .validate import absolute_iri, language_tag


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


def _expected_graph(manifest: dict, records: list[tuple[dict, dict]], digest: str) -> tuple[dict, dict, str]:
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


def expected_graph(manifest_path: Path) -> tuple[dict, dict, str]:
    return _expected_graph(*load_bundle(manifest_path))


def export(manifest_path: Path, generated_at: str) -> tuple[bytes, dict, dict]:
    manifest, records, source_digest = load_bundle(manifest_path)
    graph, record_provenance, source_digest = _expected_graph(manifest, records, source_digest)
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
    body = text.lstrip()
    if body.startswith("<?"):
        end = body.find("?>")
        if end < 0:
            raise ValueError("unterminated XML declaration or processing instruction")
        declaration = body[: end + 2]
        declaration_pattern = (
            r"<\?xml[ \t\r\n]+version=(?P<version_quote>['\"])1\.0(?P=version_quote)"
            r"(?:[ \t\r\n]+encoding=(?P<encoding_quote>['\"])[Uu][Tt][Ff]-8(?P=encoding_quote))?"
            r"(?:[ \t\r\n]+standalone=(?P<standalone_quote>['\"])(?:yes|no)(?P=standalone_quote))?"
            r"[ \t\r\n]*\?>"
        )
        if not re.fullmatch(declaration_pattern, declaration):
            raise ValueError("processing instructions are outside the SEAG CXL profile")
        body = body[end + 2 :]
    if "<?" in body or "<!--" in body or "<![CDATA[" in body:
        raise ValueError("processing instructions, comments, and CDATA are outside the SEAG CXL profile")
    root = ET.fromstring(text)

    def expect_container(element: ET.Element, tag: str, children: list[str]) -> list[ET.Element]:
        if element.tag != tag or element.attrib:
            raise ValueError(f"unexpected CXL element or attributes: {element.tag}")
        if element.text and element.text.strip():
            raise ValueError(f"unexpected text in CXL container: {element.tag}")
        actual = list(element)
        if [child.tag for child in actual] != children:
            raise ValueError(f"unexpected CXL children in {element.tag}")
        if any(child.tail and child.tail.strip() for child in actual):
            raise ValueError(f"unexpected mixed content in {element.tag}")
        return actual

    metadata, map_node = expect_container(root, f"{{{CXL}}}cmap", [f"{{{CXL}}}res-meta", f"{{{CXL}}}map"])
    title_node, identifier_node, language_node = expect_container(
        metadata,
        f"{{{CXL}}}res-meta",
        [f"{{{DC}}}title", f"{{{DC}}}identifier", f"{{{DC}}}language"],
    )
    for node in (title_node, identifier_node, language_node):
        if node.attrib or list(node) or node.text is None or not node.text.strip():
            raise ValueError(f"invalid CXL metadata value: {node.tag}")
    if not absolute_iri(identifier_node.text):
        raise ValueError("CXL identifier must be an absolute IRI")
    if not language_tag(language_node.text):
        raise ValueError("CXL language must be a well-formed BCP 47 tag")

    concept_list, link_list, connection_list = expect_container(
        map_node,
        f"{{{CXL}}}map",
        [f"{{{CXL}}}concept-list", f"{{{CXL}}}linking-phrase-list", f"{{{CXL}}}connection-list"],
    )

    def nodes(element: ET.Element, child_tag: str) -> dict[str, str]:
        if element.attrib or (element.text and element.text.strip()):
            raise ValueError(f"invalid CXL list: {element.tag}")
        result: dict[str, str] = {}
        for child in element:
            if child.tag != child_tag or set(child.attrib) != {"id", "label"} or list(child):
                raise ValueError(f"unexpected CXL node shape: {child.tag}")
            if (child.text and child.text.strip()) or (child.tail and child.tail.strip()):
                raise ValueError(f"unexpected CXL node mixed content: {child.tag}")
            identifier, label = child.attrib["id"], child.attrib["label"]
            if not absolute_iri(identifier) or not label.strip():
                raise ValueError("CXL nodes require an absolute IRI and nonempty label")
            if identifier in result:
                raise ValueError(f"duplicate CXL node identifier: {identifier!r}")
            result[identifier] = label
        return result

    concepts = nodes(concept_list, f"{{{CXL}}}concept")
    links = nodes(link_list, f"{{{CXL}}}linking-phrase")
    if set(concepts) & set(links):
        raise ValueError("CXL concept and linking-phrase identifiers must be disjoint")
    if connection_list.attrib or (connection_list.text and connection_list.text.strip()):
        raise ValueError("invalid CXL connection list")
    connections = []
    for child in connection_list:
        if child.tag != f"{{{CXL}}}connection" or set(child.attrib) != {"from-id", "to-id"} or list(child):
            raise ValueError(f"unexpected CXL connection shape: {child.tag}")
        if (child.text and child.text.strip()) or (child.tail and child.tail.strip()):
            raise ValueError("unexpected CXL connection mixed content")
        edge = (child.attrib["from-id"], child.attrib["to-id"])
        if edge[0] not in concepts | links or edge[1] not in concepts | links:
            raise ValueError("CXL connection endpoint is not declared")
        if (edge[0] in concepts) == (edge[1] in concepts):
            raise ValueError("CXL connection must join one concept and one linking phrase")
        if edge in connections:
            raise ValueError("duplicate CXL connection")
        connections.append(edge)
    for identifier in links:
        incoming = [edge for edge in connections if edge[1] == identifier and edge[0] in concepts]
        outgoing = [edge for edge in connections if edge[0] == identifier and edge[1] in concepts]
        if len(incoming) != 1 or len(outgoing) != 1:
            raise ValueError("each SEAG CXL linking phrase requires one source and one target concept")
    connections.sort()
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
