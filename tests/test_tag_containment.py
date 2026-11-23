# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

import contextlib
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "tag_containment", ROOT / "scripts" / "check-tag-containment.py"
)
TAG_CONTAINMENT = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TAG_CONTAINMENT)


def result(returncode: int = 0, stdout: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(("git",), returncode, stdout, "")


class RemoteIdentityTests(unittest.TestCase):
    def test_accepts_gitlab_https_and_ssh_forms_without_credentials(self) -> None:
        expected = ("gitlab.example", "group/project")
        self.assertEqual(
            expected,
            TAG_CONTAINMENT.remote_identity(
                "https://gitlab-ci-token:secret@gitlab.example/group/project.git"
            ),
        )
        self.assertEqual(
            expected,
            TAG_CONTAINMENT.remote_identity("git@gitlab.example:group/project.git"),
        )

    def test_rejects_unsupported_local_remote(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported"):
            TAG_CONTAINMENT.remote_identity("/tmp/project.git")


class TagPolicyTests(unittest.TestCase):
    commit = "a" * 40

    def verify(self):
        return TAG_CONTAINMENT.verify(
            self.commit, "origin", "main", "gitlab.example", "group/project"
        )

    def test_rejects_option_shaped_remote_before_running_git(self) -> None:
        accepted, detail = TAG_CONTAINMENT.verify(
            self.commit, "--upload-pack=hostile", "main", "gitlab.example", "group/project"
        )
        self.assertFalse(accepted)
        self.assertIn("invalid name", detail)

    @patch.object(TAG_CONTAINMENT, "git")
    def test_records_fresh_observed_commit_after_containment(self, git_mock) -> None:
        observed = "b" * 40
        git_mock.side_effect = [
            result(stdout="https://gitlab.example/group/project.git\n"),
            result(),
            result(stdout=observed + "\n"),
            result(),
        ]
        self.assertEqual((True, observed), self.verify())
        self.assertIn("--no-tags", git_mock.call_args_list[1].args)
        self.assertIn(TAG_CONTAINMENT.POLICY_REF, git_mock.call_args_list[2].args[1])

    @patch.object(TAG_CONTAINMENT, "git")
    def test_fails_closed_when_remote_identity_differs(self, git_mock) -> None:
        git_mock.return_value = result(stdout="https://evil.example/group/project.git\n")
        accepted, detail = self.verify()
        self.assertFalse(accepted)
        self.assertIn("does not match", detail)
        git_mock.assert_called_once()

    @patch.object(TAG_CONTAINMENT, "git")
    def test_fails_closed_when_fresh_policy_fetch_fails(self, git_mock) -> None:
        git_mock.side_effect = [
            result(stdout="https://gitlab.example/group/project.git\n"),
            result(returncode=1),
        ]
        accepted, detail = self.verify()
        self.assertFalse(accepted)
        self.assertIn("fetch failed", detail)

    @patch.object(TAG_CONTAINMENT, "git")
    def test_fails_closed_when_tag_is_not_contained(self, git_mock) -> None:
        observed = "b" * 40
        git_mock.side_effect = [
            result(stdout="git@gitlab.example:group/project.git\n"),
            result(),
            result(stdout=observed + "\n"),
            result(returncode=1),
        ]
        accepted, detail = self.verify()
        self.assertFalse(accepted)
        self.assertIn("not contained", detail)


class RealGitTagPolicyTests(unittest.TestCase):
    def git(self, repository: Path, *arguments: str) -> str:
        completed = subprocess.run(
            ("git", "-C", str(repository), *arguments),
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return completed.stdout.strip()

    def test_real_fetch_rev_parse_and_containment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            remote = root / "remote.git"
            client = root / "client"
            source.mkdir()
            self.git(source, "init", "-b", "main")
            self.git(source, "config", "user.name", "SEAG test")
            self.git(source, "config", "user.email", "test@example.invalid")
            self.git(source, "commit", "--allow-empty", "-m", "main")
            main_commit = self.git(source, "rev-parse", "HEAD")
            self.git(root, "clone", "--bare", str(source), str(remote))

            client.mkdir()
            self.git(client, "init", "-b", "side")
            self.git(client, "config", "user.name", "SEAG test")
            self.git(client, "config", "user.email", "test@example.invalid")
            self.git(client, "commit", "--allow-empty", "-m", "unrelated")
            unrelated = self.git(client, "rev-parse", "HEAD")
            public_url = "https://gitlab.example/group/project.git"
            self.git(client, "remote", "add", "origin", public_url)
            self.git(
                client,
                "config",
                f"url.{remote.as_uri()}.insteadOf",
                public_url,
            )
            self.git(client, "config", "protocol.file.allow", "always")

            with contextlib.chdir(client):
                self.assertEqual(
                    (True, main_commit),
                    TAG_CONTAINMENT.verify(
                        main_commit,
                        "origin",
                        "main",
                        "gitlab.example",
                        "group/project",
                    ),
                )
                accepted, detail = TAG_CONTAINMENT.verify(
                    unrelated,
                    "origin",
                    "main",
                    "gitlab.example",
                    "group/project",
                )
            self.assertFalse(accepted)
            self.assertIn("not contained", detail)


if __name__ == "__main__":
    unittest.main()
