# Standards and conformance

## Purpose

This document is the authoritative register policy for external standards used
by SEAG. The machine-readable register is [`standards.yaml`](../standards.yaml).
If the two disagree, this document governs until the inconsistency is corrected.

SEAG uses the terms **MUST**, **MUST NOT**, **REQUIRED**, **SHOULD**, **SHOULD
NOT**, and **MAY** as described by RFC 2119 and RFC 8174 when, and only when,
they appear in uppercase.

## Conformance classes

Each external specification is assigned one of these classes:

- **core**: every conforming SEAG 0.1 artifact or implementation in the stated
  scope follows it;
- **conditional**: required only when the named feature is used;
- **mapping**: SEAG retains its own source model and documents correspondence,
  coverage, and loss to the external model;
- **export profile**: required only when an implementation claims that named
  representation or interoperability profile; or
- **publication gate**: must be pinned and satisfied before public release,
  but is not yet a claim of the private incubation version.

Listing a standard does not by itself claim conformance. A conformance claim
requires an identified scope, pinned version, declared class, documented
limitations, and repeatable evidence.

## Core requirements

### Normative language

SEAG specifications use RFC 2119 as updated by RFC 8174. Lower-case words such
as "must" or "should" are ordinary prose and are not normative keywords.

### Language tags

Language identification follows BCP 47, specifically RFC 5646. Language-range
matching and fallback follow RFC 4647 Lookup. Registry-aware validation pins
the `File-Date` value of the IANA Language Subtag Registry in its evidence.
SEAG's detailed requirements are in the
[language-tag policy](language-tags.md).

### Identifiers

Absolute URI identifiers follow RFC 3986. Internationalized identifiers follow
RFC 3987. SEAG records whether a field permits a URI, an IRI, or a specific URN
form; implementations must not silently treat all three as interchangeable.

When SEAG tooling generates UUIDs, it follows RFC 9562. A UUID is an identity
mechanism, not evidence of ownership, authority, chronology, or uniqueness
beyond the guarantees of the selected generation method.

### JSON and schemas

Normative JSON interchange follows RFC 8259 and uses UTF-8. SEAG 0.1 JSON
schemas use JSON Schema Draft 2020-12 and identify its meta-schema explicitly.
Diagnostics that identify a location inside a JSON document use JSON Pointer
as defined by RFC 6901.

Schema validity is not complete SEAG conformance. Cross-file identity,
provenance, compatibility, semantic-minimality, and prohibited-process checks
remain validator responsibilities.

### Time

Machine-readable timestamps use the RFC 3339 date-time profile. An instant uses
an explicit UTC offset; generated provenance should use `Z`. A date without a
time is allowed only when the field explicitly models a calendar date rather
than an instant. Implementations must not infer a timezone from the host.

### Unicode

Text is Unicode and interchange is UTF-8. Where SEAG requires normalized text,
it uses Unicode Normalization Form C (NFC) as specified by the Unicode Standard
and UAX #15. A validator records the Unicode data version it used.

Normalization must not be used to conceal an authored change. Identifiers are
compared according to their governing URI, IRI, or UUID specification, and
security-sensitive tooling must report suspicious mixed-script or confusable
identifiers rather than silently rewriting them.

## Conditional requirements

### Canonical JSON

If a digest or signature is defined over canonical semantic JSON rather than
the exact stored bytes, canonicalization follows RFC 8785 (JSON Canonicalization
Scheme). The artifact records which bytes were digested and the digest
algorithm. Exact-file digests do not require RFC 8785 and must not be described
as canonical semantic digests.

### Published licence expressions

Published SEAG artifacts use SPDX licence expressions and pin the applicable
SPDX specification and licence-list versions. Private-incubation metadata may
remain provisional, but publication cannot proceed with an ambiguous licence
identifier or missing licence text.

## Semantic mappings

### W3C PROV

SEAG provenance must have a documented mapping to the W3C PROV data model.
Source artifacts map to entities, transformations and extraction map to
activities, and responsible humans or software map to agents. This requirement
does not make RDF, OWL, or PROV-O the authoritative SEAG storage syntax.

A future PROV-O exporter is an export profile. It must document unmapped SEAG
fields, identifier preservation, qualification of relationships, and
round-trip limits before claiming compatibility.

### W3C SKOS

SEAG glossary concepts and linguistic values must have a documented mapping to
SKOS where the meanings overlap. Preferred and alternative labels, definitions,
notes, and broader/narrower relationships are mapping candidates. SEAG identity,
cardinality, assertion status, and provenance requirements may be stricter than
SKOS and remain authoritative.

SEAG must not claim that its source model "is SKOS". A SKOS export profile must
declare every omission or approximation and provide fixtures demonstrating the
claimed mapping.

## Representation profiles

CmapTools CXL, JSON-LD, RDF, OWL, PROV-O serialization, and other external
representations are export profiles, not core dependencies. Each profile must:

1. identify the external specification or tool and exact version;
2. define the supported source subset and transformation version;
3. preserve stable identifiers and provenance, or declare loss explicitly;
4. list unsupported constructs and approximations;
5. provide deterministic fixtures where the format permits it; and
6. retain round-trip or independent-consumer evidence appropriate to the claim.

CXL interoperability must pin the tested CmapTools or compatible implementation
because CXL behavior is partly tool-defined. SEAG must not describe untested CXL
output as CmapTools-compatible.

## Evidence and change control

A conformance claim records:

- the SEAG release, implementation, or artifact being assessed;
- the standard identifier and pinned version;
- conformance class and applicable feature scope;
- validator and dependency versions;
- commands, fixtures, and results;
- deviations, warnings, and known unsupported features; and
- the reviewer and provenance of the assessment.

Updating a pinned standard is a reviewed compatibility change. Tooling may
recognize a newer version without claiming support for it, but must reject an
artifact whose required standard or capability it cannot satisfy. It must not
silently downgrade, discard, or reinterpret required semantics.

## Normative references

- RFC 2119, *Key words for use in RFCs to Indicate Requirement Levels*
- RFC 8174, *Ambiguity of Uppercase vs Lowercase in RFC 2119 Key Words*
- RFC 3986, *Uniform Resource Identifier (URI): Generic Syntax*
- RFC 3987, *Internationalized Resource Identifiers (IRIs)*
- RFC 5646, *Tags for Identifying Languages*
- RFC 4647, *Matching of Language Tags*
- RFC 6901, *JavaScript Object Notation (JSON) Pointer*
- RFC 8259, *The JavaScript Object Notation (JSON) Data Interchange Format*
- RFC 8785, *JSON Canonicalization Scheme (JCS)*
- RFC 9562, *Universally Unique IDentifiers (UUIDs)*
- RFC 3339, *Date and Time on the Internet: Timestamps*
- JSON Schema Draft 2020-12
- Unicode Standard Annex #15, *Unicode Normalization Forms*
- W3C PROV Data Model and PROV-O
- W3C SKOS Reference
- SPDX Specification and SPDX License List

