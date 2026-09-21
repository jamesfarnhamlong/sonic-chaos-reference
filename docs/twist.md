# Twisting strip / “Möbius” section

Recovered code: bank 12 CPU `$94C1..$9829` (file `$314C1..$31829`), plus entry code `$6E56..$6F60` and the shared vector math `$6089/$60FB`.

## Entry

The previous continuation recovered the type `$17` contact handler. In THZ, rightward entry requires X velocity at least +3.0 and a recognized entry tile (`$59/$5C`). Leftward entry recognizes `$73/$72/$6B` and requires velocity strictly below -3.0. Current-state eligibility is also tested.

Entry requests state `$22`. It calculates the magnitude byte by shifting the absolute 8.8 X velocity left five times and storing the high byte. Thus it is approximately `abs(speed_pixels) * 32`, with the original 16-bit wrapping retained. Angle is `$40` rightward or `$C0` leftward; variant is 0 or 1 in THZ. Level index 3 selects variants 2 or 3.

## Dispatch

`$94C1` checks damage, updates floor contact, and continues only while the current surface type AND `$3F` equals `$17`. It selects one of four tables with `object+$38 & 3`, then selects the handler using `tile_id - $58`.

| Variant | Table CPU address | Entries | Tile range |
|---:|---|---:|---|
| 0 | `$94FD` | 28 | `$58..$73` |
| 1 | `$9535` | 28 | `$58..$73` |
| 2 | `$956D` | 28 | `$58..$73` |
| 3 | `$95A5` | 28 | `$58..$73` |

Every mapping is in [twist-dispatch.csv](../data/twist-dispatch.csv). Individual handlers set angle, sometimes change magnitude, and can align X/Y to tile-relative positions. Exiting the special surface clears angle/magnitude and requests rolling state `$09`.

## Movement

After the tile handler, `$95DD` calls vector `$036E` → `$6089`, then `$0338` → `$60FB`.

```text
vx_8_8 = arithmetic_shift_right(signed_table[angle] * magnitude, 4)
vy_8_8 = arithmetic_shift_right(signed_table[(angle + 192) & 255] * magnitude, 4)
```

The signed byte table is at file/CPU `$0200`. Both positions are then integrated with retained fractional bytes. Differential tests cover all 256 angles at eight magnitudes, including zero and 255.

This explains why ordinary slope following made Sonic glide across the strip. The original has explicit angle-driven movement and tile alignment, not just a change in sprite rotation.

## Preserve what the instructions actually do

- `$974D` immediately returns. The two increments after it are not executed by a call to `$974D`.
- `$9772` also immediately returns. The subtraction/falloff code after it is not executed by calls to that entry.
- `$9755` decrements magnitude and may select variant 2 below `$10`.
- `$9763` increases magnitude by two below `$A0`.
- Some table entries reach an `LD ($0000),A` instruction and then fall through. The harness ignores writes to ROM, as hardware would. The purpose of those entries remains unconfirmed; they are not replaced with invented behavior.

The dispatch tables and instructions are byte-verified; vector conversion is CPU-tested. A complete traversal of all four variants, including animation scheduling and camera/activation behavior, still requires gameplay tracing.
