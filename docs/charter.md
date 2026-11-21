<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# SEAG project charter

## Purpose

SEAG provides a semantic capture and transformation framework for agentic
software development. It helps a team record what its product concepts mean,
how they relate, which rules govern them, and where implementation and
verification evidence can be found. SEAG then validates that source and exports
it into representation modes required by people, agents, and tools.

SEAG does not define, curate, or publish the domain ontology of Rediflow or any
other adopting project. Domain statements remain owned by the adopting project.
SEAG does define its own domain-neutral meta-ontology: the kinds of semantic
artifacts it can capture, how mappings and transformations are described, and
how their provenance is verified.

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
4. **SEAG does not model processes.** It captures meaning and references
   process artifacts. State machines, decision tables, and workflow models own
   their behaviour in external notations.
5. **Traceability is evidence, not proof.** A link to code or a test identifies
   a claim to inspect; it does not establish correctness by itself.
6. **Small slices precede whole-domain models.** An adopting project captures
   concepts when a product slice needs them. SEAG does not require a complete
   project ontology before its tools are useful.
7. **Interoperability is explicit and optional.** AGF, Ponytail, Caveman Mode,
   and future integrations use adapters or profiles without becoming required.
8. **Framework and content stay separate.** SEAG owns schemas, transformation
   semantics, validators, exporters, and conformance fixtures. Adopting projects
   own their concepts, propositions, rules, lifecycle models, and evidence.
9. **Adopt, profile, map, or define; never silently redefine.** Standards and
   established vocabularies are reused where their normative meanings fit.
   Every difference is given a distinct SEAG identity and an explicit mapping.
10. **Provenance is reproducible.** A future user can locate the cited source,
    identify its version and exact passage, verify available content by digest,
    and inspect who made and reviewed the SEAG interpretation.
11. **Expressions are minimally complete.** SEAG keeps the smallest expression
    that preserves intended meaning, constraints, uncertainty, and provenance.
12. **Roles are responsibility contracts.** SEAG defines semantic-work roles,
    not mandatory agent instances or a duplicate governance pipeline.

## Boundary between artifacts

| Artifact | Owns | Does not own |
|---|---|---|
| Glossary | stable terms, definitions, aliases, status | sequence or authorization |
| Proposition map | typed static relationships and cardinalities | temporal guards or workflow |
| Lifecycle vocabulary | state identifiers, definitions, and state-axis identity | transitions, guards, or execution |
| Rule register | named semantic constraints and references to authoritative rules | executable decisions or orchestration |
| External decision table | referenced outcomes for multi-condition rules | SEAG domain definitions |
| External workflow model | referenced ordering, branches, concurrency, and handoffs | SEAG semantic authority |
| Trace register | links to requirements, UI, code, tests, evidence | correctness verdicts |

All artifacts cross-reference stable SEAG identifiers.

## SEAG meta-ontology boundary

The initial SEAG meta-ontology covers at least:

- semantic artifacts: concept, term, definition, proposition, association,
  lifecycle axis, state vocabulary, rule reference, trace, and evidence claim;
- framework operations: capture, validate, map, transform, export, import, and
  round-trip verification;
- representation artifacts: source record, generated representation, profile,
  adapter, and conformance fixture;
- vocabulary alignment: adopted term, profiled term, SEAG-defined term,
  deprecated term, and exact, close, broader, narrower, or related mapping; and
- provenance: source, source version, locator, retrieval, digest, licence,
  derivation activity, responsible agent, review, and decision status.

This is a conceptual contract. SEAG may serialize it without requiring users to
adopt RDF or OWL. The authoritative source format must preserve these meanings.

Detailed rules are in
[the term adoption and provenance policy](term-adoption-and-provenance.md).

## Hard non-goal: process and workflow modelling

SEAG will not represent or execute:

- ordered steps or sequence flow;
- gateways, branches, joins, loops, or concurrency;
- state-transition graphs or executable guards;
- timers, retries, compensation, transactions, or error paths;
- task assignment, work queues, orchestration, or automation; or
- process-instance state, event processing, or runtime monitoring.

These capabilities are intentionally out of scope, not deferred roadmap items.
SEAG source and validators should fail clearly when a record attempts to use
SEAG relationships as workflow edges or transition semantics.

SEAG may register the identity, meaning, provenance, version, and location of
an external process artifact. It may map that artifact's vocabulary to project
concepts and verify that referenced identifiers resolve. It must not infer,
generate, validate, simulate, or execute the artifact's behavioural semantics.

This boundary prevents a weak second implementation of BPMN, state-machine,
decision-model, and orchestration tooling. It also keeps SEAG transformations
loss-aware: process behaviour stays in the notation designed to express it.

## Initial controlled relationship vocabulary

The first vocabulary should remain deliberately small:

- `is a kind of`
- `is part of`
- `refers to`
- `has lifecycle state`
- `is governed by rule`
- named associations with `exactly one`, `zero or one`, `one or more`, or
  `zero or more` cardinality at both ends

Generic phrases such as `relates to`, `supports`, `uses`, and `has many` are not
accepted as authoritative relationships. Process-like phrases such as
`precedes`, `triggers`, `changes state to`, and `is followed by` are forbidden
as SEAG proposition predicates. Conditional `requires` statements belong in a
named semantic constraint or an external rule artifact with scope, evaluation
time, outcome, and unknown-input behaviour.

## Rediflow provenance

Rediflow is the originating use case and may be credited publicly. Its ontology,
glossary, rules, product decisions, and evidence remain in Rediflow. They may be
used privately to test SEAG against real complexity, but they are not SEAG
framework content and are not copied into a SEAG release.

SEAG uses invented, domain-neutral conformance fixtures to demonstrate capture,
validation, and transformation. A separate integration test may consume a
project-owned fixture by reference when access and confidentiality allow it;
the source project remains authoritative and the fixture is not redistributed.

## Independence

SEAG must not become a Rediflow subdirectory, ontology distribution,
product-specific documentation set, AGF extension, Ponytail plugin, or
communication-style package. Rediflow may consume SEAG and provide private
conformance evidence for its evolution, while each project keeps its content,
release cycle, governance, and repository.

## Publication gate

Public release requires:

- a reviewed specification and domain-neutral conformance fixtures;
- correct Apache-2.0 and CC BY 4.0 license texts and SPDX labelling;
- no copied material with incompatible licensing or uncertain ownership;
- passing schema, validator, documentation, and CXL round-trip checks;
- accurate, pinned compatibility statements;
- contribution and security policies; and
- a clean independent review of the framework/content boundary.

