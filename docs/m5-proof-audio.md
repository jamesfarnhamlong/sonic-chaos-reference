# M5-P1 selected audio and coupled-noise proof — composition FAIL / HOLD

24 October 2026. This is a temporary PRIVATE proof, not a GameMaker release.
No P2/P3 track, Sound Test implementation or POC asset/source change occurred.
All WAV/PCM/VGM/register/read/event data remain below ignored
`build/m5-proof/`. Only non-reconstructive numeric results are public.

## Solo production and provenance

[m5p1_proof.py](../tools/m5p1_proof.py) reused the existing pinned M4 renderer:
libvgm `a6eed945ecf4e5a25cf82004779c6f7e4fd5c319`, MAME PSG only, executable
SHA-256 `36821f4cfb6a1b6e386f1b468504245c21c6e24a2cbb0cba4b268703c96334a0`.
No compiler/core/toolchain change. PAL3,546,893Hz,60 driver ticks/s,735 samples
per tick,44,100Hz signed16 mono delivery; stereo reference lanes match.
No normalization, EQ, resampling, crossfade or alternative synthesis.

The eight requested IDs88/A0/A3/AC/B6/BA/BC/C0 were produced with20 post-end
ticks. One additional **diagnostic-only B8** captures fixed-rate noise for the
explicit required fixed-rate interaction. The selected noise IDs all execute
tone2-clocked F3; B8 is the indexed SFX with fixed-rate F3. B8 is not an
additional proposed production batch. BF/A6 and existing81/82/99 references
were reused from authenticated M4 files; no M4 library regeneration.

Original ROM headers and independent slot release times are recorded with
each render. Private manifest hashes cover every reference, stem and derived
experimental file; public [p1-library.json](../data/m5-proof/p1-library.json)
contains header identity, format, endpoint, mix/stream hashes and metrics.
BC/C0 mixed WAV hashes match; their raw priorities remain60/40 respectively.

| ID | Total ticks with pad | Slot completion ticks, request-at1 | Max raw stem-sum residual |
|---|---:|---|---:|
|88 |232 |all music inactive212 |5LSB |
|A0 |66 |tone2 46 |0 |
|A3 |69 |noise49 |0 |
|AC |74 |noise49 /tone1 54 |1 |
|B6 |47 |noise16 /tone1 27 |3 |
|BA |45 |noise5 /tone1 25 |3 |
|BC |49 |tone2 29 |0 |
|C0 |49 |tone2 29 |0 |
|B8 diagnostic |159 |noise139 |0 |

All nine: matching stereo reference lanes, expected sample count, separate
fresh-process determinism, zero clipping and zero measured pitch windows beyond
the inherited25-cent guard. Noise RMS/zero-crossing/spectral diagnostics are
recorded; the spectral metric uses the tool's stated nonzero-sample segment and
is descriptive, not proof of hardware timbre. Sega PSG core/clock conformance
reuses accepted M4 evidence, not a newly claimed hardware comparison.

**Raw duration-proxy failure retained:** A3 has1 expected-register/AC-RMS gate
mismatch at its first tick. Its first735 samples are constant−4096, with AC RMS0,
despite a non-off noise attenuation register. Thus attenuation alone does not
prove an oscillating/audible signal in that startup tick. Nothing was cropped,
zeroed or changed to pass the test. This is a measured output/metric qualification;
analogue DC audibility and listening are not established. Other solo per-voice
register-versus-RMS gate comparisons pass. No aggregate “all duration PASS”.

## Four-voice residual experiment

Raw schedule-preserving four-voice MAME stems are retained. Experimental
tone0 receives `reference mix − sum(raw voices)`; other voices are unchanged.
All nine solo reconstructions equal the reference at every sample, without
clipping. The residual is at most5LSB in this selection. For effects whose
original tone0 is silent, this can introduce a tiny nonzero residual on a voice
that has no effect slot. That is an explicit experimental limitation, not an
accepted original channel assignment or approved runtime algorithm.

Existing M4 tone2 and other3 bytes remain intact. Experimental music tone0
is computed from accepted other3 minus original tone1/noise; unmodified other
voices then sum to accepted M4 output. Before/after SHA-256 checks cover36
authenticated M4 preparation WAVs plus11 accepted private POC PCM files
(47 files). Neither the production cache nor GameMaker repository was written.

## Continuous original driver versus composed PCM

Nine required scenarios were captured continuously from the original driver
and rendered without PSG restarts at event boundaries. Their full references,
four isolated reference voices and deliberately experimental compositions are
private. Exact ownership/priority/tempo/mailbox/fade projections match the
original executions at every compared tick. This **does not** imply register
or sample equality: dry-template register projections and PCM are tested
separately, with failures retained in [coupled-noise.json](../data/m5-proof/coupled-noise.json).

| Case | Mix envelope correlation | Max tick RMS difference, % reference peak | Register projection |
|---|---:|---:|---|
|BF→A3 |0.997292 |3.224 |audible components match |
|A3→BF |0.987361 |7.929 |audible components match |
|AC→A0 |0.997211 |4.008 |audible components match |
|B6→A0 |0.988854 |18.314 |1 tone1 attenuation tick differs |
|BA partial replacement |0.978821 |28.138 |audible components match |
|fixed-rate B8+BC |0.806784 |21.336 |104 audible noise attenuation/control ticks differ |
|A6 near81 selected loop boundary |0.998814 |16.573 |audible components match |
|fade with several slots |0.999878 |2.025 |retained generic-fade projection differences |
|late A6 over finite99 |0.999995 |1.471 |audible components match |

“Audible components” compares tone periods when original attenuation is non-off,
each audible attenuation, and audible noise control; it does not compare stale
muted period registers. **Exact register parity is FAIL** for the named cases.
**All nine mixed waveforms differ sample-wise.** Per-voice waveform/envelope
correlations, reference/composed pitch and noise metrics are retained. Measured
pitch windows remain within25 cents in both sets, which does not establish
waveform or envelope equivalence.

Fresh standalone oscillators/noise state and relative phase can produce unlike
waveforms and coherent interference in a multi-tone sum, even when individual
voice RMS/pitch match. This was already a documented M4 limitation. The new
fixed-rate failure is categorically different: [driver proof](m5-proof-driver.md)
demonstrates104 ticks of held PSG noise incorrectly muted by the prototype.
Noise-only envelope correlation falls to0.37463. This is a real unsupported
ownership/output class, not excused by phase or diluted in an aggregate PASS.
The one B6 attenuation tick remains unresolved. Generic fade remains an approved
approximation, not register/sample parity.

The near-loop case uses the existing continuously captured unrolled81 source
around its selected3999-tick boundary. Driver recovery is checked there; intro/
body address wrapping is tested separately with82 chunks. Do not claim that
this unrolled composition proves an inaudible native loop seam.

No listening, native GameMaker run or hardware output comparison was performed.
No “unacceptably audible” subjective verdict is invented. The objective missing
noise segment is enough to **HOLD full production and complete P0/P1 parity**.
Rendering stopped after this bounded set. Existing captures explain the main
failure; the later review performs no rendering. Keep the failed files for
Manager review and authorize a focused output-state correction before expansion.
