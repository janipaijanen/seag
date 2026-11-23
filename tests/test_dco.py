# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Regression tests for prospective DCO trailer enforcement."""

from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "scripts" / "check-dco.py"


def run(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)


class DcoCheckTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name)
        self.assertEqual(0, run("git", "init", "-q", cwd=self.repo).returncode)
        run("git", "config", "user.name", "Example Contributor", cwd=self.repo)
        run("git", "config", "user.email", "example@example.com", cwd=self.repo)
        self.baseline = self.commit("baseline", signed=False)
        self.main_branch = run(
            "git", "branch", "--show-current", cwd=self.repo
        ).stdout.strip()

    def tearDown(self):
        self.temporary.cleanup()

    def commit(self, subject: str, *, signed: bool) -> str:
        marker = self.repo / "history.txt"
        marker.write_text(marker.read_text() + subject + "\n" if marker.exists() else subject + "\n")
        run("git", "add", "history.txt", cwd=self.repo)
        command = ["git", "commit", "-q", "-m", subject]
        if signed:
            command.insert(2, "--signoff")
        result = run(*command, cwd=self.repo)
        self.assertEqual(0, result.returncode, result.stderr)
        return run("git", "rev-parse", "HEAD", cwd=self.repo).stdout.strip()

    def check(self, revision: str = "HEAD") -> subprocess.CompletedProcess[str]:
        return run(
            "python3",
            str(CHECK),
            "--baseline",
            self.baseline,
            "--revision",
            revision,
            cwd=self.repo,
        )

    def test_accepts_signed_commit_after_unsigned_baseline(self):
        self.commit("certified", signed=True)
        result = self.check()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("1 post-transition commit", result.stdout)

    def test_rejects_unsigned_commit_after_baseline(self):
        commit = self.commit("uncertified", signed=False)
        result = self.check()
        self.assertEqual(1, result.returncode)
        self.assertIn(commit, result.stderr)

    def test_accepts_unsigned_merge_that_reuses_certified_parent_tree(self):
        run("git", "checkout", "-q", "-b", "feature", cwd=self.repo)
        self.commit("certified feature", signed=True)
        run("git", "checkout", "-q", self.main_branch, cwd=self.repo)
        merge = run(
            "git", "merge", "--no-ff", "-m", "host-generated merge", "feature",
            cwd=self.repo,
        )
        self.assertEqual(0, merge.returncode, merge.stderr)
        result = self.check()
        self.assertEqual(0, result.returncode, result.stderr)

    def test_rejects_unsigned_merge_whose_tree_matches_no_parent(self):
        run("git", "checkout", "-q", "-b", "feature", cwd=self.repo)
        self.commit("certified feature", signed=True)
        run("git", "checkout", "-q", self.main_branch, cwd=self.repo)
        marker = self.repo / "main.txt"
        marker.write_text("main\n")
        run("git", "add", "main.txt", cwd=self.repo)
        commit = run("git", "commit", "-q", "--signoff", "-m", "certified main", cwd=self.repo)
        self.assertEqual(0, commit.returncode, commit.stderr)
        merge = run(
            "git", "merge", "--no-ff", "-m", "content-combining merge", "feature",
            cwd=self.repo,
        )
        self.assertEqual(0, merge.returncode, merge.stderr)
        merge_commit = run("git", "rev-parse", "HEAD", cwd=self.repo).stdout.strip()
        result = self.check()
        self.assertEqual(1, result.returncode)
        self.assertIn(merge_commit, result.stderr)

    def test_fails_closed_when_baseline_is_unavailable(self):
        result = run(
            "python3",
            str(CHECK),
            "--baseline",
            "0" * 40,
            cwd=self.repo,
        )
        self.assertEqual(1, result.returncode)
        self.assertIn("baseline commit is unavailable", result.stderr)

    def test_rejects_revision_outside_baseline_history(self):
        run("git", "checkout", "-q", "--orphan", "unrelated", cwd=self.repo)
        run("git", "rm", "-q", "-rf", ".", cwd=self.repo)
        revision = self.commit("unrelated", signed=True)
        result = self.check(revision)
        self.assertEqual(1, result.returncode)
        self.assertIn("is not a descendant", result.stderr)


if __name__ == "__main__":
    unittest.main()
