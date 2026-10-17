# U5-A: Sonic presentation gaps and the opening animation

Research only. No POC change, no gameplay change, no ROM bytes or pixel dumps are committed (PNGs go to the ignored `build/u5a/`).

- Research base: `c30c06e6c428b64e843ea5834ff52b7bc3304708`. POC read at `b4737e834982b2985c6fdcb8d4d76cb78c9092c8` (read only).
- ROM: Sonic Chaos (Europe) v1.2, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
- Evidence classes: **ROM** = decoded tables / byte-verified assembly; **EMU** = emulated original (the approximate `sms_frame_harness`, not cycle exact); **POC** = POC source at the commit above.
- Machine-readable matrix: `data/u5a/evidence-matrix.json`. Handoff: `data/u5a/poc-handoff.json`.

## 1. Verdicts

| Part | Question | Verdict |
|---|---|---|
| A | Strip run/walk art | **Missing resource.** ROM frames `$3C-$3F` are not imported; states 5/6 are not presented from ROM art in the POC. Gameplay (marker, strip fall) is already implemented. |
| A | Strip vs type `$28` platform | Different mechanisms. Only the terrain surface `$19` handler (`$6B23`) writes the marker; platforms and `$1C` decks never select the strip set. |
| B | Spring Shoes shows jump | **Mismatch confirmed.** POC maps state `$12` to the legacy `SPR_player_jump`. ROM holds Sonic frame `$0B` (the upright pose) on every update. The sprite has to be imported; it is not in the POC. |
| C | Weak spring / strip fall `$1C-$21` | **Implemented and exact** at source level (program cases 11 and 20, 18 frame resources). No state-selection or presentation mismatch found. James's symptom cannot be derived from source; a POC trace is requested. |
| D | Introduction | The ROM has an opening **cinematic** (zone 7 act 0, 738 updates) before the title. There is **no Sega logo** in the ROM. The POC has neither the cinematic nor the attract demos. |

## 2. Existing evidence versus new findings

| id | Item | Existing research reused | New in U5-A | Status |
|---|---|---|---|---|
| A1 | Frames `$3C-$3F` | `gpz-surface19-audit.md`, `player-fall-control-audit.md` | byte-matched selectors, frames, palettes, 3 emulated cases | MISSING_RESOURCE |
| A2 | Marker lifetime, strip fall `$14` | same | 3 emulated cases | IMPLEMENTED |
| A3 | Strip vs platform `$28` / `$1C` deck | `isometric-platform-audit.md`, `sez-platform-28-audit.md` | 4 emulated cases | NO_CHANGE_NEEDED |
| B1 | Sonic pose in state `$12` | `spring-shoes-presentation-audit.md`, `powerup-shoes-audit.md` | frame `$0B` geometry, script `$8346`, POC state-12 mapping | MISMATCH |
| B2 | Footwear object animation | `spring-shoes-presentation-audit.md` | none | NO_CHANGE_NEEDED |
| C1 | Weak mapped spring `$0B` -> `$1C-$21` | `player-spring-airborne-state-closure.md` | literal transcription of the POC selector run over 26 scenarios: 2,081 presented updates, 0 mismatches | IMPLEMENTED |
| C2 | Strip fall `$14` | `player-fall-control-audit.md` | 81 presented updates reproduced | IMPLEMENTED |
| D1 | Start-up flow | `g0-campaign-contract.md`, `u4-ordinary-results.md` | dispatcher, handlers, census | ABSENT_FROM_POC |
| D2 | Cinematic data | none | static, observed and replay data | ABSENT_FROM_POC |
| D3 | Sega logo | none | proof of absence | NOT_PRESENT_IN_ROM |

## 3. Part A: strip run and walk

**ROM** (`player-static.json`, `selectors`; bank `$0C`, byte-matched):
- Marker: Sonic +`$24` bit 0 (`$D524`). Set by the surface-`$19` handler `$6B23`; cleared by the walk/run selector when the previous surface (`$D36C & $1F`) is not `$19`, by a normal jump (`$45ED`), the ordinary fall setter (`$463C`) and surface-zero handler (`$6C45`); retained by the strip-fall setter `$4663`.
- Run selector `$8F45`: duration 4. Ordinary frames `$07-$0A`; strip frames `$3C-$3F` (cycle 4).
- Walk selector `$8EE1`: order is side contact (`$D523 & $0C`, frame `$5E`, duration 2) first; then marker set and previous surface `$19` gives the strip set `$3C-$3F`; else clear the marker. Ordinary walk frames `$01-$06`. Duration by |x speed| high byte: `10, 8, 6, 4, 4, ...`, loaded only when the record reloads.
- Walk and run share one index (`$D52F`: increment, wrap at cycle length, frame = index + base). A `$05 <-> $06` change keeps the phase.
- Strip frames: `data/u5a/player-static.json` `frames` (canvas size, GameMaker origin, index and RGBA hashes). Sonic's eleven colours are identical in every act.
- Facing: walk calls `$48A7` (bit 4 follows input); run does not and leaves the flag untouched.
- Registration: BG origin = camera + (1,17); sprite top line = y + rel_y - camY + 1; GameMaker origin = (-min_x, -min_y) of the piece bounds.

**EMU** (`player-observed.json`, 12 cases): full speed on GPZ2 / MGHZ1 strips presents `$3F,$3C,$3D,$3E` at 4 updates each (order set by the shared index). Walk at +3.0 requests `$14` on update 1. Run, then release, chains run -> walk -> `$14`. A marker set on ordinary floor is cleared by the selector. Riding or walking type `$28` (static `$83`, moving `$89`) and a `$1C` deck use `$0B` / `$01-$06` / `$07-$0A`, with the marker staying 0.

**POC**: `SCR_chaos_player_animation` supports states 5/6 only through legacy sprites; no case for frames `60-63`; marker and strip fall are already in `SCR_chaos_core` (line 403) and `SCR_cc_*`.

## 4. Part B: Spring Shoes

- **ROM**: state `$12` script `$8346` is one record (4 updates, frame `$0B`) then `FF 00`: Sonic holds frame `$0B` every update. Frame `$0B`: 5 pieces, 24x32, origin (10,32), 10 tiles from bank `$04` `$8F80`. Facing follows Left/Right only. The footwear object (type `$2F`) has its own cadence (frame 3 for 12, then 4) and is kept separate.
- **EMU**: the existing `data/rom-cache/spring-shoes-presentation.json` traces (player frame always 11, timer 4..1).
- **POC**: `SCR_chaos_adapter` lines 59/65/98 choose `SPR_player_jump`, image 0, for state 12; `chaos_player_animation_supported` excludes 18; the program table has no case 18.
- The sprite is **not** in the POC; frame `$0B` must be imported (it is also the ROM idle frame of states 0/1).
- The earlier unresolved "too active" remark is not explained: the POC shows a single static jump frame.

## 5. Part C: weak spring and strip fall

- Weak mapped spring (`$26` parameter != 0 / span aux1 != 0, boss `$50` bounce): state `$0B` with `$D448` bit 0 clear shows frames `$1C-$21`, 4 updates each, 82-update cycle. Strong springs show `$61`.
- Strip fall `$14`: tumble set `$1C-$21`, 24-update cycle, starting the update after the request.
- POC: program cases 11 and 20 plus `SPR_chaos_player_frame_1C..21` are pixel- and origin-identical to the ROM frames. The literal transcription of the POC selector reproduces ROM frames on 2,081 presented updates (0 mismatches).
- Outstanding: the reported missing tumble cannot be derived from source. Request a POC trace (`cp_state`, next state, `$D448`, visual_anim state/active/frame, `sprite_index`) during a weak mapped-spring bounce. A Windows-only cause is not excluded.

## 6. Part D: the opening animation

### 6.1 Which sequence

Census from power-on (`startup-census.json`): opening cinematic (871 frames) -> title (1,310) -> attract demos (1,230 each: THZ1 Sonic, GPZ1 Tails, SEZ1 Sonic) -> opening. Flow flag `$D292` bits 7..2, dispatcher `$2B50`; opening handler `$2B77` (bit 5) runs routine `$06C7`; title `$0719`; demos `$2BC3/$2C34`. Button 1 or 2 skips the opening to a fade-out and the title (63 frames from the press), not to New Game. Act title cards (`$3175`) are a separate, already-implemented feature.

Alternatives, if "introduction" meant something else: A2 title screen (POC `ROM_menu_title`), A3 attract demo (absent), A4 act title card (done), A5 Sega logo (not in ROM; the POC's `SPR_opening_sega` is inherited Open Sonic SMS art). The cinematic is the recommended reading.

### 6.2 Cinematic mechanism (ROM and EMU)

- Zone 7 act 0, run by the ordinary level engine (layout 256x8 blocks of 32 px) for 30 + 708 = 738 updates (`opening_routine`, loops `$07B8` BC=`$1E`, `$079F` BC=`$2C4`).
- Sonic and Tails use the shared state-`$29` script: X speed `$0600` (6.0 px/update), 150 iterations of the run selector (frames `$07-$0A`, 4 updates each). Sonic starts at x=96. Tails (type 2, selector `$8EE1`) appears at update 661 at camera X - 32 + 4.
- Camera follows the actor 118 px behind, frozen at 3578 from update 601. Background X = camera + 1.
- Type `$1F` machine (17 pieces, tile base `$6A`) spawns at update 40 (observed; the placement window that creates it is unresolved) with states 40/43/66/113/486/536 and callbacks `$AF8C/$AF94/$AF94/$AF8C`.
- Fades: first fade-in pass is black; 4 fade-in passes every 5 updates; 3 fade-out passes after the last update; then 30 waits, then the title. Music request `$90` is recorded numerically (no asset).
- Validation: the model reproduces all 738 observed updates (0 mismatching columns); background and sprites are pixel-identical to a composition from ROM data on 159 sampled frames.

### 6.3 Data

`opening-static.json` (flow, level, scripts, mappings, palettes, window table), `opening-replay.json` (738 per-update rows), `opening-observed.json`, `startup-census.json`, `opening-export-manifest.json`. Frame PNGs and the contact sheet are in ignored `build/u5a/opening/`.

## 7. POC handoff (smallest presentation-only changes; not made here)

Full list with assets, hashes and acceptance checks: `data/u5a/poc-handoff.json` (28 assets).

1. **A-1** Add cases 60..63 to `chaos_player_frame_sprite` and four sprites to `chaos_player_rom_resource` (no AQZ variant).
2. **A-2** For requested states 5/6: strip = `(special & 1) && (previous & 31) == 25`, evaluated only when the record reloads; side contact keeps the legacy sprite and takes precedence; wrap the shared index at 4, frame = `$3C + index`.
3. **A-3** Keep facing bit 4 current in walk (calls `$48A7`), untouched in run.
4. **B-1/B-2** Add program case 18 (`[[0,4,11,33606],[1,0,0,33610]]`), frame 11 sprite and `cp_state == 18` to supported. **B-3** no adapter edit needed afterwards.
5. **C-1** No change.
6. **D-1** New presentation room replaying `opening-replay.json`. **D-2** Manager decision: keep or remove the non-canonical Sega logo.

## 8. Reproduction

```
ROM=/path/to/Sonic_Chaos_Europe.sms
python tools/u5a_player_presentation.py $ROM --poc <POC worktree>   # --check to compare
python tools/u5a_opening.py $ROM                                    # ~1 minute; --check to compare
python tools/u5a_handoff.py                                         # needs only the JSON; --check
python tests/test_u5a_player_presentation.py                        # 26 tests (SONIC_CHAOS_ROM=$ROM unskips ROM-backed)
python tests/test_u5a_opening.py                                    # 19 tests
```

Generated PNG sheets: `build/u5a/sheets/{u5a-strip-run,u5a-spring-shoes-pose,u5a-tumble}.png`, `build/u5a/opening/opening-contact-sheet.png`.

## 9. Evidence boundaries and unresolved items

- The harness is approximate (VDP, NTSC timing, picture timing); Europe hardware runs at 50 Hz. Frame counts above are harness frames; update counts are the authority for game logic. Not run on Windows.
- Unresolved: the placement window that creates the machine (observed at update 40); the camera Y ramp rule (8,8,8,9..15); hardware 50 Hz pacing; audio request `$90` has no PC asset; type `$1F` states 6/7 not exercised; platform types `$24/$2E/$3F` riders not run; side-contact frame `$5E` has no resource; what James means by "introduction"; the cause of the C symptom.
- Candidate AGENTS.md notes (not applied): the ROM has no Sega logo; the walk/run strip decision is made only on record reload; Spring Shoes Sonic pose is frame `$0B`.
