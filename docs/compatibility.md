<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Compatibility policy

## Separate version surfaces

SEAG distinguishes:

- the package release in `VERSION`;
- each source-contract and schema identifier;
- each representation or integration profile version; and
- external standard versions recorded in `standards.yaml`.

Compatibility on one surface does not imply compatibility on another. A tool
must identify every surface it claims to support.

## Pre-1.0 releases

Before 1.0, a minor package release may make incompatible normative changes. A
patch release preserves the accepted source contract and corrects behavior or
documentation. A prerelease such as `0.1.0-rc.1` is for review and may change
incompatibly before its corresponding stable version.

No prerelease is a supported compatibility baseline unless its release notes
say so explicitly.

## Source-contract behavior

A validator accepts only contract identifiers it implements exactly. It must
reject an unknown contract version, unknown required field, unsupported
required capability, or incompatible profile. It must not silently downgrade,
discard, reinterpret, or default required semantics.

The current validator accepts exactly `0.1-draft.2`. This is a closed draft
contract, not a promise that future SEAG validators will accept it.

### Migration from `0.1-draft`

Release candidates before the draft identifier was corrected required
`grammatical_number: "singular"` on every concept without changing the
`0.1-draft` identifier. That was an incompatible accepted-input change and an
identifier collision, not backward compatibility. `0.1-draft.2` corrects the
contract identity and retains the singular-label requirement.

Consumers detect the boundary by reading both the pinned SEAG package version
or commit and `seag_schema`. A source carrying `0.1-draft` must not be relabelled
automatically. Migration requires a human to inspect every concept label, add
`grammatical_number: "singular"`, revise a plural preferred label where needed,
retain the original source wording in provenance, update fragment digests, and
then set the manifest and every fragment to `0.1-draft.2`. The validator does
not infer grammatical number.

Backward compatibility means that every artifact valid under an identified
older supported contract retains its declared meaning and validates under the
new implementation. Forward compatibility exists only when a contract
explicitly defines ignorable extensions; the 0.1 draft does not.

## Validator changes

A change is incompatible when it alters accepted source meaning, changes a
previously valid artifact to invalid or vice versa, removes a diagnostic
contract relied upon by tooling, or changes a transformation without declared
loss. Such a change requires an appropriate package and contract version change,
migration guidance, fixtures for both sides of the boundary, and release notes.

Stricter rejection of behavior that was already forbidden may be a correction,
but its operational impact must still be disclosed.

## Bundles, variants, and profiles

Bundle and fragment identity is stable across location and representation
changes. A generated variant records its exact source digest, generator, format,
profile, omissions, and unsupported constructs. Profile compatibility is
declared by a tested SEAG version range; a profile name alone proves nothing.

Lossy output is not source-compatible merely because another tool can open it.
Round-trip compatibility requires pinned tools, retained fixtures, comparison
rules, and explicit treatment of every non-representable semantic field.

## Deprecation and migration

Deprecation identifies the affected version, replacement or rationale, earliest
removal version, semantic difference, and migration procedure. Removal before
1.0 still requires release notes and fixtures; pre-1.0 status is not permission
for silent semantic drift.

## Evidence

A compatibility claim names the exact SEAG version or commit, source-contract
version, profile and external-tool versions, test environment, fixtures,
commands, results, limitations, and reviewer. Planned mappings or successful
file parsing are not compatibility evidence.

SEAG currently makes no CmapTools CXL, SKOS serialization, PROV-O
serialization, or cross-version compatibility claim.
