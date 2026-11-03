# Sonic Chaos — Manager handover / current facts
**Updated 3 November 2026 · Manager-san #9**

See [AGENTS.md](AGENTS.md) for operating rules, [ROADMAP.md](ROADMAP.md) for live status, [production quality and cleanup receipts](docs/sonic-chaos-final-packaging-and-deletion-plan-20261102.md), and [owner issue ledger](docs/CURRENT_BASE_GAME_REMAINING_20261101.md). Older historical management content is recoverable in Git history/H:.

## CURRENT — Both full campaigns complete, corrections pending

**3 Nov:** Sonic full natural playthrough COMPLETE on unchanged `8b3b435` Windows ZIP; no additional defects, partial emerald run also uneventful. Tails full campaign complete earlier with new physics/audio/presentation findings. Both Sonic/Tails repro AQZ TV explosion bad palette and raised animation, plus AQZ boss $8C replaced by zone $93 on invincibility expiration. **NOT YET FROZEN.** Tails full dry/underwater ROM input/velocity audit underway; THZ3 missing moving-spike SFX requires automated full SFX requester review. Canonical boss-music question unresolved: ROM $189B zone restore guard $D4A3 and boss-active $D44E are distinct. [New authoritative issue register](docs/tails-final-campaign-defect-triage-20261103.md). One consolidated correction package then limited targeted human acceptance; no routine third Sonic full run.

## PREVIOUS — final owner test planning

- **Final private candidate prepared by Designer; committed locally `8b3b435`, clean worktree.** `E:\AI\Codex\Sonic Chaos\releases\SonicChaos_Production_20261103_FINAL_CANDIDATE_SOURCE_PRIVATE.zip` (12.10 MB), `SonicChaos_Windows_20261103_FINAL_CANDIDATE_PRIVATE.zip` (5.93 MB), `SonicChaos_Production_20261103_FINAL_CANDIDATE_RECEIPT.json` (dependency manifest/checksums). GameMaker standard Windows output unmodified.
- **One authentic gameplay Z80 sound engine now serves gameplay AND F2 Sound Test.** Driver matched 408,000 independent ROM-source ticks for all 68 IDs previously; new integrated native catalogue/UI, queue, startup and cross-zone checks PASS per Designer. All 63 playable and five intentionally empty entries remain; obsolete B1/C10/G1B/M4 production playback, all 26 sample/GMSound assets and obsolete Notes retired; all registered resource paths and source ZIP opening/Windows extraction/compilation checks PASS. **Five inherited raw verifier failures remain recorded.** This is an automated preflight pass; **Chief has not yet completed real natural full Sonic/Tails test or human listening.**
- **Next:** Chief uses the exact Nov 3 Windows ZIP for **one Sonic and one Tails full run**. Collect substantive issues in one list. If PASS, Chief may authorize a private base freeze/tag with exact ZIP hashes, clean commit, verified independent H: source/commit recovery. The new local `8b3b435` has not been confirmed backed up to H: or pushed, unlike ancestor `8e9d224`; verify independent recovery before declaring freeze. No further packaging after Chief testing without a new acceptance candidate.

## ACCEPTED AND PROTECTED

- M6-H spike-gated MGHZ3 reveal Chief F5 PASS 2 Nov; game source commit `c3e40a7a3d6c17be3e17d7c1eb729b2a705a3089`. Source camera lock just before spike4, then boss/tree reveal through spike8.
- Chief-tested $A7 distant-spike sound lifecycle correction accepted from live `SonicChaos_Production/SonicChaos.yyp`; committed `8e9d22499dc910922bd788346bb35678b4a28494`.
- M6-F/G offscreen rings/enemy retention accepted; M6-C opening layering; M6-D original $19 km/h, no developer shortcuts; M6-E 348-wide checker; Special Stages 1–5, 25 known-use music routes, native256 fidelity and 348-wide presentation. Prior acceptance was scoped; no full natural campaign run of latest Nov 3 candidate yet.

## WORKSPACE CLEANUP — BOTH JOBS CLOSED

- Bulk E: cleanup: **112.53 GB** removed, 856 deleted, 89 worktrees retired; five safe-skips and two partial targets logged. Original ROM and accepted package hashes, Git integrity and independent H: recovery of ancestor `8e9d224` PASS.
- Root housekeeping: **19.69 GB additional** removed; 49 more worktrees + 11 old snapshot/build directories retired; 357,603 files / 182,980 dirs removed. **74 top-level folders + 11 loose files → 12 folders + one concise root `AGENTS.md`**. Fifty-two old Manager docs preserved in one SHA-256-verified H: archive. Accepted ZIPs unchanged, four Git stores integrity PASS, active production untouched by housekeeping.
- Exceptions **A1L golden PSG verification DLL** and **M4 separate tooling reference** remain *outside the production game* until their supporting tooling dependencies are retired. Do not launch another cleanup campaign or disturb active canonical source.

## PARKED / HONEST LIMITS

- First-ever launch audio may lag ~2–3 s, repeated launches normal; cause not established, no card/timing change authorized. AQZ Tails palette provisionally fine. Attract demos, save/emerald progression, graphics polish, 60 FPS research and Vita port parked until Chief approves post-freeze pilots.
- Preserve five inherited raw failures; distinguish original-ROM trace/source-host/unit/runtime checks from normal human gameplay, do not mark them all green.
- No automatic main merge, public release, push of private assets, or enhancement development without Chief authority. Public GitHub documentation is not equivalent to local private source assets; H: backs up unique private material.
