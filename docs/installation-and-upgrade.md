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
uv run --locked --no-sync python scripts/check-dependency-policy.py
uv run --locked --no-sync python -m unittest discover -s tests -v
```

`project.dependencies` is deliberately empty. Packages in the `conformance`
group provide testing, differential-oracle, licence, and schema checks; they
are not required by the shipped commands and do not define SEAG semantics.
Changing Python, uv, any direct pin, or any resolved artifact is a reviewed
toolchain change and must update the lock and its evidence in the same commit.

## 0.2.0-alpha.2 evaluation candidate

Alpha.2 is an unsupported successor candidate, not an upgrade recommendation
or approval to start a pilot. Until its annotated tag, checksum, and exact-head
review evidence exist, use of the release branch is candidate testing, not use
of an alpha.2 release. After publication, an evaluation must pin the annotated
`v0.2.0-alpha.2` tag, verify the published archive checksum, and retain its
exact source commit in the evidence log.

The immutable alpha.1 release is superseded for new evaluations after review
found input-boundary defects. Preserve alpha.1 artifacts and evidence for
replay, but do not silently relabel or replace them with alpha.2 results.

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

### Candidate verification limits

`scripts/build-release-bundle.py --verify` checks the archive's safe member
paths and every source digest declared by its embedded manifest. It is a
builder self-check, not independent attestation of an untrusted downloaded
archive. Verify the separately published checksum first, inspect the provenance
and manifest, and retain the exact artifact used by an evaluation.

The alpha.2 CI environment pins the Python image, Git package version, uv
version, direct conformance dependencies, and resolved Python artifacts to the
extent recorded in the repository. It does not yet establish an absolute
byte-pinned network bootstrap: the uv installer wheel hash and Alpine package
repository metadata are not pinned by digest, and the tag-containment check
fetches the then-current `origin/main`. These are known reproducibility and
supply-chain limits, not evidence that an observed candidate archive differs
between the two CI builds. The H6 byte-pinning gate remains open.

Current development has since published a separate Linux/amd64 CI toolchain
candidate and recorded a fresh read-only post-publication technical review.
That review is procedurally separate, not account-level or human organizational
independence. Its accepted evaluation identity is
`registry.gitlab.com/janipaijanen/seag/ci-toolchain@sha256:b427405058274309921ce6cf8e8e0cedc278bba492da46152c208222eb55a632`.
That later evidence does not rewrite alpha.2's historical verification limits,
does not make the candidate a SEAG release, and does not rewrite any immutable
alpha.2 artifact. Current development selects the accepted manifest digest for
general CI consumers and removes live Git and uv installation from their job
startup. This is not a claim that CI is fully offline: uv still retrieves
hash-locked project dependencies, tag containment queries current authenticated
default-branch policy, and producer and publisher jobs retain their separately
pinned runtimes. H6 remains open until the consumer change, protected-main
pipeline, and non-publishing tag-path rehearsal have successful retained
evidence and independent review. The rehearsal's authenticated containment
phase necessarily runs with ordinary CI job authority. Its local
clone/tag/bundle phase is separately scrubbed to an exact `HOME`, `LC_ALL`, and
`PATH` allowlist; the job does not claim that credentials are absent from the
authorization phase.

Current-development H6 is now closed for this bounded CI-toolchain adoption.
MR !34 merged the consumer change at commit
`3320eb1d242b59a7efbf42112af0dc7f662572ff`; protected-main pipeline
`3114095373` passed every automatic job, including the non-publishing
tag-path rehearsal in job `18362786962`, and a fresh post-pipeline review found
no P1, P2, or P3 findings. The durable identities and review boundary are in
[`reviews/toolchain-adoption-3320eb1d.json`](reviews/toolchain-adoption-3320eb1d.json).
This closes only the accepted digest's current-development protected-main CI
adoption gate. It does not rewrite alpha.2's immutable limitation, establish a
SEAG release, approve publication, claim fully offline CI, or authorize the
manual publisher.
