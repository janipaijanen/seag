<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Installation, use, and upgrade

The current SEAG development line supports the exact Python 3.14.8 runtime
recorded in `.python-version` and has no third-party runtime dependencies.
Verify a release archive against its published SHA-256, unpack it, and run
commands from its root. Installation into site-packages is not required.

```sh
python3 -m seag.validate source/manifest.json
python3 -m seag.glossary source/manifest.json --language en --generated-at 2026-11-22T00:00:00Z --output glossary.json
python3 -m seag.cxl source/manifest.json --generated-at 2026-11-22T00:00:00Z --output map.cxl --verify
```

The supported source identifier is `0.1-draft.2`. Inputs using the collided
`0.1-draft` identifier require the human-reviewed migration documented in the
source-contract guide. Back up source bytes, finish all content and identifier
edits, calculate final fragment digests, then validate. Never rewrite source
provenance to make an input appear compatible.

Generated glossary and CXL formats are versioned profiles. Consumers must
check their schema/profile identifiers and provenance sidecars. Upgrade by
generating new variants from the unchanged authoritative source, comparing
declared omissions and digests, and retaining the earlier provenance chain.
SEAG provides no daemon, database migration, network service, or automatic
mutation of user source.

## Contributor and conformance environment

uv 0.12.9 is the only supported Python environment manager for this source
tree. The repository requires that exact uv version, declares only exact
direct dependency pins, and commits `uv.lock` with resolved versions and
artifact hashes. Do not install an unpinned requirements set or regenerate the
lock as a side effect of testing.

```sh
uv sync --locked --only-group conformance
uv lock --check
python scripts/check-dependency-policy.py
uv run --locked --no-sync python -m unittest discover -s tests -v
```

`project.dependencies` is deliberately empty. Packages in the `conformance`
group provide testing, differential-oracle, licence, and schema checks; they
are not required by the shipped commands and do not define SEAG semantics.
Changing Python, uv, any direct pin, or any resolved artifact is a reviewed
toolchain change and must update the lock and its evidence in the same commit.

## 0.2.0-alpha.1 evaluation

The alpha is an unsupported pilot release, not an upgrade recommendation. A
pilot must pin the annotated `v0.2.0-alpha.1` tag, verify the published archive
checksum, and retain its exact source commit in the evidence log. Until that
tag and checksum exist, use of the release branch is release-candidate testing,
not use of the alpha release.

It retains the `0.1-draft.2` source contract and adds two experimental commands:

```sh
python3 -m seag.canonical source/manifest.json --output-dir canonical-source
python3 -m seag.semantic_diff \
  before/manifest.json after/manifest.json \
  --format json --fail-on breaking
```

Do not replace authoritative source automatically. Review canonical output,
retain project-owned adjacent files, and commit the byte-only rewrite separately
from semantic edits. Treat semantic-review JSON as at least as sensitive as its
inputs because added and removed records can be reproduced in full.

The alpha makes no compatibility promise for its canonical byte form,
diagnostic codes, result schemas, or conflict boundary. Preserve the original
source and pilot outputs so a later alpha can be compared or abandoned without
data loss.
