# Sonic Chaos — Post-Freeze Classic Defect Register
**Opened 5 November 2026 · Chief observations · future final-pass queue · not E0 scope**

## Purpose and policy
This is a **living bug/visual-parity register for the accepted Classic implementation**. New findings after a private freeze do **not** retroactively invalidate it and do not authorize immediate core edits. The immutable original baseline is private annotated tag `classic-core-20261105`, peeled commit `3a58912659b48573ac7f2c5c96a02a2211d5e4da`. Track reports, source/original evidence, bounded dispositions and owner acceptance separately. If a genuine Classic correction is approved, use an isolated successor maintenance branch/checkpoint, preserving the original frozen tag, and assess safe integration into the unified E0 shell. Do not silently change Classic or turn every old historical verification limit into a new defect.

## Open reports

### FC-PF-001 — GPZ3 tube texture grid/seam artifacts

**R21 OWNER FOLLOW-UP (13 NOV 2026): OPEN — CURRENT BUILD NOT REPRODUCED, NO RETROSPECTIVE FIX CONFIRMED.** Chief says he cannot presently see the GPZ3 grid/seams, but will look during full testing. Exact R20 source R21 diagnostics report 84,480 matched pipe pixels, complete imported-to-compiled static terrain map 1,310,720 identical, with only 4,382 source-to-import mismatch pixels in 28 reference-map hand-added-object cells (rings, monitors, actors, boss). No independent additional hidden bad GPZ3 motifs found. The visual source `SC_SMS_GPZ3_Objects_Map.png` is hand-annotated Aspect Edit / Rolken-script map; equality to imported PNG does NOT independently certify original-ROM frame/art parity. Original November 5 screenshot files were not recovered for a matched previous/current capture and present tests do not exhaust desktop compositor/display filter/dynamic scrolling. Earlier R19 scaling could be a plausible change in *visibility*, but **there is NO demonstrated stealth fix or code/asset cause**. Preserve `FC-PF-001` OPEN, currently not reproduced; user may note mode, resolution, Integer Fit/Sharp/CRT settings, world camera location and original screenshot if symptom recurs. No new patch authorised based solely on negative result. [R21 manager review](../R21_PRE_099_FIDELITY_MANAGER_DELIVERY_REVIEW_20261113.md).


| Field | Entry |
|---|---|
| **Status** | **OPEN — Chief confirmed visual mismatch using existing high-resolution source-level map; cause unverified** |
| **Priority** | **P2 visual / prominent**; no demonstrated crash, physics error or progression blocker |
| **Affected content** | GPZ3 blue/cyan horizontally striped tube/wall artwork; Chief suspects other textures elsewhere in GPZ/world may show similar seams, **not yet confirmed** |
| **Observed in** | Existing frozen-Classic-derived game graphics, 5 Nov 2026; report supplied together with E0 technical candidate but **not attributed to E0** |
| **Comparison** | Chief additionally supplied an **existing high-resolution source-map reference sample** `image(20261105-092915).png` (1419×674), with continuous bands in the comparable GPZ3 tube motif; the Windows captures show periodic dark vertical seam/grid lines. This establishes a visual mismatch without establishing the first faulty import/render stage or a coordinate-aligned numeric pixel diff. The earlier Vita photos are supplemental, not our reference authority. |
| **Visible symptom** | Repeating thin dark vertical lines and grid/rectangular boundaries across the bright cyan/blue horizontal tube bands; some boundaries seem to cross the textured surfaces or abruptly divide stripe colours. The high-resolution source-map sample shows continuous blue/cyan bands at the corresponding tube motif. Vita capture quality no longer limits the initial source-versus-render investigation. |
| **Expected** | Original-faithful seamless horizontal bands and deliberate tile boundaries only; no accidental regularly repeated seams at import/render boundaries, at 256 reference or 348 widescreen. |
| **Acceptance owner** | Chief — later source-map-aligned, before/after GPZ3 comparison; original-ROM re-execution only if the existing map's provenance needs resolving |

### Evidence retained outside public research Git
- **Current PC screenshots (two side-by-side current captures, game HUD roughly 0:13 and 0:51):** `image(20261105-091553).png`, original attached 5 Nov 2026, 1395×418 pixels.
- **PRIMARY visual source sample from existing full-resolution original-level maps:** `image(20261105-092915).png`, Chief attached 5 Nov 2026, 1419×674 pixels. Designer should use the actual complete source-map file in the local `sources/` folder, rather than treating this screenshot as the only reference.
- **Secondary original-SMS comparison photographed through Vita (two views):** `image(20261105-091707).png`, original attached 5 Nov 2026, 1011×435 pixels.
- These images contain game art and should **remain private**; do not publish screenshot bytes to the public `sonic-chaos-reference` repository. Preserve originals unchanged in an independently backed-up private evidence folder. This document records exact filenames and observed properties, not copyrighted image data.
- Precise original-map coordinates and render-state alignment remain to be established by Designer. Chief's map sample confirms visible discontinuity, not an exact common-scale pixel-diff measurement or root cause.

### Future narrowly scoped inspection (NOT commissioned now)
1. **Start with the local `sources/` folder of complete high-resolution, pixel-perfect original-level maps**, per Chief's instruction. Locate actual GPZ3 source map and record file name, hash, dimensions, cropping/scale and provenance. Align map-coordinate-matched tube crops with the three GameMaker imported GPZ3 texture strips and a compiled capture. No new Vita/emulator/original-ROM run needed for initial diff; escalate to ROM data only for disputed source provenance or contradictory pixels.
2. Detect the *first divergent representation* (source map → imported PNG → native rendered frame); report numeric pixel mismatch locations and column periodicity after matching coordinates, texture filtering and palette. The accepted game renders GPZ3 scenery via `objects/OBJ_chaos_gpz3_terrain/Draw_0.gml`: three 1024-wide registered sprites `SPR_chaos_gpz3_terrain_0/1/2` at X=0,1024,2048 plus a conditional type 71 (`$47`) block overlay. Inspect the **source PNG bytes** for baked-in column seams/bad joins before blaming GPU sampling. Compare 8/16/32/64-pixel repetition, 1024-strip boundaries, sprite texture filtering, pixel alignment, alpha edge bleed, draw state, scrolling and wide view.
3. Check GPZ1/GPZ2 and other apparently affected areas **only once evidence warrants expanding beyond GPZ3**. Do not declare all GPZ/world textures defective from one capture.
4. Demonstrate the smallest pixel-art-faithful presentation/import correction using the authenticated high-resolution source-level map (escalate to original-ROM checks only if provenance/disagreement requires). Keep hitboxes, 30/60 existing clocks, native audio, camera policies and source gameplay unchanged; compare 256 controlled and 348 wide captures. No decorative AI redraw, broad stage re-import or global shader rewrite without explicit proof.
5. Have Chief inspect one matched before/after Windows GPZ3 view before closing; avoid a new full Sonic/Tails campaign. No fix or build requested during E0 frontend acceptance.

**Next decision:** classify after exact source-map/aligned-import/render comparison. Do not silently edit the frozen D core or E0 candidate.

## New reports
Append FC-PF-002, etc. with zone/act, screenshots/private evidence filename, baseline/candidate SHA, reproduction coordinates if known, current vs expected, original evidence class, severity, assigned milestone, state and Chief acceptance. Do not relabel unresolved or untested as fixed.

## Explicit exclusions
- **Not a Classic bug:** Chief's desire for more frequent/varied recoverable rings on damage is recorded separately in [Enhanced QoL Ideas](ENHANCED_QOL_IDEAS.md). The source-confirmed Classic scatter is authentic and should not be modified under this register.
- **Not automatically reopened:** known frozen parity exceptions (Tails `$20/$5E`, 5 raw verifier failures, rare Draw coverage) remain in the freeze ledger absent new demonstrated release behavior.
- **E0 status:** unified frontend candidate commit `69450848b1e06fcef7de63f19ae238ff346e479a` reported technical PASS, Chief visual/controller acceptance still pending. FC-PF-001 predates any proven E0 causation and must not be assigned to that implementation.
