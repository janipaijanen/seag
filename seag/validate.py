# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Dependency-free validator for the bounded SEAG 0.1 draft source contract."""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import sys
import unicodedata
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
MANIFEST_FIELDS = {"seag_schema", "bundle_id", "namespace", "title", "default_language", "status", "licence", "fragments"}
INVENTORY_FIELDS = {"fragment_id", "path", "role", "sha256"}
FRAGMENT_FIELDS = {"seag_schema", "bundle_id", "namespace", "fragment_id", "role", "language", "revision", "records"}
COMMON_FIELDS = {"id", "kind", "status", "implementation_alignment", "provenance", "confirmation", "replacement_or_reason"}
RECORD_FIELDS = {
    "concept": COMMON_FIELDS | {"label", "definition"},
    "lifecycle_state": COMMON_FIELDS | {"label", "definition"},
    "rule_reference": COMMON_FIELDS | {"label", "definition", "iri"},
    "external_reference": COMMON_FIELDS | {"label", "definition", "iri"},
    "proposition": COMMON_FIELDS | {"source", "target", "predicate", "name", "definition", "source_cardinality", "target_cardinality"},
}
PROVENANCE_FIELDS = {"source", "locator", "proposer", "normative", "verification_status"}
CONFIRMATION_FIELDS = {"decision_ref", "decided_at", "confirmer", "reviewer", "review_ref", "reviewed_at", "role_collapse_note", "review_limit"}
VARIANT_FIELDS = {"variant_id", "representation_of", "format", "source_manifest_sha256", "output_sha256", "generator", "generated_at", "lossless", "omissions", "unsupported_constructs"}
# Only initial transition/action phrases are rejected automatically. Ambiguous
# interior words and static names require human semantic review.
PROCESS_NAME = re.compile(r"^(?:precedes?|preceded by|preceding|is followed by|trigger(?:s|ed|ing)?(?: by)?|transition(?:s|ed|ing)? to|chang(?:e|es|ed|ing) state(?: to)?|next state|leads? to|results? in|is succeeded by|becomes?|is caused by|caused by|causes?)(?:\b|$)")
VAGUE_NAMES = {"relates to", "relates to the", "related to", "is related to", "associated with", "is associated with", "linked to", "is linked to", "connection", "relation", "supports", "uses", "has many"}
EVIDENCE_STATUS = {"unresolved", "qualified", "verified", "rejected"}


def normalized_actor(value: object) -> str:
    return unicodedata.normalize("NFKC", value).strip().casefold() if isinstance(value, str) else ""


def normalized_name(value: str) -> str:
    # Fold separators, case and compatibility forms; hidden format characters are rejected separately.
    folded = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(re.sub(r"[_\-\W]+", " ", folded, flags=re.UNICODE).split())


def iso_date(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return datetime.date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def iso_timestamp(value: object) -> bool:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})", value):
        return False
    try:
        return datetime.datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is not None
    except ValueError:
        return False


def absolute_iri(value: object) -> bool:
    if not isinstance(value, str) or not value or any(c.isspace() or unicodedata.category(c) == "Cc" for c in value):
        return False
    parts = urlsplit(value)
    if parts.scheme in {"http", "https"}:
        return bool(parts.netloc)
    return bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9+.-]*", parts.scheme)) and bool(value.split(":", 1)[1])


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
    check(not (set(manifest) - MANIFEST_FIELDS), "manifest", "unsupported fields: " + ", ".join(sorted(set(manifest) - MANIFEST_FIELDS)))
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
        check(not (set(item) - INVENTORY_FIELDS), where, "unsupported fields: " + ", ".join(sorted(set(item) - INVENTORY_FIELDS)))
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
        check(not (set(fragment) - FRAGMENT_FIELDS), name, "unsupported fields: " + ", ".join(sorted(set(fragment) - FRAGMENT_FIELDS)))
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
            if isinstance(kind, str) and kind in KINDS:
                extras = sorted(set(record) - RECORD_FIELDS[kind])
                check(not extras, loc, "unsupported record fields: " + ", ".join(extras))
            if isinstance(ident, str):
                check(ident not in records, loc + ".id", "duplicate expanded record ID")
                if ident not in records:
                    records[ident] = record
            check(isinstance(record.get("status"), str) and record["status"] in STATUS, loc + ".status", "invalid semantic status")
            check(isinstance(record.get("implementation_alignment"), str) and record["implementation_alignment"] in ALIGNMENT, loc + ".implementation_alignment", "separate alignment status required")
            provenance = record.get("provenance")
            check(isinstance(provenance, dict) and all(isinstance(provenance.get(k), str) and provenance[k].strip() for k in ("source", "locator", "proposer")) and isinstance(provenance.get("normative"), bool) and isinstance(provenance.get("verification_status"), str) and provenance["verification_status"] in EVIDENCE_STATUS, loc + ".provenance", "source, locator, proposer, normative boolean, and evidence verification status required")
            if isinstance(provenance, dict):
                check(not (set(provenance) - PROVENANCE_FIELDS), loc + ".provenance", "unsupported fields: " + ", ".join(sorted(set(provenance) - PROVENANCE_FIELDS)))
            confirmation = record.get("confirmation")
            if "confirmation" in record:
                check(isinstance(confirmation, dict) and all(isinstance(confirmation.get(k), str) and confirmation[k].strip() for k in ("decision_ref", "decided_at", "confirmer", "reviewer", "review_ref", "reviewed_at")), loc + ".confirmation", "confirmed record needs separate decision and review references, dates, confirmer, and reviewer")
                if isinstance(confirmation, dict):
                    check(not (set(confirmation) - CONFIRMATION_FIELDS), loc + ".confirmation", "unsupported fields: " + ", ".join(sorted(set(confirmation) - CONFIRMATION_FIELDS)))
                    check(iso_date(confirmation.get("decided_at")), loc + ".confirmation.decided_at", "ISO calendar date required")
                    check(iso_date(confirmation.get("reviewed_at")), loc + ".confirmation.reviewed_at", "ISO calendar date required")
                    if iso_date(confirmation.get("decided_at")) and iso_date(confirmation.get("reviewed_at")):
                        check(confirmation["reviewed_at"] <= confirmation["decided_at"], loc + ".confirmation.reviewed_at", "review date must not follow decision date")
                    if normalized_actor(confirmation.get("reviewer")) == normalized_actor(confirmation.get("confirmer")) and not (isinstance(provenance, dict) and normalized_actor(confirmation.get("reviewer")) == normalized_actor(provenance.get("proposer"))):
                        check(isinstance(confirmation.get("review_limit"), str) and bool(confirmation["review_limit"].strip()), loc + ".confirmation.review_limit", "same declared reviewer and confirmer needs review-limit disclosure")
                if isinstance(confirmation, dict) and isinstance(provenance, dict):
                    if normalized_actor(confirmation.get("confirmer")) == normalized_actor(provenance.get("proposer")):
                        check(isinstance(confirmation.get("role_collapse_note"), str) and bool(confirmation["role_collapse_note"].strip()), loc + ".confirmation.role_collapse_note", "same declared actor needs role-collapse disclosure")
                    if normalized_actor(confirmation.get("reviewer")) == normalized_actor(provenance.get("proposer")):
                        check(isinstance(confirmation.get("review_limit"), str) and bool(confirmation["review_limit"].strip()), loc + ".confirmation.review_limit", "self-review must be disclosed, not called independent")
            if record.get("status") == "confirmed":
                check(isinstance(confirmation, dict), loc + ".confirmation", "confirmed record needs separate decision and review references, dates, confirmer, and reviewer")
                check(isinstance(provenance, dict) and provenance.get("verification_status") in {"qualified", "verified"}, loc + ".provenance.verification_status", "confirmed record needs qualified or verified source evidence")
            if record.get("status") == "deprecated":
                check(isinstance(record.get("replacement_or_reason"), str) and bool(record["replacement_or_reason"].strip()), loc + ".replacement_or_reason", "deprecated record needs replacement or rationale")
            if kind == "proposition":
                propositions.append((loc, record))
            elif isinstance(kind, str) and kind in KINDS:
                for field in ("label", "definition"):
                    check(isinstance(record.get(field), str) and bool(record[field].strip()), loc + "." + field, "nonempty string required")
                if kind in {"external_reference", "rule_reference"}:
                    check(absolute_iri(record.get("iri")), loc + ".iri", "absolute external artifact IRI required")

    taxonomy: dict[str, list[str]] = {}
    for loc, record in propositions:
        predicate = record.get("predicate")
        check(isinstance(predicate, str) and predicate in ENDPOINTS, loc + ".predicate", "one of six static controlled predicates required")
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
                normalized = normalized_name(name)
                check(not any(unicodedata.category(c) == "Cf" for c in name), loc + ".name", "hidden format characters forbidden")
                check(not PROCESS_NAME.search(normalized), loc + ".name", "process or transition association name forbidden")
                check(normalized not in VAGUE_NAMES, loc + ".name", "vague association name; use a bounded static semantic relation")
            check(isinstance(record.get("definition"), str) and bool(record["definition"].strip()), loc + ".definition", "bounded static association definition required")
            for end in ("source_cardinality", "target_cardinality"):
                check(isinstance(record.get(end), str) and record[end] in CARDINALITY, loc + "." + end, "explicit both-end cardinality required")
                if record.get("status") == "confirmed":
                    check(record.get(end) != "unresolved", loc + "." + end, "confirmed cardinality cannot be unresolved")
        elif isinstance(predicate, str) and predicate in ENDPOINTS:
            extra = sorted(set(record) & {"name", "definition", "source_cardinality", "target_cardinality"})
            check(not extra, loc, "named-association fields unsupported for controlled predicate: " + ", ".join(extra))

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
    extras = sorted(set(variant) - VARIANT_FIELDS)
    if extras:
        errors.append("variant: unsupported fields: " + ", ".join(extras))
    for field in ("variant_id", "representation_of"):
        if not absolute_iri(variant.get(field)):
            errors.append(f"variant.{field}: absolute immutable IRI required")
    for field in ("format", "generator", "generated_at"):
        if not isinstance(variant.get(field), str) or not variant[field].strip():
            errors.append(f"variant.{field}: nonempty string required")
    if isinstance(variant.get("generated_at"), str) and variant["generated_at"].strip() and not iso_timestamp(variant["generated_at"]):
        errors.append("variant.generated_at: ISO timestamp with timezone required")
    for field in ("source_manifest_sha256", "output_sha256"):
        value = variant.get(field)
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
            errors.append(f"variant.{field}: SHA-256 hex required")
    if not isinstance(variant.get("lossless"), bool):
        errors.append("variant.lossless: boolean required")
    for field in ("omissions", "unsupported_constructs"):
        value = variant.get(field)
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            errors.append(f"variant.{field}: explicit string array required")
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
    print("SEAG 0.1 draft source shape valid; actor identities and authority unverified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
