# Sonic Chaos — E0-R1 Chief Acceptance
**5 November 2026 · Manager-san #10 · E0 CLOSED — CHIEF ACCEPTED**

## Owner acceptance
Chief responded **'yes thats fine'** to Manager's E0-R1 focused acceptance request, following the revised private candidate and explicit five-point checklist. Manager treats this as **full scoped E0-R1 Chief acceptance, without further UI notes**. This closes E0 as a unified Classic/Enhanced *frontend*, not as proof of all possible gameplay paths or acceptance of any subsequent enhancement.

**Chief-approved behavior:** a roughly two-second silent static inherited OpenSonicSMS blue/white SEGA splash (PC-only addition, not retail ROM); a **two-entry** Classic/Enhanced picker with Classic selected on new launch; Classic enters the original Sonic Chaos cinematic directly; Enhanced enters a single visible `ENHANCED OPTIONS` screen showing `No additional features installed` until actual features exist, `START GAME` as the bottommost selectable action, and Escape/pad B Back. Future actual enhancements are clearly listed as ON/OFF choices where applicable. No developer feature-key switches or parallel gameplay builds.

## Accepted exact private source
- Repository: `jamesfarnhamlong/SonicChaos_POC` (private).
- Branch: `enhancement/e0-r1-ui-20261105`.
- **Chief-accepted E0-R1 commit:** `deccefc0acd822f74b6b26895ec278cdf67a7cee` (independently verified remote branch tip).
- Direct E0 parent: `69450848b1e06fcef7de63f19ae238ff346e479a`; compare is exactly one commit ahead, zero behind.
- Accepted candidate: `SonicChaos_Windows_20261105_E0_R1_PRIVATE.zip`, and source `SonicChaos_Production_20261105_E0_R1_SOURCE_PRIVATE.zip`; exact SHA-256 hashes and H: copies are documented in Designer's private `SonicChaos_20261105_E0_R1_RECEIPT.json`. **Hashes have not been reproduced by Manager because the private receipt/archives are not attached here; don't invent numeric hashes.**
- Preserved first E0 candidate remains historical and must not be replaced.

## Frozen original and scope
- Original Classic tag **remains immutable**: annotated `classic-core-20261105` tag object `87f13ef24877519c820d4d2612b58279a43578e6` → source `3a58912659b48573ac7f2c5c96a02a2211d5e4da`.
- Frozen production branch remains on D, and private game `main` remains `03a6e7dfcaed519993a9422cc35b60753d5d3dbd`.
- E0-R1 is now the **accepted Enhanced-shell baseline** for *future* isolated feature research/branches. It does not replace or overwrite the frozen Classic source; Classic access in a unified E0 build is behaviorally protected, while this executable's startup is intentionally different.
- Source diff from first E0 comprises only two E0-specific frontend runtime files, plus focused verifier/docs. Designer reports 6,590 frozen original runtime files byte-identical, 1,767 source-host checks passed, 1,440 deterministic core updates equal, one standard Windows compile/smoke PASS and independent H: recovery. Scope limits are in [technical review](E0_R1_MANAGER_TECHNICAL_REVIEW_20261105.md). Chief's acceptance supplies practical UI approval, not a retroactive instrumented native timing measurement.
- No change to actual gameplay Step/Draw/clock sequencing, audio driver, ROM art or palette, 60 FPS implementation, scaling, CRT, save, QoL, ring scatter or GPZ3 textures.

## Decision and follow-up
**E0 STATUS: CLOSED — CHIEF ACCEPTED.** Use exact SHA `deccefc0...` as the next enhancement study baseline. Do **not** silently merge to game `main`, modify frozen Classic tag, publish public binaries or retag the original baseline. Existing H: backup and accepted ZIP remain preserved.

**Next programme:** E1 **60 FPS feasibility/research only**, since the accepted GameMaker zone Create explicitly sets `global.chaosTickRate=60` and `game_set_speed(60,gamespeed_fps)`. Establish the actual distinction between gameplay state tick rate, GameMaker Step frequency, animation updates, rendering/present cadence and original ROM timing before proposing interpolation, fixed-update or GPU rendering architecture. No changes or new build until Chief/Manager separately authorize an E1 pilot. See [enhancement backlog](ENHANCEMENTS_ROADMAP_20261105.md).

**Separate deferred registers:** [FC-PF-001 GPZ3 tube artwork seams](tracking/POST_FREEZE_CLASSIC_DEFECTS.md) and [ENH-QOL-001 richer ring scatter](tracking/ENHANCED_QOL_IDEAS.md). Do not bundle those into E1.
