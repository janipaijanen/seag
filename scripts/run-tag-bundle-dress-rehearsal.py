#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Run the credential-scrubbed local phase of the tag-path rehearsal."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import subprocess
import sys


ALLOWED_ENVIRONMENT = frozenset({"HOME", "LC_ALL", "PATH"})
TAGGER_ENVIRONMENT = {
    "GIT_COMMITTER_EMAIL": "rehearsal@example.invalid",
    "GIT_COMMITTER_NAME": "SEAG tag rehearsal",
}
COMMIT_RE = re.compile(r"[0-9a-f]{40}\Z")
BOUNDARY = (
    "DRESS REHEARSAL ONLY — NOT A RELEASE, REMOTE TAG, OR PUBLICATION ARTIFACT\n"
    "The authorization phase used ordinary CI job authority before this scrubbed "
    "local phase.\n"
    "This phase received only HOME, LC_ALL, and PATH; the annotated tag exists "
    "only in its disposable local clone.\n"
    "The bundle has release_status=candidate and publication_gate=not-asserted.\n"
)


def require_scrubbed_environment(environment: dict[str, str]) -> None:
    keys = frozenset(environment)
    if keys != ALLOWED_ENVIRONMENT:
        unexpected = sorted(keys - ALLOWED_ENVIRONMENT)
        missing = sorted(ALLOWED_ENVIRONMENT - keys)
        raise ValueError(
            f"local rehearsal environment mismatch; unexpected={unexpected!r}; "
            f"missing={missing!r}"
        )
    if environment["PATH"] != "/usr/local/bin:/usr/bin:/bin":
        raise ValueError("local rehearsal PATH is not the reviewed allowlist")
    if environment["LC_ALL"] != "C":
        raise ValueError("local rehearsal locale is not C")
    home = Path(environment["HOME"])
    if not home.is_absolute() or not home.is_dir() or home.is_symlink():
        raise ValueError("local rehearsal HOME must be an existing absolute directory")
    if any(home.iterdir()):
        raise ValueError("local rehearsal HOME must be empty")


def run(*arguments: str, cwd: Path | None = None, extra_env: dict[str, str] | None = None) -> str:
    environment = dict(os.environ)
    if extra_env:
        environment.update(extra_env)
    completed = subprocess.run(
        arguments,
        check=True,
        cwd=cwd,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    require_scrubbed_environment(dict(os.environ))
    if not COMMIT_RE.fullmatch(args.commit):
        raise ValueError("commit must be exactly 40 lowercase hexadecimal characters")

    if not args.source.is_absolute() or args.source.is_symlink():
        raise ValueError("source must be an absolute non-symlink path")
    if not args.output.is_absolute() or args.output.is_symlink():
        raise ValueError("output must be an absolute non-symlink path")
    source = args.source.resolve(strict=True)
    output = args.output.resolve(strict=True)
    if not source.is_dir():
        raise ValueError("source must be a real directory")
    if not output.is_dir():
        raise ValueError("output must be a real directory")

    repository = output / "repository"
    bundle = output / "bundle"
    tag_object = output / "local-tag-object.txt"
    boundary = output / "BOUNDARY.txt"
    for path in (repository, bundle, tag_object, boundary):
        if path.exists() or path.is_symlink():
            raise ValueError(f"refusing to overwrite rehearsal path: {path.name}")

    run("git", "clone", "--no-local", "--no-tags", str(source), str(repository))
    run("git", "checkout", "--detach", args.commit, cwd=repository)
    version = (repository / "VERSION").read_text(encoding="ascii").removesuffix("\n")
    if not version or "\n" in version or "\r" in version:
        raise ValueError("VERSION is not one canonical line")
    tag = f"v{version}"
    tag_date = run("git", "show", "-s", "--format=%cI", args.commit, cwd=repository).strip()
    run(
        "git",
        "tag",
        "-a",
        tag,
        args.commit,
        "-m",
        "local non-publishing tag-path rehearsal",
        cwd=repository,
        extra_env={**TAGGER_ENVIRONMENT, "GIT_COMMITTER_DATE": tag_date},
    )
    run(
        sys.executable,
        "scripts/build-release-bundle.py",
        "--commit",
        args.commit,
        "--check-tag",
        tag,
        "--output-dir",
        str(bundle),
        "--verify",
        cwd=repository,
    )
    resolved = run("git", "rev-parse", f"{tag}^{{commit}}", cwd=repository).strip()
    if resolved != args.commit:
        raise ValueError("local annotated tag does not identify the requested commit")
    tag_object.write_text(run("git", "cat-file", "-p", tag, cwd=repository), encoding="utf-8")
    boundary.write_text(BOUNDARY, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
