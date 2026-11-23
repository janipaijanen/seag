# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import urllib.parse


ROOT = Path(__file__).parents[1]
TOOLCHAIN = ROOT / "ci" / "toolchain"
PREPARER_PATH = ROOT / "scripts" / "prepare-toolchain-context.py"
SPEC = importlib.util.spec_from_file_location("prepare_toolchain_context", PREPARER_PATH)
preparer = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(preparer)


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
                self.assertIs(type(item["size"]), int)
                self.assertGreater(item["size"], 0)
                url = urllib.parse.urlsplit(item["url"])
                self.assertEqual("https", url.scheme)
                self.assertEqual(item["filename"], Path(url.path).name)
                self.assertFalse(url.query)
                self.assertFalse(url.fragment)

    def test_exact_primary_versions(self):
        versions = {item["name"]: item["version"] for item in self.manifest["artifacts"]}
        self.assertEqual("2.54.1-r0", versions["git"])
        self.assertEqual("0.12.9", versions["uv"])

    def test_source_date_epoch_is_canonical_and_reviewed(self):
        value = (TOOLCHAIN / "SOURCE_DATE_EPOCH").read_text(encoding="ascii")
        self.assertEqual("1795432630\n", value)
        self.assertEqual(1795432630, int(value))

    def test_ci_proof_is_reproducible_and_non_publishing(self):
        ci = (ROOT / ".gitlab-ci.yml").read_text(encoding="utf-8")
        proof = ci.split("# Non-publishing proof", 1)[1].split("\ntag-authorization:", 1)[0]
        self.assertIn('SOURCE_DATE_EPOCH="$(cat ci/toolchain/SOURCE_DATE_EPOCH)"', proof)
        self.assertIn("rewrite-timestamp=true,compatibility-version=30", proof)
        self.assertIn("toolchain-build-proof-a:", proof)
        self.assertIn("toolchain-build-proof-b:", proof)
        self.assertIn("cmp toolchain-proof-a/seag-ci-toolchain.oci.tar", proof)
        self.assertIn('context_dir="$CI_PROJECT_DIR/toolchain-build-context"', proof)
        self.assertIn('test ! -e "$context_dir/.git"', proof)
        self.assertIn('--local context="$context_dir"', proof)
        self.assertNotIn('--local context="$CI_PROJECT_DIR"', proof)
        self.assertIn("--oci-worker-no-process-sandbox", proof)
        self.assertNotIn("docker login", proof)
        self.assertNotIn("push=true", proof)

    def test_ci_context_is_an_explicit_non_symlink_allowlist(self):
        ci = (ROOT / ".gitlab-ci.yml").read_text(encoding="utf-8")
        proof = ci.split("# Non-publishing proof", 1)[1].split(
            "\ntag-authorization:", 1
        )[0]
        self.assertIn(
            'cp ci/toolchain/inputs.json ci/toolchain/install.py "$context_dir/ci/toolchain/"',
            proof,
        )
        self.assertIn(
            'for path in ci/toolchain/downloads/*; do test -f "$path" -a ! -L "$path" || exit 1;',
            proof,
        )
        self.assertIn(
            'cp "$path" "$context_dir/ci/toolchain/downloads/" || exit 1;', proof
        )
        self.assertIn('chmod -R a-w "$context_dir"', proof)
        self.assertIn(
            'find "$context_dir" ! -type d ! -type f -print -quit', proof
        )
        self.assertNotIn('cp -R "$CI_PROJECT_DIR"', proof)

    def test_recipe_installs_only_local_verified_payloads(self):
        recipe = (TOOLCHAIN / "Containerfile").read_text(encoding="utf-8")
        installer = (TOOLCHAIN / "install.py").read_text(encoding="utf-8")
        self.assertNotIn("http://", recipe)
        self.assertNotIn("https://", recipe)
        self.assertNotIn("ARG ", recipe)
        self.assertNotIn("--mount=type=secret", recipe)
        self.assertIn("RUN --network=none", recipe)
        self.assertIn('"--no-network"', installer)
        self.assertIn('"query"', installer)
        self.assertIn('"installed"', installer)
        self.assertIn('"--no-index"', installer)
        self.assertIn('"--no-deps"', installer)
        self.assertIn('"--no-compile"', installer)
        self.assertIn('Path("/var/log/apk.log").unlink(missing_ok=True)', installer)
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

    def test_preparer_rejects_symlinked_destination_before_network(self):
        artifact = self.manifest["artifacts"][0]
        document = {
            **self.manifest,
            "artifacts": [artifact],
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "inputs.json"
            manifest.write_text(json.dumps(document), encoding="utf-8")
            downloads = root / "downloads"
            downloads.mkdir()
            outside = root / "outside"
            outside.write_bytes(b"do not overwrite")
            (downloads / artifact["filename"]).symlink_to(outside)
            with (
                mock.patch.object(preparer, "MANIFEST", manifest),
                mock.patch.object(preparer, "OUTPUT", downloads),
                mock.patch.object(preparer.urllib.request, "urlopen") as opener,
                self.assertRaisesRegex(SystemExit, "not a regular file"),
            ):
                preparer.main()
            opener.assert_not_called()
            self.assertEqual(b"do not overwrite", outside.read_bytes())

    @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "O_NOFOLLOW unavailable")
    def test_preparer_uses_no_follow_exclusive_temporary_file(self):
        source = PREPARER_PATH.read_text(encoding="utf-8")
        self.assertIn("os.O_EXCL", source)
        self.assertIn('getattr(os, "O_NOFOLLOW", 0)', source)

    def test_preparer_rejects_redirect_outside_allowlist(self):
        artifact = {**self.manifest["artifacts"][0], "size": 1}
        document = {**self.manifest, "artifacts": [artifact]}
        response = io.BytesIO(b"x")
        response.geturl = lambda: f"https://example.invalid/{artifact['filename']}"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "inputs.json"
            manifest.write_text(json.dumps(document), encoding="utf-8")
            downloads = root / "downloads"
            with (
                mock.patch.object(preparer, "MANIFEST", manifest),
                mock.patch.object(preparer, "OUTPUT", downloads),
                mock.patch.object(
                    preparer.urllib.request, "urlopen", return_value=response
                ),
                self.assertRaisesRegex(SystemExit, "unapproved toolchain input URL"),
            ):
                preparer.main()
            self.assertEqual([], list(downloads.iterdir()))

    def test_preparer_stops_stream_above_exact_size(self):
        artifact = {**self.manifest["artifacts"][0], "size": 1}
        document = {**self.manifest, "artifacts": [artifact]}
        response = io.BytesIO(b"xx")
        response.geturl = lambda: artifact["url"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "inputs.json"
            manifest.write_text(json.dumps(document), encoding="utf-8")
            downloads = root / "downloads"
            with (
                mock.patch.object(preparer, "MANIFEST", manifest),
                mock.patch.object(preparer, "OUTPUT", downloads),
                mock.patch.object(
                    preparer.urllib.request, "urlopen", return_value=response
                ),
                self.assertRaisesRegex(SystemExit, "exceeds declared size"),
            ):
                preparer.main()
            self.assertEqual([], list(downloads.iterdir()))

    def test_preparer_rejects_short_stream(self):
        artifact = {**self.manifest["artifacts"][0], "size": 2}
        document = {**self.manifest, "artifacts": [artifact]}
        response = io.BytesIO(b"x")
        response.geturl = lambda: artifact["url"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "inputs.json"
            manifest.write_text(json.dumps(document), encoding="utf-8")
            downloads = root / "downloads"
            with (
                mock.patch.object(preparer, "MANIFEST", manifest),
                mock.patch.object(preparer, "OUTPUT", downloads),
                mock.patch.object(
                    preparer.urllib.request, "urlopen", return_value=response
                ),
                self.assertRaisesRegex(SystemExit, "wrong final size"),
            ):
                preparer.main()
            self.assertEqual([], list(downloads.iterdir()))

    def test_preparer_rejects_existing_regular_file_with_wrong_size(self):
        artifact = self.manifest["artifacts"][0]
        document = {**self.manifest, "artifacts": [artifact]}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "inputs.json"
            manifest.write_text(json.dumps(document), encoding="utf-8")
            downloads = root / "downloads"
            downloads.mkdir()
            (downloads / artifact["filename"]).write_bytes(b"wrong")
            with (
                mock.patch.object(preparer, "MANIFEST", manifest),
                mock.patch.object(preparer, "OUTPUT", downloads),
                mock.patch.object(preparer.urllib.request, "urlopen") as opener,
                self.assertRaisesRegex(SystemExit, "wrong size"),
            ):
                preparer.main()
            opener.assert_not_called()


if __name__ == "__main__":
    unittest.main()
