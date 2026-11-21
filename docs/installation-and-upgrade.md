<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Installation, use, and upgrade

SEAG 0.1 requires Python 3.11 or newer and has no third-party runtime
dependencies. Verify the release archive against its published SHA-256, unpack
it, and run commands from its root. Installation into site-packages is not
required.

```sh
python3 -m seag.validate source/manifest.json
python3 -m seag.glossary source/manifest.json --language en --output glossary.json
python3 -m seag.cxl source/manifest.json --output map.cxl --verify
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
