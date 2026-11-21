<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# SEAG semantic-work roles

## Purpose

SEAG defines roles as responsibility contracts. A role identifies jurisdiction,
inputs, outputs, permitted and prohibited actions, required evidence, and
escalation conditions. It does not require a dedicated agent process.

A person or agent may hold several compatible roles. Projects record where an
independent role was unavailable. Human semantic authority cannot be inferred
from an LLM's ability to perform the work.

## Minimal roles

### Semantic Discovery Consultant

Guides humans and agents in identifying, eliciting, delimiting, and collecting
candidate concepts and their evidence.

- **Inputs:** product language, stakeholder interviews, requirements, UI text,
  code, tests, standards, and observed terminology conflicts.
- **Outputs:** discovery questions, candidate concept inventories, source
  pointers, ambiguity and duplication findings, and collection guidance.
- **May:** facilitate workshops; ask contrast, boundary, identity, and
  cardinality questions; suggest singular candidate labels; and advise which
  evidence the Semantic Modeller should collect.
- **Must not:** declare a candidate authoritative, manufacture missing evidence,
  silently merge meanings, or confirm its own proposals.
- **Escalates:** domain disagreement, unclear ownership, irreducibly plural
  labels, incompatible sources, and decisions about project meaning to the
  Semantic Steward.

This is a consultation responsibility, not a required dedicated person or
agent. It may be combined with the Semantic Modeller role when the combination
is disclosed; semantic confirmation remains with the Semantic Steward.

### Semantic Steward

Owns semantic authority for the adopting project.

- **Inputs:** proposals, conflicts, evidence, review findings.
- **Outputs:** confirmed or rejected meanings, mappings, and release decisions.
- **May:** resolve project meaning; assign authority; accept reviewed records.
- **Must not:** treat an agent inference or implementation observation as a
  confirmed product decision without the project's decision authority.
- **Escalates:** unresolved stakeholder conflict, ownership ambiguity, or legal
  and policy questions to the appropriate human authority.

### Semantic Modeller

Captures concepts, propositions, associations, lifecycle vocabularies, semantic
constraints, and external mappings.

- **Inputs:** requirements, domain sources, observed implementation, decisions,
  and discovery-consultation findings.
- **Outputs:** proposed semantic records and change rationale.
- **May:** discover, compare, propose, and revise semantic expressions.
- **Must not:** confirm its own proposals or invent missing cardinality and scope.
- **Escalates:** ambiguous meaning, incompatible sources, and model changes that
  require a product decision.

### Provenance Verifier

Checks whether sources and derivation claims can be independently verified.

- **Inputs:** citations, versions, locators, digests, licences, mappings.
- **Outputs:** verified, qualified, rejected, or unresolved provenance findings.
- **May:** verify authority, version, scope, licence, mapping, and retrieval.
- **Must not:** decide product meaning merely because an external source exists.
- **Escalates:** inaccessible or conflicting normative sources, licensing doubt,
  mutable citations, and unsupported conformance claims.

### Transformation Maintainer

Implements and maintains schemas, validators, importers, exporters, and
representation profiles.

- **Inputs:** confirmed framework contracts, source bundles, target profiles.
- **Outputs:** transformation code, variants, diagnostics, and verification.
- **May:** implement the smallest complete transformation preserving declared
  semantics and provenance.
- **Must not:** change source meaning to satisfy a target format, hide loss, or
  add process-modelling behavior.
- **Escalates:** unrepresentable constructs, lossy output, ambiguous mappings,
  and target-format conflicts.

### Conformance Reviewer

Independently checks source-contract, transformation, and representation
conformance.

- **Inputs:** pinned source, implementation, variants, tests, provenance.
- **Outputs:** findings with severity, evidence, limits, and verdict.
- **May:** test completeness, semantic preservation, rejection behavior, and
  round trips.
- **Must not:** independently attest the same material it authored.
- **Escalates:** material semantic loss, false compatibility, insufficient
  evidence, and unavailable independence.

## Separation rules

- Semantic Modeller and Semantic Steward are distinct authorities even when one
  human performs both; the record must show proposal and confirmation actions.
- Transformation Maintainer cannot supply the only conformance attestation for
  its own change.
- Provenance verification establishes source claims, not product decisions.
- Conformance review establishes bounded evidence, not universal correctness.
- Role collapse is recorded as a limitation rather than hidden.

## Optional framework mappings

AGF and other governance systems may map their agents onto SEAG roles. Such a
mapping is an integration profile, not part of SEAG core. A mapping must state
its pinned framework version, authority differences, collapsed roles, and
uncovered responsibilities. Similar names do not establish equivalence.

