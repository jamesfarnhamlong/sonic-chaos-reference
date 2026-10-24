# M5-A2 original sound language and runtime-data specification

24 October 2026. Research parent `ad6aa301a7cc37a75f36a3d15c4804bcaa37b02b`;
management read `ec0c979556404d000487dc1f7a44651cddcbf121`. This is one bounded
independently implemented interpreter, not a complete replacement sound driver.
Original ROM SHA-256: `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.

The private ROM was available and freshly authenticated. Evidence below comes
from original control-flow inspection and fresh execution of its unmodified Z80
driver, using the existing AUDIO-1 harness. No new hardware, natural gameplay,
GameMaker, YYC or human listening observation is claimed.

## Boundary and evidence

`private SCSP records -> Decoder -> ordered bytes -> persistent A1L PSG -> PCM`.
The [decoder](../tools/m5a2/decoder.py) reads original data bytes and follows
stream pointers, counters, loops, subroutines and envelopes. It never consumes
dry-intent banks, prerecorded port rows, combined VGM or oracle PCM. The
[extractor/comparator](../tools/m5a2/proof.py) first executes the candidate with
a demand-reading DATA accessor, freezes only the accessed data and headers,
checks each run against the authenticated ROM, packs and reloads that fixture,
and completes candidate execution before instantiating the oracle per scenario.
The separate Z80 execution supplies expected ordered bytes and state.

CPU `$4000..$BFFF` maps to ROM offsets CPU address + `$4000`; this applies only
to the research sound-bank mapping. The runtime retains original data addresses
as compact identifiers, not an SMS address space or executable bank. It does
not emulate instructions. Public documentation gives semantics and addresses;
no program payload, melody, envelope byte sequence or driver binary is published.

## Headers and channel initialization

At `$407F..$40AF`, three mailboxes `$DE04..$DE06` are considered in order. A zero
low-seven-bit request is ignored. The priority table is CPU `$506F`, indexed by
`(request & 127)-1`. Compare the raw priority byte against the current priority;
on admission store its low seven bits and replace the selected request. Later
eligible mailboxes win. A blocked request neither initializes slots nor resets
the PSG. `$F8` has raw priority `$57` and can be rejected. The direct request
API is the research IRQ-equivalent boundary; deferred game-to-IRQ transfer is
outside this prototype.

Music dispatch `$4168..$41A6` uses pointer table `$50E1`; SFX dispatch
`$41A7..$422A` uses `$511F`. A header begins with an envelope-table pointer.
Music fields: channel count at +2, reserved +3, duration multiplier +4, tempo
divider +5, then four bytes per channel: stream pointer LE16, transpose, volume.
SFX fields: multiplier +2, count +3, then six bytes per stream: flags, PSG latch,
pointer LE16, transpose, volume. The selected fixtures use the existing global
envelope table `$49FD`; arbitrary alternate table bases are not verified.

Music initialization resets shared state, sends the original ten reset bytes,
sets tempo and initializes slots `$DE40,$DE70,$DEA0,$DED0`, latches `$80,$A0,$C0,$E0`.
SFX slots `$DF00,$DF30,$DF60` map to latches `$A0,$C0,$E0`. Original initialization
clears only designated fields, preserving other old slot bytes. Tone2 SFX can
inhibit the live noise slot and emit FF; it suppresses music tone2. Noise and
tone1 SFX suppress their corresponding music slots. Replacement is per slot,
not an inferred whole-effect lifetime. Complete 48-byte slot comparisons test
these stale and current fields together.

Selected channel offsets (relative to each 48-byte slot):

| Offset | Meaning |
|---|---|
| +0 | flags: active bit7, fixed-noise bit6, pitch hold bit5, write inhibit bit4, raw-pitch bit3, suppressed bit2, tie bit1 |
| +1,+2 | latch and duration multiplier |
| +3..+4 | next stream pointer |
| +5,+6 | transpose and base attenuation |
| +7,+8 | pitch modulation and volume-envelope selector |
| +9 | subroutine stack cursor |
| +10,+13 | remaining duration and remembered duration |
| +11..+12 | base frequency |
| +14,+15 | gate countdown and reload |
| +16..+23 | vibrato source pointer, accumulated offset and counters |
| +29..+36 | ADSR state, mode, level and five rates/thresholds |
| +37 | signed fine pitch offset |
| +39..+41 | three counted-loop counters |
| +42..+47 | bounded prototype call stack storage |

## Note and timing rules

Tone reader `$4341..$43E4` clears tie and inhibition when a duration expires.
Bytes below `$80` set a new duration using the channel multiplier, with original
8-bit arithmetic. `$80` starts note release/rest handling. Ordinary `$81..$D7`
select a pitch-table index: `(byte & 127) + transpose`, wrapped to 8 bits; read
LE16 at `$4436 + 2*index`. `$D8..$DF` set volume to low three bits and continue
reading. A note followed by a low byte takes that explicit duration; a high byte
reuses the previous duration and remains unread for the next stream step.
The selected SFX headers also exercise raw-frequency flag bit3: consume a
big-endian16-bit frequency, apply signed transpose when nonzero, then consume
an explicit duration (`$43C7..$43E4`). This path is supported even though
changing that mode with opcode FD is not yet verified.

Tempo `$4066..$407E` runs before fade/dispatch/channel processing. On divider
expiry it reloads and increments all four music-duration counters, so the
subsequent per-channel decrement skips an effective music duration step. Effects
retain their separate per-tick duration progression. No BPM approximation or
per-program wall-clock event table is involved.

Music noise has a separate reader `$464A..$46D4`: highest set bit among low six
note bits selects a percussion envelope, base attenuation and noise-control
class. Zero low bits performs rest/off. Its read path returns after parsing;
it does not run that tick's ordinary attenuation stage. This differs from the
three music tone readers and all three SFX readers. Their original slot order
is tone0, tone1, tone2, music noise, SFX tone1, SFX tone2, SFX noise.

## Stream operations

Dispatch table CPU `$46ED`, handlers reached through `$46D5..$46E8`.
Lengths below include the opcode. These operations were reached and compared
exactly in at least one selected case; per-case counts are in
[emission.json](../data/m5-a2/emission.json).

| Byte | Length | Semantics and original handler |
|---|---:|---|
| E0 | 6 | five ADSR bytes, select algorithmic envelope; `$4889..$48A2` |
| E6 | 2 | relative attenuation modulo16, ignored during fade; `$472D..$473C` |
| E7 | 1 | tie flag, next byte remains unread; `$4878..$487D` |
| F0 | 5 | save four-byte vibrato record pointer, select algorithmic pitch; `$486A..$4877` |
| F2 | 1 | release stream/ownership, explicit terminal writes; `$47C8..$481B` |
| F3 | 2 | physical noise control, tone2 coupling and suppression; `$4753..$47AB` |
| F5 | 2 | volume-envelope selector; `$47AC..$47AF` |
| F6 | 3 | absolute LE16 stream jump; `$47B4..$47B9` |
| F7 | 5 | loop index, count, LE16 target; decrement/reload counter and branch; `$4849..$485F` |
| F8 | 3 | call LE16 target, save operand-end pointer; `$481C..$4835` |
| F9 | 1 | return through channel-local stack; `$4836..$4848` |
| FB | 2 | relative transpose, wrap8; `$4748..$474E` |

The interpreter bounds the call stack to three return pairs and loop indices
to 0..2; the original code itself does not supply these safety bounds. A stream
read has a 256-operation budget. Looping across driver ticks is genuine pointer
execution, never conversion into a captured sequence.

Recovered but **unverified and rejected by the runtime whitelist**: E1 fine
pitch, E2 alias of relative volume, E4 shared noise-volume field, E5 ADSR mode,
E8 gate, ED tempo change, F4 table pitch selector, FA duration multiplier and FD
raw-frequency mode. E3/E9/EA/EB/EC/EE/FC/FE/FF point to RET-style handlers, and
EF/F1 point into data rather than an authenticated ordinary handler. Do not
interpret those as silence or safe NOPs. Full request control D0/D1/D2 and DE08
pause/silence-counter paths are outside the current API. The host can seed the
three fade bytes for the authenticated finite-fade controls.

## Pitch and volume programs

Algorithmic vibrato `$4267..$4304` loads initial delay, step divider, signed
step and half-cycle countdown from the four-byte record. Each eligible call
updates the accumulated signed frequency displacement and reverses its step at
the original boundary. Add signed fine offset before packing PSG low/high bytes
at `$44FF..$4526`. A subtle source dependency is retained: `$42F6` reloads through
the current **shared IY pointer**. Arbitration sets IY to `$DE03` each tick;
initialization, F3 and eligible modulation steps can replace it. THZ tick55 and
AC relative tick3 expose a reload of zero from `$DE06`, not the intuitive saved
vibrato record. The full-channel differential test found this even though its
initial audible emissions already matched. Positive/table pitch programs
`$4305..$4340` remain unsupported, including their DE-relative control behavior.

Volume processing `$4546..$4638` supports the reached algorithmic ADSR and table
envelopes. ADSR uses attack subtraction, decay toward threshold, alternate
decay/sustain state transitions and saturating/release addition, with original
8-bit carry and high-nibble attenuation. Table pointers are read from `$49FD`;
ordinary values advance the cursor, `$80` rewinds, `$81` inhibits writes, `$82`
performs explicit terminal off. Other DE-relative envelope controls are rejected
pending focused evidence. Envelope and stream termination are distinct.

## Physical output, release, fades and recovery

Processing order is mailbox arbitration, tempo, fade, dispatch, ordered readers.
Fade `$40B0..$4118` releases active SFX ownership first, advances its divider,
then increments capped tone attenuation bases. When its counter reaches zero,
reset writes occur before any remaining channel processing. The original
shared noise-volume field is retained even where the demonstrated noise reader
does not consult it. Underlying music can resume its saved envelope position.

Suppression can return before an envelope step; write inhibition does not imply
silence or reset. The music-noise non-read path processes an envelope before
ordinary suppression guards. Read and non-read frequency paths have different
guards. F2 releases ownership, resets shared priority and emits own-off; a tone2
off is DF. Noise/default-latch F2 also outputs saved `$DE11` before own-off.
That restore is a normal PSG protocol byte: zero changes the currently selected
register. It must not be promoted into a guaranteed noise latch. F3 clock mode3
couples tone2, with original rejection/suppression rules and ordered DF/FF writes.
The persistent PSG register file and data latch consume every byte in order,
including duplicate noise controls. The candidate uses the accepted P0R
`Registers` protocol helper only; none of P0R's dry-timeline scheduling is called.

Bounded outcomes include B8/BC's **104 physically held noise ticks**63..166,
terminal off167 and stream release168; tone1 suppression and read recovery61 in
B6/A0; and eight audible resumed-noise ticks40..47 in the finite88 fade. No
source padding or inferred silent tail is used. Music requests replace prior
music; automatic resurrection of a replaced song is not invented. SFX
interruption and restoration of still-running music are separately demonstrated.

## SCSP v1 private format

[bank.py](../tools/m5a2/bank.py) packs eight-byte magic `SCSP`, version1 and three
framing bytes; LE32 uncompressed length; zlib-compressed canonical UTF-8 JSON;
32-byte SHA-256 of uncompressed JSON. Maximum input and decoded record length
is256KiB. Loader bounds decompression and rejects trailing compressed data,
bad checksums, wrong version/source, overlapping/truncated records and bad starts.

Metadata contains schema version, authenticated ROM hash, supported global
horizon4200, priority bytes, and selected programs. Per-program records retain
duration multiplier, tempo, stream initialization, source header offset/length
and SHA-256. Contiguous data segments have original CPU data address, validated
length, SHA-256 and hex payload. Headers/control flow are source program data;
there are no timestamped notes or PSG event rows. Pointer traversal must remain
inside extracted records, with execution budget and stack bounds. Missing data
and unknown instructions raise `DecodeError`; the host must abort that request,
not silently continue with zeros. Checksums detect corruption, not malicious
replacement of a bank and all its receipts; authenticate the published private
package hash separately.

The extraction is **demand-bounded to the selected cases**, not a static proof
that every reachable branch at every request phase has been extracted. Reaching
an unextracted branch fails explicitly. Increasing a horizon or changing a
request phase requires another authenticated differential gate. Even repeated
THZ state is conservatively capped at4200 in this package.

Nine distinct headers,33 contiguous data records,2,469 accessed ROM data bytes,
138 header bytes and70 priority entries yield a4,285-byte container. Sparse-map
JSON is31,742 bytes (zlib9,099); contiguous-record JSON12,421 bytes. Packed SCSP
is larger than the2,677 bytes of raw data/header/priority values because it
includes addresses, hashes, lengths and validation metadata. No compression
claim against raw ROM bytes is made. Selected runtime-data hash:
`c0118830a4f7779b8d53d4b6cefd129487633689532e52500cddcd6f4dddfaf1`.

The prototype materializes a sparse Python map; this is not an optimized native
layout. Measured channel buffers total336 bytes; accepted A1L native state296
bytes. Python decoded bank+decoder current allocation195,131 bytes, peak223,481,
excluding interpreter baseline and PCM/trace arrays. Performance details and
host-scheduling outliers are retained in [facts](../data/m5-a2/facts.json) and
[emission](../data/m5-a2/emission.json). Native/GameMaker decoder cost is unmeasured.
