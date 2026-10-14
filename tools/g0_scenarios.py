"""G0-R scenario library: each function drives the ORIGINAL ROM through one ordinary-campaign transition and returns a JSON-able observation.

Observations contain only numbers/strings derived from emulated RAM at named checkpoints (state captured when the CPU reaches a routine, before the
instruction there runs).  Fixtures used by each scenario are listed in its ``fixtures`` field (see tools/g0_rig.py for the three fixture kinds).
Nothing here encodes an expected value; the expectations live in tools/g0_campaign.py and are checked against these observations.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from g0_rig import (Session, RAM, BTN_1, BTN_2, BTN_BOTH, BTN_RIGHT, BTN_LEFT, BTN_UP, BTN_DOWN)  # noqa: E402

THZ_SIGN = {0: 558, 1: 654}


def hx(v, n=2):
    return format(v, "0%dX" % n)


def norm(sn):
    """Snapshot -> stable, human-readable state (BCD fields stay BCD digit strings)."""
    return dict(
        frame=sn["frame"], flow=hx(sn["flow"]), mode=hx(sn["mode"]), menu=hx(sn["menu"]), started=hx(sn["started"]),
        zone=sn["zone"], act=sn["act"], saved_zone=sn["saved_zone"], character=sn["character"],
        lives_bcd=hx(sn["lives"]), continues_raw=hx(sn["continues"]), emeralds=hx(sn["emeralds"]), result_card=hx(sn["card"]),
        rings_bcd=hx(sn["rings"]), score_bcd="%02X%02X%02X" % tuple(sn["score"]), bonus=hx(sn["bonus"], 4),
        time="%02X:%02X.%02d" % (sn["timer"][0], sn["timer"][1], sn["timer"][2]), timer_run=hx(sn["timer_run"]), timeover=hx(sn["timeover"]),
        powerup=hx(sn["powerup"]), power_timer=hx(sn["power_timer"], 4),
        player=dict(type=sn["player"][0], state=hx(sn["player"][1]), requested=hx(sn["player"][2]), x=sn["player"][3], y=sn["player"][4]),
    )


def events_dict(S, names=None, after=0):
    """First occurrence of each marked event (and the hit count)."""
    out = {}
    for n, sn in S.events:
        if names is not None and n not in names:
            continue
        if sn["frame"] < after:
            continue
        e = out.setdefault(n, dict(count=0, first=norm(sn)))
        e["count"] += 1
    return out


def brightness(cram):
    return sum((x & 3) + ((x >> 2) & 3) + ((x >> 4) & 3) for x in cram)


def fade_series(S, start_frame, end_frame):
    """[(frame - start, summed CRAM brightness)] for every frame in the window at which CRAM changed (0..288 = black..all-white)."""
    return [[f - start_frame, brightness(c)] for f, c in S.cram_log if start_frame <= f <= end_frame]


def post_tally_fade(series, tally_rel, inc_rel):
    """Palette changes between the end of the tally and the act-index increment (offsets relative to the same origin as `series`)."""
    steps = [[f, b] for f, b in series if tally_rel < f <= inc_rel]
    white = next((f for f, b in steps if b == 288), None)
    black = next((f for f, b in steps if b == 0 and white is not None and f > white), None)
    return dict(window=[tally_rel, inc_rel], steps=steps, first_change=steps[0][0] if steps else None, to_white_frame=white, to_black_frame=black,
                tally_to_first_change=(steps[0][0] - tally_rel) if steps else None, black_to_increment=(inc_rel - black) if black is not None else None)


def pulse(period=20, width=3):
    return lambda S: (BTN_BOTH if S.s.frame % period < width else 0)


# --------------------------------------------------------------------------------------------------------------------------------------------
def sc_new_game(rom, character=0):
    """Reset -> title -> button -> character select -> new game, with deliberately dirty run state set while the title is up."""
    S = Session(rom)
    for a, n in ((0x2C17, "title_start"), (0x07CE, "zone_act_reset"), (0x3065, "character_select"), (0x3564, "select_confirmed"), (0x04D4, "new_game_init")):
        S.mark_pc(a, n)
    dirty = dict(emeralds=0x1F, rings=0x55, score0=0x99, score1=0x99, score2=0x99, lives=0x07, continues=0x85, zone=0x03, act=0x02)

    def title_hook(S_):
        for k, v in dirty.items():
            S_.w(k, v)
    S.boot_new_game(character=character, title_hook=title_hook)
    ev = events_dict(S)
    return dict(
        fixtures=["PAD title/select buttons", "RAM dirty run state written while the title is displayed: " + json.dumps(dirty, sort_keys=True)],
        character_cursor=character,
        checkpoints={k: v["first"] for k, v in ev.items()},
        in_play=norm(S.snap()),
    )


# --------------------------------------------------------------------------------------------------------------------------------------------
FLAG_MARKS = [
    (0xA8A7, "sign_contact", 0x0C), (0xA8FA, "sign_prize_landing", 0x0C), (0x4892, "player_state_20_request", None), (0x83E9, "flag_bit5_set", 0x0C),
    (0x83ED, "flag_bit4_set", 0x0C), (0x14AE, "act_clear_sequence", None), (0x1543, "zone_clear_sequence", None), (0x32F9, "results_screen", None),
    (0x2D55, "act3_bonus_tally", None), (0x2D08, "ring_time_tally", None), (0x33E8, "tally_returned", None), (0x1507, "fade_request", None),
    (0x1521, "palette_fill_3f", None), (0x1524, "fade_slots_reset", None), (0x152F, "progress_act", None), (0x1534, "act_incremented", None),
    (0x1594, "zone_results_gate", None), (0x15CE, "zone_increment", None), (0x15D6, "zone_store", None), (0x1673, "level_reload", None),
    (0x1365, "end_path", None),
]


def attach_marks(S, marks):
    for a, n, b in marks:
        S.mark_pc(a, n, b)


def advance_until(S, pred, pad=0, limit=6000):
    return S.run_until(pred, pad=pad, limit=limit)


def after_act(S, zone, act, limit=4000):
    """Run until the given (zone, act) is loaded and in play."""
    S.run_until(lambda s: s.m[0xD297] == zone and s.m[0xD298] == act and s.playing(), pad=0, limit=limit)


def sc_ordinary_clear(rom, rings=0x00, character=0):
    """THZ1 -> THZ2 through the real sign chain (contact, hop, prize, `$19` child, player state `$20`, `$83A6`, `$14AE`)."""
    S = Session(rom)
    attach_marks(S, FLAG_MARKS)
    S.boot_new_game(character=character, arrival=Session.place_at_sign(0))
    S.cram_trace()
    pre = dict(rings=rings, powerup=0x04, power_timer=0, emeralds=0x03, continues=0x00)
    S.w("rings", rings)
    S.w("powerup", 0x04)
    S.s.w16(0xD44C, 0x0100)
    S.w("emeralds", 0x03)
    S.w("score2", 0x00)
    start = norm(S.snap())
    S.run_until(lambda s: s.m[0xD293] & 0x30, pad=lambda s: BTN_RIGHT if s.m[0xD501] != 0x20 else 0, limit=3000)
    flag = norm(S.snap())
    S.run_until(lambda s: s.m[0xD298] == 1 and s.playing(), pad=0, limit=4000)
    end = norm(S.snap())
    ev = events_dict(S)
    f = {k: v["first"]["frame"] for k, v in ev.items()}
    fade = fade_series(S, f["act_clear_sequence"], S.s.frame)
    return dict(
        fixtures=["ARRIVAL player+camera placed 160 px before the THZ1 sign (tools/object_18.py fixture)", "PAD RIGHT held until the act-clear flag",
                  "RAM at gameplay start: " + json.dumps({k: hx(v) for k, v in pre.items()})],
        start=start, flag_raised=flag, end_in_play=end, checkpoints={k: v["first"] for k, v in ev.items()},
        relative_frames={k: f[k] - f["sign_contact"] for k in f if k in f and "sign_contact" in f},
        fade_after_act_clear=fade,
        post_tally_fade=post_tally_fade(fade, f["tally_returned"] - f["act_clear_sequence"], f["act_incremented"] - f["act_clear_sequence"]),
    )


def sc_campaign_spine(rom):
    """One continuous Sonic run through all 18 acts from a natural New Game to the ending and back to the title.

    Acts THZ1/THZ2 use the real sign chain, THZ3 forces player state `$20` (the shared tail of the boss path), every other act raises the
    act-clear flag (`$D293` bit 5, or bit 4 for the third act) at the point the state `$20` handler would; everything after the flag is unmodified ROM.
    """
    S = Session(rom)
    S.mark_pc(0x32F9, "results_screen")
    S.mark_pc(0x2D55, "act3_bonus_tally")
    S.mark_pc(0x2D08, "ring_time_tally")
    S.mark_pc(0x1365, "end_path")
    S.mark_pc(0x04B4, "title")
    S.mark_pc(0x1594, "zone_results_gate")
    S.mark_pc(0x18ED, "ending_selector")
    S.mark_pc(0x1A41, "ending_partial")
    S.mark_pc(0x18FE, "ending_full")
    S.boot_new_game(arrival=Session.place_at_sign(0))
    rows = []
    for zone in range(6):
        for act in range(3):
            assert S.m[0xD297] == zone and S.m[0xD298] == act, (zone, act, S.snap())
            S.run(60)
            before = norm(S.snap())
            n_results = len(S.event_frames("results_screen"))
            if zone == 0 and act < 2:
                if act == 0:
                    S.walk_right_until(lambda s: s.m[0xD293] & 0x30, limit=3000)
                else:
                    # arrival fixture was not armed for act 2 (armed below); same sign chain
                    S.walk_right_until(lambda s: s.m[0xD293] & 0x30, limit=3000)
                how = "real sign chain"
            elif zone == 0:
                S.w("player_req", 0x20)
                S.s._write(0xD15E, 0x80)
                S.s._write(0xD15F, 0x01)
                S.s.w16(0xD2DA, S.u16(0xD174))
                S.s.w16(0xD2DC, S.u16(0xD176))
                S.run_until(lambda s: s.m[0xD293] & 0x30, limit=1500)
                how = "forced player state $20 (shared tail of the boss path)"
            else:
                S.s._write(0xD293, S.m[0xD293] | (0x10 if act == 2 else 0x20))
                how = "act-clear flag raised"
            at_flag = norm(S.snap())
            if zone == 5 and act == 2:
                S.run_until(lambda s, f=at_flag["frame"]: s.first_event("title", after=f) is not None, limit=40000)
                after = norm(S.snap())
            else:
                nz, na = (zone, act + 1) if act < 2 else (zone + 1, 0)
                if act == 0 and zone == 0:
                    S.arm_arrival(Session.place_at_sign(1))
                S.run_until(lambda s, nz=nz, na=na: s.m[0xD297] == nz and s.m[0xD298] == na and s.playing(), limit=5000)
                after = norm(S.snap())
            rows.append(dict(zone=zone, act=act, how=how, before=before, at_flag=at_flag, after=after,
                             results_shown=len(S.event_frames("results_screen")) - n_results))
    ev = events_dict(S)
    return dict(fixtures=["ARRIVAL sign placement (THZ1, THZ2)", "RAM forced player state $20 (THZ3)", "RAM act-clear flag (other 15 acts)"],
                acts=rows, events={k: dict(count=v["count"]) for k, v in ev.items()}, final=norm(S.snap()))


# --------------------------------------------------------------------------------------------------------------------------------------------
DEATH_MARKS = [
    (0x15F2, "life_lost", None), (0x15FE, "life_decremented", None), (0x1653, "time_over_gate", None), (0x3495, "time_over_screen", None),
    (0x1661, "lives_check", None), (0x166B, "no_lives_left", None), (0x1673, "level_reload", None), (0x138A, "game_over_path", None),
    (0x13ED, "continue_check", None), (0x13F5, "continue_screen", None), (0x1491, "continue_accepted", None), (0x13C9, "continue_restore", None),
    (0x13A3, "game_over_screen", None), (0x13C6, "to_title", None), (0x04B4, "title", None), (0x2A00, "new_game_reset", None),
    (0x1CAF, "fade_slots_reset", None),
]


def sc_death(rom, kind="pit", lives=3, continues=0, character=0, answer="none", then_new_game=False, start_index=None, tag=None):
    """Kill the player on a fresh THZ1 start (or START_INDEX act) and follow the ROM: lives, restart, continue, Game Over, title.

    kind: pit (player Y pushed below the screen bottom -> `$3C06` rule) | time_over (timer forced to 9:59.59 -> `$27EE` sets `$D44B`).
    answer: none | continue (button on the continue screen) | wait (no button, continue screen times out).
    """
    S = Session(rom)
    attach_marks(S, DEATH_MARKS)
    if start_index is not None:
        S.set_start_index(*start_index)
    S.boot_new_game(character=character)
    S.run(150)
    start_pos = [S.u16(0xD511), S.u16(0xD514)]
    pre = dict(lives=lives, continues=continues, emeralds=0x07, rings=0x23, score0=0x30, score1=0x12, score2=0x00, powerup=0x04)
    for k, v in pre.items():
        S.w(k, v)
    S.s.w16(0xD44C, 0x0100)
    before = norm(S.snap())
    f0 = S.s.frame
    if kind == "pit":
        S.s.w16(0xD514, S.u16(0xD514) + 400)
    else:
        S.w("timer_min", 0x09)
        S.w("timer_sec", 0x59)
        S.w("timer_ticks", 59)
    st = dict(accept_at=None)

    def pad(s):
        ce = S.first_event("continue_screen", after=f0)
        if answer == "continue" and ce and s.s.frame - ce["frame"] > 200:
            return BTN_1 if s.s.frame % 8 < 3 else 0
        return 0
    died = f0
    S.run_until(lambda s: s.first_event("life_lost", after=f0) is not None, pad=0, limit=9000 if kind == "time_over" else 1500)
    died = S.first_event("life_lost", after=f0)["frame"]
    if lives > 1:
        S.run_until(lambda s: s.first_event("level_reload", after=died) is not None and s.playing(), pad=0, limit=3000)
    elif answer == "wait":
        S.run_until(lambda s: s.first_event("title", after=died) is not None, pad=pad, limit=9000)
    elif answer == "continue":
        S.run_until(lambda s: s.first_event("level_reload", after=died) is not None and s.playing(), pad=pad, limit=6000)
    else:
        S.run_until(lambda s: s.first_event("title", after=died) is not None, pad=pad, limit=4000)
    end = norm(S.snap())
    ev = events_dict(S, after=f0)
    out = dict(
        fixtures=["RAM run state while in play: " + json.dumps({k: hx(v) for k, v in pre.items()}), "RAM " + ("player Y +400 (below the screen bottom)" if kind == "pit" else "timer 09:59.59"),
                  "PAD button 1/2 on the continue screen" if answer == "continue" else "PAD none"],
        kind=kind, character=character, start_position=start_pos, before=before, died_frame_after_fixture=died - f0,
        checkpoints={k: v["first"] for k, v in ev.items()}, counts={k: v["count"] for k, v in ev.items()}, end=end,
    )
    if then_new_game:
        S.start_from_title(character=character)
        out["new_game_in_play"] = norm(S.snap())
        out["new_game_events"] = {k: v["first"] for k, v in events_dict(S, names={"new_game_reset"}, after=end["frame"]).items()}
    return out


# --------------------------------------------------------------------------------------------------------------------------------------------
def sc_hundred_ring(rom, how="ring", rings=0x99, character=0, emeralds=0x00, monitor=0, start_index=None, preset=None):
    """The 100th ring on a fresh act: ring wrap, +1 life, and the special-stage gate `$178F` (Sonic only, zone < 6, not all five emeralds)."""
    S = Session(rom)
    for a, n in ((0x3104, "life_award"), (0x178F, "ss_gate"), (0x17B0, "ss_entry_sequence"), (0x4AC0, "monitor_ten_rings"), (0x4ADA, "monitor_one_up")):
        S.mark_pc(a, n)
    if start_index is not None:
        S.set_start_index(*start_index)
    S.boot_new_game(character=character)
    S.run(90)
    S.w("emeralds", emeralds)
    for k, v in (preset or {}).items():
        S.w(k, v)
    before = norm(S.snap())
    f0 = S.s.frame
    if how == "ring":
        S.inject_call(0x3138, {"rings": rings})
    elif how == "ten_ring_monitor":
        S.inject_call(0x4AA3, {"rings": rings, 0xD3A3: 0x01})
    elif how == "one_up_monitor":
        S.inject_call(0x4AA3, {0xD3A3: 0x02})
    S.run(30)
    after_award = norm(S.snap())
    # let a stage entry (if any) run until the stage is playable
    entered = False
    for _ in range(1200):
        S.s.pad = 0
        S.s.run_frame()
        if S.m[0xD294] == 0x80 and S.m[0xD500] == 1:
            entered = True
            break
    stage = norm(S.snap())
    ev = events_dict(S, after=f0)
    return dict(fixtures=["RAM emeralds=%s" % hx(emeralds)] + (["CALL $3138 (ring pickup) with D29A=%s" % hx(rings)] if how == "ring" else
                ["CALL $4AA3 (monitor reward dispatcher) with D3A3 bit set and D29A=%s" % hx(rings)] if how == "ten_ring_monitor" else
                ["CALL $4AA3 (monitor reward dispatcher) with D3A3 bit 1"]),
                how=how, character=character, before=before, after_award=after_award, stage_entered=entered, stage=stage,
                checkpoints={k: v["first"] for k, v in ev.items()}, counts={k: v["count"] for k, v in ev.items()})


# --------------------------------------------------------------------------------------------------------------------------------------------
SS_MARKS = [
    (0x183F, "ss_success", None), (0x1815, "ss_failure", None), (0x1869, "ss_return", None), (0x14AE, "act_clear_sequence", None),
    (0x32F9, "results_screen", None), (0x2D55, "act3_bonus_tally", None), (0x2D08, "ring_time_tally", None), (0x33E8, "tally_returned", None),
    (0x1507, "fade_request", None), (0x1521, "palette_fill_3f", None), (0x152F, "progress_act", None), (0x1534, "act_incremented", None),
    (0x1673, "level_reload", None), (0x3104, "life_award", None),
]


def snap_image(S, image):
    """Normalised state of a saved RAM image ($C000..$DFFF) without disturbing the live machine."""
    live = bytes(S.m[0xC000:0xE000])
    S.m[0xC000:0xE000] = image
    try:
        return norm(S.snap())
    finally:
        S.m[0xC000:0xE000] = live


def sc_special_stage(rom, kind="success", stage=1, origin=(0, 0)):
    """100th ring in an ordinary act -> Special Stage `stage` -> exit (success by the accepted input-only route / timeout / pit death) -> return."""
    import ss_natural
    from ss_rig import SSRig, STAGE_BIT
    from ss_search import restore
    origin = tuple(origin)
    g = SSRig(rom, stage, origin=origin)
    S = Session(rom, sms=g.s)
    attach_marks(S, SS_MARKS)
    entry = dict(before_ring=snap_image(S, g.pre_ram), stage_playable=snap_image(S, g.post_ram), entry_log=g.entry_log)
    S.cram_trace()
    s, m = g.s, g.m
    restore(g, g.e.base)
    f0 = s.frame
    route = None
    if kind == "success":
        rle = json.loads((ROOT / "data/rom-cache/special-stages/natural-inputs.json").read_text(encoding="utf-8"))[f"ss{stage}"]
        n = ss_natural.replay(g, rle)
        route = dict(input_runs=len(rle), input_frames=sum(a for _, a in rle), frames_to_emerald=n, source="data/rom-cache/special-stages/natural-inputs.json")
    elif kind == "timeout":
        for _ in range(5000):
            s.pad = 0
            s.run_frame()
            if m[0xD294] & 0x60:
                break
    elif kind == "death":
        bottom = s.u16(0xD27E)
        g.begin(s.u16(0xD511), bottom + 232, cur=0x0E, f3=1, floor=False, rings=0)
        for _ in range(600):
            s.pad = 0
            s.run_frame()
            if m[0xD294] & 0x60:
                break
    exit_state = norm(S.snap())
    nz, na = origin[0], origin[1] + 1
    S.run_until(lambda x: x.m[0xD297] == origin[0] and x.m[0xD298] == na and x.playing(), pad=0, limit=6000)
    end = norm(S.snap())
    ev = events_dict(S, after=f0)
    f = {k: v["first"]["frame"] for k, v in ev.items()}
    base = f.get("act_clear_sequence", f0)
    return dict(
        fixtures=["START_INDEX zone %d act %d" % origin, "CALL $3138 with D29A=99 at an update boundary (natural 100th ring)",
                  "D2CC mask selecting stage %d" % stage] + (["PAD input-only route replay"] if kind == "success" else ["RAM player Y below the stage bottom"] if kind == "death" else ["PAD none"]),
        kind=kind, stage=stage, origin=list(origin), entry=entry, route=route, exit_state=exit_state, end_in_play=end,
        checkpoints={k: v["first"] for k, v in ev.items()}, counts={k: v["count"] for k, v in ev.items()},
        relative_frames={k: f[k] - base for k in f}, fade_after_act_clear=fade_series(S, base, S.s.frame), emerald_bit=STAGE_BIT[stage],
        post_tally_fade=post_tally_fade(fade_series(S, base, S.s.frame), f["tally_returned"] - base, f["act_incremented"] - base),
    )


# --------------------------------------------------------------------------------------------------------------------------------------------
END_MARKS = [
    (0x1543, "zone_clear_sequence", None), (0x1594, "zone_results_gate", None), (0x32F9, "results_screen", None), (0x15CE, "zone_increment", None),
    (0x15D6, "zone_store", None), (0x1365, "end_path", None), (0x18ED, "ending_selector", None), (0x18FE, "ending_full_sonic", None),
    (0x1A41, "ending_partial_sonic", None), (0x1ACD, "ending_tails", None), (0x04B4, "title", None),
]


def sc_ending(rom, character=0, mask=0x3F, zone=5, act=2):
    """Final act of the last zone: act-clear flag -> `$1543` -> end path `$1365` -> `$18ED` ending selector -> title -> next New Game."""
    S = Session(rom)
    attach_marks(S, END_MARKS)
    S.set_start_index(zone, act)
    S.boot_new_game(character=character)
    S.run(60)
    S.w("emeralds", mask)
    before = norm(S.snap())
    f0 = S.s.frame
    S.s._write(0xD293, S.m[0xD293] | 0x10)
    S.run_until(lambda s: s.first_event("title", after=f0) is not None, pad=0, limit=60000)
    title = norm(S.snap())
    ev = events_dict(S, after=f0)
    S.start_index = None
    S.start_from_title(character=character)
    return dict(fixtures=["START_INDEX zone %d act %d" % (zone, act), "RAM emeralds=%s" % hx(mask), "RAM act-clear flag $D293 bit 4 (what the state-$20 handler sets in act index 2)"],
                character_cursor=character, before=before, checkpoints={k: v["first"] for k, v in ev.items()}, counts={k: v["count"] for k, v in ev.items()},
                frames_flag_to_title=title["frame"] - f0, title=title, next_new_game=norm(S.snap()))


def sc_restart_matrix(rom):
    """All 18 acts: start position of a fresh load versus the position after a pit death (checkpoint existence)."""
    rows = []
    for zone in range(6):
        for act in range(3):
            S = Session(rom)
            S.mark_pc(0x1673, "level_reload")
            S.set_start_index(zone, act)
            S.boot_new_game()
            S.run(100)
            fresh = [S.u16(0xD511), S.u16(0xD514)]
            cam_fresh = [S.u16(0xD174), S.u16(0xD176)]
            S.run(300)                       # walk a little, so a stored position would differ
            S.run(120, pad=BTN_RIGHT)
            moved = [S.u16(0xD511), S.u16(0xD514)]
            f0 = S.s.frame
            S.s.w16(0xD514, S.u16(0xD514) + 600)
            try:
                S.run_until(lambda s: s.first_event("level_reload", after=f0) is not None and s.playing(), limit=3000)
                S.run(100)
                restarted = [S.u16(0xD511), S.u16(0xD514)]
                rows.append(dict(zone=zone, act=act, fresh_start=fresh, moved_to=moved, after_death=restarted, same=restarted == fresh,
                                 lives_after=hx(S.m[0xD299])))
            except RuntimeError:
                rows.append(dict(zone=zone, act=act, fresh_start=fresh, moved_to=moved, error="no restart observed"))
    return dict(fixtures=["START_INDEX per act", "PAD RIGHT 120 frames", "RAM player Y +600 (pit death)"], acts=rows)


# --------------------------------------------------------------------------------------------------------------------------------------------
def sc_score_continue_rule(rom):
    """CONTROLLED ROUTINE RESULT: the original score-add routine `$262F` run (tools/oracle.py) across every thousands-digit crossing 0..99,999 raw.

    The increment table entry `$27E5` (+10 raw) is added to a score of x,995 so the thousands digit changes; the continue byte `$D2C3` is observed.
    """
    from oracle import Oracle
    o = Oracle(rom)
    m = o.mem
    out = {}
    for char, name in ((1, "sonic"), (2, "tails")):
        awards = []
        for k in range(100):                      # score before = k*1000 + 995 (raw, BCD)
            raw = k * 1000 + 995
            digits = "%06d" % raw
            b = [int(digits[4:6], 16), int(digits[2:4], 16), int(digits[0:2], 16)]   # D29D, D29E, D29F
            m[0xD292] = 0
            m[0xD2C8] = char
            m[0xD29D], m[0xD29E], m[0xD29F] = b
            m[0xD2A0], m[0xD2A1], m[0xD2A2] = b[0], b[1], b[2]
            m[0xD2C3] = 0
            o.cpu.hl = 0x27E5
            o.call(0x262F)
            new = "%02X%02X%02X" % (m[0xD29F], m[0xD29E], m[0xD29D])
            awards.append([digits, new, m[0xD2C3]])
        gained = [a for a in awards if a[2] != 0]
        thousands = [int(a[1][:3]) for a in gained]
        out[name] = dict(crossings=100, awarded=len(gained), awarded_thousands=thousands[:12], period_thousands=sorted({b - a for a, b in zip(thousands, thousands[1:])}), awarded_from_to=[[a[0], a[1]] for a in gained][:20],
                         new_thousands_digit_set=sorted({a[1][2] for a in gained}),
                         non_awarded_thousands_digits=sorted({a[1][2] for a in awards if a[2] == 0}))
    return dict(fixtures=["CONTROLLED routine call: HL=$27E5 (+10 raw), D2C3=0, score=x,995 raw"], rules=out)
