#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Enforce DCO sign-off trailers after SEAG's documented transition baseline."""

import argparse
import re
import subprocess
import sys


HISTORICAL_BASELINE = "a2fee6e32b1bdcbcb78bb36791ce3910ae0d1d29"
SIGN_OFF = re.compile(r"^Signed-off-by:\s+.+\s+<[^<>\s]+@[^<>\s]+>\s*$", re.I)


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", *args), capture_output=True, text=True, check=False
    )


def commit_message(commit: str) -> str:
    result = git("show", "-s", "--format=%B", commit)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"cannot read commit {commit}")
    return result.stdout


def parsed_trailers(message: str) -> list[str]:
    result = subprocess.run(
        ("git", "interpret-trailers", "--parse"),
        input=message,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "cannot parse commit trailers")
    return result.stdout.splitlines()


def has_sign_off(commit: str) -> bool:
    return any(SIGN_OFF.fullmatch(line) for line in parsed_trailers(commit_message(commit)))


def is_content_neutral_merge(commit: str) -> bool:
    """Return whether a merge reuses one parent's tree without changing it."""

    result = git("show", "-s", "--format=%T %P", commit)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"cannot inspect commit {commit}")
    values = result.stdout.split()
    if len(values) < 3:
        return False
    tree, *parents = values
    for parent in parents:
        parent_result = git("show", "-s", "--format=%T", parent)
        if parent_result.returncode:
            raise RuntimeError(
                parent_result.stderr.strip() or f"cannot inspect parent {parent}"
            )
        if parent_result.stdout.strip() == tree:
            return True
    return False


def commits_after(baseline: str, revision: str) -> list[str]:
    for value, label in ((baseline, "baseline"), (revision, "revision")):
        result = git("rev-parse", "--verify", f"{value}^{{commit}}")
        if result.returncode:
            raise RuntimeError(f"DCO {label} commit is unavailable: {value}")

    ancestry = git("merge-base", "--is-ancestor", baseline, revision)
    if ancestry.returncode == 1:
        raise RuntimeError(f"DCO revision {revision} is not a descendant of {baseline}")
    if ancestry.returncode:
        raise RuntimeError(ancestry.stderr.strip() or "cannot check DCO ancestry")

    result = git("rev-list", "--reverse", "--topo-order", f"{baseline}..{revision}")
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "cannot enumerate commits")
    return result.stdout.splitlines()


def check(baseline: str, revision: str) -> list[str]:
    return [
        commit
        for commit in commits_after(baseline, revision)
        if not has_sign_off(commit) and not is_content_neutral_merge(commit)
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", default=HISTORICAL_BASELINE)
    parser.add_argument("--revision", default="HEAD")
    args = parser.parse_args()

    try:
        commits = commits_after(args.baseline, args.revision)
        failures = [
            commit
            for commit in commits
            if not has_sign_off(commit) and not is_content_neutral_merge(commit)
        ]
    except RuntimeError as error:
        print(f"DCO check: FAILED: {error}", file=sys.stderr)
        return 1

    if failures:
        print("DCO check: FAILED: commits without valid Signed-off-by trailers", file=sys.stderr)
        for commit in failures:
            subject = git("show", "-s", "--format=%s", commit).stdout.strip()
            print(f"{commit} {subject}", file=sys.stderr)
        return 1

    print(f"DCO check: {len(commits)} post-transition commit(s) certified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
