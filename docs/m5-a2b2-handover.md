# M5-A2B2 remaining short finite music — Manager handover

**GO for a separately scoped, class-stratified SFX preflight and bounded proof.**
All six authorised finite requests passed. This is a proposal for Manager review,
not permission or execution of another content batch. No new decoder operation
was required. The short finite-music class is complete in the demonstrated
scopes; longer finite8D and unverified repeating tracks remain outside them.

25 October2026. Topic `research/m5-a2b2-remaining-finite` starts exactly at accepted
B1 `ae294d202d3165d2026373f9164d518cb40e489f`; management instructions read from
`cb1266f77b802dc44978c1144efd67daf395edbe`. Original ROM freshly authenticated:
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
Accepted M4 POC remains `11bff34356d5f5d979218896dc95fdc4bb265eae`, read-only.

## A–C. Implementation, completion and exact original-driver gate

The existing [A2 decoder](../tools/m5a2/decoder.py), [B1 E1 extension](../tools/m5a2b1/decoder.py),
SCSP v1 loader and A1L synthesizer are unchanged. B2 adds research orchestration,
private data extraction, tests and aggregate evidence only. Original stream
bytes and pointers determine notes, durations, envelopes and frequency updates;
there are no ID-specific timing rules, prerecorded combined event inputs,
unrecognised commands reinterpreted as silence or substitute notes.

| Request | Existing catalogue name | Original and candidate inactive tick | Post-completion ticks | Result |
|---|---|---:|---:|---|
|8E | Unknown $8E |188 |32 | PASS |
|94 | Continue-screen music |1081 |32 | PASS |
|96 | Player death music |340 |32 | PASS |
|97 | Act 3 clear music |274 |32 | PASS |
|98 | TRY AGAIN ending-card music |305 |32 | PASS |
|9A | Partial Sonic ending music |1153 |32 | PASS |

Each complete original finite stream was independently decoded from a frozen
private record, compared with fresh original Z80 execution and followed by32
additional ticks. All six finish attenuation15 on all four physical channels.
Registers remain stable, no slot reactivates and no new port write occurs in
those post-windows. Legitimate F2 output is compared, not replaced with a
general host mute or forced terminal register state.

**46 scenarios /24,847 ticks /117,677 ordered PSG bytes: exact PASS.** This
contains13 new cases/8710 ticks/38297 bytes, plus the full33 accepted A2/B1
scenarios/16137 ticks/79380 bytes. Every tick compares ordered bytes, physical
PSG registers and data latch, savedDE11, sharedIY,336 channel bytes and12 global
bytes, including priorities/mailboxes, pointers, durations and envelopes.
There is zero emission or timing tolerance. All actual original control-transfer
targets, order, ticks and channel identities equal the candidate. The candidate
finishes before the oracle is created per case; recorded oracle writes are
comparison/reference inputs only.

The seven new interactions are THZ→94 through completion without resurrecting
THZ;9A withAC/BC/B6 and rejected lower-priorityA3;94 withB6/A0/A3/BC across
tone1/tone2/noise;8E→97→97 restart→98;9A fade/reset followed by96;94 numericF8
followed by8E; and98 with simultaneous B6/A3/AC mailboxes, where B6 wins and
the lower priorities are rejected. These include counted-loop and envelope
progression under suppression/recovery. They are admitted original request
sequences, not a Cartesian pairing matrix or natural gameplay observations.

### Zero divider and actual counted-loop results

Both94 and9A retain original tempo globals `[0,0]` throughout their solo runs.
The ordinary 8-bit channel-duration progression is still active and compared
byte-for-byte; zero does not become a conventional BPM, silence, invalid-data
error or an extra duration-increment step. No horizon was extended.

| Solo | Executed F7 commands | Taken original/candidate branches |
|---|---:|---:|
|94 |6 |4 |
|98 |14 |12 |
|9A |12 |7 |

The branch counts are dynamic, not static site counts. Target/tick/channel
hashes and original/candidate equality are in [emission.json](../data/m5-a2b2/emission.json)
and [facts.json](../data/m5-a2b2/facts.json); full targets and captures remain
private. No unverified E2/E4/E5/E8/ED/F4/FA/FD, table pitch, alternate envelope
base or host-control mechanism was enabled. Existing original modulation reload
and saved-latch behavior are preserved by the unchanged interpreter.

## D–E. Continuous PCM and six ROM-free replays

Unchanged A1L is compared with fresh original-driver/pinned-MAME audio at the
accepted PAL3,546,893Hz,44,100Hz mono and735-frame/60Hz cadence. Tick-boundary
emission is retained; no Z80-cycle/hardware sample-identity claim is made.

| Solo | Mix max signed16 LSB | Mix RMS LSB | Largest tone-voice max LSB | Noise-voice max LSB | Samples incl32 post ticks |
|---|---:|---:|---:|---:|---:|
|8E |3 |0.233828 |2 |2 |161700 |
|94 |3 |0.215052 |2 |2 |818055 |
|96 |3 |0.175850 |2 |2 |273420 |
|97 |4 |0.244916 |2 |2 |224910 |
|98 |3 |0.156040 |2 |0 |247695 |
|9A |4 |0.201191 |2 |2 |870975 |

All13 new solos/interactions measured mix max3..4LSB and voice max0..3LSB,
with zero compared PSG register/counter/LFSR mismatches. Per-voice maximum and
RMS errors and block-RMS envelope differences are retained separately in
[pcm.json](../data/m5-a2b2/pcm.json). Driver envelope and physical attenuation
state are exact. No new case exceeds the prior observed5LSB range; no policy,
resampler arithmetic or tolerance was widened. These are new measurements,
not advance permission for untested content. No human listening was performed.

All46 candidates are identical for735 versus100+635 rendering partitions.
All33 previous A2/B1 candidate PCM outputs are byte-identical to their accepted
private files. The inherited8A case still holds period0/tone2 attenuation0 and
the same constant+8192 post-completion PCM. No DC suppression, artificial fade
or assumption that inactive readers imply digital zero was introduced.

Six separate fresh processes reload the expanded SCSP and play one complete
new finite selection plus its post-window. Original-driver imports and ROM,
VGM and dry-bank access are explicitly forbidden in those processes. Every
resulting WAV matches the independent candidate byte-for-byte. Playback uses
the unchanged B1 runtime with only SCSP, a host request schedule and the pinned
A1L backend as inputs; it has no emulator or recorded combined event input.

Expanded private SCSP remains **version1**, horizon **4200**, now **7759 bytes**
(+1694 over B1's6065). It contains21 unique headers,45 contiguous data records,
5380 original data bytes (+1664),402 header bytes and70 priority entries.
Raw data/header/priority values total5852 bytes; validation/address/hash
metadata contributes overhead. Record JSON24939 bytes. Private bank SHA-256:
`00f89cee32b1a9c31f887504182dfbed724e32ebab659f3eb7e1c923db4bc74c`.
All15 previous headers and all previous3716 data bytes match exactly. Standalone
A2 and B1 private banks and hashes remain untouched. Missing data, invalid
commands, corrupt pointers, stack/loop/operation bounds and explicit horizon
rejection retain their accepted behavior.

Python benchmark10599 finite ticks: median3.9µs, p9914.5µs, max58.8µs in this
run. Comparative bank+decoder allocation: B1 current318123/peak355540 bytes;
B2 current399861/peak444685 bytes, +81738 current/+89145 peak. This includes
sparse data and bounded diagnostic flow log, excludes interpreter base and PCM
arrays, and is **not GameMaker performance**. Per-case stream work and maximum
ordered-write workload are recorded in `emission.json`.

## F. Seventy-ID coverage and proposal only

[coverage.json](../data/m5-a2b2/coverage.json) retains all70 original rows/names:
**21 verified within authenticated scopes;7 empty/control;42 unsupported or
unverified;0 partial;0 preflight-only.**8E remains **Unknown $8E**. The covered
music comprises14 short finite requests and the previously bounded THZ loop;
the previous six SFX remain covered. This is not all finite music: long8D is
still outside scope. There are21 extracted unique headers, distinct from request
semantics, original68 indexed headers and61 bounded solo-emission fingerprints.
No inference of61 distinct audible outputs or universal interference parity
is made.

**Next proposal:** preflight common SFX candidates A4/A6/BF/A1/A2/A7, then choose
at most one small implementation group by actual tone2-only, fixed-noise,
periodic-noise and tone2-coupled ownership class. Retain numeric names where
unknown. Class-specific controls should cover savedDE11/data-latch restoration,
duplicate noise retriggers, channel replacement, suppression/recovery, priority
rejection and fade termination. This is a suggested set for Manager selection,
not six newly scanned or implemented programs. Continue remaining SFX by those
classes before moderate repeating music; long boss/zone tracks and8D require
separate horizon/render budgets.

Remaining language risks are unchanged: positive table-pitch programs,
DE-relative envelope controls, unverified stream commands, alternate envelope
bases, numericD0/D1/D2, DE08 and new phase-dependent interference paths. Demand
extraction proves the tested paths, not all possible branches or request phases.
New unsupported paths must fail and receive a bounded original reproduction.

## G–H. Tests, preservation and reproduction

**41 tests PASS:**31 unchanged A2/B1 tests plus10 B2 evidence/negative controls.
All46 original differential cases and33 legacy PCM checks are rerun. New
checks cover actual zero-divider/loop progression, finite/end-state/output,
source hashes, six isolated replays, precise catalogue counts and scope.
Mutated pitch data fails at tick1, omitted terminal writes at116, and deleting
a required program byte raises `DecodeError`. Existing corrupt data, pointer,
loop/call bounds, unknown opcode and horizon rejection tests remain green.

```text
python tools/m5a2b2/proof.py PRIVATE_ROM
python tools/m5a2b2/pcm.py
python tools/m5a2b2/evidence.py
python tools/m5a2b2/isolation.py
python -m unittest discover -s tests -p test_m5a2*.py
python tools/m5a2b2/package.py
```

Use Python3.12, the existing local NumPy directory on PYTHONPATH, and the
already-pinned reference renderer/A1L DLL. Only extraction/new oracle execution
requires the original ROM. Private data, detailed captures and WAV/VGM remain
outside the repository under workspace `private-research/m5-a2b2`; the separate
archive is in workspace `releases`. Public Git receives source, docs, tests,
aggregate numerical evidence and hash receipts only. No ROM or PSG DLL enters
the archive or public branch. Packaging checks all eight earlier proof archive
hashes,47 M4 payloads, clean accepted POC, original standalone A2/B1 banks,
A1P source/native/compiled VM artifacts read-only.

**STOP for Manager review.** No next content batch, full soundtrack, repeating
track production, Sound Test, GameMaker integration, main merge, maintainer
contact or component release has been performed or authorised by this result.
