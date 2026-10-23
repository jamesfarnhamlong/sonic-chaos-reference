# Manager M2 — natural Tails campaign: fidelity log review

**23 October 2026 — evidence checkpoint, not M2/ROM fidelity closure**

## Executive disposition

Chief completed an input-played public New Game → Tails 18-act campaign in **private, unstaged/uncommitted/unpushed Package E**, reached the own ending/result/credits and returned to the title. This is an **accepted functional Windows campaign observation**, not the final original-ROM fidelity claim or permission to commit. Native earlier E drowning regression passed; previous script-write fatal did not block the completed route. Chief also reported numerous candidate animation/visual/collision/reward defects (separate backlog below).

The **natural GameMaker-side Tails state20/frame `$5E` exception is confirmed**, not merely inferred from the red HUD screenshot. The ordinary original-ROM reachability of this same predicate has **not** been proven; original Research M2-R1 only established the ROM's invalid mapping/VRAM reads if the state and side contact occur. We must distinguish a genuine original reachable bug from a POC side-contact/state-ownership mismatch.

## Source of evidence and boundaries

Chief uploaded the **latest unedited append-only** `m2-tails-fidelity(2).jsonl`. Manager parsed it directly in the current sandbox session, without changing the file.

- Raw uploaded-file SHA-256: `2863c2c358b38fca181ae5167a198a7993f711047e9b8333c06d351c5b1a9cd1`; **82,753 bytes**, **239 JSONL records**, **zero parse errors**.
- The earlier `m2-tails-fidelity.jsonl` and `m2-tails-fidelity(1).jsonl` are byte-identical **26,863-byte prefixes** of this new history (old digest `043cdaa696a068c44531d071593248cffb4134003527766de44cddac53913a3d`). Do not count these as independent full campaigns.
- The full append-only history includes older developer fixtures and earlier sessions. Isolate the **single latest natural public-New-Game run** for event attribution; its records are **138** (one session-start, one Tails run start, one public-new-game, 24 act-entry including restarts/Continues, 17 act-clear-entry, 17 act-clear-complete, 76 frame5E events, one Tails-ending-title-return).
- The natural-run `public-new-game` event records type2, natural=true, fixture=false, act1. Natural `act-entry` records cover **all integer acts 1..18**. Its 17 `act-clear-complete` events cover **acts 1..17**; act18 uses a different terminal ending route. A terminal `tails-ending-title-return` includes `clear_acts:1..17`, ending/credits counters and `final_closure_blocked:true`.
- **None of the 76 `OPEN-frame5E-no-draw` rows are from developer fixtures.** Each reports `natural:true`, type2, state32 (`$20`), selected frame94 (`$5E`), request32, background/contact flags6 and the 348×196 viewport.
- Original screenshots of gameplay, red diagnostic banner and Tails result were supplied by Chief, but are **not uploaded to this public repository**. Nor is the raw JSONL or any local user path. This report describes only non-sensitive metadata.

## Four natural POC state20/frame$5E event bursts

| Act ID | Zone/act | First GameMaker player update | Approximate original world X/Y at first event | `contacts` / `bg` | Entries in burst | Last update |
|---:|---|---:|---|---|---:|---:|
| 4 | Gigalopolis 1 | 2762 | (5111.0625, 430.4296875) | 6 / 6 | 19 | 2798 |
| 5 | Gigalopolis 2 | 3433 | (4087.0625, 686.25) | 6 / 6 | 19 | 3469 |
| 10 | Mecha Green Hill 1 | 1511 | (4087.0625, 366.4375) | 6 / 6 | 19 | 1547 |
| 16 | Electric Egg 1 | 2478 | (4087.0625, 430.671875) | 6 / 6 | 19 | 2514 |

All four are **normal sign clears**, not bosses. Each burst logs **19 successive animation reloads spaced two player updates apart**, accumulating 19 event counts per act (total76), rather than 76 distinct level errors. `contacts=6` has side-contact bit `4` and floor-contact bit `2`; background flags also6. This directly aligns with original M2-R1's **side-bit → numeric frame94/duration2** selector. It does **not** establish why GameMaker produced/retained side contact or whether the canonical SMS reaches the same predicate naturally at the same route.

### Next M2-R5 independent Research questions

1. Use these four **exact original POC arrival coordinates, acts, frame and contact histories** to identify terrain/goal placement and which POC owner wrote/latched `contacts=6`. Map against original ROM same terrain and sign contact generation, with proper world/tile/plane and 256-to-348 viewport adapters; record any uncertainty.
2. Execute the original Z80 **actual natural sign chains** via credible stage-arrival plus input-owned player motion; never force state20 or contact bits in the test whose purpose is natural reachability. If input histories are unavailable, explicitly label observed route **POC-natural / ROM-unresolved**. Controlled state20-side fixtures remain valuable but distinct evidence.
3. Compare original sign-runoff callback `$83A6`, selector `$8EE1`, prior-to-callback contact ownership, end-state repeat cadence and state reset. Determine whether POC side flag persists incorrectly from a wall/loop/surface.
4. Respect authentic ROM fact: type2 frame `$5E` points outside valid authored mappings, resolving code at `$0785`; original forced cases corrupt tile/render. Do **not** invent replacement Tails art, substitute Sonic frame, clear side collision speculatively, silently suppress the event, or claim the no-draw guard is ROM parity.
5. Supply a minimum source-backed resolution recommendation or unresolved reasons for Designer. Ensure event logging survives even if the on-screen red banner stops being sticky after recording.

### Additional Chief-observed issues (candidate, not yet source-proven)

| Severity/owner | Symptom | Research/verification requirement |
|---|---|---|
| **P1 — Tails animation** | Tails' loop/twist animation incorrect | Compare type2 state/selector, contact/banked transfer and imported frame origins to actual POC natural route |
| **P1 — monitor visuals** | A 1-UP monitor displayed Sonic portrait during Tails gameplay | **Contradicts independent M2-R2 source contract**: life parameter2 must choose character-dependent Tails portrait before art latch; verify exact placed monitor/instance and rendering |
| **P1 — GPZ3 presentation** | Multiple thin horizontal texture lines observed | Compare tile/background/raster and viewport seam owners; no unsupported re-extraction |
| **P1 — shared collision** | AQZ1 crumble wall side-sticking, also with Sonic | Capture actual tile/plane/side-mask and test original contact behaviour, including M2-R4 inherited type30 side-projection gap; no blanket physics patch |
| **P2 — Tails Spring Shoes** | Check all authentic frame/pose phases; player appears not to break monitors | Original parameter2 life monitor and Spring Shoes state12 distinct; monitor requires attack flag and specific top/side/bottom/downward contact semantics; don't assume inability is a bug |
| **P2 — continues** | Continue portraits filled/maximum by EEZ2 after only one use | Original Tails receives score continues at 3,000 threshold; compare actual BCD/bit-packed flag and display count. **Do not interpret raw log field `continues:139` as 139 continues**: ROM Continue flag uses bit7 after accept, so preserve raw and masked interpretations |
| **Open inherited — AQZ** | Visible split palette discrepancy and violent reverse+jump report | R4 original/shared-callback controls support some canonical effects but not the particular native route; keep open without guess patches |
| **UI diagnostic** | Red `M2 FRAME 5E EVENT — FIDELITY OPEN` banner persisted over subsequent scenes | Keep append-only trace and unmistakable developer/debug status, but separate persisted user-visible overlay from the one-time event; do not hide fidelity issue from tests/release gate |

## Manager actions

- **Freeze Package E**. No M2 commit, push or full-fidelity release. Preserve accepted functional Tails New Game→18 acts→Tails ending/title and earlier Sonic baseline.
- Commission **M2-R5 original-vs-POC natural contact/frame5E route research** as a focused task on an isolated Research branch; it may read the metadata in this document, not the private JSONL.
- Commission a **separate Designer source audit only**, prioritising Tails 1-UP portrait, loop poses, original Spring Shoes state12 contact and GPZ3 visual/zone seams, while Research adjudicates frame5E. No unsourced gameplay changes.
- Combine verified corrections into **one new private source-only candidate**, with automated natural-case-inspired smoke and brief Chief Windows checks; **no request for another full campaign or manual reverse-jump capture**.
- **Do not conflate successful natural POC campaign with proven original-ROM natural frame5E reachability**; keep both facts visible in AGENTS/MEMORY/ROADMAP.

## Grounded references

- [R1 original invalid type2 frame $5E mapping](https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/d6f2fafcda7903c0fc7082b2a9cbf4fed6e0bf98/docs/m2r1-tails-act-clear-frame5e.md).
- [R2 character-dependent monitor portraits / Spring Shoes contact](https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/cd417c16b9e4ae614a3592f5b851a351af786afa/docs/m2r2-character-interaction-matrix.md).
- [R4 AQZ/side projection and residual source differences](https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/d8a15a1eb764c9e4709e65ab6a4c8b2f2e68c734/docs/m2r4-aqz-water-reversal.md).
- [Canonical management](../AGENTS.md), [handover](../MEMORY.md), [roadmap](../ROADMAP.md).
