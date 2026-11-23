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
import os
import subprocess


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "check-toolchain-publish-admission.py"
PUBLISHER = ROOT / "scripts" / "publish-toolchain-candidate.sh"
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
                "layers": [
                    {
                        "mediaType": "application/vnd.oci.image.layer.v1.tar",
                        "digest": digest(b"layer"),
                        "size": len(b"layer"),
                    }
                ],
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
            (f"blobs/sha256/{digest(b'layer').removeprefix('sha256:')}", b"layer"),
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
            "registry.gitlab.com/janipaijanen/seag", environment["registry_image"]
        )
        with tempfile.TemporaryDirectory() as directory:
            proof = admission.validate_proof(self.proof(Path(directory)))
            self.assertRegex(proof["manifest_digest"], r"^sha256:[0-9a-f]{64}$")
            output = Path(directory) / "admission"
            admission.write_admission(output, environment, proof)
            record = json.loads((output / "admission.json").read_text())
            self.assertEqual(
                "registry.gitlab.com/janipaijanen/seag/ci-toolchain:candidate-"
                + "a" * 40
                + "-"
                + proof["manifest_digest"].removeprefix("sha256:"),
                record["destination"],
            )
            self.assertEqual(proof["manifest_digest"], record["manifest_digest"])
            self.assertEqual(
                proof["archive_sha256"],
                (output / "archive-sha256.txt").read_text().strip(),
            )

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

    def test_rejects_tampered_or_unreferenced_layer_blobs(self):
        with tempfile.TemporaryDirectory() as directory:
            proof = self.proof(Path(directory))
            archive = proof / "seag-ci-toolchain.oci.tar"
            with tarfile.open(archive, "a:") as output:
                info = tarfile.TarInfo("blobs/sha256/" + "f" * 64)
                info.size = 1
                output.addfile(info, io.BytesIO(b"x"))
            archive_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
            (proof / "SHA256SUMS").write_text(
                f"{archive_hash}  seag-ci-toolchain.oci.tar\n", encoding="ascii"
            )
            with tarfile.open(archive, "r:") as source:
                listing = [
                    member.name + "/" if member.isdir() else member.name
                    for member in source.getmembers()
                ]
            (proof / "oci-members.txt").write_text(
                "\n".join(listing) + "\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "unreferenced blobs"):
                admission.validate_proof(proof)

    def test_ci_keeps_build_admission_and_publication_separate(self):
        ci = (ROOT / ".gitlab-ci.yml").read_text(encoding="utf-8")
        publisher = ci.split("\ntoolchain-publish-candidate:", 1)[1]
        admission_job = ci.split("\ntoolchain-publish-admission:", 1)[1].split(
            "\ntag-authorization:", 1
        )[0]
        self.assertIn("toolchain-reproducibility-proof", admission_job)
        self.assertIn("- job: validate", admission_job)
        self.assertIn("artifacts: false", admission_job)
        self.assertIn("$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH", admission_job)
        self.assertIn('$CI_COMMIT_REF_PROTECTED == "true"', admission_job)
        self.assertNotIn("CI_REGISTRY_PASSWORD", admission_job)
        self.assertIn("when: manual", publisher)
        self.assertIn("- when: never", publisher)
        self.assertIn("- job: toolchain-publish-admission", publisher)
        self.assertIn("artifacts: true", publisher)
        self.assertIn("$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH", publisher)
        self.assertIn('$CI_COMMIT_REF_PROTECTED == "true"', publisher)
        self.assertIn("resource_group: seag-toolchain-publisher", publisher)
        self.assertIn("name: seag-toolchain-candidate", publisher)
        self.assertIn("scripts/publish-toolchain-candidate.sh", publisher)
        self.assertNotIn("latest", publisher)
        self.assertNotIn("docker login", publisher)
        rules_block = publisher.split("\n  rules:\n", 1)[1].split(
            "\n  script:\n", 1
        )[0]
        self.assertEqual(
            "    - if: '$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH && "
            '$CI_COMMIT_REF_PROTECTED == "true"' + "'\n"
            "      when: manual\n"
            "      allow_failure: true\n"
            "    - when: never",
            rules_block,
        )
        self.assertNotIn("merge_request_event", publisher)
        self.assertNotIn("CI_COMMIT_TAG", publisher)
        needs_block = publisher.split("\n  needs:\n", 1)[1].split(
            "\n  resource_group:", 1
        )[0]
        self.assertEqual(
            "    - job: toolchain-reproducibility-proof\n"
            "      artifacts: true\n"
            "    - job: toolchain-publish-admission\n"
            "      artifacts: true",
            needs_block,
        )

    def publisher_fixture(self, root: Path, mode: str) -> dict[str, str]:
        proof = root / "toolchain-proof"
        admission_dir = root / "toolchain-publish-admission"
        bin_dir = root / "bin"
        proof.mkdir()
        admission_dir.mkdir()
        bin_dir.mkdir()
        archive = proof / "seag-ci-toolchain.oci.tar"
        archive.write_bytes(b"exact archive")
        archive_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
        (proof / "SHA256SUMS").write_text(
            f"{archive_sha}  seag-ci-toolchain.oci.tar\n", encoding="ascii"
        )
        commit = "a" * 40
        raw_manifest = '{"schemaVersion":2,"mediaType":"test"}'
        manifest = digest(raw_manifest.encode("utf-8"))
        destination = "registry.example/seag/ci-toolchain:candidate-test"
        (admission_dir / "source-commit.txt").write_text(commit + "\n")
        (admission_dir / "archive-sha256.txt").write_text(archive_sha + "\n")
        (admission_dir / "manifest-digest.txt").write_text(manifest + "\n")
        (admission_dir / "destination.txt").write_text(destination + "\n")
        (admission_dir / "admission.json").write_text("{}\n")
        stub = bin_dir / "skopeo"
        stub.write_text(
            """#!/bin/sh
set -eu
command=$1
shift
printf '%s %s\n' "$command" "$*" >> "$SKOPEO_ARGS_MARKER"
case "$command" in
  login) cat >/dev/null; : > "$SKOPEO_LOGIN_MARKER" ;;
  copy) : > "$SKOPEO_COPY_MARKER" ;;
  inspect)
    if test -e "$SKOPEO_COPY_MARKER"; then
      printf '%s' "$SKOPEO_RAW_MANIFEST"
    elif test "$SKOPEO_MODE" = exists; then
      printf '%s' "$SKOPEO_RAW_MANIFEST"
    elif test "$SKOPEO_MODE" = missing; then
      echo 'time="2026-11-23T12:00:00Z" level=fatal msg="Error parsing image name \\"docker://registry.example/seag/ci-toolchain:candidate-test\\": reading manifest candidate-test in registry.example/seag/ci-toolchain: manifest unknown"' >&2; exit 1
    elif test "$SKOPEO_MODE" = name-missing; then
      echo 'Error parsing image name "docker://registry.example/seag/ci-toolchain:candidate-test": reading manifest candidate-test in registry.example/seag/ci-toolchain: name unknown: repository name not known to registry' >&2; exit 1
    elif test "$SKOPEO_MODE" = mixed; then
      echo 'Error parsing image name "docker://registry.example/seag/ci-toolchain:candidate-test": reading manifest: unauthorized: authentication required; manifest unknown' >&2; exit 1
    elif test "$SKOPEO_MODE" = other-resource; then
      echo 'Error parsing image name "docker://registry.example/seag/ci-toolchain:other": reading manifest: manifest unknown' >&2; exit 1
    elif test "$SKOPEO_MODE" = multiline; then
      echo 'warning: registry response was incomplete' >&2
      echo 'Error parsing image name "docker://registry.example/seag/ci-toolchain:candidate-test": reading manifest: manifest unknown' >&2; exit 1
    elif test "$SKOPEO_MODE" = auth; then
      echo 'unauthorized: authentication required' >&2; exit 1
    elif test "$SKOPEO_MODE" = server; then
      echo 'StatusCode: 500, internal server error' >&2; exit 1
    elif test "$SKOPEO_MODE" = rate; then
      echo 'StatusCode: 429, too many requests' >&2; exit 1
    else
      echo 'connection reset by peer' >&2; exit 1
    fi ;;
  *) exit 64 ;;
esac
""",
            encoding="utf-8",
        )
        stub.chmod(0o755)
        curl_stub = bin_dir / "curl"
        curl_stub.write_text(
            """#!/bin/sh
set -eu
printf '%s\n' "$*" >> "$CURL_ARGS_MARKER"
output=
headers=
bearer=false
netrc=false
url=
while test "$#" -gt 0; do
  case "$1" in
    --output|--dump-header|--header|--netrc-file|--data-urlencode|--write-out|--max-time|--max-redirs|--request)
      option=$1; value=$2; shift 2
      test "$option" = --output && output=$value
      test "$option" = --dump-header && headers=$value
      test "$option" = --netrc-file && netrc=true
      case "$option:$value" in --header:@*) bearer=true ;; esac
      ;;
    --silent|--show-error|--get) shift ;;
    *) url=$1; shift ;;
  esac
done
test -n "$output"
: > "$output"
test -z "$headers" || : > "$headers"
case "$url" in
  https://gitlab.example/jwt/auth)
    test "$netrc" = true
    if test "$SKOPEO_MODE" = auth; then
      printf '%s' '{"errors":[{"code":"DENIED"}]}' > "$output"
      printf 403
    elif test "$SKOPEO_MODE" = token-malformed; then
      printf '%s' '{"token":"header.payload.signature",THIS IS NOT JSON}' > "$output"
      printf 200
    elif test "$SKOPEO_MODE" = token-duplicate; then
      printf '%s' '{"token":"header.payload.signature","token":"other"}' > "$output"
      printf 200
    elif test "$SKOPEO_MODE" = token-nested; then
      printf '%s' '{"metadata":{"token":"header.payload.signature"}}' > "$output"
      printf 200
    elif test "$SKOPEO_MODE" = token-nonfinite; then
      printf '%s' '{"token":"header.payload.signature","expires_in":NaN}' > "$output"
      printf 200
    else
      printf '%s' '{"token":"header.payload.signature"}' > "$output"
      printf 200
    fi
    ;;
  https://registry.example/v2/*)
    if test "$bearer" = false; then
      printf '%s\r\n' 'HTTP/1.1 401 Unauthorized' \
        'WWW-Authenticate: Bearer realm="https://gitlab.example/jwt/auth",service="container_registry"' \
        > "$headers"
      printf '%s' '{"errors":[{"code":"UNAUTHORIZED"}]}' > "$output"
      printf 401
      exit 0
    fi
    case "$SKOPEO_MODE" in
      exists) printf '%s' "$SKOPEO_RAW_MANIFEST" > "$output"; printf 200 ;;
      missing) printf '%s' '{"errors":[{"code":"MANIFEST_UNKNOWN","message":"manifest unknown"}]}' > "$output"; printf 404 ;;
      name-missing) printf '%s' '{"errors":[{"code":"NAME_UNKNOWN","message":"repository name not known"}]}' > "$output"; printf 404 ;;
      mixed|multiline) printf '%s' '{"errors":[{"code":"MANIFEST_UNKNOWN"},{"code":"DENIED"}]}' > "$output"; printf 404 ;;
      other-resource) printf '%s' '{"errors":[{"code":"BLOB_UNKNOWN"}]}' > "$output"; printf 404 ;;
      malformed) printf '%s' 'not-json "code":"MANIFEST_UNKNOWN"' > "$output"; printf 404 ;;
      malformed-prefix) printf '%s' '{"errors":[{"code":"MANIFEST_UNKNOWN",THIS IS NOT JSON}]}' > "$output"; printf 404 ;;
      duplicate-code) printf '%s' '{"errors":[{"code":"MANIFEST_UNKNOWN","code":"NAME_UNKNOWN"}]}' > "$output"; printf 404 ;;
      duplicate-errors) printf '%s' '{"errors":[{"code":"MANIFEST_UNKNOWN"}],"errors":[{"code":"MANIFEST_UNKNOWN"}]}' > "$output"; printf 404 ;;
      nested-error) printf '%s' '{"errors":[{"code":"MANIFEST_UNKNOWN","detail":{"code":"DENIED"}}]}' > "$output"; printf 404 ;;
      nonfinite-nan) printf '%s' '{"errors":[{"code":"MANIFEST_UNKNOWN","detail":NaN}]}' > "$output"; printf 404 ;;
      nonfinite-infinity) printf '%s' '{"errors":[{"code":"MANIFEST_UNKNOWN","detail":{"value":Infinity}}]}' > "$output"; printf 404 ;;
      nonfinite-negative-infinity) printf '%s' '{"errors":[{"code":"MANIFEST_UNKNOWN","detail":[-Infinity]}]}' > "$output"; printf 404 ;;
      server) printf '%s' '{"errors":[{"code":"UNKNOWN"}]}' > "$output"; printf 500 ;;
      rate) printf '%s' '{"errors":[{"code":"TOOMANYREQUESTS"}]}' > "$output"; printf 429 ;;
      network) exit 7 ;;
      *) exit 64 ;;
    esac
    ;;
  *) exit 65 ;;
esac
""",
            encoding="utf-8",
        )
        curl_stub.chmod(0o755)
        return {
            **os.environ,
            "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
            "CI_COMMIT_SHA": commit,
            "CI_JOB_ID": "123",
            "CI_REGISTRY": "registry.example",
            "CI_REGISTRY_USER": "publisher",
            "CI_REGISTRY_PASSWORD": "secret",
            "CI_SERVER_URL": "https://gitlab.example",
            "CI_SERVER_HOST": "gitlab.example",
            "TOOLCHAIN_PUBLISH_COMMIT": commit,
            "SKOPEO_MODE": mode,
            "SKOPEO_MANIFEST": manifest,
            "SKOPEO_RAW_MANIFEST": raw_manifest,
            "SKOPEO_LOGIN_MARKER": str(root / "login-called"),
            "SKOPEO_COPY_MARKER": str(root / "copy-called"),
            "SKOPEO_ARGS_MARKER": str(root / "skopeo-arguments"),
            "CURL_ARGS_MARKER": str(root / "curl-arguments"),
        }

    def test_publisher_copies_only_after_definite_absence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            environment = self.publisher_fixture(root, "missing")
            result = subprocess.run(
                [str(PUBLISHER)], cwd=root, env=environment, capture_output=True, text=True
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertTrue((root / "copy-called").is_file())
            skopeo_calls = (root / "skopeo-arguments").read_text().splitlines()
            self.assertTrue(skopeo_calls[0].startswith("login "))
            self.assertTrue(skopeo_calls[1].startswith("copy "))
            self.assertIn("inspect --raw", skopeo_calls[2])
            curl_calls = (root / "curl-arguments").read_text()
            self.assertIn("/v2/seag/ci-toolchain/manifests/candidate-test", curl_calls)
            self.assertEqual(3, PUBLISHER.read_text().count("ulimit -f 128"))
            self.assertEqual(
                environment["SKOPEO_MANIFEST"],
                (root / "toolchain-publication/registry-manifest-digest.txt")
                .read_text()
                .strip(),
            )

    def test_publisher_never_copies_on_exists_auth_or_network_result(self):
        for mode, diagnostic in (
            ("exists", "candidate destination already exists"),
            ("auth", "candidate absence could not be established"),
            ("network", "candidate absence could not be established"),
            ("server", "candidate absence could not be established"),
            ("rate", "candidate absence could not be established"),
        ):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                environment = self.publisher_fixture(root, mode)
                result = subprocess.run(
                    [str(PUBLISHER)],
                    cwd=root,
                    env=environment,
                    capture_output=True,
                    text=True,
                )
                self.assertNotEqual(0, result.returncode)
                self.assertIn(diagnostic, result.stderr)
                self.assertFalse((root / "copy-called").exists())

    def test_publisher_accepts_real_name_unknown_for_exact_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            environment = self.publisher_fixture(root, "name-missing")
            result = subprocess.run(
                [str(PUBLISHER)], cwd=root, env=environment, capture_output=True, text=True
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertTrue((root / "copy-called").is_file())

    def test_publisher_rejects_mixed_multiline_and_other_resource_errors(self):
        for mode in (
            "mixed",
            "multiline",
            "other-resource",
            "malformed",
            "malformed-prefix",
            "duplicate-code",
            "duplicate-errors",
            "nested-error",
            "nonfinite-nan",
            "nonfinite-infinity",
            "nonfinite-negative-infinity",
        ):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                environment = self.publisher_fixture(root, mode)
                result = subprocess.run(
                    [str(PUBLISHER)], cwd=root, env=environment, capture_output=True, text=True
                )
                self.assertNotEqual(0, result.returncode)
                self.assertIn("candidate absence could not be established", result.stderr)
                self.assertFalse((root / "copy-called").exists())
                self.assertFalse((root / "login-called").exists())

    def test_publisher_rejects_malformed_ambiguous_and_nested_token_documents(self):
        for mode in ("token-malformed", "token-duplicate", "token-nested", "token-nonfinite"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                environment = self.publisher_fixture(root, mode)
                result = subprocess.run(
                    [str(PUBLISHER)], cwd=root, env=environment, capture_output=True, text=True
                )
                self.assertNotEqual(0, result.returncode)
                self.assertIn("candidate absence could not be established", result.stderr)
                self.assertFalse((root / "login-called").exists())
                self.assertFalse((root / "copy-called").exists())

    def test_publisher_never_sends_credentials_outside_ci_registry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            environment = self.publisher_fixture(root, "missing")
            (root / "toolchain-publish-admission/destination.txt").write_text(
                "evil.example/seag/ci-toolchain:candidate-test\n", encoding="utf-8"
            )
            result = subprocess.run(
                [str(PUBLISHER)], cwd=root, env=environment, capture_output=True, text=True
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn("outside CI_REGISTRY", result.stderr)
            self.assertFalse((root / "login-called").exists())
            self.assertFalse((root / "copy-called").exists())
            self.assertFalse((root / "curl-arguments").exists())


if __name__ == "__main__":
    unittest.main()
