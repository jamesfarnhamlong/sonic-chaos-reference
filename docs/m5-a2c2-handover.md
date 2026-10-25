# M5-A2C2 remaining preflighted SFX — Manager handover

**All three requests PASS. GO for a separately authorised next small SFX-class
preflight/proof.** FD is now supported in its authenticated SFX tone2 scope;
other reader classes and unrelated commands remain gated. No further request
ID was implemented. Stop for Manager review.

25 October2026. Topic `research/m5-a2c2-remaining-preflight-sfx` starts exactly
at C1 `c487a835a5c76771d46c1e1d3fa350366737fc9f`; management read from
`27ca8f65b9a8112a3f854f832a6ec969d21475ce`. Original ROM authenticated:
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
Accepted M4 POC `11bff34356d5f5d979218896dc95fdc4bb265eae`, A1P and A1L are
unchanged. Optional redistribution approval remains separate from this proof.

## FD prerequisite and implementation boundary

[FD original-handler analysis](m5-a2c2-fd.md) gives exact source addresses,
operand consumption, flag changes and reader grammar. The isolated gate passed
before A2 entered the expanded bank: actual A2 for67 ticks, six24-tick synthetic
ordinary/raw/ordinary transitions and16 direct original-handler flag/operand
edge calls. Actual A2 executes FD once at tick2. Only channel flag bit3 changes;
the caller consumes one operand. FD1 sets raw mode; all other operands clear it.
No guessed NOP, borrowed opcode meaning or timing table was introduced.

The small [decoder extension](../tools/m5a2c2/decoder.py) derives from accepted
B1 and enables FD only for SFX tone2 slot5/latchC0. Its reader-scope rejection
is an explicit validation limit, not a new rule attributed to the original.
Old A2/B1 source and SCSP format remain unchanged. The new ROM-free runtime
selects this decoder through the already accepted optional factory argument;
the PSG/core/resampler is unchanged. Other unverified operations still fail.

## Three-request completion and original-driver comparisons

| ID | Preserved catalogue name | Observed original class | Original/candidate inactive tick | Post ticks | Result |
|---|---|---|---:|---:|---|
|A1 | Unknown $A1 | tone2-only |30 |32 | PASS |
|A2 | Unknown $A2 | tone2 with actual FD raw-mode transition |35 |32 | PASS after FD gate |
|A7 | Unknown $A7 | raw-initialized noise slot, F3 mode7 / tone2-clocked white noise |7 |32 | PASS |

All three end with physical attenuation15 on all channels and no subsequent
port byte or reader reactivation. Registers stay stable throughout the32 post
ticks; the original128-tick physical-tail checks from C1 remain applicable.
No output was forced off because a reader became inactive. Counter/LFSR time
continues even after attenuation off.

**81 main scenarios /29,905 ticks /142,263 ordered PSG bytes: exact PASS.**
This includes19 new cases/2578 ticks/11782 bytes and all62 accepted C1 cases/
27327 ticks/130481 bytes. The FD prerequisite's actual/synthetic gate211 ticks
and16 handler calls are additional, reported separately rather than inflated
into the main matrix. Every main tick compares ordered writes, physical PSG
registers/latch, DE11, sharedIY,336 channel bytes and12 globals, including slot
ownership, priorities/mailboxes, pointers, durations and envelopes. Actual
control-transfer targets/ticks/channel order agree exactly. There is no numeric
or timing tolerance at this gate. Candidate generation completes before the
independent original Z80 oracle is instantiated per comparison.

New interactions cover THZ with A1/A2 and A7 at two music phases; A1 replaced
by ring; A2 replaced by spring and retriggered at30/32/50; A7 retriggered at
30/32/36/60; A7 replaced by ring; lower-priority A7 rejected during A1 and
later admitted; A7 superseded by A3 with blocked reverse request; A3→BC→A7;
B8→BC→A7; A2 fade/reset→fresh A7; numeric reset→fresh A1; and the three new
effects during finite invincibility music. These are original-admissible seeded
request schedules, not an exhaustive Cartesian or natural gameplay proof.

## Coupled-white-noise findings

Each admitted A7 invocation executes **one** F3 mode7 command. The single solo
has one; the four admitted retriggers have four. No extra F3 write or internal
loop was fabricated. Requests blocked by priority generate no new invocation.
F3 genuinely selects white noise clocked by tone2, emits original tone2-off,
and suppresses music tone2/noise until the original release path.

At THZ request30, suppression is30..35, release36; both music readers next
become eligible at37. At request73, suppression is73..78, release79; music noise
becomes eligible85 and tone2 at97. Thus release is not an invented immediate
restart of a note/envelope. All delay, suppression and physical output states
match the original.

Solo A7 F2 at7 restores savedDE11=0 through current data latch7 before its own
FF; during THZ it restoresE4 through latch3 at36 or79. Ordered protocol writes
preserve those different contexts rather than reinterpreting zero as a noise
latch. At solo termination attenuation is off, yet native LFSR state changes
across31 adjacent post-window boundaries. The persistent chip is not recreated
or frozen on reader completion. Full register/counter/LFSR snapshots match the
reference diagnostic in every new PCM run.

The FD-specific cases preserve raw flag/pointer behavior under retransmission,
release and replacement. Actual A2 begins ordinary mode at1, executes FD at2,
and is inactive35 with the raw bit cleared. Spring replacement reloads normal
header flags, clearing raw mode at the authentic replacement tick. Synthetic
transition probes separately cover clearing FD and parsing an ordinary note
again, with signed transpose and duration/modulation variations. They are
authored test data, not additional game requests or production sound records.

## Stateful A1L versus original/MAME audio

Unchanged accepted PAL3,546,893Hz,44,100Hz signed16 mono,735-frame/60Hz cadence
and tick-boundary emission are used. No Z80-cycle/hardware sample identity or
human listening claim is made.

| Solo | Mix max LSB | Mix RMS LSB | Tone2 max LSB | Noise max LSB | Frames incl32 post ticks |
|---|---:|---:|---:|---:|---:|
|A1 |3 |0.193826 |3 |0 |45570 |
|A2 |3 |0.161159 |3 |0 |49245 |
|A7 |3 |0.194464 |0 |3 |28665 |

All19 new cases measure mix max2..4 signed16 LSB and per-voice max0..3, with
zero compared core register/counter/LFSR mismatches. [pcm.json](../data/m5-a2c2/pcm.json)
retains separate mix/voice maximum and RMS, block-RMS envelope differences,
lengths and hashes. Driver envelope and physical attenuation state are exact.
No new value exceeds the previously observed5LSB range; no tolerance or A1L
arithmetic changed. That remains an observed engineering qualification, not
advance permission for future content.

All81 candidate outputs are identical under735 versus100+635 render partitions.
All62 prior candidate PCM outputs remain byte-identical to accepted files,
including8A's original+8192 held DC. Three fresh processes reload the new SCSP
and play A1/A2/A7 to completion plus post-window, with original-tool imports and
ROM/VGM/dry-bank access forbidden. Every WAV matches the corresponding independent
candidate exactly. Only private SCSP, host requests and unchanged A1L enter
PC-style playback; no recorded combined event timeline is an input.

## Private data and Python resource measurements

SCSP stays **v1**, explicit horizon **4200**, now **8559 bytes** (+403 over8156).
It has27 unique headers,52 validated data records,5554 original data bytes (+54),
462 header bytes and70 priority entries. Raw values total6086 bytes; validation,
address and hash metadata adds overhead. Record JSON27508 bytes. Bank SHA-256:
`fbc69aa85ed782089630197ce791769b6a25ace2abccf47147e1e81f1c434052`.
All24 old headers and5500 data bytes are identical; standalone A2/B1/B2/C1 banks
remain untouched. Synthetic FD probes are excluded from the expanded bank.
Old SCSP records still load; new A2 requires the C2 FD-capable decoder and
older decoders reject that command explicitly.

Python benchmark6720 ticks includes2880 active and3840 inactive/post ticks.
Combined median0.8µs, active median3.2µs, inactive median0.7µs, p9911.3µs and
max59.5µs in this run. Comparative current/peak allocation: old516472/661035
bytes, new517487/665975 bytes. Scope is sparse Python bank, decoder and bounded
flow log; excludes interpreter baseline and PCM. These are **not GameMaker
decoder measurements**. Per-case stream and write workloads remain in
[emission.json](../data/m5-a2c2/emission.json).

## Coverage, remaining risks and proposal only

All70 original rows preserve names and relationships: **27 verified in tested
scope,7 empty/control,36 unverified**. This comprises15 music programs and12
SFX, not27 universally interchangeable audible assets or all request phases.
Original68 indexed headers and61 bounded solo-emission fingerprints remain
separate metadata counts. No speculative labels were added.

**Proposed next small batch:** original class preflight then Manager-selected
implementation of B0 (coupled-white-noise retrigger), B7 (tone2-periodic-noise
retrigger) and BA (tone1 plus coupled-white-noise multi-slot). This proposal
uses the already accepted P1C class catalogue, not new executions or production
records. Existing fixed-white-noise classification contains B8, already verified;
do not invent another unverified fixed-noise ID merely to fill a category.
Each future class needs its own priority/retrigger/DE11/latch/ownership gate.
No next-batch work started.

FD on other readers, positive table pitch, DE-relative envelope controls,
E2/E4/E5/E8/ED/F4/FA and other unverified operations, alternate envelope bases,
DE08 and numericD0/D1/D2 remain separate risks. Demand extraction covers selected
paths, not arbitrary interference or an unlimited loop/horizon. No broader
language investigation was performed.

## Regression, negative controls and preservation

**65 tests PASS:**51 inherited contracts plus14 C2 command/evidence tests.
The FD prerequisite separately compares actual67 ticks, six synthetic24-tick
mode transitions and16 direct original-handler edges. New negative controls
reject truncated FD operands, missing next pointers, unsupported reader
transitions and unrelated commands. Treating FD as a NOP fails actual A2 at2;
omitting A7 terminal writes fails at7. Prior source/pointer/corruption/loop/stack/
unknown-opcode/horizon tests remain green. No failing result was replaced by
silence, padding, altered expected output or widened tolerance.

```text
python tools/m5a2c2/fd_gate.py PRIVATE_ROM
python tools/m5a2c2/proof.py PRIVATE_ROM
python tools/m5a2c2/pcm.py
python tools/m5a2c2/evidence.py
python tools/m5a2c2/isolation.py
python -m unittest discover -s tests -p test_m5a2*.py
python tools/m5a2c2/package.py
```

Use existing Python3.12/NumPy and the unchanged pinned local renderer/A1L DLL.
ROM is needed only for extraction/fresh original execution. Program records,
detailed traces and WAV/VGM stay outside Research Git in workspace
`private-research/m5-a2c2`; the separate archive is in `releases`. Public output
is safe source, semantics, tests, aggregate numbers and integrity receipts.
Packaging verifies all ten earlier proof archives, standalone A2/B1/B2/C1 banks,
47 accepted M4 payloads, clean accepted POC and A1P source/native/compiled VM
artifacts read-only. No ROM or DLL is included in the new archive.

**STOP for Manager review.** No other request ID, GameMaker work, Sound Test,
long music, component release, upstream contact or Research main merge follows
automatically from this result. The personal learning/documentation purpose
and the optional distribution-authority boundary remain intact.
