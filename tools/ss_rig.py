"""Whole-game rig for the Special Stage audit.

Boots the ORIGINAL game into an ordinary act, forces `$D2CC` (completed-stage bitfield) to choose the stage, and then enters the stage by running the
original ring-collect routine `$3138` with `$D29A = $99` at an update boundary.  Everything after that (the `$178F` entry gate, the `$17B0` entry
sequence, `$187B` stage selection, the level loader, the stage objects) is the unmodified ROM.  This is the same natural entry that a hundredth ring
causes; nothing about the stage itself is injected.

Evidence label for everything produced with this rig: EMULATED ORIGINAL FRAME / controlled runtime trace (approximate SMS harness, see
`tools/sms_frame_harness.py`).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from sez_surfaces_rig import ZoneGame, PAD  # noqa: E402
from sms_frame_harness import BTN_1, BTN_2   # noqa: E402

# D2CC value that makes `$187B` select special stage N (1..5): the stage index is 8 + the count of consecutive set bits from bit 0 (max 4).
STAGE_MASK = {1: 0x00, 2: 0x01, 3: 0x03, 4: 0x07, 5: 0x0F}
STAGE_ZONE = {n: 7 + n for n in range(1, 6)}      # SS1..SS5 -> ROM zone 8..12
STAGE_BIT = {n: 1 << (n - 1) for n in range(1, 6)}

RAM = dict(
    zone=0xD297, act=0xD298, saved_zone=0xD296, flow=0xD293, mode=0xD294, character=0xD2C8, lives=0xD299, rings=0xD29A,
    score0=0xD29D, score1=0xD29E, score2=0xD29F, emeralds=0xD2CC, result_card=0xD2CD, ss_count=0xD2C3, timer_sec=0xD2BF,
    timer_min=0xD2C0, timer_run=0xD2BE, timer_frames=0xD2C2, powerup=0xD532, power_timer=0xD44C, power_copy=0xD3A1,
    bonus_hold=0xD3C4, boss_active=0xD3C1, reward_ring=0xD2A6,
)


def hook_ring_collect(g: ZoneGame, rings: int = 0x99, once=None):
    """Arrange for the original `$3138` (ring counter increment) to run at the next player-update boundary with `$D29A = rings`."""
    m = g.m
    state = once if once is not None else [False]

    prior = g.s.pc_hooks.get(0x64FA)

    def inject(mm):
        if prior is not None:
            prior(mm)
        if state[0] or mm.cpu.ix != 0xD500:
            return
        state[0] = True
        m[0xD29A] = rings
        sp = mm.cpu.sp - 2
        mm.mem[sp], mm.mem[sp + 1] = 0xFA, 0x64            # return to the engine entry that was about to run
        mm.cpu.sp = sp
        mm.cpu.pc = 0x3138
    g.hook(0x64FA, inject)
    return state


class SSRig(ZoneGame):
    """ZoneGame that is already inside special stage `stage`, with the post-load snapshot installed as the restore base."""

    def __init__(self, rom: bytes, stage: int, origin=(0, 0), settle: int = 90, character: int = 1, extra_ram=None, boot_hooks=None):
        assert stage in STAGE_MASK
        super().__init__(rom, origin[0], origin[1], hooks={}, boot_hooks=boot_hooks)
        self.stage = stage
        s, m = self.s, self.m
        m[0xD2CC] = STAGE_MASK[stage]
        for a, v in (extra_ram or {}).items():
            m[a] = v
        self.entry_log = []
        self.pre_ram = bytes(m[0xC000:0xE000])
        hook_ring_collect(self)
        prev = None
        for f in range(1500):
            s.pad = 0
            s.run_frame()
            cur = (m[0xD293], m[0xD294], m[0xD297], m[0xD296])
            if cur != prev:
                self.entry_log.append(dict(frame=f, flow=cur[0], mode=cur[1], zone=cur[2], saved_zone=cur[3], rings=m[0xD29A], timer=m[0xD2BF]))
                prev = cur
            if m[0xD297] == STAGE_ZONE[stage] and m[0xD294] == 0x80 and m[0xD500] == 1 and m[0xD2BE]:
                break
        else:
            raise RuntimeError('special stage never loaded')
        for _ in range(settle):
            s.pad = 0
            s.run_frame()
        self.post_ram = bytes(m[0xC000:0xE000])
        self.e.base = self.e.snapshot()
        self.base_cpu = bytes(self.s.cpu.get_state_view())
        self.upd = 0

    def restore_snapshot(self) -> None:
        """Complete-state restore (harness snapshot plus the z80 core's full state view) so forks are history independent."""
        self.e.restore(self.e.base)
        self.s.cpu.get_state_view()[:] = self.base_cpu
