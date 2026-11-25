#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen
# SPDX-License-Identifier: Apache-2.0

"""Generate SEAG's bounded AI evaluation aids from authoritative sources."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
CONTEXT = Path("docs/ai-evaluation-context.md")
DOSSIER = Path("docs/ai-evaluation-dossier.md")
MANIFEST = Path("docs/ai-evaluation-dossier.json")
SOURCE_PATHS = (
    Path("VERSION"),
    Path("README.md"),
    Path("DISCLAIMER.md"),
    Path("AGENTS.md"),
    Path("CONTRIBUTING.md"),
    Path("SECURITY.md"),
    Path("maturity.yaml"),
    Path("standards.json"),
    Path("scripts/generate-evaluation-dossier.py"),
    Path("schema/source-0.1.schema.json"),
    Path("docs/canonical-source.md"),
    Path("docs/charter.md"),
    Path("docs/compatibility.md"),
    Path("docs/conformance.md"),
    Path("docs/cxl-profile.md"),
    Path("docs/glossary-extraction.md"),
    Path("docs/installation-and-upgrade.md"),
    Path("docs/licensing.md"),
    Path("docs/maturity.md"),
    Path("docs/semantic-diff.md"),
    Path("docs/semantic-mappings.md"),
    Path("docs/source-contract-0.1.md"),
)
CONTEXT_MAX_BYTES = 8_000
CONTEXT_MAX_WORDS = 1_100
BOUNDARY = (
    "SEAG is a file-oriented framework, not a hosted service or a claim that "
    "semantic content is true, actor identities are authenticated, or every "
    "planned export exists."
)
STEWARDSHIP_PATTERN = re.compile(
    r"SEAG is currently maintained by [^\n]{1,80}? as a single-maintainer "
    r"project in public review\."
)
SUPPORT_BOUNDARY = (
    "These procedures do not create a community programme, support commitment, "
    "review deadline, or production-readiness claim."
)
SECURITY_STEWARDSHIP = "SEAG is a single-maintainer project."
AI_DISCLOSURE = "SEAG is developed with AI assistance."
AI_CORE_BOUNDARY = (
    "The tested local validation and transformation path does not require an AI "
    "service."
)
EVIDENCE_STATE_RULE = """- **Confirmed:** the supplied dossier or a directly verified cited source supports
  the statement.
- **Explicitly absent:** an authoritative cited source expressly establishes
  absence.
- **Unknown/not covered:** the supplied material does not establish either
  presence or absence.

An evaluator, AI agent, or other reader **MUST NOT** invent facts,
capabilities, evidence, events, intentions, or conclusions. Silence **MUST NOT**
be converted into absence. Missing information **MUST** be reported as unknown,
not covered, or not evidenced by the supplied material. Inference **MUST** be
labelled as inference, and external information **MUST** be separated from
dossier-derived conclusions with its own source and verification status.

For example, when this dossier embeds no pilot result, report “No pilot result
is evidenced by the supplied dossier.” Do not report “No pilot exists.”
“Unpublished” means evidence establishes that material exists but it has not
been published. “Not supplied” means it is outside the supplied input and says
nothing by itself about existence. “Not verified” means it is stated but the
reader has not checked it. “Nonexistent” requires an authoritative cited source
that expressly establishes absence."""
MATURITY_NAMES = {
    1: "Planned",
    2: "Surface-defined",
    3: "Instantiated",
    4: "Validated",
    5: "Deployable",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def strict_json(data: bytes, source: str) -> object:
    def object_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"{source}: duplicate JSON member {key!r}")
            result[key] = value
        return result

    def reject_constant(value: str) -> object:
        raise ValueError(f"{source}: forbidden JSON number {value}")

    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"{source}: JSON must be UTF-8") from error
    return json.loads(text, object_pairs_hook=object_pairs, parse_constant=reject_constant)


def markdown_cell(value: object) -> str:
    text = str(value)
    if any(ord(character) < 0x20 and character not in "\t" for character in text):
        raise ValueError("generated Markdown cell contains a control character")
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("|", "&#124;")
        .replace("\t", " ")
    )


def parse_capabilities(text: str) -> list[dict[str, object]]:
    """Parse the closed block without adding PyYAML to the runtime dependency set."""
    lines = text.splitlines()
    try:
        start = lines.index("capabilities:") + 1
    except ValueError as error:
        raise ValueError("maturity.yaml has no capabilities block") from error
    capabilities: list[dict[str, object]] = []
    identifiers: set[str] = set()
    current: dict[str, object] | None = None
    current_fields: set[str] = set()
    list_name: str | None = None
    for line in lines[start:]:
        if line and not line.startswith(" "):
            break
        match = re.fullmatch(r"  ([a-z0-9-]+):", line)
        if match:
            if current is not None:
                capabilities.append(current)
            identifier = match.group(1)
            if identifier in identifiers:
                raise ValueError(f"duplicate maturity capability id: {identifier}")
            identifiers.add(identifier)
            current = {"id": identifier, "evidence": [], "limitations": []}
            current_fields = set()
            list_name = None
            continue
        if current is None:
            continue
        scalar = re.fullmatch(r"    (level|name): (.+)", line)
        if scalar:
            key, value = scalar.groups()
            if key in current_fields:
                raise ValueError(f"capability {current['id']} repeats field {key}")
            current_fields.add(key)
            if key == "level":
                if not re.fullmatch(r"[1-5]", value):
                    raise ValueError(f"capability {current['id']} level must be an integer 1..5")
                current[key] = int(value)
            else:
                current[key] = value
            list_name = None
            continue
        heading = re.fullmatch(r"    (evidence|limitations):", line)
        if heading:
            key = heading.group(1)
            if key in current_fields:
                raise ValueError(f"capability {current['id']} repeats field {key}")
            current_fields.add(key)
            list_name = key
            continue
        item = re.fullmatch(r"      - (.+)", line)
        if item and list_name:
            value = item.group(1)
            target = current[list_name]
            assert isinstance(target, list)
            target.append(value)
            continue
        if line.strip():
            raise ValueError(f"unsupported maturity capability syntax: {line!r}")
    if current is not None:
        capabilities.append(current)
    for capability in capabilities:
        if set(capability) != {"id", "level", "name", "evidence", "limitations"}:
            raise ValueError(f"incomplete capability record: {capability['id']}")
        level = capability["level"]
        if level not in MATURITY_NAMES or capability["name"] != MATURITY_NAMES[level]:
            raise ValueError(
                f"capability {capability['id']} has inconsistent maturity level and name"
            )
    if not capabilities:
        raise ValueError("maturity.yaml capabilities block is empty")
    return capabilities


def parse_evidence_status(text: str) -> dict[str, str]:
    if sum(line == "evidence_status:" for line in text.splitlines()) != 1:
        raise ValueError("maturity.yaml must contain exactly one evidence_status block")
    match = re.search(
        r"(?m)^evidence_status:\n"
        r"  problem_framing: ([a-z-]+)\n"
        r"  independent_project_benefit: ([a-z-]+)\n",
        text,
    )
    if not match:
        raise ValueError("maturity.yaml has no supported evidence_status block")
    result = {
        "problem_framing": match.group(1),
        "independent_project_benefit": match.group(2),
    }
    allowed = {"empirically-validated", "empirically-informed", "theoretical"}
    if any(value not in allowed for value in result.values()):
        raise ValueError("maturity.yaml evidence_status contains an unknown value")
    return result


def parse_evaluation_evidence_scope(text: str) -> dict[str, str]:
    if sum(line == "evaluation_evidence_scope:" for line in text.splitlines()) != 1:
        raise ValueError(
            "maturity.yaml must contain exactly one evaluation_evidence_scope block"
        )
    match = re.search(
        r"(?m)^evaluation_evidence_scope:\n"
        r"  control: ([a-z-]+)\n"
        r"  nonauthor_in_project_review: ([a-z-]+)\n"
        r"  nonauthor_review_context: ([a-z-]+)\n"
        r"  external_consumer_or_adopter_attestation: ([a-z-]+)\n",
        text,
    )
    if not match:
        raise ValueError("maturity.yaml has no supported evaluation_evidence_scope block")
    result = {
        "control": match.group(1),
        "nonauthor_in_project_review": match.group(2),
        "nonauthor_review_context": match.group(3),
        "external_consumer_or_adopter_attestation": match.group(4),
    }
    if result["control"] not in {
        "project-controlled",
        "mixed-control",
        "external-controlled",
    }:
        raise ValueError("maturity.yaml evaluation evidence control is unknown")
    for field in (
        "nonauthor_in_project_review",
        "external_consumer_or_adopter_attestation",
    ):
        if result[field] not in {"present", "absent"}:
            raise ValueError(f"maturity.yaml evaluation evidence {field} is unknown")
    if result["nonauthor_review_context"] not in {
        "none",
        "human",
        "ai-agents-in-same-project",
        "mixed",
    }:
        raise ValueError("maturity.yaml nonauthor review context is unknown")
    review_present = result["nonauthor_in_project_review"] == "present"
    context_present = result["nonauthor_review_context"] != "none"
    if review_present != context_present:
        raise ValueError(
            "maturity.yaml nonauthor review presence and context are inconsistent"
        )
    return result


def require_boundary(readme: str) -> None:
    normalized = " ".join(
        line.removeprefix("> ").strip() for line in readme.splitlines()
    )
    normalized = " ".join(normalized.split())
    if BOUNDARY not in normalized:
        raise ValueError("README.md no longer contains the canonical evaluation boundary")
    if not STEWARDSHIP_PATTERN.search(normalized) or SUPPORT_BOUNDARY not in normalized:
        raise ValueError("README.md no longer contains the canonical stewardship boundary")


def require_security_stewardship(security: str) -> None:
    normalized = " ".join(security.split())
    if SECURITY_STEWARDSHIP not in normalized:
        raise ValueError("SECURITY.md no longer contains the stewardship boundary")


def require_ai_disclosure(readme: str, disclaimer: str) -> None:
    normalized_readme = " ".join(readme.split())
    normalized_disclaimer = " ".join(disclaimer.split())
    if AI_DISCLOSURE not in normalized_readme or AI_DISCLOSURE not in normalized_disclaimer:
        raise ValueError("README.md and DISCLAIMER.md must disclose AI assistance")
    if AI_CORE_BOUNDARY not in normalized_disclaimer:
        raise ValueError("DISCLAIMER.md no longer contains the optional-AI boundary")


def standard_version(entry: dict[str, object]) -> str:
    versions = entry.get("versions")
    if isinstance(versions, list):
        return ", ".join(str(value) for value in versions)
    return str(entry.get("version", "unversioned"))


def validate_standards(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise ValueError("standards.json standards must be an array")
    result: list[dict[str, object]] = []
    identifiers: set[str] = set()
    for index, entry in enumerate(value):
        if not isinstance(entry, dict):
            raise ValueError(f"standards.json standards/{index} must be an object")
        identifier = entry.get("id")
        standard_class = entry.get("class")
        if not isinstance(identifier, str) or not identifier:
            raise ValueError(f"standards.json standards/{index}/id must be a nonempty string")
        if identifier in identifiers:
            raise ValueError(f"standards.json contains duplicate standard id {identifier}")
        identifiers.add(identifier)
        if not isinstance(standard_class, str) or not standard_class:
            raise ValueError(f"standard {identifier} class must be a nonempty string")
        claim = entry.get("claim")
        if claim is not None and (not isinstance(claim, str) or not claim):
            raise ValueError(f"standard {identifier} claim must be a nonempty string")
        version = entry.get("version")
        versions = entry.get("versions")
        if not (
            isinstance(version, str) and version
            or isinstance(versions, list)
            and versions
            and all(isinstance(item, str) and item for item in versions)
        ):
            raise ValueError(f"standard {identifier} must have a nonempty version pin")
        result.append(entry)
    return result


def capability_table(capabilities: list[dict[str, object]]) -> str:
    rows = ["| Capability | Level | Evidence locators | Limitations |", "|---|---:|---|---|"]
    for capability in capabilities:
        limitations = capability["limitations"]
        assert isinstance(limitations, list)
        evidence = capability["evidence"]
        assert isinstance(evidence, list)
        evidence_summary = "<br>".join(markdown_cell(item) for item in evidence[:2])
        if len(evidence) > 2:
            evidence_summary += f"<br>+{len(evidence) - 2} in `maturity.yaml`"
        rows.append(
            f"| `{markdown_cell(capability['id'])}` | {capability['level']} "
            f"{markdown_cell(capability['name'])} | {evidence_summary} | "
            f"{markdown_cell('; '.join(limitations)) if limitations else 'None recorded'} |"
        )
    return "\n".join(rows)


def standards_table(standards: list[dict[str, object]]) -> str:
    rows = ["| Identifier | Class | Pinned version | Claim |", "|---|---|---|---|"]
    for entry in standards:
        rows.append(
            f"| `{markdown_cell(entry['id'])}` | {markdown_cell(entry['class'])} | "
            f"{markdown_cell(standard_version(entry))} | "
            f"{markdown_cell(entry.get('claim', 'no additional compatibility claim'))} |"
        )
    return "\n".join(rows)


def render(root: Path = ROOT) -> dict[Path, bytes]:
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    maturity = (root / "maturity.yaml").read_text(encoding="utf-8")
    capabilities = parse_capabilities(maturity)
    evidence_status = parse_evidence_status(maturity)
    evidence_scope = parse_evaluation_evidence_scope(maturity)
    register = strict_json((root / "standards.json").read_bytes(), "standards.json")
    if not isinstance(register, dict):
        raise ValueError("standards.json does not have the expected register shape")
    for field in ("seag_standards_register", "status"):
        if not isinstance(register.get(field), str) or not register[field]:
            raise ValueError(f"standards.json {field} must be a nonempty string")
    standards = validate_standards(register.get("standards"))
    schema = strict_json(
        (root / "schema/source-0.1.schema.json").read_bytes(),
        "schema/source-0.1.schema.json",
    )
    if not isinstance(schema, dict) or not isinstance(schema.get("$id"), str):
        raise ValueError("source schema does not have a string $id")
    cap_table = capability_table(capabilities)
    std_table = standards_table(standards)
    readme = (root / "README.md").read_text(encoding="utf-8")
    disclaimer = (root / "DISCLAIMER.md").read_text(encoding="utf-8")
    require_boundary(readme)
    require_security_stewardship((root / "SECURITY.md").read_text(encoding="utf-8"))
    require_ai_disclosure(readme, disclaimer)
    deployable = [item for item in capabilities if item["level"] == 5]
    deployable_statement = (
        f"Level 5 capabilities in this assessment: {', '.join(str(item['id']) for item in deployable)}."
        if deployable
        else "No capability is Level 5 Deployable in this assessment."
    )

    context = f"""<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->
<!-- Generated by scripts/generate-evaluation-dossier.py; do not edit. -->

# SEAG compact AI evaluation context

Status: **alpha evaluation aid**, generated for SEAG `{version}`. This page is
an orientation and verification aid, not a release, certification, semantic
authority, or substitute for its cited sources. Record the checkout under
review with `git rev-parse HEAD`; the adjacent manifest binds the authoritative
input files by SHA-256.

## Identity and boundary

- Canonical repository: `https://gitlab.com/janipaijanen/seag`
- Source schema: `{schema['$id']}`
- SEAG captures and transforms project-owned semantic records. It does not own
  an adopter's ontology.
- {BOUNDARY}
- It is also not process/workflow modelling, an ontology reasoner, a truth
  oracle, an agent runtime, or a hosted collaboration service.
- Passing validation proves only the bounded structural and semantic checks
  implemented by that exact revision.
- Evidence control: {evidence_scope['control'].replace('-', ' ')}. Non-author
  in-project review is {evidence_scope['nonauthor_in_project_review']} with
  context `{evidence_scope['nonauthor_review_context']}`; external consumer or
  adopter attestation is {evidence_scope['external_consumer_or_adopter_attestation']}.
  Non-author in-project review alone is not independent external attestation.
- Stewardship: single-maintainer project in public review. There is no community
  programme, support commitment, review deadline, or production-readiness claim.
- Development transparency: SEAG is developed with AI assistance, while the
  human maintainer remains responsible for accepted changes and project claims.
  The tested local validation and transformation path does not require an AI
  service. See `DISCLAIMER.md` for cost, resource, environmental, and
  external-service limits.

## Evidence states and no-invention rule

{EVIDENCE_STATE_RULE}

## Reading aid

- **Adopt for evaluation:** only when text-first, provenance-preserving semantic
  records solve a demonstrated problem and the listed limitations are acceptable.
- **Wait for supported adoption:** {deployable_statement} For a bounded
  evaluation, instead require the documented level and evidence needed by the
  intended use. Wait when a necessary profile lacks tested evidence or the
  adopter cannot own semantic review and provenance.
- **Skip:** when the need is workflow execution, behavioural modelling, semantic
  truth determination, or an immediately supported hosted product.

These are maturity-linked questions, not SEAG recommendations.

## Capability snapshot

{cap_table}

Level 1 is {MATURITY_NAMES[1]}, 2 {MATURITY_NAMES[2]}, 3 {MATURITY_NAMES[3]},
4 {MATURITY_NAMES[4]}, and 5 {MATURITY_NAMES[5]}. Capability maturity is
separate from evidence status. SEAG's independent-project benefit is
{evidence_status['independent_project_benefit'].replace('-', ' ')} in `maturity.yaml`.

## Verify locally

Use Python 3.14.8 and uv 0.12.9, then run:

```sh
uv sync --locked --only-group conformance
uv run --locked --no-sync python scripts/generate-evaluation-dossier.py --check
uv run --locked --no-sync python scripts/check-conformance.py
uv run --locked --no-sync python -m unittest discover -s tests -v
git diff --check
```

The dossier `--check` command regenerates the outputs in memory and verifies
the committed Markdown and manifest bytes against every locally bound input.
The exact runtime pins are reproducibility inputs, not a compatibility
tolerance range.

Report the version, commit, files read, commands actually run, strengths,
source-cited gaps, proposals, and anything not verified. Use the
[full dossier](ai-evaluation-dossier.md) before making standards,
compatibility, security, licensing, or transformation claims.
"""

    dossier = f"""<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->
<!-- Generated by scripts/generate-evaluation-dossier.py; do not edit. -->

# SEAG AI evaluation dossier

## Evaluation brief

This is an **alpha evaluation aid** for SEAG `{version}`. It gives AI assistants
and human reviewers one bounded, source-traceable route through the project. It
does not replace the authoritative documents, certify SEAG, or convert roadmap
claims into shipped capabilities. Record `git rev-parse HEAD` in every review;
the machine-readable [dossier manifest](ai-evaluation-dossier.json) binds the
inputs used to generate this page by path and SHA-256.

Review posture: confirm identity first, cite exact source paths, distinguish
capability maturity from evidence status, reproduce only the checks you claim
to have run, disclose uncertainty, and treat generated representations as
potentially lossy.

## Identity check

| Field | Value |
|---|---|
| Canonical repository | `https://gitlab.com/janipaijanen/seag` |
| Version file | `{version}` |
| Source schema | `{schema['$id']}` |
| Standards register | `{register['seag_standards_register']}` / `{register['status']}` |
| Evidence control | {evidence_scope['control'].replace('-', ' ')} |
| Non-author in-project review | {evidence_scope['nonauthor_in_project_review']}; `{evidence_scope['nonauthor_review_context']}` |
| External consumer/adopter attestation | {evidence_scope['external_consumer_or_adopter_attestation']} |
| Stewardship | Single-maintainer; public review; no support commitment or review SLA |
| Development | AI-assisted; accepted changes remain under human-maintainer responsibility |
| Evaluation status | Alpha aid; not a release or certification |

{BOUNDARY}

Adopters own their concepts, ontologies, product decisions, access controls,
and review authority. SEAG does not judge ontology quality, model or execute
workflow behaviour, or claim interoperability beyond an exact tested profile.
Project-controlled evidence and non-author in-project review alone do not
become independent external attestation merely because they are reproducible.
SEAG is developed with AI assistance, but the tested local validation and
transformation path does not require an AI service. See `DISCLAIMER.md` for the
resource, cost, environmental, and external-service boundaries.

## Evidence states and no-invention rule

{EVIDENCE_STATE_RULE}

## Bounded reading tracks

### Compact orientation

Read [the compact AI context](ai-evaluation-context.md), `README.md`, and
`maturity.yaml`. This is sufficient only for deciding whether deeper evaluation
is warranted.

### Claim assessment

Read, in order:

1. `docs/charter.md` for purpose and permanent exclusions;
2. `docs/source-contract-0.1.md` and the source schema for the semantic contract;
3. `docs/maturity.md` and `maturity.yaml` for capability and evidence status;
4. `docs/conformance.md` and `standards.json` for standards claims;
5. `docs/compatibility.md` for compatibility vocabulary and limits;
6. `docs/installation-and-upgrade.md` for the currently supported operator path;
7. `SECURITY.md`, `docs/licensing.md`, and `CONTRIBUTING.md` for responsibility,
   rights, reporting, and review boundaries.

A full documentation-corpus appendix is deliberately deferred. This avoids
duplicating normative sources and presenting context volume as review quality.

## Adopt, wait, or skip reading aid

- Consider evaluation only if stable identity, provenance, semantic diff, and
  loss-aware transformations address a measured need.
- Wait for supported adoption: {deployable_statement} For bounded evaluation,
  require the documented capability level and evidence needed by the intended
  use. Wait when an exporter lacks needed consumer evidence or ownership of
  semantic decisions is unresolved.
- Skip when the need is behavioural process modelling, orchestration, automated
  truth determination, a complete ontology reasoner, or a supported hosted UI.

This is not an adoption recommendation. The current maturity and evidence rows
below govern; no aggregate project score is implied.

## Capability maturity

{cap_table}

The authoritative evidence locators and the independent-project evidence status
remain in `maturity.yaml`. A capability can be technically Level 4 while its
claimed benefit remains theoretical. A release does not promote every included
capability automatically.

## Standards and compatibility claims

{std_table}

Register inclusion alone is not conformance. Confirm the applicable class,
scope, pinned version, limitations, implementation, fixtures, and repeatable
evidence in `docs/conformance.md` and `standards.json`. In particular, bounded
CXL compatible-parser round-trip evidence is not CmapTools desktop compatibility,
and documented PROV/SKOS mappings are not RDF, OWL, JSON-LD, or PROV-O exporter
claims.

## Transformation honesty

For each glossary, CXL map, canonical rendering, semantic diff, or future
adapter, verify:

1. exact source release or commit and source-contract identity;
2. transformation implementation and version;
3. preserved identifiers and provenance;
4. omissions, approximations, fallback, and declared semantic loss;
5. deterministic fixtures and the exact consumer used for round-trip evidence;
6. whether the result is authoritative source, a generated view, or review evidence.

Opening an output successfully is not semantic equivalence. Matching labels do
not establish identical concepts.

## Verification checks

Use Python 3.14.8 and uv 0.12.9. Run only commands whose prerequisites you have
inspected, and report failures without weakening the checks:

```sh
uv sync --locked --only-group conformance
uv run --locked --no-sync python scripts/check-dependency-policy.py
uv lock --check
uv run --locked --no-sync reuse lint
uv run --locked --no-sync python scripts/check-spdx.py
uv run --locked --no-sync python scripts/check-dco.py
uv run --locked --no-sync python scripts/generate-evaluation-dossier.py --check
uv run --locked --no-sync python scripts/check-conformance.py
uv run --locked --no-sync check-jsonschema --check-metaschema schema/*.schema.json
uv run --locked --no-sync check-jsonschema --schemafile schema/source-0.1.schema.json fixtures/valid/manifest.json fixtures/valid/fragment.json fixtures/valid/variant.json
uv run --locked --no-sync python -m unittest discover -s tests -v
git diff --check
```

The dossier check proves deterministic agreement with the listed local inputs.
It does not independently authenticate the repository, commit, author, or
external sources.

## Security, licensing, and responsibility

Read `SECURITY.md` before publishing a vulnerability. Read `docs/licensing.md`
and `DISCLAIMER.md` before using external AI or substantial computing resources.
Read per-file SPDX declarations before redistributing content. A DCO sign-off is
provenance and rights certification, not copyright assignment. Generated
semantic views inherit relevant source licensing, access, privacy, and
classification restrictions; a public SEAG tool does not make adopter content
public.

## Adoption and pilot evidence

SEAG's problem framing is
{evidence_status['problem_framing'].replace('-', ' ')}, while benefit to
independent projects is
{evidence_status['independent_project_benefit'].replace('-', ' ')} according to
`maturity.yaml`. No adopter pilot result is embedded or claimed here. Do not
infer pilot status, semantic acceptance, stable support, or independent
validation from this dossier. A public evidence summary belongs here only
after classification, review, and an explicit publication decision.

## Required review output

Label the review as a critique, fit assessment, improvement backlog,
self-application, adoption mapping, or other. Include:

1. scope reviewed: version, commit, paths, and commands;
2. identity confirmation;
3. strengths, each with a source path;
4. risks, gaps, and inconsistencies, each with a source path;
5. proposals naming the affected file or contract;
6. capability level and evidence status kept separate;
7. uncertainty and material not independently verified.

Do not report generated wording as an independent source. Cite the authoritative
path named by this dossier and verify it directly.
"""

    context_bytes = context.encode("utf-8")
    dossier_bytes = dossier.encode("utf-8")
    word_count = len(re.findall(r"\S+", context))
    if len(context_bytes) > CONTEXT_MAX_BYTES or word_count > CONTEXT_MAX_WORDS:
        raise ValueError(
            f"compact context exceeds budget: {len(context_bytes)} bytes, {word_count} words"
        )
    sources = []
    for path in SOURCE_PATHS:
        data = (root / path).read_bytes()
        sources.append({"path": path.as_posix(), "sha256": sha256(data), "size": len(data)})
    manifest = {
        "schema": "seag/ai-evaluation-dossier/v1",
        "status": "alpha-evaluation-aid",
        "seag_version": version,
        "canonical_repository": "https://gitlab.com/janipaijanen/seag",
        "source_commit_instruction": "record git rev-parse HEAD in the evaluation receipt",
        "source_contract_schema": schema["$id"],
        "source_digest_algorithm": "sha256",
        "evaluation_evidence_scope": evidence_scope,
        "stewardship": {
            "maintainer_model": "single-maintainer",
            "status": "public-review",
            "support_commitment": "none",
        },
        "sources": sources,
        "outputs": [
            {"path": CONTEXT.as_posix(), "sha256": sha256(context_bytes), "size": len(context_bytes)},
            {"path": DOSSIER.as_posix(), "sha256": sha256(dossier_bytes), "size": len(dossier_bytes)},
        ],
        "compact_context_budget": {
            "encoding": "UTF-8",
            "maximum_bytes": CONTEXT_MAX_BYTES,
            "actual_bytes": len(context_bytes),
            "word_definition": "non-whitespace runs counted by Python regular expression \\S+",
            "maximum_words": CONTEXT_MAX_WORDS,
            "actual_words": word_count,
        },
        "verification_commands": [
            "python3 scripts/generate-evaluation-dossier.py --check",
            "python3 -m unittest discover -s tests -v",
        ],
        "limitations": [
            "The manifest binds local bytes but does not authenticate the Git repository or external sources.",
            "The dossier is an evaluation aid, not a certification, release, or semantic truth claim.",
            "The full documentation corpus and adopter pilot results are not embedded.",
        ],
    }
    manifest_bytes = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    return {CONTEXT: context_bytes, DOSSIER: dossier_bytes, MANIFEST: manifest_bytes}


def check(outputs: dict[Path, bytes], root: Path = ROOT) -> list[str]:
    errors = []
    for path, expected in outputs.items():
        target = root / path
        try:
            actual = target.read_bytes()
        except OSError as error:
            errors.append(f"{path}: cannot read generated output: {error}")
            continue
        if actual != expected:
            errors.append(f"{path}: stale; regenerate with scripts/generate-evaluation-dossier.py")
    return errors


def write(outputs: dict[Path, bytes], root: Path = ROOT) -> None:
    for path, data in outputs.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if committed outputs are stale")
    arguments = parser.parse_args(argv)
    try:
        outputs = render()
        if arguments.check:
            errors = check(outputs)
            if errors:
                print("\n".join(errors), file=sys.stderr)
                return 1
        else:
            write(outputs)
    except (KeyError, OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        print(f"evaluation dossier generation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
