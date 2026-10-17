# G2-E: the score owner, the score display and every score award

Research only. No POC change, no ROM bytes or pixels committed, no root `AGENTS.md` edit, no Igor, no executable.

- Research base: `30655e088421ac10eab456e8fa8a3cb2aae8040b` (main after U5-A). POC read-only at `b4737e834982b2985c6fdcb8d4d76cb78c9092c8`.
- ROM: Sonic Chaos (Europe) v1.2, SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
- Tool: `tools/g2e_score.py`. Data: `data/g2e/` (`score-static.json`, `score-controlled.json`, `score-observed.json`, `score-poc-source.json`, `award-matrix.json`, `g2e-contract.json`). Tests: `tests/test_g2e_score.py` (27 tests, 4 need the ROM).
- Evidence classes: **DECODED / BYTE-VERIFIED** (ROM bytes asserted at generation), **CONTROLLED** (original Z80 routines on `tools/oracle.py`, a CPU only, with the real placement records and decoded layouts), **EMULATED** (whole game on the approximate `sms_frame_harness` through `g0_rig`; scoring does not depend on picture timing), **POC SOURCE** (read, not run).
- Reused rather than redone: G0 (`docs/g0-campaign-contract.md` T17, U1, U7), G2-B (the threshold writer), U4-A (`docs/u4-ordinary-results.md`, card geometry and tally pacing), U2 (`docs/u2-act3-boss-bonus.md`) and the per-type audits cited in section 5.

## 1. Answers in brief

| Question | Answer |
|---|---|
| U1 Is there a live score HUD? | **No.** `D29D..D29F` are read only by the adder `$262F` and the card drawer `$26F8`; `$26F8` has exactly four call sites, all on the results card (`$33A8` card draw, `$2D1F` ring step, `$2D4B` word step, `$2D6E` boss step). Continue, Game Over, title and gameplay never draw the score. Emulated: 0 draws while playing in all 18 acts. |
| U1 Fixed glyph at `$3BA6` | A **literal `0`**: the block is two stacked tiles read from `bank $13:$A516`, which are the same tile pair as digit 0 of the digit table. Displayed score = raw BCD score x 10, maximum 9,999,990. |
| U1 Leading zeros / formatting | Six raw BCD digits, most significant first, 8x16 glyphs. The first five zero digits are blank; the sixth raw digit is always drawn; then the fixed `0`. If all three bytes are zero the digit loop is skipped entirely and the old field contents stay. |
| U1 Update cadence | Drawn once with the card (before the fade-in) and again after every tally step (ring, word, boss step). Pacing of the steps is U4-A's. |
| U1 Six-digit limit | **Wraps modulo 1,000,000 raw** (ADC/DAA on three bytes). It never saturates. The carry only writes `D2A3..D2A5 := 90 99 99` and `D2BB := 2`, which nothing reads. The wrap is a thousands-digit change (9 -> 0), so it awards a continue to both characters. |
| U7 How many writers? | Two: the results tally (`$2F0C`, three call sites) and the shared defeat conversion (`$5F81`). Plus two resets (new game, accepted continue). Nothing else touches the score. |
| U7 Amount per enemy / monitor / boss | One flat value for every type below `$50`: `+10 raw = 100 displayed` (table entry `$27EB`). There is **no per-type score table**. Types `>= $50` (every boss) award **nothing**. |
| U7 Does every award pass `$262F`? | Yes. The only `JP/CALL $262F` are `$2F0C` and `$5F81`. |
| U7 Duplicates | None within a life: the award and the conversion to type `$0F` happen in the same update. Defeated placements stay occupied and do not respawn in the same act load; deletion and scrolling never reach the conversion. A death reloads the placements, so the same enemy can score again in the next life (observed). |
| POC | Five paths are **missing** (monitors, types `$21 $25 $27 $2C`), four are **mis-scaled** by 10x (`$20/$23`, `$3D`, `$24`, `$38`), the tally and bosses are correct. |

## 2. U1: the display

**Data (BYTE-VERIFIED).** `$26F8` loads `HL = $D29D`; if `D29D|D29E|D29F == 0` it skips to `$2717`; otherwise it draws the six digits through `$2726` at name-table `$3B9A` (column 13, row 14, two cells per digit). It always finishes with `LD DE,$A516 / LD HL,$3BA6 / LD BC,$0201 / CALL $2383`, a 1-column, 2-row block read from the glyph table. The table (bank `$13`, CPU `$A516`) holds one top/bottom tile pair per digit; its first pair is `(01,02)` and so is the fixed block. The tile ids are the ones U4-A already exports, so no graphics are extracted here.

**Observed (EMULATED, results card with the score preset):**

| score (raw BCD) | card at start | after the tally |
|---|---|---|
| 0 | `      0` (six blanks, fixed 0) | |
| 10 | `    100` | |
| 12,340 | ` 123400` | |
| 999,990 | `9999900` | wraps during the tally, one continue awarded |
| 999,999 | `9999990` | wraps, one continue awarded |
| 999,990 + one ring, time word zeroed | `9999900` | score RAM `000000`, continues +1, **the field still shows `9999900`** |

The last row is the only visible consequence of the skip-when-zero rule: a tally that lands exactly on 0 does not redraw the field. It is unreachable in normal play and optional for the POC (contract rule H2).

**Not a defect in the POC.** `chaos_results_card_nt` already draws `floor(score/10)` as the raw digits with five blanks, skips the digits while the score is zero and draws the constant `0`; its modulo-10 digit extraction shows the low six raw digits, which is the ROM's wrapped display.

## 3. U7: how a score is awarded (static)

- **`$262F` (score add).** `HL` points at a three-byte BCD amount. `D292 != 0` (title, menu, attract flow) returns before anything changes. Otherwise the previous score is saved to `D2A0..D2A2`, the amount is added with `ADC/DAA` and the thousands digit (high nibble of `D29E`) is compared with the saved one. If it changed: Sonic (`D2C8 == 1`) awards a continue when the new digit is 0 or 5; the other character awards when `(thousands + ten-thousands + hundred-thousands) mod 3 == 0`. The award is a binary +1 of `D2C3` keeping bit 7 (G2-B).
- **Award table `$27E2` (4 x 3 BCD bytes):** `+1` (word step), `+10` (ring step), `+50` (**never referenced; dead data**), `+10` (boss step and the enemy award).
- **Gate `$5F77`:** `CP $50 / RET NC` then `LD HL,$27EB / JP $262F`. All 256 type bytes were executed: `0x00..0x4F` add `+10 raw`, `0x50..0xFF` add nothing. The following `RET Z` can never fire.
- **Conversion `$5F54`:** gate, then (IX) := `$0F`, state/request/script fields/flags zeroed, placement token (`+$3E`) and parameter (`+$3F`) cleared. No condition of its own.
- **`$5F3D` (vector `$0323`):** contact bits (`+$21 & $0F`) AND (`D532 == 6` OR `D503` bit 1), then falls into the conversion.
- **Vectors:** `$0323 -> $5F3D` (8 call sites), `$033E -> $5F54` (12 call sites). `$034D -> $5FA0` (9 sites) is the solid-contact helper and **not** a score path. Every possible score award from an object therefore goes through one of those 20 sites; the list of types is complete by construction.
- **Results sites:** `$2D18` (`$2F00`, +10 per ring), `$2D44` (`$2EFB`, +1 per word step), `$2D6A` (`$2F05`, +10 per boss step, N = 50/100/150/200/250 by zone).

## 4. U7: what was executed

1. **Adder sweep (CONTROLLED).** `$262F` for 1,000 thousand-crossings x 2 characters against an independent Python model: **0 mismatches**. Sonic is paid 200 times per 1,000,000 raw (every 5,000), Tails 334 times (every 3,000, plus the wrap). The wrap row (999,990 + 10) gives 0, continues +1, `D2A3 = 90 99 99`, `D2BB = 2` for both characters; with `D292 != 0` nothing changes.
2. **Gate (CONTROLLED).** 256 type bytes, as in section 3.
3. **Object fixtures (CONTROLLED).** The original creator `$80EB` on each distinct placement record (type, flags, parameter, aux bytes) of the 10 families, in the act's own decoded layout, original `$64FA` + callback per update, synthetic overlap:
   - families `$20 $23 $25 $27 $2C $3D` and `$21`: attack and invincible contact award `100000` (+10) and the slot becomes `$0F`; airborne-only and plain contact award nothing (`$21` writes a damage request `$D3B0 = $FF` instead); a second update never adds. Delayed `$3D` records (parameters 4, 8) award once their delay has run.
   - `$21` grid: top contact (player Y at least 20 above the object) bounces without scoring in any posture; centre and low contact score only with the attack bit or invincibility.
   - monitors `$10` (parameters 1, 2, 3, 4, 6): 26 of 84 cells award, all with the **attack bit** and a **downward Y velocity**; `D532 == 6` alone and plain contact never award.
   - `$24` converts 74 updates after the player is parked 40 px to either side (shake, fall, landing) and scores whatever the player does afterwards; `$38` parameter 0 converts 35 updates after the player is within 32 px on both axes, attack or not; the `$38` parameter-1 producer never self-destructs (its children do); with the player far away neither moves in 900 updates.
4. **Natural run (EMULATED).** All 18 acts, new game, Right held, attack posture forced, no teleport: 19 awards, every one through table `$27EB` with `+10` raw; the AQZ3 boss reached the gate 6 times (type `$5A`) and `$262F` ran 0 times; the score field was drawn 0 times while playing.
5. **Revisit (EMULATED).** After a defeat the player re-walked the spot three times from 600 px away: 0 further gate events for that placement.

## 5. Event-to-award matrix

Full rows (with eligibility text and notes) are in `data/g2e/award-matrix.json`. `Raw` is the BCD amount added by `$262F`; the POC column is in displayed points (POC `score` = raw x 10).

| Id | Event | ROM source | Placed in | Eligible when | Raw | POC writer | Status |
|---|---|---|---|---|---|---|---|
| E01 | type `$27` contact | `$0323` (states 1-3) | THZ1-2 | attack or invincible | 10 | `OBJ_chaos_object_27`: bytes only | **MISSING** |
| E02 | type `$2C` contact | same callbacks as `$27` | GPZ1-2, EEZ1-2 | attack or invincible | 10 | inherits `$27` | **MISSING** |
| E03 | type `$25` contact | `$0323` (states 1, 2) | GPZ1-2 | attack or invincible | 10 | `OBJ_chaos_object_25`: bytes only | **MISSING** |
| E04 | type `$21` side/low contact | `$033E` after the attack test (states 3-6) | THZ1-2, MGHZ1-2 | not top contact, and attack or invincible | 10 | `OBJ_chaos_object_21`: bytes only | **MISSING** |
| E05 | types `$20`, `$23` contact | `$0323` | SEZ1-2 | attack or invincible | 10 | SEZ `add(10)` | **MIS-SCALED** (10, needs 100) |
| E06 | type `$3D` contact | `$0323` (states 1, 2) | AQZ1-2 | attack or invincible | 10 | AQZ `add(10)` | **MIS-SCALED** |
| E07 | type `$24` lands | `$033E`, state 3 | MGHZ1-2 | autonomous after Sonic is near | 10 | M3 `+10` then `add(diff)` | **MIS-SCALED** |
| E08 | type `$38` self-destructs | `$033E`, state 2/3 | EEZ1-2 (+children) | autonomous when the player is within 32 px | 10 | EEZ `add(10)` | **MIS-SCALED** |
| E09 | monitor `$10`, any parameter | `$033E`, state 2 | all zones, Special Stages | attack bit and Y velocity > 0 | 10 | `OBJ_chaos_object_10`: bytes only | **MISSING** |
| E10 | boss hit/defeat, types `>= $50` | gate returns | THZ3-EEZ3 | never | 0 | none | CORRECT |
| E11 | ring tally | `$2D18` | act clear | per ring | 10 | tally, `add(raw*10)` | CORRECT |
| E12 | time word tally | `$2D44` | act clear | per step | 1 | tally | CORRECT |
| E13 | act-3 boss step | `$2D6A` | act-3 clear | per step | 10 | tally | CORRECT |
| E14 | off-screen deletion / lifetime / scrolling | none (writes `$FE/$FF`) | all | never | 0 | none | CORRECT |
| E15 | repeated contact with a converted object | slot is type `$0F` | all | never | 0 | destroyed / consumed | CORRECT |
| E16 | any award while `D292 != 0` | `$262F` returns | attract | never | 0 | not applicable | n/a |
| E17 | score past 999,990 raw | `$262F` wraps | any | still added | | no modulus | **MISSING** |

Type census from the placement lists (zones 0-6 and the Special Stages): `$10` 134 records, `$20` 7, `$21` 37, `$23` 8, `$24` 12, `$25` 12, `$27` 14, `$2C` 16, `$38` 7, `$3D` 19. State-table aliases of `$27` (`$29 $2A $2B`) and of the boss table (`$33`, `$40..$4F`) contain the same call sites but are neither placed nor script-spawned.

**Not scoring** (confirmed by the site list): `$3C` (hurts only), `$36 $37 $39` (hazards), `$2F` and `$26` (shoes and springs), `$2D/$2E`, `$28` platforms, `$09` rings, `$18` goal sign and its prizes, `$0A` bonus object, all types `>= $50`.

## 6. Thresholds (G2-B)

Every award above is `+10 raw` and enters the same `$262F`, so the G2-B writer is the right place. For single awards of at most 10 raw the POC's stateless formula (`floor(score_raw / period)` before and after) equals the ROM for Sonic at every one of the 1,000 crossings and for Tails at every crossing inside the cycle (tested). The two differ only for Tails at the wrap, and that difference is **in G2-E scope** (Manager decision): the shared score owner must pay the wrap award for both characters. For Tails there are two separate award events near the end of a cycle, each paying exactly one continue: (1) when the score crosses 999,000 raw (thousands value 999, a multiple of 3) and (2) 1,000 raw later when it wraps to 0 (thousands value 0, also a multiple of 3). The POC's stateless formula pays only event 1 (`floor(1,000,000 / 3000)` equals `floor(999,990 / 3000)`), so it needs the wrap added (contract rules S7 and S8). Sonic is unchanged: 5,000 raw divides 1,000,000, so the wrap is simply his 200th award. Broader Tails gameplay remains G6. Larger single adds would behave differently (the ROM pays at most once, only when the thousands digit changed), but no ROM source adds more than 50 raw.

## 7. Proposed G2-E implementation contract

Machine-readable: `data/g2e/g2e-contract.json`.

1. **One owner, one writer.** `score` stays in displayed points. Add `chaos_score_award_raw(raw)` = `chaos_continue_score_add(raw * 10)`; nothing else modifies `score` except the two resets (new game, accepted continue).
2. **Flat award.** Every converted object with ROM type below `$50` awards raw 10 = 100 points; bosses award nothing; no per-type table.
3. **Once, at conversion.** Call it in the update where the object becomes `$0F`, at the existing bytes-only call (monitor, `$21`, `$25`, `$27`/`$2C`), and replace `add(10)` by it for `$20/$23`, `$3D`, `$38`; for `$24` forward `10 x` the counter difference. Eligibility stays the existing per-type logic: no attack requirement on `$24`/`$38`, no invincibility-only monitors.
4. **Wrap** inside the writer: after evaluating the threshold on the unwrapped pair, `score = score mod 10,000,000`; the wrap pays one continue to both characters (for Tails this is a second event after the 999,000 award).
5. **No live HUD.** Do not add an in-level score display.
6. **Acceptance checks** (also in the JSON): the THZ1 attack run scores 100/100/100 for `$21`, monitor, `$21`; no second award for a defeated placement; a boss adds 0; `$24` landing and `$38` self-destruct add exactly 100 without the player attacking; invincibility-only monitor adds 0; 999,900 + 100 wraps to 0 with one continue for both characters.

## 8. Confirmed facts and remaining uncertainties

**Confirmed (ROM data or controlled execution):** everything in sections 1-4 except the items below.

**Remaining:**
- Special Stage monitors run the same global object code but were not separately executed (the Special Stage object lists contain monitors and the Chaos Emerald `$31` only).
- Forced-state fixture: `$20` states 1-2 and `$21` state 2 did not return from the engine call in the harness ("not exercised"); `$21` state 1 and `$3D` state 3 award nothing. The call-site map and the posture matrix are unaffected.
- The natural run reaches defeats in 12 of 18 acts; the other six acts had no contact with an enemy on the simple Right-held route. The placement census and the fixtures cover those families.
- Objects created by callbacks (not by script commands) were not enumerated; any such object still reaches the same 20 sites, so the award rule is complete, but the list of which zones place which type could grow.
- Child chain of the EEZ `$38` parameter-1 producer depends on the shared 11-slot pool (EEZ objects audit).
- The wrap, and the stale field at an exact zero, are verified on the ROM but reachable only after ~1,000,000 raw points; the POC need not reproduce the stale field.
- Tails-specific behaviour beyond the shared threshold and wrap rule belongs to G6.

**Corrections to earlier Research text (not edited there):**
- `docs/object-10.md` and `docs/eez-objects-audit.md` say `$5F77` selects a per-type score-table entry. It does not: every type below `$50` uses the one entry `$27EB`.
- G0 U1 (display factor) and U7 (per-object awards, other paths) are closed by this document: `x10` with a literal `0` glyph; all adds go through `$262F` and the only object award is the flat `+10 raw`.
- `docs/object-27.md`: `$27 +10 raw = 100 displayed`, never "+10 points".

## 9. Reproduction

```
ROM=/path/to/Sonic_Chaos_Europe.sms
python tools/g2e_score.py $ROM --poc <SonicChaos_POC checkout>   # about 4 minutes; --check compares with data/g2e
python tools/g2e_score.py $ROM --only static                     # seconds
python tools/g2e_score.py --validate                             # no ROM
python tests/test_g2e_score.py                                   # SONIC_CHAOS_ROM=$ROM also runs the 4 ROM-backed tests
```

## 10. Candidate `AGENTS.md` notes (not applied)

- The score is shown only on the results card; there is no in-level score HUD.
- Displayed score = raw BCD x 10 (the fixed glyph is the `0` digit); every object award is the flat raw 10 (100 points); bosses award nothing.
- Unit rule for the POC: `score` is in displayed points, so every ROM raw amount is multiplied by 10 at the writer.
