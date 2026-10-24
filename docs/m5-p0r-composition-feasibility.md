# M5-P0R static-stem feasibility and bounded PCM reevaluation

24 October 2026. New PCM work began only after the focused exact register gate
passed. Original P0/P1 references were reused. The existing pinned libvgm MAME
binary/clock/format are unchanged: SHA-256
`36821f4cfb6a1b6e386f1b468504245c21c6e24a2cbb0cba4b268703c96334a0`,
PAL3,546,893Hz,60 ticks/s,44,100Hz signed16 mono. No GameMaker or accepted
M4 PCM changed, and no new synthesis engine was implemented.

## Unchanged baked stems are insufficient

An emission-correct model alone cannot reconstruct audio removed from a static
file. In the existing B8 noise stem, source blocks corresponding to absolute
ticks159–166 of the required held span are exactly zero. The original output
is still held at attenuation2. Gain and gating cannot recover a missing noise
carrier from those zero blocks. Repeating/copying an arbitrary earlier block
would introduce an unjustified phase discontinuity and is not a solution.

Thus the **unchanged existing static PCM-stem representation does not support
complete original output semantics**. This conclusion is separate from the
now-passing register-emission model. No interaction bank or universal PASS is
inferred from the following bounded extension.

## Fixed-rate carrier diagnostic

One finite159-tick B8 carrier was rendered with the established attenuation-
forcing technique: preserve every original clock/noise-control write and the
continuous sample index, expose noise at constant volume during its finite
active span, retain termination afterward. This does not restart the carrier
at the BC completion/hold boundary. Gain comes from the corrected original
attenuation state and the pinned MAME integer volume table
`round(8192*2^(-level/3))`, with level15=0.

This is an **experimental asset-representation extension**, not the old baked
stem algorithm or an approved runtime asset. It adds no oscillator code or
alternative PSG synthesis. Four small unique diagnostic targets were rendered:
B8 carrier, matched-entry B8+BC noise reference, B6 music-context tone1 and BA
music-context tone1. A separate fresh carrier process checks determinism: five
successful renderer processes total, each at most159 ticks. No long track or
arbitrary-phase bank. An initial temporary-directory access failure was resolved
by using the owned workspace; a report-stage NameError was corrected and the
already successful render files were hash-cached rather than rendered again.
Missing per-process timings are recorded as null, not invented measurements.

The carrier retains one-shot phase continuously across all104 held ticks. The
arbitrary music-entry phase still differs from a reset standalone capture,
which is the existing M4 compromise. A separate original B8@1→BC@6 reference
with matched entry conditions isolates that compromise:

- waveform correlation0.999999889; envelope correlation0.999999548;
- RMS sample error2.445LSB, not sample equality;
- maximum error685LSB occurs at the first sample of a tick;
- outside those first samples, maximum error2LSB, zero samples beyond5LSB.

Applying gain after the renderer's resampling/quantization differs from changing
PSG attenuation before that process, especially at a one-sample boundary bucket.
That measured qualification is retained. No bytes are zeroed or shifted to pass.
This demonstrates a bounded fixed-rate solution without a new phase reset at
inhibition; it does **not** demonstrate arbitrary original oscillator-state
restoration or tone2-clocked-noise correctness for every interaction.

## Before/after with original continuous references

Full results, noise metrics, pitch and per-voice differences are in
[composition-feasibility.json](../data/m5-p0r/composition-feasibility.json).

| Control | Mix envelope correlation, before→after | Max tick RMS error as % reference peak, before→after |
|---|---|---|
|B8→BC |0.806784 →0.994137 |21.336 →5.108 |
|B6→A0 |0.988854 →0.995866 |18.314 →3.610 |
|BA partial replacement |0.978821 →0.996383 |28.138 →4.070 |

All104 required held-noise ticks are restored; mean held-noise tick RMS is
5036.932LSB original versus5037.028LSB candidate. Noise-envelope correlation
improves from0.37463 to0.999945; waveform correlation remains0.680427 in the
arbitrary-entry music case. No sample-identical claim. Measured pitch windows
in all three revised compositions retain zero failures beyond the inherited
25-cent guard. Noise statistics remain descriptive, not hardware timbre proof.

B6/BA use separate original-driver captures initialized with the **actual
music-context saved noise byte E4**. The originals with saved byte0 remain
unchanged and legitimate for that solo context. B6 changes relative block16
plus one sample in17; BA changes block5 plus its boundary bucket in6. Neither
is silently substituted into the accepted P1 library. A production exporter
must explicitly represent/validate the applicable context rather than treating
one solo mix as universal per-ID PCM.

## BA's large discrepancy was real extra output

At the old maximum-error tick34, original voice RMS values are
`[2562.856,0,0,0]`; the old composition contains an additional tone1 RMS
8142.055LSB. Mix RMS is2562.856 versus8449.343LSB. Energy decomposition gives
66,293,053LSB² of added per-voice energy, partly offset by−1,469,885LSB² of
cross-covariance. This is the dry zero-restore/latch error, **not phase**.

After context correction, the worst tick moves to165. Per-voice RMS values
are close: original `[2037.431,4071.351,3238.251,1123.965]`, candidate
`[2037.430,4061.110,3236.181,1127.448]`. The remaining mix-energy difference
is accounted for by cross-voice covariance: self-energy delta−88,848LSB²,
cross-covariance delta9,130,719LSB², observed9,041,869LSB². The small residual
is rounding/reconstruction error. This quantitatively explains that remaining
worst-tick mix difference; it does not certify inaudibility or harmlessness.

The A3 first-tick constant−4096/DC versus AC-RMS qualification is retained
unchanged. Generic fade and oscillator-phase limitations are not reclassified
as exact PCM parity. Original failure metrics remain intact under `data/m5-proof/`.

## Practical alternatives and decision

| Approach | Evidence and limit | Disposition |
|---|---|---|
|Existing baked stems plus gates |Cannot recover eight zero carrier blocks; solo context can corrupt another voice |insufficient unchanged |
|Context-valid finite stems |B6/BA diagnostics remove the demonstrated false levels; need explicit context selection/audit |candidate for a bounded next proof |
|Finite fixed-rate carrier plus emission-derived gain |104 ticks restored, matched-entry near-reference output without a hold-boundary phase reset |bounded experimental extension; broader validation required |
|Pre-render every interaction/phase |Combinatorial storage and still context-dependent |not recommended or performed |
|Runtime PSG/synthesis architecture |Could retain oscillator state, but is a different architecture and outside authorization |not implemented; no automatic recommendation to replace M4 |

**Recommendation: CONDITIONAL GO only for a separately authorized small
carrier/context-asset proof batch. Full M5 production and GameMaker remain HOLD.**
Before broader production, validate the proposed representation on other affected
ownership classes and source contexts, include explicit-off states in all guards,
retain the exact emission gate and obtain Manager acceptance of measured PCM
limitations. No full-library readiness, native cache/listening acceptance or
universal oscillator-phase fidelity is claimed.
