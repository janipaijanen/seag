<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Contributing to SEAG

## Project status

SEAG is currently a single-maintainer project in public review. Contributions
are welcome as proposals, but submission does not create a right to acceptance,
a response deadline, support, commit access, or continued inclusion. The
maintainer makes final scope, roadmap, governance, repository, and release
decisions.

Acceptance does not make a contributor a project representative and grants no
authority over the SEAG name, releases, governance, or other contributions.

## Right and responsibility to contribute

Only submit material that you have the legal right and authority to contribute.
Obtain any required employer, client, co-author, or other rights-holder approval
before submission.

Every commit must certify the unmodified
[Developer Certificate of Origin 1.1](https://developercertificate.org/) with:

```text
Signed-off-by: Legal Name <email@example.com>
```

Create this trailer with `git commit --signoff`. The sign-off certifies the
DCO statements, including your right to submit the work and your understanding
that the contribution, sign-off, and associated personal information are public
and retained. A sign-off is a provenance and authority certification; it is not
a copyright assignment.

The contributor is responsible for the accuracy of these certifications and
for reviewing everything submitted under their sign-off, including
agent-assisted or generated material. This policy does not impose unlimited
personal liability or an indemnity.

## Contribution licence and ownership

Contributors retain copyright in their contributions. By intentionally
submitting a contribution for inclusion in SEAG, you license it under the
licence identified for the affected artifact:

- Apache-2.0 for software, CI configuration, executable tooling, and tests; or
- CC BY 4.0 for framework documentation and semantic registers.

For Apache-2.0 material, the copyright and patent grants and the contribution
terms of that licence apply. For CC BY 4.0 material, you grant the licensed
rights needed to reproduce, adapt, publish, and distribute the contribution as
part of SEAG. These are non-exclusive licence grants, not a transfer of
ownership to Jani Päijänen or to an unincorporated “SEAG project.”

SEAG does not currently require a contributor licence agreement or copyright
assignment. Any future assignment, additional patent grant, or relicensing
authority would require separate, explicit terms reviewed for the applicable
jurisdiction; it will not be inferred from a merge request.

## Required representations

By signing off a contribution, you also represent to the best of your knowledge
that:

- its authorship, sources, citations, provenance, and modification history are
  disclosed accurately;
- third-party material is identified with its source, licence, attribution, and
  compatibility basis;
- it contains no confidential information, credentials, unlawfully obtained
  material, unnecessary personal data, or material you lack authority to
  publish;
- agent-assisted content has been reviewed by you and you can make the same
  rights and provenance representations for it;
- tests, evidence, compatibility statements, and documentation are not
  knowingly false or misleading; and
- any suspected rights, licensing, security, or provenance uncertainty is
  disclosed before acceptance.

The maintainer may reject or remove material whose authority, provenance,
licensing, or project fit cannot be established.

## Contribution requirements

Keep proposals focused and reviewable. A contribution should:

- include tests and documentation appropriate to its risk;
- preserve the SEAG framework/content boundary and use invented,
  domain-neutral fixtures;
- contain no private Rediflow ontology or product content;
- preserve provenance, uncertainty, semantic loss, and source authority;
- avoid process- or workflow-modelling behavior;
- disclose incompatible contract or validator changes;
- use the repository's per-file SPDX policy; and
- pass the complete validation suite.

Run:

```sh
python3 scripts/check-spdx.py
python3 -m unittest discover -s tests -v
git diff --check
```

External changes should normally arrive through a merge request. Independent
review is required where SEAG's release or conformance policy calls for it; the
maintainer's acceptance alone does not manufacture independence.

## Copyright notices

Do not remove or replace valid third-party copyright or attribution notices.
Add an accurate `SPDX-FileCopyrightText` line when a separate notice is
appropriate. Git history and sign-offs supplement, but do not falsify or
silently transfer, copyright ownership.
