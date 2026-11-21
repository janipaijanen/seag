#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Build a reproducible SEAG source release-candidate bundle."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile
import tempfile


VERSION_RE = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?\Z")
EXCLUDED = {".gitlab-ci.yml"}
EXCLUDED_PREFIXES = ("dist/",)


def git(*args: str, text: bool = True) -> str | bytes:
    return subprocess.check_output(("git", *args), text=text)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_entries(commit: str) -> list[tuple[str, int, bytes, str]]:
    raw = git("ls-tree", "-rz", "--full-tree", commit, text=False)
    entries: list[tuple[str, int, bytes, str]] = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, encoded_path = record.split(b"\t", 1)
        mode, kind, object_id = metadata.decode("ascii").split()
        path = encoded_path.decode("utf-8")
        if path in EXCLUDED or path.startswith(EXCLUDED_PREFIXES):
            continue
        if kind != "blob":
            raise ValueError(f"unsupported Git entry {kind!r}: {path!r}")
        if mode not in {"100644", "100755"}:
            raise ValueError(f"unsupported Git mode {mode!r}: {path!r}")
        pure = PurePosixPath(path)
        if pure.is_absolute() or ".." in pure.parts:
            raise ValueError(f"unsafe source path: {path!r}")
        data = git("cat-file", "blob", object_id, text=False)
        file_mode = 0o755 if mode == "100755" else 0o644
        entries.append((path, file_mode, data, object_id))
    return sorted(entries)


def tar_info(name: str, mode: int, size: int, epoch: int) -> tarfile.TarInfo:
    info = tarfile.TarInfo(name)
    info.mode = mode
    info.size = size
    info.mtime = epoch
    info.uid = 0
    info.gid = 0
    info.uname = "root"
    info.gname = "root"
    return info


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def build(version: str, commitish: str, output_dir: Path) -> tuple[Path, Path, Path]:
    if not VERSION_RE.fullmatch(version):
        raise ValueError(f"invalid release version: {version!r}")
    commit = git("rev-parse", "--verify", f"{commitish}^{{commit}}").strip()
    epoch = int(git("show", "-s", "--format=%ct", commit).strip())
    entries = source_entries(commit)
    prefix = f"seag-{version}"
    source_files = [
        {
            "path": path,
            "bytes": len(data),
            "sha256": sha256(data),
            "git_object": object_id,
        }
        for path, _mode, data, object_id in entries
    ]
    manifest = {
        "format": "seag/source-release-manifest/v1",
        "name": "seag",
        "version": version,
        "source_commit": commit,
        "source_date_epoch": epoch,
        "release_status": "candidate",
        "files": source_files,
    }
    manifest_bytes = canonical_json(manifest)

    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / f"{prefix}.tar.gz"
    with archive.open("wb") as raw_output:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_output, mtime=epoch) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as tar:
                directory = tar_info(prefix + "/", 0o755, 0, epoch)
                directory.type = tarfile.DIRTYPE
                tar.addfile(directory)
                for path, mode, data, _object_id in entries:
                    info = tar_info(f"{prefix}/{path}", mode, len(data), epoch)
                    tar.addfile(info, io.BytesIO(data))
                manifest_path = f"{prefix}/RELEASE-MANIFEST.json"
                info = tar_info(manifest_path, 0o644, len(manifest_bytes), epoch)
                tar.addfile(info, io.BytesIO(manifest_bytes))

    archive_digest = sha256(archive.read_bytes())
    checksum = output_dir / f"{archive.name}.sha256"
    checksum.write_text(f"{archive_digest}  {archive.name}\n")
    provenance = output_dir / f"{prefix}.provenance.json"
    provenance.write_bytes(
        canonical_json(
            {
                "format": "seag/release-build-provenance/v1",
                "subject": {"path": archive.name, "sha256": archive_digest},
                "source_commit": commit,
                "source_date_epoch": epoch,
                "builder": "scripts/build-release-bundle.py",
                "builder_digest": next(
                    item["sha256"] for item in source_files
                    if item["path"] == "scripts/build-release-bundle.py"
                ),
                "reproducible": True,
                "publication_gate": "not-asserted",
            }
        )
    )
    return archive, checksum, provenance


def verify_archive(archive: Path) -> None:
    with tarfile.open(archive, "r:gz") as tar:
        members = tar.getmembers()
        names = [member.name for member in members]
        if any(PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts for name in names):
            raise ValueError("archive contains an unsafe path")
        manifest_members = [member for member in members if member.name.endswith("/RELEASE-MANIFEST.json")]
        if len(manifest_members) != 1:
            raise ValueError("archive must contain exactly one release manifest")
        extracted = tar.extractfile(manifest_members[0])
        if extracted is None:
            raise ValueError("release manifest is not a regular file")
        manifest = json.load(extracted)
        prefix = manifest_members[0].name.removesuffix("RELEASE-MANIFEST.json")
        by_name = {member.name: member for member in members}
        for expected in manifest["files"]:
            member = by_name.get(prefix + expected["path"])
            if member is None or not member.isfile():
                raise ValueError(f"missing bundled file: {expected['path']}")
            stream = tar.extractfile(member)
            if stream is None or sha256(stream.read()) != expected["sha256"]:
                raise ValueError(f"digest mismatch: {expected['path']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--commit", default="HEAD")
    parser.add_argument("--output-dir", type=Path, default=Path("dist"))
    parser.add_argument("--verify", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    archive, checksum, provenance = build(args.version, args.commit, args.output_dir)
    if args.verify:
        verify_archive(archive)
    print(archive)
    print(checksum)
    print(provenance)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

