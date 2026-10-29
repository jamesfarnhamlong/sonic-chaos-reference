# M5-G1-R3 — compositional continuation decision

29 October 2026. **HOLD for arbitrary-time and repeated `$BF` over `$83`.
STOP for Manager review. No new continuation permission is issued.**

Management: `2794060c68d3d253472590c69c520b9e0a0bb107`.
Research parent: `a057504dacb09a9c994bc55991e14237497e2e6e`.
Read and reuse [G1-R](m5-g1r-gameplay-audio-interactions.md) and
[G1-R2](m5-g1r2-interaction-continuation.md). Their completed original execution
and catalogue research were not repeated. No GameMaker source, main branch,
management file, sound clock, loader or decoder was changed.

## Decision and its practical meaning

**A general-state simulation proof is feasible in principle with this style
of decoder, but is not established by the existing verification architecture
or this investigation.** The original driver is not inherently limited to
4200 updates. That number is our evidence/eligibility boundary. Nor does a
failed attempt to derive a small invariant prove that arbitrary rings cannot
work, that the decoder is wrong, or that an original-CPU replacement is necessary.

The current decoder is a hand-translated, guarded partial interpreter. Existing
proofs authenticate particular original trajectories and exact recurrences.
They do not establish that its transition relation simulates original Z80
execution over an input-closed set of states. R3 identifies the missing proof
obligations and rejects two insufficient candidate state abstractions. It does
not manufacture a permission to remove the horizon check.

**Designer contract now:** preserve existing bounded behavior and exact R2/solo
capabilities in their accepted scopes. Do not enable indefinite `$83+BF` for
normal gameplay, reset music after ring release, discard SFX residue, substitute
a solo chip/checkpoint, bypass guards or issue a Chief build on R3 authority.
No other music/SFX request class receives a new GO.

## Smallest adequate proof target

Start with one original83 initialization from the accepted fresh-driver
baseline. At each sound update thereafter allow input `u` to be either no
mailbox write or a BF write to DE04. Allow that choice at **every** update,
including consecutive updates, active-ring restart, release/read boundaries,
and arbitrarily long histories. Multiple BF writes before one driver update
collapse to the original mailbox's last value; this is not a queued-event API.
Do not include fades, resets, other music, auxiliary mailboxes, pause/control
paths or game deferred-delivery timing in this first proof target.

Let `O` contain original driver RAM400, IY, mapped immutable data and logical
PSG/data latch, with the original driver-entry/stack assumptions. Let `D`
contain the corresponding seven channel structures, globals, logical PSG,
plus decoder-only owner/reader metadata. Let `N` be the actual persistent
accepted-A1L chip state. Define an explicit well-formed reachable-state
predicate `K` and representation relation `R(O,D)`.

An adequate claim must establish, not assume:

1. **Base:** authentic83 initialization establishes `K` and `R` from the
   accepted initial memory/CPU/bank conditions. Both renderers start equal.
2. **Input closure:** for every state in `K` and both choices of `u`, the
   original mailbox/arbitration, complete tick and candidate tick return;
   every decoder guard succeeds; resulting states satisfy `K` and `R` again.
3. **Output simulation:** that same step emits exactly the same **ordered**
   PSG byte sequence and corresponding stream transfer events. Equal final
   register values alone do not establish this.
4. **Chip lifting:** equal persistent starting `N`, equal ordered writes,
   equal clock/rate and735 rendered samples imply equal PCM and resulting
   `N`. Keep actual oscillator/LFSR state; do not require it to recur or reset
   it at music/driver proof boundaries. This is a conditional deterministic
   consequence after step3, not an independent driver-semantics proof.
5. **Native refinement:** pin the actual native decoder source/bank and prove
   its update order, byte arithmetic, owner/reader metadata and emitted writes
   implement the same established transition relation. Manager-reported G1-B
   bounded native comparisons are valuable finite evidence, not this lemma.

Induction on update count would then handle every finite prefix of every
allowed ring history. Further rings would be ordinary closed transitions,
not certificate invalidations. No collection of per-history recordings would
be needed. **The required input-closure/simulation lemma remains unproved.**

## Source audit: the missing invariants are specific

Original ranges below are CPU addresses in the accepted sound-bank mapping.
Their private-ROM source hashes and the pinned inherited Python function hashes
are in `data/m5-g1r3/original-searches.json` and `source-audit.json`. They are
provenance/audit pins, **not** a machine-checked equivalence certificate. The
Python reference is the semantic research subject; no new equivalence claim
about uninspected/current native GameMaker source is made.

| Obligation | Original evidence / inherited decoder | What must hold under every BF/no-event transition |
|---|---|---|
| Entry/global representation | Original4000 arbitration and driver RAM; `Decoder.tick`, `reset`; G1-R full400 reconstruction | All omitted global bytes remain zero, CPU entry/return/bank assumptions hold, selected/mail/tempo/priority/IY match. The model's zero padding is not a proof that original execution preserves those zeros for all histories. |
| Ring admission and partial initialization | Original41A7..4266; `init`, `direct` | BF header-selected tone2 ownership, priority, noise-slot suppression and initialization writes match, including equal-priority repeated requests. Initialization overwrites offsets0..10 and39..41; unoverwritten fields must be retained and related, not presumed fresh. |
| Music control and F7/stack closure | Original4341..43E4, transfer/F7 handlers; `read`, `command`, `duration`, `finish_read` | Music and SFX pointers/return stacks/counters remain in authenticated stream grammar. Every F7 index, call cursor and operation count remains inside existing guards. A possible phase-only invariant for control pointers needs its own original-backed proof; unchanged nominal song age is insufficient. |
| Suppression, inhibit and envelope state | Original channel processing and4546..4638; `channel`, `env`, `attenuate` | Reader versus non-reader paths, bit2 versus bit4, cursor/reset behavior and repeated suppression preserve envelope-domain bounds. A mask on audible writes does not describe this transition. |
| Shared pitch/IY and data address closure | Original4267..4340, especially42F6; `pitch` and83 scoped `word` | Actual current IY determines reload source; read order, initialization and other eligible channels matter. Every reload/note/envelope pointer must be covered by exact data and owner/reader rules, with correct byte wrap/carry behavior. Per-channel independence cannot simply be assumed. |
| Completion and persistent residue | Original47C8..481B; `release` | Exact ending-slot flags, shared priority reset, music suppression-clear/inhibit-set and ordered off writes match. Inactive channels and saved noise/latch remain represented. A later BF must be safe from the actual retained residue. |
| Data/reader and budget safety | Exact83 contract; base sparse bank, stream/envelope256-step limits and F7/call guards | Bank authenticity alone does not prove every dynamically computed read/branch stays in it, reaches only supported operations, or terminates within budget. Need a closed reachable domain, not broad pointer permissions. |
| Physical PSG/PCM | Original ordered port writes; accepted A1L hash and existing continuous comparisons | Do not split into independently rendered song/effect recordings or equate only final registers. Noise/LFSR retrigger and data-latch effects require exact write order. No new uncertainty about A1L is alleged; this is the dependency of the induction argument. |

The scope-specific83 pitch pair at4634 remains restricted to its authenticated
tone1 note reader/owner/transpose; it is not stream data. The92 F7 exception is
unrelated and receives no new scope. All memory, F7, reader and operation guards
remain unchanged. Historical early language docs describe superseded opcode
whitelists; the actual pinned inherited class chain in `source-audit.json`
determines the current implementation.

## Evidence that rejects shortcuts, without repeating old execution

The cached, accepted original83 solo and R2 `83-BF-30` captures already show:

- At update30 the interrupted music's **tone2 channel offset31** differs from
  solo, even after excluding the flags byte. That offset is envelope cursor/
  level state. Thus “the solo music state always continues unchanged, only
  output is masked” is false. It does **not** refute a richer relation that
  tracks envelope state, or a narrower invariant for control pointers.
- At update50 the ring SFX slot is inactive but has20 nonzero retained bytes.
  Thus “inactive SFX equals the initial all-zero SFX state” is false. This
  establishes a full-state distinction; it does **not** prove every residual
  byte is observably relevant to every later ring or prohibit a proved quotient.
- R2 checks literal host actions before stepping. An otherwise valid BF at an
  unlisted phase is rejected by design. Its recurrence theorem covers a
  no-further-host-action tail, not an input-closed transition system. Testing
  every isolated first-ring phase would still leave arbitrary later histories
  and the invariant itself to prove.

`cached-obstructions.json` gives hashes, offsets and aggregate facts only.
The reused interrupted capture is checked against its accepted R2 capture
hash; solo full400/IY/logical-PSG hashes are checked against the original cached
state sequence, and the complete solo artifact hash is pinned. No cached
per-tick payload is republished.

An additional **synthetic, not claimed reachable** state moves an active
stream pointer outside the sparse bank and demonstrates the retained guard
rejection. This is not a discovered gameplay bug or a counterexample to
equality on reachable states. It shows why unrestricted “all equal400-byte
states simulate” is not a sufficient totality claim: `K` must exclude such
states and prove they cannot be entered under the supported input alphabet.

## Two bounded adversarial searches, not a general proof

Only two new short original executions were performed, frozen before candidate
comparison:512 updates each. One supplies BF on every update2..257 then allows
release; the other supplies17 clustered requests around early reader/release
boundaries. These stress repeated partial initialization and ordering.

All1,024 updates,752,640 continuous PCM samples, full400/IY/logical PSG states,
ordered writes, transfer events and26 native before/after fields match. One
persistent chip is used per stream; no extension/checkpoint/reset is installed.
Both executions stay within the unchanged4200 bound. No schedule continuation
certificates are generated. These searches found **no new reachable divergence**;
they are not evidence that arbitrary histories close.

Six additional guard negatives reject raw83 pair access, pair access outside
its reader, unverified opcode, F7 index3, requested horizon4201 and ordinary
window exhaustion. The synthetic pointer rejection above is separately scoped.
Neither finite passing searches nor successful guard negatives discharge the
universal source-transition/closure obligation.

All six new public decision/evidence tests pass. No old original execution or
catalogue test sweep was repeated; inherited source hashes verify preservation.

## Practical alternatives for Manager

| Option | Work needed and benefit | Limitation / approval boundary |
|---|---|---|
| **A. Prove the existing macro decoder compositionally** | For83/BF only, derive original control-flow/bit-vector semantics and prove a closed state predicate for the table above. Use original/candidate basic-block or helper refinement plus an inductive invariant, retaining every current guard. Could reuse most architecture and native owner. | Recommended first proof approach if further research is funded. Requires actual translation/closure verification, not another schedule sweep. No claim here that its cost or solver complexity is small. Future native implementation needs its own source pin/refinement and acceptance. |
| **B. A closed proof-carrying state family** | Build an original-backed state abstraction/product automaton for music control, envelope/pitch, ring residue and shared state; prove BF/no-event transitions preserve it and outputs. Permit continuation by invariant membership rather than exact history. | Feasible in principle because state is finite; state explosion and abstraction refinement are unresolved. Unsound to collapse fields merely because a sampled trace never reads them. This can remain the current decoder; it need not be a CPU runtime. |
| **C. Separately authenticate an original-driver execution runtime** | An exact restricted Z80/original-driver interpreter or mechanically validated source translation would execute the real transition semantics rather than rely on trajectory certificates. Pin original driver/private data, CPU instructions/flags, memory/bank/stack and port model, tick entry/return and resource bounds; retain single physical PSG/A1L and host ordering. | A separate architectural project, **not implemented or authorised here**. It moves proof obligations to the CPU/translation/mapping boundary; it does not eliminate them. Private original code/data must stay private. Runtime/performance and native acceptance also need separate proof. Not shown necessary by R3. |
| **D. Retain current bounded/exact policy** | Preserve all accepted evidence and fail closed outside qualified context. No new architecture or unsupported claim. | Safe interim policy only; it does not deliver ordinary indefinite gameplay audio and should not be presented for a new Chief acceptance test. |

**Technical gate:** optionsA/B are possible research directions, not GO to
change playback policy. The current source and evidence do not establish the
needed invariant; C is an alternative if Manager chooses a different proof
boundary, not a mandatory replacement. R3 ends with a clear HOLD and no
automatic follow-on work.

## Reproduction and public/private boundary

Use existing Python3.13/z80/NumPy, private checked83 bank/caches and accepted
A1L DLL `47e15c47e255900b819847e0ddefd7e3f0751dcc8f75dff3a1690f7e76adcf65`.

```text
python tools/m5g1r3_gate.py cached
python tools/m5g1r3_gate.py audit
python tools/m5g1r3_gate.py original PRIVATE_ROM
python tools/m5g1r3_gate.py verify
python tools/m5g1r3_gate.py negatives
python -m unittest discover -s tests -p test_m5g1r3.py
```

The script writes raw searches/schedules only to the established private
research root. Public files contain independently written harness code,
source/trace/state/PCM hashes, bounded counts/offsets, proof obligations and
decision metadata. No original ROM/programme records, instruction listings,
raw states/writes, audio, native binaries or captures are published. No
GameMaker build, new native test, natural route, broad sweep or cross-chat
communication occurred. Root AGENTS and management documents remain untouched.
