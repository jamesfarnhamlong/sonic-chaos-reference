# RQ4 — Campaign start-position and camera registration

Research branch `research/rq4-campaign-start-registration` from Research main `850a60303b91a0885052510554e2a07ad056999a`. ROM: `Sonic Chaos (Europe) v1.2`, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607` (local only; no ROM bytes or pixels are committed).
Machine data: `data/rq4/start-registration.json`. Generator and checker: `tools/rq4_start_registration.py`. Tests: `tests/test_rq4_start_registration.py`.
Evidence classes: **STATIC** (ROM bytes), **EMULATED** (unmodified ROM code, real New Game, approximate VDP; only the G0-R START_INDEX fixture for acts other than THZ1), **FIXTURE-SWEEP** (one Y offset written at the loader return), **SOURCE-READ** (POC code read, never executed).

## 1. Answer

1. **The ROM never applies a 4 px (or any) shift to the start record.** The record words are stored unchanged into the player anchor `$D511/$D514` and the camera target `$D2D6/$D2D8`; the camera is committed directly from the record with no clamp. In all 18 acts the loader result equals the table, the first-update camera equals the record camera, and a fresh load equals a pit-death reload.
2. **THZ1 record Y 654 is also THZ1's rest anchor.** Sonic stands on the floor from the first player pass: 654 at pass 0, 1, 2 … 200. There is no first-update shift.
3. **A start that is not at rest is resolved by ordinary terrain physics, not by the loader.** An embedded 658 is snapped up to 654 on the second pass (section 4); a start 14 px above the floor falls 14 px in state `$0E`. Nine of 18 acts do not start at rest: THZ3, GPZ1–3, MGHZ1/3, EEZ1/3 fall 14 px; SEZ3 is lifted 7 px.
4. **The POC's 658 is an instance coordinate, not a ROM anchor.** The POC player instance y is `core anchor + chaosAnchorOffset (5)`. The THZ branch of `OBJ_chaos_zone` passes the literal 658 as the *instance* y, so the core starts at anchor 653 (1 px above ROM) and, with a ROM-exact core, rests at 654, i.e. instance y 659. The same branch passes THZ2 (110,398) and THZ3 (110,224) as instance y, so their cores start at 393 and 219, 5 px above the ROM record. GPZ/MGHZ/SEZ/AQZ/EEZ/SS already treat the record as the canonical anchor. (SOURCE-READ; the unproven runtime part is in section 6.)
5. **Register meaning for THZ2/THZ3** (formerly DEV_SPAWN / UNVERIFIED): the record is `[camera X, camera Y, player anchor X, player anchor Y]` (four little-endian words). The player words go to `$D511/$D514`, the same anchor that terrain, ring, spring and object contact use. THZ2 (110,398) is a rest position. **THZ3 (110,224) is not**: the ROM falls to 238 over 10 passes while the camera follows (screen anchor stays (110,112)).

## 2. Routine trace (STATIC)

* `$1673` reload → `$2934` loader → `$4DAD` camera/scroll initialisation → `CALL $4E57`.
* `$4E57..$4E97`: zone `$D297` → pointer table `$4E98`; act `$D298` → record pointer (`$4E65`); record `+0 → $D2D6`, `+2 → $D2D8`, `+4 → $D511`, `+6 → $D514`; `RET` at `$4E97`. No add, subtract or shift. (`$2A4F` is a different per-act record reader, table `$2A9A`.)
* `$4DFF..$4E0E`: `$D174 := $D284 := $D2D6`, `$D176 := $D286 := $D2D8` (camera committed directly). `$4E11..$4E30`: 29 map-fill passes. `$4E32..$4E52`: camera re-committed, `$D173 := (camY + 16) mod $E0`.
* Routine hashes are in the JSON (`static.routine_hashes`).

## 3. Observations (EMULATED, real New Game; 18 acts, fresh load and pit-death reload)

A *pass* is one entry of the player engine `$64FA` with IX = `$D500`; "after n passes" is the state seen at the entry of pass n+1. Frame offsets are harness frames after the loader returns (`$4E97`).

* Display is enabled at frame +1. The first engine pass is at frame +30 (THZ1). The player object exists after pass 1 (state `$00` → `$01`/`$0E`) and the **first rendered player sprite is after pass 2, frame +32**.
* Camera at entry (after pass 0) is exactly the record in all 18 acts. Afterwards only the ordinary camera follow moves camera Y toward the player: THZ1/THZ2 go from screen anchor (104,124) to rest (104,112) (camera Y +12 over roughly passes 13–40); falling acts keep screen anchor y 112 while the camera drops 14. Camera X does not move at rest in any act. This is camera follow, not an initial clamp.
* Reload equals fresh in all 18 acts (loader result and passes 0–200, ignoring frame offsets), consistent with the G0-R `restart_matrix`.
* Sprite registration (idle frame, state `$02`, five 8×16 hardware sprites): opaque pixels span **x −9..+9, y −30..0** around the anchor's screen position `(anchor − camera)`; SAT rows are `Y+1`. With background scroll `R9 = (camY + 17) mod 224` and `R8 = −(cam+1)` the visible foot row is **world y = anchor + 17**, directly above the floor probe row anchor + 18 (`docs/collision-geometry-audit.md`). The shape is identical in all 18 acts.

## 4. THZ1 start-Y sweep (FIXTURE-SWEEP, one write at `$4E97`)

| Start Y written | Pass 0 | Pass 1 | Pass 2 | Rest |
|---|---|---|---|---|
| 646 (−8), 649 (−5), 650 (−4) | as written | as written | +1 (falling, state `$0E`) | 654 (by pass 5–10) |
| **653 (−1)**, the POC core anchor from instance 658 | 653 | 653 | **654** | 654 |
| 654 (0), the ROM record | 654 | 654 | 654 | 654 |
| **658 (+4)**, the literal 658 treated as a ROM anchor | 658 | 658 | **654** | 654 |
| 659 (+5), 662 (+8) | as written | as written | 654 | 654 |

THZ2: a start of 393 (POC core from the DEV_SPAWN instance y) falls to 398 by pass 5 and rests there. THZ3: a start of 219 falls to 238, as does the ROM record 224. Neither a lift nor a fall is reachable from the ROM record for THZ1.

## 5. G1-B implementation handoff

Rule: **pass the ROM record as the canonical anchor; do not add a Y shift.** Convert once at the adapter boundary using the existing POC registration (`instance y = anchor + 5`, `draw y = anchor + 18`, `draw x = anchor + 1`; SOURCE-READ, unchanged). The camera record is the left/top edge of the original 256×192 window (not a centre, not clamped); its first-update value equals the record.

| Quantity | ROM fact | G1-B use |
|---|---|---|
| Player anchor at entry | record `+4,+6` → `$D511/$D514` | seed the core directly (`core.yu := record`, as GPZ…EEZ do); THZ1/2/3 should use the same path, retiring the literal 658 and the two DEV_SPAWN macros |
| After first update | equals entry for resting starts; otherwise falls (+1, +2, +4 … until contact) or is lifted (embedded) | let the shared core resolve it; no per-act offset |
| Rest anchor | THZ1 654, THZ2 398, THZ3 238; see table | rest (not record) is the stable oracle for THZ3 and the other eight shifted acts |
| Sprite anchor | opaque x −9..9, y −30..0 around the anchor screen position; foot world row anchor + 17 | no new offset; existing ROM-art player registration encodes it. Legacy Sonic art keeps its engine registration |
| Camera at entry | record, committed directly | THZ1 POC currently uses XView 0 / YView 550 (legacy); ROM entry is **(38,530)**. Use the record, then the shared follow (screen anchor y 124 → 112) |
| Camera at rest | table below | follow behaviour, not initial data |
| 256 → 348 | ROM gives the left edge `cam` of a 256 px window; `anchor − cam` is 78–112 px from the left | the 348 view is a PC adapter: Research specifies no widescreen offset. Whether `cam` stays the left edge (viewport audit: a wide view extends RIGHT only) or is re-centred is a G1-B adapter decision, documented separately from these ROM facts |

<!-- BEGIN handoff-table -->
| Act | ROM record: anchor (X,Y) / camera (X,Y) | Entry = after pass 0 | After 1 pass | After 2 passes | Rest (pass 200) | Anchor shift to rest | Camera at rest | Screen anchor entry -> rest |
|---|---|---|---|---|---|---|---|---|
| THZ1 | (142,654) / (38,530) | (142,654) | (142,654) | (142,654) | (142,654) | +0 | (38,542) | (104,124) -> (104,112) |
| THZ2 | (110,398) / (6,274) | (110,398) | (110,398) | (110,398) | (110,398) | +0 | (6,286) | (104,124) -> (104,112) |
| THZ3 | (110,224) / (0,112) | (110,224) | (110,224) | (110,225) | (110,238) | +14 | (0,126) | (110,112) -> (110,112) |
| GPZ1 | (110,384) / (0,272) | (110,384) | (110,384) | (110,385) | (110,398) | +14 | (0,286) | (110,112) -> (110,112) |
| GPZ2 | (110,448) / (0,336) | (110,448) | (110,448) | (110,449) | (110,462) | +14 | (0,350) | (110,112) -> (110,112) |
| GPZ3 | (187,352) / (75,240) | (187,352) | (187,352) | (187,353) | (187,366) | +14 | (75,254) | (112,112) -> (112,112) |
| SEZ1 | (110,718) / (0,608) | (110,718) | (110,718) | (110,718) | (110,718) | +0 | (0,608) | (110,110) -> (110,110) |
| SEZ2 | (110,846) / (0,742) | (110,846) | (110,846) | (110,846) | (110,846) | +0 | (0,742) | (110,104) -> (110,104) |
| SEZ3 | (110,821) / (0,702) | (110,821) | (110,821) | (110,814) | (110,814) | -7 | (0,702) | (110,119) -> (110,112) |
| MGHZ1 | (78,192) / (0,80) | (78,192) | (78,192) | (78,193) | (78,206) | +14 | (0,94) | (78,112) -> (78,112) |
| MGHZ2 | (112,558) / (0,447) | (112,558) | (112,558) | (112,558) | (112,558) | +0 | (0,447) | (112,111) -> (112,111) |
| MGHZ3 | (110,160) / (0,48) | (110,160) | (110,160) | (110,161) | (110,174) | +14 | (0,62) | (110,112) -> (110,112) |
| AQZ1 | (110,206) / (0,99) | (110,206) | (110,206) | (110,206) | (110,206) | +0 | (0,99) | (110,107) -> (110,107) |
| AQZ2 | (110,558) / (0,447) | (110,558) | (110,558) | (110,558) | (110,558) | +0 | (0,447) | (110,111) -> (110,111) |
| AQZ3 | (110,238) / (0,132) | (110,238) | (110,238) | (110,238) | (110,238) | +0 | (0,132) | (110,106) -> (110,106) |
| EEZ1 | (238,864) / (126,752) | (238,864) | (238,864) | (238,865) | (238,878) | +14 | (126,766) | (112,112) -> (112,112) |
| EEZ2 | (170,430) / (58,318) | (170,430) | (170,430) | (170,430) | (170,430) | +0 | (58,318) | (112,112) -> (112,112) |
| EEZ3 | (110,288) / (0,176) | (110,288) | (110,288) | (110,289) | (110,302) | +14 | (0,190) | (110,112) -> (110,112) |
<!-- END handoff-table -->

"Anchor shift to rest" is rest minus record (pass 200). Full per-pass rows (0,1,2,3,4,5,10,20,40,80,200), frame offsets, VDP scroll registers, sprite rectangles and the reload comparison are in `data/rq4/start-registration.json`.

## 6. Remaining uncertainty and next evidence step

* **The POC was not executed.** Section 1 item 4 rests on reading `SCR_chaos_adapter.gml` (`chaosAnchorOffset`, `SCR_cc_new(x, y − offset)`, publish `+5`), `SCR_chaos_level.gml` and `OBJ_chaos_zone/Create_0.gml` at POC `68615389…`, plus Research's own assertion `chaosAnchorOffset == 5` (`tests/test_collision_geometry.py`). Prediction to check on Windows with the POC player trace (`chaosPlayerTrace`; `draw` events print `core_y` and `instance_y`): THZ1 `core_y` 653 → 654 within two updates and `instance_y` 659 at rest; THZ2 393 → 398; THZ3 219 → 238.
* If the POC rest instance y differs from ROM rest + 5, the cause is POC collision, not the ROM start table; G1-B should then record a known exception and keep the accepted visuals rather than add a Y offset.
* The sprite rectangle comes from one idle frame; other animation frames are outside this question.
* The camera Y follow (about +1 per update toward screen anchor y 112) is observed, not re-derived; vertical follow clamps near map edges are outside RQ4.
* The 18 acts are measured at idle with no input; no hazard contact occurred within 200 passes in any act.

## 7. Reproduce

```
python tools/rq4_start_registration.py ROM            # rewrite data/rq4/start-registration.json
python tools/rq4_start_registration.py ROM --check    # byte compare (about 40 s)
python tools/rq4_start_registration.py --validate     # no ROM
python tools/rq4_start_registration.py --table        # re-render the handoff table
python -m unittest tests.test_rq4_start_registration  # ROM tests skip without the ROM
```
