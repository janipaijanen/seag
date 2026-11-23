# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "check-toolchain-publish-admission.py"
SPEC = importlib.util.spec_from_file_location("toolchain_publish_admission", SCRIPT)
admission = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(admission)


def digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


class ToolchainPublishAdmissionTests(unittest.TestCase):
    def environment(self):
        commit = "a" * 40
        return {
            "CI_COMMIT_SHA": commit,
            "CI_COMMIT_BRANCH": "main",
            "CI_DEFAULT_BRANCH": "main",
            "CI_COMMIT_REF_PROTECTED": "true",
            "CI_REGISTRY_IMAGE": "registry.gitlab.com/janipaijanen/seag",
            "CI_PIPELINE_ID": "123",
            "CI_JOB_ID": "456",
        }

    def proof(self, root: Path) -> Path:
        proof = root / "toolchain-proof"
        proof.mkdir()
        config_data = json.dumps(
            {"architecture": "amd64", "os": "linux"},
            separators=(",", ":"),
        ).encode()
        config_digest = digest(config_data)
        manifest_data = json.dumps(
            {
                "schemaVersion": 2,
                "config": {
                    "mediaType": "application/vnd.oci.image.config.v1+json",
                    "digest": config_digest,
                    "size": len(config_data),
                },
                "layers": [],
            },
            separators=(",", ":"),
        ).encode()
        manifest_digest = digest(manifest_data)
        index_data = json.dumps(
            {
                "schemaVersion": 2,
                "manifests": [
                    {
                        "mediaType": "application/vnd.oci.image.manifest.v1+json",
                        "digest": manifest_digest,
                        "size": len(manifest_data),
                        "platform": {"architecture": "amd64", "os": "linux"},
                    }
                ],
            },
            separators=(",", ":"),
        ).encode()
        members = [
            ("blobs", None),
            ("blobs/sha256", None),
            (f"blobs/sha256/{manifest_digest.removeprefix('sha256:')}", manifest_data),
            (f"blobs/sha256/{config_digest.removeprefix('sha256:')}", config_data),
            ("index.json", index_data),
            ("oci-layout", b'{"imageLayoutVersion":"1.0.0"}'),
        ]
        archive = proof / "seag-ci-toolchain.oci.tar"
        with tarfile.open(archive, "w:") as output:
            for name, content in members:
                info = tarfile.TarInfo(name)
                if content is None:
                    info.type = tarfile.DIRTYPE
                    info.size = 0
                    output.addfile(info)
                else:
                    info.size = len(content)
                    output.addfile(info, io.BytesIO(content))
        archive_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
        (proof / "SHA256SUMS").write_text(
            f"{archive_hash}  seag-ci-toolchain.oci.tar\n", encoding="ascii"
        )
        (proof / "oci-members.txt").write_text(
            "\n".join(name + "/" if content is None else name for name, content in members)
            + "\n",
            encoding="utf-8",
        )
        (proof / "build-metadata.json").write_text(
            json.dumps(
                {
                    "containerimage.config.digest": config_digest,
                    "containerimage.digest": manifest_digest,
                    "containerimage.descriptor": {
                        "digest": manifest_digest,
                        "platform": {"architecture": "amd64", "os": "linux"},
                    },
                }
            ),
            encoding="utf-8",
        )
        return proof

    def test_accepts_protected_default_branch_and_exact_oci_identity(self):
        environment = admission.validated_environment(self.environment())
        self.assertEqual("a" * 40, environment["commit"])
        self.assertEqual(
            "registry.gitlab.com/janipaijanen/seag/ci-toolchain:candidate-" + "a" * 40,
            environment["destination"],
        )
        with tempfile.TemporaryDirectory() as directory:
            proof = admission.validate_proof(self.proof(Path(directory)))
            self.assertRegex(proof["manifest_digest"], r"^sha256:[0-9a-f]{64}$")
            output = Path(directory) / "admission"
            admission.write_admission(output, environment, proof)
            record = json.loads((output / "admission.json").read_text())
            self.assertEqual(environment["destination"], record["destination"])
            self.assertEqual(proof["manifest_digest"], record["manifest_digest"])

    def test_rejects_unprotected_non_default_or_unpinned_context(self):
        for key, value in (
            ("CI_COMMIT_REF_PROTECTED", "false"),
            ("CI_COMMIT_BRANCH", "feature"),
            ("CI_COMMIT_SHA", "short"),
            ("CI_PIPELINE_ID", "1.0"),
        ):
            environment = self.environment()
            environment[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                admission.validated_environment(environment)

    def test_rejects_tampering_extra_files_and_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proof = self.proof(root)
            archive = proof / "seag-ci-toolchain.oci.tar"
            archive.write_bytes(archive.read_bytes() + b"tamper")
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                admission.validate_proof(proof)
        with tempfile.TemporaryDirectory() as directory:
            proof = self.proof(Path(directory))
            (proof / "unexpected").write_text("x")
            with self.assertRaisesRegex(ValueError, "exact required file set"):
                admission.validate_proof(proof)
        with tempfile.TemporaryDirectory() as directory:
            proof = self.proof(Path(directory))
            metadata = proof / "build-metadata.json"
            metadata.unlink()
            metadata.symlink_to("SHA256SUMS")
            with self.assertRaisesRegex(ValueError, "not a regular file"):
                admission.validate_proof(proof)

    def test_refuses_to_overwrite_admission_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "admission"
            output.mkdir()
            with self.assertRaisesRegex(ValueError, "must not already exist"):
                admission.write_admission(output, {}, {})

    def test_ci_keeps_build_admission_and_publication_separate(self):
        ci = (ROOT / ".gitlab-ci.yml").read_text(encoding="utf-8")
        publisher = ci.split("\ntoolchain-publish-candidate:", 1)[1]
        admission_job = ci.split("\ntoolchain-publish-admission:", 1)[1].split(
            "\ntag-authorization:", 1
        )[0]
        self.assertIn("toolchain-reproducibility-proof", admission_job)
        self.assertNotIn("CI_REGISTRY_PASSWORD", admission_job)
        self.assertIn("when: manual", publisher)
        self.assertIn("resource_group: seag-toolchain-publisher", publisher)
        self.assertIn("name: seag-toolchain-candidate", publisher)
        self.assertIn('test "${TOOLCHAIN_PUBLISH_COMMIT:-}" = "$CI_COMMIT_SHA"', publisher)
        self.assertIn("--preserve-digests", publisher)
        self.assertIn("candidate destination already exists", publisher)
        self.assertNotIn("latest", publisher)
        self.assertNotIn("docker login", publisher)


if __name__ == "__main__":
    unittest.main()
