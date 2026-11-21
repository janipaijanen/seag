<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Source-contract 0.1 integration review record

## Scope

This record identifies the evidence used to assess the bounded 0.1 semantic
source contract and validator as Level 4 Validated. It is not a release,
publication approval, identity attestation, or Level 5 claim.

## Reviewed source

- original SEAG base: `14bfb3ac40a58e444141310b95f2e239c884c292`;
- independently reviewed source-contract candidate:
  `cb3d9585d1660ecf4c66131ba9ea95c4e9f2c797`;
- integrated tree: `2370d999022f9fe5c5c32aef7c943fd7ed5be3df`;
- integration merge parents:
  `0d1a9f292865df71fb3dbb4e845e4fe19708ef2b` and
  `cb3d9585d1660ecf4c66131ba9ea95c4e9f2c797`; and
- documentation-only correction reviewed after integration:
  `ad566999a9f93bd7c76910b8bc650f9853a656ae`.

The complete integration review bundle contained 62,933 bytes and had SHA-256
`01d56009bbc8468bac34035bbc53b1dc76643bc67c83c7c490f1b3e32694a62f`.
The targeted documentation-delta bundle contained 1,774 bytes and had SHA-256
`afb359c874d1774d43a3e1cfe0016f5d787d72e6f345d1ce5e9b87e0f366522e`.

## Verification evidence

- The source-contract candidate received independent, non-author review with no
  blocking P1 or P2 finding remaining before integration.
- Integration preserved the reviewed validator logic, schema, fixture JSON,
  and test bodies. Differences in those files were limited to SPDX declarations
  and adjacent licence sidecars.
- The combined local suite passed 45 tests, including positive and negative
  contract cases.
- JSON Schema Draft 2020-12 root and valid manifest, fragment, and variant were
  checked with `jsonschema` 4.25.1 in an ephemeral environment.
- Integration pipeline `3097930514` passed validation and reproducible bundle
  jobs for `2370d999022f9fe5c5c32aef7c943fd7ed5be3df`.
- Documentation-correction pipeline `3097943301` passed the same jobs for
  `ad566999a9f93bd7c76910b8bc650f9853a656ae`.
- SPDX coverage, archive verification, two-build byte comparison, and archive
  SHA-256 verification passed in the CTO environment.

## Findings and disposition

The integration review found two documentation defects: the maturity register
still described the integrated contract and validator as merely planned, and
the release policy carried originating-project operational detail. The
documentation-only correction identified above promoted only the bounded,
tested capabilities to Level 4, stated their limitations, updated the
changelog, and made the pipeline-source policy project-neutral.

A targeted re-review found both original defects corrected. It also required
the maturity register to use this durable record instead of ephemeral
coordination references and to distinguish the assessed integration tree from
the later documentation correction. That evidence-reference correction does
not change the source contract, validator, schema, fixtures, or tests.

## Remaining limitations

Nonblocking follow-ups remain for validation parity and coverage, lexical
process-name limits, release-build assurance wording, SPDX checker hardening,
cross-image reproducibility, and publication security gates. The validator
does not prove semantic truth, actor identity, authority, review independence,
or complete Unicode/process detection. No supported release exists.
