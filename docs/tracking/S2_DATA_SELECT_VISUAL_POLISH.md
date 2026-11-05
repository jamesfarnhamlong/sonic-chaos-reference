# S2 Data Select — Visual/Presentation Polish Backlog
**Opened 5 November 2026 · Chief actual Windows review · PARKED — NOT A CURRENT DEVELOPMENT TASK**

## Baseline and scope
S2 five-slot Enhanced Data Select is **CHIEF FUNCTIONALLY ACCEPTED** at private local `0809ef9cbc9ea9c1fda3bc0ead45aa9aa749a5a7`, one Windows ZIP `SonicChaos_Windows_20261105_S2_DATA_SELECT_PRIVATE.zip`. Chief naturally played Sonic into GPZ1, earned 2 persisted Emeralds across process reloads, played Tails into SEZ2 and resumed at SEZ1, tested cards/controls/delete and original Classic; all PASS.

Chief supplied **five private illustrative screenshots** after acceptance. They are not a license to redistribute Sonic 3 art nor sufficient to diagnose the exact GML render code. This is one **future bundled display-UI polish scope**, not justification for a new ZIP/build/management approval per item. Preserve baseline packages, Classic isolation, S1 options/defaults, the authentic source sound/music and data semantics.

## Open presentation issues

| ID | Owner observation | Investigation / proposed outcome | Severity |
|---|---|---|---|
| S2-VIS-01 | Tails looks like he has a **weird yellow hat** | On selected/empty Tails card, top/head silhouette looks unnaturally flat/capped. Compare actual source sprite frame and its subimage bounds, crop, UV, scissor and card overlay/palette. Diagnose before touching art. Restore correct head/ears without source-art stretching or changing gameplay Tails. | High (visible defect) |
| S2-VIS-02 | Empty TVs should have **Sonic 3-like animated static** | Investigate a subtle moving noise effect restricted to the small TV aperture in **NEW/empty** slots. Preserve readable `NEW`/occupied-state presentation, low overhead, safe resource ownership, no new sound or legacy audio meddling. | Medium (feature polish) |
| S2-VIS-03 | Six TV zone **thumbnails look too crunchy** | Reframe real THZ, GPZ, SEZ, MGHZ, AQZ, EEZ native-stage screenshots or create careful native-style small-card versions; improve distinctive landmarks, palette balance and legibility at the *actual* preview size. No resampling of user-supplied third-party Sonic 3 art. Compare at 1:1 output. | Medium (art/readability) |
| S2-VIS-04 | Earned Emeralds **too dull/dead** | Examine current small UI gem sprite, per-frame colour/shader and placement. Propose bright jewel-like multi-hue gems with highlights/edges, aesthetically inspired by Sonic 3 but newly created for Enhanced and not constrained by the game-world SMS palette if not technically required. Show all 0–5 plus eligible sixth and ensure Tails none; **do not** change underlying bit ownership/reward logic. | High (prominent UI quality) |
| S2-VIS-05 | **Sonic/Tails vertical/height discrepancy; Sonic overlaps TV box** | Calibrate both character anchors, size/animation frames and feet baseline. Preserve native sprite pixels (do not nonuniformly stretch). Avoid overlaps with yellow/white TV border, zone label, gem row and selection outline at 256/290/348 logical widths. | High (card composition) |

### S2-VIS-06 — Animated Sonic/Tails running poses (Chief follow-up)

**Chief request:** all characters shown on Data Select cards should actually **run in motion**, like the original character-selection screen, not remain stuck on one running sprite. Use the existing original character-choice six-frame Sonic/Tails sprite sequences and correct native palette shader/timing where suitable. Give the cards a lightweight continuous animation cycle (including unselected/empty character previews); preserve character identity, fixed feet baseline, TV frame clearance and layout at all accepted view widths. Avoid per-card mutable gameplay owners, unbounded surfaces, repeated sprite allocations or anything that changes game simulation/audio. If current preview has a deliberate idle/selected distinction, make its behavior clear and consistent. Review several cycles for head/ear clipping, partial sprites or TV overlap. **Do not copy new Sonic 3 artwork**.

### Important colour-constant clarification

Chief recalled that during S2 development an initially used colour caused a Draw crash. Designer's final S2 report confirms the concrete correction **`c_magenta` → `c_fuchsia`**. That explains the *invalid named constant* crash, **not an established cause** for the 'yellow hat' on Tails or dull Emerald colours. Inspect the original S2 shader, palette, sprite/crop and chosen frame at pixel level before assigning cause; don't falsely conclude a global palette limitation or change an otherwise correct named constant speculatively.

## Audio and functionality keepers
- Chief complimented **reuse of original Data Select music**: retain exactly.
- No redesign of left/right slot, up/down character/zone/act navigation, locked character, character-accurate Emerald ownership, save versioning, wipe confirmation or Classic choice.
- The actual Save/Load/zone/SS gameplay tests passed. Do not relabel presentation wishes as S2 functional failures.
- Existing accepted S1 Sharp/Integer/CRT effects remain optional; **final permanent graphics defaults undecided** until fullscreen/CRT product decisions.

## Efficient future handling
- Address these six items together as a **single coherent UI-art/presentation sprint** or bundle with later endgame interface polish when Chief commissions it; do not stop Boss Rush/gameplay work to run five isolated cosmetic fixes.
- During future source audit, first identify Tails hat/crop root cause and sprite/frame origin, then implement actual continuous Sonic/Tails choice-screen running animation and consolidate composition, TV static, preview curation and gem redesign.
- One private native candidate, source diff/receipts and single Chief side-by-side visual check, not separate packages per symptom.
- Visual checks should include **multi-frame animated** empty and occupied Sonic/Tails (including unselected cards and head/ear bounds), occupied each of six zones, Emerald progression 0/1/3/5/6, completed/partial Sonic, complete Tails, changing card focus, original Classic menu, 256/290/348 widths, S1 filter combos and controller navigation.
- Do not copy screenshots/reference art into public Git. Chief can retain private local image examples/references with management audit for future Designer.

**Status: PARKED / DOCUMENTED.** S2 Chief functional acceptance remains valid.
