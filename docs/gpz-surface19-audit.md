# GPZ surface $19: state-conditioned loss of support

Surface `$19` is a one-way running strip. Slowing ordinary running Sonic
causes the walk callback to request **special fall `$14`**, after which the
one-way projection refuses support. This is a state-conditioned rule: a
synthetically placed idle-state Sonic at speed zero remains supported. Do not
implement a universal speed cutoff independent of player state.

Evidence: verified Europe v1.2 ROM, source-traced original instructions,
14,852 signed-speed suffix cases, 96 original floor-projection cases, and
deterministic original animation-engine/state-callback update fixtures.
Reproduce with `tools/gpz_surface19.py ROM --check` and
`tests/test_gpz_surface19.py`. The generated cache contains numeric inputs and
results, short region hashes and no ROM/art dump. No POC file was changed.

## Entry, slowing, stopping and support

Blocks `$85/$87` both have header `$59`, modifier zero, vertical profile 32
at every X, horizontal profile `$40` at every Y, and no alternate header.
They therefore use the ordinary one-way floor path on either plane. At the
GPZ2 requested anchor `(528,686)`, block `$87` is in the supporting row at
Y704; X496 instead tests `$85`.

`$691A` samples the foot (`anchorY+18`) and projects using the **previous**
surface before dispatching the newly sampled subtype. `$6B23` then sets
player `+$24` bit0 and increments `$D3BC` modulo 256. It changes no velocity,
position, plane or requested state itself.

Ordinary dry walk callback `$3783` first runs the normal movement/terrain
pass. With requested state still `$05`, `$3791` then runs the ordinary
input/contact helper, converts the full signed X speed to its absolute
value, and compares its high byte to `$D374` (current speed limit high byte).
**Equality** requests running `$06` before testing the strip bit. Otherwise,
bit0 requests `$14` through `$4663`. On water (`$D443 != 0`) this comparison
and strip-fall branch are skipped. The normal integration clamps speed, so
the equality normally means reaching the current maximum, ordinarily 4.0.
Do not replace the recovered equality with an unconditional `>=` test.

Run callback `$384D` has a different comparison: it takes the absolute
value of the **signed high byte**, and requests walk `$05` if it is below
4, independent of `$D374`. Fractional speeds make this directionally
asymmetric: rightward run survives at `vx >= 1024/256`; leftward run
survives at `vx <= -769/256`. This is not a directional entry restriction;
both directions can enter and cross the strip. The walk comparison uses
the full signed speed and is symmetric.

`$4663` sets requested `$14`, Y speed +1.0, movement bit0 (airborne), clears
attack bit1 and floor bit1, and zeros `$D3BC`; it **retains** `+$24` bit0 and
does not change X speed, X/Y position or plane. Current state stays unchanged
until the next `$64FA` animation-engine call accepts the request. State
`$14` callback is `$3A48` (script trampoline `$03F8`); it runs ordinary
movement, gravity and terrain, and requests ordinary walking on landing.
This state is distinct from ordinary fall `$0E` and act-clear `$20`.

`$6FBB` checks strip bit0 and **requested** `$14`; that combination returns
before one-way support/projection. It applies to any one-way surface while
the bit persists, not only subtype `$19`. Solid surfaces still use their
normal support path. Surface-zero handler `$6C45` clears both `+$24` bits
0/1 without a direct `$D3BC` write; its subsequent fall-selection path may
call a setter which resets the counter. Normal jump `$45ED` and ordinary fall setter
`$463C` clear strip bit0 and reset the counter. Sonic's walk/run frame
selectors also clear/reset after detecting a non-`$19` surface.

The original-routine GPZ2 fixtures show:

| Input | First two updates | Result |
|---|---|---|
| Run `$06`, +4.0, hold right | X532/536, Y686/686 | Supported crossing |
| Run `$06`, -4.0, hold left | X524/520, Y686/686 | Supported crossing |
| Walk `$05`, +3.0, hold right | request `$14`; Y686 then687 | Falls through |
| Walk `$05`, 0, neutral | request `$14`; Y686 then687 | Falls through |
| Run `$06`, +4.0, release | +1004/256 requests `$05`; +984/256 requests `$14` | Falls through on second update |
| Forced idle `$01`, 0, neutral | Y686/686 | Remains supported |

Y then follows ordinary gravity: stopped walk goes 686,687,688,690,...,
723 by update16. It does not need a counter threshold to begin falling.
The floor path clears support immediately when `$4663` runs; actual downward
motion begins on the next update. Counter increments resume during falling
while the foot still samples `$19`; they do not restore support.

The exit/reentry fixture uses explicit synthetic relocation after twelve
fall updates to `(110,448)`, then runs sixteen original updates. It asserts
actual ordinary solid landing and bit0 cleanup before relocating back to
`(528,686)` in run `$06`. Original updates then reacquire bit0 and support.
This is a controlled lifecycle fixture, not a claimed continuous route or
whole-game replay. IRQ, VDP, object scheduling and controller polling are
outside this subroutine harness; pad bytes and map/row tables are explicit.

## Complete relevant consumer inventory

All nine occurrences of little-endian operand `$D3BC` in the canonical ROM
were classified as actual instructions. Fixed CPU addresses below equal
file offsets and lie in bank1; bank `$0C` entries use
`file = $30000 + CPU - $8000`.

| CPU / file | Instruction role |
|---|---|
| `$4604` | normal jump zeros counter |
| `$465B` | ordinary fall zeros counter |
| `$467C` | special strip fall zeros counter |
| `$6B1E` | surface `$1B` increments every fourth `$D12F` update, sets `+$24` bit1 |
| `$6B27` | surface `$19` increments every contact pass, sets bit0 |
| `$703D` | **only numeric read**: one-way bit1 sinking projection adds counter to corrected Y |
| `$0C:$8D1B` / `$30D1B` | other-character run selector clears counter on leaving `$19` |
| `$0C:$8F00` / `$30F00` | Sonic walk selector clears counter on leaving `$19` |
| `$0C:$8F5B` / `$30F5B` | Sonic run selector clears counter on leaving `$19` |

The numeric read belongs to the separate `+$24` **bit1** path selected at
`$6FC7`, associated with surface `$1B`, not a speed-strip countdown or
minimum-speed consumer. When both bits are synthetically set, requested
`$14` returns before bit1; other requested states can enter the bit1 path.
Surface-zero clears both bits, but counter storage can persist harmlessly.

Every direct player bit0 instruction was also checked: reads `$37BF`,
`$6FBB`, `$0C:$8CBF/$8D07/$8EEC/$8F47`; set `$6B23`; clears
`$460F/$4656/$6C45/$0C:$8D16/$8EFB/$8F56`. Other-character walk selector
uses the bit solely for its frame sequence; this audit's gameplay fixtures
are Sonic. Generic slot initialization/cleanup can clear entire slots.

Sonic strip walk/run choose frames `$3C..$3F` instead of ordinary walk/run
frames. Walk duration remains its existing speed table; run duration remains
4. Frame IDs do not alter support, speed, plane or collision profiles. The
special fall script uses frames `$1C..$21` with duration4. No animation timing
consumer is required to decide strip support.

## AGENTS candidate updates

- Surface `$19`, blocks `$85/$87`, sets `+$24` bit0: ordinary dry walking
  below the current maximum requests special fall `$14`; retained bit0 plus
  requested `$14` disables one-way support. Running deceleration reaches this
  path through `$06 -> $05 -> $14`. Forced idle is an exception; avoid a
  universal speed-only cutoff. Neither entry nor fall changes plane.
- `$D3BC` is shared with surface `$1B` / `+$24` bit1 sinking projection;
  its increments on `$19` do not determine the strip fall timing.
- Preserve the signed-high-byte left/right fractional asymmetry of the run
  callback, and the full-absolute-speed equality against `$D374` in walking.

No GPZ enemies or boss `$51` were audited. Original visual gameplay acceptance
remains separate from these deterministic controlled-routine results.
