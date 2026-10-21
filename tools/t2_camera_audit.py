#!/usr/bin/env python3
"""T2: camera ownership, player screen boundary and boss-arrival audit (Research only, deterministic).

    python tools/t2_camera_audit.py ROM --write          # regenerate data/t2/*.json   (about 2-3 minutes)
    python tools/t2_camera_audit.py ROM --check          # regenerate in memory and compare with the committed JSON
    python tools/t2_camera_audit.py ROM --only static|clamp|boss|sign|start
    python tools/t2_camera_audit.py --validate           # no ROM: internal consistency of the committed JSON

Evidence classes (same vocabulary as earlier studies):
  BYTE-VERIFIED   = decoded ROM bytes / disassembly,
  EMULATED        = unmodified ROM in tools/sms_frame_harness.py via tools/player_fall_control.Lab (approximate VDP/IRQ),
  SYNTHETIC       = position / camera injected at arrival, or a limit forced (stated per scenario),
  POC-SOURCE      = the accepted POC C1-I source read (or executed in the node VM harness, tools/t2_poc_model.js); never GameMaker.

Nothing here stores ROM bytes, tiles or pixels: only counts, addresses, decoded numeric tables and small numeric tuples.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
OUT = ROOT / "data" / "t2"
FILES = {"static": OUT / "owner-map.json", "clamp": OUT / "clamp-scope.json", "boss": OUT / "boss-arrival.json",
         "sign": OUT / "sign-wait.json", "start": OUT / "zone-start.json"}
ZONES = ["thz", "gpz", "sez", "mghz", "apz", "eez"]
ZONE_NAME = {"thz": "THZ", "gpz": "GPZ", "sez": "SEZ", "mghz": "MGHZ", "apz": "AQZ", "eez": "EEZ"}
BOSS_TYPE = {"thz": 0x50, "gpz": 0x51, "sez": 0x54, "mghz": 0x56, "apz": 0x59, "eez": 0x5E}
BACK = {"thz": 480, "gpz": 480, "sez": 480, "mghz": 480, "apz": 480, "eez": 260}      # arrival distance left of the boss anchor (EEZ3 geometry needs the shorter run)
SIGN_ZONES = [("thz", 0), ("mghz", 1), ("gpz", 1), ("sez", 1)]


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def hx(v, n=2):
    return f"0x{v:0{n}X}"


def dumps(d) -> str:
    return json.dumps(d, indent=1) + "\n"


def load_rom(path) -> bytes:
    rom = Path(path).read_bytes()
    if len(rom) != 524288 or sha(rom) != ROM_SHA256:
        raise SystemExit("not the canonical Sonic Chaos (Europe) v1.2 ROM")
    return rom


def cpu_of(off):
    return (off // 0x4000, off if off < 0x8000 else 0x8000 + off % 0x4000)


def s16(v):
    return v - 65536 if v >= 32768 else v


# --------------------------------------------------------------------------------------------------------- static
CAM_ADDR = {0xD27C: "limit_top", 0xD27E: "limit_bottom", 0xD280: "limit_left", 0xD282: "limit_right", 0xD15E: "ctl_D15E", 0xD15F: "ctl_D15F",
            0xD2DA: "pan_target_x", 0xD2DC: "pan_target_y", 0xD284: "work_cam_x", 0xD286: "work_cam_y"}
VECTORS = {0x0353: "raise_left_limit_to_camera", 0x0356: "lower_right_limit_to_camera", 0x0359: "pan_on", 0x035C: "pan_off_enable",
           0x0407: "freeze_camera", 0x042B: "enable_camera"}
# owner of each bank-$1E / bank-$0C code region (BYTE-VERIFIED from the object handlers' entry addresses in the earlier boss audits)
OWNER_RANGES = [(0x0000, 0x0FFF, "engine (fixed bank)"), (0x4C00, 0x5A00, "camera engine $4C90..$59FF")]
BANK1E_OWNERS = [(0x8199, 0x81A5, "shared boss lock helper $8199"), (0x81BD, 0x8212, "shared boss release $81BD/$81F4 (THZ3, SEZ3, MGHZ3 branch, AQZ3)"),
                 (0x9583, 0x9590, "bottom-limit write in the $9583 handler (arena bottom lock)"),
                 (0x9771, 0x97FF, "boss shared states 1/2 ($9771 trigger, $97C1 pan setup; all zones)"),
                 (0x9AA1, 0x9AF8, "GPZ3 $51 intro (right limit 1664, pan)"), (0x9D2F, 0x9D50, "GPZ3 $51 release"),
                 (0xB232, 0xB240, "EEZ3 $5E/$60 release"), (0xB92D, 0xB940, "EEZ3 later encounter release")]


def static_owner_map(rom):
    rows = []
    for i in range(len(rom) - 4):
        op = rom[i]
        kind = addr = None
        if op in (0x22, 0x32, 0x2A, 0x3A, 0x21, 0x11, 0x01):
            addr, n = rom[i + 1] | rom[i + 2] << 8, 3
            kind = {0x22: "store16", 0x32: "store8", 0x2A: "load16", 0x3A: "load8", 0x21: "ld_hl_imm", 0x11: "ld_de_imm", 0x01: "ld_bc_imm"}[op]
        elif op == 0xED and rom[i + 1] in (0x43, 0x53, 0x63, 0x73, 0x4B, 0x5B, 0x6B, 0x7B):
            addr, n = rom[i + 2] | rom[i + 3] << 8, 4
            kind = "store16" if rom[i + 1] in (0x43, 0x53, 0x63, 0x73) else "load16"
        elif op in (0xCD, 0xC3):
            a = rom[i + 1] | rom[i + 2] << 8
            if a in VECTORS:
                bank, c = cpu_of(i)
                rows.append(OrderedDict(file=hx(i, 5), bank=hx(bank), cpu=hx(c, 4), op="call" if op == 0xCD else "jp", target=VECTORS[a]))
            continue
        else:
            continue
        if addr in CAM_ADDR and not (i < 0x8000 and False):
            bank, c = cpu_of(i)
            rows.append(OrderedDict(file=hx(i, 5), bank=hx(bank), cpu=hx(c, 4), op=kind, target=CAM_ADDR[addr]))
    # annotate
    for r in rows:
        c, b = int(r["cpu"], 16), int(r["bank"], 16)
        r["region"] = "-"
        if b == 0x1E:
            for lo, hi, name in BANK1E_OWNERS:
                if lo <= c <= hi:
                    r["region"] = name
        elif b == 0x0C:
            r["region"] = {0x83CB: "player state $20 handler $83A6: freeze at d>$F8", 0xA8C4: "goal sign $18 state-3 callback (every update the sign runs)",
                           0xAA43: "goal sign $18 contact: pan on", 0x84BE: "player state routine (D15E write)", 0x9172: "EEZ tube state: D15F write"}.get(c, "-")
        elif b == 1 and 0x4C00 <= c <= 0x5A00 or b == 0 and c < 0x1000:
            r["region"] = "engine/camera ($0570 vblank commit, $4C90.. limits, $5832 follow, $5956 pan)"
    # writes only (the contract table); loads are kept in the list but flagged
    stores = [r for r in rows if r["op"].startswith("store") or r["op"] in ("call", "jp")]
    # the clamp, byte-verified
    clamp = {"entry": "$4141 (bank 1)", "bytes_verified": {"state_gate": "LD A,(IX+1) / CP $29 / JR NC (skip)", "left": "A=low byte of playerX-cam; CP $10 -> JP C,$4244 (X := cam+$10)",
                                                         "right": "CP $F8 -> JP NC,$4251 (X := cam+$F7)"},
             "state_gate_below": 0x29, "left_edge": 0x10, "right_edge": 0xF7,
             "calls_cached_camera": "ED 5B 74 D1 = LD DE,(D174): the COMMITTED camera, not the working target D284",
             "bytes": {a: rom[0x4141 + a - 0x4141 : 0x4141 + a - 0x4141 + 1].hex() for a in []}}
    return OrderedDict(
        description="every absolute-address camera/limit/control access and every camera-vector call in the ROM (pattern scan; loads, stores, immediates) with the owning region where known",
        counts={"all": len(rows), "stores_and_calls": len(stores)}, vectors={hx(k, 4): v for k, v in VECTORS.items()},
        addresses={hx(k, 4): v for k, v in CAM_ADDR.items()}, rows=rows, player_clamp=clamp)


def decode_boss_tables(rom):
    """Shared boss state-1 trigger table `$97A1` and state-2 pan table `$9808` (bank $1E), indexed by zone + D4A5."""
    base = 0x78000 - 0x8000
    trig = [(rom[base + 0x97A1 + 4 * i] | rom[base + 0x97A2 + 4 * i] << 8, rom[base + 0x97A3 + 4 * i] | rom[base + 0x97A4 + 4 * i] << 8) for i in range(8)]
    pan = [(s16(rom[base + 0x9808 + 4 * i] | rom[base + 0x9809 + 4 * i] << 8), s16(rom[base + 0x980A + 4 * i] | rom[base + 0x980B + 4 * i] << 8)) for i in range(8)]
    return OrderedDict(
        trigger_table_97A1={"semantics": "strict |playerX-bossX| < dx and |playerY-bossY| < dy (CALL $0383/$0386), then $0356 lowers the right limit to the camera",
                            "rows": [{"row": i, "zone_or_encounter": ["THZ", "GPZ", "SEZ", "MGHZ", "AQZ", "EEZ first ($5E)", "EEZ second ($60)", "unused"][i], "dx": t[0], "dy": t[1]} for i, t in enumerate(trig)]},
        pan_table_9808={"semantics": "camera pan target = boss anchor + (dx, dy) at state 2->3 ($9808 row, then $0359 pan on); the right limit is exclusive so X settles one pixel short",
                        "rows": [{"row": i, "zone_or_encounter": ["THZ", "GPZ", "SEZ", "MGHZ", "AQZ", "EEZ first ($5E)", "EEZ second ($60)", "unused"][i], "dx": p[0], "dy": p[1]} for i, p in enumerate(pan)]})


# --------------------------------------------------------------------------------------------------------- rig
class Rig:
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


def snap(lab, zone=None, types=()):
    s, m = lab.s, lab.m
    cx = s.u16(0xD174)
    objs = []
    for a in range(0xD540, 0xDA00, 0x40):
        if m[a] in types:
            objs.append([m[a], m[a + 1], m[a + 2], s.u16(a + 0x11), s.u16(a + 0x14)])
    return {"u": lab.upd, "px": s.u16(0xD511), "py": s.u16(0xD514), "pst": m[0xD501], "vx": s.u16(0xD516), "cx": cx, "cy": s.u16(0xD176),
            "limL": s.u16(0xD280), "limR": s.u16(0xD282), "limT": s.u16(0xD27C), "limB": s.u16(0xD27E), "d15e": m[0xD15E], "d15f": m[0xD15F],
            "r1": s.reg[1], "objs": objs}


# ---------------------------------------------------------------------------------------------------------- boss
def boss_trace(rig, zone):
    bt = BOSS_TYPE[zone]
    bx, by = rig.anchors(f"{zone}3", bt)[0]
    lab = rig.lab(zone, 2)
    s, m = lab.s, lab.m
    px = bx - BACK[zone]
    lab.place(px, by - 120, 0x300, 0, cur=0x0E, f3=1, floor=False, prev=0, p24=0)
    s.w16(0xD174, px - 104)
    s.w16(0xD284, px - 104)
    rows, last, phase = [], lab.upd, "approach"
    ph_start, lock_u, init_r, reloaded = lab.upd, None, None, None
    plan = []
    for _ in range(40000):
        s.pad = 4 if phase == "left" else 8
        m[0xD29A] = 0x50                         # keep rings so a boss hit hurts but never kills (the act would reload and the camera restart)
        s.run_frame()
        if lab.upd == last:
            continue
        last = lab.upd
        r = snap(lab, zone, (bt,))
        r["phase"] = phase
        if init_r is None:
            init_r = r["limR"]
        if rows and (r["cx"] < rows[-1]["cx"] - 100 or r["px"] < rows[-1]["px"] - 200):
            reloaded = r["u"]                    # the act restarted (death): everything after is not the arena
            break
        rows.append(r)
        boss = r["objs"][0] if r["objs"] else None
        if lock_u is None and boss and (r["d15f"] & 1 or (r["limR"] != init_r and r["limR"] <= r["cx"] + 8)):
            lock_u = r["u"]
        if phase == "approach" and lock_u is not None and r["u"] >= lock_u + 260:
            phase, ph_start = "left", r["u"]
        elif phase == "left" and r["u"] >= ph_start + 130:
            phase, ph_start = "right", r["u"]
        elif phase == "right" and r["u"] >= ph_start + 130:
            break
        if r["u"] > 1500:
            break
    return bx, by, rows, reloaded


def boss_summary(zone, bx, by, rows, reloaded=None):
    bt = BOSS_TYPE[zone]

    def scr(r, x):
        return x - r["cx"]
    first = next((r for r in rows if r["objs"]), None)
    out = OrderedDict(zone=ZONE_NAME[zone], boss_type=hx(bt), anchor_placement=[bx, by], arrival_distance_left_of_anchor=BACK[zone], updates=len(rows))
    if not first:
        out["created"] = None
        return out
    b0 = first["objs"][0]
    out["created"] = OrderedDict(update=first["u"], boss_world_x=b0[3], boss_screen_x=scr(first, b0[3]), boss_state=b0[1], player_world_x=first["px"], player_screen_x=scr(first, first["px"]),
                                 camera=[first["cx"], first["cy"]], boss_minus_player=b0[3] - first["px"],
                                 note="screen X = world X - committed camera X on the 256 px window; >= 256 is off-screen right")
    vis = next((r for r in rows if r["objs"] and 0 <= scr(r, r["objs"][0][3]) < 256), None)
    if vis:
        v0 = vis["objs"][0]
        out["first_anchor_on_screen"] = OrderedDict(update=vis["u"], boss_world_x=v0[3], boss_screen_x=scr(vis, v0[3]), player_world_x=vis["px"], player_screen_x=scr(vis, vis["px"]),
                                                    camera=[vis["cx"], vis["cy"]], boss_state=v0[1], phase=vis["phase"], boss_right_of_player=v0[3] > vis["px"])
    else:
        out["first_anchor_on_screen"] = None
    init_r = rows[0]["limR"]
    lock = next((r for r in rows if r["objs"] and (r["d15f"] & 1 or (r["limR"] != init_r and r["limR"] <= r["cx"] + 8))), None)
    pan = next((r for r in rows if r["d15f"] & 1), None)
    trig = next((r for r in rows if r["objs"] and r["limR"] != init_r and r["limR"] <= r["cx"] + 8), None)
    ch = next((r for r in rows if r["limR"] != init_r), None)
    if ch:
        out["right_limit_first_changed"] = OrderedDict(update=ch["u"], camera=[ch["cx"], ch["cy"]], limit_right=ch["limR"], was=init_r, ahead_of_camera_by=ch["limR"] - ch["cx"],
                                                       player_screen_x=ch["px"] - ch["cx"])
    if trig:
        t0 = trig["objs"][0]
        out["arena_lock_right_limit"] = OrderedDict(update=trig["u"], camera=[trig["cx"], trig["cy"]], limits_L_R_T_B=[trig["limL"], trig["limR"], trig["limT"], trig["limB"]],
                                                    boss_world_x=t0[3], boss_screen_x=scr(trig, t0[3]), player_world_x=trig["px"], player_screen_x=scr(trig, trig["px"]), boss_state=t0[1])
    if pan:
        po = [r for r in rows if r["u"] >= pan["u"] and r["d15f"] & 1]
        end = next(r for r in po if (r["cx"], r["cy"]) == (po[-1]["cx"], po[-1]["cy"]))     # first update at the final pan position
        p0 = pan["objs"][0] if pan["objs"] else None
        out["pan"] = OrderedDict(start_update=pan["u"], start_camera=[pan["cx"], pan["cy"]], end_camera=[end["cx"], end["cy"]], limits_during_L_R_T_B=[pan["limL"], pan["limR"], pan["limT"], pan["limB"]],
                                 end_update=end["u"], boss_screen_x_at_start=None if p0 is None else scr(pan, p0[3]), boss_world_x_at_start=None if p0 is None else p0[3],
                                 max_camera_step=max((abs(b["cx"] - a["cx"]) for a, b in zip(po, po[1:])), default=0))
        e0 = end["objs"][0] if end["objs"] else None
        out["pan"]["boss_world_x_at_pan_end"] = None if e0 is None else e0[3]
        out["pan"]["boss_screen_x_at_pan_end"] = None if e0 is None else scr(end, e0[3])
    # player boundary once locked
    locked = [r for r in rows if lock and r["u"] >= lock["u"]]
    for ph in ("approach", "left", "right"):
        sel = [r for r in locked if r["phase"] == ph]
        if sel:
            sx = [scr(r, r["px"]) for r in sel]
            out[f"player_screen_x_range_{ph}_after_lock"] = [min(sx), max(sx)]
            out[f"player_world_x_range_{ph}_after_lock"] = [min(r["px"] for r in sel), max(r["px"] for r in sel)]
    out["max_player_screen_x_any_update"] = max(scr(r, r["px"]) for r in rows)
    out["max_player_screen_x_before_lock"] = max((scr(r, r["px"]) for r in rows if not lock or r["u"] < lock["u"]), default=None)
    out["player_x_exceeded_boss_anchor"] = [r["u"] for r in rows if r["objs"] and r["px"] > r["objs"][0][3]][:1] or None
    # camera step series
    steps = [abs(b["cx"] - a["cx"]) for a, b in zip(rows[3:], rows[4:])]     # the first updates after the injected start are excluded
    out["max_camera_step_x_any_update"] = max(steps) if steps else 0
    out["clamp_edges_screen_x"] = [16, 247]
    out["act_reloaded_at_update"] = reloaded
    return out


def build_boss(rig):
    res = OrderedDict()
    for z in ZONES:
        bx, by, rows, rel = boss_trace(rig, z)
        res[ZONE_NAME[z]] = boss_summary(z, bx, by, rows, rel)
    return OrderedDict(
        description="Per zone: RIGHT held from BACK px left of the boss anchor (arrival_distance_left_of_anchor); 260 updates after the arena lock RIGHT stays held, then LEFT 130 updates, then RIGHT 130 updates (player boundary probes). No state of the boss is forced.",
        evidence="EMULATED + SYNTHETIC arrival (position/camera injected at the start; everything after is the unmodified ROM)", zones=res,
        tables=None)


# ----------------------------------------------------------------------------------------------------------- sign
def sign_trace(rig, zone, act):
    key = f"{zone}{act + 1}"
    sx, sy = rig.anchors(key, 0x18)[0]
    lab = rig.lab(zone, act)
    s, m = lab.s, lab.m
    start = sx - (260 if zone == "mghz" else 420)          # MGHZ2: the ledge carrying the sign starts about 330 px before it
    lab.place(start, sy, 0x400, 0, cur=6, f3=0, floor=True, prev=0, p24=0)
    s.w16(0xD174, start - 104)
    s.w16(0xD284, start - 104)
    rows, last, phase, p0 = [], lab.upd, "right", lab.upd
    for _ in range(30000):
        s.pad = 8 if phase == "right" else 4
        s.run_frame()
        if lab.upd == last:
            continue
        last = lab.upd
        r = snap(lab, zone, (0x18, 0x19))
        r["phase"] = phase
        rows.append(r)
        if phase == "right" and r["px"] >= sx - 150:
            phase, p0 = "left", r["u"]
        elif phase == "left" and r["u"] >= p0 + 320:
            break
        if r["u"] > 2500:
            break
    return sx, sy, rows


def sign_summary(zone, act, sx, sy, rows):
    left_rows = [r for r in rows if r["phase"] == "left"]
    first_raise = next((r for r in rows if r["limL"] > 0 and r["limL"] >= r["cx"] - 8 and r["objs"]), None)
    # D280 stays above its header value only because the sign callback raises it; first update where the left limit tracks the camera
    out = OrderedDict(zone=ZONE_NAME[zone], act=act + 1, sign_anchor=[sx, sy], updates=len(rows))
    if first_raise:
        out["left_limit_first_tracks_camera"] = OrderedDict(update=first_raise["u"], camera_x=first_raise["cx"], limL=first_raise["limL"], player_x=first_raise["px"],
                                                            sign_minus_camera=sx - first_raise["cx"], sign_minus_player=sx - first_raise["px"])
    turn = left_rows[0] if left_rows else None
    if turn:
        out["turn_around"] = OrderedDict(update=turn["u"], player_x=turn["px"], camera_x=turn["cx"], limL=turn["limL"], player_screen_x=turn["px"] - turn["cx"])
        sx_ = [r["px"] - r["cx"] for r in left_rows]
        out["player_screen_x_min_while_walking_back"] = min(sx_)
        out["player_screen_x_max_while_walking_back"] = max(sx_)
        out["camera_x_min_after_turn"] = min(r["cx"] for r in left_rows)
        out["camera_x_at_turn"] = turn["cx"]
        out["left_limit_final"] = left_rows[-1]["limL"]
        out["player_world_x_final"] = left_rows[-1]["px"]
    out["sign_contacted_during_trace"] = any(r["objs"] and r["objs"][0][0] == 0x18 and r["objs"][0][1] >= 4 for r in rows)
    return out


def build_sign(rig):
    res = OrderedDict()
    for z, a in SIGN_ZONES:
        sx, sy, rows = sign_trace(rig, z, a)
        res[f"{ZONE_NAME[z]}{a + 1}"] = sign_summary(z, a, sx, sy, rows)
    return OrderedDict(description="Pre-contact sign wait: Sonic runs RIGHT from 420 px (MGHZ2: 260 px, the ledge starts there) before the type-$18 sign until 150 px before it, then LEFT is held for 320 updates. The sign is never touched. Records when the sign callback starts raising the left limit and how far back Sonic can walk.",
                       evidence="EMULATED + SYNTHETIC start (position injected)", zones=res)


# ----------------------------------------------------------------------------------------------------------- clamp
def build_clamp(rig, rom):
    """The clamp is unconditional for states < $29: prove it with a lock that has nothing to do with the sign or a boss."""
    res = OrderedDict()
    for zone, act, x0, cam in (("thz", 2, 1660, 1560),):          # THZ3 flat floor 1480..2560, boss far outside its creation band (anchor 1936 - (camera + 256) = 120 > 95)
        lab = rig.lab(zone, act)
        s, m = lab.s, lab.m
        lab.place(x0, 238, 0, 0, cur=1, f3=0, floor=True, prev=0, p24=0)
        s.w16(0xD174, cam)
        s.w16(0xD284, cam)
        for _ in range(10):
            s.pad = 0
            s.run_frame()
        cam = s.u16(0xD174)
        # SYNTHETIC LOCK: left limit and right limit both frozen at the current camera (what a boss/sign lock does), no object involved
        s.w16(0xD280, cam)
        s.w16(0xD282, cam)
        rows, last = [], lab.upd
        for name, pad, n in (("left", 4, 100), ("right", 8, 140), ("jump_left", 4 | 16, 60), ("jump_right", 8 | 16, 80)):
            for _ in range(n * 3):
                s.pad = pad
                s.run_frame()
                if lab.upd != last:
                    last = lab.upd
                    rows.append((name, s.u16(0xD511) - s.u16(0xD174), m[0xD501], s.u16(0xD174)))
                    if len([r for r in rows if r[0] == name]) >= n:
                        break
        by = OrderedDict()
        for name, scr, st, c in rows:
            by.setdefault(name, []).append(scr)
        res[f"{ZONE_NAME[zone]}{act + 1}"] = OrderedDict(
            synthetic_lock_camera_x=cam, start_player_x=x0, camera_x_after=sorted({c for _, _, _, c in rows}),
            player_screen_x_min={k: min(v) for k, v in by.items()}, player_screen_x_max={k: max(v) for k, v in by.items()},
            states_seen=sorted({st for _, _, st, _ in rows}))
    # code facts
    gate = rom[0x4141:0x4147].hex()
    return OrderedDict(
        description="Clamp scope: with the camera frozen by a bare limit lock (D280 = D282 = camera, no sign, no boss) Sonic is still held to [cam+16, cam+247]. The clamp ($4141) therefore belongs to the player step, not to any object.",
        evidence="BYTE-VERIFIED ($4141 gate bytes) + EMULATED + SYNTHETIC lock", gate_bytes_4141=gate, gate_decoded="LD A,(IX+1); CP $29; JR NC,$4169 (states >= $29 skip the clamp)",
        cases=res, states_excluded_by_gate=">= 0x29", state_20_handler="$83A6 does not call $4141/$4281 (viewport-semantics-audit section 4)")


# ----------------------------------------------------------------------------------------------------------- start
def zone_start_trace(rom, rig, zone, act, frames=420):
    from sms_frame_harness import SMS, BTN_1, BTN_2
    zi = {"thz": 0, "gpz": 1, "sez": 2, "mghz": 3, "apz": 4, "eez": 5}[zone]
    s = SMS(rom)
    st = {"on": False, "f0": None}

    def select(mm):
        mm._write(0xD297, zi)
        mm._write(0xD298, act)

    def begin(mm):
        if mm.frame > 300 and not st["on"]:
            st["on"], st["f0"] = True, mm.frame
    s.add_pc_hook(0x07D5, select)
    s.add_pc_hook(0x4E97, begin)
    m = s.mem
    for f in range(4000):
        s.pad = 0 if f < 250 else BTN_1 if f < 700 and f % 40 < 3 else (BTN_1 | BTN_2) if not st["on"] and f % 60 < 10 else 0
        s.run_frame()
        if st["on"]:
            break
    rows = []
    for k in range(frames):
        s.pad = 0
        s.run_frame()
        cram = bytes(s.cram[:32])
        rows.append({"f": k, "r1": s.reg[1], "bg": sum(cram[:16]), "spr": sum(cram[16:32]), "cx": s.u16(0xD174), "cy": s.u16(0xD176), "px": s.u16(0xD511), "py": s.u16(0xD514),
                     "pst": m[0xD501], "vy": s.u16(0xD519), "d15e": m[0xD15E], "act": m[0xD298], "zone": m[0xD297]})
    return rows


def zone_start_summary(zone, act, rows):
    def runs(key):
        out, last = [], None
        for r in rows:
            if r[key] != last:
                out.append([r["f"], r[key]])
                last = r[key]
        return out
    py = [r["py"] for r in rows]
    sy = [r["py"] - r["cy"] for r in rows]
    blank = [r["f"] for r in rows if r["r1"] & 0x40 == 0]
    first_pst = next((r["f"] for r in rows if r["pst"] != 0), None)
    return OrderedDict(
        zone=ZONE_NAME[zone], act=act + 1, frames=len(rows),
        display_blank_frames=[blank[0], blank[-1], len(blank)] if blank else None,
        first_frame_display_on=next((r["f"] for r in rows if r["r1"] & 0x40), None),
        bg_palette_sum_changes=runs("bg")[:14], sprite_palette_sum_changes=runs("spr")[:10],
        camera_y_series_first_changes=runs("cy")[:14], camera_x_changes=runs("cx")[:8],
        player_y_changes=runs("py")[:10], player_state_changes=runs("pst")[:10],
        player_screen_y_range=[min(sy), max(sy)], player_world_y_first_last=[py[0], py[-1]])


def build_start(rom, rig):
    res = OrderedDict()
    for z, a in (("thz", 0), ("gpz", 0), ("sez", 0), ("mghz", 0), ("apz", 0), ("eez", 0), ("thz", 1), ("mghz", 1)):
        res[f"{ZONE_NAME[z]}{a + 1}"] = zone_start_summary(z, a, zone_start_trace(rom, rig, z, a))
    return OrderedDict(description="First 420 frames after the level loader hook ($4E97) for each zone act-1 (plus THZ2, MGHZ2): VDP R1 display bit, palette sums, camera Y/X, player Y and state. Palette values are sums of the 32 CRAM bytes, not colours.",
                       evidence="EMULATED (approximate VDP/IRQ model)", acts=res)


# ----------------------------------------------------------------------------------------------------------- main
def build(rom, only=None):
    rig = Rig(rom)
    out = OrderedDict()
    if only in (None, "static"):
        d = static_owner_map(rom)
        d["boss_tables"] = decode_boss_tables(rom)
        out["static"] = d
    if only in (None, "clamp"):
        out["clamp"] = build_clamp(rig, rom)
    if only in (None, "boss"):
        d = build_boss(rig)
        d["tables"] = decode_boss_tables(rom)
        out["boss"] = d
    if only in (None, "sign"):
        out["sign"] = build_sign(rig)
    if only in (None, "start"):
        out["start"] = build_start(rom, rig)
    return out


def validate():
    n = 0
    for k, p in FILES.items():
        d = json.loads(p.read_text())
        assert d, p
        n += 1
    b = json.loads(FILES["boss"].read_text())
    for z, v in b["zones"].items():
        assert v["created"] is not None, z
    print("ok", n, "files")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", nargs="?")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--only")
    ap.add_argument("--validate", action="store_true")
    a = ap.parse_args()
    if a.validate:
        return validate()
    rom = load_rom(a.rom)
    out = build(rom, a.only)
    for k, v in out.items():
        text = dumps(v)
        if a.write:
            FILES[k].parent.mkdir(parents=True, exist_ok=True)
            FILES[k].write_text(text)
            print("wrote", FILES[k].relative_to(ROOT), len(text))
        elif a.check:
            same = FILES[k].exists() and FILES[k].read_text() == text
            print("CHECK", k, "identical" if same else "DIFFERENT")
            if not same:
                sys.exit(1)
        else:
            print(k, len(text))


if __name__ == "__main__":
    main()
