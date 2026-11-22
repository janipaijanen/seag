<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# SEAG concepts for software engineers

This introduction is for readers who know ordinary software-development
practices but are new to concept maps and ontologies. It gives enough context
to understand SEAG without treating SEAG as an ontology course, diagram editor,
or reasoning engine.

## The software problem

A project gives important words meanings: `account`, `permission`, `release`,
`component`, and `dependency`, for example. Those meanings appear in
requirements, UI text, schemas, code, tests, diagrams, decisions, and agent
instructions. The representations drift. Two teams may use one label for
different concepts, or different labels for the same concept.

SEAG treats semantic source material with familiar engineering controls:
stable identity, bounded syntax, provenance, validation, versioning, review,
and reproducible derived artifacts. It does not decide the customer's domain
meaning. It records what the source says, what has been decided, and what
remains unresolved.

## A small vocabulary

| Term | Meaning in this introduction | Software analogy |
| --- | --- | --- |
| Label | A human-readable name for a concept | A display name, not a primary key |
| Concept | An identified meaning that can retain its identity when its label changes | An entity with a stable ID |
| Definition | A statement that bounds the intended meaning | A documented contract |
| Relation | A named static semantic connection | A typed association |
| Proposition | Concepts connected by a relation to make a meaningful statement | A small, reviewable assertion |
| Provenance | Evidence of where an assertion came from and how it was handled | Commit and decision metadata |
| Ontology | An explicit specification of concepts and relations in a domain | A semantic domain model, not an object model |
| Source bundle | Versioned SEAG source with identity, inventory, and digests | A validated source package |
| Variant | A generated representation tied to its source | A build artifact with provenance |

## Concept maps

A concept map is a human-oriented representation of knowledge. Concepts are
shown as nodes. Linking phrases connect them. Two or more connected concepts
and their linking phrase form a proposition that should be readable as a
meaningful statement.

For example:

```text
web application -- is a kind of --> software component
software component -- is governed by rule --> support policy
```

Concept maps are useful for learning, discussion, discovery, and review. A
drawing alone does not necessarily define stable identifiers, formal
cardinality, provenance, validation rules, or machine reasoning.

The standard introductory reference is Joseph D. Novak and Alberto J. Cañas,
[The Theory Underlying Concept Maps and How to Construct and Use
Them](https://cmap.ihmc.us/docs/theory-of-concept-maps.php), IHMC CmapTools
Technical Report 2006-01, revised 2008.

## Ontologies

In software and knowledge engineering, an ontology explicitly specifies a
shared conceptualization of a domain: its concepts, relations, and applicable
constraints. An ontology is about the domain meaning, not merely the spelling
of words and not primarily the methods of object-oriented classes.

There is no single correct model for every purpose. A useful ontology states
its scope and modelling choices so that people and tools can determine whether
it fits their application.

Foundational and practical introductions are:

- Thomas R. Gruber,
  [A Translation Approach to Portable Ontology Specifications](https://tomgruber.org/writing/ontolingua-kaj-1993.pdf),
  *Knowledge Acquisition* 5(2), 1993, DOI
  [10.1006/knac.1993.1008](https://doi.org/10.1006/knac.1993.1008).
- Natalya F. Noy and Deborah L. McGuinness,
  [Ontology Development 101](https://protege.stanford.edu/publications/ontology_development/ontology101.pdf),
  Stanford Knowledge Systems Laboratory, 2001.
- Rudi Studer, V. Richard Benjamins, and Dieter Fensel,
  [Knowledge Engineering: Principles and Methods](https://doi.org/10.1016/S0169-023X(97)00056-6),
  *Data & Knowledge Engineering* 25, 1998.

## Where SEAG fits

SEAG is the governed semantic source and transformation framework between
domain evidence and useful representations:

```text
domain evidence
      |
      v
SEAG source bundle
      |-- glossary
      |-- concept map
      |-- SKOS representation
      `-- another compatible variant
```

The customer owns the ontology and domain decisions. SEAG provides source
identity, validation, provenance, review declarations, and loss-aware
transformation. An exporter may generate a concept map or another exchange
format, but the generated view does not silently become the authoritative
source.

SEAG is not:

- the customer's ontology;
- a universal upper ontology;
- a CmapTools replacement;
- a complete RDF or OWL reasoner;
- a process or workflow modeller; or
- proof that a recorded meaning is true or that a named actor had authority.

## Example domain: the concept of a state machine

A state machine is a model for describing a system in terms of its possible
states and the rules by which it can change from one state to another. It is
useful when a system's permitted behaviour depends on its current condition.

Consider a simple access turnstile. At a particular moment it may be `locked`
or `unlocked`. Inserting an accepted token while it is locked may change it to
unlocked. Passing through while it is unlocked may return it to locked. The
model makes invalid or unspecified behaviour visible instead of scattering it
among `if` statements.

The basic concepts are:

| Concept | Introductory meaning |
| --- | --- |
| State machine | The model that defines the applicable states and change rules |
| State | A named condition relevant to the modelled behaviour |
| Initial state | The state in which an instance begins |
| Transition | A permitted change from a source state to a target state |
| Event | An occurrence considered by the state machine |
| Guard | A condition that must hold before a transition may occur |
| Action | An effect associated with handling an event or transition |

A behavioural notation might express part of the example as:

```text
locked -- accepted token --> unlocked
unlocked -- person passes --> locked
```

That diagram describes behaviour: ordering, permitted change, and response to
events. It belongs in a state-machine language or implementation, not in SEAG's
semantic relation vocabulary.

SEAG can still record the meaning of the vocabulary used by that model. For
example, it can identify and define the singular concepts `state machine`,
`state`, `transition`, `event`, and `guard`; record the source and review status
of each definition; and refer to the external turnstile model by a stable IRI.
It can also record static semantic statements such as `guard is a kind of
rule`, if the project's evidence supports that classification.

### Static logging concepts around a state machine

A project may separately describe static architecture associated with a state
machine. For example, it may define these distinct identities:

| Local ID | SEAG kind | Preferred label | Meaning in the example |
| --- | --- | --- | --- |
| `LoggingConcept` | `concept` | Logging | The semantic notion or capability of recording diagnostic information |
| `LoggingComponent` | `concept` | Logging component | A software component that implements logging |
| `Configuration` | `concept` | Configuration | The static settings used by a component |

The state-machine concept **may have** the `LoggingConcept`, and the
`LoggingComponent` **has** `Configuration`. In authoritative SEAG source, the
relation and quantity remain separate:

```text
source: StateMachine
relation: has logging
target: LoggingConcept
source cardinality: unresolved
target cardinality: 0..1

source: LoggingComponent
relation: has configuration
target: Configuration
source cardinality: unresolved
target cardinality: 1..1
```

An exporter may therefore render the first statement as “state machine may
have Logging” and the second as “Logging component has Configuration.” The
cardinalities above are explicit example decisions: use `0..*` instead of
`0..1` if a state machine may have several logging concepts, and do not infer
`1..1` merely from the English word “has” when the project has not decided the
quantity.

`LoggingConcept` and `LoggingComponent` must not share an identifier merely
because a diagram shortens both labels to “Logging.” If “Logging” denotes one
concrete code module or deployed resource rather than a domain concept, record
that artifact as an `external_reference` and keep its implementation model
authoritative.

SEAG must not translate the two turnstile arrows into ordinary semantic
associations such as `locked precedes unlocked`. Doing so would hide executable
transition meaning inside a static relation. The state-machine artifact remains
authoritative for source states, target states, events, guards, actions,
ordering, and runtime behaviour.

This separation is useful rather than restrictive:

- the state-machine tool answers, “What may happen next?”;
- SEAG answers, “What do these terms mean, where did those meanings come from,
  and which reviewed artifact defines the behaviour?”

## Identity is not a label

A label is presentation. A concept is meaning with stable identity. Renaming a
label or translating it must not create a new concept unless the meaning also
changes.

SEAG concept labels are always recorded in singular form. This keeps class-like
concept names consistent and avoids modelling `component` and `components` as
different concepts. The declaration is machine-checked; a linguistically
competent human determines whether the actual label is singular in its stated
language.

## Relations and cardinality are separate

A phrase such as `has one or more` combines a relation with a quantity. That is
convenient on a drawing but ambiguous as authoritative semantic source. SEAG
records the semantic relation and both endpoint cardinalities separately.

```text
source concept: Project
relation: has member
target concept: Person
source cardinality: 0..*
target cardinality: 1..*
```

A presentation exporter may render a natural-language phrase from those
fields. A cardinality change then remains a cardinality change instead of
silently changing the relation vocabulary.

`is a kind of` has a specific taxonomic meaning. If `web application is a kind
of software component`, every web application described by that classification
is also a software component. SEAG rejects taxonomy cycles but does not infer a
complete domain ontology from a few propositions.

## Provenance and review

For an assertion to be useful later, readers need more than its text. They need
to know its source and locator, whether that source is normative, who proposed
the interpretation, its verification status, and whether a separate decision
and review were recorded.

SEAG validates the declarations and their internal consistency. It does not
authenticate the people, prove their authority, or turn self-review into
independent evidence.

## Source and generated variants

Treat a SEAG source bundle like reviewed source code. Treat a glossary,
diagram, or exchange file generated from it like a build artifact. A variant
must identify its source and generator and disclose omissions, unsupported
constructs, and semantic loss. Editing a generated variant does not update the
source automatically.

## Worked review questions

When capturing a concept, ask:

1. What single meaning are we identifying?
2. Is its preferred label singular in the declared language?
3. What definition includes the intended cases and excludes nearby meanings?
4. Where did that definition come from, exactly?
5. Is the source normative, informative, or still unresolved?
6. Which static relations are actually supported by evidence?
7. Are relation direction and both cardinalities explicit?
8. Who proposed, decided, and reviewed the interpretation?
9. What would be lost when exporting it to another representation?

These questions guide semantic discovery. They are not a workflow language:
SEAG records the meaning and evidence of the resulting material, not the
execution sequence used to produce it.

## Continue reading

- [SEAG source contract 0.1 draft](source-contract-0.1.md)
- [Identity, bundles, and variants](identity-bundles-and-variants.md)
- [Term adoption and provenance](term-adoption-and-provenance.md)
- [Semantic minimality](semantic-minimality.md)
- [Standards and conformance](conformance.md)
- [Explicit process-modelling boundary](charter.md#hard-non-goal-process-and-workflow-modelling)
