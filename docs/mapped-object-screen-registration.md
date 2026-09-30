# Mapped-object screen registration (Sonic Chaos SMS, Europe v1.2)

Research only. ROM SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607` (verified; the ROM is not committed).
Machine-readable facts: `data/rom-cache/mapped-object-registration.json` (source facts and interpretation are separate sections).
Tooling: `tools/mapped_object_registration.py`, `tools/sms_frame_harness.py`, `tools/poc_sprite_registration_report.py`.
Tests: `tests/test_mapped_object_registration.py`.
POC checkpoint compared read-only: `poc/thz1-cleanup` @ `6819722201b169c4dac136efdb4236c5cf470327` (not modified).

Evidence classes: DECODED DATA, BYTE-VERIFIED ASSEMBLY, SOURCE-TRACED BEHAVIOR, CONTROLLED ROUTINE RESULT,
EMULATED ORIGINAL FRAME (exact game code driving an approximate VDP; my own label), GAMEMAKER ADAPTER ONLY, UNRESOLVED.

## 1. Answer

**Conclusion A: one shared renderer rule exists.** Every mapped object goes through the same chain, and there are no per-class anchors.
Between the stored world anchor and the visible pixel the engine applies, in this order:

1. `screen = anchor - camera` (16-bit, `$3FC8`).
2. `SAT_Y = screen_y + frame_y_origin + piece_y` and `SAT_X = screen_x + x_origin' + piece_x'` (`$226A`, `$22B6`).
3. The VDP draws a sprite at line `SAT_Y + 1`, and the game programs the background vertical scroll to `(cam_y + 17) mod 224` and horizontal scroll to `-(cam_x + 1)`.

So relative to the terrain/background the object appears at

    terrain_row = anchor_y + y_origin + m_y + 18        (1 from SAT, 17 from VScroll)
    terrain_col = anchor_x + x_origin' + m_x + 1        (1 from HScroll)

The mapping bounds from the extractor are correct but *pre-presentation*. The missing stage is a constant (+1, +18) between object space and terrain space, identical for all types.
The collision floor probe adds the same 18 (`$7690`), consistent with anchors being terrain-space minus (1, 18). (SOURCE-TRACED BEHAVIOR.)

## 2. Routine chain (BYTE-VERIFIED ASSEMBLY; each routine's bytes are compared literally in the JSON)

| Stage | Routine | ROM offset | Bank / CPU |
|---|---|---|---|
| slot loop (64-byte slots at `$D500`, IX) | `$220E` | 0x0220E | 0 / `$220E` |
| anchor - camera into +$1A/+$1C | `$3FC8` (IX+$11/$14 minus `$D174`/`$D176`) | 0x03FC8 | 0 / `$3FC8` |
| Y pieces to SAT Y buffer (`$DB00`), visible iff -16..191 else `$E0` | `$226A` | 0x0226A | 0 / `$226A` |
| X and tile to SAT buffer (`$DB40`), high byte set -> X=0 | `$22B6` | 0x022B6 | 0 / `$22B6` |
| flicker toggle | `$2335` | 0x02335 | 0 / `$2335` |
| frame record select | `$6567` | 0x06567 | 1 / `$6567` |
| camera to R8/R9 (`+17`, `mod 224`; `+1`, NEG) | `$4D3E` | 0x04D3E | 1 / `$4D3E` |
| R8/R9 output at vblank | `$0538` | 0x00538 | 0 / `$0538` |
| SAT upload | `$1E36` | 0x01E36 | 0 / `$1E36` |
| VDP register init (R0=$26, R1=$E2, R5=$FF, R6=$FB) | `$1D2D` | 0x01D2D | 0 / `$1D2D` |
| floor probe (+18) | `$7690` | 0x07690 | 1 / `$7690` |
| placement create | `$80EB` | 0x700EB | 28 / `$80EB` |

Mapping tables and frame records live in bank 15 (ROM 0x3C000, CPU `$8000+`). The type-$09 table is CPU `$8C71` = ROM 0x3CC71; frame 1 record is CPU `$8CE3` = ROM 0x3CCE3.
VDP: R1=$E2 means 8x16 sprites, R6=$FB means sprite pattern base tile 0 (an early measurement of mine wrongly assumed base 256; fixed).

## 3. Explicit arithmetic (CONTROLLED ROUTINE RESULT, real `$6567`/`$3FC8`/`$226A`/`$22B6` run on a Z80 with explicit slot RAM; a pure-Python model of the same routines agrees in all 12 fixtures)

### Type $09 at (2880, 384), camera (2704, 308), frame 1 (record `$8CE3`, y_origin 0, piece y -16,-16, piece x -8,0, tiles 16,18)

- `$3FC8`: screen = (2880-2704, 384-308) = (176, 76)
- `$226A`: SAT_Y = 76 + 0 - 16 = **60** (both pieces)
- `$22B6`: SAT_X = 176-8 = **168**, and 176+0 = **176**; tiles 16, 18
- VDP draws lines 61..76. R9 = (308+17) mod 224 = 101, so line 61 shows terrain row 61+101+... = cam_y+17+61 = **386**, last row **401**.
- Relative to the anchor: rows +2..+17. (Mapping alone says -16..-1; the +18 is the presentation term.)

### Type $09 at (3124, 548), camera (2964, 446)

- screen = (160, 102); SAT_Y = 102 - 16 = **86**; SAT_X = 152, 160; lines 87..102; same +2..+17 relative rows.
  Also computed: (3160,522) -> SAT_Y 60, X 188/196; (3208,512) -> SAT_Y 50, X 236/244.

### Type $10 (param 4) at (336, 270), camera (250, 200), frame record `$8D0F`

- y_origin = **8**; piece y -32 (x3) and -16 (x3); screen_y = 70
- SAT_Y = 70 + 8 - 32 = **46** (top row) and 70 + 8 - 16 = **62** (bottom row); lines 47..78
- Terrain rows relative to anchor: -6..+17 (image row r lands at anchor + 8 - 32 + r + 18 = anchor - 6 + r; opaque rows r = 0..23). **Why the POC needed +18:** the frame's own y_origin (8) and piece offsets are already in the data; the only term the POC lacked is the shared VScroll (17) + SAT (1) = 18. It is not a per-type constant; the same +18 applies to $21 and (with the folded +1 already included) makes $09 need +17.

### Type $21 (flipped) at (800, 590), camera (604, 490), frame record `$9121`

- y_origin 0; pieces y -32/-16; screen_y = 100; SAT_Y = 68 and 84; lines 69..100.
- X uses the mirrored table (`$0D08`, entry -x-8) with negated x_origin: SAT_X = 200,192,184 (x3 each row).
- Relative rows -14..+17. Same +18 as $10, so the POC's +18 on $21 is the same shared term.

## 4. Control table (source = EMULATED ORIGINAL FRAME rows; mapping = DECODED DATA)

| Type | Table (CPU / ROM) | Original opaque rows rel. anchor | Note |
|---|---|---|---|
| $09 | `$8C71` / 0x3CC71 | +2..+17 | identical for all 4 frames |
| $10 | `$8C71` / 0x3CC71 | -6..+17 | frame 11/12 |
| $18 | `$8EAE` / 0x3CEAE | -30..+17 | top row UNRESOLVED vs POC (see 6) |
| $1B | `$8C71` / 0x3CC71 | -6..+17 | four states, bottom fixed at +17 |
| $21 | `$911B` / 0x3D11B | -14..+17 | mirrored X |
| $26 | `$91C0` / 0x3D1C0 | -6..+17 (frame 2) | one 32x24 mapped image |
| $27 | `$91F5` / 0x3D1F5 | +3..+17 | |
| $28 | `$9217` / 0x3D217 | +2..+17 | |

Every observed type ends at +17: the shared rule, seen empirically, not just derived.

## 5. Extractor audit (`tools/thz1_object_assets.py`)

Parsing of frame records, signed offsets, piece counts, even tile offsets and the mirror rule are all correct and locked by tests.
It reports literal mapping geometry, which is what it claims to. It does not model the +1/+18 presentation. **Conclusion C (extractor wrong) is false.**
B (per-class anchors) is false: one renderer, one constant. D (elsewhere) is subsumed: the "elsewhere" is the R9/R8 programming plus the SAT +1, both shared.

## 6. Predicted POC discrepancies (GAMEMAKER ADAPTER ONLY, needs Windows visual confirmation; POC minus original, negative = POC too high)

| Type | Top | Bottom | Comment |
|---|---|---|---|
| $09 | -17 | -17 | adapter 0; needs +17 on top of the folded +1 |
| $10 | 0 | 0 | consistent |
| $21 | 0 | 0 | consistent |
| $27 | -18 | -18 | `draw_self()` at anchor |
| $28 | -2 | -2 | collision-top vs visual-top semantics UNRESOLVED |
| $18 | +4 | 0 | possible dynamic art, UNRESOLVED |
| $1B | n/a | n/a | tips +4 taller in first three states per my crop comparison |
| $26 | +15 (cap) | n/a | POC composite vs single ROM frame |
| all | X -1 | | HScroll +1 |

These are predictions from reading POC sprite PNG alpha and macros. They contradict some "accepted" POC notes; I did not repeat empirical offset experiments, and I treat the original as authoritative.

## 7. Unresolved (precisely bounded)

- $18: whether art is dynamically loaded, which decides the +4 top difference.
- $26: bespoke POC composite vs ROM frame; not resolved.
- $28: which of collision-top or visual-top the POC's "anchor" intends.
- Level-start fill transient (+$10) not modelled; screen-shake shifts BG but not sprites.
- The harness is approximate (no PSG, sprite overflow flags, mid-line timing); all pixel claims are also cross-checked against byte-verified arithmetic.
- No Windows/GameMaker run was made.

## 8. Reproduce

    PYTHONPATH=<z80 build> python tools/mapped_object_registration.py sc.sms --check data/rom-cache/mapped-object-registration.json
    python -m unittest tests.test_mapped_object_registration
    python tools/poc_sprite_registration_report.py <SonicChaos_POC checkout>   # read-only

`tests/verify_cache.py` regenerates the static part (byte checks, tables, controlled fixtures, rule).
