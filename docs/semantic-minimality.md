# Semantic minimality

## Rule

Use the smallest expression that preserves the complete intended meaning,
constraints, uncertainty, and provenance.

Semantic minimality is influenced by Ponytail's smallest-complete-change
discipline. SEAG applies the principle to semantic capture and transformation;
it does not bundle Ponytail or require an agent skill.

## Required practice

1. Reuse a suitable standard term before defining a SEAG term.
2. Keep one authoritative definition and generate other representations.
3. Add no alias, relation, qualifier, abstraction, or profile without an
   identified consumer or semantic requirement.
4. Keep the controlled predicate vocabulary as small as current requirements
   permit.
5. Prefer a simple record or table over a new ontology mechanism when it fully
   captures the required meaning.
6. Generate only representations consumed by an identified person or tool.
7. Replace duplicated prose with stable references when readability remains.
8. Avoid intermediate formats that add no demonstrated interoperability value.
9. Test meaningful transformations, rejection behavior, and round trips rather
   than tests that merely mirror implementation structure.
10. Record a known limitation with the condition that would justify expansion.

When two expressions are equally complete, prefer the one with fewer concepts,
relations, mappings, transformations, and interpretation steps. Character or
line count alone is not a quality measure. An expression requiring readers to
reconstruct omitted meaning is not minimal.

## Never remove for brevity

- stable identity and namespace;
- direction and cardinality;
- proposed, confirmed, deprecated, or unresolved status;
- scope and temporal applicability;
- normative versus informative source status;
- provenance, licence, and derivation;
- uncertainty, exceptions, and conflicting evidence;
- transformation loss and unsupported constructs;
- validation at import and export boundaries; or
- information required for the declared round trip.

## Tool behavior

SEAG tools should:

- flag duplicate definitions and semantically redundant mappings;
- recommend existing identifiers before minting new ones;
- reject vague predicates where a controlled one is required;
- show the semantic information a proposed reduction would lose;
- keep generated variants no richer than their declared consumer profile;
- never auto-delete a confirmed semantic statement solely as “redundant”; and
- require review for reductions that alter identifiers, mappings, constraints,
  provenance, or compatibility claims.

## Provenance of the influence

The initial influence is
[Ponytail `v5.3.3`](https://github.com/DietrichGebert/ponytail/blob/7801d061243d7b753bad0e0b3c057cd250b11755/skills/ponytail/SKILL.md),
commit `7801d061243d7b753bad0e0b3c057cd250b11755`, particularly its preference for
the smallest complete change, reuse before addition, and preservation of
validation, error handling, and user-required behavior. SEAG's rules above are
its own semantic application and must be reviewed independently when the pinned
Ponytail source changes.
