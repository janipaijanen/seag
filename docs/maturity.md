<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Maturity and evidence

## Adoption source

SEAG adopts the capability-maturity ladder, evidence-status vocabulary, and
data-maturity ladder from the Agents Govern Framework source identified below:

- framework: AGF26;
- framework version: `1.9.0`;
- source commit: `e4ceea4a615fed9cae0ed675aa38b947abfddb99`; and
- source section: `agf26/handbook/agf26core.md`, blocks
  `maturity-vocabulary` and `data-maturity-ladder`.

This is an attributed adoption, not a claim that AGF governs SEAG or that an
AGF integration profile has been implemented. A future change in the upstream
vocabulary requires an explicit SEAG review and version update; it does not
silently change existing SEAG assessments.

## Capability maturity

Every material SEAG capability claim uses one of these levels:

1. **Level 1 Planned:** identified only in a plan, issue, roadmap, or design
   note.
2. **Level 2 Surface-defined:** its interface, command, adapter, or behaviour
   is declared or documented but is not wired to working behaviour.
3. **Level 3 Instantiated:** implementation exists and has been partially or
   manually exercised, but verification is incomplete.
4. **Level 4 Validated:** implemented and repeatably verified in the stated
   branch, checkout, or environment, but not yet distributed through the
   supported release path.
5. **Level 5 Deployable:** implemented, tested, documented, released, and
   available through the supported operator or distribution path.

Binary terms such as "supported", "complete", "production-ready", or "fully
working" must not replace a maturity assessment. A maturity-sensitive claim
states its level, exact scope, evidence, and limitation.

### Promotion gates

- **Level 1 to 2:** stable purpose, interface, inputs, outputs, and limitations
  are documented.
- **Level 2 to 3:** implementation exists and at least one representative
  execution is recorded.
- **Level 3 to 4:** repeatable tests, expected outcomes, negative cases, and
  matching documentation exist.
- **Level 4 to 5:** a versioned supported release contains the tested
  capability, installation or upgrade guidance, and documented compatibility
  boundaries.

Promotion is evidence-based and capability-specific. A release does not
automatically promote every capability it contains. Removal of evidence or a
newly discovered incompatibility may require demotion.

## Evidence status

Framework- or methodology-level claims separately use:

- **Empirically validated:** exercised by multiple independent projects with
  consistent results.
- **Empirically informed:** derived from one sustained project, one
  self-application thread, or relevant adjacent-domain evidence.
- **Theoretical:** derived from principles or design reasoning without direct
  project evidence.

Evidence produced by the same author or project as the claim supports at most
Empirically informed status, regardless of repetition. Capability maturity and
evidence status are separate dimensions: tested software can be Level 4 while
the broader framework benefit claimed for it remains Theoretical.

SEAG does not adopt AGF's process-aware compliance profile. SEAG validates
semantic artifacts and transformations and remains explicitly outside process
and workflow modelling.

## Data maturity ladder

SEAG uses AGF's data-maturity ladder as a restraint on premature semantic
modelling:

```text
Free text
  -> Suggested values
  -> Validated values
  -> Lookup or reference tables
  -> Controlled vocabularies
  -> Semantic models and machine-readable constraints
```

The right stage is the simplest one that satisfies the current interoperability,
governance, traceability, validation, and risk requirements. This ladder does
not require every value to become an ontology concept. Open-ended narrative
may remain free text; small stable application-owned sets may remain validated
values or reference data.

Semantic modelling is justified when stable identity, relationships,
cross-system meaning, governed vocabulary, provenance, graph-shaped validation,
or machine-readable semantics solve a demonstrated problem. SEAG records the
reason for selecting the semantic stage and the provenance of any adopted
vocabulary.

## Current assessment

The machine-readable assessment is [`maturity.yaml`](../maturity.yaml). Its
levels describe the identified capability scope at the recorded source commit;
they are not a blanket project score.

As of the initial assessment:

| Capability | Level | Evidence and limitation |
|---|---:|---|
| Framework charter and boundary policies | 2 Surface-defined | Normative documents exist; no released source contract |
| Identity, provenance, language, and standards policies | 2 Surface-defined | Documented and reviewed locally; not wired into the released validator |
| Reproducible release-candidate bundling | 4 Validated | Local repeatability tests and passing GitLab pipelines; no supported release |
| SPDX coverage enforcement | 4 Validated | Exact-header check and CI evidence; no public release |
| Normative semantic source contract | 1 Planned | Roadmap on `main`; external candidate is not integrated evidence |
| Semantic validator | 1 Planned | Not present on `main` |
| Ontology-to-glossary extraction | 1 Planned | Contract assigned; no implementation on `main` |
| CmapTools CXL exchange | 1 Planned | Roadmap only |
| AGF, Ponytail, and Caveman profiles | 1 Planned | Interoperability targets only |

SEAG's problem framing is **Empirically informed** by Rediflow and SEAG's own
incubation. Claims that SEAG improves independent projects remain
**Theoretical** until multiple independent adopters provide verifiable evidence.
