# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import hashlib
import json
import tempfile
import unittest

from seag.cxl import export, parse
from seag.glossary import extract
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
        self.assertEqual("none", provenance["fallback_policy"])

    def test_glossary_rejects_implicit_language_fallback(self):
        with self.assertRaisesRegex(ValueError, "fallback policy is none"):
            extract(MANIFEST, "fi", WHEN)

    def test_cxl_round_trip_preserves_bounded_graph(self):
        data, sidecar, expected = export(MANIFEST, WHEN)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.cxl"
            path.write_bytes(data)
            self.assertEqual(expected, parse(path))
        self.assertFalse(sidecar["lossless"])
        self.assertIn("cardinalities", sidecar["omissions"])
        self.assertEqual(hashlib.sha256(data).hexdigest(), sidecar["output_sha256"])

    def test_outputs_are_deterministic_for_fixed_timestamp(self):
        first, provenance, _ = export(MANIFEST, WHEN)
        second, repeated, _ = export(MANIFEST, WHEN)
        self.assertEqual(first, second)
        self.assertEqual(json_bytes(provenance), json_bytes(repeated))


if __name__ == "__main__":
    unittest.main()
