# SEAG

**Semantic Engineering for Agentic Development**

*A semantic capture and transformation framework for meaning-preserving software work by humans and LLM agents.*

SEAG provides a framework for capturing project-specific semantics once and
transforming them into the representations needed by people, LLM agents, and
tools. It keeps product language, domain rules, lifecycle models,
implementation, and verification traceable without owning any project's domain
ontology. Its artifacts remain readable and reviewable without an agent runtime.

SEAG originated from semantic and product-modelling work in the Rediflow
project. It is incubated as an independent framework so that its specification,
examples, and tools can be used without Rediflow.

## Version 0.1 scope

SEAG 0.1 will define:

- SEAG's own domain-neutral meta-ontology for semantic artifacts,
  transformations, representations, mappings, and provenance;
- a version-controlled glossary of stable concept identifiers and definitions;
- typed, directional propositions with explicit cardinalities;
- lifecycle axes and references to state models;
- a rule register for conditional and temporal constraints;
- trace links from concepts and rules to requirements, UI, code, tests, and evidence;
- CmapTools-compatible exchange, with CXL treated as an export rather than the
  authoritative source; and
- lightweight validators and domain-neutral conformance fixtures.

Project ontologies, including Rediflow's concepts and rules, remain in their
own projects. A project may use SEAG schemas and tooling without contributing
its domain model to SEAG.

SEAG does not attempt to express workflow ordering, branching, concurrency, or
all executable policy in a concept map. State diagrams, decision tables, and
workflow notation retain their own jobs and share stable SEAG identifiers.

## Related tools and frameworks

SEAG is independently usable. Optional integration profiles may connect it to:

- **Agents Govern Framework (AGF) 3.0** for authority, governance, evidence,
  delegation, and review;
- **Ponytail** for implementation-reduction discipline; and
- **Caveman Mode** for short, direct operational communication.

These are interoperability targets, not dependencies and not bundled
components. SEAG does not claim compatibility until an integration profile has
been implemented and verified against a pinned version.

## Status

Private incubation. No public-release or stability claim has been made.

See [the project charter](docs/charter.md) and [the 0.1 roadmap](docs/roadmap-0.1.md).
External vocabulary reuse and divergence follow the
[term adoption and provenance policy](docs/term-adoption-and-provenance.md).

## Licensing intent

Tooling code will be offered under Apache-2.0. Framework and methodology
documents will be offered under CC BY 4.0. Exact license texts and per-file
SPDX identifiers must be present before public release.
