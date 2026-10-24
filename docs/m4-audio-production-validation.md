# M4 private audio production and objective validation

24 October 2026. Manager-san #6 assignment, following accepted [M4 contract `cbf3e9c`](m4-audio-pilot-specification.md). **Production pass complete; private assets ready for Manager review and later Designer integration. Listening, native GameMaker playback and inaudibility are not claimed.**

The six requested IDs were rendered from the SHA-256-verified SMS Europe v1.2 ROM using the pinned libvgm MAME PSG core, at approved PAL3,546,893Hz and60 driver ticks/s. No GameMaker/M3 file, executable build, Research main merge or management-document edit occurred. The only executable compiled was the expressly authorised private offline renderer. No renderer binary, WAV, VGM, original ROM, full read map or private ZIP belongs in the public commit.

## Deliverables and provenance

Private package, relative to this Research worktree:

`build/m4/SonicChaos_M4_AUDIO_20261024_PRIVATE.zip`

- ZIP SHA-256: `a5a636ade42a48526b76cf85abb7783f0d9cf50e6817a39b37aec4cbba4a53b9`
- 47,304,292 bytes; **1,561 members**; ZIP CRC and every manifest member hash verified.
- One authoritative private `manifest.json`, SHA-256 `c57d37af7a8d4c7e83acbf1a1b2c9ef13ef4066e482cf575438006c30040d722`.
- Includes six complete preparation renders, original synchronized raw stems, grouped runtime stems, private VGM/reference WAVs/read maps, selected loop intervals,737 phase tails, five full opening listening fixtures, numeric private receipts and restoration/integration instructions.
- Public numeric evidence: [production-validation.json](../data/m4/production-validation.json). Fresh restoration evidence: [production-restoration.json](../data/m4/production-restoration.json). These contain measurements/hashes, not audio or stream contents.

Canonical Research main AGENTS/MEMORY/ROADMAP were fetched/read again; work continues only on `research/m4-audio-integration`, after accepted `cbf3e9c`. The private local ROM was verified before each generation command: `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`. Existing accepted M2 source was not modified. Designer must use the separately accepted future M3 commit, not this report as permission to change M3.

### Renderer availability resolved

No existing `vgm2wav` was found in the checked local audio/Research build locations. Visual Studio did not have a C/C++ compiler; Ubuntu had neither GCC nor CMake/zlib headers. A portable, workspace-only Windows toolchain built the **existing renderer**, not a replacement PSG implementation:

| Component | Exact selection |
|---|---|
| libvgm | `a6eed945ecf4e5a25cf82004779c6f7e4fd5c319`, same AUDIO-1B pin |
| PSG | `SNDEMU__ALL=OFF`, `SNDEMU_SN76496_MAME=ON`; only MAME enabled; `VGM_SN_CORE=MAME` |
| Build-only patch | Same AUDIO-1B environment-based `set_core` patch; no PSG core edits |
| Patched `vgm2wav.cpp` SHA-256 | `1958c83e225e7d1192417cf951b45b218661151b4ce0ba6ed45628ba21ad5ce7` |
| zlib | v1.3.1, commit `51b7f2abdade71cd9bb0e7a373ef2610ec6f9daf` |
| Compiler/build tools | Zig0.13.0 / Clang18.1.6, target`x86_64-windows-gnu`; CMake4.4.4; Ninja1.13.2 |
| Private renderer binary SHA-256 | `36821f4cfb6a1b6e386f1b468504245c21c6e24a2cbb0cba4b268703c96334a0` |
| Invocation | `--samplerate 44100 --bps 16 --fade 0 --loops 1` |

Initial restricted-token compiler cache writes failed; the authorised private build succeeded outside that sandbox. zlib's generated `zconf.h` required pointing libvgm at the binary include directory. Both are resolved environment/build issues; no audio was substituted. Cores, renderer and compression source remain ignored/private. The renderer distribution/licence limits in the accepted contract still apply; this is not a new legal clearance.

**Cross-platform conformance:** reproducing all five original AUDIO-1B reference lengths yielded **byte-identical WAV SHA-256s** to its Linux build:90/82/81 at900 ticks, BF21 and A6 37. Thus the restricted MAME-only Windows build reproduces the already validated core/format pipeline, rather than merely having a matching executable name. Each of the six new full mixes also matched a second fresh renderer process exactly.

## Six-ID production results

Delivery WAVs are **44,100Hz, signed16 little-endian mono**. Original renderer reference WAVs are stereo with identical lanes. One driver tick is735 samples. No per-file normalization, EQ, high-pass, resampling, crossfade, invented loop or compressed-codec conversion was applied.

| ID / ownership | Rendered ticks | Samples per lane | Seconds | Peak /32768 | Pitch windows | Maximum absolute error |
|---|---:|---:|---:|---:|---:|---:|
|90 opening dry prefix |800 |588,000 |13.333333 |21,986 | See numeric evidence |1.394 cents |
|99 finite title |1,300 |955,500 |21.666667 |20,920 |425 |2.969 cents |
|82 character choice |13,954 |10,256,190 |232.566667 |18,514 | See numeric evidence |1.749 cents |
|81 THZ |6,469 |4,754,715 |107.816667 |20,920 | See numeric evidence |1.920 cents |
|BF ring |41 |30,135 |0.683333 |8,192 | See numeric evidence |3.490 cents |
|A6 ordinary spring |61 |44,835 |1.016667 |8,192 | See numeric evidence |2.041 cents |

**All six:** zero detected clipped frames; identical stereo lanes; zero constant-period pitch windows beyond25 cents; zero audible/silent tick-pattern mismatches against decoded PSG registers on every measured voice. SFX retain quiet post-release padding intentionally; the padded WAV lengths are not arbitration lifetimes. Full precision counts and per-channel results are in the numeric evidence/private manifest. The mix output has inherited small DC offset and naive-square aliasing; these were not silently filtered.

### Newly produced title99

This is the original request at title site`$0756`, not the historical82 “title” preview filename. Independent signal measurements on the new rendered output give:

- 425 pitch windows over three tone voices, zero >25-cent failures; median0.733 cents, maximum2.969 cents.
- Zero expected/measured audible-tick mismatches on all four PSG voices, zero clipping, peak20,920 (3.90dB headroom).
- All music channels inactive at original driver tick1189. Its last non-off register tick is1182. PCM after sample`1189×735` is exactly zero. The first all-off tick1086 remains a temporary rest; it is not used as an endpoint.
- The 1300-tick output includes86,735 trailing samples at or below the signal threshold used by AUDIO-1B's sanity check. Retaining complete cue/padding avoids cropping on transient silence. **No title loop is defined.**
- Fresh renderer-process output is bit-identical. The separately implemented AUDIO-1B counter/LFSR synthesizer gives tick-RMS envelope correlation0.99634; raw waveform correlation0.6390 is not sample parity. Its difference is consistent with the documented renderer phase/model limits; this is not a causal decomposition of every sample difference. This check is independent of MAME's synthesis code, not a second ROM/hardware execution.

### Stem summation: preserved raw failure and exact runtime grouping

The raw four isolated attenuation stems reach a **6-LSB** maximum sum difference for99 and the longer82/81 renders, versus AUDIO-1B's **observed5-LSB** maximum for its short samples. The initial5-LSB assertion therefore failed; that comparison remains explicitly **FAIL** in the evidence for those three full renders.90 reaches5; BF/A6 zero. It has not been relabelled an inherited5-LSB PASS.

The renderer performs integer quantization in the core (`out >>1`), resampler division, volume/output conversion (`24→16 >>8`); separately rendered, then summed stems need not equal a once-quantized mix. Title residual RMS is approximately1.43 LSB, maximum6 (about−74.7dBFS). Source arithmetic is consistent with a rounding residual; no new hardware-mixing equivalence is asserted. An explicit8-LSB production guard was used, distinguished from the inherited observed maximum, and is visible for Manager review.

To avoid handing Designer that reconstruction difference, all raw stems remain intact and a separate runtime group is supplied:

```text
other3.wav = reference_mix.wav − ch2.wav
ch2.wav + other3.wav = reference_mix.wav, exactly at every sample
```

`other3-raw.wav` preserves `ch0+ch1+ch3`. The grouped runtime stem differs from that raw sum by at most6 LSB; it receives only the measured integer residual, with no normalization or timing shift. All six runtime two-stem sums have **zero sample error**. This is a documented quantization reconciliation, not an assertion that the raw four-stem comparison passed or an invented replacement sound. During tone2 steals, the grouped other3 residual remains; the known hybrid waveform/oscillator-phase limits remain unchanged.

## Stream maps and recovery

Each full original-driver capture includes a private channel read map from CPU`$4341`; the pilot authority is its tone2 map. Do not infer full future noise/tone1 stream coverage from this hook. Music age/stream timing advances while tone2 is stolen; map phase is never rewound or paused with the effect.

- **192/192** new flag-based phase checks: four pilot music IDs × BF/A6 ×24 request phases. Restoration is the eligible read after release, not an arbitrary attenuation-off write. This extends the earlier120-phase coverage without invalidating its documented predicate limits.
- **Four loop-wrap controls** pass for81/82 with BF/A6. Requests straddle the selected wrap; original-driver recovery matches the unrolled map, including the intro/body offset.
- A late A6 over finite title99 finishes with all channels inactive; terminated title music is not resurrected.
- BF owns tone2 for20 ticks, A6 for40; audible spans remain20/36 ticks. The supplied files include padding and private header/release metadata. No “resume when WAV ends” rule is introduced.
- Six rerun original-driver-versus-gated-audio experiments over THZ at ticks200/331/702 give envelope correlation1.000, maximum envelope error0.06–0.38% of peak; the other three channels are bit-identical. Naive overlay errors reach39.64%. Tone2 pitch agreement is0.885–1.000, **not universal waveform equality**: fresh one-shot oscillator phase remains a known hybrid compromise.

### Common loop seams

The driver command periods repeat exactly. A joint tick-boundary scan minimizes the worst normalized wrap jump over all four raw stems plus mix, then selects the earliest tie. No crossfade was applied. These loops are for82/81 only;90 is the finite opening use,99 a finite cue.

| ID | Driver recurrence after tick | Period | Selected common cut after tick | `[start,end)` samples | Measured endpoint jump |
|---|---:|---:|---:|---|---|
|81 |1093 |2688 ticks /44.8s |1311 |`[963585,2939265)` |0 LSB on all four stems and mix |
|82 |130 |6912 ticks /115.2s |1879 |`[1381065,6461385)` |0 LSB on all four stems and mix |

Prefix is`[0,start)` and repeats use exactly that common body, including private read-map phase. The residual-corrected runtime group also has zero endpoint jump because mix and tone2 do. Ordinary per-channel/mix step distributions are retained in the evidence (mix99.9th percentile12,320 LSB for81;10,249 for82). **Zero endpoint difference is not proof of phase continuity over the surrounding waveform, an inaudible seam or gapless GameMaker playback.** Native listening remains necessary. Do not loop the entire preparation WAV or the15-second historical previews.

## Opening exact-phase fade bank

All **737** reachable fade ticks`F=9..745` were generated from continuous prefix+fade execution, applying original `(DE09,DE0A,DE0B)=(12,1,2)` beforeF. The selected phase's full prefix is rendered from reset once, checked against dry90, and only its23-tick tail is retained. Completed hashes/receipts cache each phase; four workers batch missing phases. No phase tail is rendered from a fresh standalone PSG reset.

**737/737 prefix comparisons are sample-exact.** Original driver reset isF+22 for every phase. The first PCM sample of that reset tick can retain the preceding attenuation in libvgm's fractional resampling bucket: worst887 LSB, **at most one sample (22.676μs)**. Every subsequent sample in that tick is exactly zero. The initial “whole reset tick must be zero” assertion failed; the one-sample behavior was measured, preserved and reported rather than zeroed. The renderer's independent SFX end check already allowed its0–1 sample boundary behavior; no new audio timing shift was invented.

Five complete compositions were compared with fresh full continuous driver/render executions, including prefix-to-tail splice and silence through handoff. **Every composition has zero sample difference.**

| Accepted post entryE | Fade beforeF=E+7 | ResetF+22 | Title handoffH=E+40 | Reconstruction error |
|---:|---:|---:|---:|---:|
|2 (earliest skip) |9 |31 |42 |0 |
|70 |77 |99 |110 |0 |
|300 |307 |329 |340 |0 |
|600 |607 |629 |640 |0 |
|738 (natural/latest) |745 |767 |778 |0 |

This is the approved M2 audio-only timing adaptation, **not the original PAL wall-time sequence**. First-tick skip remains ignored by accepted opening logic. Visual updates/fades are untouched. Use dry samples`[0,(F−1)×735)`, then`opening-tails/fade_FFFF.wav`, then zeros untilH. The bank includes five complete listen_E fixtures for the eventual short listening session. Their existence is not listening acceptance.

## Reproduction and restoration

The build/generation scripts add no GameMaker dependencies. Run in this Research checkout, keeping all payloads below ignored`build/`. Acquire the ROM privately; its hash guard is mandatory. Reuse the resulting renderer for future work rather than rebuilding it.

```powershell
python -m pip install --target build/deps -r requirements.txt numpy
python -m pip install --target build/m4/tooldeps cmake==4.4.4 ninja==1.13.2 ziglang==0.13.0
# Private source checkouts:
git clone --no-checkout https://github.com/ValleyBell/libvgm.git build/m4/renderer/libvgm-src
git -C build/m4/renderer/libvgm-src checkout --detach a6eed945ecf4e5a25cf82004779c6f7e4fd5c319
git clone --depth 1 --branch v1.3.1 https://github.com/madler/zlib.git build/m4/renderer/zlib-src
python tools/m4_build_renderer.py
# If the restricted token prevents compiler-cache writes, run this authorised
# build in a normal user PowerShell. No system-wide compiler install is needed.
$env:PYTHONPATH = 'build/deps'
$env:AUDIO1B_VGM2WAV = (Resolve-Path build/m4/renderer/libvgm-build/bin/vgm2wav.exe).Path
New-Item -ItemType Directory -Force build/m4/tmp | Out-Null
$env:TEMP = (Resolve-Path build/m4/tmp).Path
$env:TMP = $env:TEMP
$rom = 'PRIVATE_VERIFIED_ROM.sms'
python tools/m4_produce_audio.py $rom library
python tools/m4_produce_audio.py $rom tails --jobs 4
python tools/m4_produce_audio.py $rom package
```

Library caches are keyed by VGM+renderer bytes and verify saved raw WAV hashes. They avoid repeating completed stem renders, while a separate fresh renderer process remains the determinism check. Tail caches verify renderer and tail hashes. Reproduction must use the recorded source/tool versions; modified inputs require invalidating the corresponding ignored cache. The private manifest records tool-source raw-byte hashes, ROM hash, renderer provenance, all file hashes, format, sample counts, loops, stem and fade policies. Binary build hashes can vary with toolchain; the five AUDIO-1B PCM/WAV conformance hashes and validation outcomes are the functional reproduction gate.

Restore the private package to a new private directory using its independently supplied ZIP hash:

```powershell
python tools/m4_restore_audio.py build/m4/SonicChaos_M4_AUDIO_20261024_PRIVATE.zip build/m4/restored --sha256 a5a636ade42a48526b76cf85abb7783f0d9cf50e6817a39b37aec4cbba4a53b9
python tools/m4_restore_audio.py build/m4/SonicChaos_M4_AUDIO_20261024_PRIVATE.zip build/m4/restored --sha256 a5a636ade42a48526b76cf85abb7783f0d9cf50e6817a39b37aec4cbba4a53b9 --check
```

The restoration tool checks the archive hash, CRC, exact unique member inventory, traversal-safe destinations and every member hash **before writing**, then atomically installs changed files. It never deletes files. Fresh restore, immediate second restore0, check-only, deliberately corrupted local WAV detection/repair and wrong-archive-hash rejection were exercised; counts are in the restoration receipt. Neither the ROM nor renderer is needed to restore these verified generated assets.

## Focused final checks

The nine M4 original-driver/control tests and nine AUDIO-1B ROM-free renderer/export tests passed (18/18, no skips/errors). Production invariant checks confirm six runtime stem reconstructions, five byte-identical AUDIO-1B samples,737 exact phase prefixes, five complete opening compositions,192 recovery phases, four wrap controls and six waveform-envelope controls. Scripts compile and `git diff --check` is clean. See [production-checks.json](../data/m4/production-checks.json). These reuse the scoped production evidence; no broad unrelated gameplay suite or native Runner was run.

## Handoff and remaining acceptance

Designer receives the private ZIP plus accepted dispatcher contract, the selected sample intervals/read maps and exact opening bank. Keep only these six IDs enabled; the remaining M5 catalogue, extra frontend/SFX cues and complete multi-slot driver behavior are not supplied. Preserve original priority/mailbox order, same-ID restarts, F8, declared pause/generic-fade approximations and tone2 recovery contract. Do not confuse native queue scheduling with these offline tests.

One later short Windows listening session should cover normal/early/mid/late opening, finite99→choice82→THZ81, rings/springs while music runs, repeated effects/pause/reset, and seek-near-boundary81/82 loops. No full campaign, M3 recompilation or extra gameplay test cycle was requested here. Timbre, loop audibility, device resampling, runtime queue latency/underruns and original-chip waveform phase remain unaccepted natively. The raw6-LSB stem residual and one-sample reset boundary are explicit numeric qualifications for Manager review, not concealed parity claims.

Stop for Manager review after this production pass. Public commits contain only source scripts, this report and safe numeric results; the47MB original-audio package stays local/private.
