<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Security policy

## Support status

SEAG is a single-maintainer project in public review. No version is currently a
stable, supported, or production-ready release. Security reports are evaluated
against the latest public-review release and current `main` on a best-effort
basis. There is no response or remediation service-level agreement.

## Report a vulnerability privately

Do not disclose a suspected unpatched vulnerability in a public issue, merge
request, discussion, or social channel.

Use a
[GitLab confidential issue](https://gitlab.com/janipaijanen/seag/-/issues/new):

1. start a new issue;
2. select **This issue is confidential** before submitting; and
3. verify that GitLab shows the issue as confidential before adding sensitive
   details.

If you cannot create a confidential issue, open a public issue containing only
a request for a private security contact. Do not include vulnerability details.
This repository does not publish an unmonitored placeholder security address.

## Include in the report

Provide only information you are authorized to disclose:

- affected tag, commit, component, and configuration;
- reproduction steps and required preconditions;
- expected security impact and affected trust boundary;
- a minimal proof of concept, if safe;
- suggested mitigation, if known; and
- whether anyone else has received or published the report.

Do not include real credentials, unnecessary personal data, customer data, or
third-party confidential material.

## Scope

Relevant reports include validator input handling, bundle integrity and
reproducibility, provenance substitution, unsafe file or path handling,
dependency and CI supply-chain risks, and bypass of a release or publication
gate.

Semantic disagreements, ordinary correctness bugs without a security impact,
unsupported production deployments, social engineering, and testing that
requires unauthorized access or harms shared infrastructure are out of scope.

## Handling and disclosure

The maintainer will acknowledge, assess, and communicate about credible reports
as capacity permits. Confirmed issues may be fixed, documented, or rejected
with a rationale. Disclosure timing should be coordinated so users can evaluate
available mitigation. Reporter credit is offered when requested and legally
possible.

This policy does not authorize access to systems or data, destructive testing,
privacy violations, service disruption, or testing of third-party
infrastructure. It does not promise immunity or bind third parties. A formal
safe-harbor policy may be adopted later only from a reviewed legal template.
