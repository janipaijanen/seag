<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Canonical source rendering

> **Status: 0.2 alpha evaluation capability.** It is not part of the
> immutable 0.1.0 release, a supported compatibility baseline, or evidence
> that the 0.2 exit gate has passed.

Canonical rendering removes byte-level formatting and ordering noise before
review without changing declared semantic values. It operates on one validated,
immutable input snapshot and either checks its exact bytes or creates a new
bundle directory. It never rewrites an input bundle in place and never
overwrites an existing destination.

## Commands

```sh
python3 -m seag.canonical source/manifest.json --check
python3 -m seag.canonical source/manifest.json --output-dir canonical-source
```

Check mode returns 0 when the manifest and every declared fragment already use
canonical bytes, 1 when valid source differs from canonical bytes, and 2 for an
invalid bundle or operational error. Output mode stages and validates the full
result before creating the requested new directory. The destination parent must
exist and the destination itself must not exist.

## Canonical rules

The experimental renderer:

- emits UTF-8 JSON with two-space indentation, lexicographically sorted object
  keys, and one trailing newline;
- orders fragment inventory entries by `fragment_id` and then path;
- orders records in each fragment by stable local `id`;
- preserves every validated field value, including language, status,
  provenance, confirmation, definitions, and cardinality;
- recalculates every fragment SHA-256 from its canonical bytes; and
- validates the completed output bundle again before publication.

Fragment and record array order has no declared semantic meaning in the 0.1
source contract. The renderer does not normalize Unicode, rewrite prose, change
identifiers, infer singular forms, alter a fragment revision, resolve an IRI,
or retrieve network content.

Only the manifest and fragments declared by that manifest are emitted. Adjacent
README files, licence sidecars, editor settings, and other repository files are
not bundle members and are not copied. A project moving canonical output back
into its repository must preserve or recreate those project-owned files itself.

## Identity and review consequences

Canonical rendering preserves the bundle ID, namespace, fragment IDs, record
IDs, and semantic declarations, but it changes bytes and normally changes
fragment and manifest digests. The output is therefore a new exact source
snapshot even when semantic diff reports no changes. A project must review and
commit that byte change under its own revision and provenance policy; SEAG does
not silently replace the authoritative source.

The canonical renderer is useful with any text editor and does not require Git.
In Git-based projects, `--check` can enforce stable formatting after the team
has deliberately adopted canonical bytes. Do not introduce that check and a
large semantic edit in the same review: separate formatting adoption keeps the
semantic history inspectable.
