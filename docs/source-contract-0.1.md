<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# SEAG source contract 0.1 draft

This draft defines a small, domain-neutral JSON source format. It implements a
bounded part of roadmap increments 1 and 2. It does not define a domain
ontology, process model, exchange format, release procedure, or publication
claim. `schema/source-0.1.schema.json` describes the file shapes; the CLI also
checks cross-file and semantic invariants that JSON Schema cannot express.

## Files and identity

One `manifest.json` declares `seag_schema: "0.1-draft"`, a permanent absolute
`bundle_id`, one resolved absolute `namespace` ending in `#` or `/`, title,
default language, draft status, licence, and an inventory of fragments. Each
inventory entry has a stable `fragment_id`, relative file path, role, and
SHA-256 of the exact file bytes. A fragment repeats the schema version,
`bundle_id`, `namespace`, `fragment_id`, role, language, and draft revision so
it remains identifiable when separated. The repeated values must match the
manifest. No network resolution is needed. The namespace plus each local
record `id` is its expanded identity. IDs are stable, unique across all
fragments, and must not be reused for another meaning.

`records` may contain `concept`, `lifecycle_state`, `rule_reference`,
`external_reference`, and `proposition`. Concepts and vocabulary records have
`label` and `definition`. Rule and external references also have an absolute
`iri` naming the referenced artifact. Every
record has `status` (`proposed`, `confirmed`, `deprecated`, or `unresolved`),
`implementation_alignment` (`unchecked`, `matches`, `diverges`, or
`not_applicable`), and provenance with `source`, `locator`, `proposer`, a
separate `normative` boolean, and `verification_status` (`unresolved`,
`qualified`, `verified`, or `rejected`). A confirmed claim needs a `confirmation`
with separate decision and review references, ISO calendar dates, confirmer,
and reviewer. The review date must be no later than the decision date. Qualified
evidence can be a traceable project-owned source with an explicit locator; it
need not be an external publication. Qualified or verified evidence can support a declared decision;
the evidence status does not itself decide meaning. If the same declared actor
proposed and confirmed, `role_collapse_note` records the distinct authorities;
if the proposer reviewed, or the same actor reviewed and confirmed,
`review_limit` discloses that the review is not independent. The validator checks declared fields and disclosures, not actor
identity, authority, the substance of either action, or actual independence.
External-term dispositions still need independent review under the governing
term-adoption policy; a self-review disclosure cannot satisfy that requirement.
A deprecated claim needs a replacement or rationale. A missing fact is
recorded as `unresolved`, never filled by a validator default.

## Proposition vocabulary

`source` and `target` name local record IDs. `predicate` is one of:

| Predicate | Source | Target |
| --- | --- | --- |
| `is a kind of` | concept | concept |
| `is part of` | concept | concept |
| `refers to` | concept | concept or external_reference |
| `has lifecycle state` | concept | lifecycle_state |
| `is governed by rule` | concept | rule_reference |
| `named association` | concept | concept |

A named association also has a bounded static `name` and `definition`, plus two explicit end cardinalities,
`source_cardinality` and `target_cardinality`: `0..1`, `1..1`, `1..*`,
`0..*`, or `unresolved`. `unresolved` is allowed only while the proposition is
not confirmed. Direction is always source to target; do not infer its inverse.
Taxonomy (`is a kind of`) cycles are invalid. Process or transition names such
as `precedes`, `changes state to`, `triggers` and `is followed by`, and vague
names such as `relates to`, `supports`, `uses`, and `has many` are rejected even
inside `named association`. The 0.1 draft has closed field sets for every
record kind and file shape: an unknown field such as `guard`, `next_state`,
`sequence`, or `workflow` fails validation rather than carrying unreviewed
transition semantics. A future extension needs a new versioned contract.
Association names are normalised for case, compatibility characters and common
separators; hidden format characters fail. The process-name rule only rejects
recognised initial action phrases, not a process-like stem anywhere in a name:
`has transition fee` and `enables access to` are allowed as static names.
This is a bounded lexical check, not a proof that all paraphrases or look-alike
characters are excluded.
Free-text definitions are not machine-interpreted, so human review must still
check that a permitted static name is not used to smuggle process meaning.
Static lifecycle names do not imply transitions.

## Variants and limits

Variant metadata lives in a detached JSON record, never inside the source
manifest (which would make its own source digest circular). Each must identify an
immutable absolute `variant_id` and `representation_of` release ID, format,
source manifest digest, output digest, generator, generation timestamp,
`lossless` boolean, and explicit `omissions` and `unsupported_constructs`
arrays. This validator checks metadata shape, not generation, byte matching,
round-trip fidelity, or release immutability across revisions. A claimed
lossless variant with unsupported constructs is invalid. Additional source
fields are reserved for a future version, not silently accepted by this one.
The timestamp is an ISO date-time with timezone. The absolute-IRI check accepts
any syntactically valid scheme with nonempty remainder, including `tag:` and
`did:`; it does not adjudicate scheme safety or dereference targets. Consumers
must apply their own trusted-scheme policy before using a link.

Run `python3 -m seag.validate manifest.json` or
`python3 -m seag.validate --variant variant.json`. The command prints actionable
errors with record/file locations and exits nonzero. It does not modify input.
