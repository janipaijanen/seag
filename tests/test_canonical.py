# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Canonical source rendering and no-overwrite behavior."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from seag.canonical import is_canonical, render, write
from seag.semantic_diff import compare
from seag.validate import validate


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "fixtures" / "valid" / "manifest.json"


class CanonicalSourceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_render_is_deterministic_and_orders_records(self):
        first = render(MANIFEST)
        second = render(MANIFEST)
        self.assertEqual(first, second)
        fragment = json.loads(first[2]["fragment.json"])
        identifiers = [record["id"] for record in fragment["records"]]
        self.assertEqual(sorted(identifiers), identifiers)
        self.assertFalse(is_canonical(MANIFEST))

    def test_written_copy_validates_and_has_no_semantic_change(self):
        output_manifest = write(MANIFEST, self.root / "canonical")
        self.assertEqual([], validate(output_manifest))
        self.assertTrue(is_canonical(output_manifest))
        self.assertEqual([], compare(MANIFEST, output_manifest)["changes"])

    def test_two_outputs_are_byte_identical(self):
        first = write(MANIFEST, self.root / "first").parent
        second = write(MANIFEST, self.root / "second").parent
        first_files = {path.relative_to(first): path.read_bytes() for path in first.rglob("*") if path.is_file()}
        second_files = {path.relative_to(second): path.read_bytes() for path in second.rglob("*") if path.is_file()}
        self.assertEqual(first_files, second_files)

    def test_existing_output_is_never_overwritten(self):
        output = self.root / "existing"
        output.mkdir()
        marker = output / "owned.txt"
        marker.write_text("preserve")
        with self.assertRaisesRegex(ValueError, "already exists"):
            write(MANIFEST, output)
        self.assertEqual("preserve", marker.read_text())

    def test_invalid_input_creates_no_output(self):
        invalid = self.root / "invalid.json"
        invalid.write_text("{}")
        output = self.root / "output"
        with self.assertRaisesRegex(ValueError, "invalid SEAG bundle"):
            write(invalid, output)
        self.assertFalse(output.exists())

    @unittest.skipUnless(hasattr(os, "mkfifo"), "named pipes are unavailable")
    def test_fifo_fragment_is_rejected_without_blocking(self):
        bundle = self.root / "fifo-bundle"
        bundle.mkdir()
        shutil.copyfile(MANIFEST, bundle / "manifest.json")
        os.mkfifo(bundle / "fragment.json")
        result = subprocess.run(
            (
                sys.executable,
                "-m",
                "seag.canonical",
                str(bundle / "manifest.json"),
                "--check",
            ),
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("invalid SEAG bundle", result.stderr)

    def test_cli_check_exit_codes(self):
        noncanonical = subprocess.run(
            (sys.executable, "-m", "seag.canonical", str(MANIFEST), "--check"),
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(1, noncanonical.returncode)
        output = self.root / "canonical"
        created = subprocess.run(
            (sys.executable, "-m", "seag.canonical", str(MANIFEST), "--output-dir", str(output)),
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, created.returncode, created.stderr)
        canonical = subprocess.run(
            (sys.executable, "-m", "seag.canonical", str(output / "manifest.json"), "--check"),
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, canonical.returncode, canonical.stderr)


if __name__ == "__main__":
    unittest.main()
