> Historical release 01 report. Paths and commands below describe that earlier package. Use the current [README](../README.md) and [corrections](findings.md) for this release.

# Sonic Chaos SMS — disassembly continuation 01

A focused continuation of RF / Amber Davis's partial Sonic Chaos disassembly, using the supplied SMS ROM. Original author credits remain in the source. This package is research source and decoded data for the Windows POC; it is **not a new GameMaker build**.

## What was completed

- Recovered 2,447 bytes of previously opaque code as 1,067 Z80 instructions: spring state changes and contact handlers, three loop paths and their entry states, moving-platform behavior, and twisting-strip entry/dispatch.
- Added descriptive entry labels and comments without changing the original instructions.
- Decoded all 53 Turquoise Hill Act 1 object records, including the six platform placements.
- Exported three original loop lookup paths to CSV.
- Built the supplied original source with WLA-DX, then built the recovered source. Both outputs matched the supplied 524,288-byte ROM byte-for-byte. The packaged build script was also exercised successfully.

**What this validation establishes:** the new assembly reconstructs the original bytes. It does not prove every semantic annotation or a GameMaker translation, and does not constitute emulator or Windows gameplay testing.

## Confirmed findings

### Object placement coordinates

The loader at file `$700EB` copies each coordinate's low byte, then decrements the high byte. Consequently, both stored coordinates contain a `$0100` bias:

```
world_x = (stored_x - 256) & 65535
world_y = (stored_y - 256) & 65535
```

THZ1 begins at file `$705AE`; each record is nine bytes. There are 53 records followed by `$FF` at `$7078B`.

| Record bytes | Loaded meaning |
|---|---|
| 0 | Object type, object+$00 |
| 1–2 | X, subtract 256; copied to current and saved position |
| 3–4 | Y, subtract 256; copied to current and saved position |
| 5 | Initial flags; loader also sets bit 6 |
| 6 | Object parameter, object+$3F |
| 7 | Object+$08; interpretation depends on type |
| 8 | Object+$09; interpretation depends on type |

Bytes 7–8 should not be assumed to form a function pointer. Platform initialization uses byte 8 as a travel counter. Prior POC notes containing unadjusted X/Y need this correction before using those records as placements. This does not, by itself, explain the POC's independently placed test enemies.

### The initial lift

The user-supplied original-game clip confirms that the first upper route uses a rising platform. The ROM's type `$28` platform code provides the mechanics:

| World X | World Y | Parameter | Decoded behavior |
|---:|---:|---:|---|
| 592 | 464 | `$0A` | Starts upward at 1 pixel per active update; reverses every 144 updates |
| 3664 | 512 | `$0A` | Starts upward at 1 pixel per active update; reverses every 208 updates |
| 1040 | 384 | `$84` | Stationary base position with rider-triggered sag/bob behavior |
| 1136 | 320 | `$84` | Same |
| 1232 | 256 | `$84` | Same |
| 1328 | 208 | `$84` | Same |

For parameter `$0A`, initialization selects state `$0B`. Its sequence sets Y velocity to `$FF00` (-1.0), then calls `$86DA` in bank 30. The counter at `$8925` reverses velocity every `16 * record_byte_8` updates through `$80F1`. Continuous active motion therefore spans Y=320..464 for the first lift and Y=304..512 for the second. Camera activation/despawning can affect when a lift starts; these figures are not a global level timer.

Rider handling at `$88A0` sets the player's Y relative to the platform top and adds the platform's horizontal delta to player X. A moving graphic without this support logic will not reproduce the behavior. The `$84` platforms have an eight-pixel sag/bob limit; the complete recovered code is included rather than substituting a guessed sinusoid.

### Springs

These values are original signed 8.8 fixed-point velocities, in original pixels per update.

| Contact | Launch velocity | Requested player state |
|---|---|---|
| Upright terrain spring, `$6A75` | Y=-7.5 | `$0B` |
| Diagonal terrain spring in THZ, `$6A90` | X=+4 or -4; Y=-7 | `$1C` |
| Same diagonal handler in other levels | X=+4 or -4; Y=-5.5 | `$1C` |
| Horizontal spring facing right, `$72B0` | X=+6 | `$09` |
| Horizontal spring facing left, `$720A` | X=-6 | `$09` |

The upright and diagonal handlers reject certain player states/contact conditions; their state setters also reject an already-upward Y velocity. The diagonal handler sets facing and horizontal velocity explicitly. The horizontal setters write the original maximum-speed field `$D373`, which affects what happens after launch. They do not merely apply a brief visual spring effect.

**Porting consequence:** do not copy these numbers into a POC with different gravity, speed caps and update timing. Translate the state behavior, then calibrate the units consistently. The first upper platform is not evidence that its spring needs a stronger launch.

### Loops

The player traverses explicit position tables in bank 13. This is a dedicated movement state, beyond ordinary floor-height collision.

| Routine (file/CPU) | Y table (file) | X table (file) | Exit cursor threshold |
|---|---|---|---|
| `$3C1B`, rightward path | `$34000` | `$34398` | `$180` |
| `$3DAE`, leftward path | `$346AE` | `$34A46` | `$180` |
| `$3CFC`, alternate exit | `$34DDC` | `$35140` | `$1A0` |

A three-byte cursor at `$D39D..$D39F` accumulates horizontal speed with eight fractional bits. Its integer portion indexes signed 16-bit X/Y offsets, added to a saved entry origin. Before cursor `$90`, speed magnitude decreases by `$000A` per update; afterward it increases by `$000C`. The routines include low-speed falloff and distinct exit behavior.

Entry code at `$3EAB` snaps X to a 32-pixel boundary, snaps Y to a 32-pixel boundary plus 4, saves the origin, and clears the cursor. Leftward entry adds 32 to X before using that common setup. Contact handlers at `$6CBA/$6CCD` check direction/contact flags and previous tile IDs `$52/$51/$57` before entry. Exact POC trigger placement still needs mapping to the level's tile transitions.

The CSVs contain samples from index zero through each exit threshold. The original reads position before checking the threshold, so a fast step can read beyond it. These CSVs are **not complete backing arrays** or ready-to-drop-in movement scripts. Preserve that overshoot behavior when extracting the full tables for an implementation. The alternate-exit path's precise level usage remains to be verified.

### Twisting strip / “Möbius” section

Collision flag `$17` dispatches to `$6E56`. That handler recognizes directional entry tiles and requests player state `$22`.

- Rightward entry checks tiles `$59` or `$5C`. In THZ it requires X speed at least +3.0.
- Leftward entry checks tiles `$73`, `$72`, or `$6B`, requiring X speed strictly less than -3.0.
- Only selected existing player states may enter.
- State `$22` dispatch at file `$314C1` uses the direction variant in object+$38 and the current tile ID minus `$58` to select a movement handler.
- It continues while the relevant collision flag remains `$17`; otherwise it requests rolling state `$09`.

Entry and dispatch code are recovered here. The full per-tile direction/speed handlers and angle-to-velocity calculation remain to be annotated and translated. Artwork-based collision contours alone omit this state machine.

## Scope for the next Windows POC

1. Add the decoded platforms with their travel counters and explicit rider support. Check the first lift against the supplied clip.
2. Map loop entry tiles and implement the original path cursor, falloff and exits. Replace the temporary loop bypass only when this is working.
3. Complete the twisting-strip per-tile handlers and movement conversion.
4. Translate spring states and speed limits consistently with player gravity/input. Verify both directions and nearby contacts.
5. Use the corrected object coordinates to replace placeholder enemy placements after confirming each object type and sprite origin.

The supplied map corrects the earlier breakable-block hypothesis: do not add breakables to those solid sections. Walkthrough monitor passages and the spring near the far lower-right route should be checked against the actual tile/object data. That spring's exact POC placement is not claimed fixed by this package.

## Files and reproduction

- `overlay/`: replacement assembly files and new `research/*.asm` includes. All other original source/binary inputs are required from the supplied disassembly.
- `decoded/`: corrected object records, platform parameters and loop path samples.
- `source_ranges.json`: precise recovered file ranges and instruction counts.
- `verification.json`: successful packaged rebuild result.
- `export_data.py`: standard-library-only exporter; rejects a different ROM hash.
- `build_check.py`: copies the original tree into a new directory, applies the overlay, builds it and compares every byte.

With Python 3 and WLA-DX installed:

```sh
python build_check.py "/path/to/original/Sonic Chaos" --output research-build
python export_data.py "/path/to/original/Sonic Chaos/SonicChaos.sms" --output decoded
```

If WLA-DX is not on PATH, supply `--wla-z80 /path/to/wla-z80 --wlalink /path/to/wlalink`. The output directory must not already exist and must be outside the original source directory. On Windows use the `.exe` paths. The script preserves the original source tree.

Tested with WLA-DX 5.24a on Linux. Modern linker options are passed separately (`-r -s`), unlike the original old batch file's combined `-rs`. Generated source keeps absolute layout intentionally; future edits that change instruction lengths will require converting remaining numeric addresses to relocated labels.

Research ROM SHA-256:
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`

Original-game video and map supplied by the user were used for visual comparison. ROM behavior findings above come from the supplied Chaos code itself; similar Sonic 2 routines are supporting navigation aids, not substitutes for Chaos evidence.
