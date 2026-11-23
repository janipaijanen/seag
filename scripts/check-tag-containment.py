#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Verify a tag commit against fresh default-branch policy state."""

import argparse
import re
import subprocess
from urllib.parse import urlsplit


FULL_SHA = re.compile(r"[0-9a-f]{40}\Z")
POLICY_REF = "refs/seag-policy/default"


def remote_identity(value: str) -> tuple[str, str]:
    if "://" in value:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https", "ssh"} or not parsed.hostname:
            raise ValueError("unsupported Git remote URL")
        host = parsed.hostname.casefold()
        path = parsed.path.lstrip("/")
    else:
        match = re.fullmatch(r"(?:[^@/:]+@)?([^/:]+):(.+)", value)
        if not match:
            raise ValueError("unsupported Git remote URL")
        host, path = match.groups()
        host = host.casefold()
    if path.endswith(".git"):
        path = path[:-4]
    if not path or any(character in path for character in "\r\n\0"):
        raise ValueError("invalid Git remote project path")
    return host, path


def git(*arguments: str, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", *arguments),
        check=False,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def verify(
    commit: str, remote: str, branch: str, server_host: str, project_path: str
) -> tuple[bool, str]:
    if not FULL_SHA.fullmatch(commit):
        return False, "commit must be a full lowercase Git SHA"
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", remote):
        return False, "policy remote has an invalid name"
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", branch) or ".." in branch:
        return False, "default branch has an invalid name"
    if not server_host or not project_path:
        return False, "expected GitLab project identity is incomplete"

    configured = git("config", "--get", f"remote.{remote}.url", capture=True)
    if configured.returncode:
        return False, "cannot resolve the configured policy remote"
    try:
        identity = remote_identity(configured.stdout.strip())
    except ValueError as error:
        return False, str(error)
    if identity != (server_host.casefold(), project_path):
        return False, "policy remote does not match the expected GitLab project"

    fetched = git(
        "fetch",
        "--no-tags",
        "--force",
        remote,
        f"+refs/heads/{branch}:{POLICY_REF}",
    )
    if fetched.returncode:
        return False, "fresh default-branch policy fetch failed"
    observed = git("rev-parse", f"{POLICY_REF}^{{commit}}", capture=True)
    observed_sha = observed.stdout.strip()
    if observed.returncode or not FULL_SHA.fullmatch(observed_sha):
        return False, "fetched policy state is not an unambiguous commit"
    ancestry = git("merge-base", "--is-ancestor", commit, observed_sha)
    if ancestry.returncode:
        return False, f"tag commit is not contained in observed default branch {observed_sha}"
    return True, observed_sha


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", required=True)
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--branch", required=True)
    parser.add_argument("--server-host", required=True)
    parser.add_argument("--project-path", required=True)
    arguments = parser.parse_args()
    accepted, detail = verify(
        arguments.commit,
        arguments.remote,
        arguments.branch,
        arguments.server_host,
        arguments.project_path,
    )
    if not accepted:
        print(f"tag authorization: DENIED: {detail}")
        return 1
    print(f"tag authorization: accepted; observed default-branch commit {detail}")
    print("this is live publication-policy evidence, not a reproducible build input")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
