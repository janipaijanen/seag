# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "generate-evaluation-dossier.py"
SPEC = importlib.util.spec_from_file_location("evaluation_dossier", SCRIPT)
evaluation_dossier = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(evaluation_dossier)


class EvaluationDossierTests(unittest.TestCase):
    def test_committed_outputs_are_current_and_reproducible(self):
        first = evaluation_dossier.render()
        second = evaluation_dossier.render()
        self.assertEqual(first, second)
        self.assertEqual(evaluation_dossier.check(first), [])

    def test_manifest_binds_sources_outputs_and_budget(self):
        outputs = evaluation_dossier.render()
        manifest = json.loads(outputs[evaluation_dossier.MANIFEST])
        self.assertEqual(manifest["status"], "alpha-evaluation-aid")
        self.assertEqual(
            [item["path"] for item in manifest["sources"]],
            [path.as_posix() for path in evaluation_dossier.SOURCE_PATHS],
        )
        self.assertEqual(len(manifest["outputs"]), 2)
        budget = manifest["compact_context_budget"]
        self.assertLessEqual(budget["actual_bytes"], budget["maximum_bytes"])
        self.assertLessEqual(budget["actual_words"], budget["maximum_words"])

    def test_dossier_contains_every_capability_and_standard(self):
        outputs = evaluation_dossier.render()
        dossier = outputs[evaluation_dossier.DOSSIER].decode("utf-8")
        maturity = (ROOT / "maturity.yaml").read_text(encoding="utf-8")
        for capability in evaluation_dossier.parse_capabilities(maturity):
            self.assertIn(f"`{capability['id']}`", dossier)
        register = json.loads((ROOT / "standards.json").read_text(encoding="utf-8"))
        for standard in register["standards"]:
            self.assertIn(f"`{standard['id']}`", dossier)

    def test_check_rejects_changed_output(self):
        outputs = evaluation_dossier.render()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for path, data in outputs.items():
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            (root / evaluation_dossier.CONTEXT).write_text("changed", encoding="utf-8")
            self.assertTrue(evaluation_dossier.check(outputs, root))

    def test_machine_input_rejects_duplicate_json_and_escapes_markdown(self):
        with self.assertRaisesRegex(ValueError, "duplicate JSON member"):
            evaluation_dossier.strict_json(b'{"id": 1, "id": 2}', "probe.json")
        with self.assertRaisesRegex(ValueError, "forbidden JSON number"):
            evaluation_dossier.strict_json(b'{"value": NaN}', "probe.json")
        self.assertEqual(
            evaluation_dossier.markdown_cell("claim | <script>"),
            "claim &#124; &lt;script&gt;",
        )
        with self.assertRaisesRegex(ValueError, "control character"):
            evaluation_dossier.markdown_cell("claim\nsecond row")

    def test_maturity_and_boundary_inputs_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "no capabilities block"):
            evaluation_dossier.parse_capabilities("schema: probe\n")
        inconsistent = """capabilities:
  probe:
    level: 3
    name: Implemented
    evidence:
      - test:probe
"""
        with self.assertRaisesRegex(ValueError, "inconsistent maturity"):
            evaluation_dossier.parse_capabilities(inconsistent)
        duplicate_id = inconsistent + inconsistent.removeprefix("capabilities:\n")
        with self.assertRaisesRegex(ValueError, "duplicate maturity capability id"):
            evaluation_dossier.parse_capabilities(duplicate_id)
        duplicate_level = inconsistent.replace(
            "    name: Implemented", "    level: 3\n    name: Implemented"
        )
        with self.assertRaisesRegex(ValueError, "repeats field level"):
            evaluation_dossier.parse_capabilities(duplicate_level)
        nonnumeric_level = inconsistent.replace("level: 3", "level: three")
        with self.assertRaisesRegex(ValueError, "integer 1..5"):
            evaluation_dossier.parse_capabilities(nonnumeric_level)
        with self.assertRaisesRegex(ValueError, "exactly one evidence_status block"):
            evaluation_dossier.parse_evidence_status("schema: probe\n")
        with self.assertRaisesRegex(ValueError, "canonical evaluation boundary"):
            evaluation_dossier.require_boundary("SEAG is something else.")

    def test_standards_table_input_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "must be an object"):
            evaluation_dossier.validate_standards(["not-an-object"])
        with self.assertRaisesRegex(ValueError, "id must be a nonempty string"):
            evaluation_dossier.validate_standards([{"class": "core", "version": "1"}])
        duplicate = {"id": "probe", "class": "core", "version": "1"}
        with self.assertRaisesRegex(ValueError, "duplicate standard id"):
            evaluation_dossier.validate_standards([duplicate, duplicate.copy()])
        with self.assertRaisesRegex(ValueError, "nonempty version pin"):
            evaluation_dossier.validate_standards([{"id": "probe", "class": "core"}])

    def test_reading_aid_discloses_no_deployable_capability_and_no_pilot_state(self):
        outputs = evaluation_dossier.render()
        for path in (evaluation_dossier.CONTEXT, evaluation_dossier.DOSSIER):
            text = outputs[path].decode("utf-8")
            self.assertIn("No capability is Level 5 Deployable", text)
            self.assertNotIn("pilot is in progress", text)


if __name__ == "__main__":
    unittest.main()
