import importlib.util
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts" / "build-release-bundle.py"
SPEC = importlib.util.spec_from_file_location("release_bundle", SCRIPT)
release_bundle = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(release_bundle)


class ReleaseBundleTests(unittest.TestCase):
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
            self.assertEqual(provenance["subject"]["sha256"], digest)
            self.assertEqual(provenance["publication_gate"], "not-asserted")
            with tarfile.open(archive_a, "r:gz") as archive:
                names = archive.getnames()
            self.assertTrue(any(name.endswith("/RELEASE-MANIFEST.json") for name in names))
            self.assertFalse(any(name.endswith("/.gitlab-ci.yml") for name in names))


if __name__ == "__main__":
    unittest.main()

