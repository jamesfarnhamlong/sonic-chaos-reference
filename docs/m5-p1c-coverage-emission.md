# M5-P1C coverage and exact emission evidence

Coverage was committed to local numerical metadata before new PCM work. It reuses the accepted 70-ID catalogue and existing complete solo F3 metadata, without a wholesale new scan. Labels remain inherited; no new sound names are assigned. See `data/m5-p1c/coverage.json` for all 37 SFX headers, priorities, slots, F3 counts, release ticks, held/off behavior and DE11/latch dependencies.

| Original mechanism | IDs (hex) | Count |
|---|---|---:|
| tone2-only | A0, A1, A2, A4, A5, A6, A8, A9, AA, AB, AD, AE, B2, B3, B4, B5, BC, BD, BF, C0, C1, C2, C3 | 23 |
| coupled-white-noise-single-F3 | A3, A7, AF, B1, B9, BB, BE, C4 | 8 |
| tone1-plus-coupled-white-noise | AC, B6, BA | 3 |
| coupled-white-noise-retrigger | B0 | 1 |
| tone2-periodic-noise-retrigger | B7 | 1 |
| fixed-white-noise | B8 | 1 |

B8 uses fixed white noise E5. B7 uses periodic tone2-derived E3 with repeated F3 at ages 1/4; B0 similarly retriggers white E7. The other noise effects use E7. Tone2 initialization can inhibit noise; coupled F3 can suppress tone2. All noise F2 paths require checking the saved DE11 byte and current data latch, not just a nominal noise owner. Repeated same-value noise-control writes can reset noise evolution and are retained in ordered emission.

## Exact original execution gate

Original Z80 execution was compared against the accepted P0R emission model for each tick: ordered port bytes, all physical PSG registers (including off states), register/data latch, DE11, slot flags mask D4 and global priority. Private captures also retain source age, waiting/release state and emitter audit. The model reuses measured intrinsic note/envelope intents; this is an independent emission integration proof, not an independent decoder of every stream byte. Only finite $88 needed a new intrinsic export. No emission changes were required.

| Selected original-driver control | Ticks | Ordered bytes | Result |
|---|---:|---:|---|
| fixed-hold | 210 | 1065 | PASS |
| coupled-steal-recover | 90 | 124 | PASS |
| clock-switch-with-live-tone2 | 90 | 114 | PASS |
| periodic-retrigger | 50 | 28 | PASS |
| music-context-B6 | 180 | 1166 | PASS |
| music-context-BA | 180 | 1254 | PASS |
| isolated-context-B6 | 47 | 82 | PASS |
| off-then-fresh | 90 | 97 | PASS |
| finite-fade | 90 | 332 | PASS |

Total 9 controls / 1,027 ticks. Requests/phases and seeded fade values are in the coverage matrix. Original execution, rather than a fabricated natural-game route, authenticates the response. Complete F2/off/recovery boundaries in each bounded window are compared. Prior P0R ownership 1480 cases and 111 recovery cases remain cached evidence; no1369-pair regeneration was performed. The existing P0R register protocol tests retain the104-tick held-noise negative control, B6 data-latch mismatch and BA false-audible negative control.

## PCM outcomes — no aggregate PASS

| Control | Full-mix correlation | Envelope correlation | Worst tick RMS error (% ref peak) | Interpretation |
|---|---:|---:|---:|---|
| fixed-hold | 0.865806 | 0.994137 | 5.1078 | reused P0R bounded correction |
| coupled-steal-recover | 0.826660 | 0.999671 | 3.8711 | HOLD exact oscillator-history continuity not represented |
| clock-switch-with-live-tone2 | 0.285763 | 0.999727 | 4.2433 | BOUNDED APPROXIMATION; NOT NATIVE ACCEPTED |
| periodic-retrigger | 0.999442 | 1.000000 | 0.0624 | BOUNDED APPROXIMATION; NOT NATIVE ACCEPTED |
| music-context-B6 | 0.756480 | 0.995866 | 3.6101 | reused P0R bounded correction |
| music-context-BA | 0.238853 | 0.996383 | 4.0704 | reused P0R bounded correction |
| off-then-fresh | 0.473673 | 0.999489 | 5.5979 | BOUNDED APPROXIMATION; NOT NATIVE ACCEPTED |
| finite-fade | 0.374440 | 0.999485 | 4.6694 | HOLD unsupported physical clock/source context |

The JSON contains every per-voice correlation, noise spectrum, valid/invalid pitch windows, timing exceptions and reference comparison. No pitch/envelope thresholds were relaxed. Invalid autocorrelation estimates are marked unresolved rather than converted to a pitch PASS. A zero-window pitch result is not pitch evidence. The tone-period gate is exact even where estimator windows are weak.

New fixtures are44,100 Hz mono signed 16-bit; all stems share735-sample tick boundaries. Full-mix versus voice reconstruction residual and worst-tick cross-voice covariance accounting are recorded explicitly in the JSON. Summing independently rendered/mixed voices can differ through rounding, phase and resampler boundaries; these are not sample-identical claims. Large mix sample deltas in reused P0R phase comparisons are retained. No new residual-to-tone0 acceptance is claimed.

The 1 LSB AC-RMS timing proxy reports boundary-only residual buckets as well as missing segments; it is a measurement locator, not an acceptance tolerance. A3's first 735 samples may be constantDC with zero AC RMS despite nonoff attenuation. Candidate output is strictly gated after explicitoff. In finite-fade, the missing noise 40–47 and 24 incompatible audible tone clocks are structural failures, not resampler artifacts. The high aggregate envelope correlation there does not override them. Clock-switch and off/fresh controls still have arbitrary-entry phase/covariance differences and boundary remnants, so their bounded status does not authorize unrestricted production.

## Production budget and provenance

Pinned MAME renderer SHA256 36821f4cfb6a1b6e386f1b468504245c21c6e24a2cbb0cba4b268703c96334a0; accepted libvgm commit a6eed945ecf4e5a25cf82004779c6f7e4fd5c319. ROM SHA256 eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607. PAL 3,546,893 Hz, 60 Hz driver,44,100 signed 16-bit unchanged.

Thirty bounded renderer processes, 2,332 total rendered ticks, longest new target 90 ticks. Sum measured process elapsed time 0.751922 s (render wrapper/process time only; not total investigation or a long-track throughput guarantee). Two new finite carriers A3/B7 and one continuous reference were independently repeated and byte-equal. Follow-up analysis spawned 0 new processes. Initial scratch measured 24,372,936 bytes; budget 1 GiB scratch / 128 MiB archive with about 803 GB free. Package receipt reports actual final compressed and uncompressed sizes. Peak working memory was not instrumented; no native cache-performance claim is made. No long-track extrapolation is justified by these short startup-dominated timings, and no $90/$91/$8C target was rendered.

Tests: `python -m unittest discover -s tests -p test_m5p1c.py`. Original gate requires private authenticated ROM; public tests validate retained numeric evidence and known-bad claims. The inherited P0R tests can additionally execute original comparisons when SONIC_CHAOS_ROM and their private dry bank are available. Prior accepted tests and failure records remain unchanged. See the verification receipt for actual executed commands/counts.
