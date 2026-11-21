"""Behavioral rejection tests against invented, domain-neutral fixtures."""

import copy
import hashlib
import json
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
        self.assert_rejects("process flow and transitions")

    def test_process_name_cannot_hide_as_named_association(self):
        for name in ("precedes", "changes state to", "is followed by"):
            with self.subTest(name=name):
                self.fragment["records"][-1]["name"] = name
                self.assert_rejects("process or transition association name forbidden")

    def test_vague_name_is_rejected(self):
        self.fragment["records"][-1]["name"] = "relates to"
        self.assert_rejects("vague association name")

    def test_process_extension_fields_are_rejected(self):
        for field in ("guard", "next_state", "sequence"):
            with self.subTest(field=field):
                self.fragment["records"][-1][field] = "invented"
                self.assert_rejects("unsupported proposition fields")
                del self.fragment["records"][-1][field]

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
        association = self.fragment["records"][-1]
        association["provenance"]["verification_status"] = "verified"
        association.update(status="confirmed", confirmation={"decision_ref":"urn:uuid:33333333-3333-4333-8333-333333333333","decided_at":"2026-11-21","confirmer":"invented-confirmer","reviewer":"invented-reviewer"}, target_cardinality="unresolved")
        self.assert_rejects("confirmed cardinality cannot be unresolved")

    def test_confirmed_requires_independent_review(self):
        self.fragment["records"][-1]["status"] = "confirmed"
        self.assert_rejects("confirmed record needs decision reference")

    def test_deprecated_requires_rationale(self):
        self.fragment["records"][0]["status"] = "deprecated"
        self.assert_rejects("deprecated record needs replacement or rationale")

    def test_malformed_record_kind_is_reported(self):
        self.fragment["records"][0]["kind"] = ["concept"]
        self.assert_rejects("unknown record kind")


if __name__ == "__main__":
    unittest.main()
