# M5-A0 emission, state continuity and PCM comparisons

**All 12 bounded original-driver emission controls PASS:** 5,587 ticks / 32,512 ordered PSG bytes. This is same-core MAME integration validation, not independent chip emulation or human/native GameMaker listening acceptance.

The candidate receives only intrinsic private event programs and the external request/fade schedule, and completes before the original Z80 oracle is constructed. All comparisons retain exact ordered writes, every model/original register including off states, latch, saved DE11, slot flags D4 and priority. A reference-only diagnostic chip receives original writes to compare counter/LFSR snapshots; it does not supply candidate playback data. Per-voice sinks only mask attenuation, retaining all other writes; the actual full mix uses one persistent four-voice chip.

## P1C counterexamples

A3 at 1 then BC at 6: all 28 muted ticks 6–33 have different counter/LFSR history from uninterrupted solo A3, and the recorded LFSR changes at 27 successive muted-tick boundaries. Combined LFSR at 33 is 46829 versus solo 37953. Resumed noise 34–48 now correlates 0.999999999818 with reference, max 1 LSB error in the 735-frame path, versus the P1C carrier's 0.055473879. There is no reset at 34 or replacement with oracle history. Exact counter-state diagnostic agreement and byte equality with matched callback segmentation provide continuity evidence beyond RMS similarity.

Finite $88 with AC at 30, A0 at 35 and seeded fade at 40: reference and candidate both contain all 5,880 nonzero noise samples across ticks 40–47, max 1 LSB error. Cancellation of the source stream does not remove physical held period/control/amplitude. No finite lifetime, source padding, invented tail or carrier extension is involved. The complete 90-tick output is byte-identical when callback boundaries match; later off/reset is driven by original events.

B8→BC retains control 5/attenuation 2 for all 104 ticks 63–166, terminal envelope-off at 167, F2 at 168. BF→A3/reverse, B7 repeated F3, simultaneous tone2/noise clock changes, B6/BA saved context, admitted F8 then fresh output and the accepted loop-boundary control pass the same gate. Numeric F8 never calls the chip constructor. Near-loop A6 at 3989 reuses the prior 4200-tick continuous reference; no long-track production PCM was rendered.

## Residuals and fidelity classification

The queue-oriented 735-frame API differs by 1–3 signed-16-bit levels. The pinned resampler documents fixed-point block-size sensitivity. Splitting the independently generated candidate at the reference wrapper's 2048-frame callback boundaries yields byte-identical PCM in all 12 controls, without changing events or oscillator history. Splitting 735 into 100+635 also produces 2-LSB errors in 81 samples of A3→BC. The 735-frame queue remains the proposed contract; callback alignment is diagnostic, not a GameMaker change or relaxed tolerance.

Per-voice/full-mix waveform/envelope, pitch, noise and covariance measurements are recorded in results.json. The worst valid candidate tone pitch estimate is 2.049113 cents from expected register pitch; these controls have zero invalid estimator windows. Zero-window results are not pitch evidence. A3 constant-DC startup remains explicitly preserved. No original sample or earlier failure record was replaced. Old finite-carrier/phase and generic-fade limitations remain part of the accepted M4 runtime history; the new prototype is not installed there.

## Intermediate diagnostics retained

The first unity-gain trial produced half amplitude. Source inspection established single-PSG VGMPlayer normalization 0x80→0x200; the adapter now uses that fixed gain, with no per-case fitting. An initial chip assertion compared unwritten MAME attenuation-register 0 to P0R logical off 15, although actual core amplitudes initialize to zero. These defaults are counted explicitly; all post-write chip-register checks and full original/model assertions remain exact. The loop test first stopped at its 1400-tick intent guard. Only solo $81 intents were extended to 4200; no combined oracle was exported as candidate data and the guard remains enabled. The numerical report retains all three diagnostics.

All original references are reused from existing private captures: zero new reference-render processes. The proof is ROM-backed, but candidate playback has no ROM/Z80 dependency. No independent real-chip timing, full-song decoder, native queue performance or human listening PASS is claimed.

## Measurements

| Control | Ticks | Ordered bytes | 735-frame max error | RMS error | Callback-aligned max error |
|---|---:|---:|---:|---:|---:|
| fixed-hold | 210 | 1065 | 2 | 0.065143 | 0 |
| coupled-steal-recover | 90 | 124 | 1 | 0.017817 | 0 |
| clock-switch-with-live-tone2 | 90 | 114 | 2 | 0.035846 | 0 |
| periodic-retrigger | 50 | 28 | 2 | 0.032991 | 0 |
| music-context-B6 | 180 | 1166 | 2 | 0.065638 | 0 |
| music-context-BA | 180 | 1254 | 3 | 0.108727 | 0 |
| isolated-context-B6 | 47 | 82 | 3 | 0.062049 | 0 |
| off-then-fresh | 90 | 97 | 2 | 0.024896 | 0 |
| finite-fade | 90 | 332 | 2 | 0.061844 | 0 |
| BF-A3 | 180 | 1077 | 2 | 0.058386 | 0 |
| A3-BF | 180 | 1055 | 2 | 0.053945 | 0 |
| near-loop | 4200 | 26118 | 2 | 0.060419 | 0 |
