# AUDIO-1: original SMS sound driver and PSG playback feasibility

Target: Sonic Chaos (Europe), SMS v1.2, SHA-256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
Base: accepted Research `main` `b6467ba0ad79fad0937f750083a5261e7ea64e8f`.
Branch: `research/audio1-psg-feasibility`. Research only: no POC change, no ROM bytes,
no rendered or ripped audio, no Research `main` promotion.

Machine-readable companions: [`data/audio1/pilot-plan.json`](../data/audio1/pilot-plan.json),
[`data/audio1/pilot-trace-summary.json`](../data/audio1/pilot-trace-summary.json).
Tooling: [`tools/audio1_psg_trace.py`](../tools/audio1_psg_trace.py),
[`tests/test_audio1_psg.py`](../tests/test_audio1_psg.py).

## 1. Managerial summary

**Recommendation: CONDITIONAL GO** for a small, local-only, five-request original-audio pilot.

The central feasibility question is answered with evidence: **the original driver can be executed
unmodified from the ROM and its PSG output captured exactly.** No song or sound-effect format needed
to be reverse-engineered into a new decoder, and no VGM/emulator tool needs to "understand" the
proprietary streams. The original Z80 driver (ROM `$08000`, CPU `$4000`) interprets them; the harness
runs that driver and records every write to PSG port `$7F`.

Strongest result (**verified**, approximate-harness label): feeding the isolated driver only the inputs
game code gives it (mailbox byte, pause/fade bytes) reproduces the game's own IRQ-driven PSG byte
stream **identically for all 4,559 captured driver ticks** of an unattended boot/attract run. That
run contains `$90` (opening), `$81` (Turquoise Hill), 14 × `$BF` ring, `$A6` spring, `$A2`/`$A5`
SFX, 44 requests in total and three game-issued fades, including SFX over running music.

Other decisive findings:

* The driver's logical tick is **60 per second on both NTSC and PAL** (PAL gets an extra call every
  fifth frame). The accepted POC's 60 updates/s therefore maps 1:1 to driver ticks.
* Every music request loops forever by per-channel stream jumps; exact periodic driver state is
  measurable, so seamless loop points are derivable rather than guessed.
* SFX steal one of three music channels, and recovery is **at the next note onset of that channel**,
  not an immediate resume. A pre-mixed music file cannot reproduce that; per-channel stems can.
* A fade is attenuation addition with a clamp to "off", not a gain multiply; exact arbitrary-phase
  fades need either runtime driver execution or a documented approximation.

**Preferred approach: hybrid (candidate C), staged.** Offline-render music, as per-PSG-channel stems,
and SFX one-shots from driver-executed PSG logs. Reproduce mailbox, priority, restart, `$F8`, steal and
recovery in one small GameMaker request owner, validated against the driver trace. Keep runtime PSG
(candidate B) as the escalation path if exact arbitrary-phase fades prove necessary. Rationale in §4.

**Conditions for GO:**

1. Manager approves an asset-handling plan: generated audio stays locally ignored, nothing ships.
2. A licensed PSG renderer is chosen (build-time tool, not linked into the POC).
3. An independent controlled capture confirms per-tick PSG parity on a local machine (this task's
   parity evidence is the repo's *approximate* frame harness, not hardware or a cycle-exact emulator).
4. Manager decides PSG clock (PAL 3,546,893 Hz for the Europe ROM versus NTSC 3,579,545 Hz).

## 2. Evidence classes and boundaries

Every substantial finding carries one tag.

| Tag | Meaning |
|---|---|
| **verified** | Executed in this task on the hash-verified ROM with the committed harness; re-runnable. |
| **source-traced** | Read from ROM bytes/disassembly or the accepted AUDIO-0 ledger; not executed end to end. |
| **proposed** | Design recommendation; not demonstrated. |
| **unresolved** | Evidence missing. |

Three layers are kept separate throughout:

* **SMS hardware**: the SN76489-compatible PSG behind port `$7F`.
* **Original driver behaviour**: the Z80 sound code and its data.
* **Documented adapter**: any PC choice (update rate, clock, resampling, loop cut, mixing, delivery).

**ROM handling.** The manager brief says cloud agents lack the ROM. In this session the user attached
a ROM file; its SHA-256 matched the target before anything ran. It was copied to ignored `roms/`
(`.gitignore` covers `*.sms` and `roms/`), used read-only, and is not committed. All "verified" items
below were executed on it. They have **not** been independently reproduced on the Windows machine;
§8 lists the commands for that.

**Not claimed:** no waveform was rendered or listened to; no comparison with hardware or a
cycle-exact emulator was made; no GameMaker runtime was run.

## 3. Investigation A: the original sound engine

### A.1 Structure and call path

| Fact | Evidence |
|---|---|
| Entry CPU `$4000` = ROM `$08000`. Sound bank 2 sits in slot 1, bank 3 in slot 2, so song/SFX pointers (`CPU` `$4000..$BFFF`) are contiguous; file offset = stored pointer + `$4000`. | source-traced; AUDIO-0 |
| One update = fade/pause gate, tempo tick `$4066`, arbitration `$407F`, fade `$40B0`, dispatch `$4119`, then channel updates. | source-traced (disassembly `$08000..$08065`) |
| Channels: music `$DE40 $DE70 $DEA0 $DED0` (tone0, tone1, tone2, noise); SFX `$DF00 $DF30 $DF60`; 0x30 bytes each. | source-traced; **verified** by execution |
| IRQ `$005C9..$005E0` copies `$D4A4` to mailbox `$DE04`, maps banks 2/3 and calls `$4000`. | source-traced |
| Region flag `$D12D` from `$01C76`: 1 = NTSC, 0 = PAL. If `$D12D == 0`, `$005EA..$005F6` calls the driver a **second time every fifth frame**. | source-traced |
| 72 driver entries per 60 frames counted in the repo harness (6:5). Its region flag read 0. | **verified** (approximate harness) |

**Consequence (source-traced + verified):** driver ticks run at a nominal **60 Hz on both regions**.
On PAL they arrive in bursts (six per five 50 Hz frames), not evenly spaced.

### A.2 How music data is encoded and played

Song header (pointer from the index at ROM `$090E1`, entry `(id-$81)*2`):

| Offset | Meaning (source-traced; consistent with execution) |
|---|---|
| +0 | word `$49FD`, shared volume-envelope table |
| +2 | channel count (4 for all three music pilots) |
| +4 | duration multiplier (`(IX+2)`) |
| +5 | tempo byte → `$DE01`/`$DE02` (matches ROM table `$090C2`) |
| +6.. | per channel: stream pointer (2), transpose (signed), volume attenuation; latch from table `$4263` = `$80 $A0 $C0 $E0` |

Stream grammar read by `$4341` (**source-traced**):

* `< $80`: duration (times the channel multiplier). Repeats the previous note when it follows a note.
* `$80`: rest. `$81..$D7`: note; index = `(byte & $7F) + transpose` into the word table at ROM `$08436` (first periods `$0356 $0326 $02F9 $02CE ...`, semitone ratio ≈ 1.0596).
* `$D8..$DF`: set channel volume attenuation (`& 7`).
* `$E0..$FF`: command via the word table at ROM `$086ED`.

Command map (handler addresses read from the ROM table; names inferred from handler code):

| Cmd | Handler | Behaviour | Seen in pilots |
|---|---|---|---|
| E0 | `$4889` | custom ADSR (5 bytes) | **verified** used |
| E1 | `$487E` | detune/pitch offset | **verified** used |
| E2, E6 | `$472D` | relative volume (ignored while a fade is active) | E6 used by `$A6` |
| E4 | `$473D` | adjust shared byte `$DE16` | not used |
| E5 | `$48A3` | ADSR flag | not used |
| E7 | `$4878` | tie (sets flag bit1, no retrigger) | used |
| E8 | `$4860` | note gate length | not used |
| ED | `$4882` | set tempo (`$DE01`/`$DE02`) | not used |
| F0 | `$486A` | vibrato/pitch-envelope pointer (4 parameter bytes) | used |
| F2 | `$47C8` | **end of track**, restores any stolen channel | used by SFX |
| F3 | `$4753` | noise control byte | not used |
| F4, F5 | `$47B0`, `$47AC` | pitch / volume envelope select | F5 used |
| F6 | `$47B4` | **absolute jump** (loop) | used |
| F7 | `$4849` | counted repeat | used |
| F8 / F9 | `$481C` / `$4836` | call / return (per-channel stack) | used by `$A6` |
| FA, FB | `$474F`, `$4748` | duration multiplier / transpose add | not used |
| FD | `$47BA` | literal-period mode flag | not used |
| E3, E9..EC, EE, FC, FE, FF | `$473C` | `RET` (no-op, consumes one parameter byte) | not used |
| EF, F1 | `$48AC` | points into the pitch-envelope **data** table | **unresolved**, likely unused |

Executed command usage for the five pilots is in `pilot-trace-summary.json`
(`stream_commands_executed`). Table semantics beyond those exercised are source-traced only.

### A.3 How the PSG is controlled

All output is `OUT ($7F),n`. The harness decodes the SN76489 protocol (latch byte
`1 cc t dddd`, then data byte `0 0 dddddd`).

* Tone: period split across a latch (low 4 bits) and data byte (high 6 bits); Hz = clock / (32 × period). Source-traced at `$44F9..$4526`.
* Attenuation: latch `base | $10 | level`; level = envelope level + channel volume, clamped to 15 (= off). Source-traced at `$4528..$4545`.
* Noise: channel struct latch `$E0`; its stream bytes select presets writing `$E4/$E5/$E6` (white noise, three shift rates) plus an envelope id. Tone-2-driven noise (`$E7`) handling is at `$4753`. Source-traced (`$4674..$46D4`).
* Reset/silence: `OTIR` of `80 00 A0 00 C0 00 9F BF DF FF` (periods 0, attenuation off) at `$43FB`. **Verified** (`$F8` emits exactly these bytes).
* Envelopes: volume envelopes via table `$49FD`, pitch envelopes via `$48AC`, plus the custom ADSR in the channel struct. Source-traced; their sample-by-sample output is **verified** only as part of the executed PSG trace.

SMS hardware (reference-documented; the shift-register facts were checked in emulator source, see §4):
the Sega VDP PSG uses a **16-bit** noise shift register with taps on bits 0 and 3, unlike the
TI SN76489's 15-bit register with taps 0 and 1. Attenuation is 2 dB per step, 15 = off.
PSG clocks of 3,579,545 Hz (NTSC) and 3,546,893 Hz (PAL) are widely documented but were
**not re-verified from a primary source in this session** (the reference site was unreachable).

### A.4 Tempo, frame updates, looping and completion

* **Frame updates (verified):** one driver tick per update; channel timers count ticks.
* **Tempo (source-traced; verified by the measured loop lengths):** `$DE02` is a divider. Every `$DE02`th tick `$4066` adds 1 to all four music duration counters, stretching time by `$DE02/($DE02-1)`. Tempo byte 0 means no stretch. Measured: `$81` (byte 0) loops every exactly 2,688 ticks; `$82` (byte 6) every 1,382.67 average ticks, consistent with 1,152 base ticks × 6/5.
* **Looping (verified):** no driver-level loop flag. Each channel ends its pass with `F6` jumps and `F7` repeats; all five pilot requests were seen to keep playing for thousands of ticks and the music never self-terminates in the simulated span.
* **Exact periodic state (verified):** driver RAM `$DE00..$DF8F` recurs exactly, and the PSG byte stream of the following period is byte-identical:

| ID | State first seen | Period (ticks) | At 60 ticks/s |
|---|---|---|---|
| `$81` THZ | 1,093 | 2,688 | 44.8 s |
| `$82` title | 130 | 6,912 | 115.2 s |
| `$90` intro/EEZ3 | 803 | 19,768 | 329.5 s |

  A seamless loop cut must use this recurrence. For `$81`, channel 0 first jumps at tick 2,785, not at the recurrence point, so "channel 0's loop target" is the wrong cut.
* **Completion (source-traced):** a channel stops at `F2`; the song is complete when all four music channels are inactive. No pilot music reached `F2` in the simulated span.

### A.5 How SFX interrupt, steal and restore music channels

* **Init `$081A7` (source-traced):** the SFX header's channel byte picks the slot: `$A0` → `$DF00` over tone1, `$C0` → `$DF30` over tone2, otherwise `$DF60` over noise. It sets **bit 2** on the corresponding music channel (suppresses that channel's PSG writes) and installs a separate stream. Tone0 is never stolen.
* **Music keeps running while stolen (verified):** the music stream pointers and timers advance silently; only the PSG writes are withheld.
* **Restore (verified):** at SFX end (`F2`, `$47C8`) the driver clears bit 2, sets bit 4 on the music channel, writes attenuation-off, and clears `$DE0F`. The music channel then stays silent until its **next note onset**, not mid-note. For `$BF` over `$81` (request at tick 200): tone 2 flagged at tick 200, flag cleared at 220, audible again at 229.
* **Pilot SFX (verified):** `$BF` and `$A6` both use latch `$C0`, so both steal tone 2 only. `$BF` is active 20 ticks, `$A6` 40 ticks. `$BF` also writes `$FF` once to the noise latch at init; the music noise channel's own next write re-establishes noise within the same tick, so no lasting noise cut (verified in the trace).
* **Music request during SFX (verified):** music init resets everything including active SFX slots.

### A.6 Restart, stop, priority and fade

| Behaviour | Result | Tag |
|---|---|---|
| Priority | `prio = byte[$0906F + (id & $7F) - 1]`. A request is dropped when `prio < $DE0F`; equal is accepted; accepted value `& $7F` becomes `$DE0F`. | source-traced; **verified** (equal accepted, higher current drops) |
| Music priority | All indexed music IDs `$81..$9F` read `$80`; reset zeroes `$DE0F`, so music is always admitted. | **verified** (table dump) |
| SFX priority | `$BF = $A6 = $38`; e.g. `$A0 $A8 $A9 $B4 = $78`, `$A4 $AA $AB $BB $C3 = $70`, `$C4 $B2 $BC = $60`. A higher-priority SFX in progress drops a lower-priority one. | **verified** (table); rule verified |
| Cleared priority | `$DE0F` is cleared when any SFX channel reaches `F2`, even if another SFX stream is still running. | source-traced |
| Same-ID restart | No early return; header reloads. `$81` re-request resets all four stream pointers. | **verified** |
| `$A6` over `$BF` or vice versa | Equal priority: accepted, restarts on the same slot. | **verified** |
| `$00` | Ignored; running music unchanged. | **verified** |
| `$F8` | Reset path `$43E5`/`$43FB`: all channels inactive, silence bytes emitted in the same tick. | **verified** |
| Gameplay fade (`$18E1`: `$DE09=12 $DE0A=1 $DE0B=2`) | Each step raises every channel's volume offset by 1 (capped at 12) every 2 ticks (`$40B0..$4118`); final attenuation is `min(15, envelope + offset)`, so a fade is additive attenuation with a clamp to "off", not a gain multiply. Ends in reset. Music inactive after **23 ticks**. | **verified** |
| `$D0` fade request | Same mechanism with `$DE0A=$DE0B=$12`; music inactive after **217 ticks**. No gameplay site requests `$D0` (AUDIO-0). | **verified** (driver); site search per AUDIO-0 |
| Pause (`$DE08 = $80`, written by game code at `$174A`; cleared at `$16A5`) | First tick mutes (silence bytes), then the driver returns immediately (frozen); on resume the PSG state is re-asserted within 1–3 ticks. | **verified** |
| `$D3` / `$D1` control table | Table at `$4138`: `$D1` → reset; `$D3` entry decodes as `$7000` (data), likely unreachable. | **unresolved** (no gameplay request) |

Mailbox: three bytes `$DE04..$DE06` are examined each tick. A byte-pattern scan of the ROM found
**no absolute-address instruction storing `$DE05` or `$DE06`**, so the game uses `$DE04` only
(source-traced; a pattern scan, not a proof). A later write before the driver consumes `$DE04`
replaces the earlier one (AUDIO-0).

### A.7 What is still missing for accurate audible synthesis

| Gap | Why it matters | Tag |
|---|---|---|
| No hardware or cycle-exact-emulator PSG capture compared against the harness | The strongest parity evidence is the repo's *approximate* harness; VDP/IRQ timing there is not hardware | **unresolved** |
| PSG clock for the Europe ROM and whether music pitch is judged at NTSC or PAL clock | ±0.9 % (~15 cents) pitch offset | **unresolved** (manager decision) |
| Sub-tick timing of PSG writes within a frame | Driver writes occur once per tick near VBlank; sample-exact start offsets are not modelled | **unresolved** (likely negligible) |
| Mixing: relative channel levels, DAC curve, high-pass behaviour of real SMS output | Affects loudness balance, not pitch/rhythm | **unresolved** |
| Noise LFSR implementation details (initial state, phase on rewrite) | Noise timbre is chaotic; renderer-dependent | **unresolved** (emulator source checked, not hardware) |
| Real-time cadence of PAL burst ticks | Adapter evens them out at 60 Hz | **proposed** adapter decision |
| Length/timing of the original opening in wall time | Approximate harness frame count only | **unresolved** |
| Sound IDs with no request site (`$8E $9B..$9F $A8 $B2 $C1`) and 31 unnamed IDs | Out of pilot scope | **unresolved** (AUDIO-0) |

## 4. Investigation B: reproduction strategies

Common point: **none of the candidate technologies decodes Sonic Chaos's streams.** VGM files, SMS
emulators and PSG cores consume PSG *register writes* (or whole Z80 images), not this driver's
command language. The route that works is already demonstrated: execute the original driver,
record its port writes (the harness), then render those writes with any PSG core.

### Open-source technology actually checked

| Technology | Facts checked in this task | Relevance and limits |
|---|---|---|
| MAME `src/devices/sound/sn76496.cpp` | Header: `license:BSD-3-Clause`, copyright Nicola Salmoria. Defines `segapsg_device` with a **16-bit** noise register, taps `0x01` and `0x08`, XOR feedback, versus `sn76489_device` 15-bit, taps `0x01 0x02`. | Permissive licence; correct Sega variant exists. Standing alone requires extraction from MAME's device framework (adaptation effort not assessed). |
| Game_Music_Emu (libgme) | `license.txt` is **LGPL-2.1**. `Sms_Apu.cpp` header: LGPL 2.1 or later, Shay Green. 16-bit shifter, default feedback `0x0009`, bit 2 of the noise control selects the feedback mask, band-limited (blip) output, no fixed sample rate. | Good offline renderer candidate. LGPL obligations are minimal if used as a separate build-time tool; they grow if linked into a shipped GameMaker extension. |
| libvgm, VGMPlay, other players | Licence fetch failed (404). | **Not verified.** Do not assume licences. |
| GameMaker audio | Manual search results: `audio_sound_loop_start` / `audio_sound_loop_end` exist, settable while playing, loop end must follow start, `0.0` means the sound's end. Procedural audio exists: `audio_create_play_queue`, `audio_queue_sound` (buffer format must match the queue; buffer cannot be deleted until the queue is freed). | Version in which these arrived, per-platform limits and whether compressed-OGG loop points are sample-accurate are **unresolved**; test on the pinned IDE/runtime locally. No official GameMaker PSG support exists. |
| VGM format (open container of PSG writes) | Used as the interchange: `--vgm` writes a minimal VGM 1.50 with SN76489 clock, 16-bit shift register and one 735-sample wait per 60 Hz tick. | A renderer-side choice; no VGM was played back here. |

### Candidates

**A. Offline ROM-derived rendering**

* Fidelity: exact notes/durations/tempo/loop periods (driver-executed). Fades and channel interactions are exact only for *the exact request timeline that was rendered*; one pre-mixed file cannot represent SFX steal/recovery or arbitrary-phase fade.
* Complexity: low. Dependencies: a PSG renderer at build time only. Loop handling: exact (recurrence). CPU at runtime: negligible (stock audio playback). Maintenance: re-run script. Distribution: output is derived audio, not ROM bytes; must stay local and ignored under the current policy.
* Weakness: SFX interruption and music-channel recovery are not reproduced by simply mixing a one-shot over a pre-mixed track.

**B. Runtime PSG playback in GameMaker**

* Fidelity: potentially exact for everything, including fades and steals, because it can run the real driver logic. Options: (B1) port ~1.4 KB of Z80 driver logic to GML; (B2) embed a Z80 core in GML running the original driver bytes; (B3) a native extension wrapping a PSG core plus a Z80 core.
* Complexity: highest. B1/B2 need the sound bank *bytes* at runtime, so ROM-derived data would have to be packaged or the ROM supplied at run time, which conflicts with the "never package ROM bytes" rule unless Manager changes it. B3 adds binary/platform dependencies and licences. GML synthesis cost at audio rates is **unmeasured**; no CPU figure is asserted. Maintenance: highest.

**C. Hybrid**

* Offline-render music as **per-PSG-channel stems** with identical loop length and recurrence-derived loop points, and SFX as one-shots; implement driver-level semantics (mailbox, priority, restart, `$F8`, steal, recovery) as a small deterministic request owner in GameMaker.
* Steal reproduction: for each stealable channel, export a note-onset timeline from the trace (timing metadata, derived). On an SFX start, gate that stem; after SFX end, keep it gated until the stem's next onset. This reproduces the verified driver rule without a PSG at runtime.
* Fade: approximate with stepped per-stem gain (adapter, labelled). The one exact exception that matters now: the opening cinematic is non-interactive and its end fade starts at a fixed tick (game fade start at driver tick 957, 922 ticks after the `$90` request, in the harness), so its fade tail can be **pre-rendered exactly** with the driver's own fade.

### Comparison

| Criterion | A offline mix | B runtime | C hybrid (stems) |
|---|---|---|---|
| Notes, tempo, loop | exact | exact | exact |
| SFX priority/restart | needs request owner | native | request owner (verified rules) |
| SFX steal and recovery | not reproducible | native | reproducible with stems + onset table |
| Fade / restart | fixed timeline only | native | approx. gain; opening fade exact |
| Complexity | low | high | medium |
| Runtime dependency | none | PSG/Z80 code or DLL | none |
| Runtime CPU | negligible | unmeasured | negligible |
| Loop handling | exact | native | exact |
| Offline source-only POC | yes (local assets) | needs sound-bank bytes at runtime | yes (local assets) |
| Maintenance | low | high | medium |

### Choice and reasoning

**C, staged.** It is the only candidate that keeps the POC source-only and ROM-free at runtime
while still reproducing the one behaviour that offline mixing cannot (steal and recovery), and the
rules it must implement were measured on the real driver, not inferred from request names.
B is rejected *for the pilot* because it forces ROM-derived bytes into the build and has an
unmeasured CPU/maintenance cost. B remains the escalation path if Manager requires exact
arbitrary-phase fades.

## 5. Investigation C: five-item pilot

All five requests were executed through the original driver (**verified**). Per-ID detail, claims
with tags, unresolved questions and validation steps are in `data/audio1/pilot-plan.json`.

| ID | Context | Header (ROM) | Behaviour measured | Looping / restart |
|---|---|---|---|---|
| `$90` | Opening cinematic; EEZ act 3 | `$0B8EB` | 4 ch, tempo 28; in-situ boot request at tick 35; game fade ends the opening | loops; recurrence 803 / 19,768 |
| `$82` | Title / character select | `$0963F` | 4 ch, tempo 6 (5/6 stretch) | loops; recurrence 130 / 6,912; restart from header |
| `$81` | Turquoise Hill | `$09169` | 4 ch, tempo 0 | loops; recurrence 1,093 / 2,688; restart from header |
| `$BF` | Ring feedback | `$0E376` | tone 2 only; 20 ticks; priority `$38` | one-shot (`F2`); equal priority restarts |
| `$A6` | Spring feedback | `$0DFC4` | tone 2 only; 40 ticks; priority `$38`; call/return pitch pattern | one-shot (`F2`); equal priority restarts |

Context evidence is AUDIO-0 (zone/act table rows, request sites). The "opening cinematic" attribution
of `$90` comes from the accepted U5-A/AGENTS material and the zone-7 table rows; this task re-derives
only that the unattended ROM requests `$90` at boot.

### Toolchain (built, committed, deterministic)

`tools/audio1_psg_trace.py` (hash gate first, ROM never written):

* `--pilot [--check]`: execute the five requests; write or compare `data/audio1/pilot-trace-summary.json` (counts, header offsets, recurrence, SFX facts, command histogram, **hash of the PSG write log**; no register values or audio).
* `--insitu`: boot the ROM in `tools/sms_frame_harness.py`, capture the game's own PSG bytes per driver entry, replay only mailbox/pause/fade inputs through the isolated driver and compare.
* `--dump ID --out build/audio1/…`: full write log (ignored path).
* `--vgm ID --frames N --clock HZ --out build/audio1/…`: local VGM for an external renderer (ignored path).

Not built, by design: no audio renderer, no stems, no GameMaker code.

### Unresolved pilot questions

* Which PSG clock and renderer; mixing levels (§3 A.7).
* Wall-clock length of the opening before its fade, and whether the POC cinematic reproduces the original fade timing.
* Whether `$82` is re-requested on title re-entry paths (not traced).
* Seam: whether OGG decode padding preserves a sample-exact loop in the pinned GameMaker runtime (test with WAV and OGG).

## 6. Investigation D: validation and GameMaker contract

### Validation protocol (original behaviour versus generated playback)

| Topic | Method | Pass criterion | Status |
|---|---|---|---|
| Notes, durations, tempo, tone/noise | Capture PSG writes from an independent emulator running the ROM with a debugger-forced `$DE04` request; compare per driver tick with the harness log. Render VGM through two independent cores and compare onset times and pitch. | Identical write sequences per tick; onsets agree within one tick | harness parity **verified** (approximate); independent capture **unresolved** |
| 50 Hz PAL vs 60 updates | Verify tick count over a long window (60 ticks/s). Compare long-window position, not per-frame phase. | Equal tick counts per second; per-frame jitter documented as adapter | cadence **verified** in approximate harness; hardware **unresolved** |
| BGM loop | Render two periods from the recurrence; compare. In GameMaker, compare loop wrap against the render. | Second period equals first; no audible seam | periodic writes **verified**; GameMaker seam **unresolved** |
| BGM restart | Re-request mid-song; compare to a fresh request | Pointers and PSG writes match fresh start | **verified** (driver) |
| SFX interrupt and recovery | Request `$BF`/`$A6` at many phases over `$81`; compare tone-2 gating and next-onset recovery | Tone 2 silent from request to next music tone-2 onset after SFX end | rule **verified** for one phase; multi-phase **proposed** |
| `$F8` vs `$00` | `$00` leaves music unchanged; `$F8` emits silence bytes and clears music channels the same tick | as stated | **verified** |
| Fade / transition | Driver: 23 ticks (gameplay), 217 ticks (`$D0`). Compare an adapter gain ramp's tail with the driver's attenuation trace | Adapter deviation recorded numerically | driver **verified**; adapter **proposed** |

### Narrow GameMaker integration contract (proposed)

Principle: **one owner of music state.** The ROM's single mailbox and priority model is the model;
GameMaker receives only the original request ID.

1. A single persistent controller owns all pilot-covered music and SFX playback. Nothing else starts or stops those sounds.
2. One entry point, e.g. `chaos_audio_request(id)`, called wherever original logic would store `$DE04`. Last call before the update boundary wins (matches the mailbox); at the update, run arbitration with the priority bytes above.
3. Update tick = the POC's 60/s step. Internally count ticks for SFX length (`$BF` 20, `$A6` 40) and the steal gate.
4. `$00` = ignore. `$F8` = stop and silence everything now. Unknown or unrendered IDs = silent and logged. Never substitute another sound.
5. Re-requesting an ID restarts from the start. Music request cancels active SFX.
6. Existing inherited `SFX_ring`, `SFX_sonic_spring`, `OBJ_pause` `audio_*` calls and any `audio_stop_all` must route through the controller (or be gated off) for pilot IDs, or the old sounds will double-play. Which sites exist at the accepted POC tip is a POC-san preflight item; this task did not inspect the accepted tip.
7. Pilot flag defaulting to off, so the accepted POC behaviour is unchanged unless enabled.
8. Pause: map to mute-and-freeze (verified driver behaviour); not part of Package A unless trivial.

Original driver behaviour (items 2–5) stays distinct from adapter choices (60 Hz even ticks, clock, resampling, loop cut, fade approximation, delivery format), which must be listed as such in code and docs.

### Proposed AUDIO Package A boundary

**In:** local-only generation of assets for `$90 $82 $81 $BF $A6` from the user's ROM (renderer choice
approved first); stems for music tone 2 versus the rest and an onset table for the tone-2 gate; the controller and
request entry point; exact pre-rendered opening-end fade; Windows F5 checklist (hear the opening, title,
THZ1 loop; ring over music; spring over music; `$F8`; restart).
**Out:** all other IDs, special-stage audio, exact arbitrary-phase fades, sound test, pause polish,
Tails, options/volume UI, any committed or shipped audio, any ROM bytes.
**Gates:** the five in `pilot-plan.json` (hash; summary regenerates; loop seam; independent capture;
two renderers agree) plus Manager approval of the asset-handling plan.

## 7. Risks

* The parity evidence is from an approximate harness; an independent capture may reveal timing effects it cannot show.
* Stem approximation of fades may be audibly different from hardware in the tail.
* PAL burst ticks smoothed to even ticks change micro-timing of SFX start relative to music by up to one tick.
* Renderer choice carries licence and noise-timbre implications.
* Existing POC audio calls may conflict; unaudited here.

## 8. Tests run and not run

**Run in this task (ROM supplied by the user, hash verified):**

* `python -m unittest discover -s tests -p test_audio1_psg.py -v`: 14 tests (7 ROM-free, 7 ROM-dependent) pass.
* `python -m unittest discover -s tests -p test_audio_requests.py -v`: AUDIO-0 regression, 8 tests pass (unchanged).
* `python tools/audio1_psg_trace.py ROM --pilot --check` and `--insitu`: pass.
* ROM-free subset with the ROM hidden: 7 pass, 7 skipped, as designed.
* `git diff --check`.

**Could not run here (require local resources):**

* Independent controlled playback capture (cycle-exact emulator or hardware) and per-tick comparison.
* Rendering through a PSG core, listening comparison, loudness and pitch measurement.
* Windows-local reproduction of the above commands.
* GameMaker runtime: loop-point accuracy, OGG vs WAV, `audio_*` conflicts, performance.
* Licence verification of tools whose fetch failed (libvgm, VGMPlay) and primary-source PSG clock values.

Commands for local reproduction:

```powershell
python tools/audio1_psg_trace.py "$env:SONIC_CHAOS_ROM" --pilot --check
python tools/audio1_psg_trace.py "$env:SONIC_CHAOS_ROM" --insitu
python tools/audio1_psg_trace.py "$env:SONIC_CHAOS_ROM" --vgm 0x81 --frames 3781 --out build/audio1/81.vgm
python -m unittest discover -s tests -p test_audio1_psg.py -v
```

## 9. Sources consulted

* MAME `sn76496.cpp` (header and noise definitions): <https://raw.githubusercontent.com/mamedev/mame/master/src/devices/sound/sn76496.cpp>
* Game_Music_Emu licence: <https://raw.githubusercontent.com/libgme/game-music-emu/master/license.txt>
* Game_Music_Emu `Sms_Apu.cpp`: <https://raw.githubusercontent.com/libgme/game-music-emu/master/gme/Sms_Apu.cpp>
* GameMaker manual, `audio_queue_sound`: <https://manual.gamemaker.io/lts/en/GameMaker_Language/GML_Reference/Asset_Management/Audio/Audio_Buffers/audio_queue_sound.htm>
* GameMaker manual, audio overview and loop functions (search result summary): <https://manual.gamemaker.io/lts/en/GameMaker_Language/GML_Reference/Asset_Management/Audio/Audio.htm>
* AUDIO-0: `docs/audio-request-audit.md`, `data/rom-cache/audio/request-ledger.json`.
