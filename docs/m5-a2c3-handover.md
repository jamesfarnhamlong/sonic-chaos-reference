# M5-A2C3 noise and multi-slot SFX — Manager handover

**All three authorised requests PASS. GO for another separately authorised,
class-stratified small SFX preflight/proof.** The accepted decoder, scoped FD,
SCSP v1 and A1L synthesizer are unchanged. No additional request IDs were
implemented. Work stops for Manager review.

25 October2026. Topic `research/m5-a2c3-noise-multislot-sfx` starts exactly at C2
`f3eeb6e66b44852d4d6245bec19db0ce3c820a1a`; canonical management read from
`79ef876b2ec72f06aeb2cb3f0dea2d5d8ed5eac9`. Original ROM freshly authenticated:
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
Accepted private M4 remains `11bff34356d5f5d979218896dc95fdc4bb265eae`, read-only.

## Original-only class preflight

The earlier P1C classes were treated as hypotheses. Before new runtime extraction
or candidate PCM, the unmodified original Z80 executed each complete solo plus128
post ticks and one THZ context. The [preflight](../data/m5-a2c3/preflight.json)
retains source headers/hashes, pointers/flags, priorities, actual command sets,
selectors, F3 counts/modes, slot release, DE11/latch and physical registers.

| ID | Preserved name | Actually observed class | Solo slot use | F3 ticks/modes | Inactive tick |
|---|---|---|---|---|---:|
|B0 | Unknown $B0 | tone2-clocked white noise, internal control repeat | noise / E0 |1,4 /7,7 |7 |
|B7 | Unknown $B7 | tone2-clocked periodic noise, internal control repeat | noise / E0 |1,4 /3,3 |7 |
|BA | Unknown $BA | tone1 plus tone2-clocked white noise | tone1 A0 + noise E0 concurrently |1 /7 |25 |

BA's noise reader releases at5 while tone1 remains active until25. Both slots
are simultaneously active at entry; this is not merely their union across
separate times. All three become physically attenuated15 on all channels and
remain so for the128 original-only post ticks. No extended held solo tail was
found, so the independent candidate retains32 post-completion ticks.

B0/B7 execute E0/F2/F3/F7, and BA executes E0/E6/F0/F2/F3/F7. No unsupported
command, alternate envelope table or FD invocation was reached. In particular,
FD was not enabled in a noise/tone1 reader: the C2 slot5/latchC0 guard remains
intact. Raw-frequency header flags use the already authenticated reader path.

### What the repeated F3 actually resets

An original-only observer forwards original Z80 writes into the pinned accepted
MAME-core diagnostic adapter. It advances reference time while discarding samples;
it neither generates candidate PCM nor supplies a candidate event program.
The adapter hash is checked against the accepted A2 receipt. This is the
accepted tick-boundary reference model, not a claim of SMS cycle-level hardware
measurement.

The second B0 E7 write at4 changes LFSR8356→32768; the second B7 E3 write changes
512→32768. In both, **noise countdown21 stays21** across the instantaneous write.
Tone2 period32/noise period64 are observed at that boundary. An equal register
value therefore still has a real LFSR side effect, without resetting the entire
chip or its current countdown. Independently decoded candidate observations
match every corresponding original-only before/after field.

## Exact finite and interaction gate

| Request | Original/candidate inactive tick | Candidate post ticks | Final attenuation | Result |
|---|---:|---:|---|---|
|B0 |7 |32 |15,15,15,15 | exact PASS |
|B7 |7 |32 |15,15,15,15 | exact PASS |
|BA |25 |32 |15,15,15,15 | exact PASS |

No post-window reader reactivation or port write occurs. The original terminal
writes are reproduced, not replaced by a host off, fade or guessed silent tail.
The PSG continues evolving even when output attenuation is off.

**99 scenarios /32,531 ticks /154,221 ordered PSG bytes: exact PASS.** This
includes18 new cases/2626 ticks/11958 bytes and all81 accepted C2 cases/29905
ticks/142263 bytes. Every tick compares ordered writes, physical registers/latch,
DE11, sharedIY,336 channel bytes and12 globals, including priorities/mailboxes,
pointers, durations, envelopes and suppression. Original control-transfer
targets/ticks/slot order and SFX admissions are checked. No numeric or timing
tolerance is used. Candidate generation completes before the independent
original Z80 oracle is created per comparison; captured combined output is
never playback input.

The15 new interactions cover each effect during THZ; distinct-phase B0/B7/BA
retriggers; a tone2 hurt effect interrupting B0; blocked ring followed by admitted
ring after B7; concurrent BA/hurt; BA replaced by B6; equal-priority noise-slot
replacement with rejected lower-priority requests; fixed B8→BA; fade→fresh B7;
numeric reset→fresh BA; and B7 followed by finite music98. Cases are bounded
original-admissible schedules, not a Cartesian or natural-gameplay proof.

Four B0 requests at30/32/36/60 produce **seven** F3 executions. Four B7 requests
at30/33/36/60 produce **six**, because replacement can pre-empt the old instance's
second F3. Four BA requests produce four F3 executions. Counts are measured from
actual stream execution, not obtained by multiplying a solo template. All
selected retriggers are admitted. During BA, ring31 and B0 at32 are rejected;
equal-priority B7 at33 replaces the noise slot while BA tone1 continues. During
B7 solo, ring3 is rejected and ring8 admitted after original priority release.

BA plus hurt has three active SFX slots at32: BA tone1/noise and hurt tone2.
Each slot retains its authentic reader, suppression and release order. THZ
B0/B7 suppress tone2/noise30..35, then eligible reads resume37. THZ BA releases
tone2/noise suppression after33, eligible reads37, while tone1 suppression
continues through53 with next read61.

## DE11, clock ownership, mute and release

Solo B0/B7 F2 at7 writes savedDE11=0 through data latch7, then its own off byte.
Solo BA noise F2 at5 writes0 through tone1 attenuation latch3, then noise off;
tone1 still runs. THZ B0/B7 restoreE4 at36, and THZ BA restoresE4 at34, through
the authentic protocol. Those context-dependent ordered writes and resulting
physical registers are exact; no zero-byte noise-latch interpretation or
standalone-stem substitution is made.

Rich native snapshots record noise control, tone2 period, noise countdown and
LFSR before/after controls and per tick, including B0/tone2 interruption, BA
retrigger and BA/hurt. Muted frame pairs still show LFSR progression; the
original-reference chip-state comparator has zero mismatches in those runs.
No request boundary recreates the chip. Diagnostic traces remain private;
aggregate facts are in [facts.json](../data/m5-a2c3/facts.json).

The specific changing-**music**-tone2 observation is intentionally qualified:
after B7 finishes, requesting verified finite music98 at15 leaves periodic-noise
control3 selected. Over337 observed frames, music tone2 takes periods
0/81/91/107/108/120/121 while noise attenuation is15. This authentically exercises
retained noise-clock/counter state under music frequency changes **while muted**.
It is not evidence of an audible noise stream co-owned by unsuppressed music.
During the tested audible coupled effects, original ownership suppresses music
tone2 and SFX drives that clock. No schedule or sound was fabricated to claim
an absent audible ownership class.

## A1L versus original/MAME PCM and private playback

The unchanged accepted A1L core/resampler uses PAL3,546,893Hz,44,100Hz signed16
mono,735 frames per60Hz tick. The pinned reference renderer consumes independent
original-driver writes. No hardware/cycle-timed sample-identity or human
listening claim is made.

| Solo | Mix max signed16 LSB | Mix RMS LSB | Tone1 max LSB | Noise max LSB | Frames incl32 post ticks |
|---|---:|---:|---:|---:|---:|
|B0 |2 |0.187057 |0 |2 |28665 |
|B7 |2 |0.095055 |0 |2 |28665 |
|BA |3 |0.147380 |2 |2 |41895 |

All18 new mixes measure2..5LSB maximum, voice maxima0..3, with zero compared
register/counter/LFSR mismatches. The two5LSB mixes are BA retrigger and BA with
concurrent hurt, RMS0.269837 and0.313515 respectively. No case exceeds the prior
observed5LSB range and no tolerance or arithmetic changed. This is a new-case
measurement, not a universal permission. [pcm.json](../data/m5-a2c3/pcm.json)
retains every mix/voice maximum and RMS, block-RMS envelope error, frame count
and hash. Driver envelope and attenuation state are exact.

All99 candidate renders are identical for735 versus100+635 partitions. All81
prior PCM outputs remain byte-identical, including8A's original held+8192 DC.
Three fresh processes reload SCSP and independently play B0/B7/BA plus post
windows, with original-tool imports and ROM/VGM/dry-bank access forbidden.
Every resulting WAV matches its independent candidate. Playback takes only
private SCSP, host requests and unchanged A1L, without a Z80 or captured timeline.

## SCSP, Python cost and catalogue

SCSP remains **v1**, horizon **4200**, now **8942 bytes** (+383 over8559), with
30 unique headers,55 data records,5647 source data bytes (+93),498 header bytes
and70 priority entries. Raw values total6215 bytes; source/address/hash/validation
metadata adds overhead. Record JSON28814 bytes. Expanded bank SHA-256:
`569304890648310d93a0741ab6a2601610bcab03e54d794fe340c73fd668e215`.
All27 previous headers and5554 data bytes match exactly; original standalone
A2/B1/B2/C1/C2 banks/hashes remain untouched. Pointer, stack, loop, opcode,
operation and explicit horizon guards remain unchanged.

Python benchmark6750 solo/post ticks comprises1950 active and4800 inactive
ticks: active median3.8µs, inactive/combined median0.7µs, p9910.7µs, max71.1µs
in this run. Whole-proof worst work remains20 stream operations/21 writes in
one tick. Comparative traced current/peak allocation: old521663/665975 bytes,
new524644/670950 bytes, +2981/+4975. Scope includes sparse Python data, decoder
and bounded diagnostics, excludes interpreter base/PCM, and is **not GameMaker
decoder performance**.

All70 rows retain names and identities: **30 verified within measured scope,
7 empty/control,33 unverified**. This is15 music programs and15 SFX, not30
universally interchangeable audible outputs. Original68 indexed headers and61
bounded solo-emission fingerprints remain distinct metadata. Unknown B0/B7/BA
labels are preserved. Demand extraction proves tested paths, not all possible
request phases or unbounded loops.

**Next proposal only:** preflight a small group of remaining single-F3
coupled-white-noise effects, for example AF/B1/B9 from the accepted P1C class
catalogue, before selecting an implementation batch. Their classes are historical
evidence, not new C3 execution or decoder promotion. Remaining tone2 effects
need separate opcode/envelope review. FD outside slot5/latchC0, table pitch,
DE-relative envelope controls, other unverified commands, alternate envelope
bases, DE08 and numericD0/D1/D2 remain explicit language/reader risks. No other
request, repeating music or long-track batch was begun.

## Negative controls, preservation and review boundary

**78 tests PASS:**65 unchanged inherited contracts plus13 C3 tests. New controls
verify original F3 modes/counts and instantaneous states, split BA ownership,
admissions/recovery, all99 exact cases,18 mix/four-voice comparisons,81 frozen
PCM outputs, three isolated replays and all70 coverage rows. Suppressing the
second equal noise-control byte in a diagnostic negative causes36 LFSR-state
mismatching ticks and a16384-LSB maximum waveform error in each B0/B7 solo.
The unchanged control register alone would miss that failure. Omitting BA's
terminal release writes fails at5. Existing corrupt/truncated data, pointer,
FD reader, other-opcode, stack/loop and horizon negatives remain green.

```text
python tools/m5a2c3/preflight.py PRIVATE_ROM
python tools/m5a2c3/proof.py PRIVATE_ROM
python tools/m5a2c3/pcm.py
python tools/m5a2c3/evidence.py
python tools/m5a2c3/isolation.py
python -m unittest discover -s tests -p test_m5a2*.py
python tools/m5a2c3/package.py
```

Use existing Python3.12/NumPy and pinned local PSG/reference tools. Original
source execution requires ROM access; runtime/replay does not. Program records,
full traces, negative audio and WAV/VGM stay outside public Git under workspace
`private-research/m5-a2c3`; the separate private archive is in `releases`.
Public output is safe source, semantics, aggregate numbers, tests and integrity
receipts. Packaging verifies all eleven earlier proof archives, five standalone
banks,47 M4 payloads, clean accepted POC and A1P source/native/compiled VM
read-only. The new archive includes no ROM or PSG DLL.

**STOP for Manager review.** No GameMaker/Sound Test work, component release,
upstream contact, main merge or automatic next class follows. The purpose
remains personal ROM understanding, faithful experimentation and public-safe
technical documentation.
