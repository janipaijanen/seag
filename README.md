<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# SEAG

**Semantic Engineering for Agentic Development**

*A semantic capture and transformation framework for meaning-preserving software work by humans and LLM agents.*

SEAG provides a framework for capturing project-specific semantics once and
transforming them into the representations needed by people, LLM agents, and
tools. It keeps product language, domain rules, lifecycle vocabularies,
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

## Explicit non-goal: process modelling

SEAG is not process-modelling, workflow-design, orchestration, or execution
tooling. Trying to encode process flow in SEAG is unsupported and will waste
effort: the framework will not grow sequence flows, gateways, transitions,
concurrency, timers, compensation, task routing, or runtime semantics.

SEAG may define the meaning of terms such as Activity, Event, State, Rule, and
Role. It may also reference an external BPMN model, state machine, decision
table, or workflow by stable identifier and provenance. The external notation
remains authoritative for process behaviour. SEAG captures meaning across
representations; it does not replace those representations.

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

## Standards and conformance

SEAG pins the standards used for normative language, language tags,
identifiers, JSON schemas, timestamps, Unicode, provenance mappings, glossary
mappings, and published licence expressions. Listing an external standard does
not by itself claim compatibility: core requirements, conditional use,
semantic mappings, and export profiles are distinguished explicitly.

The authoritative policy is [standards and conformance](docs/conformance.md).
Its machine-readable register is [`standards.yaml`](standards.yaml).

## Release candidates

GitLab CI validates the repository and bakes a reproducible source
release-candidate archive with a content manifest, SHA-256 checksum, and build
provenance record. Candidate artifacts are review inputs, not public-release or
stability claims. Stable publication tags fail closed until the publication
gate and release-specific independent review requirements are satisfied.

`VERSION` is the authoritative package version and release tags must match it
exactly as `v<version>`, following the AGF release-numbering pattern. Commit
identity stays in build provenance rather than being embedded in a synthetic
CI version. See the [release and version policy](docs/release-policy.md).

Build and verify the same candidate locally:

```sh
python3 scripts/build-release-bundle.py \
  --commit HEAD --output-dir dist --verify
```

See [the project charter](docs/charter.md) and [the 0.1 roadmap](docs/roadmap-0.1.md).
External vocabulary reuse and divergence follow the
[term adoption and provenance policy](docs/term-adoption-and-provenance.md).
Portable identity and generated representations follow the
[identity, bundle, and variant policy](docs/identity-bundles-and-variants.md).
Multilingual values and generated language variants follow the
[BCP 47 language-tag policy](docs/language-tags.md).
Responsibility contracts are defined in [SEAG roles](docs/roles.md), and
expression discipline in [semantic minimality](docs/semantic-minimality.md).

## Licensing intent

Tooling code is licensed under Apache-2.0. Framework and methodology documents
are licensed under CC BY 4.0. Complete licence texts, the per-file SPDX policy,
and rules for non-commentable formats are documented in
[licensing and SPDX declarations](docs/licensing.md).
