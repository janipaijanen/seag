# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

import importlib.util
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).parents[1] / "scripts" / "build-release-bundle.py"
SPEC = importlib.util.spec_from_file_location("release_bundle", SCRIPT)
release_bundle = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(release_bundle)


class ReleaseBundleTests(unittest.TestCase):
    def test_version_and_tag_match(self):
        version = release_bundle.package_version("HEAD")
        commit = subprocess.check_output(("git", "rev-parse", "HEAD"), text=True).strip()
        with patch.object(release_bundle, "package_version", return_value=version), patch.object(
            release_bundle,
            "git",
            side_effect=("tag", f"object {commit}\ntype commit\ntag v{version}\n\nrelease", commit),
        ):
            self.assertEqual(release_bundle.check_tag(f"v{version}", "HEAD"), version)
        with self.assertRaises(ValueError):
            release_bundle.check_tag("v9.9.9", "HEAD")

    def test_rejects_lightweight_or_wrong_commit_tag(self):
        version = release_bundle.package_version("HEAD")
        commit = subprocess.check_output(("git", "rev-parse", "HEAD"), text=True).strip()
        with patch.object(release_bundle, "package_version", return_value=version), patch.object(
            release_bundle, "git", return_value="commit"
        ):
            with self.assertRaisesRegex(ValueError, "annotated tag"):
                release_bundle.check_tag(f"v{version}", "HEAD")
        with patch.object(release_bundle, "package_version", return_value=version), patch.object(
            release_bundle,
            "git",
            side_effect=("tag", f"object {'a' * 40}\ntype commit\ntag v{version}\n\nrelease", commit),
        ):
            with self.assertRaisesRegex(ValueError, "does not directly identify commit"):
                release_bundle.check_tag(f"v{version}", "HEAD")
        with patch.object(release_bundle, "package_version", return_value=version), patch.object(
            release_bundle,
            "git",
            side_effect=("tag", f"object {'a' * 40}\ntype tag\ntag v{version}\n\nrelease", commit),
        ):
            with self.assertRaisesRegex(ValueError, "directly identify a commit"):
                release_bundle.check_tag(f"v{version}", "HEAD")

    def test_rejects_unsafe_version(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):
                release_bundle.build("../escape", "HEAD", Path(temporary))

    def test_current_commit_build_is_reproducible_and_verifiable(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            archive_a, checksum_a, provenance_a = release_bundle.build("0.0.0-test.1", "HEAD", Path(first))
            archive_b, _checksum_b, _provenance_b = release_bundle.build("0.0.0-test.1", "HEAD", Path(second))
            self.assertEqual(archive_a.read_bytes(), archive_b.read_bytes())
            release_bundle.verify_archive(archive_a)
            digest, filename = checksum_a.read_text().strip().split("  ")
            self.assertEqual(filename, archive_a.name)
            self.assertEqual(digest, release_bundle.sha256(archive_a.read_bytes()))
            provenance = json.loads(provenance_a.read_text())
            commit = subprocess.check_output(("git", "rev-parse", "HEAD"), text=True).strip()
            tree = subprocess.check_output(("git", "rev-parse", "HEAD^{tree}"), text=True).strip()
            self.assertEqual(provenance["subject"]["sha256"], digest)
            self.assertEqual(provenance["source_commit"], commit)
            self.assertEqual(provenance["source_tree"], tree)
            self.assertEqual(provenance["release_status"], "candidate")
            self.assertEqual(provenance["publication_gate"], "not-asserted")
            with tarfile.open(archive_a, "r:gz") as archive:
                names = archive.getnames()
                manifest_name = next(name for name in names if name.endswith("/RELEASE-MANIFEST.json"))
                manifest = json.load(archive.extractfile(manifest_name))
            self.assertEqual(manifest["release_status"], "candidate")
            self.assertEqual(manifest["publication_gate"], "not-asserted")
            self.assertEqual(manifest["source_commit"], commit)
            self.assertEqual(manifest["source_tree"], tree)
            self.assertTrue(any(name.endswith("/RELEASE-MANIFEST.json") for name in names))
            self.assertFalse(any(name.endswith("/.gitlab-ci.yml") for name in names))

    def test_default_version_comes_from_version_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            archive, _checksum, _provenance = release_bundle.build(None, "HEAD", Path(temporary))
            self.assertEqual(archive.name, f"seag-{release_bundle.package_version('HEAD')}.tar.gz")

    def test_stable_bundle_records_asserted_gate(self):
        with tempfile.TemporaryDirectory() as temporary:
            archive, _checksum, provenance_path = release_bundle.build(
                None, "HEAD", Path(temporary), "stable", "asserted"
            )
            provenance = json.loads(provenance_path.read_text())
            self.assertEqual(provenance["release_status"], "stable")
            self.assertEqual(provenance["publication_gate"], "asserted")
            with tarfile.open(archive, "r:gz") as source:
                name = next(item for item in source.getnames() if item.endswith("/RELEASE-MANIFEST.json"))
                manifest = json.load(source.extractfile(name))
            self.assertEqual(manifest["release_status"], "stable")
            self.assertEqual(manifest["publication_gate"], "asserted")

    def test_rejects_inconsistent_release_assertions(self):
        with tempfile.TemporaryDirectory() as temporary:
            for status, gate in (("stable", "not-asserted"), ("candidate", "asserted")):
                with self.subTest(status=status, gate=gate):
                    with self.assertRaises(ValueError):
                        release_bundle.build(None, "HEAD", Path(temporary), status, gate)


if __name__ == "__main__":
    unittest.main()

