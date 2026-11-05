# Sonic Chaos — Corrective C/D Chief Acceptance
**5 November 2026 · Manager-san #10**

## Chief verdict: FULL PASS (scoped)
- **A — Sonic AQZ1 hidden 1-UP passage:** PASS. The previous incorrect leftward return transport is resolved in normal play.
- **B — Tails passage and Pause Level Select character choice:** PASS. Pause → Level Select → Zone/Act → Sonic/Tails → Start accepted; defaults to session character.
- **C — Ring-sparkle presentation:** PASS. Chief noticed no visible defect; do not mistake this for a claim the subtle difference is obvious.

## Accepted source and evidence boundary
- **Chief-accepted local private source:** Corrective D 3a58912659b48573ac7f2c5c96a02a2211d5e4da, parent Corrective C 337480a054999545535192a63b86dba9a9de2aea.
- **Private Windows candidate:** SonicChaos_Windows_20261105_CORRECTIVE_D_PRIVATE.zip.
- **Private source/receipt:** SonicChaos_Production_20261105_CORRECTIVE_D_SOURCE_PRIVATE.zip; SonicChaos_20261105_CORRECTIVE_D_RECEIPT.json; SonicChaos_20261105_CORRECTIVE_D_SHA256.txt. Designer reports H: independent recovery and clean local worktree; public reference GitHub does not host these private binaries, and the local D commit is not independently verified on GitHub. No main merge or publication.
- **C root cause:** Missing authenticated Sonic frames $19..$1B returned sprite -1 at AQZ state $34; C also corrected stale draw-only facing cache and registered ring sparkle Draw.
- **D root cause:** Original animation script command FF02 conditionally reverses X velocity according to player facing. C's literal interpretation incorrectly forced leftward return. D restores original instruction semantics and existing character-selection presentation.
- **Designer verification:** C sampled 10,381,631 sprite calls with zero unexpected invalid resources, 52 of 81 registered Draw files in principal matrices; D tested both characters and widths in original-ROM controlled comparison and compiled Windows passage/Level Select cases. These are scoped results, not universal original-game parity.
- D retains reward-phase/fixture differences and five inherited raw verifier failures. The Chief's two prior full campaigns were on an earlier baseline, not D.

## Production source publication — independently confirmed

**Production Git publication independently verified 5 Nov:** the private `jamesfarnhamlong/SonicChaos_POC` remote branch [`production/corrective-d-20261105`](https://github.com/jamesfarnhamlong/SonicChaos_POC/tree/production/corrective-d-20261105) points exactly to Chief-accepted D `3a58912659b48573ac7f2c5c96a02a2211d5e4da`. Remote C `337480a054999545535192a63b86dba9a9de2aea` is its one-commit direct ancestor (compare API: 1 ahead, 0 behind). The separate `docs/corrective-cd-acceptance-20261105` branch contains `docs/production/CHIEF_ACCEPTANCE.md` without changing D's production tree. `main` remains at `03a6e7dfcaed519993a9422cc35b60753d5d3dbd`. The Designer reports 0 ahead/behind local sync, clean worktree, exact source/package match and clean outgoing restricted-payload audit; remote SHA and public/private repository metadata were independently checked through GitHub. **No merge, tag, binary publication or private Classic freeze.**

**Next evidence-only gate:** use the remote C `docs/production/corrective-c-verification.json` `unexecuted_registered_draw_events` array (29 exact paths), `verification/corrective-c/coverage-matrix.csv`, and local source/original-ROM records to classify unexercised paths. This includes menu/choice/Pause paths not reached by the C *principal* matrix but sometimes covered by independent checks, so do not equate the list with 29 active bugs. Separately disposition Tails state `$20` / frame `$5E` reachability and exception. No runtime edits, builds or Chief tests without evidence of a real release blocker.

## Remaining before any private Classic freeze
1. Classify 29 unexecuted registered Draw paths from C's existing coverage matrices: natural production, rare active, or dormant/optional. No new mass audit or build without an evidenced risk.
2. Disposition inherited Tails state $20 / selected frame $5E exception: actual original mapping, source reachability, current guard and release risk. Do not invent frame art or suppress legitimate draw paths.
3. Establish exact D source and package hashes, independent recovery and explicit Chief private freeze approval. No automatic POC main merge, external release or enhancement implementation.

**Current management status: C/D CHIEF ACCEPTED; Classic base NOT YET FROZEN. Next activity is evidence-only final-gate review, not another Chief campaign.**
