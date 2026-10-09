# Zone 5 foundation — A1

Base `89641f8093e62401cd81f94e6ac889422f600472`. Research branch only;
not reviewed or merged. Verified Europe v1.2 SHA-256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
Numeric zone 5 is used until title/control-flow evidence establishes naming
and reachable terminal progression. Three act table records are decoded;
this alone does not prove game-completion behavior.

| Act | Cells | Pixels | Player start | Camera start | Camera right/bottom | Written cells | Terrain rings | Mapped records |
|---|---|---|---|---|---|---|---|---|
| 1 | 128×32 | 4096×1024 | 238,864 | 126,752 | 3840,784 | 4095 | 146 | 19 |
| 2 | 128×32 | 4096×1024 | 170,430 | 58,318 | 3840,784 | 4095 | 276 | 35 |
| 3 | 112×32 | 3584×1024 | 110,288 | 0,176 | 3328,784 | 3584 | 0 | 5 |

All acts load left/top camera limits 0/8. The implementation manifest retains
the header RAM field names; camera limits must not be mistaken for player
world clamps. The original start/header loaders and RLE decoder execute in
the routine oracle. All 11,774 written cells match, with untouched end
sentinels. Both 4096-cell encoded maps retain their final unloaded cell in
the cache; no invented padding is treated as written terrain.

Mappings use bank `$14`, CPU `$A4E0`, file `$524E0`. All 256 block indices in
both original pointer-consumer paths pass for each act (1,536 checks).
The erroneous table-relative formula differs by `$24E0` and produces different
data for all 256 blocks. Preserve the bank-relative decoder.

| Type | Act 1 | Act 2 | Act 3 | Total |
|---|---|---|---|---|
| $09 | 0 | 6 | 0 | 6 |
| $10 | 4 | 3 | 0 | 7 |
| $17 | 2 | 2 | 1 | 5 |
| $18 | 1 | 1 | 0 | 2 |
| $26 | 0 | 2 | 0 | 2 |
| $28 | 4 | 3 | 2 | 9 |
| $2C | 1 | 8 | 0 | 9 |
| $36 | 4 | 6 | 0 | 10 |
| $38 | 3 | 4 | 0 | 7 |
| $5E | 0 | 0 | 1 | 1 |
| $60 | 0 | 0 | 1 | 1 |

The census retains all nine placement bytes, tokens, numeric parameters,
art bases and original creator outputs. Earlier object contracts are reuse
candidates, not blanket runtime approval. `$17/$36/$38/$5E/$60` need fresh
closure; scripts already reveal `$37/$39/$5F/$61/$63` child dependencies.

Surfaces: `$00/$01/$02/$03/$05/$07/$09/$0A/$0B/$0C/$0D/$0E/$13/$14/$16/$1A`.
Surface `$01` has a zone5-only path `$6A5D`; `$0B` creates `$37`; `$0E` is
floor-gated displacement; `$13` requests player `$21` through directional
transport gates. Full conditions and update order belong to A2, not inference
from this census. In particular there are no AQZ water controllers here.

Background/sprite palettes 26/11 and nine initial graphics loads are recorded.
Ring frames use `$1D:$855D` -> VRAM `$2AE0`, 128 bytes every eight updates.
Descriptor effect IDs are 5,6,8,13. Both ordinary and boss-active 192-update
effect outputs are cached. These are controlled effect routine observations,
not proof of whole-frame raster/camera coupling.

Reproduce with the repository `.venv/Scripts/python.exe`:

```
tools/eez_foundation.py ROM [--check]
-m unittest discover -s tests -p test_eez_foundation.py
tools/eez_art.py ROM
```

Render `tools/eez_art_render.py` using the bundled Pillow Python. Pixel inputs
and PNGs remain under ignored `build/eez-approval`; committed approval metadata
records original mappings. Current boards are provisional: animated VRAM
initialization must be reconciled before terrain approval. Boss compositions
are deferred until their dynamic art chain is traced. No approval is claimed.

AGENTS candidate: Zone5 A1 is on a separate unmerged research branch; retain
the `$14:$A4E0` mapping regression and the 112-cell act3 row stride. Do not
consume unresolved runtime reconnaissance as an implementation contract.
