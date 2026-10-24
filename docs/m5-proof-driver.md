# M5-P0 driver proof: bounded ownership PASS, full output gate HOLD

24 October 2026. Parent: accepted M5-R1
`7d700d0f2d51812d48d9743443e688bc1f9c5793`. Private POC remains
`11bff34356d5f5d979218896dc95fdc4bb265eae`, unchanged. Local ROM was authenticated
as SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
Read alongside [M5-R1 driver contract](m5-driver-integration-contract.md) and
the accepted [M4 production contract](m4-audio-production-validation.md).

**Overall P0 acceptance is HOLD.** The new event-driven model matches the
bounded ownership/dispatch projection described below, but that projection
does not prove complete PSG output-state behavior. P1 exposes a real missing
distinction between write inhibition and physical mute. No full driver or
composition parity is claimed. [gate.json](../data/m5-proof/gate.json) is the
overall result; raw `p0-result.json:status=PASS` refers only to its named fields.

## Independent model and its inputs

[m5p0_model.py](../tools/m5p0_model.py) is a PCM-independent Python ownership
reference with no Z80/ROM/renderer dependency. It implements three separate
SFX occupants/ages/generations, four music occupants, original shared priority,
three pending mailboxes, deferred byte, tempo/fade order, F2/F3 ownership effects,
restart/reset and write-inhibit bookkeeping. Its unconditional administrative
Stop is distinct from original priority-gated numeric F8. Nonzero-only deferred
transfer is the approved M5 target. No accepted GameMaker behavior was changed.

The model consumes PRIVATE intrinsic channel event metadata: dry per-ID
stream-reader/F2/F3/tempo event times, headers and priorities. These are exported
once from **solo** original-driver executions by [m5p0_proof.py](../tools/m5p0_proof.py).
It is deliberately an ownership integration model, **not an independent note,
envelope, modulation or sound-stream decoder**. Combined test traces never
drive it. Intrinsic event timing is inherited authority, not a second proof of
the original stream decoder. Exhausting a captured program's coverage raises
an error; it never silently extends an unrecorded music schedule.

This separation tests whether dry metadata can support the proposed hybrid
dispatcher. It is stronger than replaying combined observed flags, but weaker
than a complete independent original-driver implementation. Private programs
and recovery timelines remain under ignored `build/m5-proof/`; none is public.

## Exact comparisons

The combined oracle is the existing original Z80 harness, not hardware or a
GameMaker Runner. [p0-result.json](../data/m5-proof/p0-result.json) retains all
counts, scope and failures; PRIVATE extended comparison records retain detailed
recovery events. New code does not modify accepted M5-R1 evidence.

| Comparison | Count | Raw result |
|---|---:|---|
| All ordered SFX pairs from R1 | 1,369 | exact ownership/priority match |
| Same-ID SFX, music replacement and F8 attempts | 111 | exact ownership/priority match, including dropped F8 |
| SFX37 +F8 × stored priority0..127 | 4,864 | exact admitted selection and priority |
| R1 single-effect recovery at three THZ phases | 111 | exact projected state;159 release/eligible-reader facts match |
| Existing M4 music4 × effects2 × request phases24 | 192 | projected fields match original execution |
| Existing81/82 loop-boundary effects | 4 | projected fields match original execution |
| New collision/stagger/fade/pause/finite controls | 15 | projected fields match original execution |

The1,480 original cases compare seven `flags & $C4` values and global priority
at every tick:5,671,360 scalar field comparisons. The322 extended cases compare
those fields plus two tempo counters, three pending bytes and three fade
counters (16 fields/tick). The priority loop separately compares selection and
stored priority. **Normal envelope/rest bit4 and complete PSG register writes
are not included in that green projection.** Recovery bookkeeping is checked
against the159 existing release/next-reader facts rather than asserting all
normal bit4 transitions are modeled.

Original IRQ transfer was executed from CPU `$05C9` at its original address,
stopping at `$05D6` before mapper writes. Direct A0 plus deferred0 retains A0;
direct A0 plus deferredBF delivers BF; direct0 plus deferredA0 delivers A0;
direct0/deferred0 remains0. This is original code execution, not merely a
Python reproduction of the expected branch. Direct0 still cancels a pending
direct byte. Original F8 raw priority57 admits at57 and drops at58/78.

Other focused controls include AC→A0→staggered A6; BF→coupled A3→BF;
fixed-rate B8→BC; fade with three active slots; selected99 erased by terminal
fade reset; music/sfx on fade-start tick; pending request through pause;
administrative Stop; late A6 over finite99; same-ID finite88 restart.
These are bounded phases and captured metadata coverage, not every original
playback phase, music/SFX combination, mailbox writer or hardware schedule.

## New blocking output-state distinction

In original THZ with B8 at30 and BC at35:

- B8 selects fixed-rate noise control5. BC concurrently occupies tone2.
- BC completes at63. F2's tone2 branch sees an active noise SFX, clears its
  suppression and sets its bit4, then emits **tone2-off**, not noise-off.
- Noise remains active with flagsD8. PSG noise attenuation stays2 and control5
  for ticks63–166 despite inhibited ordinary noise writes. At167 the envelope
  end path emits noise-off; the noise stream itself finishes168.

The failed PCM selector treats `waiting/bit4` as mute. It therefore loses104
ticks of real held output. Original CPU `$47FB..$4816`, `$4528..$4545` and
`$4639..$4649` explain the distinction: inhibited attenuation writes do not
clear the PSG register, while the envelope terminal-off helper can still emit
off. The regression executes the original driver and checks that held span.
This is **not** an oscillator-phase excuse. The complete state-machine target
must retain emission/held-register semantics before full P0 acceptance.

M5-R1's next-reader shorthand remains useful for its observed music recovery
cases, but is insufficient as a universal physical-silence rule for SFX slots.
This additive finding supersedes that interpretation; old R1 files are intact.
The reference model now labels `waiting` as write-inhibit bookkeeping. The
deliberately failing selector is retained and explicitly marked NEVER SHIP.

One B6 tone1 attenuation-projection tick also remains unresolved; generic fade
and standalone oscillator phase remain approved approximations. See the
[audio report](m5-proof-audio.md). A next assignment should first extend the
PCM-independent output/emission model and prove held-register behavior, then
repeat only the failed bounded compositions. No synthesis rewrite or all-phase
asset bank is authorized or proposed by this proof.
