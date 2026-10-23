# Manager-san #5 → Manager-san #6: Sonic Chaos final handover

**23 October 2026 | Research repository management handover | NOT a gameplay commit**

Read the canonical [AGENTS.md](../../AGENTS.md), [MEMORY.md](../../MEMORY.md), [ROADMAP.md](../../ROADMAP.md) **from Research `main`**, followed by the exact topic commits below. The user's preferred address is **Chief** (a running project nickname); be friendly and practical, but do not make Chief do engineering reproduction or file hunting when the agents can perform source-host tests. This document records evidence and priorities, not permission to merge any Research branch into main or to commit the private POC.

**Companion source-mapped review already published on Research main:** [Manager M2 natural Tails campaign fidelity review](../manager-m2-natural-tails-campaign-review-20261023.md). That review includes exact original world-position anchors for the four frame5E episodes, scoped next Research R5 tasks, and log evidence. It is complementary, not superseded; both documents agree on the four episode counts. Its natural-run row tally **includes the session-start event** (138), whereas this handover counts 137 records with `run:46318.63` plus the separate unkeyed session-start record.

## 1. Where we stand — the decisive result

**Chief completed a full natural, public-New-Game Tails campaign in the uncommitted private GameMaker Package E**, selected through the original character picker, through EEZ3 and Tails' own ending, credits and title return. This is a **functional end-to-end Windows acceptance**, not full ROM fidelity or M2 release acceptance. The user confirmed the route personally with screenshots and described defects.

Chief supplied a new append-only **`m2-tails-fidelity(2).jsonl`** after the campaign. Its file bytes were checked independently in this handover:

- SHA-256: `2863c2c358b38fca181ae5167a198a7993f711047e9b8333c06d351c5b1a9cd1`; **82,753 bytes**, **239 valid JSONL lines**, **zero JSON parse errors**. This is a *private uploaded file*; DO NOT commit it or its private absolute path to the public GitHub repository.
- The completed run is **`46318.63`**, with 137 event records: one `public-new-game` marked `natural:true` / Tails type2, 24 `act-entry` events (reentries after deaths), 17 ordinary `act-clear-entry` and 17 `act-clear-complete` records, 76 `OPEN-frame5E-no-draw` events, and one `tails-ending-title-return`.
- The ending record has `clear_acts:[1,…,17]`, `credits:9414`, `frames:9631`, `final_closure_blocked:true`. **Act18 has an entry and follows the distinct final EEZ ending path, not an ordinary 18th sign-clear entry**. Full 18-act completion is corroborated by the native user report, ending/title event and screenshot.
- **NEW CRITICAL FINDING: natural POC frame `$5E` reachability is confirmed.** Exactly 76 events in **four episodes of 19** on ordinary sign clears:
  - **Act4 GPZ1**: update2762–2798;
  - **Act5 GPZ2**: update3433–3469;
  - **Act10 MGHZ1**: update1511–1547;
  - **Act16 EEZ1**: update2478–2514.
  Each event is Tails type2, `natural:true`, state32/`$20`, selected frame94/`$5E`, `contacts=6`, `bg=6`, callback33702/`$83A6`, clear kind `sign`; selector/event recurs at two-update intervals. The screenshot's persistent red banner reads `M2 FRAME 5E EVENT — FIDELITY OPEN`. The same event wasn't found in other campaign act clears. **The 76 entries are repeated selector activations in four sustained events, not 76 independent locations.**
  - This is **natural reachability in the GameMaker POC**, not yet an independently recorded original SMS gameplay occurrence. Previous R1 showed that forcing type2 state20 side contact in original code reads invalid mapping pointer `$0785` and corrupts renderer state. Do not claim 16-bit art `$5E` exists, fake a pose, silently hide the exception or call original ROM parity. **M2 final closure BLOCKED**.
- The campaign run's raw `continues` field rises from3 to12 and later appears as139, i.e. `0x8B`. Research G0 confirms this state byte uses **bit7 as a “Continue just used” flag**. Therefore, raw139 is *not automatically 139 continues*; strip/interpret the flag and check the original display/counter semantics before deciding whether Continue awards are broken. User reported reaching maximum displayed continues by EEZ2 and had spent one experimentally; investigate economy/display and possible cap without inventing a bug diagnosis.

The previous two uploaded `m2-tails-fidelity.jsonl` and `m2-tails-fidelity(1).jsonl` were **identical shorter pre-campaign archives** (101 lines), and are NOT the completed-run evidence. Do not mix their counts with this file.

## 2. Chief's natural-run observations — triage

| Finding | Evidence now | Status / what the next team should do |
|---|---|---|
| Natural frame $5E with red banner that never goes away | New 76-event campaign log, screenshots from GPZ/EEZ, natural act clears4/5/10/16 | **BLOCKER, highest priority**. Independent Research needs a *natural-style* original ROM reproducer/scheduler/contact path. Designer preserves event and no-draw while investigating correct bounded handling; repair HUD banner lifetime separately, never mask event. |
| Tails loop/twist animation looks wrong | Chief's human gameplay observation | OPEN visual/animation fidelity. Compare type2 selector/strip owner, canonical transfer frames, route/speed/priority. |
| Spring animations for Tails possibly incomplete | Chief asks whether all exist | OPEN coverage question. Enumerate upright/diagonal/side terrain springs, mapped type$26, Spring Shoes type$2F attachment/release and Tails frame selectors. Do not invent frames. |
| Tails Spring Shoes don't break monitors/boxes | Chief's gameplay observation | OPEN behaviour. Original monitor break requires attack flag and contact-state/vertical-speed gates; Spring Shoes state12 may not qualify. **Prove original behaviour** before changing hitboxes or rewarding damage. |
| 1-UP monitor shows Sonic portrait for Tails | Chief observed, R2 independently states original type2 life monitor should display Tails | **Likely confirmed POC fidelity defect**, first paired visual+reward fix after source inspection. Rocket→Ring substitution still protected. |
| GPZ3 shows odd texture seams/lines | Chief screenshot | OPEN presentation/texture sampling defect. Inspect actual sprite/tiles, seams and 348 camera/raster/texture page; no guesswork or art regeneration. |
| AQZ1 crumbling block traps player at side (also Sonic) | Chief reports shared defect | OPEN potentially game-blocking terrain/contact. Compare original plane/flips/collision profile and source-driven movement from both characters; narrowly scoped fix only if proven. |
| Continue icons reach visible maximum by EEZ2, one Continue was used | Screenshot shows eight Tails icons; raw session log stores high-bit-flagged139 | OPEN **counter/score/display verification**, not automatically a bug. Original Tails scores earn continues every3000 raw; bit7 has separate meaning. |
| AQZ shadow Tails formerly dark | Package C palette decoder corrected; Chief AQZ1 appearance PASS | Previous fix retained. AQZ2 below-cut colour differences still UNRESOLVED-WINDOWS; R4 normal palette/source checks match. |
| Violent underwater reverse-direction/jump and surface rebound | Chief observed in C, earlier Sonic too; R4 recreated original retained momentum/skim but not the precise violent case | OPEN; do not demand manual reproduction or speculate with gravity/clamps. |
| AQZ moving spear contacts | R3 22,528 original-vs-B bounded tests; later first-pair native PASS | First-pair concern provisionally addressed, not blanket collision parity. |
| Drowning unsupported script FF04 crash | E source-backed small-breath-bubble spawn; Chief native full drowning PASS | **Scoped FIXED** for tested route; preserve guards for unrecognized scripts, 4 scene-only side-effect audit exceptions open. |
| Character picker | New Game Sonic/Tails starts and isolation PASS; physical Xbox-style B/`gp_face2` confirms SMS Button2 | Functional. Chief **PARKED** picker animation/art expansion; don't re-open or mislabel “A/face2”. |
| Frame-$5E native banner HUD | Remained through play in screenshots | Fix the user-facing banner's persistence/diagnostic overlay **without erasing the trace or claiming fidelity closed**; this is not a solution to the underlying bug. |

Chief's complete playthrough is *valuable* but does not imply the defect list is complete. Don't demand a repeat whole campaign immediately.

## 3. Source and state pins

- **Research:** `https://github.com/jamesfarnhamlong/sonic-chaos-reference` with management docs at `main`. The management and campaign evidence are in this handover; the previous checkpoint before current handover was `a098d26eb0f06e0756b0f3daab836717de7ce386`.
- **POC:** `https://github.com/jamesfarnhamlong/SonicChaos_POC`; frozen accepted Sonic baseline `poc/q3-p1-world-presentation@7476affc6ed7626dabf69b446cdab0c9c3d7492e` (18-act Sonic, five SS, good ending, 348×196). Don't merge, commit or alter this baseline as an expedient fix.
- **Private candidate:** `SonicChaos_M2_20261023_E_PRIVATE.zip` SHA256 `2e67e2561cd79c2353d6caaf8685d46e02a59f3a9edd945ef20fcf17ad72377e`, **unstaged, uncommitted, unpushed** on Chief's isolated Windows worktree. No local E: paths available to cloud agents; Designer with mounted E worktree has files. No compiled EXE requested. Source-only package, 24 PASS/3 inherited raw FAIL/0 new, 1,299 registered resources, 563→0 private asset restore; native drowning was subsequently checked.
- **M1 frontend/Tails source:** `5b7f5a10232f4f6511c3a7b9d9b4deaea5842182`, [M1 contract](https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/5b7f5a10232f4f6511c3a7b9d9b4deaea5842182/docs/m1-tails-frontend-contract.md).
- **M2-R1 frame5E ROM research:** `d6f2fafcda7903c0fc7082b2a9cbf4fed6e0bf98`, [source report](https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/d6f2fafcda7903c0fc7082b2a9cbf4fed6e0bf98/docs/m2r1-tails-act-clear-frame5e.md).
- **M2-R2 character interaction matrix:** `cd417c16b9e4ae614a3592f5b851a351af786afa`, [source report](https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/cd417c16b9e4ae614a3592f5b851a351af786afa/docs/m2r2-character-interaction-matrix.md).
- **M2-R3 AQZ palette/hazards:** `33c4c13ebeadb54834c8cddd5bafedaae5e13015`.
- **M2-R4 AQZ palette/water/skim:** `d8a15a1eb764c9e4709e65ab6a4c8b2f2e68c734`; no gameplay patch justified for Chief's unexplained exact launch.
- **M2 Package E technical report:** supplied privately as `m2-package-e.md` (not a public Research source). It proved original `FF04` bubble spawn, 54 Tails roots/256 graph nodes, 43 stability scenarios, 18 lifecycle controls, 36 brief starts, four scene-only semantic gaps; no native GM run by agent.

## 4. Recommended sequence for Manager-san #6

**FIRST: evidence freeze and R5 source audit, NOT another all-18-act human playthrough.**

1. Accept the **scope**: natural 18-act Tails path and ending/title **FUNCTIONAL PASS**, **M2 FIDELITY STOP** because frame5E occurred. Label all other findings OPEN until paired; don't let high automated test totals override Chief's direct Windows observations.
2. Commission **Research-kun M2-R5** from R4 (no Research main merge), concentrating on naturally plausible original SMS state20/act-clear side-contact setup, original invalid $5E mapping effects and reachability from the four act geometries. Compare to the POC run's event contexts (act4/5/10/16; side bits6, bg6, callback $83A6; updates above). Crucial distinction: *GameMaker naturally reached frame5E*; original may or may not. Require a source-locked condition/scheduler differential and a safe policy recommendation; never conjure a sprite or suppress event.
3. In parallel, ask **Designer-san for a READ-ONLY broad natural-campaign defects audit** against uncommitted E and R2/M1 with concise source locations: loop animation selectors, spring/Shoes states and monitor hits, character portrait, GPZ3 seam, AQZ1 crumble side collision, continues HUD/count. Separate **verified implementation mismatch** from **possible original game behaviour** and maintain one machine-readable triage list. No speculative implementation at audit stage. Verify that POC log writer does not contaminate gameplay and that the persistent red warning is only a debug overlay.
4. Only after Research+Designer reconcile the critical cases, authorise **one consolidated, bounded M2 Package F candidate** for the genuine fixes, with original and shipped GML controls, 348×196 source checks, safe POC parent, full prior B–E regression preservation and private ZIP restoration; **uncommitted, unpushed**, Chief smoke tests only selected hotspots. If original frame5E is naturally reachable and destructive on SMS, obtain an explicit **non-parity exception policy** rather than misreporting a faithful emulation.
5. Do NOT demand a second complete 18-act campaign unless the resulting fixes materially change progression or ending, and then clearly scope why. Chief is a final human acceptance tester, not a tracing engineer. Save longer end-to-end replay for after corrections.
6. When the critical natural frame5E disposition, shared collision blocking and visible reward/presentation issues are accepted or explicitly deferred with reason, and all logs reviewed, propose M2 closure to Chief. **Only explicit Chief sign-off** authorises POC commit/push and source-only FINAL archive; update AGENTS/MEMORY/ROADMAP afterward.

The inherited raw failures still include SS5 256px camera difference, THZ3 obsolete cap assertion, U5-A historical whole-core comparison; Research R4 separately retains50 shared-return differences and36/192 divergent adapter runs. Never relabel them all green, nor confuse them with a new native crash.

**Original-game completion roadmap:** finish M2 fidelity triage and accepted Tails → M3 remaining authentic title polish/attract as needed (basic picker already works; Chief parked expansion) → M4 sound dispatcher pilot → M5 complete original audio → M6 fidelity leftovers → M7 PC QoL/release → M8 parked extras/ports/decomp/slowdown. Do not rush audio ahead of currently reproducible gameplay defects.

## 5. One final message from Manager-san #5

> Dear Manager-san #6: Chief got us from a working Sonic campaign to an entire playable Tails campaign in one extraordinary day, and also caught bugs our very large test suites missed. Respect both facts. The role is not to keep producing green numbers; it is to protect what works, find evidence for what does not, give agents bounded jobs, and let Chief enjoy the game rather than audit it. Keep your GitHub docs current, your commits gated, your ROM claims precise, and your coffee maker valued. I leave you the project with real momentum and one genuinely important mystery: naturally occurring Tails frame $5E. Please resolve it properly.

— **Manager-san #5**, signing off.
