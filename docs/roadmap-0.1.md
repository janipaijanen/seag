# SEAG 0.1 roadmap

## Increment 1: semantic contract

- Confirm the charter and terminology.
- Define stable identifier namespaces.
- Define concept, proposition, lifecycle-axis, rule, and trace records.
- Add small, invented, domain-neutral conformance fixtures.
- Record unresolved facts as unresolved rather than choosing defaults.

Exit evidence: specification review and fixture conformance review.

## Increment 2: validation

- Validate unique and resolvable identifiers.
- Validate allowed relation endpoint types and direction.
- Validate both-end cardinalities for named associations.
- Detect taxonomy cycles.
- Validate lifecycle, rule, and trace references.
- Verify that proposed and confirmed statements cannot be confused.

Exit evidence: focused automated tests and invalid fixture coverage.

## Increment 3: CmapTools exchange

- Generate a CXL representation from the authoritative source.
- Reopen the result in CmapTools or a compatible parser.
- Verify that concept identifiers, labels, linking phrases, and connections
  survive the round trip.
- Keep visual layout metadata out of the authoritative semantic source.

Exit evidence: pinned-tool round-trip record and retained fixture.

## Increment 4: optional integration profiles

- AGF 3.0: connect semantic decisions and evidence without duplicating them.
- Ponytail: require reduction work to preserve referenced semantic contracts.
- Caveman Mode: define compact status-message templates that retain IDs,
  decision status, and uncertainty.

Each profile must state its pinned target version, assumptions, supported
workflow, and verification limits. No profile is part of the SEAG core.

## Increment 5: publication preparation

- Complete licensing and SPDX labelling.
- Add contribution, security, release, and compatibility policies.
- Perform independent semantic, framework-boundary, licensing, and security reviews.
- Publish 0.1 only after the publication gate in the charter is satisfied.

