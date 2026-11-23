<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Enterprise integration and multi-user direction

## Status

This document records proposed product direction. It does not claim that SEAG
0.1 implements enterprise synchronization, semantic merge, SKOS interchange,
real-time collaboration, access-control enforcement, or a hosted service.

## Product invariant: text remains the common interface

SEAG began as a simple semantic source usable with any text editor. That remains
a product invariant, not a temporary limitation. The authoritative source must
remain:

- human-readable and editable offline;
- understandable in small examples by a learner;
- deterministic and reviewable as an ordinary version-control diff;
- consumable by an AI without scraping a user interface;
- validatable without a required network service; and
- independent of a particular editor, database, graph store, or vendor.

Visual editors, indexes, databases, search services, and collaboration systems
may consume or coordinate SEAG artifacts. They do not silently replace the
text source as semantic authority.

## What an enterprise already has

An enterprise commonly has important concepts without calling the collection
an ontology. Meanings may be distributed across business glossaries, data
catalogs, canonical models, schemas, API specifications, architecture
repositories, CMDBs, policies, knowledge graphs, code, and subject-matter
experts. These sources often overlap, disagree, use different release cycles,
or have different access restrictions.

SEAG must therefore federate with existing authority rather than copy an
enterprise vocabulary into a new universal ontology. Reuse is based on stable
identity, definition, scope, version, authority, licence, and provenance—not a
matching label.

## Four replaceable planes

```text
Authoring plane
  text files + any editor + local validation

Collaboration plane
  Git, merge requests, owner rules and review first; optional service later

Integration plane
  versioned imports, exports, mappings and checkpoints

Read/query plane
  generated indexes, glossaries, maps and bounded agent contexts
```

Only the authoring source is authoritative. The other planes are replaceable
consumers or coordinators. A future web service may use this repository, but
this repository must not become that service or its web page.

## Enterprise reuse decisions

| Situation | Proposed treatment |
| --- | --- |
| The enterprise meaning fits exactly | Reference the authoritative external identifier and meaning; do not mint a competing local definition |
| The project needs a narrower meaning | Create a project identity, retain the external identity, and record a reviewed directional specialization or narrower mapping |
| Meanings overlap but are not substitutable | Keep separate identities and record close, broader, narrower, related, or incompatible mapping evidence |
| The label matches but the meaning differs | Treat the records as different concepts and document the conflict |
| The enterprise record is disputed or incomplete | Preserve it as unresolved or qualified; do not present it as confirmed project truth |
| No suitable enterprise concept exists | Create a project-local concept and optionally propose it to the enterprise authority |
| The source is a concrete schema, component, policy, or model | Reference the external artifact and keep that artifact authoritative for what it owns |
| The source cannot legally or safely be copied | Retain only permitted identifiers, citations, mappings, digests, and access restrictions |

The existing [term-adoption policy](term-adoption-and-provenance.md) defines
adopted, profiled, mapped, SEAG-defined, and deprecated dispositions. An
enterprise profile should reuse those distinctions rather than invent a second
mapping vocabulary.

## Proposed integration lifecycle

1. **Inventory sources and owners.** Locate glossaries, schemas, catalogs,
   ontologies, policies, and responsible authorities. Record uncertainty rather
   than assuming that the most visible system is authoritative.
2. **Assign authority by subject and claim.** Decide which source owns each
   kind of meaning. One system need not own every semantic claim.
3. **Pin identity and revision.** Record namespace, authority, version or
   immutable revision, locator, licence, access classification, retrieval time,
   and a digest where permitted.
4. **Select the project slice.** Import or reference only concepts required by
   the product slice. Do not require a complete enterprise ontology before a
   project can begin.
5. **Reference before copying.** Reuse authoritative identifiers when the
   meaning fits. Copying creates a fork that can drift.
6. **Create local meaning deliberately.** Mint a project identity only for a
   genuine specialization, divergence, unresolved proposal, or missing concept.
7. **Review mappings and conflicts.** Compare definition, scope, direction,
   cardinality, status, provenance, and constraints—not labels alone.
8. **Generate bounded views.** Produce glossaries, maps, agent contexts, and
   integration representations with exact source revisions and disclosed loss.
9. **Detect upstream change.** Report affected concepts, mappings, generated
   views, and agent contexts. Never silently accept a changed enterprise
   meaning.
10. **Propose useful local concepts upstream.** Generate a proposal artifact
    for the enterprise authority. SEAG does not write directly to the upstream
    source, treat submission as acceptance, or rewrite project history.

This lifecycle describes semantic state and evidence. SEAG does not model or
execute the enterprise's approval workflow.

## Multi-user scale without silent semantic loss

Multiple users introduce two different kinds of conflict:

- a **text conflict**, where edits touch the same lines; and
- a **semantic conflict**, where separate clean edits make incompatible claims
  about the same identity, authority, mapping, status, or cardinality.

Git resolves distribution and provides history, but a clean textual merge does
not prove a clean semantic merge. The first multi-user contract should therefore
define modular fragments, stable ordering, exact base revisions and digests,
deterministic validation, semantic diff categories, host pull-request review
with owner rules such as `CODEOWNERS`, and fail-closed conflict reports.
Last-write-wins is not acceptable for confirmed meaning. Review states,
approval routing, queues, and assignments remain responsibilities of the host
collaboration system; SEAG does not encode their workflow.

Real-time cursors, CRDTs, hosted workspaces, SSO, tenancy, and database locking
are service concerns. They may be added by a separate collaboration product
after the file and conflict semantics are stable.

## Bidirectional interchange, not live synchronization

Data may enter and leave SEAG, but “bidirectional” does not mean live sync,
direct writes into an enterprise authority, or automatic reconciliation. An
import or export profile should record:

- external authority, namespace, source revision, and retrieval checkpoint;
- adapter and profile identity and version;
- selected scope and selection rules;
- input, output, and base-revision digests;
- identity and mapping decisions;
- additions, changes, deprecations, conflicts, and proposed deletions;
- omissions, approximations, unsupported constructs, and fallback behavior;
- idempotence and round-trip claims with retained evidence; and
- the reviewer and decision status of imported proposals.

An import should first produce a pinned, digested snapshot and a deterministic
dry-run change plan. A first importer should be read-only and must not edit
existing authoritative SEAG concepts. No adapter may silently delete records,
mint replacement identifiers, collapse meanings, accept upstream changes, or
promote imported and AI-generated suggestions to confirmed status. Access
classification in a file is metadata to propagate; it is not authorization
enforcement.

## Pilot-derived review requirements

An adopting project may have concepts that exist only in decisions,
specifications, or reviewed models. The absence of a code locator is therefore
a valid, explicit condition rather than a validation failure. A source record
still needs evidence and status; implementation absence must not be confused
with missing provenance or with confirmation that implementation matches.

Review and future federation profiles should preserve these distinctions:

- every record exposes whether its meaning is unresolved, proposed, confirmed,
  or deprecated independently of implementation alignment;
- a homonym, synonym, or conflicting-meaning finding identifies both semantic
  identities and both stable, versioned source locators rather than reporting
  only a shared label;
- a supersession finding identifies the before identity and revision, the after
  identity and revision, and the decision or record that performs the
  supersession;
- locators prefer immutable version plus artifact identifier or anchored
  section identity; a line number may be a navigation hint but cannot be the
  durable locator because ordinary edits move it; and
- lifecycle states remain named vocabulary. Transitions, guards, sequence, and
  execution continue to belong to the referenced external state-machine or
  workflow artifact.

These are domain-neutral requirements derived from adopter feedback. They do
not import the adopter's concept inventory, conflict examples, or decisions
into SEAG.

## Priorities

### P0 — federation foundations

1. Preserve editor-neutral, offline, deterministic source files.
2. Specify a small external-sources manifest containing authority, owner,
   subject domain, namespace, revision, licence, access classification,
   retrieval checkpoint, and digest. Its filename and serialization remain a
   design decision.
3. Specify provenance-bearing exact, close, broader, narrower, related, and
   incompatible mapping assertions. `incompatible` is an explicit SEAG
   do-not-merge disposition, not a SKOS mapping term.
4. Define Git-based concurrent editing, semantic diff categories, base
   revisions, and fail-closed semantic conflicts.
5. Define pinned, digested import snapshots and the loss-aware, dry-run
   import/export contract above.
6. Keep learner examples and AI diagnostics small, explanatory, and
   status-aware.

### P1 — one useful interoperability path

1. Implement one well-bounded SKOS profile before several shallow vendor
   connectors or complete OWL reasoning. Begin with read-only import that
   writes a digested snapshot and change proposal; add export only with explicit
   loss and round-trip evidence.
2. Report upstream drift and downstream impact on mappings, glossaries, maps,
   and agent contexts.
3. Generate semantic review views that distinguish identity, definition,
   status, provenance, mapping, and cardinality changes.
4. Support reproducible composition of modular, namespace-scoped bundles.
5. Define a service-neutral API contract for read, validate, diff, resolve,
   import, and export operations without implementing a server here.
6. Generate an immediate human-readable glossary or map preview with links back
   to evidence; layout remains a view, never semantic authority.
7. Warn when local and imported records reuse a label without a reviewed
   mapping; never merge them automatically.
8. Propagate access classification into generated views and lint for the most
   restrictive applicable classification without claiming to enforce access.

### P2 — defer or place in a separate product

- real-time cursor-level co-editing and CRDTs;
- hosted workspaces, browser graph editing, SSO, tenancy, and RBAC enforcement;
- a graph database, general query engine, or full-text/vector search service;
- complete OWL reasoning or automatic ontology merging;
- a vendor connector marketplace;
- LLM-authorized acceptance of enterprise changes; and
- a universal enterprise ontology; and
- multi-repository federation before single-repository semantics and one
  importer have adoption evidence.

SEAG also continues to reject process and workflow modelling as core work.

## Proposed differentiator

SEAG should not compete with mature tools primarily on canvas drawing, graph
storage, general reasoning, or real-time collaboration. Its proposed
differentiator is:

> A learner can understand and edit the same small semantic source that an AI
> consumes and an enterprise synchronizes, while every change, suggestion,
> mapping, and generated representation remains status-aware,
> provenance-verifiable, and loss-disclosing.

The corresponding agent-facing questions are concrete:

- Which meaning is authoritative for this scope?
- Is it proposed, confirmed, deprecated, or unresolved?
- Which source and version support it?
- Did an upstream enterprise meaning change?
- Does this project intentionally diverge?
- Which generated contexts and representations are affected?
- What was omitted or approximated in this view?

## Market evidence and limits

This direction is informed by recurring capabilities emphasized by existing
tools and their public documentation:

- [WebProtégé](https://github.com/protegeproject/webprotege#what-is-webprotégé)
  emphasizes change tracking, revision history, permissions, discussions,
  notifications, forms, and import/export for collaborative ontology work.
- [CmapTools](https://cmap.ihmc.us/cmaptools/) and IHMC's
  [concept-map guidance](https://cmap.ihmc.us/docs/theory-of-concept-maps)
  emphasize approachable propositions, focus questions, linking phrases,
  linked evidence, iterative revision, sharing, and critique.
- [TopQuadrant](https://www.topquadrant.com/use-case/ontology-governance),
  [PoolParty](https://www.poolparty.biz/),
  [Stardog](https://www.stardog.com/platform/), and
  [GraphDB](https://graphdb.ontotext.com/documentation/11.3/) repeatedly
  position governance, versioning, integration, impact, search, security, and
  open standards as enterprise capabilities.
- [LinkML](https://linkml.io/linkml/) and its
  [collaborative modelling guidance](https://linkml.io/linkml/howtos/collaborative-development.html)
  demonstrate a text/Git-oriented model with imports, mappings, validation,
  generated representations, CI, and controlled releases.
- The [Ontology Development Kit workflow](https://pmc.ncbi.nlm.nih.gov/articles/PMC9547537/)
  demonstrates declared ontology imports, ROBOT-based builds, Git, pull
  requests, and automated quality checks.
- [DataHub's business-glossary source](https://docs.datahub.com/docs/generated/ingestion/sources/business-glossary)
  demonstrates YAML glossary ingestion and Git-oriented metadata management.
- [VocBench](https://aims.fao.org/index.php/publications/vocbench-web-application-collaborative-development-multilingual)
  documents distinct editing, terminology, validation, and publication
  responsibilities in collaborative vocabulary development.
- The [SKOS Recommendation](https://www.w3.org/TR/skos-reference/) defines the
  exact, close, broad, narrow, and related mapping properties used as the basis
  for SEAG's proposed external mappings.

Vendor pages demonstrate product positioning, not independent proof of
customer satisfaction. The prioritization above is an inference from repeated
market signals, SEAG's charter, and the need to preserve its simpler original
product idea. It remains subject to validation with real learners, project
teams, enterprise semantic stewards, and AI-tool builders.

## Evidence required before claiming enterprise readiness

SEAG should not claim enterprise or multi-user readiness until independent
evidence demonstrates at least:

- two users can make concurrent changes without silent semantic overwrite;
- an external vocabulary revision produces a correct, reviewable impact report;
- one bounded import/export profile is deterministic and loss-aware;
- a learner can author and understand a small source without a proprietary UI;
- an AI consumes only a selected context and respects status and provenance;
- access-restricted source material is not leaked into generated artifacts; and
- the service-neutral contract can be used by a separate integration service.
