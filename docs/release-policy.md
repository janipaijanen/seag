<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Release and version policy

## Version identity

SEAG follows the AGF release-numbering pattern. `VERSION` contains the single
authoritative package version in Semantic Versioning form. Release archives are
named `seag-<version>.tar.gz`, and a release tag is exactly `v<version>`.

Git commits, pipeline IDs, timestamps, and branch names are build provenance;
they do not become alternate release versions. An untagged CI artifact remains
a release candidate for the version in `VERSION` and is distinguished by its
source commit and digest.

## Version meaning

Before 1.0, a minor-version increment may contain incompatible changes to the
draft source contract. Patch increments contain compatible corrections and
tooling fixes. Pre-release identifiers may be used for deliberately published
preview series, but ordinary branch artifacts do not acquire invented
pre-release numbers.

An `alpha` is an unsupported evaluation release intended to discover contract,
usability, and interoperability defects. A `beta` requires a stable intended
capability boundary but may still lack adoption or compatibility evidence. An
`rc` freezes the intended release contract and accepts only release-blocking
corrections. None of these labels substitutes for the evidence required by the
corresponding stable release.

After 1.0, SEAG applies Semantic Versioning normally:

- major: incompatible normative source-contract or validator behavior;
- minor: backward-compatible capabilities; and
- patch: backward-compatible corrections.

A representation or integration profile has its own profile version and also
records the compatible SEAG version range. Changing only an export profile does
not silently redefine the SEAG core version.

## Release procedure

1. Start `release-X.Y.Z` from current `main`.
2. Change `VERSION` to `X.Y.Z` if necessary.
3. Move relevant `CHANGELOG.md` entries from `Unreleased` into `## X.Y.Z`.
4. Include only release metadata corrections needed for that release.
5. Open and independently review a merge request into `main`.
6. Verify conformance, SPDX coverage, reproducible bundle output, security
   checks, compatibility evidence, and the applicable release gate on the exact
   head.
7. Merge the reviewed release MR.
8. Create an annotated, protected tag `vX.Y.Z` on that merge commit.
9. Push the tag; CI verifies that it matches `VERSION` and is contained in
   `main`. A stable tag opens the publication gate and builds a reproducible
   stable bundle.
10. Publish only the stable bundle from the tag's `stable-publication-gate`
    job. Its manifest and provenance must say `release_status: stable` and
    `publication_gate: asserted`; branch and pre-gate bundles remain candidates.

The tag pipeline treats default-branch containment as live authorization
evidence, not as a reproducible build input. Before any tag bundle job starts,
`tag-authorization` verifies that `origin` names the expected GitLab host and
project, fetches only the current default-branch ref without tags, records the
observed commit, and fails closed unless the tag commit is its ancestor. Bundle
construction has no live branch fetch. Reproducing bundle bytes therefore does
not claim to reproduce a later publication-policy decision.
If the forge is unavailable, rate-limits the fetch, or returns ambiguous state,
authorization fails closed: the tag pipeline fails, no bundle job starts, and
the release waits for a new successful pipeline rather than bypassing the
check.

Direct version-release tags on unreviewed commits are forbidden. A tag that
does not exactly match `VERSION`, is lightweight rather than annotated, or
does not identify the requested release commit is rejected.

### Deliberate preview publication

A prerelease follows the same release-branch, exact-head review, signed commit,
annotated tag, checksum, reproducibility, and immutability rules. Its tag
pipeline builds a verified artifact with `release_status: candidate` and
`publication_gate: not-asserted`; the stable-publication job must not run. The
project may publish that artifact only as a clearly labelled unsupported
preview with its intended audience, evaluation scope, known gaps, source
commit, checksum, and feedback channel. It must never be presented through the
stable download path or called a supported compatibility baseline.

## Immutability

A pushed release tag and published package version are immutable. A defective
release is retained and superseded by a new version; its tag is never moved,
deleted, or reused. Checksums, manifests, and release evidence remain attached
to the original version.

Candidate bundles are not releases. They may expire from CI artifact storage,
but their embedded source commit, content manifest, and digest prevent them
from being confused with a different build.

## Relationship to AGF

SEAG adopts the AGF numbering and release mechanics as a project policy, not as
a runtime dependency or a claim that AGF governs SEAG. SEAG retains its own
publication criteria, licensing, semantic compatibility rules, and artifacts.

## CI pipeline-source policy

SEAG selects pipeline sources as follows:

- merge requests always receive a pipeline;
- `main` pushes and tags always receive a pipeline;
- scheduled, API-triggered, and manually requested branch pipelines remain
  available; and
- ordinary feature or release branch pushes do not create a duplicate pipeline
  before or alongside their merge request.

Every admitted SEAG pipeline runs the complete SEAG validation set because the
repository is small and no test tier is currently expensive enough to justify
path-based omission. Tag pipelines retain the same validation rather than
assuming that an earlier branch pipeline covered the tagged commit.

Product deployment pipelines are outside SEAG's scope. A version tag must equal
`v<VERSION>` and its commit must be contained in `main` before a bundle can be
considered for publication.
