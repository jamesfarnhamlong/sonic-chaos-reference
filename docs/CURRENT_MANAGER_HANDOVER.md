# Sonic Chaos — LIVE MANAGER HANDOVER
**Updated 6 November 2026 · Manager-san #11 · S3 final Chief acceptance / next sprint discussion**

> **START HERE if a management chat is lost.** This stable-path handover is intended for incoming Manager-san. Read this, then root `AGENTS.md` (rules), `ROADMAP.md` (milestones), `MEMORY.md` (context) and the linked milestone reports. Most dated historical "NOW/NEXT" paragraphs are superseded; **S3 is Chief-accepted and the next task is milestone planning only**. Do not resurrect old work orders.

## Current decision, owner next action

**S3 — FINAL CHIEF ACCEPTED AND CLOSED ON 6 NOVEMBER 2026.** Chief reported after testing integrated R2: “Yes, thats all good - all passes. Nothing to add for now, all seems functional!” This is an explicit owner PASS of final visuals, native GG `$9B` soundtrack, BOSS RUSH CLEAR results and game flow. Earlier two full natural wins established underlying original S3/S3-R1 boss/level mechanics. There are **no presently outstanding S3 defects**; no further Chief test or Designer correction requested. [S3 final acceptance receipt](S3_CHIEF_FINAL_ACCEPTANCE_20261106.md).

**NOW — HOUSEKEEPING AND NEXT FEATURE DESIGN DISCUSSION ONLY.** Chief asks whether anything needs pushing to Git before beginning the next enhancement. GitHub confirms `jamesfarnhamlong/SonicChaos_POC` is private; `enhancement/s3-r2-visual-audio-results-20261106` and shortened commit `29044ca` were **not found on the remote**. Designer has reported local clean commit plus validated H: recovery. Before future source changes verify full R2 SHA/tree/ZIP and independent E:/H: recovery locally; do **not** assume remote push occurred or that local data was lost. Optional push to private feature branch, fresh tag or main merge needs explicit Chief decision and prior private-asset/secret checks; public reference must contain only public-safe docs. No next Designer implementation sprint commissioned; discuss six-item S2 Data Select presentation polish vs display/CRT/fullscreen and agree scope first.

**CLOSED MILESTONE:** Original Classic immutable `classic-core-20261105`, Enhanced S1/S2 accepted, S3-R2 Boss Rush accepted. Preserve current exact S3-R2 Windows/source/receipt H: evidence. Next Manager should read `AGENTS.md`, `ROADMAP.md`, `MEMORY.md`, and this receipt before any new instructions.

## Production/package provenance — private E:/H: only
- Public-safe management repo: `jamesfarnhamlong/sonic-chaos-reference`; private GameMaker production project: `SonicChaos_Production/SonicChaos.yyp`. Connected GitHub reference is documentation, **not** a guarantee of access to local private source or packages.
- Immutable original Classic tag: `classic-core-20261105` → `3a58912659b48573ac7f2c5c96a02a2211d5e4da`. Preserve it and its private backups.
- Accepted Enhanced S2 base source `0809ef9cbc9ea9c1fda3bc0ead45aa9aa749a5a7`; accepted R1 functional source `8b5086c68d748c7a53731034531f7d07efc93427`. S3 original source `7a6a4b714171cadcfd9f9efb77763f31f8ac5885`.
- **R2:** branch `enhancement/s3-r2-visual-audio-results-20261106`; Designer-reported abbreviated commit `29044ca`; **full candidate commit/tree must be obtained from private delivery receipt before any freeze/merge**. Manager has not independently opened the E:/H: binaries, ZIP hashes, separate linked screenshots or WAV evidence.
- R2 Windows: `E:\AI\Codex\Sonic Chaos\releases\SonicChaos_Windows_20261106_S3_R2_BOSS_RUSH_CANDIDATE_PRIVATE.zip`
- R2 complete source: `E:\AI\Codex\Sonic Chaos\releases\SonicChaos_Production_20261106_S3_R2_BOSS_RUSH_SOURCE_PRIVATE.zip`
- R2 report: `E:\AI\Codex\Sonic Chaos\SonicChaos_Production\docs\production\S3_R2_BOSS_RUSH_20261106.md` (Chief separately uploaded text to current management conversation).
- R2 hashes: `E:\AI\Codex\Sonic Chaos\releases\SonicChaos_20261106_S3_R2_BOSS_RUSH_SHA256.txt`
- R2 audio A/B: `E:\AI\Codex\Sonic Chaos\SonicChaos_Production\docs\production\s3-r2-native\9B-reference-then-native.wav`. H: independent recoverability and accepted E:/H: package preservation **reported by Designer**.

## R2 delivered corrections — source-report facts, not Chief F5
1. Invisible opening surface23 swirly platform now draws **continuous MGHZ grey/white ribbon**; **56 original curve base/front alpha masks** match; movement/collision unchanged.
2. GPZ rings retained at **3 existing authored rings in each first-four connector**, offset to terrain-relative Y−28; under original strict 12px pickup radius and checked collectible by Sonic/Tails. Entry three rings unchanged; **no newly placed final AQZ→EEZ rings**. Original GPZ structural pipe textures/transparency restored against EEZ background.
3. Six SEZ crumble platforms still use authentic `$AF` → `$B0`, original `$13` timing/effect/fall/sound, but now **visible original EEZ mechanical block175** and matching fragments.
4. Green MGHZ boss-looking patch diagnosed as grass/palette overlay atlas cells 210/211, **not boss sprite pixels**; those challenge-only decoration cells omitted, controlled green pixels drop **2,628→0**. MGHZ boss-supporting tree/reveal intact.
5. Boss Rush-only invincibility monitor placement filter removes all, including retained GPZ parameter6. THZ parameter1 ring monitor remains; original shared monitors/campaign stages untouched.
6. BOSS RUSH CLEAR snapshots **TIME, RINGS, LIVES remaining** once at `chaos_ending_open`; session-only/nonpersistent; START restart and B/ESC title unchanged. Controlled sample Sonic **2:00/37/2**, Tails **9:00/0/1**, at 348/290/256. No score, records or leaderboard.
7. **Genuine unused Game Gear programme `$9B`** integrated via a fixed 4KB challenge-only supplement in Z80 context RAM `$C000–$CFFF`, new native-host installer and altered challenge-context `$9B` pointer. **Original SMS Z80 driver instructions/song data, CPU/PSG implementation and shared PCM queue unchanged**; normal gameplay contexts do not install it. Host DLL from `experiments/m5-g1d/bridge.c` extended, but no OGG runtime dependency, no alternate playback engine. Challenge background `$9B`, ordinary boss1–5 `$8C`, final EEZ `$8B`, death `$96`, game over `$87`, normal title/character choice. No inter-boss `$97` jingle or invincibility `$84` music interruption.

## R2 verification/limitations
Designer reports:
- Original GG CPU vs native **12,000** updates identical ordered PSG (loop period **2,304 updates / 38.4 seconds at 60Hz**); ordinary SMS **68 programme/SFX contexts × 32,640 updates** identical CPU/RAM/PSG accepted vs extended host; **742 actual GameMaker PCM blocks** exact against golden original PSG replay.
- Chief reference OGG is **86.6275s**; best ten-second pitch-class similarity **0.95975**, which is supporting song identity, **not** proof of identical recording mix or pitch.
- **684** compiled player/boss/camera samples equal R1, **25** native handoffs, **10** controlled original-input approaches, dual-character EEZ terminal chains, **178** focused source checks + **2,918** campaign checks, and unchanged **5,693** protected original files.
- Real campaign saves and ten populated disposable native generation files remain byte-identical during probes; standard uninstrumented Windows export/smoke PASS. Historical U5-A whole-core `shoes@256 u1` remains **inherited FAIL**, not newly passing.
- The compiled-game checks are controlled, **not** a third natural Chief full-course completion. Real-time listening and full R2 visuals remain Chief's judgment.

## Guardrails and manager workflow
- Protect original Classic, ordinary Enhanced S1/S2, save slots/Emerald ownership, authentic boss routines, camera locks, loops, native Z80 sound and original 256x192 reference vs 348x196 Wide (plus 290x218 Retro), all accepted archives/H: backups.
- Private ROM/audio/art binaries, exact screenshots and source ZIPs **must not be pushed to public reference**. No assumptions that external/cloud agents can read Chief's E:/H:.
- One substantial integrated Designer sprint per approved feature, with internal deterministic tests and one Chief-facing Windows candidate / acceptance gate. Do not commission repeated tiny builds or ask Chief for redundant whole-character campaigns.
- Old project caveats remain: historical raw verifier failures must be reported honestly; no public release/port/repo-visibility changes without explicit consent.
- **When Chief accepts S3:** update this file, root `AGENTS.md`, `ROADMAP.md`, `MEMORY.md`, S3 acceptance log and archival hash/commit status. Future scoring/best-time records are deferred, not implicitly included.

## Parked future work (not commissioned)
- S2 Data Select **six-item visual batch:** Tails odd yellow head, looping authentic running Sonic/Tails with matching floor anchors, animated TV static, improved zone thumbnails, vibrant Emeralds, consistent sprite proportions/TV clearance. See `docs/tracking/S2_DATA_SELECT_VISUAL_POLISH.md`.
- Endgame frontend/display polish: shared window/fullscreen settings, Sharp/Integer/CRT final defaults, richer CRT, remove release-facing Pause→Level Select; original idle attract/demo and GPZ3 Classic art seam deferred.
- Potential score / beat-last-time / rings-time-lives challenge records, optional ring-scatter QoL, frame pacing/60fps presentation research; AM-san parked Vita port, ROM-accessible disassembly, slowdown patch, other ports. See ROADMAP and project issue registers.

## Documentation entry points
- `AGENTS.md` — binding development rules / current team.
- `ROADMAP.md` — accepted and pending milestones.
- `MEMORY.md` — concise handover, history/links.
- `docs/S3_R2_VISUAL_AUDIO_RESULTS_CORRECTIONS_20261106.md` — Chief-approved R2 design spec.
- `docs/S3_R1_MANAGER_TECHNICAL_REVIEW_20261106.md`, `docs/S3_R1_CHIEF_MAP_AND_POLISH_CORRECTIONS_20261106.md` — earlier S3 stage evidence/decisions.
- `docs/S2_CHIEF_ACCEPTANCE_20261105.md` — last functionally accepted Enhanced save system.
- Detailed private Designer delivery: `S3_R2_BOSS_RUSH_20261106.md` in private E: production workspace.
