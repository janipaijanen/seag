# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Deterministic semantic diff and bounded three-way conflict detection."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from .source import load_bundle, package_version
from .transform import json_bytes


DIFF_SCHEMA = "seag/semantic-diff/0.2-draft.1"
CONFLICT_SCHEMA = "seag/semantic-conflict/0.2-draft.1"
MISSING = object()

# Code, category, default severity, human description. The first matching field
# wins. Unknown future fields remain visible through SD299 rather than being
# silently ignored.
FIELD_RULES: dict[str, tuple[str, str, str, str]] = {
    "kind": ("SD200", "identity", "breaking", "record kind changed"),
    "label": ("SD210", "definition", "review", "preferred label changed"),
    "definition": ("SD211", "definition", "review", "definition changed"),
    "status": ("SD220", "status", "review", "semantic status changed"),
    "implementation_alignment": ("SD221", "status", "review", "implementation alignment changed"),
    "provenance": ("SD230", "provenance", "review", "provenance changed"),
    "confirmation": ("SD231", "confirmation", "review", "confirmation evidence changed"),
    "replacement_or_reason": ("SD232", "status", "review", "replacement or rationale changed"),
    "predicate": ("SD240", "relationship", "breaking", "relationship predicate changed"),
    "source": ("SD241", "relationship", "breaking", "relationship source changed"),
    "target": ("SD242", "relationship", "breaking", "relationship target changed"),
    "name": ("SD243", "relationship", "review", "association name changed"),
    "source_cardinality": ("SD250", "cardinality", "breaking", "source cardinality changed"),
    "target_cardinality": ("SD251", "cardinality", "breaking", "target cardinality changed"),
    "iri": ("SD260", "external-reference", "breaking", "external IRI changed"),
    "language": ("SD261", "language", "review", "record language changed"),
    "grammatical_number": ("SD270", "definition", "breaking", "grammatical-number declaration changed"),
}

BUNDLE_RULES: dict[str, tuple[str, str, str, str]] = {
    "seag_schema": ("SD001", "contract", "breaking", "source contract changed"),
    "bundle_id": ("SD002", "identity", "breaking", "bundle identity changed"),
    "namespace": ("SD003", "identity", "breaking", "namespace changed"),
    "title": ("SD010", "metadata", "informational", "bundle title changed"),
    "default_language": ("SD011", "language", "review", "default language changed"),
    "status": ("SD012", "status", "review", "bundle status changed"),
    "licence": ("SD013", "licensing", "breaking", "bundle licence changed"),
}


def implementation_digest() -> str:
    """Identify the exact local code that defines comparison behavior."""
    package = Path(__file__).resolve().parent
    inputs = [package / name for name in ("semantic_diff.py", "source.py", "transform.py", "validate.py")]
    inputs.append(package.parent / "VERSION")
    digest = hashlib.sha256()
    for path in sorted(inputs, key=lambda item: item.name):
        digest.update(path.name.encode("utf-8") + b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _snapshot(path: Path) -> dict[str, Any]:
    manifest, located_records, digest = load_bundle(path)
    namespace = manifest["namespace"]
    # Language is inherited from the containing fragment and therefore belongs
    # in the semantic comparison even though it is not a record JSON field.
    records = {
        namespace + record["id"]: {"language": fragment["language"], **record}
        for fragment, record in located_records
    }
    return {"manifest": manifest, "manifest_sha256": digest, "records": records}


def _source(snapshot: dict[str, Any], role: str) -> dict[str, str]:
    manifest = snapshot["manifest"]
    return {
        "role": role,
        "bundle_id": manifest["bundle_id"],
        "namespace": manifest["namespace"],
        "seag_schema": manifest["seag_schema"],
        "manifest_sha256": snapshot["manifest_sha256"],
    }


def _value(value: object) -> object:
    return None if value is MISSING else value


def _change(
    code: str,
    category: str,
    severity: str,
    description: str,
    *,
    record_id: str | None,
    field: str,
    before: object,
    after: object,
) -> dict[str, object]:
    return {
        "code": code,
        "category": category,
        "severity": severity,
        "description": description,
        "record_id": record_id,
        "field": field,
        "before": _value(before),
        "after": _value(after),
    }


def _status_severity(before: object, after: object) -> str:
    if before == "confirmed" and after != "confirmed":
        return "breaking"
    if before == "deprecated" and after != "deprecated":
        return "breaking"
    return "review"


def _sort_key(change: dict[str, object]) -> tuple[str, str, str]:
    return (str(change.get("record_id") or ""), str(change["code"]), str(change["field"]))


def _summary(changes: list[dict[str, object]]) -> dict[str, object]:
    severities = Counter(str(change["severity"]) for change in changes)
    categories = Counter(str(change["category"]) for change in changes)
    return {
        "total": len(changes),
        "by_severity": {key: severities[key] for key in sorted(severities)},
        "by_category": {key: categories[key] for key in sorted(categories)},
    }


def _compare_snapshots(before: dict[str, Any], after: dict[str, Any]) -> list[dict[str, object]]:
    changes: list[dict[str, object]] = []
    before_manifest, after_manifest = before["manifest"], after["manifest"]
    for field, (code, category, severity, description) in BUNDLE_RULES.items():
        old, new = before_manifest.get(field, MISSING), after_manifest.get(field, MISSING)
        if old != new:
            changes.append(
                _change(
                    code,
                    category,
                    severity,
                    description,
                    record_id=None,
                    field=f"manifest.{field}",
                    before=old,
                    after=new,
                )
            )

    before_records, after_records = before["records"], after["records"]
    for record_id in sorted(set(before_records) | set(after_records)):
        old, new = before_records.get(record_id), after_records.get(record_id)
        if old is None:
            changes.append(
                _change(
                    "SD100",
                    "inventory",
                    "informational",
                    "record added",
                    record_id=record_id,
                    field="record",
                    before=MISSING,
                    after=new,
                )
            )
            continue
        if new is None:
            changes.append(
                _change(
                    "SD101",
                    "inventory",
                    "breaking",
                    "record removed",
                    record_id=record_id,
                    field="record",
                    before=old,
                    after=MISSING,
                )
            )
            continue
        for field in sorted(set(old) | set(new)):
            if field == "id":
                continue
            old_value, new_value = old.get(field, MISSING), new.get(field, MISSING)
            if old_value == new_value:
                continue
            code, category, severity, description = FIELD_RULES.get(
                field,
                ("SD299", "record", "review", "record field changed"),
            )
            if field == "status":
                severity = _status_severity(old_value, new_value)
            changes.append(
                _change(
                    code,
                    category,
                    severity,
                    description,
                    record_id=record_id,
                    field=field,
                    before=old_value,
                    after=new_value,
                )
            )
    return sorted(changes, key=_sort_key)


def compare(before_path: Path, after_path: Path) -> dict[str, object]:
    """Compare two valid bundles without relying on filenames or Git state."""
    before, after = _snapshot(before_path), _snapshot(after_path)
    changes = _compare_snapshots(before, after)
    return {
        "schema": DIFF_SCHEMA,
        "generator": f"seag/{package_version()}",
        "implementation_sha256": implementation_digest(),
        "operation": "two-way",
        "sources": [_source(before, "before"), _source(after, "after")],
        "summary": _summary(changes),
        "changes": changes,
    }


def _flatten(value: dict[str, object], prefix: tuple[str, ...] = ()) -> dict[tuple[str, ...], object]:
    leaves: dict[tuple[str, ...], object] = {}
    for key in sorted(value):
        child = value[key]
        path = prefix + (key,)
        if isinstance(child, dict):
            leaves.update(_flatten(child, path))
        else:
            leaves[path] = child
    return leaves


def _conflict(
    code: str,
    description: str,
    record_id: str | None,
    field: str,
    base: object,
    ours: object,
    theirs: object,
) -> dict[str, object]:
    return {
        "code": code,
        "severity": "conflict",
        "description": description,
        "record_id": record_id,
        "field": field,
        "base": _value(base),
        "ours": _value(ours),
        "theirs": _value(theirs),
    }


def _record_conflicts(
    base_records: dict[str, dict[str, object]],
    ours_records: dict[str, dict[str, object]],
    theirs_records: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    conflicts: list[dict[str, object]] = []
    for record_id in sorted(set(base_records) | set(ours_records) | set(theirs_records)):
        base = base_records.get(record_id)
        ours = ours_records.get(record_id)
        theirs = theirs_records.get(record_id)
        if base is None:
            if ours is not None and theirs is not None and ours != theirs:
                conflicts.append(
                    _conflict("SC102", "same identity added differently", record_id, "record", MISSING, ours, theirs)
                )
            continue
        if ours is None and theirs is not None and theirs != base:
            conflicts.append(
                _conflict("SC101", "record deleted on ours and modified on theirs", record_id, "record", base, MISSING, theirs)
            )
            continue
        if theirs is None and ours is not None and ours != base:
            conflicts.append(
                _conflict("SC101", "record modified on ours and deleted on theirs", record_id, "record", base, ours, MISSING)
            )
            continue
        if ours is None or theirs is None:
            continue
        base_fields, ours_fields, theirs_fields = _flatten(base), _flatten(ours), _flatten(theirs)
        paths = set(base_fields) | set(ours_fields) | set(theirs_fields)
        ours_changed = {path[0] for path in paths if ours_fields.get(path, MISSING) != base_fields.get(path, MISSING)}
        theirs_changed = {path[0] for path in paths if theirs_fields.get(path, MISSING) != base_fields.get(path, MISSING)}
        structural = {"kind", "predicate", "source", "target"}
        evidence_scope = {"status", "provenance", "confirmation", "replacement_or_reason"}
        if ours != theirs and ours_changed and theirs_changed and (
            ours_changed & structural or theirs_changed & structural
        ):
            conflicts.append(
                _conflict(
                    "SC103",
                    "structural semantic change overlaps another branch change",
                    record_id,
                    "record",
                    base,
                    ours,
                    theirs,
                )
            )
            continue
        if ours != theirs and ours_changed and theirs_changed and (
            ours_changed & evidence_scope or theirs_changed & evidence_scope
        ):
            conflicts.append(
                _conflict(
                    "SC104",
                    "status or evidence change overlaps another branch change",
                    record_id,
                    "record",
                    base,
                    ours,
                    theirs,
                )
            )
            continue
        for path in sorted(paths):
            old = base_fields.get(path, MISSING)
            our_value = ours_fields.get(path, MISSING)
            their_value = theirs_fields.get(path, MISSING)
            if our_value != old and their_value != old and our_value != their_value:
                conflicts.append(
                    _conflict(
                        "SC100",
                        "both branches changed the semantic field differently",
                        record_id,
                        ".".join(path),
                        old,
                        our_value,
                        their_value,
                    )
                )
    return conflicts


def three_way(base_path: Path, ours_path: Path, theirs_path: Path) -> dict[str, object]:
    """Detect bounded conflicts between two valid descendants of a valid base."""
    base, ours, theirs = _snapshot(base_path), _snapshot(ours_path), _snapshot(theirs_path)
    conflicts: list[dict[str, object]] = []
    for field in BUNDLE_RULES:
        old = base["manifest"].get(field, MISSING)
        our_value = ours["manifest"].get(field, MISSING)
        their_value = theirs["manifest"].get(field, MISSING)
        identity_field = field in {"bundle_id", "namespace"}
        divergent_change = our_value != old and their_value != old and our_value != their_value
        if identity_field and (our_value != old or their_value != old):
            conflicts.append(
                _conflict(
                    "SC001",
                    "three-way inputs do not retain the base semantic identity",
                    None,
                    f"manifest.{field}",
                    old,
                    our_value,
                    their_value,
                )
            )
        elif divergent_change:
            conflicts.append(
                _conflict(
                    "SC100",
                    "both branches changed the bundle field differently",
                    None,
                    f"manifest.{field}",
                    old,
                    our_value,
                    their_value,
                )
            )
    conflicts.extend(_record_conflicts(base["records"], ours["records"], theirs["records"]))
    conflicts.sort(key=lambda item: (str(item.get("record_id") or ""), str(item["code"]), str(item["field"])))
    ours_changes = _compare_snapshots(base, ours)
    theirs_changes = _compare_snapshots(base, theirs)
    return {
        "schema": CONFLICT_SCHEMA,
        "generator": f"seag/{package_version()}",
        "implementation_sha256": implementation_digest(),
        "operation": "three-way",
        "sources": [_source(base, "base"), _source(ours, "ours"), _source(theirs, "theirs")],
        "summary": {
            "ours_changes": len(ours_changes),
            "theirs_changes": len(theirs_changes),
            "conflicts": len(conflicts),
        },
        "ours_changes": ours_changes,
        "theirs_changes": theirs_changes,
        "conflicts": conflicts,
    }


def format_human(result: dict[str, object]) -> str:
    """Render a concise terminal-safe report from a semantic review result."""
    if result["operation"] == "two-way":
        changes = result["changes"]
        if not changes:
            return "No semantic changes."
        lines = []
        for item in changes:
            subject = json.dumps(item["record_id"], ensure_ascii=True) if item["record_id"] else "bundle"
            lines.append(
                f"{str(item['severity']).upper()} {item['code']} {subject} {item['field']}: {item['description']}"
            )
        return "\n".join(lines)
    conflicts = result["conflicts"]
    if not conflicts:
        return (
            "No bounded semantic conflicts. "
            f"Ours: {result['summary']['ours_changes']} change(s); "
            f"theirs: {result['summary']['theirs_changes']} change(s)."
        )
    return "\n".join(
        f"CONFLICT {item['code']} "
        f"{json.dumps(item['record_id'], ensure_ascii=True) if item['record_id'] else 'bundle'} "
        f"{item['field']}: {item['description']}"
        for item in conflicts
    )


def _should_fail(result: dict[str, object], policy: str) -> bool:
    if policy == "never":
        return False
    if result["operation"] == "three-way":
        if policy == "conflict":
            return bool(result["conflicts"])
        changes = list(result["ours_changes"]) + list(result["theirs_changes"])
    else:
        if policy == "conflict":
            return False
        changes = result["changes"]
    if policy == "change":
        return bool(changes)
    return policy == "breaking" and any(item["severity"] == "breaking" for item in changes)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifests", type=Path, nargs="*", metavar="MANIFEST")
    parser.add_argument("--base", type=Path)
    parser.add_argument("--ours", type=Path)
    parser.add_argument("--theirs", type=Path)
    parser.add_argument("--format", choices=("human", "json"), default="human")
    parser.add_argument("--fail-on", choices=("never", "change", "breaking", "conflict"))
    args = parser.parse_args(argv)
    three_paths = (args.base, args.ours, args.theirs)
    if any(three_paths):
        if args.manifests or not all(three_paths):
            parser.error("three-way mode requires --base, --ours, and --theirs together")
        mode = "three-way"
    elif len(args.manifests) == 2:
        mode = "two-way"
    else:
        parser.error("provide BEFORE AFTER, or --base BASE --ours OURS --theirs THEIRS")
    if mode == "two-way" and args.fail_on == "conflict":
        parser.error("--fail-on conflict requires three-way mode")
    try:
        result = (
            three_way(args.base, args.ours, args.theirs)
            if mode == "three-way"
            else compare(args.manifests[0], args.manifests[1])
        )
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2
    if args.format == "json":
        sys.stdout.buffer.write(json_bytes(result))
    else:
        print(format_human(result))
    policy = args.fail_on or ("conflict" if mode == "three-way" else "never")
    return 1 if _should_fail(result, policy) else 0


if __name__ == "__main__":
    raise SystemExit(main())
