# AUDIO-1B: first authentic audio rendering and validation

Target: Sonic Chaos (Europe), SMS v1.2, SHA-256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
Base: accepted AUDIO-1 `ff075a8fc6d2dc36a6c672ec160c95a2a40a5b79`. Branch `research/audio1b-audio-render`.
Research only. No POC change, no ROM bytes, no generated audio in Git (`*.wav *.vgm *.kss *.ogg` are now ignored).

Tooling: [`audio1b_render.py`](../tools/audio1b_render.py), [`audio1b_checks.py`](../tools/audio1b_checks.py),
[`audio1b_analyze.py`](../tools/audio1b_analyze.py), [`audio1b_build_renderers.sh`](../tools/audio1b_build_renderers.sh).
Tests: [`test_audio1b_render.py`](../tests/test_audio1b_render.py).
Metrics and hashes (no audio): [`render-validation-summary.json`](../data/audio1b/render-validation-summary.json).

Evidence tags: **verified** (executed and measured here), **independent** (confirmed by code written by someone else),
**harness-only** (checked against this repo's own harness or exporter), **proposed**, **unresolved**.

## 1. Managerial summary

**Recommendation for GameMaker AUDIO Package A: CONDITIONAL GO.**

Five genuinely audible, reproducible recordings were produced from the original driver's PSG output, and the
questions that decide Package A design now have measured answers. Nothing here is a hardware-fidelity claim.

| Question | Answer |
|---|---|
| Do the five sounds exist as audio? | Yes: 15 s of `$90 $82 $81`, and the full `$BF` (0.350 s) and `$A6` (0.617 s). 44.1 kHz 16-bit PCM WAV. |
| Is the VGM export trustworthy? | Yes. A separate parser round-trips every byte and sample time (**verified**); two unrelated PSG cores follow the registers exactly (**independent**). |
| Is the driver output itself trustworthy? | Strong evidence: Game_Music_Emu's own Z80 core executing the raw sound bank reproduces the harness's register-level pitch to about 1-1.7 cents median (**independent Z80**). Still not a hardware or cycle-exact-emulator capture. |
| Is Game_Music_Emu a safe renderer? | **No, not for `$90`.** It plays the wrong tone pitch for 73 of 282 pitch windows of the opening. `$82`, `$81`, ring and spring are fine. |
| Is a looped PCM sample-continuous? | **No, for any renderer tested.** The PSG command stream repeats exactly; oscillator phase does not, so a rendered loop needs a chosen seam or crossfade. |
| Can SFX interrupt music like the ROM? | **Yes, with per-channel stems and a tone-2 gate.** The restore rule matches the executed driver at 120 of 120 phases. A plain mix-over-music does not. |
| Opening sync? | Anchor the `$90` request to the first opening update and its fade to 30 updates after the scene ends; this keeps the accepted 738-update visuals untouched (section 7). |

**Conditions for GO:** (1) James or Manager approves the sounds by listening (timbre/aliasing, PAL vs NTSC clock);
(2) Manager approves the asset-handling plan (generated audio stays local and ignored, built from the user's own ROM);
(3) the production renderer is decided (section 8); (4) a GameMaker seam/loop test on the pinned runtime;
(5) an independent hardware or cycle-exact capture is scheduled as a later gate, not a blocker for the pilot.

## 2. Renderers: exact versions, configuration, licences

| Renderer | Version / pin | Configuration | Licence (checked) |
|---|---|---|---|
| **libvgm, MAME core** (primary) | commit `a6eed945ecf4e5a25cf82004779c6f7e4fd5c319` | `vgm2wav --samplerate 44100 --bps 16 --fade 0 --loops 1`; env `VGM_SN_CORE=MAME` | No top-level licence file in the checkout. `sn76496.c` header: `license:BSD-3-Clause`, Nicola Salmoria. Glue code licence **unresolved**. |
| libvgm, Maxim core | same commit | `VGM_SN_CORE=MAXM` | `sn76489.c` (Maxim) states **no licence**. Do not redistribute. |
| Game_Music_Emu | tag `0.6.5`, commit `9e23d10f9fd2a6a2f33b10912dd8dc7153258995` (`GME_VERSION 0x000605`) | CMake Release, shared, `GME_ZLIB=OFF`, `GME_YM2612_EMU=Nuked`; 44.1 kHz; fade start 10^9 ms; `ignore_silence`; autoload limit off; equalizer `flat` (treble 0 dB, bass 1 Hz) or GME's VGM default (treble -14 dB, bass 80 Hz) | LGPL-2.1 (`license.txt`; `Sms_Apu.cpp` header: LGPL 2.1 or later) |

Build host: gcc 13.3.0, cmake 3.28.3, Python 3.13.16, numpy 2.5.3, Linux x86_64. Two independent builds
(a private `/tmp` build and the scripted build below) produced **identical WAV hashes for all 20 files** (**verified**).

**libvgm patch (build-only, in the script, not committed):** `vgm2wav.cpp` carries a comment marking where cores
may be set; the script inserts a six-line `getenv("VGM_SN_CORE")` call there so the environment chooses the
SN76489 core. Without it libvgm picks its own default.

**Wrapper findings (verified, GME 0.6.5):**
* `gme_set_equalizer` and `gme_mute_voices` are **silently ignored if called after `gme_start_track`**. No error is returned. The wrapper calls them first. (My own first stems and "flat" renders were wrong until this was caught.)
* Output depends on the `gme_play` chunk size at sample level. The wrapper pins 4096 frames; results are deterministic for that setting.
* The default VGM equalizer colours the sound (treble -14 dB, bass 80 Hz high-pass), so `flat` is the primary GME setting.

## 3. Reproduction

Prerequisites: git, cmake, a C/C++ toolchain, Python 3.8+ with `numpy` and the repo's `requirements.txt`, the verified ROM.

```bash
python -m pip install -r requirements.txt numpy
tools/audio1b_build_renderers.sh                       # prints two `export` lines; output is git-ignored
export AUDIO1B_GME_LIB=...   AUDIO1B_VGM2WAV=...       # as printed
python tools/audio1b_render.py PATH/TO/SonicChaos.sms samples --out build/audio1/audio1b
python tools/audio1b_render.py PATH/TO/SonicChaos.sms validate --out build/audio1/audio1b   # ~30 s; add --write-summary to refresh the JSON
python tools/audio1b_render.py PATH/TO/SonicChaos.sms timeline --request 0x81 --ticks 3781
python -m unittest discover -s tests -p test_audio1b_render.py -v
python -m unittest discover -s tests -p test_audio1_psg.py -v
python -m unittest discover -s tests -p test_audio_requests.py -v      # needs SONIC_CHAOS_ROM
git diff --check
```

On Windows, `AUDIO1B_VGM2WAV` / `AUDIO1B_GME_LIB` are set with `$env:` and point at `vgm2wav.exe` / `gme.dll`. The build
script is bash (use WSL or MSYS2, or run the same CMake commands). **Windows was not tested.** The ROM path may also be given
as `$env:SONIC_CHAOS_ROM`; the tool refuses any file whose SHA-256 differs.

The clock is the provisional PAL value 3,546,893 Hz and the driver tick is 60 per second (735 samples at 44.1 kHz,
exact). Each rendered tick is one `$4000` call; all of a tick's PSG bytes are written at the tick start (a VGM wait
of 735 samples follows).

## 4. The five recordings

Primary set `build/audio1/audio1b/libvgm_mame/`. Format: RIFF PCM, 16-bit, 44,100 Hz, **stereo with identical channels**
(the PSG is mono; stereo is the renderer's container). Not looped; no fade. SHA-256 of the WAV files (this build):

| File | ID | Ticks | Seconds | Frames | SHA-256 |
|---|---|---|---|---|---|
| `90_opening.wav` | `$90` | 900 | 15.000 | 661,500 | `6c5236eeb8cea069b3afba618484fa9299bb5789d8dec890ec68417be96bd7ac` |
| `82_title.wav` | `$82` | 900 | 15.000 | 661,500 | `1508bf44d9e70260bd6a3268c8725c8af110fee2fd08af2983ca25ee01f0a16b` |
| `81_thz.wav` | `$81` | 900 | 15.000 | 661,500 | `bd62a05f02f555b8c60899b3fd0490512dbe654fbda35722971f93702785ea75` |
| `BF_ring.wav` | `$BF` | 21 | 0.350 | 15,435 | `620e59241585a81c6c9d046fbd1a6bf27d8751982fe2ffc905430e34e739ddd8` |
| `A6_spring.wav` | `$A6` | 37 | 0.617 | 27,195 | `30e98a0be3f6953835a432908ae8e0f2d958a8289958c2f916d0e457f415f34e` |

The SFX files run until every PSG attenuation reaches 15 (the driver's release tick): `$BF` 20 audible ticks + 1,
`$A6` 36 audible ticks + 1. The other renderer sets (same file names, same ticks) are in `libvgm_maxim/`, `gme_flat/`
and `gme_default/`; their hashes are in `data/audio1b/render-validation-summary.json` and reproduce from the commands above.
Three extra opening renders are in `libvgm_mame/opening_*.wav` (section 7).

**Correction to AUDIO-1.** `$A6` occupies the SFX channel for **40** ticks (so it holds tone 2 for 40) but is **audible for 36**:
its attenuation reaches 15 at tick 37 and the stream then idles. `$BF` is 20 and 20. AUDIO-1 reported channel-active
ticks. AUDIO-1 also said music "resumes at its next note onset"; the measured rule is "at the first stream read"
(section 6), which for `$82` can be a duration-only repeat-note byte, not a note byte.

## 5. Objective audio checks

All checks are in `audio1b_checks.py` and re-run by `validate`.

### 5.1 Audible, unclipped, no extra silence (verified, primary renderer)

| Sample | Peak | Headroom | Clipped frames | Leading silent frames | DC offset (fraction of full scale) |
|---|---|---|---|---|---|
| `$90` | 21,986 | 3.47 dB | 0 | 0 | -0.0108 |
| `$82` | 18,514 | 4.96 dB | 0 | 0 | -0.0114 |
| `$81` | 20,920 | 3.90 dB | 0 | 0 | -0.0132 |
| `$BF` | 8,192 | 12.04 dB | 0 | 0 | +0.0002 |
| `$A6` | 8,192 | 12.04 dB | 0 | 0 | +0.0003 |

The MAME-core output has a small constant DC offset (about 1% for music) and is naive-square (not band-limited). Both are
adapter decisions (high-pass, oversampling), not driver behaviour. GME removes DC and is band-limited.

### 5.2 Pitch against the exported registers (verified)

For every window of three or more ticks with constant period and attenuation, the pitch of the isolated channel stem is
measured by autocorrelation and compared with `clock / (32 x period)`:

| Sample | Windows | Median abs error | Max | Windows off by > 25 cents |
|---|---|---|---|---|
| `$90` libvgm MAME | 283 | 0.51 c | 1.8 c | **0** |
| `$82` libvgm MAME | 64 | 0.13 c | 1.7 c | **0** |
| `$81` libvgm MAME | 362 | 0.28 c | 1.3 c | **0** |
| `$BF` (tick level) | 14 | 1.5 c | 3.5 c | 0 |
| `$A6` (tick level) | 36 | 0.67 c | 2.0 c | 0 |
| `$90` Game_Music_Emu | 282 | 0.52 c | 998 c | **73** (ch0 14/15 late windows; ch2 59/127) |

`$82`, `$81`, `$BF`, `$A6` on GME: 0 windows off (median 0.1-0.5 c). The libvgm Maxim core also has 0 off windows on all three
music samples. This is **independent** evidence about the PSG renderers against the register file, not about the register file.

**GME `$90` defect (verified, cause unresolved).** GME plays a tone-2 (and late tone-0) note at the *next* note's pitch,
exactly 7 ticks (5,145 samples) before the register write that sets it. It survives every chunk size, VGM wait opcode, PSG
clock and write-schedule change tried, and reproduces from the register stream of a single channel. The same wrong
pitches appear when GME runs the driver through its own Z80 core (74 windows) without my VGM exporter, so the fault
is in GME's SMS PSG emulation, not the export. I did not find the root cause. Treat GME 0.6.5 as unreliable for `$90`.

### 5.3 Durations and tempo (verified)

* Per-tick audible/silent pattern of each channel stem equals the register file: **0 mismatched ticks** on all four voices of `$90`, `$82`, `$81` (libvgm MAME).
* `$BF`: audible end at sample 14,701 (expected 14,700 = 20 ticks), `$A6`: 26,460 (expected 36 x 735). Delta 0-1 samples on the MAME core; 12-30 samples (a filter tail) on GME. Both are tick-quantised: the driver cannot start or stop an effect mid-tick.
* Tempo and loop length are consequences of the driver's tick counts (AUDIO-1); the renderers add no timing drift (900 ticks = 661,500 frames exactly).

### 5.4 Noise is the Sega variant (verified, with a negative control)

The noise register file was clocked by tone 2 (NF=3) so each LFSR output bit is readable, and 1,200 bits were compared with the Sega 16-bit
(taps 0,3) and TI 15-bit (taps 0,1) sequences. The VGM header (feedback `0x0009`, width 16) selects the variant, so a TI header
is rendered as a negative control:

| Renderer | Sega header: sega16 / ti15 | TI header: sega16 / ti15 |
|---|---|---|
| libvgm MAME | **1.000** / 0.57 | 0.58 / **1.000** |
| GME (flat) | 0.91 / 0.55 | 0.55 / 0.92 |
| libvgm Maxim | 0.58 / 0.57 | 0.57 / 0.60 (**inconclusive**: my decoder does not match this core's noise clock; it ignores the header) |
| numpy reference | 1.000 / 0.57 | - |

The exporter emits the Sega header on every file. That the real chip is the Sega VDP PSG (16-bit register) is reference-documented
(MAME `segapsg`, GME `Sms_Apu` both implement it; checked in their source), not re-measured on hardware.

### 5.5 Determinism (verified)

Same process twice, and a fresh Python process: identical PCM hash for all four renderer configurations. The VGM regenerates
byte-identically from the ROM. Hashes can differ on another compiler/OS (floating-point in GME); the libvgm cores are integer-based.

### 5.6 Independence of each check

| Check | What it is independent of |
|---|---|
| Round-trip VGM parse | The exporter's code (separate parser) - **harness-only** for what the PSG bytes are |
| Pitch/duration vs registers on libvgm cores | GME and my reference; third-party PSG code - **independent** renderers |
| numpy reference synth | Written by me; independent of the third-party cores. Waveform-correlates with the MAME core at 0.9994/0.9999 (ring, spring) |
| GME-KSS run | A second Z80 core executing the same bytes - **independent Z80** (section 5.7) |
| Driver vs game IRQ path (AUDIO-1) | Same kosarev Z80 core and approximate harness - **harness-only** |
| Hardware / cycle-exact emulator | **Not done** |

Renderer agreement on per-tick loudness (DC-removed RMS correlation, MAME vs GME vs Maxim): 0.95-0.99 for music, 1.00 for SFX.
Levels differ by renderer (MAME 1.00, Maxim 0.95-0.98, GME 0.78-0.83 relative to the reference), and the Maxim core is polarity-inverted.
For `$90`, my reference differs (tick-RMS correlation 0.69-0.73): tone 0 and tone 2 are at the same period for long stretches, so their summed
loudness depends on their relative oscillator phase, which each implementation initialises differently. That is a real hardware-modelling
ambiguity (**unresolved**), not a driver difference.

### 5.7 Independent Z80: GME running the driver itself (independent)

The unmodified sound region (ROM `$8000..$FFFF` = CPU `$4000..$BFFF`) plus a 15-byte stub is wrapped as a KSS file (`kss_bytes`, local only) so
GME's own Z80 core (Kss_Cpu) executes the original driver. Per-voice pitch of that audio versus the harness's registers (NTSC clock, which
GME fixes for KSS): `$82` 64 windows, median 1.4 c, 0 off; `$81` 362 windows, median 1.0 c, 0 off; `$BF` 14, `$A6` 36, 0 off. The only failures
are the same `$90` windows as 5.2. This confirms the register timeline, not the audio hardware.

## 6. Looping and channel separation

### 6.1 `$81` recurrence (AUDIO-1: state recurs from tick 1093, period 2,688)

Rendered 1,093 + 3 x 2,688 ticks (152.6 s, in memory only).

* **PSG command stream: repeats exactly** (byte-identical per tick). **verified**
* **PCM: not sample-continuous.** Period 1 vs 2: libvgm MAME differs in 83.9% of samples (RMS difference / RMS signal 1.36); GME 99.9%. Period 2 vs 3 the same. Neither renderer repeats exactly. **verified**
* By stem (MAME): tone 0 equals itself in only 18% of samples, tone 1 77%, tone 2 86% (the rest is silence matching silence), noise 99.8%. The tone oscillators carry phase across periods; the noise LFSR is re-seeded by each noise write. Per-tick loudness still correlates 0.97 (MAME) / 0.88 (GME).
* Why: a tone counter only repeats if the period in PSG clocks is a multiple of the note periods; it is not. This is a property of the PSG, not a renderer fault; real hardware also never repeats sample-exactly.
* **Seam:** looping body 2 jumps by 7,725 LSB at the wrap, inside the ordinary step distribution (99.9th percentile 12,277; max 23,434), because square waves are all edges. Of 1,400 candidate loop starts, 90.5% (MAME) are below that percentile; the best candidate has a jump of 0.

**Consequence (proposed):** a rendered loop is a *phase-glitch seam*, one per tone channel per loop (about 45 s for THZ). Choose the loop start from the seam scan
(any tick at or after the first recurrence tick is a valid body start), or crossfade a few ms. Audibility was **not** evaluated by listening. Whether GameMaker
loops WAV or OGG without an extra gap is **unresolved**.

### 6.2 Stems and the tone-2 timeline

* `attenuation_stem` produces per-channel stems by keeping every write and forcing the other channels' attenuation to 15. They sum to the mix within 5 LSB (MAME) and 3-9 LSB (GME, `$82`, `$81`). Deleting other channels' writes, or GME's mute mask, is not a safe stem method here: GME tracks idle-oscillator phase from the write schedule, and `$90` stems do not sum.
* The timeline is the ticks at which the driver reads the tone-2 music stream (`$4341`), exported locally by `timeline` (`$81`: 414 reads in 3,781 ticks; `$82`: 79 in 900). The file is derived timing data and stays in ignored `build/`.

### 6.3 SFX interrupting music (verified)

Driver rule, tested against the executed driver at 24 request phases each for `$81`+`$BF`, `$81`+`$A6`, `$82`+`$BF`, `$82`+`$A6`, `$90`+`$BF` (120 phases):
the music tone-2 channel writes again at **the first stream read after the SFX frees the channel (`tick = request + active ticks`), never earlier: 120 of 120 matches.** The silence after the SFX ends is 1-21 ticks depending on phase.

Audio test (primary renderer; `$81` + SFX at ticks 200, 331, 702; tone-2 channel; stems + gate + one-shot versus the executed driver's combined log):

| SFX | Gate: envelope correlation | Gate: max envelope error | Naive mix: max envelope error | Other three channels |
|---|---|---|---|---|
| `$BF` | 1.000 | 0.06-0.16% of peak | 1.5-31.9% | bit-identical (0 LSB) |
| `$A6` | 1.000 | 0.15-0.38% | 35.0-39.6% | bit-identical (0 LSB) |

Waveform *phase* of the interrupted channel is not reproducible by stems (the SFX starts a fresh oscillator while the chip continues the music's), so sample equality
after the interruption is not claimed; envelope and pitch are. Tick-level pitch agreement of the gated tone 2 with the driver: 0.885-1.0.

## 7. Opening audio synchronisation

All timings are in the repo's **approximate** frame harness (PAL-like cadence: 1.2 driver ticks per update). They are the ROM's own sequence, not hardware captures.

| Event | Natural run | Skip pressed at update 70 / 300 / 600 |
|---|---|---|
| `$90` request ($189B at $06EF) | update 0 (frame 79) | same |
| Scene ends, visual fade-out begins ($1CAF) | update 738 (886 ticks) | update 70 / 300 / 600 |
| **Music fade written ($18E1, DE09/0A/0B = 12/1/2)** | **update 768 (922 ticks)** | **100 / 330 / 630** |
| Title routine ($0719) | update 799 (959 ticks) | 131 / 361 / 661 |

* The ROM fades the music only **after the scene routine returns**, 30 updates after the scene ends, on both paths. The same code runs for a skip, so a skip needs no separate audio path: only a different scene-end update.
* Fade takes **23 ticks** to silence. With one tick per update the music is silent at update 791, 8 updates before the title routine (799); at the original 1.2 cadence it is silent at tick 945 against 959.
* U5-A frames confirm: request 79, last update row 818 (738 rows from frame 81), first visual fade-out 821, title flag 880. Music fade lands at frame 847.

**Accepted POC (738 recorded updates, 60 updates/s) versus the ROM audio:** the POC runs one update per tick (60/s). The original at 50 Hz runs 1.2 ticks per update.
At the music fade the audio position is therefore **tick 769 (NTSC-equivalent) in the POC but tick 923 on the Europe original**; the original plays 154 more ticks (2.6 s) of the score
before fading. This is a regional timing property of the ROM, not an error.

**Proposed integration contract (adapter decision, no visual change):**
1. Request `$90` on the opening's first update.
2. Start the 23-tick fade **30 updates after the scene ends** (update 768 naturally; scene-end + 30 on skip). Anchoring it equivalently to **33 updates before the title handoff** (frames 847 to 880) avoids depending on how the POC counts its fade-out passes. The 2-update ambiguity between waits and frames is **unresolved**.
3. Audio ticks equal POC updates (1:1). Pre-render the natural case: `libvgm_mame/opening_natural_nominal_60hz_adapter.wav` (791 ticks = 13.18 s, fade-to-silence included, fade written before tick 769). The Europe-cadence alternative `opening_natural_pal_cadence_original.wav` (945 ticks = 15.75 s) exists for comparison; a skip render `opening_skip_at_update_300.wav` (353 ticks = 5.88 s) shows the skip shape.
4. A skip at update `u` needs the fade tail from tick `u + 30`: pre-render the fade tails at a few phases or render the opening in stems and apply the 12 attenuation steps to the stems (**proposed**, the opening fade is additive attenuation clamped at 15, not a gain multiply).
5. If Manager later wants Europe pacing (50 Hz visuals), the 1.2 cadence file is the audio for it.

I did not change or read the POC's opening implementation; the POC milestones above come from the accepted U5-A data.

## 8. Remaining fidelity risks and decisions

| Risk / decision | Status |
|---|---|
| No hardware or cycle-exact emulator PSG capture | **unresolved** (an independent Z80 was used, and an approximate harness) |
| PSG clock: PAL 3,546,893 (provisional) vs NTSC 3,579,545 Hz = 0.9% / ~15 cents | **unresolved**, Manager decision; clock values reference-documented, not re-verified |
| GME fails `$90`; libvgm cores pass but have no clear licence for their glue code | **unresolved**; see below |
| Renderer timbre: MAME/Maxim cores are naive squares (aliasing); GME is band-limited; output level and polarity differ | **unresolved**, needs listening |
| Period-0 tones (the driver starts `$90` with period-0 tones at audible attenuation): GME is silent, libvgm cores output DC | **unresolved** hardware semantics; affects about the first 7 ticks of `$90` only |
| Relative phase of equal-period channels (`$90`) | **unresolved** |
| Loop seams are phase glitches | **proposed** mitigation; not heard |
| Fade on stems is additive-clamped attenuation | **proposed**; exact only for the pre-rendered opening |
| Tick-quantised timing, PAL burst cadence smoothed to even 60 Hz | adapter |
| Windows reproduction, GameMaker playback, WAV vs OGG loop accuracy | **unresolved**, not run |

**Renderer for production (proposed):** keep libvgm's MAME core as the evaluation reference. For the Package A *tool*, choose one of (a) extracting the BSD-3 `sn76496.c` core with its notice
into a small local renderer, (b) our own renderer validated against the MAME/Maxim cores and the register log (the numpy reference is a start; it needs band-limiting), or (c) GME after the `$90` fault is understood.
No renderer code is committed to this repository; the tool only calls externally built binaries.

## 9. Tests

Run here (verified ROM and renderers present):

* `test_audio1b_render.py`: 20 tests pass (9 ROM-free, 11 needing ROM + renderers). With ROM/renderers hidden: 9 pass, 11 skipped as designed.
* `test_audio1_psg.py`: 14 pass (AUDIO-1). `test_audio_requests.py`: 8 pass (AUDIO-0).
* `audio1b_render.py validate`: runs clean with `-W error::RuntimeWarning`. `git diff --check`: clean.
* Marker test `test_gme_known_pitch_defect_on_90_is_documented` fails if GME starts rendering `$90` correctly, as a prompt to revisit section 5.2.

Not run: Windows build/run; hardware or cycle-exact emulator comparison; listening by a person (I cannot hear audio); GameMaker playback, loop points, OGG, performance; libvgm licence resolution.

## 10. Recommended next integration scope (Package A, proposed)

**In:** a local, ignored asset build for `$90 $82 $81 $BF $A6` from the user's ROM; music as two stems (tone 2 and the rest) with the stream-read timeline; the SFX one-shots;
a single GameMaker request owner implementing mailbox/priority/restart/`$F8`/steal-and-restore (AUDIO-1 rules, now validated); the exact pre-rendered opening with the section 7 contract;
a loop seam chosen by scan or crossfade; a Windows F5 checklist (opening with fade and skip, title loop, THZ loop, ring and spring over THZ, restart, `$F8`).
**Out:** other sounds, special-stage audio, arbitrary-phase fades, committed or shipped audio, any ROM bytes, hardware-fidelity claims, 50 Hz pacing.
**Gates:** the listening approval and clock decision in section 1, plus a GameMaker seam test.
