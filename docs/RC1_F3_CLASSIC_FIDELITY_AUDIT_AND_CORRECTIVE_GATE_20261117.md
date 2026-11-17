# Sonic Chaos — F3 Classic Fidelity Audit & Corrective Gate
**17 November 2026 · Manager-San #13 · PLANNED, not yet commissioned**

## Owner acceptance and current release status

Chief tested the combined private **v0.99.2-f2** game at source **`5d045ae0bba8dcbfa3f220c8e96d78baaa4fc22e`**, checking and **passing all 17 F1/F2 acceptance tickets**; he additionally completed a full Classic Sonic campaign and a one-emerald Enhanced Sonic campaign. This is **Chief acceptance of those scoped fixes, not blanket complete ROM parity**. No fresh Tails full run on F2 is claimed, though Tails was previously played on RC1. Immutable RC1, F1 and F2 trial files/SHA256, original saves and H: recovery are protected.

During the Classic campaign Chief saw a **new P1**: MGHZ3 boss arena camera framed **too high** compared with original ROM, despite F1's separately working GPZ3 +17 correction. He also requested removing white Classic Pause instructions, noticed intermittent missing spike and MGHZ Motobug sounds, and observed corner sticking/embedding into crumble blocks in SEZ/AQZ in Classic and Enhanced. These are **SC-RC1-23 through 26** in the [active register](RC1_CHIEF_FULL_RUN_DEFECT_REGISTER_20261115.md).

**Do NOT nominate or promote RC2/v1.0 yet, or merge Super Sonic.** New Classic camera fidelity P1 must be investigated and corrected, preserving accepted F1/F2. This document defines an **audit-first F3 follow-up** to be commissioned with Chief GO, not an order to execute automatically.

## Goals and workstreams

### A. SC-RC1-23 — P1 comprehensive Classic camera parity
- Confirm actual original-ROM and F2 captured MGHZ3 entry/fight; identify exact first mismatch, world-to-screen transform and camera owner. **Do not assume another +17 shift is right**.
- **Audit all six Classic bosses**, not just GPZ and MGHZ: THZ3, GPZ3, SEZ3, MGHZ3, AQZ3, EEZ3. Include moving-camera scenes and special vertical phases.
- For each: record native 256x192 render, ROM VScroll / camera X,Y, pixel anchor of floor/boss/player and camera lock/unlock entry/exit, actor state and collision bounds. Distinguish camera used by mechanics from view drawing/centering, especially F1 GPZ3 PreDraw/PostDraw correction. Review GameMaker viewport/window resize/4:3/aspect selectors and prior Enhanced widescreen branch layers for leakage; **prove** or disprove cross-mode contamination rather than accepting it as predetermined cause.
- Audit relevant Classic normal-level camera and title/Pause/transition viewport semantics where shared overrides could be involved. Preserve exact original gameplay timeline, spawn, collision, bosses, controls, Classic 256x192, and Enhanced 348x196 independent widening. Compare uninstrumented screenshots and real fight triggers to original ROM, not only fixed-position fixtures. Only source-backed minimal corrections, no global camera fudge or physics rewrite.
- Deliver a **six-arena parity matrix**, cause, changed source and targeted before/after native/screenshot evidence, unchanged Enhanced/Boss Rush/RC1-F2 accepted features. If full ROM numeric alignment cannot be attained, explicitly HOLD with residual cases.

### B. SC-RC1-24 — P2 Classic Pause white-text cleanup
- Remove only non-ROM white instructional overlay in Classic Pause; user says README or existing confirmation prompts suffice. Identify actual owner/draw order; ensure Pause freeze, quit-to-title/desktop, input control, option focus, fullscreen and Enhanced Pause are identical.
- Native Classic 256x192 screenshot against ROM Pause, Sonic/Tails spot-check. Independent small code commit.

### C. SC-RC1-25 — research-first intermittent SFX
- Two Chief routes: spike impact while Spring Shoes worn with missing spike SFX, and intermittent MGHZ Motobug spring/contact SFX. The port `SCR_chaos_audio` uses one mailbox with overwritten pending requests, transferred at `chaos_audio_tick`; **this is a candidate explanation, not a confirmed defect**. Map actual original-ROM SFX priority/overwrite semantics, exact mailbox/D4A4->DE04 timing and driver playback, and compare to native GameMaker **audible PCM** and request trace under concurrent events, both modes/characters.
- Determine separate cases if sources are distinct; coordinate with separately parked SC-RC1-22 original ROM `$A5` twist sound. If ROM intentionally suppresses, close authentic/no change. If true mismatch, propose small fix/test and obtain explicit review before modifying shared SFX queue; avoid adding always-play sound or changing music arbitration.

### D. SC-RC1-26 — research-first crumble corner penetration
- ROM `$AF/$0C/$13` verified rider hold **T+1..T+16**, Y anchor=cell_top−16 (player feet 2px inside), Y speed 0 and **no presence check**; can hover after leaving ledge. Thus some apparent sticking is **canonical**. But top-side/corner entry SEZ/AQZ needs exact matched approach before declaring it authentic.
- Capture original-ROM vs F2 frame-aligned X/Y/flags/foot sample/collision plane, first activation, hold and break, approach speeds and character states. Include SEZ and AQZ; Sonic/Tails, Classic/Enhanced OFF/ON, footwear. If exact behavior matches, **NO gameplay change** (document intentional original oddity). If divergent, propose smallest verified local fix; preserve F1 93-cell crumble and original platform behavior.

## Working rules
- Create a new private F3 worktree/branch from **exact F2 game SHA `5d045ae0bba8dcbfa3f220c8e96d78baaa4fc22e`**, not RC1 nor Super R3d; preserve all prior source SHA, packages, 22 private dependencies and H: recovery.
- Isolated SCTest standard account for potentially dirty runtime tests. Bound captures/logs by explicit quota and record zero Chief AppData writes; preserve Sonic/Tails completed RC1 and F2 saves/namespace. No new 5,000-file AppData spills or enormous data dumps.
- Report ROM vs F2 contrast and hypotheses before changing camera/audio collision; independently commit narrow verified corrections, retain owner acceptance from F1/F2 and rerun relevant native regressions/true original-ROM checks.
- If ROM parity for sound and crumble is confirmed, **do not create a bug fix**; preserve them as researched authenticity dispositions. Classify source suite inherited failures without relabeling all 178 tests as PASS.
- Deliver compact camera parity matrix (six arenas, normal camera owner boundaries), Pause UI pixel comparison, SFX arbitration research, crumble ROM results, preservation matrix. Prepare **one private F3 Windows/source candidate** if any code fixes prove necessary; include SHA256, dependency closure, H: verified recoverability, new Chief 5–10-minute targeted verification.
- Chief retains authority for release and any merge. RC2 nomination only after acceptance of camera parity plus no P1 regressions. NG+ separate integration afterward as previously agreed.

## Protected open work and status
- All 17 earlier F1/F2 items: **Chief PASS** within tested scope. Existing RC1/F1/F2 code/ZIP immutable; do not reopen completed items without demonstrated regression.
- SC-RC1-21: MGHZ2 twist alleged freeze **closed ROM false positive**. SC-RC1-17 loop fall-off remains independent research. SC-RC1-22 A5 twist sound research still separate.
- **F3 is PLANNED, no implementation authorised in this documentation alone.** User may request a formal paste-ready commission next.

