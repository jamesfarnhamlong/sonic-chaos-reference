# Terrain collision

All addresses in this document are CPU addresses in fixed banks 0/1 unless a ROM file offset is explicitly given. Evidence: [recovered assembly](../asm/recovered/), [readable translation](../tools/reference.py), and [differential report](../reports/differential-verification.json).

## Anchors and sensors

Object position has 16 integer bits plus eight fractional bits. Player integer X/Y are `$D511/$D514`. The lookup routine `$7666` adds the supplied offsets, then adds **18 to Y**. Thus the stored Y is not the foot position.

| Query | Offset passed to lookup | Effective probe relative to stored position | Evidence |
|---|---|---|---|
| Ordinary player floor | `(0,0)` | `(X,Y+18)` | `$691A..$694F` |
| Right side | `(+9,-12)` | `(X+9,Y+6)` | `$3686`, `$716B` |
| Left side | `(-9,-12)` | `(X-9,Y+6)` | `$3686`, `$7210` |
| Ceiling | `(0,-24)` | `(X,Y-6)` | `$73C9..$73EF` |

Floor probing has state exceptions: `$21` uses dy=-14 and `$12` uses dy=+8. Side offsets are stored in RAM and should not be treated as immutable; the table describes initialization. The top special-effect query at `$753E` is separate from ordinary ceiling collision.

## Full lookup at `$7666`

1. Preserve the current slot-2 bank and map bank 14.
2. Compute adjusted X and Y; negative adjusted Y is clamped to zero.
3. Calculate the layout address using the row-offset table referenced by `$D168`, then base `$C001`.
4. Reject an address outside `$C000..$CFFF`. The fallback reports tile `$FF` and zero type/profiles. It does not clear the modifier byte `$D100`.
5. Index the collision-header pointer table referenced by `$D2E0`.
6. If header flag bit 5 is set and object `+$25` is nonzero, advance seven bytes to the alternate header.
7. Read the modifier byte; index the first profile by adjusted X & 31, and the second by adjusted Y & 31.
8. Restore the bank.

For THZ the pointer table is CPU `$8000` in bank 14 (file `$38000`). The same pointer value is present in the six normal zones' three act headers examined here. No claim is made about every bonus/special mode.

The first profile is the **vertical projection profile indexed by X**, stored in `$D368`. The second is the **horizontal projection profile indexed by Y**, stored in `$D367`. This naming avoids the ambiguity of “X collision value” in older notes.

The lighter lookup `$7725` reads a base header's surface type but does not perform the alternate-header selection or fetch both profiles. It must not be substituted indiscriminately.

## Update order and previous surface

The shared updater `$3FEF` calls input/modifier handling, X integration `$402A`, Y integration `$4097`, and collision `$690B`. Collision runs:

1. Floor `$691A`.
2. Sides `$715E`.
3. Ceiling `$73C9`.
4. Top special-effect probe `$753E`.
5. Merge contact flags `$64CB`.

Floor processing saves the previous modifier in `$D36A` and clears the current modifier `$D369`. It fetches the current foot tile, then calls `$6F61`. That function tests **the old `$D36C` surface flags**. Only after projection does `$691A` store the newly fetched `$D364` into `$D36C` and dispatch its low five bits through `$6973`.

This distinction is observable in the differential tests. Changing it to “always use the current tile” is a behavior change.

## Ordinary solid projection

The old surface's bit 7 selects the solid path. Upward Y velocity returns without grounding. For a basic sample:

```text
height = raw_vertical & 63
correction = height + (adjusted_y & 31) - 32
if correction >= 0:
    player_y -= correction
    background_contacts |= 2
    current_modifier = sampled_modifier
```

This is a simplified expression of the ordinary branch, not the entire routine. The original uses byte arithmetic, checks an above-tile continuation for height 32, and has a bit-6/type-`$1C` special case. `tools/reference.py` preserves these details for its stated subset.

### Above-tile continuation at `$7056`

When requested, the routine adds the signed negative map width at `$D16A` to the current layout pointer to inspect one row above. It honors alternate collision headers.

- For an above header with bit 7, it can subtract that tile's low-six-bit height directly from player Y and replace the speed modifier.
- For bit 6, it can extend the current vertical sample to `32 + upper_height`. Subtype 9 is excluded.

For example, at the start of the curve the foot query can land in the full block **below** the visible slope. The above-tile correction is what places the player on the actual curved surface. Converting every tile to a separately capped 32-pixel mask loses that relationship.

## One-way projection

Previous surface bit 6 selects this branch if bit 7 is clear. With the ordinary object flags, upward motion returns. It clears the ground-contact bit, then accepts a downward correction only if it is **strictly less than** `unsigned_high_byte(vy) + 9`.

The generic object floor path uses a related threshold of +7. Its behavior must be distinguished from the player's; applying the player's sprite dimensions to enemies can embed or float them.

Object `+$24` bits 0/1 lead to additional paths. They are recovered in assembly but excluded from the current Python projection subset and randomized fixture checks.

## Side projection

The ordinary right/left cores are `$71B2/$7257`. They require surface bit 7. They use `raw_horizontal & 63` as an extent; zero means no side projection. Bit 6 selects the boundary orientation. They project X and set background contact bit 2 (right) or 3 (left). Special tile types dispatch before these ordinary cores.

The next horizontal integration uses those merged side bits to stop velocity in the obstructed direction. This is different from testing Sonic's whole box against all floor polygons before moving.

## Collision planes and breakables

Tiles `$A1/$A2` can change object `+$25` at `$73A7/$73B8`, affecting selection of alternate headers. A plane transition is a rule in the data, not an instruction to make every nearby wall permeable.

Breakable handling exists: `$7857` writes replacement tile `$46`; `$7898` writes `$9D`, refreshes the mapping, and creates fragments. The first-curve problem does not justify inserting breakables. Exact placements must come from the actual map and applicable surface types.
