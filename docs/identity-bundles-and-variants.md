<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Identity, bundles, and representation variants

## Goals

SEAG artifacts must remain identifiable when copied out of a repository,
generated into another format, combined with another bundle, or inspected years
later. Identity must not depend on a file path, Git branch, display label, or
current network access.

SEAG separates semantic identity from version, location, representation, and
content identity. One identifier must never be overloaded to mean all five.

## Identity layers

| Layer | Purpose | Stability |
|---|---|---|
| `bundle_id` | identifies one semantic collection across its lifetime | permanent |
| `release_id` | identifies one immutable released state of a bundle | permanent and immutable |
| `fragment_id` | identifies a source fragment within a bundle | stable within the bundle |
| record `id` | identifies a concept, proposition, rule reference, mapping, or other semantic record | permanent within its namespace |
| `variant_id` | identifies one generated representation of a release | immutable |
| content digest | identifies exact bytes | changes with any byte change |

Moving or renaming a file changes none of these identities. A changed label or
definition creates a revision of the same record unless its identity criteria
change. A materially different meaning receives a new record identifier and an
explicit supersession or mapping relation.

## Namespace policy

Every valid SEAG bundle has exactly one default namespace for locally defined
semantic record identifiers. The namespace is therefore always required in the
resolved data model, but it need not be manually supplied.

During initialization a user chooses one of two paths:

1. provide an absolute, stable IRI under a namespace they control; or
2. accept a tool-generated UUID URN namespace, which the tool persists.

For example:

```yaml
bundle_id: https://example.org/semantics/workforce-planning
namespace: https://example.org/semantics/workforce-planning#
```

or, for an offline/private project:

```yaml
bundle_id: urn:uuid:65a0af22-7ac8-4e89-ae96-ab73d7ea2d87
namespace: urn:uuid:65a0af22-7ac8-4e89-ae96-ab73d7ea2d87#
```

An IRI need not resolve over the network to be a valid identifier. Published
bundles should prefer a publisher-controlled HTTPS namespace when long-term
control and resolution are credible. Repository URLs, branch URLs, temporary
hosting URLs, and mutable filenames are poor namespaces.

The namespace is immutable after records have been issued. Migration to a new
namespace creates mappings; it does not rewrite history. Prefix aliases are
optional conveniences and never establish identity.

Local record IDs are required, stable, and unique within the namespace. They
should be readable but must not encode labels or classifications likely to
change. The expanded identifier is the default namespace plus the local ID.
Imports retain their original expanded identifiers.

## Bundle manifest

Every bundle has one manifest. It contains information that applies to the
semantic collection rather than duplicating it in every record:

```yaml
seag_schema: 0.1
bundle_id: urn:uuid:65a0af22-7ac8-4e89-ae96-ab73d7ea2d87
namespace: urn:uuid:65a0af22-7ac8-4e89-ae96-ab73d7ea2d87#
title: Example semantic bundle
default_language: en
status: draft
licence: CC-BY-4.0
```

The complete manifest model includes:

- schema version and declared SEAG profiles;
- bundle identity, namespace, title, description, and default language;
- publication status and release version;
- publisher, rights holder, licence, and access classification;
- imported bundles and external vocabularies, pinned by identifier, version,
  locator, and digest where available;
- fragment inventory with role, media type, and digest;
- bundle-level provenance and review state; and
- optional signature and verification information.

`default_language`, fragment languages, and representation languages are BCP
47 tags and follow the [language-tag policy](language-tags.md). A language tag
describes content and never participates in semantic record identity.

A bundle is a packaging and identity boundary, not a process boundary or an
ontology claim. One adopting project may maintain several bundles when their
ownership, release cadence, access, or namespace differs.

## Self-identifying fragments

Source files that may travel separately carry a minimal envelope:

- `seag_schema`;
- `bundle_id`;
- the default `namespace`, unless every record identifier is already expanded;
- `fragment_id`;
- fragment role and language when applicable; and
- the bundle release or draft revision they describe.

They do not duplicate the complete manifest. A repeated namespace must match
the manifest. File digests live in the manifest or a detached verification
record; embedding a file's own digest in its content would create a circular
value.

## Releases and revisions

`version` is a publisher-assigned release label. SEAG does not require semantic
versioning, although a project may adopt it. The publishing tool mints or
validates an absolute `release_id`, freezes the manifest and fragment inventory,
and calculates their digests. A released version and release ID are immutable.

Draft revisions may use source-control commits plus content digests. A Git
commit is useful provenance but is not the bundle's permanent semantic identity.

## Representation variants

A variant is a generated representation of one immutable bundle release. It
does not acquire authority over the source semantics.

Examples include CXL, JSON, JSON-LD, Markdown documentation, a compact agent
context, or a tool-specific integration profile. A variant record contains:

- `variant_id` and `representation_of` release ID;
- format, media type, language, audience, and profile;
- generator name, version, and build identity;
- transformation identifier and version;
- normalized transformation parameters;
- source manifest digest and output digest;
- generation timestamp and responsible software agent;
- whether the transformation is lossless for its declared scope;
- known omissions, approximations, and unsupported source constructs; and
- round-trip or conformance verification result.

The tool generates variant identity, digests, timestamps, generator data, and
transformation provenance. A user selects requested format, language, audience,
profile, and any semantic subset. Cosmetic layout or theme is variant metadata.
A subset or projection must record its selection expression; it must not imply
that omitted semantics do not exist.

Two files with different bytes have different content identities even if they
are equivalent representations. Two outputs with different semantic selection,
language, profile, or lossy behavior are distinct variants.

## User-set and tool-set information

### Set or confirmed by the user or publisher

- title, description, default language, and access classification;
- publisher-controlled bundle ID and namespace, when available;
- stable local record IDs, with optional safe tool suggestions;
- semantic definitions, status, mappings, and ownership;
- licence and rights-holder assertions;
- release version and publication decision;
- requested output format, profile, audience, language, and subset; and
- acceptance of reviewed provenance and compatibility claims.

### Generated or verified by SEAG tooling

- UUID-based bundle ID and namespace when the user provides none;
- release, fragment, and variant identifiers when not publisher-assigned;
- expanded record identifiers;
- schema and generator versions;
- canonical content and manifest digests;
- generated and retrieved timestamps;
- source-control revision observations;
- normalized transformation parameters;
- file inventory and media types;
- validation, mapping-consistency, and round-trip results; and
- derivation links between source releases and variants.

Tool-generated facts are not editable assertions. Regeneration replaces them
only when their inputs change and retains the earlier provenance chain.

### Imported from an external authority

- external identifiers and namespaces;
- source versions, publication status, definitions, and licences; and
- normative locators and available digests.

SEAG preserves these as sourced claims. The user or tool may add an
interpretation or mapping but must not rewrite the external authority's claim.

## Validation requirements

Validators must reject:

- missing resolved namespace or bundle identity;
- duplicate expanded identifiers;
- relative identifiers where a portable identity is required;
- changes to an issued namespace or released bundle;
- reused release, record, or variant identifiers with different meanings;
- variants without an immutable source release and source digest;
- claimed lossless variants with unreported unsupported constructs; and
- external imports lacking sufficient provenance to identify the source;
- malformed language tags or unsupported required language capabilities; and
- generated language variants that conceal fallback, missing values, or lost
  linguistic provenance.
