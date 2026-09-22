# Turquoise Hill Act 1 springs and retracting spikes

This document records the object handlers recovered for Windows POC 15. File
offsets refer to the supplied ROM revision identified in `docs/provenance.md`.

## Object type `$26`: concealed contact springs

The fixed animation table at `$65BA` selects CPU `$8212` in bank 30 for type
`$26`. The table contains ten object states. Frame zero is the concealed/dormant
presentation; the spring is not a permanently visible map object.

### Initialization and parameters

Handler `$825A` requests state 7 and shifts the object Y anchor down 12 pixels,
saving that position as its retraction limit.

If parameter bit 7 is set, the low seven bits are multiplied by 16 and stored as
a horizontal trigger span. Initialization then requests state 8. Parameter `$8A`
therefore means a 160-pixel concealed span, not merely a weak spring.

### Fixed contact state 7

Handler `$82AF` rejects upward-moving Sonic, missing floor/object contact and
player state `$21`. Its vertical contact window is measured against object Y-28.

| Parameter | Player Y impulse | Extension state | Hold |
|---:|---:|---:|---:|
| `$00` | `-7.375` (`$F8A0`) | 1 | 32 updates |
| nonzero | `-5.0` (`$FB00`) | 3 | 10 updates |

States 1/3 subtract seven from counter `$1E` and move object Y upward seven
pixels while the result is nonnegative. Starting at 28 produces four moves and
a 28-pixel extension. States 2/4 hold; states 5/6 move down seven pixels per
update until the saved base is reached, then restore state 7 or 8.

### Span states 8/9

State 8 (`$83BF`) checks whether Sonic's X lies inside the stored interval. State
9 (`$8401`) aligns the spring X to Sonic on a 16-pixel boundary, applies the same
parameter-selected launch and enters the weak or strong extension sequence.

The four THZ1 records are:

| Position | Parameter | Contract |
|---:|---:|---|
| `(688,864)` | `$00` | fixed strong |
| `(3568,768)` | `$00` | fixed strong |
| `(1296,608)` | `$8A` | 160-pixel concealed span, weak |
| `(1912,864)` | `$01` | fixed weak |

## Object type `$1B`: retracting spikes

The type table selects CPU `$AC4A` in bank 12. State 0 initializes the object,
requests state 1 and clears hit cooldown `$1F`.

| Phase | Original behavior |
|---|---|
| State 1 | Move Y upward 6 pixels per active update; after 18 pixels request state 2 |
| State 2 | Remain raised for script duration `$30`; run damage/contact helper |
| State 3 | Move Y downward 6 pixels per update; at base request state 4 |
| State 4 | Remain hidden for script duration `$30`, then return to state 1 |

Damage checks occur during states 1 and 2, not while retracting or hidden. The
four parameter-zero THZ1 placements are `(1344,864)`, `(1936,864)`, `(2464,864)`
and `(2912,864)`.

## Verification

`reports/windows-poc-15-objects.json` records selected executions of the original
handlers: both launch impulses, both extension paths, retraction, and spike rise
and fall. These isolated comparisons do not emulate the camera object manager,
rendering, damage aftermath or complete SMS scheduler.
