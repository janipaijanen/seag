<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Rediflow evaluation plan for SEAG 0.2.0-alpha.1

## Decision and boundary

Rediflow is the first controlled adopter of the SEAG 0.2 semantic-review
prototype. It supplies product evidence and defects; it does not govern SEAG or
donate its ontology to SEAG. Rediflow concepts, source files, access controls,
and business decisions remain in Rediflow-owned repositories. The SEAG
repository retains only invented fixtures or deliberately sanitized evidence
that can be published under SEAG's contribution terms.

This pilot evaluates a pinned `v0.2.0-alpha.1` release archive. Before the tag
exists, release-branch runs test the candidate only. The evidence record must
name the tag, full commit, archive SHA-256, Python and Git versions, operating
system, commands, and Rediflow source revisions.

## Questions

1. Can a Rediflow contributor author and review a bounded semantic source with
   an ordinary text editor and no AI dependency?
2. Does semantic diff expose consequential changes that ordinary Git diff or
   plain JSON review obscures?
3. Does three-way review catch clean textual merges that would attach changed
   meaning to the wrong structure, status, provenance, or confirmation?
4. Does canonical rendering reduce review noise without changing declared
   meaning or damaging project-owned files?
5. Which genuine Rediflow concepts or associations cannot be expressed without
   violating SEAG's domain-neutral and non-process boundaries?

## Corpus selection

The semantic owner selects a small but real vertical slice rather than exporting
the complete Rediflow ontology. The provisional target is 25–75 singular
concepts, their static associations and cardinalities, at least two source
fragments, and at least two genuine historical semantic-change events. Adjust
the size before execution if confidentiality, review effort, or source shape
makes that range misleading; record the reason rather than changing it after
results are known.

Exclude executable workflow, state transitions, credentials, customer data,
personal data, secrets, and content that cannot be retained in the Rediflow
evidence environment. Reference authoritative external artifacts rather than
copying them when the 0.1 source contract permits. SKOS import and semantic
mapping records are not implemented in this alpha and must be logged as gaps,
not simulated with matching labels.

## Baseline and exercises

Retain a baseline review of the same changes using Git diff and the project's
current JSON or documentation checks. Then perform:

1. validation of the original Rediflow-owned SEAG bundle;
2. canonical rendering into a new directory, followed by validation and a
   semantic diff proving zero declared semantic changes;
3. two-way review of at least two real historical changes;
4. seeded definition, label, status, provenance, cardinality, removal, and
   external-IRI changes with expected diagnostic classes;
5. three-way divergent-definition, delete/modify, divergent-addition,
   structural-overlap, and confirmation-scope cases;
6. one complete human-only run; and
7. an optional AI-assisted run whose proposals remain unconfirmed until a
   responsible human decision outside SEAG.

Use `--format json` and retain the exact outputs. Use `--fail-on breaking` for
two-way CI experiments and the default fail-on-conflict policy for three-way
experiments. The pilot may recommend different policy, but SEAG does not encode
Rediflow's approval workflow or reviewer authority.

## Feedback record

Each finding records:

- Rediflow source revision and sanitized scenario identifier;
- expected and actual outcome;
- diagnostic or conflict code;
- false-positive, false-negative, usability, performance, security,
  documentation, or source-contract classification;
- whether the problem is SEAG-generic or Rediflow-specific;
- human review time compared with the baseline;
- workaround, if any, and whether it risks semantic loss; and
- disclosure status: private, sanitizable, or publishable.

Raw restricted content must not be pasted into public SEAG issues. A sanitized
reproducer uses invented names and retains only the structural condition needed
to reproduce the defect.

## Pilot exit decision

Continue toward another 0.2 prerelease only if Rediflow demonstrates a material
review advantage over its baseline, no implemented conflict class produces a
known silent false negative in the retained cases, canonical output remains
semantically unchanged, and the remaining authoring burden is credible for
human-only use.

Revise the alpha contract if diagnostic meaning, canonical bytes, or conflict
boundaries must change. Stop or narrow semantic-review development if ordinary
Git plus validation is equally effective, reviewers cannot understand the
findings, or maintaining SEAG source costs more than the observed semantic
failures. No outcome from this single related project is independent-adopter
evidence or sufficient for stable 0.2 publication.
