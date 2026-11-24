<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Agent instructions

This file routes repository work. It does not define SEAG semantics, agent
roles, project status, or release authority. Follow the normative documents it
links instead of copying their content into prompts or generated files.

## Repository boundaries

- SEAG captures semantic records and transformations; it is not a process,
  workflow, or agent-orchestration framework. See `docs/charter.md`.
- Treat the roles in `docs/roles.md` as responsibility contracts. Do not infer
  that a role is an autonomous agent or that an agent has approval authority.
- Every recorded concept has `grammatical_number: "singular"`. Do not weaken,
  pluralize, or silently repair this requirement.
- Preserve provenance, uncertainty, semantic loss, compatibility evidence, and
  human confirmation boundaries. Ambiguous or incompatible input fails closed.
- Use invented, domain-neutral fixtures. Do not add private product ontologies,
  customer content, credentials, confidential data, or unnecessary personal
  data.
- Do not bypass publication, DCO, licensing, security, compatibility, or
  independent-review gates. Candidate artifacts are not releases.

## Make a change

- Read `CONTRIBUTING.md` and the documentation governing the affected surface.
- Follow the pinned Ponytail discipline in `docs/semantic-minimality.md`: inspect
  affected callers and representations, reuse an existing path, and implement
  the smallest complete change.
- Update tests and documentation with the implementation. Preserve per-file
  SPDX notices and sign content-bearing commits with `git commit --signoff`.
- Treat schemas, validators, fixtures, transformations, compatibility claims,
  and release tooling as one contract. Do not change only one representation.
- Record durable semantic decisions in the appropriate normative document;
  do not use this file as a decision log or status tracker.

## Validate

Use Python 3.14.8 and uv 0.12.9 exactly. Run from the repository root:

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

Do not regenerate `uv.lock`, update dependencies, publish artifacts, create a
tag, or assert a release gate merely to make validation pass. Dependency and
publication changes require their documented review and evidence.

## Find authoritative guidance

- `README.md`: supported surface and navigation
- `docs/charter.md`: scope and non-goals
- `docs/roles.md`: responsibility and separation contracts
- `docs/compatibility.md`: compatibility and migration contract
- `docs/release-policy.md`: versioning and publication gates
- `SECURITY.md`: private reporting and security scope
- `CONTRIBUTING.md`: rights, provenance, validation, and review requirements
