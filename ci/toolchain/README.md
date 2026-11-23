<!--
SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
SPDX-License-Identifier: Apache-2.0
-->

# SEAG CI toolchain candidate

This directory defines a Linux/amd64 candidate, not a published or accepted CI
image. `inputs.json` binds the base image and every added package to immutable
identity. `prepare-toolchain-context.py` enforces each requested and final URL,
exact byte size and SHA-256 before the build. `install.py` repeats size and hash
verification inside the network-disabled build.

The generated CycloneDX 1.6 document covers every installed APK, the CPython
runtime and every installed Python distribution. Input artifacts carry their
SHA-256 and distribution URL. Packages inherited from the pinned base carry
their installed name, version, architecture and purl; the CPython component
records the upstream source SHA-256 declared by the pinned base. The document
is a component inventory and does not claim a dependency graph.

The pinned Python base must expose `PYTHON_SHA256`; absence fails the build
closed before SBOM creation. That value is the base image's declaration of the
upstream CPython source hash, not a hash of the installed interpreter binary.

Redirect policy is checked against the final response URL after the client has
connected to and received headers from the redirect target, but before any
response body is read. Exact size and SHA-256 checks remain mandatory even
when the requested and final URLs are identical.

The Containerfile declares no build arguments and accepts no secret mounts,
tokens or source checkout. CI constructs a separate read-only build context
from an explicit allowlist: `inputs.json`, `install.py`, and the verified
download closure. The checkout, `.git`, CI configuration, and every unrelated
path are outside that context, so repository credentials cannot enter the
BuildKit context. BuildKit receives only the committed canonical decimal in
`SOURCE_DATE_EPOCH` through its documented special reproducibility argument.
The value `1795432630` is the UTC commit time of main merge
`3988791df27011a00616f56473457e6854a1ba28`, which closed the independently
reviewed recipe follow-ups. It is not supplied by a CI variable or user. The
OCI exporter pins compatibility version 30 and rewrites timestamps to that
epoch.

Two independent rootless build jobs on the same GitLab runner class and pinned
BuildKit version must produce byte-identical OCI archives, metadata and
descriptor listings. This demonstrates reproducibility in that tested
environment; it does not claim reproducibility across runner, kernel, or
BuildKit changes. The comparison job retains one verified archive only after
every comparison passes. This is a non-publishing proof, not acceptance of the
artifact.

Rootless BuildKit uses `--oci-worker-no-process-sandbox` because the shared
runner cannot create the otherwise-required nested process sandbox. This is
accepted only for this reviewed recipe: all executable inputs are pinned and
verified before use, and every `RUN` is network-disabled. The flag must not be
reused for untrusted source, user-supplied build instructions, or an input set
that has not passed the same identity checks.

The offline installation of the added uv wheel disables generation of new
bytecode because `.pyc` headers would otherwise inherit artifact-extraction
times. This does not remove bytecode or cache files already present in the
pinned CPython/pip base; those inherited bytes remain part of the pinned base
layers and OCI identity. The timestamped apk transaction log is removed after
the structured inventory and SBOM are written. No bytecode derived from the
downloaded addition closure, and no transaction log containing the build wall
clock, is retained as toolchain evidence.

A candidate build must run before any registry login and with no credentials
or CI variables forwarded into the build environment. Registry authentication,
candidate publication and digest attestation are separate post-build
operations and require their own reviewed protected pipeline.

The candidate publisher is a separate manual job on protected `main`. An
automatic admission job first validates the reproduced archive, its canonical
checksum manifest, OCI member listing, Linux/amd64 descriptor, and manifest and
config blob digests without registry credentials. The publisher receives the
verified archive only after that admission, requires the operator to repeat
the exact source commit in `TOOLCHAIN_PUBLISH_COMMIT`, and serializes all
candidate publications. It uses a digest-pinned Skopeo 1.24.1 image and a
`candidate-<commit>-<manifest-digest>` discovery tag, fails closed unless the
registry lookup specifically reports the destination absent, preserves the OCI
manifest digest, and emits a credential-free receipt. The lookup and copy are
not an atomic create-only registry operation: the candidate tag is never an
authority or approval, and only the recorded manifest digest identifies bytes.
Registry tag protection must restrict competing writers before the first run.

The `seag-toolchain-candidate` GitLab environment must be protected before the
manual job is ever run. A successful candidate publication is review evidence,
not acceptance or adoption: an independent reviewer must inspect the registry
manifest, config, layers, inventories and SBOM, and the accepted digest must be
recorded durably before any SEAG job consumes it.

`TOOLCHAIN_PUBLISH_COMMIT` is supplied only for the individual manual job; do
not store it as a project, group or protected variable. Run the publisher while
the seven-day proof artifacts remain available, or rerun the exact protected
main pipeline. If copying succeeds but the post-copy digest check fails, stop:
retain the failed job and registry identity as evidence, have a maintainer
quarantine the discovery tag, and publish a corrected candidate under a new
commit/digest identity. Never repair it by replacing the tag. The two complete
BuildKit builds on each protected-main pipeline are an intentional runner-cost
tradeoff for byte-reproducibility evidence.
