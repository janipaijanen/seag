<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Rediflow evaluation plan for SEAG 0.2.0-alpha.1

> **Historical, superseded plan.** Alpha.1 was rejected before the Rediflow
> pilot started after input-boundary defects were found during review. Preserve
> this version-pinned plan and any alpha.1 candidate evidence for replay; a new
> evaluation requires a separately reviewed successor tag and adopter-side
> decision record.

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

## Adopter-controlled schedule

The adopter owns its dates, decision authority, staffing, and deadline changes.
Those product-governance decisions belong in the adopter's versioned evidence
record and are deliberately not distributed in a SEAG release.

For a time-bounded evaluation, SEAG recommends recording these checkpoints in
that evidence record:

- start and source-freeze;
- baseline, named owners, durable location, and corpus readiness;
- immutable SEAG tag and exact tagged-candidate replay;
- two-way historical review;
- three-way review and version replay; and
- final evidence package and adopter decision.

Before the selected SEAG tag exists, read-only scratch work and tool runs are
candidate evaluation only: every run records the exact release-branch commit
and archive checksum, changes no adopter product tree, and cannot count as
tagged-release evidence. After the tag, the adopter replays the retained cases
against the immutable tagged archive.

Missing a checkpoint must not silently change the evaluation window. The
adopter records any dated re-baseline, its authority, and its reason in the
adopter-controlled evidence record. SEAG defines neither that authority nor an
approval workflow.

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

## Cross-artifact participation

This is a Rediflow product pilot, not an ontology-team-only exercise. Rediflow
must name one semantic owner, one durable-evidence owner, and participating
contacts for the selected slice across specifications, plans, code, UI, API,
database, documentation, and tests. One person may cover several areas when
that reflects the actual team. An area that genuinely does not represent or
consume the selected concepts records `not applicable` with a reason rather
than creating artificial work.

Each participating area contributes:

- the exact artifact revision and locator where selected meanings appear;
- the terms, identifiers, fields, labels, or constraints it owns or consumes;
- at least one known ambiguity, drift risk, or historical meaning change when
  available;
- review of the expected SEAG identity, definition, status, provenance,
  association, and implementation-alignment result; and
- observed authoring and review effort for the baseline and SEAG-assisted run.

The artifacts are evidence sources and consumers, not material to convert in
full. A UI label, API field, database column, code symbol, test name, plan, or
specification phrase does not automatically become a SEAG concept. The pilot
selects concepts only where stable identity and cross-artifact meaning provide
value, and it references concrete artifacts for what they authoritatively own.
Plans remain plans, code remains executable authority, schemas retain structural
authority, and SEAG does not model their workflow or runtime behavior.

Rediflow keeps a versioned cross-artifact trace in its evidence store linking
each selected concept to relevant artifact revisions and review findings. That
trace is pilot evidence, not a new mandatory SEAG core record type.

## Rediflow repository placement

The default system of record is the existing Rediflow product repository. This
keeps semantic source, product artifacts, tests, instructions, and evidence on
one commit graph and requires no additional service credential. Rediflow should
use these paths:

| Path | Contents | Primary steward |
| --- | --- | --- |
| `semantics/seag/` | Authoritative Rediflow-owned SEAG manifest and fragments | Semantic owner |
| `docs/testing/seag/` | Human instructions, pilot scope, interpretation guidance, and decision summaries | Evidence owner and documentation contact |
| `scripts/seag/` | Thin Rediflow runner, checksum verification, replay, and report-index scripts | Build/test contact |
| `test/fixtures/seag/corpus/` | Immutable sanitized or repository-authorized replay cases | Evidence owner |
| `test/fixtures/seag/expectations/` | Versioned expected diagnostics, conflicts, and rationales | Semantic owner and test contact |
| `test/evidence/seag/runs/` | Append-only baseline and SEAG run manifests, outputs, timings, and findings | Evidence owner |
| `test/evidence/seag/migrations/` | Derived version-lift copies and migration/loss evidence; never original replacement | Evidence owner and migration reviewer |
| `test/tools/seag/<version>/` | Exact SEAG release archive, checksum, and release provenance used for replay | Build/test contact |

The authoritative SEAG Python implementation remains inside the pinned SEAG
release archive under `test/tools/seag/<version>/`; Rediflow must not copy
individual SEAG modules into its own source tree. Rediflow-specific Python
scripts live under `scripts/seag/` and remain thin orchestration: verify the
archive checksum, create an isolated temporary extraction, invoke the pinned
commands, capture outputs, and write a run manifest. Generated canonical source
stays under the run evidence until a human reviews and deliberately commits it
to `semantics/seag/`.

The initial corpus and JSON results are small enough for ordinary Git. Do not
introduce Git LFS, a database, or a hosted evidence service without measured
need. If some evidence is more restricted than the Rediflow product repository,
place only that material in a dedicated Rediflow-controlled private evidence
repository using the same logical layout. The product repository then retains
an access-safe immutable locator, digest, classification, corpus version, and
replay instructions. SEAG never receives that credential or restricted content.

Pilot work uses ordinary Rediflow branches and merge requests. Suggested owner
rules require semantic-owner review for `semantics/seag/` and expectations,
evidence-owner review for corpus and runs, and build/test review for runners and
pinned tools. These are Rediflow repository controls, not SEAG workflow fields.

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

## Durable evidence on the Rediflow side

Rediflow MUST preserve the pilot corpus, expectations, executions, findings,
and migration exercises in a Rediflow-controlled versioned repository or
equivalently durable controlled evidence store. A SEAG issue, CI log, checksum,
or summary report alone is insufficient because it cannot replay a later
version lift. The retained evidence must contain the actual exercisable input
bytes; restricted inputs may remain encrypted or access-controlled, but they
must remain recoverable by authorized Rediflow maintainers.

A recommended logical layout is:

```text
seag-evidence/
  corpus/v1/cases/<case-id>/
    before/ or base/
    after/ or ours/ and theirs/
    case.json
  expectations/v1.json
  baselines/<baseline-id>/
  runs/<seag-version>/<run-id>/
    run.json
    stdout/
    stderr/
    outputs/
    findings.json
  migrations/<source-contract-from>--<source-contract-to>/<case-id>/
  tools/<seag-version>/
  index.json
```

The physical path and storage technology belong to Rediflow. The logical
evidence MUST retain:

- exact input manifest and fragment bytes for every two-way and three-way case;
- stable case IDs, corpus version, expected codes and severities, and the human
  rationale for each expectation;
- the ordinary Git or JSON baseline inputs, outputs, review time, and verdict;
- the exact SEAG archive or another durable immutable copy, tag, full commit,
  archive checksum, and implementation digest;
- operating system, architecture, Python and Git versions, relevant locale and
  environment values, complete command arguments, exit codes, stdout, stderr,
  and generated files;
- measured duration and resource observations where collected;
- the responsible semantic owner, executor, reviewer, execution time, and
  source revision; and
- every finding, disposition, workaround, confidentiality classification, and
  link to any sanitized SEAG defect.

Corpus and expectation versions are immutable. Corrections create a new corpus
or expectation version with a recorded decision and predecessor; old cases and
results are not rewritten. Runs are append-only and receive stable run IDs. A
new SEAG version first replays an unchanged historical corpus and expectations.
If the source contract requires migration, Rediflow preserves the old source,
stores the migrated copy under `migrations/`, records the migration tool and
loss assessment, and exercises both the old-version baseline and the new-version
result. It must never relabel or overwrite old input to make a new tool pass.

All evidence inherits the most restrictive classification of its inputs. Public
SEAG issues receive only separately reviewed sanitized reproducers. Expiring CI
artifacts may be convenient run outputs but are not the system of record. The
Rediflow evidence owner must verify backup, restoration, access continuity, and
the ability to run the corpus before a pilot is called preserved.

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
