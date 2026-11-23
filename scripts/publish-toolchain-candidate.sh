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
test -n "${CI_SERVER_URL:-}" -a -n "${CI_SERVER_HOST:-}" -a \
  -n "${CI_REGISTRY:-}"
test "$CI_SERVER_URL" = "https://$CI_SERVER_HOST"
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
trap 'rm -rf "$auth_dir"' EXIT

repository_and_tag="${destination#"$CI_REGISTRY"/}"
repository="${repository_and_tag%:*}"
tag="${repository_and_tag##*:}"
case "$repository:$tag" in
  :*|*:|*[@[:space:]]*)
    echo "candidate destination has an unsupported repository or tag" >&2
    exit 1
    ;;
esac
readonly repository tag
readonly manifest_url="https://$CI_REGISTRY/v2/$repository/manifests/$tag"
readonly response_headers="$auth_dir/response-headers"
readonly response_body="$auth_dir/response-body"
readonly token_body="$auth_dir/token-body"
readonly netrc_file="$auth_dir/netrc"
readonly bearer_header="$auth_dir/bearer-header"

# Discover the registry's authentication endpoint without sending a credential.
challenge_status="$(curl --silent --show-error --max-time 30 --max-redirs 0 \
  --request GET --header 'Accept: application/vnd.oci.image.manifest.v1+json' \
  --dump-header "$response_headers" --output "$response_body" \
  --write-out '%{http_code}' "$manifest_url")" || {
    echo "candidate absence could not be established" >&2
    exit 1
  }
if test "$challenge_status" = 200; then
  echo "candidate destination already exists" >&2
  exit 1
fi
test "$challenge_status" = 401 || {
  echo "candidate absence could not be established" >&2
  exit 1
}
challenge="$(tr -d '\r' <"$response_headers" | awk '
  BEGIN { IGNORECASE=1 }
  /^WWW-Authenticate:[[:space:]]*Bearer[[:space:]]/ {
    sub(/^[^:]*:[[:space:]]*/, ""); print
  }
')"
test "$(printf '%s\n' "$challenge" | awk 'NF {count++} END {print count+0}')" -eq 1 || {
  echo "candidate absence could not be established" >&2
  exit 1
}
realm="$(printf '%s\n' "$challenge" | sed -n 's/.*realm="\([^"]*\)".*/\1/p')"
service="$(printf '%s\n' "$challenge" | sed -n 's/.*service="\([^"]*\)".*/\1/p')"
test "$realm" = "${CI_SERVER_URL%/}/jwt/auth" -a -n "$service" || {
  echo "candidate absence could not be established" >&2
  exit 1
}
case "$CI_REGISTRY_USER:$CI_REGISTRY_PASSWORD" in
  *[!A-Za-z0-9._~+=:/-]*)
    echo "registry credential has an unsupported transport form" >&2
    exit 1
    ;;
esac
realm_host="${realm#https://}"
realm_host="${realm_host%%/*}"
test "$realm_host" = "$CI_SERVER_HOST" || {
  echo "candidate absence could not be established" >&2
  exit 1
}
printf 'machine %s login %s password %s\n' \
  "$realm_host" "$CI_REGISTRY_USER" "$CI_REGISTRY_PASSWORD" >"$netrc_file"
chmod 0600 "$netrc_file"
token_status="$(curl --silent --show-error --max-time 30 --max-redirs 0 \
  --netrc-file "$netrc_file" --get \
  --data-urlencode "service=$service" \
  --data-urlencode "scope=repository:$repository:pull,push" \
  --output "$token_body" --write-out '%{http_code}' "$realm")" || {
    echo "candidate absence could not be established" >&2
    exit 1
  }
test "$token_status" = 200 -a "$(wc -c <"$token_body")" -le 65536 || {
  echo "candidate absence could not be established" >&2
  exit 1
}
token_fields="$(LC_ALL=C grep -oE '"(token|access_token)"[[:space:]]*:[[:space:]]*"[A-Za-z0-9._~-]+"' "$token_body" || true)"
test "$(printf '%s\n' "$token_fields" | awk 'NF {count++} END {print count+0}')" -eq 1 || {
  echo "candidate absence could not be established" >&2
  exit 1
}
token="$(printf '%s\n' "$token_fields" | sed 's/^[^:]*:[[:space:]]*"//; s/"$//')"
test -n "$token" || {
  echo "candidate absence could not be established" >&2
  exit 1
}
printf 'Authorization: Bearer %s\n' "$token" >"$bearer_header"
chmod 0600 "$bearer_header"

# Preserve the HTTP status and complete structured body. Only one exact
# missing-resource code carried by HTTP 404 is definite absence.
manifest_status="$(curl --silent --show-error --max-time 30 --max-redirs 0 \
  --request GET --header 'Accept: application/vnd.oci.image.manifest.v1+json' \
  --header "@$bearer_header" --dump-header "$response_headers" \
  --output "$response_body" --write-out '%{http_code}' "$manifest_url")" || {
    echo "candidate absence could not be established" >&2
    exit 1
  }
if test "$manifest_status" = 200; then
  echo "candidate destination already exists" >&2
  exit 1
fi
test "$manifest_status" = 404 -a "$(wc -c <"$response_body")" -le 65536 || {
  echo "candidate absence could not be established" >&2
  exit 1
}
error_codes="$(LC_ALL=C grep -oE '"code"[[:space:]]*:[[:space:]]*"[A-Z_]+"' "$response_body" || true)"
test "$(printf '%s\n' "$error_codes" | awk 'NF {count++} END {print count+0}')" -eq 1 || {
  echo "candidate absence could not be established" >&2
  exit 1
}
compact_error="$(tr -d '\r\n\t ' <"$response_body")"
case "$compact_error" in
  '{"errors":[{"code":"MANIFEST_UNKNOWN",'*'}]}'|\
  '{"errors":[{"code":"NAME_UNKNOWN",'*'}]}') ;;
  *)
    echo "candidate absence could not be established" >&2
    exit 1
    ;;
esac
case "$compact_error" in
  *'},{'*)
    echo "candidate absence could not be established" >&2
    exit 1
    ;;
esac
case "$error_codes" in
  *'"MANIFEST_UNKNOWN"'|*'"NAME_UNKNOWN"') ;;
  *)
    echo "candidate absence could not be established" >&2
    exit 1
    ;;
esac

printf '%s' "$CI_REGISTRY_PASSWORD" | skopeo login \
  --authfile "$auth_file" \
  --username "$CI_REGISTRY_USER" \
  --password-stdin "$CI_REGISTRY"

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
