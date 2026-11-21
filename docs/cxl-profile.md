<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# CmapTools CXL export profile 0.1

SEAG 0.1 emits the public IHMC CXL structure documented at
<https://cmap.ihmc.us/xml/cxl.html>. The evidence pins the retrieved
`cmap.xsd` bytes to SHA-256
`aa8ffda7d51ce4864e76186a349240cb6f01e086fab9cbc34e9c816bd778802a`
and the official `PlantsSimple.cxl` example to SHA-256
`935b98a0804d3ae11dbc602e37291942ac945367cf04eb87aad27d5d526de860`.

```sh
python3 -m seag.cxl source/manifest.json \
  --generated-at 2026-11-22T00:00:00Z \
  --output concept-map.cxl --verify
```

Named records become CXL concepts using their expanded SEAG identifiers.
Propositions become linking phrases; controlled predicates use their predicate
text and named associations use their bounded static name. Each proposition is
represented by source-to-link and link-to-target connections. Ordering and XML
serialization are deterministic.

The compatible-parser round trip verifies identifiers, labels, linking
phrases, and directed connections. It does not claim execution in the
CmapTools desktop application. The profile is intentionally lossy: definitions,
status, implementation alignment, cardinality, confirmation metadata, and
layout are not encoded in CXL. The required sidecar declares those omissions,
retains every source record's provenance, and binds source and output by
SHA-256. The SEAG JSON source remains authoritative.
