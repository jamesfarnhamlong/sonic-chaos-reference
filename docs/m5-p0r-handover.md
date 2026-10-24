# Manager handover — M5-P0R emission closure

24 October 2026. Topic `research/m5-p0r-emission-closure`, direct child of
accepted investigation `e8494d52ec30b9bc86d29f5c4f4824f4586e21e3`.
Canonical management read at main293b5a32; no AGENTS/MEMORY/ROADMAP edits.
Accepted private POC11bff343 and M4 PCM remain unchanged.

**Recommendation: CONDITIONAL GO for one separately authorized small
carrier/context-asset proof batch; full M5 production and GameMaker HOLD remain.**
The existing unchanged baked-stem composer is insufficient for complete M5.
There is now a demonstrated bounded extension, not a universal production PASS.

| Required deliverable | Result and authority |
|---|---|
|A emission correction |[Emission report](m5-p0r-emission-correction.md), [model](../tools/m5p0r_emission.py): exact focused register/port/latch gate PASS;104 held ticks correct |
|B B6 closure |Same report and [boundary facts](../data/m5-p0r/boundary-closure.json): original45=4, corrected45=4, prior dry projection0; saved restore/data-latch context explained |
|C focused comparisons |[Differential results](../data/m5-p0r/emission-results.json):12 controls,2,329 ticks,11,250 ordered bytes exact;1,480 cached ownership cases and159/159 facts across111 recovery cases retained |
|D PCM feasibility |[Feasibility report](m5-p0r-composition-feasibility.md): B8 hold restored by finite carrier experiment; B6/BA context artifacts corrected; full-static representation still insufficient |
|E tests |[Focused tests](../tests/test_m5p0r.py), including original-driver comparisons and old incorrect-selector/readback negative controls; historical failure fixtures unchanged |
|F handover |This document, [preservation facts](../data/m5-p0r/boundary-closure.json), [private sidecar receipt](../data/m5-p0r/private-sidecar-receipt.json) |

## What is conclusively established

The model distinguishes active streams, inhibited writes, persistent PSG registers,
explicit off, envelope terminal off and stream release. It also separates the
saved music-noise restore byte from current PSG noise control and retains the
actual data latch. B8 control5/attenuation2 hold at63–166, off at167 and stream
completion168 all match exactly. Fade and reverse-order priority behavior match.

B6's mismatch is a solo-capture restore/data-latch artifact. Authentic solo
age16=0 is preserved; in-music tick45=4 is correctly modeled. BA's old large
RMS discrepancy is another false-audible solo-context artifact: original tone1
is off at34. Its earlier audible-only guard failed to examine that state.
The corrected comparator includes original-off and stale muted registers.
No tolerance was widened and no original PCM was silently replaced.

Only intrinsic solo program metadata supplies note/envelope timing; no combined
oracle trace is fed to the model. This is an emission integration reference,
not a new note decoder or synthesis engine. Exactness is bounded to the listed
controls and metadata coverage. No1,369-pair ROM recapture or campaign replay.

## PCM result and limitations

Existing B8 PCM contains eight zero source blocks where held sound is required.
Gain/gating alone cannot recover them. A constant-volume finite carrier rendered
with the pinned MAME core, followed continuously at its original age, restores
all104 ticks without restarting phase at the hold boundary. Matched-entry
reference correlation exceeds0.999999; interior error is at most2LSB, with
larger first-sample resampler-boundary differences explicitly retained.
Arbitrary music-entry oscillator phase remains the accepted compromise.

Music-context B6/BA diagnostics fix demonstrated false levels. Mix-envelope
correlations improve to0.995866/0.996383 respectively; BA's maximum tick-RMS
error drops28.138%→4.070% of reference peak. Remaining worst-tick energy is
accounted for by cross-voice covariance, not excused without measurement.
No native listening or sample-identical arbitrary-entry waveform claim.

Five successful small diagnostic renderer processes, including one fresh repeat,
were used; no target exceeds159 ticks. No full catalogue, long90/91/8C, phase
bank, Sound Test, GameMaker file or native build. A3's DC startup qualification,
generic fade approximation and historical numerical failures remain recorded.

## Conditions for any next authorization

1. Approve or reject the finite-carrier/context-asset representation explicitly;
   it is not the accepted old static-stem format or an accepted runtime algorithm.
2. Validate additional affected ownership/context classes with the emission
   oracle before accepting their assets. Do not generalize fixed-rate B8 to
   all tone2-clocked noise or all source contexts.
3. Keep zero/off-state checks, PCM error qualifications, no hold-boundary reset,
   source hashes and unchanged M4 bytes. Preserve a separate reliable PC Stop.
4. Give any subsequent batch its own bounded scope and Manager review. This
   recommendation grants no P2/P3 or Designer permission.

## Reproduction and preservation

Original P0/P1 ZIP SHA-256 remains
`3adf174848e83fc40644a7e12142dbd44062c25c5dff674d09df031fe4b9881f`.
All47 previously authenticated M4 preparation/runtime payloads match their
recorded hashes. The old proof package, caches and earlier public failure
measurements were read-only. New binary evidence is in a separate PRIVATE
sidecar under ignored build storage; its actual path/hash are supplied in chat.
No original ROM or renderer binary is included in that sidecar.

```powershell
$env:SONIC_CHAOS_ROM = 'PRIVATE_VERIFIED_ROM.sms'
$env:PYTHONPATH = 'EXISTING_M4_NUMPY_DEPENDENCY_DIRECTORY'
python tools/m5p0r_proof.py $env:SONIC_CHAOS_ROM
# Only after emission-results.status == PASS; bounded diagnostics with cache:
$env:AUDIO1B_VGM2WAV = 'EXISTING_PINNED_MAME_vgm2wav.exe'
python tools/m5p0r_pcm.py $env:SONIC_CHAOS_ROM
python tools/m5p0r_receipt.py
python -m unittest discover -s tests -p test_m5p0r.py -v
python -m unittest discover -s tests -p test_m5_audio_contract.py -v
python -m unittest discover -s tests -p test_m4_audio.py -v
```

Tools expect the existing private P0/P1 proof directory beside this checkout,
as shown by `m5p0r_probe.PRIOR`; a successor without that mounted storage must
receive the private inputs separately and adjust its local path configuration.
Do not pretend that public Research contains the private inputs.

Final scoped tests: **12 P0R +16 inherited M5-R1 +9 inherited M4 =37 PASS**,
zero skips/errors/unit failures with authenticated private inputs. Python
compilation and whitespace checks pass. Unaffected chunk/native-cache tests
were not repeated; no native build or listening acceptance is claimed.

Exact added-file inventory and hashes are recorded in
[verification.json](../data/m5-p0r/verification.json). Final commit/remote SHA and
clean-worktree proof are supplied after publication. STOP for Manager review.
