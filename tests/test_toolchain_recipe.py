# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

import hashlib
import json
from pathlib import Path
import unittest
import urllib.parse


ROOT = Path(__file__).parents[1]
TOOLCHAIN = ROOT / "ci" / "toolchain"


class ToolchainRecipeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(
            (TOOLCHAIN / "inputs.json").read_text(encoding="utf-8")
        )

    def test_platform_and_base_are_immutable_amd64(self):
        self.assertEqual({"os": "linux", "architecture": "amd64"}, self.manifest["platform"])
        base = self.manifest["base"]
        self.assertEqual("3.14.8", base["python"])
        self.assertRegex(base["reference"], r"@sha256:[0-9a-f]{64}$")
        self.assertRegex(base["index_digest"], r"^sha256:[0-9a-f]{64}$")
        self.assertRegex(base["config_digest"], r"^sha256:[0-9a-f]{64}$")
        containerfile = (TOOLCHAIN / "Containerfile").read_text(encoding="utf-8")
        self.assertIn(f"FROM {base['reference']}", containerfile)
        self.assertIn('test "$(uname -m)" = x86_64', containerfile)

    def test_closure_has_safe_unique_exact_inputs(self):
        artifacts = self.manifest["artifacts"]
        self.assertEqual(18, len(artifacts))
        self.assertEqual(18, len({item["filename"] for item in artifacts}))
        for item in artifacts:
            with self.subTest(item=item["filename"]):
                self.assertEqual(item["filename"], Path(item["filename"]).name)
                self.assertEqual(64, len(item["sha256"]))
                int(item["sha256"], 16)
                url = urllib.parse.urlsplit(item["url"])
                self.assertEqual("https", url.scheme)
                self.assertEqual(item["filename"], Path(url.path).name)
                self.assertFalse(url.query)
                self.assertFalse(url.fragment)

    def test_exact_primary_versions(self):
        versions = {item["name"]: item["version"] for item in self.manifest["artifacts"]}
        self.assertEqual("2.54.1-r0", versions["git"])
        self.assertEqual("0.12.9", versions["uv"])

    def test_recipe_installs_only_local_verified_payloads(self):
        recipe = (TOOLCHAIN / "Containerfile").read_text(encoding="utf-8")
        installer = (TOOLCHAIN / "install.py").read_text(encoding="utf-8")
        self.assertNotIn("http://", recipe)
        self.assertNotIn("https://", recipe)
        self.assertIn('"--no-network"', installer)
        self.assertIn('"query"', installer)
        self.assertIn('"installed"', installer)
        self.assertIn('"--no-index"', installer)
        self.assertIn('"--no-deps"', installer)
        self.assertIn('"CycloneDX"', installer)

    def test_downloaded_inputs_match_when_present(self):
        downloads = TOOLCHAIN / "downloads"
        if not downloads.exists():
            self.skipTest("candidate inputs have not been prepared")
        for item in self.manifest["artifacts"]:
            with self.subTest(item=item["filename"]):
                path = downloads / item["filename"]
                self.assertTrue(path.is_file())
                self.assertEqual(item["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
