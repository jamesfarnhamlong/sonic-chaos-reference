#!/usr/bin/env python3
"""G0-R: ordinary-campaign ROM contract - oracle runner, static census, contract assembly and checker.

    python tools/g0_campaign.py /path/to/SonicChaos.sms                 # regenerate data/g0/*.json (needs Python >= 3.10 and the z80 package)
    python tools/g0_campaign.py /path/to/SonicChaos.sms --check         # re-run everything and compare with the committed files
    python tools/g0_campaign.py /path/to/SonicChaos.sms --only new_game_sonic,death_pit_lives3 --print
    python tools/g0_campaign.py --validate                              # no ROM: evaluate the contract's expectations on the committed oracle

Outputs:
  data/g0/campaign-oracle.json   observations of the ORIGINAL ROM (deterministic harness frames, hex/BCD strings)
  data/g0/campaign-contract.json hand-authored transition contract + evaluated expectations + static ROM census + palette-fade answer
  data/g0/g1-g2-ledger.json      ordered G1/G2 dependency ledger and the FULLGAME-0 reconciliation (tools/g0_ledger.py)

The ROM is read from the argument or SONIC_CHAOS_ROM; no ROM bytes are written anywhere.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import g0_contract as C  # noqa: E402

OUT = ROOT / "data" / "g0"
ORACLE_JSON = OUT / "campaign-oracle.json"
CONTRACT_JSON = OUT / "campaign-contract.json"
LEDGER_JSON = OUT / "g1-g2-ledger.json"
ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
BASE_COMMIT = "0bb7390813a8fa4320ef35253a2c39598eee8e08"

# (oracle id, scenario function, kwargs) - order is the order in the JSON
ORACLE = [
    ("new_game_sonic", "sc_new_game", dict(character=0)),
    ("new_game_tails", "sc_new_game", dict(character=1)),
    ("clear_thz1_rings00", "sc_ordinary_clear", dict(rings=0x00)),
    ("clear_thz1_rings15", "sc_ordinary_clear", dict(rings=0x15)),
    ("clear_thz1_rings55", "sc_ordinary_clear", dict(rings=0x55)),
    ("clear_thz1_rings09", "sc_ordinary_clear", dict(rings=0x09)),
    ("campaign_spine", "sc_campaign_spine", dict()),
    ("death_pit_lives3", "sc_death", dict(kind="pit", lives=3)),
    ("death_time_over_lives3", "sc_death", dict(kind="time_over", lives=3)),
    ("death_continue_accept_sonic", "sc_death", dict(kind="pit", lives=1, continues=2, answer="continue")),
    ("death_continue_accept_tails", "sc_death", dict(kind="pit", lives=1, continues=2, answer="continue", character=1)),
    ("death_continue_timeout", "sc_death", dict(kind="pit", lives=1, continues=2, answer="wait", then_new_game=True)),
    ("death_game_over_no_continue", "sc_death", dict(kind="pit", lives=1, continues=0, then_new_game=True)),
    ("ring100_sonic", "sc_hundred_ring", dict()),
    ("ring100_tails", "sc_hundred_ring", dict(character=1)),
    ("ring100_all_emeralds", "sc_hundred_ring", dict(emeralds=0x1F)),
    ("ring100_ten_monitor", "sc_hundred_ring", dict(how="ten_ring_monitor", rings=0x95)),
    ("ring100_lives_cap", "sc_hundred_ring", dict(preset=dict(lives=0x99))),
    ("oneup_monitor", "sc_hundred_ring", dict(how="one_up_monitor")),
    ("ring100_act3_forced", "sc_hundred_ring", dict(start_index=[0, 2])),
    ("ss_select_mask00", "sc_hundred_ring", dict(emeralds=0x00)),
    ("ss_select_mask01", "sc_hundred_ring", dict(emeralds=0x01)),
    ("ss_select_mask03", "sc_hundred_ring", dict(emeralds=0x03)),
    ("ss_select_mask07", "sc_hundred_ring", dict(emeralds=0x07)),
    ("ss_select_mask0F", "sc_hundred_ring", dict(emeralds=0x0F)),
    ("special_stage_success", "sc_special_stage", dict(kind="success")),
    ("special_stage_timeout", "sc_special_stage", dict(kind="timeout")),
    ("special_stage_death_act2", "sc_special_stage", dict(kind="death", origin=[0, 1])),
    ("special_stage_death_act3_forced", "sc_special_stage", dict(kind="death", origin=[0, 2])),
    ("ending_sonic_full", "sc_ending", dict(character=0, mask=0x3F)),
    ("ending_sonic_partial", "sc_ending", dict(character=0, mask=0x1F)),
    ("ending_sonic_20_only", "sc_ending", dict(character=0, mask=0x20)),
    ("ending_tails", "sc_ending", dict(character=1, mask=0x3F)),
    ("restart_matrix", "sc_restart_matrix", dict()),
    ("score_continue_rule", "sc_score_continue_rule", dict()),
]


# --------------------------------------------------------------------------------------------------------------------------------------------
def load_rom(path=None):
    import rom as R
    p = Path(path or os.environ.get("SONIC_CHAOS_ROM", str(ROOT.parent / "source" / "Sonic Chaos (Europe).sms")))
    return R.load(p)


def _run_one(args):
    """Worker: one scenario in its own process (each builds its own console)."""
    rom_path, sid, fn, kw = args
    import g0_scenarios as S
    rom = load_rom(rom_path)
    return sid, getattr(S, fn)(rom, **kw)


def run_oracle(rom_path, only=None, jobs=4):
    work = [(str(rom_path), sid, fn, kw) for sid, fn, kw in ORACLE if only is None or sid in only]
    results = {}
    if jobs <= 1:
        for w in work:
            sid, r = _run_one(w)
            results[sid] = r
    else:
        with ProcessPoolExecutor(max_workers=jobs) as ex:
            for sid, r in ex.map(_run_one, work):
                results[sid] = r
    order = [sid for sid, _, _ in ORACLE if sid in results]
    return {sid: results[sid] for sid in order}


# --------------------------------------------------------------------------------------------------------------------------------------------
# static ROM census
# --------------------------------------------------------------------------------------------------------------------------------------------
TRACKED = {
    0xD299: "lives", 0xD2C3: "continues", 0xD2CC: "emeralds", 0xD2CD: "result_card", 0xD2A6: "bonus", 0xD29A: "rings", 0xD29D: "score_lo", 0xD29E: "score_mid",
    0xD29F: "score_hi", 0xD2C8: "character", 0xD295: "started", 0xD296: "saved_zone", 0xD44B: "timeover",
}
OPS = {0x32: "ST A,(nn)", 0x3A: "LD A,(nn)", 0x21: "LD HL,nn", 0x22: "ST HL,(nn)", 0x2A: "LD HL,(nn)", 0x01: "LD BC,nn", 0x11: "LD DE,nn"}
# sites read and classified in this package (CPU address in its bank -> role)
CLASSIFIED = {
    ("lives", 0x13D4): "continue restore: lives := 3 (Sonic) / 5", ("lives", 0x15F5): "life lost: read", ("lives", 0x15FB): "life lost: lives - 1 (DAA)",
    ("lives", 0x165B): "lives == 0 test after death", ("lives", 0x3113): "$3104 award: lives + 1 (cap $99)", ("lives", 0x355D): "character select init: 3 Sonic / 5 Tails",
    ("continues", 0x1396): "game over/continue branch test (bit7)", ("continues", 0x13ED): "continue check: RES bit7, test low bits", ("continues", 0x1491): "continue accepted: DEC, SET bit7",
    ("continues", 0x26BD): "score award: read", ("continues", 0x26C9): "score award: +1 (bit7 kept)", ("continues", 0x337F): "results card: draw icons", ("continues", 0x3561): "character select init: 0 Sonic / 3 Tails",
    ("continues", 0xA9CF): "sign prize class 3: read", ("continues", 0xA9D6): "sign prize class 3: +1 (BCD INC, bit7 dropped)", ("continues", 0x94BC): "stage success: read", ("continues", 0x94C2): "stage success: +1",
    ("emeralds", 0x2A1F): "New Game: cleared", ("emeralds", 0x179A): "stage entry gate: read", ("emeralds", 0x1883): "stage selector: read", ("emeralds", 0x18F4): "ending selector: read",
    ("emeralds", 0x33F1): "results card icons: read", ("emeralds", 0x94A7): "stage Emerald object: |= bit", ("emeralds", 0xBB69): "final-zone $61 object: |= $20",
    ("result_card", 0x17AC): "stage entry: := 1", ("result_card", 0x3308): "results card selector", ("result_card", 0x33D7): "results card drawn: := 0", ("result_card", 0x94AC): "stage success: := $FF",
    ("rings", 0x3138): "ring pickup +1 (wrap)", ("rings", 0x2A50): "level load: := 0", ("rings", 0x2D15): "tally: -1 per step", ("rings", 0x4AC8): "ten-ring monitor +$10", ("rings", 0xA9C5): "sign prize class 2: +$10",
    ("rings", 0x2CBB): "attract demo setup := $20", ("bonus", 0x2D28): "tally: read bonus word", ("bonus", 0x2D41): "tally: store counted-down bonus", ("bonus", 0xAB52): "$19 sign child: := bonus",
    ("bonus", 0x9C96): "type $0A bonus object: := bonus ($041F)", ("bonus", 0x949D): "stage success: := seconds << 8",
    ("started", 0x2C18): "title START: := 0", ("started", 0x3549): "character select done: := $FF", ("started", 0x086C): "hidden level select done: := $FF",
    ("saved_zone", 0x187E): "stage entry: := zone", ("timeover", 0x281E): "timer 10:00: := $C0",
}


def writer_census(rom):
    rows = []
    for addr, name in TRACKED.items():
        lo, hi = addr & 255, addr >> 8
        i = 0
        sites = []
        while True:
            i = rom.find(bytes([lo, hi]), i)
            if i < 0:
                break
            op = rom[i - 1]
            if op in OPS and i - 1 >= 0:
                off = i - 1
                bank = off // 0x4000
                cpu = off if off < 0x8000 else 0x8000 + off % 0x4000
                sites.append(dict(file=format(off, "05X"), bank=format(bank, "02X"), cpu=format(cpu, "04X"), kind=OPS[op],
                                  role=CLASSIFIED.get((name, cpu)) or CLASSIFIED.get((name, cpu & 0xFFFF)) or "unclassified (not read in this package)"))
            i += 1
        rows.append(dict(name=name, address=format(addr, "04X"), sites=sites))
    return rows


def routine_hashes(rom):
    return [dict(name=n, start=format(a, "04X"), end=format(b, "04X"), length=b - a, sha256=hashlib.sha256(rom[a:b]).hexdigest()) for n, a, b in C.ROUTINES]


def start_positions(rom):
    u = lambda o: rom[o] | (rom[o + 1] << 8)  # noqa: E731
    rows = []
    for z in range(6):
        tbl = u(0x4E98 + 2 * z)
        for a in range(3):
            rec = u(tbl + 2 * a)
            rows.append(dict(zone=z, act=a, record=format(rec, "04X"), camera_x=u(rec), camera_y=u(rec + 2), player_x=u(rec + 4), player_y=u(rec + 6)))
    return rows


def prize_tables(rom):
    """The two 64-byte ring-count tables used by the goal-sign landing `$A8FA` (bank $0C, CPIR over 4 groups of 16)."""
    def rows(cpu):
        off = 0x0C * 0x4000 + cpu - 0x8000
        t = rom[off:off + 64]
        return [["%02X" % x for x in t[i * 16:(i + 1) * 16] if x != 0xFF] for i in range(4)]
    return dict(selection="LD A,($D297); INC A; RRCA; carry -> table $A919 (zones 0,2,4), no carry -> table $A962 (zones 1,3,5)",
                zones_0_2_4=rows(0xA919), zones_1_3_5=rows(0xA962),
                class_rule="class = 3 - (index of the first CPIR match // 16); no match = $FF; class 3 -> D2C3 + 1 (continue), 2 -> rings + $10, 1 -> $03F2 -> $3104 (life), 0 -> retry",
                correction="docs/object-18-act-clear.md labels class 3 as 'lives' (D2C3): D2C3 is the CONTINUE counter (G0-R); class 1 ($03F2 -> $3104) is the life award")


def act3_bonus_table(rom):
    iters = [rom[0x2D84 + 2 * z] | (rom[0x2D85 + 2 * z] << 8) for z in range(6)]
    return dict(iterations=iters, raw_units_each=10, raw_total=[10 * n for n in iters], used_zones=[0, 1, 2, 3, 4], note="index 5 (EEZ) is unreachable: zone 5 skips the results screen")


# --------------------------------------------------------------------------------------------------------------------------------------------
# expectations
# --------------------------------------------------------------------------------------------------------------------------------------------
def dec(n, w=6):
    return "%0*d" % (w, n)          # BCD digit strings equal the decimal digits


def bonus_word(rings_dec, time_entry=9):
    low = (rings_dec - 11) % 100
    return "%02d%02d" % (time_entry, low)


def clear_score(rings_dec_after_prize, time_entry=9):
    return dec(10 * rings_dec_after_prize + time_entry * 100 + (rings_dec_after_prize - 11) % 100)


EXPECT = []


def X(sid, path, op, value, why):
    EXPECT.append(dict(scenario=sid, path=path, op=op, value=value, why=why))


def build_expectations():
    EXPECT.clear()
    # ---- T02 New Game
    for sid, lives, cont, chara in (("new_game_sonic", "03", "00", 1), ("new_game_tails", "05", "03", 2)):
        X(sid, "in_play.lives_bcd", "==", lives, "$3550..$355D: B := 3 (Sonic cursor) / 5 (Tails cursor)")
        X(sid, "in_play.continues_raw", "==", cont, "$3560/$3561: C := 0 / 3")
        X(sid, "in_play.character", "==", chara, "$30C5 increments the cursor into D2C8")
        for k, v in (("zone", 0), ("act", 0), ("rings_bcd", "00"), ("score_bcd", "000000"), ("emeralds", "00"), ("flow", "40"), ("started", "FF")):
            X(sid, "in_play." + k, "==", v, "T02 reset values ($07CE, $2A00, $3549)")
        X(sid, "checkpoints.new_game_init.emeralds", "==", "1F", "fixture: dirty pre-state is really present when $04D4 runs")
        X(sid, "checkpoints.new_game_init.rings_bcd", "==", "55", "fixture: dirty rings present before $2A00")
    # ---- T04 act clear (THZ1 -> THZ2, real sign chain)
    for sid, rings, prize_cont, prize_life, after_rings in (("clear_thz1_rings00", 0, 0, 0, 0), ("clear_thz1_rings15", 15, 1, 0, 15), ("clear_thz1_rings55", 55, 0, 1, 55), ("clear_thz1_rings09", 9, 0, 0, 19)):
        X(sid, "end_in_play.act", "==", 1, "$1538: act += 1")
        X(sid, "end_in_play.zone", "==", 0, "act clear does not change the zone")
        X(sid, "end_in_play.rings_bcd", "==", "00", "tally drains and $2A50 zeroes rings")
        X(sid, "end_in_play.emeralds", "==", "03", "emerald byte is run-scoped and survives the act clear")
        X(sid, "end_in_play.powerup", "==", "00", "object RAM block cleared by $297E (fixture set D532 := 4)")
        X(sid, "start.powerup", "==", "04", "fixture check")
        X(sid, "end_in_play.character", "==", 1, "player identity kept")
        X(sid, "end_in_play.lives_bcd", "==", "%02d" % (3 + prize_life), "sign prize class 1 -> $3104 (+1 life) only for rings 55")
        X(sid, "end_in_play.continues_raw", "==", "%02d" % prize_cont, "sign prize class 3 -> D2C3 + 1 (a continue) only for rings 15")
        X(sid, "end_in_play.score_bcd", "==", clear_score(after_rings), "tally: +10 raw per ring then the bonus word (time entry 9 x100 + (rings-11)) +1 raw per step")
        X(sid, "flag_raised.bonus", "==", bonus_word(after_rings), "$041F bonus word computed by the $19 child")
        X(sid, "relative_frames.flag_bit5_set", "==", 309, "contact -> flag, REUSED object-18 timeline (+309)")
        X(sid, "relative_frames.results_screen", "-", dict(b="relative_frames.act_clear_sequence", equals=198), "$14AE waits 60+96+30+12 frames before $32F9")
        X(sid, "relative_frames.palette_fill_3f", "-", dict(b="relative_frames.fade_request", equals=96), "$1507 .. $1521: wait 96")
        X(sid, "relative_frames.progress_act", "-", dict(b="relative_frames.palette_fill_3f", equals=48), "$1524 wait 48 then $152F")
        X(sid, "post_tally_fade.to_white_frame", ">", 0, "palette fades to full white after the tally")
        X(sid, "post_tally_fade.to_black_frame", ">", 0, "and then to black before the next act loads")
    X("clear_thz1_rings15", "flag_raised.continues_raw", "==", "01", "class 3 prize lands at the sign (before the results)")
    X("clear_thz1_rings55", "flag_raised.lives_bcd", "==", "04", "class 1 prize lands at the sign")
    X("clear_thz1_rings09", "flag_raised.rings_bcd", "==", "19", "class 2: rings + $10 (carry dropped) before the tally")
    # ---- full campaign spine
    seq = [(z, a) for z in range(6) for a in range(3)]
    for i, (z, a) in enumerate(seq[:-1]):
        nz, na = seq[i + 1]
        X("campaign_spine", "acts.%d.after.zone" % i, "==", nz, "next (zone, act) after (%d,%d)" % (z, a))
        X("campaign_spine", "acts.%d.after.act" % i, "==", na, "next (zone, act) after (%d,%d)" % (z, a))
        X("campaign_spine", "acts.%d.results_shown" % i, "==", 1, "$32F9 runs for every non-final clear")
    X("campaign_spine", "acts.17.results_shown", "==", 0, "zone 5 skips the results screen ($1597 CP 5)")
    X("campaign_spine", "acts.17.after.zone", "==", 6, "$15D6 zone := 6 -> end path")
    X("campaign_spine", "events.end_path.count", "==", 1, "$1365 once")
    X("campaign_spine", "events.ending_partial.count", "==", 1, "no emeralds -> partial ending")
    X("campaign_spine", "events.results_screen.count", "==", 17, "17 results screens in 18 clears")
    X("campaign_spine", "events.act3_bonus_tally.count", "==", 17, "$2D55 runs in each results screen (returns at once unless act index 2)")
    X("campaign_spine", "final.lives_bcd", "==", "03", "no life is gained or lost in a clean run")
    boss = {0: 500, 1: 1000, 2: 1500, 3: 2000, 4: 2500}
    for zone, bonus in boss.items():
        i = zone * 3 + 2
        prev = 0
        X("campaign_spine", "acts.%d.at_flag.zone" % i, "==", zone, "act index 2 of zone %d" % zone)
        X("campaign_spine", "acts.%d.results_shown" % i, "==", 1, "zone < 5 shows results")
    # score deltas via explicit running sums (acts 0/1 of THZ pay the 0989 sign bonus; everything else is injected so only the boss bonus pays)
    total = 0
    for i, (z, a) in enumerate(seq[:-1]):
        if z == 0 and a < 2:
            total += 989
        elif a == 2:
            total += boss[z]
        X("campaign_spine", "acts.%d.after.score_bcd" % i, "==", dec(total), "running score: THZ1/THZ2 sign bonus 989 raw (0 rings, <0:30), boss bonus table for act index 2, injected acts pay nothing")
    X("campaign_spine", "acts.11.after.continues_raw", "==", "01", "score crossed 5,000 raw (4978 -> 6978) -> Sonic continue award")
    X("campaign_spine", "acts.10.after.continues_raw", "==", "00", "before the crossing no continue")
    # ---- T07/T08/T09 deaths
    X("death_pit_lives3", "before.lives_bcd", "==", "03", "fixture")
    X("death_pit_lives3", "checkpoints.life_decremented.lives_bcd", "==", "02", "$15FB: lives - 1")
    X("death_pit_lives3", "end.lives_bcd", "==", "02", "one life lost")
    X("death_pit_lives3", "end.zone", "==", 0, "same zone")
    X("death_pit_lives3", "end.act", "==", 0, "same act")
    X("death_pit_lives3", "end.rings_bcd", "==", "00", "rings reset by the reload")
    X("death_pit_lives3", "end.powerup", "==", "00", "power-up cleared")
    X("death_pit_lives3", "end.emeralds", "==", "07", "emeralds kept")
    X("death_pit_lives3", "end.score_bcd", "==", "001230", "score kept on death")
    X("death_pit_lives3", "end.continues_raw", "==", "00", "continues kept")
    X("death_pit_lives3", "end.time", "startswith", "00:00.", "timer restarted at 0:00")
    X("death_pit_lives3", "end.player.x", "==", 142, "ROM start position of THZ1 (no checkpoint)")
    X("death_pit_lives3", "end.player.y", "==", 654, "ROM start position of THZ1 (no checkpoint)")
    X("death_pit_lives3", "counts.time_over_screen", "absent", None, "a pit death shows no TIME OVER screen")
    X("death_time_over_lives3", "counts.time_over_screen", "==", 1, "D44B bit7 -> $3495")
    X("death_time_over_lives3", "end.lives_bcd", "==", "02", "TIME OVER costs one life")
    X("death_time_over_lives3", "end.time", "startswith", "00:00.", "timer restarted")
    X("death_continue_accept_sonic", "checkpoints.continue_accepted.continues_raw", "==", "02", "state before $1491 decrements")
    X("death_continue_accept_sonic", "end.continues_raw", "==", "81", "$1491: (2 - 1) | $80")
    X("death_continue_accept_sonic", "end.lives_bcd", "==", "03", "$13C9: lives := 3 for Sonic")
    X("death_continue_accept_sonic", "end.score_bcd", "==", "000000", "$13D8..$13DE: score cleared")
    X("death_continue_accept_sonic", "end.emeralds", "==", "07", "emeralds kept")
    X("death_continue_accept_sonic", "end.zone", "==", 0, "restarts the same zone")
    X("death_continue_accept_sonic", "end.act", "==", 0, "restarts the same act")
    X("death_continue_accept_sonic", "counts.game_over_screen", "absent", None, "no Game Over when a continue is taken")
    X("death_continue_accept_tails", "end.lives_bcd", "==", "05", "$13C9: lives := 5 for the other character")
    X("death_continue_accept_tails", "end.continues_raw", "==", "81", "same consume rule")
    X("death_continue_accept_tails", "end.character", "==", 2, "character kept")
    X("death_continue_timeout", "counts.continue_screen", "==", 1, "continue screen shown")
    X("death_continue_timeout", "counts.game_over_screen", "==", 1, "countdown expiry -> Game Over")
    X("death_continue_timeout", "counts.continue_accepted", "absent", None, "no button")
    X("death_continue_timeout", "end.continues_raw", "==", "02", "an unused continue is not consumed (bit7 cleared by $13ED)")
    X("death_continue_timeout", "end.emeralds", "==", "07", "emeralds still set at the title")
    X("death_continue_timeout", "new_game_in_play.emeralds", "==", "00", "New Game clears emeralds")
    X("death_continue_timeout", "new_game_in_play.lives_bcd", "==", "03", "New Game lives")
    X("death_continue_timeout", "new_game_in_play.continues_raw", "==", "00", "New Game continues")
    X("death_continue_timeout", "new_game_in_play.score_bcd", "==", "000000", "New Game score")
    X("death_game_over_no_continue", "counts.continue_screen", "absent", None, "no continues -> no continue screen")
    X("death_game_over_no_continue", "counts.game_over_screen", "==", 1, "$139D Game Over")
    X("death_game_over_no_continue", "counts.title", "==", 1, "-> title")
    X("death_game_over_no_continue", "new_game_in_play.emeralds", "==", "00", "New Game clears emeralds")
    # ---- T11 hundred rings / life awards
    X("ring100_sonic", "after_award.lives_bcd", "==", "04", "$3104 +1")
    X("ring100_sonic", "after_award.mode", "==", "88", "$17A7")
    X("ring100_sonic", "after_award.result_card", "==", "01", "$17AC")
    X("ring100_sonic", "stage.zone", "==", 8, "no emeralds -> Special Stage 1 = zone 8")
    X("ring100_sonic", "stage.saved_zone", "==", 0, "$187E")
    X("ring100_tails", "after_award.lives_bcd", "==", "06", "5 + 1")
    X("ring100_tails", "stage_entered", "==", False, "$178F: D2C8 != 1 refuses entry")
    X("ring100_all_emeralds", "after_award.lives_bcd", "==", "04", "life still awarded")
    X("ring100_all_emeralds", "stage_entered", "==", False, "$179A..$17A1: all five bits set -> refused")
    X("ring100_ten_monitor", "after_award.rings_bcd", "==", "05", "$4AC5 keeps the post-wrap value")
    X("ring100_ten_monitor", "after_award.lives_bcd", "==", "04", "$4AD4 -> $3104")
    X("ring100_ten_monitor", "stage_entered", "==", True, "$4AD7 JP $178F")
    X("ring100_lives_cap", "after_award.lives_bcd", "==", "99", "$310C: cap at $99")
    X("ring100_lives_cap", "stage_entered", "==", True, "cap does not stop the stage")
    X("oneup_monitor", "after_award.lives_bcd", "==", "04", "$4ADA -> $3104")
    X("oneup_monitor", "stage_entered", "==", False, "no ring wrap")
    X("ring100_act3_forced", "before.act", "==", 2, "fixture: act index 2")
    X("ring100_act3_forced", "stage_entered", "==", True, "$178F does not read the act index (FORCED-ONLY, see T16)")
    for sid, zone in (("ss_select_mask00", 8), ("ss_select_mask01", 9), ("ss_select_mask03", 10), ("ss_select_mask07", 11), ("ss_select_mask0F", 12)):
        X(sid, "stage.zone", "==", zone, "$187B: 8 + consecutive set low bits")
    # ---- T12-T15 Special Stage detours
    X("special_stage_success", "entry.before_ring.lives_bcd", "==", "03", "before the 100th ring")
    X("special_stage_success", "entry.stage_playable.lives_bcd", "==", "04", "+1 at the ring wrap")
    X("special_stage_success", "entry.stage_playable.zone", "==", 8, "Special Stage 1")
    X("special_stage_success", "exit_state.mode", "==", "C0", "success + stage active")
    X("special_stage_success", "exit_state.emeralds", "==", "01", "1E:$94A7")
    X("special_stage_success", "exit_state.continues_raw", "==", "01", "1E:$94C2 +1")
    X("special_stage_success", "exit_state.result_card", "==", "FF", "1E:$94AC")
    X("special_stage_success", "end_in_play.zone", "==", 0, "back in the origin zone")
    X("special_stage_success", "end_in_play.act", "==", 1, "NEXT act, not the same act")
    X("special_stage_success", "end_in_play.rings_bcd", "==", "00", "rings do not carry")
    X("special_stage_success", "end_in_play.emeralds", "==", "01", "emerald kept")
    X("special_stage_success", "end_in_play.continues_raw", "==", "01", "continue kept")
    X("special_stage_success", "end_in_play.powerup", "==", "00", "power-ups do not carry")
    X("special_stage_success", "end_in_play.result_card", "==", "00", "card consumed")
    X("special_stage_success", "end_in_play.score_bcd", ">", "000000", "tally added score")
    X("special_stage_success", "counts.life_award", "==", 2, "the accepted input-only SS1 route wraps the ring counter twice inside the stage")
    X("special_stage_success", "end_in_play.lives_bcd", "==", "06", "lives earned in the stage persist after the return (04 + 2)")
    X("special_stage_success", "post_tally_fade.to_white_frame", ">", 0, "post-tally fade to white also runs after a stage")
    X("special_stage_success", "post_tally_fade.to_black_frame", ">", 0, "and to black before the act is loaded")
    X("special_stage_timeout", "exit_state.mode", "==", "A0", "failure + stage active")
    X("special_stage_timeout", "exit_state.emeralds", "==", "00", "no emerald")
    X("special_stage_timeout", "exit_state.lives_bcd", "==", "04", "no life lost")
    X("special_stage_timeout", "end_in_play.act", "==", 1, "next act")
    X("special_stage_timeout", "end_in_play.lives_bcd", "==", "04", "no life lost")
    X("special_stage_timeout", "end_in_play.continues_raw", "==", "00", "no continue")
    X("special_stage_death_act2", "end_in_play.act", "==", 2, "origin act index 1 -> act index 2 (Act 3)")
    X("special_stage_death_act2", "end_in_play.zone", "==", 0, "zone kept")
    X("special_stage_death_act2", "exit_state.lives_bcd", "==", "04", "no life lost on a stage death")
    X("special_stage_death_act3_forced", "end_in_play.act", "==", 3, "FORCED-ONLY alias: act index 3")
    X("special_stage_death_act3_forced", "end_in_play.score_bcd", "==", "000500", "act-3 boss bonus (zone 0: 50 x 10 raw) paid on the stage return")
    X("special_stage_death_act3_forced", "end_in_play.player.y", "==", 384, "zone 0 act 3 loads the zone-1 act-0 data (start y 384)")
    # ---- T06 endings
    for sid, ev in (("ending_sonic_full", "ending_full_sonic"), ("ending_sonic_partial", "ending_partial_sonic"), ("ending_sonic_20_only", "ending_partial_sonic"), ("ending_tails", "ending_tails")):
        X(sid, "counts.zone_results_gate", "==", 1, "$1594 reached")
        X(sid, "counts.results_screen", "absent", None, "zone 5 skips $32F9")
        X(sid, "checkpoints.end_path.zone", "==", 6, "$15D6 zone := 6")
        X(sid, "checkpoints.end_path.flow", "==", "C0", "bit7 end path")
        X(sid, "counts." + ev, "==", 1, "ending branch")
        X(sid, "counts.title", "==", 1, "returns to the title")
        X(sid, "title.emeralds", "==", "%02X" % (0x3F if sid != "ending_sonic_partial" and sid != "ending_sonic_20_only" else (0x1F if sid == "ending_sonic_partial" else 0x20)), "emerald byte is left as it was")
        X(sid, "next_new_game.emeralds", "==", "00", "New Game clears emeralds")
        X(sid, "next_new_game.zone", "==", 0, "New Game starts at zone 0 (fixture disabled)")
    for sid, other in (("ending_sonic_full", ("ending_partial_sonic", "ending_tails")), ("ending_sonic_partial", ("ending_full_sonic", "ending_tails")), ("ending_sonic_20_only", ("ending_full_sonic", "ending_tails")), ("ending_tails", ("ending_full_sonic", "ending_partial_sonic"))):
        for o in other:
            X(sid, "counts." + o, "absent", None, "exactly one ending branch")
    # ---- checkpoints
    for i in range(18):
        X("restart_matrix", "acts.%d.same" % i, "==", True, "death restart position == fresh load position")
    X("restart_matrix", "acts.0.fresh_start.0", "==", 142, "THZ1 start x from the ROM table")
    # ---- score rule
    X("score_continue_rule", "rules.sonic.awarded", "==", 20, "Sonic: +1 continue every 5,000 raw")
    X("score_continue_rule", "rules.sonic.new_thousands_digit_set", "==", ["0", "5"], "Sonic rule: new thousands digit 0 or 5")
    X("score_continue_rule", "rules.tails.awarded", "==", 33, "other character: digit-sum rule")
    X("score_continue_rule", "rules.sonic.period_thousands", "==", [5], "Sonic: every 5,000 raw")
    X("score_continue_rule", "rules.tails.period_thousands", "==", [3], "Tails: every 3,000 raw (digit sum mod 3 == thousands count mod 3)")


# --------------------------------------------------------------------------------------------------------------------------------------------
def resolve(obj, path):
    cur = obj
    for part in path.split("."):
        if isinstance(cur, list):
            cur = cur[int(part)]
        elif isinstance(cur, dict):
            if part not in cur:
                raise KeyError(path)
            cur = cur[part]
        else:
            raise KeyError(path)
    return cur


def evaluate(oracle, expectations=None):
    expectations = EXPECT if expectations is None else expectations
    failures = []
    for e in expectations:
        sid = e["scenario"]
        if sid not in oracle:
            failures.append((e, "scenario not in oracle"))
            continue
        obs = oracle[sid]
        try:
            op, want = e["op"], e["value"]
            if op == "absent":
                try:
                    resolve(obs, e["path"])
                    failures.append((e, "present"))
                except KeyError:
                    pass
                continue
            got = resolve(obs, e["path"])
            if op == "==":
                ok = got == want
            elif op == "startswith":
                ok = str(got).startswith(want)
            elif op == ">":
                ok = got is not None and got > want
            elif op == "-":
                ok = got - resolve(obs, want["b"]) == want["equals"]
            else:
                raise ValueError(op)
            if not ok:
                failures.append((e, "got %r" % (got,)))
        except KeyError:
            failures.append((e, "path missing"))
    return failures


# --------------------------------------------------------------------------------------------------------------------------------------------
def palette_answer(oracle):
    rows = {}
    for sid in ("clear_thz1_rings00", "special_stage_success", "special_stage_timeout"):
        o = oracle.get(sid)
        if not o:
            continue
        f = o["post_tally_fade"]
        rf = o["relative_frames"]
        o0 = rf["act_clear_sequence"]
        rows[sid] = dict(tally_returned=rf["tally_returned"] - o0, fade_request=rf["fade_request"] - o0, palette_fill_3f=rf["palette_fill_3f"] - o0, act_incremented=rf["act_incremented"] - o0,
                         palette_steps_after_tally=f["steps"], first_change_after_tally=f["tally_to_first_change"], to_white_frame=f["to_white_frame"], to_black_frame=f["to_black_frame"],
                         black_to_act_increment=f["black_to_increment"], origin="frames relative to the $14AE act-clear sequence entry")
    return dict(
        question="Is there a palette fade or other transition after the Special Stage results tally and before the next ordinary act loads?",
        answer="YES - PROVEN (source-traced + emulated): the Special Stage return runs the ordinary act-clear tail `$14AE`..`$153E`, so after the tally returns the ROM waits 48 frames, requests the fade slots D492/D494 (`$1507..$1517`), waits 96 frames, fills the palette buffer (`$342A`), resets the slots (`$1CAF`), waits 48 frames and only then increments the act (`$1534`) and reloads (`$1673`). The summed CRAM brightness steps up to full white (288) in three 5-frame steps and then down to black (0) in three steps before the act increment; the loader then fades the new act in.",
        code_path=["$1869 sets D293 bit5", "$1333 -> $14AE", "$14FC CALL $32F9 (results + $2D08 tally) returns", "$14FF wait 48", "$1507 D492/D494 := 0|bit6|bit4 (fade request)", "$1519 wait 96", "$1521 CALL $342A (D472..D491 := $3F)", "$1524 CALL $1CAF (slots := 0|bit6)", "$1527 wait 48", "$152F RES 5, act += 1, SET 1 -> $1673 reload"],
        emulated=rows,
        caveats=["CRAM is written by the ROM's own palette routine; the harness VDP is approximate, so the exact frame offsets of CRAM visibility are EMULATED (the 48/96/48 waits are source-exact).",
                 "Brightness is the sum of the 32 CRAM entries' 2-bit channels (0 = black, 288 = all white): it proves a fade to white then black, not the exact palette colours of each step.",
                 "The fade BEFORE the results card (act-clear white flash and results fade-in) is separate and was already known."],
        status="resolved",
    )


def build_all(oracle, rom):
    build_expectations()
    failures = evaluate(oracle)
    import g0_ledger as L
    contract = dict(
        format=1, rom_sha256=ROM_SHA256, base_commit=BASE_COMMIT, evidence_classes=__doc_classes(),
        ram=C.RAM, flow_bits=C.FLOW_BITS, fields=C.FIELDS, transitions=C.TRANSITIONS, rules=C.RULES, outcomes=C.OUTCOMES, unresolved=C.UNRESOLVED,
        routines=routine_hashes(rom), writer_census=writer_census(rom),
        writer_census_caveat="byte census of absolute stores/loads and immediate pointer loads only; register-addressed writes through computed pointers and block clears (the power-on LDIR, $297E) are not enumerated. 'unclassified' means not read in this package, not benign.", start_positions=start_positions(rom), sign_prize_tables=prize_tables(rom),
        act3_boss_bonus_table=act3_bonus_table(rom), palette_fade_answer=palette_answer(oracle),
        expectations=[dict(e, ok=True) for e in EXPECT] if not failures else [dict(e, ok=not any(f[0] is e for f in failures)) for e in EXPECT],
        expectation_failures=[dict(scenario=f[0]["scenario"], path=f[0]["path"], reason=f[1]) for f in failures],
    )
    ledger = L.build(oracle)
    return contract, ledger, failures


def __doc_classes():
    return {k: v for k, v in (
        ("SOURCE-TRACED", "read from the disassembly of the cited routine; byte regions hashed in `routines`"),
        ("EMULATED", "observed in a whole-game run of the original ROM in the approximate SMS harness (named fixtures)"),
        ("CONTROLLED", "an original routine executed alone with explicit RAM"),
        ("REUSED", "accepted earlier Research, cited and not re-derived"),
        ("UNRESOLVED", "not established"))}


def dump(obj):
    return json.dumps(obj, indent=1, ensure_ascii=False) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rom", nargs="?", help="path to the canonical ROM (or SONIC_CHAOS_ROM)")
    ap.add_argument("--check", action="store_true", help="regenerate and compare with the committed files")
    ap.add_argument("--only", help="comma-separated oracle ids (no files are written)")
    ap.add_argument("--print", action="store_true", help="print the selected observations")
    ap.add_argument("--validate", action="store_true", help="evaluate the expectations on the committed oracle (no ROM)")
    ap.add_argument("--from-oracle", action="store_true", help="rebuild contract and ledger from the committed oracle (static ROM parts still recomputed; no emulation)")
    ap.add_argument("--doc", action="store_true", help="re-render the generated tables of docs/g0-campaign-contract.md from the committed JSON (no ROM)")
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args(argv)
    build_expectations()
    if a.doc:
        contract = json.loads(CONTRACT_JSON.read_text(encoding="utf-8"))
        ledger = json.loads(LEDGER_JSON.read_text(encoding="utf-8"))
        import g0_doc
        g0_doc.update(contract, ledger)
        print("updated docs/g0-campaign-contract.md")
        return 0
    if a.validate:
        oracle = json.loads(ORACLE_JSON.read_text(encoding="utf-8"))
        fails = evaluate(oracle)
        for e, why in fails:
            print("FAIL", e["scenario"], e["path"], e["op"], e["value"], "->", why)
        print("expectations:", len(EXPECT), "failures:", len(fails))
        return 1 if fails else 0
    rom_path = a.rom or os.environ.get("SONIC_CHAOS_ROM") or str(ROOT.parent / "source" / "Sonic Chaos (Europe).sms")
    rom = load_rom(rom_path)
    if a.only:
        only = set(a.only.split(","))
        oracle = run_oracle(rom_path, only=only, jobs=min(a.jobs, len(only)))
        fails = evaluate({k: v for k, v in oracle.items()}, [e for e in EXPECT if e["scenario"] in oracle])
        if a.print:
            print(dump(oracle))
        for e, why in fails:
            print("FAIL", e["scenario"], e["path"], e["op"], e["value"], "->", why)
        print("checked", len([e for e in EXPECT if e["scenario"] in oracle]), "expectations; failures:", len(fails))
        return 1 if fails else 0
    oracle = json.loads(ORACLE_JSON.read_text(encoding="utf-8")) if a.from_oracle else run_oracle(rom_path, jobs=a.jobs)
    contract, ledger, failures = build_all(oracle, rom)
    for e, why in failures:
        print("FAIL", e["scenario"], e["path"], e["op"], e["value"], "->", why)
    texts = {CONTRACT_JSON: dump(contract), LEDGER_JSON: dump(ledger)}
    if not a.from_oracle:
        texts[ORACLE_JSON] = dump(oracle)
    if a.check:
        bad = [p.name for p, t in texts.items() if not p.exists() or p.read_text(encoding="utf-8") != t]
        print("check:", "OK" if not bad and not failures else "MISMATCH %s" % bad, "- expectations", len(EXPECT), "failures", len(failures))
        return 1 if bad or failures else 0
    OUT.mkdir(parents=True, exist_ok=True)
    for p, t in texts.items():
        p.write_text(t, encoding="utf-8", newline="\n")
    print("wrote", ", ".join(p.name for p in texts), "- expectations", len(EXPECT), "failures", len(failures))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
