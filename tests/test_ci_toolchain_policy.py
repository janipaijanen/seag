# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import importlib.util
import re
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CI_PATH = ROOT / ".gitlab-ci.yml"
TOOLCHAIN_DIGEST = (
    "registry.gitlab.com/janipaijanen/seag/ci-toolchain@"
    "sha256:b427405058274309921ce6cf8e8e0cedc278bba492da46152c208222eb55a632"
)
REHEARSAL_PATH = ROOT / "scripts" / "run-tag-bundle-dress-rehearsal.py"
REHEARSAL_SPEC = importlib.util.spec_from_file_location(
    "run_tag_bundle_dress_rehearsal", REHEARSAL_PATH
)
rehearsal_module = importlib.util.module_from_spec(REHEARSAL_SPEC)
assert REHEARSAL_SPEC.loader is not None
REHEARSAL_SPEC.loader.exec_module(rehearsal_module)


class CiToolchainPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ci = CI_PATH.read_text(encoding="utf-8")
        cls.default = cls.ci.split("\ndefault:\n", 1)[1].split("\nvalidate:\n", 1)[0]

    def test_general_consumers_use_only_the_accepted_manifest_digest(self) -> None:
        self.assertIn(f"  image: {TOOLCHAIN_DIGEST}\n", self.default)
        self.assertNotIn("candidate-", self.default)
        self.assertIn("@sha256:", self.default.split("  before_script:", 1)[0])
        self.assertNotIn("$", self.default.split("  before_script:", 1)[0])

    def test_general_consumers_observe_exact_primary_versions(self) -> None:
        self.assertIn('test "$(python --version)" = "Python 3.14.8"', self.default)
        self.assertIn('test "$(git --version)" = "git version 2.54.1"', self.default)
        self.assertIn(
            'test "$(uv --version)" = '
            '"uv 0.12.9 (x86_64-unknown-linux-musl)"',
            self.default,
        )
        self.assertIn("python scripts/check-dependency-policy.py", self.default)
        self.assertIn("uv lock --check", self.default)
        self.assertIn("uv sync --locked --only-group conformance", self.default)

    def test_ci_has_no_runtime_package_manager_bootstrap(self) -> None:
        prohibited = (
            r"\bapk\s+add\b",
            r"\bpip(?:3)?\s+install\b",
            r"python\s+-m\s+pip\s+install\b",
            r"curl[^\n|]*\|\s*(?:sh|bash)\b",
        )
        for pattern in prohibited:
            with self.subTest(pattern=pattern):
                self.assertIsNone(re.search(pattern, self.ci, flags=re.IGNORECASE))

    def test_producer_and_publisher_images_remain_explicit_and_separate(self) -> None:
        self.assertIn(
            "name: python:3.14.8-alpine@sha256:"
            "f6a589d43c42b9e7f7dc67a12d37132491f362859a5d750607710cc56da3bc72",
            self.ci,
        )
        self.assertIn(
            "name: moby/buildkit@sha256:"
            "7d02292556e66feea6d2d89b7ec143503b57e4f59a4efc6b7ece8547e4d3e5be",
            self.ci,
        )
        self.assertIn(
            "name: quay.io/containers/aio@sha256:"
            "24796f148f8f78dc842ccd1a58552aa79dbf537cb248f604168089b7f1d91be3",
            self.ci,
        )
        self.assertEqual(1, self.ci.count(TOOLCHAIN_DIGEST))

    def test_tag_dress_rehearsal_is_local_non_publishing_and_retained(self) -> None:
        rehearsal = self.ci.split("\ntag-bundle-dress-rehearsal:\n", 1)[1].split(
            "\nrelease-candidate-bundle:\n", 1
        )[0]
        self.assertIn("CI_COMMIT_REF_PROTECTED", rehearsal)
        self.assertIn('test -z "${CI_COMMIT_TAG:-}"', rehearsal)
        self.assertIn("scripts/check-tag-containment.py", rehearsal)
        self.assertIn("tag-authorization.txt", rehearsal)
        self.assertIn("env -i", rehearsal)
        self.assertIn("PATH=/usr/local/bin:/usr/bin:/bin", rehearsal)
        self.assertIn('HOME="$CI_PROJECT_DIR/tag-dress-rehearsal/empty-home"', rehearsal)
        self.assertIn("LC_ALL=C", rehearsal)
        self.assertIn("scripts/run-tag-bundle-dress-rehearsal.py", rehearsal)
        self.assertIn("local-tag-object.txt", rehearsal)
        self.assertNotRegex(rehearsal, r"\bgit\s+push\b")
        self.assertNotIn("publish-toolchain", rehearsal)
        self.assertNotIn("release-cli", rehearsal)

    def test_local_rehearsal_script_enforces_the_exact_environment_allowlist(self) -> None:
        self.assertEqual(
            frozenset({"HOME", "LC_ALL", "PATH"}),
            rehearsal_module.ALLOWED_ENVIRONMENT,
        )
        self.assertEqual(
            {
                "GIT_COMMITTER_EMAIL": "rehearsal@example.invalid",
                "GIT_COMMITTER_NAME": "SEAG tag rehearsal",
            },
            rehearsal_module.TAGGER_ENVIRONMENT,
        )
        with tempfile.TemporaryDirectory() as directory:
            accepted = {
                "HOME": directory,
                "LC_ALL": "C",
                "PATH": "/usr/local/bin:/usr/bin:/bin",
            }
            rehearsal_module.require_scrubbed_environment(accepted)
            with self.assertRaisesRegex(ValueError, "unexpected=.*CI_JOB_TOKEN"):
                rehearsal_module.require_scrubbed_environment(
                    {**accepted, "CI_JOB_TOKEN": "secret"}
                )
            with self.assertRaisesRegex(ValueError, "PATH"):
                rehearsal_module.require_scrubbed_environment(
                    {**accepted, "PATH": "/unreviewed"}
                )

    def test_local_rehearsal_script_contains_no_remote_or_publication_operation(self) -> None:
        source = REHEARSAL_PATH.read_text(encoding="utf-8")
        self.assertIn('"clone", "--no-local", "--no-tags"', source)
        self.assertIn('"--check-tag"', source)
        self.assertIn("publication_gate=not-asserted", source)
        self.assertNotRegex(source, r"\bpush\b")
        self.assertNotIn("publish-toolchain", source)
        self.assertNotIn("CI_REGISTRY", source)


if __name__ == "__main__":
    unittest.main()
