# Sonic Chaos — Manager memory / concise handover
**Rewritten 2 November 2026 · For the next Manager or combined Research/Designer Codex agent**

Read [AGENTS.md](AGENTS.md) for rules and roles, [ROADMAP.md](ROADMAP.md) for live milestones, [base issue register](docs/CURRENT_BASE_GAME_REMAINING_20261101.md) for current/parked decisions. Complete old memory at [the immutable archival revision](docs/archive/management/MANAGER_PRE_REWRITE_20261102.md).

## Current authoritative status

- **M6-H MGHZ3 boss reveal — CHIEF F5 ACCEPTED / MGHZ-007 CLOSED (2 Nov).** Chief tested the single private `SonicChaos_M6H_20261102_A_PRIVATE.zip` and reported **"Yes, perfect! No notes, thats now working as intended."** Initial348 camera stops between spikes3/4 before tree, subsequent pan reveals tree/boss and all eight spikes, fight/progression accepted. Source-only verification12 PASS/4 preserved raw FAIL; full exact contract and owner acceptance in [M6-H receipt](docs/m6h-chief-acceptance-and-base-status-20261102.md). No MGHZ3 retest or code fix requested.
- **IMPORTANT SOURCE POINTER:** The accepted M6-H **private candidate is not yet committed/pushed**. Local source worktree `poc/m6h-mghz3-spike-gated-reveal` branches from M6-G `6e2ffcc1f333c5cdaa0048ac696b55c4f6308905`. This M6-G SHA remains **last published Chief-accepted Git revision**, not the source of accepted M6-H improvement. Ask Designer to commit/push the exact no-change accepted diff, report full new SHA, clean branch and private package/hash concordance, and update this pointer. No rebuild, public private-assets or main merge.
- **Now: owner full normal base-game playthrough, then private freeze decision.** No other production defect is currently confirmed as mandatory. Log only fresh current blockers in a consolidated list; do not rerun accepted G2 audio, M6-D goal display, M6-F/R1 rings/bee, M6-G enemies, M6-H camera individually.
- **M6-F/R1/G protected ancestors:** R1 `636ed72be111bc3de4c297e5768c40c8f38a54e6` accepted GPZ3 high-hit ring recovery and THZ2 triggered flying-bee continuity. M6-G `6e2ffcc1...` accepted THZ/GPZ patrols and SEZ hopper; original GPZ `$25` sleeping movement correction and bounded five-family wide QoL. 19 PASS / 2 retained raw FAIL at M6-G. `$20/$23` are left-moving; multiple visible enemies weren't established duplicated objects.

## Accepted implementation already protected

- Master System Europe v1.2 original 256×192 is fidelity control; 348×196 widescreen is normal PC target. Some intentional QoL adapters exist—label them, do not claim byte-exact original.
- Both Sonic and Tails campaign/character abilities, all five Special Stages, bosses, endings in scoped accepted runs. Main original soundtrack: 25/25 known-use programmes accepted in M5-G2, native driver default. F2 Sound Test 63 playable/5 genuinely empty; $8E unused-no-known-retail-trigger; Continue $94 controlled-audio proven but not heard in Chief's sampled run. Historical SFX natural reachability gaps exist, not a blanket failed soundtrack.
- **M6-C2** Robotnik opening machine goes behind original foreground black bars, Chief F5 passed `3cf379240c6e1e06b52a4b57fcfd087fcd1fffa2`.
- **M6-D** original rolling type$19 km/h panel and **ALL developer shortcut removal** accepted `7acdd39f469a74d41362f2998c6783d815b719bf`; original time1:50+28rings→617 km/h, existing bonus/tally untouched. Pause→Level Select and user-facing Sound Test remain.
- **M6-E** checker background widescreen accepted; 1,314 registered resources and 38 IncludedFiles in accepted source. Preserve private PNG/audio dependencies; public GitHub-only checkout may be incomplete.
- Avoid retesting accepted title/cards/spring transparency, broadly re-running 93 AUDIT-0 issues or changing original physics because a source-only case looked odd. Chief directly corrected a wrong Manager assertion that original SMS had no km/h feature; **current owner observation outweighs an incomplete source audit**.

## Known parked items and honesty limits

- **MGHZ-007 is RESOLVED by M6-H Chief acceptance**, superseding older M6-A no-code/parked dispositions. Original spike-tip coordinates, held right edge world3256, boss (3269,288), final arena right world3328 are preserved in [M6-H receipt](docs/m6h-chief-acceptance-and-base-status-20261102.md).
- First-launch audible/visible startup delay occurs once; cause unproven. Optional measurement before cosmetic opening cards. The original F8 AF-carry discrepancy is an independently documented source-only exception, not a proven audible problem.
- AQZ Tails underwater palette provisionally accepted from Chief's original-footage comparison; no further action now.
- Original attract demonstrations and optional persistent emerald/save progression are **post-base**, not mandatory unfinished gameplay. Historical Spring Shoes/monitor/rebound/SS3 glitches weren't reproduced by bounded tests; preserve provenance but not active without new evidence.
- Original `$8E` unused jingle has no known retail requester, `$9B-$9F` are intentionally empty; other SFX natural-site coverage and controlled-only Continue remain evidence limits.
- SS5 native256 camera, obsolete THZ3 cap, M5 F8 carry and M6-F/M6-G/M6-H inherited raw harness FAILs stay recorded. Do not paint raw failures green when a bounded replacement policy-aware check passes.
- Agent Windows `Runner.exe` occasionally fails with loader error623; Chief's F5 runs. Do not repeat sandbox troubleshooting.
- The 93 historic AUDIT-0 records are archival evidence, not current open defects; the current [owner-led register](docs/CURRENT_BASE_GAME_REMAINING_20261101.md) is authoritative.

## New Chief direction — presentable game and permanent cleanup (2 Nov)

- **Final workspace counted:** 133 GB, 2,929,194 files and 1,268,255 folders; Chief confirms final count.
- **DO NOT archive every old worktree.** Chief explicitly wants redundant working copies, old generated outputs and duplicate milestone ZIPs **permanently deleted** once a per-path inventory proves their redundancy and essential source/private dependencies are independently preserved.
- **Rename branding** from `SonicChaos_A4B_EXPERIMENTAL` to clean `SonicChaos.yyp` and `SonicChaos.exe` through GameMaker safe workflow on isolated packaging branch. Windows source options already use display name `Sonic Chaos` but have stale executable filename and placeholder metadata.
- **Standalone file caveat:** `data.win`, `options.ini`, native `g1d_z80.dll`/bank, `a3v_psg.dll`, `a3v_programs.scsp`, policy and OGGs are not assumed rubbish. `g1d_cases.json`, `g1e_cases.json`, `m4/` and earlier G1B SCSP require file-access/route audit before exclusion. Verification and experiments folders may contain untracked unique research/private assets.
- Next agent work: close exact accepted M6-H source commit, audit/minimize clean Windows VM package, read-only count/size+Git topology inventory, show Chief path-specific DELETE/KEEP/UNKNOWN manifest. No file deletion until Chief approves and canonical restore is demonstrated. [Full plan](docs/sonic-chaos-final-packaging-and-deletion-plan-20261102.md).

## Management and workflow decisions

**Workspace deletion protocol:** [WORKSPACE_ARCHIVE_STRATEGY](docs/WORKSPACE_ARCHIVE_STRATEGY.md), read-only inventory first; permanent deletion is Chief's desired outcome but exact paths are not yet authorised.



**Team is Chief, Manager-san, AM-san, ONE combined Research/Designer Codex agent.** No Janitor, Cloud-kun or separate Claude agent assigned here. Combined agent handles ROM code plus GameMaker implementation, but does not approve its own Chief gates.

**Builds and credits are expensive:** gather evidence/implement related tasks first, cheap targeted tests during coding, one integrated risk-based regression and one private source ZIP / Chief F5 once stable. Only repackage after an actual failure. Preserve source SHA, ZIP checksum/manifest, resource count, exact raw inherited failures; no automatic main merge or public publication of private ROM-derived assets.

**Post-base AM-san proposals:** compare 30-FPS Classic with interpolation to 60 rendered frames while maintaining 30 gameplay Step cadence, then optional time-normalized 60-Hz game-logic engineering; sharp bilinear/nearest pixel preservation and optional palette/effects without rewriting sprites; Vita feasibility later via current YoYo Loader versus native VitaSDK; GMS1.4 backport not preferred. *None yet authorised implementation*. Chief wants a full playthrough first.

**Workspace archival problem:** the earlier ~170-folder count was a *top-level development-group estimate*, not a full Windows Properties result. The newer 2 Nov screenshot shows **133 GB, 2,929,194 files and 1,268,255 folders** (Chief confirms final); earlier 1.41 GB screenshot was a count-in-progress. No Janitor available. First preserve accepted M6-H private ZIP/manifest/source separately; run read-only high-level inventory to plan 133GB/million-file backup without blind full-tree Robocopy. At base freeze use read-only local inventory of `git worktree list --porcelain`, dirty/untracked states, hashes/archives/asset dependencies and independent backup+restore. Show Chief a dry-run keep/archive/delete proposal. Do **not** delete or move registered worktrees, untracked private assets or E: folders unilaterally.

## Key documents and historical source

- [Current agent contract](AGENTS.md), [live roadmap](ROADMAP.md), [current base-game queue](docs/CURRENT_BASE_GAME_REMAINING_20261101.md), [M6-H Chief acceptance](docs/m6h-chief-acceptance-and-base-status-20261102.md).
- [M6-F Chief split verdict + THZ2 R1](docs/m6f-chief-thz2-bee-failure-20261102.md), [earlier M6-F Manager source review](docs/m6e-chief-acceptance-m6f-manager-review-20261101.md), [M6-F detailed POC evidence](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/70cac5dea79e5e81fb88513effec367cb1af4d0c/docs/m6f-offscreen-persistence.md).
- [M5-G2 Chief audio acceptance](docs/m5-g2-chief-acceptance-20261101.md), [Chief 21-ID historical triage](docs/chief-current-issue-triage-20261101.md), [AUDIT-0 historical 93-ID ledger](docs/audit0/README.md).
- [Full manager history before cleanup](docs/archive/management/MANAGER_PRE_REWRITE_20261102.md) and Git commit `84282afebe6f2f851dc4039b2ff9b5a8a994755d`.

After each milestone **rewrite the relevant status line here**, not another page of dated banner snippets.
