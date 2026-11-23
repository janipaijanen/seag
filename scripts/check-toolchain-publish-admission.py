#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Validate a reproduced OCI archive before a separate publisher sees credentials."""

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tarfile


DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
SHA = re.compile(r"[0-9a-f]{40}\Z")
CHECKSUM = re.compile(r"([0-9a-f]{64})  (seag-ci-toolchain\.oci\.tar)\n\Z")
REQUIRED = {
    "SHA256SUMS",
    "build-metadata.json",
    "oci-members.txt",
    "seag-ci-toolchain.oci.tar",
}


def strict_json(data: bytes):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON member: {key}")
            result[key] = value
        return result

    return json.loads(data.decode("utf-8"), object_pairs_hook=unique)


def sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validated_environment(environment: dict[str, str]) -> dict[str, str]:
    commit = environment.get("CI_COMMIT_SHA", "")
    branch = environment.get("CI_COMMIT_BRANCH", "")
    default = environment.get("CI_DEFAULT_BRANCH", "")
    registry_image = environment.get("CI_REGISTRY_IMAGE", "")
    if not SHA.fullmatch(commit):
        raise ValueError("CI_COMMIT_SHA must be a full lowercase Git SHA")
    if not branch or branch != default:
        raise ValueError("toolchain publication admission requires the default branch")
    if environment.get("CI_COMMIT_REF_PROTECTED") != "true":
        raise ValueError("toolchain publication admission requires a protected ref")
    if not re.fullmatch(r"[a-z0-9.-]+(?::[0-9]+)?/[A-Za-z0-9._/-]+", registry_image):
        raise ValueError("CI_REGISTRY_IMAGE has an unsupported form")
    for name in ("CI_PIPELINE_ID", "CI_JOB_ID"):
        if not environment.get(name, "").isdigit():
            raise ValueError(f"{name} must be decimal")
    return {
        "commit": commit,
        "destination": f"{registry_image}/ci-toolchain:candidate-{commit}",
        "job_id": environment["CI_JOB_ID"],
        "pipeline_id": environment["CI_PIPELINE_ID"],
    }


def validate_proof(directory: Path) -> dict[str, str]:
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("proof directory must be a real directory")
    entries = {path.name for path in directory.iterdir()}
    if entries != REQUIRED:
        raise ValueError("proof directory does not contain the exact required file set")
    for path in directory.iterdir():
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"proof member is not a regular file: {path.name}")

    checksum_text = (directory / "SHA256SUMS").read_text(encoding="ascii")
    match = CHECKSUM.fullmatch(checksum_text)
    if match is None:
        raise ValueError("SHA256SUMS is not the canonical single-file manifest")
    archive = directory / match.group(2)
    archive_sha256 = sha256_file(archive)
    if archive_sha256 != match.group(1):
        raise ValueError("OCI archive checksum mismatch")

    metadata = strict_json((directory / "build-metadata.json").read_bytes())
    expected_manifest = metadata.get("containerimage.digest")
    expected_config = metadata.get("containerimage.config.digest")
    descriptor = metadata.get("containerimage.descriptor")
    if not DIGEST.fullmatch(expected_manifest or "") or not DIGEST.fullmatch(expected_config or ""):
        raise ValueError("build metadata has an invalid manifest or config digest")
    if not isinstance(descriptor, dict) or descriptor.get("digest") != expected_manifest:
        raise ValueError("build descriptor does not match the manifest digest")
    if descriptor.get("platform") != {"architecture": "amd64", "os": "linux"}:
        raise ValueError("build descriptor is not Linux/amd64")

    with tarfile.open(archive, "r:") as oci:
        members = oci.getmembers()
        actual_names = [member.name for member in members]
        if len(actual_names) != len(set(actual_names)):
            raise ValueError("OCI archive contains duplicate member names")
        canonical_listing = [
            member.name + "/" if member.isdir() else member.name for member in members
        ]
        declared_names = (directory / "oci-members.txt").read_text(encoding="utf-8").splitlines()
        if canonical_listing != declared_names:
            raise ValueError("OCI member listing does not match the archive")
        for member in members:
            pure = PurePosixPath(member.name)
            if pure.is_absolute() or ".." in pure.parts or not (member.isfile() or member.isdir()):
                raise ValueError(f"unsafe OCI archive member: {member.name}")

        def bytes_for(name: str) -> bytes:
            selected = oci.getmember(name)
            stream = oci.extractfile(selected)
            if stream is None:
                raise ValueError(f"OCI member is not readable: {name}")
            return stream.read()

        index = strict_json(bytes_for("index.json"))
        manifests = index.get("manifests") if isinstance(index, dict) else None
        if not isinstance(manifests, list) or len(manifests) != 1:
            raise ValueError("OCI index must select exactly one manifest")
        if manifests[0].get("digest") != expected_manifest:
            raise ValueError("OCI index and build metadata disagree")
        if manifests[0].get("platform") != {"architecture": "amd64", "os": "linux"}:
            raise ValueError("OCI index is not Linux/amd64")
        manifest_data = bytes_for(f"blobs/sha256/{expected_manifest.removeprefix('sha256:')}")
        if sha256(manifest_data) != expected_manifest:
            raise ValueError("OCI manifest blob digest mismatch")
        manifest = strict_json(manifest_data)
        if manifest.get("config", {}).get("digest") != expected_config:
            raise ValueError("OCI manifest and config metadata disagree")
        config_data = bytes_for(f"blobs/sha256/{expected_config.removeprefix('sha256:')}")
        if sha256(config_data) != expected_config:
            raise ValueError("OCI config blob digest mismatch")
        config = strict_json(config_data)
        if (
            not isinstance(config, dict)
            or config.get("architecture") != "amd64"
            or config.get("os") != "linux"
        ):
            raise ValueError("OCI config is not Linux/amd64")

    return {
        "archive_sha256": archive_sha256,
        "config_digest": expected_config,
        "manifest_digest": expected_manifest,
    }


def write_admission(output: Path, environment: dict[str, str], proof: dict[str, str]) -> None:
    if output.exists() or output.is_symlink():
        raise ValueError("admission output must not already exist")
    output.mkdir(mode=0o755)
    record = {
        "schema": "seag/toolchain-publication-admission/v1",
        "source_commit": environment["commit"],
        "destination": environment["destination"],
        "pipeline_id": environment["pipeline_id"],
        "admission_job_id": environment["job_id"],
        **proof,
    }
    (output / "admission.json").write_text(
        json.dumps(record, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    for name, value in (
        ("destination.txt", environment["destination"]),
        ("manifest-digest.txt", proof["manifest_digest"]),
        ("source-commit.txt", environment["commit"]),
    ):
        (output / name).write_text(value + "\n", encoding="ascii")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proof-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    arguments = parser.parse_args()
    environment = validated_environment(dict(os.environ))
    proof = validate_proof(arguments.proof_dir)
    write_admission(arguments.output_dir, environment, proof)
    print("toolchain publication admission: verified non-publishing evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
