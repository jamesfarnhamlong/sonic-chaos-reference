# M1 — SMS Tails and original frontend contract

**23 October corrective addendum:** `m2r2-character-interaction-matrix.md` closes
the missing normal Rocket-monitor lifecycle: initialization converts parameter4
to Ring1 for Tails before artwork selection, and breaking it grants +10 rings.
The Rocket reward gate below remains correct but is not the whole pickup chain.
M2-R2 also adds paired mapped Spring Shoes execution and life-monitor art selection.

22 October 2026. Research-only, original **Master System Europe v1.2**. POC read-only `7476affc6ed7626dabf69b446cdab0c9c3d7492e`. New evidence: hash-gated static ROM tables/instructions, not new ROM execution. Existing G0/U4-B/U5-A/EEZ emulator observations are reused with their original limits. No Game Gear behaviour inferred.

## Evidence package and how to use it

`data/m1/tails-asset-census.json` contains 89 type-2 mapping entries (0 blank, 88 nonblank), 54 state scripts `$00..$35`, per-frame transfer source/hash, canvas/origin/index/RGBA hashes, 18 act palette bindings, 40 POC Tails-named resources and exact script reference owners, title/attract tables and selected mnemonic listings with region hashes. Regenerate with:

```powershell
python tools/m1_census.py PRIVATE_ROM --poc ACCEPTED_Q3_WORKTREE --check
python -m unittest discover -s tests -p test_m1_contract.py -v
```

No PNG, palette pixel array, ROM bytes or input-stream payload is emitted. The tool reuses `u5a_opening`, `thz1_object_assets`, `level_package` and `g2e_score` decoders. Static scripts list commands; **they are not a complete executable behavioural model**. FF08 alternatives, selector frames and shared callbacks must be interpreted, not flattened into an unconditional animation list. State-table presence alone is not proof of reachability. The 80-operation safety bound inherited from the script decoder must not truncate any newly used scene; full ending authority is the existing 512-op EEZ decoder/cache.

## A. Character control and movement

ROM type 1 is Sonic, type 2 Tails; `D2C8` selects it. Existing accepted POC gameplay is largely Sonic-oriented: `SCR_chaos_core`, `SCR_chaos_adapter`, `SCR_chaos_player_animation` and `SCR_chaos_visual_p1` own canonical state, publication and Sonic frame lookup. `SCR_player_sprites_tails` is legacy presentation assignment, not a canonical Tails implementation.

| Contract | ROM owner / exact result | Implementation implication / evidence limit |
|---|---|---|
| Ordinary movement | Shared `$3FEF` calls power-up/death/input/integration/terrain/contact, then tests fresh action bits `D147 & $30`. `$402A` integrates signed 8.8 speed with state/surface deltas; `$4141` selects parameters. | Reuse accepted fixed-point ownership, terrain probes and attack resolver. No independent Tails acceleration multiplier is justified. State/callback-specific differences still require paired source tests; shared code is not all-scene parity. See `docs/movement.md`. |
| Up + fresh action | `$371E..$373B`: type 1 branches to Peel-Out `$46CE`; other type tests `D443` water first, then fresh bits → `$473C`. | Tails flight is the SMS look-up/action path. Don't substitute an airborne double-jump flight trigger or Sonic Peel-Out. Water prevents this entry. |
| Flight setup `$18` | `$473C..$4774`: VX=0, VY=`$FF00`, integer Y−4, timer `D3A1=$012C` (300), clears attack bit1 and flag6 of +3, clears bit1 of +$22/+21/+23, support owner `D3C0=0`, requests state `$18`. | Preserve setter side effects and initial lift; flight is not an attacking spin. Timing is updates, not an asserted PAL wall-clock duration. |
| Flight update | `$03EC→$3EFD`: camera lead `$60`; power-up update first; water nonzero immediately calls fall `$463C`. Held Right wins over Left; integer X +=1/−1/0. Held Down wins over Up; integer Y and VY get +1/−1/0. Calls screen checks, terrain `$690B`, contact `$48BC`, then input facing `$48A7`. | Direct integer movement, not normal acceleration/integration. Horizontal input priority differs from input-facing writer (Left is checked first there); preserve both orders when opposing directions are held. Do not introduce free underwater swimming from inherited `SPR_tails_water_swim`. |
| Flight exit | `$3F61..$3F85`: `D441` bit7, timer reaching zero, ground-contact +$23 bit1 or +4 bit6 calls ordinary fall `$463C`; otherwise returns. Timer decrements after terrain/contact/facing unless the first exit applies. | Exhaustion/ceiling/contact transition order needs tests at 1→0 and simultaneous contact/water. Do not replace with an invented tired-flight mode. |
| Original screen checks | `$3F86/$3FA7`: horizontal screen X below20 or ≥244 reverses the attempted one-pixel movement; vertical below24 or ≥192 similarly reverses it. | Source 256×192 semantics are known. Integration with accepted once-prepublish wide player bounds needs an explicit adapter design; no per-owner generic clamp added silently. |
| Down + action | Shared `$3759..$3782` requests `$4701` (charge state `$0F`) before ordinary movement. | Spin Dash uses shared setter/state with Tails art. Tails state `$15` is an idle alias, so Sonic Peel-Out art/behaviour must not leak into Tails. |
| Collision / attacks | Shared `$690B`, `$48BC`, `$D503` bit1 and power selector exclusions are existing attack/terrain contracts (`docs/player-attack-badnik-audit.md`). Flight clears attack posture. | Preserve 8×24 / `$0F` 9×24 established player extent until a character-specific source discrepancy proves otherwise. Tail rotor artwork alone does not authorise an attack hitbox. |
| Power-ups | `$4ADF..$4AE5` clears Rocket reward bit3, reads player type, decrements and returns unless type1. Tails state `$11` is the stand-init alias `$8A36`; `$12` holds Tails frame `$0A`. Spring Shoes `$78B64..$78B94` has no character gate and top attachment requests12. | **Tails does not receive Sonic Rocket Shoes from this reward path.** Do not expose a Tails Rocket mode. Confirm natural monitor/attachment and expiry interactions in focused controls. Speed-up/invincibility retain shared owners; do not copy the entire Sonic state11 route. |

**Pre-implementation behavioural gates:** build deterministic ROM callback controls for ordinary walk/run/brake/jump/roll and water, flight input pairs/edges/contact/timeout, Spring Shoes and Rocket reward selection, hurt/death, carrier/loop/spring and boss release. Existing tables make these bounded recovery tasks, not a reason to invent physics. Natural Tails routes and every equipment eligibility branch have **not** been executed in this assignment. These gaps prevent claiming a fully closed implementation contract; Manager may authorise their completion as the first bounded evidence preflight of M2, before runtime edits.

## B. Animation, mappings and palette import

Tails state table is bank `$0C:$89BB`; mapping table bank `$0F:$85BF`; dynamic tile transfer table fixed ROM `$11CF`, four bytes per frame: bank, source CPU word, count of 64-byte blocks. Source offset = `bank*$4000 + cpu−$8000`. Compose original 8×16 pieces at their signed relative coordinates; transparent index0; origin = negative minimum piece coordinates. Preserve index bytes and origin, not a guessed Sonic canvas. Census stores all transfer hashes and piece-count-derived geometry. Frame0 is blank and has no canvas.

| State / use | Tails sequence and record duration | Source owner |
|---|---|---|
| Stand `$00/$01` | frame `$0A`, 8; `$00` first calls setup, then requests idle `$02` | `$8A36/$8A3A` |
| Idle `$02` | Exact variable script in census, including long holds and frames `$0A..$10`; do not replace with a two-frame generic wait | `$8A4D` |
| Look up/down `$03/$04` | `$0D` / `$11`, 6 each | `$8A8E/$8A94` |
| Walk `$05` | selector `$8CB4`: ordinary `$01..$06`; strip marker chooses `$34..$36`; side contact takes frame `$55`, duration2 | speed-high-byte duration lookup `$8CEC`: 10,8,6,4 then4; side contact before strip |
| Run `$06` | selector `$8D05`: `$07..$09`, duration2; strip `$34..$36`, duration2; clears stale strip marker off surface `$19` | **Three frames, not Sonic's four** |
| Jump `$0A` / spin | selector `$8F76`, shared counter logic | Decode selector with shared command engine; don't equate a numeric frame across characters |
| Weak spring `$0B` | `$1B..$20`; records include four-update loops and later 6/8 holds; FF08 strong-spring branch must be followed | `$8AD6`, alternate `$8B15`; census includes branch operands |
| Fall `$0E` | `$02,$03,$04,$05,$06,$01`, 8 each in repeated records | `$8B67` |
| Charge `$0F` | `$21,$22,$23`, 2 each | `$8BDD` |
| Spring Shoes `$12` | `$0A`, 4 | `$8BF3` |
| Strip tumble `$14` | `$1B..$20`, 4 each | `$8B4D` |
| Flight `$18` | `$12,$13,$14`, 4 each; entry calls `$8C6F` | `$8C5D`; sound `$B0` if `D522 &15==0`, otherwise `$C0` |
| Hurt `$1E`, death `$1F` | `$17` for6; `$18` for128 respectively, with shared callbacks | census state records; animation duration is not entire death sequence duration |
| Twist `$22` | `$24,$25,$26`, 3 each | Tails differs from accepted Sonic `$25..$29`; keep loop/transport state owners separate |
| Opening `$29` | Shared script includes selectors `$8F45` and `$8EE1`, i.e. not simply Tails ordinary run selector | Existing U5-A opening replay is accepted. Do not alter it while importing gameplay art. |
| Choice `$30` | `$01..$06`, 6 each with `$846D` callbacks between records | `$8C82` |
| Ending `$31..$33` | Own walk/run/tumble/flight script chain; `$32` includes `$15` for8, `$16` for32, then `$12..$14` for4 | census plus full `data/rom-cache/eez/ending-scripts.json`; do not truncate at80 |
| Continue `$35` | `$0F,$10`, 8 each loop; accept `$07..$09`, 4 each and shared accelerating runoff | U4-B `$8EB2/$8ECE`; already imported |

The census lists all other table entries, including aliases. A record's callback executes across its hold; timing must use the accepted animation command/counter engine, not image_speed approximations. Tile transfer frames and selector-generated frames must both be included. Underwater flight/swim art must not be invented: entry is blocked and active flight falls on water detection. Underwater ordinary palettes/poses and drowning use shared state logic but still require Tails-specific route checks.

Palette selection is stage-dependent: sprite records 6,7,8,9,10,11 for THZ,GPZ,SEZ,MGHZ,AQZ,EEZ; 18 bindings and complete-palette hashes are in census. Continue uses record7; opening record41. Those complete palette hashes differ, so an opening-colour RGBA file is not automatically the gameplay import. The census RGBA digest is explicitly palette7; index digest is palette-independent. Import per required palette or retain indexed data with an approved palette owner. No new pixel assets were written here.

### Existing assets and exact replacement owners

There are **11 authenticated imported Tails resources**: opening `SPR_chaos_opening_tails_01..06` and Continue `SPR_chaos_continue_tails_07,08,09,0F,10`. Research already records their sources in `data/u5a/opening-static.json` and `data/u4b/death-screens-static.json`; retain their accepted scene owners (`SCR_chaos_opening`, `SCR_chaos_death`). They are reusable source material, not proof of a complete gameplay set.

The other **29** Tails-named resources are inherited (`SPR_tails_*`, including super, swim, transform). Census gives exact metadata paths, dimensions, frame counts, origins, hashes and all referring scripts. Do not publish new private PNGs, delete inherited resources, or treat the inherited super/swim choices as SMS features. `SCR_player_sprites_tails` assigns the legacy stop/wait/up/down/walk/run/brake/spin/charge/jump/fall/fly/death/air set; the canonical replacement belongs in character-aware frame/program lookups in `SCR_chaos_player_animation` and `SCR_chaos_visual_p1`, with `SCR_chaos_adapter` publishing selected frame/facing. Core state ownership remains shared; avoid a second movement authority. Audit all census reference owners before retiring any legacy assignment.

## C. Campaign, rewards and ending

Reuse `docs/g0-campaign-contract.md` T02/T06/T08/T10/T11 and `data/g0/campaign-oracle.json`. Start Tails at THZ1 with **5 lives, 3 continues**, zero score/rings/Emeralds; Sonic remains3/0. Continue accept restores5 lives, score0, same act and character, keeps Emeralds, consumes one continue and sets bit7. Expiry does not spend one. Game Over returns to title; stale run state is cleared on next New Game, not merely title entry. Life cap99 and once-only death spending remain existing owners.

Score grants **continues, not lives**: Tails every3,000 raw via digit-sum rule, including the already implemented G2-E boundary/wrap cases. Ring wrap gives a life but `$178F` refuses Special Stage entry unless `D2C8==1`; Tails does **not** play SS1–SS5. Debug forced stages remain separate. Reuse sign prize classes and prove character art/award selection, not a new Tails reward engine.

Terminal selector `$18ED` sends type2 to `$1ACD` regardless of Sonic Emerald mask. Existing EEZ audit has Tails ending scripts: bank14 `$ABDA`, player state `$31`, type `$16` companion; credits `D3C1=$FF` advances `$31→$32`, player+$26=1 releases companion, companion writes `D526=$FF` to advance `$32→$33`, then gravity/deletion. Music `$8D`, return `$04B4` title. This is source/cached-emulator evidence; **no Tails ending Windows acceptance**. Do not reuse Sonic TRY AGAIN or require impossible Tails Emerald collection.

## D. Authentic frontend

**Verified separate screen:** title action leads to `$3065` character choice. It initialises cursor `D2C8=0` (Sonic), actor type cursor+1, actor state `$30`, anchor(128,136), BG palette `$1E`, sprite7, music `$82`. `$356A` consumes fresh Left/Right (bits2/3), Left tested first, clamps0/1 without wrapping, plays `$B4` only on a change. `$3531` checks **fresh Button2 bit5 only** for confirmation; Button1 is not this confirm. It then waits6 updates, marks started, assigns3/0 or5/3, requests `$A0`; `$30C5` converts cursor to character1/2, holds30, fade and90 wait. No back/cancel branch exists in this bounded loop. Don't invent a mandatory Back action as original behaviour.

Title `$0719` resets/fills/loads scene, requests palettes `$1B/$1C`, waits24, requests `$BE`, builds title objects via `$2F77`, waits12, requests **`$99`**, zeroes blink counter, waits30 then1140 update loop. `$0774` toggles PRESS START BUTTON cells on counter bit5 using blocks at `$BCD0/$BCF4`. Existing U5-A cached startup census measured title1,310 harness frames (includes transitions); do not equate it with1140 logical updates. The catalog's `$99` friendly name is still unknown, but its title request site is proven; historical `$82 “title”` shorthand must not cause a wrong cue.

### Art and demo extraction dependencies

| Resource | Proven source / extraction procedure | Remaining gate |
|---|---|---|
| Title tiles | `$798D` loads bank27 `$9E00` →VRAM `$1000`; static decoder yields297 tiles and digest in census. Bank9 `$BEC0` copies `$80` bytes to VRAM `$0200`. `$2F49` blits bank27 `$BA14` 18×14 at `$388E`, `$BC0C`10×1 at `$3DE8`. | Compose title scene, dynamic objects `$2F77/$3008`, their mappings/animation and palettes, compare full sequence. No final title PNG or dynamic title-motion oracle produced here. |
| Character choice | `$79B7` bank19 `$8000` →VRAM `$1800`,153 tiles; `$3075` maps bank19 `$8E9C`32×24 at `$3800`; player normal type2 frames above. `$3595..$361D` selection text/arrow redraw. | Decode redraw tile blocks and compose both cursor states with original palette/fades. Use existing `$2349` blitter/tile decoder, not inherited menu art. |
| Attract recordings | `$2C34` table rows at `$2C72/$2C7E`; six pointer records in census, bank selector byte `$1F`. PAL table pointers `$9400,$8000,$8A00`; other table `$B200,$9E00,$A800`. Initial row1 → THZ1 Sonic, row2 GPZ1 Tails, row0 SEZ1 Sonic; length `$438`=1080 active updates. | Recover input stream decoder/setup at `$2C34` onward, region table selection `D12D`, abort conditions and reset isolation; compare playback before including in M3. Cached startup measured1230 harness frames/demo, not1080 total scene frames. No input payload copied. |
| Opening | Existing accepted OPENING-1 with738 logical replay updates, authentic skip fade/title handoff; no Sega logo in ROM. | Preserve byte-for-byte runtime unless a separately evidenced requirement demands change. Audio later. |

Current `OBJ_menu_title` draws inherited `SPR_title`. `OBJ_menu_title_options/Alarm_1.gml` invokes `SCR_chaos_level:chaos_run_new_game()`, which explicitly passes character1 to `chaos_run_initial_values`. Developer Level Select/Sound Test, pause selectors and launch fixtures remain separate, documented test paths. Original hidden code menus (`D2CE`, `$0D02/$0D0B`) are not equivalent to today's developer UI.

Preserve the accepted Sonic launch/reset as the default through M2. Add a developer-only Tails entry once character-aware core/animation/ending is ready. M3 may then parameterise that same launch owner after validating character1/2 and preserving Sonic reset side effects; do not fork a second reset routine. Switch the public opening→title→choice path only after Tails acceptance. Continue/Game Over and both endings must return to a usable title, with next choice defaulting to Sonic; continue retains current character and act. No public nonfunctional Tails option.

## E. One substantial Designer dependency matrix

| Bundle / owner | Available input | Required before runtime edit / delivery | Source checks / Chief 348×196 gate |
|---|---|---|---|
| Character state and flight / core-adapter | Shared movement/contacts, static flight listing, Tails state table | Complete bounded callback controls and equipment eligibility; document wide flight boundary policy | Input priority/opposing keys, water entry/exit,300→0, ground/ceiling/hurt; flight across ordinary routes |
| Genuine animation import / animation-visual layer | 89 mapping entries, transfer hashes/origins,11 existing imports | Private deterministic exporter using census addresses; branch/selector frame closure; palette variants and restoration metadata | Index/origin/hash/registration/idempotence; stand/run/charge/jump/spring/flight/water/hurt/death/boss/transport poses |
| Campaign and ending / existing level-death-ending owners | G0/G2 reward data, U4-B art, EEZ full ending scripts | Character-aware entry, explicit Tails scene importer, preserve Sonic path |5/3 reset, ring no-SS, score continue, death/Continue/expiry; full natural Tails campaign/ending/title; protected Sonic samples |
| Public frontend / title owner | Separate choice input/default confirmed, tile streams located | Full dynamic title and choice picture/timing composition proof; accepted M2 | Opening normal/skip, Sonic/Tails selection and new run, Continue/ending/Game Over/title, no dead option |
| Attract / flow owner | Source tables and cached boot order | Recording decoder, abort/reset/scene proof; otherwise defer clearly | Three demos, abort to correct title/choice, no contamination of natural run |

Recommendation: Manager authorises **one M2 evidence-and-implementation milestone only after reviewing these gates**, with a single integrated private source package and one substantial Windows session. Do not split frame imports into tiny acceptance releases. M3 follows; audio is separate. Missing local materials: no new ROM upload is needed in this mounted session. A cloud successor needs the canonical ROM privately plus private import restoration assets; dynamic title/choice and character callback traces must be generated locally, not asserted from this static census.
