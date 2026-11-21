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
`label` and `definition`. An external reference has an absolute `iri`. Every
record has `status` (`proposed`, `confirmed`, `deprecated`, or `unresolved`),
`implementation_alignment` (`unchecked`, `matches`, `diverges`, or
`not_applicable`), and provenance with `source`, `locator`, and a separate
`normative` boolean. A confirmed claim needs a nonempty decision reference;
validation of the decision's authority remains a human review task. A missing
fact is recorded as `unresolved`, never filled by a validator default.

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

A named association also has a `name` and two explicit end cardinalities,
`source_cardinality` and `target_cardinality`: `0..1`, `1..1`, `1..*`,
`0..*`, or `unresolved`. `unresolved` is allowed only while the proposition is
not confirmed. Direction is always source to target; do not infer its inverse.
Taxonomy (`is a kind of`) cycles are invalid. A process-flow or state-transition
edge is outside this vocabulary and is rejected. Static lifecycle names do not
imply transitions.

## Variants and limits

Variant metadata lives in a detached JSON record, never inside the source
manifest (which would make its own source digest circular). Each must identify an
immutable absolute `variant_id` and `representation_of` release ID, format,
source manifest digest, output digest, generator, generation timestamp,
`lossless` boolean, and explicit `omissions` and `unsupported_constructs`
arrays. This validator checks metadata shape, not generation, byte matching,
round-trip fidelity, or release immutability across revisions. A claimed
lossless variant with unsupported constructs is invalid. Source files can
carry additional fields for future interpretation; this validator preserves
them but makes no conformance claim about their semantics.

Run `python3 -m seag.validate manifest.json` or
`python3 -m seag.validate --variant variant.json`. The command prints actionable
errors with record/file locations and exits nonzero. It does not modify input.
