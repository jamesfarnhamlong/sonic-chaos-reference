# M5-C7-1R83 — exact Gigalopolis pitch-data contract

**27 October 2026: $83 GO within the authenticated research scopes below.**
The complete candidate now passes the former tick2784 rejection and the full
3072-tick recurrence. Uninterrupted solo continuation passes13000 ticks with a
pinned-bank, exact-state renewal capability. **Long gameplay playback after SFX,
retrigger or other host actions remains outside that renewal certificate.**
No GameMaker integration or F2 playable marking is approved by this research.

Branch `research/m5-c7-1r83-pitch-region` starts at accepted C7-1
`7496725dd1a1cc1dda339e1334931b7a5a495198`. Canonical AGENTS/MEMORY/ROADMAP authority
is `main@759cbd8a8077b75a8d5609de63281fc9aa2ced63`; B0 audit authority is
`management/m5-b0-manager7-audit@3d31a7c6a0f26bdaa22901f74db01fdb78aaa8df`.
The Manager's explicit one-ID continuation supplies the new work authority.
Canonical management documents, $92 support, GameMaker/A4B and A1L are untouched.

## Original access and minimum source region

The fresh, independently hash-authenticated Europe v1.2 ROM is
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
Original-only probes at4415,4422,4424,4426 and4382 reconfirm the eight-bit
note-plus-transpose wrap, the low and high **actual CPU read addresses**, returned
word and the subsequent channel frequency store. At2784, music tone1 with
transpose247/-9 reaches index255. Original address arithmetic is
`4436 + 2*255 = 4634`; the next byte is read at4635. No index clamp, guessed pitch
or musical correction is applied. Detailed before/after channel, DE/IY, source
bytes and frequency observations remain private.

The minimum additional region is **exactly two bytes at CPU4634..4635**, ROM
offset8634..8635 under the authenticated sound-bank mapping. They occupy driver
executable addresses but are consumed here strictly as pitch **data**. The
candidate neither imports nor executes surrounding Z80 instructions.

| Receipt | SHA256 |
|---|---|
| Exact two-byte region | adcafa4fcf2eff3e3fe49e504aa73303b8b0ea5c89162703717a90cfaf0f1b2e |
| Original83 header | 307b8461133deabd7649dceeb62547d785440e2f748bb9e5558731dd502b5272 |
| Canonical83 header metadata | 882ed37dc8bce866f990a14017d1385d2304805c39deaed287a7b2200bd28ddb |
| Complete83 solo-demand record | 0582aa789fb17feb3be191487daa29907df12f297b50448027485f1a775a002b |
| New private SCSP bank | 3869da8a8121a0408728b022b41dc05c9795f094fe2e9972391142a521f2584f |

The per-song record hashes canonical JSON `{header, data}`, where data contains
sorted `[address,value]` pairs actually demanded by the full4200-tick solo:
**1467 source bytes**, including the authenticated pair. This covers the first
complete original recurrence, rather than C7-1's1156-byte rejected solo prefix.
Full records and every source byte stay private. Each extracted segment is
checked against its exact authenticated ROM range before packing/reloading.

## Narrow architecture extension

The existing SCSPv1 wire format, magic, compression, size bound, checksums,
source metadata and header fields are unchanged. The new bank is11006B, versus
C6's10234B. It contains exactly the previous39 programmes plus83; no92 record
or other new request is added. Every old header/data byte is retained.

[contract.py](../tools/m5c71r83/contract.py) wraps the unchanged legacy loader:

1. Bound and verify the compressed container before inspecting records.
2. Recognise only an exact4634/length2 segment, with its pinned source hash and
   the exact authenticated83 header metadata. Wrong bytes still fail even if
   an attacker recomputes the segment and container hashes.
3. Remove that one record only for delegation to the unchanged complete legacy
   schema/region/pointer validator; return the authenticated pair afterward.
   Ordering, overlap, truncated records, other executable regions, invalid
   headers/pointers, source/version and the4200 horizon continue to fail.

The associated decoder subclass gates the pair to the inherited ordinary
**83 music-tone1 note-table word lookup**, with original transpose and ownership.
Direct byte/word access, command/call/branch readers, other channels/owners,
raw readers, modulation and envelope readers cannot use this permission.
Accepted note arithmetic, commands, envelopes, modulation, scheduling, priority
and PSG semantics are inherited unchanged. No executable-region range is opened.
The old loader intentionally continues to reject the new bank; using the paired
new loader/decoder is mandatory. Old banks load identically through either loader.

No claim is made that self-reported source metadata alone authenticates arbitrary
old SCSP payloads. The additional pair/header are source-pinned, extraction checks
all saved segments against the ROM, and the renewal capability pins the complete
tested bank. Corrupted ordinary pitch data is also caught by the original
differential even after its internal checksums are rebuilt.

## Independent original and complete candidate verification

All seven fresh original scenarios are frozen before candidate extraction or
comparison. The original phase executes only the unmodified Z80 driver; it does
not call a candidate decoder. Runtime playback consumes only the private bank,
external host schedule and accepted A1L. Captured original writes/states/audio
are comparison inputs only.

Six scenarios each run4200 ticks: solo; boundary-adjacent ring/spring/fixed-noise/
tone2/multislot steals; priority rejection; retriggers; fade/reset/restart; and
death→stage-card→fresh83. Their schedules and all results are committed as safe
methods/numerical evidence. The seventh is a13000-tick uninterrupted83 solo.
Context requests are already accepted C6 controls, not additional new music work.
No further unsupported original operation or source region appeared.

**Seven complete scenarios PASS:38200 ticks,161402 ordered PSG bytes, zero
state/emission/transfer differences.** Every tick compares all336 channel bytes,
12 relevant globals, shared IY, DE11, priority/mailboxes, active/suppressed flags,
logical PSG registers/data latch and every port write in order. Control-transfer
tick/slot/target sequences match, including across coverage renewals.

**28077000 continuous accepted-A1L samples match exactly**, with zero differing
samples and zero before/after native-state mismatching ticks. All26 exposed
native fields are compared both immediately after the writes and after rendering
each tick. All seven cases are identical for735 versus100+635 partitions and
replay identically in fresh processes with ROM/oracle imports and capture reads
blocked; three guard probes per process verify that isolation.

A1L remains pinned to
`47e15c47e255900b819847e0ddefd7e3f0751dcc8f75dff3a1690f7e76adcf65`,
PAL3546893Hz,44100Hz mono,735 samples per unchanged60Hz sound tick.
No chip is reset at a loop or request boundary beyond actual original reset
writes. These exact same-A1L comparisons are not a new hardware, analogue,
MAME-waveform or human listening claim.

## $83-specific continuation and its limits

Fresh original full400-byte RAM/PSG/IY state repeats at **522→3594, period3072**.
The full candidate relevant state and the complete subsequent period match,
including ordered writes and transfers. Original physical chip phase is never
used as a loop-cut assumption.

The ordinary new decoder still rejects tick4201. Only the separately selected
[renewal.py](../tools/m5c71r83/renewal.py) can renew coverage, under all of these
conditions:

- It was constructed with the exact tested bank (canonical-bank SHA256
  `0f7b8a17250efdf301143eb20f1ed8ffba96ea7366213a912adb9a8b586d1bdc`).
- Its only host request was the initial83, with no later request or fade.
- At coverage tick3594, all four music owners are83 and the full relevant driver,
  channel, global, logical PSG and latch signature is exactly
  `b330f0e3c6dbea3cd0835ca6048791c2796691ec2560cd61792ddb97c1516871`.

Then, and only then, the **coverage bookkeeping** maps3594 back to522. Original
driver state, phase, native chip, tempo and schedule are neither copied nor
reset. Absolute trace timestamps remain continuous. Diagnostic transfer logging
is capped at64 entries; the long proof exercises this bound and compares an
external observer's complete transfer trace. Renewal history is a counter and
last-tick value, not an unbounded runtime list.

Renewals occur at absolute3594,6666,9738,12810 during the13000-tick proof.
The full candidate has passed, so this is stronger than an original-only loop
certificate. Exact-state recurrence with the pinned programme supports further
uninterrupted solo iterations by deterministic induction;13000 ticks were
measured, not infinite execution.

**Any subsequent request or fade revokes further renewal**, including ordinary
SFX or a fresh83. Playback can use only the remainder of its current certified
4200-tick window. A ring before the first renewal therefore still rejects4201;
a ring at4000 after one valid renewal rejects7273. A wrong state signature
grants no new coverage. This deliberately conservative contract does not certify
general live-game SFX, retrigger, interruption or restart continuation. That
remains HOLD pending a separately scoped state/ownership lifecycle proof.

## Negative tests and preservation

**30/30 negative controls detected**, with no unexplained failure. They cover
invalid/unaligned pointers, direct/command/wrong-reader/wrong-owner pair access,
adjacent and arbitrary forged executable regions, extended/truncated records,
wrong source bytes/hashes and forged83 headers, corrupt/truncated containers,
unsupportedE2 and unchanged F7 index4 bounds, constructor/container/execution
horizon violations, wrong renewal bank/state and host actions before/after a
valid renewal. Ordinary pitch corruption is detected against the independent
original writes. [negatives.json](../data/m5-c7-1r83/negatives.json) gives each case.

**154 public tests PASS:136 inherited+8 C7-1+10 R83 contracts.** In addition,
all **158 accepted C6 schedules /42075 ticks** replay with the new bounded
subclass exactly against their frozen accepted state/write captures. Those are
preservation comparisons, not newly executed original scenarios or new-ID proof.
The old SCSP bank is byte-identical and loads identically; all accepted source,
test and evidence files remain unchanged in Git. $92 F7 handling remains HOLD
and no broader loop index is accepted.

A4B is still clean at `afdd6a1e62e5e61234159266a05bcddab825faf9`; A1L's pinned
DLL and the C7-1 private archive are unchanged. See numerical
[preservation](../data/m5-c7-1r83/preservation.json),
[verdict/test totals](../data/m5-c7-1r83/verdict.json),
[source receipts](../data/m5-c7-1r83/source-receipts.json) and
[private archive receipt](../data/m5-c7-1r83/package.json).
The archive contains private programme/state/audio evidence and safe source,
excludes ROM/DLL/EXE, and is locally CRC/member-hash verified. It is not published.

## Reproduction and Designer handoff

Use the recorded Python3.13/z80/NumPy environment, authenticated local ROM,
accepted private C6 bank and pinned A1L. In this isolated checkout:

```text
python tools/m5c71r83/proof.py original PRIVATE_ROM
python tools/m5c71r83/proof.py candidate PRIVATE_ROM
python tools/m5c71r83/continuation.py
python tools/m5c71r83/pcm.py
python tools/m5c71r83/evidence.py
python tools/m5c71r83/finalise.py
python tools/m5c71r83/package.py
```

Unexpected operations, regions, state/PSG/PCM differences and negative-control
acceptances raise. Packaging refuses to overwrite an existing private archive.
Original records, SCSP, full captures, audio and libraries must stay private.

**Designer handoff:**83's full4200-tick programme and bounded interaction cases
are now original-authenticated. A future approved port must preserve the paired
loader/reader permission, exact source receipts, inherited operations and guard
behaviour. Opt-in continuation is currently certified only for uninterrupted
solo playback. Do not reuse the old C7-1 partial diagnostic bank, silently renew
coverage during live gameplay, mark92 playable, or infer GameMaker approval.
No GameMaker changes, additional new request, main merge or canonical management
update were made. **STOP after this one-ID task for Manager review.**
