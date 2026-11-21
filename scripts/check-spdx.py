#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Check SPDX copyright and licence declarations on tracked SEAG files."""

from pathlib import Path
import subprocess
import sys


COPYRIGHT = "SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen"
LICENCE_PREFIX = "SPDX-License-Identifier: "
ALLOWED_LICENCES = {"Apache-2.0", "CC-BY-4.0"}


def tracked_files() -> list[Path]:
    output = subprocess.check_output(("git", "ls-files", "-z"))
    return [Path(item.decode("utf-8")) for item in output.split(b"\0") if item]


def declaration(path: Path) -> str:
    sidecar = path.with_name(path.name + ".license")
    source = sidecar if sidecar.is_file() else path
    text = source.read_text(encoding="utf-8")
    return text if source == sidecar else "\n".join(text.splitlines()[:12])


def main() -> int:
    errors: list[str] = []
    files = tracked_files()
    for path in files:
        if path.parts and path.parts[0] == "LICENSES":
            continue
        if path.name.endswith(".license"):
            continue
        try:
            text = declaration(path)
        except UnicodeDecodeError:
            errors.append(f"{path}: binary file requires an SPDX .license sidecar")
            continue
        if COPYRIGHT not in text:
            errors.append(f"{path}: missing exact SPDX copyright declaration")
        licences = {
            line.split(LICENCE_PREFIX, 1)[1].strip().rstrip(" -->")
            for line in text.splitlines()
            if LICENCE_PREFIX in line
        }
        if len(licences) != 1:
            errors.append(f"{path}: expected exactly one SPDX licence declaration")
        elif not licences <= ALLOWED_LICENCES:
            errors.append(f"{path}: unsupported SPDX licence expression {licences.pop()!r}")
    for licence in sorted(ALLOWED_LICENCES):
        if not Path(f"LICENSES/{licence}.txt").is_file():
            errors.append(f"missing canonical licence text: LICENSES/{licence}.txt")
    if errors:
        print("SPDX check: FAILED", file=sys.stderr)
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"SPDX check: {len(files)} tracked files covered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
