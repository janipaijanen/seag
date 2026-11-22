<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Input validation and normalization

SEAG validates every external value against the contract of the field that
receives it. It does not accept a nearby value and silently turn it into the
expected one. Rejection is the default when a value is malformed, ambiguous,
duplicated, outside a closed vocabulary, or contains an unknown field.

This is an application of the pinned
[Ponytail full discipline](semantic-minimality.md#provenance-of-the-influence):
use the existing shared validator, make the smallest complete change, and never
remove trust-boundary validation for brevity.

The standard-library-only `seag.validation` package is the shared lexical and
strict-JSON boundary used by commands, transformations, and repository gates.
Field-specific semantic checks remain in the source validator. Pinned
`jsonschema`, `check-jsonschema`, `defusedxml`, `langcodes`, `rfc3986`, and
Hypothesis packages run as conformance or differential oracles under uv; they
do not replace this contract or become shipped runtime dependencies. A
difference from an oracle must be rejected as a defect or documented as an
intentional SEAG profile boundary.

## Current boundaries

| Boundary | Required behavior |
| --- | --- |
| JSON manifest, fragment, variant, and release evidence | UTF-8 JSON; one top-level value; duplicate object members and `NaN`/infinities rejected; closed field sets |
| BCP 47 field or CLI language argument | RFC 5646 well-formed tag; repeated variants and extension singletons rejected; comparison is case-insensitive without rewriting authored bytes |
| Absolute IRI | Syntactically valid absolute IRI using the exact RFC 3987 `ucschar` ranges and `iprivate` only in a query; valid percent escapes; authority ports in `0..65535`; IPv4-looking hosts with exactly four decimal octets in `0..255`; valid bracketed IPv6 when present. The strict SEAG profile additionally rejects Unicode whitespace instead of normalizing or preserving visually ambiguous spacing |
| Typed Internet port | JSON integer in `0..65535`; booleans, strings, fractions, negative values, and larger values are rejected. A profile that means an assignable or connectable service port may narrow this to `1..65535` |
| Typed IPv4 or IPv6 address | Strict IPv4 dotted decimal or a valid IPv6 address; legacy shortened/octal IPv4 forms and IPv6 interface zone IDs are not accepted |
| Local identifier | Exact ASCII pattern `[A-Za-z][A-Za-z0-9._-]*` |
| SHA-256 | Exactly 64 lower-case hexadecimal digits |
| Date and timestamp | Exact ISO date or RFC 3339 timestamp shape required by that field, followed by calendar validation |
| Enumerated status, kind, predicate, cardinality, or CLI policy | One listed value; no case folding, aliases, or fallback |
| Boolean | JSON `true` or `false`; strings and integers are not coerced |
| `SOURCE_DATE_EPOCH` | Canonical nonnegative decimal integer: `0` or a nonzero digit followed by digits |
| CmapTools CXL verification input | UTF-8 XML in the bounded SEAG CXL profile; no DTD, entity declaration, processing instruction, comment, CDATA, unknown element or attribute, duplicate identifier, undeclared endpoint, or non-SEAG connection shape |
| Human-authored text | Nonempty where required and free of forbidden control or surrogate characters; semantic content is preserved, not trimmed or rewritten |

Lexical requirements stay lexical. If a future field requires exactly three
decimal digits, its source representation is a string with the contract
`^[0-9]{3}$`; it is not parsed as an integer that would erase a leading zero.
If a field instead represents a numeric quantity, its contract separately
defines range, precision, scale, and whether exponent notation is permitted.

These network checks apply only to fields whose contract declares an absolute
IRI, Internet port, IPv4 address, or IPv6 address. CI exercises the shared
validators and their boundary values. It does not search labels, definitions,
notes, locators, or other human text for strings that merely resemble network
values; such a scan would reject legitimate concepts and examples.

Property-based boundary tests are deterministic and bounded in CI. Their role
is to search larger input classes, especially port, IP-address, and strict-JSON
edges; retained hand-written fixtures remain the readable compatibility
contract.

## Validation, normalization, and sanitation

- **Validation** decides whether input already conforms. Invalid input receives
  a located diagnostic and no semantic output.
- **Normalization** is allowed only when the governing specification declares
  two spellings equivalent. The original value remains available for
  provenance. BCP 47 case-insensitive comparison is one such operation.
- **Sanitation** is for a different output context, such as XML escaping or
  terminal-safe rendering. It must not repair semantic source or turn invalid
  input into valid input.

Schema validation is useful editor feedback but is not the complete boundary.
Callers must run the SEAG validator because JSON Schema cannot express every
cross-file, registry, duplicate-member, graph, and semantic rule.

## CLI, API, and UI rule

SEAG currently ships command-line tools and files, not a web UI or hosted API.
Any future UI or service must use the same field contracts at its authoritative
server or tool boundary. HTML input types, browser validation, drop-downs, and
client-side checks improve usability but are never authority. Pasted, uploaded,
API-submitted, imported, and agent-generated values receive the same validation
as manually typed values.

An adapter may report several errors in one pass, but it must not partially
accept a semantic record. Unknown future fields require a versioned contract;
they are not ignored for forward compatibility.

## Limits

The 0.2 alpha does not claim IANA Language Subtag Registry membership checking,
general OWL/RDF import, arbitrary CXL import, or UI validation. It validates the
implemented SEAG source contract, detached variant record, transformation CLI
arguments, and the bounded CXL graph used for compatible-parser verification.
