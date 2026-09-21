# Data formats and exported indexes

## Collision headers

Pointer table: file `$38000`, 256 little-endian CPU pointers in bank 14. Convert a pointer to a file offset by adding `$30000`.

| Header offset | Size | Interpretation |
|---:|---:|---|
| +0 | 1 | Surface flags/type |
| +1 | 1 | Byte offset into speed-modifier table `$459D` |
| +2 | 2 | Vertical-profile pointer; index with adjusted X & 31 |
| +4 | 2 | Horizontal-profile pointer; index with adjusted Y & 31 |
| +6 | 1 | Trailing metadata byte; purpose not established by this lookup |

The low five surface bits dispatch tile behavior. Bits 7/6 distinguish major projection paths. Bit 5 permits an alternate header at +7 when object `+$25` is nonzero. The 256 base entries yield 16 alternate headers here. Pointers can alias the same profile; do not assume unique arrays per tile.

`data/thz-collision-headers.json` contains raw values, not capped mask heights. `thz-collision-index.csv` provides a compact index with file offsets. The trailing byte is exported without an invented name.

The six normal zone/act header chains examined via the table at `$2A9A` all supply collision-table pointer `$8000`. Their 18 results are exported in `zone-collision-pointers.csv`.

## Level layout and the 4095-cell boundary

THZ1's compressed stream begins at file `$48000`. A non-`$FF` byte is literal. `$FF,value,count` repeats a byte; count zero ends the stream.

Decoding all the way to its terminator yields 4096 cells. **The original loader does not write all of them.** It starts at RAM `$C001`, checks the destination before every literal and every repeated byte, and stops when it reaches `$D000`. Thus the runtime layout has 4095 cells. The final possible grid cell is outside the collision lookup's valid RAM region.

This was verified by executing the original loop `$4DC4..$4DFA`, stopping at `$4DFB`, and checking that `$D000` remains untouched. The exporter reproduces the bounded result. Do not append an arbitrary solid or empty block to the runtime layout and call it ROM data.

Rows use 128 cells in THZ1. The full lookup derives addresses from the actual row-offset table at `$D168`; the CPU harness supplies an equivalent table at an unused RAM address. The helper is not intended to assume 128 columns for every level.

## Object placements and paths

The original continuation's exporter is retained in `tools/export_legacy.py`. It exports all 53 THZ1 records from file `$705AE` to the `$FF` terminator at `$7078B`.

Each record is nine bytes. X/Y words have a `$0100` bias which the loader removes. The parameter and final two bytes are object-specific. They must not universally be interpreted as pointers. Six platform records are decoded with their established movement parameters.

The three loop CSVs preserve the earlier documented ranges through their exit cursor thresholds. The original can overshoot before testing exit; those CSVs are not asserted to contain every possible overshoot sample. See [the earlier continuation](continuation-01.md) and the current recovered loop code.

## Movement tables

`movement-tables.csv` contains six arrays of 32 state entries, each with two signed 16-bit values. Their branch usage is described in [movement.md](movement.md). `surface-modifiers.csv` contains 11 signed increments indexed by an even byte offset from `$459D`.

`sonic-state-scripts.csv` exports the 61 pointers in the Sonic state table beginning at file `$30000`. These point to animation/state command streams, not necessarily machine-code functions.

## Sound pointer index

All 68 offsets supplied in the conversation were independently matched to the ROM table at file `$090E1`, IDs `$81..$C4`. In this table, `file_offset = stored_address + $4000`. The table ends immediately before the first indexed header at `$09169`.

`sound-index-sms.csv` records each ID, pointer location, stored address, resolved file offset, and first header word. The `$A0` music/SFX boundary is retained as **reported classification**; the pointer values themselves are verified. Track names, playback duration, instrument decoding and audio conversion have not been established by this export. Game Gear offsets were not checked against a Game Gear ROM.
