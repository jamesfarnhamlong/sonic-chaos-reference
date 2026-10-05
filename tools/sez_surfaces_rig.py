"""Whole-game rig for the SEZ terrain-mechanics audit (surfaces $0C/$13 crumble and $1A booster).

Boots the ORIGINAL game in the approximate SMS harness into any zone/act (the MGHZ GameLab hard-codes zone 3), snapshots after a 90 frame
settle, and forks deterministic cases from the snapshot.

Game-loop order (observed with PC hooks): player engine ($64FA, IX = $D500) -> player callback (terrain pass inside) -> object scheduler ($5DD1) -> wait for
the frame.  A row is recorded at EVERY player-engine entry, i.e. exactly once per loop iteration ("player update"), and describes the state after the previous
iteration (player callback + object pass).  Rows therefore never merge two updates when the harness lags (a frame can contain two iterations).
Placement fixtures are written at an engine entry (an update boundary).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import mghz_surface_ceiling as M            # noqa: E402  (GameLab, P)
import platform_spike_collision as P        # noqa: E402

SLOT_BASE = 0xD540
N_SLOTS = 19
PAD = dict(UP=1, DOWN=2, LEFT=4, RIGHT=8, B1=16, B2=32)

# (cpu address) -> label of the events recorded per player update
EVENTS = {
    0x6B79: "h0c",          # surface $0C floor handler (entry)
    0x5EB7: "spawn13",      # positioned spawn used by $6B79
    0x6C1F: "replace",      # cell replacement vector target ($0428 -> $6C1F)
    0xA2DD: "13s0",         # type $13 state 0 callback
    0xA31B: "13shard",      # type $13 state 3 callback
    0xA33F: "13rm",         # remove callback (states 1-tail, 2)
    0xA344: "13rider",      # type $13 state 1 rider callback
    0xA36A: "13break",      # type $13 state 1 replace callback
    0x7646: "h1a",          # surface $1A booster handler (entry)
    0x48F7: "hurt",
    0x5EE1: "alloc11",      # command-4 child allocator (slots 7..17)
    0x5E9C: "alloc16",      # 16-slot allocator
    0x690B: "terrain",      # shared terrain pass
    0x691A: "floorpass",    # floor sampling
    0x753E: "ringprobe",    # terrain ring probe (also the $1A booster dispatch)
}


class ZoneGame(M.GameLab):
    """GameLab for an arbitrary zone/act with extra PC hooks and per-update rows."""

    def __init__(self, rom: bytes, zone: int, act: int, hooks: dict | None = None, boot_hooks: dict | None = None):
        from sms_frame_harness import SMS, BTN_1, BTN_2
        self.rom, self.zone, self.act_index = rom, zone, act
        self.key = f"z{zone}a{act}"
        s = SMS(rom)
        done = [False]

        def select(m):
            m._write(0xD297, zone)
            m._write(0xD298, act)

        def start(m):
            if m.frame > 300 and not done[0]:
                done[0] = True
        s.add_pc_hook(0x07D5, select)
        s.add_pc_hook(0x4E97, start)
        for a, fn in (boot_hooks or {}).items():
            s.add_pc_hook(a, fn)
        for f in range(4000):
            s.pad = 0 if f < 250 else BTN_1 if f < 700 and f % 40 < 3 else (BTN_1 | BTN_2) if not done[0] and f % 60 < 10 else 0
            s.run_frame()
            if done[0] and s.mem[0xD500] == 1:
                break
        else:
            raise RuntimeError("boot failed")
        for _ in range(90):
            s.pad = 0
            s.run_frame()
        self.s, self.m = s, s.mem
        self.upd = 0
        self.pending = []
        self.pending_info = []
        self.rows = []
        self.collect_types = None
        self.recording = False
        self._apply = None
        self._apply_done = False
        self.pre = {}                       # address -> fn(mm) run BEFORE the event is logged (fixture hooks: camera / pool / sleep injection)
        s.add_pc_hook(0x5E91, self._on_callback)
        s.add_pc_hook(0x64FA, self._engine_hook)
        for a, name in (hooks or EVENTS).items():
            s.add_pc_hook(a, self._ev(a, name))
        self.e = P.Emu.__new__(P.Emu)
        self.e.s, self.e.rom, self.e.act = s, rom, self.key
        self.e._place = P._load("spring_interaction")._place
        self.e.base = self.e.snapshot()

    NOP_ADDR = 0x429D                       # a $00 byte in the fixed ROM (verified in __init__)

    def restore_snapshot(self) -> None:
        """Restore the boot snapshot AND the z80 core's hidden decode state.

        The harness snapshot (platform_spike_collision.Emu) restores registers, memory and the VDP, but the core also keeps `index_rp_kind` (the pending DD/FD prefix) and
        `int_disabled` (the EI/DI shadow) which have no setter.  A previous run can end between a prefix and its opcode; resuming the snapshot PC with a stale IX prefix executes
        the first instruction wrongly (observed: the player teleported 3300 px).  One real NOP executed in the core clears both, then the snapshot is restored again."""
        self.e.restore()
        c = self.s.cpu
        if str(c.index_rp_kind).lower() != "hl" or c.int_disabled:
            c.pc = self.NOP_ADDR
            c.ticks_to_stop = 1
            c.run()
            self.e.restore()
        assert str(c.index_rp_kind).lower() == "hl" and not c.int_disabled

    def _ev(self, addr, name):
        base = self._event(name)

        def fn(mm):
            pre = self.pre.get(addr)
            if pre is not None:
                pre(mm)
            base(mm)
        return fn

    def hook(self, addr: int, fn) -> None:
        """Fixture hook at an address that is not one of the logged events."""
        self.s.add_pc_hook(addr, fn)

    # -- per-update recording --------------------------------------------------------
    def _snap_objs(self) -> list:
        return [(o['slot'], o['type'], o['state'], o['req'], o['x'], o['y'], o['vy'], o['p3f'], o['f4']) for o in self.objs(self.collect_types)]

    def _engine_hook(self, mm) -> None:
        if mm.cpu.ix != 0xD500:
            return
        if self._apply is not None:
            fn, self._apply = self._apply, None
            fn(self)
            self.rows = []
            self.pending = []
            self.pending_info = []
            self.recording = True
            self._apply_done = True
            return
        if self.recording:
            r = self.row()
            r['u'] = len(self.rows) + 1
            if self.collect_types is not None:
                r['o'] = self._snap_objs()
            self.rows.append(r)

    def begin(self, x, y, vx=0, vy=0, cur=5, f3=0, floor=True, prev=0x82, face=None, rings=0, p24=None, k=None, patch=None, width=128, d532=None, d3b1=None,
              apply=None, types=None) -> None:
        """Restore the snapshot and apply a placement at an update boundary (a player-engine entry); the next engine entry records update 1.

        `types`: also record the live objects of these types on every row (None: no object snapshots)."""
        self.restore_snapshot()
        self._apply_done = False
        self.recording = False
        self.collect_types = types

        def do(mm):
            s, m = self.s, self.m
            self.e._place(s, x, y, vx & 0xFFFF, vy & 0xFFFF)
            m[0xD502] = cur
            m[0xD501] = cur
            m[0xD50E] = m[0xD50F] = 0
            m[0xD503] = f3
            m[0xD522] = 0x02 if floor else 0
            if prev is not None:
                m[0xD36C] = prev
            m[0xD29A] = rings
            if face is not None:
                m[0xD504] = (m[0xD504] & ~0x10) | (0x10 if face else 0)
            if p24 is not None:
                m[0xD524] = p24
            if k is not None:
                m[0xD3BC] = k
            if d532 is not None:
                m[0xD532] = d532
            if d3b1 is not None:
                m[0xD3B1] = d3b1
            if patch:
                self.patch_cells(patch, width)
            if apply:
                apply(self)
        self._apply = do
        for _ in range(8):
            self.s.pad = 0
            self.s.run_frame()
            if self._apply_done:
                break
        else:
            raise RuntimeError("placement never applied")

    def run(self, updates: int, padf=None, stop=None, hook=None, max_frames: int = 0) -> list:
        """Run until `updates` rows exist (row u = the state after update u).  padf(u, f): pad for the next frame, u = rows so far; stop(row, rows) ends early;
        hook(self, f) runs after every frame (fixture writes happen on a frame boundary, which is an update boundary)."""
        limit = max_frames or updates * 3 + 12
        for f in range(limit):
            if len(self.rows) >= updates:
                break
            self.s.pad = padf(len(self.rows), f) if padf else 0
            self.s.run_frame()
            if hook:
                hook(self, f)
            if stop and self.rows and stop(self.rows[-1], self.rows):
                break
        return list(self.rows)

    def run_objs(self, updates: int, padf=None, stop=None, hook=None, types=(0x13,)) -> list:
        self.collect_types = types
        return self.run(updates, padf, stop, hook)

    # -- state -----------------------------------------------------------------------
    def patch_cells(self, cells: dict, width: int = 128) -> None:
        """Write block ids into the live layout RAM ($C001 + cy*width + cx)."""
        for (cx, cy), blk in cells.items():
            a = 0xC001 + cy * width + cx
            self.s._write(a, blk)

    def cell(self, cx: int, cy: int, width: int = 128) -> int:
        return self.m[0xC001 + cy * width + cx]

    def row(self) -> dict:
        r = super().row()
        s, m = self.s, self.m
        r.update({"d520": m[0xD520], "d521": m[0xD521], "d523": m[0xD523], "d519": m[0xD519], "d373": s.u16(0xD373), "d354": s.u16(0xD354),
                  "d356": s.u16(0xD356), "d358": s.u16(0xD358), "d35a": s.u16(0xD35A), "d3a4": s.u16(0xD3A4), "d174": s.u16(0xD174), "d176": s.u16(0xD176),
                  "d532": m[0xD532], "d3b1": m[0xD3B1], "hurtf": m[0xD503], "face": (m[0xD504] >> 4) & 1, "d504": m[0xD504], "d522": m[0xD522],
                  "d12f": m[0xD12F], "d44e": m[0xD44E], "d516": s.u16(0xD516)})
        return r

    # -- observation -----------------------------------------------------------------
    def objs(self, types=None) -> list:
        s, m = self.s, self.m
        out = []
        for i in range(N_SLOTS):
            b = SLOT_BASE + i * 0x40
            t = m[b]
            if t and (types is None or t in types):
                out.append({"slot": i, "type": t, "state": m[b + 1], "req": m[b + 2], "frame": m[b + 6], "dur": m[b + 7], "f4": m[b + 4],
                            "x": s.u16(b + 0x11), "y": s.u16(b + 0x14), "vx": M.s16(s.u16(b + 0x16)), "vy": M.s16(s.u16(b + 0x18)),
                            "p3f": m[b + 0x3F], "cell": s.u16(b + 0x30), "cx": s.u16(b + 0x34), "cy": s.u16(b + 0x36)})
        return out

    def free_slots(self) -> list:
        return [i for i in range(N_SLOTS) if not self.m[SLOT_BASE + i * 0x40]]
