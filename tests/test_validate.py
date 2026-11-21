"""Behavioral rejection tests against invented, domain-neutral fixtures."""

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from seag.validate import validate, validate_variant

ROOT = Path(__file__).resolve().parents[1]
VALID = ROOT / "fixtures" / "valid"


class SourceValidationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = json.loads((VALID / "manifest.json").read_text())
        self.fragment = json.loads((VALID / "fragment.json").read_text())

    def run_case(self):
        payload = (json.dumps(self.fragment, indent=2) + "\n").encode()
        (self.root / "fragment.json").write_bytes(payload)
        self.manifest["fragments"][0]["sha256"] = hashlib.sha256(payload).hexdigest()
        (self.root / "manifest.json").write_text(json.dumps(self.manifest))
        return validate(self.root / "manifest.json")

    def assert_rejects(self, expected):
        errors = self.run_case()
        self.assertTrue(any(expected in error for error in errors), errors)

    def assert_only_error(self, expected):
        errors = self.run_case()
        self.assertEqual(1, len(errors), errors)
        self.assertIn(expected, errors[0])

    def confirm(self, index=0):
        record = self.fragment["records"][index]
        record["status"] = "confirmed"
        record["provenance"]["verification_status"] = "qualified"
        record["confirmation"] = {"decision_ref": "urn:uuid:33333333-3333-4333-8333-333333333333", "decided_at": "2026-11-21", "confirmer": "fixture-steward", "reviewer": "fixture-reviewer", "review_ref": "fixture/review-1", "reviewed_at": "2026-11-20"}
        return record

    def test_valid_fixture(self):
        self.assertEqual([], self.run_case())

    def test_duplicate_record_id(self):
        self.fragment["records"].append(copy.deepcopy(self.fragment["records"][0]))
        self.assert_rejects("duplicate expanded record ID")

    def test_wrong_endpoint_type(self):
        self.fragment["records"][-1]["target"] = "StateB"
        self.assert_rejects("wrong endpoint type")

    def test_missing_target_cardinality(self):
        del self.fragment["records"][-1]["target_cardinality"]
        self.assert_rejects("explicit both-end cardinality")

    def test_process_flow_rejected(self):
        self.fragment["records"][-1]["predicate"] = "triggers"
        self.assert_rejects("six static controlled predicates")

    def test_process_name_cannot_hide_as_named_association(self):
        for name in ("precedes", "changes state to", "is followed by", "changes_state_to", "changes-state-to", "triggered by", "preceding", "changed state to", "leads to", "results in", "is succeeded by", "becomes"):
            with self.subTest(name=name):
                self.fragment["records"][-1]["name"] = name
                self.assert_only_error("process or transition association name forbidden")

    def test_static_names_are_not_over_rejected(self):
        for name in ("is named after", "has sequence number", "has step count", "has workflow owner"):
            with self.subTest(name=name):
                self.fragment["records"][-1]["name"] = name
                self.assertEqual([], self.run_case())

    def test_hidden_format_character_rejected(self):
        self.fragment["records"][-1]["name"] = "pre\u200bcedes"
        self.assert_rejects("hidden format characters forbidden")

    def test_vague_name_is_rejected(self):
        for name in ("relates to", "relates to the", "related to", "supports", "uses", "has many", "HAS_MANY"):
            with self.subTest(name=name):
                self.fragment["records"][-1]["name"] = name
                self.assert_only_error("vague association name")

    def test_process_extension_fields_are_rejected(self):
        for field in ("guard", "next_state", "sequence"):
            with self.subTest(field=field):
                self.fragment["records"][-1][field] = "invented"
                self.assert_only_error("unsupported record fields")
                del self.fragment["records"][-1][field]

    def test_process_fields_rejected_everywhere(self):
        self.manifest["sequence"] = ["a"]
        self.assert_only_error("manifest: unsupported fields: sequence")
        del self.manifest["sequence"]
        self.fragment["workflow"] = ["a"]
        self.assert_only_error("fragment.json: unsupported fields: workflow")
        del self.fragment["workflow"]
        self.fragment["records"][2]["transitions_to"] = "StateB"
        self.assert_only_error("unsupported record fields: transitions_to")
        del self.fragment["records"][2]["transitions_to"]
        self.fragment["records"][0]["next_state"] = "StateB"
        self.assert_only_error("unsupported record fields: next_state")

    def test_non_named_predicate_cannot_hide_process_name(self):
        self.fragment["records"][-1].update(predicate="is part of", name="precedes")
        self.assert_only_error("named-association fields unsupported")

    def test_provenance_required(self):
        del self.fragment["records"][0]["provenance"]
        self.assert_rejects("evidence verification status required")

    def test_namespace_mismatch(self):
        self.fragment["namespace"] = "urn:uuid:00000000-0000-4000-8000-000000000000#"
        self.assert_rejects("does not match manifest")

    def test_taxonomy_cycle(self):
        base = copy.deepcopy(self.fragment["records"][-1])
        base.update(id="TaxA", predicate="is a kind of", source="ThingA", target="ThingB")
        reverse = dict(base, id="TaxB", source="ThingB", target="ThingA")
        self.fragment["records"].extend([base, reverse])
        self.assert_rejects("taxonomy: cycle")

    def test_variant_without_source_digest(self):
        variant = json.loads((VALID / "variant.json").read_text())
        del variant["source_manifest_sha256"]
        path = self.root / "variant.json"
        path.write_text(json.dumps(variant))
        self.assertTrue(any("source_manifest_sha256" in e for e in validate_variant(path)))

    def test_variant_fixture(self):
        self.assertEqual([], validate_variant(VALID / "variant.json"))

    def test_invalid_fixture_directories(self):
        for name, expected in (("process-flow", "controlled predicate"), ("wrong-endpoint", "wrong endpoint type"), ("missing-cardinality", "explicit both-end cardinality")):
            with self.subTest(name=name):
                errors = validate(ROOT / "fixtures" / "invalid" / name / "manifest.json")
                self.assertTrue(any(expected in error for error in errors), errors)

    def test_malformed_endpoint_is_reported(self):
        self.fragment["records"][-1]["target"] = ["ThingB"]
        self.assert_rejects("unresolved local endpoint")

    def test_confirmed_association_cannot_hide_cardinality(self):
        association = self.confirm(-1)
        association["target_cardinality"] = "unresolved"
        self.assert_only_error("confirmed cardinality cannot be unresolved")

    def test_confirmed_requires_review_and_decision(self):
        self.fragment["records"][-1]["status"] = "confirmed"
        self.assert_rejects("separate decision and review references")

    def test_qualified_evidence_and_distinct_actions_can_be_confirmed(self):
        self.confirm()
        self.assertEqual([], self.run_case())

    def test_role_collapse_and_self_review_are_disclosed(self):
        record = self.confirm()
        record["confirmation"]["confirmer"] = " INVENTED-FIXTURE-AUTHOR "
        self.assert_only_error("role-collapse disclosure")
        record["confirmation"]["role_collapse_note"] = "Same human acting as separate steward; decisions recorded separately."
        record["confirmation"]["reviewer"] = "Invented-Fixture-Author"
        self.assert_only_error("self-review must be disclosed")
        record["confirmation"]["review_limit"] = "Author review is not independent conformance evidence."
        self.assertEqual([], self.run_case())

    def test_confirmed_date_and_evidence_status(self):
        record = self.confirm()
        record["confirmation"]["decided_at"] = "soon"
        self.assert_only_error("ISO calendar date required")
        record["confirmation"]["decided_at"] = "2026-11-21"
        record["provenance"]["verification_status"] = "unresolved"
        self.assert_only_error("qualified or verified source evidence")

    def test_rule_and_external_reference_require_label_definition_iri(self):
        rule = self.fragment["records"][3]
        for field in ("label", "definition", "iri"):
            with self.subTest(field=field):
                value = rule.pop(field)
                self.assertEqual(1, len(self.run_case()))
                rule[field] = value
        external = copy.deepcopy(rule)
        external.update(id="ExternalX", kind="external_reference", iri="tag:example.org,2026:term")
        self.fragment["records"].append(external)
        self.assertEqual([], self.run_case())

    def test_manifest_digest_and_path(self):
        self.assertEqual([], self.run_case())
        stored = json.loads((self.root / "manifest.json").read_text())
        stored["fragments"][0]["sha256"] = "0" * 64
        (self.root / "manifest.json").write_text(json.dumps(stored))
        self.assertEqual(1, len(validate(self.root / "manifest.json")))
        self.manifest["fragments"][0]["path"] = "../fragment.json"
        self.assert_rejects("safe relative path")

    def test_duplicate_fragment_id(self):
        self.manifest["fragments"].append(copy.deepcopy(self.manifest["fragments"][0]))
        self.assert_rejects("duplicate fragment ID")

    def test_cli_exit_codes(self):
        ok = subprocess.run([sys.executable, "-m", "seag.validate", str(VALID / "manifest.json")], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(0, ok.returncode, ok.stderr)
        bad = subprocess.run([sys.executable, "-m", "seag.validate", str(ROOT / "fixtures" / "invalid" / "process-flow" / "manifest.json")], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(1, bad.returncode, bad.stdout)

    def test_deprecated_requires_rationale(self):
        self.fragment["records"][0]["status"] = "deprecated"
        self.assert_rejects("deprecated record needs replacement or rationale")

    def test_malformed_record_kind_is_reported(self):
        self.fragment["records"][0]["kind"] = ["concept"]
        self.assert_rejects("unknown record kind")


if __name__ == "__main__":
    unittest.main()
