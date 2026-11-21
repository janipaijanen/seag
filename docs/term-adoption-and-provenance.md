# Term adoption and provenance policy

## Purpose

SEAG defines a domain-neutral meta-ontology for capturing and transforming
project-owned semantics. It reuses standards and established vocabularies where
their definitions fit. Familiar labels never justify semantic substitution.

## Decision order

For every candidate SEAG term:

1. Search relevant normative standards first.
2. Search mature, publicly documented de-facto vocabularies when no suitable
   standard term exists.
3. Compare the complete definition, scope, constraints, identity, direction,
   cardinality, lifecycle, and intended use—not the label alone.
4. Record the search and choose exactly one disposition below.
5. Obtain independent review before marking the disposition confirmed.

Absence of a suitable term is a result to document. It is not evidence that no
such term exists everywhere.

## Allowed dispositions

### Adopted

Use the external identifier and normative meaning unchanged. SEAG may provide a
display label or serialization alias but must not weaken or extend the meaning.

### Profiled

Create a SEAG identifier that specializes or restricts an external term while
preserving all of the external term's requirements. Record the added
constraints and a directional `specializes` mapping. Do not call a term
profiled if SEAG contradicts the source definition.

### Mapped

Create a distinct SEAG identifier when the meanings overlap but are not
substitutable. Declare the relationship as exact, close, broader, narrower, or
related and record the rationale. Exact mapping requires substitutability for
SEAG's supported uses; label similarity is insufficient.

### SEAG-defined

Create a new SEAG term when no suitable standard or de-facto definition exists,
or when existing meanings conflict with SEAG's required semantics. The record
must include:

- a unique SEAG identifier and preferred label;
- a necessary-and-sufficient definition where practical;
- scope, identity criteria, constraints, examples, and non-examples;
- avoided or conflicting external terms;
- the search record and reason existing terms were rejected;
- proposed or confirmed status, author, reviewer, and decision date; and
- compatibility and migration consequences.

Choose a qualified or different label when reusing a familiar label would cause
users to assume an incompatible external meaning.

### Deprecated

Retain the identifier and provenance. Point to its replacement or explain why
there is none. Never recycle an identifier for a new meaning.

## Mapping vocabulary

SEAG aligns vocabulary mappings with the W3C SKOS mapping distinctions:
`exactMatch`, `closeMatch`, `broadMatch`, `narrowMatch`, and `relatedMatch`.
SEAG's source format may use readable names, but exporters must preserve the
distinctions and direction. Contradictory mappings, such as exact and broader
for the same pair, are invalid.

SEAG-specific `adopts` and `specializes` dispositions describe governance of a
term and are not substitutes for the mapping relationship.

## Verifiable provenance record

Each adopted, profiled, mapped, or rejected external term records:

- source organization and authoritative title;
- stable identifier or namespace URI;
- specification edition, version, status, and publication date;
- exact section, anchor, page, clause, or term locator;
- canonical URL and retrieval timestamp;
- content digest when the referenced artifact is legally retrievable and
  stable enough to hash;
- source licence or access restrictions;
- a short interpretation or permitted quotation;
- disposition and mapping relationship;
- rationale, known differences, and unresolved uncertainty;
- deriving activity, responsible person or software agent, and date;
- independent reviewer and review outcome; and
- superseded source or SEAG record, when applicable.

Normative and informative sources are marked separately. A mutable web page
without a version, locator, or archived revision cannot be the sole normative
provenance for a confirmed SEAG term.

The provenance model should align with W3C PROV concepts such as Entity,
Activity, Agent, derivation, attribution, revision, and primary source. SEAG
does not require RDF serialization to preserve those semantics. Dublin Core
metadata terms may be used for identifiers, source, references, dates, licence,
and publisher. Checksummed external-document references should follow the same
verifiability principle used by SPDX.

## Change and conflict handling

When an external source changes:

1. retain the old provenance record;
2. create a new source-version record;
3. compare definitions and constraints;
4. rerun affected mapping and transformation tests;
5. mark incompatible mappings as needing review; and
6. publish migration guidance before changing a confirmed SEAG meaning.

When authorities disagree, SEAG records both sources, their normative status,
scope, and conflict. It selects a meaning only for a stated SEAG use case and
does not claim universal resolution.

When a definition is unavailable, paywalled, unstable, or legally unsuitable
to reproduce, SEAG stores the citation and a SEAG-authored interpretation. It
does not copy restricted text or claim that the interpretation is the source's
normative definition.

## Initial standards baseline

The first assessment should evaluate, without assuming wholesale adoption:

- W3C PROV-O / PROV-DM for provenance;
- W3C SKOS for concepts, labels, notes, collections, and mappings;
- Dublin Core Metadata Terms for general resource metadata;
- SPDX practices for licences, checksums, and external references;
- CmapTools CXL for concept-map exchange; and
- relevant lifecycle, rule, decision-table, and workflow standards only for the
  boundaries and transformations SEAG actually supports.

Every baseline entry remains pinned to a version or dated recommendation and is
subject to the disposition process above.

Initial candidate sources, not yet wholesale-adopted:

- [PROV-O, W3C Recommendation 30 April 2013](https://www.w3.org/TR/2013/REC-prov-o-20130430/)
- [SKOS Reference, W3C Recommendation 18 August 2009](https://www.w3.org/TR/2009/REC-skos-reference-20090818/)
- [DCMI Metadata Terms, DCMI Recommendation 20 January 2020](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/2020-01-20/)
- [SPDX Specification 3.0.1](https://spdx.github.io/spdx-spec/v3.0.1/)
- [CmapTools CXL format](https://cmap.ihmc.us/xml/cxl.html)

The assessment must verify each locator, status, licence, and applicable
errata. Listing a candidate source here is not a conformance claim.
