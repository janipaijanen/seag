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
import sys
import tarfile
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from seag.validation import strict_json_loads


VERSION_RE = re.compile(
    r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-(?:0|[1-9][0-9]*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9][0-9]*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?\Z"
)
EXCLUDED = {".gitlab-ci.yml"}
EXCLUDED_PREFIXES = ("dist/",)


def git(*args: str, text: bool = True) -> str | bytes:
    return subprocess.check_output(("git", *args), text=text)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def package_version(commitish: str = "HEAD") -> str:
    version = git("show", f"{commitish}:VERSION").strip()
    if not VERSION_RE.fullmatch(version):
        raise ValueError(f"VERSION is not valid Semantic Versioning: {version!r}")
    return version


def check_tag(tag: str, commitish: str = "HEAD") -> str:
    version = package_version(commitish)
    expected = f"v{version}"
    if tag != expected:
        raise ValueError(f"tag {tag!r} does not match VERSION {version!r}; expected {expected!r}")
    ref = f"refs/tags/{tag}"
    try:
        object_type = git("cat-file", "-t", ref).strip()
        tag_object = git("cat-file", "-p", ref)
        requested_commit = git("rev-parse", f"{commitish}^{{commit}}").strip()
    except subprocess.CalledProcessError as error:
        raise ValueError(f"tag {tag!r} is unavailable") from error
    if object_type != "tag":
        raise ValueError(f"tag {tag!r} must be an annotated tag object")
    headers = {}
    for line in tag_object.splitlines():
        if not line:
            break
        key, separator, value = line.partition(" ")
        if separator:
            headers[key] = value
    if headers.get("type") != "commit":
        raise ValueError(f"tag {tag!r} must directly identify a commit object")
    if headers.get("object") != requested_commit:
        raise ValueError(f"tag {tag!r} does not directly identify commit {requested_commit}")
    return version


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


def build(
    version: str | None,
    commitish: str,
    output_dir: Path,
    release_status: str = "candidate",
    publication_gate: str = "not-asserted",
) -> tuple[Path, Path, Path]:
    version = version or package_version(commitish)
    if not VERSION_RE.fullmatch(version):
        raise ValueError(f"invalid release version: {version!r}")
    if release_status not in {"candidate", "stable"}:
        raise ValueError(f"invalid release status: {release_status!r}")
    if publication_gate not in {"not-asserted", "asserted"}:
        raise ValueError(f"invalid publication gate state: {publication_gate!r}")
    if (release_status, publication_gate) not in {
        ("candidate", "not-asserted"),
        ("stable", "asserted"),
    }:
        raise ValueError("stable status and asserted publication gate must be selected together")
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
        "release_status": release_status,
        "publication_gate": publication_gate,
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
                "release_status": release_status,
                "publication_gate": publication_gate,
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
        manifest = strict_json_loads(extracted.read())
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
    parser.add_argument("--version")
    parser.add_argument("--commit", default="HEAD")
    parser.add_argument("--output-dir", type=Path, default=Path("dist"))
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--check-tag")
    parser.add_argument("--release-status", choices=("candidate", "stable"), default="candidate")
    parser.add_argument("--publication-gate", choices=("not-asserted", "asserted"), default="not-asserted")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.release_status == "stable" and not args.check_tag:
            raise ValueError("stable bundles require --check-tag with an annotated release tag")
        if args.check_tag:
            check_tag(args.check_tag, args.commit)
        archive, checksum, provenance = build(
            args.version,
            args.commit,
            args.output_dir,
            args.release_status,
            args.publication_gate,
        )
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if args.verify:
        verify_archive(archive)
    print(archive)
    print(checksum)
    print(provenance)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

