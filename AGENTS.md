# Sonic Chaos — AGENTS.md

**Canonical coordination instructions | Manager-san #5 | 23 October 2026**
**Authority:** this file on Research repository `main`, together with [MEMORY.md](MEMORY.md), [ROADMAP.md](ROADMAP.md), and the exact research/POC commits named below. This is a management-document migration, **not** a GameMaker release or promotion of topic-branch research into Research `main`.

## Read first: authority and synchronization

1. Read `AGENTS.md`, `MEMORY.md`, `ROADMAP.md` **from this repository's `main` branch**, even when your own worktree predates their addition. Read the linked scoped Research contracts and accepted POC closure next.
2. The accepted **GameMaker POC baseline is `poc/q3-p1-world-presentation@7476affc6ed7626dabf69b446cdab0c9c3d7492e`**. Research `main` is historically at `b6467ba0ad79fad0937f750083a5261e7ea64e8f` before this management commit. Research topic-branch results are **not** merged into `main` by changing these documents.
3. When asked to check a hash, distinguish **SHA-256 of raw file bytes** from **Git commit SHA**, **Git blob SHA**, and a **historical candidate hash**. Renaming `AGENTS(...).md` to `AGENTS.md` alone changes none of its bytes; line endings, encoding or content updates do. Record source file, version, exact expected digest and bytes before alleging mismatch. Do not treat a historical archived SHA as the current expected SHA.
4. The 22-Oct uploaded Windows coordination file described itself as “CANDIDATE / NOT INSTALLED,” even though it was supplied as the user's then-current root copy. **That internal header was stale.** It is preserved separately as historical evidence, not installed here verbatim as active instructions.
5. Cloud agents **do not have Chief's Windows E: drive**, ignored private ROM/art/audio, local worktrees or archives unless made available in their environment. Do not claim to have inspected inaccessible paths. GitHub source, public numeric evidence and uploaded private inputs have different authority.
6. These documents may be updated by Manager with Chief's authorisation. Agents assigned runtime or research work must **not** independently rewrite canonical management files or promote topic branches. New accepted milestones should update root AGENTS/MEMORY/ROADMAP in a single documented management checkpoint.

## Mission and responsibilities

Build a **faithful 348×196 widescreen GameMaker adaptation of Master System Sonic Chaos (Europe v1.2)**. The private canonical ROM's SHA-256 is `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`. Use original ROM evidence; do not fabricate mechanics, mappings, placements, assets, timings, collisions, palette choices or audible parity. Treat original 256×192 as ROM comparison and 348×196 as the normal Chief/Windows acceptance mode. Record deliberate widened-camera adaptations.

| Role | Responsibility / permission |
|---|---|
| **Chief (human)** | Selects priorities, reports Windows F5 findings, gives explicit candidate and milestone approval. No agent can self-accept human gameplay. |
| **Manager-san** | Owns scope, authority docs, fidelity findings, cross-agent consistency, acceptance and release decisions. |
| **Research-kun** | Original-code/ROM/cached evidence, natural reachability, complete behavioural contracts, source provenance, focused tests. Works only in authorised Research topic branch. |
| **Designer-san** | GameMaker implementation, private source-only packages, restoration and tests. Works in isolated POC worktree, **uncommitted/unpushed until Chief approval**. |
| **Assistant Manager-san** | Parked PS Vita/YoYo Loader, source decomp/disassembly and SMS/GG slowdown patch. No POC scope changes without approval. |
| **Janitor-san** | Approved-only archive/worktree hygiene. Never discard unidentified local edits or move registered worktrees via file explorer. |

Do not build an executable unless separately requested. Private ROM, extracted game pixels, private WAVs, source packages and secrets do **not** belong in the Research public tree. Original image/video captures may be described by filename/hash/metadata instead of publishing the payload. Avoid needless full-suite recomputations: focused evidence + risk-based adjacent verifiers, with **raw inherited failure IDs retained**.

## Accepted game and current implementation gate

- **Sonic campaign:** Chief completed 18 natural acts, all Emeralds, good ending/credits/title at 348×196. Five Special Stages, core campaign/death/Continue and original opening have scoped acceptance. This is not frame-perfect or every-path parity.
- **Frozen POC:** Q3-P1 `7476affc6ed7626dabf69b446cdab0c9c3d7492e` is the next implementation parent; Q2/Q3 camera/world/fragment corrections are accepted. Private Q3 FINAL ZIP reported SHA-256 `b409be469f27e8b6270c510281dc601f04b471c8d3432f47ebe639e10e43c859` (not independently opened by Manager).
- **M0/M1 Research:** `5b7f5a10232f4f6511c3a7b9d9b4deaea5842182` accepted as planning/contract checkpoint.
- **M2-R1 Research:** `d6f2fafcda7903c0fc7082b2a9cbf4fed6e0bf98` confirms Tails state $20 side-contact selection of frame $5E follows invalid mapping pointer $0785; forced ROM code corrupts rendering, **natural reachability UNRESOLVED**.
- **M2-R2 Research:** `cd417c16b9e4ae614a3592f5b851a351af786afa` confirms Tails Rocket monitor **becomes Ring monitor before art selection and awards +10 rings**; life-monitor portraits select character; Spring Shoes work for both. Source-model evidence is not native Windows or complete natural coverage.
- **M2 private Windows Package B** (23-Oct) is **NOT accepted for commit**. Chief passed six *targeted* retests: Shift+T act fixture, AQZ movement/water, Rocket→Ring, Spring Shoes, jump feel, Continue. The newly reported dark AQZ Tails silhouette is now a **confirmed source-level decoder-routing defect**; selected spear-like contact misses are still **OPEN Windows observations**. Both were reported by Chief; neither B nor accepted Q3 is approved for commit/change here.
- **M2-R3 AQZ Research: ACCEPTED for its bounded evidence**, `research/m2r3-aqz-palette-hazards@33c4c13ebeadb54834c8cddd5bafedaae5e13015`, one child of M2-R1, remote 0/0. Against the **actual private Package B**, 176 indexed Tails textures matched canonical art; `chaos_aqz_player_draw` incorrectly routes RGB-indexed Tails pixels to Sonic's alpha-index decoder, leaving dark RGB encoding visible. Original type `$3C` spear object contacts and B matched in 22,528 controlled contact cases; no shared collision defect proven. Opening AQZ1 pair: (1104,686)/(1232,686). `$3C` object is not terrain block `$3C`. Windows contact/lifecycle timing is unresolved; do not invent a broad hitbox. **Manager authorised only one tightly scoped Package C palette decoder fix plus non-intrusive spear diagnostics**; F5 and full campaign acceptance still pending.
- **M2 frame $5E deliberate exception:** exactly Tails/type2 + state $20 + selected frame $5E: no draw/resource read; preserve numeric frame, timing and callback, log an append-only fidelity event. This is **not** ROM parity. Any *natural* trigger blocks final closure, regardless of whether the game continues. Package B natural event status **UNVERIFIED**: absence of a supplied log is NOT zero events.
- M2 Package B remains private, **unstaged, uncommitted, unpushed**, with parent Q3-P1. F5 tests and local package assertions are evidence, **not a commit authorisation**.
- Original title/character choice/attract and **in-game audio** remain unimplemented. Existing Sound Test's five authentic WAVs are previews, not a live soundtrack.

## Behavioural completeness: mandatory character-difference gate

**A negative eligibility statement is never the whole implementation contract.** The earlier “Tails cannot receive Rocket Shoes” finding omitted the canonical monitor **conversion, artwork and +10-ring substitute reward**, and both Research and Manager review missed it. For every character-dependent rule, Research must trace:

**ROM placement → character-dependent initialisation/conversion → displayed art/palette → contact/activation → actual reward/state → lifetime/cancellation → natural route and adjacent Sonic comparison.**

Mark each link **ROM gameplay proven / controlled only / static source / unresolved**. Designer supplies matching positive, negative and character-paired implementation controls. Manager cross-checks evidence, actual shipped behaviour and Windows checklist before sending a candidate. Do not dismiss Chief's observation using a narrow source statement; reproduce and reconcile it.

The same discipline applies to AQZ spike collisions, underwater palettes, Spring Shoes ownership, score and sign rewards, future audio triggers and project-wide contact/physics changes. A conditional branch, visually similar asset or passing high-level test does not prove full natural gameplay.

## Acceptance, tests and release discipline

1. **Preflight:** exact frozen parent, private ignored asset availability/restoration, scoped Research contract, impacted owner and known exceptions.
2. **Implementation:** one meaningful themed package. No speculative physics/gravity/ring/spike hitbox tweaks, cloned state ownership, arbitrary art substitutions or silent fallback. Preserve Sonic and previously accepted routes.
3. **Verification:** source/ROM code and shipped GML execution clearly distinguished from actual native F5. Include representative natural-positive/negative cases and paired Sonic/Tails regressions. Preserve test failures honestly: SS5 256-width camera-X (max 2 px), obsolete THZ3 camera-cap; Package B also retains U5-A historical whole-core comparison mismatch. Historical GPZ sprite-ID/MGHZ timeout not universally rerun.
4. **Windows:** Chief tests brief initial fixture before long campaign; a natural 18-act Tails run, complete ending/title and append-only run log still required for M2 final scoped campaign acceptance.
5. **Closure:** only after explicit Chief/Manager approval, a single direct-child POC commit and push, exact remote 0/0/clean, source-only private FINAL archive with hash, payload proof and fresh-clone idempotent restoration. No automatic merge to POC or Research main from agent topic work.
6. **Management:** update root AGENTS/MEMORY/ROADMAP after accepted changes. Preserve older versions in Git history and archive receipts, not competing current copies named AGENTS.md.

## Other open and parked items

Keep accepted Q3 features frozen. Retain **historical visible spring/Badnik oscillation**, slope sticking, SS3 monitor embed, unidentified “SLZ1” priority, MGHZ3 pit/tree reveal, unsettled sign centering, non-SEZ/AQZ/SS4 fragment owners, spike width/phase, state-$20 lag, and other findings as OPEN/KNOWN-ADAPTER until source-backed evidence changes them. **Do not convert every human observation into a confirmed engine-wide bug, nor call it canonically intended without comparing the specific route.**

**Audio:** 70 original sound request IDs; five approved Sound Test samples. M4 dispatcher pilot then M5 full authentic music/SFX/stop/pause/restore is required for original-game completion. No fake loops or claimed PSG parity.

**Future:** M3 authentic title and character choice only after Tails acceptance; M6 other original fidelity/attract/content; M7 optional PC QoL/release; M8 extras/ports parked. Follow [ROADMAP.md](ROADMAP.md).

## Evidence links

- [Frozen Q3 POC](https://github.com/jamesfarnhamlong/SonicChaos_POC/commit/7476affc6ed7626dabf69b446cdab0c9c3d7492e) and [Q3 closure](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/7476affc6ed7626dabf69b446cdab0c9c3d7492e/docs/q3p1-closure.md).
- [M0/M1 planning and contracts](https://github.com/jamesfarnhamlong/sonic-chaos-reference/tree/5b7f5a10232f4f6511c3a7b9d9b4deaea5842182/planning) (later [M2-R1 Fidelity Register](https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/d6f2fafcda7903c0fc7082b2a9cbf4fed6e0bf98/planning/FIDELITY_REGISTER.md)).
- [M2-R2 full character interaction matrix](https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/cd417c16b9e4ae614a3592f5b851a351af786afa/docs/m2r2-character-interaction-matrix.md).
- [M2-R1 frame $5E evidence](https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/d6f2fafcda7903c0fc7082b2a9cbf4fed6e0bf98/docs/m2r1-tails-act-clear-frame5e.md).
- [AQZ waterline palette research](https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/d6f2fafcda7903c0fc7082b2a9cbf4fed6e0bf98/docs/aqz-water-environment-audit.md); [spike collision study](https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/d6f2fafcda7903c0fc7082b2a9cbf4fed6e0bf98/docs/platform-spike-collision-audit.md).
- [Historical installed AGENTS text snapshot](archive/management/AGENTS_20261023_WINDOWS_UPLOAD.md); [archive inventory and SHA-256](archive/management/AGENTS_BACKUP_MANIFEST_20261023.md).

This management file intentionally stays concise. Detailed historical chronology belongs in linked closure reports and archives, not repeated as active instructions.
