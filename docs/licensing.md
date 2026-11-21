<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Licensing and SPDX declarations

Copyright (C) 2026 Jani Päijänen.

SEAG uses a split licence appropriate to the artifact:

- software, CI configuration, executable tooling, and tests use Apache-2.0;
- framework documentation, semantic policies, and machine-readable semantic
  registers use CC-BY-4.0; and
- third-party material, if introduced, retains its own copyright and licence
  and must be isolated and identified rather than relicensed implicitly.

Every tracked distributable file carries both `SPDX-FileCopyrightText` and
`SPDX-License-Identifier`. A format that cannot legally contain comments, such
as strict JSON, uses an adjacent `<filename>.license` sidecar. The sidecar is
distributed with the governed file and is included in release manifests.

Copyright declarations identify the actual rights holder or holders; they are
not project-ownership assertions. Existing valid notices must be preserved.
External contributors retain copyright under [the contribution
policy](../CONTRIBUTING.md) and may add an accurate declaration for their work.
CI requires at least one nonempty declaration but does not replace contributor
ownership with the maintainer's name.

## AGF maturity-vocabulary authorization

The maturity vocabulary incorporated into [`maturity.md`](maturity.md) and
[`maturity.yaml`](../maturity.yaml) is adapted from the exact AGF26 source
identified there. Jani Päijänen is the declared copyright holder of that AGF26
source and of this SEAG adaptation. For avoidance of doubt, Jani Päijänen
authorizes the incorporated SEAG adaptation under CC-BY-4.0.

This authorization covers only the vocabulary and adapted explanatory text
actually distributed in SEAG. It does not relicense the AGF repository, the AGF
framework as a whole, or any other proprietary AGF material. The exact upstream
commit and source blocks remain recorded as attribution and provenance.

The root [`LICENSE`](../LICENSE) is the Apache-2.0 text for software, while
[`LICENSE-DOCS`](../LICENSE-DOCS) is the CC-BY-4.0 text for documentation and
semantic registers. Their canonical SPDX copies are stored in
`LICENSES/Apache-2.0.txt` and `LICENSES/CC-BY-4.0.txt`. SPDX identifiers are
metadata; the corresponding licence text remains authoritative.

Run the repository check with:

```sh
python3 scripts/check-spdx.py
```

The CI validation stage runs this check. Files without a nonempty declaration,
files using an unapproved expression, missing licence texts, and root licence
copies that differ from their canonical SPDX texts fail the pipeline.
