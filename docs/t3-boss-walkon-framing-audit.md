# T3: boss walk-on and widescreen framing audit

Research only (read-only audit of the accepted POC). ROM: Sonic Chaos (Europe) v1.2, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607` (verified, never committed).
Research base `f1047e5c63df1f0f408b5f7802377f108b227d23` (T2, which contains V1/T1 `c956688`). POC read only at C1-I `69527335011bacf22ff16bd25d3a94874a1fa563` (clean checkout, nothing modified; no AGENTS edit).
**The final V1/T1 SHA was not supplied; nothing below compares it.** Every statement about the POC is about C1-I source and the node VM model of that source, not GameMaker and not Windows. Section 12 gives the one-line re-baseline for when the SHA arrives.

Machine-readable: `data/t3/` (`rom-series.json`, `frame-extents.json`, `poc-series.json`, `boss-walkon-summary.json`, `boss-framing-matrix.json`, `adapter-register.json`, `discrepancy-register.json`).
Tools: `tools/t3_boss_walkon_audit.py` (ROM series, decoded frame extents, derived summary), `tools/t3_poc_boss_run.js` (POC series, needs the checkout), `tools/t3_register.py` (matrix, adapter and discrepancy registers, tables). Tests: `tests/test_t3_boss_walkon_audit.py` (26, ROM-free, 0.1 s).
Evidence classes: **BYTE-VERIFIED** (decoded ROM: mapping-frame extents), **EMULATED** (unmodified ROM in the approximate SMS harness, 256 px only), **SYNTHETIC** (the arrival position is injected; stated), **POC-SOURCE MODEL** (shipped GML executed in the POC's own node VM harness).

## 0. Answers in brief

| # | Observation | Cause | Class |
|---|---|---|---|
| 1 | GPZ3: camera rolls backwards during the intro | At creation the POC writes the **canonical** right limit 1664, but the fight camera target is width-adjusted (1664-(W-256) = 1572 at 348). The camera therefore runs forward to 1663 and the pan then retreats **92 px** to 1571 at 1 px/update (91 updates), dragging Sonic back 65 px through the viewport clamp, while the head is still invisible. At 256 target and limit coincide, so nothing retreats | proven gap (T3-01) |
| 2 | MGHZ3: camera pans upwards | Two movements. In the ROM the pan Y target is 256 and, with Sonic standing, the camera Y moves **2 px** in total. The POC adds an **upward 29 px (256) / 32 px (348) scroll the moment the boss exists** (modes 1-2 keep the pre-C1-I rule Y = player.y - h/1.5) and then pans back down 18 / 21 px | proven gap (T3-03) |
| 3 | "Other zone-specific behaviour" | (a) **Takeover step at creation** in GPZ3, SEZ3, AQZ3 (256: camera jumps backwards 12 px, Y 11-19 px in one update; MGHZ3 7 px/update upward for 4 updates); (b) **AQZ3 never locks the arena**: the trigger does not lower the right limit, so the camera runs ahead and then rolls back 166 px (256) / 76 px (348); (c) **EEZ3 pan start**: a 49 px (256) / 25 px (348) vertical camera snap (model-derived, needs a Windows look); (d) THZ3 = T2-01/T1-01 (no clamp, snaps); (e) wider exposure of the arrival (THZ3, MGHZ3: sliver becomes a nearly whole sprite) | T3-02, T3-05, T3-06, T3-08 |
| 4 | Is the walk-on one mechanism? | **No.** The ROM has six different entries: THZ3 walks in by its own motion, GPZ3 relocates then emerges in place, SEZ3 relocates then drops from above, MGHZ3 is revealed by the pan, AQZ3 flies parts in from the right, EEZ3 relocates, stays invisible and appears at the right edge. There is no universal screen-edge rule (section 7) | T3-07 |

Recommendation in one line: four small camera-only packages (section 10: T3-A boss modes 1-2 keep the C1-I follow, T3-B AQZ3 trigger lock, T3-C GPZ3 limit, T3-D EEZ3 pan Y) in the camera-module package already proposed for THZ3 in T2; the entry presentation at 348 stays as it is pending an F5 look (D-T3-2). No boss, sprite or world coordinate moves.

What is **correct**: every pan ends where the ROM puts it (THZ3 (1679,78), GPZ3 (1663,96/97), SEZ3 (2975,462), MGHZ3 (3060,256), AQZ3 (1727/1728,78), EEZ3 (1951,333)) at 256; boss world coordinates, relocations and state order match the ROM in all six zones; the widescreen target positions are deliberate and documented (section 4). The defects are in the camera **between** creation and the pan, not in the arena composition.

## 1. Scope, scenarios and limits

Scenario (`data/t3/*-series.json`): Sonic starts on the act floor `back` px left of the boss placement (THZ3 376 because its floor starts at X 1480, EEZ3 260, others 480), state 1, **hold** = RIGHT held for the whole run (a player who keeps running, the T2 convention), **stop** = RIGHT released at the first update the boss camera owner is past the trigger (a player who waits). 450 updates each. Widths 256x192 and 348x196. POC frame order is OBJ_chaos_zone Step_2 (adapter step, objects phase, ordinary follow if allowed, then every boss camera step).
Update numbers are scenario-relative (the injected start differs between ROM and POC only through the creation distance); compare the deltas ("u+n after creation"). In the ROM runs GPZ3, AQZ3 and EEZ3 are created while Sonic is still settling from the injected start, so absolute ROM Y totals in those zones include that settling; use the `stop` rows and the pan columns for vertical comparisons.
Limits: approximate VDP/IRQ harness; ROM at 256 only (a 348 ROM does not exist; "ROM camera in a 348 window" in Table 4 only re-projects the ROM scene); no forced defeats, so camera **release** is classified from code (section 8) and T1; MGHZ3 `hold` ends with Sonic walking into the arena pit (T2), so MGHZ3 vertical numbers are quoted from `stop`; no GameMaker or Windows run; V1/T1 final SHA unavailable.

## 2. Canonical ROM walk-on, six zones (EMULATED, BYTE-VERIFIED extents)

Mapping extents are decoded from bank `$0F` (THZ3 ±20 x 48, GPZ3 head/segment ±12 x 32, SEZ3 ±20 x 80, MGHZ3 ±16 x 48, AQZ3 body ±20 x 64, EEZ3 ±16): a boss is "visible" when any piece lies inside the view. Table 1 (ROM, 256 px, RIGHT held; "u+n" = updates after creation):

| zone | created (boss screen X) | relocation | right limit lowered | pan start..end | first visible (anchor screen; columns) | combat state begins | Sonic left of boss at first visible |
|---|---|---|---|---|---|---|---|
| THZ3 | u39 (346) | none | u+18 (1658) | u+102..u+154 | u+103 (271,109; 5) | u+171 | yes |
| GPZ3 | u67 (338) | u+1 (1728,270)->(1856,270), screen (462,220) | u+1 (1664) | u+130..u+194 | u+194 (193,173; 24) | u+194 | no |
| SEZ3 | u67 (338) | u+102 (3200,622)->(3136,430), screen (209,-83) | u+16 (2922) | u+101..u+153 | u+150 (161,1; 40) | u+103 | no |
| MGHZ3 | u67 (338) | none | u+16 (2991) | u+101..u+153 | u+108 (268,1; 4) | u+103 | yes |
| AQZ3 | u67 (338) | u+102 body (1856,238)->(1856,14), screen (209,-114) | u+32 (1642) | u+101..u+182 | u+226 (259,136; 1) | u+103 | yes |
| EEZ3 | u11 (340) | u+102 (2080,494)->(2208,494), screen (337,108) | u+33 (1866) | u+101..u+182 | u+327 (257,160; 15) | u+327 | yes |

Common ROM facts: every boss is created off-screen right (screen X 338-346) in state 0, **invisible** (mapping frame 0) until its entry; the left limit is raised to the camera every update before the trigger and the right limit is lowered to the camera at the trigger (limit trails the camera by one scroll step: `limit = camera-4`); the camera **never moves left** (x retreat 0 in all 12 ROM runs); Sonic never exceeds screen X 251; the HUD slot wait gates the pan (state 2 -> 3, about 100 updates after creation; GPZ3 waits for the camera-ready gate instead, 130); the pan is 1 px/axis/update (2 sampled). The camera step at the creation update equals the ordinary follow step (X +4, Y 0..5): **there is no takeover**.

Per zone:

* **THZ3** (`$50`): no relocation. State 18 starts at the pan with X velocity -128 (-0.5 px/update); the anchor is at screen X 271, left extent 251, so 5 columns are visible and the camera pans +16 px at the same time. State 18 ends when the anchor is 223 px right of the live camera (world 1902), state 6 begins. Arrival from the right by the boss's own motion.
* **GPZ3** (`$51`): the head is moved 1728 -> 1856 one update after creation (screen 462), keeps frame 0 until the camera-ready gate (both axes within 4 of (1664,96)), then appears in one update at screen (193,173) (state 7, 24 columns) and rises. The right limit is **world-fixed** (1664, exclusive) 270 px ahead of the camera at creation: the camera runs into it by itself. Nothing arrives from the right and the head is left of Sonic (Sonic hugs the clamp at screen 246).
* **SEZ3** (`$54`): at state 3 the anchor jumps to (3136,430): screen X 209, screen Y -83. State 6 begins at once; the body falls and enters through the top edge at u+150 (full width, one pixel row at first). Sonic can be right of the boss (T2-14).
* **MGHZ3** (`$56`): X stays 3269. State 11 begins at the pan with the anchor at screen (272,-4); the pan (+52 px in the hold run, +65 in the stop run) brings its left edge in from the right edge (4 columns at first in the hold run) while it descends. The pan target Y 256 is also the bottom limit; with Sonic standing the camera Y is 258 at the trigger.
* **AQZ3** (`$59`): at state 3 the body is moved to y 14 (above the screen); the visible parts (`$5A`, frame 29) are created off-screen right (WORLD 2048 = EDGE(RIGHT,+65) at the settled camera) and fly in: first visible 1 column at screen X 259.
* **EEZ3** (`$5E`): at state 3 the anchor jumps +128 (screen 337), stays invisible through state 12 while the pan brings it to screen 257, and state 6 shows it there (15 columns) and walks it left. The ROM pans the camera Y 1 px/update from 387 to 334 (the bottom limit is written first).

## 3. POC C1-I at 256 and 348 (POC-SOURCE MODEL)

Full numbers: `python tools/t3_register.py --tables` (Tables 2 and 3 for `hold` and `stop`). The rows that matter (RIGHT held; camera X,Y; boss = screen anchor; Sonic = screen X):

| zone | event | ROM 256 | POC 256 | POC 348 |
|---|---|---|---|---|
| GPZ3 | creation | u67 cam (1390,50) | u101 cam (1380,139) | u89 cam (1294,146) |
| GPZ3 | pan start | u197 cam (1662,161) boss (194,109) Sonic 247 | u230 cam (1663,146) boss (193,124) Sonic 247 | u218 cam (1662,143) boss (194,127) Sonic 314 |
| GPZ3 | pan end / combat | u261 cam (1663,97) boss (193,173) | u280 cam (1663,96) boss (193,174) | **u309 cam (1571,112)** boss (286,158) Sonic 340 |
| MGHZ3 (stop) | creation | u67 cam (2931,258) | u102 cam (2937,260) | u90 cam (2843,263) |
| MGHZ3 (stop) | pan start | u168 cam (2995,258) boss (274,30) | u202 cam (**2982,239**) boss (287,49) | u190 cam (**2939,239**) boss (330,49) |
| MGHZ3 (stop) | pan end | u233 cam (3060,256) boss (209,176) | u280 cam (3060,256) boss (209,171) | u198 cam (2968,256) boss (301,33) |
| SEZ3 | pan start | u168 cam (2926,514) | u178 cam (2913,493) | u166 cam (2870,487) |
| SEZ3 | pan end | u220 cam (2975,462) | u240 cam (2975,462) | u173 cam (2883,462) |
| AQZ3 | pan start | u168 cam (1646,129) | u191 cam (**1893**,109) | u180 cam (**1803**,106) |
| AQZ3 | pan end | u249 cam (1727,78) | u356 cam (1728,78) | u255 cam (1728,78) |
| EEZ3 | pan start / end | cam (1870,387) -> (1951,334) | cam (1873,**333**) -> (1951,333) | cam (1827,333) -> (1951,333) |

Camera continuity from creation to the end of the pan (Table 3, `hold`; X retreat = largest drop from the running maximum; step = pixels per update):

| zone | config | step at creation (dx,dy) | X retreat | Y travel up/down | largest pan step | Sonic max screen X |
|---|---|---|---|---|---|---|
| GPZ3 | ROM 256 / POC 256 / POC 348 | (4,0) / **(-12,-11)** / (-4,-4) | 0 / 12 / **92** | 64/111 / 62/8 / 46/8 | 1 / 1 / 1 | 248 / 247 / 340 |
| SEZ3 | ROM / 256 / 348 | (4,0) / **(-12,-16)** / (-4,-4) | 0 / 12 / 4 | 52/0 / 48/0 / 48/0 | 1 / 1 / 4 | 248 / 247 / 339 |
| MGHZ3 (stop) | ROM / 256 / 348 | (4,0) / (0,**-7** x4) / (0,-4 x8) | 0 / 0 / 0 | **2/0** / **29/18** / **32/21** | 1 / 1 / 4 | 220 / 207 / 253 |
| AQZ3 | ROM / 256 / 348 | (4,5) / **(-12,-19)** / (-4,-4) | 0 / **166** / **76** | 51/54 / 51/0 / 51/0 | 2 / 1 / 1 | 250 / 315 / 340 |
| EEZ3 | ROM / 256 / 348 | - / (2,0) / - | 0 / 0 / 0 | 53/113 / 49/0 / 25/17 | 1 / **49** / **25** | 251 / 247 / 339 |
| THZ3 | ROM / 256 / 348 | (4,0) / (0,0) / (0,0) | 0 / 0 / 0 | 53/0 / 48/0 / 48/0 | 2 / 1 / 1 | 248 / **443** / **441** |

(Y travel = pixels up/down summed over the window. The ROM down totals in GPZ3, AQZ3 and EEZ3 include the injected start settling, see section 1.)

(THZ3 Sonic X 443/441: T2-01, no clamp in modes 1-2; this audit only reproduces it.)

## 4. Recovered ROM behaviour versus deliberate adapters versus unintended rules

`data/t3/adapter-register.json` lists 30 items with code anchors (line numbers at C1-I; `tools/t3_register.py --verify-anchors <checkout>` re-finds them). Classification:

**Recovered ROM behaviour (keep).** Pan tables `$9808` and their end positions at 256 (A-THZ-4); THZ3 state 18 -> 6 at 223 px of the live camera (A-THZ-5); SEZ3 and MGHZ3 `$0356` right-limit lock at the trigger (A-SEZ-4, A-MGH-4); EEZ3 follow with the boss-written limits (A-EEZ-3); GPZ3 head relocation 1728 -> 1856 (matrix).

**Deliberate widescreen adapters (documented in the code headers).**
* Pan targets that keep the canonical RIGHT edge and expose the extra width to the left: GPZ3 1664-(W-256) (A-GPZ-1), SEZ3 3232-W (A-SEZ-1), MGHZ3 boss at RIGHT-48 (A-MGH-1). Fight Y 112 for tall wide views (A-GPZ-2).
* Pans bounded to 4 px/update per axis at wide: SEZ3, MGHZ3 (A-SEZ-2, A-MGH-2). GPZ3 and AQZ3 keep 1 px.
* THZ3 arena extension (+W-256, A-THZ-2) and creation band from the live edge (A-THZ-1).
* AQZ3 `$5A` parts translated in VIEW space by `W-256+ceil(wait/2)` and hidden until the pan has been settled 16 updates (A-AQZ-3/4). EEZ3 state-3 relocation `+128+(W-256)` and a widened trigger (A-EEZ-1/2): this one **does change a world coordinate** (2300 at 348).
* Clamp EDGE(LEFT,+16)..EDGE(RIGHT,-9) for GPZ3, MGHZ3, SEZ3, AQZ3 (A-SH-2).

**Legacy non-ROM rules (no adapter note, no ROM basis; pre-C1-I zone cameras that C1-I did not reach).** THZ3 mode 1 centre follow and frozen Y, mode 4 centring (A-THZ-3/6); GPZ3 modes 1/4 centre follow with Y = player.y - h/1.5 (A-GPZ-4); SEZ3, MGHZ3, AQZ3 modes 1-2 centre follow with Y = player.y - h/1.5 (A-SEZ-3, A-MGH-3, A-AQZ-2); the shared switch that turns the C1-I ordinary follow off for every boss owner (A-SH-1). The ROM has no such owner switch before the pan.

**Omissions of a ROM rule.** GPZ3 width-adjusted right limit (A-GPZ-3); AQZ3 `$9771` left raise and right lock (A-AQZ-1); EEZ3 pan Y clamp that the ROM does not have (A-EEZ-4).

## 5. GPZ3: the rollback and its width-adjusted target

ROM: `$9A99` writes the exclusive right limit 1664 when the head is created and relocates it 1728 -> 1856; the camera follows Sonic and simply stops at 1663 (right edge 1919). The intro pans Y 161 -> 97 (64 updates) with X 1662 -> 1663, and the head appears at screen (193,173). The camera never moves left.

POC at 348 (hold; `data/t3/poc-series.json` GPZ3 w348):

| update | event | camera | Sonic world / screen X | head screen X |
|---|---|---|---|---|
| u89 | boss controller active (mode 1) | (1294,146), -4 px takeover step | 1460 / 166 | 562 |
| u183 | camera approaching the canonical limit | 1662 | 1836 / 174 | 194 |
| u200 | camera at the canonical limit | 1663 | 1904 / 241 | 193 |
| u218 | `$9AED`: mode 2, pan to the width-adjusted target | 1662 | **1976** / 314 | 194 |
| u240 | retreat in progress | 1640 | 1980 / 340 | 216 |
| u280 | | 1600 | 1940 / 340 | 256 |
| u306 | | 1574 | 1914 / 340 | 282 |
| u309 | settled; head appears (state 7, frame 2) | **1571**, Y 112 | **1911** / 340 | 286 |

Mechanism: `chaos_51_fight_camera_target(w) = 1664-max(0,w-256)` (line 24) keeps the canonical right edge 1919 by pulling the fight view 92 px to the left, but the creation callback still writes `camera_right=1664` (line 114), so the approach follows Sonic to 1663 (right edge 2011) first. The mode 2/3 step (line 293, `cp_x+=sign(cp_target-1-cp_x)`) then walks the camera back 1 px/update, and the viewport clamp (`SCR_chaos_adapter.gml:199`) carries Sonic with it (1976 -> 1911 world, the clamp rectangle's right edge is 1910 at both widths). At 256 target and limit are the same number, which is why only 348 shows it. How much camera retreats depends only on how far Sonic got before the head's timed intro reaches `$9AED` (129 updates after creation in every config): stopping at world X <= 1650 retreats 8 px (the takeover only), 1700 -> 31 px, 1740 -> 71 px, 1760 -> 91 px, >= 1800 -> 92 px (`gpz3_w348_stop_x_sweep` in `poc-series.json`; the head's anchor is 1856). Any approach that walks or runs the last 200 px shows some of it and a run-through shows all 92 px. It is not hidden by anything: the head is still invisible. The report does not say at which width it was seen; the rollback cannot occur at 256.

The adapter's intent (canonical right edge, extra width to the left) is sound and costs nothing in mechanics; the defect is that the limit was not given the same adjustment. Making the limit `1664-(W-256)` at creation lets the existing follow stop at 1571 by itself: no X pan is left to do, Y converges 1 px/update as now (section 10, T3-C). Side effect to check: the clamp rectangle is unchanged on the right (1910) and 92 px wider on the left.

## 6. MGHZ3: the vertical pan and the timing at widescreen

ROM (stop): the camera Y is 258 at the trigger, the pan table row 3 (`(-208,-32)` from the anchor (3269,288)) gives Y 256, and the bottom limit is written as 256: Y moves 2 px in total (X +65 over 65 updates). When Sonic is lower or higher the ordinary follow keeps Y within +-16 of its lead, so the canonical vertical pan is at most about 30 px (2 px in the standing run above).

POC (stop):

| | 256 | 348 |
|---|---|---|
| ordinary follow before creation | Y 267, Sonic screen Y 99 | Y 267 |
| creation u102 / u90 | mode 1: Y 267 -> 238 at 7 px/update (4 updates) | Y 267 -> 235 at 4 px/update (8 updates) |
| Sonic screen Y after takeover | 128 | 131 |
| pan (state 3) | u202..u280: Y 239 -> 256 (+17), X 2982 -> 3060 at 1 px | u190..u198: Y 239 -> 256 (+17), X 2939 -> 2968 at 4 px |
| total Y travel | 29 up, 18 down | 32 up, 21 down |
| boss at pan end | screen X 209 | screen X 301 (RIGHT-48 + 1) |

Cause: `chaos_56_follow_y` (line 437) is `clamp(round(player.y - h/1.5))`, a rigid vertical rule from before C1-I that the boss camera still uses in modes 1-2 (line 519), and `chaos_camera_follow_allowed()` turns the C1-I follow off from creation. The ordinary C1-I follow holds Sonic at screen Y 99 (lead 96, zone +-16); the old rule wants 128, so the camera scrolls up about 30 px the instant the boss appears and the `$9808` pan later brings it back. This is the most likely source of the reported "panning upwards" (model-derived, not yet seen on Windows); the ROM's own pan towards Y 256 is real but tiny in this run.

Timing at widescreen: creation is measured from the live right edge (u90 vs u102), so everything starts earlier in absolute time; the HUD wait that gates the pan is the same 100 updates after creation (pan start u190 vs u202). The lock (u117) is player-distance based and identical. The wide pan is bounded to 4 px/update: it lasts 8 updates (X 29 px, Y 21 px) against 78 at 256 (X 78 px at 1 px), so at 256 the camera is still panning for 76 updates of the first fight phase and at 348 for 6. The boss starts descending (state 11) at the pan start in both; the final composition differs by design (boss at screen X 209 vs 301). A ROM-rate pan at 348 would last 29 updates (the longer axis), still shorter than at 256, so the 4 px bound is not needed for timing parity (decision D-T3-3).

## 7. Where the wider view exposes the boss, and how each boss arrives

Table 4 (RIGHT held; first update any boss piece is inside the view; anchor screen X,Y; visible columns):

| zone | ROM 256 | ROM scene in a 348 window | POC 256 | POC 348 |
|---|---|---|---|---|
| THZ3 | u142 (271,109; 5 col) | u142 (271,109; **40 col**) | u177 (275,121; 1 col) | u159 (330,115; **38 col**) |
| GPZ3 | u261 (193,173; 24 col) | same | u279 (193,173; 24) | u307 (**283**,158; 24) |
| SEZ3 | u217 (161,1; 40 col) | same | u223 (178,1; 40) | u211 (**253**,1; 40) |
| MGHZ3 | u175 (268,1; 4 col) | u175 (268,1; **32 col**) | u218 (271,42; 1) | u192 (322,1; **32**) |
| AQZ3 | u293 (259,136; 1 col) | u203 (350,121; 2 col), **90 updates earlier** | u194 (158,132; 8)* | u395 (351,145; 1) |
| EEZ3 | u338 (257,160; 15 col) | u338 (257,160; **32 col**) | u376 (257,161; 15) | u344 (349,161; 15) |

\* AQZ3 POC 256 is the camera-overshoot artefact of section 8.

Reading:
* **Exposed more completely by the wide window** (same ROM camera): THZ3 (the sliver of 5 columns becomes the whole 40-column sprite), MGHZ3 (4 -> 32), EEZ3 (15 -> 32). GPZ3 and SEZ3 are unaffected because their sprite appears whole in place at 256 too. **Exposed earlier**: only AQZ3 (the `$5A` parts, 90 updates earlier).
* The POC answers differently per zone: EEZ3 and AQZ3 carry **relocation adapters** (EEZ3 world +92, AQZ3 view-space translation) that restore the ROM sliver (15 and 1 columns); THZ3 and MGHZ3 do not, so at 348 THZ3 appears with 38 of 40 columns at screen X 330 (18 px inside the right edge) and MGHZ3 with 32 of 32 at 322; GPZ3 and SEZ3 appear 90 px further right than at 256 (283 vs 193, 253 vs 161) because the fight view was moved left.
* Three distinct mechanisms must not be conflated: **arriving from the right** (THZ3 by its own motion; AQZ3 parts), **being relocated** (GPZ3, SEZ3, AQZ3 body, EEZ3 in the ROM; plus the two POC relocation adapters), **becoming visible through camera movement** (MGHZ3 and EEZ3 reach the right edge by the pan; the ROM never "slides" them in).

Entry modes (ROM) and what 348 does to each: THZ3 appears with 38 of 40 columns, anchor 18 px inside the right edge (motion unchanged); GPZ3/SEZ3 unchanged apart from screen position; MGHZ3 is no longer revealed by the pan (full sprite at pan start); AQZ3 and EEZ3 restored by adapters. The register holds the full text (`entry_mode` in `boss-framing-matrix.json`).

## 8. Other findings

**AQZ3 does not lock the arena (T3-05).** `case $9771` (SCR_chaos_aqz_boss.gml:285) copies the right limit and sets mode 2 but, unlike SEZ3 (line 247) and MGHZ3 (line 192), never lowers the right limit to the camera, and the left limit is raised only once at creation. The ROM locks at the trigger (limit 1642 with the camera at 1646 on u99). In the POC the limit stays 2304 until the pan, so the follow keeps scrolling: with RIGHT held the camera is at X 1893 when the pan begins (ROM 1646), then retreats **166 px** at 1 px/update over 165 updates (348: 76 px); a player who stops at the trigger still sees 101 px (22). In the model Sonic then stays at world X 2043 (core next state `$1F`) while the camera retreats past him, ending at screen X 315 of 256 (cause not examined; possibly specific to the harness, so it is not used as evidence). The lock is a ROM rule that was never ported, not an adapter.

**Creation-time takeover (T3-02).** Table 3: at 256 GPZ3, SEZ3, AQZ3 step (-12,-11), (-12,-16), (-12,-19) in one update, MGHZ3 -7 on Y for 4 updates; at 348 the same takeover is spread at 4 px/update. THZ3 and EEZ3 have no such step. The ROM has none.

**EEZ3 pan start (T3-06, unresolved).** `cp_y=min(cp_y,cp_b.bottom-1)` (SCR_chaos_eez_boss.gml:323) clamps the camera Y to the freshly written bottom limit in the first pan update: 382 -> 333 (-49) at 256 and 358 -> 333 (-25) at 348. The ROM writes the same bottom limit and then pans 1 px/update (387 -> 334). If the model is faithful there is a visible vertical jump; it needs a Windows capture (R-T3-3).

**Sonic framing during modes 1-2 (T3-09).** With the left limit raised and a centre target the camera stalls until Sonic passes the centre: Sonic's screen X at the lock is 132 (256) / 178 (348) in SEZ3 and MGHZ3, 116 in the ROM.

**THZ3**: T2-01/T2-02 (no clamp) and T1-01/02 (snaps, position dependent) stand; the pan, the walk-on world positions and the 223-px rule are ROM-faithful at both widths.

**Camera release (not re-traced; code-level).** THZ3 mode 4 centres on Sonic in one update (A-THZ-6; T1: 33 px example). GPZ3 mode 4: X centre follow (snap at 256, 4 px/update wide), Y stays at the fight Y; release writes `D280=camera, D282=1920, D27E=96`. SEZ3, MGHZ3 and AQZ3 mode 4: ROM-form X follow after the clear (lead slew, zone +-8, cap 7 at 256; 4 px/update wide) with Y from the legacy rule (snap at 256); AQZ3 at wide holds the fight view and relies on the state-`$20` freeze. EEZ3: limits restored from the saved bytes, ordinary-form follow. T1 traced THZ3, SEZ3, MGHZ3; GPZ3, AQZ3, EEZ3 release are unverified here (T3-11).

## 9. Presentation options and their compromises

**Arena framing at wide (per zone, not universal).**

| option | what it does | gains | costs | where it is today |
|---|---|---|---|---|
| A: keep the canonical LEFT edge, extend right | camera X as in the ROM; view reaches W-256 px past the canonical arena edge | no retreat, ROM camera series unchanged; boss comes in from the same side | reveals terrain/objects beyond the arena right edge; arena right wall (clamp) moves, THZ3 needed a patrol extension | THZ3, AQZ3, EEZ3 |
| B: keep the canonical RIGHT edge, extend left | pan target shifted left by W-256 | arena and clamp identical on the right; the extra view shows ground already walked | the camera may have to move left of where the follow carried it (GPZ3 rollback) unless the limit is adjusted too; boss ends further right on screen | GPZ3, SEZ3, MGHZ3 |
| C: centre on the boss | target relative to the boss, not the ROM pan | symmetric | invents a framing the ROM never had | none (MGHZ3 RIGHT-48 is a B variant) |

**Retreat avoidance.** (1) Give the limit the same width adjustment as the target (GPZ3): no motion at all, one expression; (2) lock at the current camera when the pan would retreat: shifts the arena and breaks the canonical right edge; (3) keep the retreat but slow it: still rolls backwards, longer; (4) pan faster: a visible snap instead. Recommended (1) for GPZ3 and the ROM lock for AQZ3; in the runs of this audit the lock camera of the other zones is left of the pan target, so their pans only move forward (assert it in the acceptance numbers).

**Entry presentation at wide (needs a Manager decision, D-T3-2).**
* E1 accept (THZ3, MGHZ3): the boss appears inside the right edge region (18 and 26 px from it) with the ROM motion and timing; no coordinates change. Cost: a pop instead of a slide.
* E2 world spawn shift by W-256 (the EEZ3 precedent): restores the sliver but moves a world coordinate and lengthens THZ3's walk (34 px -> 126 px, 252 updates at 0.5 px) unless the end position is also moved. Not recommended: no ROM evidence supports a coordinate change and the Manager rule is to preserve coordinates.
* E3 view-space translation (the AQZ3 precedent): coordinates stay, but draw and contact move together; contact uses the translated X in AQZ3. A new instance of this for THZ3/MGHZ3 would be speculative sprite movement.
* E4 frame the wide camera so the spawn is outside the view (B for THZ3): the boss then walks the extra 92 px, changing the fight start; not recommended.
Recommended: E1, judged at F5; keep the two existing adapters as they are.

**Wide pan rate.** ROM 1 px/axis/update everywhere. SEZ3/MGHZ3 bound it at 4 px; GPZ3, AQZ3, EEZ3 do not. With the lock camera always closer to the target at wide than at 256, the ROM rate would take at most 29 (MGHZ3) / 25 (SEZ3) updates, shorter than at 256, so the bound is optional (D-T3-3).

## 10. Recommended zone-specific plan (small packages)

**T3-A: boss modes 1-2 keep the C1-I ordinary follow** (GPZ3, SEZ3, MGHZ3, AQZ3; THZ3 inside the T2/T1 camera-module package, decision D-T2-3). In `chaos_camera_follow_allowed()` stop treating an active boss in mode 0/1/2 as an owner; supply the limits from the boss (left = camera each update, right = camera after the trigger, GPZ3's fixed limit) through `chaos_camera_ordinary_limits`; delete the per-zone `chaos_5x_follow_x/_y` use in modes 1-2 (about 5 lines per zone). Modes 3/4 and every pan target stay. Removes T3-02, T3-03, T3-09 and the THZ3 Y freeze with one rule.
**T3-B: AQZ3 trigger** (`$9771`): `chaos_59_left_limit` every update and the `$0356` right lock at the trigger, copied from SEZ3/MGHZ3 (3 lines). Removes T3-05.
**T3-C: GPZ3 limit**: `camera_right = 1664 - max(0, viewport_w - 256)` at `$9A99` (1 expression). Removes T3-01; the mode 2/3 X step then has nothing to do at either width.
**T3-D: EEZ3 pan Y**: drop the `min(cp_y, bottom-1)` in the pan branch (1 line); keep the limit for the follow branch. Removes T3-06 if confirmed.
**Not in scope unless the Manager decides**: entry presentation (E1 stays), wide pan rate, release changes.
Nothing here moves a boss, changes a state script, a hit box or a world threshold. The four packages touch `SCR_chaos_camera.gml` and the camera branches of the five boss scripts; they can ride one Windows package with T2/T1 PKG-T1A and the clamp predicate.

**Numeric verification** (node harness, the T3 runner as the oracle; widths 256, 348 and 400; scenarios hold and stop; `tests/test_t3_boss_walkon_audit.py::TargetContract` states the rules):
1. Camera X never retreats between boss creation and the end of the pan (retreat 0) in every zone, width and scenario.
2. The camera step at the creation update is within [0,7] in X and |dy| <= 7 (equal to the ordinary follow step; differential check against the accepted parent on the same input until the creation update: identical series).
3. Standing Sonic (stop): |camera Y at pan start - camera Y before creation| <= 16 in THZ3, SEZ3, MGHZ3; MGHZ3 total Y travel <= 4 at 256; pan end Y 256.
4. GPZ3: final camera (1663,96) at 256, (1571,112) at 348, (1519,112) at 400 (= 1664-(W-256)-1); right screen edge 1919 at the fight at every width; Sonic max world X 1910 at every width.
5. AQZ3: from the trigger update the right limit <= camera+8 and camera X constant until the pan; pan end X 1727/1728; Sonic screen X <= W-5 in every update.
6. EEZ3: largest Y step in the pan <= 1 at 256 (<= 4 if the wide bound is kept).
7. SEZ3/MGHZ3: pan end (2975,462)/(3060,256) at 256, (3232-W-1,462)/(3269-(W-48)-1,256) at wide, unchanged.
8. Unchanged sets (regression): boss world coordinates, relocations (matrix), state sequences, fight-start positions (THZ3 world 1902), first-visible columns at 256 equal the POC series of this audit.
9. Sonic screen X in [16, W-9]+slack for every update from creation to the end of the pan (T2 predicate; THZ3 needs the T2 package).

**Windows F5 criteria (new and changed behaviour only; one pass at 348, one at 256):**
* GPZ3: run straight at the head and then wait: the camera never scrolls left once it has moved right; Sonic is not carried backwards; the head rises at the right of the screen as before; the right edge of the view at the fight is the same arena column at both widths.
* MGHZ3: the moment the boss appears nothing scrolls vertically; the floor stays where it was; after the pan Sonic stands near screen Y 110; boss at the right as before.
* SEZ3 and AQZ3: no step when the boss appears; AQZ3: run right through the intro: the screen stops scrolling at the trigger, Sonic cannot leave the screen, the camera does not slide back.
* EEZ3 (if T3-D): the pan starts smoothly, no vertical jump.
* THZ3 together with the T2 package: boss comes from the right at both widths (decision E1).
* Smoke: one ordinary act clear and one boss defeat/release (SEZ3 or MGHZ3) to confirm nothing else moved.
* Capture (R-T3-1): a debug-only per-update dump of view X/Y/W/H, Sonic x/y, boss x/y/state/frame, camera owner mode for 600 updates from 300 px before each boss; the node series are the expected values.

## 11. Decisions and probes for the Manager

* **D-T3-1** bundle T3-A..D with T2/T1 PKG-T1A in one camera-module package (recommended: same files, same predicate).
* **D-T3-2** entry presentation at wide for THZ3 and MGHZ3: accept E1 (recommended) or choose E2-E4 after an F5 look.
* **D-T3-3** keep the wide pan bound at 4 px/update (SEZ3, MGHZ3) or return to the ROM 1 px.
* **R-T3-1** Windows capture of GPZ3 at 348 (expect the 92 px retreat) and of MGHZ3 (expect Y 267 -> 235 -> 256) before the fix, to confirm the model.
* **R-T3-2** AQZ3 running through the intro at 256 and 348 (expect the 166/76 px retreat).
* **R-T3-3** EEZ3 pan start (expect the 49/25 px jump).
* **R-T3-4** supply the final V1/T1 SHA; re-run the tools (section 12).
* Not authorised / not done: any POC change, any boss or sprite movement, release traces for GPZ3/AQZ3/EEZ3, GameMaker or Windows runs. An attempt to patch a scratch copy of the POC (outside the repository) to demonstrate the fixes was denied by the session's permission check and was not retried; the numbers in section 10 are therefore derived from the ROM series and the arithmetic of the adapters, not from a prototype.

## 12. Reproduction and limits

```text
python tools/t3_boss_walkon_audit.py ROM --write|--check rom       # ~40 s; ROM series + frame extents (needs z80==1.2.0, z80dis==1.0.6)
POC=<checkout> node tools/t3_poc_boss_run.js --write|--check        # ~3 s; POC series (read only; ignores the checkout head when comparing)
python tools/t3_boss_walkon_audit.py --write|--check summary        # derived events and metrics, no ROM, no POC
python tools/t3_register.py --write|--check                         # matrix, adapter and discrepancy registers
python tools/t3_register.py --tables                                # markdown tables
python tools/t3_register.py --verify-anchors <checkout>             # adapter anchors still present / moved
python -m unittest tests.test_t3_boss_walkon_audit
```

Re-baseline for the final V1/T1: `POC=<final checkout> node tools/t3_poc_boss_run.js --check`; if DIFFERENT, `--write`, then `--write summary`, `python tools/t3_register.py --write` and read the diff of `boss-walkon-summary.json` (the tests' "known violations" test is the baseline that should shrink).
Limits: see section 1. Additionally: ROM first-visible uses decoded piece boxes (frame extents), not the SAT, because the approximate VDP cannot separate boss sprites from Sonic's hurt frames; widths other than 256 and 348 are not run; the second EEZ3 encounter and the GPZ3 left boundary are not examined; the POC scenarios use real terrain, scripted input and the shipped player adapter, but the zone End Step's AQZ/EEZ view clamps are not modelled (they bound the world edge, not the arena).
