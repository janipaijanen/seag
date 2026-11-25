<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Changelog

Each release has one section headed `## <version>`. `## Unreleased` collects
changes until a release branch moves them into the section matching `VERSION`.
CI uses that release section as the future release-note source.

## Unreleased

- Selected the reviewed CI toolchain candidate by immutable digest for general
  consumers, removed live Git and uv installation from job startup, added
  fail-closed consumer-policy tests, and added a protected-main-only local
  tag-path rehearsal whose scrubbed local phase performs no remote tag or
  publication operation.
- Recorded the published Linux/amd64 CI toolchain candidate and its fresh
  read-only post-publication technical review by immutable manifest digest,
  while distinguishing procedural review separation from organizational
  independence and keeping candidate evidence separate from release status
  and protected-main CI adoption.
- Bound release manifests and external build provenance to the complete Git
  tree so exact reviewed-tree identity survives merge-commit comparison even
  though CI policy remains outside the distributable archive.
- Added explicit AI-development transparency and a separate notice covering
  optional AI/service costs, computing resources, energy and environmental
  effects, data handling, and the controlling licence boundaries.
- Made the AI dossier distinguish project-controlled evidence, non-author
  in-project review, and absent external consumer/adopter attestation; surfaced
  the README and security-policy single-maintainer support boundary and
  clarified manifest verification without promising an unpublished toolchain.
- Hardened AI dossier generation against duplicate capability fields and
  identifiers, invalid evidence status, and malformed standards-table inputs.
- Routed rootless BuildKit proof jobs to the dedicated `dind` runner after
  ordinary Docker executors rejected the required subordinate UID/GID mapping.
- Added deterministic compact and full AI evaluation aids, a digest-bound
  machine manifest, and a stale-generation check without claiming independent
  validation or embedding adopter evidence.
- Separated fresh default-branch containment authorization from reproducible
  tag-bundle construction, with exact GitLab remote identity checking,
  fail-closed policy fetches, recorded observed commits, and negative tests.

## 0.2.0-alpha.2

Unsupported successor evaluation release. It supersedes alpha.1 for new
evaluations but remains outside the supported compatibility baseline and does
not itself start or approve an adopter pilot.

- Clarified prerelease-candidate wording, the scope of the builder's
  reproducibility claim, the complete term-disposition vocabulary, and how
  implementation alignment records a specified but absent implementation.
- Applied the strict host profile to every nonempty IRI authority: the host is
  required and numeric IPv4 and IPv6 forms are validated for every scheme.
  Also rejected JSON exponents that overflow the runtime to infinity.
- Made fragment loading fail closed through one confined, nonblocking,
  regular-file reader in standalone validation and transformations. Named
  pipes and fragment symlinks are rejected, including symlinks whose targets
  remain inside the bundle. The bundle-root path itself may be reached through
  a symlink because the root is resolved before manifest confinement begins.
- Synchronized Python project and lock metadata with the candidate version and
  made CI reject future drift from the authoritative `VERSION` file.

Known verification limits for this unsupported candidate are documented in
the installation guide. In particular, the builder's archive check is an
internal consistency check rather than independent untrusted-package
attestation, and the CI bootstrap and tag-ancestry checks are not yet
byte-pinned end to end.

## 0.2.0-alpha.1

Unsupported evaluation release for the silver-birch pilot and other controlled
experiments. It retains the 0.1 source contract while adding experimental
canonical and semantic-review tooling. It does not satisfy the 0.2 adoption
gate or establish a supported compatibility baseline.

The following three capabilities were present in the immutable alpha.1
artifact but were mistakenly left under `Unreleased` in that artifact. Their
placement here corrects the changelog attribution; it does not change alpha.1.

- Adopted uv 0.12.9 for the contributor and conformance environment, with
  exact direct dependency pins, a hash-bearing lock, a fail-closed dependency
  policy gate, and no added shipped runtime dependencies.
- Centralized strict JSON and lexical field validation in `seag.validation`,
  and added deterministic property and differential-oracle tests for schemas,
  language tags, identifiers, network values, and bounded XML parsing.
- Replaced the hand-parsed YAML standards register with strict UTF-8 JSON and
  a closed, machine-checked top-level contract.

- Added a silver-birch-owned, replayable pilot-evidence contract for immutable
  corpora, expectations, run results, tool identity, and version-lift migration
  exercises without placing silver-birch domain content in SEAG.
- Moved adopter schedules and product-governance decisions out of the release
  content while retaining a reusable public evaluation protocol.
- Allowed unsigned hosting-platform merge commits only when their tree exactly
  reuses an already-checked parent tree; content-bearing merges still require
  DCO sign-off.

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
- Added an experimental no-overwrite canonical source renderer and checker
  that sorts source deterministically, updates fragment digests, stages output,
  and validates the completed bundle without modifying the input.
- Hardened absolute-IRI validation against malformed percent escapes,
  authorities, ports, IPv6 literals, and Unicode values outside RFC 3987
  `ucschar` and query-only `iprivate` ranges, and completed structural RFC
  5646 language-tag checks for duplicate variants and extension singletons.
  The documentation now distinguishes structural validation from
  unimplemented IANA-registry membership validation.
- Adopted the pinned Ponytail full discipline for SEAG development and added a
  strict input-boundary policy. JSON now rejects duplicate members and
  non-finite numbers, language CLI input is validated, reproducible timestamps
  require canonical decimal input, unsafe control text is rejected, and CXL
  verification accepts only the bounded SEAG graph profile.

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
