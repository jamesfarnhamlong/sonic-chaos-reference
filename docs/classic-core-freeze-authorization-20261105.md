# Sonic Chaos Classic — Chief freeze authorization
**Authorized by Chief: 5 November 2026 · Manager-san #10**

## Decision
Chief explicitly accepted the Manager's final-readiness GO recommendation and **authorized the private Classic core freeze**. This is authorization to carry out the archival procedure, not a claim that the tag/archive has already been created and verified.

**Exact frozen core candidate:** private `jamesfarnhamlong/SonicChaos_POC` branch `production/corrective-d-20261105`, commit `3a58912659b48573ac7f2c5c96a02a2211d5e4da` (direct C parent `337480a054999545535192a63b86dba9a9de2aea`). Keep the exact accepted production tree untouched. Authorized private annotated tag name: `classic-core-20261105`; verify that it resolves (by peeling tag object if annotated) to the exact D SHA. The tag currently does not exist, so **execution is pending**.

**Verified publication before authorization:** remote production branch matches D; `main` remains `03a6e7dfcaed519993a9422cc35b60753d5d3dbd`. Designer's documentation-only final-readiness branch `docs/final-classic-readiness-20261105` / reported local SHA `fdb7b3ae468753edbf69c0ea2ae469e4c40c39dd` is not yet on the remote; publish that *documentation only* before final freeze archival closeout, without changing D.

## Core maintenance policy after freeze
Chief: **'Any changes we make going forward will be wrapped around this core.'** The Classic game logic/assets/source at D remain the immutable reference baseline. New graphical enhancements, presentation options, portability, conveniences and other adapters must be developed in separate branches/layers outside the frozen core contract where feasible, with original-game fidelity preserved.

**Only presently anticipated future core-adjacent maintenance:**
1. Removal or production hiding of the *developer* Level Select route when appropriate for a non-debug presentation. Its current function in the accepted D source must remain available in the frozen artifact; do not change it as part of freeze. Chief must approve any later removal/gating.
2. Disallowing Pause at specific forbidden gameplay/transition intervals. The exact intervals and original-ROM/UX rules are not yet specified or authorized for implementation. Document and scope them separately; do not change current Pause behaviour during freeze.

Any rare necessary future core change requires an individually scoped reason, evidence/validation and Chief acceptance on a new branch/checkpoint. **Never rewrite, retag, force-update or silently mutate this frozen core revision.** Prior freeze tag remains permanent; a future accepted maintenance revision gets its own independently named successor marker.

## Accepted provenance and explicitly retained exceptions
- `SonicChaos_Windows_20261105_CORRECTIVE_D_PRIVATE.zip`: SHA-256 `1fa9c7394e5b87faa65574efbb416456112d7f0a7cf1dbef0387b501b5677f95`.
- `SonicChaos_Production_20261105_CORRECTIVE_D_SOURCE_PRIVATE.zip`: SHA-256 `e56a8e25778c5502551ad438a05d1e32a8747e846b625f70d5c84f088e0be5f2`.
- H: incremental `production-corrective-d-20261105.bundle`: SHA-256 `e6c7d796cb76e76f6995dcaf8ba4d62fadd0e23f968723ea9a35b4821c584571`; its C ancestor dependency remains preserved.
- D source ZIP contains a **stale internal B `SOURCE_MANIFEST.json`**; the verified external receipt, D archive checksum and immutable D Git SHA control provenance. Do not repackage the accepted archive silently.
- Remaining accepted fidelity/verification limitations: reachable original-ROM Tails state `$20`/selected frame `$5E` corruption hazard deliberately handled through explicit no-draw/safe-progression exception; one active THZ enemy Draw native-counter gap; 20 dormant/legacy Draw paths; five inherited raw verifier failures; D phase/fixture differences; other documented uncommon path/coverage limits. No demonstrated crash or progression blocker. These are known exceptions, not blanket claims of universal ROM parity.

## Authorized archival work (not yet executed)
1. Publish and verify Designer's documentation-only readiness branch and commit, confirming no runtime changes.
2. Create and push a **private annotated tag `classic-core-20261105`** that peels to accepted D exactly; do not tag docs HEAD or `main`.
3. Create a documentation-only freeze ledger/manifest pointing to this authorization, Chief C/D acceptance, readiness report, accepted SHA, package hashes, stale-manifest caveat and H: recovery prerequisites.
4. Verify remote tag SHA, immutable production branch, unchanged main, local working tree, and the named recovery artifacts. Preserve all B/C/D receipts. No rebuild, merge, runtime modification or public release.
5. Manager records completed freeze **only after** receiving and checking the final archival receipt.

**Status as of this authorization: CHIEF FREEZE APPROVED · ARCHIVAL EXECUTION PENDING · no public release.**
