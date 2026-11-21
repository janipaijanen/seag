"""Dependency-free validator for the bounded SEAG 0.1 draft source contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

SCHEMA = "0.1-draft"
LOCAL_ID = re.compile(r"^[A-Za-z][A-Za-z0-9._-]*$")
STATUS = {"proposed", "confirmed", "deprecated", "unresolved"}
ALIGNMENT = {"unchecked", "matches", "diverges", "not_applicable"}
CARDINALITY = {"0..1", "1..1", "1..*", "0..*", "unresolved"}
ENDPOINTS = {
    "is a kind of": ({"concept"}, {"concept"}),
    "is part of": ({"concept"}, {"concept"}),
    "refers to": ({"concept"}, {"concept", "external_reference"}),
    "has lifecycle state": ({"concept"}, {"lifecycle_state"}),
    "is governed by rule": ({"concept"}, {"rule_reference"}),
    "named association": ({"concept"}, {"concept"}),
}
KINDS = {"concept", "lifecycle_state", "rule_reference", "external_reference", "proposition"}
PROPOSITION_FIELDS = {"id", "kind", "status", "implementation_alignment", "provenance", "confirmation", "replacement_or_reason", "source", "target", "predicate", "name", "definition", "source_cardinality", "target_cardinality"}
PROCESS_NAME = re.compile(r"\b(precedes?|follows?|followed|triggers?|transitions?|changes?\s+state|next\s+state|before|after|causes?|enables?|step|workflow|sequence)\b", re.IGNORECASE)
VAGUE_NAMES = {"relates to", "is related to", "associated with", "is associated with", "linked to", "is linked to", "connection", "relation"}
EVIDENCE_STATUS = {"unresolved", "qualified", "verified", "rejected"}


def absolute_iri(value: object) -> bool:
    if not isinstance(value, str) or not value or any(c.isspace() for c in value):
        return False
    parts = urlsplit(value)
    if parts.scheme in {"http", "https"}:
        return bool(parts.netloc)
    return parts.scheme == "urn" and ":" in parts.path and all(parts.path.split(":", 1))


def _load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def validate(manifest_path: Path) -> list[str]:
    errors: list[str] = []

    def check(ok: bool, location: str, message: str) -> None:
        if not ok:
            errors.append(f"{location}: {message}")

    try:
        manifest = _load_json(manifest_path)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"{manifest_path}: cannot read JSON: {exc}"]
    if not isinstance(manifest, dict):
        return [f"{manifest_path}: manifest must be an object"]
    check(manifest.get("seag_schema") == SCHEMA, "manifest.seag_schema", f"expected {SCHEMA}")
    bundle_id = manifest.get("bundle_id")
    namespace = manifest.get("namespace")
    check(absolute_iri(bundle_id), "manifest.bundle_id", "absolute IRI required")
    check(absolute_iri(namespace) and namespace.endswith(("#", "/")), "manifest.namespace", "absolute IRI ending in # or / required")
    for field in ("title", "default_language", "licence"):
        check(isinstance(manifest.get(field), str) and bool(manifest[field].strip()), f"manifest.{field}", "nonempty string required")
    check(manifest.get("status") == "draft", "manifest.status", "this validator accepts draft bundles only")
    inventory = manifest.get("fragments")
    if not isinstance(inventory, list) or not inventory:
        return errors + ["manifest.fragments: nonempty array required"]

    seen_fragments: set[str] = set()
    records: dict[str, dict] = {}
    propositions: list[tuple[str, dict]] = []
    for index, item in enumerate(inventory):
        where = f"manifest.fragments[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{where}: object required")
            continue
        fragment_id = item.get("fragment_id")
        check(isinstance(fragment_id, str) and bool(LOCAL_ID.fullmatch(fragment_id)), where + ".fragment_id", "stable local ID required")
        check(isinstance(item.get("role"), str) and bool(item["role"].strip()), where + ".role", "nonempty role required")
        if isinstance(fragment_id, str):
            check(fragment_id not in seen_fragments, where + ".fragment_id", "duplicate fragment ID")
            seen_fragments.add(fragment_id)
        name = item.get("path")
        if not isinstance(name, str) or not name or Path(name).is_absolute() or ".." in Path(name).parts:
            errors.append(f"{where}.path: safe relative path required")
            continue
        path = manifest_path.parent / name
        if not path.resolve().is_relative_to(manifest_path.parent.resolve()):
            errors.append(f"{where}.path: path escapes manifest directory")
            continue
        try:
            raw = path.read_bytes()
            fragment = json.loads(raw)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"{where}.path: cannot read fragment: {exc}")
            continue
        digest = hashlib.sha256(raw).hexdigest()
        check(item.get("sha256") == digest, where + ".sha256", "fragment byte digest mismatch")
        if not isinstance(fragment, dict):
            errors.append(f"{name}: fragment must be an object")
            continue
        for field, expected in (("seag_schema", SCHEMA), ("bundle_id", bundle_id), ("namespace", namespace), ("fragment_id", fragment_id), ("role", item.get("role"))):
            check(fragment.get(field) == expected, name + "." + field, "does not match manifest")
        for field in ("language", "revision"):
            check(isinstance(fragment.get(field), str) and bool(fragment[field].strip()), name + "." + field, "nonempty string required")
        source_records = fragment.get("records")
        if not isinstance(source_records, list):
            errors.append(f"{name}.records: array required")
            continue
        for record_index, record in enumerate(source_records):
            loc = f"{name}.records[{record_index}]"
            if not isinstance(record, dict):
                errors.append(f"{loc}: object required")
                continue
            ident, kind = record.get("id"), record.get("kind")
            check(isinstance(ident, str) and bool(LOCAL_ID.fullmatch(ident)), loc + ".id", "stable local ID required")
            check(isinstance(kind, str) and kind in KINDS, loc + ".kind", "unknown record kind")
            if isinstance(ident, str):
                check(ident not in records, loc + ".id", "duplicate expanded record ID")
                if ident not in records:
                    records[ident] = record
            check(isinstance(record.get("status"), str) and record["status"] in STATUS, loc + ".status", "invalid semantic status")
            check(isinstance(record.get("implementation_alignment"), str) and record["implementation_alignment"] in ALIGNMENT, loc + ".implementation_alignment", "separate alignment status required")
            provenance = record.get("provenance")
            check(isinstance(provenance, dict) and all(isinstance(provenance.get(k), str) and provenance[k].strip() for k in ("source", "locator", "proposer")) and isinstance(provenance.get("normative"), bool) and isinstance(provenance.get("verification_status"), str) and provenance["verification_status"] in EVIDENCE_STATUS, loc + ".provenance", "source, locator, proposer, normative boolean, and evidence verification status required")
            if record.get("status") == "confirmed":
                confirmation = record.get("confirmation")
                check(isinstance(confirmation, dict) and all(isinstance(confirmation.get(k), str) and confirmation[k].strip() for k in ("decision_ref", "decided_at", "confirmer", "reviewer")), loc + ".confirmation", "confirmed record needs decision reference, date, confirmer, and independent reviewer")
                if isinstance(confirmation, dict) and isinstance(provenance, dict):
                    check(confirmation.get("reviewer") != provenance.get("proposer"), loc + ".confirmation.reviewer", "reviewer must differ from proposer")
                check(isinstance(provenance, dict) and provenance.get("verification_status") == "verified", loc + ".provenance.verification_status", "confirmed record needs verified evidence")
            if record.get("status") == "deprecated":
                check(isinstance(record.get("replacement_or_reason"), str) and bool(record["replacement_or_reason"].strip()), loc + ".replacement_or_reason", "deprecated record needs replacement or rationale")
            if kind == "proposition":
                extras = sorted(set(record) - PROPOSITION_FIELDS)
                check(not extras, loc, "unsupported proposition fields: " + ", ".join(extras) + "; process/extension semantics are not supported")
                propositions.append((loc, record))
            elif kind == "external_reference":
                check(absolute_iri(record.get("iri")), loc + ".iri", "absolute external IRI required")
            elif kind == "rule_reference":
                check(absolute_iri(record.get("iri")), loc + ".iri", "absolute rule artifact IRI required")
            elif isinstance(kind, str) and kind in KINDS:
                for field in ("label", "definition"):
                    check(isinstance(record.get(field), str) and bool(record[field].strip()), loc + "." + field, "nonempty string required")

    taxonomy: dict[str, list[str]] = {}
    for loc, record in propositions:
        predicate = record.get("predicate")
        check(isinstance(predicate, str) and predicate in ENDPOINTS, loc + ".predicate", "controlled predicate required; process flow and transitions are outside SEAG source vocabulary")
        source, target = record.get("source"), record.get("target")
        source_found = isinstance(source, str) and source in records
        target_found = isinstance(target, str) and target in records
        check(source_found, loc + ".source", "unresolved local endpoint")
        check(target_found, loc + ".target", "unresolved local endpoint")
        if isinstance(predicate, str) and predicate in ENDPOINTS and source_found and target_found:
            src_kinds, dst_kinds = ENDPOINTS[predicate]
            source_kind = records[source].get("kind")
            target_kind = records[target].get("kind")
            check(isinstance(source_kind, str) and source_kind in src_kinds, loc + ".source", "wrong endpoint type")
            check(isinstance(target_kind, str) and target_kind in dst_kinds, loc + ".target", "wrong endpoint type")
            if predicate == "is a kind of":
                taxonomy.setdefault(source, []).append(target)
        if predicate == "named association":
            check(isinstance(record.get("name"), str) and bool(record["name"].strip()), loc + ".name", "association name required")
            name = record.get("name")
            if isinstance(name, str):
                normalized = " ".join(name.lower().split())
                check(not PROCESS_NAME.search(normalized), loc + ".name", "process or transition association name forbidden")
                check(normalized not in VAGUE_NAMES, loc + ".name", "vague association name; use a bounded static semantic relation")
            check(isinstance(record.get("definition"), str) and bool(record["definition"].strip()), loc + ".definition", "bounded static association definition required")
            for end in ("source_cardinality", "target_cardinality"):
                check(isinstance(record.get(end), str) and record[end] in CARDINALITY, loc + "." + end, "explicit both-end cardinality required")
                if record.get("status") == "confirmed":
                    check(record.get(end) != "unresolved", loc + "." + end, "confirmed cardinality cannot be unresolved")

    visiting: set[str] = set()
    visited: set[str] = set()

    def walk(node: str) -> None:
        if node in visiting:
            errors.append(f"taxonomy: cycle at {node}")
            return
        if node in visited:
            return
        visiting.add(node)
        for parent in taxonomy.get(node, []):
            walk(parent)
        visiting.remove(node)
        visited.add(node)

    for node in taxonomy:
        walk(node)

    return errors


def validate_variant(path: Path) -> list[str]:
    """Check metadata shape only; release provenance needs independent review."""
    try:
        variant = _load_json(path)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"{path}: cannot read JSON: {exc}"]
    if not isinstance(variant, dict):
        return [f"{path}: variant must be an object"]
    errors: list[str] = []
    for field in ("variant_id", "representation_of"):
        if not absolute_iri(variant.get(field)):
            errors.append(f"variant.{field}: absolute immutable IRI required")
    for field in ("format", "generator", "generated_at"):
        if not isinstance(variant.get(field), str) or not variant[field].strip():
            errors.append(f"variant.{field}: nonempty string required")
    for field in ("source_manifest_sha256", "output_sha256"):
        value = variant.get(field)
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
            errors.append(f"variant.{field}: SHA-256 hex required")
    if not isinstance(variant.get("lossless"), bool):
        errors.append("variant.lossless: boolean required")
    for field in ("omissions", "unsupported_constructs"):
        if not isinstance(variant.get(field), list):
            errors.append(f"variant.{field}: explicit array required")
    if variant.get("lossless") and variant.get("unsupported_constructs"):
        errors.append("variant: lossless claim conflicts with unsupported constructs")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, nargs="?")
    parser.add_argument("--variant", type=Path, help="validate detached variant metadata only")
    args = parser.parse_args(argv)
    if bool(args.manifest) == bool(args.variant):
        parser.error("provide exactly one manifest or --variant")
    errors = validate_variant(args.variant) if args.variant else validate(args.manifest)
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        print(f"{len(errors)} validation error(s)", file=sys.stderr)
        return 1
    print("SEAG 0.1 draft source valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
