# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Deterministic semantic review and bounded conflict tests."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from seag.semantic_diff import compare, format_human, three_way
from seag.transform import json_bytes


ROOT = Path(__file__).resolve().parents[1]
VALID = ROOT / "fixtures" / "valid"
SEMANTIC_DIFF = ROOT / "fixtures" / "semantic-diff"


class SemanticDiffTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = json.loads((VALID / "manifest.json").read_text())
        self.fragment = json.loads((VALID / "fragment.json").read_text())

    def bundle(self, name, mutate=None):
        directory = self.root / name
        directory.mkdir()
        manifest = copy.deepcopy(self.manifest)
        fragment = copy.deepcopy(self.fragment)
        if mutate:
            mutate(manifest, fragment)
        fragment_data = json_bytes(fragment)
        manifest["fragments"][0]["sha256"] = hashlib.sha256(fragment_data).hexdigest()
        (directory / "fragment.json").write_bytes(fragment_data)
        (directory / "manifest.json").write_bytes(json_bytes(manifest))
        return directory / "manifest.json"

    def test_identical_bundles_have_no_semantic_changes(self):
        before = self.bundle("before")
        after = self.bundle("after")
        result = compare(before, after)
        self.assertEqual("seag/semantic-diff/0.2-draft.1", result["schema"])
        self.assertRegex(result["implementation_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(0, result["summary"]["total"])
        self.assertEqual([], result["changes"])
        self.assertNotIn(str(self.root), json.dumps(result))

    def test_retained_before_after_fixture(self):
        result = compare(
            SEMANTIC_DIFF / "before" / "manifest.json",
            SEMANTIC_DIFF / "after" / "manifest.json",
        )
        self.assertEqual(2, result["summary"]["total"])
        self.assertEqual(["SD251", "SD211"], [item["code"] for item in result["changes"]])
        self.assertEqual(
            ["breaking", "review"],
            [item["severity"] for item in result["changes"]],
        )

    def test_change_taxonomy_and_order_are_stable(self):
        before = self.bundle("before")

        def mutate(manifest, fragment):
            manifest["title"] = "Renamed invented fixture"
            fragment["records"][0]["definition"] = "A revised invented thing."
            fragment["records"][-1]["target_cardinality"] = "1..*"

        after = self.bundle("after", mutate)
        first = compare(before, after)
        second = compare(before, after)
        self.assertEqual(json_bytes(first), json_bytes(second))
        self.assertEqual(["SD010", "SD251", "SD211"], [item["code"] for item in first["changes"]])
        self.assertEqual({"breaking": 1, "informational": 1, "review": 1}, first["summary"]["by_severity"])

    def test_removed_record_and_confirmed_downgrade_are_breaking(self):
        before = self.bundle("before", lambda _manifest, fragment: self.confirm(fragment["records"][0]))

        def mutate(_manifest, fragment):
            self.confirm(fragment["records"][0])
            fragment["records"][0]["status"] = "unresolved"
            del fragment["records"][0]["confirmation"]
            fragment["records"] = [record for record in fragment["records"] if record["id"] != "RuleC"]

        after = self.bundle("after", mutate)
        result = compare(before, after)
        breaking = {(item["code"], item["record_id"]) for item in result["changes"] if item["severity"] == "breaking"}
        namespace = self.manifest["namespace"]
        self.assertIn(("SD220", namespace + "ThingA"), breaking)
        self.assertIn(("SD101", namespace + "RuleC"), breaking)

    def test_invalid_bundle_fails_closed(self):
        before = self.bundle("before")

        def mutate(_manifest, fragment):
            fragment["records"][0]["grammatical_number"] = "plural"

        invalid = self.bundle("invalid", mutate)
        with self.assertRaisesRegex(ValueError, "invalid SEAG bundle"):
            compare(before, invalid)

    def test_inherited_fragment_language_is_semantic(self):
        before = self.bundle("before")
        after = self.bundle("after", lambda _manifest, fragment: fragment.update(language="fi"))
        result = compare(before, after)
        self.assertEqual(5, result["summary"]["total"])
        self.assertEqual({"SD261"}, {item["code"] for item in result["changes"]})

    def test_three_way_detects_divergent_leaf_change(self):
        base = self.bundle("base")
        ours = self.bundle(
            "ours",
            lambda _manifest, fragment: fragment["records"][0].update(definition="Our invented definition."),
        )
        theirs = self.bundle(
            "theirs",
            lambda _manifest, fragment: fragment["records"][0].update(definition="Their invented definition."),
        )
        result = three_way(base, ours, theirs)
        self.assertEqual(1, result["summary"]["conflicts"])
        self.assertEqual("SC100", result["conflicts"][0]["code"])
        self.assertEqual("definition", result["conflicts"][0]["field"])

    def test_three_way_allows_disjoint_changes(self):
        base = self.bundle("base")
        ours = self.bundle(
            "ours",
            lambda _manifest, fragment: fragment["records"][0].update(label="Renamed thing A"),
        )
        theirs = self.bundle(
            "theirs",
            lambda _manifest, fragment: fragment["records"][0].update(definition="A clarified invented thing."),
        )
        result = three_way(base, ours, theirs)
        self.assertEqual([], result["conflicts"])
        self.assertEqual(1, result["summary"]["ours_changes"])
        self.assertEqual(1, result["summary"]["theirs_changes"])

    def test_three_way_detects_divergent_bundle_metadata(self):
        base = self.bundle("base")
        ours = self.bundle("ours", lambda manifest, _fragment: manifest.update(title="Our title"))
        theirs = self.bundle("theirs", lambda manifest, _fragment: manifest.update(title="Their title"))
        result = three_way(base, ours, theirs)
        self.assertEqual(1, result["summary"]["conflicts"])
        self.assertEqual("manifest.title", result["conflicts"][0]["field"])

    def test_three_way_detects_delete_modify_and_divergent_addition(self):
        base = self.bundle("base")

        def ours_change(_manifest, fragment):
            fragment["records"] = [record for record in fragment["records"] if record["id"] != "RuleC"]
            fragment["records"].append(self.new_concept("Added", "Our added concept."))

        def theirs_change(_manifest, fragment):
            next(record for record in fragment["records"] if record["id"] == "RuleC")["definition"] = "A revised rule."
            fragment["records"].append(self.new_concept("Added", "Their added concept."))

        ours = self.bundle("ours", ours_change)
        theirs = self.bundle("theirs", theirs_change)
        codes = [item["code"] for item in three_way(base, ours, theirs)["conflicts"]]
        self.assertEqual(["SC102", "SC101"], codes)

    def test_three_way_guards_confirmation_scope(self):
        base = self.bundle("base")
        ours = self.bundle("ours", lambda _manifest, fragment: self.confirm(fragment["records"][0]))
        theirs = self.bundle(
            "theirs",
            lambda _manifest, fragment: fragment["records"][0].update(definition="Unreviewed branch definition."),
        )
        result = three_way(base, ours, theirs)
        self.assertEqual(["SC104"], [item["code"] for item in result["conflicts"]])

    def test_three_way_guards_structural_relationship_scope(self):
        base = self.bundle("base")
        ours = self.bundle(
            "ours",
            lambda _manifest, fragment: fragment["records"][-1].update(target="ThingA"),
        )
        theirs = self.bundle(
            "theirs",
            lambda _manifest, fragment: fragment["records"][-1].update(target_cardinality="1..*"),
        )
        result = three_way(base, ours, theirs)
        self.assertEqual(["SC103"], [item["code"] for item in result["conflicts"]])

    def test_cli_json_and_failure_policy(self):
        before = self.bundle("before")
        after = self.bundle(
            "after",
            lambda _manifest, fragment: fragment["records"][-1].update(target_cardinality="1..*"),
        )
        completed = subprocess.run(
            (
                sys.executable,
                "-m",
                "seag.semantic_diff",
                str(before),
                str(after),
                "--format",
                "json",
                "--fail-on",
                "breaking",
            ),
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(1, completed.returncode)
        self.assertEqual(1, json.loads(completed.stdout)["summary"]["total"])
        self.assertEqual("", completed.stderr)

    def test_cli_rejects_conflict_policy_in_two_way_mode(self):
        before = self.bundle("before")
        after = self.bundle("after")
        completed = subprocess.run(
            (
                sys.executable,
                "-m",
                "seag.semantic_diff",
                str(before),
                str(after),
                "--fail-on",
                "conflict",
            ),
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(2, completed.returncode)
        self.assertIn("requires three-way mode", completed.stderr)

    def test_human_output_escapes_untrusted_identity_text(self):
        output = format_human(
            {
                "operation": "two-way",
                "changes": [
                    {
                        "severity": "review",
                        "code": "SD211",
                        "record_id": "urn:test:\u202eunsafe#Thing",
                        "field": "definition",
                        "description": "definition changed",
                    }
                ],
            }
        )
        self.assertNotIn("\u202e", output)
        self.assertIn("\\u202e", output)

    @staticmethod
    def confirm(record):
        record["status"] = "confirmed"
        record["provenance"]["verification_status"] = "qualified"
        record["confirmation"] = {
            "decision_ref": "urn:uuid:33333333-3333-4333-8333-333333333333",
            "decided_at": "2026-11-21",
            "confirmer": "fixture-steward",
            "reviewer": "fixture-reviewer",
            "review_ref": "fixture/review-1",
            "reviewed_at": "2026-11-20",
        }

    @staticmethod
    def new_concept(identifier, definition):
        return {
            "id": identifier,
            "kind": "concept",
            "status": "proposed",
            "implementation_alignment": "not_applicable",
            "provenance": {
                "source": "invented test",
                "locator": "test/addition",
                "normative": False,
                "proposer": "test-author",
                "verification_status": "unresolved",
            },
            "label": "Added concept",
            "grammatical_number": "singular",
            "definition": definition,
        }


if __name__ == "__main__":
    unittest.main()
