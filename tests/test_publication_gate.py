# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("publication_gate", ROOT / "scripts" / "check-publication-gate.py")
GATE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GATE)


class ReleaseEvidenceTest(unittest.TestCase):
    def evidence(self):
        head = subprocess.check_output(("git", "rev-parse", "HEAD"), cwd=ROOT, text=True).strip()
        return {
            "schema": "seag/release-review-evidence/v1",
            "release": "0.1.0",
            "candidate_commit": head,
            "reviews": [
                {"scope": scope, "reviewer": "reviewer-a" if index < 2 else "reviewer-b", "verdict": "approved", "reviewed_commit": head, "reviewed_at": "2026-11-22T00:00:00Z", "evidence_ref": f"review:{scope}"}
                for index, scope in enumerate(sorted(GATE.REVIEW_SCOPES))
            ],
        }

    def check(self, evidence):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            path.write_text(json.dumps(evidence))
            previous = Path.cwd()
            try:
                __import__("os").chdir(ROOT)
                return GATE.check_review_evidence(path)
            finally:
                __import__("os").chdir(previous)

    def check_raw(self, raw):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            path.write_text(raw)
            return GATE.check_review_evidence(path)

    def test_accepts_complete_exact_candidate_evidence(self):
        self.assertEqual([], self.check(self.evidence()))

    def test_rejects_missing_scope_and_single_reviewer(self):
        evidence = self.evidence()
        evidence["reviews"] = evidence["reviews"][:3]
        for review in evidence["reviews"]:
            review["reviewer"] = "one-reviewer"
        errors = self.check(evidence)
        self.assertTrue(any("scopes incomplete" in error for error in errors), errors)
        self.assertTrue(any("two distinct" in error for error in errors), errors)

    def test_rejects_malformed_review_provenance(self):
        evidence = self.evidence()
        evidence["reviews"][0]["reviewed_at"] = "not-a-date"
        evidence["reviews"][0]["evidence_ref"] = "https:%ZZ"
        errors = self.check(evidence)
        self.assertTrue(any("RFC 3339 UTC" in error for error in errors), errors)
        self.assertTrue(any("valid absolute URI" in error for error in errors), errors)

    def test_rejects_duplicate_unknown_and_wrong_top_level_content(self):
        errors = self.check_raw('{"schema":"first","schema":"second"}')
        self.assertTrue(any("duplicate JSON object member" in error for error in errors), errors)
        evidence = self.evidence()
        evidence["unexpected"] = True
        errors = self.check(evidence)
        self.assertTrue(any("unsupported fields" in error for error in errors), errors)
        self.assertEqual(["release review evidence must be an object"], self.check_raw("[]"))


if __name__ == "__main__":
    unittest.main()
