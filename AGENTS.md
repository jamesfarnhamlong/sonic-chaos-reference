# Sonic Chaos — AGENTS.md
**Working instructions · revised 2 November 2026 · Manager-san #9**

This is a **living operations document**, not an append-only milestone diary. Update the relevant section in place after meaningful decisions. See [ROADMAP.md](ROADMAP.md) for milestones, [MEMORY.md](MEMORY.md) for handover facts, and [current base-game issues](docs/CURRENT_BASE_GAME_REMAINING_20261101.md) for the owner-led queue. The entire pre-rewrite history is accessible at [the immutable archival revision](docs/archive/management/MANAGER_PRE_REWRITE_20261102.md).

## 1. Mission, provenance and screen contract

Build a faithful, privately playable **GameMaker Sonic Chaos (Master System Europe v1.2)** adaptation, preserving the original 256×192 gameplay contract while offering the accepted **348×196 widescreen** presentation. Preserve the original character-specific mechanics, levels, special stages, bosses, results and sound without inventing parity. Original-source evidence informs changes; Chief's own current F5 observations decide practical acceptance. Where widescreen fairness needs noncanonical changes, label them **PC quality-of-life adapters** rather than claiming byte-exact ROM behaviour.

Repositories:
- Public-safe reference and management: `jamesfarnhamlong/sonic-chaos-reference` (this repo).
- GameMaker POC: `jamesfarnhamlong/SonicChaos_POC`; current accepted project file `SonicChaos_A4B_EXPERIMENTAL.yyp`. **Check actual repository visibility/access before any binary upload**; do not assume private.
- ROM cache/source research may require Chief's local private assets; GitHub-only agents cannot access Chief's `E:\AI\Codex\Sonic Chaos` folders without a real local connection.

**Do not publish** the copyrighted ROM, extracted sprite/PCM/banks, private GameMaker ZIPs, user-supplied videos, passwords or other private payload to the public reference repository. A private repo does not by itself settle redistribution rights. This is a personal, noncommercial project; public release has not been commissioned.

## 2. Team — current, not historical

| Role | Responsibility |
| --- | --- |
| **Chief (owner)** | Sets priorities, performs the limited human F5 play checks, declares a candidate accepted, approves any cleanup/merge/distribution. |
| **Manager-san** | Maintains authoritative plan and acceptance state; reviews source evidence/commits; scopes single substantive batches and keeps full history accessible. |
| **Assistant Manager-san (AM-san)** | Side-project feasibility/enhancements advice: 60-FPS options, graphics presentation, Vita, broader ROM/slowdown research; may propose documented scope, not change POC unauthorised. |
| **One combined Research/Designer Codex agent** | Both ROM/source research **and** GameMaker implementation, verification, private package/integrity receipts in isolated branches; clearly separates ROM evidence, source-host tests and native F5 observations. |

**No active Janitor-san, Cloud-kun or separate Claude Research/Designer agent on this project.** Do not assign work to them or assume a cloud agent has local Windows/GameMaker access. The earlier Claude team now works on another project.

## 3. Accepted production checkpoint and current gate

**M6-H CHIEF F5 ACCEPTED — MGHZ-007 RESOLVED (2 Nov):** Chief's single ordinary MGHZ3 F5 on `SonicChaos_M6H_20261102_A_PRIVATE.zip` returned **"Yes, perfect! No notes, thats now working as intended."** Original spike3/4 right gate (no visible tree), boss/tree reveal, completed eight-spike arena and normal fight/progression accepted. [M6-H owner acceptance and evidence](docs/m6h-chief-acceptance-and-base-status-20261102.md). No further MGHZ3 work or recheck unless a fresh regression emerges.

**Source-publication caveat:** M6-H is **accepted as the private F5 candidate**, but the local M6-H branch `poc/m6h-mghz3-spike-gated-reveal` was **uncommitted and unpushed** at handover. The last **published, exact Chief-accepted Git source SHA** is still M6-G `6e2ffcc1f333c5cdaa0048ac696b55c4f6308905`. Designer must publish the identical M6-H source/evidence and supply its new full SHA and clean/remote parity before it becomes our immutable production source pointer. Do not confuse this bookkeeping gate with failed Chief acceptance; do not automatically merge main or rebuild.

**M6-F / R1 / M6-G — CHIEF ACCEPTED (2 Nov):** GPZ3 off-top recoverable rings, THZ2 triggered flying-bee identity, and THZ/GPZ ground patrol/SEZ hopper encounter retention all passed scoped owner F5. Preserve five-family targeted wide QoL retention, native GPZ `$25` sleeping callback progression and finite X/lifetime policy. SEZ `$20` hopper / `$23` leaper are left-moving, not bidirectional; Chief's visual overlap of two was not a demonstrated duplicate bug. [M6-G Chief acceptance](docs/m6g-chief-acceptance-20261102.md).

Previously Chief-accepted and **not to be routinely retested**: 25/25 known-use authentic SMS music using the default native driver (M5-G2), F2 Sound Test (63 playable originals + five empty; `$8E` no known retail requester), Sonic/Tails campaigns and five Special Stages in prior scoped runs, opening Robotnik foreground border (M6-C2), original rolling km/h panel and all developer keyboard shortcuts removed (M6-D), widescreen checker character choice (M6-E), GPZ3 rings and M6-F/R1/M6-G enemies.

Original speed-rating evidence: time **1:50 + 28 rings = 617 km/h**; do not substitute physical velocity. Continue audio had controlled proof but was not heard in Chief's sampled normal run. Preserve honest source/ROM/test boundary distinctions.

## 4. Active work and parked scopes

**NOW: base-finish phase — no currently confirmed mandatory implementation defect.** M6-H/MGHZ-007 is **closed by Chief F5**, not active. The only near-term agent operation is to **commit/push the exact accepted private M6-H diff and public-safe evidence without modification** and report an immutable SHA/receipt. Then Chief resumes the **one complete normal playthrough** and records only new concrete issues in a consolidated punch list. If none materially block the experience, Chief may approve a **private base freeze** (manifest/hash/source SHA, required assets and restoration/launch evidence). This is a release-readiness gate, not another speculative audit. See [base register](docs/CURRENT_BASE_GAME_REMAINING_20261101.md) and [M6-H receipt](docs/m6h-chief-acceptance-and-base-status-20261102.md).

**Parked, not base blockers:** first-start-only audio onset delay (measure before cosmetic cards); AQZ Tails underwater palette provisionally satisfactory; original attract/demo playback; optional save + emerald-progress unlock; historical contact/Spring Shoes/SS3 reports without current recreation; some SFX natural-event coverage and raw emulator/harness exceptions. The historic 93-ID AUDIT-0 archive and 21-ID owner triage are provenance, **not an active 93-bug queue**.

Only **after** the complete base playthrough and Chief's approval, consider AM-san's optional proposals on independent branches: 30→60 FPS *presentation* proof while retaining 30 gameplay Steps first (switching the Step rate outright changes timing/physics), sharp-bilinear/nearest pixel-friendly scaling, palette modes and high-res effects. True 60-Hz logic is a separate larger undertaking. Vita routes (modern YoYo Loader/native VitaSDK before GMS1.4 backport) are later feasibility, not active work.

## 5. Research + Designer workflow and expensive-test discipline

1. **Read** this file, `ROADMAP.md`, the current issue register, newest relevant accepted reports, then inspect *actual accepted commit and its parent*. Do not execute commands from historical dated “NEXT” banners.
2. For new production work, branch from the **latest immutable, Chief-accepted published source SHA** (after the pending M6-H publication); do not substitute an uncommitted candidate or newest no-code audit. Preserve its accepted private package until that publication is confirmed. Work in one isolated worktree; push the exact branch SHA with traceable manifests. Chief acceptance is not implied by a source PASS or Manager GO.
3. Combine related research and implementation into **one substantial batch**. Use cheap deterministic ROM/Z80 and shipped-GML source tests while developing; run broad adjacent regressions/integrity once the integrated work is stable. Rerun only a failing focused suite during correction. **One private source ZIP, one combined Chief F5 gate**, unless that candidate actually fails. Chief has stated builds/credits/checks are expensive.
4. Report which checks are source-only, synthetic/controlled original ROM, packaged GameMaker, or actual Chief-native F5. Never claim a full natural route from injected input/state. Preserve raw inherited FAIL statuses and explain superseded-policy expectations rather than repainting them green.
5. Keep original native256 parity as control; list any bounded **348 widescreen QoL** policy and its hard resource limits. Protect both characters, camera/goal/result transitions, native audio default, Pause→Level Select and removed shortcut policy.
6. Existing Codex Windows sandbox sometimes fails to create `Runner.exe` with error623 on Windows build26300, while Chief's ordinary GameMaker IDE F5 works. **Do not spend another cycle diagnosing sandbox loader permissions or claiming a code failure from it**; use Chief's single bundled F5 gate for the final experience.
7. No automatic POC main merge, public binary upload, cleanup, repo-visibility change or “release ready” declaration. Obtain Chief's explicit decision.

## 6. Workspace safety and eventual archiving

**Operational archive plan:** [inventory-first workspace archiving](docs/WORKSPACE_ARCHIVE_STRATEGY.md). This is a future proposal, NOT deletion permission.



Chief reports roughly **170 working folders** again. Janitor-san is no longer assigned. **Do not delete, move, compress or deregister any local worktree yet.** At base freeze, commission one new **inventory-first archiving plan**, not an improvised cleanup:

- Inventory paths and sizes, `git worktree list --porcelain`, repository/branch/head, working-tree dirty/untracked states, included/excluded original assets, ZIP receipts and hashes. Identify named canonical candidate, research proof, useful unmerged edits, reproducible generated files, caches, and redundant copies.
- Build a **dry-run classification manifest** with proposed keep/archive/regenerate/discard actions; retain a verified private final source checkpoint and independent backup (GitHub alone is not a backup), plus restore/open test.
- Only after Chief approves the manifest and restore proof may an authorised local cleanup agent execute minimal safe worktree pruning/archiving. Avoid Windows Explorer moves of registered Git worktrees and blanket `git clean -fdx`; never remove unknown dirty folders or private assets.

## 7. Reference links and document ownership

- [Live roadmap](ROADMAP.md), [short manager memory](MEMORY.md), [current base-game register](docs/CURRENT_BASE_GAME_REMAINING_20261101.md).
- [M6-H Chief acceptance / base closeout](docs/m6h-chief-acceptance-and-base-status-20261102.md), [M6-G Chief acceptance](docs/m6g-chief-acceptance-20261102.md), [Manager source review](docs/m6g-manager-review-chief-f5-gate-20261102.md), [original all-family directive](docs/m6g-regular-enemy-persistence-chief-directive-20261102.md), [R1 historical review](docs/m6fr1-manager-review-chief-gate-20261102.md).
- [AUDIT-0 93-ID historical register](docs/audit0/README.md), [Chief's 21-ID triage](docs/chief-current-issue-triage-20261101.md), [pre-rewrite root history](docs/archive/management/MANAGER_PRE_REWRITE_20261102.md).

**Manager controls this file.** After each Chief milestone result, **edit relevant statuses in place**, update ROADMAP/MEMORY and link a dated evidence receipt. Do not append another cascade of “CURRENT” blocks. Previous Managers' full notes remain accessible via Git history.
