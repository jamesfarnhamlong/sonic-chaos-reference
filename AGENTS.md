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

**CURRENT CANDIDATE — Manager technical pre-review GO / Chief gameplay PENDING (3 Nov 2026):** Designer reports `SonicChaos_Production` committed locally at **`8b3b435`**, worktree clean; `releases/SonicChaos_Production_20261103_FINAL_CANDIDATE_SOURCE_PRIVATE.zip` **12.10 MB** and `releases/SonicChaos_Windows_20261103_FINAL_CANDIDATE_PRIVATE.zip` **5.93 MB**, with independent `releases/SonicChaos_Production_20261103_FINAL_CANDIDATE_RECEIPT.json`. Both are private local E: paths (not uploaded here). Windows archive is **unmodified ordinary GameMaker output**, with source project load, compilation, extraction, native request/queue/startup/cross-zone, Sound Test checks reported PASS. One original Z80 gameplay driver now handles F2, **all 68 ID entries** (63 playable, five deliberately empty); 26 old GMSound samples, old Notes and redundant B1/C10/G1B/M4 runtime implementations removed from the production game. **Five inherited raw verification failures remain documented, not repainted PASS.** No Chief listening/full playthrough yet and no public release approval. **Do not modify/rebuild this candidate after Chief starts testing** without recording new hashes and requesting fresh acceptance.

**Prior accepted gameplay protected:** M6-H spike3/4 boss/tree reveal Chief F5 PASS (2 Nov), committed implementation `c3e40a7a3d6c17be3e17d7c1eb729b2a705a3089`; Chief-tested $A7 spike audio correction committed as ancestor `8e9d22499dc910922bd788346bb35678b4a28494`. M6-F/R1/M6-G recoverable rings/enemy persistence; original 25 known-use tracks, native256 fidelity + 348-wide QoL, all five Special Stages, Sonic/Tails gameplay, opening black-bar layering, character choice, original $19 km/h results. New final audio consolidation claims no changes to accepted $A7 scripts; owner full natural campaign remains necessary to confirm integrated production candidate.

**Independent preservation before freeze:** Previous H: Git bundle includes `8e9d224`, but the new `8b3b435` commit is **reported local only**. Ensure source ZIP and exact `8b3b435` history are recoverable on independent H: (verified) before final freeze; do not substitute the old Candidate B snapshot. No main merge or public push without Chief approval.

**3 Nov Chief natural Tails campaign revealed new RELEASE BLOCKERS:** Complete Tails playthrough on final-candidate local `8b3b435` surfaced missing THZ3 spike SFX (requires automated **all real SFX requesters** ROM/PSG/PCM-to-GameMaker audit), fast/slippery Tails spin dash/roll and underwater movement, AQZ boss music overwritten by invincibility expiry, AQZ monitor smoke palette/placement. Chief accepted authentic MGHZ falling $24 hazard Spring Shoes ring loss and <48px/slow-player trigger as **provisionally expected**, not active fixes; identify object opportunistically. Pause during results remains temporary debug; final Robotnik vertical camera/input behavior check is lower priority. **Sonic complete campaign on same ZIP underway.** Engineer can audit read-only ROM vs actual production GML including exact Tails land+water input/state/8.8 motion and Sonic control; **do not mutate the Chief-running package** or issue microbuilds. Batch only proven changes after Sonic's list. [Full owner issue register](docs/tails-final-campaign-defect-triage-20261103.md).

**3 Nov Sonic complete:** Chief reports full Sonic campaign on unchanged `8b3b435` ZIP, no additional bugs, partial emerald run uneventful. AQZ TV destruction effects and AQZ boss-music overwritten when invincibility expires reproduced by both characters. Dedicated Tails dry/underwater movement audit is underway; THZ3 $A7 and full automated SFX requester audit remain open. Original `$189B` restore has `$D4A3` guard, not automatically identical to AQZ boss-active `$D44E`; test exact original sequence before deciding canon vs PC QoL. [Combined final-campaign triage](docs/tails-final-campaign-defect-triage-20261103.md). No third complete Sonic playthrough; one correction batch and focused new candidate acceptance.

**3 Nov final ROM physics/music verdict:** Source-level original-ROM audit reports tested Tails acceleration, friction, speed caps, spin-dash release **match**; excessive campaign roll speed not recreated so no speculative retune. **Real issues**: Tails flight cancellation missing terrain-probe flags (first mismatch tick2) and shared AQZ surface `$1E` wall projection (first mismatch tick61; velocity diverges next), fix with exact ROM correspondence and protect Sonic/256/348. **AQZ boss music overwrite by invincibility expiration confirmed original ROM and explicitly Chief-approved to KEEP: FT-08 CLOSED, do NOT patch.** Other open work: THZ3 moving spike missing SFX + all-SFX automated coverage, AQZ TV explosion palette/position. Both character full campaigns done. Source `8b3b435` and existing ZIPs unchanged; only integrated fixes after current investigations, one candidate and focused Chief acceptance. [Issue register](docs/tails-final-campaign-defect-triage-20261103.md).

## 4. Active work and parked scopes

**NOW:** Chief conducts **ONE normal complete Sonic playthrough and ONE complete Tails playthrough** on the exact 3 Nov Windows candidate, including ordinary music, audio triggers and normal Sound Test use. Record only substantial new defects in one short punch list. After Chief acceptance, tag/freeze exact commit/ZIP SHA-256 and backup; do not repeat old isolated checks. The 2–3-second first-ever audio startup delay remains a known observation and is not currently an assigned enhancement.

**PARKED after base freeze:** optional 60-FPS presentation pilot, rendering filters, enhanced palettes, attract demos, save/emerald progression, Vita investigation, ROM source accessibility and slowdown patch. Chief authorization required before implementation. Original AUDIT-0/old reports are history, not a live defect queue.

## 5. Research + Designer workflow and expensive-test discipline

1. **Read** this file, `ROADMAP.md`, the current issue register, newest relevant accepted reports, then inspect *actual accepted commit and its parent*. Do not execute commands from historical dated “NEXT” banners.
2. For new production work, branch from the **latest immutable, Chief-accepted published source SHA** (published M6-H implementation above); do not substitute an uncommitted candidate or newest no-code audit. Preserve its accepted private package until that publication is confirmed. Prefer the existing protected production worktree for scoped final-release changes; use a separate worktree only for approved experiments. Push the exact branch SHA with traceable manifests. Chief acceptance is not implied by a source PASS or Manager GO.
3. Combine related research and implementation into **one substantial batch**. Use cheap deterministic ROM/Z80 and shipped-GML source tests while developing; run broad adjacent regressions/integrity once the integrated work is stable. Rerun only a failing focused suite during correction. **One private source ZIP, one combined Chief F5 gate**, unless that candidate actually fails. Chief has stated builds/credits/checks are expensive.
4. Report which checks are source-only, synthetic/controlled original ROM, packaged GameMaker, or actual Chief-native F5. Never claim a full natural route from injected input/state. Preserve raw inherited FAIL statuses and explain superseded-policy expectations rather than repainting them green.
5. Keep original native256 parity as control; list any bounded **348 widescreen QoL** policy and its hard resource limits. Protect both characters, camera/goal/result transitions, native audio default, Pause→Level Select and removed shortcut policy.
6. Existing Codex Windows sandbox sometimes fails to create `Runner.exe` with error623 on Windows build26300, while Chief's ordinary GameMaker IDE F5 works. **Do not spend another cycle diagnosing sandbox loader permissions or claiming a code failure from it**; use Chief's single bundled F5 gate for the final experience.
7. No automatic POC main merge, public binary upload, cleanup, repo-visibility change or “release ready” declaration. Obtain Chief's explicit decision.

## 6. Workspace hygiene — CLOSED 3 Nov 2026

**Bulk cleanup:** 112,534,500,297 bytes removed, 856 targets + 89 Git worktrees; five safe-skipped and two partial targets logged. Original ROMs, accepted packages and independent H: backups intact.

**Root housekeeping:** Additional **19.69 GB**, **357,603 files**, **182,980 directories** removed; **49 more registered worktrees** and **11 old snapshot/build directories** retired. Root reduced from **74 folders + 11 loose files to 12 folders + one current `AGENTS.md`**. Fifty-two historical management files moved into **one H: SHA-256-verified archive**, old root instructions replaced, accepted package hashes preserved, four Git stores integrity-PASS; `SonicChaos_Production` not modified by housekeeping. A1L golden PSG DLL and M4 tooling reference are **two deliberate non-production-support exceptions**: do not blindly delete while tools depend on them. No further cleanup sweep assigned.

**Root policy:** Keep only active production, necessary Git/research/private originals, accepted releases and active instructions. Historical tracked source lives in Git and unique private material in H:. Do not create permanent milestone worktrees or restore obsolete loose documents. Final audio code/asset removal was done *inside production* by the separately accepted Designer task; cleanup processes did not touch it.

## 7. Reference links and document ownership

- [Live roadmap](ROADMAP.md), [short manager memory](MEMORY.md), [current base-game register](docs/CURRENT_BASE_GAME_REMAINING_20261101.md).
- [M6-H Chief acceptance / base closeout](docs/m6h-chief-acceptance-and-base-status-20261102.md), [M6-G Chief acceptance](docs/m6g-chief-acceptance-20261102.md), [Manager source review](docs/m6g-manager-review-chief-f5-gate-20261102.md), [original all-family directive](docs/m6g-regular-enemy-persistence-chief-directive-20261102.md), [R1 historical review](docs/m6fr1-manager-review-chief-gate-20261102.md).
- [AUDIT-0 93-ID historical register](docs/audit0/README.md), [Chief's 21-ID triage](docs/chief-current-issue-triage-20261101.md), [pre-rewrite root history](docs/archive/management/MANAGER_PRE_REWRITE_20261102.md).

**Manager controls this file.** After each Chief milestone result, **edit relevant statuses in place**, update ROADMAP/MEMORY and link a dated evidence receipt. Do not append another cascade of “CURRENT” blocks. Previous Managers' full notes remain accessible via Git history.
