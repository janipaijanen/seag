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
   checks, compatibility evidence, and the publication gate on the exact head.
7. Merge the reviewed release MR.
8. Create an annotated, protected tag `vX.Y.Z` on that merge commit.
9. Push the tag; CI verifies that it matches `VERSION` before any publication.

Direct version-release tags on unreviewed commits are forbidden. A tag that
does not exactly match `VERSION` is rejected.

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
