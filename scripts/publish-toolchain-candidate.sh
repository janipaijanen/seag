#!/bin/sh
# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

# Publish only the already admitted OCI archive. This script deliberately
# distinguishes a definite registry absence from every other lookup failure.
set -eu

# The pinned publisher image must supply the parser before any network or
# credential operation. Fail closed if that runtime contract changes.
command -v python >/dev/null

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
readonly manifest_accept='Accept: application/vnd.oci.image.manifest.v1+json, application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.v2+json, application/vnd.docker.distribution.manifest.list.v2+json'
readonly response_headers="$auth_dir/response-headers"
readonly response_body="$auth_dir/response-body"
readonly token_body="$auth_dir/token-body"
readonly netrc_file="$auth_dir/netrc"
readonly bearer_header="$auth_dir/bearer-header"

# Discover the registry's authentication endpoint without sending a credential.
challenge_status="$(
  ulimit -f 128
  exec curl --silent --show-error --max-time 30 --max-redirs 0 \
    --request GET --header "$manifest_accept" \
    --dump-header "$response_headers" --output "$response_body" \
    --write-out '%{http_code}' "$manifest_url"
)" || {
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
challenge_values="$(python - "$response_headers" "$repository" <<'PY'
import re
import sys


raw_headers = open(sys.argv[1], "rb").read()
if b"\r" in raw_headers.replace(b"\r\n", b""):
    raise ValueError("invalid authentication response line ending")
sections = [
    section.rstrip(b"\n").split(b"\n")
    for section in raw_headers.replace(b"\r\n", b"\n").split(b"\n\n")
    if section
]
if not sections:
    raise ValueError("authentication response has no header section")
for section in sections:
    if not re.fullmatch(
        rb"HTTP/[0-9]+(?:\.[0-9]+)?[ \t]+[0-9]{3}(?:[ \t]+[^\x00-\x1f\x7f]*)?",
        section[0],
    ):
        raise ValueError("invalid authentication response status line")
final_section = sections[-1]
if not re.match(rb"HTTP/[0-9]+(?:\.[0-9]+)?[ \t]+401(?:[ \t]|$)", final_section[0]):
    raise ValueError("final authentication response is not 401")
lines = final_section[1:]
if any(line[:1] in {b" ", b"\t"} for line in lines):
    raise ValueError("folded authentication header")
values = []
for line in lines:
    name, separator, value = line.partition(b":")
    if not separator or not re.fullmatch(rb"[!#$%&'*+.^_`|~0-9A-Za-z-]+", name):
        raise ValueError("malformed authentication response header")
    if name.lower() == b"www-authenticate":
        values.append(value.strip().decode("ascii"))
if len(values) != 1:
    raise ValueError("authentication challenge is ambiguous")
match = re.fullmatch(r"Bearer[ \t]+(.+)", values[0], re.IGNORECASE)
if not match:
    raise ValueError("unsupported authentication challenge")
text = match.group(1)
params = {}
position = 0
while position < len(text):
    item = re.match(
        r'[ \t]*([A-Za-z][A-Za-z0-9_-]*)[ \t]*=[ \t]*"([^"\\\x00-\x1f\x7f]*)"',
        text[position:],
    )
    if not item:
        raise ValueError("malformed authentication parameter")
    key, value = item.groups()
    key = key.lower()
    if key in params:
        raise ValueError("duplicate authentication parameter")
    params[key] = value
    position += item.end()
    while position < len(text) and text[position] in " \t":
        position += 1
    if position == len(text):
        break
    if text[position] != ",":
        raise ValueError("malformed authentication parameter separator")
    position += 1
    if not text[position:].strip():
        raise ValueError("trailing authentication parameter separator")
if not {"realm", "service"} <= set(params) or not set(params) <= {
    "realm",
    "service",
    "scope",
}:
    raise ValueError("unexpected authentication parameter set")
if not params["realm"] or not re.fullmatch(r"[A-Za-z0-9._:/-]+", params["service"]):
    raise ValueError("invalid authentication parameter value")
expected_scope = f"repository:{sys.argv[2]}:pull"
if "scope" in params and params["scope"] != expected_scope:
    raise ValueError("authentication scope does not match the read-only request")
print(params["realm"])
print(params["service"])
PY
)" || {
  echo "candidate absence could not be established" >&2
  exit 1
}
test "$(printf '%s\n' "$challenge_values" | wc -l)" -eq 2 || {
  echo "candidate absence could not be established" >&2
  exit 1
}
realm="$(printf '%s\n' "$challenge_values" | sed -n '1p')"
service="$(printf '%s\n' "$challenge_values" | sed -n '2p')"
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
token_status="$(
  ulimit -f 128
  exec curl --silent --show-error --max-time 30 --max-redirs 0 \
    --netrc-file "$netrc_file" --get \
    --data-urlencode "service=$service" \
    --data-urlencode "scope=repository:$repository:pull" \
    --output "$token_body" --write-out '%{http_code}' "$realm"
)" || {
    echo "candidate absence could not be established" >&2
    exit 1
  }
test "$token_status" = 200 -a "$(wc -c <"$token_body")" -le 65536 || {
  echo "candidate absence could not be established" >&2
  exit 1
}
token="$(python - "$token_body" <<'PY'
import json
import re
import sys


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON member")
        result[key] = value
    return result


def reject_non_json_constant(value):
    raise ValueError(f"invalid JSON constant: {value}")


with open(sys.argv[1], encoding="utf-8") as stream:
    document = json.load(
        stream,
        object_pairs_hook=unique_object,
        parse_constant=reject_non_json_constant,
    )
if not isinstance(document, dict):
    raise ValueError("token response is not an object")
allowed = {"token", "access_token", "expires_in", "issued_at"}
if not set(document) <= allowed:
    raise ValueError("unexpected token-response member")
present = [key for key in ("token", "access_token") if key in document]
if len(present) != 1:
    raise ValueError("token response is ambiguous")
token = document[present[0]]
if not isinstance(token, str) or not re.fullmatch(r"[A-Za-z0-9._~-]+", token):
    raise ValueError("invalid token")
if "expires_in" in document and (
    isinstance(document["expires_in"], bool)
    or not isinstance(document["expires_in"], int)
    or document["expires_in"] < 0
):
    raise ValueError("invalid token lifetime")
if "issued_at" in document and not isinstance(document["issued_at"], str):
    raise ValueError("invalid token issue time")
print(token)
PY
)" || {
  echo "candidate absence could not be established" >&2
  exit 1
}
test -n "$token" || {
  echo "candidate absence could not be established" >&2
  exit 1
}
printf 'Authorization: Bearer %s\n' "$token" >"$bearer_header"
chmod 0600 "$bearer_header"

# Preserve the HTTP status and complete structured body. Only one exact
# missing-resource code carried by HTTP 404 is definite absence.
manifest_status="$(
  ulimit -f 128
  exec curl --silent --show-error --max-time 30 --max-redirs 0 \
    --request GET --header "$manifest_accept" --header "@$bearer_header" \
    --dump-header "$response_headers" --output "$response_body" \
    --write-out '%{http_code}' "$manifest_url"
)" || {
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
python - "$response_body" <<'PY' || {
import json
import sys


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON member")
        result[key] = value
    return result


def reject_non_json_constant(value):
    raise ValueError(f"invalid JSON constant: {value}")


with open(sys.argv[1], encoding="utf-8") as stream:
    document = json.load(
        stream,
        object_pairs_hook=unique_object,
        parse_constant=reject_non_json_constant,
    )
if not isinstance(document, dict) or set(document) != {"errors"}:
    raise ValueError("invalid registry error document")
errors = document["errors"]
if not isinstance(errors, list) or len(errors) != 1:
    raise ValueError("registry error is ambiguous")
error = errors[0]
if not isinstance(error, dict) or not set(error) <= {"code", "message", "detail"}:
    raise ValueError("invalid registry error object")
if error.get("code") not in {"MANIFEST_UNKNOWN", "NAME_UNKNOWN"}:
    raise ValueError("resource absence was not established")
if "message" in error and not isinstance(error["message"], str):
    raise ValueError("invalid registry error message")


def contains_nested_code(value):
    if isinstance(value, dict):
        return "code" in value or any(contains_nested_code(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_nested_code(item) for item in value)
    return False


if "detail" in error and contains_nested_code(error["detail"]):
    raise ValueError("contradictory nested error code")
PY
  echo "candidate absence could not be established" >&2
  exit 1
}

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
