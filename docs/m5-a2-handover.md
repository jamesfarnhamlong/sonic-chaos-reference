# M5-A2 bounded decoder proof — Manager handover

**GO: the decoder architecture is demonstrated for measured catalogue expansion.**
This recommends the next authorised batch; no expansion or GameMaker work has
started. Unknown operations and untested content remain fail-fast boundaries.

24 October2026. Isolated topic `research/m5-a2-driver-decoder`, direct work from
A1L `ad6aa301a7cc37a75f36a3d15c4804bcaa37b02b`; management authority read at
`ec0c979556404d000487dc1f7a44651cddcbf121`. Provenance closure `4980f6d` was not
merged. Accepted private POC `11bff34356d5f5d979218896dc95fdc4bb265eae` remains
read-only and clean; M4 PCM and prior proof packages were preserved.

## Deliverables and result

| Deliverable | Evidence |
|---|---|
| A: original language, channel layout, evidence and unknowns | [language specification](m5-a2-driver-language.md) |
| B: reusable byte-stream reader and scheduler | [decoder](../tools/m5a2/decoder.py), [ROM-free executable](../tools/m5a2/runtime.py) |
| C: fresh original-driver validation | [emission results](../data/m5-a2/emission.json), [loop/recovery/failure facts](../data/m5-a2/facts.json) |
| D: persistent A1L synthesis | [PCM comparisons](../data/m5-a2/pcm.json) |
| E: SCSP versioned private records | [format implementation](../tools/m5a2/bank.py), private package receipt |
| F: complete70-request matrix and proposed batches | [coverage.json](../data/m5-a2/coverage.json) |
| G: decision and limits | this handover |

**20 scenarios,8,630 ticks,43,755 ordered bytes: exact PASS.** Every tick compares
ordered writes, all physical registers, data latch, saved DE11, active/suppressed/
inhibited/fixed flags, priority, all336 channel bytes and12 relevant global bytes.
Executed F6/F7/F8 transfer targets/ticks/slot order also agree with original
breakpoint observations. The gate uses no numeric or timing tolerance. The
oracle is the original sound driver, not a second export of candidate events.

The candidate takes only private original data and external request/fade
schedules. It finishes before original execution is instantiated for each
comparison. Frozen records are loaded without reopening the ROM. The runtime
contains no Z80 execution, executable sound-bank region or prerecorded combined
PSG timeline. The separate original trace and MAME VGM are reference inputs only.

| Target | Scope and result |
|---|---|
|88 | complete finite music, inactive212;240 compared ticks |
|99 | complete title music, inactive1189;1220 compared ticks |
|81 |4200 ticks, real jumps/counted loops; state1093 repeats3781, period2688;419 subsequent ticks match |
|AC/B6 | complete finite solos, multi-slot replacement, music suppression/recovery, solo versus music-context DE11/latch |
|A3/BC | complete finite solos, clock-coupled noise competition; reverse-order priority rejection |
|B8/A0 supporting programs | finite solos, physical hold, fade/recovery and reset controls |
|Shared controls | three simultaneous mailboxes, rejected numeric F8, admitted reset followed by new output, music replacement/restart |

All20 independently decoded continuous PCM runs measured **2..4 signed16 LSB**
maximum difference against pinned original-driver/MAME reference audio. No new
case exceeds the earlier bounded5LSB policy. There are zero compared PSG
register/counter/LFSR failures against the unchanged A0 core diagnostic. A1L PCM
is identical for735 versus100+635 render partitions. This is numerical evidence,
not original hardware sample identity or a human listening acceptance. Clock
3,546,893Hz, output44,100Hz,735 samples per60Hz tick; writes retain the existing
tick boundary rather than individual Z80-cycle timing. Total6,343,050 mono
samples per comparison path; no long90/91/8C render was started.

## Failure controls and discoveries

Public unit controls reject wrong/truncated/corrupt containers, oversized decoded
lengths, invalid record lengths/pointers, wrong source/version, unsupported stream
opcodes, truncated operands, pointer escape, instantaneous infinite loops,
call-stack/loop-index violations, unknown requests, unsupported coverage horizon
and missing termination. They use invented synthetic fixtures, not game payload.
The actual selected-data negative control changes pitch data and fails exact
emission at tick1. Removing terminal release writes fails at tick135. No failing
assertion was replaced by timing slack, silent padding or an adjusted oracle.

Three implementation errors were corrected during exploratory comparisons:
music noise's read path returns without ordinary attenuation; F2 unwinds the
whole channel invocation; and modulation reload uses shared IY, including the
DE06 zero-read quirk. Early private first-failure files remain local historical
diagnostics and are excluded from the final proof package. All current cases
are newly rerun against the final code. None is an original driver defect.

Physical held output remains explicit: B8/BC keeps noise control5/attenuation2
on104 inhibited ticks63..166, terminal off167, stream release168. Finite88 fade
retains eight resumed-noise ticks40..47. B6/A0 tone1 recovers on a genuine next
read at61, after26 suppressed ticks. Rejected BC→A3 and B6→F8 controls preserve
the incumbent state. Music88 replacing81 and later requesting81 is a restart,
not an invented automatic music restoration policy.

## Storage, performance and remaining work

Private SCSP:4,285 bytes,33 validated data records,9 unique program headers.
See the format specification for raw-versus-packed figures and overhead. The
initial Python implementation uses195,131 bytes current/223,481 peak measured
allocation for bank+decoder; channel data336 bytes plus native PSG296 bytes.
Independent decoder timing benchmark covers12,600 ticks. Exact median/p99/max
and per-case maxima are in `facts.json`/`emission.json`; Python timings are not
GameMaker decoder performance. Worst measured stream work is20 read/command
operations and20 port bytes in one tick. No native decoder, queue integration
or complete-game CPU claim follows from A1P's earlier PSG-only host acceptance.

Coverage: **9 IDs fully decoded within their tested scope;7 empty/control;
54 unsupported/unknown.** All70 rows preserve names, lifecycle, header identity
and existing alias/equal-output information. There is no speculative promotion
of an unscanned stream just because its header is understood. The five empty
music headers retain the earlier authenticated R1 classification; they were not
newly run. Partial/formatted-but-unverified categories have no newly promoted
rows. ID count is distinct from unique headers and contextual audible outputs.

Next practical batches are remaining short finite music, common SFX stratified
by clock/ownership class, remaining SFX aliases, then moderate repeating music;
long8D/8C/90/91 needs its own budget. First inspect the next batch's opcode/path
inventory. Focused follow-up is needed for table pitch programs, DE-relative
envelope controls, unverified opcodes, numeric D0/D1/D2, alternate envelope bases,
DE08 and more phase-dependent interference. Demand extraction covers selected
paths, not all possible request phases. Unexpected paths and ticks beyond4200
fail explicitly. These are named expansion limits, not a fundamental blocker
for the demonstrated architecture.

## Reproduction and preservation

Use Python3.12 with repository Z80 requirements; NumPy is needed only for PCM.
The local NumPy dependency directory from M4 can be set on PYTHONPATH. Research
rendering requires the already-pinned private MAME renderer and unchanged A1L
DLL; binaries are not included in this topic or released by this assignment.

```text
python tools/m5a2/proof.py PRIVATE_ROM
python tools/m5a2/evidence.py
python tools/m5a2/pcm.py
python tools/m5a2/isolation.py
python -m unittest discover -s tests -p test_m5a2.py
python tools/m5a2/package.py
```

The source ROM is required only for extraction/new original validation.
After extraction, `runtime.py` takes `programs.scsp`, a host schedule JSON,
the accepted A1L DLL and an output WAV path. It produces continuous audio
without ROM or traces. The isolated-process check forbids original-tool imports
and ROM/VGM/dry-bank/private-state file access during candidate playback.

Only safe source, docs, tests and aggregate numerical metadata belong in Git.
Private program payload, source segment receipts, captures, VGM and WAV stay
outside the repository in workspace `private-research/m5-a2/`, with a separate
checked ZIP under workspace `releases/` and a SHA-256 receipt.
The ZIP is a private research evidence package, excludes the experimental DLL,
and requires the existing accepted local backend for reproduction. Earlier
private package hashes and47 accepted M4 assets are checked, not rewritten.

**STOP for Manager review.** No full-library expansion, POC changes, Sound Test,
GameMaker integration, main merge or component distribution is authorised here.
