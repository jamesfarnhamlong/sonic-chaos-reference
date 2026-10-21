#!/usr/bin/env python3
"""T3: boss walk-on and widescreen framing audit (Research only, deterministic).

    python tools/t3_boss_walkon_audit.py ROM --write rom        # ROM series + decoded frame extents (needs the ROM and z80; about 1-2 minutes)
    python tools/t3_boss_walkon_audit.py ROM --check rom
    POC=<checkout> node tools/t3_poc_boss_run.js --write          # POC series (needs the accepted POC checkout, read only)
    python tools/t3_boss_walkon_audit.py --write summary          # derived events/metrics from the committed series (ROM-free, POC-free)
    python tools/t3_boss_walkon_audit.py --check summary
    python tools/t3_boss_walkon_audit.py --validate               # internal consistency of the committed JSON

Evidence classes: BYTE-VERIFIED = decoded ROM bytes (mapping frame extents); EMULATED = unmodified ROM in tools/sms_frame_harness.py via the T2 rig
(approximate VDP/IRQ); SYNTHETIC = the arrival position/camera is injected at the start (stated per scenario); POC-SOURCE = shipped GML executed in
the POC's node VM harness (tools/t3_poc_boss_run.js), never GameMaker, never Windows.

Nothing here stores ROM bytes, tiles or pixels: only counts, decoded numeric extents and small numeric tuples.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

OUT = ROOT / "data" / "t3"
F_ROM = OUT / "rom-series.json"
F_EXT = OUT / "frame-extents.json"
F_POC = OUT / "poc-series.json"
F_SUM = OUT / "boss-walkon-summary.json"
ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
UPDATES = 450
WIDTHS = {"w256": (256, 192), "w348": (348, 196)}

# zone key (ROM harness), boss family (ROM object types that carry the boss body, its parts and projectiles), the primary body type, the state that opens the
# fight, the POC camera mode that is the pan, and the arrival distance left of the placement (identical for ROM and POC; THZ3's floor starts at X 1480)
ZONES = OrderedDict([
    ("THZ3", dict(rom="thz", family=(0x50,), primary=0x50, fight_state=6, poc_pan_mode=3, back=376)),
    ("GPZ3", dict(rom="gpz", family=(0x51,), primary=0x51, fight_state=7, poc_pan_mode=2, back=480)),
    ("SEZ3", dict(rom="sez", family=(0x54, 0x55), primary=0x54, fight_state=6, poc_pan_mode=3, back=480)),
    ("MGHZ3", dict(rom="mghz", family=(0x56,), primary=0x56, fight_state=11, poc_pan_mode=3, back=480)),
    ("AQZ3", dict(rom="apz", family=(0x59, 0x5A, 0x5B, 0x5C, 0x5D), primary=0x59, fight_state=6, poc_pan_mode=3, back=480)),
    ("EEZ3", dict(rom="eez", family=(0x5E, 0x5F, 0x60, 0x61, 0x62, 0x63), primary=0x5E, fight_state=6, poc_pan_mode=3, back=260)),
])


def dumps(d) -> str:
    return json.dumps(d, separators=(",", ":")) + "\n"


def s16(v):
    return v - 65536 if v >= 32768 else v


# --------------------------------------------------------------------------------------------------------- ROM mapping extents
def cpu2rom(cpu: int) -> int:
    return 0x3C000 + (cpu - 0x8000)          # mapping tables live in bank $0F, mapped at $8000


def decode_frames(rom: bytes, type_id: int):
    """Frame records of a type: pointer word table at ROM $3C000+2*type -> word table of record pointers; record = count, ext x, ext y, coord ptr, ...
    Pieces are 8 wide, 16 tall sprites at (x, y) relative to the object anchor (no per-type offset; shared registration pipeline)."""
    ptr = rom[0x3C000 + 2 * type_id] | rom[0x3C000 + 2 * type_id + 1] << 8
    table = cpu2rom(ptr)
    ptrs, first, i = [], None, 0
    while i < 64:
        w = rom[table + 2 * i] | rom[table + 2 * i + 1] << 8
        if first is not None and table + 2 * i >= cpu2rom(first):
            break
        if not 0x8000 <= w < 0xC000:
            break
        ptrs.append(w)
        cand = [p for p in ptrs if p != 0xA0E4]          # $A0E4 = the shared empty frame record
        first = min(cand) if cand else None
        i += 1
    out = []
    for f, w in enumerate(ptrs):
        rec = cpu2rom(w)
        cnt, cp = rom[rec], rom[rec + 3] | rom[rec + 4] << 8
        pcs = []
        if cnt and 0x8000 <= cp < 0xC000:
            b = cpu2rom(cp)
            for k in range(cnt):
                pcs.append((s16(rom[b + 4 * k + 2] | rom[b + 4 * k + 3] << 8), s16(rom[b + 4 * k] | rom[b + 4 * k + 1] << 8)))
        out.append(OrderedDict(frame=f, pieces=cnt, min_x=min((x for x, _ in pcs), default=None), max_x_excl=max((x + 8 for x, _ in pcs), default=None),
                               min_y=min((y for _, y in pcs), default=None), max_y_excl=max((y + 16 for _, y in pcs), default=None)))
    return out


def build_extents(rom: bytes):
    types = sorted({t for z in ZONES.values() for t in z["family"]})
    return OrderedDict(
        description="Anchor-relative visible extents per mapping frame (BYTE-VERIFIED, bank $0F). min/max are piece boxes (8x16 pieces); an empty frame has no pieces. Mirrored objects (flags4 bit 4) negate and swap x.",
        rom_sha256=ROM_SHA256, types={f"0x{t:02X}": decode_frames(rom, t) for t in types})


def extent(ext_tbl, type_id: int, frame: int, mirrored: bool = False):
    fr = ext_tbl["types"].get(f"0x{type_id:02X}")
    if fr is None or frame >= len(fr) or not fr[frame]["pieces"]:
        return None
    e = fr[frame]
    if mirrored:
        return (-e["max_x_excl"], -e["min_x"], e["min_y"], e["max_y_excl"])
    return (e["min_x"], e["max_x_excl"], e["min_y"], e["max_y_excl"])


# --------------------------------------------------------------------------------------------------------- ROM series
def rom_trace(rig, zkey: str, scenario: str):
    import t2_camera_audit as T2
    z = ZONES[zkey]
    fam = z["family"]
    bx, by = rig.anchors(f"{z['rom']}3", z["primary"])[0]
    lab = rig.lab(z["rom"], 2)
    s, m = lab.s, lab.m
    px = bx - z["back"]
    lab.place(px, by - 120, 0x300, 0, cur=0x0E, f3=1, floor=False, prev=0, p24=0)
    s.w16(0xD174, px - 104)
    s.w16(0xD284, px - 104)
    cols = OrderedDict((k, []) for k in ("u", "px", "py", "pst", "cx", "cy", "limL", "limR", "limT", "limB", "pan", "boss"))
    last, stopped, init_r = lab.upd, False, None
    for _ in range(60000):
        s.pad = 0 if stopped else 8
        m[0xD29A] = 0x50                         # keep rings so a boss hit hurts but never kills (the act would reload and the camera restart)
        s.run_frame()
        if lab.upd == last:
            continue
        last = lab.upd
        r = T2.snap(lab, z["rom"], ())
        if init_r is None:
            init_r = r["limR"]
        slots = [[m[a], m[a + 1], m[a + 6], m[a + 4], s.u16(a + 0x11), s.u16(a + 0x14)] for a in range(0xD540, 0xDA00, 0x40) if m[a] in fam]
        for k in ("u", "px", "py", "pst", "cx", "cy", "limL", "limR", "limT", "limB"):
            cols[k].append(r[k])
        cols["pan"].append(r["d15f"] & 1)
        cols["boss"].append(slots)
        if scenario == "stop" and not stopped and ((r["limR"] != init_r and r["limR"] <= r["cx"] + 8) or r["d15f"] & 1):
            stopped = True
        if len(cols["u"]) >= UPDATES:
            break
    return cols


def build_rom(rom: bytes):
    import t2_camera_audit as T2
    rig = T2.Rig(rom)
    zones = OrderedDict()
    for zk in ZONES:
        zones[zk] = OrderedDict((sc, rom_trace(rig, zk, sc)) for sc in ("hold", "stop"))
    return OrderedDict(
        description="ROM per-update boss-arrival series, 256 px (EMULATED + SYNTHETIC arrival). Sonic is placed back_px left of the boss placement on the act floor, RIGHT held (hold) or released at the arena lock (stop). Everything after the placement is the unmodified ROM. boss = [type, state, mapping frame, flags4, worldX, worldY] per boss-family slot.",
        evidence="EMULATED + SYNTHETIC arrival", rom_sha256=ROM_SHA256, updates=UPDATES, back_px={k: v["back"] for k, v in ZONES.items()}, zones=zones)


# --------------------------------------------------------------------------------------------------------- derived events
def _vis_cols(ext_tbl, slots, cam, view, types_ok=None):
    """Visible columns (0..sprite width) and the first visible slot, for slots = [(type, frame, mirrored, x, y)] against a camera and a (w, h) view."""
    best = None
    for t, fr, mir, x, y in slots:
        if types_ok is not None and t not in types_ok:
            continue
        e = extent(ext_tbl, t, fr, mir)
        if e is None:
            continue
        sx, sy = x - cam[0], y - cam[1]
        l, r = sx + e[0], sx + e[1]
        if l < view[0] and r > 0 and sy + e[2] < view[1] and sy + e[3] > 0:
            cols = min(view[0], r) - max(0, l)
            if best is None or cols > best[0]:
                best = (cols, t, [sx, sy])
    return best


def rom_rows(series, zk):
    z = ZONES[zk]
    n = len(series["u"])
    for i in range(n):
        yield {k: series[k][i] for k in series}


def summarize(rows, view, ext_tbl, zk, kind, scenario):
    """Events and camera/player metrics for one series. kind = 'rom' | 'poc'. Rows are dicts of one update."""
    z = ZONES[zk]
    W, H = view
    rows = list(rows)
    # -- boss slots per row as (type, frame, mirrored, x, y)
    def slots_of(r):
        if kind == "rom":
            return [(b[0], b[2], bool((b[3] >> 4) & 1), b[4], b[5]) for b in r["boss"]]
        out = []
        if r["act"] and r["bx"] is not None:
            out.append((z["primary"], r["bfr"] or 0, False, r["bx"], r["by"]))
        if zk == "AQZ3" and r.get("kx") is not None and r["act"]:
            if not (W > 256 and not r.get("ready")):
                out.append((0x5A, r["kfr"] or 0, False, r["kx"], r["ky"]))
        return out

    def primary_of(r):
        if kind == "rom":
            for b in r["boss"]:
                if b[0] == z["primary"]:
                    return b
            return None
        if r["act"] and r["bx"] is not None:
            return [z["primary"], r["bs"], r["bfr"], 0, r["bx"], r["by"]]
        return None

    exists = [primary_of(r) is not None for r in rows]
    cu = next((i for i, e in enumerate(exists) if e), None)
    out = OrderedDict(view=[W, H])
    if cu is None:
        out["created"] = None
        return out
    r0 = rows[cu]
    p0 = primary_of(r0)
    out["created"] = OrderedDict(u=r0["u"], camera=[r0["cx"], r0["cy"]], camera_previous=[rows[cu - 1]["cx"], rows[cu - 1]["cy"]] if cu > 0 else None, player_screen_x=r0["px"] - r0["cx"], boss_anchor=[p0[4], p0[5]], boss_screen_x=p0[4] - r0["cx"])
    # -- relocation: a jump of the primary anchor larger than normal motion between consecutive updates
    reloc, prevp = [], None
    for i in range(cu, len(rows)):
        p = primary_of(rows[i])
        if p is not None and prevp is not None and (abs(p[4] - prevp[4]) >= 24 or abs(p[5] - prevp[5]) >= 24):
            reloc.append(OrderedDict(u=rows[i]["u"], from_=[prevp[4], prevp[5]], to=[p[4], p[5]], camera=[rows[i]["cx"], rows[i]["cy"]], to_screen=[p[4] - rows[i]["cx"], p[5] - rows[i]["cy"]]))
        if p is not None:
            prevp = p
    out["relocations"] = reloc
    # -- right limit: value at creation, the update it is first lowered (the arena lock), and what it was when the pan began
    def rlim(r):
        return r["limR"] if kind == "rom" else r["right"]
    def lim_set(v, ref):
        return v is not None and v > 0 and (ref is None or ref == 0 or v < ref)
    ref = rlim(rows[cu])
    li = next((i for i in range(cu, len(rows)) if lim_set(rlim(rows[i]), ref)), None)
    def panning(r):
        return bool(r["pan"]) if kind == "rom" else r["mode"] >= z["poc_pan_mode"]
    pi = next((i for i, r in enumerate(rows) if panning(r)), None)
    pe = None
    if pi is not None:
        last = (rows[-1]["cx"], rows[-1]["cy"])
        seg_p = [i for i in range(pi, len(rows)) if panning(rows[i])]
        last = (rows[seg_p[-1]]["cx"], rows[seg_p[-1]]["cy"])
        pe = next(i for i in seg_p if (rows[i]["cx"], rows[i]["cy"]) == last)     # first update at the final camera position of the pan owner
    out["right_limit"] = OrderedDict(
        at_creation=ref, first_lowered_update=None if li is None else rows[li]["u"], first_lowered_value=None if li is None else rlim(rows[li]),
        player_screen_x_at_first_lowered=None if li is None else rows[li]["px"] - rows[li]["cx"],
        lowered_before_pan=bool(li is not None and (pi is None or li < pi)),
        at_pan_start=None if pi is None else rlim(rows[pi]), camera_minus_limit_at_pan_start=None if pi is None or rlim(rows[pi]) in (None, 0) else rows[pi]["cx"] - rlim(rows[pi]))

    def at(i):
        r = rows[i]
        p = primary_of(r)
        return OrderedDict(u=r["u"], camera=[r["cx"], r["cy"]], player_world_x=r["px"], player_screen_x=r["px"] - r["cx"], boss_world=None if p is None else [p[4], p[5]],
                           boss_screen_x=None if p is None else p[4] - r["cx"], boss_screen_y=None if p is None else p[5] - r["cy"])
    out["pan_start"] = None if pi is None else at(pi)
    out["pan_end"] = None if pe is None else at(pe)
    # -- first visible frame (any boss-family sprite piece inside the view)
    fv = None
    for i in range(cu, len(rows)):
        v = _vis_cols(ext_tbl, slots_of(rows[i]), (rows[i]["cx"], rows[i]["cy"]), (W, H))
        if v:
            r = rows[i]
            fv = OrderedDict(u=r["u"], camera=[r["cx"], r["cy"]], type=f"0x{v[1]:02X}", anchor_screen=v[2], visible_columns=v[0], player_screen_x=r["px"] - r["cx"], player_left_of_boss=r["px"] < (v[2][0] + r["cx"]))
            if kind == "poc":
                fv["camera_mode"] = r["mode"]
            break
    out["first_visible"] = fv
    # -- fight activation (primary body reaches the state that opens the fight)
    ai = next((i for i in range(cu, len(rows)) if (primary_of(rows[i]) or [0, -1])[1] == z["fight_state"]), None)
    out["fight_activation"] = None if ai is None else at(ai)
    # primary state sequence
    seq, prev = [], None
    for i in range(cu, len(rows)):
        p = primary_of(rows[i])
        st = None if p is None else p[1]
        if st != prev:
            seq.append([rows[i]["u"], st])
            prev = st
    out["primary_state_sequence"] = seq[:16]
    # -- camera continuity from the creation update to the end of the pan (or the activation when later)
    end_i = max(x for x in (pe, ai, cu) if x is not None)
    seg = rows[max(cu - 1, 0):end_i + 1]
    dx = [b["cx"] - a["cx"] for a, b in zip(seg, seg[1:])]
    dy = [b["cy"] - a["cy"] for a, b in zip(seg, seg[1:])]
    mx = best = 0
    at_u = None
    for r in seg:
        mx = max(mx, r["cx"])
        if mx - r["cx"] > best:
            best, at_u = mx - r["cx"], r["u"]
    if pi is not None and pe is not None:
        ps_ = rows[max(pi - 1, 0):pe + 1]
        pan_steps = [[abs(b["cx"] - a["cx"]), abs(b["cy"] - a["cy"])] for a, b in zip(ps_, ps_[1:])]
    else:
        pan_steps = []
    out["camera"] = OrderedDict(
        window_updates=[seg[0]["u"], seg[-1]["u"]],
        pan_max_abs_step=[max((v[0] for v in pan_steps), default=0), max((v[1] for v in pan_steps), default=0)],
        max_abs_step=[max((abs(v) for v in dx), default=0), max((abs(v) for v in dy), default=0)],
        updates_with_step_over_7=sum(1 for a, b in zip(dx, dy) if abs(a) > 7 or abs(b) > 7),
        creation_update_step=[rows[cu]["cx"] - rows[cu - 1]["cx"], rows[cu]["cy"] - rows[cu - 1]["cy"]] if cu >= 15 else None,   # None: created inside the start-up transient (EEZ3 at 348 px)
        largest_negative_x_step=min(dx, default=0), x_retreat=OrderedDict(pixels=best, at_update=at_u),
        y_range=[min(r["cy"] for r in seg), max(r["cy"] for r in seg)], y_total_down=sum(v for v in dy if v > 0), y_total_up=-sum(v for v in dy if v < 0),
        x_total_forward=sum(v for v in dx if v > 0), x_total_backward=-sum(v for v in dx if v < 0))
    # -- player against the view
    after = rows[cu:]
    psx = [r["px"] - r["cx"] for r in after]
    out["player"] = OrderedDict(screen_x_max=max(psx), screen_x_min=min(psx), updates_beyond_right_clamp_plus_4=sum(1 for v in psx if v > W - 9 + 4), updates_beyond_left_clamp_minus_4=sum(1 for v in psx if v < 16 - 4),
                                right_clamp_screen_x=W - 9, screen_x_at_creation=psx[0])
    return out


def build_summary(rom_series, ext_tbl, poc_series):
    out = OrderedDict(
        description="Derived boss-walk-on events and camera/player metrics. Update numbers are scenario-relative (start distances differ only through the injected arrival); compare the deltas between events. 'rom' = EMULATED 256 px; 'w256'/'w348' = POC-SOURCE MODEL.",
        sources=["data/t3/rom-series.json", "data/t3/poc-series.json", "data/t3/frame-extents.json"], poc_checkout_head=poc_series.get("poc_checkout_head"), zones=OrderedDict())
    for zk in ZONES:
        zr = OrderedDict()
        for sc in ("hold", "stop"):
            rs = rom_series["zones"][zk][sc]
            zr[f"rom_{sc}"] = summarize(rom_rows(rs, zk), (256, 192), ext_tbl, zk, "rom", sc)
            # what the unchanged ROM scene would show in a 348x196 window with the same camera origin (static exposure, no POC adapter involved)
            zr[f"rom_{sc}_same_camera_in_348"] = OrderedDict(first_visible=summarize(rom_rows(rs, zk), (348, 196), ext_tbl, zk, "rom", sc)["first_visible"])
            for wk, (w, h) in WIDTHS.items():
                ps = poc_series["zones"][zk][wk][sc]
                n = len(ps["u"])
                rows = ({k: ps[k][i] for k in ps} for i in range(n))
                zr[f"poc_{wk}_{sc}"] = summarize(rows, (w, h), ext_tbl, zk, "poc", sc)
        out["zones"][zk] = zr
    return out


# --------------------------------------------------------------------------------------------------------- driver
def load_rom(path) -> bytes:
    import hashlib
    rom = Path(path).read_bytes()
    if len(rom) != 524288 or hashlib.sha256(rom).hexdigest() != ROM_SHA256:
        raise SystemExit("not the canonical Sonic Chaos (Europe) v1.2 ROM")
    return rom


def validate() -> int:
    bad = 0
    for p in (F_ROM, F_EXT, F_POC, F_SUM):
        if not p.exists():
            print("MISSING", p.name)
            bad += 1
    if bad:
        return 1
    rom, ext, poc, summ = (json.loads(p.read_text()) for p in (F_ROM, F_EXT, F_POC, F_SUM))
    for zk in ZONES:
        for sc in ("hold", "stop"):
            n = len(rom["zones"][zk][sc]["u"])
            if n != UPDATES:
                print("ROM rows", zk, sc, n)
                bad += 1
            for wk in WIDTHS:
                if len(poc["zones"][zk][wk][sc]["u"]) != UPDATES:
                    print("POC rows", zk, wk, sc)
                    bad += 1
    again = build_summary(rom, ext, poc)
    if json.loads(json.dumps(again)) != summ:
        print("summary differs from a rebuild of the committed series")
        bad += 1
    print("VALIDATE", "ok" if not bad else f"{bad} problem(s)")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", nargs="?")
    ap.add_argument("--write", choices=["rom", "summary"])
    ap.add_argument("--check", choices=["rom", "summary"])
    ap.add_argument("--validate", action="store_true")
    a = ap.parse_args()
    if a.validate:
        return validate()
    which = a.write or a.check
    if not which:
        ap.error("--write/--check rom|summary or --validate")
    if which == "rom":
        if not a.rom:
            ap.error("the ROM path is required for 'rom'")
        rom = load_rom(a.rom)
        new = {F_ROM: dumps(build_rom(rom)), F_EXT: dumps(build_extents(rom))}
    else:
        rom_s, ext, poc = (json.loads(p.read_text()) for p in (F_ROM, F_EXT, F_POC))
        new = {F_SUM: dumps(build_summary(rom_s, ext, poc))}
    rc = 0
    for p, t in new.items():
        if a.write:
            OUT.mkdir(parents=True, exist_ok=True)
            p.write_text(t)
            print("wrote", p.relative_to(ROOT), len(t))
        else:
            same = p.exists() and p.read_text() == t
            print("CHECK", p.name, "identical" if same else "DIFFERENT")
            rc |= 0 if same else 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
