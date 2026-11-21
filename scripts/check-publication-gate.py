#!/usr/bin/env python3
"""Fail closed until the SEAG public-release prerequisites are present."""

from pathlib import Path
import sys


REQUIRED_FILES = (
    "LICENSES/Apache-2.0.txt",
    "LICENSES/CC-BY-4.0.txt",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "docs/release-policy.md",
)


def main() -> int:
    missing = [path for path in REQUIRED_FILES if not Path(path).is_file()]
    if missing:
        print("publication gate: CLOSED", file=sys.stderr)
        for path in missing:
            print(f"missing required file: {path}", file=sys.stderr)
        return 1
    print("publication gate file prerequisites: present")
    print("independent review evidence still requires a release-specific CI check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

