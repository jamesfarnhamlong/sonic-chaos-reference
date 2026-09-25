# Player state `$11` normal-Sonic graphics

This result applies to the 524,288-byte ROM with SHA-256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
It follows the generic player animation resolver at CPU `$64FA`, the normal-
Sonic mapping table, the interrupt-side player tile loader, and the ordinary
SAT renderer. No screenshot was used as evidence.

## Result — IMPLEMENTATION READY

State `$11` uses three distinct visible frames. The script at CPU `$8334` (ROM
`$30334`) schedules `8×$38, 4×$39, 8×$3A, 4×$39`. Normal Sonic is object type
`$01`; the bank-`$0F` pointer at ROM `$3C002` selects mapping table CPU `$80C8`
/ ROM `$3C0C8`.

| Frame | Mapping CPU / ROM | Tile source bank:CPU / ROM | Tile SHA-256 | RGBA SHA-256 |
|---:|---|---|---|---|
| `$38` | `$83E9` / `$3C3E9` | `$05:$9980` / `$15980` | `a8770f3fc6d2f5b39c13581c2da4822047a5a2ed33c13a23afe958c59a9ec313` | `39007e36a7ec3e9888df5919d824667da84a4c0fdbf79cca6971ba03b7976c41` |
| `$39` | `$83F4` / `$3C3F4` | `$05:$9B00` / `$15B00` | `416dccc8fb7022b2af0a6645d3a9ec051fb1e42a5a72bdf9fea75a1f7dfc1de2` | `22364cea9bd4190b07c28aad386f011699577e3d6fd105e851ed6980be05fc45` |
| `$3A` | `$83FF` / `$3C3FF` | `$05:$9C80` / `$15C80` | `804f6802d5507929eccac4a4bc378c15ea7be56619633293b59ee71761503f56` | `da066dd9609909a66e41b12048eae0b361460a1deb1e11d2f2dd181c05f6029e` |

The fixed-bank table at ROM `$104B + frame*4` supplies bank, source pointer and
64-byte transfer count. Each entry requests six blocks: 384 bytes, 12 Mode-4
tiles, copied to VRAM `$0000` as tile indices `$00..$0B`. `LoadPlayerTiles` is
CPU `$0D15`; `$1027` marks a transfer when player frame `$D506` or facing
changes. This is runtime dynamic loading, not level-static sprite art.

All three mapping records contain the same six 8×16 pieces and tile offsets
`$00,$02,$04,$06,$08,$0A`. Their relative pieces cover X `-16..7` and Y
`-32..-1`. The graphics payloads differ, so `$38` and `$3A` are not merely
alternative mappings or orientations.

The THZ1 sprite palette selector is `$06`; its ROM data begins at `$3B6AD`.
Palette index zero is transparent. A faithful GameMaker import uses a 24×32
canvas with origin `(16,32)`. The original facing path mirrors piece X and bit-
reverses tile bytes through the ROM table at `$0100`; ordinary GameMaker
horizontal mirroring is equivalent, so a second extracted set is unnecessary.

POC 18.6 can replace `SPR_player_falling` with these images without changing
state-`$11` physics. Metadata and extraction live in
`data/rom-cache/thz1/player-state-11-graphics.json` and
`tools/player_state_11_graphics.py`; ignored previews are generated under
`build/player-state-11/`.
