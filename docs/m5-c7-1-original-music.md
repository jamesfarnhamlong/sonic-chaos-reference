# M5-C7-1: original $83 / $92 music research

**26 October 2026. Both IDs HOLD for complete decoder playback and future
GameMaker integration. Original repeating lifecycles independently authenticated.**
The two complete solos fail existing safety guards. These are proven coverage
boundaries, not evidence that the ROM songs need musical correction. No decoder,
SCSP format, guard, native DLL, GameMaker project or previous proof changed.

Research parent: `research/m5-a2c6-preflight-tone2-proof`
`45b15a578285add733fa1def9a7e7174c0215c2d`. Canonical AGENTS/MEMORY/ROADMAP read
from `main@759cbd8a8077b75a8d5609de63281fc9aa2ced63`. C6 coverage, emission,
operation, planning, language and handover evidence were inspected. This task's
explicit two-ID assignment supplies authority beyond the older root's parked
roadmap. Manager-owned documents remain untouched.

Fresh local Europe v1.2 ROM authentication:
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
Public files contain test methods, source semantics, aggregate numerical evidence
and hashes. Private source records, detailed operations, state/write captures,
SCSP and audio remain outside this repository under `private-research/m5-c7-1`.

## Verdicts and actual source boundaries

| ID | Original identity | Verdict | Last exact solo tick | First candidate rejection |
|---|---|---|---:|---|
| $83 | Gigalopolis Zone music | HOLD | 2783 | tick2784: source data accessor rejects $4634; reloaded bank rejects unvalidated pointer |
| $92 | Mecha Green Hill Zone music | HOLD | 3265 | tick3266: F7 loop index4 outside validated 0..2 |

Both use four music slots, latches80/A0/C0/E0, multiplier1, envelope base49FD and
raw priority80 (admitted stored priority0). $83 tone transpose is -9, tempo4;
$92 tone transpose is -8, tempo0. These are original divider bytes, not a BPM
estimate or an instruction to change the accepted60Hz sound clock.

**$83 pitch data:** original note routine4415..4426 wraps the note-plus-transpose
sum to8 bits, then forms4436+2×index. At2784, music tone1 produces index255,
address4634, and reads the original word across4634/4635. This reaches the
driver's executable address region as *data*. The original takes this path;
the candidate's address arithmetic reaches the same address and correctly fails
SCSP's narrower data-region contract. Four such original reads occur in the
6666-tick two-period observation. Do not clamp the note, skip it, substitute
another pitch, publish those bytes, or broadly admit executable-region records.
The bytes/word and full note operations remain private. A future bounded
data-as-code provenance/container gate is needed before complete playback.

**$92 F7 index4:** original handler4849..485F adds39 to the index, uses the
resulting channel byte as a loop counter, initializes it from the stream only
when zero, decrements with8-bit wrap and branches while nonzero. Index4 therefore
uses offset43, inside the prototype's nominal42..47 call-stack storage area.
Four extended operations occur at3266,4034,6914,7682; the original counter moves
0→1 then1→0 in each period. Stack cursor is48 at those operations: this is
**not proof of an actual simultaneous stack collision**. All299 reached F7
operations across the two songs pass independent before/after channel assertions.
Supporting index4 needs a source-backed lifecycle/alias boundary, including stale
bytes/restarts and active call contexts. Do not globally raise the loop limit.

## Fresh original preflight and independent oracles

[preflight.json](../data/m5-c7-1/preflight.json) records13 original-only scenarios,
14500 original ticks. The capture phase imports no candidate decoder. All full
original captures and their hashes are frozen before candidate extraction or
comparison. The separate [boundary probe](../tools/m5c71/boundaries.py) authenticates
the original note/index behaviour and whole-period continuation before the final
candidate gate; it also imports no decoder. No candidate-produced timeline is
an oracle or runtime input.

Within the4200-tick original solos:

| ID | Actually dispatched commands | Pitch behaviour | Volume/table behaviour |
|---|---|---|---|
|83|E0×1,E1×3,F5×9,F6×4,F7×29,FB×5|selector0, ordinary note-table lookup; no modulation reload|selectors0,4,19,23,29,30,39,40,128;11720 actual table reads plus algorithmic envelope|
|92|E1×1,E6×33,E7×10,F0×6,F5×17,F6×4,F7×133,F8×13,F9×12,FB×2|selectors0/128;169 actual shared-IY reloads from8451/845F|selectors0,7,13,18,28,29,30,39;15987 actual table reads|

Actual envelope entry indices/counts and terminal82 observations are listed per
selector in the numerical preflight. $83 uses E0 algorithmic attack/decay/release;
$92 exercises E7 tie/gating, relative attenuation, F0 modulation, calls/returns,
counted loops and transpose. No raw reader, FD, alternate envelope base or
unclassified dispatched opcode is reached in these original solos. This does
not make F7 index4 or out-of-region pitch data supported. Whole original
two-period command counts, table reads and IY counts are separately recorded in
[boundaries.json](../data/m5-c7-1/boundaries.json); they are not candidate coverage.

For each target, scenarios cover ring/spring/fixed-noise/tone2/multislot steals,
priority rejection, retrigger/restart, death→stage-card→fresh target, fade/reset
and recovery. One cross-song scenario tests83→92→83. Context partners were
already accepted in C6: this batch authenticates no third new request.
Priority B4 at30 admits; BD31 and C232 are blocked; BD70 and C2100 admit.
The mixed steal schedule reaches suppression in music slots1/2/3 and SFX5/6.
Full channel bytes carry suppression/inhibition and release state; ownership is
tested through those original flags and admissions, not invented owner RAM.
Complete per-tick priority/mailbox, suppression, physical register state and
DE11 are compared, including restoration and subsequent reads. This is a
bounded schedule matrix, not arbitrary gameplay/interrupt phase coverage.

## Independent loops and safe continuation boundary

| ID | First recurrent state | Repeated state | Period | Original proof through | Transfer edges/period |
|---|---:|---:|---:|---:|---:|
|83|522|3594|3072|6666|17|
|92|511|4159|3648|7807|95|

No THZ certificate is borrowed. Keys include **all400 driver RAM bytes
DE00..DF8F, shared IY, logical PSG registers and data latch**. Independent
re-execution compares every tick of two full periods:0 state differences,
0 ordered-write differences, exact transfer edges including tick, slot, source
and target. $83 has13529 writes per recurrent period; $92 has23960.
Both periods and the first repeat fit within4200. Original-only verification
of the *next full period* extends beyond4200; it changes no runtime horizon.

This proves deterministic original-driver continuation under the same solo
schedule. It does **not** prove chip oscillator/LFSR phase recurrence or permit
resetting the persistent PSG, looping WAVs, truncating notes or resetting counters.
The candidate rejects before either repeat boundary, so **no candidate renewal
or safe long-play continuation is eligible**. Retain4200, pointer, call-stack,
loop-index and operation guards. After separately supporting both new paths,
future full-loop/state/PSG/A1L and interruption tests must establish any narrowly
scoped continuation implementation. This batch adds none.

## Exact comparison and failures

**13 candidate scenarios:11 complete PASS,2 solo HOLD.** The HOLD solos retain
their successfully completed prefixes; the rejection tick and later ticks are
not counted as matched. Across those windows:

- **12148 ticks,59770 ordered PSG bytes**,0 unexplained state/emission differences.
- Each tick compares336 channel bytes,12 relevant globals, shared IY, DE11,
  priority/mailboxes, active/suppressed flags, logical PSG registers/data latch,
  and ordered writes. All projected control-transfer targets/ticks/slots match.
- **8928780 exact accepted-A1L samples**, PAL3546893Hz/44100Hz mono/735 per tick;
  0 differing samples and0 native-state differing ticks across all26 exposed
  native fields. Continuous original-Z80 writes and candidate decoding use
  separate fresh persistent chips of the same pinned accepted A1L.
- All13 windows are identical with735 versus100+635 partitions and replay in
  fresh processes using only private SCSP, host schedule and A1L; three access
  guard probes per process reject ROM/oracle imports/reads.
- **10/10 negative controls detected:** unknownE2, missing4634, F7 index4,
  constructor/execution4201, forged executable-region SCSP, checksum corruption,
  truncation, and wrong pitch data for each song.
- **144 public tests PASS:136 inherited+8 C7-1 evidence contracts.** The two
  full-song guards remain failures to qualify, not adjusted passes. No broad
  historical gameplay gate or GameMaker build was performed.

Exact same-A1L PCM identity does not claim new MAME/sample equality, hardware
cycle timing, analogue output or human listening acceptance. See
[emission](../data/m5-c7-1/emission.json), [PCM](../data/m5-c7-1/pcm.json),
[isolation](../data/m5-c7-1/isolation.json) and [verdict](../data/m5-c7-1/verdict.json).

## SCSP provenance and Designer handoff

Private diagnostic bank: SCSPv1,12084B, horizon4200, SHA256
`a35cc1ccfe92fc6764643b4c7bcb722aa2f90e5b4b6e050c1c98111677919013`.
It retains every C6 header/data byte; C6 standalone bank remains unchanged
(`677e65cc6038bb193e9813b5890b2127dfa7d5b0b71f0553867995659d2ba5a6`).
Candidate-demand extraction never reads oracle captures. Every saved segment
is checked byte-for-byte through its hash against the authenticated source;
packing/reloading retains existing region and length/hash guards.
**This partial bank is a diagnostic artefact, not a soundtrack integration bank.**

| ID | Header SHA256 | Prefix record SHA256 | Solo-demand source bytes |
|---|---|---|---:|
|83|307b8461133deabd7649dceeb62547d785440e2f748bb9e5558731dd502b5272|ddfd5d80e61646f78d055e3988236bf7314aca0558c07ee4646c474a9628c107|1156|
|92|30a4d25c5450cb3126e22d170b27fd8e17ef315b06716eb052a6cf5b8896920f|11f5820a1685cfaefc298352f0b35de56a65fee68a7bfcd322160e79b396e03b|1451|

Record hashes cover canonical JSON `{header: original metadata, data: sorted
[address,value] pairs demanded by the solo prefix}`. They do not authenticate
unvisited song tails. Detailed records remain private. The bank includes
scenario-demand bytes and the prior C6 records; source-byte counts above describe
per-ID solo demand, not additive unique-bank increments.

**Designer: neither83 nor92 is eligible for complete music integration, F2
playable marking, horizon renewal or full-song status promotion.** Eligible
knowledge for a future separately scoped research gate is the source-backed
loop certificate, rejection cause and reproducible tests. Preserve current39/70
C6 scoped verified count; do not promote short interactions to two new verified
programmes. No GameMaker changes, other new requests, main merge or wider
integration is authorised. STOP after Manager review.

## Reproduction

Use Python3.13 with installed `z80`/NumPy and the existing private pinned A1L.
Python3.12 on this machine lacks NumPy; no dependency installation was performed.
From this isolated checkout, run in this order (ROM path is private):

```text
python tools/m5c71/research.py original PRIVATE_ROM
python tools/m5c71/boundaries.py PRIVATE_ROM
python tools/m5c71/research.py candidate PRIVATE_ROM
python tools/m5c71/research.py pcm
python tools/m5c71/isolation.py
python tools/m5c71/evidence.py
python -m unittest discover -s tests -p "test_m5a2*.py"
python -m unittest discover -s tests -p test_m5c71.py
```

Two expected solo rejections are reported without disabling guards. Unexpected
state/emission, native/PCM or changed rejection-boundary failures raise. Source
receipts use UTF8/LF-normalised hashes. Read-only preservation is checked by
the Git diff against C6 and unchanged private-bank hash. ROM, private evidence,
SCSP, WAV and DLL must never be staged or pushed.
