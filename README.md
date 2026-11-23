<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# SEAG — Semantic Engineering for Agentic Development

A provenance-preserving semantic source and transformation framework for
software work performed by people and LLM agents.

> **Status: 0.2.0-alpha.1 evaluation candidate.** The immutable `v0.1.0` tag
> remains the latest stable release. The alpha candidate adds canonical source
> rendering and semantic review for controlled pilots; it is unsupported, may
> change incompatibly, and has not passed the 0.2 adoption gate. The tagged
> alpha is a prerelease candidate; an untagged checkout is development input,
> not a published candidate. SEAG is a file-oriented framework, not a
> hosted service or a claim that semantic content is true, actor identities are
> authenticated, or every planned export exists.

[Source contract](docs/source-contract-0.1.md) ·
[Concept maps and ontologies](docs/introduction-for-software-engineers.md) ·
[Enterprise integration](docs/enterprise-integration.md) ·
[Semantic diff](docs/semantic-diff.md) ·
[Input validation](docs/input-validation.md) ·
[Rediflow pilot](docs/pilots/rediflow-0.2.0-alpha.1.md) ·
[Maturity](docs/maturity.md) ·
[Conformance](docs/conformance.md) ·
[Roadmap to 1.0](docs/roadmap-to-1.0.md) ·
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
- A Python-standard-library-only validator for cross-file and semantic
  invariants.
- Invented valid and invalid conformance fixtures.
- Explicit rejection of process-flow and workflow semantics.
- BCP 47 language policy, stable identity, provenance, role, and semantic
  minimality policies.
- Deterministic exact-language glossary extraction with source and extraction
  provenance.
- Deterministic CmapTools CXL export with an explicit loss sidecar and
  compatible-parser graph round trip.
- Reproducible release bundles with manifests, checksums, build
  provenance, SPDX enforcement, and fail-closed publication gating.

SEAG adopts the pinned Ponytail full discipline for smallest-complete changes
and strict trust-boundary validation; it does not bundle the agent skill or
make Ponytail part of the semantic source contract. Optional AGF and Caveman
profiles remain planned. CmapTools desktop import is not yet tested or claimed. See the
[machine-readable maturity assessment](maturity.yaml) for exact levels,
evidence, and limitations.

### 0.2 alpha evaluation capability

The 0.2 alpha candidate includes deterministic canonical source rendering,
two-way semantic diff, and bounded three-way conflict detection. Semantic
review has stable draft diagnostic codes, machine-readable output, explicit CI
failure policies, and retained tests, but has not passed the learner,
repository-history, or independent-adopter gates for a 0.2 release. See
[canonical source rendering](docs/canonical-source.md) and
[semantic diff and conflict detection](docs/semantic-diff.md).

## Text first, including at enterprise scale

SEAG's authoritative source is intended to remain editable with any text
editor, understandable by a learner, reviewable in Git, usable offline, and
directly consumable by an AI. A database, visual editor, index, or hosted
service may consume or coordinate that source; it must not silently replace it
as semantic authority. This repository remains the framework and toolchain, not
the future collaboration web application.

Enterprises usually already have concepts spread across glossaries, catalogs,
schemas, APIs, policies, architecture repositories, knowledge graphs, and
code. A project should reference those authoritative identities when meanings
fit, create local identities only for genuine specialization or difference,
and retain the external version, licence, provenance, mapping, and access
restrictions. Matching labels alone never justify merging concepts.

The proposed integration lifecycle is:

1. inventory sources and owners;
2. assign authority by subject and claim;
3. pin namespace, version, locator, licence, access, and digest;
4. select the smallest project-relevant slice;
5. reference before copying;
6. create project-local meaning deliberately;
7. review mappings and conflicts;
8. generate bounded human and agent views;
9. report upstream change and downstream impact without silent acceptance; and
10. generate proposals for useful local concepts for the enterprise authority,
    without writing directly to its source.

Multi-user scale first means Git-safe modular sources, exact base revisions,
semantic diffs, conflict reports, and loss-aware bidirectional adapters. It
does not mean live synchronization or direct upstream writes, and it does not
yet mean real-time co-editing, SSO, a hosted graph database, or a web application
in this repository. See
[enterprise integration and multi-user direction](docs/enterprise-integration.md)
for the proposed architecture, priorities, market evidence, and readiness
gates. None of those proposed capabilities is claimed by the 0.1 release.

## Try the validator

SEAG currently runs directly from a source checkout and has no installation
claim:

```sh
git clone https://gitlab.com/janipaijanen/seag.git
cd seag

python3 -m seag.validate fixtures/valid/manifest.json
python3 -m seag.validate --variant fixtures/valid/variant.json
python3 -m seag.canonical fixtures/valid/manifest.json --check
python3 -m seag.semantic_diff fixtures/valid/manifest.json fixtures/valid/manifest.json
python3 -m seag.glossary fixtures/valid/manifest.json --language en --generated-at 2026-11-22T00:00:00Z --output glossary.json
python3 -m seag.cxl fixtures/valid/manifest.json --generated-at 2026-11-22T00:00:00Z --output concept-map.cxl --verify
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

Static architecture may still be described separately: a state machine may
have the `Logging` concept, while a `Logging` component has `Configuration`.
SEAG gives the semantic concept, implementation component, and configuration
distinct identities and records optionality as cardinality rather than hiding
it inside the relation phrase. See the
[worked state-machine example](docs/introduction-for-software-engineers.md#static-logging-concepts-around-a-state-machine).

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
- CXL has a bounded, lossy export profile with compatible-parser evidence;
  CmapTools desktop compatibility is not claimed.
- JSON-LD, RDF, OWL, and PROV-O serialization remain unimplemented export
  profiles.

See [standards and conformance](docs/conformance.md) and the machine-readable
[`standards.json`](standards.json) register.

## Documentation

- [SEAG concepts for software engineers](docs/introduction-for-software-engineers.md)
- [Project charter](docs/charter.md)
- [0.1 roadmap](docs/roadmap-0.1.md)
- [Evidence-gated roadmap toward 1.0](docs/roadmap-to-1.0.md)
- [Source contract](docs/source-contract-0.1.md)
- [Identity, bundles, and variants](docs/identity-bundles-and-variants.md)
- [Term adoption and provenance](docs/term-adoption-and-provenance.md)
- [Enterprise integration and multi-user direction](docs/enterprise-integration.md)
- [Canonical source rendering](docs/canonical-source.md)
- [Semantic diff and bounded conflict detection](docs/semantic-diff.md)
- [Rediflow 0.2 alpha evaluation plan](docs/pilots/rediflow-0.2.0-alpha.1.md)
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
exactly as `v<version>`, and the tagged commit must belong to `main`. CI builds
and compares two normalized `seag-<version>.tar.gz` candidates and emits a
content manifest, SHA-256 checksum, and build-provenance record. A provenance
value of `reproducible: true` is the builder's verified comparison claim; an
independent party must rebuild the artifact before claiming independent
reproduction.

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
