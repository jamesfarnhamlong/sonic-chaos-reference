"""G0-R campaign contract: the hand-authored, source-traced transition model.

Everything in `TRANSITIONS`, `RAM`, `RULES` and `OUTCOMES` was read from the ROM disassembly (routine addresses are CPU addresses in the resident
banks unless a bank is given) and is *checked* by `EXPECTATIONS`, a list of machine-evaluable claims over the oracle observations produced by
`tools/g0_scenarios.py` (see `tools/g0_campaign.py`).  A claim that cannot be checked by the oracle says so (`oracle: []`).

Evidence vocabulary (same as earlier Research packages):
  SOURCE-TRACED   read from the disassembly of the cited routine (byte hashes in `routines` of the contract)
  EMULATED        observed in a whole-game run of the original ROM in the approximate SMS harness (tools/g0_rig.py), RAM fixtures named
  CONTROLLED      an original routine executed alone with explicit RAM (tools/oracle.py)
  REUSED          accepted earlier Research, cited, not re-derived
  UNRESOLVED      not established
"""
from __future__ import annotations

FIELDS = ["stage_index", "rings", "timer", "score", "lives", "continues", "emeralds", "result_card", "powerups", "player_identity", "restart_position"]

# --------------------------------------------------------------------------------------------------------------------------------------------
# RAM that carries the campaign.  `scope`: RUN (survives act reloads, cleared by New Game), ACT (rewritten by every level load), FLOW (control flags)
# --------------------------------------------------------------------------------------------------------------------------------------------
RAM = [
    dict(name="menu", address="D292", scope="FLOW", role="title/menu state flags (bit7 start requested, bit6 title active, bit5/4/3 attract and option sub-states); non-zero suppresses the HUD and the level timer", writers="$04B4 set, $04D1 clear, $2B50.. state machine"),
    dict(name="flow", address="D293", scope="FLOW", role="main-loop dispatch flags: bit7 end path $1365, bit6 level frame enabled (0x40 = playing), bit5 act complete $14AE, bit4 zone complete $1543, bit2 life lost $15F2, bit1 level (re)load $1673, bit0 pause $1696", writers="$83E7/$83ED (state $20 handler), $1534, $15E8, $4984/$49AA, $1869, $3C0D, $7BB2A/$7BB6E"),
    dict(name="mode", address="D294", scope="FLOW", role="stage mode: bit7 special stage active, bit6 success $183F, bit5 failure $1815, bit3 entering", writers="$17A7 (=$88), $1869 (=0), $2846, Emerald object"),
    dict(name="started", address="D295", scope="FLOW", role="$FF once a game has been started from the title/character select (or hidden level select); cleared by $2C17 when START is pressed on the title; gates the zone/act reset inside $2A00", writers="$2C18 (0), $3549 (FF), $086C (FF)"),
    dict(name="saved_zone", address="D296", scope="ACT", role="zone to restore after a special stage", writers="$187E"),
    dict(name="zone", address="D297", scope="RUN", role="zone: 0 THZ, 1 GPZ, 2 SEZ, 3 MGHZ, 4 AQZ, 5 EEZ, 6 end-of-game, 7 title, 8..12 Special Stages 1..5", writers="$07CF new game, $15D6 zone complete, $1870 stage return, $1897 stage entry, $06CD title, $2A27/$2BE8 restart paths, $2C55 attract, $0821 hidden level select"),
    dict(name="act", address="D298", scope="RUN", role="act index 0..2 (Act 1..3); unguarded +1 at $1538 on every act complete and every special-stage return", writers="$1538 (+1), $15CF (0), $07D2, $06D1, $2A2A, $2BEB, $2C6E, $0826"),
    dict(name="lives", address="D299", scope="RUN", role="lives, packed BCD; game over when the post-death value is 0 (the life being played is part of the count)", writers="$355D init (3 Sonic / 5 Tails), $15FB (-1 DAA), $3113 (+1 DAA, cap $99), $13D4 continue restore (3 Sonic / 5 Tails)"),
    dict(name="rings", address="D29A", scope="ACT", role="rings, packed BCD (wraps 99->00 at $3138)", writers="$3138 +1, $4AC8 +$10 (monitor), $A9C5 sign prize +$10 (carry dropped, no award), $2A50 level load (=0), $2D15 tally (-1), $4937 hurt (=0)"),
    dict(name="score", address="D29D", scope="RUN", role="score, 3 bytes packed BCD little-endian (D29D units/tens, D29E hundreds/thousands, D29F ten-thousands/hundred-thousands); HUD draws these six digits then a fixed block at name-table $3BA6 (display = raw x 10 is probable, glyph not decoded)", writers="$262F adder; cleared by $2A00 (new game) and $13DB (continue)"),
    dict(name="bonus", address="D2A6", scope="ACT", role="end-of-act time/ring bonus word consumed by the tally (+1 raw per step); set by the sign child $19 (0C:$AB52), the boss bonus object type $0A (0C:$9C96) and by the stage success callback ($94BD: seconds left << 8)", writers="0C:$AB52, 0C:$9C96, 1E:$949D"),
    dict(name="continues", address="D2C3", scope="RUN", role="continues in bits 0..6 (mixed binary/BCD increments), bit7 = 'a continue was just used' (cleared by $13ED, set by $1491)", writers="$3561 init (0 Sonic / 3 Tails), $26C9 score award, 0C:$A9D6 sign prize, 1E:$94C2 stage success, $1491 consume, $13ED clear bit7"),
    dict(name="character", address="D2C8", scope="RUN", role="1 = Sonic, 2 = Tails (the select cursor 0/1 is held here until $30C5 increments it)", writers="$3072 (0), $357C/$358C cursor, $30C5 (+1), $2C5D attract"),
    dict(name="emeralds", address="D2CC", scope="RUN", role="Chaos Emerald bits: $01/$02/$04/$08/$10 = Special Stages 1..5, $20 = sixth (EEZ)", writers="$2A1F cleared by new game, 1E:$94A7 (|= stage bit), 1E:$BB69 (|= $20)"),
    dict(name="result_card", address="D2CD", scope="ACT", role="results card selector: 0 ordinary, 1 stage failure card (also marks 'stage entered'), $FF stage success card; cleared by $33D7 when the card is drawn", writers="$17AC (1), 1E:$94AC ($FF), $33D7 (0)"),
    dict(name="timer", address="D2BE", scope="ACT", role="D2BE run flag ($FF running, 0 stopped); D2C2 frame ticks 0..59; D2BF seconds BCD; D2C0 minutes BCD; counts UP in acts (10:00 sets D44B=$C0 and stops), counts DOWN from 59 in a special stage", writers="$27EE tick, $2965/$296C reset on load, $1753 stop, $1758 start, 0C:$A8A8 sign contact stop"),
    dict(name="timeover", address="D44B", scope="ACT", role="$C0 set at 10:00; bit6 makes the player update call the death routine, bit7 makes the life-lost path show the TIME OVER screen", writers="$281E, $49B1 (keeps bit7), $34CF/$351E"),
    dict(name="powerup", address="D532", scope="ACT", role="power-up id (player object field +$32) and D44C timer; inside the object RAM block $D300..$DBBF that $297E clears on every level load", writers="monitor rewards $4AA0.., cleared by $297E"),
    dict(name="continue_screen", address="D2CA", scope="FLOW", role="continue countdown: D2CA frame ticks (0..$73), D2CB digit 9..0 (underflow to $FF ends the screen)", writers="$13F6/$13FB/$1471"),
    dict(name="hidden_menus", address="D2CE", scope="FLOW", role="bit0 level select unlocked, bit1 sound test unlocked (title input codes at $0D02 / $0D0B); not a normal-play path", writers="$0CA6, $0CDE, $0CF2"),
]

FLOW_BITS = {
    "D293": {"7": "end path $1365", "6": "level frame enabled (cleared by $166E when no lives are left -> $138A)", "5": "act complete $14AE", "4": "zone complete $1543",
             "2": "life lost $15F2", "1": "level (re)load $1673", "0": "pause $1696"},
    "D294": {"7": "special stage active", "6": "stage success $183F", "5": "stage failure $1815", "3": "stage entering"},
}

# --------------------------------------------------------------------------------------------------------------------------------------------
# Routine byte regions hashed into the contract (resident bank, CPU address == file offset).  The tests recompute the SHA-256 of each.
# --------------------------------------------------------------------------------------------------------------------------------------------
ROUTINES = [
    ("main_loop_dispatch", 0x1333, 0x1365), ("end_path", 0x1365, 0x138A), ("game_over_and_continue_restore", 0x138A, 0x13ED),
    ("continue_screen", 0x13ED, 0x14AE), ("act_clear_sequence", 0x14AE, 0x1543), ("zone_clear_sequence", 0x1543, 0x15F2), ("life_lost", 0x15F2, 0x1673),
    ("level_reload", 0x1673, 0x1696), ("stage_mode_dispatch", 0x1762, 0x178F), ("stage_entry_gate", 0x178F, 0x17B0), ("stage_entry_sequence", 0x17B0, 0x1815),
    ("stage_failure", 0x1815, 0x183F), ("stage_success_and_return", 0x183F, 0x187B), ("stage_selector", 0x187B, 0x189B), ("zone_music_select", 0x189B, 0x18E1),
    ("ending_selector_head", 0x18ED, 0x1900), ("new_game_reset", 0x2A00, 0x2A2E), ("level_loader", 0x2934, 0x297E), ("object_ram_clear", 0x297E, 0x2993),
    ("level_start_record", 0x2A4F, 0x2A5A), ("title_new_game_init", 0x2C17, 0x2C34), ("zone_act_reset", 0x07CE, 0x07DB), ("score_adder_and_continue_award", 0x262F, 0x26D6),
    ("timer_tick", 0x27EE, 0x285C), ("tally", 0x2D08, 0x2D55), ("act3_boss_bonus_tally", 0x2D55, 0x2D90), ("character_select_init", 0x3522, 0x356A),
    ("results_screen", 0x32F9, 0x3436), ("life_award", 0x3104, 0x3116), ("ring_pickup", 0x3138, 0x3175), ("monitor_ring_and_life_rewards", 0x4AA3, 0x4AE1),
    ("start_position_lookup", 0x4E65, 0x4E98), ("death_mode_split", 0x49A0, 0x49BD), ("pit_death_rule", 0x3C06, 0x3C15),
]

# --------------------------------------------------------------------------------------------------------------------------------------------
TRANSITIONS = [
    dict(id="T01", name="Power-on / reset to title", trigger="reset vector", routines=["$0029 clears $C001..$DFFF (LDIR BC=$1FEE)", "$06C7 title init: zone := 7, act := 0, level loader $2A4F, flow := $40"],
         evidence=["REUSED docs/decomp-1d-r2-zone-act-invariants.md"],
         effects=dict(stage_index="zone 7 (title), act 0", rings="0", timer="0", score="0", lives="0", continues="0", emeralds="0", result_card="0", powerups="none", player_identity="D2C8 = 0 until character select", restart_position="n/a"),
         oracle=["new_game_sonic"], notes="All run-scoped bytes are zero after power-on; there is no battery RAM (the only $FFFC stores are the start-up mapper writes at $0008/$0466)."),
    dict(id="T02", name="Title START -> character select -> New Game", trigger="button 1/2 on the title (START is not read; the harness has no console key)",
         routines=["$2C17: D295 := 0, $0AD0 sound-test screen (only if D2CE bit1), $07CE: zone := 0, act := 0 (hidden level select, if D2CE bit0, overwrites the pair from the table at $082A and sets D295 := $FF)",
                   "$3065 character select: D2C8 := 0, cursor LEFT/RIGHT $356A, button 2 confirms; $3522 returns through $3549 (D295 := $FF, D293 := 0) and $3550: lives/continues = 3/0 (Sonic cursor) or 5/3 (Tails cursor)",
                   "$30C5: D2C8 += 1 (Sonic 1, Tails 2)", "$04D4: $2A00 clears rings, score (D29D..F), D2A8..D2AD and the emerald byte D2CC; zone/act only if D295 = 0 (not the case here)", "D293 := $42 -> level load T03"],
         evidence=["SOURCE-TRACED", "EMULATED new_game_sonic / new_game_tails with dirty pre-state"],
         effects=dict(stage_index="zone 0, act 0 (from $07CE)", rings="0 ($2A00)", timer="0:00, running ($2965..$2973)", score="0 ($2A04..$2A0A)", lives="3 Sonic / 5 Tails", continues="0 Sonic / 3 Tails", emeralds="0 ($2A1F)", result_card="not written (stale $D2CD is consumed by the first results card)", powerups="none", player_identity="D2C8 = 1 Sonic / 2 Tails", restart_position="start position of THZ1 (T03)"),
         oracle=["new_game_sonic", "new_game_tails"], notes="Emerald flags are cleared here and ONLY here (and by power-on); Game Over, the ending and the title do not clear them."),
    dict(id="T03", name="Level (re)load - first load, next act, next zone, death restart, continue restart", trigger="D293 bit1 -> $1673",
         routines=["$1673: $4FCE, $3175, $2934 (loader), $3116, $314A, $285C, $189B (zone music), $794F, $59B3, RES bit1", "$2934: $297E clears the object RAM block $D300..$DBBF, $2A4F records the act record and sets rings := 0, $4E65.. start position + camera from the ROM table indexed by zone and act only, timer D2BF/D2C0 := 0 and D2BE := $FF (menu flag permitting)"],
         evidence=["SOURCE-TRACED", "EMULATED restart_matrix (18 acts)"],
         effects=dict(stage_index="unchanged by the load itself", rings="0", timer="00:00 and running; D2C2 ticks are NOT cleared", score="unchanged", lives="unchanged", continues="unchanged", emeralds="unchanged", result_card="unchanged", powerups="cleared (object RAM block, includes D532/D44C/D44B)", player_identity="player object type rewritten from D2C8", restart_position="ROM table (zone, act) only; no checkpoint storage exists"),
         oracle=["restart_matrix", "death_pit_lives3"], notes="The start position is read from a ROM table indexed by (D297, D298) at $4E65..$4E94; no store of a mid-level position exists, and all 18 acts restart at the fresh-load position after a death."),
    dict(id="T04", name="Act complete, act index 0 or 1 (sign chain -> next act)", trigger="goal sign `$18` contact -> $19 child -> player state $20 -> $83A6 sets D293 bit5 (REUSED docs/object-18-act-clear.md); then $14AE",
         routines=["head (REUSED): contact stops the timer (0C:$A8A8), landing prize by ring count (0C:$A8FA / tables $A919, $A962 selected by zone parity), $19 computes D2A6 (time/ring bonus)",
                   "$14AE: wait 60, $1CEB, wait 96 with fade slots D492/D494 requested, $18E1, wait 30, sound 0, $297E/$4FCE/$21DA/$342A, wait 12 (198 frames in all)", "$32F9 results card (D2CD = 0) + $2D55 (returns unless act index 2) + $2D08 tally: -1 ring per step awards +10 raw ($27E5), then D2A6 counts down awarding +1 raw per step ($27E2)",
                   "$14FF..$1521: wait 48, fade slots requested again, wait 96, $342A palette fill", "$1524, wait 48; $152F: RES 5, act += 1, SET 1 -> T03"],
         evidence=["REUSED head", "SOURCE-TRACED tail", "EMULATED clear_thz1_rings00/15/55/09 and campaign_spine"],
         effects=dict(stage_index="act + 1 (zone unchanged)", rings="tally drains to 0; loader zeroes", timer="stopped at contact, reset by the next load", score="+10 raw per ring after the prize, + bonus word (time entry x100 + (rings-$11)) raw", lives="+1 for prize class 1 (rings 55/65/77/88/95/97/99 in THZ-parity zones)", continues="+1 for prize class 3 (rings 15/30/40/60) - a CONTINUE, not a life", emeralds="unchanged", result_card="0 -> ordinary card", powerups="cleared by the reload", player_identity="unchanged", restart_position="next act's ROM start"),
         oracle=["clear_thz1_rings00", "clear_thz1_rings15", "clear_thz1_rings55", "clear_thz1_rings09", "campaign_spine"], notes="Act and zone are NOT stored in two places: $1538 is the only increment, there is no guard on the act byte."),
    dict(id="T05", name="Zone complete, act index 2, zones 0..4 (boss -> next zone)", trigger="player state $20 tail (boss defeat chain, REUSED) sets D293 bit4 -> $1543",
         routines=["$1543: wait 60, $1CEB, fade slots, wait 96, $18E1, wait 30, sound 0, $1CEB/$297E/$4FCE/$21DA/$342A, wait 12", "$1594: zone < 5 -> $32F9 results card then $2D55 act-3 boss bonus loop (table $2D84: 50,100,150,200,250,600 iterations x +10 raw -> 500/1000/1500/2000/2500/6000 raw, index = zone) and $2D08 tally", "$15CE: act := 0, zone += 1, then D293 bit4 off + bit1 on (zone < 6) -> T03"],
         evidence=["SOURCE-TRACED", "EMULATED campaign_spine (flag injected, everything after is ROM)"],
         effects=dict(stage_index="(zone+1, act 0)", rings="tally drains, loader zeroes", timer="reset by load", score="+boss bonus 500/1000/1500/2000/2500 raw for zones 0..4 + ring/time tally", lives="unchanged", continues="unchanged unless a score threshold is crossed", emeralds="unchanged", result_card="0", powerups="cleared", player_identity="unchanged", restart_position="next zone act 1 start"),
         oracle=["campaign_spine"], notes="The 6000-raw table entry (index 5) belongs to zone 5 and is never used: zone >= 5 skips the results screen."),
    dict(id="T06", name="Final zone complete (EEZ act index 2) -> ending -> title", trigger="D293 bit4 at zone 5 -> $1543 -> $1594 skips $32F9 -> $15CE",
         routines=["$15CE: act := 0, zone := 6, D293 bit4 off, bit7 on", "$1365 end path: $297E, $4FCE, $18ED ending selector, $1CAF, $18E1, wait 60, clear D293 bits 7/6/4/2, JP $04B4 (title)",
                   "$18ED: Sonic ($D2C8=1): ($D2CC & $3F) == $3F -> $18FE full ending (credits, END.); otherwise $1A41 partial ('TRY AGAIN'); any other character -> $1ACD (Tails ending)"],
         evidence=["REUSED docs/eez-boss-endgame-audit.md, docs/eez-ending-credits-audit.md", "EMULATED ending_sonic_full / ending_sonic_partial / ending_sonic_20_only / ending_tails"],
         effects=dict(stage_index="zone 6, act 0, then the title (zone 7)", rings="n/a", timer="n/a", score="no results card, no tally", lives="unchanged", continues="unchanged", emeralds="unchanged until the NEXT New Game (T02)", result_card="n/a", powerups="n/a", player_identity="unchanged", restart_position="n/a"),
         oracle=["ending_sonic_full", "ending_sonic_partial", "ending_sonic_20_only", "ending_tails"], notes="Full vs partial depends only on D2CC & $3F == $3F. The sixth bit ($20) is set by the final-zone $61 object only when flags are exactly $1F (REUSED); a $20-only mask is therefore a partial ending."),
    dict(id="T07", name="Death with lives remaining (hurt-with-no-rings, pit, crush, drown, TIME OVER at 10:00)", trigger="death routine $4984 (zone < 8) sets D293 bit2 (and $3C0D for the pit rule); time over: $27EE sets D44B := $C0 at 10:00, $362A calls $4984",
         routines=["$15F2: $1753 stop timer, lives := lives - 1 (DAA), $3116 HUD, death animation loop until D51D = 2 (forced state $1F), wait 60, $1CA8/$1CEB/$1CAF/$18E1, wait 90", "D44B bit7 set -> $3495 TIME OVER screen", "lives != 0 -> RES bit2, SET bit1 -> T03 (same zone/act)"],
         evidence=["SOURCE-TRACED", "EMULATED death_pit_lives3, death_time_over_lives3"],
         effects=dict(stage_index="unchanged (same act restarts)", rings="0", timer="reset to 00:00", score="kept", lives="-1", continues="kept", emeralds="kept", result_card="unchanged", powerups="cleared", player_identity="unchanged", restart_position="ROM start of the act"),
         oracle=["death_pit_lives3", "death_time_over_lives3"], notes="The life that was being played counts: 3 lives = 3 attempts. Time over is 10:00, not 9:59. A Special Stage death or timeout does NOT use this path (T14)."),
    dict(id="T08", name="Death on the last life, continues available", trigger="lives reach 0 -> $166B clears D293 bit6 -> main loop $138A",
         routines=["$138A: $297E, $4FCE, $21DA, $13ED: RES bit7 of D2C3; if D2C3 low bits are zero return (-> Game Over T09)", "$13F5: continue screen: player object redrawn, countdown digit D2CB from 9, 116 ($74) frames per digit, sound $94; button 1/2 -> sound $A0, $1491: D2C3 := (D2C3 - 1) | $80, wait 180",
                   "after accept or expiry $1450..$1461: RES D293 bit6, fade slots ($1CAF), $18E1, wait 60", "$1396 BIT7 set -> $13C9: lives := 3 (Sonic) / 5 (other), score := 0, RES bit2, SET bit1 and bit6 -> T03 at the CURRENT zone and act"],
         evidence=["SOURCE-TRACED", "EMULATED death_continue_accept_sonic / _tails"],
         effects=dict(stage_index="unchanged (act restarts)", rings="0", timer="reset", score="0", lives="3 Sonic / 5 Tails", continues="-1, bit7 left set", emeralds="KEPT", result_card="unchanged", powerups="cleared", player_identity="unchanged", restart_position="ROM start of the act"),
         oracle=["death_continue_accept_sonic", "death_continue_accept_tails"], notes="Continue never returns to Act 1/zone start; it restarts the act in which the last life was lost."),
    dict(id="T09", name="Game Over (no continue, or the continue countdown expires)", trigger="$13ED returns with no continue taken -> $139D",
         routines=["$139D: $21DA, $3436 Game Over screen, sound $87, wait 2 x 240 frames, $1CAF, $18E1, wait 60, JP $04B4 (title)", "continue countdown expiry: D2CB underflows to $FF -> $13ED returns with D2C3 bit7 cleared -> the same Game Over path"],
         evidence=["SOURCE-TRACED", "EMULATED death_continue_timeout, death_game_over_no_continue"],
         effects=dict(stage_index="title (zone 7 after the title init)", rings="stale until New Game", timer="stale", score="stale until New Game", lives="0 (stale)", continues="stale (an unused continue is NOT consumed by a timed-out screen)", emeralds="stale until New Game", result_card="n/a", powerups="n/a", player_identity="re-chosen at the next character select", restart_position="n/a"),
         oracle=["death_continue_timeout", "death_game_over_no_continue"], notes="A new game after Game Over starts from T02 with every run-scoped field reset."),
    dict(id="T10", name="Return to title then New Game (dirty state)", trigger="T06/T09 end in JP $04B4; START again",
         routines=["$04B4 title; $2C17 -> T02"], evidence=["EMULATED new_game_sonic dirty pre-state, death_continue_timeout.then_new_game"],
         effects=dict(stage_index="zone 0 act 0", rings="0", timer="0", score="0", lives="3/5", continues="0/3", emeralds="0", result_card="stale", powerups="none", player_identity="re-chosen", restart_position="THZ1 start"),
         oracle=["new_game_sonic", "death_continue_timeout", "death_game_over_no_continue"], notes="Run state is reset at New Game, never at the title entry."),
    dict(id="T11", name="Ring 100 (life award) and the Special Stage entry gate", trigger="$3138 wraps D29A 99 -> 00 (also the ten-ring monitor $4AC0 when the result is < $10)",
         routines=["$3104: sound $A9, lives := min(99, lives + 1) (DAA)", "$178F gate: D2C8 == 1 (Sonic), zone < 6, (D2CC & $1F) != $1F; otherwise return (life still awarded)", "$17A2: $1753 stop timer, D294 := $88, D2CD := 1"],
         evidence=["SOURCE-TRACED", "EMULATED ring100_sonic / ring100_tails / ring100_all_emeralds / ring100_ten_monitor / ring100_lives_cap / oneup_monitor"],
         effects=dict(stage_index="unchanged until T12", rings="wraps to 00 ($3138) or keeps the post-wrap value 05 (monitor)", timer="stopped when a stage is entered", score="unchanged", lives="+1 (cap 99)", continues="unchanged", emeralds="unchanged", result_card="1 when a stage is entered", powerups="unchanged", player_identity="Sonic only may enter", restart_position="n/a"),
         oracle=["ring100_sonic", "ring100_tails", "ring100_all_emeralds", "ring100_ten_monitor", "ring100_lives_cap", "oneup_monitor"], notes="The act index is NOT read by the gate (T16)."),
    dict(id="T12", name="Special Stage entry", trigger="D294 = $88 -> main loop $1762 -> $17B0",
         routines=["$17B0: sound $8A, wait 30, $1CEB, fade slots, wait 150, $187B: D296 := zone, zone := 8 + number of consecutive set low bits of D2CC (max 4), $4FCE/$2934 load, timer D2BF := $59 counting down ($17F1), D294 bit3 off"],
         evidence=["SOURCE-TRACED", "EMULATED ss_select_mask00..0F, special_stage_success"],
         effects=dict(stage_index="zone 8..12 (stage), saved zone kept in D296; act index unchanged", rings="0 in the stage", timer="0:59 countdown", score="unchanged", lives="unchanged (+1 per ring wrap inside the stage)", continues="unchanged", emeralds="unchanged", result_card="1", powerups="cleared by the load", player_identity="Sonic", restart_position="stage start"),
         oracle=["ss_select_mask00", "ss_select_mask01", "ss_select_mask03", "ss_select_mask07", "ss_select_mask0F", "special_stage_success"], notes="Selection is strictly sequential and uses the CONSECUTIVE low bits of D2CC; a failed stage is offered again."),
    dict(id="T13", name="Special Stage success", trigger="stage Emerald object (type $31) collected",
         routines=["1E:$94A0..: D2CC |= parameter bit; D2C3 := (D2C3 + 1) & $7F; D2A6 := D2BF << 8; D2CD := $FF; D294 bit6", "$183F: sound $8A, wait 30, fade slots, wait 120, then $1869"],
         evidence=["REUSED docs/special-stages-progression-audit.md", "EMULATED special_stage_success (input-only route)"],
         effects=dict(stage_index="-> T15", rings="stage rings are tallied (x10 raw), then zero", timer="seconds left x100 raw bonus", score="+rings x10 + seconds x100 raw", lives="kept (+ any ring-wrap lives earned inside the stage)", continues="+1", emeralds="| stage bit", result_card="$FF -> emerald results card", powerups="cleared", player_identity="Sonic", restart_position="n/a"),
         oracle=["special_stage_success"], notes="A same-update timeout or death does not undo success (REUSED SS1 contract)."),
    dict(id="T14", name="Special Stage failure (timer underflow or death)", trigger="$2846 (timer 0 - 1) or the shared death setup $49A0 (zone >= 8) sets D294 bit5 -> $1815",
         routines=["$1815: $1753, player death state, $18E1, fade slots, wait 30 -> $1869"], evidence=["REUSED", "EMULATED special_stage_timeout / special_stage_death_act2"],
         effects=dict(stage_index="-> T15", rings="0", timer="n/a", score="unchanged (stage rings may still be tallied)", lives="NOT decremented", continues="unchanged", emeralds="unchanged (stage offered again at the next 100 rings)", result_card="1 -> failure card", powerups="cleared", player_identity="Sonic", restart_position="n/a"),
         oracle=["special_stage_timeout", "special_stage_death_act2"], notes="No retry, no life cost."),
    dict(id="T15", name="Return from a Special Stage to the NEXT ordinary act", trigger="$1869", routines=["$1869: D294 := 0, zone := D296, D293 |= $20 -> T04 tail ($14AE..$153E): results card (success or failure card), tally, FADES, act += 1, reload"],
         evidence=["SOURCE-TRACED", "EMULATED special_stage_success / timeout / death"],
         effects=dict(stage_index="(origin zone, origin act + 1)", rings="0", timer="reset", score="+ tally", lives="as T13/T14", continues="as T13/T14", emeralds="as T13/T14", result_card="0 after the card", powerups="cleared", player_identity="unchanged", restart_position="next act ROM start"),
         oracle=["special_stage_success", "special_stage_timeout", "special_stage_death_act2"], notes="Identical code path to T04: the same fades and the same $14AE sequence run (the post-tally fade question, section 'Palette fade' of the narrative)."),
    dict(id="T16", name="FORCED-ONLY: Special Stage entered at act index 2 returns to act index 3", trigger="100th ring while D298 = 2 (not reachable by ordinary play)",
         routines=["$178F does not read D298; $1869 -> T04 tail increments D298 to 3 and pays the act-3 boss bonus ($2D55 sees D298 = 2 before the increment)"],
         evidence=["REUSED docs/special-stages-followup-audit.md section 5 (census: maximum rings in act-index-2 acts THZ3 19, GPZ3 19, SEZ3 42, MGHZ3 83, AQZ3 14, EEZ3 0)", "EMULATED ring100_act3_forced, special_stage_death_act3_forced"],
         effects=dict(stage_index="(zone, act 3): the loader selects the adjacent record, i.e. the NEXT zone's act-1 data under the old zone number", rings="0", timer="reset", score="+ boss bonus of the zone (500 raw for THZ)", lives="as T14", continues="as T14", emeralds="as T14", result_card="0", powerups="cleared", player_identity="unchanged", restart_position="(110,384) for zone 0 act 3"),
         oracle=["ring100_act3_forced", "special_stage_death_act3_forced"], forced_only=True,
         notes="Entry needs the ring counter to wrap inside act index 2 (Act 3 of a zone); every act-index-2 act holds at most 83 rings (MGHZ3), so ordinary play cannot enter. A fixture (START_INDEX act 2 + injected 100th ring) can. NOT normal behaviour; do not implement as a campaign path."),
    dict(id="T17", name="Score and continue awards", trigger="every score addition goes through $262F",
         routines=["$262F adds the three-byte BCD increment at HL; $266F: if the thousands digit changed: Sonic -> +1 continue when the new thousands digit is 0 or 5 (every 5,000 raw); other characters -> a digit-sum-mod-3 rule over the thousands/ten-thousands/hundred-thousands digits ($2691..$26BD), i.e. +1 continue every 3,000 raw (33 awards per 100,000 raw)"],
         evidence=["SOURCE-TRACED", "CONTROLLED score_continue_rule"],
         effects=dict(stage_index="n/a", rings="n/a", timer="n/a", score="n/a", lives="NO life is awarded by score", continues="+1 per threshold (binary +1 of a byte whose bit7 is preserved)", emeralds="n/a", result_card="n/a", powerups="n/a", player_identity="Sonic vs Tails rule", restart_position="n/a"),
         oracle=["score_continue_rule", "campaign_spine"], notes="The earlier hypothesis of a score-driven extra LIFE is disproved: the award increments D2C3 (continues)."),
    dict(id="T18", name="Hidden level select / sound test and attract demos (non-campaign)", trigger="title input codes (D2CE) / idle title (D292 attract sub-states)", routines=["$0CA6 / $0CDE set D2CE bit0 / bit1; $0AD0 + $07D5 level select writes zone, act and D295 := $FF ($086C); $2BC3.. attract rotates demos via $2C34 and returns with zone := act := 0"],
         evidence=["SOURCE-TRACED"], effects=dict(stage_index="level select: any of the 18 (zone, act) pairs; attract: demo acts", rings="level select starts with the New Game values", timer="n/a", score="n/a", lives="n/a", continues="n/a", emeralds="n/a", result_card="n/a", powerups="n/a", player_identity="n/a", restart_position="n/a"),
         oracle=[], notes="These are developer/test fixtures of the ORIGINAL ROM, not part of the natural campaign; START_INDEX in the oracle reproduces the level select's two stores."),
]

# --------------------------------------------------------------------------------------------------------------------------------------------
RULES = dict(
    lives=dict(initial="3 Sonic / 5 Tails (character-select cursor 0 / 1)", max=99, decrement="$15FB once per death (before the animation), BCD DAA",
               increments=["100th ring ($3138 -> $3104)", "ten-ring monitor wrap ($4AC0 result < $10 -> $3104)", "1-UP monitor (D3A3 bit1 -> $4ADA -> $3104)", "sign prize class 1 via vector $03F2 -> $3104", "sign retouch roll, class 1 (0C:$A8FA)", "a time/ring bonus word whose digits are all equal, including the $0777 substituted for a zero bonus, via $03F2 (0C:$AB66)"],
               not_awarded_by=["score thresholds (these give continues)", "Special Stage success (gives a continue)", "Special Stage failure or timeout (costs nothing)"], game_over="post-death lives == 0"),
    continues=dict(initial="0 Sonic / 3 Tails", bit7="'continue used' flag, set by $1491, cleared by $13ED", increments=["score threshold ($26BD)", "sign prize class 3 (0C:$A9CF, BCD INC with DAA, bit7 cleared)", "Special Stage success (1E:$94BC)"], consumed="only by accepting the continue screen ($1491); a timed-out screen consumes nothing", cap="display shows min(7 bits, 8) icons ($337F); the byte itself has no other cap"),
    emeralds=dict(cleared_by="power-on and New Game only", set_by="Special Stage success (bit n) and the final-zone $61 object (bit5 when flags == $1F)", selection="stage = 8 + count of consecutive set low bits (max 4); refused when (D2CC & $1F) == $1F", ending="Sonic: D2CC & $3F == $3F full ending, otherwise partial; other characters: own ending"),
    timer=dict(act="counts up; 10:00 sets D44B=$C0 -> death (TIME OVER screen); stops at sign contact; reset by every level load", stage="59 s countdown, underflow = stage failure", tick="D2C2 counts 60 frames per second and is not cleared by a load"),
    rings=dict(wrap="99+1 -> 00 awards a life and may enter a stage", scope="act: zeroed by every level load; never carried between acts; tally drains it to 0", prize="rings +$10 (class 2) drops the BCD carry and awards nothing"),
    score=dict(units="raw BCD; ring tally +10 raw per ring, time/ring bonus word +1 raw per step, act-3 boss bonus 50/100/150/200/250 steps x10 raw by zone, stage rings x10 raw, stage seconds x100 raw", cleared="New Game and continue accept", hud="six BCD digits + fixed block at $3BA6 (display factor probable x10, not decoded)"),
    player_identity=dict(character="D2C8 1 Sonic / 2 Tails, fixed for the run; only Sonic enters Special Stages; the ending path differs"),
    checkpoints=dict(exists=False, evidence="restart position comes only from the ROM table at $4E65..$4E94 keyed by (zone, act); 18/18 acts restart at the fresh-load position after a death"),
    saving=dict(exists=False, evidence="no cartridge RAM: the only $FFFC writes are the start-up mapper writes at $0008/$0466; progress lives in RAM only (REUSED special-stages-progression-audit.md)"),
)

OUTCOMES = [
    dict(event="act clear", where="act index 0 or 1, any zone", result="act := act + 1, same zone; results + tally + fades; rings 0, timer reset, powerups cleared; score += tally; lives/continues by sign prize class", transition="T04"),
    dict(event="act clear", where="act index 2, zone 0..4", result="(zone + 1, act 0); results + boss bonus + tally; score += boss bonus", transition="T05"),
    dict(event="act clear", where="act index 2, zone 5", result="zone 6 -> ending selector -> title; no results", transition="T06"),
    dict(event="death", where="lives after decrement > 0", result="same (zone, act) reloads at its ROM start; lives -1, rings 0, timer reset, powerups cleared, score/continues/emeralds kept", transition="T07"),
    dict(event="death or TIME OVER", where="lives after decrement == 0 and continues > 0", result="continue screen; button -> lives 3 (5), score 0, continues -1, same (zone, act); no button -> Game Over", transition="T08/T09"),
    dict(event="death or TIME OVER", where="lives after decrement == 0 and continues == 0", result="Game Over screen -> title", transition="T09"),
    dict(event="100th ring", where="Sonic, zone < 6, emeralds != $1F, act index 0 or 1", result="life +1, Special Stage n (n = 1 + consecutive set bits), then return to (zone, act + 1)", transition="T11/T12/T15"),
    dict(event="100th ring", where="Tails, or emeralds == $1F", result="life +1 only", transition="T11"),
    dict(event="100th ring", where="act index 2", result="FORCED-ONLY: not reachable (<= 83 rings per such act); a fixture returns to act index 3 and pays the boss bonus", transition="T16"),
    dict(event="Special Stage success", where="any", result="emerald bit, continue +1, tally, return to (zone, act + 1)", transition="T13/T15"),
    dict(event="Special Stage failure / timeout", where="any", result="no emerald, no life cost, tally of stage rings, return to (zone, act + 1)", transition="T14/T15"),
    dict(event="New Game", where="from the title", result="zone 0 act 0, lives 3 (5), continues 0 (3), rings/score/emeralds 0", transition="T02/T10"),
]

UNRESOLVED = [
    dict(id="U1", item="Display factor of the HUD score and the card text ('RING n x 100')", state="partial: the HUD draws six BCD digits plus a fixed block at name-table $3BA6; whether it is a literal '0' glyph (x10 display) is not decoded", blocks="G2 score display only"),
    dict(id="U2", item="Which boss objects allocate the bonus object type $0A (0C:$9C58..$9C96, which calls $041F) in each zone's act 3", state="evidenced for AQZ3 $59 and EEZ $61 in earlier audits; THZ3/GPZ3/SEZ3/MGHZ3 not traced here; the spine injects the flag so it contains no boss time bonus", blocks="exact act-3 score for natural boss play"),
    dict(id="U3", item="Sign prize table for zones with odd parity (table $A962) semantics beyond the class mapping, and the $A8FA retouch re-roll for every zone", state="decoded in docs/object-18-act-clear.md for the THZ table; the oracle exercises only zone 0", blocks="G2 sign prize completeness"),
    dict(id="U4", item="Presentation of the ordinary results card, continue screen, Game Over screen, TIME OVER screen and the act-clear fades (tile data, palettes, text)", state="control flow and timings traced; graphics not extracted (card tilemaps at $A58C/$A60C, $3436/$345B/$3478/$3495 draw routines)", blocks="G1/G2 presentation"),
    dict(id="U5", item="Sound request meanings ($87 Game Over, $94 continue, $A0 accept, $89/$97 clear, $A9 life, $B4 tally step, $8A stage)", state="request numbers observed; names/assets unresolved (AUDIO-0)", blocks="audio only"),
    dict(id="U6", item="Tails-specific campaign differences beyond lives/continues start, the score-continue rule and the ending branch", state="unresearched (movement, signs, bosses, art)", blocks="G6"),
    dict(id="U7", item="Whether any enemy/monitor/boss score table awards use a path other than $262F", state="all adds found go through $262F (JP at 1:$5F81 and CALL $2F0C); award values per object type not enumerated", blocks="G2 score parity"),
    dict(id="U8", item="Timing equality between the harness frame counter and the real console for the 198/96/48-frame waits", state="waits are counted loop iterations of the frame wait $062D; the harness is approximate for VDP timing only", blocks="none"),
]
