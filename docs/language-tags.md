# Language tags and multilingual content

## Scope

SEAG uses IETF BCP 47 language tags to identify the language of labels,
definitions, aliases, notes, and generated representations. BCP 47 is the
combination of RFC 5646, which defines language tags, and RFC 4647, which
defines language-range matching.

A language tag describes linguistic content. It does not identify a concept,
record, bundle, or release. Changing or adding a translation therefore does
not mint a new concept ID. Stable semantic identifiers remain language-neutral.

## Representation

Language-bearing values carry an explicit `language` tag. Bundle and fragment
defaults may reduce repetition, but a resolved value always has a determinable
language:

```yaml
id: customer
labels:
  - language: en
    value: Customer
  - language: fi
    value: Asiakas
definitions:
  - language: en-GB
    value: A party receiving the offered service.
```

Tags use BCP 47 syntax, for example `en`, `en-GB`, `fi`, `sr-Latn`, or
`zh-Hant-TW`. Tools compare tags case-insensitively and should emit the usual
display casing: lower-case language and variant subtags, title-case script
subtags, and upper-case region subtags. Casing does not change meaning.

Tools must not invent tags by converting locale names such as `English`,
`Finnish`, or `en_UK`. A user-facing locale picker may map a selection to a
valid tag, but the stored value is the tag and the mapping must be
deterministic. Private-use tags beginning with `x-` are permitted only when no
registered tag expresses the requirement; their local meaning must be
documented by the bundle.

The special tags have their BCP 47 registry meanings:

- `und` means the language is undetermined;
- `mul` means the value contains multiple languages; and
- `zxx` means the value has no linguistic content.

They are not substitutes for missing metadata. In particular, a missing
translation is absent, not an empty value tagged `und`.

## Validation and normalization

SEAG tooling must reject malformed language tags with a diagnostic identifying
the field and value. Validation and normalization must use a pinned version of
the IANA Language Subtag Registry, and the tool or validation report must expose
that registry version.

Deprecated subtags remain recognizable input. A tool may recommend or emit an
IANA `Preferred-Value`, but it must not silently change authored data. Such a
normalization records the original tag, normalized tag, registry version, tool
version, and transformation provenance. Extensions and private-use subtags
must not be discarded.

SEAG 0.1 does not infer likely subtags, dialect, script, or region. For example,
it does not expand `en` to `en-Latn-US`. A more specific tag asserts more
specific metadata and must come from the source or an explicit, traceable
transformation.

## Selection and fallback

A consumer requests one language range and may provide an ordered fallback
list. Selection uses RFC 4647 Lookup semantics: progressively truncate a
requested tag until a matching available tag is found, then try each explicit
fallback in order. A bundle's `default_language` is not an implicit fallback
unless the caller or representation profile explicitly selects that policy.

For example, with available values `fi`, `en-GB`, and `en`, a request for
`fi-FI` may select `fi`. A request for `sv-FI` with fallback `[en-GB, en]`
selects `en-GB`. It must not select an unrelated language merely because that
value exists.

Generated output records, for every selected value:

- the requested language range;
- the actual source language tag;
- whether lookup truncation or fallback was used;
- the selected fallback position, when applicable; and
- a missing marker when no permitted value exists.

A fallback value must never be presented as though it were a translation in
the requested language. Deterministic generation also records the complete
ordered fallback policy in the representation variant.

## Translation and provenance

Every translation is a distinct authored or derived linguistic assertion and
retains its own provenance. It should identify its source assertion, source
language, responsible human or software agent, creation or retrieval time,
review status, and applicable source version or digest. A translation does not
inherit the evidential authority of its source merely by referencing it.

Machine translation is outside the SEAG 0.1 core. A future transformation may
produce machine-translated candidates, but it must identify the model or
service and version, parameters where available, input digest, generation
time, source language, target language, and review state. Unreviewed generated
text must not be represented as an approved definition.

Glossary extraction preserves both layers of provenance:

1. source provenance for the selected label, definition, alias, or note; and
2. extraction provenance for the tool, version, input digest, language request,
   fallback policy, selection result, and output.

Export formats that cannot carry these facts directly require an accompanying
provenance sidecar. An exporter must fail or report a declared lossy variant;
it must never silently omit provenance.

## Compatibility

Language support is a declared source and representation capability. A tool
must reject an unsupported required language capability or language-tag policy
version with an actionable compatibility error. The presence of a valid BCP 47
tag does not claim that a translation exists, is accurate, or has been
reviewed; those are separate, provenance-backed assertions.

Normative external references:

- RFC 5646, *Tags for Identifying Languages*;
- RFC 4647, *Matching of Language Tags*; and
- the IANA Language Subtag Registry.
