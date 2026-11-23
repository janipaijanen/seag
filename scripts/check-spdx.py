#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Check SPDX copyright and licence declarations on tracked SEAG files."""

from pathlib import Path
import subprocess
import sys


# REUSE-IgnoreStart
COPYRIGHT_PREFIX = "SPDX-FileCopyrightText:"
LICENCE_PREFIX = "SPDX-License-Identifier: "
# REUSE-IgnoreEnd
ALLOWED_LICENCES = {"Apache-2.0", "CC-BY-4.0"}
ROOT_LICENCE_COPIES = {
    Path("LICENSE"): Path("LICENSES/Apache-2.0.txt"),
    Path("LICENSE-DOCS"): Path("LICENSES/CC-BY-4.0.txt"),
}


def tracked_files() -> list[Path]:
    output = subprocess.check_output(("git", "ls-files", "-z"))
    return [Path(item.decode("utf-8")) for item in output.split(b"\0") if item]


def declaration(path: Path) -> str:
    sidecar = path.with_name(path.name + ".license")
    source = sidecar if sidecar.is_file() else path
    text = source.read_text(encoding="utf-8")
    return text if source == sidecar else "\n".join(text.splitlines()[:12])


def copyright_declarations(text: str) -> list[str]:
    """Return nonempty SPDX copyright values without prescribing ownership."""
    return [
        line.split(COPYRIGHT_PREFIX, 1)[1].strip().rstrip(" -->")
        for line in text.splitlines()
        if COPYRIGHT_PREFIX in line
        and line.split(COPYRIGHT_PREFIX, 1)[1].strip().rstrip(" -->")
    ]


def main() -> int:
    errors: list[str] = []
    files = tracked_files()
    for path in files:
        if (path.parts and path.parts[0] == "LICENSES") or path in ROOT_LICENCE_COPIES:
            continue
        if path.name.endswith(".license"):
            continue
        try:
            text = declaration(path)
        except UnicodeDecodeError:
            errors.append(f"{path}: binary file requires an SPDX .license sidecar")
            continue
        if not copyright_declarations(text):
            errors.append(f"{path}: missing nonempty SPDX copyright declaration")
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
    for root_copy, canonical in ROOT_LICENCE_COPIES.items():
        if not root_copy.is_file():
            errors.append(f"missing root licence copy: {root_copy}")
        elif root_copy.read_bytes() != canonical.read_bytes():
            errors.append(f"{root_copy}: differs from canonical text {canonical}")
    if errors:
        print("SPDX check: FAILED", file=sys.stderr)
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"SPDX check: {len(files)} tracked files covered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
