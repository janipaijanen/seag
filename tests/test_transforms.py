# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch

from seag.cxl import export, main as cxl_main, parse, parse_bytes, xml_text
from seag.glossary import extract
from seag.source import load_bundle
from seag.transform import json_bytes


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "fixtures" / "valid" / "manifest.json"
WHEN = "2026-11-22T00:00:00Z"


class TransformTest(unittest.TestCase):
    def test_glossary_retains_identity_language_and_source_provenance(self):
        glossary, provenance = extract(MANIFEST, "en", WHEN)
        self.assertEqual("seag/glossary/v1", glossary["schema"])
        self.assertEqual(4, len(glossary["entries"]))
        self.assertEqual("invented fixture", glossary["entries"][0]["source_provenance"]["source"])
        self.assertEqual("terms", glossary["entries"][0]["source_fragment_id"])
        self.assertEqual(["terms"], provenance["source_fragment_ids"])
        self.assertEqual("none", provenance["fallback_policy"])

    def test_glossary_rejects_implicit_language_fallback(self):
        with self.assertRaisesRegex(ValueError, "fallback policy is none"):
            extract(MANIFEST, "fi", WHEN)

    def test_glossary_retains_confirmation_and_singular_declaration(self):
        fragment = json.loads((MANIFEST.parent / "fragment.json").read_text())
        record = fragment["records"][0]
        record["status"] = "confirmed"
        record["provenance"]["verification_status"] = "verified"
        record["confirmation"] = {
            "decision_ref": "urn:uuid:33333333-3333-4333-8333-333333333333",
            "decided_at": "2026-11-21",
            "confirmer": "fixture-steward",
            "reviewer": "fixture-reviewer",
            "review_ref": "fixture/review-1",
            "reviewed_at": "2026-11-20",
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fragment_data = json_bytes(fragment)
            (root / "fragment.json").write_bytes(fragment_data)
            manifest = json.loads(MANIFEST.read_text())
            manifest["fragments"][0]["sha256"] = hashlib.sha256(fragment_data).hexdigest()
            (root / "manifest.json").write_bytes(json_bytes(manifest))
            glossary, _provenance = extract(root / "manifest.json", "en", WHEN)
        entry = next(item for item in glossary["entries"] if item["local_id"] == "ThingA")
        self.assertEqual("singular", entry["grammatical_number"])
        self.assertEqual(record["confirmation"], entry["confirmation"])

    def test_cxl_round_trip_preserves_bounded_graph(self):
        data, sidecar, expected = export(MANIFEST, WHEN)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.cxl"
            path.write_bytes(data)
            self.assertEqual(expected, parse(path))
        self.assertFalse(sidecar["lossless"])
        self.assertIn("source and target cardinalities", sidecar["omissions"])
        self.assertIn("external reference IRIs", sidecar["omissions"])
        self.assertIn("record kind distinctions", sidecar["omissions"])
        self.assertEqual(hashlib.sha256(data).hexdigest(), sidecar["output_sha256"])

    def test_outputs_are_deterministic_for_fixed_timestamp(self):
        first, provenance, _ = export(MANIFEST, WHEN)
        second, repeated, _ = export(MANIFEST, WHEN)
        self.assertEqual(first, second)
        self.assertEqual(json_bytes(provenance), json_bytes(repeated))

    def test_cxl_rejects_forbidden_xml_and_dtd(self):
        with self.assertRaisesRegex(ValueError, "XML-forbidden"):
            xml_text("bad\x00value")
        with self.assertRaisesRegex(ValueError, "XML-forbidden"):
            xml_text("bad\ud800value")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "hostile.cxl"
            path.write_text("<!DOCTYPE cmap [<!ENTITY x 'x'>]><cmap/>")
            with self.assertRaisesRegex(ValueError, "DTD and entity"):
                parse(path)
        hostile = "<!DOCTYPE cmap [<!ENTITY x 'EXPANDED'>]><cmap>&x;</cmap>".encode("utf-16")
        with self.assertRaisesRegex(ValueError, "UTF-8 only"):
            parse_bytes(hostile)

    def test_failed_cxl_verification_does_not_write_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "invalid.cxl"
            invalid = b"<?xml version='1.0' encoding='utf-8'?><cmap>&#55296;</cmap>\n"
            with patch("seag.cxl.export", return_value=(invalid, {}, {})), patch(
                "sys.argv",
                ["seag.cxl", str(MANIFEST), "--generated-at", WHEN, "--output", str(output), "--verify"],
            ):
                self.assertEqual(1, cxl_main())
            self.assertFalse(output.exists())
            self.assertFalse(output.with_name(output.name + ".provenance.json").exists())

    def test_transform_consumes_the_validated_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = root / "manifest.json"
            fragment_path = root / "fragment.json"
            manifest_path.write_bytes(MANIFEST.read_bytes())
            fragment_path.write_bytes((MANIFEST.parent / "fragment.json").read_bytes())
            from seag.validate import validate as real_validate

            def mutate_after_validation(path, **snapshot):
                errors = real_validate(path, **snapshot)
                fragment = json.loads(fragment_path.read_text())
                fragment["records"][0]["label"] = "Substituted after validation"
                fragment_path.write_bytes(json_bytes(fragment))
                return errors

            with patch("seag.source.validate", side_effect=mutate_after_validation):
                _manifest, records, _digest = load_bundle(manifest_path)
            thing_a = next(record for _fragment, record in records if record["id"] == "ThingA")
            self.assertEqual("Thing A", thing_a["label"])

    def test_generated_timestamp_requires_rfc3339(self):
        from seag.transform import timestamp

        with self.assertRaisesRegex(ValueError, "RFC 3339"):
            timestamp("2026-11-22T00:00:00")

    def test_generated_timestamp_requires_reproducible_source(self):
        from unittest.mock import patch
        from seag.transform import timestamp

        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(ValueError, "SOURCE_DATE_EPOCH"):
                timestamp(None)


if __name__ == "__main__":
    unittest.main()
