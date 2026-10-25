# M5-A2C5 tone2 SFX variation — Manager handover

**A5, A9 and AA PASS in the demonstrated scopes. GO for a separately authorised
proof of the three remaining preflighted tone2 requests. STOP for Manager review.**
B4, BD and C2 remain original-only: no candidate programs, PCM or decoder-status
promotion. Accepted decoder, FD reader guard, SCSP v1 and A1L are unchanged.

25 October 2026. Isolated branch `research/m5-a2c5-tone2-variation`, exact C4 parent
`caf5fb567b80313aed2328635ae1149c6c719aa2`; current management AGENTS/MEMORY/ROADMAP
read at `86652cafbbbbb8c4e399f1e299184e70c878d0ad`. C4 handover, accepted original
language specification, C2 FD source analysis and P1C class evidence were read.
Original ROM freshly authenticated SHA-256:
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
Accepted private M4 POC `11bff34356d5f5d979218896dc95fdc4bb265eae` remains read-only.

## Six-ID original-only preflight

Fresh unmodified original Z80 solos,128 post-completion ticks and a bounded THZ
context preceded candidate extraction. Historical tone2 labels were hypotheses
until this execution. [preflight.json](../data/m5-a2c5/preflight.json) records
headers, priorities, source hashes/pointers, actual commands, envelope/pitch
selectors, raw/FD visits, release, physical state and THZ suppression. Native
reference time advances during original preflight with output discarded; no
candidate PCM or runtime data for deferred requests is generated.

| ID / authenticated catalogue name | Header ROM / stream CPU | Priority | Inactive tick | C5 outcome |
|---|---|---:|---:|---|
| A5 / Unknown $A5 | $DFAC / $9FB6 | 56 | 128 | candidate PASS |
| A9 / Extra life feedback | $E04B / $A055 | 120 | 66 | candidate PASS |
| AA / Goal-sign spinning feedback | $E079 / $A083 | 112 | 5 | candidate PASS |
| B4 / Results tally / continue countdown feedback | $E1B9 / $A1C3 | 120 | 31 | original-only; unverified |
| BD / Booster-pad feedback | $E330 / $A33A | 88 | 23 | original-only; unverified |
| C2 / Spring Shoes relaunch feedback | $E3CC / $A3D6 | 64 | 46 | original-only; unverified |

All six actually own **only SFX tone2 slot5/DF30, latchC0**; header flag80,
multiplier1, envelope baseCPU49FD, no raw-frequency header, no FD instruction,
no F3 or own noise output. A9 transpose7 and BD transpose4 are original header
metadata; the others are0. All have attenuation15 on all channels at completion
and throughout128 post ticks, no retained enabled solo physical output. No new
name is assigned to Unknown A5.

| ID | Original reached commands / notable variation | Envelope / pitch observations |
|---|---|---|
| A5 | E0,F0,F2 | algorithmic ADSR selector128, algorithmic modulation128 |
| A9 | E6×4,F2,F5×4,F8×3,F9×3 | volume selector0/4, no modulation; three calls/returns |
| AA | F2,F5 | volume selector4; five-tick reader lifetime |
| B4 | E6×6,F0,F2 | selector0, algorithmic modulation128; original shared-IY reload atDE03 |
| BD | E6×2,F0×4,F2,F5×4,F8×2,F9×2 | selector0/13, modulation128; two calls/returns |
| C2 | E6×12,F0,F2,F5,F7×9,FB×9 | selector2, modulation128; counted loops and transpose |

Bounded ordinary structural scan found no unclassified command. Original dynamic
paths reached no table pitch or alternate envelope base. The source table scan
for selectors4/13/2 encounters first control82 after52/176/12 ordinary bytes;
these scans are **potential table paths, not claims that every entry/control
executes during the finite effect**. No new DE-relative envelope mechanism was
identified. Deferred BD selector13 and C2 loop/transpose behaviour are original-only
observations, not evidence of candidate correctness. B4's observed IY dependency
likewise still needs its own full-state candidate gate. No missing operation
was guessed, enabled or treated as silence.

## Interpreter and independent exact gate

The existing interpreter handles all three targets without modification. E0 ADSR
uses original CPU4889..48A2; F0 modulation486A..4877 and original pitch update4267..
4304; F5 selector47AC..47AF and volume reader4546..4638; E6 relative volume472D..
473C; F8/F9 call/return481C..4848; F2 release47C8..481B. These are the previously
recovered rules in the accepted language specification, not a new opcode class.
FD remains restricted to authenticated SFX tone2 slot5/latchC0; no extension was
needed. Candidate records contain original source data/control flow, no timed
song actions or captured combined port rows.

**138 exact scenarios /39,319 ticks /185,185 ordered PSG bytes PASS.** This retains
all118 C4 scenarios/35,704 ticks/170,201 bytes and adds20 scenarios/3615 ticks/
14,984 bytes. Every tick compares ordered port bytes and physical PSG registers/
latch, DE11, IY, all336 channel bytes and12 globals, including original priority,
mailbox, pointer/duration/envelope/ownership and suppression state. Original
jump/call target order/ticks/channel and candidate control transfers are checked;
return pointers and resulting state match in the per-tick channel comparison.
Actual SFX admissions are recorded independently of host request order.
Candidate execution completes before each original Z80 oracle is instantiated.
Zero timing/state tolerance: [emission.json](../data/m5-a2c5/emission.json).

| Target | Original / candidate inactivity | Candidate post ticks | Terminal physical attenuation | Verdict |
|---|---:|---:|---|---|
| A5 |128 |32 |15,15,15,15 | PASS |
| A9 |66 |32 |15,15,15,15 | PASS |
| AA |5 |32 |15,15,15,15 | PASS |

There are no solo post-window writes or retriggers; registers stay stable while
chip counters continue naturally. Original terminal writes are kept, never
replaced with silence inferred from inactive readers.

## Priority, noise, latch and recovery interactions

The17 new interactions include each target during THZ; four admitted phase
retriggers per target; a tone2 priority chain; lower-priority rejection and later
admission; white A3/A7 and periodic B7 interference; fixed B8 coexistence; B0 over
A5; BA plus A9; and original fade/reset followed by fresh requests. These are
bounded original-admissible host schedules, not natural gameplay or an exhaustive
pair matrix. Only the three authorised new IDs enter candidate records.

The priority chain admits A5 at30, AA at40, A9 at42 and A5 again at110. AA at43 is
rejected while A9 priority120 is active. Solo A9 similarly rejects AA at3 and A5
at6, then admits AA at70 after completion. Numeric resetF8 (priority57) is rejected
during A9, but admitted at40 over A5 priority56; fresh AA at60 follows. The SFX
admission hook excludes reset because reset is a global path: the full ordered
writes/global/channel comparison establishes its actual reset execution. Host
order is never described as admission merely because it appears in a case name.

Admitted retriggers: A5 at30/35/90/240, A9 at30/34/80/180, AA at30/32/39/73.
Early requests replace an active instance; later requests follow completion.
These tone2 targets execute **zero F3 commands**, including retriggers. Noise
commands in mixed cases belong to independently verified partner programs;
none was invented for a tone2 effect.

White A3→A9 and A7→A5, periodic B7→AA, and B0 over A5 show true overlapping
reader lifetimes, while their solo-seeded physical tone2/noise output is not
simultaneously enabled. Exact inhibition/recovery and native clock state are
retained. Periodic B7 still executes both genuine F3 operations despite the
new tone2 request. BA at30 then A9 at32 reaches three active SFX slots; this is
real overlapping tone1/tone2/noise ownership, not a union of separate lifetimes.
The noise output metric in that THZ case also includes later resumed music;
it must not be read as103 audible SFX-coexistence ticks.

**Fixed B8 plus A9** is distinct:65 ticks of concurrent tone2/noise reader activity,
62 ticks of both physical channels enabled. After A9 release at71, B8 has
write-inhibited flags but held physical noise attenuation7 over **71..137 (67 ticks)**.
Noise offFF occurs138, then original F2 release139 sends saved0 and FF through
current latch7. The210-tick comparison includes the whole held/off/release tail.
A9 becoming inactive does not silence or recreate that persistent noise state.
Native counter/LFSR snapshots remain exact across the tail.

Partners expose original saved-DE11 data-latch dependencies: white A3 noise F2
at49 writes0 through latch5; periodic B7 at7 also uses latch5; B0 at36 and fixed
B8 at139 use latch7. BA noise release34 restores E4 through latch5 during A9.
New tone2 solos have **no own DE11 restore**. These are protocol data writes
through the actual current latch, not guaranteed noise latches.

THZ music tone2 suppression lasts30..156 for A5, next eligible read161;30..94
for A9, read97;30..33 for AA, read37. Stream release and next music read are
separate events. Full state and native chip snapshots compare them exactly.
Native diagnostics include all noise-control writes (music and stream controls
separately identified), per-tick tone2 period/noise countdown/LFSR/slot flags and
core22-field state. No host-side chip reinitialization occurs at a request boundary; original reset writes remain. Detailed
traces stay private; [facts.json](../data/m5-a2c5/facts.json) retains numeric summaries.

## Continuous A1L versus pinned original/MAME audio

Accepted unchanged PAL3,546,893Hz,44,100Hz signed16 mono,735 samples/60Hz tick.
Each of20 new schedules has mix and four-voice max/RMS comparisons, block-RMS
volume-envelope differences, hashes and exact register/counter/LFSR comparison:
[pcm.json](../data/m5-a2c5/pcm.json).

| Case | Ticks | Mix max LSB | Mix RMS LSB | Voice0/1/2/3 max LSB |
|---|---:|---:|---:|---|
| solo-A5 | 160 | 3 | 0.161256 | 0,0,3,0 |
| solo-A9 | 98 | 3 | 0.199437 | 0,0,3,0 |
| solo-AA | 37 | 3 | 0.106422 | 0,0,3,0 |
| THZ-A5 | 220 | 3 | 0.244178 | 3,2,3,2 |
| THZ-A9 | 160 | 3 | 0.250951 | 2,2,3,2 |
| THZ-AA | 100 | 4 | 0.236384 | 2,2,3,2 |
| A5-retrigger | 420 | 4 | 0.263895 | 3,2,3,2 |
| A9-retrigger | 300 | 4 | 0.279390 | 3,2,3,2 |
| AA-retrigger | 150 | 3 | 0.227677 | 2,2,3,2 |
| tone2-priority-chain | 280 | 4 | 0.263692 | 3,2,3,2 |
| A9-block-lower | 140 | 3 | 0.176319 | 0,0,3,0 |
| white-A3-to-A9 | 140 | 3 | 0.163031 | 0,0,3,2 |
| periodic-B7-to-AA | 100 | 3 | 0.480773 | 0,0,3,2 |
| fixed-B8-with-A9 | 210 | 4 | 0.180432 | 0,0,3,3 |
| coupled-A7-to-A5 | 180 | 3 | 0.153173 | 0,0,3,1 |
| noise-B0-over-A5 | 200 | 3 | 0.142738 | 0,0,3,3 |
| A9-BA-concurrent | 200 | 4 | 0.261289 | 3,3,3,3 |
| fade-fresh-A5 | 260 | 3 | 0.167460 | 2,2,3,2 |
| reset-fresh-AA | 120 | 3 | 0.157683 | 2,2,3,2 |
| A9-rejected-reset | 140 | 3 | 0.176319 | 0,0,3,0 |

Mix maxima3..4LSB, voice maxima0..3LSB; no new result exceeds previously observed
5LSB. That is a measurement, not advance acceptance for future content. No
arithmetic, resampler or tolerance changed. Driver envelope/attenuation state is
exact, while waveform and block-RMS residuals are reported rather than called
sample-identical. No new human listening or cycle-timed hardware claim is made.

All138 candidate renders are identical for735 versus100+635 partitions. All118
previous candidate PCM outputs remain byte-identical, including8A's authentic
constant+8192 post-completion DC. **All20 new schedules** replay in separate fresh
processes with ROM, original Z80 imports and VGM access forbidden, using SCSP,
host schedule and unchanged A1L only. Every WAV is byte-identical to independently
decoded playback: [isolation.json](../data/m5-a2c5/isolation.json). No candidate
playback reads captured combined oracle events.

## SCSP v1 and Python measurements

Expanded private bank **9667B**, prior9352B, **+315B**. There are36 unique headers,
61 validated data segments,5799 original data bytes (**+64**),558 header bytes
(+30) and70 priorities: raw value total6427B. Canonical record JSON31225B;
addresses/hashes/lengths and framing contribute container overhead rather than
implying a raw-ROM compression benefit. Bank SHA-256:
`13ce1c09bbfacc29976dd01a935e2bc4f909eb30a0f930ac37d3750588b6a2db`.
All33 old headers and5735 data bytes are identical. All seven prior standalone
A2/B1/B2/C1/C2/C3/C4 banks remain unchanged. B4/BD/C2 headers are explicitly
absent from the new runtime bank; no candidate case or PCM schedule uses them.

Source authentication, version1, pointer/loop/call-stack/operation budgets and
**4200-tick explicit coverage horizon** are unchanged. Unknown/missing data still
raises errors; no silent zero fill or expanded FD scope.

Python benchmark14750 ticks:9950 active median2.6µs,4800 idle median0.7µs, combined
median2.5µs, p998.3µs, max45.9µs in this run. Whole-proof peak20 stream operations/
21 ordered writes per tick. Traced old current/peak535863/676021B; expanded
536970/680059B, increments1107/4038B. Scope is sparse Python bank/decoder plus
bounded diagnostics, excludes interpreter baseline/PCM buffers, and is **not
native GameMaker performance**.

## Complete catalogue and remaining work

All70 rows updated: **36 verified within tested scope (15 music,21 SFX),7
empty/control,27 unverified (16 SFX,11 music)**. Original Unknown A5 remains
Unknown. Request IDs, unique program headers and distinct audible output are
separate: inherited68 indexed records/61 bounded solo-emission fingerprints do
not establish universal complete audible identities. No sound class is claimed
fully verified in every possible interference phase.

Remaining SFX by authenticated historical P1C class:

| Class | Remaining IDs / evidence level | Count |
|---|---|---:|
| Tone2-only | B4,BD,C2: fresh original-only full solo+128 post and THZ, no candidate |3 |
| Tone2-only | A8,AB,AD,AE,B2,B3,B5,C0,C1,C3: historical class, not freshly inspected |10 |
| Single-F3 coupled white noise | BB,BE,C4: historical class only; parked |3 |
| Fixed-noise / periodic / repeated-F3 / multi-slot | zero remaining in the historical37-SFX inventory; earlier representatives tested |0 |

B4/BD/C2 retain their **unverified decoder status**; only their original-preflight
scope is recorded. Their reached operations appear already supported, but BD's
selector13, B4's modulation reload and C2's loops/transposes require actual
independent decoding, emission/native and PCM gates. They are the practical
next **proposal only**, after separate Manager authorisation. None is implemented
here. No newly observed command or envelope mechanism demands a language
extension in C5; that does not prove all ten unsurveyed tone2 programs are simple.

Table-pitch programs, DE-relative envelopes, alternate envelope bases,
E2/E4/E5/E8/ED/F4/FA, FD beyond its existing reader, DE08 and numericD0/D1/D2 remain
explicit language/reader boundaries. No particular unexecuted request is claimed
to require them. Full70-row status and class inventory:
[coverage.json](../data/m5-a2c5/coverage.json). No next batch or music expansion began.

## Negative controls, preservation and reproduction

**113 public tests PASS:95 unchanged inherited plus18 C5 contracts.** These
public evidence/source-receipt tests are distinct from the138 fresh original
executions and new native/PCM/replay runs. Wrong omission of A5 modulation is
detected at7; wrong table-envelope handling fails A9 at33 and AA at1. Missing
terminal writes fail at128/66/5. Removing each required first stream byte or
inserting unsupported E2 fails explicitly. New packed-bank checksum corruption
is rejected. Inherited pointer/stack/loop/horizon and FD-scope controls remain.

The C3 equal-F3 dedup negative is freshly rerun on this bank: B0/B7 each still
produce36 wrong LFSR ticks and16384LSB maximum waveform error if their second
identical control is removed. The valid second control resets LFSR32768 while
noise countdown remains21. Repeated writes are never consolidated.

```text
python tools/m5a2c5/preflight.py PRIVATE_ROM
python tools/m5a2c5/proof.py PRIVATE_ROM
python tools/m5a2c5/pcm.py
python tools/m5a2c5/evidence.py PRIVATE_ROM
python tools/m5a2c5/isolation.py
python -m unittest discover -s tests -p test_m5a2*.py
python tools/m5a2c5/package.py
```

Use pinned local Python3.12/NumPy/native reference infrastructure. The original
gate requires private authenticated ROM access; eventual playback does not.
New private data, full traces, source records, native diagnostics and WAV/VGM
remain under private-research/m5-a2c5 outside public Git. The separate private
ZIP contains no ROM or PSG DLL. Packaging verifies thirteen prior proof archives,
seven standalone banks,47 M4 payloads, accepted M4 HEAD/clean tree and A1P source/
native/compiled VM hashes read-only. Public additions contain safe source,
semantics, numeric summaries, tests and integrity receipts only.

**GO for separately authorised B4/BD/C2 candidate investigation; STOP now for
Manager review.** No GameMaker/Sound Test work, native integration, additional
SFX/music batch, rights-policy change, component publication, upstream contact
or topic merge into main. The purpose remains personal learning, faithful
experimentation and useful public ROM documentation.
