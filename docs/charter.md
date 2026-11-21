# SEAG project charter

## Purpose

SEAG provides a semantic backbone for agentic software development. It helps a
team establish what product concepts mean, how they relate, which rules govern
them, and where implementation and verification evidence can be found.

Its primary failure mode to prevent is semantic drift: UI text, requirements,
agent instructions, code, tests, and product decisions silently using the same
word for different things or different words for the same thing.

## Design principles

1. **Humans remain the semantic authority.** Agents may discover, propose,
   validate, and trace meanings. They may not convert an unresolved proposal
   into a product decision.
2. **One authoritative home per statement.** Other artifacts reference stable
   identifiers instead of duplicating definitions or rules.
3. **Unknown is not optional.** Missing cardinality or policy remains unresolved
   until evidence or a decision settles it.
4. **Meaning and execution use different notations.** A concept map explains
   meaning. A state model explains a lifecycle. A decision table explains a
   conditional rule. A workflow diagram explains ordering and handoffs.
5. **Traceability is evidence, not proof.** A link to code or a test identifies
   a claim to inspect; it does not establish correctness by itself.
6. **Small slices precede whole-domain models.** Concepts enter SEAG when a
   product slice needs them. A comprehensive ontology is not a prerequisite.
7. **Interoperability is explicit and optional.** AGF, Ponytail, Caveman Mode,
   and future integrations use adapters or profiles without becoming required.

## Boundary between artifacts

| Artifact | Owns | Does not own |
|---|---|---|
| Glossary | stable terms, definitions, aliases, status | sequence or authorization |
| Proposition map | typed static relationships and cardinalities | temporal guards or workflow |
| Lifecycle model | states, transitions, events, guards for one state axis | cross-actor orchestration |
| Rule register | scoped conditional and temporal constraints | visual process ordering |
| Decision table | complete outcomes for multi-condition rules | domain definitions |
| Workflow model | ordering, branches, concurrency, handoffs | authoritative concept meaning |
| Trace register | links to requirements, UI, code, tests, evidence | correctness verdicts |

All artifacts cross-reference stable SEAG identifiers.

## Initial controlled relationship vocabulary

The first vocabulary should remain deliberately small:

- `is a kind of`
- `is part of`
- `refers to`
- `consumes`
- `produces`
- `is performed by role`
- `has lifecycle state`
- `is governed by rule`
- named associations with `exactly one`, `zero or one`, `one or more`, or
  `zero or more` cardinality at both ends

Generic phrases such as `relates to`, `supports`, `uses`, and `has many` are not
accepted as authoritative relationships. Conditional `requires` statements
belong in a named rule with scope, evaluation time, outcome, and unknown-input
behaviour.

## Rediflow provenance and sanitation

Rediflow is the originating reference project and may be credited publicly.
Material extracted from it must:

- contain no credentials, personal data, customer-confidential information,
  restricted records, or unpublished security details;
- distinguish observed implementation facts from owner-confirmed product
  decisions and proposed semantics;
- replace unnecessary product identifiers and operational details with neutral
  examples;
- retain attribution for material that remains recognizably derived; and
- receive an independent sanitation and semantic review before public release.

The first example should cover a person, project, month, allocation, role,
permission, lifecycle state, and a clearly marked proposed calendar-coverage
rule. It must not imply that Rediflow has implemented or approved that rule.

## Independence

SEAG must not become a Rediflow subdirectory, product-specific documentation
set, AGF extension, Ponytail plugin, or communication-style package. Rediflow
may consume SEAG and provide evidence for its evolution, while each project
keeps its own release cycle, governance, and repository.

## Publication gate

Public release requires:

- a reviewed specification and sanitized example;
- correct Apache-2.0 and CC BY 4.0 license texts and SPDX labelling;
- no copied material with incompatible licensing or uncertain ownership;
- passing schema, validator, documentation, and CXL round-trip checks;
- accurate, pinned compatibility statements;
- contribution and security policies; and
- a clean review by someone who did not author the extraction.

