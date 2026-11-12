# Sonic Chaos — C1-R3 ROM Special Stage Camera Phase: Manager Review
**12 November 2026 · Manager-san #11 · ISOLATED CANONICAL CORRECTION PASS · PRODUCTION CLASSIC REPLACEMENT HOLD**

## Scope of manager review and provenance
Chief uploaded the complete Markdown technical report `C1_R3_SPECIAL_STAGE_CAMERA_FIDELITY_20261112.md`. Manager has read that report's actual text in this conversation, but **has not independently opened private ROM traces, source ZIP, package receipt/JSON, H: recovery, compiled Windows trial, or machine-readable 382-record coverage /16-finding databases**. All numerical runtime results below are **Designer-reported**, not re-executed by Manager.

- Exact isolated C1-R3 **source commit `b667cc5cebcd3c3e047d9f527cc78b76e1e027f0`**, parent C1-R2 `316125f6f280f24a7a8af507155d9dfe86954cea`; branch `classic/c1-r3-ss-camera-phase-20261112`. Same isolated `management-audits/c1-20261112/project/SonicChaos.yyp`. Exact tree/ZIP hashes and H: recovery in private R3 receipt, not reproduced here.
- Private full report: `E:\AI\Codex\Sonic Chaos\management-audits\c1-20261112\r3\delivery\C1_R3_SPECIAL_STAGE_CAMERA_FIDELITY_20261112.md`
- Private receipt: `E:\AI\Codex\Sonic Chaos\management-audits\c1-20261112\r3\delivery\SonicChaos_20261112_C1_R3_CLASSIC_FIDELITY_RECEIPT.json`
- Trial binary and source are in C1-R3 isolated delivery directory and independent H: recovery, **not approved production release files**. H: Git fsck/bare recovery, full source ZIP and four runtime +18 original sprite PNG dependencies reported verified.
- Protected original Classic tag `classic-core-20261105`, R1/R2 trials, S4–S6 packages, S7 evidence-only no-change disposition, S6 protected Wide348×196 and settings/save data remain untouched. **No merge, push, tag, release or Chief physical user test.**

## Original ROM camera phase identified
Original Master System Europe v1.2 ROM SHA256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`; controlled actual original hundredth-ring ($3138, ring BCD99) stage-entry path, not fabricated coordinates. Original execution order: **camera $4C90 and follow/limits $4CB0/$4CF7 before player engine $64FA → objects $5DD1 → VBlank camera commit $0570/$057C**. Camera work pending D284/D286, committed D174/D176, working leads D28A/D28D. Original first working leads X104/Y120, stand callback writes target96 *after* first camera preparation. GameMaker's old SS End Step calculated follow from new player/lead, which causes one-update-early slewing and persisted ±1px differences; it had been comparing pending against the wrong original boundary when using pre-limits $4CB0.

**Two minimal Classic-only source owners** modified:
- `scripts/SCR_chaos_ss1/SCR_chaos_ss1.gml` initializes persistent `classic_camera`, prepares original-camera follow from **prior** core/lead before player, then commits prepared x/y after objects; existing Enhanced post-player helper and 112/107 lead adapters unchanged.
- `scripts/SCR_chaos_adapter/SCR_chaos_adapter.gml` calls preparation immediately after external registration import and before player input/core tick, guarding non-Classic/ordinary paths. R2 `objects/OBJ_chaos_zone/Create_0.gml` original SS2–5 Y registration fix preserved; no stage-specific offsets, artificial delay, gameplay physics, art, PSG or QoL edits.

## Native / original verified windows
Original per-stage fresh-entry/down sample (first R2 mismatch → original work/expected R3 commit):
- SS1 at player update1: X0/Y14 vs R2 Y15.
- SS2 at update43: X0/Y1727 vs R2 Y1728.
- SS3 at update1: X31/Y518 vs R2 Y519.
- SS4 at update43: X30/Y255 vs R2 Y254.
- SS5 at update45: X31/Y769 vs R2 Y768.

**Do not confuse pending and committed original views.** At SS1 first boundary original committed view is Y15 but pending work is Y14; SS3 first committed Y526 vs pending Y518. R3 compares exactly named phase/registers rather than forcing display to match pending. SS4 original look-down after40 neutral updates slews working lead as ROM and stays under exclusive Y272 limit.

- **500/500 post-limit original camera-model matches**, and five stage streams×100 player entries: 500/500 pending working leads, prior committed view, and End Step committed view all exact. 500 source integration cases /1,500 assertions PASS.
- **Equivalent settled SS5 clock**: 90 neutral settle entries then original held/pressed sequence; all **145/145 positions, prior committed camera and prepared/committed camera phases** exact. R2 player positions145/145 but cameras78/145. This resolves the demonstrated early-commit subcase, not every possible SS5 route.
- Existing **`verify_ss5_play.js` RAW still FAILS** after R3 (now reports first mismatch Y765 vs768 at update6) because its oracle is90 frames settled while native starts fresh and it compares post-update view to *next* ROM row. **No old tests/oracles edited or reclassified PASS**. New exact equivalent-state check is independent; future harness correction needs explicit timing contract, not just making red green.
- **Historical SS4 raw FAIL** from width348 at update1848 occurs with default Classic mode while expecting Enhanced right limits. Separate explicit-mode replay `check_ss4_modes.js`: **22,742 assertions PASS**, 1,879 original-route player states, Rocket/monitors/springs/crumble/timeout/failure; old raw FAIL honestly retained.
- R2 Special Stage raw original Y anchors **SS1=118, SS2=1838, SS3=622, SS4=366, SS5=878** preserved and checked for Sonic/Tails (Tails SS only debug stress, not retail natural entry).
- **Enhanced exact protected S6** in same bounded matrices: **10,542 state samples** (4,554 room +5,988 boss/ring) and **102 image matches** (46 room +12 boss +44 Options/frontend). Inherited original references are preserved; these are not whole-game Enhanced certification. **Ordinary Classic** 3,564 state samples exact to R2. 23 rooms×2 characters×3 scales = **138 native256×192 pictures with exact 1×/2×/3× nearest output**. C1 contract1,095 +R2 entry60 +R3 phase1,500 assertions PASS. No new physical pad test, natural full campaign, PSG/PCM/VBlank/PAL hardware-cycle certification claimed.

## What remains OPEN under ROM-wide mandate
- **Original loader/player initialization**: original state0/next0 dispatcher vs GameMaker state1 wrapper, and all unverified transition/terminal/contact/animation/clock paths. R3 fixes only original camera dependency/update phase.
- **Shared first16 object slots with pending $FE/$FF**: true ROM owner occupancy and reusable slot timing vs independent GM lost-ring list. R2 controlled GPZ boss peak6 and sampled seven-ring hurts: no naturally reachable shortage yet established; **NO broad slot rewrite permitted** without ROM/GM trace.
- **Original attract demos:** three actual THZ/Sonic, GPZ/Tails, SEZ/Sonic replay traces recorded; faithful loader/input/replay/dispatch port still missing.
- **VDP output fidelity:** original R0=$26 bit5 masks left8 columns to **scene-dependent backdrop colour**, not a universal black strip. Current Classic does not reproduce that rendering policy; accurate palette ownership/scene transitions/sprite scanline limits and original timing lack proof.
- Unvisited 18-act/5-SS original natural route states, PAL/NTSC original frame cadence, original PSG/SFX requests, rare gameplay/pause/results/ending conditions remain UNVERIFIED, not assumed correct.
- Private 382 coverage records/16 classified findings retained with R3 camera subcase resolved; do not count 382 records as 382 validated campaigns.

## Manager verdict and next gate
**C1-R3 evidence-backed Classic-only canonical camera correction PASS. Classic production replacement and C1→S6 integration HOLD.** C1 source remains strictly separate from frozen S6 Wide Enhanced and historical Classic tag. Both S5–S7 combined Chief Windows user gate and future Enhanced gameplay QoL remain separate. No automatic merge, push, retag, release, or forced Chief full campaign.

**Recommended next isolated C1-R4**: **ROM VDP visible-pixel policy / palette-aware left8 mask + sprite scanline limits fidelity**, beginning with exact original R0/palette/sprite evidence and only shipping proof-backed Classic-only presentation changes if native 256×192 capture and genuine-scene phases match; source-style render and palette limits must be respected. [C1-R4 binding directive](C1_R4_ORIGINAL_VDP_RENDER_POLICY_SPRINT_20261112.md). The demo-replay and shared object-slot ownership remain independent later gates, not R4 implementation. Further full-ROM gameplay/parity coverage still required before declaring C1 original-accurate.
