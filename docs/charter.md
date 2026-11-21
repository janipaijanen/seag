# SEAG project charter

## Purpose

SEAG provides a semantic capture and transformation framework for agentic
software development. It helps a team record what its product concepts mean,
how they relate, which rules govern them, and where implementation and
verification evidence can be found. SEAG then validates that source and exports
it into representation modes required by people, agents, and tools.

SEAG does not define, curate, or publish the domain ontology of Rediflow or any
other adopting project. Domain statements remain owned by the adopting project.

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
6. **Small slices precede whole-domain models.** An adopting project captures
   concepts when a product slice needs them. SEAG does not require a complete
   project ontology before its tools are useful.
7. **Interoperability is explicit and optional.** AGF, Ponytail, Caveman Mode,
   and future integrations use adapters or profiles without becoming required.
8. **Framework and content stay separate.** SEAG owns schemas, transformation
   semantics, validators, exporters, and conformance fixtures. Adopting projects
   own their concepts, propositions, rules, lifecycle models, and evidence.

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

