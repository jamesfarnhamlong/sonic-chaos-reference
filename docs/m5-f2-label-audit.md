# M5 F2 Sound Test name/label audit — 29 October 2026

**Status: metadata review, not an implementation order; NO PROGRAMME MISSING.** Source-backed by published public POC `experiments/m5-b1/prepare.py`, B0-D `experiments/m5-b0d/crosswalk.json` from isolated `1c7fb623c32f16b1fda0c9e070b92bb07ad1fb1d`, later `experiments/m5-g1e/evidence/e2-sfx-matrix.json` at `38306d5c0c4abfe0b982ade025679f1ec957c720`, and Research `docs/audio-request-audit.md`/`data/rom-cache/audio/request-ledger.json`. No editing of private policy, ROM or F2 resources done.

**Original B0-D F2 catalogue: 68 indexed F2 rows; 63 real native programs (26 music/37 effects), five empty $9B–$9F.** B1 `prepare.py` copied `row.original_name` directly into `'$%02X - %s'` display text, and the UI `OBJ_chaos_debug_select/Draw_0.gml` prints `audioEntries[*].label`, sourced from `a3v_policy.json` sound_test.entries via `chaos_debug_audio_entries()`. Subsequent C8/C10+G1-E status/audio changes did **not** refresh these original strings. Consequently **28 literally Unknown labels** remain: 22 SFX, one genuine playable music `$8E` of still-undetermined original use, five empty music `$9B..$9F` (render as EMPTY/NO ORIGINAL DATA rather than unknown tune; never enable Play). The 22 old-Unknown SFX divide into **19 known ROM request-site contexts and3 unresolved triggers (`A8/B2/C1`)**, NOT 19 fully natural-case-proved or necessarily semantically named sonic timbres.

## Source-backed replacements for old Unknown SFX (presentation-only proposal)

Descriptions reflect proven original **requester/context**, not independently established auditory semantics. Use parenthetical ID/location/context when necessary. If implementing, retain ID prefix and show a qualifier for still unverified natural use.

| ID | Safe proposed contextual F2 label | Original request-site evidence / G1-E status |
|---|---|---|
| $A1 | Grounded skid feedback | Player right/left skid setters ROM $47BD/$47D0; natural dispatch PASS |
| $A2 | Jump feedback | Jump setter ROM $4638 and contact branches; natural dispatch PASS |
| $A5 | Rolling / EEZ transport feedback | Player rolling at $47F7 plus EEZ intermediate dispatch; natural dispatch PASS, full transport partial |
| $A7 | Moving spike type $1B feedback | Original type1B state01; natural dispatch PASS |
| $A8 | UNKNOWN: trigger unlocated | No verified ROM request site; preserve UNKNOWN |
| $AB | Boss type $0F scripted feedback | Type0F state03 and boss scripts; source-wired/partial |
| $AC | Look-up / Peel-Out charge feedback | Player movement callbacks and charged action paths; source-wired/partial |
| $AD | MGHZ boss scripted feedback | MGHZ boss/type56 scripts; source-wired/partial |
| $AE | AQZ air / Tails scripted feedback | AQZ air/Tails/type01 scripts; source-wired/partial |
| $AF | AQZ environmental feedback | AQZ environment/type0E scripts; source-wired/partial |
| $B0 | Tails callback feedback (background nibble zero) | Original Tails callback selects B0 when low nibble0; source-wired/partial |
| $B1 | EEZ object/carrier scripted feedback | Original EEZ type37 and carrier paths; natural dispatch PASS in tested contexts |
| $B2 | UNKNOWN: trigger unlocated | No verified ROM request site; preserve UNKNOWN |
| $B3 | GPZ boss scripted feedback | Original GPZ boss/type51 script; source-wired/partial |
| $B7 | EEZ carrier feedback | Original EEZ type17 script; natural dispatch PASS in tested contexts |
| $B8 | Player type $01 state $34 feedback (route HOLD) | Original type01 state34 script has request site; GameMaker natural route missing |
| $B9 | Boss scripted motion/impact feedback | MGHZ landing/boss scripted sites; exact whole-context name still qualified |
| $BA | EEZ transport exit / ending scripted feedback | EEZ tube + ending original sites; corrected intermediate forwarding, full natural routes partial |
| $BB | EEZ object/terrain feedback | Original EEZ type17 terrain/contact callback; source-wired/partial |
| $BC | Goal-sign child feedback | Original type19 state02; controlled cadence PASS; natural full-chain unproven |
| $C0 | Tails callback feedback (background nibble nonzero) | Original Tails callback selects C0 when low nibble nonzero; source-wired/partial |
| $C1 | UNKNOWN: trigger unlocated | No verified ROM request site; preserve UNKNOWN |

The `$8E` music row has a real playable programme but **no verified original request trigger**. Treat as `$8E — unidentified original music`, never label EMPTY. `$9B..$9F` are original empty headers; separate from unlocated music.

## Native vs gameplay semantics

- **F2 playable:** 37/37 original SFX decoded and in accepted F2 audition route over $81; original driver priority and suppressed channels apply. Playback qualification is not proof of what event causes a sound in the game.
- **Natural real-game coverage at G1-E:** 10 naturally delivered,23 wired/context-partial,1 mapped unimplemented B8,3 original trigger unknown. At least one other gameplay SFX remains subjectively missing per Chief; do not guess which or reenable legacy sample MP3.
- **Do not rewrite authenticated private policy only to change names.** Proposed UI-only numeric-ID label overlay can preserve private policy bytes/hashes if source-level GameMaker UI change is justified, or a formally reproven policy metadata regeneration can be separately authorised. Preserve `TOTAL68`, 63 Play, 5 empty, ID/category/availability, SFX over81 audition, STOP/P historical previews, F2/zone preservation.
- Remaining real-game SFX/scene routes are a separate implementation objective. Validate original request site → natural event → mailbox → admission/rejection → ordered PSG/PCM for bosses, menu/continue, results, ending, remaining SS, B8 and wired-partial list. No numeric invented ID, no synthetic attribution by perceived timbre.

**Chief G1-E listening:** five focus groups PASS; previously withheld missing sound confirmed `A4` hurt/ring loss and heard working. Unspecified other missing effects remain open; opening audio acoustic onset uncertain; F8 CPU carry-bit mismatch still HOLD.
