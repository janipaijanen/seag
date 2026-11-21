#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Fail closed until the SEAG public-release prerequisites are present."""

from pathlib import Path
import datetime
import json
import re
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from seag.cxl import export, parse
from seag.glossary import extract
from seag.transform import json_bytes


REQUIRED_FILES = (
    "LICENSES/Apache-2.0.txt",
    "LICENSES/CC-BY-4.0.txt",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "docs/dco-historical-attestation.md",
    "docs/cxl-profile.md",
    "docs/glossary-extraction.md",
    "docs/semantic-mappings.md",
    "docs/installation-and-upgrade.md",
    "docs/release-policy.md",
    "docs/reviews/0.1.0-release.json",
    "docs/reviews/0.1.0-release.json.license",
)

REVIEW_SCOPES = {"semantic", "framework-boundary", "licensing", "security"}
RFC3339_UTC = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z\Z")
ABSOLUTE_EVIDENCE_REF = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*:[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+\Z")
INVALID_PERCENT_ESCAPE = re.compile(r"%(?![0-9A-Fa-f]{2})")


def valid_reviewed_at(value: object) -> bool:
    if not isinstance(value, str) or not RFC3339_UTC.fullmatch(value):
        return False
    try:
        return datetime.datetime.fromisoformat(value.removesuffix("Z") + "+00:00").tzinfo is not None
    except ValueError:
        return False


def valid_evidence_ref(value: object) -> bool:
    if not isinstance(value, str) or not ABSOLUTE_EVIDENCE_REF.fullmatch(value):
        return False
    if INVALID_PERCENT_ESCAPE.search(value):
        return False
    try:
        parts = urlsplit(value)
        _ = parts.port
    except ValueError:
        return False
    if parts.scheme in {"http", "https"}:
        return bool(parts.netloc)
    return bool(value.split(":", 1)[1])


def check_review_evidence(path: Path) -> list[str]:
    try:
        evidence = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        return [f"cannot read release review evidence: {error}"]
    errors = []
    if evidence.get("schema") != "seag/release-review-evidence/v1":
        errors.append("unexpected review evidence schema")
    if evidence.get("release") != "0.1.0":
        errors.append("review evidence release must be 0.1.0")
    candidate = evidence.get("candidate_commit")
    if not isinstance(candidate, str) or not re.fullmatch(r"[0-9a-f]{40}", candidate):
        errors.append("candidate_commit must be a full Git SHA")
        return errors
    ancestry = subprocess.run(("git", "merge-base", "--is-ancestor", candidate, "HEAD"), check=False)
    if ancestry.returncode:
        errors.append("reviewed candidate is unavailable or not an ancestor of HEAD")
    else:
        changed = subprocess.check_output(("git", "diff", "--name-only", f"{candidate}..HEAD"), text=True).splitlines()
        allowed = {"docs/reviews/0.1.0-release.json", "docs/reviews/0.1.0-release.json.license"}
        unexpected = sorted(set(changed) - allowed)
        if unexpected:
            errors.append("unreviewed post-candidate paths: " + ", ".join(unexpected))
    reviews = evidence.get("reviews")
    if not isinstance(reviews, list):
        return errors + ["reviews must be an array"]
    covered = set()
    reviewers = set()
    for index, review in enumerate(reviews):
        if not isinstance(review, dict):
            errors.append(f"review {index} must be an object")
            continue
        scope = review.get("scope")
        if scope not in REVIEW_SCOPES:
            errors.append(f"review {index} has an invalid scope")
        else:
            covered.add(scope)
        if review.get("verdict") != "approved":
            errors.append(f"review {index} is not approved")
        if review.get("reviewed_commit") != candidate:
            errors.append(f"review {index} does not target candidate_commit")
        for field in ("reviewer", "evidence_ref", "reviewed_at"):
            if not isinstance(review.get(field), str) or not review[field].strip():
                errors.append(f"review {index} needs {field}")
        if "reviewed_at" in review and not valid_reviewed_at(review["reviewed_at"]):
            errors.append(f"review {index} reviewed_at must be an RFC 3339 UTC timestamp")
        if "evidence_ref" in review and (
            not valid_evidence_ref(review["evidence_ref"])
        ):
            errors.append(f"review {index} evidence_ref must be a syntactically valid absolute URI")
        if isinstance(review.get("reviewer"), str) and review["reviewer"].strip():
            reviewers.add(review["reviewer"].strip().casefold())
    if covered != REVIEW_SCOPES:
        errors.append("review scopes incomplete: " + ", ".join(sorted(REVIEW_SCOPES - covered)))
    if len(reviewers) < 2:
        errors.append("at least two distinct reviewers are required")
    return errors


def main() -> int:
    if Path("VERSION").read_text().strip() != "0.1.0":
        print("publication gate: CLOSED: VERSION is not stable 0.1.0", file=sys.stderr)
        return 1
    missing = [path for path in REQUIRED_FILES if not Path(path).is_file()]
    if missing:
        print("publication gate: CLOSED", file=sys.stderr)
        for path in missing:
            print(f"missing required file: {path}", file=sys.stderr)
        return 1
    review_errors = check_review_evidence(Path("docs/reviews/0.1.0-release.json"))
    if review_errors:
        print("publication gate: CLOSED: invalid release review evidence", file=sys.stderr)
        for error in review_errors:
            print(error, file=sys.stderr)
        return 1

    dco = subprocess.run(
        (sys.executable, "scripts/check-dco.py"), check=False
    )
    if dco.returncode:
        print("publication gate: CLOSED: DCO check failed", file=sys.stderr)
        return 1
    fixed_time = "2026-11-22T00:00:00Z"
    manifest = Path("fixtures/valid/manifest.json")
    with tempfile.TemporaryDirectory() as directory:
        temporary = Path(directory)
        glossary, glossary_provenance = extract(manifest, "en", fixed_time)
        glossary_data = json_bytes(glossary)
        glossary_provenance["output_sha256"] = __import__("hashlib").sha256(glossary_data).hexdigest()
        generated = {
            "glossary-en.json": glossary_data,
            "glossary-en.json.provenance.json": json_bytes(glossary_provenance),
        }
        cxl_data, cxl_provenance, expected = export(manifest, fixed_time)
        cxl_path = temporary / "concept-map.cxl"
        cxl_path.write_bytes(cxl_data)
        if parse(cxl_path) != expected:
            print("publication gate: CLOSED: CXL round trip changed the graph", file=sys.stderr)
            return 1
        generated["concept-map.cxl"] = cxl_data
        generated["concept-map.cxl.provenance.json"] = json_bytes(cxl_provenance)
        for name, content in generated.items():
            expected_path = Path("fixtures/expected") / name
            if not expected_path.is_file() or expected_path.read_bytes() != content:
                print(f"publication gate: CLOSED: stale expected transform: {name}", file=sys.stderr)
                return 1
    print("publication gate file prerequisites: present")
    print("independent review evidence still requires a release-specific CI check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

