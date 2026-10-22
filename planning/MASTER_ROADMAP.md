# Sonic Chaos — MASTER_ROADMAP

**Planning edition 0.1 | 22 October 2026 | Manager-san #5 | proposed, not implementation authority**

## Authority and evidence rules

- **Frozen accepted POC:** [`poc/q3-p1-world-presentation@7476affc6ed7626dabf69b446cdab0c9c3d7492e`](https://github.com/jamesfarnhamlong/SonicChaos_POC/commit/7476affc6ed7626dabf69b446cdab0c9c3d7492e). Direct child of Q2-P1 `d2f0612`; Chief accepted Package A's four categories and Package B's two corrections. FINAL private archive reported: `SonicChaos_Q3P1_20261022_FINAL_PRIVATE.zip`, SHA-256 `b409be469f27e8b6270c510281dc601f04b471c8d3432f47ebe639e10e43c859` (not downloaded in this planning review).
- **ROM source of truth:** Sonic Chaos (SMS, Europe v1.2), private hash `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`; use Research's recovered assembly/cache and authentic assets, not invented behaviour. Do not publish ROM or private extracted pixels/audio.
- **Source hierarchy:** latest Windows acceptance and Q3 closure > current Manager AGENTS candidate > scoped committed POC/Research documentation > older AGENTS archive. Historical G0–G10 labels are useful planning references, *not current task authorisation*.
- **Reconciliation limitation:** this first roadmap is based on the supplied `AGENTS_ARCHIVE_20261020.md`, `AGENTS_Manager5_20261022_Q3P1_FINAL_CLOSED_REVIEW_NEXT.md`, Q1 fidelity audit, audio preflight, and live GitHub Q3/G2/AUDIO-A0/OPENING closures. The user's newly installed Windows-root AGENTS and every historical **local** release/archive were not directly opened here. Supply the current root AGENTS and any missing archive manifests to the next agent; cloud agents cannot read the Windows drive by path. Confirm their latest content and deduplicate any additional outstanding items before treating this as exhaustive.

## A. Current accepted state — DO NOT RECOMMISSION

| Area | Accepted evidence and limit |
|---|---|
| **Sonic core adventure** | Chief completed one uninterrupted **18-act New Game Sonic run**, gathered all Chaos Emeralds, received the good ending/credits and returned to title at 348×196. Q1 also has **9/9 separate targeted cross-zone smoke passes**. This is strong human functional acceptance, not frame-perfect ROM parity for every route. [Q3 closure](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/7476affc6ed7626dabf69b446cdab0c9c3d7492e/docs/q3p1-closure.md). |
| **Special Stages** | SS1–SS5 implemented and individually accepted historically; Q1 full-Emerald campaign and Q2/Q3 regression checks add integration evidence. Natural timeout, return and alternate routes retain scoped coverage, not a universal claim. |
| **Campaign plumbing** | New Game RAM reset and 18-act metadata, goal/results/title cards, all boss zone rollovers, Sonic partial/full endings, TIME OVER/death/Continue/Game Over, score and continue rewards were implemented in G1/G2. **Original campaign saving is deliberately absent**; optional PC save belongs to QoL. |
| **Opening cinematic** | Original pre-title sequence implemented/Windows accepted as OPENING-1; Sonic/Robotnik/Tails cinematic, skip-to-title and natural title handoff. **Opening audio not integrated**. [Opening closure](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/7476affc6ed7626dabf69b446cdab0c9c3d7492e/docs/opening1-closure.md). |
| **Gameplay/wide presentation** | Q2 corrected gameplay-facing/wrong-way underwater dash and native-size widescreen title/results backgrounds. Q3 corrected wide THZ3 patrol, SS4 clock-monitor sampling seam, and ROM-authentic SEZ/AQZ/SS4 breakable fragments. Q3 final has 1,100 registered resources. |
| **Sound infrastructure** | AUDIO-0 classified **70 request IDs** (31 music, 37 effects, 2 controls). AUDIO-A0 Windows-accepted a **Sound Test with five authenticated preview WAVs** for `$90`, `$82`, `$81`, `$BF`, `$A6`; these are evaluation previews, **not gameplay music integration or production loops**. [AUDIO-A0 closure](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/7476affc6ed7626dabf69b446cdab0c9c3d7492e/docs/audio-a0-closure.md). |
| **Known technical exceptions** | Q3 retains raw FAILs for SS5 256-wide camera-X (≤2 px) and the obsolete THZ3 boss-clear camera-cap assertion; other older frozen-test mismatches remain historical and explicitly tracked, not secretly green. |

## B. Original game still to complete — ORDER OF WORK

### 0. Planning/source inventory — first, research-only

Reconcile installed root AGENTS, historic `ROADMAP/FULLGAME_0/CROSSZONE/SHARED_MECHANICS/ZONE_IMPLEMENTATION/DEFERRED_ISSUES` references, public closure documents, Research contracts, and **available** local source/archive manifests. Mark each feature **ACCEPTED / SOURCE-ONLY / PARTIAL / MISSING / UNVERIFIED**, with owner, provenance, next prerequisite and Windows acceptance gate. Do not re-audit a verified closure merely because an old roadmap says OPEN. Output/update this three-document planning set; no POC modifications.

### 1. Tails technical and asset foundation — next grouped Research preflight

- Audit *original SMS Tails* player states, controls and movement (including actual flight/swim behaviour only after recovered ROM evidence), attack, collisions, speed/power-up differences, animations/frame timing, zone start/end rules, lives/continues/score thresholds and ending path. Reuse original Research cache; explicitly separate established POC shared mechanics from character-specific missing behaviour.
- Inventory, decode and hash authentic Tails player frames and mappings; account for palettes, origins, frame scripts, underwater, hurt/death, boss/transport poses and opening/ending uses. Replace **inherited/temp GameMaker sprite references** only when the corresponding authentic frame contracts exist.
- Protect previously accepted Sonic gameplay. No playable-Tails claim from inherited `SCR_player_sprites_tails` alone, and no fabricated frames. Provide one integrated implementable asset/movement contract rather than commissioning per-sprite fixes.

### 2. Playable Tails + original character front door — consolidated runtime programme

- Implement original Tails animation/state/control differences in a cohesive package, keeping the known Sonic baseline intact. Test ordinary acts, hazards, boss contacts, Special Stage eligibility/restrictions, deaths, Continue/Game Over, relevant score awards and the actual Tails ending/return behaviour.
- Restore **authentic title screen and character selection** using original-ROM UI art, animation/timing and navigation. The current title still draws inherited `SPR_title` (`OBJ_menu_title/Draw_0.gml`); the natural `chaos_run_new_game()` currently forces Sonic character 1. Do not simply expose a character-select option until Tails is playable.
- Preserve the existing original opening movie. Developer Level Select/Sound Test remain accessible as separate testing fixtures, not a substitute for character selection. Remove or rehome nonoriginal entry points only during the separately approved product/options stage.
- **Dependency gate:** unlock Tails in the real title flow only after his gameplay route is accepted. If scope proves too large, stage one Tails-implementation candidate and one integrated front-end candidate; never ship a dead Tails option.

### 3. Authentic music and effects — ORIGINAL-GAME REQUIREMENT, not QoL

- **Audio-preparation preflight can run in parallel with Tails asset research:** reconcile AUDIO-0 catalogue, Q2-era local `audio1-poc-preflight.md` (supplied source in this planning workspace), Research AUDIO-1B renderer validation, 5 preview WAV provenance, original PSG music/SFX arbitration, interrupt/restore, fades, intro/loop points, driver ticks versus accepted 60-update GameMaker runtime, and private-asset distribution/restoration. Nothing about five preview files proves production-ready 70-ID coverage.
- Choose an explicitly approved approach: verified rendered PCM with documented limitations, stems/channels with arbitration, or another validated player. Do **not** silently substitute approximated tracks or replace original timing to make a loop fit.
- Implement **one owned request dispatcher and lifecycle**, not separate players per room. Wire pilot opening/title/THZ, ring and spring **once at canonical call sites**, then expand approved zone/boss/SS/ending cues in a second meaningful audio batch. Respect `$00` as no-op and `$F8` as reset, legitimate music/SFX coexistence and controller pause/title/transition rules.
- Human acceptance must check audible music/SFX, restarts/loops, no overlap/leakage, pauses, Sound Test regression and scene transitions. Keep private WAV files out of public Git; register resources and provide source-only package with validated ignored assets. [Audio A0 details](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/7476affc6ed7626dabf69b446cdab0c9c3d7492e/docs/audio-a0-soundtest.md).

### 4. Remaining original presentation and systemic fidelity

- Source-backed **attract-mode demos** and authentic title/option transitions (archived Research lists THZ1 Sonic → GPZ1 Tails → SEZ1 Sonic; confirm against current ROM/caches before coding).
- Group genuinely reproducible gameplay defects by **physics/contact**, **camera/presentation**, and **object/fragment completeness**. Priorities/statuses are in `FIDELITY_REGISTER.md`. MGHZ3 pit/tree entrance reveal is a named open presentation item. Unknown ‘SLZ1’ foreground structure requires identification.
- Original-mode acceptance gates: full Sonic path is already human PASS; add a scoped **Tails end-to-end** run; targeted check for audio/attract integration; confirm protected endings, SS routes and title behaviour. Do not imply every per-frame ROM edge case is tested.

### 5. Quality of life and release gate — only after original functionality

Optional PC save/resume; configurable display/controller/audio settings; input-buffer/latency options if chosen as **deliberate non-ROM enhancements**; useful launcher and documentation; controller remap; production-safe debug-key/Level Select/Sound Test exposure policy; clean build/privacy/asset packaging. Original Mode must remain available and unaffected.

### 6. Extras — parked

Enhanced modes, additional visual/audio upgrades, alternate UI, other playable characters, ports (PS Vita), full decomp/disassembly, and SMS/GG slowdown patch are **separate side projects**. None is a prerequisite for completion of the source-faithful SMS widescreen game.

## C. Completion definition

**Original-game feature-complete candidate** requires a Chief-accepted Sonic campaign (already achieved), an accepted **playable Tails campaign + proper original title/character selection**, original audio implemented to an explicitly agreed fidelity tier, major source-backed original presentation (including attract mode if verified) and no unresolved critical progression/contact blockers. Remaining canonical oddities or low-priority presentation deviations may be documented/parked. **Production-ready PC release** has a further QoL, debug-removal, copyright/private-asset distribution and packaging gate.

**Not authorised by this file:** runtime implementation, Q4 launch, ROM distribution, updating remote AGENTS or GitHub branches. See `MILESTONE_PLAN.md` for one proposed grouped assignment sequence and `FIDELITY_REGISTER.md` for deferred issues.