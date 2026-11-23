#!/bin/sh
# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

# Publish only the already admitted OCI archive. This script deliberately
# distinguishes a definite registry absence from every other lookup failure.
set -eu

readonly proof_dir=toolchain-proof
readonly admission_dir=toolchain-publish-admission
readonly publication_dir=toolchain-publication

test -n "${CI_REGISTRY_USER:-}" -a -n "${CI_REGISTRY_PASSWORD:-}"
test "${TOOLCHAIN_PUBLISH_COMMIT:-}" = "${CI_COMMIT_SHA:-}"
test "$(cat "$admission_dir/source-commit.txt")" = "$CI_COMMIT_SHA"
(cd "$proof_dir" && sha256sum -c SHA256SUMS)
test "$(sha256sum "$proof_dir/seag-ci-toolchain.oci.tar" | cut -d' ' -f1)" = \
  "$(cat "$admission_dir/archive-sha256.txt")"

destination="$(cat "$admission_dir/destination.txt")"
expected_digest="$(cat "$admission_dir/manifest-digest.txt")"
auth_dir="$(mktemp -d)"
readonly destination expected_digest auth_dir
readonly auth_file="$auth_dir/auth.json"
readonly inspect_error="$auth_dir/inspect-error"
trap 'rm -rf "$auth_dir"' EXIT

printf '%s' "$CI_REGISTRY_PASSWORD" | skopeo login \
  --authfile "$auth_file" \
  --username "$CI_REGISTRY_USER" \
  --password-stdin "$CI_REGISTRY"

if skopeo inspect --authfile "$auth_file" "docker://$destination" \
  >/dev/null 2>"$inspect_error"; then
  echo "candidate destination already exists" >&2
  exit 1
fi
if test "$(wc -l <"$inspect_error")" -ne 1 || \
  ! LC_ALL=C grep -Eiq '(manifest unknown|name unknown)"?$' "$inspect_error"; then
  echo "candidate absence could not be established" >&2
  exit 1
fi

skopeo copy --preserve-digests --authfile "$auth_file" \
  "oci-archive:$proof_dir/seag-ci-toolchain.oci.tar" \
  "docker://$destination"
observed_digest="$(
  skopeo inspect --authfile "$auth_file" --format '{{.Digest}}' \
    "docker://$destination"
)"
test "$observed_digest" = "$expected_digest"

test ! -e "$publication_dir"
mkdir "$publication_dir"
cp "$admission_dir/admission.json" "$publication_dir/admission.json"
printf '%s\n' "$destination" >"$publication_dir/destination.txt"
printf '%s\n' "$observed_digest" \
  >"$publication_dir/registry-manifest-digest.txt"
printf '%s\n' "$CI_JOB_ID" >"$publication_dir/publisher-job-id.txt"
