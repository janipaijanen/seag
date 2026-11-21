<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Glossary extraction profile

`python3 -m seag.glossary` extracts named semantic records from a validated
SEAG bundle. It never invents translations or silently falls back to another
language. Version 0.1 requires an exact fragment-language match and emits
concepts, lifecycle-state names, rule references, and external references;
propositions remain graph relations rather than glossary entries.

```sh
python3 -m seag.glossary source/manifest.json \
  --language en \
  --generated-at 2026-11-22T00:00:00Z \
  --output glossary-en.json
```

The JSON envelope retains expanded and local identity, kind, label,
definition, language, semantic status, implementation alignment, confirmation,
replacement or deprecation rationale, grammatical number, licence, and the
complete source provenance object. Its adjacent provenance sidecar records
the generator, source manifest digest, output digest, language request,
selection result, fallback policy, timestamp, and entry count. The manifest
digest commits to the fragment digests in its inventory.

For reproducible output, provide `--generated-at` or `SOURCE_DATE_EPOCH`.
The tool fails if neither is present. Invalid bundles,
unsupported source-contract versions, and missing exact-language content fail
without producing a successful result.

The profile does not yet select translated labels inside one record because
the bounded 0.1 source contract does not define that structure. A future
multilingual contract change requires versioned migration and new fallback
evidence; BCP 47 handling remains governed by the language-tag policy.
