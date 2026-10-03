# GPZ regular enemies — approved research / art package

Canonical Research base: `08fb38c`; working branch `research/gpz-enemies-art-approval`.
ROM: Sonic Chaos (Europe) v1.2, SHA-256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
POC untouched. On 2026-10-03 the user approved `$25`, `$2C`, corrected `$51`,
`$34`, `$0A`, `$0F` and authorized committing/pushing the full Research package.
Main integration and POC implementation handoff remain separate steps.

Machine input: `data/rom-cache/gpz/enemy-art-approval.json`.
Exact raw placement records, file offsets, bank/CPU addresses, flags, parameters,
art bases, mapping records, state scripts, code-region hashes and reuse census
are included. Assets and instruction traces stay in ignored `build/gpz-enemy-approval/`.
Numeric identities are canonical; informal names below describe appearance only.

## Census and reuse

| Type | Description | GPZ1 | GPZ2 | GPZ3 | Later placements |
|---|---|---:|---:|---:|---|
| `$25` | Ground patrol robot | 5 | 7 | 0 | None in the six-zone mapped lists |
| `$2C` | Flying enemy with exhaust | 4 | 3 | 0 | EEZ1: 1; EEZ2: 8 |
| `$51` | Boss and linked segments | 0 | 0 | 1 | No other mapped placement |

Evidence: **decoded data** from all 18 object lists, not a claim that dynamic
spawns never reuse these types. EEZ `$2C` uses art base `$94` rather than GPZ `$8C`;
six EEZ2 placements use parameter 1. Their art approval is outside this batch.
GPZ `$2C` placements all have parameter 0 and flags 0.
GPZ `$25` parameters are 4..11, specifying distinct left patrol spans.
Preserve GPZ1's `(928,878)` `$25` record even though it is below the room's
768 px extent. Its runtime reachability is unresolved; do not relocate it.

## Type `$25`

**Decoded data / source-traced behavior:** animation type-table entry file
`$6602` selects bank `$0C:$B50D` (file `$3350D`), with states 0..2.
Mapping bank `$0F:$9198` (file `$3D198`) contains blank frame 0 and visible
frames 1/2 (`$919E/$91A9`). Each visible frame has six 8x16 SAT pieces and
object extents `+$2C=7`, `+$2D=17`.

State 0 record: duration `$E0`, blank frame 0, initializer `$B535`.
The initializer sets X speed `-$0080` (-0.5), Y speed `$0200` (+2), requests
state 1, saves `placementX - parameter*16` at `+$37/+$38` and consumes parameter
`+$3F` by clearing it. **Controlled routine result:** all 256 parameter values
match this arithmetic. Canonical records retain the original parameter.

State 1 ORs bit4 into `+$04`; state 2 clears it. Both alternate frames 1 and 2
every eight callback updates and call `$B573` each update, including record holds.
The callback integrates position (`$60FB`), performs generic object floor
projection (`$77CB`, including the fixed +18 foot probe), checks the patrol-bound
helper via `$042E`, and reverses through `$0437` while requesting the opposite
state when the bound helper reports reversal. The reversal branch returns before
player overlap on that update. Otherwise it checks `$6328` and enters shared
enemy reaction `$5F3D` through vector `$0323` on contact. Do not add the `$21`
spring-top exception: `$25` has no such branch. Ground projection is not Sonic's
terrain solver, and +2 Y speed is not evidence for adding player gravity.

The patrol window uses the saved canonical placement right limit and computed
left limit; inherited helper arithmetic is documented in `object-21.md`.
No new floor-loss state exists in the three-state `$25` script table.

## Type `$2C`

**Decoded data / source-traced behavior:** type-table entry file `$6610` selects
bank `$1E:$8947` (file `$78947`), exactly the shared `$27` state table. The
mapping is distinct: bank `$0F:$922A` (file `$3D22A`), visible frames 1/2 at
`$9230/$923B`, three SAT pieces each; extents are 12x16, not `$27`'s 9x14.
The existing `$27` movement audit applies to the shared routines, but neither
its collision dimensions nor THZ bee graphics apply.

| State | Frames / timing | Callback and behavior |
|---|---|---|
| 0 | blank 0, `$E0` | `$898E`: GPZ parameter 0 requests 1, X=-2.5, Y=0 |
| 1 | 1/2, two updates each | `$89AC`: bit6 asleep gate; overlap/reaction first; then integrate; strict post-move `abs(dx)<64` triggers 2 and keep-alive bit1 |
| 2 | 1/2, two updates each | `$89DF/$89F3`: signed Y velocity increments/decrements 3/256; shared contact tail precedes movement; independent `$80` counter underflows after 129 callbacks and requests 3 |
| 3 | 1/2, two updates each | `$8A29`: pre-move player distance `>=384` requests type `$FE`; otherwise contact first, then integrate left at -2.5 |

The state-2 script has +3, -3, +3 phases with 8/16/16 frame-pair loop counts.
The independent counter ends traversal during the last phase. Contact can skip
the movement/counter tail and delay the transition. Parameter !=0 enters state2
directly and prevents the independent countdown tail; that later-zone variant
is not used in GPZ. Existing `object-27.md` and `thz1_object_27.py` retain the
verified 129-callback oscillator model. The new tool executes signed ±63/64/65
trigger and ±383/384/385 removal boundaries with type `$2C`.

## Contact / hurt / defeat, shared by both

**Controlled routine result:** exhaustive `$6328` grids:

| Type | Closed interval in anchor space | Swept points | Mismatches |
|---|---|---:|---:|
| `$25` | X ±15, Y -17..+24 | 2,450 | 0 |
| `$2C` | X ±20, Y -16..+24 | 3,105 | 0 |

These are ordinary Sonic 8x24 results. State `$0F` has player X extent 9 and
therefore adds one pixel to horizontal reach; consume the shared extent table.
The helper uses minimum-penetration classification with vertical ties and the
recovered hurt/invulnerability gates. Vertical reach is asymmetric: do not add
player height a second time to object `+$2D`.

Shared enemy reaction tests attack posture `$D503` bit1 or selector `$D532==6`.
Airborne bit0 alone does not defeat either enemy. Contact in four directions was
executed for postures 0/1/2/3/64/128 and selectors 0/6 (48 cases per type).
Attacking/invincible eligible contact converts the object to `$0F`, zeros its
placement token and retains placement occupancy (permanent defeat until the
placement map is reset). Non-attacking contact leaves the enemy and writes
`$D520` plus directional flags; player `$48BC` resolves damage on its next update.
Use the canonical player handler for ring loss/death, i-frames and attack rebounds
(-3 from above, +0.5 from below except state9), not immediate object-side damage.
Hurt bit6 blocks overlap; invulnerability bit7 has distinct bookkeeping and must
not be confused with the visual flags. Neither enemy has a `$21` top stomp.

## Lifecycle and art

Generic mapped lifecycle remains viewport-relative (`viewport-semantics-audit.md`):
visible `[LEFT,RIGHT)`, 32 px wake margin and 32..96 px outer create/sleep bands,
vertical deletion boundaries and tracked `$FE` cleanup. Ordinary deletion releases
occupancy and can recreate from the unchanged placement; defeated conversion
detaches the token and preserves occupancy. `$2C` keep-alive after its 64 px trigger
and the final player-distance 384 rule must not be widened.

The accepted POC retention adapter currently names `$10/$21/$27`; extending it to
either GPZ type is a new documented adapter decision, not automatic ROM behavior.

Palette 7 (file `$3B6BD`) is used by the regular GPZ enemies. `$25` normal art base
is `$96`, mirrored `$A8`; the level loader's transformed copy supplies reversed
tile pixels while the original mirror coordinate table changes piece positions.
Never flip the already-composed image again. `$2C` uses `$8C/$8C`, with no separate
mirrored copy. Every GPZ placement uses bit4=0, so only that orientation is a
GPZ runtime import candidate. Forced bit4=1 is included as an explicitly unused
diagnostic; its exhaust must not be silently corrected by a whole-image flip.

SAT-relative mapping pixels become terrain-relative through shared presentation
registration (+1,+18). The magenta cross denotes the unchanged gameplay anchor.
Transparent pixels and first-SAT-piece priority are retained. Context images are
constructed from canonical terrain and original renderer results, not emulator
screenshots or proof of whole-game correctness.
The `$25` context runs the original `$77CB` with GPZ1's map/160-cell stride:
placement `(848,334)` projects to runtime `(848,302)` with floor flag2. The
context uses that controlled standing pose; the canonical placement stays334.

## Reproduction and approval gate

```powershell
.venv/Scripts/python.exe tools/gpz_enemy_approval.py ROM.sms
# Use a Python with Pillow installed (the desktop bundled Python was used).
python tools/gpz_enemy_previews.py
$env:SONIC_CHAOS_ROM='ROM.sms'
.venv/Scripts/python.exe tests/test_gpz_enemy_approval.py
.venv/Scripts/python.exe tools/gpz_enemy_approval.py ROM.sms --check
```

The extractor runs without Pillow; its CPU oracle uses the repo's `z80`/
`z80dis` dependencies. Rendering uses Pillow 12.3 locally. No synthetic art or
ImageGen output is used. See `gpz-art-approval-checklist.md` for candidate files,
visual questions and remaining boss rollout gates. Approval does not authorize
an unrequested commit or POC modification in this Research-only turn.
