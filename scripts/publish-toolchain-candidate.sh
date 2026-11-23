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
printf '%s\n' "${CI_COMMIT_SHA:-}" | grep -Eq '^[0-9a-f]{40}$'
printf '%s\n' "${TOOLCHAIN_PUBLISH_COMMIT:-}" | grep -Eq '^[0-9a-f]{40}$'
test "${TOOLCHAIN_PUBLISH_COMMIT:-}" = "${CI_COMMIT_SHA:-}"
test "$(cat "$admission_dir/source-commit.txt")" = "$CI_COMMIT_SHA"
(cd "$proof_dir" && sha256sum -c SHA256SUMS)
test "$(sha256sum "$proof_dir/seag-ci-toolchain.oci.tar" | cut -d' ' -f1)" = \
  "$(cat "$admission_dir/archive-sha256.txt")"

destination="$(cat "$admission_dir/destination.txt")"
expected_digest="$(cat "$admission_dir/manifest-digest.txt")"
case "$destination" in
  "$CI_REGISTRY"/*) ;;
  *)
    echo "candidate destination is outside CI_REGISTRY" >&2
    exit 1
    ;;
esac
auth_dir="$(mktemp -d)"
readonly destination expected_digest auth_dir
readonly auth_file="$auth_dir/auth.json"
readonly inspect_error="$auth_dir/inspect-error"
trap 'rm -rf "$auth_dir"' EXIT

printf '%s' "$CI_REGISTRY_PASSWORD" | skopeo login \
  --authfile "$auth_file" \
  --username "$CI_REGISTRY_USER" \
  --password-stdin "$CI_REGISTRY"

if skopeo inspect --raw --authfile "$auth_file" "docker://$destination" \
  >/dev/null 2>"$inspect_error"; then
  echo "candidate destination already exists" >&2
  exit 1
fi
if test "$(awk 'END {print NR}' "$inspect_error")" -ne 1; then
  echo "candidate absence could not be established" >&2
  exit 1
fi
diagnostic="$(cat "$inspect_error")"
case "$diagnostic" in
  time=\"*\"\ level=fatal\ msg=\"*\")
    diagnostic="${diagnostic#* level=fatal msg=\"}"
    diagnostic="${diagnostic%\"}"
    diagnostic="$(printf '%s' "$diagnostic" | sed 's/\\"/"/g')"
    ;;
esac
prefix="Error parsing image name \"docker://$destination\": reading manifest"
case "$diagnostic" in
  "$prefix"*) detail="${diagnostic#"$prefix"}" ;;
  *)
    echo "candidate absence could not be established" >&2
    exit 1
    ;;
esac
if printf '%s\n' "$detail" | LC_ALL=C grep -Eiq \
  '(unauthorized|authentication|required|denied|status(code)?[^0-9]*(401|403|429|5[0-9][0-9])|too many requests|rate limit|timeout|connection|network|tls|certificate)'; then
  echo "candidate absence could not be established" >&2
  exit 1
fi
case "$detail" in
  *': manifest unknown'|*': name unknown: repository name not known to registry') ;;
  *)
    echo "candidate absence could not be established" >&2
    exit 1
    ;;
esac

skopeo copy --preserve-digests --authfile "$auth_file" \
  "oci-archive:$proof_dir/seag-ci-toolchain.oci.tar" \
  "docker://$destination"
observed_manifest="$auth_dir/observed-manifest.json"
skopeo inspect --raw --authfile "$auth_file" \
  "docker://$destination" >"$observed_manifest"
observed_digest="sha256:$(sha256sum "$observed_manifest" | cut -d' ' -f1)"
test "$observed_digest" = "$expected_digest"

test ! -e "$publication_dir"
mkdir "$publication_dir"
cp "$admission_dir/admission.json" "$publication_dir/admission.json"
printf '%s\n' "$destination" >"$publication_dir/destination.txt"
printf '%s\n' "$observed_digest" \
  >"$publication_dir/registry-manifest-digest.txt"
printf '%s\n' "$CI_JOB_ID" >"$publication_dir/publisher-job-id.txt"
