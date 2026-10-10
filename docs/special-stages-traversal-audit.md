# Special Stages SS-A2 — terrain, tubes and traversal

Unmerged research on `research/special-stages-canonical`. Machine package `data/rom-cache/special-stages/traversal.json`; tool `tools/ss_traversal.py`; test `tests/test_ss_traversal.py`.
Evidence: BYTE-VERIFIED (handlers read and executed), CONTROLLED (original routines under supplied RAM), EMULATED (whole-game, approximate SMS harness).

## 1. There is no Special-Stage-specific terrain code

Every surface type used by the five maps dispatches to a handler that already exists for ordinary zones. Collision headers are global (every zone's `$D2E0` is `$8000`, bank 14), so block ids carry the same collision/surface in a Special Stage as anywhere else.

| Surface | Handler | Role | Stages (cells) | Earlier contract |
|---|---|---|---|---|
| `$00` | `$6C45` | none / decor | all | - |
| `$01` | `$6A5D` | **zone-5 only**; returns when zone != 5 -> inert as solid in all stages | SS2 254, SS3 6, SS4 1317, SS5 26 | eez-environment |
| `$02/$03` | `$6A5B/$6A5C` | plain solid / slope (`RET`) | SS3 2385, SS5 976, SS4 60 | - |
| `$07` | `$6C4D` | terrain rings (probe `$753E`) | SS1 144, SS2 26, SS5 15 | terrain-ring-collection |
| `$09` | `$6A75` | upright terrain spring | SS4 1 | spring-interaction |
| `$0A` | (side cores) | horizontal spring | SS4 16, SS5 1 | spring-interaction |
| `$0C` | `$6B79` | crumble ledge | SS4 11 | sez-surfaces |
| `$0D` | `$6B2C` | breakable block | SS4 41 | mghz-m1 |
| `$13` | `$6D43` | **tube mouth/pipe** | SS3 397, SS5 444 | eez-environment |
| `$14` | `$6A90` | diagonal / ceiling spring; zone != 0 -> Y -5.5 | SS3 73, SS4 5 | spring-interaction |
| `$16` | `$6AE3` | floor break/bounce | SS4 12 | gpz-foundation |
| `$1D` | `$69B1` | no-op (decor-like platform art `$B8`) | SS1 128, SS2 8 | - |

Surface `$01` blocks in SS2/4/5 and `$0B`-dependent behavior of the final zone therefore have **no** effect: these blocks are plain solid cells. Diagonal springs launch with Y -5.5 (zone byte is not 0), exactly like GPZ/MGHZ/SEZ.

## 2. Tubes are the final-zone transport, byte for byte

Maps SS3 and SS5 use blocks `$74..$82` (identical ids and handlers to the final zone), plus `$2B..$2F`/`$D6` cap/decor blocks with horizontal profile 64. The router (`$0C:$91BC` table, common tail `$91DC`) and player state `$21` were proven zone-independent: the original route handlers run under zone byte 8, 9, 10, 11 and 12 across 15,360 inputs each (all 16 route blocks x X in {0,14,31} x Y in {0,14,16,31} x five velocities x all 16 pad values) and every result equals the final-zone model (`eez_transport.model`) — **76,800 checks, 0 mismatches**. The model and its semantics (WORLD snap `(X&~31)+14` / `((Y-16)&~31)+44`; speed 6.0 on one axis; junction blocks `$7A..$7D` read pad bits; `$7E` keeps motion; `$80` returns; the unreachable `$80` rising branch; exit sets `$D373=$0600`, converts rising Vy to -6.5, sound `$BA`) are reused unchanged from `docs/eez-environment-audit.md`; no tube behavior differs per stage.

Entry (EMULATED, SS3 and SS5): Sonic cannot walk into a mouth. The cap column (`$2D` etc., horizontal profile 64, surface flags 0) acts as a wall for a walking Sonic (side probe `D523` bit2, `D521=64`); a **jump** carries him over it onto the mouth block (`$81`, floor probe, WORLD Y mod 32 < 16), which requests `$21` (SS3 update 110, SS5 update 68). Every later routing event of both natural traversals (SS3: 77 handler executions / 30 decisions; SS5: 39 / 20) equals the model's prediction. Leaving the pipe sets the airborne state (`$1B`/`$1C` seen), so rooms are linked by geometry: after the last pipe of a room Sonic drops into the next room's floor and, with no further input, re-enters the next mouth (SS3: the first room-to-room transitions were observed with a single initial jump). Junction choices are decided by held pad bits; with one fixed input the unattended run in SS3 loops in the upper network until timeout (3503 updates).

Ownership/control: while `$21` runs, the callback runs hurt handling, clears hide, sets `$D15F` bit1 and skips the ordinary terrain pass; player input only reaches junction selectors. Collision with enemies/hurt remains the ordinary hurt path (there are no enemies in the stages).

## 3. Camera, EDGE and PLAYER_DIST semantics

- Camera follow lead (`$58E1`): target screen X `$78` (120, CENTER-8) while `$D15F & 3` is non-zero (tube state or pan lock), otherwise `$68` / `$88` (104 / 136) by facing; the lead slews 1 px/update. Classification: **EDGE/CENTER-relative camera, do not widen constants**.
- Tube alignment and routing are **WORLD** (the 32-px grid snaps); route speeds are fixed 6.0 px/update.
- No PLAYER_DIST rule exists in the tube system. Mapped-object lifecycle (the only objects in the maps: `$10`, `$2F`, `$26`, `$31`) uses the generic viewport bands (see SS-A3/A4).
- World limits are the per-stage `D280/D282/D27C/D27E` values of the foundation package (WORLD).

## 4. Update order

Player engine (`$64FA`) -> player callback (state `$21` callback includes its own route/move/terrain tail: route selectors, `$0338` move, `$038C` terrain) -> object scheduler (`$5DD1`) -> frame wait. Routing happens before the move within the same callback; entry (`$6D43`) happens in the *previous* update's terrain pass.

## 5. Unresolved

- Whether a walking player can ever enter a mouth without jumping (no case found; cap column blocks side motion).
- Full per-room unattended routes for SS3/SS5 are part of the natural-completion search in SS-A4.
- Visual approval of the new terrain art (boards, SS-A5).
