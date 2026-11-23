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
tokens or source checkout. BuildKit receives only the committed canonical
decimal in `SOURCE_DATE_EPOCH` through its documented special reproducibility
argument. The value `1795432630` is the UTC commit time of main merge
`3988791df27011a00616f56473457e6854a1ba28`, which closed the independently
reviewed recipe follow-ups. It is not supplied by a CI variable or user. The
OCI exporter pins compatibility version 30 and rewrites timestamps to that
epoch.

Two independent rootless build jobs must produce byte-identical OCI archives,
metadata and descriptor listings. The comparison job retains one verified
archive only after every comparison passes. This is a non-publishing proof,
not acceptance of the artifact.

A candidate build must run before any registry login and with no credentials
or CI variables forwarded into the build environment. Registry authentication,
candidate publication and digest attestation are separate post-build
operations and require their own reviewed protected pipeline.
