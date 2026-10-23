# M4 authentic SMS audio pilot — implementation contract

23 October 2026. **Research complete for Manager review; implementation and native listening not accepted.**

Use one offline original-driver capture pipeline and one GameMaker PCM/request owner. Package A should play opening `$90`, **title `$99` as a finite cue**, choice `$82`, THZ `$81`, ring `$BF` and ordinary spring `$A6`. Do not loop previews, substitute choice music for title, or overlay SFX onto an ungated music mix. Use the existing libvgm MAME renderer privately for the pilot; ship neither renderer nor original audio in public Git. Full audio remains M5.

## Authority, inputs and evidence classes

Canonical Research `main` AGENTS/MEMORY/ROADMAP were read from fetched `cb1aff477080842acd264331ed7fcd276b2b0497`. Their M2-closed checkpoint supersedes the historical Windows-root Q3 candidate. None was edited. This topic is a direct child of AUDIO-1B `a1b2f5e7162f76b58de8c1d17133253335ee65d2`, preserving its tools without merging other research. Read:

- [AUDIO-1 feasibility](audio1-psg-feasibility.md), original-driver design and controls; its “next note onset” shorthand is superseded by AUDIO-1B.
- [AUDIO-1B validation](audio1b-render-validation.md), renderer/pitch/stems/120 interruption phases/opening analysis.
- [AUDIO-0 audit](audio-request-audit.md) and `data/rom-cache/audio/request-ledger.json`, 70 classified IDs, request sites and mailbox rules. Its unknown `$99` name is resolved as a title request here/M1, not a new catalogue asset.
- [M1 frontend](https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/5b7f5a10232f4f6511c3a7b9d9b4deaea5842182/docs/m1-tails-frontend-contract.md) §D and [audio readiness](https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/5b7f5a10232f4f6511c3a7b9d9b4deaea5842182/docs/m1-audio-readiness.md).
- Accepted POC [M2 `d6dd1eae96ec0f7496225e3f27438e1690f6aa2a`](https://github.com/jamesfarnhamlong/SonicChaos_POC/commit/d6dd1eae96ec0f7496225e3f27438e1690f6aa2a), read only. Next Designer work must use the **subsequently accepted M3 commit**, recorded in its preflight; do not guess that future SHA.

This session genuinely has the mounted Windows workspace. The private local ROM was read and verified as SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607` before execution. A cloud successor needs that private input or authenticated generated assets. No ROM/payload is included here. **New controlled execution** below means the existing kosarev Z80 driver harness, not hardware/cycle-exact emulation. **Inherited render evidence** means AUDIO-1B's measurements, not a new audible or Windows result. **Proposed** means an implementable adapter decision awaiting Manager/Designer/native validation.

Companions: [driver evidence](../data/m4/driver-evidence.json), [opening execution](../data/m4/opening-evidence.json), [interruption evidence](../data/m4/interruption-evidence.json), [research/export tool](../tools/m4_audio.py), [opening probe](../tools/m4_opening_probe.js), [focused tests](../tests/test_m4_audio.py).

## 1. Request ownership and pilot disposition

Addresses below are ROM offsets unless explicitly CPU/RAM. Classification is numeric original ownership, not an invented musical title.

| ID | Original owner and transition | Evidence | Package A |
|---|---|---|---|
| `$90` | Opening zone7/act0 via `$06EF → $189B`; same indexed music for EEZ3 | New verified zone table `$18BA`, indexes21/17; AUDIO-1B opening capture | Opening only; never use the 15s preview as a loop |
| `$99` | Title `$0719`: waits24, requests `$BE` at `$0746`, creates title objects, waits12, requests `$99` at `$0756`; waits30 before ordinary title input loop | New byte-checked load `$0754`/store `$0756`, M1 source | Generate complete title cue; **one-shot**, no loop flag |
| `$82` | Separate choice `$3065`, art/palette setup then `$30BA/$30BC` request before `$3522` input loop | New byte-checked site; M1 | Choice entry only, restart on genuine entry/re-request |
| `$81` | THZ acts1–3 through zone/act selector `$189B`, mailbox `$D4A4` then IRQ→`$DE04` | New table check plus AUDIO-0 | THZ music start at original level-music event, not every Step or title-card draw |
| `$BF` | Terrain/object/large-ring collection, e.g. `$75D6/$7640/$302CE/$31AF3/$31C2E/$31C49` | AUDIO-0 source sites | Successful collection once; not proximity or every animation frame |
| `$A6` | Ordinary terrain/mapped spring/rebound paths `$4829/$4864/$488E/$6AC4/$7497/$74E1/...` | AUDIO-0 and spring contracts | Emit at the existing successful activation/write point, including source gates; **Spring Shoes `$C2` is a distinct effect** |
| `$BE/$B4/$A0` | Title lead-in; changed choice cursor; choice confirmation after6 updates | M1 §D; M2 choice GML already records B4/A0 | Preserve numeric event order; audible assets/wiring deferred to M5. Do not substitute BF/A6 |
| `$F8/$00` | Reset/silence via `$43E5/$43FB` / no request | AUDIO-0/1, new controls | Implement both |
| Pause / fade | Pause RAM `$DE08`; direct fade `$18E1` writes `$DE09..0B=(12,1,2)` | AUDIO-1/1B, new phase fades | Dedicated control events; **not invented music IDs** |

**Title finding, new controlled execution:** `$99` has four header channels, multiplier1, tempo0. Its last tick with any non-off attenuation register is1182; all music channels are inactive at1189. The first all-off tick1086 is **temporary silence**, not completion. The RAM recurrence1189→1190 has zero writes: it is the **terminal idle state**, not a song loop. Render1300 ticks (21⅔s including safe silence) and retain the source completion1189; do not crop at first silence or invent a repeating 15s title. Same-ID restart at tick300 reproduces a fresh title write stream. No new `$99` PCM/pitch/listening validation was possible without the renderer binary in this environment; generation/validation below is mandatory before acceptance.

Leave approved Sound Test `82_title.wav` and its hashes unchanged. Its metadata/UI for future use should say “$82 character choice (historical filename title)”. It is not an authentic title-scene asset. Old previews remain test-only and cannot satisfy the runtime manifest.

## 2. Renderer, regional clock and output decisions

**Proposed pilot selection:** reuse AUDIO-1B's pinned libvgm `a6eed945ecf4e5a25cf82004779c6f7e4fd5c319`, explicitly `VGM_SN_CORE=MAME`, 44,100Hz signed16 PCM, mono delivery after proving both source stereo lanes are equal. Keep its original level across every file; no independent stem normalization. Keep a stereo reference WAV if convenient. Mono costs88,200 bytes/s; four mono stems cost352,800 bytes/s before packaging. Produce diagnostic full mixes and all four stems; only tone2 and a sum of tone0/tone1/noise need runtime storage for these six IDs.

The isolated original Z80 driver remains **offline**. Capture ordered port bytes per tick, export deterministic VGM, and reuse the renderer. No runtime Z80, ROM-bank bundle, song decoder, VGM player extension or generic emulator is needed. New driver captures are deterministic; inherited AUDIO-1B demonstrated independent-Z80 pitch corroboration, Sega noise and stem summation. GME0.6.5 stays excluded for `$90` because of its measured early-pitch defect. Maxim is not selected: its noise test was inconclusive.

**Clock:** recommend PAL PSG3,546,893Hz, **60 evenly spaced driver ticks/s**, 735 samples/tick. Pitch and update cadence are independent. MAME's primary SMS configuration uses PAL master53,203,425 with CPU divisor15; this is consistent with retaining the existing PAL pin, not a new hardware measurement ([MAME SMS source](https://github.com/mamedev/mame/blob/master/src/mame/sega/sms.cpp)). NTSC3,579,545 is approximately15.9 cents higher. Do not accelerate/transpose PAL PCM by1.2. PAL game logic nominally50Hz requests six driver calls per five frames; this pilot retains the accepted60-update presentation and smooths that burst cadence. Exact physical PAL refresh, sub-tick writes and analogue output remain outside this fidelity tier.

**Licensing disposition:** evaluation core's BSD-3 identifier does not license the entire libvgm tool. Upstream's [licence discussion](https://github.com/ValleyBell/libvgm/issues/129) still records incomplete module licensing; no broad redistribution permission is inferred. Use the existing external build solely as the private pilot preparation/reference tool; do not redistribute its source/binaries with this report or POC. If distributing a standalone renderer later, select the explicitly BSD-3 MAME PSG implementation and independently licensed/own glue, retain copyright, licence conditions and disclaimer in source, and reproduce required notices with binaries; audit every included dependency. That is a concrete distribution need for later extraction, **not a reason to rebuild the validated tool now**. GME's LGPL alternative would need its notices/corresponding-source and linking obligations reviewed and still fails the opening check. ROM-derived output has separate rights; a core licence is not permission to publish original music. No new legal clearance or public-asset permission is asserted.

No oversampling, DC high-pass, EQ, limiter, resampler or dither change in the reference pipeline. AUDIO-1B MAME has square-wave aliasing, small DC offset and period0/relative-phase ambiguity. Listen before changing timbre. If a48kHz output path is later required, resample the synchronized complete stems with one pinned offline converter and common offsets; verify equal lengths, endpoints and pitch again. GameMaker/device resampling from44.1kHz is an explicit native unknown. OGG is deferred until decode delay/loop accuracy is measured; WAV does not itself prove seamless playback.

## 3. Private asset generation and loop contract

Run from this topic checkout. Python3.12/z80 1.2.0 and NumPy are available here; renderer build prerequisites and exact pins remain in `tools/audio1b_build_renderers.sh`. Reuse an existing binary if supplied; otherwise its existing WSL/MSYS2/CMake recipe is the reproduction route. Windows renderer build has **not** been established here. No GameMaker executable build is requested.

```powershell
$env:SONIC_CHAOS_ROM = 'PRIVATE_PATH_TO_VERIFIED_ROM.sms'
python -m pip install -r requirements.txt numpy
$env:AUDIO1B_VGM2WAV = 'PRIVATE_PATH_TO_EXISTING_PINNED_vgm2wav.exe'
python tools/m4_audio.py $env:SONIC_CHAOS_ROM evidence --out build/m4/reproduced-evidence.json
python tools/m4_audio.py $env:SONIC_CHAOS_ROM assets --out build/m4/private
```

The asset command reuses AUDIO-1B, exports full mixes, four attenuation stems, private stream-read maps and a hash manifest. It deliberately emits `loop_ready:false`. It renders `$81` through1093+2×2688 ticks, `$82` through130+2×6912, `$90`800 dry ticks, `$99`1300, BF41 and A6 61. SFX include the release/quiet hold rather than ending arbitration when their audible WAV ends. It is preparation code, **not run against a renderer here**. A missing renderer fails explicitly instead of silently selecting GME. All outputs must remain inside ignored `build/`; existing `*.sms/*.vgm/*.wav/*.ogg/*.kss` ignore rules also apply. Never stage full port streams, read timelines, per-note maps or captures in public Git.

Required acceptance library:

| Private asset | Source duration/metadata | Acceptance gate |
|---|---|---|
| `$81` synchronized tone2 + other3, intro+body | Recurrence after tick1093, period2688 (44.8s); sample boundary1093×735 before tick1094 | At least two bodies, joint seam selection below |
| `$82` synchronized tone2 + other3, intro+body | Recurrence after tick130, period6912 (115.2s); tempo divider is included | Same; never loop the15s preview |
| `$99` synchronized stems or mix |1300 ticks export; inactive1189, last non-off1182 | New pitch/duration/stem/noise/clipping/determinism checks against registers; finite completion |
| `$90` dry opening + exact fade tails |Dry800 ticks; fade-phase bank below | Prefix/tail boundary equality, every reachable fade phase, native normal/skip |
| `$BF/$A6` tone2 one-shots |Channel active20/40 ticks; AUDIO-1B audible20/36 ticks | Hold gate for driver lifetime even after audible end; no normalization |
| Manifest + request metadata |ROM/tool/source hashes; PCM hashes, format, sample counts, priority, slot, release, recurrence/cut, read/restore maps, evidence labels | Fail on missing/corrupt/wrong-format assets; deterministic restore, second restore0 |

**Loop selection algorithm:** recurrence is driver/PSG-command recurrence, **not PCM oscillator recurrence**. For music recurrence `(a,p)`, examine common cuts at tick boundaries `k∈[a,a+p)`, with prefix samples `[0,k×735)` and body `[k×735,(k+p)×735)`. Minimize the largest wrap discontinuity across four stems and their mix, normalized to their levels; ties choose earliestk. Use the samek andp for every stem and its metadata. Publish chosen numbers/hashes/metrics privately; zero PCM repetition is not required. No arbitrary crossfade or independent zero crossing per stem. If the native seam is audible, fail that gate and review a short **documented** common crossfade plus matching metadata policy before changing assets. Do not call a seam scan proof of audibility.

On repeat, sample/read-map position is `k+(age-k)%p` in tick units; absolute music age continues increasing. Intro is never replayed at wrap. Render maps through the full intro+body, including reads at the exact wrap boundary; compare one full subsequent period. Phase, gain and sample-rate drift must remain zero between stems.

## 4. One sound owner and exact request ordering

**Proposed implementation:** persistent `OBJ_chaos_audio` plus `SCR_chaos_audio`, one instance and one mono PCM output queue. Public interface:

```text
chaos_audio_request(id, source, sequence)  // write mailbox, retain diagnostic order
chaos_audio_fade(12,1,2)                  // separate ordered control
chaos_audio_pause(on)
chaos_audio_tick()                       // consume mailbox, advance once, compose735 samples
chaos_audio_shutdown()                   // release only owned resources
```

IDs remain original bytes. One mailbox models `$DE04`; multiple writes before its consumption replace the byte, **not FIFO playback of every request**. Retain an ordered diagnostic list so overwritten requests are visible. Preserve direct frontend mailbox writes versus gameplay `$D4A4→IRQ→$DE04` transfer: transfer at the documented audio boundary, not from Draw. Clear the gameplay mailbox once consumed as original code does; writing0 into it can cancel an unconsumed request. Dispatch phase matches driver order: pause/fade gate → tempo → priority/arbitration → fade advancement → selected request → channel advancement. Verify collisions between fade, stop and music against the driver before translating to GML.

Do not poll `global.chaosLastSoundRequest` for changes: same-ID restarts and two same-ID events would disappear. Replace numeric write sites with owner calls **at their existing execution point**, using an explicit stable sequence for player/terrain/object/scene scheduling. GameMaker instance order is not proof of original object order. Pin the pilot's order in tests; retain broader object-order gaps as M5 risks. A trace of written/overwritten/selected/dropped IDs must be available without a modal UI.

State includes musicID/absoluteAge/mappedPhase/active flags, priority byte, each of three eventual SFX slots `{id,age,release,stolenChannel,generation}`, channel suppression/recovery state, fade controls, pause state, PCM output cursor and queue generation. A replaced SFX invalidates old recovery callbacks by generation; no stale timer can unmute the new effect. Music init resets all slots and cursors. All four music channels continue advancing while stolen.

**Priority:** read safe metadata derived from `$906F+(id&$7F)-1`; compare the original byte with current `$DE0F`, drop strictly lower, admit equal, store admitted priority `&$7F`. Music entries read`$80`, exceeding the normal stored0..127; same-ID music restarts and clears SFX. BF/A6 both`$38`, so either replaces the other; no additive polyphony on their shared tone2 slot. Any SFX F2 clears the global priority even if another slot runs: do not replace this with “maximum priority of active effects.” All70 numeric dispatch categories can be registered, but only six have audible pilot assets. Unknown/nonpilot music stops prior music/slots and records unsupported instead of carrying THZ into another zone; unsupported SFX records the request without substituting a sound. This is an explicit pilot omission, **not complete driver coverage**. Do not emulate unrendered channel steals or claim original priority outcomes for unsupported audible effects.

**Output synchronization:** compose the two music stems and gated SFX into **one**735-sample block per tick. This guarantees intra-block synchronization and avoids Step-timed muting of independently free-running sound instances. Use wide intermediate sums, one common headroom scale if needed, then clamp with a clipping counter that must stay0. Never silence a whole mix to implement a tone2 steal. GameMaker supports [`audio_create_play_queue`](https://manual.gamemaker.io/lts/en/GameMaker_Language/GML_Reference/Asset_Management/Audio/Audio_Buffers/audio_create_play_queue.htm) with signed16/mono and completion events. Match buffer format/rate, track returned buffer IDs and queue generation, retain buffer storage until safely released; [`audio_queue_sound`](https://manual.gamemaker.io/lts/en/GameMaker_Language/GML_Reference/Asset_Management/Audio/Audio_Buffers/audio_queue_sound.htm) explicitly constrains buffer lifetime. Do not delete in-flight buffers. Target two tick buffers queued; measure underruns and request-to-speaker delay on the pinned Windows runtime before fixing that depth. No playback API/sample-exactness claim follows from this proposal.

Audio clock must be an explicit60Hz owner, independent of Draw or a menu's Step rate. M2 opening saves/restores a project clock that may be30; **one Step=one audio tick is only valid in a60Hz scene**. Bind to the accepted60-update campaign clock; in slower frontend rooms produce the corresponding number of60Hz audio ticks from one monotonic accumulator without changing visual updates. Scene requests enter before their next consumption boundary. During true game pause, freeze this accumulator/music/SFX/fade ages. Device underrun does not advance synthetic game events; log it. Catch-up, focus loss and debugger stalls need bounded native tests; do not silently retime the game to fill buffers.

Existing accepted M2 contains36 GML files referencing play/stop/pause/resume APIs, numeric-only writers, legacy adapter sounds, `global.music`, developer Sound Test and room/reset owners. Mandatory Designer inventory covers **all** such references in the accepted M3 tree. Under pilot mode, gate legacy BF/A6 and duplicate jump/spring aliases once; leave unsupported cues silent rather than inherited unrelated audio. Route scene/reset/pause through this owner. Debug Sound Test suspends the pilot owner and tears down its voices; closing it re-enters the active scene through the scene owner. `audio_stop_all`/pause-all may not leave a live owner queue or silently kill unrelated developer playback.

## 5. Steal, recovery, stop, pause and fade contracts

- **BF/A6:** both steal music tone2. On accepted request tick`s`, replace prior slot, mute only tone2 and start the one-shot at sample`(s−1)×735`. Keep the other three stems at their uninterrupted positions. Release on`s+20` or`s+40`. A6 has four silent hold ticks after its36 audible ticks; those still own the slot.
- **Recovery:** release writes attenuation-off, clears stolen bit2 and sets suppression bit4. Unmute at the **first eligible stream read after release**, even a duration-only repeat-note read; never universally “next note onset” or immediately at WAV end. Use the private original-driver read map with current music phase, tempo and loop offset; silent/rest reads are valid state changes and may remain acoustically silent. Do not search for the next audible sample.
- **Evidence:** AUDIO-1B's five pairs×24 phases were rerun using its original range150..699 step23:120/120. New title phases100..123×BF/A6 clear suppression at the eligible read:48/48. The inherited **any-tone2-write** predicate instead reports27/48 match (21 FAIL), because `$DF` off writes can occur before recovery. Example title+BF at100: release120, off write129, flag still`$90`; stream read133 clears bit4 and reasserts tone2. Raw failed predicate results are retained, not relabelled PASS. No native waveform or universal all-song assertion follows.
- **Repeated effects:** equal priority replaces and restarts, resets release relative to the new request and invalidates old recovery. Tests cover BF→BF and BF→A6 five ticks apart. High-priority metadata controls test drop/admit; do not queue a dropped effect for later. Noise/tone1 steals and multi-slot full-library recovery remain M5 implementation scope.
- **`$F8`:** same consumed tick clears all logical voices/fade/recovery and emits silence. Flush output queued from the old generation so a new scene cannot leak old music. “Same tick” is logical; queued/device latency is measured separately. `$00` does not restart or stop an already running song.
- **Pause:** original first paused tick mutes, freezes driver evolution and resume reasserts registers within1–3 ticks (inherited). Recommended pilot pauses the owned output voice at its sample cursor and freezes every logical age/map; resume continues that cursor. This preserves synchronized stems but **does not reproduce the original1–3 tick PSG reassertion latency or chip phase**. Mark this deliberate adapter. Do not drain buffers into continuing music while gameplay is paused, or reset/advance effects under a frozen picture.
- **Fades:** `$18E1` adds channel attenuation with clamp, not linear gain. Phase tests here reset after23 inclusive ticks at five phases. Arbitrary PCM gain ramps are an approximation; title/choice/THZ exit fades in Package A may use a documented23-tick2dB-step gain envelope followed by reset, but cannot claim exact envelope/clamp/SFX interaction. New music init cancels old fades/slots. Stop/reset always wins according to observed ordered writes, not a hardcoded global priority rule. Unknown `$D1/$D3` paths are unsupported, not guessed.

For the opening, avoid the generic approximation: generate exact private fade tails at every reachable fade phase. For each fade tick`F=9..745`, call `capture(rom,0x90,F+22,{F:[('fade',(12,1,2))]})`, render **the full prefix+tail from reset** with `audio1b_render.build_vgm` and the selected renderer, then retain samples`[(F−1)×735:(F+22)×735]` as that23-tick tail. Compare the rendered prefix beforeF against the dry render (must match exactly for the pinned deterministic renderer); compare captured post-fade bytes/state against fresh driver execution. Switching at that precise shared sample boundary then preserves oscillator state through the fade. Append zeros until title. A737-tail mono bank is about24.9MB raw, build-time work only. This has **not been generated/rendered here**; it is an exact reproducible preparation algorithm with mandatory equality checks, not an accepted asset bank. Do not render the23-tick tail from a fresh PSG reset. Opening has no pilot SFX, so a mixed tail is sufficient.

## 6. Opening reconciliation — protect every visual update

**Measured M2 GML execution:** `CHAOS_OPENING_LAST_UPDATE=737`; first host Step displaysu0; natural post entry`E=738`; `post_ticks=(3−1)×5+30=40`; room/title handoff`H=778`. Skip at host tick70/300/600 givesH110/340/640. Press on tick1 is ignored by the existing`u>=0` gate; tick2 is the earliest skip. Script and Create/Step/Draw remain unchanged. These are Node VM GML executions, not fresh Windows acceptance.

AUDIO-1B ROM harness measured logical scene end738, audio fade768, title799, with23 driver fade ticks. It explicitly had **not read the POC implementation**. The POC40-update post period versus approximately61 original updates is a **material21-update timing difference**, not merely its earlier unresolved2-update counting uncertainty. Both observations are retained. Moving the original fade toE+30 in M2 would leave only10 ticks before title and truncate the23-tick fade. Extending the picture/black wait to fix it would change accepted visuals and is forbidden here.

**Recommended explicit audio adapter:** request90 immediately before first opening audio tick. On post entryE, schedule fade at`F=H−33=E+7`, notE+30. Apply before tickF; original driver reset occurs atF+22=H−11; ticksH−10..H−1 are silent. NaturalF745/reset767/H778. Skip70 givesF77/reset99/H110; skip300 givesF307/reset329/H340. Use matching exact tail. This retains a completed original fade and a short pre-title silence without moving visuals; **the fade starts23 updates earlier relative to accepted post entry than the ROM E+30 contract**. Manager must review this declared timing adaptation, not assume ROM sync. Do not reuse AUDIO-1B's791-tick natural adapter WAV: it would outlive M2's778-tick opening.

At title **entry**, ensure opening state is reset. Then let the M3 frontend issue its original title events: BE after24 waits (audible later scope),99 after another12 waits; never start82 at title entry. On choice entry82 replaces title through music init; on THZ level-music event81 replaces choice. M3 must export semantic events (title-enter/title-sound99/choice-sound82/level-music), so Designer need not guess timing from room age, draw/fade state or object existence. Relative to each actual request, the private audio begins at its next tick boundary. Do not lengthen/shorten M3 frontend animations to fit WAV length. A skip goes to title, never directly to choice/gameplay.

PAL difference: at50 visual updates/s the original plays about1.2 driver ticks per visual update. The accepted60Hz opening plays fewer score ticks before its visual end. PAL-pitch audio at60 ticks/s does not restore PAL wall-time/visual synchronization; that discrepancy is deliberate and recorded. Full PAL visual pacing is outside this assignment.

## 7. Focused verification and eventual Windows listening

New controls:9 tests in `test_m4_audio.py`; deterministic numeric regeneration, finite title/temporary silence, restart/last-writer evidence, priority lower/equal/higher,00/F8, repeated SFX, music-over-SFX, pause freeze/resume and seven GML opening paths. Private numeric evidence is regenerated from the ROM, not asserted solely from the prose. Existing suites and results are recorded in `data/m4/verification.json`; renderer-dependent tests are skipped when the binaries are absent. No new rendering, audible listening, Windows Runner, executable, M3 code review or all70 runtime test occurred here.

Designer preflight must add tests of the **actual GML owner**, not just this original-driver model: frame-order mailbox overwrite, repeated same ID, loop-wrap recovery/read boundary, stopped/paused/fading state, restart while SFX runs, priority rejection, missing/corrupt assets, old-generation callbacks,30Hz menu/60Hz audio cadence, queue lifetime/underrun and scene transitions. Compare emitted gates/requests against driver controls, including raw known failures; sample synchronization and clipping counters must pass. Register-read maps and exact opening tail switching need offline boundary checks for every supported phase. Native queue/seam/timbre approval remains required.

One concise Chief Windows348×196 session after automated preflight:

1. Normal opening→title, then early/mid/late skip: unchanged pictures/fades/handoff; opening ends cleanly, correct99 at title event, no82/title substitution or duplicate playback.
2. New Game choice→Sonic THZ, then Tails start:82 only on choice;81 at the level event; correct finite99 completion if title persists. Deferred B4/A0/BE are labelled omissions in the test card.
3. THZ collect rings and hit an ordinary spring, repeat/alternate quickly while music runs: tone2 steal/quiet recovery, no doubled SFX, wrong stinger or whole-song mute. Pause/resume during an effect and near a loop wrap; no drift or late recovery.
4. Dedicated audio fixture: same-ID restart, lower/equal/higher priority,00/F8, title/choice/THZ transitions and both loop seams (seek near seam to avoid two minutes waiting). Check CPU/queue health, clipping, clicks and stuck/leaking audio on return/disable. No full campaign requested.

Record listening judgement separately from numeric PASS. Existing M2/Q3 gameplay acceptance remains intact; do not claim sound parity from those silent campaigns.

## 8. Proposed M4 Package A and remaining risks

**In:** the six audible IDs above,00/F8, one owner/queue, private validated full assets, source event hooks for opening/title/choice/THZ/ring/spring, same-ID restart, pilot priority and tone2 steal/recovery, pause, documented generic fade approximation, exact-phase opening fade bank and explicit timing adapter, Sound Test isolation, restore manifest, focused tests, one private source-only package and listening session. The six includes newly generated99; five old Sound Test previews are insufficient.

**Out:** full70-ID library, audible BE/B4/A0 and other UI cues, other-zone/boss/SS/power-up/death/ending audio, Tails flight/C2, tone1/noise/full multi-slot arbitration, runtime Z80/PSG, hardware-analogue parity, new PC volume/options features, visual/frontend modifications, compiled executable and public audio. Unsupported music must not leak the pilot song into these scenes. M5 extends the same numeric owner and documented source ordering, not a second subsystem.

Manager review decisions are concrete: accept PAL pitch+60Hz cadence, theE+7 opening fade adaptation, private external renderer use, finite title, single PCM queue, declared pause/generic-fade approximations and six-ID pilot omissions. Remaining technical risks: new99 render validation; pinned renderer availability/build on Windows; loop seam audibility; queue latency/performance/format handling in the accepted runtime; all-phase tail-bank equality; arbitrary fades and multi-slot arbitration; source-vs-instance request order; device resampling, oscillator phase/period0/DC/aliasing and absence of hardware comparison. These are explicit implementation/native gates and M5 risks, not claims of completed runtime fidelity.

Stop here for Manager review. No GameMaker file, canonical management document, executable or public original-audio payload was changed or produced by this Research milestone.
