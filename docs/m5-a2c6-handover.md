# M5-A2C6 — three preflighted tone2 candidate proofs

**B4, BD and C2 PASS within authenticated tested scopes. GO to review a separately
authorised isolated GameMaker decoder feasibility gate; STOP for Manager now.**
No accepted decoder semantics, FD scope, SCSP v1 or A1L source changed.

25 October2026. Branch `research/m5-a2c6-preflight-tone2-proof` starts exactly at
C5 `fed0cfbe5c167fa07812bb9973da1b88082fc7aa`; management AGENTS/MEMORY/ROADMAP read
at `55aa32c7b0672e3817696740a94592e7c65072d8`. C5 preflight/handover, original language
specification and C2 FD analysis were read. Authenticated original ROM SHA-256:
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
Accepted M4 POC `11bff34356d5f5d979218896dc95fdc4bb265eae` remains read-only.

## Candidate verdicts and exact original gate

C5 original-only evidence was not used to promote requests. C6 independently
extracted required source records and completed candidate runs before creating
each independent original Z80 oracle. Fresh original-only solos+128 post and THZ
checks also reconfirm the accepted preflight: [preflight.json](../data/m5-a2c6/preflight.json).

| ID / existing name | Original/candidate inactive tick | Candidate post ticks | Slots / priority | Verdict |
|---|---:|---:|---|---|
| B4 Results tally / continue countdown feedback |31 |32 |tone2 DF30/C0,120 |PASS |
| BD Booster-pad feedback |23 |32 |tone2 DF30/C0,88 |PASS |
| C2 Spring Shoes relaunch feedback |46 |32 |tone2 DF30/C0,64 |PASS |

All use initial flag80, multiplier1, envelope base49FD. No own F3, noise reader,
raw header or FD instruction; no unclassified opcode/table-pitch/alternate base
was reached. All four physical attenuations finish15, with no new solo writes,
reader reactivation or retained enabled output in32 candidate/128 original-only
post ticks. Native counters continue rather than being reset on inactivity.

**158 exact original-driver scenarios /42,075 ticks /196,084 ordered PSG bytes.**
All138 C5 scenarios (39,319 ticks/185,185 bytes) retained;20 new cases add2756 ticks/
10,899 bytes. Per tick: every ordered port byte, original timing, physical PSG
register/data latch, DE11, shared IY, all336 channel bytes and12 relevant globals,
priorities/mailboxes, pointers/durations/envelopes, suppression and ownership.
Original control-transfer targets/ticks/slot order match. Zero unexplained
differences or numeric/timing tolerance. No combined oracle timeline is playback
input: [emission.json](../data/m5-a2c6/emission.json).

## Focused operation-level verification

An observational subclass calls the **unchanged accepted decoder** and records
command/pitch before/after state and table-data reads. It completes before a fresh
original driver is created. Original hooks compare the same boundaries: command
entry46D9 and return46E9 (normalising the original caller's pending DE increment),
pitch entry42AF/return4502, shared-IY reload42F6, actual table value4610. Every
new solo and interaction passes this additional zero-tolerance gate, including
all48 bytes of the relevant channel at command/pitch boundaries and shared IY.
The subclass supplies no playback events or alternative semantics.
[operations.json](../data/m5-a2c6/operations.json) gives counts, source hashes and
aggregate visited-path evidence; complete operation/channel traces stay private.

**B4 shared-IY:**30 solo pitch operations, six actual reloads at5/10/15/20/25/30.
Original IY=DE03 reads **IY+3=DE06**, value0, matching accumulated pitch/channel
state and writes. Original42F6 loads from current IY;42F9 stores the half-cycle
counter and42FC..4301 reverses the step. Replacing this with the saved modulation
record's byte is deliberately wrong. That negative changes channel state at5
while ordered PSG writes remain equal throughout the63-tick solo+post window.
Thus duration, emission or PCM alone would miss this error; full state is required.

**BD selector13:**four F5, four F0, two E6 and two F8/F9 pairs execute;22 pitch
operations. Exactly18 actual table reads visit **indices0..5** of selector13,
with no table control byte reached. C5's static176 ordinary bytes before82 is a
potential-table observation, not176 visited entries or a reached terminal82.
F5 selector47AC..47AF, E6 relative volume472D..473C, F8/F9 stack/pointers481C..4848
and actual table read4609..4610 all agree at their operations, including call/
return pointers and per-channel stack bytes. No envelope mechanism was invented.

**C2 loops/transpose:**nine F7 and nine FB operations, at ticks
26,30,30,34,38,38,42,46,46. Five branches are taken and four fall through; actual
returned pointers A3EF×5, A400×3, A40B×1 match. Channel loop indices/counters,
FB transpose before/after, pending stream pointer and subsequent modulation/
pitch state are exact at every operation. F7 original4849..485F and FB4748..474E
retain their accepted semantics. Omitting either counted branching or transpose
fails state and ordered writes at26. Matching inactivity46 is not the loop proof.

## Selected ownership, priority and physical-state cases

The17 new interactions cover each effect during THZ; early/late four-phase
retriggers; a priority chain and blocked lower/reset requests; accepted white,
periodic and fixed-noise partners; B0 over C2; BA plus B4; and fade/reset followed
by fresh requests. No Cartesian expansion or other new request ID was attempted.

Priority chain admits C2 at30, BD40, B4 at42, then C2 at80; BD43 is rejected during
B4. Solo B4 rejects BD3/C2 at6, admitting BD40 after completion. Numeric resetF8
is rejected during B4 priority120 but admitted over C2 priority64, after which
fresh BD plays. SFX-admission hooks exclude the separate reset dispatch; its full
port/global/channel effects are independently compared. Host order is not admission.

Each retrigger schedule admits four requests: B4 30/32/50/100, BD30/34/43/90,
C2 30/34/60/130. These targets have no F3. Genuine F3 operations in mixed cases
come from their accepted noise partners and remain ordered, including repeated
periodic controls. No synthetic noise history or new F3 operation is introduced.

White A3→B4, periodic B7→BD, A7→C2 and B0 over C2 reach overlapping reader lifetimes
without simultaneous physical tone2/noise enablement in those solo-seeded cases.
Fixed B8 plus B4 reaches30 physically enabled tone2/noise overlap ticks, then
**102 held noise ticks36..137 despite write inhibition**, offFF138 and release139.
The210-tick window includes this full tail. BA at30 then B4 at32 reaches all three
SFX slots; later resumed music must not be counted as extended SFX coexistence.

Noise F2 restoration uses actual current PSG latches: fixed B8 at139 sends saved0
through latch7; BA at34 sends E4 through latch5. New tone2 solos have no own DE11
restore. Native noise control/tone2 period/counters/LFSR are compared across mute,
release and replacement; the host does not recreate the chip at a sound boundary.
Original reset writes remain in order.

THZ music tone2 suppression and next reads: B4 suppresses30..59, resumes read61;
BD30..51/read61; C2 30..74/read97. F2 release does not force an immediate music
read. Detailed native/driver captures remain private; numeric facts and negative
controls: [facts.json](../data/m5-a2c6/facts.json).

## PCM, partitions and isolated playback

Unchanged A1L versus pinned original-driver/MAME, PAL3,546,893Hz,44,100Hz signed16
mono,735 samples per60Hz tick. Every new case measures full mix and four voices,
max/RMS residuals, block-RMS volume-envelope differences, frame count/hashes and
register/counter/LFSR parity. All compared native states match exactly.
[pcm.json](../data/m5-a2c6/pcm.json) retains full per-voice metrics.

| Case | Ticks | Mix max LSB | Mix RMS LSB | Voice0/1/2/3 max LSB |
|---|---:|---:|---:|---|
| solo-B4 | 63 | 3 | 0.124523 | 0,0,3,0 |
| solo-BD | 55 | 2 | 0.073097 | 0,0,2,0 |
| solo-C2 | 78 | 2 | 0.111364 | 0,0,2,0 |
| THZ-B4 | 150 | 3 | 0.231254 | 2,2,3,2 |
| THZ-BD | 150 | 3 | 0.216528 | 2,2,3,2 |
| THZ-C2 | 150 | 3 | 0.216046 | 2,2,2,2 |
| B4-retrigger | 180 | 3 | 0.246947 | 3,2,3,2 |
| BD-retrigger | 160 | 3 | 0.217144 | 2,2,3,2 |
| C2-retrigger | 230 | 3 | 0.230273 | 3,2,2,2 |
| tone2-priority-chain | 180 | 3 | 0.231087 | 3,2,3,2 |
| B4-block-lower | 120 | 3 | 0.102906 | 0,0,3,0 |
| white-A3-to-B4 | 100 | 3 | 0.106522 | 0,0,3,2 |
| periodic-B7-to-BD | 100 | 3 | 0.078766 | 0,0,3,2 |
| fixed-B8-with-B4 | 210 | 3 | 0.166404 | 0,0,3,3 |
| coupled-A7-to-C2 | 120 | 2 | 0.091906 | 0,0,2,1 |
| noise-B0-over-C2 | 130 | 3 | 0.139634 | 0,0,2,3 |
| B4-BA-concurrent | 150 | 3 | 0.243910 | 2,3,3,3 |
| fade-fresh-C2 | 180 | 3 | 0.161811 | 2,2,3,2 |
| reset-fresh-BD | 120 | 3 | 0.155036 | 2,2,3,2 |
| B4-rejected-reset | 130 | 3 | 0.123146 | 0,0,3,0 |

New maxima2..3LSB, no result above the earlier observed5LSB range. No universal
bound, resampler change, arithmetic correction or tolerance expansion is claimed.
No hardware cycle-timed identity or human listening test. Driver envelope state
is exact; measured waveform and block-RMS residuals are not called sample equality.

All158 candidate outputs are identical for735 versus100+635 partitions. All138
previous candidate PCM outputs are byte-identical, including8A's authentic held
+8192 DC. **All20 new solos/interactions** replay in separate fresh processes
from private SCSP and host schedules with ROM/Z80/VGM access forbidden. Every WAV
matches independent candidate decoding: [isolation.json](../data/m5-a2c6/isolation.json).
No captured combined PSG event program is consumed by runtime playback.

## Runtime bank, cost and catalogue

SCSP v1/horizon4200, pointer/call-stack/loop/operation limits unchanged. Bank
**10234B**, prior9667B, **+567B**;5930 authenticated source bytes (+131),588 header
bytes (+30),70 priorities, raw field total6588B.39 unique headers/67 validated data
segments, canonical record JSON32882B. All36 prior headers and5799 data bytes
are identical. Bank SHA-256:
`677e65cc6038bb193e9813b5890b2127dfa7d5b0b71f0553867995659d2ba5a6`.
The original eight standalone A2/B1/B2/C1/C2/C3/C4/C5 banks remain unchanged.
Container includes integrity/address metadata; no raw-ROM compression claim.

Python benchmark9800 ticks:5000 active median4.1µs,4800 idle0.7µs, combined2.4µs,
p9914.3µs,max47.6µs in this run. Whole-proof worst26 stream operations/21 writes
per tick. Traced previous current/peak540930/680059B, expanded546215/719105B,
increments5285/39046B. Scope is sparse Python bank/decoder and bounded diagnostic
transfer log, excludes interpreter base/PCM; **not native GameMaker performance**.

All70 rows: **39 verified within authenticated scope (15 music,24 SFX),7 empty/
control,24 unverified (13 SFX,11 music)**. Unknown names are unchanged; IDs, unique
headers and distinct audible output remain separate. Historical68 indexed records
and61 bounded solo-emission fingerprints are not universal completed-program or
audible-output counts. No original-only pending row was promoted without candidate
proof: [coverage.json](../data/m5-a2c6/coverage.json).

## Strategic checkpoint and preservation

[Strategic comparison](m5-a2c6-strategic-checkpoint.md) lists all ten remaining
historical tone2 IDs, three parked single-F3 effects and eleven music requests,
with language/loop/horizon risks. It compares further content research with a
new isolated actual-GameMaker interpreter/SCSP/scheduler gate. **Recommend the
latter for information gain:** A1P proved a native PSG host using a ROM-free
register script, not original-program decoding or SCSP validation in GameMaker.
The proposal defines exact state/stream/negative/audio/lifecycle/performance
gates and remains planning-only. No project, compiler run or next sound ID began.

**136 public tests PASS:113 inherited+23 C6 contracts.** Public evidence/source
receipt checks are distinct from158 original executions,20 operation-level and
native/PCM gates,20 isolated replays. New wrong modulation/envelope and missing
terminal cases fail; missing first data/unknown E2/corrupt SCSP fail explicitly.
Wrong saved-pointer IY and omitted C2 transpose/branch negatives are preserved.
Existing FD reader restriction, unsupported commands, pointers, stack, loops and
horizon negatives remain unchanged. C3 dedup negative is freshly rerun: dropping
the second B0/B7 equal F3 still causes36 LFSR mismatching ticks and16384LSB error;
valid second control resets LFSR32768 without resetting countdown21.

```text
python tools/m5a2c6/preflight.py PRIVATE_ROM
python tools/m5a2c6/proof.py PRIVATE_ROM
python tools/m5a2c6/operations.py PRIVATE_ROM
python tools/m5a2c6/pcm.py
python tools/m5a2c6/evidence.py PRIVATE_ROM
python tools/m5a2c6/isolation.py
python -m unittest discover -s tests -p test_m5a2*.py
python tools/m5a2c6/package.py
```

Pinned Python3.12/NumPy and accepted local reference tools required for research;
original comparisons need authenticated ROM, playback does not. Full source
records, command/channel traces, native captures and WAV/VGM remain outside public
Git under private-research/m5-a2c6. Separate private ZIP excludes ROM and DLL.
Packaging validates fourteen prior proof archives, eight banks,47 M4 payloads,
accepted M4 HEAD/clean tree and A1P source/native/compiled VM hashes read-only.
Public files contain safe source, semantics, aggregate metrics, tests and receipts.

**STOP for Manager review.** GO is a recommendation for a separately authorised
next gate, not C7/native implementation approval. No GameMaker/M4/A1P/A1L changes,
Sound Test, long music, additional IDs, DLL publication, upstream contact or main
merge. Personal learning, faithful experimentation and public ROM documentation
remain the purpose.
