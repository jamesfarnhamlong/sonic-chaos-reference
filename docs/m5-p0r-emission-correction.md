# M5-P0R original PSG emission correction and boundary closure

24 October 2026. Research parent `e8494d52ec30b9bc86d29f5c4f4824f4586e21e3`;
canonical management read at `293b5a32a7c8af25117c6c88d7e383d3bb36b161`.
Private POC remains `11bff34356d5f5d979218896dc95fdc4bb265eae`, unchanged.
Original ROM authenticated as SHA-256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.

**The focused exact register-emission gate passes.** This is not full-library
PCM, hardware or GameMaker acceptance. Historical P0/P1 failure files and its
private ZIP remain untouched. New evidence is additive under `data/m5-p0r/`.

## Reference model and evidence boundary

[EmissionModel](../tools/m5p0r_emission.py) extends the PCM-independent ownership
model with a persistent PSG register file, data latch, saved music-noise control,
ordinary write inhibition, explicit off, envelope progression and stream release.
No write leaves the physical registers unchanged; channel activity never directly
sets a physical register to zero/off. The model contains no oscillator or PCM
renderer. Register enable state is not an assertion of audible AC output: the
accepted A3 constant-DC startup qualification remains unchanged.

PRIVATE solo captures provide intrinsic read/F2/F3/note-volume/frequency intents
and envelope-epoch step programs. The combined scenario never supplies its output
to the model. The model independently schedules admission/ownership and decides
which intents emit, freeze, continue or restore shared state. Envelope positions
advance on eligible calls, not blindly on wall ticks. Coverage exhaustion fails
explicitly. It is an emission integration reference using original intrinsic
program data, **not an independently implemented note/envelope decoder**.

The exporter and original comparator are [m5p0r_proof.py](../tools/m5p0r_proof.py).
Only aggregate results and bounded blocker facts are public. Complete dry intents,
port traces and per-tick comparisons remain private below `build/m5-p0r/`.

## Original paths translated

| Original sound-bank CPU path | Correct emission consequence |
|---|---|
| `$47FB..$4816` | Tone2 F2 can set noise write inhibition; its own off byte is DF, not FF. Noise hardware can keep sounding. |
| `$4528..$4545` | Envelope processing precedes ordinary attenuation guards; bit2/bit4 can prevent a new attenuation write without clearing the existing register. |
| `$4639..$4649` | Explicit envelope/rest off sets inhibition and emits the channel-off byte unless bit2 suppresses it; bit4 does not prevent this terminal off. |
| `$47EF..$47F5` | Noise F2 restores the **saved music** noise byte DE11, separate from current PSG noise control. The restore byte still obeys the actual PSG data latch. |
| `$44CA..$44DA` versus `$44DC..$4545` | Read-path bit4 can prevent frequency and attenuation output; non-read frequency writes can still occur while attenuation writes are inhibited. |
| `$4341/$4650`, `$43BE/$42A3` | Reader and envelope-epoch transitions are distinct; music noise has its own reader. Suppression can freeze a tone envelope, so a fade release must resume its saved position. |

Sound-bank file offsets equal these CPU addresses plus4000 hex. Callback trace
PCs are recorded after the OUT instruction; reports use instruction addresses.
Original Z80 execution supplies the oracle. These are not guessed GameMaker rules.

## 104 held-noise ticks, off boundary and stream boundary

For original B8@30 then BC@35:

| Tick(s) | Noise stream | Ordinary writes | Last physical control/attenuation |
|---|---|---|---|
|63–166 |active |inhibited |5 /2, held exactly |
|167 |still active |terminal envelope-off executes |attenuation15 |
|168 |F2 completes stream |restore then own off |stream inactive, attenuation15 |

The model matches all104 held ticks and the two different terminal boundaries
with zero register or ordered-write differences. It does not infer silence from
bit4. Numeric F8 explicit reset is also checked separately. Reverse BC→B8
preserves real priority rejection; it is not described as two admitted effects.

## B6 boundary closed: restore byte and data latch

The affected music-context tick is45, B6's relative age16:

| State | Original | Corrected model | Prior dry-template projection |
|---|---:|---:|---:|
|tone1 attenuation at44 |3 |3 |— |
|tone1 attenuation at45 |4 |4 |0 |
|authentic B6 solo attenuation at age16 |0 |0 |0 |

The tone1 write at `$4543` is B4. In a solo capture, saved DE11 is0. Noise
F2 loads it at `$47F0` and outputs it at `$47F3`. With no other live tone effect,
the last latch is tone1 attenuation: **data byte0 changes tone1 to0**. In the
music scenario DE11 is the valid E4 noise-control latch. A0 tone2 writes also
occur between B4 and the restore, in original channel order; E4 does not overwrite
tone1. The corrected model maintains both saved context and the current data
latch, so it preserves the solo quirk and matches the in-music attenuation4.

This is a context-dependent solo readback/asset contamination, not a scheduling
shift or tolerance issue. No original driver behavior was “fixed.” A separately
seeded, original-driver music-restore-context diagnostic tone1 stem changes
relative tick16 plus one resampler-bucket sample at17; the accepted old file
is preserved. See [composition feasibility](m5-p0r-composition-feasibility.md).

## BA false-audible boundary also closed

At tick34, BA's relative age5, original tone1 attenuation is15. Its solo dry
capture's zero restore byte changes the last tone1 attenuation latch to0 instead,
creating a false loud block in the old composer. The former attenuation guard
checked only where original attenuation was non-off and missed this case.

The new comparator checks **all** register states, including original-off and
stale muted frequency registers, without widening a tolerance. The model yields
15 at34. The output-error diagnosis is independently supported by the measured
PCM energy; it is not excused as oscillator phase.

## Focused differential results

[emission-results.json](../data/m5-p0r/emission-results.json) records12 controls:
the ten requested focused cases, B6 solo context, and matched-entry B8+BC for
the carrier experiment. Over2,329 driver ticks, **11,250 ordered port bytes**
match exactly, along with all eight register values, the data latch, active/
suppressed/inhibited/fixed channel state and priority. No audible-only filter
or numeric tolerance is used. All failure lists are empty.

The1,480 accepted ownership scenarios are replayed against their existing cached
observations, not recaptured from the ROM. All match. The111 cached recovery cases
retain159/159 release/reader facts. **Zero full1,369-pair matrix recaptures**.
Earlier M4/R1 controls remain unchanged. The tests also run the old selector
and old dry readbacks as negative controls: they violate the held-noise,
B6-in-music and BA-original-off contracts while the correction passes.

This establishes the bounded emission behavior, not every request phase or
all combinations of musical/channel/oscillator state. Full PCM feasibility
and production recommendations are deliberately separate.
