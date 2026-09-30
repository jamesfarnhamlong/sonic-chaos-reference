"""Minimal Sega Master System frame harness for registration research.

This is NOT a general SMS emulator. It exists so the research can observe the
original game's own VDP state (name table, V/H scroll, SAT, CRAM) after the
original code has built a frame, and compose visible pixels from that state.

Modelled:
  * Z80 via kosarev/z80 (same core as tools/oracle.py).
  * Sega mapper slots 0/1/2 ($FFFD/$FFFE/$FFFF), 8 KB RAM with $E000 mirror.
  * VDP ports $BE/$BF: address/code latch, VRAM/CRAM writes, register writes,
    read buffer, status flags; frame IRQ (R1 bit 5) and line IRQ (R0 bit 4 /
    R10 counter); V counter port $7E (NTSC 192-line table).
  * 262 lines x 228 Z80 cycles per frame.  Register state is sampled per line.
  * Joypad 1 port $DC (active-low), scripted by the caller.

Not modelled: PSG audio, sprite collision/overflow flags, exact mid-line
timing, FM, Game Gear specifics.  Rendering implements Mode 4 background and
8x16 sprites as used by Sonic Chaos (R1 = $82 | ...).

Evidence produced with this harness is labelled "EMULATED ORIGINAL FRAME" in
the registration research: the pixels come from original code driving an
approximate VDP, and every conclusion drawn from it is cross-checked against
byte-verified assembly.
"""
from __future__ import annotations

import z80

LINES = 262
CYCLES_PER_LINE = 228
ACTIVE_LINES = 192

BTN_UP, BTN_DOWN, BTN_LEFT, BTN_RIGHT, BTN_1, BTN_2 = 1, 2, 4, 8, 16, 32


class SMS:
    def __init__(self, rom: bytes):
        self.rom = rom
        self.banks = len(rom) // 0x4000
        self.cpu = z80.Z80Machine()
        self.mem = self.cpu.memory
        self.slot = [0, 1, 2]
        self._map(0, 0); self._map(1, 1); self._map(2, 2)
        self.cpu.set_write_callback(self._write)
        # All ROM-area writes and the RAM mirror go through Python.
        self.cpu.mark_addrs(0, 0xC000, self.cpu.WRITE_MARK)
        self.cpu.mark_addrs(0xE000, 0x2000, self.cpu.WRITE_MARK)
        self.cpu.mark_addrs(0xC000, 0x2000, self.cpu.WRITE_MARK)
        self.cpu.set_input_callback(self._in)
        self.cpu.set_output_callback(self._out)
        self.vram = bytearray(0x4000)
        self.cram = bytearray(32)
        self.reg = [0] * 16
        self.latch = None
        self.code = 0
        self.addr = 0
        self.buffer = 0
        self.status = 0
        self.line = 0
        self.line_counter = 0
        self.line_irq = False
        self.pad = 0  # pressed-button bitmask
        self.frame = 0
        self.line_regs = [None] * LINES
        self.cpu.sp = 0xDFF0
        self.cpu.pc = 0
        self.pc_hooks = {}

    def add_pc_hook(self, address, fn):
        """Call fn(self) whenever execution reaches address (before it runs)."""
        self.pc_hooks[address] = fn
        self.cpu.set_breakpoint(address)

    # ----------------------------------------------------------------- memory
    def _map(self, slot, bank):
        bank %= self.banks
        self.slot[slot] = bank
        start = slot * 0x4000
        src = self.rom[bank * 0x4000:(bank + 1) * 0x4000]
        if slot == 0:
            # First 1 KB is never paged on the Sega mapper.
            self.mem[0x400:0x4000] = src[0x400:]
            self.mem[0:0x400] = self.rom[0:0x400]
        else:
            self.mem[start:start + 0x4000] = src

    def _write(self, address, value):
        if address < 0xC000:
            return  # ROM: ignore
        base = 0xC000 + (address & 0x1FFF)
        self.mem[base] = value
        self.mem[base + 0x2000] = value
        if address >= 0xFFFC:
            if address == 0xFFFD:
                self._map(0, value)
            elif address == 0xFFFE:
                self._map(1, value)
            elif address == 0xFFFF:
                self._map(2, value)

    # -------------------------------------------------------------------- I/O
    def _vcounter(self):
        ln = self.line
        return ln if ln <= 0xDA else (ln - 6) & 0xFF

    def _in(self, port):
        port &= 0xFF
        if port < 0x40:
            return 0xFF
        if port < 0x80:
            return self._vcounter() if not port & 1 else 0
        if port < 0xC0:
            if port & 1:
                s = self.status
                self.status = 0
                self.line_irq = False
                self.latch = None
                return s | 0x1F
            v = self.buffer
            self.buffer = self.vram[self.addr]
            self.addr = (self.addr + 1) & 0x3FFF
            self.latch = None
            return v
        if port & 1:
            return 0xFF
        return (~self.pad) & 0xFF

    def _out(self, port, value):
        port &= 0xFF
        if port < 0x80:
            return
        if port < 0xC0:
            if port & 1:
                if self.latch is None:
                    self.latch = value
                    return
                low = self.latch
                self.latch = None
                self.code = value >> 6
                self.addr = ((value & 0x3F) << 8) | low
                if self.code == 0:
                    self.buffer = self.vram[self.addr]
                    self.addr = (self.addr + 1) & 0x3FFF
                elif self.code == 2:
                    self.reg[value & 0x0F] = low
            else:
                self.latch = None
                if self.code == 3:
                    self.cram[self.addr & 31] = value
                else:
                    self.vram[self.addr] = value
                self.buffer = value
                self.addr = (self.addr + 1) & 0x3FFF

    # ------------------------------------------------------------------ timing
    def _irq_asserted(self):
        return ((self.status & 0x80) and (self.reg[1] & 0x20)) or \
            (self.line_irq and (self.reg[0] & 0x10))

    def _run_cycles(self, n):
        remaining = n
        while remaining > 0:
            if self._irq_asserted():
                self.cpu.on_handle_active_int()
            chunk = min(remaining, 32)
            self.cpu.ticks_to_stop = chunk
            events = self.cpu.run()
            used = chunk - self.cpu.ticks_to_stop
            if events & self.cpu._BREAKPOINT_HIT:
                hook = self.pc_hooks.get(self.cpu.pc)
                if hook:
                    hook(self)
                self._step_over()
            if used <= 0:
                used = chunk
            remaining -= used

    def _step_over(self):
        pc = self.cpu.pc
        self.cpu.clear_breakpoint(pc)
        self.cpu.ticks_to_stop = 1
        self.cpu.run()
        self.cpu.set_breakpoint(pc)
        return

    def run_frame(self):
        for ln in range(LINES):
            self.line = ln
            if ln <= ACTIVE_LINES:
                if ln == 0:
                    self.line_counter = self.reg[10]
                    self.vscroll_latched = self.reg[9]
                if ln < ACTIVE_LINES:
                    self.line_regs[ln] = (self.reg[0], self.reg[8])
            if ln <= ACTIVE_LINES:
                if self.line_counter == 0:
                    self.line_counter = self.reg[10]
                    self.line_irq = True
                else:
                    self.line_counter -= 1
            else:
                self.line_counter = self.reg[10]
            if ln == ACTIVE_LINES + 1:
                self.status |= 0x80
            self._run_cycles(CYCLES_PER_LINE)
        self.frame += 1

    # ------------------------------------------------------------------ helpers
    def ram(self, address, n=1):
        return bytes(self.mem[address:address + n])

    def u16(self, address):
        return self.mem[address] | (self.mem[address + 1] << 8)

    def w16(self, address, value):
        value &= 0xFFFF
        self._write(address, value & 0xFF)
        self._write(address + 1, value >> 8)

    # --------------------------------------------------------------- rendering
    def color(self, index):
        c = self.cram[index & 31]
        r, g, b = c & 3, (c >> 2) & 3, (c >> 4) & 3
        return (r * 85, g * 85, b * 85)

    def tile_row(self, tile, row):
        base = (tile & 0x1FF) * 32 + row * 4
        b0, b1, b2, b3 = self.vram[base:base + 4]
        out = []
        for bit in range(7, -1, -1):
            out.append(((b0 >> bit) & 1) | (((b1 >> bit) & 1) << 1) |
                       (((b2 >> bit) & 1) << 2) | (((b3 >> bit) & 1) << 3))
        return out

    def sat(self):
        """Return SAT entries in hardware order until the $D0 terminator."""
        base = ((self.reg[5] & 0x7E) << 7)
        entries = []
        for i in range(64):
            y = self.vram[base + i]
            if y == 0xD0:
                break
            x = self.vram[base + 0x80 + i * 2]
            n = self.vram[base + 0x81 + i * 2]
            entries.append((i, y, x, n))
        return entries

    def render(self):
        """Compose the 256x192 frame.  Returns (rgb_rows, layer_rows).

        layer_rows[y][x] is 'B' for background, 'S' for a sprite pixel.
        """
        name_base = (self.reg[2] & 0x0E) << 10
        vscroll = self.vscroll_latched
        bg_index = [[0] * 256 for _ in range(ACTIVE_LINES)]
        bg_prio = [[False] * 256 for _ in range(ACTIVE_LINES)]
        for y in range(ACTIVE_LINES):
            r0, hscroll = self.line_regs[y]
            if (r0 & 0x40) and y < 16:
                hscroll = 0
            for x in range(256):
                vs = vscroll
                if (r0 & 0x80) and x >= 192:
                    vs = 0
                ny = (y + vs) % 224
                nx = (x - hscroll) & 0xFF
                ent = name_base + ((ny >> 3) * 32 + (nx >> 3)) * 2
                word = self.vram[ent] | (self.vram[ent + 1] << 8)
                tile = word & 0x1FF
                hf, vf = word & 0x200, word & 0x400
                pal = 16 if word & 0x800 else 0
                row = ny & 7
                if vf:
                    row = 7 - row
                pix = self.tile_row(tile, row)
                col = nx & 7
                if hf:
                    col = 7 - col
                bg_index[y][x] = pal + pix[col]
                bg_prio[y][x] = bool(word & 0x1000) and pix[col] != 0
        sprite_index = [[None] * 256 for _ in range(ACTIVE_LINES)]
        tall = bool(self.reg[1] & 0x02)
        height = 16 if tall else 8
        pat_base = 256 if (self.reg[6] & 0x04) else 0
        shift = 8 if (self.reg[0] & 0x08) else 0
        per_line = [0] * ACTIVE_LINES
        for i, sy, sx, n in self.sat():
            top = sy + 1
            if sy >= 0xE0:
                top = sy + 1 - 256
            if tall:
                n &= 0xFE
            for r in range(height):
                ly = top + r
                if not 0 <= ly < ACTIVE_LINES:
                    continue
                if per_line[ly] >= 8:
                    continue
                per_line[ly] += 1
                pix = self.tile_row(pat_base + n + (r >> 3), r & 7)
                for c in range(8):
                    lx = sx - shift + c
                    if 0 <= lx < 256 and pix[c] and sprite_index[ly][lx] is None:
                        sprite_index[ly][lx] = 16 + pix[c]
        rgb, layer = [], []
        for y in range(ACTIVE_LINES):
            r0 = self.line_regs[y][0]
            row, lrow = [], []
            for x in range(256):
                if (r0 & 0x20) and x < 8:
                    row.append(self.color(16 + (self.reg[7] & 15)))
                    lrow.append('X')
                    continue
                s = sprite_index[y][x]
                if s is not None and not bg_prio[y][x]:
                    row.append(self.color(s)); lrow.append('S')
                else:
                    row.append(self.color(bg_index[y][x])); lrow.append('B')
            rgb.append(row); layer.append(lrow)
        return rgb, layer, bg_index, sprite_index

    def save_png(self, path, rgb=None):
        from PIL import Image
        if rgb is None:
            rgb = self.render()[0]
        img = Image.new('RGB', (256, ACTIVE_LINES))
        img.putdata([p for row in rgb for p in row])
        img.save(path)
