"""Bounded original sound-language interpreter. No CPU, ROM or trace dependency.

Private bank supplies checked sparse DATA records, headers and priority metadata.
All sequencing, envelopes and frequency emission are computed at runtime.
"""
from m5p0r_emission import Registers


class DecodeError(ValueError):
    pass


class Decoder:
    def __init__(self, bank, horizon=None):
        if bank['version'] != 1:
            raise DecodeError('unsupported bank version')
        self.bank = bank
        self.data = bank['data']
        self.limit = bank['horizon'] if horizon is None else horizon
        if not 0 < self.limit <= bank['horizon']:
            raise DecodeError('unsupported coverage horizon')
        self.psg = Registers()
        self.tempo = [0, 0]
        self.tick_number = 0
        self.writes = []
        self.ops = 0
        self.loops = []
        self.opcodes = {}
        self.iy = 0
        self.reset()
        self.writes = []

    def byte(self, p):
        try:
            return self.data[str(p)]
        except KeyError:
            raise DecodeError(f'unvalidated data pointer {p:04x}') from None

    def word(self, p):
        return self.byte(p) | self.byte(p + 1) << 8

    def emit(self, v):
        v &= 255
        self.writes.append(v)
        self.psg.write(v)

    def reset(self):
        self.ch = [bytearray(48) for _ in range(7)]
        self.priority = 0
        self.mail = [0, 0, 0]
        self.selected = 0x80
        self.fade = [0, 0, 0]
        self.saved_noise = 0
        self.last_sfx = 0
        self.noise_offset = self.fade_noise_volume = 0
        self.owners = [None] * 7
        for v in (0x80, 0, 0xA0, 0, 0xC0, 0, 0x9F, 0xBF, 0xDF, 0xFF):
            self.emit(v)

    def direct(self, rid, slot=0):
        if slot not in range(3) or str(rid) not in self.bank['priority']:
            raise DecodeError('unsupported request/mailbox')
        self.mail[slot] = rid

    def init(self, rid):
        try:
            p = self.bank['programs'][str(rid)]
        except KeyError:
            raise DecodeError('request program not extracted') from None
        if rid < 0xA0:
            self.reset()
            self.tempo = [p['tempo']] * 2
        else:
            self.last_sfx = rid
        for n, s in enumerate(p['streams']):
            latch = s['latch']
            i = n if rid < 0xA0 else {0xA0: 4, 0xC0: 5, 0xE0: 6}[latch]
            if rid >= 0xA0:
                if latch == 0xC0 and not self.ch[6][0] & 64:
                    self.ch[6][0] |= 4
                    self.emit(0xFF)
                self.ch[{4: 1, 5: 2, 6: 3}[i]][0] |= 4
            c = self.ch[i]
            # Original initialization leaves other channel fields untouched.
            c[0:11] = bytes([s['flags'], latch, p['multiplier'],
                            s['pointer'] & 255, s['pointer'] >> 8,
                            s['transpose'] & 255, s['volume'], 0, 0, 48, 1])
            c[39:42] = bytes(3)
            self.owners[i] = rid
            self.iy = 0x4264 + n if rid < 0xA0 else (0xDE40,0xDE70,0xDEA0,0xDED0)[{4:1,5:2,6:3}[i]]
        self.selected = 0x80

    def off(self, c):
        c[0] |= 16
        if not c[0] & 4:
            self.emit(c[1] + 31)

    def release(self, i):
        c = self.ch[i]
        latch = c[1]
        if latch == 0xA0:
            target = 1
        elif latch == 0xC0:
            target = 6 if self.ch[6][0] & 128 else 2
        else:
            if not c[0] & 64 and not self.ch[5][0] & 128:
                self.ch[2][0] = (self.ch[2][0] & ~68) | 16
                self.ch[5][0] = 0
            self.emit(self.saved_noise)
            target = 3
        self.ch[target][0] = (self.ch[target][0] & ~4) | 16
        self.emit(latch | 31)
        self.priority = c[0] = 0

    def noise(self, i, v):
        c = self.ch[i]
        if not self.last_sfx & 128 and v & 3 == 3 and self.ch[5][0] & 128:
            self.ch[3][0] = (self.ch[3][0] & ~4) | 16
            c[0] = 0
            self.emit(255)
            self.last_sfx = 255
            return False
        self.emit(v)
        self.iy = 0xDF30
        if v & 3 == 3:
            self.emit(0xDF)
            c[0] &= ~64
            self.ch[2][0] |= 4
            self.ch[5][0] |= 4
        else:
            c[0] |= 64
            self.ch[5 if self.ch[5][0] & 128 else 2][0] &= ~4
        return True

    @staticmethod
    def putword(c, p, v):
        v &= 65535
        c[p:p + 2] = v.to_bytes(2, 'little')

    @staticmethod
    def cw(c, p):
        return c[p] | c[p + 1] << 8

    @staticmethod
    def signed(v):
        return v - 256 if v & 128 else v

    def command(self, i, op, p):
        c = self.ch[i]
        if op not in {0xE0,0xE6,0xE7,0xF0,0xF2,0xF3,0xF5,0xF6,0xF7,0xF8,0xF9,0xFB}:
            raise DecodeError(f'unverified opcode {op:02x} at {p-1:04x}')
        a = self.byte(p)
        self.ops += 1
        self.opcodes[op] = self.opcodes.get(op, 0) + 1
        if op == 0xE0:
            c[8] = 128
            c[32:37] = bytes(self.byte(p + j) for j in range(5))
            return p + 5
        if op == 0xE6:
            if not self.fade[0]: c[6] = (c[6] + a) & 15
        elif op == 0xE7:
            c[0] |= 2
            return p
        elif op == 0xF5: c[8] = a
        elif op == 0xF0:
            self.putword(c, 16, p)
            c[7] = 128
            return p + 4
        elif op == 0xF2:
            self.release(i)
            return None
        elif op == 0xF3:
            if not self.noise(i, a): return None
        elif op in (0xF6, 0xF8):
            q = self.word(p)
            if op == 0xF8:
                if c[9] < 44: raise DecodeError('call stack overflow')
                self.putword(c, c[9] - 2, p + 1)
                c[9] -= 2
            self.loops.append((self.tick_number, i, p - 1, q))
            return q
        elif op == 0xF7:
            if a > 2: raise DecodeError('loop index outside validated channel')
            if not c[39 + a]: c[39 + a] = self.byte(p + 1)
            c[39 + a] = (c[39 + a] - 1) & 255
            if c[39 + a]:
                q = self.word(p + 2)
                self.loops.append((self.tick_number, i, p - 1, q))
                return q
            return p + 4
        elif op == 0xF9:
            if c[9] > 46: raise DecodeError('call stack underflow')
            q = self.cw(c, c[9]) + 1
            c[9] += 2
            return q
        elif op == 0xFB: c[5] = (c[5] + a) & 255
        else:
            # Original reserved RET handlers are deliberately unsupported.
            raise DecodeError(f'unsupported opcode {op:02x} at {p-1:04x}')
        return p + 1

    def note_end(self, c):
        if c[0] & 2: return
        if c[8] & 128: c[29] = (c[29] & 15) | 128
        else: self.off(c)

    def duration(self, c, a, p):
        c[10] = c[13] = (a * c[2]) & 255
        self.finish_read(c, p)

    def finish_read(self, c, p):
        self.putword(c, 3, p)
        if c[0] & 2: return
        if not c[0] & 64: c[0] &= ~32
        c[14] = c[15]
        c[21] = 0
        if not c[8] & 128: c[31] = 0

    def read(self, i):
        c = self.ch[i]
        music_noise = i == 3
        c[0] &= ~16 if music_noise else ~18
        p = self.cw(c, 3)
        for _ in range(256):
            a = self.byte(p)
            p += 1
            self.ops += 1
            if a >= 0xE0:
                p = self.command(i, a, p)
                if p is None: return
                continue
            if music_noise:
                if a < 128:
                    self.duration(c, a, p)
                    return
                choices = [(32, 30, 2, 0xE4), (16, 29, 3, 0xE6),
                           (8, 39, 2, 0xE4), (4, 40, 4, 0xE4),
                           (2, 36, 2, 0xE4), (1, 37, 2, 0xE5)]
                for bit, env, volume, control in choices:
                    if a & bit:
                        c[8], c[6] = env, volume
                        if not c[0] & 4:
                            self.saved_noise = (self.noise_offset + control) & 255
                            self.emit(self.saved_noise)
                        break
                else: self.off(c)
            elif c[0] & 8:
                v = (a << 8) | self.byte(p)
                p += 1
                if v: v = (v + self.signed(c[5])) & 65535
                self.putword(c, 11, v)
                a = self.byte(p)
                self.duration(c, a, p + 1)
                return
            else:
                if a >= 0xD8:
                    c[6] = a & 7
                    continue
                if a < 128:
                    self.duration(c, a, p)
                    return
                if a == 128: self.note_end(c)
                else:
                    c[29] &= 127
                    note = ((a & 127) + c[5]) & 255
                    self.putword(c, 11, self.word(0x4436 + 2 * note))
            a = self.byte(p)
            if a < 128:
                self.duration(c, a, p + 1)
            else:
                c[10] = c[13]
                self.finish_read(c, p)
            return
        raise DecodeError('stream operation budget exhausted')

    def env(self, c):
        a = c[8]
        if not a: return 0
        if a & 128:
            state, level = c[29], c[31]
            if state & 16:
                level = max(0, level - c[32])
                if not level: c[29] ^= 0x30
            elif state & 32:
                level = min(c[34], level + c[33])
                if level == c[34]: c[29] ^= 0x30 if state & 8 else 0x60
            elif state & 64:
                level = min(255, level + c[35])
                if level == 255: c[29] &= 0x8F
            else:
                level += c[36]
                if level > 255:
                    c[29] &= 15
                    c[31] = 255
                    self.off(c)
                    return 255
            c[31] = level
            return level >> 4
        base = self.word(0x49FD + 2 * (a - 1))
        for _ in range(256):
            a = self.byte(base + c[31])
            if a < 128:
                c[31] = (c[31] + 1) & 255
                return a
            if a == 0x82:
                self.off(c)
                return a
            if a == 0x81:
                c[0] |= 16
                return a
            if a != 0x80:
                raise DecodeError('unsupported envelope DE-relative control')
            c[31] = 0
        raise DecodeError('envelope operation budget exhausted')

    def pitch(self, c):
        v = self.cw(c, 11)
        if not c[7]: return v
        if c[7] & 128:
            c[20] = (c[20] - 1) & 255
            if c[20]: return v
            c[20] += 1
            c[21] = (c[21] - 1) & 255
            if not c[21]:
                self.iy = self.cw(c, 16)
                c[21] = self.byte(self.cw(c, 16) + 1)
                self.putword(c, 18, self.cw(c, 18) + self.signed(c[22]))
            v = (v + self.cw(c, 18)) & 65535
            c[23] = (c[23] - 1) & 255
            if not c[23]:
                address = self.iy + 3
                if 0xDE40 <= address < 0xDF90:
                    offset = address - 0xDE40
                    c[23] = self.ch[offset // 48][offset % 48]
                elif address == 0xDE06:
                    c[23] = self.mail[2]
                else:
                    c[23] = self.byte(address)
                c[22] = (-c[22]) & 255
            return v
        raise DecodeError('unverified table pitch program')

    def channel(self, i):
        c = self.ch[i]
        c[10] = (c[10] - 1) & 255
        at_read = not c[10]
        if i == 3:
            if at_read: return self.read(i)
            return self.attenuate(c)
        if at_read:
            self.read(i)
            if not c[0] & 128: return
            if c[0] & 20: return
            if c[7] & 128 and not c[0] & 2:
                p = self.cw(c, 16)
                c[20:23] = bytes(self.byte(p + j) for j in range(3))
                c[23] = self.byte(p + 3) >> 1
                c[18:20] = bytes(2)
            if c[8] & 128 and not c[0] & 2 and not c[29] & 128:
                c[31] = 255
                c[29] = 16 | c[30]
        else:
            if c[0] & 4: return
            if c[14]:
                c[14] -= 1
                if not c[14]: self.note_end(c)
        if (at_read or c[7] and not c[0] & 32) and not c[0] & 64:
            v = (self.pitch(c) + self.signed(c[37])) & 65535
            latch = 0xC0 if c[1] == 0xE0 else c[1]
            self.emit((v & 15) | latch)
            b = ((v & 0xF0) | (v >> 8)) & 255
            self.emit((b >> 4) | ((b & 15) << 4))
        self.attenuate(c)

    def attenuate(self, c):
        a = self.env(c)
        if c[0] & 20: return
        a = (a + c[6]) & 255
        if a & 16: a = 15
        self.emit((a | c[1]) + 16)

    def tick(self):
        if self.tick_number >= self.limit: raise DecodeError('unsupported coverage horizon')
        self.tick_number += 1
        self.writes = []
        self.ops = 0
        self.iy = 0xDE03
        for n, rid in enumerate(self.mail):
            if rid & 127:
                pr = self.bank['priority'][str(rid)]
                if pr >= self.priority: self.priority, self.selected = pr & 127, rid
            self.mail[n] = 0
        if self.tempo[0]:
            self.tempo[0] -= 1
            if not self.tempo[0]:
                self.tempo[0] = self.tempo[1]
                for c in self.ch[:4]: c[10] = (c[10] + 1) & 255
        if self.fade[0]:
            for c in self.ch[4:]:
                if not c[0] & 128: continue
                if c[1] == 0xA0: self.ch[1][0] &= ~4
                else:
                    if c[1] == 0xE0: self.ch[3][0] &= ~4
                    self.ch[2][0] &= ~4
                c[0] = 0
            self.fade[1] = (self.fade[1] - 1) & 255
            if not self.fade[1]:
                self.fade[1] = self.fade[2]
                self.fade[0] -= 1
                if not self.fade[0]: self.reset()
                else:
                    for c in self.ch[:3]:
                        if c[6] + 1 < 12: c[6] += 1
                    if self.fade_noise_volume + 1 < 12: self.fade_noise_volume += 1
        rid = self.selected
        if rid != 0x80:
            if rid >= 0xD4 or not rid & 128: self.reset()
            else: self.init(rid)
        for i, c in enumerate(self.ch):
            if c[0] & 128: self.channel(i)

    def snapshot(self):
        return dict(ports=list(self.writes), registers=self.psg.snapshot(),
                    latch=self.psg.latch, saved_noise=self.saved_noise,
                    channels=[c[0] & 0xD4 for c in self.ch], priority=self.priority)
