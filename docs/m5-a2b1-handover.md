# M5-A2B1 first finite-music expansion — Manager handover

**GO for a separately authorised remaining short finite-music batch.** All six
named requests passed this batch; no unexplained original-language blocker
remains in their tested scope. The other six received original-only preflight
and remain unverified as decoder/runtime content. Work stops here.

25 October2026. Topic `research/m5-a2b1-finite-music` from accepted A2
`47758830da9bb83ebb19bbd02950757838202763`; management read
`caa149cd9d2031113639884058ab98b058112e70`. Accepted M4 POC
`11bff34356d5f5d979218896dc95fdc4bb265eae`, A1P host and A1L synthesizer were
read-only. No GameMaker compile, integration, Sound Test, long-track production,
main merge, binary distribution or second implementation batch was performed.

## Result and implementation

The [preflight](m5-a2b1-preflight.md) covers all twelve remaining short finite
requests before expansion. The reusable [B1 decoder](../tools/m5a2b1/decoder.py)
subclasses accepted A2 and adds only E1 fine-frequency offset, justified by
original CPU `$487E..$4881` and signed addition at `$4504..$450D`. It has no
song-ID tests, captured note timing or prerecorded event inputs. All other
unsupported instructions retain A2's errors. The only modification to an
existing file is an optional `decoder_class` argument in A2's runtime rendering
function; its default remains the accepted decoder. SCSP v1 and A1L arithmetic
are unchanged.

| ID | Original catalogue name | Original/candidate inactive tick | Post ticks | Result |
|---|---|---:|---:|---|
|84 | Invincibility music |1088 |32 | exact PASS |
|85 | Rocket Shoes music |432 |32 | exact PASS |
|86 | Special Stage success results music |300 |32 | exact PASS |
|87 | Game over music |408 |32 | exact PASS |
|89 | Ordinary act-clear music |242 |32 | exact PASS |
|8A | Special Stage entry / success transition music |179 |32 | exact PASS; authentic held DC preserved |

All six complete original streams were independently decoded, packed, reloaded
and compared through32 further driver ticks. No slot reactivates and no new
port byte is emitted in those windows. Inactive state is not presumed to mean
zero physical output; see8A below.

**33 scenarios,16,137 ticks,79,380 ordered PSG bytes: exact PASS.** This includes
13 new cases/7507 ticks/35625 bytes plus all20 accepted A2 regression scenarios.
Every tick compares byte order, physical registers/latch, savedDE11, all336
channel bytes,12 global bytes and now shared IY directly. Original transfer
tick/target/slot order also matches. Candidate execution finishes before creating
the separate Z80 oracle per case. Every legacy candidate row also matches its
frozen private A2 expected row; no expected timeline drives the decoder.

Seven new representative controls cover THZ→84 through completion without
automatic THZ restoration;84 interrupted byAC/BC/B6 with blockedA3;85 with
B6/A0/A3/BC for tone1/tone2/noise suppression and recovery;84→85→85 restart→87;
84 fade/reset then86;85 numericF8 then89; and simultaneous B6/A3/AC mailboxes
where lower priorities are rejected. Cases are bounded and selected by actual
slot/priority behavior, not a Cartesian request matrix.

## Audio measurements

New mix and four diagnostic-voice comparisons use continuous unchanged A1L
against fresh original-driver/pinned-MAME output. PAL3,546,893Hz,44,100Hz mono,
735 samples per60Hz tick, existing tick-boundary emission cadence. No original
hardware/cycle-timed identity or human listening is claimed.

| Solo | Mix max LSB | Mix RMS LSB | Largest tone-voice max LSB | Noise-voice max LSB | PCM frames incl post window |
|---|---:|---:|---:|---:|---:|
|84 |4 |0.214410 |2 |2 |823200 |
|85 |4 |0.232876 |3 |2 |341040 |
|86 |3 |0.242146 |2 |2 |244020 |
|87 |3 |0.161739 |2 |2 |323400 |
|89 |4 |0.208084 |3 |2 |201390 |
|8A |3 |0.196546 |3 |0 |155085 |

All13 new cases have mix max3..4LSB and voice max0..3LSB, with zero PSG
register/counter/LFSR diagnostic mismatches. Every driver envelope/attenuation
state matches exactly; each voice's block-RMS envelope difference is reported
separately in [pcm.json](../data/m5-a2b1/pcm.json). No new case exceeds the
previous observed5LSB range, and no threshold or synthesizer arithmetic changed.
This measures the new content; it does not turn5LSB into an advance universal
permission. All33 candidate renders are identical for735 versus100+635 block
partitioning. All20 legacy PCM outputs are byte-identical to accepted A2 audio.

Each of the six packed finite requests was also played in a separate fresh
process with original-driver imports and ROM/VGM/dry-bank access forbidden. Its
WAV is byte-identical to the independently decoded candidate. That runtime
accepts private SCSP, an external host schedule and the existing A1L backend;
it does not open a ROM, emulator or captured combined event file.

## Original8A physical-output qualification

8A's tone2 and noise streams terminate at tick1. Tone2 F2 emits DF, selecting
the tone2 attenuation latch; music-noise F2 then sends savedDE11=0 at original
OUT `$47F3`. This data byte sets tone2 attenuation to0 before FF. The tone2
period is0. No later write corrects that physical register in the solo window.
All readers are inactive by179, but tone2 remains enabled with zero period.

The32 post-completion ticks produce23,520 samples of constant signed16 **8192**
in both original MAME and A1L, standard deviation0: held DC, no periodic AC.
This is consistent with the accepted Sega zero-period behavior, not evidence
of a spurious decoder note/retrigger. Five other new solos end with attenuation15
on all channels. Do not force8A off, truncate the chip state, insert padding or
claim the final32 ticks contain zero-valued PCM. Host DC filtering/output policy
is a separate future integration question. A focused private source-site
diagnostic and complete candidate/original rows preserve the evidence.

## Private data, workload and coverage

Expanded SCSP v1: **6065 bytes**, +1780 from4285;42 validated data segments,
3716 original data bytes (+1247),270 header bytes,70 priority entries and15
unique program headers. Raw values total4056 bytes; hash/address/length metadata
explains why the packed container exceeds raw ROM values. Contiguous-record
JSON18606 bytes. Data SHA-256:
`0668b6d432b6631513eacd56674279f02eb89ccccdb6e4fee74d717c6dfab486`.
The original nine headers and all2469 old data bytes remain unchanged; their
accepted standalone4285-byte SCSP is untouched and still loads. Horizon remains
4200, with no format version bump or relaxed pointer/size/stack/loop guards.
Only the six authorised additions are present in the bank.

Measured decoder benchmark8523 finite ticks: median4.3µs, p9918.1µs, max75.1µs
in this run. Whole proof worst work remains20 stream operations and20 emitted
bytes per tick. Comparative Python allocation: old bank+subclass197827 current/
218867 peak bytes; expanded314299 current/355540 peak, +116472 current/+136673
peak. Scope includes sparse bank, channel state and bounded diagnostic flow
log; excludes Python base process and PCM arrays. These are Python prototype
figures, not native/GameMaker decoder measurements. [facts.json](../data/m5-a2b1/facts.json)
retains raw figures and termination/negative-control details.

All70 catalogue rows are updated in [coverage.json](../data/m5-a2b1/coverage.json):
**15 fully decoded within tested scope;0 partial;6 format-understood/preflight-only;
42 unsupported/unknown;7 empty/control.** The deferred8E/94/96/97/98/9A have no
candidate implementation or audio promotion. The original68 header records and
61 bounded solo-emission fingerprints are distinct metadata counts, not a
claim of61 independently audible outputs. Names and existing equal-output
relationships are preserved.

## Checks, preservation and reproduction

31 public tests PASS:19 inherited A2 plus12 B1 controls. New controls include
truncated E1, signed fine-offset arithmetic, rejection of other unverified
instructions, exact new finite/end-state/PCM facts, source receipt checking,
six isolated replays and catalogue bounds. Existing corrupt SCSP/pointer/loop/
horizon tests remain green. The old A2 reader rejects original84's E1 at tick1;
mutated pitch data fails emission at1; removing terminal writes fails at939.
No failed comparison became a tolerance, silent fill or adjusted timing gate.

```text
python tools/m5a2b1/preflight.py PRIVATE_ROM
python tools/m5a2b1/proof.py PRIVATE_ROM
python tools/m5a2b1/pcm.py
python tools/m5a2b1/evidence.py
python tools/m5a2b1/isolation.py
python -m unittest discover -s tests -p test_m5a2*.py
python tools/m5a2b1/package.py
```

Use the existing local NumPy dependency directory for Python3.12 on PYTHONPATH and the
unchanged pinned renderer/A1L DLL. Original-only preflight and fresh oracle need
the authenticated ROM; playback and SCSP validation do not. Original-derived
records, detailed traces and WAV/VGM stay outside Research Git under workspace
`private-research/m5-a2b1`; the new private archive is separate under `releases`.
Public Git contains only source, docs, aggregate numerical evidence and hash
receipts. Earlier seven proof archives,47 M4 payloads and A1P source/native
evidence are checked read-only. The archive contains no ROM or DLL.

**STOP for Manager review.** Recommend remaining six finite requests only after
fresh authorisation; do not extend repeating music, SFX classes, full library,
Sound Test or real-game runtime from this result alone.
