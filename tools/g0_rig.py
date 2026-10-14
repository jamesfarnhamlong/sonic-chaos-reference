"""G0-R persistent whole-game session for the ordinary-campaign ROM contract.

One `Session` is one continuous run of the ORIGINAL ROM in the approximate SMS harness (`tools/sms_frame_harness.py`): reset, title, character select,
new game, ordinary acts, deaths, continues, Game Over, special-stage detours and the end of the final zone all run as unmodified ROM code.  Fixtures are
confined to the three kinds below and every scenario reports which it used:

* ARRIVAL  - at the return of the start-position loader (`$4E97`, once per act load) the player/camera are placed and/or the ring counter is preset.
             This is the same fixture `tools/object_18.py` used for the sign chain.
* RAM      - a single named byte/word is written at a frame boundary (e.g. rings = $99, lives = 1, `$D293` flag injection).  The ROM routine that would
             normally write it is cited by the scenario.
* PAD      - scripted joypad input (the harness has no console Start button; the title accepts button 1/2).

Nothing is ever written to program counters, banks, object tables or the VDP.  Evidence class for everything produced here: EMULATED ORIGINAL FRAME
(whole-game trace, approximate VDP) unless a scenario says CONTROLLED ROUTINE RESULT.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from sms_frame_harness import SMS, BTN_1, BTN_2, BTN_UP, BTN_DOWN, BTN_LEFT, BTN_RIGHT  # noqa: E402

BTN_BOTH = BTN_1 | BTN_2

# Named RAM used by the campaign (all absolute, resident bank, verified by the writer census in the contract).
RAM = dict(
    menu=0xD292, flow=0xD293, mode=0xD294, started=0xD295, saved_zone=0xD296, zone=0xD297, act=0xD298, lives=0xD299, rings=0xD29A,
    score0=0xD29D, score1=0xD29E, score2=0xD29F, bonus=0xD2A6, character=0xD2C8, continues=0xD2C3, emeralds=0xD2CC, card=0xD2CD,
    timer_run=0xD2BE, timer_sec=0xD2BF, timer_min=0xD2C0, timer_ticks=0xD2C2, timeover=0xD44B, powerup=0xD532, power_timer=0xD44C,
    continue_ticks=0xD2CA, continue_digit=0xD2CB, sound=0xDE04, player_type=0xD500, player_state=0xD501, player_req=0xD502,
    level_select=0xD2CE, cursor=0xD2C9,
)

SIGN_Y = {0: 558, 1: 654}           # THZ1 / THZ2 sign anchors (docs/object-18-act-clear.md section 2)


class Session:
    def __init__(self, rom: bytes, sms=None):
        """`sms`: adopt an already-booted harness (e.g. the Special Stage rig's) instead of resetting a new console."""
        self.rom = rom
        self.s = sms if sms is not None else SMS(rom)
        self.m = self.s.mem
        self._arrival = None            # callable(machine) run at the next in-game $4E97 return
        self.writes = []                # (frame, address, value) for watched addresses
        self._watch = set()
        self._hooks = {}
        self._marks = {}
        self.hook(0x4E97, self._on_arrival)
        self.hook(0x3065, lambda mm: self._marks.__setitem__('charsel', mm.frame))
        self.hook(0x04D4, lambda mm: self._marks.__setitem__('newgame', mm.frame))
        orig = self.s._write

        def w(address, value):
            if address in self._watch:
                self.writes.append((self.s.frame, address, value))
            orig(address, value)
        self.s._write = w
        self.s.cpu.set_write_callback(w)
        self.events = []                # (name, snapshot) at every marked PC hit
        self.start_index = None

    # ------------------------------------------------------------------ plumbing
    def hook(self, address, fn):
        """Register `fn(machine)` at a CPU address; several observers may share one address (the harness keeps one hook per address)."""
        lst = self._hooks.get(address)
        if lst is None:
            prior = self.s.pc_hooks.get(address)
            lst = self._hooks[address] = [prior] if prior is not None else []

            def mux(mm, lst=lst):
                for f in list(lst):
                    f(mm)
            self.s.add_pc_hook(address, mux)
        lst.append(fn)

    def _on_arrival(self, mm):
        fn = self._arrival
        if fn is not None and mm.mem[RAM["started"]] == 0xFF:
            self._arrival = None
            fn(mm)

    def arm_arrival(self, fn):
        self._arrival = fn

    def watch(self, *names):
        self._watch |= {RAM[n] if isinstance(n, str) else n for n in names}

    def mark_pc(self, address, name, bank=None):
        """Record a snapshot (state BEFORE the instruction at `address` runs) every time the CPU reaches `address`.

        `bank`: for addresses in slot 2 (`$8000+`) only count the hit while that bank is paged in (the same CPU address exists in every bank)."""
        def fn(mm):
            if bank is not None and mm.slot[2] != bank:
                return
            self.events.append((name, self.snap()))
        self.hook(address, fn)

    def event_frames(self, name):
        return [sn["frame"] for n, sn in self.events if n == name]

    def first_event(self, name, after=0):
        for n, sn in self.events:
            if n == name and sn["frame"] >= after:
                return sn
        return None

    def b(self, name):
        return self.m[RAM[name]]

    def w(self, name, value):
        self.s._write(RAM[name], value & 0xFF)

    def u16(self, address):
        return self.s.u16(address)

    def snap(self):
        m = self.m
        return dict(
            frame=self.s.frame, menu=m[0xD292], flow=m[0xD293], mode=m[0xD294], started=m[0xD295], saved_zone=m[0xD296], zone=m[0xD297], act=m[0xD298],
            character=m[0xD2C8], lives=m[0xD299], continues=m[0xD2C3], emeralds=m[0xD2CC], card=m[0xD2CD], rings=m[0xD29A],
            score=[m[0xD29F], m[0xD29E], m[0xD29D]], bonus=self.u16(0xD2A6), timer=[m[0xD2C0], m[0xD2BF], m[0xD2C2]], timer_run=m[0xD2BE],
            timeover=m[0xD44B], powerup=m[0xD532], power_timer=self.u16(0xD44C), player=[m[0xD500], m[0xD501], m[0xD502], self.u16(0xD511), self.u16(0xD514)],
            continue_ticks=m[0xD2CA], continue_digit=m[0xD2CB], sound=m[0xDE04],
        )

    # ------------------------------------------------------------------ running
    def run(self, n, pad=0):
        for _ in range(n):
            self.s.pad = pad
            self.s.run_frame()

    def run_until(self, pred, pad=0, limit=6000):
        """Run frames until pred(self) is true; returns the frame count used or raises."""
        for i in range(limit):
            if pred(self):
                return i
            self.s.pad = pad(self) if callable(pad) else pad
            self.s.run_frame()
        raise RuntimeError("run_until: limit reached at " + repr(self.snap()))

    def playing(self):
        """Gameplay frame loop: level frame flag only, player object present, no pending reload."""
        m = self.m
        return m[0xD293] == 0x40 and m[0xD500] != 0 and m[0xD294] & 0xE0 == 0 and m[0xD2BE] != 0

    # ------------------------------------------------------------------ title and new game
    def boot_new_game(self, character=0, arrival=None, settle=0, title_hook=None):
        """Reset -> title -> button 1/2 -> character select (cursor 0 = Sonic, 1 = Tails) -> new game -> first act in play.

        `title_hook(session)` runs once while the title is displayed (frame 299), before the first button press.  Returns the frame at which the
        first act is in play.
        """
        return self._press_start(character, arrival, settle, title_hook, first=True)

    def start_from_title(self, character=0, arrival=None, settle=0):
        """From the title screen (after Game Over or the ending) start another new game."""
        return self._press_start(character, arrival, settle, None, first=False)

    def _press_start(self, character, arrival, settle, title_hook, first):
        m = self.m
        self.arm_arrival(arrival)
        f0 = self.s.frame
        marks = self._marks
        f = 0
        while True:
            pad = 0
            if f == 299 and title_hook is not None:
                title_hook(self)
            if f >= (300 if first else 20):
                at_select = marks.get("charsel", -1) >= f0 and m[0xD295] == 0
                if at_select and character == 1 and m[0xD2C8] == 0:
                    pad = BTN_RIGHT if f % 6 < 3 else 0
                elif f % 50 < 5:
                    pad = BTN_BOTH
            self.s.pad = pad
            self.s.run_frame()
            f += 1
            if marks.get("newgame", -1) >= f0 and m[0xD295] == 0xFF and self.playing():
                break
            if f > 6000:
                raise RuntimeError("new game never reached gameplay: " + repr(self.snap()))
        self.run(settle)
        return self.s.frame

    def set_start_index(self, zone, act):
        """START_INDEX fixture: overwrite the zone/act pair that new-game init `$07CE` just cleared (the same two stores the hidden level select
        makes at `$0821/$0826`), at `$07D5`."""
        def fn(mm):
            if self.start_index is not None:
                mm._write(0xD297, self.start_index[0])
                mm._write(0xD298, self.start_index[1])
        if self.start_index is None and not getattr(self, "_start_hooked", False):
            self.hook(0x07D5, fn)
            self._start_hooked = True
        self.start_index = (zone, act)

    # ------------------------------------------------------------------ fixtures
    @staticmethod
    def place_at_sign(act, rings=None):
        """ARRIVAL fixture for THZ1/THZ2 (zone 0, act 0/1): camera and player placed 160 px before the goal sign; optional ring preset."""
        sy = SIGN_Y[act]

        def fn(mm):
            mm.w16(0xD2D6, 3700)
            mm.w16(0xD2D8, sy - 118)
            mm.w16(0xD511, 3800)
            mm.w16(0xD514, sy - 58)
            if rings is not None:
                mm._write(0xD29A, rings)
        return fn

    @staticmethod
    def preset(**ram):
        """ARRIVAL fixture: write named RAM bytes at the start-position loader return."""
        def fn(mm):
            for k, v in ram.items():
                mm._write(RAM[k], v)
        return fn

    def walk_right_until(self, pred, limit=3000):
        return self.run_until(pred, pad=lambda s: BTN_RIGHT if (s.m[0xD293] & 0x30) == 0 and s.m[0xD501] != 0x20 else 0, limit=limit)

    # ------------------------------------------------------------------ call injection and palette trace
    def inject_call(self, address, ram=None):
        """RAM + CALL fixture: at the next player-engine entry (`$64FA`, IX = `$D500`, an update boundary) write `ram` and CALL `address` as if
        the game had reached it; control returns to the engine entry.  Used to run the unmodified ring-collect routine `$3138` (the hundredth
        ring) with a preset ring byte."""
        done = [False]
        m = self.m

        def fn(mm):
            if done[0] or mm.cpu.ix != 0xD500:
                return
            done[0] = True
            for a, v in (ram or {}).items():
                mm._write(RAM[a] if isinstance(a, str) else a, v)
            sp = mm.cpu.sp - 2
            mm.mem[sp], mm.mem[sp + 1] = 0xFA, 0x64
            mm.cpu.sp = sp
            mm.cpu.pc = address
        self.hook(0x64FA, fn)
        return done

    def cram_trace(self):
        """Start recording (frame, 32-byte CRAM, name-table-independent) whenever CRAM differs from the previous frame."""
        self.cram_log = []
        self._cram_prev = None
        orig_run = self.s.run_frame

        def run_frame():
            orig_run()
            cur = bytes(self.s.cram)
            if cur != self._cram_prev:
                self.cram_log.append((self.s.frame, cur))
                self._cram_prev = cur
        self.s.run_frame = run_frame
