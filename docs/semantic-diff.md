<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Semantic diff and bounded conflict detection

> **Status: 0.2.0-alpha.1 evaluation capability.** It is not part of the
> immutable 0.1.0 contract, a supported compatibility baseline, or evidence
> that the 0.2 roadmap exit gate has passed.

SEAG semantic diff compares validated source bundles by stable expanded record
identity. It helps a reviewer see meaning-affecting changes that may be obscured
by JSON layout, fragment movement, or an otherwise clean textual merge. It does
not decide whether a change is correct, prove that two definitions are
equivalent, or merge semantic content automatically.

## Commands

Two-way review:

```sh
python3 -m seag.semantic_diff BEFORE/manifest.json AFTER/manifest.json
python3 -m seag.semantic_diff BEFORE/manifest.json AFTER/manifest.json \
  --format json --fail-on breaking
```

Bounded three-way conflict detection:

```sh
python3 -m seag.semantic_diff \
  --base BASE/manifest.json \
  --ours OURS/manifest.json \
  --theirs THEIRS/manifest.json \
  --format json
```

Every input must independently satisfy the SEAG source validator. Input failure
returns exit code 2. A valid comparison returns 0 unless `--fail-on` selects a
finding that exists:

| Policy | Exit 1 when |
| --- | --- |
| `never` | never |
| `change` | either branch contains a classified change |
| `breaking` | a classified change has `breaking` severity |
| `conflict` | a three-way comparison contains a bounded conflict |

The default is `never` for two-way review and `conflict` for three-way review.
Thus ordinary two-way use reports rather than blocks, while three-way use fails
closed for the implemented conflict classes.

## Result contract

JSON output is UTF-8 with sorted object keys and deterministic array ordering.
It contains no input filesystem path or clock value. Each source is identified
by role, bundle ID, namespace, source-contract version, and exact manifest
SHA-256. The generator records the SEAG package version.
Because an untagged checkout may contain post-release development while still
reporting the last stable package version, `implementation_sha256` also binds
the result to the exact comparison, source-loading, validation, transformation,
and version files. A published release must still be identified by its tag and
bundle digest; this implementation digest is not a substitute release number.

Two-way output uses `seag/semantic-diff/0.2-draft.1` and contains a summary plus
ordered `changes`. Three-way output uses
`seag/semantic-conflict/0.2-draft.1` and contains each branch's changes plus
ordered `conflicts`. These are experimental format identities: consumers must
reject unknown identities rather than guessing compatibility. The
[JSON Schema](../schema/semantic-review-0.2.schema.json) describes both closed
result shapes; semantic ordering and policy rules remain normative here.

Ordering is by expanded record identity, diagnostic code, and field. Bundle
findings precede record findings. Exact before/after values are retained in JSON
so a reviewer or another deterministic tool need not reconstruct the compared
snapshots. Consequently, diff output can contain all content and provenance of
an added or removed record and must receive at least the access classification
of its inputs.

Human output escapes the record identity before writing it to a terminal.
Machine JSON retains source Unicode and values exactly; consumers must render
it as untrusted data. The implementation inherits the validator's local-file
and confined-fragment behavior, performs no network access, and does not execute
labels, definitions, locators, or IRIs. It does not yet impose corpus or output
size limits, so resource budgets remain an explicit pre-0.2 hardening item.

## Change taxonomy

Severity has a deliberately bounded meaning:

- `informational` identifies inventory or descriptive metadata change;
- `review` identifies a meaning or evidence change requiring human review; and
- `breaking` identifies identity, removal, relationship, cardinality, external
  target, licence, or confirmed/deprecated-state regression that consumers must
  not accept silently.

It is a compatibility signal, not an assessment of business impact.

| Code | Category | Default severity | Meaning |
| --- | --- | --- | --- |
| `SD001` | contract | breaking | source-contract identity changed |
| `SD002` | identity | breaking | bundle ID changed |
| `SD003` | identity | breaking | namespace changed |
| `SD010` | metadata | informational | bundle title changed |
| `SD011` | language | review | default language changed |
| `SD012` | status | review | bundle status changed |
| `SD013` | licensing | breaking | bundle licence changed |
| `SD100` | inventory | informational | record added |
| `SD101` | inventory | breaking | record removed |
| `SD200` | identity | breaking | record kind changed |
| `SD210` | definition | review | preferred label changed |
| `SD211` | definition | review | definition changed |
| `SD220` | status | review or breaking | semantic status changed |
| `SD221` | status | review | implementation alignment changed |
| `SD230` | provenance | review | provenance changed |
| `SD231` | confirmation | review | confirmation evidence changed |
| `SD232` | status | review | replacement or rationale changed |
| `SD240`–`SD243` | relationship | breaking or review | predicate, endpoint, or name changed |
| `SD250`–`SD251` | cardinality | breaking | either endpoint cardinality changed |
| `SD260` | external reference | breaking | external IRI changed |
| `SD261` | language | review | inherited fragment language changed for a record |
| `SD270` | definition | breaking | singular-number declaration changed |
| `SD299` | record | review | another validated record field changed |

`SD220` is breaking when a confirmed record loses confirmed status or a
deprecated record is reactivated. Other status changes still require review.
Because source validation currently requires a single contract version,
`SD001` is reserved for comparison compatibility with future readers rather
than a currently reachable cross-version success case.

Fragment filename, fragment order, formatting, fragment revision labels, and
inventory digests are transport changes, not record-semantic changes, and are
not reported. A fragment's language is inherited by its records and is
therefore compared as `SD261`. The compared manifest digests still expose that
the exact source snapshots differ.

## Three-way conflict boundary

| Code | Conflict |
| --- | --- |
| `SC001` | a branch changes the base bundle ID or namespace |
| `SC100` | both branches change the same semantic leaf or bundle field differently |
| `SC101` | one branch removes a record that the other modifies |
| `SC102` | both branches add the same expanded identity differently |
| `SC103` | a kind, predicate, source, or target change overlaps another branch edit |
| `SC104` | a status, provenance, confirmation, or replacement change overlaps another branch edit |

Other different-field edits are not called conflicts. `SC103` prevents a clean
textual merge from applying an edit to a structurally different relationship or
record kind. `SC104` prevents newly edited meaning from silently inheriting a
confirmation or evidence change that reviewed different content. A one-branch
addition, a one-branch deletion with the other branch unchanged, and identical
changes on both branches are not conflicts. The result does not perform a
merge; the source files remain authoritative and a human resolves every
reported conflict.

The algorithm compares declared JSON values. It does not interpret prose,
infer aliases, detect equivalent definitions, assess provenance truth, compare
external resource content, or find conflicts between different records whose
meanings happen to overlap. Those remain explicit human-review boundaries.
The 0.1 source contract has no mapping record, so mapping-change diagnostics do
not yet exist and must not be inferred from labels. The command also does not
discover Git revisions: callers provide independently materialized, validated
bundle snapshots.

## Git use

Git is a recommended carrier, not an input requirement. CI can materialize the
base, target, and branch bundles into separate directories and call the command.
Do not run the tool on a textually conflicted or invalid working tree: each
snapshot must validate first. `--fail-on conflict` can protect a merge without
turning SEAG into an approval workflow.

For example, a GitLab merge-request job with complete Git history can compare a
bundle stored at `semantics/manifest.json` against the merge-request base:

```sh
mkdir -p .semantic-review/base .semantic-review/head
git archive "$CI_MERGE_REQUEST_DIFF_BASE_SHA" semantics \
  | tar -x -C .semantic-review/base
git archive "$CI_COMMIT_SHA" semantics \
  | tar -x -C .semantic-review/head
python3 -m seag.semantic_diff \
  .semantic-review/base/semantics/manifest.json \
  .semantic-review/head/semantics/manifest.json \
  --format json --fail-on breaking
```

The job must pin the SEAG release or commit, retain the JSON result as a review
artifact, and arrange semantic-owner review outside SEAG. The example is not a
complete CI policy: the adopting project decides which severities block, who
may approve, how protected content is stored, and how the exact base revision
is obtained on its hosting platform.
