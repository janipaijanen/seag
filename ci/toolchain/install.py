#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Verify and install the offline SEAG CI toolchain closure."""

import hashlib
import json
from pathlib import Path
import platform
import subprocess


ROOT = Path("/usr/local/share/seag-toolchain")
DOWNLOADS = Path("/tmp/seag-toolchain-inputs")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main() -> None:
    manifest = json.loads((ROOT / "inputs.json").read_text(encoding="utf-8"))
    if platform.machine() != "x86_64":
        raise SystemExit("toolchain input closure is Linux/amd64 only")
    artifacts = manifest["artifacts"]
    expected = {item["filename"] for item in artifacts}
    actual = {path.name for path in DOWNLOADS.iterdir() if path.is_file()}
    if actual != expected:
        raise SystemExit("toolchain input set does not exactly match the manifest")
    for item in artifacts:
        path = DOWNLOADS / item["filename"]
        if digest(path) != item["sha256"]:
            raise SystemExit(f"SHA-256 mismatch: {item['filename']}")

    apks = [str(DOWNLOADS / item["filename"]) for item in artifacts if item["kind"] == "apk"]
    wheel = next(DOWNLOADS / item["filename"] for item in artifacts if item["kind"] == "wheel")
    subprocess.run(
        (
            "apk",
            "add",
            "--no-network",
            "--no-cache",
            "--repositories-file",
            "/dev/null",
            *apks,
        ),
        check=True,
        env={"PATH": "/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin", "APK_NO_NETWORK": "1"},
    )
    subprocess.run(
        ("python", "-m", "pip", "install", "--no-index", "--no-deps", str(wheel)),
        check=True,
    )

    inventory = {
        "format": "seag-ci-toolchain-inventory-1",
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "git": subprocess.check_output(("git", "--version"), text=True).strip(),
        "uv": subprocess.check_output(("uv", "--version"), text=True).strip(),
        "apk": sorted(
            subprocess.check_output(
                ("apk", "info", "--installed"),
                text=True,
                env={"PATH": "/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin", "APK_NO_NETWORK": "1"},
            ).splitlines()
        ),
        "inputs": artifacts,
    }
    (ROOT / "inventory.json").write_text(
        json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    components = [
        {
            "type": "library",
            "name": item["name"],
            "version": item["version"],
            "hashes": [{"alg": "SHA-256", "content": item["sha256"]}],
            "externalReferences": [{"type": "distribution", "url": item["url"]}],
            "properties": [{"name": "seag:artifact-kind", "value": item["kind"]}],
        }
        for item in artifacts
    ]
    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "version": 1,
        "components": components,
    }
    (ROOT / "sbom.cdx.json").write_text(
        json.dumps(sbom, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
