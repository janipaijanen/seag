#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Fail closed until the SEAG public-release prerequisites are present."""

from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from seag.cxl import export, parse
from seag.glossary import extract
from seag.transform import json_bytes


REQUIRED_FILES = (
    "LICENSES/Apache-2.0.txt",
    "LICENSES/CC-BY-4.0.txt",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "docs/dco-historical-attestation.md",
    "docs/cxl-profile.md",
    "docs/glossary-extraction.md",
    "docs/semantic-mappings.md",
    "docs/installation-and-upgrade.md",
    "docs/release-policy.md",
)


def main() -> int:
    missing = [path for path in REQUIRED_FILES if not Path(path).is_file()]
    if missing:
        print("publication gate: CLOSED", file=sys.stderr)
        for path in missing:
            print(f"missing required file: {path}", file=sys.stderr)
        return 1

    dco = subprocess.run(
        (sys.executable, "scripts/check-dco.py"), check=False
    )
    if dco.returncode:
        print("publication gate: CLOSED: DCO check failed", file=sys.stderr)
        return 1
    fixed_time = "2026-11-22T00:00:00Z"
    manifest = Path("fixtures/valid/manifest.json")
    with tempfile.TemporaryDirectory() as directory:
        temporary = Path(directory)
        glossary, glossary_provenance = extract(manifest, "en", fixed_time)
        glossary_data = json_bytes(glossary)
        glossary_provenance["output_sha256"] = __import__("hashlib").sha256(glossary_data).hexdigest()
        generated = {
            "glossary-en.json": glossary_data,
            "glossary-en.json.provenance.json": json_bytes(glossary_provenance),
        }
        cxl_data, cxl_provenance, expected = export(manifest, fixed_time)
        cxl_path = temporary / "concept-map.cxl"
        cxl_path.write_bytes(cxl_data)
        if parse(cxl_path) != expected:
            print("publication gate: CLOSED: CXL round trip changed the graph", file=sys.stderr)
            return 1
        generated["concept-map.cxl"] = cxl_data
        generated["concept-map.cxl.provenance.json"] = json_bytes(cxl_provenance)
        for name, content in generated.items():
            expected_path = Path("fixtures/expected") / name
            if not expected_path.is_file() or expected_path.read_bytes() != content:
                print(f"publication gate: CLOSED: stale expected transform: {name}", file=sys.stderr)
                return 1
    print("publication gate file prerequisites: present")
    print("independent review evidence still requires a release-specific CI check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

