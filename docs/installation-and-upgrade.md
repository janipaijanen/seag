<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Installation, use, and upgrade

SEAG 0.1 requires Python 3.11 or newer and has no third-party runtime
dependencies. Verify the release archive against its published SHA-256, unpack
it, and run commands from its root. Installation into site-packages is not
required.

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
