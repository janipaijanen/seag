<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Disclaimer and resource-use notice

This notice provides development transparency and practical operating guidance.
It does not replace, amend, or add restrictions to SEAG's software and
documentation licences. The applicable licence texts remain authoritative for
warranty, liability, permissions, and conditions.

## AI-assisted development

SEAG is developed with AI assistance. AI systems have assisted with research,
planning, drafting, code, tests, and review. The human maintainer decides what
is accepted and remains responsible for the repository's project decisions and
published claims. Content-bearing contributions remain subject to human review
and DCO sign-off under [the contribution policy](CONTRIBUTING.md).

AI-generated or AI-reviewed material can be incomplete, incorrect, insecure,
biased, misleading, or incompatible with its sources. AI involvement does not
by itself establish authorship, provenance, rights, correctness, independent
review, external attestation, or semantic truth. Contributors remain
responsible for every representation made under their DCO sign-off, including
representations about agent-assisted material.

When AI agents perform non-author review inside the project, that is
**non-author in-project review**, not independent external attestation.

## AI is optional

The tested local validation and transformation path does not require an AI
service. An adopter may use that path with ordinary text editors, Git, and
local command-line tools.

External agents, model providers, hosted services, CI systems, and future
adapters are separate systems with their own behavior, terms, and trust
boundaries. Connecting one does not make it part of the SEAG core contract.

## Financial and computing resources

Running builds, tests, CI jobs, virtual machines, containers, databases, model
inference, or third-party services can consume CPU or GPU time, memory, storage,
network bandwidth, API tokens, service credits, or other metered resources. It
can create direct charges or indirect infrastructure costs. Prices, quotas, and
billing behavior are controlled by the relevant provider or operator, not by
SEAG.

Before running a workload, inspect the commands and provider terms, estimate
the intended scope, set appropriate budgets and quotas, monitor consumption,
and retain a way to stop the workload. SEAG makes no guarantee about the cost
of an adopter's environment or external services.

## Energy and environmental impact

Computing equipment and supporting infrastructure consume electricity and
other resources. Associated environmental effects, including greenhouse-gas
emissions, depend on workload, hardware, utilization, data-centre operation,
energy source, location, and provider practices. SEAG does not claim a measured
carbon footprint for itself or for an adopter's deployment.

Use the smallest workload that provides the required evidence. Avoid needless
repeated model calls, builds, retained artifacts, and always-on environments;
apply time, storage, concurrency, and resource limits where practical.

## Data and external-service responsibility

Do not submit credentials, confidential material, customer data, personal data,
or restricted semantic sources to an AI or hosted service unless you have the
authority to do so and have reviewed that service's privacy, retention,
training, security, residency, and deletion terms. A public SEAG tool does not
make private adopter content safe to disclose.

SEAG validates only the bounded declarations and transformations implemented by
the exact version being run. Users remain responsible for semantic decisions,
access control, backups, recovery, regulatory obligations, and determining
whether an output is suitable for its intended use.

## Applicable licences

Software, CI, and tests are provided under [Apache-2.0](LICENSE). Framework
documentation and semantic registers, including this notice, are provided under
[CC BY 4.0](LICENSE-DOCS). Consult those licence texts and the
[licensing policy](docs/licensing.md); this notice is informational and does not
create a separate licence, warranty, service level, or indemnity.
