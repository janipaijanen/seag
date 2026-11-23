<!-- SPDX-FileCopyrightText: Copyright (C) 2026 Jani Päijänen -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Historical DCO attestation

## Purpose and boundary

SEAG published eleven commits after adopting an every-commit Developer
Certificate of Origin requirement but before enforcing the required
`Signed-off-by` trailer. Their commit messages do not satisfy that mechanical
requirement. Rewriting them would change already published release tags,
source identities, review evidence, checksums, and downstream mirrors.

This record preserves those commit objects and makes the historical deviation
explicit. It does not add trailers to them, alter their authorship, or claim
that the repository complied at the time.

## Maintainer certification

On 2026-11-22, Jani Päijänen certified that the contribution represented by
each commit listed below satisfies Developer Certificate of Origin 1.1. The
`Signed-off-by` trailer on the commit that first adds this record is the
maintainer's certification of this statement and list.

| Commit | Subject |
| --- | --- |
| `2693854aafd78854ffa8c9c9a0e398514e1ae88b` | Add public contribution security and compatibility policies |
| `838bd29665c3159cafdf84f1adcf7446591417d2` | Allow truthful contributor SPDX ownership |
| `caa7becdaca8471a942c46c62c043c3ef9913afa` | Prepare 0.1.0-rc.2 public review release |
| `18f63cc1bea9fe292da84a501f2d0c9c6f0f39b0` | Harden source contract validation parity |
| `79a7eacf17b4ff15e5ba03487b73ce36473e8d10` | Guard actor-collapse diagnostics against missing identities |
| `c781651a38a4c46cba3c46749e96ff9a940a6a52` | Add concept map and ontology introduction |
| `3e1c7cdd3aaa5acafd2fffec1bf8fa6e0c6cb0e9` | Use state machine in minimal semantic record |
| `1ac7abb153d969751f675eb3327413243be397e6` | Explain state machines to new SEAG readers |
| `9f4ee88f0e14c444ef57e1fdecdeb431d711bc3a` | Version singular-label draft contract boundary |
| `20c555915d7020fa7514b69c4668e09c62c7edc8` | Correct source migration digest order |
| `a2fee6e32b1bdcbcb78bb36791ce3910ae0d1d29` | Prepare 0.1.0-rc.3 public review release |

## Prospective rule

Every content-bearing commit after
`a2fee6e32b1bdcbcb78bb36791ce3910ae0d1d29` must contain at least one
syntactically valid `Signed-off-by` trailer. An unsigned merge is accepted only
when its tree exactly equals one parent tree, proving that the merge commit
itself adds no content beyond an already-checked history. CI and the publication
gate fail closed when the baseline is unavailable, the target is not its
descendant, or a later content-bearing commit lacks the trailer.

This transition is specific to the exact commits above. It is not a general
waiver and does not change the unmodified DCO 1.1 terms.
