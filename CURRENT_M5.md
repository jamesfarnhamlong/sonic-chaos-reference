# Sonic Chaos — M5 Audio Milestone: CLOSED HISTORICAL SUMMARY
**Updated 2 November 2026 · NOT a live task controller**

**M5-G2 authentic known-use soundtrack was Chief accepted on 1 November 2026.** The GameMaker project has since advanced through Chief-accepted M6-C2, M6-D, M6-E and M6-F-R1 (GPZ3 recoverable rings and THZ2 bee continuity). New **M6-G** all-family enemy persistence is active, independent of closed M5 audio. For current instructions, use [AGENTS.md](AGENTS.md), [ROADMAP.md](ROADMAP.md), [MEMORY.md](MEMORY.md) and [current base-game register](docs/CURRENT_BASE_GAME_REMAINING_20261101.md). **All past M5 “NEXT,” “GO,” “HOLD,” “music missing” and “F5 pending” blocks are superseded.**

## Accepted historical milestone

- G2 source branch: `SonicChaos_POC:poc/m5-g2-complete-audio-default@91fd74b56296bb9182768c3a9db78a186fa78f9e`. Main not auto-merged. Public safe reference [G2 Chief acceptance](docs/m5-g2-chief-acceptance-20261101.md), [G2 original rollout directive](docs/m5-final-audio-rollout-manager8-20261030.md).
- Native Z80 original-driver audio is GameMaker's ordinary default; no hand-editing `g1d_backend.txt`. The 25 music programmes with supported retail uses were routed and accepted in Chief's F5, across zones/bosses/ending as scoped.
- Original music/test ledger has 70 request IDs and 193 request-site contexts; 26 playable music headers (one, `$8E`, without known gameplay requester), 37 SFX, 2 control requests, 5 genuinely empty music headers `$9B–$9F`. F2 Sound Test retains 68 catalogue rows, **63 playable / 5 empty**, not 68 audible programmes.
- Original fading/priority/boss-clear audio and native engine lifecycle tested. Designer's G2 reported 97,233 exact PCM-generating native ticks /71,466,255 samples; Chief confirmed the targeted main-gameplay listen-through and original powerup cues. Do not equate artificial driver tests with 18-act natural playback for all sound events.

## Remaining technical exceptions, not an open soundtrack task

- Continue `$94`: controlled proof previously PASS; Chief did not reach/hear it during G2 run (not automatically FAIL).
- `$8E`: unused/no known retail gameplay trigger; do not invent one.
- A few natural SFX event contexts were never naturally reached; `$B8` player state34 and unidentified original `$A8/$B2/$C1` triggers require specific evidence if new symptom. No blanket 37/37 natural SFX claim.
- F8 CPU AF carry-bit mismatch while PSG/RAM/PCM agree; scoped emulation technical exception, not audible defect.
- Chief notices one-time startup onset delay, no subsequent recurring transition lag. Unmeasured root cause; **parked final presentation polish**, not grounds to destabilize driver.
- A prior old ring-SFX latency observation was believed fixed by Chief and is inactive without a new complaint. Authentic SMS Speed Shoes do **not** speed up/request a different song; Game Gear differs.

## Preservation and evidence

[Original sound request ledger](docs/audio-request-audit.md) and M5 technical milestones remain useful archived evidence. Current accepted implementation source after R1 is `636ed72be111bc3de4c297e5768c40c8f38a54e6` (**Chief F5 PASS** for GPZ3 rings and THZ2 bee). M6-G is the next separate regular-enemy persistence milestone, not a reopening of M5 audio.

The long original `CURRENT_M5.md` with hundreds of contradictory dated banners is preserved through [immutable Git history](docs/archive/management/MANAGER_PRE_REWRITE_20261102.md). Don't append new updates here for M6 or future graphics/Vita work. **M5 is closed.**
