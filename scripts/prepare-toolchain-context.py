#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Fetch the reviewed SEAG CI toolchain closure and verify every byte."""

import hashlib
import json
from pathlib import Path
import sys
import urllib.parse
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "ci" / "toolchain" / "inputs.json"
OUTPUT = ROOT / "ci" / "toolchain" / "downloads"
ALLOWED_HOSTS = {"dl-cdn.alpinelinux.org", "files.pythonhosted.org"}


def main() -> int:
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if document.get("format") != "seag-ci-toolchain-inputs-1":
        raise SystemExit("unsupported toolchain input manifest")
    artifacts = document.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise SystemExit("toolchain input manifest has no artifacts")
    filenames: set[str] = set()
    for item in artifacts:
        filename = item.get("filename")
        checksum = item.get("sha256")
        if not isinstance(filename, str) or Path(filename).name != filename:
            raise SystemExit("toolchain input filename must be one safe basename")
        if filename in filenames:
            raise SystemExit(f"duplicate toolchain input filename: {filename}")
        filenames.add(filename)
        if (
            not isinstance(checksum, str)
            or len(checksum) != 64
            or any(character not in "0123456789abcdef" for character in checksum)
        ):
            raise SystemExit(f"invalid SHA-256: {filename}")
        split_url = urllib.parse.urlsplit(item.get("url", ""))
        if (
            split_url.scheme != "https"
            or split_url.hostname not in ALLOWED_HOSTS
            or Path(split_url.path).name != filename
            or split_url.query
            or split_url.fragment
        ):
            raise SystemExit(f"unapproved toolchain input URL: {item.get('url')}")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    expected = {item["filename"] for item in artifacts}
    unexpected = {path.name for path in OUTPUT.iterdir()} - expected
    if unexpected:
        raise SystemExit(f"unexpected toolchain inputs: {sorted(unexpected)!r}")
    for item in artifacts:
        destination = OUTPUT / item["filename"]
        temporary = destination.with_suffix(destination.suffix + ".part")
        value = hashlib.sha256()
        with urllib.request.urlopen(item["url"], timeout=60) as response, temporary.open("wb") as handle:
            for block in iter(lambda: response.read(1024 * 1024), b""):
                value.update(block)
                handle.write(block)
        if value.hexdigest() != item["sha256"]:
            temporary.unlink(missing_ok=True)
            raise SystemExit(f"SHA-256 mismatch: {item['filename']}")
        temporary.replace(destination)
        print(f"verified {item['filename']} {item['sha256']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
