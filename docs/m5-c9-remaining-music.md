# M5-C9 — remaining eight music programmes

28 October 2026. **Eight new scoped Research GO verdicts; no remaining music
HOLD in this assigned batch. Research catalogue63/63 in documented contexts.
Native F2 remains39/63 pending Designer/native/Chief acceptance.**

Authority: management `main@0ee614a7e040bdcc566f3816fa419b2c41343dea`,
`CURRENT_M5.md`, and Manager7's explicit C9 assignment. This isolated topic is a
direct child of accepted Research C7 batch
`96ae9ea877abbdb7419647aff72807c456ffcc42`. No original55 qualification was
re-proved, no GameMaker/PSG/queue/clock change, no management edit or main merge.
R83 retains its earlier83 solo certificate without any extension here.

## Independent results

| ID | Verdict | Original first/repeat/period | Exact solo verification through |
|---|---|---|---:|
|91 Sleeping Egg|GO scoped|395 /32651 /32256|64907 ticks|
|93 Aqua Planet|GO scoped|2040 /5040 /3000|8040 ticks|
|95 Electric Egg1/2|GO scoped|1224 /5256 /4032|9288 ticks|
|8B EEZ first encounter entry|GO scoped|805 /4261 /3456|7717 ticks|
|90 opening / EEZ3|GO scoped|807 /20575 /19768|40343 ticks|
|82 character selection|GO scoped|130 /7042 /6912|13954 ticks|
|8C ordinary boss|GO scoped|497 /81137 /80640|161777 ticks|
|8D full ending|GO scoped, finite|All music slots inactive at10432; no musical loop|11968 ticks, including1536 idle ticks|

Each looping ID has independently identical **all400 driver RAM bytes,
shared IY, logical PSG/data latch**, every ordered PSG write and transfer edge
across two full original periods. This extends the insufficient C7 coverage for
91/8C and supplies complete original oracles for the repaired reader/lifecycle
contracts. Previously established periods from C6/C7 were used as reference
checks; prior55 qualifications were not replayed.

No remaining technical blocker prevents these scoped Research verdicts. The
remaining integration limits are explicit: fresh solo playback with the exact
bank, listed checkpoint/reader contracts, and the controlled90 contexts below.
Long playback after SFX, retrigger, another request or fade is **not** certified.
This is not natural gameplay routing, every interaction phase, full scene timing,
hardware/analogue parity or M5 completion.

## Group A: independently authenticated pitch DATA

Original ROM: Europe v1.2, SHA256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.

Original-only hooks4415/4422/4424/4426 record the incoming note, channel state,
transpose, index, actual low/high CPU reader addresses and returned word.
Every out-of-region note read independently satisfies
`index=((note&127)+transpose)&255`, `address=4436+2*index`, high read=address+1,
and actual returned word equals the source pair. Detailed notes/source bytes
remain private. No pitch clamp or replacement is applied.

| ID | Original owner / reader | Transpose byte | Exact note indices / pair addresses | Reached reads in complete solo |
|---|---|---:|---|---:|
|91|91 music tone1, slot1|246|253→4630;255→4634|156|
|93|93 music tone1, slot1|248|255→4634|30|
|95|95 music tone1, slot1|245|253→4630;255→4634|4|
|8B|8B music tone2, slot2|243|254→4632|1|
|90|90 music tone1, slot1|243|255→4634|54|

Each pair is exactly two bytes. The distinct source union is six bytes at
4630..4635, but **no six-byte global permission exists**. The loader requires
exact per-ID programme metadata and independently pinned pair hashes. Decoder
access additionally requires the specified owner, reader slot and transpose,
ordinary note mode and inherited note arithmetic. Direct bytes/words, command,
call/branch, raw, modulation, envelope and wrong-owner reads cannot borrow these
permissions. R83's83 permission is not imported or widened.

`reader-policy.json` contains independent per-ID programme/header hashes,
reader scopes and pair hashes. `contract.py` validates bounded SCSP compression,
lengths/checksums and sorted nonoverlapping records before recognising only
the exact permitted pair segments. It removes those records temporarily for
the unchanged complete legacy schema/region/pointer validation, then restores
authenticated pairs. Wrong bytes fail even with rebuilt container/segment hashes.
All eight banks retain the original C6 headers and data unchanged.

## Group B and long Group A lifecycles: checkpoint capabilities

The legacy interpreter and SCSP horizon remain4200. No constructor can enlarge
that ordinary window. `runtime.py` composes request-specific capabilities over
the unchanged interpreter:

1. Pin the complete bank hash and exact programme identity.
2. Admit only the first, uninterrupted solo request. Further requests or fades
   permanently revoke extension; once absolute time reaches4200 they fail closed,
   even if an earlier window was already extended.
3. Before each next4200-tick window, compare the complete candidate driver/PSG
   fingerprint with the independently matched original checkpoint. A missing
   checkpoint, state change or modified bank denies extension.
4. At an original full-state recurrence, require its exact fingerprint and
   return only the **proof position** to the original first recurrence tick.
   Driver/channel state and the persistent PSG are never rewound, reset or copied.
5. Keep absolute tick/transfer diagnostics and at most64 transfer-log records.

This provides enough verified prefix windows to reach82's7042,91's32651,
90's20575 and8C's81137 repeat boundaries. One runtime renewal and the entire
following period were compared against the original for each looping ID.
The certificate permits deterministic recurrence under that same solo schedule;
it does not claim physical oscillator/LFSR phase recurrence or infinitely many
measured PCM samples. Current measured bounds are the table above.

**Finite8D:** no recurrence is used. At10432 the runtime requires the exact
completion fingerprint, every channel inactive and all four attenuations15,
then exposes `completed=True`. The captured1536 subsequent idle ticks remain
exact. Execution beyond11968 is explicitly rejected; a host should recognise
finite completion rather than invent a repeat or reset the persistent chip.
No silent fallback or automatic restart is supplied.

Diagnostic demand extraction traverses windows only in the research harness.
It is not the delivered runtime or its oracle. Original captures are frozen
first; diagnostic comparisons establish candidate checkpoints and source demand;
the final pinned/gated runtime is then separately compared for every tick.
Only this final runtime's state/PSG/PCM/isolation receipts qualify a GO.

##90 opening and EEZ3 are separate controlled contexts

The established C6/M5 source crosswalk and U5-A opening evidence are reused.
Fresh original execution of writer189B verifies opening zone7/act0 and EEZ3
zone5/act2 independently. Both select90 from their own18BA table entries and
write DE04 plus pending D4A4 when D4A3=0; D4A3=1/255 suppress both writes.
The writer span is source-hashed; no original instruction bytes are published.

- Opening: writer-derived90, inherited controlled fade at745, title99 request
  at800, verified through1100. This is a bounded lifecycle fixture, not a claim
  that the entire original cinematic naturally runs on that exact schedule.
- EEZ3: writer-derived90, controlled same-ID retrigger at2472 immediately after
  the former pitch failure, verified through3000. The full uninterrupted90
  composition has its separate40343-tick proof; no short opening WAV is used.

These cases explicitly test the shared original composition's two request
sources without equating source playback with complete opening/EEZ3 gameplay
integration. After replacement/fade/retrigger, further continuation stays denied.

## Verification and disclosure

Ten final gated scenarios: **322094 exact original/candidate ticks,
236739090 exact accepted-A1L PCM samples**. Zero driver-state, ordered PSG,
transfer-edge, PCM or before/after26-field native-state differences. Every tick
also matches735 versus100+635 render partitioning. PAL3546893Hz,44100Hz and
735 samples/tick remain unchanged.

Each scenario replays in a fresh process using only its private SCSP, explicit
host schedule, public capability policies and accepted A1L. Three active access
guards reject original-ROM reads, oracle reads and original CPU imports. PCM,
native-state and emission/state hashes match the direct verification process.
Continuous original/candidate chips are separately created once per scenario;
no chip resets occur at a coverage boundary or musical loop.

**163 negative controls detected**, including per-ID container corruption,
metadata forgery, unchanged4201 limits, modified continuation bank, subsequent
same/other requests, fades, late requests, checkpoint and recurrence damage;
per-reader wrong owner/slot/transpose/raw/command/address, direct byte/word
access, missing pairs and source changes with rebuilt checksums; and finite8D
completion corruption/proof exhaustion. **167 public tests PASS**:
136 inherited A2 +18 C7/R83 +6 C7 batch +7 C9. These are not new proof runs for
the prior55 sound programmes.

Private root: `<PRIVATE_RESEARCH_ROOT>/m5-c9`, outside this repository. Private
files include eight per-ID SCSP banks, complete source records, note/channel
records, compressed per-tick original captures, host schedules and isolated
receipts. Public JSON contains counts, addresses, hashes, reader scopes,
capability checkpoints and independent verdicts only. No original programme
bytes, reconstructed byte arrays, raw per-tick captures, ROM, audio or binaries
belong in the published tree. PCM is continuously compared and hashed in memory;
no WAV or external M4 asset supplies playback.

## Designer intake and reproduction

`data/m5-c9/verdict.json` is the per-ID GO/scope ledger; `diagnostic.json` records
header/source-segment and private-bank hashes; `capabilities.json` pins each
bank and its lifecycle; `*-verified.json` records the final runtime receipts.
Banks `<ID>.scsp` are separate and retain the frozen C6 records. Repacking or
combining with C8 changes bank hashes and requires fresh capability/native
verification. No63/63 native F2 marking is justified by these Research receipts.

Use installed Python3.13 with z80/NumPy and the existing pinned A1L DLL. From
this checkout, PRIVATE_ROM means the authenticated private original ROM:

```text
python tools/m5c9/original.py PRIVATE_ROM
python tools/m5c9/proof.py PRIVATE_ROM
python tools/m5c9/verify.py
python tools/m5c9/contexts.py original PRIVATE_ROM
python tools/m5c9/contexts.py candidate
python tools/m5c9/evidence.py
python -m unittest discover -s tests -p "test_m5a2*.py"
python -m unittest discover -s tests -p "test_m5c71*.py"
python -m unittest discover -s tests -p test_m5c7batch.py
python -m unittest discover -s tests -p test_m5c9.py
```

Manager review is next. No GameMaker changes, Chief package, main merge or
broader audio/gameplay certification is included.

Publication inspection: all35 added files (26 generated numeric JSON reports,
seven Python tools, one Python test and this document) were inspected. JSON
arrays are limited to reader-scope metadata, aggregate F7 scopes, small writer
case tables and active/attenuation summaries; no raw capture arrays or source
payloads are present. Python byte literals are newline delimiters and synthetic
invalid-container test input. No ROM, SCSP, game audio, binary, reconstructed
source-byte array or absolute private workstation path is included. Original
payloads and the detailed publication inventory receipt remain outside Git.
