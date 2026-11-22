#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Enforce SEAG's exact, locked Python toolchain policy."""

from __future__ import annotations

from pathlib import Path
import re
import sys
import tomllib


ROOT = Path(__file__).resolve().parents[1]
EXACT_REQUIREMENT = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9._-]*(?:\[[A-Za-z0-9._,-]+\])?=="
    r"[A-Za-z0-9][A-Za-z0-9._+-]*"
)
EXPECTED_PYTHON = "3.14.8"
EXPECTED_UV = "==0.12.9"
EXPECTED_EXCLUDE_NEWER = "2026-11-22T23:59:59Z"


def check() -> list[str]:
    errors: list[str] = []
    try:
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
        return [f"cannot parse dependency policy input: {error}"]

    if project.get("project", {}).get("dependencies") != []:
        errors.append("project.dependencies must remain an explicit empty list")

    groups = project.get("dependency-groups")
    if not isinstance(groups, dict) or set(groups) != {"conformance"}:
        errors.append("dependency-groups must contain only conformance")
        requirements: list[object] = []
    else:
        requirements = groups["conformance"]
        if not isinstance(requirements, list):
            errors.append("dependency-groups.conformance must be a list")
            requirements = []
    for requirement in requirements:
        if not isinstance(requirement, str) or EXACT_REQUIREMENT.fullmatch(requirement) is None:
            errors.append(f"dependency is not an exact name==version pin: {requirement!r}")

    uv = project.get("tool", {}).get("uv", {})
    if uv.get("required-version") != EXPECTED_UV:
        errors.append(f"tool.uv.required-version must be {EXPECTED_UV!r}")
    if uv.get("package") is not False:
        errors.append("tool.uv.package must remain false")
    if uv.get("default-groups") != ["conformance"]:
        errors.append("tool.uv.default-groups must contain only conformance")
    if uv.get("exclude-newer") != EXPECTED_EXCLUDE_NEWER:
        errors.append(f"tool.uv.exclude-newer must be exactly {EXPECTED_EXCLUDE_NEWER}")

    try:
        python_version = (ROOT / ".python-version").read_text(encoding="ascii").strip()
    except (OSError, UnicodeError) as error:
        errors.append(f"cannot read .python-version: {error}")
    else:
        if python_version != EXPECTED_PYTHON:
            errors.append(f".python-version must be exactly {EXPECTED_PYTHON}")

    packages = lock.get("package")
    if not isinstance(packages, list) or not packages:
        errors.append("uv.lock contains no packages")
    else:
        for package in packages:
            if not isinstance(package, dict):
                errors.append("uv.lock contains a non-table package entry")
                continue
            name = package.get("name", "<unnamed>")
            if "version" not in package:
                errors.append(f"uv.lock package {name!r} has no exact version")
            source = package.get("source", {})
            if source.get("registry"):
                artifacts = ([package["sdist"]] if "sdist" in package else []) + package.get("wheels", [])
                if not artifacts:
                    errors.append(f"uv.lock registry package {name!r} has no hashed artifact")
                for artifact in artifacts:
                    digest = artifact.get("hash", "") if isinstance(artifact, dict) else ""
                    if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
                        errors.append(f"uv.lock package {name!r} has an unpinned artifact")
    return errors


def main() -> int:
    errors = check()
    if errors:
        print("dependency policy check: FAILED", file=sys.stderr)
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("dependency policy check: exact direct pins and locked artifacts passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
