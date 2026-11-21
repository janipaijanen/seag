<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# SEAG — Semantic Engineering for Agentic Development

A provenance-preserving semantic source and transformation framework for
software work performed by people and LLM agents.

> **Status: public review, version 0.1.0-rc.3.** This release candidate is
> published for evaluation and review. It is not a stable or supported release,
> makes no production-readiness or complete-conformance claim, and may change
> incompatibly before 0.1.0. Capabilities are reported with AGF's evidence-based
> maturity ladder; nothing is Level 5 Deployable before a supported release.

[Source contract](docs/source-contract-0.1.md) ·
[Concept maps and ontologies](docs/introduction-for-software-engineers.md) ·
[Maturity](docs/maturity.md) ·
[Conformance](docs/conformance.md) ·
[Roadmap](docs/roadmap-0.1.md) ·
[Release policy](docs/release-policy.md) ·
[Compatibility](docs/compatibility.md) ·
[Licensing](docs/licensing.md)

## Why SEAG

Software projects define important meaning in many places: requirements,
glossaries, diagrams, UI copy, schemas, code, tests, decisions, and agent
instructions. Those representations drift. Terms lose their origin, generated
views become accidental authorities, and agents cannot reliably distinguish a
confirmed definition from a plausible interpretation.

SEAG provides one domain-neutral contract for capturing project semantics with
stable identity, explicit status, and verifiable provenance. Projects retain
their own ontologies and domain content. SEAG supplies the framework and tools
for validating and transforming that content without taking ownership of it.

SEAG originated from semantic and product-modelling needs discovered in the
Rediflow project, but is developed and distributed independently. Rediflow
concepts, rules, and product decisions do not belong in SEAG.

## New to concept maps and ontologies?

Read [SEAG concepts for software engineers](docs/introduction-for-software-engineers.md).
It introduces concepts, propositions, concept maps, ontologies, provenance,
source bundles, and generated variants through familiar software-engineering
ideas. It also explains why SEAG is neither a diagram editor nor a complete
ontology reasoner, and why it keeps semantic relations separate from
cardinality.

## The three promises

### 1. Meaning has stable identity

Concepts and propositions use stable identifiers that do not change when a
label, language, filename, repository location, or generated representation
changes.

### 2. Claims retain provenance

Definitions, mappings, confirmation decisions, translations, and generated
variants retain their source, status, responsible declared actions, and known
verification limits. SEAG validates declarations; it does not authenticate the
real identity or authority of the named actors.

### 3. Transformations stay honest

Generated glossaries, diagrams, agent contexts, and integration formats must
identify their source release and transformation. Omission, fallback, and loss
are disclosed instead of being silently presented as equivalent semantics.

## What is available now

- A bounded, domain-neutral [0.1 draft source contract](docs/source-contract-0.1.md).
- A JSON Schema Draft 2020-12 source shape.
- A dependency-free Python validator for cross-file and semantic invariants.
- Invented valid and invalid conformance fixtures.
- Explicit rejection of process-flow and workflow semantics.
- BCP 47 language policy, stable identity, provenance, role, and semantic
  minimality policies.
- Reproducible release-candidate bundles with manifests, checksums, build
  provenance, SPDX enforcement, and fail-closed publication gating.

The ontology-to-glossary exporter, CmapTools CXL exchange, and optional AGF,
Ponytail, and Caveman profiles remain planned. See the
[machine-readable maturity assessment](maturity.yaml) for exact levels,
evidence, and limitations.

## Try the validator

SEAG currently runs directly from a source checkout and has no installation
claim:

```sh
git clone https://gitlab.com/janipaijanen/seag.git
cd seag

python3 -m seag.validate fixtures/valid/manifest.json
python3 -m seag.validate --variant fixtures/valid/variant.json
python3 -m unittest discover -s tests -v
```

The validator reads local JSON only. It makes no network calls, publishes
nothing, and performs no transformation. A successful result confirms the
bounded source checks implemented by that version; it does not prove semantic
truth, actor identity, authority, or review independence.

## A minimal semantic record

```json
{
  "id": "StateMachine",
  "kind": "concept",
  "status": "proposed",
  "implementation_alignment": "not_applicable",
  "label": "state machine",
  "grammatical_number": "singular",
  "definition": "A model that describes a system using states and rules for changing between states.",
  "provenance": {
    "source": "illustrative SEAG documentation",
    "locator": "README.md#A minimal semantic record",
    "normative": false,
    "proposer": "SEAG maintainer",
    "verification_status": "unresolved"
  }
}
```

This proposed, non-normative example defines the concept `state machine`; it
does not encode a particular machine or its executable transitions. A project
may similarly define the singular concepts `state`, `transition`, `event`, and
`guard`, record their provenance, and refer to an external state-machine
artifact. The external notation remains authoritative for transition
behaviour. Complete SEAG bundles also carry manifest identity, namespace,
fragment inventory, digests, language, licensing, and revision information.

## Explicit non-goal: process modelling

SEAG is not process-modelling, workflow-design, orchestration, or execution
tooling. It will not grow sequence flows, gateways, transitions, concurrency,
timers, compensation, task routing, or runtime semantics.

SEAG may define the meaning of terms such as Activity, Event, State, Rule, and
Role, and may reference an external BPMN model, state machine, decision table,
or workflow by stable identifier and provenance. The external notation remains
authoritative for behaviour.

## Standards and compatibility

SEAG distinguishes core conformance, conditional requirements, semantic
mappings, export profiles, and publication gates. Listing an external standard
does not itself claim compatibility.

- Language values follow BCP 47 and the [language-tag policy](docs/language-tags.md).
- JSON schemas use JSON Schema Draft 2020-12.
- Provenance and glossary concepts have documented W3C PROV and SKOS mapping
  obligations; neither is the authoritative SEAG storage syntax.
- CXL, JSON-LD, RDF, OWL, and PROV-O serialization remain export profiles until
  implemented and independently verified.

See [standards and conformance](docs/conformance.md) and the machine-readable
[`standards.yaml`](standards.yaml) register.

## Documentation

- [SEAG concepts for software engineers](docs/introduction-for-software-engineers.md)
- [Project charter](docs/charter.md)
- [0.1 roadmap](docs/roadmap-0.1.md)
- [Source contract](docs/source-contract-0.1.md)
- [Identity, bundles, and variants](docs/identity-bundles-and-variants.md)
- [Term adoption and provenance](docs/term-adoption-and-provenance.md)
- [Glossary extraction](docs/glossary-extraction.md)
- [CmapTools CXL export profile](docs/cxl-profile.md)
- [PROV and SKOS mappings](docs/semantic-mappings.md)
- [Installation and upgrade](docs/installation-and-upgrade.md)
- [Language tags](docs/language-tags.md)
- [Roles](docs/roles.md)
- [Semantic minimality](docs/semantic-minimality.md)
- [Maturity and evidence](docs/maturity.md)
- [Standards and conformance](docs/conformance.md)
- [Release and version policy](docs/release-policy.md)
- [Licensing and SPDX declarations](docs/licensing.md)

## Releases

`VERSION` is the authoritative package version. Release tags must match it
exactly as `v<version>`, and the tagged commit must belong to `main`. CI bakes a
reproducible `seag-<version>.tar.gz` candidate with a content manifest,
SHA-256 checksum, and build-provenance record.

Candidate artifacts are review inputs, not releases. Stable publication remains
blocked until licensing, security, contribution, compatibility, and
release-specific independent-review gates are satisfied.

Build the current candidate locally:

```sh
python3 scripts/build-release-bundle.py \
  --commit HEAD --output-dir dist --verify
```

## Stewardship and participation

SEAG is currently maintained by Jani Päijänen as a single-maintainer project in
public review. See [Contributing](CONTRIBUTING.md) and
[Security](SECURITY.md). These procedures do not create a community programme,
support commitment, review deadline, or production-readiness claim.

## Licensing

Copyright (C) 2026 Jani Päijänen.

Software, CI, and tests are licensed under [Apache-2.0](LICENSE). Framework
documentation and semantic registers are licensed under
[CC BY 4.0](LICENSE-DOCS). The per-file SPDX policy is in
[licensing and SPDX declarations](docs/licensing.md).
