# Sonic Chaos — ROADMAP.md

**Canonical project roadmap | 23 October 2026 | Manager-san #5**

See [AGENTS.md](AGENTS.md) for binding rules and [MEMORY.md](MEMORY.md) for the current handover. This roadmap is a manager-owned work sequence, not automatic permission to start a milestone. Research topic branches are **not merged** by updating these management docs.

## Current game baseline

**CLOSED for scoped Windows acceptance:** the 348×196 Sonic 18-act campaign, all five Special Stages, Emerald good ending/credits/title, authentic opening cinematic, campaign/death/Continue/score flow, Q2 and Q3 accepted world/camera/fragments.

Accepted POC parent: [`poc/q3-p1-world-presentation@7476affc`](https://github.com/jamesfarnhamlong/SonicChaos_POC/commit/7476affc6ed7626dabf69b446cdab0c9c3d7492e). Any Tails implementation remains an **isolated, uncommitted** candidate until Chief's final acceptance.

## Workstream status and next gates

| Milestone | Status as at 23 Oct 2026 | Next action and acceptance |
|---|---|---|
| **M0 archive/source reconciliation** | Research completed within accessible evidence at `5b7f5a1`; original Windows-root authority now moved to Research main in manager-owned docs. Private archives not all independently inspected. | Preserve historical provenance; do not re-audit accepted Sonic campaign. |
| **M1 Tails/frontend/audio contracts** | Research `5b7f5a1`, 89 mappings (88 nonblank), 54 scripts; separate original character choice confirmed; title sound $99 versus choice $82. | Contracts remain scoped; dynamic gameplay branches require focused validation. |
| **M2 authentic playable Tails** | **ACTIVE, NOT CLOSED.** Package C source-only/uncommitted; Chief F5: AQZ1 Tails colours/Sonic palettes/AQZ1 spears/six B essentials PASS; combined AQZ2/3 palette ambiguous FAIL and underwater reverse+jump launch OPEN. | M2-R4 evidence first; integrate real New Game character picker in same private candidate **before** the one natural full 18-act Tails acceptance run. Review full same-run frame5E log and ending/title before final M2 closure; no premature POC commit. |
| **M2-R1 frame $5E** | SOURCE INVESTIGATION COMPLETE, NATURAL REACHABILITY OPEN. Original malformed read authentic in forced scenario. | Retain strict no-draw diagnostic exception and natural event STOP gate; do not invent art or call ROM parity. |
| **M2-R2 Sonic/Tails interaction differences** | Research checkpoint [`cd417c1`](https://github.com/jamesfarnhamlong/sonic-chaos-reference/commit/cd417c16b9e4ae614a3592f5b851a351af786afa), 30 focused tests reported. | Reconcile full monitor/sign/equipment/icon/reward/substitute matrices with Designer code; don't mistake “not eligible” for “nothing occurs.” |
| **M2-R3 AQZ palette and spike contact** | **RESEARCH ACCEPTED** [`33c4c13`](https://github.com/jamesfarnhamlong/sonic-chaos-reference/commit/33c4c13ebeadb54834c8cddd5bafedaae5e13015). Actual private B source shows Tails indexed RGB sent to Sonic alpha proxy decoder. AQZ moving object `$3C` has 22,528 bounded contacts matching B; Windows observation OPEN. | Fix only Tails decoder routing using authenticated RGB palette indexes; preserve original CRAM above/split/fully submerged. Instrument actual native 348-wide spear contact phase/sleep/protection; no unproven shared collision rewrite. |
| **M2-R4 AQZ palette/reversal launch** | **RESEARCH ACCEPTED** [`d8a15a1`](https://github.com/jamesfarnhamlong/sonic-chaos-reference/commit/d8a15a1eb764c9e4709e65ab6a4c8b2f2e68c734). Ordinary C palette agrees; conditional special full→split upper-CRAM mismatch not naturally reached. Repeated skim/reverse+jump authentic in controls; exact violent Windows launch still OPEN. 50 raw shared-call differences and 36/192 diverging adapter traces retained. | No speculative physics/palette patch. Capture same-pose AQZ waterline F6/F7 and precisely reproduced fast reverse+jump with held/fresh/input/jump/facing/VY-owner logs. Character picker can proceed as separate contained frontend work in uncommitted M2 candidate. |
| **M3 frontend — phased acceptance order** | **FRONT-DOOR SLICE AUTHORISED FOR PRIVATE M2 CANDIDATE** after R4 review. Separate original choice art/dynamic contract needs ROM source-backed preflight; Sonic default, bounded Left/Right, fresh Button2 confirmation. | Designer implements real New Game → choice → selected Sonic/Tails THZ1 using shared init, preserves opening/title/Continue. Add only bounded AQZ diagnostic instrumentation; short 348-wide human frontend + precise water captures precede the natural 18-act Tails run. No full title overhaul, attract or live audio. |
| **M4 audio driver pilot** | PLANNED; Sound Test has five authentic private preview WAVs but no in-game dispatch. | Validate PSG/render/loop fidelity tier, one request-ID dispatcher, opening/title/THZ/ring/spring pilot, stop/pause/transition/arbitration. |
| **M5 full original audio** | PLANNED, needs M4. | Music/SFX original 70-ID catalogue coverage, authentic loops, channel steals/restores, boss/SS/ending/death, human audible acceptance. |
| **M6 remaining original fidelity** | DEFERRED; register findings remain. | Prioritise reproducible critical contact/progression, then staged MGHZ3 presentation, fragments in GPZ/MGHZ/EEZ, attract demos, other source-backed visual issues. |
| **M7 PC QoL/release** | LATER, only after original game complete. | Opt-in save/resume, controller/display/audio config, debug key gate, packaging/legal/private asset distribution, clean install. |
| **M8 extras/ports** | PARKED. | Vita YoYo Loader, comprehensive decomp/disassembly, SMS/GG speed patch, enhancements; separate projects. |

## Chief-approved end-to-end acceptance sequence (23 October)

**M2-R4 original-vs-C AQZ report → source-backed AQZ correction only if necessary → M3 front-door character picker in private M2 worktree → short New Game Sonic/Tails confirmation/return smoke → one uninterrupted 18-act Tails New Game campaign → original Tails ending/credits/title → review full same-run frame-$5E log → explicit human acceptance → final commit/archive.**

The earlier rule requiring the complete Tails campaign **before** implementing public character choice is superseded only for the **private integrated test candidate**. No untested public/committed Tails option and no independent M3 release is authorised. Original M1 screen: Sonic default, bounded Left/Right, fresh Button 2 confirm, separate choice tiles and timing. Existing title and opening should be protected; original title visual rebuild, attract recordings and live audio are not prerequisites to this natural playthrough. M2-R4 Research finished; Manager reviewed and authorised the bounded private frontend candidate without a water-physics fix. The remaining AQZ native captures and frame5E logger are still M2 closure requirements.

## Mandatory open gates before M2 close

**Visible AQZ blockers / current disposition:** C repaired the dark silhouette in Chief's AQZ1 test. Sonic presentation, opening AQZ1 spear checks and six B essentials passed. Chief reports absent visible Tails palette transitions during water scenes, with a combined AQZ2/AQZ3 card FAIL; **AQZ3 must not switch because the ROM has no water controller**. The separate fast-underwater reversal+jump backward sky-launch is OPEN and may involve the original repeated skim impulse, but is not source-matched. M2-R4 found original/C matched ordinary palette and authentic retained-momentum jumps/skims but did not recreate Chief's exact visual or violent native route. Keep the Windows AQZ issue OPEN; no gameplay change without matched captures. Earlier spear issue is provisionally closed for the tested first pair, not universal collision fidelity.

**Fidelity event**: `OPEN-frame5E-no-draw` may not occur in natural play, but its natural reachability has not been proven unreachable. A natural trigger blocks final M2 milestone closure. Logs missing = UNVERIFIED, never ZERO. Do not replay corrupt mapping/tile bytes in GameMaker or quietly show a substitute frame.

**Cross-character completeness**: original `$10/$04` Rocket monitor becomes `$10/$01` Ring with Tails, **including art and +10 rings**; lives show player portrait; Spring Shoes type`$2F` available to both but animation differs. Every future character-dependent change must verify object placement→visual→reward→state/lifetime and original gameplay reachability.

**Sonic protection**: after M2 changes, test normal Sonic New Game, Rocket monitor, representative Special Stage and boss/transitions, endings where touched; preserve all accepted Q3 parent assets and routes.

## Release discipline

Each milestone uses: exact original ROM/research evidence → bounded Manager approval → fresh isolated Designer worktree from accepted POC SHA → focused and adjacent verifiers **including raw known failures** → one private source-only F5 package → Chief tests 348×196 → only after explicit human approval commit direct child and push, remote SHA0/0/clean, private FINAL source ZIP/hash/restoration receipt → Manager updates these three root documents.

Do not add hidden gameplay modifications during docs migration, promote Research topic branches to `main` without separate review or silently make `M2-R2` or `M2-R3` accepted GameMaker runtime simply because Research tests passed.

## Detailed documents and durable references

The planning originals uploaded on 22-Oct (edition 0.1) are historical. Their **updated edition 0.2** lives on the [M0/M1 topic checkpoint](https://github.com/jamesfarnhamlong/sonic-chaos-reference/tree/5b7f5a10232f4f6511c3a7b9d9b4deaea5842182/planning): `MASTER_ROADMAP.md`, `FIDELITY_REGISTER.md`, `MILESTONE_PLAN.md`. The frame-$5E status later updated the [R1 register](https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/d6f2fafcda7903c0fc7082b2a9cbf4fed6e0bf98/planning/FIDELITY_REGISTER.md). The M2-R2 branch contains the separate interaction matrix, and M2-R3 holds the newer AQZ palette/hazard study. None of these topic branches has been silently merged into main.

Relevant source documents:
- [M0 reconciliation](https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/5b7f5a10232f4f6511c3a7b9d9b4deaea5842182/docs/m0-reconciliation-report.md)
- [M1 Tails/frontend](https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/5b7f5a10232f4f6511c3a7b9d9b4deaea5842182/docs/m1-tails-frontend-contract.md)
- [M2-R1 frame $5E](https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/d6f2fafcda7903c0fc7082b2a9cbf4fed6e0bf98/docs/m2r1-tails-act-clear-frame5e.md)
- [M2-R2 complete character interactions](https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/cd417c16b9e4ae614a3592f5b851a351af786afa/docs/m2r2-character-interaction-matrix.md)
- [M2-R3 AQZ palette and spear evidence](https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/33c4c13ebeadb54834c8cddd5bafedaae5e13015/docs/m2r3-aqz-palette-hazards.md)
- [M2-R4 waterline palette and reverse-jump research](https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/d8a15a1eb764c9e4709e65ab6a4c8b2f2e68c734/docs/m2r4-aqz-water-reversal.md)
- [Q3 accepted GameMaker closure](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/7476affc6ed7626dabf69b446cdab0c9c3d7492e/docs/q3p1-closure.md)
- [Historical AGENTS/archive manifest](archive/management/AGENTS_BACKUP_MANIFEST_20261023.md)

**No automatic next assignment is authorised solely by this roadmap.**
