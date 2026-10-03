# GPZ3 $51 composition correction — approved 2026-10-03

Research only, branch `research/gpz-enemies-art-approval`, canonical base `08fb38c`.
ROM Europe v1.2 verified SHA-256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
User approved the corrected `$51` package and authorized Research commit/push.
No POC edits or handoff; main integration remains separate. Approved `$25`, `$2C`, `$34`, `$0A`,
`$0F` and HUD support visuals are preserved. Old `$51` board is rejected.

## Evidence and correction

The old board was assembled in the **wrong vertical order**. It interpreted
`+$34` as an upper predecessor, put the head on parameter1 and unconditionally
added parameter4. ROM linker `$1E:$A141` (file `$7A141`) proves the opposite:
upper object's `+$34` = lower support; lower object's `+$36` = upper predecessor.
Routine `$9E4B` (file `$79E4B`) positions the upper object from that lower object.
There was no missing middle-ball graphic; the wrong object/link assignments and
extra fourth ball created the erroneous silhouette. Landing dust `$51/$11`
was missing as a runtime child and misclassified as table-only art.

**Original-game observation:** supplied recording
`Screen Recording 2026-10-03 131035.mp4` (11.5 seconds) was decoded and visually
checked at 1,3,5,6,7,9 seconds. Respectively: head+3, head+2, head+1, head-only
with a detached ball overhead, regrowth from below the floor, restored head+3.
Video SHA and observations are retained in the composition cache. The clip
supports normal three-ball composition; it does not establish mode2 presentation.

**Controlled original scheduler:** execute `$5DD1` over its 19 object slots with
the canonical mapped record at `$1C:$8DF6` / file `$70DF6`. Original allocator,
animation state changes and callbacks run, including delayed child creation.
Camera `(1664,96)`, static player X1500, Y64/160/256 select modes0/1/2. A separate
X2200 run verifies rightward detachment. This is not full-game CPU/VDP/IRQ replay
and ticks are not synchronized to the supplied recording. No contact/health/
clear certification follows from these controlled composition fixtures.

## Exact starting composition and registration

| Top to bottom | Type / parameter | Normal visual | Link |
|---|---|---|---|
| Head/controller | `$51/$00` | state7 frame2; hit frame1 | supports from ball1 |
| Upper ball | `$51/$01` | state6 frames3..9 | supports from ball2 |
| Middle ball | `$51/$02` | state6 frames3..9 | supports from ball3 |
| Bottom ball | `$51/$03` | states8 then10, frames3..9 | floor-driven; no lower support |
| Mode2 extra bottom | `$51/$04` | states8 then10, frames3..9 | only when mode2; ball3 follows it |

Canonical placement is `(1728,270)`; init moves controller X to1856. Setup
creates children at successive dy+32: `(1856,302)`, `(1856,334)`, `(1856,366)`
and, mode2 only, `(1856,398)`. These positions are initially below the floor.
The bottom rises at -1 px/update to gameplay Y270 (`$10E`), carrying the stack
through its signed sway table and the original sequential update order.

The first settled mode1 fixture, tick232, has anchors:
head `(1868,180)` frame2; ball1 `(1863,209)` frame7;
ball2 `(1859,239)` frame7; ball3 `(1856,270)` frame3.
The head anchor is 90 px above the bottom here. Its complete opaque silhouette
occupies terrain X1846..1879 and Y166..286 inclusive: **34 x121 pixels**.
This is the exact illustrated pose, not a universal fixed-height box. Phase sway
and sequential updates vary the offsets; do not replace them with rigid 32px gaps.
Head mapping bounds are X-12..+11, Y-32..-1 before transparency; six 8x16 SAT pieces.
All ball mappings likewise use six pieces. Dust uses one piece.

Shared art registration remains terrain-space `(+1,+18)` from each gameplay
anchor, independent of collision. Original 256x192 context uses background
origin camera+(1,17) = `(1665,113)`, consistent with the hardware SAT +1 row.
This keeps the orange floor in view and the boss correctly registered to it.
Opaque priority terrain pixels are composited over sprites. Transparent deck
openings can reveal fragments of below-floor balls during regrowth; the
unclipped diagnostic deliberately shows all allocated slots.
Transparent frame PNGs use canvas128x112 and anchor `(64,56)` **before** the
terrain presentation offset. Magenta crosses mark gameplay anchors; yellow line
in the unclipped regrowth diagnostic is terrain floor Y288. Never move canonical
placement/collision to match the diagnostic canvas.

Mode selector `$9A99` uses `(playerY_low -16) mod256`: low Y16..143 =>mode0,
144..239 =>mode1, 240..255 or0..15 =>mode2. Initial health5/8/10 accompanies those
selections. `$9B91` requests state6 instead of finishing state4 in modes0/1,
thereby skipping parameter4. All 256 initializer low bytes and spawn gates are
checked through original code. Mode2 has four balls; it is separately labelled
and must not be mistaken for the normal form in this clip.

## Throw, shrink and regrow

The **existing bottom ball** detaches. No substitute projectile child is spawned
for it. Normal throw order is parameters3 ->2 ->1; mode2 begins with4. Odd
parameters arc (states19/20); even parameters slide (11/15). Left/right selects
motion state, with the same bit4=0 graphics, not a bitmap flip. Arc launch speed
is X±1.5, Y-4.5; gravity+0.125, floor bounce Y-4.0. These are source/scheduler facts,
not a complete contact specification.

| Mode1 fixture tick | Result |
|---:|---|
| 332/333 | ball3 requests/enters19 and launches left; attached head+2 |
| 334/335 | ball2 detects detached lower support and enters9, falling toY270 |
| 356/357 | ball2 lands; new dust child enters18; ball2 becomes bottom state10 |
| 446/447 | ball2 requests/enters11, slides left; attached head+1 |
| 470/471 | ball1 lands atY270, emits dust, becomes bottom |
| 578/579 | ball1 requests/enters19; attached head-only |
| 580/581 | head detects lost support and enters12, falling |
| 601 | head reachesY270 and requests1, starting a fresh spawn chain |
| 602..606 | create parameters1,2,3 in that order below floor; mode0/1 skips4 |
| 607..704 | new bottom rises; remaining linked objects follow upward; full stack restored |

Detached balls can remain alive during regrowth. At tick602 there are **two
parameter1 slots**: the old thrown ball and the new upper ball. Follow live slot
links, not parameter counts, to determine attached composition. Retain detached
attack objects independently until their original removal path runs.

Dust is a new `$51/$11` child (parameter17 decimal). Floor callback `$9F14`
installs script pointer `$9C0F` (file `$79C0F`); that tail spawns it at dx+10,dy0.
Initializer `$9AE0` requests `parameter+1`, therefore state18. State18 `$9DBE`
uses frames10/11 with three-update records and repeat control, then deletes via
`$9DB9`. Both frames occur in scheduler replay in all three modes. These are
landing/regrowth support art, **not extra stack balls** or unused table entries.

## Frame and approval checklist

| Frames | Canonical role | Evidence |
|---|---|---|
| 0 | blank init/controller record | source/script + scheduler |
| 1 | head hit/reaction state13 | source-traced state7 contact ->13; not independently seen in selected video samples |
| 2 | normal head | scheduler + visual comparison |
| 3..9 | attached/detached ball rotations | scheduler + visual comparison |
| 10/11 | `$51/$11` landing dust, state18 | callback-installed spawn + scheduler |

12 mapping entries, **11 nonblank canonical frames**. No remaining frame is
classified solely as an unresolved table/script reference. Frame1's evidence is
source-traced; do not mislabel it video-observed. No runtime horizontal mirror:
bit4=0, shared art for both throw directions. Forced mirrors from the original
package are excluded. Palette `$0D`, dynamic selector `$14`, boss tiles104 at
VRAM `$05C0`; supporting puff tiles12 at `$12C0`. Existing `$12/$34/$0A` support
dependencies remain as previously audited and approved.

Approval granted for corrected boss art/composition and newly identified
runtime dust use on 2026-10-03. Approved boards: `51-sequence-context.png`, `51-stack-registration.png`,
`51-sequence-summary.png`, `51-composed-registration.png`, `51-raw-tiles.png`,
`51-mode-direction.png`.
The normal board must show head+3 ->head+2 ->head+1 ->head-only ->regrow ->head+3,
with complete middle balls, consistent blue/yellow/orange colors and floor
registration. Mode2 and rightward movement are separately labelled diagnostics.
The prior boss composition is superseded. A POC handoff still requires a separate
implementation instruction; art approval does not certify the remaining boss runtime gates.

## Reproduction and remaining scope

Run Python from the Research workspace, preserving local-only ROM/art:

```text
.venv/Scripts/python.exe tools/gpz_enemy_approval.py build/task08-verify-final/input.sms
.venv/Scripts/python.exe tools/gpz51_composition.py build/task08-verify-final/input.sms
<Pillow-capable Python> tools/gpz51_previews.py
.venv/Scripts/python.exe tools/gpz_approval_manifest.py --check
```

Only the Pillow command writes corrected `$51` PNGs in ignored
`build/gpz51-correction/`; approved sibling PNGs are not regenerated. Original
rejected boss board remains available as history. Each corrected image has a
hash and size in `png-manifest.json`. Original approved PNG hashes are checked
against their retained manifest. Focused tests cover pointer order, normal/mode2
counts, throws/shrink/regrowth, duplicate-parameter slots, live dust, 256 mode
boundaries and both-direction scheduler regeneration. Full boss contact/health/
arena/defeat/clear implementation remains a separate bounded research gate.
