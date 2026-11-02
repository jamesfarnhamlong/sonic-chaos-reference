# Sonic Chaos — Manager memory / concise handover
**Rewritten 2 November 2026 · For the next Manager or combined Research/Designer Codex agent**

Read [AGENTS.md](AGENTS.md) for rules and roles, [ROADMAP.md](ROADMAP.md) for live milestones, [base issue register](docs/CURRENT_BASE_GAME_REMAINING_20261101.md) for current/parked decisions. Complete old memory at [the immutable archival revision](docs/archive/management/MANAGER_PRE_REWRITE_20261102.md).

## Current authoritative status

- **Chief-accepted production POC:** `jamesfarnhamlong/SonicChaos_POC:poc/m6f-r1-bee-vertical-retention@636ed72be111bc3de4c297e5768c40c8f38a54e6`, after Chief explicitly confirmed R1's THZ2 bee is working correctly. M6-F GPZ3 ring recovery also Chief PASS; both accepted together. Predecessor M6-E `a4c26e13...` remains an accepted ancestor. GameMaker `SonicChaos_A4B_EXPERIMENTAL.yyp` in full private source package. No main merge.
- **M6-F + R1 final outcome:** Original M6-F `70cac5...` GPZ3 rings passed, THZ2 bees failed. Corrective R1 `636ed72be...` fixed triggered bee vertical camera deletion/recreation; Chief now confirms “working canon”. **M6-F-R1 FULL CHIEF ACCEPTED**. The last fully accepted SHA is R1, not M6-E. Protect ring and flying code.
- **NEW M6-G requested by Chief:** roll out protection against offscreen enemy despawn/reset across **all regular enemy families, particularly THZ `$21` and GPZ `$25` patrols**. Combined agent should enumerate placement owners and original asleep behaviour across SEZ `$20/$23`, AQZ `$3D` / classify `$3C`, MGHZ `$24/$2E` dynamic slots, THZ/GPZ/EEZ flying `$27/$2C` aliases. Actual ROM vs shipped GML traces, corrected/intentional 348-wide QoL with finite lifecycle and no boss/hazard globalization. Branch `poc/m6g-all-enemy-persistence` from accepted R1. One integrated private candidate and one future Chief patrol-focused test, not many small builds. [M6-G binding directive](docs/m6g-regular-enemy-persistence-chief-directive-20261102.md).
- **Next after M6-G:** Chief plans a complete normal base-game playthrough **before enhancements** and may identify a couple more fixes. Attract demos/save system deferred post-base; MGHZ3 presentation/startup lag/AQZ Tails palette parked.

## Accepted implementation already protected

- Master System Europe v1.2 original 256×192 is fidelity control; 348×196 widescreen is normal PC target. Some intentional QoL adapters exist—label them, do not claim byte-exact original.
- Both Sonic and Tails campaign/character abilities, all five Special Stages, bosses, endings in scoped accepted runs. Main original soundtrack: 25/25 known-use programmes accepted in M5-G2, native driver default. F2 Sound Test 63 playable/5 genuinely empty; $8E unused-no-known-retail-trigger; Continue $94 controlled-audio proven but not heard in Chief's sampled run. Historical SFX natural reachability gaps exist, not a blanket failed soundtrack.
- **M6-C2** Robotnik opening machine goes behind original foreground black bars, Chief F5 passed `3cf379240c6e1e06b52a4b57fcfd087fcd1fffa2`.
- **M6-D** original rolling type$19 km/h panel and **ALL developer shortcut removal** accepted `7acdd39f469a74d41362f2998c6783d815b719bf`; original time1:50+28rings→617 km/h, existing bonus/tally untouched. Pause→Level Select and user-facing Sound Test remain.
- **M6-E** checker background widescreen accepted; 1,314 registered resources and 38 IncludedFiles in accepted source. Preserve private PNG/audio dependencies; public GitHub-only checkout may be incomplete.
- Avoid retesting accepted title/cards/spring transparency, broadly re-running 93 AUDIT-0 issues or changing original physics because a source-only case looked odd. Chief directly corrected a wrong Manager assertion that original SMS had no km/h feature; **current owner observation outweighs an incomplete source audit**.

## Known parked items and honesty limits

- MGHZ3 boss entrance **playable but widescreen composition looks messy** to Chief; owner expressly parked it. No invented vertical reveal or speculative camera pan edit.
- First-launch audible/visible startup delay occurs once, later transitions fine; cause unproven. Consider measuring before using cosmetic opening cards.
- AQZ Tails underwater palette now provisionally fine from Chief's original-footage comparison; no new work.
- Historical Spring Shoes/monitor, rebound, SS3 monitor embedding glitches not reproduced by bounded source evidence. Preserve issue IDs/provenance without reopening until a fresh concrete route.
- SS5 raw256 camera, obsolete THZ3 cap and M5 raw F8 carry differences remain documented technical exceptions; don't mark old raw fails green. New M6-F source test intentionally fails obsolete all-width384 expectation.
- Agent Windows `Runner.exe` may fail loader error623 in Codex Windows sandbox; do not waste cycles reinstalling or changing system security. Chief's IDE F5 succeeds. Source tests alone do **not** establish native gameplay acceptance.

## Management and workflow decisions

**Workspace cleanup protocol:** [WORKSPACE_ARCHIVE_STRATEGY](docs/WORKSPACE_ARCHIVE_STRATEGY.md), read-only inventory first; no deletion permission.



**Team is Chief, Manager-san, AM-san, ONE combined Research/Designer Codex agent.** No Janitor, Cloud-kun or separate Claude agent assigned here. Combined agent handles ROM code plus GameMaker implementation, but does not approve its own Chief gates.

**Builds and credits are expensive:** gather evidence/implement related tasks first, cheap targeted tests during coding, one integrated risk-based regression and one private source ZIP / Chief F5 once stable. Only repackage after an actual failure. Preserve source SHA, ZIP checksum/manifest, resource count, exact raw inherited failures; no automatic main merge or public publication of private ROM-derived assets.

**Post-base AM-san proposals:** compare 30-FPS Classic with interpolation to 60 rendered frames while maintaining 30 gameplay Step cadence, then optional time-normalized 60-Hz game-logic engineering; sharp bilinear/nearest pixel preservation and optional palette/effects without rewriting sprites; Vita feasibility later via current YoYo Loader versus native VitaSDK; GMS1.4 backport not preferred. *None yet authorised implementation*. Chief wants a full playthrough first.

**Workspace archival problem:** approximately 170 folders; no Janitor available. At base freeze use read-only local inventory of `git worktree list --porcelain`, dirty/untracked states, hashes/archives/asset dependencies and independent backup+restore. Show Chief a dry-run keep/archive/delete proposal. Do **not** delete or move registered worktrees, untracked private assets or E: folders unilaterally.

## Key documents and historical source

- [Current agent contract](AGENTS.md), [live roadmap](ROADMAP.md), [current base-game queue](docs/CURRENT_BASE_GAME_REMAINING_20261101.md).
- [M6-F Chief split verdict + THZ2 R1](docs/m6f-chief-thz2-bee-failure-20261102.md), [earlier M6-F Manager source review](docs/m6e-chief-acceptance-m6f-manager-review-20261101.md), [M6-F detailed POC evidence](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/70cac5dea79e5e81fb88513effec367cb1af4d0c/docs/m6f-offscreen-persistence.md).
- [M5-G2 Chief audio acceptance](docs/m5-g2-chief-acceptance-20261101.md), [Chief 21-ID historical triage](docs/chief-current-issue-triage-20261101.md), [AUDIT-0 historical 93-ID ledger](docs/audit0/README.md).
- [Full manager history before cleanup](docs/archive/management/MANAGER_PRE_REWRITE_20261102.md) and Git commit `84282afebe6f2f851dc4039b2ff9b5a8a994755d`.

After each milestone **rewrite the relevant status line here**, not another page of dated banner snippets.
