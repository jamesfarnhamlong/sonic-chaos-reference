# M5-A2C1 common SFX — Manager handover

**All three authorised requests PASS. CONDITIONAL GO for a separately authorised
next SFX class:** supported tone2/coupled-noise classes can receive another
bounded proof; A2 requires authenticated FD command validation before promotion.
No fourth effect was implemented. Work stops for Manager review.

25 October2026. Topic `research/m5-a2c1-common-sfx` begins exactly at B2
`deca0a99cc59ec10b2ee7ad408cc8fd4c6d0f61e`; management read at
`b3c8b09f94bc285e300a636d9baa7548de9066ab`. Original ROM freshly authenticated:
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
The accepted A2/B1 decoder, E1 extension, SCSP v1 and A1L arithmetic are unchanged.
All new source is research orchestration, metadata, tests and documentation.
Accepted M4 POC `11bff34356d5f5d979218896dc95fdc4bb265eae` remains read-only.

## A. Original-only six-request class preflight

Before extraction/candidate playback, all six requests were run through the
authenticated original driver, complete solo lifetime plus128 post ticks, and
one THZ context (request at30, then through release/recovery). Headers, raw flags,
stream pointers, priorities, executed commands, pitch/envelope selectors,
F3 modes/repetition, slot use, savedDE11/latch releases and physical state are
in [preflight.json](../data/m5-a2c1/preflight.json). No preflight PCM was rendered.

| ID | Existing catalogue label | Original inactive tick | Class actually reached | Slot/latch | Priority raw | Scope |
|---|---|---:|---|---|---:|---|
|A4 | Player hurt with ring loss |82 | tone-only, algorithmic pitch + table volume, calls/loops | tone2 / C0 |70h | implement |
|A6 | Spring / rebound feedback |41 | tone-only, algorithmic pitch + table volume, repeated calls | tone2 / C0 |38h | implement |
|BF | Ring / Large Ring collection feedback |21 | tone-only, algorithmic pitch/ADSR | tone2 / C0 |38h | implement |
|A1 | Unknown $A1 |30 | tone-only, algorithmic pitch | tone2 / C0 |38h | preflight only |
|A2 | Unknown $A2 |35 | tone-only, FD raw-frequency mode reached | tone2 / C0 |38h | preflight only; FD unsupported |
|A7 | Unknown $A7 |7 | tone2-clocked white noise, raw-frequency initial flag | noise / E0 |30h | preflight only |

The three targets and A1/A2 produce no F3 commands or enabled physical noise
in their solo windows. A7 executes one F3 with mode7; it suppresses music tone2
and noise in the bounded THZ context. It has no repeated F3 in that observation.
None of the six has enabled physical output after its solo reader termination
over the128 observed post ticks. These are register observations, not a human
listening result or universal proof under other surrounding state.

A4/A6/BF all own only the SFX tone2 slot (`DF30`), and steal music tone2. Their
own F2 terminates with DF and does not restore DE11. Tone2 entry can emit FF and
inhibit a coupled-noise reader; that off is not a noise-generating F3. Fixed-rate
noise can coexist, depending on flags. Music resumes on an eligible next read,
not necessarily at the instant the SFX releases its slot. Release resets shared
priority. The original-only preflight reports each source header/envelope base,
selector, and bounded suppression/release observation without importing its
captured output into the decoder. Raw-header mode in A7 is treated as dynamic
original evidence; a generic music syntax scan is not misapplied to it.

FD in A2 is the only newly reached **unverified command** among these preflights.
Its source handler at `$47BA..$47C7` changes raw-frequency mode; it remains
disabled in this runtime. A1/A2/A7 have no new SCSP records, decoded PCM or
verification promotion. Unknown friendly names are preserved.

## B–C. Three-request implementation and exact interaction gate

The targets use existing stream control, envelopes, pitch modulation and their
original pointers; **no decoder language or native synthesizer change** was
necessary. Only A4/A6/BF were added to the private runtime bank.

| Request | Original/candidate inactive tick | Candidate post ticks | Final physical attenuation | Result |
|---|---:|---:|---|---|
|A4 |82 |32 |15,15,15,15 | exact PASS |
|A6 |41 |32 |15,15,15,15 | exact PASS |
|BF |21 |32 |15,15,15,15 | exact PASS |

No reader reactivates or new port byte occurs in those post windows. The
128-tick original-only physical checks confirm that extending the candidate
post-window was unnecessary for these solos. Runtime produces actual continuous
chip samples; it does not append silent PCM or infer off from inactive flags.

**62 scenarios /27,327 ticks /130,481 ordered bytes: exact PASS**, comprising
16 new cases/2480 ticks/12804 bytes and all46 B2 cases/24847 ticks/117677 bytes.
Every tick compares ordered bytes, physical PSG registers and data latch,
DE11, IY, all336 channel bytes and12 global bytes, priorities/mailboxes and
original control-transfer targets/ticks/channel order. Original SFX dispatch
admissions are separately logged. Candidate generation finishes before creating
the independent original Z80 oracle; no oracle timeline drives playback.

Thirteen new interactions cover THZ ring and spring; hurt after a completed ring
and concurrently with AC; ring retriggers at30/32/48/80 and spring retriggers at
30/33/60/100; spring→hurt replacement with rejected ring/spring/BC at45/50/55;
A3→BC→ring in coupled-noise history; B8→BC→spring with fixed noise; hurt during
B8/BC held noise; fade→fresh ring; numeric reset→fresh spring; and common SFX
over finite invincibility music. These schedules are admitted original sequences,
not artificial whole-pair recordings or a Cartesian coverage claim.

Observed context details:

- THZ ring suppresses music tone2 on30..49; next-read recovery is61.
- THZ spring suppresses tone2 on30..69; next-read recovery is73.
- Ring/spring retriggers listed above are all admitted. During hurt, the three
  lower-priority requests are rejected; only spring30 and hurt40 initialize.
- Hurt with AC at35 has all three SFX slots active: AC retains tone1/noise
  readers while hurt owns tone2. Their suppression/output behavior is exact.
- Coupled-noise A3 at1, BC at6 and ring at35 are all admitted. Ring has no own
  F3; the existing coupled-noise state supplies the clock/history interaction.
- B8/BC→spring holds real inhibited noise for104 ticks34..137, explicit off138,
  reader release139. B8/BC→hurt holds104 ticks63..166, off167, release168.
  These are existing authenticated noise partners, not noise invented for the
  new tone-only effects. Saved DE11 restoration and physical latch consequences
  are compared in the complete state/ordered-byte gate.

Repeated F3 noise-control generation by a newly decoded target was **not**
reached: these three targets are tone2 effects. A7's coupled-white-noise class,
other fixed/periodic-noise programs and their repeated-F3 paths remain later
research. The bounded partner scenarios and earlier controls remain scoped.

## D–E. Continuous PCM and three private ROM-free replays

Unchanged A1L at PAL3,546,893Hz,44,100Hz mono,735 frames per60Hz tick is compared
with original-driver/pinned-MAME audio. Writes preserve the accepted tick cadence,
not a new Z80-cycle-timed model. No human listening or hardware sample identity
is claimed.

| Solo | Mix max signed16 LSB | Mix RMS LSB | Tone2 max LSB | Noise max LSB | Samples incl32 post ticks |
|---|---:|---:|---:|---:|---:|
|A4 |3 |0.286278 |3 |0 |83790 |
|A6 |3 |0.058560 |3 |0 |53655 |
|BF |3 |0.166506 |3 |0 |38955 |

All16 new cases have mix maximum3..5LSB, per-voice maximum0..3LSB and zero
compared PSG register/counter/LFSR errors. **The two5LSB mix cases are
`hurt-concurrent` and `hurt-held-noise`**; their RMS errors are0.471188 and
0.324299LSB respectively. No case exceeds the previously observed5LSB range,
and no tolerance or A1L arithmetic was widened. Exact core/driver states and
the small per-voice residuals retain the established resampler qualification;
this does not imply universal numerical acceptance for untested content.

[pcm.json](../data/m5-a2c1/pcm.json) gives all mix/voice maximum and RMS errors,
per-voice block-RMS envelope differences, frame counts and hashes. Driver
envelope and physical attenuation state agree exactly. All62 candidate outputs
are invariant for735 versus100+635 render partitions. All46 prior PCM outputs,
including 8A's held+8192 DC, are byte-identical to accepted private files.

Three fresh processes reload the expanded SCSP and run A4/A6/BF through their
full solos and post windows, with original-driver imports and ROM/VGM/dry-bank
access forbidden. Each WAV matches the independently decoded candidate exactly.
Only SCSP, host requests and the existing A1L backend enter that runtime.

## F. Data, catalogue and next-class proposal

SCSP remains **v1**, horizon **4200**, now **8156 bytes** (+397 over7759).
There are24 unique program headers,48 validated data records,5500 original data
bytes (+120),432 header bytes and70 priority entries. Raw values total6002
bytes; addresses, lengths, hashes and validation metadata add container overhead.
Record JSON26232 bytes. Expanded bank SHA-256:
`9a8721d5993c4ddecfed13f9bdd49f0ace238ab292117f266b425fc8978c8409`.
All21 previous headers and5380 old data bytes match. Original standalone A2,
B1 and B2 banks/hashes are unchanged. Source authentication, missing-data errors,
unknown-command rejection, pointer/loop/call/operation budgets and4200-tick
horizon guard are unchanged.

Python timing benchmark7200 solo/post ticks: median3.0µs, p9912.3µs, max61.2µs
in this run. Comparative current/peak traced allocation: previous404157/444685
bytes, expanded512152/661035 bytes (+107995/+216350). This measures the Python
sparse bank, decoder and bounded flow log; excludes interpreter base and PCM.
The sparse Python representation has allocation overhead unrelated to just120
new ROM data bytes. It is not a native/GameMaker memory or performance result.
Per-case work and port-byte maxima are retained in [emission.json](../data/m5-a2c1/emission.json).

All70 catalogue rows retain original names and relationships:
**24 verified within tested scope,7 empty/control,39 unverified**. A1/A2/A7
remain in the unverified category with explicit preflight-only annotations and
no extracted runtime records. The24 headers represent15 music programs and9
SFX requests in their measured contexts; they are not a claim of24 universally
interchangeable audible assets. Original68 indexed headers and61 bounded solo
emission fingerprints remain distinct metadata, not a count of audible outputs.

**Proposal only:** next Manager-selected group may investigate A1's existing
tone2 class, A2's FD raw-frequency transition and A7's coupled-white-noise class.
FD needs exact source-backed command/state/corruption controls before enablement;
A7 needs phase-stratified tone2/noise and DE11/latch restoration checks. Neither
should be promoted from preflight alone. Other repeated-F3/fixed/periodic or
multi-slot effects need their own class gates. Existing risks remain table pitch,
DE-relative envelope controls, unverified commands, alternate envelope bases,
DE08, numericD0/D1/D2 and new interference phases. No new class was started.

## G–H. Checks, preservation and reproduction

**51 tests PASS:**41 unchanged previous contracts plus10 C1 tests. Accepted
62-case fresh original gate,16 new mix/four-voice comparisons,46 frozen PCM
regressions and three isolated playback proofs pass. Corrupted pitch data is
detected at1, omitted terminal writes at82, and deleting a required program
byte raises an explicit error. Earlier corruption, pointer, opcode, stack/loop
and horizon rejection tests remain green. No failure was adjusted into silence,
a looser timing gate or expected-output replacement.

```text
python tools/m5a2c1/preflight.py PRIVATE_ROM
python tools/m5a2c1/proof.py PRIVATE_ROM
python tools/m5a2c1/pcm.py
python tools/m5a2c1/evidence.py
python tools/m5a2c1/isolation.py
python -m unittest discover -s tests -p test_m5a2*.py
python tools/m5a2c1/package.py
```

Use existing Python3.12/NumPy dependencies and pinned local renderer/A1L DLL.
Only extraction/fresh oracle execution needs ROM access. Program data, full
captures and WAV/VGM stay outside Research Git in `private-research/m5-a2c1`;
the separate private proof archive is under workspace `releases`. Public Git
contains safe source, docs, tests, aggregate metadata and integrity receipts.
Packaging checks nine prior proof archive hashes,47 accepted M4 payloads,
clean M4 POC, standalone A2/B1/B2 banks, and A1P source/native/compiled VM files
read-only. The new archive excludes ROM and DLL.

**STOP for Manager review.** No other SFX, long music, GameMaker integration,
Sound Test, component publication, upstream contact or main merge is authorised
by this result. Optional component distribution approval remains separate.
