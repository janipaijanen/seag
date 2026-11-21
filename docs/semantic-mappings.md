<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# PROV and SKOS mapping profile

These are correspondence mappings, not claims that SEAG storage is RDF,
PROV-O, or SKOS. SEAG identity, evidence status, cardinality, review, and
compatibility rules remain authoritative.

## W3C PROV

| SEAG construct | PROV correspondence | Qualification |
| --- | --- | --- |
| Source manifest, fragment, source record, generated output | `prov:Entity` | Preserve the SEAG identifier and byte digest |
| Extraction or export | `prov:Activity` | Bind generator version, start/result timestamp, input and output digests |
| Proposer, reviewer, confirmer, or software generator | `prov:Agent` | A textual actor is not authenticated merely by mapping it |
| Output derived from source | `prov:wasDerivedFrom` | The transformation sidecar supplies the qualified activity evidence |
| Activity used source | `prov:used` | Reference the exact manifest digest and bundle identity |
| Activity generated output | `prov:wasGeneratedBy` | Reference the exact output digest |
| Responsible actor association | `prov:wasAssociatedWith` | Preserve SEAG role and role-collapse disclosures separately |

## W3C SKOS

| SEAG construct | SKOS correspondence | Loss or constraint |
| --- | --- | --- |
| Concept record | `skos:Concept` | SEAG additionally requires singular preferred labels and provenance |
| Authoritative label | `skos:prefLabel` | Language comes from the containing fragment |
| Definition | `skos:definition` | Status and verification remain SEAG metadata |
| `is a kind of` | `skos:broader` from source to target | Only for the bounded taxonomy predicate |
| Related non-taxonomic concept | `skos:related` when explicitly profiled | Never infer from every SEAG proposition |
| Bundle or governed vocabulary | `skos:ConceptScheme` candidate | Bundle identity is not automatically a published SKOS scheme |

Named associations, both-end cardinality, lifecycle states, rule references,
confirmation records, and implementation alignment have no lossless core-SKOS
mapping. An exporter must retain them in a sidecar, use a separately versioned
extension, or declare them omitted. No SKOS serializer is claimed in 0.1.
