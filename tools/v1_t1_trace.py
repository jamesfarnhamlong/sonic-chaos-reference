#!/usr/bin/env python3
"""V1 (twist/Mobius presentation) and T1 (goal/boss transition) fidelity audit (Research only, deterministic).

    python tools/v1_t1_trace.py ROM --write            # regenerate data/v1/*.json and data/t1/*.json  (about 3-5 minutes)
    python tools/v1_t1_trace.py ROM --check            # regenerate in memory, compare with the committed JSON
    python tools/v1_t1_trace.py ROM --only twist|goal|post|boss|spark
    python tools/v1_t1_trace.py --validate             # no ROM: internal consistency of the committed JSON

Evidence classes (same vocabulary as earlier studies): DECODED DATA, BYTE-VERIFIED ASSEMBLY, EMULATED ORIGINAL FRAME (unmodified ROM in
tools/sms_frame_harness.py via tools/player_fall_control.Lab, approximate VDP), SYNTHETIC CONTROL (position/camera injected at arrival, or the boss's
requested state forced to its defeat state; always stated per scenario), POC SOURCE (read only).

Nothing here stores ROM bytes, tiles or pixels: only counts, addresses, hashes of small numeric tuples and decoded numeric tables.
Ignored screenshots/contact sheets go to build/v1 (never committed).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
V1_JSON = ROOT / "data" / "v1" / "twist-audit.json"
T1_JSON = ROOT / "data" / "t1" / "transition-audit.json"
ZONES = {"thz": 0, "gpz": 1, "sez": 2, "mghz": 3, "apz": 4, "eez": 5}
ZONE_NAME = {"thz": "THZ", "gpz": "GPZ", "sez": "SEZ", "mghz": "MGHZ", "apz": "AQZ", "eez": "EEZ"}
BOSS_TYPE = {"thz": 0x50, "gpz": 0x51, "sez": 0x54, "mghz": 0x56, "apz": 0x59, "eez": 0x5E}
DEFEAT_STATE = {"thz": 4, "sez": 4, "mghz": 4}          # only these were verified to reach the clear flag by forcing the request
TWIST_BASE = 0x30425                                     # state $22 script, bank $0C $8425


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def hx(v, n=2):
    return f"0x{v:0{n}X}"


def dumps(d) -> str:
    return json.dumps(d, indent=1, sort_keys=False) + "\n"


def load_rom(path) -> bytes:
    rom = Path(path).read_bytes()
    if len(rom) != 524288 or sha(rom) != ROM_SHA256:
        raise SystemExit("not the canonical Sonic Chaos (Europe) v1.2 ROM")
    return rom


class Rig:
    """Thin wrapper over player_fall_control.Lab with the two extra zones the Lab table lacks."""

    def __init__(self, rom):
        import player_fall_control as F
        F.ZONES.update({"apz": 4, "eez": 5})
        self.F, self.rom = F, rom
        import isometric_platform as I
        self.I = I

    def lab(self, zone, act):
        return self.F.Lab(self.rom, zone, act)

    def anchors(self, key, type_id):
        a = self.I.act_data(self.rom, key)
        return [(r["world_x"], r["world_y"]) for r in a["objects"] if int(r["type_id"], 16) == type_id]


# --------------------------------------------------------------------------------------------------------------- V1
def twist_static(rom, rig):
    import level_package as L
    # state $22 script: records until FF 00
    pos, recs = TWIST_BASE, []
    while rom[pos] != 0xFF:
        recs.append({"duration": rom[pos], "frame": hx(rom[pos + 1]), "callback": hx(rom[pos + 2] | rom[pos + 3] << 8, 4)})
        pos += 4
    tail = {"command": f"FF {rom[pos + 1]:02X}", "meaning": "restart the script (state-$22 program loops forever)"}
    # direct frame/facing writers inside the twist code region $94C1..$9829 (bank $0C, file $314C1..$31829)
    region = rom[0x314C1:0x31829]
    writers = {"IX+6_frame_writes": region.count(bytes([0xDD, 0x36, 0x06])) + region.count(bytes([0xDD, 0x77, 0x06])),
               "IX+4_flag_writes": sum(region.count(bytes([0xDD, 0xCB, 0x04, op])) for op in (0xC6, 0x86, 0xE6, 0xA6)) + region.count(bytes([0xDD, 0x36, 0x04])) + region.count(bytes([0xDD, 0x77, 0x04])),
               "IX+2_state_requests": [hx(rom[0x314C1 + i + 3]) for i in range(len(region) - 4)
                                       if region[i:i + 3] == bytes([0xDD, 0x36, 0x02])][:4]}
    entry = rom[0x6E56:0x6F61]
    entry_facts = {"entry_code": "0x6E56..0x6F60 (fixed bank)", "sound_request_A5_before_speed_test": entry.count(bytes([0x3E, 0xA5])) == 2,
                   "right_entry_tiles": ["0x59", "0x5C"], "left_entry_tiles": ["0x73", "0x72", "0x6B"],
                   "right_speed_gate_non_mghz": "speed >= 0x0300 (SBC HL,$0300; carry returns)",
                   "right_speed_gate_mghz": "zone index 3: speed below 0x0500 is RAISED to 0x0500, then entry (no minimum)",
                   "left_speed_gate": "speed < 0xFD00 (strict, all zones)",
                   "eligible_prior_states": ["0x05", "0x06", "0x09", "0x10", "0x1A"],
                   "variant_by_zone": {"non_MGHZ": {"right": 0, "left": 1}, "MGHZ(zone 3)": {"right": 2, "left": 3}},
                   "magnitude": "high byte of (abs(x speed 8.8) << 5): equals speed_px * 32 truncated",
                   "angle": {"right": "0x40", "left": "0xC0"},
                   "facing_flag_ix4_bit4_written_by_entry": False}
    # census: which acts contain surface-$17 blocks, per-block priority cells
    cen, prio = OrderedDict(), OrderedDict()
    for key in rig.I.ACTS:
        a = rig.I.act_data(rom, key)
        rows = []
        for i, b in enumerate(a["cells"][:4095]):
            h = rig.I.rom_tables.header(rom, b)
            if (h["flags"] & 0x3F) == 0x17:
                rows.append((i % a["width"], i // a["width"], b))
        if rows:
            cen[key] = {"cells": len(rows), "distinct_blocks": len({b for _, _, b in rows}),
                        "cell_x": [min(r[0] for r in rows), max(r[0] for r in rows)], "cell_y": [min(r[1] for r in rows), max(r[1] for r in rows)],
                        "entry_block_cells": [[x, y, hx(b)] for x, y, b in rows if b in (0x59, 0x5C, 0x73, 0x72, 0x6B)]}
            hdr = L.act_header(rom, ZONES[key[:-1].replace("aqz", "apz")] if key[:-1] in ZONES else 0, int(key[-1]) - 1)
            cells = {}
            for b in sorted({b for _, _, b in rows}):
                attr = L.block_mapping(rom, hdr["block_mapping_rom"], b)["attributes"]
                n = sum(1 for w in attr if w & 0x1000)
                if n:
                    cells[hx(b)] = {"priority_cells_of_16": n, "mask": "".join("P" if w & 0x1000 else "." for w in attr)}
            prio[key] = {"mapping_rom": hx(hdr["block_mapping_rom"], 5), "blocks_with_priority": cells}
    # the two block-priority sets are act-independent inside a zone (THZ1/2/3 identical)
    same = len({json.dumps(prio[k]["blocks_with_priority"], sort_keys=True) for k in prio if k.startswith("thz")}) == 1
    return {"script": {"cpu": "0x8425", "rom": hx(TWIST_BASE, 5), "records": recs, "tail": tail, "cycle_updates": sum(r["duration"] for r in recs)},
            "frame_ids": [r["frame"] for r in recs], "direct_writers_in_twist_code": writers, "entry": entry_facts,
            "census": cen, "block_priority": prio, "thz_priority_sets_identical_across_acts": same}


def _row(lab):
    m, s = lab.m, lab.s
    r = lab.row()
    r.update(frame=m[0xD506], cnt=m[0xD507], f4=m[0xD504], ang=m[0xD50A], mag=m[0xD50B], var=m[0xD538], tile=m[0xD353])
    return r


def twist_run(rig, zone, act, x, y, vx, right, cur=6, f4=None, frames=900, hold=None):
    lab = rig.lab(zone, act)
    lab.place(x, y, vx, 0, cur=cur, f3=0, floor=True, prev=0, p24=0)
    if f4 is not None:
        lab.m[0xD504] = f4
    rows, last = [], lab.upd
    for _ in range(frames):
        lab.s.pad = 8 if right else 4
        lab.s.run_frame()
        if lab.upd != last:
            last = lab.upd
            rows.append(_row(lab))
    return rows


def twist_summary(rows):
    tw = [r for r in rows if r["cur"] == 0x22]
    if not tw:
        return {"entered": False, "states_seen": sorted({hx(r["cur"]) for r in rows})}
    # first contiguous run
    run = []
    for r in rows:
        if r["cur"] == 0x22:
            run.append(r)
        elif run:
            break
    e = run[0]["u"]
    frames_ok = all(r["frame"] == 0x25 + ((r["u"] - e) % 15) // 3 for r in run)
    after = next((r for r in rows if r["u"] == run[-1]["u"] + 1), None)
    return {"entered": True, "entry_update": e, "updates_in_state": len(run),
            "entry": {"x": run[0]["x"], "y": run[0]["y"], "vx": run[0]["vx"], "angle": run[0]["ang"], "magnitude": run[0]["mag"], "variant": run[0]["var"], "facing_bit4": run[0]["f4"] & 16},
            "prior_state": hx(rows[rows.index(run[0]) - 1]["cur"]) if rows.index(run[0]) else None,
            "frame_rule_holds_every_update": frames_ok,
            "frame_sequence_first_17": [hx(r["frame"]) for r in run[:17]],
            "facing_bit4_values_inside": sorted({r["f4"] & 16 for r in run}),
            "vx_range": [min(r["vx"] for r in run), max(r["vx"] for r in run)],
            "angles_seen": sorted({r["ang"] for r in run}), "variants_seen": sorted({r["var"] for r in run}),
            "exit": {"x": run[-1]["x"], "y": run[-1]["y"], "next_state": hx(after["cur"]) if after else None, "facing_bit4_after": (after["f4"] & 16) if after else None}}


def sonic_pixels(s):
    tall = bool(s.reg[1] & 2)
    shift = 8 if (s.reg[0] & 8) else 0
    pat = 256 if (s.reg[6] & 4) else 0
    pts = set()
    for _i, sy, sx, n in s.sat():
        if n >= 0x10:
            continue
        for r in range(16 if tall else 8):
            ly = sy + 1 + r
            if not 0 <= ly < 192:
                continue
            pix = s.tile_row(pat + (n & 0xFE) + (r >> 3), r & 7)
            for c in range(8):
                lx = sx - shift + c
                if 0 <= lx < 256 and pix[c]:
                    pts.add((lx, ly))
    return pts


def twist_priority(rig, zone, act, x, y, vx, cur=6, frames=400):
    """Per twist update: Sonic sprite pixels and how many are hidden by a foreground-priority background tile (SMS name-table bit 12)."""
    lab = rig.lab(zone, act)
    lab.place(x, y, vx, 0, cur=cur, f3=0, floor=True, prev=0, p24=0)
    last, out = lab.upd, []
    for _ in range(frames):
        lab.s.pad = 8
        lab.s.run_frame()
        if lab.upd != last:
            last = lab.upd
            if lab.m[0xD501] == 0x22:
                pts = sonic_pixels(lab.s)
                layer = lab.s.render()[1]
                out.append((lab.upd, len(pts), sum(1 for (px, py) in pts if layer[py][px] == "B")))
    hid = [h for _, t, h in out]
    tot = [t for _, t, h in out]
    return {"twist_updates": len(out), "updates_with_any_hidden_pixel": sum(1 for h in hid if h), "updates_fully_hidden": sum(1 for t, h in zip(tot, hid) if t and h >= 0.95 * t),
            "max_hidden_pixels": max(hid) if hid else 0, "sprite_pixels_min_max": [min(tot), max(tot)] if tot else None,
            "hidden_profile_every_10_updates": [[u, t, h] for (u, t, h) in out[::10]]}


def twist_art_probe(rig, zone, act, x, y, vx, cur, frames=420):
    """Do level tiles or BG palette animate during the strip?  Reported separately from the sprite (EMULATED)."""
    lab = rig.lab(zone, act)
    lab.place(x, y, vx, 0, cur=cur, f3=0, floor=True, prev=0, p24=0)
    s, last = lab.s, lab.upd
    base_v = base_c = None
    changed, cram_updates = set(), 0
    for _ in range(frames):
        s.pad = 8
        s.run_frame()
        if lab.upd != last:
            last = lab.upd
            if lab.m[0xD501] == 0x22:
                if base_v is None:
                    base_v, base_c = bytes(s.vram), list(s.cram[:16])
                else:
                    for t in range(0x20, 0x100):          # BG tile range below the sprite pattern base (256)
                        if s.vram[t * 32:(t + 1) * 32] != base_v[t * 32:(t + 1) * 32]:
                            changed.add(t)
                    if list(s.cram[:16]) != base_c:
                        cram_updates += 1
    return {"bg_tiles_changed_during_strip": sorted(changed), "bg_palette_changed_updates": cram_updates}


def twist_ambient_palette(rig):
    lab = rig.lab("mghz", 1)
    lab.place(2270, 366, 0, 0, cur=1, f3=0, floor=True, prev=0, p24=0)
    s, last, seq = lab.s, None, []
    for f in range(400):
        s.pad = 0
        s.run_frame()
        c = tuple(s.cram[:16])
        if c != last:
            seq.append((f, [i for i in range(16) if last is None or c[i] != last[i]]))
            last = c
    return {"scenario": "MGHZ2 standing still 400 harness frames", "bg_palette_change_events": len(seq) - 1, "changed_colour_indices": sorted({i for _, l in seq[1:] for i in l}),
            "period_frames": seq[3][0] - seq[2][0] if len(seq) > 3 else None, "conclusion": "level-wide ambient cycle, independent of the strip"}


def build_twist(rom, rig):
    out = OrderedDict(format=1, rom_sha256=ROM_SHA256, evidence="DECODED DATA + BYTE-VERIFIED ASSEMBLY + EMULATED ORIGINAL FRAME (+ SYNTHETIC CONTROL placement)")
    out["static"] = twist_static(rom, rig)
    sc = OrderedDict()
    sc["THZ1_right_run"] = {"placement": "(3000,558) vx +0x0400 state 6, RIGHT held", **twist_summary(twist_run(rig, "thz", 0, 3000, 558, 0x400, True))}
    sc["THZ1_left_run_facing_left"] = {"placement": "(3430,558) vx -0x0400 state 6, facing bit set, LEFT held", **twist_summary(twist_run(rig, "thz", 0, 3430, 558, -0x400, False, f4=0x10))}
    sc["THZ1_left_run_facing_flag_clear"] = {"placement": "same, facing bit clear (proves the strip never writes it)", **twist_summary(twist_run(rig, "thz", 0, 3430, 558, -0x400, False, f4=0))}
    sc["THZ2_right_run"] = {"placement": "(2000,238) vx +0x0400", **twist_summary(twist_run(rig, "thz", 1, 2000, 238, 0x400, True, frames=700))}
    sc["THZ2_left_run"] = {"placement": "(2470,238) vx -0x0400", **twist_summary(twist_run(rig, "thz", 1, 2470, 238, -0x400, False, f4=0x10, frames=700))}
    sc["THZ3_right_run"] = {"placement": "(820,110) vx +0x0400", **twist_summary(twist_run(rig, "thz", 2, 820, 110, 0x400, True, frames=700))}
    sc["THZ1_slow_walk_0x0200"] = {"placement": "(3000,558) vx +0x0200 state 5 (below the 0x0300 gate; the run state accelerates past it before the strip)", **twist_summary(twist_run(rig, "thz", 0, 3000, 558, 0x200, True, cur=5, frames=500))}
    m1 = twist_run(rig, "mghz", 1, 2270, 366, 0x400, True, cur=5, frames=900)
    m2 = twist_run(rig, "mghz", 1, 2270, 366, 0x200, True, cur=5, frames=900)
    sc["MGHZ2_right_run"] = {"placement": "(2270,366) vx +0x0400 state 5", **twist_summary(m1)}
    sc["MGHZ2_right_slow_0x0200"] = {"placement": "(2270,366) vx +0x0200 state 5: entry speed raised to 0x0500 by the zone-3 rule", **twist_summary(m2)}
    tw = [r for r in m1 if r["cur"] == 0x22]
    sc["MGHZ2_right_run"]["vy_range_inside"] = [min(r["vy"] for r in tw), max(r["vy"] for r in tw)]
    sc["MGHZ2_right_run"]["note"] = "vx goes negative inside the chute while the facing bit stays clear: a vx-sign facing rule (POC legacy path) would flip Sonic here, the ROM does not"
    sc["MGHZ2_left_from_bottom_LEFT_held_3000f"] = {"placement": "(2560,686) vx -0x0400 state 6, LEFT held: the bottom entry swings up the chute and re-enters", **twist_summary(twist_run(rig, "mghz", 1, 2560, 686, -0x400, False, cur=6, f4=0x10, frames=1500))}
    out["emulated_scenarios"] = sc
    out["foreground_priority_hiding"] = {"THZ1_right_run": twist_priority(rig, "thz", 0, 3000, 558, 0x400),
                                         "MGHZ2_right_run": twist_priority(rig, "mghz", 1, 2270, 366, 0x400, cur=5, frames=500)}
    out["level_art_animation_probe"] = {"THZ1": twist_art_probe(rig, "thz", 0, 3000, 558, 0x400, 6), "MGHZ2": twist_art_probe(rig, "mghz", 1, 2270, 366, 0x400, 5),
                                        "MGHZ_ambient_cycle": twist_ambient_palette(rig),
                                        "note": "BG tile indices >= 0x20 and < 0x100 only; sprite pattern tiles (index 256+) stream the player frame and are excluded"}
    return out


# --------------------------------------------------------------------------------------------------------------- T1
def goal_run(rig, zone, act, dx=-60, frames=2400):
    key = f"{zone}{act + 1}"
    sx, sy = rig.anchors(key, 0x18)[0]
    lab = rig.lab(zone, act)
    lab.place(sx + dx, sy, 0x400, 0, cur=6, f3=0, floor=True, prev=0, p24=0)
    s, m = lab.s, lab.m
    rows, last, contact, types = [], lab.upd, None, {}
    for _ in range(frames):
        s.pad = 8
        s.run_frame()
        if lab.upd != last:
            last = lab.upd
            r = lab.row()
            r.update(cx=s.u16(0xD174), cy=s.u16(0xD176), flow=m[0xD293], tm=m[0xD2BE], frame=m[0xD506])
            for i in range(19):
                b = 0xD540 + i * 0x40
                if m[b]:
                    types.setdefault(m[b], []).append(lab.upd)
            rows.append(r)
            if contact is None and m[0xD2BE] == 0 and len(rows) > 2:
                contact = lab.upd
            if m[0xD293] & 0x30 and contact is not None:
                break
    flag = rows[-1]["u"]
    st20 = next(r for r in rows if r["cur"] == 0x20)
    run20 = [r for r in rows if r["cur"] == 0x20]
    frames20 = []
    for r in run20:
        if not frames20 or frames20[-1][0] != r["frame"]:
            frames20.append([r["frame"], 1])
        else:
            frames20[-1][1] += 1
    return {"sign_anchor": [sx, sy], "contact_update": contact, "state20_update_after_contact": st20["u"] - contact, "flag_update_after_contact": flag - contact,
            "camera_at_flag": [rows[-1]["cx"], rows[-1]["cy"]], "player_at_flag": [rows[-1]["x"], rows[-1]["y"]],
            "camera_settled_vs_sign": [rows[-1]["cx"] - sx, rows[-1]["cy"] - sy], "flag_player_minus_camera": rows[-1]["x"] - rows[-1]["cx"],
            "pool_types_seen": {hx(k): [v[0] - contact, v[-1] - contact] for k, v in sorted(types.items()) if k in (0x18, 0x19)},
            "unexpected_pool_types": sorted(hx(k) for k in types if k not in (0x18, 0x19, 0xFE, 0xFF)),
            "run_off_frame_runs_first_12": [[hx(a), b] for a, b in frames20[:12]], "run_off_updates": len(run20),
            "player_screen_x_at_state20_start": st20["x"] - st20["cx"], "player_screen_x_last_update": rows[-1]["x"] - rows[-1]["cx"]}


def post_flag(rig, zone, act, boss=False, dx=-60):
    """CRAM / display-enable / zone timeline measured from the act-complete flag (harness frames)."""
    lab = rig.lab(zone, act)
    s, m = lab.s, lab.m
    if boss:
        bx, by = rig.anchors(f"{zone}{act + 1}", BOSS_TYPE[zone])[0]
        px = bx - 480
        lab.place(px, by - 120, 0x300, 0, cur=0x0E, f3=1, floor=False, prev=0, p24=0)
        s.w16(0xD174, px - 104)
        s.w16(0xD284, px - 104)
    else:
        sx, sy = rig.anchors(f"{zone}{act + 1}", 0x18)[0]
        lab.place(sx + dx, sy, 0x400, 0, cur=6, f3=0, floor=True, prev=0, p24=0)
    z0 = (m[0xD297], m[0xD298])
    flagf = fight0 = None
    forced = False
    log, lastc, lastr1 = [], None, None
    for f in range(24000):
        if boss:
            b = next((a for a in range(0xD500, 0xDA00, 0x40) if m[a] == BOSS_TYPE[zone]), None)
            st = m[b + 1] if b else None
            if b and st >= 6 and st != 0x0B and fight0 is None:
                fight0 = lab.upd
            if b and fight0 is not None and lab.upd - fight0 >= 3 and not forced:
                m[b + 2] = DEFEAT_STATE[zone]
                forced = True
            s.pad = 8 if (fight0 is None and (b is None or st < 2)) else 0
        else:
            s.pad = 8
        s.run_frame()
        if flagf is None and (m[0xD293] & 0x30):
            flagf = f
        if flagf is not None:
            c = bytes(s.cram[:32])
            if c != lastc:
                log.append(["cram", f - flagf, sum(c[:16]), sum(c[16:32])])
                lastc = c
            if s.reg[1] != lastr1:
                log.append(["r1", f - flagf, s.reg[1]])
                lastr1 = s.reg[1]
            if (m[0xD297], m[0xD298]) != z0:
                log.append(["next_zone_act", f - flagf, m[0xD297], m[0xD298]])
                break
            if f - flagf > 1700:
                break
    return {"flag_harness_frame": flagf, "events": log, "notes": "cram rows: [kind, frames_after_flag, sum of 16 BG colour bytes, sum of 16 sprite colour bytes]; 1008 = all 16 colours 0x3F (white), 0 = black. r1 rows: VDP register 1 (0xE2 display on, 0xA2/0xA2 blank variants)"}


def snap(lab, zone, rig):
    s, m = lab.s, lab.m
    b = next((a for a in range(0xD500, 0xDA00, 0x40) if m[a] == BOSS_TYPE[zone]), None)
    return {"u": lab.upd, "x": s.u16(0xD511), "y": s.u16(0xD514), "pst": m[0xD501], "cx": s.u16(0xD174), "cy": s.u16(0xD176),
            "limL": s.u16(0xD280), "limR": s.u16(0xD282), "limB": s.u16(0xD27E), "pan": m[0xD15F] & 1, "d15e7": (m[0xD15E] >> 7) & 1,
            "flow": m[0xD293], "art": m[0xD3B3], "snd": m[0xDE04], "r1": s.reg[1],
            "spal": hashlib.md5(bytes(s.cram[16:32])).hexdigest()[:6], "bpal": hashlib.md5(bytes(s.cram[:16])).hexdigest()[:6],
            "boss": None if b is None else [m[b + 1], m[b + 2], s.u16(b + 0x11), s.u16(b + 0x14), m[b + 0x26]], "act": m[0xD298], "zone": m[0xD297]}


def boss_run(rig, zone, frames=15000, force=True):
    bx, by = rig.anchors(f"{zone}3", BOSS_TYPE[zone])[0]
    lab = rig.lab(zone, 2)
    s, m = lab.s, lab.m
    px = bx - (700 if zone == "eez" else 480)
    lab.place(px, by - 120, 0x300, 0, cur=0x0E, f3=1, floor=False, prev=0, p24=0)
    s.w16(0xD174, px - 104)
    s.w16(0xD284, px - 104)
    rows, last, fight0, forced = [], lab.upd, None, False
    z0 = (m[0xD297], m[0xD298])
    for _ in range(frames):
        b = next((a for a in range(0xD500, 0xDA00, 0x40) if m[a] == BOSS_TYPE[zone]), None)
        st = m[b + 1] if b else None
        if b and st >= 6 and st != 0x0B and fight0 is None:
            fight0 = lab.upd
        if force and zone in DEFEAT_STATE and b and fight0 is not None and lab.upd - fight0 >= 3 and not forced:
            m[b + 2] = DEFEAT_STATE[zone]
            forced = True
        s.pad = 8 if (fight0 is None and (b is None or st < 2)) else 0
        s.run_frame()
        if lab.upd != last:
            last = lab.upd
            rows.append(snap(lab, zone, rig))
            if (m[0xD297], m[0xD298]) != z0:
                break
            if not force and lab.upd > 700:
                break
    return rows


def boss_milestones(rows, forced=False):
    def first(pred):
        return next((r for r in rows if pred(r)), None)
    b0 = first(lambda r: r["boss"])
    out = OrderedDict()
    out["boss_created_update"] = b0["u"] if b0 else None
    out["boss_anchor"] = b0["boss"][2:4] if b0 else None
    s0 = first(lambda r: r["boss"] and r["boss"][0] == 0 and r["snd"] == 0x8C) or first(lambda r: r["snd"] == 0x8C)
    out["music_request_8C_update"] = s0["u"] if s0 else None
    trig = first(lambda r: r["boss"] and r["boss"][0] == 1 and r["limR"] != 0 and r["limR"] <= r["cx"] + 8 and r["limR"] != rows[0]["limR"]) \
        or first(lambda r: r["boss"] and r["limR"] != rows[0]["limR"])
    out["right_limit_lowered_update"] = trig["u"] if trig else None
    out["right_limit_lowered_to_camera"] = [trig["cx"], trig["limR"]] if trig else None
    pan = first(lambda r: r["pan"] == 1)
    out["pan_start_update"] = pan["u"] if pan else None
    if pan:
        out["pan_start_camera"] = [pan["cx"], pan["cy"]]
        pend = [r for r in rows if r["u"] >= pan["u"] and r["pan"] == 1]
        out["pan_end_camera"] = [pend[-1]["cx"], pend[-1]["cy"]] if pend else None
        out["limits_during_pan_L_R_B"] = [pan["limL"], pan["limR"], pan["limB"]]
        xs = [r["cx"] for r in pend]
        out["pan_camera_step_max_abs_px_per_update"] = max((abs(b - a) for a, b in zip(xs, xs[1:])), default=0)
    sp = first(lambda r: r["spal"] != rows[0]["spal"] and pan and pan["u"] <= r["u"] <= pan["u"] + 60 and r["boss"])
    out["sprite_palette_swap_update"] = sp["u"] if sp else None
    art = first(lambda r: r["art"] not in (0,))
    out["art_selector_first_nonzero"] = [art["u"], hx(art["art"])] if art else None
    out["background_palette_changes_in_boss_window"] = len({r["bpal"] for r in rows if r["boss"]}) - 1
    out["display_blank_events"] = [r["u"] for r in rows if r["r1"] != 0xE2][:6]
    rel = first(lambda r: r["pan"] == 0 and pan and r["u"] > pan["u"]) if forced else None
    if rel:
        out["release_update"] = rel["u"]
        out["release_limits_L_R_B"] = [rel["limL"], rel["limR"], rel["limB"]]
        post = [r for r in rows if r["u"] >= rel["u"]][:14]
        xs = [r["cx"] for r in post]
        out["camera_x_first_14_updates_after_release"] = xs
        out["release_max_camera_step"] = max((abs(b - a) for a, b in zip(xs, xs[1:])), default=0)
    p20 = first(lambda r: r["pst"] == 0x20) if forced else None
    if p20:
        out["player_state_20_update"] = p20["u"]
        out["player_state_20_screen_x"] = p20["x"] - p20["cx"]
    fl = first(lambda r: r["flow"] & 0x30) if forced else None
    if fl:
        out["clear_flag_update"] = fl["u"]
        out["flag_player_minus_camera"] = fl["x"] - fl["cx"]
        out["camera_at_flag"] = [fl["cx"], fl["cy"]]
    nxt = first(lambda r: (r["zone"], r["act"]) != (rows[0]["zone"], rows[0]["act"])) if forced else None
    out["next_level_loaded"] = [nxt["zone"], nxt["act"]] if nxt else None
    out["defeat_driven"] = forced
    return out


def spark_trail(rig, zone="thz"):
    bx, by = rig.anchors(f"{zone}3", BOSS_TYPE[zone])[0]
    lab = rig.lab(zone, 2)
    s, m = lab.s, lab.m
    px = bx - 480
    lab.place(px, by - 120, 0x300, 0, cur=0x0E, f3=1, floor=False, prev=0, p24=0)
    s.w16(0xD174, px - 104)
    s.w16(0xD284, px - 104)
    fight0 = None
    forced = False
    z0 = (m[0xD297], m[0xD298])
    cur, spawns, ctrl = {}, [], []
    for _ in range(24000):
        b = next((a for a in range(0xD500, 0xDA00, 0x40) if m[a] == BOSS_TYPE[zone]), None)
        st = m[b + 1] if b else None
        if b and st >= 6 and st != 0x0B and fight0 is None:
            fight0 = lab.upd
        if b and fight0 is not None and lab.upd - fight0 >= 3 and not forced:
            m[b + 2] = DEFEAT_STATE[zone]
            forced = True
        s.pad = 8 if (fight0 is None and (b is None or st < 2)) else 0
        s.run_frame()
        if forced:
            for i in range(19):
                a = 0xD540 + i * 0x40
                if m[a] == 0x0A:
                    par = m[a + 0x3F]
                    rec = (lab.upd, a, s.u16(a + 0x11), s.u16(a + 0x14), s.u16(0xD511), s.u16(0xD514), m[a + 6], m[a + 1])
                    if par == 0:
                        ctrl.append(lab.upd)
                    else:
                        run = cur.get(a)
                        if run and rec[0] == run[-1][0] + 1:
                            run.append(rec)
                        elif not run or rec[0] != run[-1][0]:
                            run = [rec]
                            cur[a] = run
                            spawns.append(run)
            if (m[0xD297], m[0xD298]) != z0:
                break
    spawns.sort(key=lambda r: r[0][0])
    first = spawns[:6]
    intervals = [b[0][0] - a[0][0] for a, b in zip(spawns, spawns[1:])]
    return {"scenario": "THZ3 boss, defeat forced (SYNTHETIC CONTROL), RIGHT not held after the fight starts",
            "controller_param0_first_last_update": [ctrl[0], ctrl[-1]] if ctrl else None,
            "sparkle_count_until_zone_change": len(spawns), "spawn_interval_updates": sorted(set(intervals)),
            "first_spawn_after_controller_update": spawns[0][0][0] - ctrl[0] if spawns and ctrl else None,
            "lifetime_rows_each": sorted({len(r) for r in spawns}),
            "spawn_offset_from_player_anchor_first_6": [[r[0][2] - r[0][4], r[0][3] - r[0][5]] for r in first],
            "world_displacement_during_life": sorted({(r[-1][2] - r[0][2], r[-1][3] - r[0][3]) for r in spawns}),
            "frame_sequence_first_sparkle": [r[6] for r in spawns[0]] if spawns else None,
            "reading": "sparkles are created at the PLAYER's current world position (dx 0, dy alternating -12/-8), never move in world space and last 29 object rows (28 after creation); the visible 'motion' is the camera scrolling"}


def build_goal(rig):
    out = OrderedDict(format=1, rom_sha256=ROM_SHA256, evidence="EMULATED ORIGINAL FRAME; sign sequence entered by placing Sonic 60 px left of the sign anchor at run speed (SYNTHETIC CONTROL placement only; every later step is unmodified ROM)")
    acts = OrderedDict()
    for zone in ZONES:
        for act in (0, 1):
            acts[f"{ZONE_NAME[zone]}{act + 1}"] = goal_run(rig, zone, act)
    out["ordinary_act_clear"] = acts
    return out


def build_boss(rig):
    out = OrderedDict()
    for zone in ZONES:
        force = zone in DEFEAT_STATE
        try:
            rows = boss_run(rig, zone, force=force)
            out[ZONE_NAME[zone]] = {"method": "act 3 booted, Sonic injected 480 px left of the boss anchor falling at vx +0x0300 with the camera 104 px behind him, RIGHT held until the boss object exists; "
                                    + ("boss requested state forced to 4 three updates after its fight state began (SYNTHETIC CONTROL), then no input" if force else "intro only (no defeat forcing: the defeat entry state of this boss differs; see its audit)"),
                                    "milestones": boss_milestones(rows, force)}
        except Exception as exc:                              # pragma: no cover - reported, never hidden
            out[ZONE_NAME[zone]] = {"error": repr(exc)}
    return out


def build_t1(rom, rig, only=None):
    out = OrderedDict(format=1, rom_sha256=ROM_SHA256)
    if only in (None, "goal"):
        out["goal"] = build_goal(rig)
    if only in (None, "post"):
        out["post_flag_transition"] = {"THZ1 ordinary act clear": post_flag(rig, "thz", 0), "GPZ2 ordinary act clear": post_flag(rig, "gpz", 1),
                                       "THZ3 boss route (defeat forced)": post_flag(rig, "thz", 2, boss=True), "SEZ3 boss route (defeat forced)": post_flag(rig, "sez", 2, boss=True)}
    if only in (None, "boss"):
        out["boss"] = build_boss(rig)
    if only in (None, "spark"):
        out["defeat_sparkle_trail"] = spark_trail(rig)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", nargs="?")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--only", choices=("twist", "goal", "post", "boss", "spark"))
    ap.add_argument("--validate", action="store_true")
    a = ap.parse_args()
    if a.validate:
        v1, t1 = json.loads(V1_JSON.read_text()), json.loads(T1_JSON.read_text())
        assert v1["rom_sha256"] == ROM_SHA256 and t1["rom_sha256"] == ROM_SHA256
        assert v1["static"]["frame_ids"] == ["0x25", "0x26", "0x27", "0x28", "0x29"]
        print("committed JSON consistent")
        return
    if not a.rom:
        ap.error("ROM path required")
    rom = load_rom(a.rom)
    rig = Rig(rom)
    results = {}
    if a.only in (None, "twist"):
        results[V1_JSON] = build_twist(rom, rig)
    if a.only != "twist":
        t1 = build_t1(rom, rig, a.only)
        if a.only is None:
            results[T1_JSON] = t1
        else:
            print(dumps(t1))
    for path, data in results.items():
        text = dumps(data)
        if a.check:
            print(path.name, "identical" if path.exists() and path.read_text() == text else "DIFFERS")
        elif a.write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
            print("wrote", path.relative_to(ROOT), len(text), "bytes")
        else:
            print(text[:3000])


if __name__ == "__main__":
    main()
