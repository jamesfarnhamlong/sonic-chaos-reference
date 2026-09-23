# Turquoise Hill object type `$27`

This note separates verified behavior from semantic naming. Type `$27` is a
flying object with coherent ROM-derived frames, but no canonical enemy name is
claimed here.

## Verified data chain

- THZ1 object records: ROM `$7067D`, `$70686`, `$7068F`.
- World positions: `(3504,224)`, `(2288,768)`, `(2240,112)`.
- Record fields: flag `$10`, parameter `$00`, art bases `$AA/$AA`.
- Mapping table: CPU `$91F5`, ROM `$3D1F5`.
- Object-specific frame records: `$91FB`, `$9206`.
- Animation state table: bank-30 CPU `$8947`, ROM `$78947`.
- Handler range: ROM `$7898E..$78A44`.

## State behavior

| State | Behavior |
|---:|---|
| 0 | Initialize; parameter zero requests state 1, X velocity `-$2.5`, Y velocity zero. |
| 1 | Alternate frames 1/2 and move left; enter state 2 inside 64 horizontal pixels of Sonic. |
| 2 | Stop X; counter `$80`; callbacks adjust signed 8.8 Y velocity by `+$0003` or `-$0003` according to the script loops. |
| 3 | Restore `-$2.5` X movement; remove at horizontal distance `$0180` or greater. |

The `$80` counter changes state on the underflow update, so a direct port runs
129 handler updates from initial value `$80` through zero.

## Limits

The recovered callbacks call shared player-contact and position-integration
routines. This note does not claim full scheduler timing, camera object-manager
behavior, or a canonical enemy name. Those are separate validation layers.
