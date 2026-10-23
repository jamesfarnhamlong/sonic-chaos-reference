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
| **M2 authentic playable Tails** | **ACTIVE, NOT CLOSED.** Package C produced, source-only/uncommitted; Chief F5: AQZ1 Tails colours PASS, Sonic palette PASS, first-pair spear retest PASS, six B essentials PASS; combined AQZ2/3 palette FAIL/ambiguous, high-speed underwater reverse+jump sky-launch OPEN. | Research M2-R4 reconstructs actual palette switching in AQZ1/2 and paired original/C reverse-jump motion; source-evidence gate before any Designer change. AQZ3 has no water controller. Full natural campaign/ending and frame5E log gate remain pending. |
| **M2-R1 frame $5E** | SOURCE INVESTIGATION COMPLETE, NATURAL REACHABILITY OPEN. Original malformed read authentic in forced scenario. | Retain strict no-draw diagnostic exception and natural event STOP gate; do not invent art or call ROM parity. |
| **M2-R2 Sonic/Tails interaction differences** | Research checkpoint [`cd417c1`](https://github.com/jamesfarnhamlong/sonic-chaos-reference/commit/cd417c16b9e4ae614a3592f5b851a351af786afa), 30 focused tests reported. | Reconcile full monitor/sign/equipment/icon/reward/substitute matrices with Designer code; don't mistake “not eligible” for “nothing occurs.” |
| **M2-R3 AQZ palette and spike contact** | **RESEARCH ACCEPTED** [`33c4c13`](https://github.com/jamesfarnhamlong/sonic-chaos-reference/commit/33c4c13ebeadb54834c8cddd5bafedaae5e13015). Actual private B source shows Tails indexed RGB sent to Sonic alpha proxy decoder. AQZ moving object `$3C` has 22,528 bounded contacts matching B; Windows observation OPEN. | Fix only Tails decoder routing using authenticated RGB palette indexes; preserve original CRAM above/split/fully submerged. Instrument actual native 348-wide spear contact phase/sleep/protection; no unproven shared collision rewrite. |
| **M2-R4 AQZ palette/reversal launch** | **RESEARCH NEXT**; commissioned by Manager after C Windows results, no branch outcome yet. Earlier AQZ A2 ROM research confirms a repeated submerged skim impulse at speed but has not reproduced Chief's new high-velocity reverse+jump symptom. | Compare original SMS + shipped C per update for both characters and matched input/camera/waterline; inspect sprite row/CRAM above/split/full, original 568/788 world waterlines and 348 adapter. No global physics adjustment from intuition. |
| **M3 original title + character selection** | NOT STARTED; separate choice screen/source contract known, public title still inherited. | After M2: original art/animations/fades, authentic choice default/input, Sonic/Tails launch without dead option, preserve opening/title return. Attract only with verified playback evidence. |
| **M4 audio driver pilot** | PLANNED; Sound Test has five authentic private preview WAVs but no in-game dispatch. | Validate PSG/render/loop fidelity tier, one request-ID dispatcher, opening/title/THZ/ring/spring pilot, stop/pause/transition/arbitration. |
| **M5 full original audio** | PLANNED, needs M4. | Music/SFX original 70-ID catalogue coverage, authentic loops, channel steals/restores, boss/SS/ending/death, human audible acceptance. |
| **M6 remaining original fidelity** | DEFERRED; register findings remain. | Prioritise reproducible critical contact/progression, then staged MGHZ3 presentation, fragments in GPZ/MGHZ/EEZ, attract demos, other source-backed visual issues. |
| **M7 PC QoL/release** | LATER, only after original game complete. | Opt-in save/resume, controller/display/audio config, debug key gate, packaging/legal/private asset distribution, clean install. |
| **M8 extras/ports** | PARKED. | Vita YoYo Loader, comprehensive decomp/disassembly, SMS/GG speed patch, enhancements; separate projects. |

## Mandatory open gates before M2 close

**Visible AQZ blockers / current disposition:** C repaired the dark silhouette in Chief's AQZ1 test. Sonic presentation, opening AQZ1 spear checks and six B essentials passed. Chief reports absent visible Tails palette transitions during water scenes, with a combined AQZ2/AQZ3 card FAIL; **AQZ3 must not switch because the ROM has no water controller**. The separate fast-underwater reversal+jump backward sky-launch is OPEN and may involve the original repeated skim impulse, but is not source-matched. M2-R4 must establish exact palette and physics differences before edits; the earlier spear issue is provisionally closed for the tested first pair, not universal collision fidelity.

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
- [Q3 accepted GameMaker closure](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/7476affc6ed7626dabf69b446cdab0c9c3d7492e/docs/q3p1-closure.md)
- [Historical AGENTS/archive manifest](archive/management/AGENTS_BACKUP_MANIFEST_20261023.md)

**No automatic next assignment is authorised solely by this roadmap.**
