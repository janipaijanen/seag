#!/bin/sh
# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

# Verify the complete external-command contract of the credential-bearing
# publisher before it performs any network or credential operation. With an
# output directory, retain the real CI image and tool versions as evidence.
set -eu

for command_name in \
  cat chmod cp curl cut dirname grep mkdir mktemp python rm sed sha256sum \
  skopeo tr wc
do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "publisher runtime is missing required command: $command_name" >&2
    exit 1
  }
done

if test "$#" -eq 0; then
  exit 0
fi
test "$#" -eq 1 || {
  echo "usage: $0 [evidence-directory]" >&2
  exit 2
}
test -n "${CI_JOB_IMAGE:-}" || {
  echo "CI_JOB_IMAGE is required when recording runtime evidence" >&2
  exit 1
}

python -c 'import json, re, sys; assert sys.version_info >= (3, 11)'
skopeo --version >/dev/null

evidence_dir=$1
test ! -e "$evidence_dir"
mkdir "$evidence_dir"
printf '%s\n' "$CI_JOB_IMAGE" >"$evidence_dir/image.txt"
python --version >"$evidence_dir/python-version.txt" 2>&1
skopeo --version >"$evidence_dir/skopeo-version.txt"
(
  cd "$evidence_dir"
  sha256sum image.txt python-version.txt skopeo-version.txt >SHA256SUMS
)
