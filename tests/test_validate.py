# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Behavioral rejection tests against invented, domain-neutral fixtures."""

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from seag.validate import ipv4_address, ipv6_address, port_number, validate, validate_variant

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

    def test_json_rejects_duplicate_members_and_non_finite_numbers(self):
        self.assertEqual([], self.run_case())
        manifest_path = self.root / "manifest.json"
        original = manifest_path.read_text()
        duplicate = original.replace(
            '"title": "Invented neutral fixture"',
            '"title": "Invented neutral fixture", "title": "Hidden replacement"',
            1,
        )
        manifest_path.write_text(duplicate)
        self.assertTrue(any("duplicate JSON object member" in error for error in validate(manifest_path)))
        manifest_path.write_text(original.replace('"title": "Invented neutral fixture"', '"title": NaN', 1))
        self.assertTrue(any("non-finite JSON number forbidden" in error for error in validate(manifest_path)))

    def test_fragment_json_rejects_duplicate_members(self):
        self.assertEqual([], self.run_case())
        fragment_path = self.root / "fragment.json"
        raw = fragment_path.read_text().replace(
            '"revision": "draft-1"',
            '"revision": "draft-1", "revision": "hidden"',
            1,
        ).encode()
        fragment_path.write_bytes(raw)
        manifest = json.loads((self.root / "manifest.json").read_text())
        manifest["fragments"][0]["sha256"] = hashlib.sha256(raw).hexdigest()
        (self.root / "manifest.json").write_text(json.dumps(manifest))
        self.assertTrue(any("duplicate JSON object member" in error for error in validate(self.root / "manifest.json")))

    def test_json_files_accept_utf8_only(self):
        self.assertEqual([], self.run_case())
        manifest_path = self.root / "manifest.json"
        fragment_path = self.root / "fragment.json"
        manifest_text = manifest_path.read_text()
        fragment_text = fragment_path.read_text()
        manifest_path.write_bytes(manifest_text.encode("utf-16"))
        self.assertTrue(any("cannot read JSON" in error for error in validate(manifest_path)))

        manifest_path.write_text(manifest_text)
        fragment_raw = fragment_text.encode("utf-32")
        fragment_path.write_bytes(fragment_raw)
        manifest = json.loads(manifest_text)
        manifest["fragments"][0]["sha256"] = hashlib.sha256(fragment_raw).hexdigest()
        manifest_path.write_text(json.dumps(manifest))
        self.assertTrue(any("cannot read fragment" in error for error in validate(manifest_path)))

        variant_path = self.root / "variant.json"
        variant = json.loads((VALID / "variant.json").read_text())
        variant_path.write_bytes(json.dumps(variant).encode("utf-16"))
        self.assertTrue(any("cannot read JSON" in error for error in validate_variant(variant_path)))

    def test_language_tags_require_supported_bcp47_shape(self):
        for tag in ("en_US", "not a tag", "en-a-foo-a-bar", "sl-rozaj-rozaj", "en-u-ca-gregory-u-nu-latn"):
            with self.subTest(tag=tag):
                self.manifest["default_language"] = tag
                self.assert_only_error("well-formed BCP 47")

    def test_supported_well_formed_bcp47_shapes(self):
        for tag in ("en", "en-GB", "sr-Latn", "zh-Hant-TW", "de-CH-1901", "en-a-foo-b-bar", "x-seag", "i-klingon"):
            with self.subTest(tag=tag):
                self.manifest["default_language"] = tag
                self.assertEqual([], self.run_case())

    def test_concept_requires_singular_number_declaration(self):
        record = self.fragment["records"][0]
        del record["grammatical_number"]
        self.assert_only_error("concept label must be declared singular")
        record["grammatical_number"] = "plural"
        self.assert_only_error("concept label must be declared singular")

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
        for name in ("precedes", "directly precedes", "is preceded by", "preceded by", "changes state to", "is followed by", "followed by", "changes_state_to", "changes-state-to", "triggered by", "is triggered by", "triggers", "moves to", "goes to", "happens before", "succeeds", "changed state to", "leads to", "results in", "is succeeded by", "becomes"):
            with self.subTest(name=name):
                self.fragment["records"][-1]["name"] = name
                self.assert_only_error("process or transition association name forbidden")

    def test_static_names_are_not_over_rejected(self):
        for name in ("is named after", "has sequence number", "has step count", "has workflow owner", "has transition fee", "has cause code", "trigger condition for", "cause code of", "preceding version of", "cause of", "follows standard", "enables access to", "is following member of"):
            with self.subTest(name=name):
                self.fragment["records"][-1]["name"] = name
                self.assertEqual([], self.run_case())

    def test_hidden_format_character_rejected(self):
        self.fragment["records"][-1]["name"] = "pre\u200bcedes"
        self.assert_rejects("hidden format characters forbidden")

    def test_required_human_text_rejects_forbidden_control_characters(self):
        self.fragment["records"][0]["label"] = "Thing\u0000A"
        self.assert_only_error("forbidden control characters")

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

    def test_variant_closed_shape_and_timestamp(self):
        variant = json.loads((VALID / "variant.json").read_text())
        path = self.root / "variant.json"
        for field, value, message in (
            ("sequence", ["a"], "unsupported fields: sequence"),
            ("omissions", ["layout", 1], "explicit string array"),
            ("unsupported_constructs", [None], "explicit string array"),
            ("generated_at", "sometime", "ISO timestamp with timezone"),
            ("source_manifest_sha256", "bad", "SHA-256 hex required"),
        ):
            with self.subTest(field=field):
                changed = dict(variant, **{field: value})
                path.write_text(json.dumps(changed))
                errors = validate_variant(path)
                self.assertEqual(1, len(errors), errors)
                self.assertIn(message, errors[0])

    def test_variant_lossless_conflict(self):
        variant = json.loads((VALID / "variant.json").read_text())
        variant.update(lossless=True, unsupported_constructs=["invented-layout"])
        path = self.root / "variant.json"
        path.write_text(json.dumps(variant))
        self.assertEqual(["variant: lossless claim conflicts with unsupported constructs"], validate_variant(path))

    def test_invalid_fixture_directories(self):
        for name, expected in (("process-flow", "controlled predicate"), ("wrong-endpoint", "wrong endpoint type"), ("missing-cardinality", "explicit both-end cardinality")):
            with self.subTest(name=name):
                errors = validate(ROOT / "fixtures" / "invalid" / name / "manifest.json")
                self.assertEqual(1, len(errors), errors)
                self.assertIn(expected, errors[0])

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

    def test_reviewer_confirmer_collapse_is_disclosed(self):
        record = self.confirm()
        record["confirmation"]["reviewer"] = " FIXTURE-STEWARD "
        self.assert_only_error("same declared reviewer and confirmer needs review-limit disclosure")
        record["confirmation"]["review_limit"] = "Same steward did both actions; no independent review is claimed."
        self.assertEqual([], self.run_case())

    def test_proposed_confirmation_is_checked(self):
        record = self.fragment["records"][0]
        record["confirmation"] = self.confirm(1)["confirmation"].copy()
        record["confirmation"]["junk"] = "unreviewed"
        self.assert_only_error("unsupported fields: junk")

    def test_empty_confirmation_does_not_claim_actor_collapse(self):
        record = self.fragment["records"][0]
        record["confirmation"] = {}
        errors = self.run_case()
        self.assertFalse(any("reviewer and confirmer" in error for error in errors), errors)
        self.assertTrue(any("confirmation block needs" in error for error in errors), errors)

    def test_malformed_proposer_does_not_claim_actor_collapse(self):
        record = self.fragment["records"][0]
        record["confirmation"] = {}
        for proposer in (None, "", "   ", 42):
            with self.subTest(proposer=proposer):
                record["provenance"]["proposer"] = proposer
                errors = self.run_case()
                self.assertFalse(any("role-collapse" in error or "self-review" in error for error in errors), errors)
        del record["provenance"]["proposer"]
        errors = self.run_case()
        self.assertFalse(any("role-collapse" in error or "self-review" in error for error in errors), errors)

    def test_optional_disclosures_and_replacement_are_nonempty_strings(self):
        record = self.fragment["records"][0]
        for value in ("", 42):
            with self.subTest(field="replacement_or_reason", value=value):
                record["replacement_or_reason"] = value
                self.assert_only_error("replacement or rationale must be a nonempty string")
        del record["replacement_or_reason"]
        confirmation = self.confirm()["confirmation"]
        for field in ("review_limit", "role_collapse_note"):
            for value in ("", 42):
                with self.subTest(field=field, value=value):
                    confirmation[field] = value
                    self.assert_only_error("disclosure must be a nonempty string")
            confirmation.pop(field)

    def test_review_must_precede_decision(self):
        record = self.confirm()
        record["confirmation"]["reviewed_at"] = "2026-11-22"
        self.assert_only_error("review date must not follow decision date")

    def test_reviewed_at_requires_iso_date(self):
        record = self.confirm()
        record["confirmation"]["reviewed_at"] = "yesterday"
        self.assert_only_error("reviewed_at: ISO calendar date required")

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

    def test_unknown_inventory_and_provenance_fields(self):
        self.manifest["fragments"][0]["sequence"] = 1
        self.assert_only_error("unsupported fields: sequence")
        del self.manifest["fragments"][0]["sequence"]
        self.fragment["records"][0]["provenance"]["workflow"] = "unexpected"
        self.assert_only_error("unsupported fields: workflow")

    def test_core_manifest_shape_rejections(self):
        cases = (
            ("seag_schema", "0.1-draft", "expected 0.1-draft.2"),
            ("status", "release", "draft bundles only"),
            ("bundle_id", "relative", "absolute IRI required"),
            ("namespace", "urn:example:terms", "ending in # or /"),
            ("title", "", "nonempty string"),
            ("default_language", "", "nonempty string"),
            ("licence", "", "nonempty string"),
        )
        for field, value, message in cases:
            with self.subTest(field=field):
                original = self.manifest[field]
                original_fragment = self.fragment.get(field)
                self.manifest[field] = value
                if field in ("bundle_id", "namespace"):
                    self.fragment[field] = value
                self.assert_only_error(message)
                self.manifest[field] = original
                if field in ("bundle_id", "namespace"):
                    self.fragment[field] = original_fragment

    def test_core_record_shape_rejections(self):
        record = self.fragment["records"][-1]
        cases = (
            ("id", "bad id", "stable local ID"),
            ("status", "certified", "invalid semantic status"),
            ("implementation_alignment", "shipped", "separate alignment status"),
        )
        for field, value, message in cases:
            with self.subTest(field=field):
                original = record[field]
                record[field] = value
                self.assert_only_error(message)
                record[field] = original
        record["provenance"]["normative"] = "yes"
        self.assert_only_error("normative boolean")

    def test_non_object_fragment_and_non_array_records(self):
        self.fragment = ["wrong"]
        self.assert_only_error("fragment must be an object")
        self.fragment = json.loads((VALID / "fragment.json").read_text())
        self.fragment["records"] = {}
        self.assert_only_error("array required")

    def test_duplicate_fragment_id(self):
        self.manifest["fragments"].append(copy.deepcopy(self.manifest["fragments"][0]))
        self.assert_rejects("duplicate fragment ID")

    def test_cli_exit_codes(self):
        ok = subprocess.run([sys.executable, "-I", str(ROOT / "seag" / "validate.py"), str(VALID / "manifest.json")], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(0, ok.returncode, ok.stderr)
        self.assertIn("identities and authority unverified", ok.stdout)
        bad = subprocess.run([sys.executable, "-I", str(ROOT / "seag" / "validate.py"), str(ROOT / "fixtures" / "invalid" / "process-flow" / "manifest.json")], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(1, bad.returncode, bad.stdout)

    def test_deprecated_requires_rationale(self):
        self.fragment["records"][0]["status"] = "deprecated"
        self.assert_rejects("deprecated record needs replacement or rationale")

    def test_deprecated_with_rationale_is_valid(self):
        record = self.fragment["records"][0]
        record.update(status="deprecated", replacement_or_reason="Replaced by ThingB.")
        self.assertEqual([], self.run_case())

    def test_fragment_language_revision_and_manifest_identity_are_checked(self):
        for field in ("language", "revision"):
            with self.subTest(field=field):
                original = self.fragment[field]
                self.fragment[field] = ""
                self.assert_only_error("nonempty string required")
                self.fragment[field] = original
        for field, value in (("bundle_id", "urn:uuid:aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"), ("fragment_id", "other"), ("role", "other")):
            with self.subTest(field=field):
                original = self.fragment[field]
                self.fragment[field] = value
                self.assert_only_error("does not match manifest")
                self.fragment[field] = original

    def test_invalid_iri_and_namespace_forms(self):
        rule = self.fragment["records"][3]
        for iri in (
            "relative",
            "https://example.invalid/%zz",
            "https://example.invalid:bad/id",
            "https://example.invalid:-1/id",
            "https://example.invalid:65536/id",
            "https://256.1.1.1/id",
            "https://192.168.01.1/id",
            "https://[invalid",
            "https://[2001:db8:::1]/id",
        ):
            with self.subTest(iri=iri):
                rule["iri"] = iri
                self.assert_only_error("absolute external artifact IRI required")
        rule["iri"] = "urn:uuid:22222222-2222-4222-8222-222222222222"
        self.manifest["namespace"] = "https://example.invalid/terms"
        self.fragment["namespace"] = self.manifest["namespace"]
        self.assert_only_error("ending in # or / required")

    def test_valid_absolute_iri_forms(self):
        rule = self.fragment["records"][3]
        for iri in (
            "HTTPS://example.invalid/path",
            "https://example.invalid:0/path",
            "https://example.invalid:65535/path",
            "https://192.168.1.1/path",
            "https://[2001:db8::1]/path",
            "https://例え.invalid/用語",
            "tag:example.org,2026:term",
            "did:example:123",
        ):
            with self.subTest(iri=iri):
                rule["iri"] = iri
                self.assertEqual([], self.run_case())

    def test_typed_network_value_validators_do_not_coerce(self):
        self.assertTrue(port_number(0))
        self.assertTrue(port_number(65535))
        for value in (-1, 65536, True, "443", 443.0):
            with self.subTest(port=value):
                self.assertFalse(port_number(value))
        self.assertTrue(ipv4_address("192.0.2.1"))
        for value in ("256.0.2.1", "192.0.02.1", "192.0.2", 3221225985):
            with self.subTest(ipv4=value):
                self.assertFalse(ipv4_address(value))
        self.assertTrue(ipv6_address("2001:db8::1"))
        self.assertTrue(ipv6_address("2001:0DB8:0:0:0:0:0:1"))
        for value in ("2001:db8:::1", "fe80::1%eth0", "192.0.2.1", 1):
            with self.subTest(ipv6=value):
                self.assertFalse(ipv6_address(value))

    def test_unknown_record_kind_and_non_object_record(self):
        self.fragment["records"][0]["kind"] = "unknown"
        self.assert_rejects("unknown record kind")
        self.fragment = json.loads((VALID / "fragment.json").read_text())
        self.fragment["records"][0] = []
        self.assert_rejects("object required")

    def test_cli_variant_success_names_variant_metadata(self):
        result = subprocess.run([sys.executable, "-I", str(ROOT / "seag" / "validate.py"), "--variant", str(VALID / "variant.json")], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("variant metadata valid", result.stdout)

    def test_confirmed_source_cardinality_cannot_be_unresolved(self):
        association = self.confirm(-1)
        association["source_cardinality"] = "unresolved"
        self.assert_only_error("confirmed cardinality cannot be unresolved")

    def test_variant_requires_absolute_identifiers(self):
        variant = json.loads((VALID / "variant.json").read_text())
        path = self.root / "variant.json"
        for field in ("variant_id", "representation_of"):
            with self.subTest(field=field):
                changed = dict(variant, **{field: "relative"})
                path.write_text(json.dumps(changed))
                self.assertEqual([f"variant.{field}: absolute immutable IRI required"], validate_variant(path))

    def test_malformed_record_kind_is_reported(self):
        self.fragment["records"][0]["kind"] = ["concept"]
        self.assert_rejects("unknown record kind")

    def test_symlink_cannot_escape_manifest_directory(self):
        outside = self.root.parent / (self.root.name + "-outside.json")
        outside.write_text(json.dumps(self.fragment))
        self.addCleanup(outside.unlink)
        (self.root / "fragment.json").symlink_to(outside)
        self.manifest["fragments"][0]["sha256"] = hashlib.sha256(outside.read_bytes()).hexdigest()
        (self.root / "manifest.json").write_text(json.dumps(self.manifest))
        errors = validate(self.root / "manifest.json")
        self.assertEqual(1, len(errors), errors)
        self.assertIn("path escapes manifest directory", errors[0])

    def test_external_reference_endpoint_is_predicate_scoped(self):
        external = copy.deepcopy(self.fragment["records"][3])
        external.update(id="ExternalX", kind="external_reference", iri="tag:example.org,2026:term")
        self.fragment["records"].append(external)
        proposition = self.fragment["records"][4]
        proposition.update(predicate="refers to", target="ExternalX")
        for key in ("name", "definition", "source_cardinality", "target_cardinality"):
            del proposition[key]
        self.assertEqual([], self.run_case())
        proposition["predicate"] = "is part of"
        self.assert_only_error("wrong endpoint type")


if __name__ == "__main__":
    unittest.main()
