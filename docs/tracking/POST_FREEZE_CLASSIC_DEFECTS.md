# Sonic Chaos — Post-Freeze Classic Defect Register
**Opened 5 November 2026 · Chief observations · future final-pass queue · not E0 scope**

## Purpose and policy
This is a **living bug/visual-parity register for the accepted Classic implementation**. New findings after a private freeze do **not** retroactively invalidate it and do not authorize immediate core edits. The immutable original baseline is private annotated tag `classic-core-20261105`, peeled commit `3a58912659b48573ac7f2c5c96a02a2211d5e4da`. Track reports, source/original evidence, bounded dispositions and owner acceptance separately. If a genuine Classic correction is approved, use an isolated successor maintenance branch/checkpoint, preserving the original frozen tag, and assess safe integration into the unified E0 shell. Do not silently change Classic or turn every old historical verification limit into a new defect.

## Open reports

### FC-PF-001 — GPZ3 tube texture grid/seam artifacts

| Field | Entry |
|---|---|
| **Status** | **OPEN — Chief observed; cause and exact-ROM parity pending investigation** |
| **Priority** | **P2 visual / prominent**; no demonstrated crash, physics error or progression blocker |
| **Affected content** | GPZ3 blue/cyan horizontally striped tube/wall artwork; Chief suspects other textures elsewhere in GPZ/world may show similar seams, **not yet confirmed** |
| **Observed in** | Existing frozen-Classic-derived game graphics, 5 Nov 2026; report supplied together with E0 technical candidate but **not attributed to E0** |
| **Comparison** | User supplied two current Windows game captures in one PNG and a separate photographed original Sonic Chaos running on PS Vita. The Vita photograph is lower-quality; not a same-coordinate pixel-accurate original frame test. |
| **Visible symptom** | Repeating thin dark vertical lines and grid/rectangular boundaries across the bright cyan/blue horizontal tube bands; some boundaries seem to cross the textured surfaces or abruptly divide stripe colours. The original photo looks more continuous at equivalent motifs, subject to photography/scaling artifacts. |
| **Expected** | Original-faithful seamless horizontal bands and deliberate tile boundaries only; no accidental regularly repeated seams at import/render boundaries, at 256 reference or 348 widescreen. |
| **Acceptance owner** | Chief — later focused before/after GPZ3 comparison after original-ROM proof |

### Evidence retained outside public research Git
- **Current PC screenshots (two side-by-side current captures, game HUD roughly 0:13 and 0:51):** `image(20261105-091553).png`, original attached 5 Nov 2026, 1395×418 pixels.
- **Original-SMS comparison photographed through Vita (two views):** `image(20261105-091707).png`, original attached 5 Nov 2026, 1011×435 pixels.
- These images contain game art and should **remain private**; do not publish screenshot bytes to the public `sonic-chaos-reference` repository. Preserve originals unchanged in an independently backed-up private evidence folder. This document records exact filenames and observed properties, not copyrighted image data.
- Precise character, player world X, stage seed and camera coordinates have not yet been captured; screenshot visual impression alone does not establish the specific render-layer root cause.

### Future narrowly scoped inspection (NOT commissioned now)
1. Verify original Europe v1.2 ROM GPZ3 tube tilemap, tile/palette entries, stripe continuity, block boundaries and viewport through a direct emulator/native-pixel screenshot at approximately matched world camera positions. Separate genuinely original hard tile edges from new gaps.
2. The accepted game renders GPZ3 scenery via `objects/OBJ_chaos_gpz3_terrain/Draw_0.gml`: three 1024-wide registered sprites `SPR_chaos_gpz3_terrain_0/1/2` at X=0,1024,2048 plus a conditional type 71 (`$47`) block overlay. Inspect the **source PNG bytes** for baked-in column seams/bad joins before blaming GPU sampling. Compare 8/16/32/64-pixel repetition, 1024-strip boundaries, sprite texture filtering, pixel alignment, alpha edge bleed, draw state, scrolling and wide view.
3. Check GPZ1/GPZ2 and other apparently affected areas **only once evidence warrants expanding beyond GPZ3**. Do not declare all GPZ/world textures defective from one capture.
4. Demonstrate smallest pixel-art-faithful presentation/import correction with authentic ROM source. Keep hitboxes, 30/60 existing clocks, native audio, camera policies and source gameplay unchanged; compare 256 controlled and 348 wide captures. No decorative AI redraw, broad stage re-import or global shader rewrite without explicit proof.
5. Have Chief inspect one matched before/after Windows GPZ3 view before closing; avoid a new full Sonic/Tails campaign. No fix or build requested during E0 frontend acceptance.

**Next decision:** classify after source/ROM matched investigation. Do not silently edit the frozen D core or E0 candidate.

## New reports
Append FC-PF-002, etc. with zone/act, screenshots/private evidence filename, baseline/candidate SHA, reproduction coordinates if known, current vs expected, original evidence class, severity, assigned milestone, state and Chief acceptance. Do not relabel unresolved or untested as fixed.

## Explicit exclusions
- **Not a Classic bug:** Chief's desire for more frequent/varied recoverable rings on damage is recorded separately in [Enhanced QoL Ideas](ENHANCED_QOL_IDEAS.md). The source-confirmed Classic scatter is authentic and should not be modified under this register.
- **Not automatically reopened:** known frozen parity exceptions (Tails `$20/$5E`, 5 raw verifier failures, rare Draw coverage) remain in the freeze ledger absent new demonstrated release behavior.
- **E0 status:** unified frontend candidate commit `69450848b1e06fcef7de63f19ae238ff346e479a` reported technical PASS, Chief visual/controller acceptance still pending. FC-PF-001 predates any proven E0 causation and must not be assigned to that implementation.
