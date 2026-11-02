# M6-G — Chief native F5 acceptance
**Manager-san #8 · 2 November 2026 · COMPLETED**

## Chief's verdict: ALL THREE PASS — M6-G CHIEF ACCEPTED

Chief reports after running the consolidated private GameMaker M6-G candidate:

> “Yes that looks more correct I think. All 3 behaved as expected. ... Enemies are much more natural now and respawning less. All good I think!”

This is **Chief acceptance of the specified three-scenario F5 scope**: THZ ground patrol vertical departure/return, GPZ ground patrol backtracking and SEZ hopping walker departure/return. The acceptance confirms user-visible behaviour, **not** exhaustive natural playthrough of all 95 records, proof of every original-ROM callback, or independent inspection of the Chief's local ZIP. The prior scripted source/ROM checks remain separate evidence.

**Accepted production baseline:** `jamesfarnhamlong/SonicChaos_POC:poc/m6g-all-enemy-persistence@6e2ffcc1f333c5cdaa0048ac696b55c4f6308905`, direct child of accepted `M6-F-R1@636ed72be111bc3de4c297e5768c40c8f38a54e6`. GitHub compared exactly 1 ahead/0 behind and remote branch at SHA during prior Manager review. No POC main merge, private release/public distribution or automatic archiving is implied. Existing 1,314 resource registrations/38 IncludedFiles preserved per candidate integrity report.

Prior accepted gameplay remains protected: GPZ3 high-Y recoverable scattered rings (M6-F) and THZ2 triggered bee encounter continuity (M6-F-R1); original native audio default, goal km/h display, removal of dev shortcuts, widescreen character-select, opening foreground masks and other scoped campaigns.

## Chief's SEZ hopper observation — classifying it correctly

Chief asks whether the hopper has a patrol and reports **two enemies briefly visible** as one travelled very far left and another appeared near an origin.

Shipped `scripts/SCR_chaos_sez_enemy/SCR_chaos_sez_enemy.gml` and original SEZ S4 contract distinguish:
- **`$20` SEZ walking/hopping enemy:** original initialization horizontal velocity `-128/256` (left at 0.5 px/update), walking and jumping states 3/4; direction does **not** reverse at a ledge or patrol end. Movement pauses asleep, animation can continue. Existing finite horizontal retirement permits ordinary placement recreation after sufficiently long separation.
- **`$23` SEZ leaper:** original launch/relaunch horizontal velocity `-256/256` (left at 1 px/update) with leap/rest cycle; no patrol reversal. Script can continue while asleep.
- Separate original SEZ placement records coexist. Seeing two left-moving enemies near one another is **plausible and not by itself evidence of duplicate occupancy or same-token respawn**. The Chief's description does not establish whether it was two distinct placements or a legitimate far-distance retirement/recreation. No unasked new bug or further human tests should be inferred.
- Core M6-G objective is to prevent **premature** deletion/reset on moderate vertical or horizontal returns while respecting finite long-distance retirement and per-type original asleep rules. Chief reports the hopper behaved correctly and passed. Do not modify the SEZ movement logic based solely on the overlap.

## Verification and known limitations remain explicit

Manager reviewed four production files, 95 regular-enemy placements across seven original numeric types, 760 policy scenarios, 20 physical terrain/player/camera cases, 19 integrated PASS / **2 genuine raw FAIL**. One raw failure `verify_viewport_adapter.js:249` is inherited all-width384 expectation; the other `verify_sez_s4.js:329` is **newly superseded** by intended M6-G wide-Y sleep/retention; distinct policy-aware checks PASS. No silent repainting. Five families had M6-G changes (THZ/MGHZ `$21`, GPZ `$25`, SEZ `$20/$23`, AQZ `$3D`); flying `$27/$2C` R1 unchanged. Original GPZ `$25` sleeping callback correction applies at both native256 and wide348; per-type wide vertical retention is an explicitly documented PC QoL deviation, not ROM byte parity.

Known limits intentionally remain: THZ `$21` falling `$B2F0` motion-while-asleep GML mismatch (distinct from patrol), and GPZ1 type`$25` token18 below normal authored map. Neither was newly reported as a gameplay issue in Chief's short check. No blanket full-ROM/natural-route equivalence claim.

## NEXT: Chief's comprehensive base-game playthrough, before enhancements

**M6-G is complete; do not commission more enemy-persistence tests or correction builds without a fresh specific current symptom.**

Chief's established sequence:
1. Play through the base game normally on the accepted M6-G source, recording a concise list of actual gameplay, audiovisual or progression concerns if any. The owner may still have one or two additional base-game improvements; don't invent them.
2. Consolidate and triage any concrete problems, address meaningful blockers efficiently, and receive Chief's **explicit private base freeze / archive checkpoint** decision. Attract demos and optional Sonic3-style save/emerald unlock remain **post-base parked**; AQZ Tails palette provisionally satisfactory, MGHZ3 widescreen visual roughness and first-start audio onset delay parked.
3. **Only after the complete playthrough and base-freeze decision**, consider AM-san's optional 30-vs-60 rendered FPS, pixel-preserving graphics improvements; Vita porting and separate ROM/decomp/slowdown projects are later independent work. The local ~170-folder archive inventory and safe cleanup require a dry-run, private asset backup+restore proof and Chief's explicit approval, not automatic deletion.

**Supporting evidence:** [M6-G previous Manager GO review](m6g-manager-review-chief-f5-gate-20261102.md); [M6-G Chief directive](m6g-regular-enemy-persistence-chief-directive-20261102.md); [candidate source report](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/6e2ffcc1f333c5cdaa0048ac696b55c4f6308905/docs/m6g-enemy-persistence.md).
