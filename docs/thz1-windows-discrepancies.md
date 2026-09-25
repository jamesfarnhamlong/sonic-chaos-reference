# THZ1 Windows-discrepancy audit

## Scope and revisions

This audit is limited to the four POC 18.4 Windows findings. Reference input
was `918b39b5f996ff9bfd553415e1319e5cb8c88d59`; the read-only POC input was
`acf154b76b2145099c7c9155c280b660b96299ca`. The canonical ROM SHA-256 is
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.

## 1. Type `$10` vertical presentation — CANONICAL

The placement creator `$80EB` (ROM `$700EB`) copies record Y directly to
object integer Y `+$14/+$15`. Initializer `$A149` does not change Y. Generic
pre-render `$3FC8` writes `object_y-camera_y` to `+$1C/+$1D`. Renderer `$226A`
adds each signed mapping-piece Y to that screen anchor and writes the result
to the VDP SAT. SMS sprite display begins on SAT-Y plus one; the frame `$0B/$0C`
pieces therefore occupy exact world scanlines `object_y-24..object_y+7`.
There is no generic or type-specific settling adjustment.

The relevant decoded collision surface is not the apparent bottom of every
foreground pixel reported from the flattened POC image.

| Placement (parameter) | Relevant surface | ROM sprite top..bottom | Empty rows before surface | Evidence |
|---|---:|---:|---:|---|
| `(656,846)` (`$06`) | 864 | 822..853 | 10 | placement/create trace + `$226A` + collision header |
| `(1712,494)` (`$06`) | 512 | 470..501 | 10 | same |
| `(336,270)` (`$04`) | 288 | 246..277 | 10 | same; POC apparent surface near 304 is not collision Y |
| `(1472,110)` (`$04`) | 128 | 86..117 | 10 | same; POC apparent surface near 144 is not collision Y |
| `(2688,686)` (`$02`) | 864 below | 662..693 | 170 | same; intentionally suspended placement |

Thus the reported air beneath the two `$04` objects is original. Do not move
their coordinates. POC 18.4's 40-pixel canvas/Y-origin 28 is compatible only
because its four transparent top rows leave the first visible pixel at -24;
the implementation must preserve that transparency and draw at canonical Y.

## 2. Parameter `$04` / player state `$11` — contract complete

The implementation contract and controlled fixtures are in
`player-state-11.md` and `windows-discrepancies.json`. In short: entry zeroes
velocity, sets maximum `$0700`, timer 300 in ordinary THZ1, sound `$85`, and
state `$11`; frames `$38,$39,$3A,$39` loop; vertical input accelerates Y by
`$0040` to ±`$0400`, no vertical input decelerates Y by `$0020`; horizontal
input remains on the shared movement path with maximum `$0700`; shared movement
and terrain collision remain active; jump/roll controls are suppressed; timer
expiry restores level music and requests falling state `$0E`. Shared damage
has an explicit state-`$11` cancellation branch and requests hurt state `$1E`.

POC 18.4 only writes the numeric reward globals and never implements this
state. That omission is the direct cause of the retained rolling presentation.

## 3. Fixed terrain spikes — POC BUG, but upper traversal is canonical

All four cells `(1504,832)`, `(1536,832)`, `(2208,832)`, `(2240,832)` are
layout block `$3D`. Plane-zero collision header ROM `$383AB` is flags `$85`
(solid bit 7 plus floor-handler type 5), modifier zero, vertical profile
`16 × 32`, and horizontal profile `[$40 × 16, $60 × 16]`. There is no separate
ceiling profile; the vertical profile is reused by the ceiling lookup, subject
to the ordinary ceiling routine and flags.

This means:

- the floor is flat at world Y 848 across each cell;
- local Y 0..15 has horizontal extent zero and does not side-block;
- local Y 16..31 is a full-width solid side wall;
- floor projection runs before the low-five-bit handler;
- handler `$6ACE` damages only when background floor-contact bit `+$22.1` is
  set, except protected/shared cancellation cases;
- side, underside and diagonal overlap alone do not request spike damage;
- a falling contact that is projected onto Y 848 sets floor contact and then
  requests damage; exact misses one pixel above/outside do not;
- horizontal or shallow diagonal travel may legitimately cross the visible
  upper half. It is neither a full-graphic damage box nor a full-height wall.

The controlled lookup matrix tests all four exact cells at local X
`0,1,15,16,30,31` and local Y `14,15,16,17,30,31`. The existing type `$1B`
object code is independent and unchanged.

POC 18.4 has two competing approximations: the core header adapter carries the
ROM profile/hazard flag, but each `$3D` cell is also an invisible solid
`OBJ_CHAOS_mask_12` with a full 32×32 mask. The latter is not canonical and
can make approach behavior depend on which collision path wins. POC 18.5
should remove/bypass that full-cell mask for THZ1 and use only the decoded
profile: side-solid lower 16 pixels, floor hazard at Y 848.

## 4. Type `$21` contact — POC BUG at the adapter boundary

For ordinary THZ1 Sonic fields, player extents are X 9 and Y 18; type `$21`
uses X 11 and Y 26. `$6328` compares integer anchors, not sprite pixels:

```text
abs(player_x-object_x) <= 20
object_y-26 <= player_y <= object_y+18
```

Equality is contact; one pixel beyond is not. The helper sets directional bits
in object `+$21`, retaining the axis of least penetration, but type `$21`
tests only whether the low nibble is nonzero. It does not require a top bit.
After overlap, its local classification is exactly:

1. if `player_y <= object_y-4`, bounce with state `$0B`, Y velocity `$F940`,
   airborne set, rolling/floor contact cleared, sound `$A6`;
2. otherwise, attack flag `$D503.1` or selector `$06` defeats/converts it;
3. otherwise write `$FF` to damage request `$D3B0`.

Consequences: a clean top and a shallow top/side diagonal anywhere inside the
20-pixel horizontal boundary bounce; rolling from above also bounces because
the top branch precedes attack. At Y offsets -3 through +18, ordinary contact
damages, rolling attack defeats, and selector `$06` defeats. Contact from
underneath is included only through offset +18. Type `$21` is **not solid**:
neither `$6328` nor the local handler projects, pushes or stops Sonic. Ordinary
damaging side contact merely queues shared player damage; any later knockback
belongs to that player-damage system.

POC 18.4 substitutes animated GameMaker `bbox_*` values and `cp_p.y` for the
ROM integer anchor/extents. That can enlarge or shift overlap and the `-4`
split as sprites/origins change. POC 18.5 must use the chaos-core integer
anchor with fixed 9/18 extents and the inequalities above. It may ignore the
helper's direction bits for behavior, exactly as the ROM type `$21` callback
does.

## Implementation answers

- Type `$10` floating: **CANONICAL**.
- Parameter `$04` / state `$11`: implementation-ready contract **YES**.
- Static spike diagonal collision: **POC BUG** (full-cell mask); upper-half
  traversal without damage is canonical.
- Type `$21` contact: **POC BUG** (bbox/anchor approximation); the ROM's broad
  shallow-top bounce itself is canonical.

The POC remains read-only in this task and THZ1 should not be called complete
until state `$11` and both adapter corrections are integrated and retested.
