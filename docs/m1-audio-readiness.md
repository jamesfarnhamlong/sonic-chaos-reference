# M1-C — bounded original-audio readiness

22 October 2026. Research only; no rendering, soundtrack payload, playback, GameMaker wiring or compile. Accepted POC read-only `7476affc6ed7626dabf69b446cdab0c9c3d7492e`. Earlier tests/listening remain attributed, not newly rerun.

## Existing authority and actual coverage

| Layer | Exact authority | What it establishes / limit |
|---|---|---|
| AUDIO-0 | Research `docs/audio-request-audit.md`, `data/rom-cache/audio/request-ledger.json`, `data/audio-request-contexts.json`, inherited on this branch |70 classified IDs:31 music `$81..$9F`,37 SFX `$A0..$C4`, controls `$00/$F8`. Numeric sites and driver categories, not70 authentic playable assets. Unknown friendly names and no-site entries remain unresolved. |
| AUDIO-1 | `research/audio1-psg-feasibility@ff075a8fc6d2dc36a6c672ec160c95a2a40a5b79`, `docs/audio1-psg-feasibility.md`, `data/audio1/` | Original-driver request/priority/steal/restore/tick model. Historical approximate-harness PSG parity4,559 ticks; not new hardware verification. |
| AUDIO-1B | `research/audio1b-audio-render@a1b2f5e7162f76b58de8c1d17133253335ee65d2`, `docs/audio1b-render-validation.md`, `data/audio1b/render-validation-summary.json` | Deterministic five-ID evaluation renders, pitch/noise/stem/loop analysis. Not full library, production licence clearance or a sample-continuous loop. |
| AUDIO-A0 | POC `docs/audio-a0-closure.md`, `audio-a0-soundtest.md`, `audio-a0-provenance.json` at accepted Q3 | Six Windows checks accepted corrected physical Package B (Manager called it A). Sound Test previews only. Earlier defective A is not accepted. All21 inherited sound resources retained, not recertified authentic. |

The five accepted private WAVs are `$90` opening, `$82` character-selection (historically called title), `$81` THZ, `$BF` ring and `$A6` spring. Music previews are15 seconds; ring0.350s, spring0.616667s; PCM16-bit44,100Hz stereo with identical mono channels; no looping. Exact filenames, byte/frame counts and SHA-256 are already in POC provenance; reuse them, don't regenerate a substitute under the same name. A0 accepted listening of these files does not approve arbitrary future renders/clock choices/library or live synchronization.

**Frontend correction:** static M1 `$0719/$0756` requests `$99` on the title; `$30BC` requests `$82` on the separate choice screen. AUDIO-0 correctly retains `$99`'s unknown friendly name and startup request site. A pilot that covers the real title must add authenticated `$99` asset/evidence, rather than play `$82` there. The existing preview filename `82_title.wav` stays unchanged for provenance.

## Driver contract to preserve

These are reused AUDIO-1 results, not new executions:

| Concern | Original behaviour / source |
|---|---|
| Requests / ticks | One effective game mailbox `$DE04` (IRQ mirrors `$D4A4`); last write before consumption wins. Logical sound tick60/s, PAL has an extra call every fifth50Hz frame. Accepted60-update POC can use1:1 ticks as an explicit smoother adapter. |
| Priority | Byte at ROM `$0906F+(id&$7F)-1`; reject if below `$DE0F`, accept equal, store accepted priority&`$7F`. Music entries `$80`; BF/A6 `$38`; A0/A8/A9/B4 `$78`; A4/AA/AB/BB/C3 `$70`; C4/B2/BC `$60`. Store full table metadata for full library, not a generic “all SFX equal”. |
| Restart / music change | Same-ID requests reload headers. Music init resets active SFX too. Higher-priority active SFX rejects lower; equal restarts/replaces. |
| Slots / stealing | Music tone0/tone1/tone2/noise at `$DE40/$DE70/$DEA0/$DED0`; SFX `$DF00/$DF30/$DF60` steal tone1/tone2/noise respectively. Tone0 never stolen. BF/A6 steal tone2; music streams keep advancing silently. |
| Restoration | SFX `F2` clears steal flag, sets next-note recovery flag and silences channel; music audible only at next onset. Historical BF-at200 over81: SFX ends220, music onset229. `$DE0F` clears when **any** SFX ends, even if another slot runs. |
| Stop | `$00` empty request is ignored, not silence. `$F8` resets all channels and emits silence same tick. Unknown/unrendered IDs stay explicitly unavailable; do not substitute unrelated effects. |
| Fade | `$18E1`: offset limit12, step1 every2 ticks, final attenuation=min(15,envelope+offset), reset after23 ticks in measured case. `$D0` driver fade217 ticks; no game request site found. This is additive PSG attenuation, not stock linear volume ramp. |
| Pause | `$DE08=$80` first mutes then freezes driver; resume reasserts PSG within1–3 ticks. Model freeze/restore and preserve song position, not restart-on-unpause. |

Original driver command recurrence does **not** mean PCM recurrence: AUDIO-1B THZ periods differed in83.9% of MAME samples because tone phases continue. State recurrence for81 starts1093, period2688 ticks;82 starts130, period6912;90 starts803, period19768. Cut from verified recurrence with a measured seam policy; don't use a convenient first-channel jump or loop the15-second preview.

## Architecture recommendation — one owner, hybrid stems

Adopt the existing AUDIO-1 hybrid recommendation subject to Manager's fidelity decision. One persistent dispatcher accepts request IDs, publishes one update-boundary mailbox and owns music/stem handles, SFX slots, priority, per-tick phase/onset metadata, pause/fade and stop. Call sites request events once at existing canonical writes; rooms, menus and gameplay objects must not independently start covered sounds. Sound Test becomes an explicit audition mode of this owner, preserving A0's opt-in preview interface and stop/back behaviour.

Music uses synchronised per-channel stems or at least separately stealable voices plus the never-stolen voice; all share identical intro/loop boundaries. SFX use authenticated one-shots and driver-derived slot/duration/priority metadata. Gate stolen stem until next note onset after SFX end, keeping its timeline running. Stems must be generated by preserving all PSG writes and attenuating other voices: AUDIO-1B showed deleting writes or using GME mute masks can alter phase and break sums. Sum check should reproduce the reference mix within the documented renderer tolerance.

Arbitrary-phase fades remain an approximation with PCM stems unless sufficient attenuation variants or an approved runtime synthesis strategy is used. Record numerical/audible deviation; don't advertise hardware-exact fades. The noninteractive opening can have a verified pre-rendered natural fade, but skip needs the dynamic policy. AUDIO-1B's nominal60Hz opening adapter render791 ticks differs from PAL-cadence945; neither the15-second preview nor a nominal runtime duration is proof of correct sync. Driver-in-runtime alternatives require an explicit asset/licence/platform decision; do not bundle ROM driver bytes or a binary extension under this assignment.

## Assets, tools and runtime prerequisites

1. Decide production renderer and PSG clock: prior evaluation used provisional PAL3,546,893Hz; NTSC3,579,545 differs about15 cents. Existing MAME-core libvgm pin `a6eed945ecf4e5a25cf82004779c6f7e4fd5c319` has BSD-3 core but unresolved glue licence. GME90 transposition fault and Maxim noise interpretation remain documented; no silent switch to another renderer.
2. Generate full pilot durations, stems, next-onset maps, request headers/priority/stop metadata and hash manifest privately. Include title99 now identified; keep accepted A0 files unchanged. All remaining music/effects require the same validation before M5.
3. Validate recurrence, stem sum, pitch/noise, silence/DC/clipping, SFX completion versus audible tail (A6 driver40 ticks but audible36), and seam choice. Test pinned GameMaker WAV/OGG decode/loop accuracy natively; it was not established by driver recurrence.
4. Inventory all current `audio_play_sound`, `audio_stop_all`, pause music and inherited ring/spring calls in the accepted POC before wiring. `SCR_chaos_debug_select` ordinary defaults still map legacy A4/A6/BF; A0 opt-in alone does not supply a runtime owner. Cover or gate duplicate writers once. Exact runtime mutation list belongs to the separately authorised Designer preflight.
5. Use `verification/restore_audio_a0_assets.py --restore/--check` for the existing five payloads. New library needs equivalent atomic hash/header/resource-path checks, ignored payload paths `sounds/RESOURCE/RESOURCE.wav`, missing/corrupt negative controls and repeated restore0. Existing Q3 package restores181 total private resources; do not interpret that number as181 sound files.

The local Q3 inventory was read; no audio payload hash/listening/restoration rerun happened here. A cloud successor needs Chief to supply five approved WAVs plus canonical private ROM for newly approved generation, or a fully hash-authenticated private asset set; no complete soundtrack request is necessary for this readiness checkpoint. Existing WAV hashes/filenames and Research pins already suffice to specify the request.

## Coherent pilot → full-library sequence

| Proposed group | Scope | Evidence / Windows gate |
|---|---|---|
| M4 preparation and dispatcher pilot | Approved renderer/clock/asset policy, one dispatcher; opening90 natural+skip, title99, choice82, THZ81, BF/A6; F8/00/restart/priority/steal/recovery/pause/fade, Sound Test isolation | Deterministic driver-vs-dispatch timelines, high/low/equal requests, phase offsets, missing asset controls; Chief hears startup/skip/title/choice/THZ, ring/spring under music, loops/pause/restart/stop and no duplicate/leaking playback. |
| M5 full library | Inventory all70 IDs including unresolved/no-site ones separately; zone/boss/SS/power-up/death/Continue/clear/ending cues and all stealable slots | Every implemented ID has source/context, asset/hash, duration/loop/onset metadata, priority/slot, restoration proof; no blanket claim for unavailable IDs. Chief hears representative zones/boss/SS/ending/death/Continue with interruption and scene transitions; campaign soak scope agreed separately. |

No M4/M5 authorisation is implied. M2 Tails remains the intended next implementation decision, with M3 frontend after Tails is functional. This document replaces neither existing preview acceptance nor the outstanding fidelity decisions.
