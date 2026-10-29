# M5-G1-R2 — exact interaction continuation capabilities

29 October 2026. **GO for the exact certified Research contexts below.
HOLD for arbitrary live gameplay event phases. STOP for Manager review.**

Research parent: `cf07885b5ccb719d5db9e3b09ebb79471ec09587` (G1-R).
Management read through GitHub at
`81461eb98542acd52a72f9c783a0bb60f296f78c`, including its G1-A acceptance and
separate G1-B/G1-R2 assignments. No main promotion, GameMaker edits, native
acceptance, catalogue census or inter-agent/thread contact.

## What this supplies

There is now a reusable **exact interaction checkpoint/recurrence mechanism**
over the unchanged bounded decoder. It can continue music indefinitely after
the certified SFX history, without restarting music, copying channel state,
rewinding a stream or resetting the physical PSG. Original Z80 evidence,
not candidate-discovered repetition, supplies every continuation permission.

It is a deliberately narrow capability: **the complete initial condition,
bank and host request schedule must match**. It does not yet make arbitrary
normal gameplay ring/spring timing safe. Designer must not remove that HOLD
by treating these 25 controlled contexts as an all-phase contract. This is
a usable research reference implementation and proof format, not a claim
that the requested universal live-game solution is complete.

## Consolidated GO/HOLD matrix

Updates are absolute sound-driver updates from a fresh original driver start,
with one fresh physical chip at session creation. All later events retain that
same chip. Requests are delivered through the genuine original DE04 mailbox;
these are controlled driver schedules, not naturally achieved pickups.

| Music / context | Exact qualified host history after initial request | Later original period | Decision |
|---|---|---|---|
| `$83` Gigalopolis | One of BF ring, A6 spring or C4 noise at update30 **or**211; then no further host action | 3072 updates | **GO exact**, six certificates |
| `$93` Aqua Planet | Same six individual effect/phase combinations | 3000 updates | **GO exact**, six certificates |
| `$8F` Special Stage | Same six individual effect/phase combinations | 1248 updates | **GO exact**, six certificates |
| Each of83/93/8F, competing/repeated effects | BF30, A6 at35, C4 at36, BF211, A6 at4190, C4 at4300; then no further host action | Corresponding period above, discovered only after the final request | **GO exact**, three certificates, including an interaction after the former4200 horizon |
| Each of83/93/8F, accepted music replacement | A6 at30, same music request250, BF451; then no further host action | Corresponding period above, using the actual post-replacement full state | **GO exact**, three new-epoch chain certificates |
| `$8F` clock/reset/restoration | F8 at30; ten B5 requests at90,150,…,630; genuine new8F request690; BF901; then no further host action | 1248 updates | **GO exact**, one certificate. Controlled60-update countdown spacing inherited from G1-R; natural first-tick offset remains unproven |
| Any programme above, a different SFX phase, additional/missing request, fade, auxiliary/deferred-mailbox action or different initial driver/chip history | Not covered by these schedules | Not inferred | **HOLD**, reject this capability; retain separately qualified bounded handling only |
| Different music ID replacement, power-up/restoration, death/card/clear chains | G1-R supplies bounded semantics; this investigation proves same-ID and clock restoration chains only | No fresh interrupted certificate here | **HOLD for extended playback** |
| `$81,$91,$92,$95,$90,$8B,$8C` and other programmes | Their existing solo and bounded G1-R evidence is preserved | No transfer from83/93/8F | **HOLD for new interaction continuation**; no catalogue rerun |
| Native GameMaker | Not executed or edited by Research | Requires exact native bank, state, ordered-write and persistent-PCM proof | **HOLD for native acceptance** |

All25 exact cases, their original hashes, admissions, suppression/release facts,
reset events, real music initializations, checkpoints and verification receipts
are under [`data/m5-g1r2`](../data/m5-g1r2). `evidence.json` consolidates the
counts and progression facts. GO is per complete context, not a blanket GO per ID.

Final comparison: **248,523 driver updates;182,664,405 exact continuous PCM
samples;82 recurrence renewals;24 authenticated window extensions; zero state,
ordered-PSG, transfer, PCM, native-state or render-partition mismatches**.
All25 isolated replays match. All27 private negative controls, eight new public
evidence tests and14 inherited G1-R/C9 public tests pass. These counts describe
the final run; an earlier full comparison preceded the added epoch-observation
check and is not added to the totals.

## Mechanism and integration contract

Use [`tools/m5g1r2.py`](../tools/m5g1r2.py) as the reference, alongside the
unchanged G1-R and C6–C9 decoder/loader contracts.

1. Select a trusted certificate whose exact canonical decoded-bank hash and
   initial driver conditions match. Keep the83 pitch reader,93 C9 pitch-reader
   policy and8F ordinary reader unchanged. The private G1-R union banks are
   pinned afresh; **no solo continuation certificate is reused**. Native bank
   repacking or a different owner/reader policy needs independent reconciliation.
2. Keep the existing single native audio owner,60Hz driver updates,735 samples
   per update, queue policy and one persistent A1L chip. The certificate wrapper
   owns separate **absolute update** and **proof position** counters. A proof
   position is never a stream pointer, music age or physical PSG clock.
3. Before each update, check that actual host actions exactly equal the
   certified action list for that absolute update. Wrong/missing/extra actions
   fail closed before the next engine tick. The reference API only accepts
   request events; fades, mailbox bypasses and other unsupported mutations must
   revoke the capability in a native integration. Do not silently ignore them.
4. At each4200-update proof boundary, compare the complete actual driver
   fingerprint with the frozen original checkpoint before allowing the next
   unchanged4200 engine window. The fingerprint includes all seven48-byte
   channel structures,12 globals, priority, saved noise, IY, logical PSG and
   data latch. Independent reconstruction checks all400 original RAM bytes,
   including the zero unused bytes. Native parity must retain those invariants.
5. At the certified repeat position, compare that complete state again. Only
   equality permits moving **proof position** back to the certified first
   position. Do not write driver RAM, owners, counters, IY, PSG registers,
   native oscillator counters or LFSR. Transfer diagnostics retain absolute
   timestamps; only their bounded diagnostic history is discarded.
6. Original capture establishes equal full400/IY/logical-PSG states across an
   entire later period, equal ordered writes including repeated noise writes,
   and equal transfer events at period-relative offsets. The final gated
   candidate is then compared per update against the continuous original
   through later renewals, including exact continuous accepted-A1L PCM and all
   26 native before/after fields. Physical-chip state need not recur: it keeps
   evolving under the actual equal ordered write stream.

This supplies an actual continuation path past4200 for an altered post-SFX
state; it does not reset or simply disable the4200 limit. No memory-range,
pointer, F7, pitch-data or decoder-operation exception is added. Existing
loaders still reject unauthenticated data/reader contexts. G1-R semantics
remain: music sequences advance during suppression, music runs before SFX,
F2 release is not an immediate retroactive music note, and competing effects
do not restore displaced SFX.

## Programme epochs and physical PSG

The reference observes **actual successful decoder music initialization**,
not merely a request, and compares those events with the original reset/
initialization evidence. Same-ID music at250 creates a new programme epoch;
F8 at30 in the clock case is a reset, **not** a music epoch. Restored8F at690
is a new programme epoch. SFX completion does not create a music epoch.

The original driver reset/initialization writes occur naturally; the physical
chip is never recreated. The certified chain carries the real prelude and
the actual resulting PSG register/latch state into the new epoch. It does not
substitute a fresh solo chip, assume immediate logical-PSG convergence or
restore a saved music position. The proof coordinate can continue spanning
the chain while actual programme age starts again at accepted initialization.

These are new interaction/epoch certificates pinned to G1-R banks. G1-R's
original-only5001-update restart probes are reused as causal evidence, not as
candidate continuation permission. Different-ID transitions remain HOLD until
their actual bank, reader policies and persistent-chip chain are qualified.

## Proof scope and remaining blockers

The original captures were frozen before candidate comparison. Each new case
contains normal playback, an original effect request, channel suppression,
original release, continuing music after recovery, playback past4200 and a
later authenticated full-state recurrence. Competing fixtures include repeated
requests and requests at4190/4300. Whole400 RAM reconstruction, channel/IY/
global/priority/noise/latch comparisons, ordered writes, transfer events,
continuous PCM, native fields and100+635 versus735 partitioning all remain
separate checks. The isolated candidate process denies original ROM reads,
original capture reads and original CPU imports; it generates playback from
private checked programme records, host actions and public hash certificates.

The 27 fresh negatives cover wrong phase, missing event, wrong ID, extra event,
changed bank and channel/IY/priority/latch corruption at continuation boundaries
for all three programmes. The inherited seven G1-R and seven C9 public evidence
tests are reused without repeating their original catalogue execution.

**Exact blocker for arbitrary live ring/spring usage:** no independent original
proof maps every possible incoming complete driver state and event phase to
a qualified post-interaction checkpoint. A song's nominal phase alone does
not describe SFX residue, shared IY, saved noise, latch, suppression-delayed
pitch/envelope progression or other active streams. A new request after an
otherwise successful recurrence also changes that condition. Candidate-only
cycle detection, apparent recovery, a stale solo fingerprint or a generic
period calculation cannot authenticate that state.

A future broader certificate needs either independently verified phase/state
families closed under the supported request transitions, or an original-backed
compositional invariant that covers those states without relaxing real reader
and memory guards. This investigation proves neither. Generating another25
arbitrary examples would not by itself close that gap. Other programmes are
not expanded because this missing contract, rather than their catalogue
identity, limits common gameplay support. Manager should review this narrow
GO and remaining HOLD before Designer treats it as a normal-play solution.

## Reproduction and publication

Python3.13 with existing z80/NumPy and the accepted private A1L DLL
`47e15c47e255900b819847e0ddefd7e3f0751dcc8f75dff3a1690f7e76adcf65`.
Reuse private G1-R83/93/8F banks; the Europev1.2 ROM is hash-checked.

```text
python tools/m5g1r2.py original PRIVATE_ROM
python tools/m5g1r2.py verify
python tools/m5g1r2.py negatives
python tools/m5g1r2_evidence.py
python -m unittest discover -s tests -p test_m5g1r2.py
python -m unittest discover -s tests -p test_m5g1r.py
python -m unittest discover -s tests -p test_m5c9.py
```

Only independently written harnesses, exact small host schedules, aggregate
facts, hashes, public evidence tests and this contract are published. Original
ROM, SCSP/records, full per-update captures, native binaries and audio remain
private under the established private research root. No waveform supplies
candidate playback. Root AGENTS and management files are untouched. No Windows
F5, hardware, natural-route or full campaign audio acceptance is claimed.
