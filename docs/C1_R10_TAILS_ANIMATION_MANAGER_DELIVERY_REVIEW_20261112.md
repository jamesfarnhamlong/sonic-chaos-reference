# Sonic Chaos — C1-R10 Tails animation: Manager #12 delivery review
**12 November 2026 · ISOLATED CORRECTION CANDIDATE ACCEPTED FOR FOLLOW-ON C1 SOURCE ONLY · CLASSIC REPLACEMENT HOLD**

## Evidence basis and disposition
Chief supplied the complete private `C1_R10_TAILS_ANIMATION_FIDELITY_20261112.md` report. Manager has read it and the current R7/R9 context; Manager has **not independently executed** the ROM, Windows candidate, local source ZIP, H: recovery or raw traces.

**Decision: retain C1-R10 as the next isolated C1 branch parent**, not as a Chief-accepted production Classic replacement. Candidate source SHA `f5e77b061276a60dfa6dc72043113be4b19e42fe`, tree `c24c48c201bced056428790eaad769c90c1d7904`; parent R3 SHA `b667cc5cebcd3c3e047d9f527cc78b76e1e027f0`. These are Designer-reported local identities and must be reverified by the next agent before branching. Private original ROM SHA256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`. Frozen historical Classic tag `3a58912659b48573ac7f2c5c96a02a2211d5e4da` and Enhanced S6 `47c501ecb994a4fcb1eeac1c29793f3f1142a304` remain protected.

## Proven bounded correction
Original ROM Tails animation current0/request0 first loads8, then next update requests state1 and **reloads8**, before decrementing to7 at update3. Existing R3 GameMaker had started animation directly in wrapper state1, decrementing on update2. Only `SCR_chaos_adapter.gml` and `SCR_chaos_tails.gml` change: Classic ordinary Tails starts animation0/0 while keeping initialized gameplay wrapper1/1, preserving authentic request/reload phase. No artificial +1 counter, frame timing patch, sprite replacement or gameplay physics change.

Reported compiled retail route comparisons: **Tails180/180 counters, pointers, selected frames, facing, positions and probe parity**; Sonic180/180 counters/positions. **462 controlled Tails animation-engine rows** across eight sequences, **309 full flight callback updates**, **104 Sonic negative control updates** matched. Enhanced S6 preserved **10,542 state samples +102 images**; Classic **138 captures +30 frontend outputs** unchanged; R2/R3 start/camera controls preserved. H: full source/22 ignored dependencies and evidence recovery reported. Historical raw death helper ERROR, GPZ and THZ camera FAILs, raw SS4/SS5 FAILs and raw Tails host-dependency ERROR remain explicit, not converted to PASS.

This does **not** prove exact ROM vs GameMaker *presented frame* phase: original frame180 displayed frame4 while native selected/drew frame5 in the bounded comparison, and original frame181 remained partially different. Natural death/Continue, full routes, PAL timing, original left8 VDP mask, original first16 object slots and original attract demos remain unverified. C1-R9 ordinary-camera integration stays **DESIGN HOLD**, with no source changes.

## Next strategic action
Chief explicitly prefers substantive implementation rather than more 5–10-minute fidelity probes. Commission [C1-R11 three authentic attract demos](C1_R11_ORIGINAL_ATTRACT_DEMOS_INTEGRATED_IMPLEMENTATION_SPRINT_20261112.md) from this exact isolated R10 branch, if local SHA/tree/E:/H: preflight passes. Implement original demo functionality and report remaining camera/display differences without concealing them. No C1→Enhanced merge, push, tag, release or Chief acceptance request.
