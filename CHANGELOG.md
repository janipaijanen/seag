<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Changelog

Each release has one section headed `## <version>`. `## Unreleased` collects
changes until a release branch moves them into the section matching `VERSION`.
CI uses that release section as the future release-note source.

## Unreleased

- Clarified the state-machine example with distinct `Logging` semantic and
  component identities, a `Configuration` concept, and explicit optional and
  required target cardinalities separated from the relation phrases.
- Documented the text-first enterprise integration lifecycle, four-plane
  architecture, multi-user conflict boundary, bidirectional adapter contract,
  evidence-informed priorities, and readiness gates without claiming that the
  proposed service or interoperability features are implemented.
- Added an evidence-gated implementation roadmap from discovery through 1.0,
  with per-increment scope, order, exit evidence, stop conditions, permanent
  exclusions, and a narrow adoption-backed definition of 1.0 stability.
- Added an experimental deterministic semantic-diff command with stable draft
  change codes, machine-readable output, selectable CI failure policies, and
  bounded three-way conflict detection. This is post-0.1 development and does
  not claim that the 0.2 evidence gate has passed.

## 0.1.0

Initial stable release of the bounded SEAG semantic-source and transformation
tooling. Stability applies only to the documented 0.1 compatibility boundary;
optional integration profiles and unclaimed external representations remain
outside support.

- Added a software-engineer introduction to concept maps, ontologies, and
  SEAG's semantic-source role, linked from the main README.
- Corrected the source-contract identifier to `0.1-draft.2` for the mandatory
  singular-concept-label boundary and documented detection and human-reviewed
  migration from the collided `0.1-draft` identifier.
- Aligned dependency-free validation with the source schema for optional
  replacement and role-disclosure fields.
- Removed a misleading actor-collapse diagnostic from incomplete confirmation
  blocks and made CLI success output identify variant validation.
- Expanded tested process-phrase rejection while preserving static semantic
  names and the documented need for human semantic review.
- Added focused negative and boundary coverage for source, fragment, variant,
  provenance, identity, cardinality, and deprecation validation.
- Recorded the maintainer's explicit DCO certification for the eleven
  preserved commits published during the unenforced sign-off transition and
  added fail-closed prospective DCO checks to CI and the publication gate.
- Added deterministic provenance-preserving glossary extraction and a lossy,
  sidecar-bound CmapTools CXL export with compatible-parser round-trip checks.
- Pinned the 0.1 standards register, documented PROV and SKOS mappings, and
  added installation, upgrade, and transformation-profile guidance.
- Replaced the source schema's placeholder identity with its immutable
  canonical `v0.1.0` GitLab raw-file URL.

## 0.1.0-rc.2

Public review governance release. This release candidate remains unsupported,
non-production-ready, and incomplete against the stable publication gate.

- Added contribution and security policies for the single-maintainer public
  review phase.
- Added the package, contract, profile, validator, deprecation, and evidence
  compatibility policy.
- Made SPDX enforcement preserve truthful maintainer and contributor copyright
  ownership instead of requiring one owner on every file.

## 0.1.0-rc.1

Public review release. This release candidate is not a stable or supported
release and does not claim production readiness or complete conformance.

- Established the SEAG charter, framework boundaries, identity model,
  provenance policy, semantic minimality, and role contracts.
- Documented BCP 47 language handling and the external-standards conformance
  register.
- Added reproducible release-candidate bundles, complete licence texts, and
  per-file SPDX enforcement.
- Added the bounded 0.1 semantic source contract, JSON Schema, dependency-free
  validator, and domain-neutral positive and negative conformance fixtures.
