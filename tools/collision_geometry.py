#!/usr/bin/env python3
"""Collision-geometry audit (research only, deterministic).

Recomputes from the checked ROM:
  * the player's collision extents $D52C/$D52D per player state (original animation engine executed),
  * a reference model of the shared overlap helper $6328, compared with the original on a large grid,
  * a reference model of the solid-projection helper $5FA0, compared with the original,
  * which shared helper every THZ object type reaches (recursive descent from its state callbacks),
  * box sweeps of the real object callbacks,
  * the terrain side-sensor constants and proof that terrain code never reads $D52C/$D52D,
  * the list of research/POC assumptions that disagree with the recovered geometry.

Output: data/rom-cache/collision-geometry.json (machine-facing, numeric labels only).

Usage:
  python tools/collision_geometry.py ROM.sms                 # write the cache
  python tools/collision_geometry.py ROM.sms --check         # compare with the cache
  python tools/collision_geometry.py ROM.sms --static-only   # no Z80 execution
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
OUTPUT = ROOT / "data" / "rom-cache" / "collision-geometry.json"
SLOT = 0xD700


def h(v: int, digits: int = 4) -> str:
    return f"0x{v:0{digits}X}"


def u16(rom: bytes, pos: int) -> int:
    return rom[pos] | (rom[pos + 1] << 8)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def cpu_of(off: int) -> tuple:
    b = off // 0x4000
    return b, off % 0x4000 + (0 if b == 0 else 0x4000 if b == 1 else 0x8000)


def check_rom(rom: bytes) -> None:
    if len(rom) != 524288 or sha(rom) != ROM_SHA256:
        raise ValueError("expected the documented Sonic Chaos SMS research ROM")


EVIDENCE = {
    "DECODED DATA": "ROM tables/records decoded by a parser",
    "BYTE-VERIFIED ASSEMBLY": "routine bytes compared literally and disassembled by hand",
    "SOURCE-TRACED BEHAVIOR": "behavior read from the disassembly, not executed",
    "CONTROLLED ROUTINE RESULT": "original routine executed on a Z80 core with explicit RAM",
    "EMULATED ORIGINAL FRAME": "whole original game run in the approximate SMS harness",
    "POC SOURCE (READ-ONLY)": "value read from the Windows POC project files; never executed, never modified",
    "UNRESOLVED": "not established",
}


# --------------------------------------------------------------------------- #
# 1. player extents
# --------------------------------------------------------------------------- #
def _engine_walk(rom: bytes, ptype: int, state: int, speed: int) -> dict:
    """Run the original animation engine ($64FA) for the player slot and record every frame's extents."""
    from oracle import Oracle
    o = Oracle(rom)
    m = o.mem
    base = 0xD500
    m[base + 0x0E] = 0
    m[base + 0x0F] = 0
    m[0xD500] = ptype
    m[base + 1] = state
    m[base + 2] = state
    o.word(0xD516, speed)
    o.word(0xD174, 1000)
    o.word(0xD511, 1100)
    seen, frames, transitions, callbacks = set(), collections.OrderedDict(), set(), []
    for _ in range(3000):
        o.bank(2, 12)
        m[0xD12B] = 12
        o.cpu.ix = base
        o.call(0x64FA)
        st = m[base + 1]
        key = (st, m[base + 6], m[base + 0xE] | m[base + 0xF] << 8, m[base + 7], m[base + 2])
        frames[(m[base + 6], m[base + 0x2C], m[base + 0x2D])] = 1
        cb = m[base + 0xC] | m[base + 0xD] << 8
        if cb not in callbacks:
            callbacks.append(cb)
        if m[base + 2] != m[base + 1]:
            transitions.add(m[base + 2])
            break
        if key in seen:
            break
        seen.add(key)
    return {"frames": list(frames), "transitions": sorted(transitions), "callbacks": callbacks}


def player_extents(rom: bytes) -> dict:
    out = {"evidence": "CONTROLLED ROUTINE RESULT (original animation engine $64FA)",
           "method": "for every player state 0..$33 the state script is run through the real engine with the player slot ($D500); "
                     "$D52C/$D52D are read after each record load. Run-frame selectors see speeds 0, $0100, $0300, $0600 and -$0300."}
    speeds = (0x0000, 0x0100, 0x0300, 0x0600, 0xFD00)
    for ptype, label in ((1, "sonic_type_1"), (2, "type_2")):
        rows = []
        for state in range(0x34):
            frames = collections.OrderedDict()
            trans, cbs = set(), []
            for sp in speeds:
                w = _engine_walk(rom, ptype, state, sp)
                for f in w["frames"]:
                    frames[f] = 1
                trans.update(w["transitions"])
                for c in w["callbacks"]:
                    if c not in cbs:
                        cbs.append(c)
            ext = sorted({(f[1], f[2]) for f in frames})
            rows.append({"state": state, "frames": sorted({f[0] for f in frames}),
                         "extents_x_y": [list(e) for e in ext],
                         "script_requests_state": sorted(trans), "callbacks": [h(c) for c in cbs[:4]]})
        out[label] = rows
    son = {r["state"]: r["extents_x_y"] for r in out["sonic_type_1"]}
    out["sonic_summary"] = {
        "distinct_extent_pairs": sorted({tuple(e) for v in son.values() for e in v}),
        "states_with_8_24_only": [s for s, v in son.items() if v == [[8, 24]]],
        "states_with_other_extents": {str(s): v for s, v in son.items() if v != [[8, 24]]},
    }
    return out


def extent_writers_and_readers(rom: bytes) -> dict:
    """Byte-level proof of who reads/writes $D52C/$D52D."""
    readers, writers = [], []
    for name, pat in (("D52C", b"\x2c\xd5"), ("D52D", b"\x2d\xd5")):
        for m in re.finditer(re.escape(pat), rom):
            o = m.start()
            op = rom[o - 1]
            b, c = cpu_of(o - 1)
            (readers if op == 0x3A else writers).append({"field": name, "opcode": h(op, 2), "bank": h(b, 2), "cpu": h(c)})
    ix_writers = []
    for label, pats in (("IX+$2C", (b"\xdd\x77\x2c", b"\xdd\x36\x2c")), ("IX+$2D", (b"\xdd\x77\x2d", b"\xdd\x36\x2d")),
                        ("IY+$2C", (b"\xfd\x77\x2c", b"\xfd\x36\x2c")), ("IY+$2D", (b"\xfd\x77\x2d", b"\xfd\x36\x2d"))):
        for p in pats:
            for m in re.finditer(re.escape(p), rom):
                b, c = cpu_of(m.start())
                ix_writers.append({"target": label, "bank": h(b, 2), "cpu": h(c), "bytes": p.hex(" ")})
    return {
        "evidence": "BYTE-VERIFIED (opcode scan of the whole ROM)",
        "absolute_reads_of_D52C_D52D": readers,
        "absolute_writes_of_D52C_D52D": writers,
        "index_register_writes_of_extent_fields": ix_writers,
        "conclusion": "$D52C/$D52D are read only by the overlap helpers ($6328 at $6359/$6377/$6398, the unused variant at $643B/$6459/$6478) and by the "
                      "solid helper $5FA0 ($5FE1, $6024, $6053); they are written only by the animation engine ($6595/$659A) for the player slot. "
                      "No player state setter, terrain routine or object routine writes them. The other IX/IY writes ($3266, $1B83, $1BC6, $7A4A4/$7A4A8) "
                      "belong to other objects (HUD/effects and the bank-$1E small projectile).",
    }


# --------------------------------------------------------------------------- #
# 2. overlap helper $6328
# --------------------------------------------------------------------------- #
def model_6328(s: dict) -> dict:
    """Bit-exact reference model of $6328 (outputs: +$20, +$21, $D520, $D521)."""
    out = {"b20": 0, "b21": s["b21"] & 0xF0, "d520": s["d520"], "d521": s["d521"]}
    f3, d503 = s["f3"], s["d503"]
    if f3 & 0x40:
        return out
    if not (f3 & 0x80) and (d503 & 0x40):
        return out
    fail = {"b20": 0, "b21": s["b21"] & 0xF0, "d520": s["d520"], "d521": s["d521"]}
    # horizontal
    px, ox = s["px"] & 0xFFFF, s["ox"] & 0xFFFF
    span = (s["ex"] + s["oex"]) & 0xFF
    hl = (px - ox) & 0xFFFF
    bits = 0
    if px >= ox:                                   # no carry
        if hl >> 8 != 0:
            return fail
        l = hl & 0xFF
        if span < l:
            return fail
        c = (span - l) & 0xFF
        bits |= 4
    else:
        if hl >> 8 != 0xFF:
            return fail
        l = (-(hl & 0xFF)) & 0xFF
        if l == 0 or span < l:
            return fail
        c = (span - l) & 0xFF
        bits |= 8
    # vertical
    py, oy = s["py"] & 0xFFFF, s["oy"] & 0xFFFF
    hl = (py - oy) & 0xFFFF
    if py >= oy:
        if hl >> 8 != 0:
            return fail
        l = hl & 0xFF
        if s["ey"] < l:
            return fail
        lv = (s["ey"] - l) & 0xFF
        bits |= 2
    else:
        if hl >> 8 != 0xFF:
            return fail
        l = (-(hl & 0xFF)) & 0xFF
        if l == 0 or s["oey"] < l:
            return fail
        lv = (s["oey"] - l) & 0xFF
        bits |= 1
    mask = 12 if c < lv else 3
    b21 = bits & mask                               # the old high nibble is cleared by the AND
    b20 = 0 if (d503 & 0x80) else 1
    d520 = s["d520"]
    if not (f3 & 0x80):
        d520 = (((s["ix"] - 0xD500) & 0xFFFF) >> 6 & 0xFF) + 1 & 0xFF
    low = b21 & 15
    cc = 12 if (low & 3) == 0 else 3
    d521 = (s["d521"] & 15) | (((low ^ cc) & 15) << 4)
    return {"b20": b20, "b21": b21, "d520": d520, "d521": d521}


def _overlap_case(rng: random.Random, edge: bool) -> dict:
    ox = rng.choice((0, 5, 300, 1000, 4000, 0xFF00, 0xFFF0, 0xFFFF)) if edge else rng.randrange(256, 4000)
    oy = rng.choice((0, 5, 300, 1000, 0xFF00, 0xFFF0)) if edge else rng.randrange(256, 2000)
    spread = 600 if not edge else 40
    px = (ox + rng.randrange(-spread, spread + 1)) & 0xFFFF
    py = (oy + rng.randrange(-spread, spread + 1)) & 0xFFFF
    if rng.random() < 0.5:                          # bias towards the boundaries
        px = (ox + rng.choice((-1, 0, 1)) * rng.randrange(0, 60) + rng.choice((-1, 0, 1))) & 0xFFFF
        py = (oy + rng.choice((-1, 0, 1)) * rng.randrange(0, 60) + rng.choice((-1, 0, 1))) & 0xFFFF
    ex = rng.choice((0, 1, 8, 9, 12, 255, rng.randrange(0, 60)))
    ey = rng.choice((0, 1, 18, 24, 255, rng.randrange(0, 60)))
    return {"ox": ox, "oy": oy, "px": px, "py": py, "ex": ex, "ey": ey,
            "oex": rng.choice((0, 3, 8, 12, 16, 20, 255, rng.randrange(0, 60))),
            "oey": rng.choice((0, 14, 16, 24, 26, 42, 48, 255, rng.randrange(0, 60))),
            "f3": rng.choice((0x00, 0x00, 0x80, 0x40, 0xC0)), "d503": rng.choice((0x00, 0x02, 0x40, 0x80, 0xC0)),
            "b21": rng.randrange(256), "d521": rng.randrange(256), "d520": rng.randrange(256),
            "ix": rng.choice((0xD540, 0xD580, 0xD700, 0xD9C0))}


def _oracle_for(rom: bytes):
    from oracle import Oracle
    o = Oracle(rom)
    o.bank(2, 0x0C)
    return o


def overlap_grid(rom: bytes, n_random: int = 30000) -> dict:
    o = _oracle_for(rom)
    m = o.mem
    rng = random.Random(0x6328)
    mism, total = [], 0
    by_outcome = collections.Counter()
    cases = [_overlap_case(rng, i % 4 == 0) for i in range(n_random)]
    # structured sweep: the sign/monitor style boxes, every dx/dy in a window
    for ex, ey, oex, oey in ((8, 24, 12, 42), (9, 18, 10, 24), (8, 24, 10, 24), (8, 24, 16, 24)):
        for dx in range(-40, 41):
            for dy in range(-60, 40):
                cases.append({"ox": 1000, "oy": 500, "px": 1000 + dx, "py": 500 + dy, "ex": ex, "ey": ey, "oex": oex,
                              "oey": oey, "f3": 0x80, "d503": 0, "b21": 0x50, "d521": 0x0A, "d520": 0x33, "ix": SLOT})
    for c in cases:
        total += 1
        for k, a in (("ox", SLOT + 0x11), ("oy", SLOT + 0x14)):
            o.word(a, c[k])
        o.word(0xD511, c["px"])
        o.word(0xD514, c["py"])
        m[0xD52C], m[0xD52D] = c["ex"], c["ey"]
        ix = c["ix"]
        m[ix + 0x2C], m[ix + 0x2D] = c["oex"], c["oey"]
        m[ix + 3] = c["f3"]
        m[ix + 0x21] = c["b21"]
        m[ix + 0x20] = 0x77
        m[0xD503] = c["d503"]
        m[0xD521] = c["d521"]
        m[0xD520] = c["d520"]
        if ix != SLOT:
            o.word(ix + 0x11, c["ox"])
            o.word(ix + 0x14, c["oy"])
        o.cpu.ix = ix
        o.call(0x6328)
        got = {"b20": m[ix + 0x20], "b21": m[ix + 0x21], "d520": m[0xD520], "d521": m[0xD521]}
        want = model_6328(dict(c, ix=ix))
        if got != want:
            mism.append({"case": c, "got": got, "want": want})
        by_outcome["contact" if (want["b21"] & 15) else "none"] += 1
    return {"evidence": "CONTROLLED ROUTINE RESULT (original $6328 vs reference model)", "cases_compared": total,
            "random_cases": n_random, "structured_sweep_cases": total - n_random,
            "mismatches": len(mism), "first_mismatches": mism[:3], "contact_cases": by_outcome["contact"],
            "no_contact_cases": by_outcome["none"],
            "outputs_compared": ["+$20", "+$21 (all 8 bits)", "$D520", "$D521"]}


def overlap_spec() -> dict:
    return {
        "evidence": "BYTE-VERIFIED ASSEMBLY + CONTROLLED ROUTINE RESULT (grid in `overlap_grid`)",
        "address": "0x6328 (fixed bank 1, vector $033B); variants: $630B (+ damage request, vector $0434), $640B (no direct caller)",
        "inputs": {"object": "IX: +$11/+$12 X, +$14/+$15 Y (16-bit world anchors), +$2C X extent, +$2D Y extent, +$03 flags",
                   "player": "$D511 X, $D514 Y (16-bit anchors), $D52C X extent, $D52D Y extent, $D503 flags"},
        "gates": ["+$03 bit 6 set: no test", "+$03 bit 7 clear and $D503 bit 6 set: no test",
                  "(the sign, and the boss state 3, set +$03 bit 7 to ignore the player's bit-6 gate)"],
        "rule": {
            "dx": "dx = playerX - objectX as an UNSIGNED 16-bit subtraction. No borrow: need dx <= 255 and dx <= (playerExtX + objectExtX) & $FF. "
                  "Borrow: need objectX - playerX in 1..255 (256 fails because NEG 0 = 0) and objectX - playerX <= (playerExtX + objectExtX) & $FF.",
            "dy": "dy = playerY - objectY, same unsigned scheme. No borrow (player at/below the object anchor): dy <= 255 and dy <= playerExtY ($D52D) ONLY. "
                  "Borrow (player above): objectY - playerY in 1..255 and <= objectExtY (+$2D) ONLY.",
            "edges": "all comparisons are inclusive (<=). A player exactly at dx = 0 or dy = 0 takes the no-borrow branch.",
            "interval_form": "equivalent to overlap of the closed intervals player X [px-ExtX, px+ExtX] x Y [py-ExtY, py] with "
                             "object X [ox-oExtX, ox+oExtX] x Y [oy-oExtY, oy]; i.e. both boxes hang ABOVE their anchors, the player box is 2*ExtX+1 wide and "
                             "ExtY+1 tall, the anchor is the bottom edge of both boxes",
            "wrap": "sums are 8-bit: ExtX + objectExtX wraps modulo 256 (no real extent reaches that); any |d| >= 256 fails; positions compare as unsigned 16-bit, so a "
                    "wrapped world coordinate near $FFFF/0 behaves as a huge distance",
        },
        "outputs": {
            "+$20": "1 when $D503 bit 7 is clear and the test passed, else 0 (always cleared at entry)",
            "+$21": "low nibble: bit0 player above, bit1 player below, bit2 player right (dx >= 0), bit3 player left; on success only the axis of minimum "
                    "penetration survives (horizontal if hPen < vPen, vertical on ties) and the HIGH nibble is cleared; on failure the high nibble is kept and the low nibble is 0",
            "$D520": "slot id ((IX - $D500) >> 6) + 1 when +$03 bit 7 is clear and the test passed",
            "$D521": "low nibble kept; high nibble = (+$21 low nibble) XOR (12 if the surviving axis is horizontal else 3): the mirrored contact from the object's side",
            "return_convention": "none: callers test (IX+$21) & $0F. Registers are not a convention (A holds the last byte written).",
        },
        "penetration": "hPen = (playerExtX + objectExtX) - |dx|; vPen = (playerExtY - dy) for dy >= 0 else (objectExtY - |dy|). Bit choice: horizontal iff hPen < vPen.",
    }


# --------------------------------------------------------------------------- #
# 3. solid helper $5FA0
# --------------------------------------------------------------------------- #
def model_5fa0(s: dict) -> dict:
    """Reference model of $5FA0 (overlap, then a one-bit dispatch that moves only the player's position)."""
    ov = model_6328(s)
    out = dict(ov, px=s["px"] & 0xFFFF, py=s["py"] & 0xFFFF)
    low = ov["b21"] & 15
    d523 = s["d523"]
    if low == 0:
        return out
    if low == 1:                                    # player above: stand on top, Y = objY - objExtY
        if not d523 & 1:
            out["py"] = (s["oy"] - s["oey"]) & 0xFFFF
    elif low == 2:                                  # player below: Y = objY + playerExtY
        if not d523 & 2:
            out["py"] = (s["oy"] + s["ey"]) & 0xFFFF
    elif low == 4:                                  # player right of the object
        if not d523 & 4:
            if ((s["camx"] + 0xE0) & 0xFFFF) >= (s["px"] & 0xFFFF):
                out["px"] = (s["ox"] + s["oex"] + s["ex"]) & 0xFFFF
    elif low == 8:                                  # player left of the object
        if not d523 & 8:
            if ((s["camx"] + 0x20) & 0xFFFF) < (s["px"] & 0xFFFF):
                out["px"] = (s["ox"] - (s["oex"] + s["ex"])) & 0xFFFF
    return out


def solid_grid(rom: bytes, n_random: int = 20000) -> dict:
    o = _oracle_for(rom)
    m = o.mem
    rng = random.Random(0x5FA0)
    mism, total = [], 0
    stats = collections.Counter()
    cases = []
    for i in range(n_random):
        c = _overlap_case(rng, i % 5 == 0)
        c.update(ix=rng.choice((0xD540, 0xD700, 0xD9C0)), d523=rng.randrange(16), camx=rng.choice((0, 100, 900, 1000, 4000, rng.randrange(0, 4400))),
                 f3=rng.choice((0x00, 0x00, 0x80)), d503=rng.choice((0x00, 0x02, 0x80)))
        c["px"] = (c["ox"] + rng.randrange(-70, 71)) & 0xFFFF
        c["py"] = (c["oy"] + rng.randrange(-70, 71)) & 0xFFFF
        c["ex"], c["ey"] = rng.choice(((8, 24), (9, 24), (9, 18), (12, 32), (0, 0))), None
        c["ex"], c["ey"] = c["ex"]
        c["oex"], c["oey"] = rng.choice(((10, 24), (16, 16), (16, 24), (20, 48), (9, 14), (11, 26)))
        cases.append(c)
    for c in cases:
        total += 1
        ix = c["ix"]
        m[ix + 0x11], m[ix + 0x12] = c["ox"] & 255, c["ox"] >> 8
        m[ix + 0x14], m[ix + 0x15] = c["oy"] & 255, c["oy"] >> 8
        o.word(0xD511, c["px"])
        o.word(0xD514, c["py"])
        m[0xD52C], m[0xD52D] = c["ex"], c["ey"]
        m[ix + 0x2C], m[ix + 0x2D] = c["oex"], c["oey"]
        m[ix + 3] = c["f3"]
        m[ix + 0x21] = c["b21"]
        m[0xD503] = c["d503"]
        m[0xD521] = c["d521"]
        m[0xD520] = c["d520"]
        m[0xD523] = c["d523"]
        o.word(0xD174, c["camx"])
        vx, vy = rng.randrange(0x10000), rng.randrange(0x10000)
        o.word(0xD516, vx)
        o.word(0xD518, vy)
        m[0xD502], m[0xD501], m[0xD522] = 5, 5, 3
        o.cpu.ix = ix
        o.call(0x5FA0)
        got = {"b20": m[ix + 0x20], "b21": m[ix + 0x21], "d520": m[0xD520], "d521": m[0xD521],
               "px": o.word(0xD511), "py": o.word(0xD514)}
        want = model_5fa0(dict(c))
        unchanged = (o.word(0xD516) == vx and o.word(0xD518) == vy and m[0xD502] == 5 and m[0xD501] == 5 and m[0xD522] == 3)
        if got != want or not unchanged:
            mism.append({"case": c, "got": got, "want": want, "velocity_or_state_changed": not unchanged})
        low = want["b21"] & 15
        stats[{0: "no_contact", 1: "player_above", 2: "player_below", 4: "player_right", 8: "player_left"}.get(low, "other")] += 1
        if low and (got["px"] != (c["px"] & 0xFFFF) or got["py"] != (c["py"] & 0xFFFF)):
            stats["position_pushed"] += 1
        elif low:
            stats["position_not_pushed"] += 1
    return {"evidence": "CONTROLLED ROUTINE RESULT (original $5FA0 vs reference model)", "cases_compared": total,
            "mismatches": len(mism), "first_mismatches": mism[:3], "classification_counts": dict(sorted(stats.items())),
            "also_verified_per_case": "player X/Y velocity ($D516/$D518), player current/requested state ($D501/$D502) and floor flags ($D522) are never modified"}


def solid_spec() -> dict:
    return {
        "evidence": "BYTE-VERIFIED ASSEMBLY + CONTROLLED ROUTINE RESULT (grid in `solid_grid`)",
        "address": "0x5FA0 (fixed bank 1, vector $034D): CALL $6328, then a 16-entry jump table at $5FB9 indexed by the +$21 low nibble",
        "dispatch": {"nibble 1 (player above)": "$5FF1", "nibble 2 (player below)": "$5FDA", "nibble 4 (player right)": "$6038",
                     "nibble 8 (player left)": "$6009", "0 / combined bits": "RET (the overlap helper leaves exactly one bit, so combinations do not occur)"},
        "actions": {
            "player_above": "unless $D523 bit 0 is set: playerY = objectY - objectExtY (+$2D): the player's anchor is placed ON the object's top edge",
            "player_below": "unless $D523 bit 1 is set: playerY = objectY + playerExtY ($D52D)",
            "player_right": "unless $D523 bit 2 is set and only while playerX <= cameraX + $E0: playerX = objectX + objectExtX + playerExtX",
            "player_left": "unless $D523 bit 3 is set and only while playerX > cameraX + $20: playerX = objectX - (objectExtX + playerExtX)",
        },
        "consumes": {"player_extents": "$D52C in both side pushes, $D52D only in the 'below' push (and, through $6328, in the dy >= 0 test)",
                     "object_extents": "+$2C in both side pushes, +$2D in the 'above' push (and in the dy < 0 test)",
                     "camera": "$D174 (side pushes are suppressed near the screen edges)",
                     "flags": "$D523 (combined player contact flags: a push is skipped when the player is already blocked on that side)"},
        "tie_behavior": "inherited from $6328: horizontal wins only when hPen < vPen; an exact tie selects the vertical axis",
        "velocity_and_state": "NONE. $5FA0 writes no velocity, no player state, no floor flag and does not set the player's grounded bit; callers (type $10 at $A177) "
                              "handle bounces, rewards and state themselves. Standing on a solid object therefore depends on the caller and on the next terrain update.",
        "also_from_6328": "+$20, +$21, $D520 and $D521 (see overlap_spec)",
    }


# --------------------------------------------------------------------------- #
# 4. per-type helper matrix (recursive descent from every state callback)
# --------------------------------------------------------------------------- #
HELPERS = {0x033B: "overlap_6328", 0x034D: "solid_5FA0", 0x0434: "overlap_damage_630B", 0x0323: "attack_check_5F3D",
           0x033E: "destroy_convert_5F54", 0x035F: "vertical_spring_setter_5F17", 0x0365: "set_position_5F27", 0x03F5: "level_complete_4892",
           0x0383: "proximity_x_61A5", 0x0386: "proximity_y_61B1", 0x0389: "proximity_61BB", 0x037D: "player_type_fix_613C",
           0x03F2: "reward_3104", 0x0347: "ring_counter_3138", 0x0380: "ring_pickup_box_617E", 0x0338: "move_60FB",
           0x0350: "accelerate_5F84", 0x0353: "camera_left_lock", 0x0359: "camera_pan", 0x032C: "spawn_child_pool", 0x0329: "spawn_child_5EE1"}


def _anim_walk(rom: bytes, t: int) -> tuple:
    from oracle import Oracle
    bank = 0x0C if t < 0x26 else 0x1E
    tbl = u16(rom, 0x65BA + (t - 1) * 2)
    off = bank * 0x4000 + tbl - 0x8000
    n = (u16(rom, off) - tbl) // 2
    res = {}
    for s in range(n):
        o = Oracle(rom)
        m = o.mem
        m[SLOT:SLOT + 0x40] = bytes(0x40)
        m[SLOT], m[SLOT + 1], m[SLOT + 2], m[SLOT + 4] = t, s, s, 0x40
        o.word(0xD174, 1000)
        o.word(0xD176, 400)
        cbs, exts, frames, seen = [], set(), set(), set()
        for _ in range(2000):
            o.bank(2, bank)
            m[0xD12B] = bank
            o.cpu.ix = SLOT
            try:
                o.call(0x64FA)
            except Exception:
                break
            cb = m[SLOT + 0xC] | m[SLOT + 0xD] << 8
            key = (m[SLOT + 1], m[SLOT + 6], m[SLOT + 0xE] | m[SLOT + 0xF] << 8, m[SLOT + 7], m[SLOT + 2])
            if cb not in cbs:
                cbs.append(cb)
            exts.add((m[SLOT + 0x2C], m[SLOT + 0x2D]))
            frames.add(m[SLOT + 6])
            if key in seen or (m[SLOT + 2] != s and m[SLOT + 2] != m[SLOT + 1]):
                break
            seen.add(key)
        res[s] = {"callbacks": cbs, "extents": sorted(exts), "frames": sorted(frames)}
    return bank, res


def _reach(rom: bytes, bank: int, entries: list) -> tuple:
    from z80dis import z80
    img = rom[0:0x8000] + rom[bank * 0x4000:(bank + 1) * 0x4000]
    seen, stack, calls = set(), list(entries), collections.Counter()
    ram = collections.defaultdict(set)
    watch = {0xD3B0, 0xD3A3, 0xD29A, 0xD29D, 0xD532, 0xD44C, 0xD448, 0xD3B3}
    while stack:
        pc = stack.pop()
        while 0x8000 <= pc < 0xC000 and pc not in seen:
            seen.add(pc)
            d = z80.decode(img[pc:pc + 4], pc)
            s = z80.disasm(d)
            ln = d.len or 1
            for a in re.findall(r"\(0x(d[0-9a-f]{3})\)", s):
                addr = int(a, 16)
                if 0xD500 <= addr < 0xD540 or addr in watch:
                    ram[addr].add("W" if s.startswith("LD (") else "R")
            mm = re.match(r"(CALL|JP|JR|DJNZ)\s+(?:[a-z]+,)?(0x[0-9a-f]+)$", s)
            if mm:
                op, tgt = mm.group(1), int(mm.group(2), 16)
                if tgt >= 0x8000:
                    stack.append(tgt)
                else:
                    calls[tgt] += 1
                if op in ("JP", "JR") and not re.match(r"(JP|JR)\s+[a-z]+,", s):
                    break
            elif s == "RET" or s.startswith("JP (HL)") or s.startswith("JP (IX"):
                break
            pc += ln
    return seen, calls, ram


TYPE_LIST = (0x09, 0x0A, 0x0F, 0x10, 0x12, 0x18, 0x19, 0x1B, 0x21, 0x26, 0x27, 0x28, 0x34, 0x50)


def helper_matrix(rom: bytes) -> dict:
    out = {"evidence": "SOURCE-TRACED BEHAVIOR (recursive descent over the real state-script callbacks; the animation engine is executed to obtain them)",
           "helper_names": {h(k): v for k, v in sorted(HELPERS.items())}, "types": {}}
    for t in TYPE_LIST:
        bank, walk = _anim_walk(rom, t)
        cbs = sorted({c for v in walk.values() for c in v["callbacks"] if c >= 0x8000})
        seen, calls, ram = _reach(rom, bank, cbs)
        out["types"][h(t, 2)] = {
            "bank": h(bank, 2), "callbacks": [h(c) for c in cbs],
            "reachable_instructions": len(seen),
            "helpers": {HELPERS.get(k, h(k)): v for k, v in sorted(calls.items()) if k in HELPERS},
            "player_and_related_ram": {h(k): "".join(sorted(v)) for k, v in sorted(ram.items())},
            "extents_by_state": {str(s): v["extents"] for s, v in walk.items()},
        }
    return out


# --------------------------------------------------------------------------- #
# 5. real-callback box sweeps
# --------------------------------------------------------------------------- #
def _make_obj(rom, t, state, ox=1000, oy=500, flags4=0x10):
    from oracle import Oracle
    o = Oracle(rom)
    m = o.mem
    bank = 0x0C if t < 0x26 else 0x1E
    m[SLOT:SLOT + 0x40] = bytes(0x40)
    m[SLOT], m[SLOT + 1], m[SLOT + 2], m[SLOT + 4] = t, state, state, flags4
    o.word(SLOT + 0x11, ox)
    o.word(SLOT + 0x14, oy)
    o.word(0xD174, ox - 128)
    o.word(0xD176, oy - 96)
    m[0xD500] = 1
    m[0xD52C], m[0xD52D] = 8, 24
    o.bank(2, bank)
    m[0xD12B] = bank
    o.cpu.ix = SLOT
    o.call(0x64FA)
    return o, bank


def _sweep(rom, t, state, cb, rng=(-45, 45, -70, 40), pre=None):
    o, bank = _make_obj(rom, t, state)
    m = o.mem
    oex, oey = m[SLOT + 0x2C], m[SLOT + 0x2D]
    snap = bytes(m[0xC000:0xE000])
    hits = set()
    for dy in range(rng[2], rng[3] + 1):
        for dx in range(rng[0], rng[1] + 1):
            m[0xC000:0xE000] = snap
            o.word(0xD511, 1000 + dx)
            o.word(0xD514, 500 + dy)
            o.word(0xD516, 0x0400)
            m[0xD502], m[0xD503] = 2, 0
            if pre:
                pre(o, m)
            o.bank(2, bank)
            m[0xD12B] = bank
            o.cpu.ix = SLOT
            o.call(cb)
            if m[SLOT + 0x21] & 15:
                hits.add((dx, dy))
    return (oex, oey), hits


def callback_sweeps(rom: bytes) -> dict:
    rows = []
    cases = (("0x10", 0x10, 2, 0xA16C, "monitor, solid via $5FA0"), ("0x1B", 0x1B, 2, 0xACC3, "spike, overlap via $ACFD"),
             ("0x27", 0x27, 1, 0x89AC, "object $27 state 1"), ("0x27", 0x27, 2, 0x89DF, "object $27 state 2"),
             ("0x28", 0x28, 5, 0x879A, "platform state 5"), ("0x28", 0x28, 2, 0x86A1, "platform state 2"),
             ("0x21", 0x21, 3, 0xB2AF, "enemy contact routine $B2AF"))
    for name, t, st, cb, note in cases:
        (oex, oey), hits = _sweep(rom, t, st, cb)
        xs = [a for a, b in hits]
        ys = [b for a, b in hits]
        full = bool(hits) and len(hits) == (max(xs) - min(xs) + 1) * (max(ys) - min(ys) + 1)
        expect = {(dx, dy) for dx in range(-45, 46) for dy in range(-70, 41)
                  if _pred(dx, dy, 8, 24, oex, oey)}
        rows.append({"type": name, "state": st, "callback": h(cb), "note": note, "object_extents": [oex, oey], "player_extents": [8, 24],
                     "contact_dx": [min(xs), max(xs)] if hits else None, "contact_dy": [min(ys), max(ys)] if hits else None,
                     "rectangular": full, "cells": len(hits),
                     "cells_matching_formula": len(hits & expect), "cells_only_in_formula": len(expect - hits), "cells_only_in_callback": len(hits - expect)})
    return {"evidence": "CONTROLLED ROUTINE RESULT (real callbacks, Sonic extents (8,24), velocity set so the object does not move first)",
            "rows": rows,
            "note": "Rows whose callback first moves the object (type $28) differ from the formula by that one-pixel move; all others match exactly."}


def _pred(dx, dy, ex, ey, oex, oey):
    span = (ex + oex) & 0xFF
    h_ = (dx >= 0 and dx <= 255 and dx <= span) or (dx < 0 and dx > -256 and -dx <= span)
    v_ = (dy >= 0 and dy <= 255 and dy <= ey) or (dy < 0 and dy > -256 and -dy <= oey)
    return h_ and v_


def spring_26_sweep(rom: bytes) -> dict:
    """Type $26 state 7 ($82AF): no overlap helper; proximity |dx| < 12 and a 6-pixel Y window."""
    o, bank = _make_obj(rom, 0x26, 7)
    m = o.mem
    snap = bytes(m[0xC000:0xE000])
    hits = set()
    for dy in range(-60, 20):
        for dx in range(-20, 21):
            m[0xC000:0xE000] = snap
            o.word(0xD511, 1000 + dx)
            o.word(0xD514, 500 + dy)
            m[0xD519] = 0
            m[0xD522] = 2
            m[0xD502] = 2
            o.bank(2, bank)
            m[0xD12B] = bank
            o.cpu.ix = SLOT
            o.call(0x82AF)
            if m[SLOT + 2] != 7:
                hits.add((dx, dy))
    xs = [a for a, b in hits]
    ys = [b for a, b in hits]
    gates = {}
    for name, setup in (("baseline", lambda: None), ("player_moving_up_D519_bit7", lambda: m.__setitem__(0xD519, 0xFF)),
                        ("no_floor_contact_D522_bit1", lambda: m.__setitem__(0xD522, 0)),
                        ("requested_state_21", lambda: m.__setitem__(0xD502, 0x21)),
                        ("object_offscreen_bit6", lambda: m.__setitem__(SLOT + 4, 0x50))):
        m[0xC000:0xE000] = snap
        o.word(0xD511, 1000)
        o.word(0xD514, 500 - 30)
        m[0xD519], m[0xD522], m[0xD502] = 0, 2, 2
        setup()
        o.bank(2, bank)
        m[0xD12B] = bank
        o.cpu.ix = SLOT
        o.call(0x82AF)
        gates[name] = m[SLOT + 2] != 7
    return {"evidence": "CONTROLLED ROUTINE RESULT (original $82AF)", "contact_dx": [min(xs), max(xs)], "contact_dy_relative_to_object_Y": [min(ys), max(ys)],
            "cells": len(hits), "rectangular": len(hits) == (max(xs) - min(xs) + 1) * (max(ys) - min(ys) + 1),
            "gates_at_dx0_dy_minus_30": gates,
            "rule": "after $82AF requires: +$04 bit 6 clear, $D519 bit 7 clear (not moving up), $D522 bit 1 set (floor contact), requested state != $21; "
                    "|playerX - objectX| < 12 (STRICT, vector $0383 -> $61A5 with BC = 12); "
                    "0 <= (objectY - 28) - playerY < 6, i.e. playerY in [objectY-33, objectY-28]. Object X/Y are the runtime anchor (+$11/+$14)."}


def proximity_spec(rom: bytes) -> dict:
    from oracle import Oracle
    o = Oracle(rom)
    m = o.mem
    rows = []
    for dist in (10, 11, 12, 13, -10, -11, -12, -13):
        m[SLOT + 0x11], m[SLOT + 0x12] = 1000 & 255, 1000 >> 8
        o.word(0xD511, 1000 + dist)
        o.cpu.ix = SLOT
        o.cpu.bc = 12
        o.call(0x61A5, bc=12)
        rows.append({"dx": dist, "result_A": m_a(o)})
    ring = []
    for dx, dy in ((11, 0), (12, 0), (0, 11), (0, 12), (11, 11), (-11, -11), (-12, 0), (0, -12)):
        o.word(SLOT + 0x11, 1000)
        o.word(SLOT + 0x14, 500)
        o.word(0xD511, 1000 + dx)
        o.word(0xD514, 500 + dy)
        o.cpu.ix = SLOT
        o.call(0x617E)
        ring.append({"dx": dx, "dy": dy, "hit": m_a(o) == 0xFF})
    return {"evidence": "CONTROLLED ROUTINE RESULT", "x_proximity_61A5_bc_12": rows, "ring_box_617E": ring,
            "rule": "$61A5/$61B1/$61BB: hit (A = $FF) iff |d| < BC (strict). $617E: |dx| < 12 and |dy| < 12 on the two anchors, no extents."}


def m_a(o) -> int:
    return o.cpu.a


# --------------------------------------------------------------------------- #
# 6. terrain constants
# --------------------------------------------------------------------------- #
def terrain_constants(rom: bytes) -> dict:
    off = 0x3686
    code = rom[off:off + 0x40]
    writes = []
    for name, pat in (("D498", b"\x98\xd4"), ("D49A", b"\x9a\xd4"), ("D49C", b"\x9c\xd4"), ("D49E", b"\x9e\xd4")):
        for m in re.finditer(re.escape(pat), rom):
            o = m.start()
            b, c = cpu_of(o - 1)
            writes.append({"field": name, "opcode_byte_before": h(rom[o - 1], 2), "bank": h(b, 2), "cpu": h(c)})
    return {
        "evidence": "BYTE-VERIFIED ASSEMBLY ($3686 side-sensor initializer) + opcode scan",
        "side_probe_offsets": {"left_x": -9, "right_x": 9, "y_both": -12,
                              "bytes_at_3686": code[:0x3F].hex(" "),
                              "rule": "$D498/$D49A (left X/Y) = ($FFF7, $FFF4), $D49C/$D49E (right X/Y) = ($0009, $FFF4); the ground/side lookup adds +18 to the probe Y "
                                      "($7666 caller), so the side probes sample at anchorY + 6 and anchorX -9 / +9"},
        "floor_anchor_correction": "the terrain lookup used for the floor adds +18 to the anchor Y (docs/ram.md $D35A); this constant is independent of $D52D",
        "state_dependence": "no state-dependent side-probe values exist: the only writes of $D498..$D49E are the initializer ($3686, for both player types) and "
                            "the Y-offset reset at $3F50/$3F54 (value $FFF4); $7212/$716D only read them",
        "probe_field_references": writes,
        "terrain_never_reads_extents": "see extent_fields.absolute_reads_of_D52C_D52D: no terrain routine reads $D52C/$D52D",
        "layout_ring_probe": {"evidence": "SOURCE-TRACED (asm/recovered/layout_ring_handler.asm $753E)",
                              "rule": "terrain-ring pickup samples one terrain cell at player X + 0 and Y - 26 (Y - 16 when the animation timer +$07 bit 0 is set) through $7725; "
                                      "it does not use $D52C/$D52D or any object box"},
        "placed_rings_type_09": "type $09 uses the $617E box: |dx| < 12 and |dy| < 12 between the two anchors (strict), no extents",
    }


# --------------------------------------------------------------------------- #
# 7. emulated confirmation of Sonic's extents during real play
# --------------------------------------------------------------------------- #
def emulated_extents(rom: bytes, frames: int = 8000) -> dict:
    from sms_frame_harness import SMS, BTN_1, BTN_2, BTN_RIGHT, BTN_LEFT, BTN_DOWN, BTN_UP
    s = SMS(rom)
    st = {"done": False}
    s.add_pc_hook(0x07D5, lambda mm: (mm._write(0xD297, 0), mm._write(0xD298, 0)))

    def start(mm):
        if mm.frame > 300:
            st["done"] = True
    s.add_pc_hook(0x4E97, start)
    f = 0
    while True:
        if f < 250:
            s.pad = 0
        elif f < 700:
            s.pad = BTN_1 if f % 40 < 3 else 0
        elif not st["done"]:
            s.pad = (BTN_1 | BTN_2) if f % 60 < 10 else 0
        else:
            break
        s.run_frame()
        f += 1
        if f > 4000:
            raise RuntimeError("no gameplay")
    rnd = random.Random(1)
    obs = collections.defaultdict(set)
    m = s.mem
    pad = 0
    for i in range(frames):
        if i % 20 == 0:
            pad = rnd.choice([BTN_RIGHT, BTN_RIGHT, BTN_RIGHT | BTN_2, BTN_RIGHT | BTN_DOWN, BTN_LEFT, BTN_DOWN, BTN_2, BTN_RIGHT | BTN_1, BTN_UP, 0])
        s.pad = pad
        s.run_frame()
        obs[m[0xD501]].add((m[0xD52C], m[0xD52D]))
        if (m[0xD293] & 0x3F) and m[0xD293] != 0x40:
            m[0xD293] = 0x40
    return {"evidence": "EMULATED ORIGINAL FRAME", "frames": frames, "seed": 1,
            "method": "THZ1 from the start, pseudo-random input every 20 frames; ($D501, $D52C, $D52D) sampled after every frame",
            "observed_by_current_state": {h(k, 2): [list(e) for e in sorted(v)] for k, v in sorted(obs.items())}}


# --------------------------------------------------------------------------- #
# 8. assumption audit (static records; values read from the repositories)
# --------------------------------------------------------------------------- #
def assumption_audit() -> list:
    R = "research"
    P = "poc"
    return [
        # research repository
        {"where": "tools/thz1_object_10.py:200-201 and overlap_contact() defaults", "repo": R, "assumed": "player extents (9,18)", "rom": "(8,24)",
         "class": "TEST-ONLY", "effect": "cached type-$10 boundary fixtures: right edge 19 -> really 18; bottom edge 18 -> really 24 (top edge 24 unchanged)",
         "evidence": "CONTROLLED (collision_geometry.solid_grid, callback_sweeps '0x10')"},
        {"where": "data/rom-cache/thz1/object-10.json overlap_boundaries (horizontal 18/19/20, bottom 17/18/19)", "repo": R, "assumed": "derived from (9,18)",
         "rom": "contact at right <= 18 and bottom <= 24", "class": "TEST-ONLY", "effect": "the recorded 'no contact at 19 right' and 'no contact at 19 bottom' are wrong for Sonic",
         "evidence": "same"},
        {"where": "docs/object-10.md (overlap/solid description)", "repo": R, "assumed": "strict-overlap boundary values of the (9,18) fixtures", "rom": "see above",
         "class": "TEST-ONLY", "effect": "documentation numbers only", "evidence": "same"},
        {"where": "tools/thz1_object_21.py:189-190", "repo": R, "assumed": "(9,18)", "rom": "(8,24)", "class": "TEST-ONLY",
         "effect": "fixtures sit at dx = 0 and |dy| <= 4 (inside both boxes); results unchanged. Box edges were not exercised.",
         "evidence": "CONTROLLED (callback_sweeps '0x21')"},
        {"where": "tools/thz1_object_27.py:255-256", "repo": R, "assumed": "(9,18) for $27 contact", "rom": "(8,24)", "class": "TEST-ONLY",
         "effect": "fixtures at dx = dy = 0; results unchanged. Proximity/removal fixtures use no extents.", "evidence": "CONTROLLED (callback_sweeps '0x27')"},
        {"where": "tools/object_50.py:652 and contact matrix", "repo": R, "assumed": "(9,18) 'fixture values'", "rom": "(8,24)", "class": "TEST-ONLY",
         "effect": "all matrix cases (dx +-26, dy +10 / -40) are inside both boxes; results unchanged; the documented geometry sentence is wrong",
         "evidence": "derived: boss extents (20,48)"},
        {"where": "tools/player_state_11.py:23,49", "repo": R, "assumed": "(9,18)", "rom": "(8,24)", "class": "TEST-ONLY",
         "effect": "player-state-$11 fixtures use the extents only as inputs to the shared helpers", "evidence": "CONTROLLED"},
        {"where": "tools/thz2_thz3_object_deltas.py:94-95", "repo": R, "assumed": "(9,18)", "rom": "(8,24)", "class": "TEST-ONLY",
         "effect": "delta fixtures; same reasoning", "evidence": "CONTROLLED"},
        {"where": "docs/object-50.md section 8 ('contact extents X 20, Y 48; player extents X 9, Y 18')", "repo": R, "assumed": "(9,18)", "rom": "(8,24)", "class": "TEST-ONLY",
         "effect": "documentation", "evidence": "CONTROLLED"},
        # POC repository (read-only)
        {"where": "SCR_chaos_adapter.gml SCR_chaos_object_spring_contact: abs(player.x - trigger_x) <= 12", "repo": P, "assumed": "inclusive 12",
         "rom": "|dx| < 12 (strict), i.e. <= 11 ($82AF via $61A5, BC = 12)", "class": "EDGE",
         "effect": "a player exactly 12 px from the concealed spring triggers in the POC but not in the original",
         "evidence": "CONTROLLED (spring_26_sweep)"},
        {"where": "SCR_chaos_object_spring_contact: no floor-contact test", "repo": P, "assumed": "trigger in the Y window regardless of floor contact",
         "rom": "requires $D522 bit 1 (floor), not moving up, requested state != $21", "class": "EDGE",
         "effect": "an airborne player crossing the 6-pixel window (anchor 28..33 above the spring anchor) launches the POC spring but not the original",
         "evidence": "CONTROLLED (spring_26_sweep gates)"},
        {"where": "SCR_chaos_object_spring_contact: foot = chaosCore.yu/256 + 18 in [layoutY-3, layoutY+2]", "repo": P, "assumed": "6-pixel window expressed in foot coordinates",
         "rom": "playerY anchor in [objectY-33, objectY-28] where objectY is the runtime object Y", "class": "NOT A BUG (window width and +18 anchor match; offset from layoutY not re-derived here)",
         "effect": "window width 6 matches", "evidence": "CONTROLLED"},
        {"where": "SCR_chaos_spike_step: player bbox vs spike x +-16 and y range", "repo": P, "assumed": "GameMaker mask bbox (11 x 31 px, x -4..+6, y -12..+18 in ROM anchor coordinates) against +-16 / visible height",
         "rom": "overlap with spike extents (16,24): |dx| <= 24, -24 <= dy <= 24 (relative to the moving spike anchor), plus cooldown and downward-velocity gates", "class": "EDGE",
         "effect": "POC horizontal window -22..+20 vs ROM -24..+24; vertical window differs by the mask placement",
         "evidence": "POC SOURCE (READ-ONLY) + CONTROLLED"},
        {"where": "SCR_chaos_platform_overlap: bbox_right >= x-16 and bbox_left < x+16", "repo": P, "assumed": "mask width 11, platform +-16",
         "rom": "type $28 overlap extents (16,16): |dx| <= 24 for Sonic", "class": "EDGE",
         "effect": "the POC platform support interval is narrower than the original landing interval (POC -22..+15 vs ROM -24..+24 in anchor coordinates)",
         "evidence": "POC SOURCE (READ-ONLY) + CONTROLLED"},
        {"where": "OBJ_ring Step_0: place_meeting(x, y, OBJ_player)", "repo": P, "assumed": "mask overlap (11 x 31 player mask vs ring sprite mask)",
         "rom": "placed rings: |dx| < 12 and |dy| < 12 between anchors ($617E); layout rings: terrain probe at (0, -26/-16)", "class": "CRITICAL",
         "effect": "ring pickup reach differs in every direction; the POC reach depends on sprite masks, the ROM reach is a 23 x 23 anchor box",
         "evidence": "POC SOURCE (READ-ONLY) + CONTROLLED (proximity_spec)"},
        {"where": "SCR_monitor_collisions / OBJ_monitor_* Collision_OBJ_player (solid = true, destroy on jump/spin)", "repo": P, "assumed": "GameMaker solid collision with sprite masks; destroy on any overlap while jumping/spinning",
         "rom": "type $10: solid helper $5FA0 (extents (8+10, 24) box) then attack/velocity gates: top hit needs downward Y speed and requested state not in {$0F,$10,$15,$1A}; "
                "bottom hit launches the monitor; side hit needs downward speed",
         "class": "CRITICAL", "effect": "which side/velocity breaks a monitor, and the solid push positions, come from different rules",
         "evidence": "SOURCE-TRACED ($A16C) + CONTROLLED (solid_grid)"},
        {"where": "player mask SPR_player_mask (bbox x 16..26, y 3..33, origin (20,20)) and chaosAnchorOffset", "repo": P,
         "assumed": "one fixed 11 x 31 mask for every player state", "rom": "ROM extents are (8,24) in every Sonic state (state $0F: 9,24), equivalent to a 17-wide box hanging 24 above the anchor",
         "class": "NOT A BUG (intentional adapter)", "effect": "a constant mask is consistent with the constant ROM extents; only its numeric size and offset differ",
         "evidence": "POC SOURCE (READ-ONLY) + CONTROLLED"},
        {"where": "POC terrain probes (SCR_chaos_core SCR_cc_lookup +18, side sensors)", "repo": P, "assumed": "anchor + 18 foot probe; +-9 side probes",
         "rom": "$D35A +18 and side probes (-9,-12)/(+9,-12) (+18 added): constants independent of extents", "class": "NOT A BUG",
         "effect": "none found", "evidence": "BYTE-VERIFIED ($3686)"},
        {"where": "OBJ_chaos_object_27 (parent OBJ_badniks; Step_0 only moves/animates; contact comes from the generic badnik collision and SCR_chaos_sample_damage)", "repo": P,
         "assumed": "GameMaker mask collision with SPR_chaos_object_27", "rom": "type $27: overlap $6328 with extents (9,14) (x +-17, y -14..+24 for Sonic), then attack check $5F3D "
                                                                    "($D503 bit 1 or $D532 == 6 converts the object, otherwise no damage request is issued by the object)",
         "class": "EDGE", "effect": "contact reach and the damage/attack decision use different rules; the ROM $27 callback itself never writes the damage request (research: docs/object-27.md)",
         "evidence": "POC SOURCE (READ-ONLY) + CONTROLLED (callback_sweeps '0x27')"},
        {"where": "type $21 enemy", "repo": P, "assumed": "not implemented in the POC (no OBJ_chaos_object_21)", "rom": "$B2AF: overlap (11,26): x +-19, y -26..+24; top contact bounces ($5F17), attack/power-up converts, else damage",
         "class": "NOT A BUG", "effect": "nothing to compare yet", "evidence": "CONTROLLED (callback_sweeps '0x21')"},
        {"where": "POC goal sign geometry (x >= signX + 10, y > signY - 108)", "repo": P, "assumed": "adapter constants", "rom": "see docs/object-18-act-clear.md",
         "class": "CRITICAL", "effect": "trigger region differs (one-sided, open-ended, no movement gate)", "evidence": "CONTROLLED (previous task)"},
    ]


# --------------------------------------------------------------------------- #
# build
# --------------------------------------------------------------------------- #
def poc_player_mask() -> dict:
    """Numbers read from the POC project (SPR_player_mask.yy and SCR_chaos_adapter.gml); derivation only, nothing executed."""
    left, right, top, bottom, ox, oy = 16, 26, 3, 33, 20, 20
    anchor_offset = 18 - (bottom - oy)
    return {
        "evidence": "POC SOURCE (READ-ONLY)",
        "poc_commit": "a3b0382 (SonicChaos_Act1_POC_17_4)",
        "sprite": {"name": "SPR_player_mask", "bbox_left": left, "bbox_right": right, "bbox_top": top, "bbox_bottom": bottom, "origin": [ox, oy],
                   "used_by": "OBJ_player_char, OBJ_player_char_spin and the other player objects (one constant mask)"},
        "chaosAnchorOffset": anchor_offset,
        "formula": "chaosAnchorOffset = 18 - (bbox_bottom - yorigin); ROM anchor Y = POC y - chaosAnchorOffset; foot = ROM anchor + 18 = bbox_bottom",
        "mask_relative_to_poc_position": {"x": [left - ox, right - ox], "y": [top - oy, bottom - oy]},
        "mask_relative_to_rom_anchor": {"x": [left - ox, right - ox], "y": [top - oy + anchor_offset, bottom - oy + anchor_offset]},
        "rom_overlap_box_relative_to_rom_anchor_sonic": {"x": [-8, 8], "y": [-24, 0]},
        "note": "The ROM overlap helpers treat the player as the closed box x [-8,+8], y [-24,0] around the anchor (object boxes hang above the object anchor in the same way); "
                "the POC mask is 11 px wide and reaches from 12 px above to 18 px below the ROM anchor. The two are not the same region, so a mask overlap is not "
                "equivalent to the ROM test even where the dimensions look similar.",
    }


def unresolved() -> list:
    return [
        "player states above $33 and player types other than 1/2 were not enumerated",
        "frames chosen by callbacks (not by the state script) are covered only through the emulated random-play sample",
        "the variant overlap helper at $640B has no direct caller; whether a computed jump can reach it was not proven",
        "type $28 and $26 full contact-side behaviour (riding, carrying, launch) was not re-derived here; only their contact geometry",
        "how the player's D523 combined contact flags are produced was not re-derived (the solid helper consumes them)",
        "POC runtime mask behaviour (GameMaker bbox rounding, sprite subimage masks) was not executed",
        "the layout-ring probe parity rule uses the player's animation timer +$07 bit 0; its purpose is not established",
    ]


def build(rom: bytes, static_only: bool = False) -> dict:
    check_rom(rom)
    report = {
        "format": 1,
        "rom_sha256": ROM_SHA256,
        "subject": "player/object collision geometry audit",
        "research_only": True,
        "poc_untouched": True,
        "evidence_classes": EVIDENCE,
        "machine_facing_label": "collision_geometry",
        "extent_fields": extent_writers_and_readers(rom),
        "overlap_6328": overlap_spec(),
        "solid_5FA0": solid_spec(),
        "terrain_constants": terrain_constants(rom),
        "assumption_audit": assumption_audit(),
        "poc_player_mask": poc_player_mask(),
        "unresolved": unresolved(),
    }
    if not static_only:
        report["player_extents"] = player_extents(rom)
        report["emulated_player_extents"] = emulated_extents(rom)
        report["overlap_6328"]["grid"] = overlap_grid(rom)
        report["solid_5FA0"]["grid"] = solid_grid(rom)
        report["helper_matrix"] = helper_matrix(rom)
        report["callback_sweeps"] = callback_sweeps(rom)
        report["spring_26"] = spring_26_sweep(rom)
        report["proximity"] = proximity_spec(rom)
    return report


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("rom", type=Path)
    p.add_argument("--output", type=Path, default=OUTPUT)
    p.add_argument("--check", action="store_true")
    p.add_argument("--static-only", action="store_true")
    a = p.parse_args()
    rom = a.rom.read_bytes()
    report = build(rom, a.static_only)
    text = json.dumps(report, indent=2) + "\n"
    if a.check:
        old = a.output.read_text(encoding="utf-8")
        if a.static_only:
            old_j, new_j = json.loads(old), json.loads(text)
            for k in new_j:
                o = old_j.get(k)
                if isinstance(o, dict):
                    o = {a_: b_ for a_, b_ in o.items() if a_ != "grid"}     # the grids are execution results
                if o != new_j[k]:
                    print("MISMATCH", k)
                    sys.exit(1)
        elif old.replace("\r\n", "\n") != text:
            print("MISMATCH")
            sys.exit(1)
        print("collision-geometry cache matches ROM")
        return
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps({"output": str(a.output)}))


if __name__ == "__main__":
    main()
