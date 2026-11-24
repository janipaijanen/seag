<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Evidence-gated roadmap toward SEAG 1.0

## Status and interpretation

This is a draft capability and implementation plan. It is not a delivery-date
commitment, an enterprise-readiness claim, or evidence that the listed features
exist. Planned increments may be combined, reordered, skipped, or cancelled
when evidence does not justify them.

SEAG 0.1.0 is the released baseline: bounded text source, validation, retained
fixtures, glossary extraction, and a lossy CXL profile with compatible-parser
round-trip evidence. Optional AGF, Ponytail, and Caveman profiles were not part
of its publication gate and do not become prerequisites for later core releases.

SEAG 1.0 is a narrow compatibility promise over capabilities proven useful in
real projects. It is not the point at which SEAG becomes a hosted ontology
platform, complete enterprise product, general AI-safety system, or workflow
engine.

## Product invariants

Every increment must preserve these constraints:

1. Authoritative source remains human-readable, text-editor friendly, usable
   offline, deterministic, and directly consumable by software and AI tools.
2. SEAG remains useful when AI is absent.
3. Humans or an authorized external system confirm meaning; AI may only
   discover, explain, validate, and propose.
4. Stable identity, status, provenance, uncertainty, and transformation loss
   are never silently discarded.
5. Network retrieval is an explicit operation, never a side effect of ordinary
   validation.
6. Generated indexes, maps, contexts, databases, and services never become the
   semantic authority merely because they are convenient.
7. Core source, optional profiles, and external services have separate
   compatibility identities.
8. SEAG does not model or execute process, workflow, state-transition,
   authorization, approval-routing, or task-queue semantics.
9. This repository remains the framework and toolchain, not a hosted web
   application.
10. Access classification is metadata to propagate and lint, not access-control
    enforcement.

## Capability dependency map

```text
0.1 stable source, validation and bounded transformation baseline
  │
  ├─ discovery and comparative evidence gate
  │
  ▼
0.2 semantic review core
  │
  ├─ if an agent workflow proves demand ─────────────┐
  ▼                                                  ▼
0.3 bounded agent context + authority manifest    stop AI expansion
  │
  ├─ if an external-vocabulary pilot persists ──────┐
  ▼                                                  ▼
0.4 one federation vertical slice                stop connector expansion
  │
  ├─ if multi-user pilots expose real scale needs ──┐
  ▼                                                  ▼
0.5 composition and team hardening              retain simpler model
  │
  ├─ evidence chooses any additional profile work
  ▼
1.0.0-rc compatibility preview and feature freeze
  │
  ▼
1.0 narrow supported contract
```

Version labels communicate the intended order, not entitlement to the next
increment. There is intentionally no precommitted 0.6–0.9 platform backlog. If
0.5 does not satisfy the adoption bar, SEAG remains 0.x or stops; it does not
enter a 1.0 release-candidate series.

## Discovery gate before 0.2

### Purpose

Prove that SEAG detects or prevents a repeated semantic failure materially
better than a Markdown glossary, plain JSON, and an appropriate established
alternative such as LinkML, SKOS, or the Ontology Development Kit.

### Required discovery artifacts

- at least two candidate projects with retained semantic-drift examples;
- at least one candidate using multiple AI agents;
- at least one candidate reusing an external glossary or vocabulary;
- a responsible human semantic owner for every pilot;
- a baseline implementation using simpler existing tools;
- a small, anonymized failure corpus and measurement method; and
- explicit adoption, support, licensing, and access constraints.

### Entry decision

Begin 0.2 only if at least one repeated failure and one identifiable user are
found, a semantic owner can make decisions, and SEAG has a measurable advantage
worth testing. Otherwise keep SEAG as a research specification or stop further
product expansion.

## 0.2 — semantic review core

### Current implementation status

The `main` branch now contains an experimental two-way semantic diff and
bounded three-way conflict detector with a draft result schema, retained
fixtures, stable draft codes, documented failure policies, and a deterministic
canonical source renderer/checker. It has not yet supplied editor assistance,
mapping conflicts, real-history replay, learner evidence, or independent
adoption evidence. Therefore this is implementation progress, not completion
of the discovery or 0.2 exit gate.

### User outcome

A learner or reviewer can understand what meaning changed between two source
revisions and whether a clean textual merge contains a bounded semantic
conflict.

### Capability scope

- a normative semantic-change taxonomy;
- canonical formatting and stable ordering rules;
- deterministic semantic diff with a versioned machine-readable result;
- stable diagnostic codes paired with educational human messages;
- bounded conflict classes for identity, definition, status, provenance,
  mapping, cardinality, deprecation, and replacement;
- small authoring templates and editor/schema assistance; and
- documented Git, merge-request, and semantic-owner conventions.

SEAG does not claim complete conflict detection or automatic semantic merge.
Free-text meaning and ambiguous equivalence continue to require human review.

### Implementation order

1. Specify the change taxonomy, conflict boundary, result schema, and
   compatibility identity.
2. Add retained positive, negative, and adversarial before/after fixtures.
3. Implement canonicalization and diff as deterministic library operations.
4. Expose file, stdin/stdout, human, and JSON CLI results.
5. Add CI examples and owner-review guidance without encoding an approval
   workflow in SEAG.
6. Replay retained real repository histories and record limitations.

### Exit evidence

- golden fixtures cover every claimed change and conflict category;
- results match across supported runtimes and repeated execution;
- clean textual merges with supported semantic conflicts fail closed;
- reviewers identify material changes that ordinary line diffs obscure;
- false positives, false negatives, and human-review boundaries are recorded;
- at least two real histories are replayed; and
- text-editor, offline, glossary, and CXL workflows do not regress.

The provisional usability trial is five unaided learners authoring ten records
each, with a median time to first valid commit of no more than 30 minutes and a
blind review of three seeded semantic conflicts. These numbers are experiment
design hypotheses, not current product evidence; the discovery work must
pre-register or revise them before the trial begins.

### Stop condition

Stop semantic-diff expansion if reviewers obtain no material advantage over Git
plus existing validation. If ordinary authors require AI assistance to produce
valid records, redesign the source syntax or authoring guidance before adding
more capability.

## 0.3 — bounded agent context and authority manifest

This increment proceeds only if a real agent workflow passes the discovery gate
and 0.2 provides stable selection and change semantics.

### User outcome

An AI receives a small, reproducible, citation-ready context rather than an
unbounded documentation dump, while human-only use remains fully supported.

### Capability scope

- a task-scoped selection manifest;
- deterministic selection with an explained inclusion closure;
- content-addressed context packages and included-record inventory;
- explicit status, language, provenance, citation, omission, and fallback
  policies;
- exact source, selection, and generator digests;
- content and relationship-depth budgets;
- an incremental “what changed since context digest X?” result; and
- proposal-only AI output with no confirmation authority.

This increment also defines the minimum dependency and authority manifest needed
to interpret the context: namespace, owner, pinned version, locator, licence,
access classification, digest, and reviewed mapping references. It records and
pins dependencies but does not retrieve or import their contents; that usable
federation path belongs to 0.4.

Selection must never flatten or merge `proposed`, `unresolved`, and `confirmed`
records. Every package carries an omission report explaining records excluded by
scope, budget, status, incompatibility, staleness, or access classification.

External-identity and mapping extension points must be designed here so the
package does not need to be broken by 0.4. A server, vector database, model
provider, prompt framework, or MCP dependency is not part of core.

### Implementation order

1. Specify the selection and authority manifests, deterministic closure,
   package schema, and content-budget behavior.
2. Define citation completeness, stale-context detection, and access filtering.
3. Threat-model prompt injection, restricted content, malicious labels,
   oversized graphs, and citation substitution.
4. Add fixtures before implementing the compiler and incremental change result.
5. Expose files and CLI JSON first; keep any agent-protocol adapter external.
6. Compare real tasks against repository documentation alone.

### Exit evidence

- repeated compilation produces identical bytes and digest;
- every supplied claim has complete source and revision evidence;
- stale, incompatible, and access-ineligible inputs fail closed;
- restricted fixtures do not leak into lower-classification contexts;
- cache identity and incremental change results are verified;
- at least one real agent workflow shows lower semantic error, smaller context,
  or another predeclared measurable benefit;
- an AI proposal cannot become confirmed without an external human decision;
- no test output presents a proposed or unresolved record as confirmed; and
- every exclusion is represented in the omission report.

The provisional comparison is 20 paired tasks against repository documentation
alone, testing whether terminology-drift errors decrease without any status
misrepresentation. This threshold is subject to the measurement rule below.

### Stop condition

Stop AI-specific expansion if bounded context does not improve a real task over
ordinary documentation retrieval. In that case retain, at most, a deterministic
plain export and do not promote an agent-specific context contract.

## 0.4 — one federation vertical slice

This increment extends the 0.3 authority manifest with mappings, import,
snapshot, change planning, and impact. Splitting the operational path would
produce metadata with no usable path or an importer with unsafe authority
semantics.

### User outcome

A project can reproducibly reuse one maintained external SKOS vocabulary,
detect a pinned upstream change, and review its local impact without silent
mutation.

### Capability scope

- a small external-sources manifest recording authority, owner, subject domain,
  namespace, immutable revision, licence, access classification, retrieval
  checkpoint, and digest;
- reviewed exact, close, broader, narrower, related, specializes, adopts, and
  explicit SEAG incompatible/do-not-merge assertions;
- a read-only SKOS import profile;
- a pinned, digested import snapshot;
- deterministic dry-run additions, changes, deprecations, conflicts, and
  proposed-deletions report;
- an explicit upstream revision check; and
- downstream impact on mappings, glossaries, maps, and context packages.

`incompatible` is a SEAG disposition, not a SKOS mapping property. Ordinary
validation remains offline. Retrieval is explicit and cannot modify confirmed
local concepts, confirm imported content, write upstream, or perform live
synchronization.

### Implementation order

1. Specify the external manifest, mapping assertions, snapshot identity, and
   offline-versus-retrieval boundary.
2. Pin the supported SKOS subset and explicitly list blank-node, language,
   mapping, hierarchy, collection, and unsupported-construct behavior.
3. Add neutral fixtures from two independently maintained vocabularies where
   licences permit retention.
4. Implement explicit retrieval into a content-addressed staging area.
5. Implement read-only snapshot generation and dry-run change planning.
6. Implement upstream revision and downstream impact reports.
7. Threat-test malformed RDF, entity expansion, parser resources, hostile IRIs,
   licence loss, identifier substitution, and retrieval redirection.

### Exit evidence

- repeated import is deterministic and idempotent;
- identifiers, language, mappings, licence, authority, and provenance survive;
- blank nodes and unsupported constructs are deterministically handled or
  rejected;
- an actual upstream change identifies every affected supported consumer;
- no imported record becomes confirmed without human review;
- ordinary validation performs no network access;
- at least one adopter commits to maintaining the external dependency;
- two real, independently maintained vocabularies exercise the supported
  subset; and
- seeded supported upstream changes produce no false-negative impact result.

### Stop condition

Stop connector expansion if no adopter will maintain a real external
dependency or if reviewing mappings costs more than authoring the bounded local
content. Retain the authority manifest without import if that is the useful
limit. Do not add OWL reasoning, vendor catalog connectors, or upstream writes
merely to complete a feature matrix.

## 0.5 — composition and team hardening

This increment proceeds only when earlier pilots expose actual multi-user or
corpus-scale needs.

### User outcome

Several users can maintain modular semantic sources through Git without silent
semantic overwrite, and generated views respect declared access classifications.

### Capability scope

- reproducible modular bundle and dependency composition;
- exact base revisions and optimistic-concurrency semantics;
- semantic diff across local modules and pinned dependencies;
- host-based owner-review conventions such as `CODEOWNERS`;
- duplicate-label-without-mapping warnings;
- access-classification propagation and most-restrictive-wins lint;
- performance budgets derived from real pilot sizes; and
- optional human-readable glossary and map change views.

Real-time cursors, CRDTs, hosted workspaces, locks, SSO, tenancy, and RBAC
enforcement remain external service concerns.

### Implementation order

1. Measure pilot corpus sizes, edit patterns, contention, and generation costs.
2. Specify composition order, dependency identity, cycle handling, base
   revision, and optimistic-conflict behavior.
3. Add concurrent-edit, incompatible-version, dependency-cycle, duplicate-label,
   and classification-leak fixtures.
4. Implement deterministic composition and cross-module semantic diff.
5. Add classification propagation and export lint without claiming enforcement.
6. Write a threat and information-leakage model for composition and generated
   views.
7. Optimize only against recorded budgets and retain deterministic behavior.

### Exit evidence

- multi-user edits produce no silent overwrite in supported conflict classes;
- clean textual merges with bounded semantic conflicts fail closed;
- dependency cycles and incompatible source versions are diagnosed;
- restricted fixtures do not leak into lower-classification generated views;
- composition and output remain reproducible; and
- performance meets published budgets on real corpus shapes.

The provisional adoption trial is two external, non-maintainer pilots operating
for eight weeks, each with at least three unprompted uses and a retained issue
log. Pilots should use consenting or invented content where publication is
possible. If both pilots leave the capability unused, do not freeze it into the
1.0 contract.

## Evidence decision after 0.5

SEAG does not reserve 0.6–0.9 for speculative platform construction. Evidence
must select the next work, which may be:

- a separately versioned SKOS export and round-trip profile;
- better context selection or semantic impact analysis;
- another adapter with a named adopter and pinned target;
- a service-neutral operation specification after two real consumers exist;
- usability, performance, security, or migration work; or
- no further capability expansion.

An experimental API, MCP adapter, web interface, or collaboration service may
be developed in another repository. It must consume established SEAG semantics
and must not define core meaning by accident.

## 1.0 release candidate — compatibility freeze

Enter a `1.0.0-rc` series only after evidence selects and freezes the intended
1.0 support floor. Feature work stops except for findings required to make that
floor honest. Remaining feature demand keeps SEAG in 0.x; it is not a reason to
hide development under a release-candidate label.

### Required work

- freeze the normative core/profile boundary;
- freeze supported schemas and machine-readable result formats;
- document compatibility, deprecation, migration, installation, upgrade,
  rollback, and support policies;
- supply migration tools and retained fixtures from every supported 0.x source
  version;
- publish the compatibility matrix and platform/runtime pins;
- complete threat models and negative security evidence for every included
  capability;
- obtain independent human semantic and usability review in addition to
  licensing, security, and framework-boundary review; and
- publish reproducible integrity-verifiable release candidates with no
  unresolved release-blocking finding.

### Exit evidence

At least two independent adopting projects must successfully migrate and run
the supported workflows on the same exact candidate. Every incompatible change
must have explicit migration evidence rather than release-note prose alone.

## 1.0 — narrow stability promise

Version 1.0 guarantees only capabilities with retained adoption and migration
evidence. The minimum supported floor is:

- stable text source, identity, status, provenance, and source-bundle contract;
- deterministic validation with a versioned diagnostic format;
- versioned semantic diff and documented human-review boundary;
- core/profile version separation and explicit compatibility ranges;
- migration without silent identity or provenance loss;
- supported installation and upgrade path; and
- published support and security-response limitations appropriate to
  maintainer capacity.

The 1.0 floor may also include the context-package contract if the agent pilot
succeeds, and the external-authority/mapping contract if the federation pilot
succeeds. Optional CXL, SKOS, agent-protocol, and vendor profiles remain
separately versioned unless evidence justifies promoting one into the support
floor.

AGF interoperability is also optional and evidence-gated. The attributed
AGF26 maturity-vocabulary adoption is not an AGF compatibility profile and is
not equivalent to silver-birch's operational AGF 3.0 overlay. Before SEAG names any
AGF profile, it must have a verified normative locator and retained source
bytes, a pinned field mapping, explicit loss semantics, native validation on
both sides, and retained round-trip fixtures. The first experiment, if a pilot
later justifies it, is restricted to static concepts and immutable references;
process, workflow, roles, gates, plans, coordination, and delegation remain out
of scope.

Version 1.0 does not claim enterprise readiness, production operation,
complete ontology management, general AI safety, CmapTools desktop
compatibility, complete RDF/OWL reasoning, or universal interoperability.

## Hard 1.0 evidence bar

- pinned fixtures pass on every supported operating-system, runtime, and Git
  version in the published matrix;
- the earliest supported 0.x source migrates automatically and losslessly, with
  identical record digests for unchanged records;
- at least two external, non-maintainer adopters complete real semantic-change
  cycles over at least eight weeks, with retained issue logs;
- at least one non-AI human workflow demonstrates measurable value;
- an included AI context capability has evidence from a real multi-agent
  workflow;
- an included federation capability has a maintained external dependency and a
  recorded upstream-change event;
- retained 0.x fixtures migrate without identity or provenance loss;
- no generated output presents proposed or unresolved content as confirmed;
- validator fixtures reject every claimed violation of a normative non-goal;
- the core supported workflow runs offline without AI, a network, or a service;
- exact-head review includes independent human semantic and usability review,
  not only clean-context AI review;
- support scope, maintainer capacity, and security-response limitations are
  documented; and
- no compatibility promise is broader than tested evidence.

Conditional bullets apply only when the corresponding capability is included
in the 1.0 support floor.

## Measurement rule

The numeric thresholds in this roadmap—learner counts, record counts, elapsed
time, paired tasks, pilot duration, and unprompted uses—are provisional study
designs. They make proposed evidence falsifiable, but they are not standards,
market facts, or evidence SEAG already possesses. Before each study, record the
population, baseline, task, success measure, exclusion rule, and any justified
threshold revision. Do not revise a threshold after observing results merely to
make an increment pass.

## Release-wide implementation discipline

Every increment follows the same order:

1. user problem and baseline evidence;
2. normative scope, compatibility identity, non-goals, and threat model;
3. neutral fixtures and expected machine-readable evidence;
4. smallest deterministic library operation;
5. files and CLI before any service interface;
6. negative, adversarial, reproducibility, and migration tests;
7. learner, operator, compatibility, and security documentation;
8. exact-head independent review; and
9. protected immutable release with reproducible artifacts.

Security, licensing, access, privacy, and compatibility are addressed in the
increment that introduces the risk. They are not deferred to a later hardening
release.

## Permanent core exclusions

SEAG core will not become:

- a hosted workspace, web UI, graph database, or search platform;
- an authentication, SSO, tenancy, or RBAC enforcement system;
- an approval workflow, governance queue, or project-management tool;
- a BPMN, state-machine execution, orchestration, or process-modelling tool;
- an automatic ontology merger or label/embedding equivalence engine;
- a general RDF/OWL reasoner;
- a live bidirectional synchronization system or direct upstream writer;
- a connector marketplace;
- an authority that permits an LLM to confirm meaning; or
- a home for adopting-project or enterprise domain content.

## Compatibility risks to resolve early

- identifier or namespace meaning changes;
- core fields that force every small project to adopt enterprise metadata;
- mapping labels whose semantics subtly differ from SKOS;
- context selection growing into an implicit query or workflow language;
- runtime-dependent ordering, Unicode behavior, or RDF blank-node identity;
- network retrieval undermining offline reproducibility;
- access metadata being mistaken for enforcement;
- adapters silently weakening source meaning;
- a service API freezing before operation semantics and consumers exist; and
- profile versions silently redefining the core contract.
