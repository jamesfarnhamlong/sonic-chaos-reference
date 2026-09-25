# Player state `$11`

This is the bounded THZ1 implementation contract for the state requested by
type `$10` parameter `$04`. Numeric names are retained. Evidence is the
canonical ROM, recovered regions, and controlled original-routine fixtures in
`windows-discrepancies.json`.

## Entry and animation

The setter at fixed CPU `$4775` zeroes both velocities, writes maximum
horizontal speed `$0700` to `$D373`, selects sound `$85` and timer `$012C` in
ordinary THZ1, copies the timer to `$D3A1`, clears player flag bits 1 and 6,
and requests state `$11`. Level `$08` instead uses `$1770` and skips sound
`$85`.

State `$11` is script CPU `$8334` / ROM `$30334`:

| Duration | Frame | Callback |
|---:|---:|---:|
| 8 | `$38` | `$03C2` → `$3A7C` |
| 4 | `$39` | same |
| 8 | `$3A` | same |
| 4 | `$39` | same |

`FF 00` repeats the four records. No roll or jump script is entered.

## Per-update contract

`$3A7C` clears presentation flag `+$04.7`, adjusts Y velocity, applies the
vertical screen-bound helper, updates facing, calls the ordinary shared
movement/collision path, handles grounded correction, and tests the active
timer `$D44C`.

- neither vertical direction: Y velocity moves toward zero by `$0020` per callback;
- input bit 0: subtract `$0040` from Y velocity, clamped at `-$0400`;
- input bit 1: add `$0040` to Y velocity, clamped at `+$0400`;
- horizontal movement remains the ordinary shared movement path, bounded by
  `$D373=$0700`; normal left/right input therefore remains effective;
- direction updates facing through `$48A7`;
- shared movement and terrain projection remain active;
- normal jump and roll controls are suppressed: this callback has no jump or
  roll-input path;
- while `$D44C` is nonzero state `$11` continues;
- at zero, `$189B` restores the level music request and `$463C` requests
  falling state `$0E`, sets Y velocity `+$0100`, and marks airborne.

`$D3A1` is the duration copy written on entry; state `$11` itself reads
`$D44C`, not `$D3A1`. A damage request reaches shared handler `$48BC`. Its
state-`$11` branch clears `$D532`, clears queued reward bit 3, restores music,
and proceeds to shared hurt state `$1E`; selector `$06` suppresses damage in
the shared precheck. There is no state-local sound after entry except the
music restoration/cancellation paths.

The controlled fixtures cover the shared entry path, neutral/up/down vertical
acceleration, both clamps, ordinary continuation, timer expiry, and the
source-traced state-specific damage cancellation. They are subroutine traces,
not emulator gameplay observations.
