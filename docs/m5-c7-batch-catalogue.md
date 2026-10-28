# M5 C7 catalogue batch — 28 October 2026

**15 new IDs GO in scoped Research; eight music IDs HOLD. Native F2 remains39/63.**

Management authority: `main@89b32f3dfabdfc195a1a21a295d639c0cf658e77`,
`CURRENT_M5.md`, and Manager7's explicit batch assignment. This isolated topic
starts at completed R83 `9961b05eb9962bdeb43983028aa4b9ca4b802cec` to reuse
C6/C7/R83 tooling, rather than treating management main as executable Research.
No management document, accepted decoder, GameMaker project, native PSG,
queue/clock, or previously accepted programme changed. No main promotion.

## Independent per-ID results

| ID | Research verdict | Exact tested scope / blocker |
|---|---|---|
|92 Mecha Green Hill|GO scoped|Six4200-tick scenarios; pinned uninterrupted solo13000; exact F7 index4 alias extension below|
|91 Sleeping Egg|HOLD|First rejection1732, actual original tone1 index255 pitch read4634; original4200 also reaches4630|
|93 Aqua Planet|HOLD|First rejection293, actual original tone1 index255 pitch read4634|
|95 Electric Egg1/2|HOLD|First rejection4068, actual original tone1 index253 pitch read4630; original4200 also reaches4634|
|82 character choice|HOLD|4200 exact prefix; original recurrence130→7042, period6912 cannot renew inside existing4200 window|
|8B EEZ first encounter entry|HOLD|First rejection121, actual original tone2 index254 pitch read4632|
|8C ordinary boss|HOLD|4200 exact prefix; no full400-byte original-state recurrence within bounded24000 search; no eligible continuation certificate|
|8D full ending|HOLD|4200 exact prefix does not complete finite programme; later10432→11968 recurrence has zero PSG writes and is an idle-state recurrence, not a music loop|
|8F Special Stage|GO scoped|Six bounded scenarios; original78→1326 period1248; pinned uninterrupted solo13000|
|90 opening / EEZ3|HOLD|First rejection2471, actual original tone1 index255 pitch read4634; original period19768 also exceeds window; opening/EEZ3 gameplay contexts remain unqualified|
|A8 AB AD AE B2 B3 B5 C0 C1 C3|GO scoped|Ten C6 tone2 cases: each solo, active81 overlay, retrigger, replacement and fade/reset, five600-tick schedules|
|BB BE C4|GO scoped|Three C6 single-F3/noise cases, same five schedules independently verified per ID|

All13 SFX finish their solo programmes and reach attenuation15 on all physical
channels within600 ticks. Original release ticks respectively: A8=46, AB=9,
AD=65, AE=15, B2=58, B3=77, B5=19, C0=29, C1=10, C3=46, BB=65, BE=38, C4=65.
These are individual executions, not assumed safety from a shared C6 label.
No standalone SFX over other songs or arbitrary interaction phase is inferred.

R83 remains DONE in its previous Research scope; it was not re-proved or
integrated here. Including that separate proof, baseline39 plus R83 plus these15
gives55 independently scoped Research programmes, with eight still unresolved.
This arithmetic is **not** a native55/63 claim: all24 formerly missing IDs
remain outside Chief-accepted B2 until Designer's native/Windows gates.

## Exact92 alias and lifecycle

The original handler4849..485F uses channel offset39+index. Index4 is byte43,
also within nominal call-stack storage. This extension does not invent separate
loop storage or clear stale bytes. It preserves the original zero-initialize,
8-bit decrement and branch behaviour in byte43 itself.

`tools/m5c7batch/alias92.py` permits only music tone2, original92 ownership,
exact authenticated programme metadata and header, exact source command87C1
(operand pointer87C2), index4, and stack cursor48. The command's five source
bytes are hash-pinned and remain private. Active call cursors42/44/46, other
owners/slots/commands, index3, forged metadata and changed command bytes fail.
Legacy0..2 F7 support and all other command semantics remain unchanged.

The **existing C7-1 original92 loop certificate is reused**, not re-searched:
511→4159, period3648, original proof through7807. Its four original extended
operations use tone2/cursor48, with byte43 alternating0→1→0. Targeted original
F8/F9 dispatch observation through7807 finds no tone2 call write to42/43.
All256 synthetic stale byte43 values are independently executed through the
actual Z80 handler and compared with candidate: all48 channel bytes and next
stream pointer agree. Synthetic coverage is not natural reachability evidence.

Six4200 scenarios include steals/priority, restart after first alias, death/card
bridge and fade/reset. Complete channel bytes validate reset/restart and
suppression/recovery; no normalisation hides stale or aliased state. Calls can
still use the same RAM according to inherited semantics. A later alias reached
with an active call frame is deliberately denied, even if the original could
execute it; no general F7 permission is claimed.

## Original oracles, continuation, PCM and guards

Original Europe v1.2 ROM SHA256:
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
Original-only captures are frozen and hash-checked before candidate extraction.
The92 solo4200 capture is reused byte-for-byte from C7-1. New13000-tick92 and8F
captures validate continuation; they do not repeat the prior92 loop search.
Fresh targeted original pitch hooks confirm actual reader addresses for HOLDs.
R83's exact-owner4634 permission is never borrowed for another programme.

Across127 scenarios / matched HOLD prefixes:

- **138322 exact ticks,755577 ordered PSG bytes**, zero state/transfer/write differences.
- All336 channel bytes,12 relevant globals, shared IY, priority/mailboxes,
  suppression/release flags, DE11, logical PSG and data latch compared every tick.
- **101666670 exact continuous A1L samples**, PAL3546893Hz,44100Hz,735/tick.
  Zero differing samples or before/after native-state ticks across26 fields.
- Every window matches735 versus100+635 sample partitions and a fresh isolated
  process. Each process actively tests three ROM/oracle import/read guards.
- **24 negative controls detected**: legacy F7 rejection, wrong alias scope,
  forged metadata/source, active call contexts, unchanged4201 constructor/tick
  guards, E2, executable-region pitch reads, malformed SCSP, modified renewal
  bank, subsequent requests/fades and recurrence-state damage.
- Public tests:136 inherited A2 +18 C7/R83 +6 new batch contracts = **160 PASS**.

`continuation-certificates.json` pins each entire bank and candidate full-state
fingerprint.92 renews at4159,7807,11455;8F at1326 then every1248 through12558.
Original keys include all400 driver RAM bytes, shared IY and logical PSG/latch;
each repeated full period's state/write stream matches. Runtime renewal changes
only coverage accounting, retains absolute diagnostic time and bounds transfer
logs at64. It resets no driver, oscillator, counter or LFSR state. Any later
host request or active fade revokes further renewal. No physical PSG phase
recurrence, hardware timing, analogue/MAME identity or human listening is claimed.

Other songs retain the ordinary4200 guard. In particular82/8C/8D are HOLD even
though their bounded prefixes match; this batch adds no extended-horizon
exception. The eight unresolved IDs require separate exact reader contracts or
source-backed lifecycle coverage, not guessed loops or global pointer/4200 changes.

## Designer intake and private receipts

Private root: `<PRIVATE_RESEARCH_ROOT>/m5-c7-batch` (outside the repository).
Public `data/m5-c7-batch/` contains numerical results, hashes and scoped verdicts
only. ROM, complete sparse records/SCSP, per-tick state/PSG captures and WAVs
remain private. The accepted C6 bank is unchanged:
`677e65cc6038bb193e9813b5890b2127dfa7d5b0b71f0553867995659d2ba5a6`.
All group banks retain its original records. Existing39 were not researched again.

Use `source-records.json` for per-ID header, metadata, demanded-source and bank
hashes; `verdict.json` is the permission ledger. The separate private banks are:

- `92.scsp`:92 bounded alias and pinned solo capability.
- `82-8B-8C-8D-8F-90.scsp`: only8F is newly qualified; other new headers are
  diagnostic HOLD records. The8F continuation pins this exact bank.
- `A8-AB-AD-AE-B2-B3-B5-C0-C1-C3-BB-BE-C4.scsp`: all13 new SFX in listed contexts.
- `91-93-95.scsp`: diagnostic prefixes only, no new playable programme.

Do not enable every header merely because it occurs in a diagnostic bank.
Combining/repacking banks changes renewal pins and needs fresh native evidence.
Designer can ingest these15 in a combined F2 candidate alongside separate R83,
after exact GML/native-state/PSG/PCM verification; no one-track Chief package is
requested. No gameplay-zone/SFX interaction beyond these schedules is approved.

## Reproduction

Use installed Python3.13 with z80/NumPy and the unchanged private accepted A1L
DLL. From this topic checkout, `PRIVATE_ROM` means the authenticated local ROM:

```text
python tools/m5c7batch/proof.py original PRIVATE_ROM 91 93 95
python tools/m5c7batch/proof.py candidate PRIVATE_ROM 91 93 95
python tools/m5c7batch/proof.py original PRIVATE_ROM 82 8B 8C 8D 8F 90
python tools/m5c7batch/proof.py candidate PRIVATE_ROM 82 8B 8C 8D 8F 90
python tools/m5c7batch/proof.py original PRIVATE_ROM A8 AB AD AE B2 B3 B5 C0 C1 C3 BB BE C4
python tools/m5c7batch/proof.py candidate PRIVATE_ROM A8 AB AD AE B2 B3 B5 C0 C1 C3 BB BE C4
python tools/m5c7batch/proof.py original PRIVATE_ROM 92
python tools/m5c7batch/proof.py candidate PRIVATE_ROM 92
python tools/m5c7batch/source.py PRIVATE_ROM
python tools/m5c7batch/continuation.py original PRIVATE_ROM
python tools/m5c7batch/continuation.py candidate
python tools/m5c7batch/pcm.py
python tools/m5c7batch/evidence.py
python -m unittest discover -s tests -p "test_m5a2*.py"
python -m unittest discover -s tests -p "test_m5c71*.py"
python -m unittest discover -s tests -p test_m5c7batch.py
```

The92 original phase requires preserved C7-1 private captures; it imports rather
than regenerates its completed solo proof. Programme payloads are extracted by
candidate demand only and every saved segment is checked against the original
ROM before packing/reloading. Unexpected state/PSG differences abort. Documented
decoder/data guards produce independent per-ID HOLDs and preserve matched prefixes.

## Publication inspection — 28 October 2026

Manager7 authorised publication to `jamesfarnhamlong/sonic-chaos-reference`,
topic branch `research/m5-c7-batch-catalogue`. All29 batch files were inspected:
19 generated JSON reports, eight independently written Python tools, one Python
test file and this document. JSON keys, values and arrays contain aggregate
counts, visited-index sets, metadata, sparse admission/renewal event timings,
verdicts and provenance hashes; they contain no original programme-byte arrays,
per-tick channel/PSG/PCM captures or embedded SCSP. Python constants and fixtures
contain research methods, addresses, IDs, synthetic controls and hashes; the
only byte-string literal is a one-byte synthetic checksum-corruption control.
No ROM, game audio, complete SCSP, extracted source payload or binary is included.
The private workstation path above was replaced with a generic placeholder.
Research verdicts and all numerical verification results are unchanged.
