# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

import importlib.util
import json
from pathlib import Path
import shutil
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
        self.assertEqual(
            manifest["evaluation_evidence_scope"]["control"], "project-controlled"
        )
        self.assertEqual(
            manifest["evaluation_evidence_scope"][
                "external_consumer_or_adopter_attestation"
            ],
            "absent",
        )
        self.assertEqual(manifest["stewardship"]["maintainer_model"], "single-maintainer")
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
        duplicate_evidence = inconsistent.replace(
            "      - test:probe", "      - test:probe\n    evidence:"
        )
        with self.assertRaisesRegex(ValueError, "repeats field evidence"):
            evaluation_dossier.parse_capabilities(duplicate_evidence)
        with self.assertRaisesRegex(ValueError, "exactly one evidence_status block"):
            evaluation_dossier.parse_evidence_status("schema: probe\n")
        evidence_status = """evidence_status:
  problem_framing: theoretical
  independent_project_benefit: theoretical
"""
        with self.assertRaisesRegex(ValueError, "unknown value"):
            evaluation_dossier.parse_evidence_status(
                evidence_status.replace(
                    "problem_framing: theoretical", "problem_framing: unsupported"
                )
            )
        with self.assertRaisesRegex(ValueError, "exactly one evidence_status block"):
            evaluation_dossier.parse_evidence_status(evidence_status * 2)
        evidence_scope = """evaluation_evidence_scope:
  control: project-controlled
  nonauthor_in_project_review: present
  nonauthor_review_context: ai-agents-in-same-project
  external_consumer_or_adopter_attestation: absent
"""
        with self.assertRaisesRegex(ValueError, "exactly one evaluation_evidence_scope"):
            evaluation_dossier.parse_evaluation_evidence_scope("schema: probe\n")
        with self.assertRaisesRegex(ValueError, "control is unknown"):
            evaluation_dossier.parse_evaluation_evidence_scope(
                evidence_scope.replace("project-controlled", "unclassified")
            )
        with self.assertRaisesRegex(ValueError, "presence and context are inconsistent"):
            evaluation_dossier.parse_evaluation_evidence_scope(
                evidence_scope.replace(
                    "nonauthor_in_project_review: present",
                    "nonauthor_in_project_review: absent",
                )
            )
        with self.assertRaisesRegex(ValueError, "canonical evaluation boundary"):
            evaluation_dossier.require_boundary("SEAG is something else.")
        with self.assertRaisesRegex(ValueError, "canonical stewardship boundary"):
            evaluation_dossier.require_boundary(evaluation_dossier.BOUNDARY)
        evaluation_dossier.require_boundary(
            "\n".join(
                (
                    evaluation_dossier.BOUNDARY,
                    "SEAG is currently maintained by J. Example as a "
                    "single-maintainer project in public review.",
                    evaluation_dossier.SUPPORT_BOUNDARY,
                )
            )
        )
        with self.assertRaisesRegex(ValueError, "SECURITY.md"):
            evaluation_dossier.require_security_stewardship("# Security\n")

    def test_standards_table_input_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "must be an object"):
            evaluation_dossier.validate_standards(["not-an-object"])
        with self.assertRaisesRegex(ValueError, "id must be a nonempty string"):
            evaluation_dossier.validate_standards([{"class": "core", "version": "1"}])
        duplicate = {"id": "probe", "class": "core", "version": "1"}
        with self.assertRaisesRegex(ValueError, "duplicate standard id"):
            evaluation_dossier.validate_standards([duplicate, duplicate.copy()])
        with self.assertRaisesRegex(ValueError, "class must be a nonempty string"):
            evaluation_dossier.validate_standards([{"id": "probe", "version": "1"}])
        with self.assertRaisesRegex(ValueError, "claim must be a nonempty string"):
            evaluation_dossier.validate_standards(
                [{"id": "probe", "class": "core", "version": "1", "claim": 1}]
            )
        with self.assertRaisesRegex(ValueError, "nonempty version pin"):
            evaluation_dossier.validate_standards([{"id": "probe", "class": "core"}])
        with self.assertRaisesRegex(ValueError, "nonempty version pin"):
            evaluation_dossier.validate_standards(
                [{"id": "probe", "class": "core", "versions": ["1", ""]}]
            )
        self.assertEqual(
            evaluation_dossier.validate_standards(
                [{"id": "probe", "class": "core", "versions": ["1", "2"]}]
            )[0]["versions"],
            ["1", "2"],
        )

    def test_standards_register_fields_fail_closed(self):
        for field in ("seag_standards_register", "status"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                for source in evaluation_dossier.SOURCE_PATHS:
                    target = root / source
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(ROOT / source, target)
                register_path = root / "standards.json"
                register = json.loads(register_path.read_text(encoding="utf-8"))
                register[field] = ""
                register_path.write_text(json.dumps(register), encoding="utf-8")
                with self.assertRaisesRegex(
                    ValueError, f"standards.json {field} must be a nonempty string"
                ):
                    evaluation_dossier.render(root)

    def test_reading_aid_discloses_no_deployable_capability_and_no_pilot_state(self):
        outputs = evaluation_dossier.render()
        for path in (evaluation_dossier.CONTEXT, evaluation_dossier.DOSSIER):
            text = outputs[path].decode("utf-8")
            self.assertIn("No capability is Level 5 Deployable", text)
            self.assertIn("project controlled", text)
            self.assertIn("single-maintainer", text.lower())
            self.assertNotIn("pilot is in progress", text)

    def test_check_binds_changed_source_into_the_manifest(self):
        baseline = json.loads(evaluation_dossier.render()[evaluation_dossier.MANIFEST])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for source in evaluation_dossier.SOURCE_PATHS:
                target = root / source
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / source, target)
            readme = root / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8") + "\n<!-- evaluation probe -->\n",
                encoding="utf-8",
            )
            changed_outputs = evaluation_dossier.render(root)
            changed = json.loads(changed_outputs[evaluation_dossier.MANIFEST])
            baseline_readme = next(
                item for item in baseline["sources"] if item["path"] == "README.md"
            )
            changed_readme = next(
                item for item in changed["sources"] if item["path"] == "README.md"
            )
            self.assertNotEqual(baseline_readme["sha256"], changed_readme["sha256"])
            self.assertIn("stale", "\n".join(evaluation_dossier.check(changed_outputs)))


if __name__ == "__main__":
    unittest.main()
