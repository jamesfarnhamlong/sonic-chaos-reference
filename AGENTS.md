# Sonic Chaos — AGENTS.md
**Working instructions · revised 2 November 2026 · Manager-san #8**

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

**Last Chief-accepted playable source:** `SonicChaos_POC:poc/m6g-all-enemy-persistence@6e2ffcc1f333c5cdaa0048ac696b55c4f6308905` (**M6-G Chief F5 PASS**, all three THZ/GPZ/SEZ patrol/hopper routes). Direct child of accepted R1; previous GPZ3 ring and THZ2 flying-bee acceptance retained. No automatic main merge.

**M6-F / R1 / M6-G — CHIEF ACCEPTED (2 Nov):** GPZ3 off-top recoverable rings, THZ2 triggered flying-bee identity, and now THZ/GPZ ground patrol and SEZ hopper encounter retention all passed the scoped Chief F5 checks. M6-G `6e2ffcc1f333c5cdaa0048ac696b55c4f6308905` is the production baseline. Preserve five-family targeted wide QoL retention, original native GPZ `$25` sleeping callback progression and finite X/lifetime policy; do not assert that every original-ROM sleeping/transition trace is exact. SEZ `$20` hopper and `$23` leaper are **left-moving, not bidirectional patrols**; Chief saw two visually overlapping, but no duplicate-token defect was established. [M6-G Chief acceptance](docs/m6g-chief-acceptance-20261102.md).

Previously Chief-accepted and **not to be routinely retested**: complete known-use native SMS music at default backend (M5-G2), playable F2 Sound Test catalogue, complete Sonic/Tails campaigns and five Special Stages in their accepted scope, original opening Robotnik foreground border (M6-C2), rolling goal km/h panel and **all developer keyboard shortcut removal** while preserving Pause→Level Select (M6-D), and widescreen character-choice background (M6-E).

The original speed-rating example **time 1:50 + 28 rings = 617 km/h** is proven; do not replace original scoring with actual physical speed. Sound Test is **63 playable original programmes + 5 originally empty entries**; `$8E` has no known retail requester. Continue request has controlled proof but was not heard in Chief's run; don't relabel that as a gameplay fail.

## 4. Active work and parked scopes

**Active right now:** **Chief's complete normal base-game playthrough on accepted M6-G**, before optional 60-FPS/graphics changes and Vita. Record any concrete visible issues as one consolidated punch list; fix only proven impactful regressions in coherent batches. No obligatory reruns of accepted rings, bees, regular enemy patrol checks, audio, frontend or Special Stages. Inherited raw verifier FAILs remain documented (viewport all-width384, M6-G wide-SEZ delete assumption); original THZ `$21` falling-while-asleep adapter discrepancy and GPZ below-map placement remain known technical limits, not new reported defects. After the playthrough, Chief explicitly decides base freeze, optional final polish and safe archiving. Attract/demo and save/emerald progression remain parked post-base.

**Explicitly parked / not blockers unless Chief promotes them:** MGHZ3 boss approach works but wide camera presentation looks messy; first-start-only audio onset delay (do not add fake waiting cards without evidence); AQZ Tails underwater palette provisionally satisfactory; original attract/demo playback; optional save + emerald-progress unlock in Level Select; old contact/Spring Shoes/SS3 reports lacking a currently reproducible route. Older 93-ID AUDIT-0 and 21-ID Chief triage are history and priority evidence, **not an active 93-bug ticket queue**.

After base playthrough, AM-san's suggested optional enhancements can be considered in a separate branch: **30→60 FPS proof** (current Step-based game-speed option is 30; blindly switching to 60 changes physics/timers), display interpolation at60 while maintaining canonical gameplay ticks first, sharp-bilinear/nearest optional scaling around unchanged pixel art, palette modes and high-resolution effects. True 60-Hz logic is a separate larger undertaking. Vita investigation comes **after** stabilization; evaluate contemporary YoYo Loader/native VitaSDK routes before legacy GMS1.4 backport. None is authorised implementation today.

## 5. Research + Designer workflow and expensive-test discipline

1. **Read** this file, `ROADMAP.md`, the current issue register, newest relevant accepted reports, then inspect *actual accepted commit and its parent*. Do not execute commands from historical dated “NEXT” banners.
2. For new production work, branch directly from the **latest Chief-accepted SHA**, not the newest no-code audit or an unaccepted candidate. Work in one isolated worktree; push the exact branch SHA with traceable manifests. Chief acceptance is not implied by a source PASS or Manager GO.
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
- [M6-G Chief acceptance](docs/m6g-chief-acceptance-20261102.md), [Manager source review](docs/m6g-manager-review-chief-f5-gate-20261102.md), [original all-family directive](docs/m6g-regular-enemy-persistence-chief-directive-20261102.md), [R1 historical review](docs/m6fr1-manager-review-chief-gate-20261102.md).
- [AUDIT-0 93-ID historical register](docs/audit0/README.md), [Chief's 21-ID triage](docs/chief-current-issue-triage-20261101.md), [pre-rewrite root history](docs/archive/management/MANAGER_PRE_REWRITE_20261102.md).

**Manager controls this file.** After each Chief milestone result, **edit relevant statuses in place**, update ROADMAP/MEMORY and link a dated evidence receipt. Do not append another cascade of “CURRENT” blocks. Previous Managers' full notes remain accessible via Git history.
