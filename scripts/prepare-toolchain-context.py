#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Fetch the reviewed SEAG CI toolchain closure and verify every byte."""

import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import urllib.parse
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "ci" / "toolchain" / "inputs.json"
OUTPUT = ROOT / "ci" / "toolchain" / "downloads"
ALLOWED_HOSTS = {"dl-cdn.alpinelinux.org", "files.pythonhosted.org"}


def main() -> int:
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if set(document) != {"format", "platform", "base", "artifacts"}:
        raise SystemExit("toolchain input manifest has unknown or missing fields")
    if document.get("format") != "seag-ci-toolchain-inputs-1":
        raise SystemExit("unsupported toolchain input manifest")
    if document.get("platform") != {"os": "linux", "architecture": "amd64"}:
        raise SystemExit("toolchain input manifest must target Linux/amd64")
    artifacts = document.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise SystemExit("toolchain input manifest has no artifacts")
    filenames: set[str] = set()
    for item in artifacts:
        if set(item) != {"kind", "name", "version", "filename", "url", "sha256"}:
            raise SystemExit("toolchain artifact has unknown or missing fields")
        if item["kind"] not in {"apk", "wheel"}:
            raise SystemExit("toolchain artifact kind is unsupported")
        if not all(
            isinstance(item[field], str) and item[field]
            for field in ("name", "version")
        ):
            raise SystemExit("toolchain artifact name and version must be nonempty strings")
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
    output_status = OUTPUT.lstat()
    if OUTPUT.is_symlink() or not stat.S_ISDIR(output_status.st_mode):
        raise SystemExit("toolchain download directory must be a real directory")
    expected = {item["filename"] for item in artifacts}
    unexpected = {path.name for path in OUTPUT.iterdir()} - expected
    if unexpected:
        raise SystemExit(f"unexpected toolchain inputs: {sorted(unexpected)!r}")
    for item in artifacts:
        destination = OUTPUT / item["filename"]
        temporary = destination.with_suffix(destination.suffix + ".part")
        if destination.exists() or destination.is_symlink():
            status = destination.lstat()
            if destination.is_symlink() or not stat.S_ISREG(status.st_mode):
                raise SystemExit(f"toolchain input is not a regular file: {item['filename']}")
            if digest(destination) != item["sha256"]:
                raise SystemExit(f"existing toolchain input has wrong SHA-256: {item['filename']}")
            print(f"verified {item['filename']} {item['sha256']}")
            continue
        if temporary.exists() or temporary.is_symlink():
            raise SystemExit(f"temporary toolchain input path already exists: {temporary.name}")
        value = hashlib.sha256()
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        flags |= getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(temporary, flags, 0o600)
        try:
            with urllib.request.urlopen(item["url"], timeout=60) as response, os.fdopen(
                descriptor, "wb"
            ) as handle:
                descriptor = -1
                for block in iter(lambda: response.read(1024 * 1024), b""):
                    value.update(block)
                    handle.write(block)
        except BaseException:
            if descriptor >= 0:
                os.close(descriptor)
            temporary.unlink(missing_ok=True)
            raise
        if value.hexdigest() != item["sha256"]:
            temporary.unlink(missing_ok=True)
            raise SystemExit(f"SHA-256 mismatch: {item['filename']}")
        os.replace(temporary, destination)
        print(f"verified {item['filename']} {item['sha256']}")
    return 0


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


if __name__ == "__main__":
    sys.exit(main())
