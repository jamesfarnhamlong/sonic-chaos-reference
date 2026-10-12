"""DECOMP-1D-R1: which sound-stream command bytes can reach the flag dispatcher at ROM ``$086E8`` (CPU ``$46E8``).

The dispatcher at ``$46D5``/``$46D8`` in the bank-2 sound driver is entered with ``A >= $E0`` fetched from a music or
sound-effect stream (``LD A,(DE)`` at ``$434F`` for tone channels, ``$465A`` for the noise channel). Its table has two
entries (``$EF`` and ``$F1``) that point into a data table at ``$48AC``. Whether those two commands can occur is a
question about stream *data*, not about the dispatcher, so this module answers it from the data:

1. **Stream starts** come from the original driver. For each of the 68 request ids ``$81-$C4`` the original request
   arbitration (``$407F``) and dispatch (``$4119``) run on a plain Z80 core with the real ROM mapped (bank 0 resident,
   bank 2 in slot 1, bank 3 in slot 2). Every active channel's stream pointer and flag byte are read back; the channel
   base selects the token grammar (only ``$DED0`` runs the noise routine ``$464A``) and bit 3 of the flag byte the
   initial note mode. Nothing is read from the header by hand.
2. **Operand lengths** of the flag handlers are measured by running each handler from the dispatch table on random
   operand bytes and reading ``DE`` back; the controlled-routine result must be identical for six fills. The five
   control-flow handlers (stop, jump, loop, call, return) and the note-mode toggle are identified by their code bytes
   (``SIGNATURES``), not by position, and the tool fails if the ROM disagrees.
3. **Token walk** (static): a depth-first walk of every stream under the grammar the driver actually uses (tone:
   duration, ``$D8-$DF`` single byte, note with optional duration, custom three-byte note when mode 3; noise: duration,
   note with optional duration; both: ``$E0+`` flag with operands), following jumps, loops and calls, so the set of
   flag bytes that can reach the dispatcher is the set of ``$E0+`` tokens found.
4. **Dynamic cross-check**: the same driver run for up to 4,000 updates per request records every token fetch and every
   dispatched flag. Every fetch must be a position the static walk reached and every dispatched flag a flag it found.

The result is a ROM-derived domain for the flag byte; it is evidence for ``prove_dispatch(..., data_domain=...)`` and
never changes the code-defined domain the proof reports.
"""
import random
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

CHANNELS = (0xDE40, 0xDE70, 0xDEA0, 0xDED0, 0xDF00, 0xDF30, 0xDF60)
NOISE_CHANNEL = 0xDED0
REQUEST_IDS = range(0x81, 0xC5)
FLAG_TABLE = 0x46ED                 # CPU address of the flag dispatch table (word per flag $E0..$FF)
FILE_FROM_PTR = 0x4000              # stream pointers $4000-$BFFF are banks 2-3: file = ptr + $4000
WINDOW = (0x4000, 0xC000)
TONE_FETCH, NOISE_FETCH = 0x434F, 0x465A
FLAG_ENTRY_TONE, FLAG_ENTRY_NOISE = 0x46D5, 0x466B

# Code bytes (hex) that identify the control handlers; they are checked against the ROM, never assumed.
SIGNATURES = OrderedDict([
    ("jump", "eb5e23561bc9"),                                     # EX DE,HL / LD E,(HL) / INC HL / LD D,(HL) / DEC DE / RET
    ("loop", "13c6274f0600dde5e1097eb720021a771335c2b44713c9"),   # INC DE / ADD A,$27 / ... / DEC (HL) / JP NZ,$47B4
    ("call", "4f131a47c5dde5e1dd3509dd4e09dd3509060009722b73d11bc9"),
    ("return", "dde5e1dd4e090600095e2356dd3409dd3409c9"),
    ("stop", "dd7e01fea0"),                                       # LD A,(IX+1) / CP $A0 ...
    ("note_mode", "fe012005ddcb00dec9ddcb009ec9"),                # CP 1 / JR NZ / SET 3,(IX) / RET / RES 3,(IX) / RET
])
CONTROL_ORDER = ("stop", "jump", "loop", "call", "return")


class FlagSemanticsError(Exception):
    pass


def make_driver(rom):
    import z80
    cpu = z80.Z80Machine()
    mem = cpu.memory
    mem[0:0x4000] = rom[0:0x4000]
    mem[0x4000:0x8000] = rom[2 * 0x4000:3 * 0x4000]
    mem[0x8000:0xC000] = rom[3 * 0x4000:4 * 0x4000]
    return Driver(cpu, mem)


class Driver:
    RETURN = 0x0100

    def __init__(self, cpu, mem):
        self.cpu, self.mem = cpu, mem
        cpu.set_breakpoint(self.RETURN)
        self.tone, self.noise, self.flags = set(), set(), set()

    def call(self, addr, **regs):
        c = self.cpu
        c.pc, c.sp = addr, 0xDFE0
        for k, v in regs.items():
            setattr(c, k, v)
        self.mem[c.sp:c.sp + 2] = self.RETURN.to_bytes(2, "little")
        for _ in range(60):
            c.ticks_to_stop = 200000
            c.run()
            if c.pc == self.RETURN:
                return
        raise RuntimeError("call $%04X did not return (pc=$%04X)" % (addr, c.pc))

    def trace(self):
        c = self.cpu

        def read(addr):
            if addr == TONE_FETCH:
                self.tone.add(c.de)
            elif addr == NOISE_FETCH:
                self.noise.add(c.de)
            else:
                self.flags.add(c.a)
            return self.mem[addr]

        c.set_read_callback(read)
        for a in (TONE_FETCH, NOISE_FETCH, FLAG_ENTRY_TONE, FLAG_ENTRY_NOISE):
            c.mark_addr(a, c.READ_MARK)

    def request(self, rid):
        self.mem[0xDE00:0xDF90] = bytes(0x190)
        self.mem[0xDE03] = 0x80
        self.mem[0xDE04] = rid
        self.call(0x407F)
        self.call(0x4119)

    def active_channels(self):
        return [(b, self.mem[b + 3] | self.mem[b + 4] << 8, self.mem[b]) for b in CHANNELS if self.mem[b] & 0x80]


def stream_starts(rom):
    """{(pointer, grammar, mode): sorted [(request id, channel base)]} for every active channel of every request."""
    out = OrderedDict()
    for rid in REQUEST_IDS:
        d = make_driver(rom)
        d.request(rid)
        for base, ptr, flag in d.active_channels():
            key = (ptr, "noise" if base == NOISE_CHANNEL else "tone", 3 if flag & 8 else 0)
            out.setdefault(key, []).append((rid, base))
    return out


def word(rom, ptr):
    f = ptr + FILE_FROM_PTR
    return rom[f] | rom[f + 1] << 8


def flag_handlers(rom):
    t = FLAG_TABLE + FILE_FROM_PTR
    return OrderedDict((0xE0 + i, rom[t + 2 * i] | rom[t + 2 * i + 1] << 8) for i in range(32))


def measure_operands(rom, handlers):
    """Operand bytes consumed per flag (including the first, which the dispatcher loads into A), by running each
    handler. ``None`` for flags whose handler does not return to the dispatcher with a position-independent result."""
    out = OrderedDict()
    for flag, handler in handlers.items():
        results = set()
        for seed in range(6):
            rnd = random.Random(seed * 7 + flag)
            fill = [rnd.randrange(256) for _ in range(12)]
            d = make_driver(rom)
            d.mem[0xDE00:0xDF90] = bytes(0x190)
            for i, b in enumerate(fill):
                d.mem[0xC000 + i] = b
            d.cpu.ix = 0xDE40
            d.mem[0xDE49] = 0x24
            try:
                d.call(handler, de=0xC000, a=fill[0])
            except RuntimeError:
                results.add(None)
                continue
            n = d.cpu.de - 0xC000 + 1
            results.add(n if d.cpu.sp == 0xDFE2 and 0 <= n <= 8 else None)
        out[flag] = results.pop() if len(results) == 1 else None
    return out


def classify_handlers(rom, handlers):
    """{flag: control kind} identified by code bytes; raises when a signature does not match the ROM."""
    kinds = OrderedDict()
    for kind, sig in SIGNATURES.items():
        want = bytes.fromhex(sig)
        hits = [f for f, h in handlers.items() if bytes(rom[h + FILE_FROM_PTR:h + FILE_FROM_PTR + len(want)]) == want]
        if len(hits) != 1:
            raise FlagSemanticsError("handler signature %r matches flags %s" % (kind, [hex(h) for h in hits]))
        kinds[hits[0]] = kind
    return kinds


def walk_stream(rom, start, grammar, mode0, semantics, operands, consumed=None):
    """Depth-first token walk of one stream. Returns (token positions, {flag: positions}, problems); every byte a token
    occupies is added to ``consumed`` when given."""
    seen, flags, fetched, problems = set(), {}, set(), []
    stack = [(start, mode0)]
    eat = consumed.update if consumed is not None else (lambda _: None)
    while stack:
        pos, mode = stack.pop()
        while True:
            if (pos, mode) in seen:
                break
            seen.add((pos, mode))
            if not WINDOW[0] <= pos < WINDOW[1]:
                problems.append(("out_of_window", pos))
                break
            b = rom[pos + FILE_FROM_PTR]
            fetched.add(pos)
            if b >= 0xE0:
                flags.setdefault(b, set()).add(pos)
                kind = semantics.get(b)
                if kind in ("stop", "return"):
                    eat(range(pos, pos + 1))
                    break
                if kind == "jump":
                    eat(range(pos, pos + 3))
                    pos = word(rom, pos + 1)
                    continue
                if kind == "call":
                    eat(range(pos, pos + 3))
                    stack.append((pos + 3, mode))
                    pos = word(rom, pos + 1)
                    continue
                if kind == "loop":
                    eat(range(pos, pos + 5))
                    stack.append((word(rom, pos + 3), mode))
                    pos += 5
                    continue
                n = operands[b]
                if n is None:
                    problems.append(("unmeasured_flag", b, pos))
                    break
                if kind == "note_mode":
                    mode = 3 if rom[pos + 1 + FILE_FROM_PTR] == 1 else 0
                eat(range(pos, pos + 1 + n))
                pos += 1 + n
                continue
            start_of_token = pos
            if grammar == "tone" and mode == 3:          # custom note: high byte, low byte, duration
                pos += 3
            elif grammar == "tone" and b >= 0xD8:        # one-byte setting
                pos += 1
            elif b < 0x80:                               # duration
                pos += 1
            else:                                        # note or rest, optional duration (< $80)
                pos += 1
                if rom[pos + FILE_FROM_PTR] < 0x80:
                    pos += 1
            eat(range(start_of_token, pos))
    return fetched, flags, problems


def analyse(rom, dynamic_updates=4000):
    """The complete stream proof as an evidence dict (also usable as a ``data_domain``)."""
    handlers = flag_handlers(rom)
    semantics = classify_handlers(rom, handlers)
    operands = measure_operands(rom, handlers)
    starts = stream_starts(rom)
    tone, noise, flags, problems, consumed = set(), set(), {}, [], set()
    for (ptr, grammar, mode), who in starts.items():
        fetched, f, p = walk_stream(rom, ptr, grammar, mode, semantics, operands, consumed)
        (tone if grammar == "tone" else noise).update(fetched)
        for k, v in f.items():
            flags.setdefault(k, set()).update(v)
        problems.extend((hex(ptr), grammar, mode) + tuple(x) for x in p)
    seen = sorted(flags)
    dynamic = dynamic_check(rom, tone, noise, set(seen), dynamic_updates)
    out = OrderedDict()
    out["method"] = ("stream starts and operand lengths from the original driver on a Z80 core; token walk over the "
                     "ROM streams; cross-checked against a full controlled run of every request")
    out["requests"] = [REQUEST_IDS[0], REQUEST_IDS[-1]]
    out["stream_start_states"] = len(starts)
    out["distinct_pointers"] = len({k[0] for k in starts})
    out["flag_handlers"] = OrderedDict((hex(f), hex(h)) for f, h in handlers.items())
    out["control_flags"] = OrderedDict((hex(f), k) for f, k in sorted(semantics.items()))
    out["operand_bytes"] = OrderedDict((hex(f), n) for f, n in operands.items() if n is not None)
    out["flags_reaching_the_dispatcher"] = [hex(f) for f in seen]
    out["token_positions_walked"] = OrderedDict([("tone", len(tone)), ("noise", len(noise))])
    out["walk_problems"] = problems
    out["dynamic_cross_check"] = dynamic
    out["complete"] = not problems and dynamic["consistent"]
    out["values"] = set(seen) if out["complete"] else set(range(0xE0, 0x100))
    out["applies_to_unknown_loads"] = ["LD A,(DE)"]
    out["data_files"] = intervals([p + FILE_FROM_PTR for p in consumed])
    out["stream_bytes"] = len(consumed)
    return out


def intervals(offsets):
    """Merge file offsets into half-open [lo, hi) intervals."""
    out = []
    for o in sorted(set(offsets)):
        if out and out[-1][1] == o:
            out[-1][1] = o + 1
        else:
            out.append([o, o + 1])
    return [tuple(x) for x in out]


def dynamic_check(rom, tone, noise, flags, updates):
    miss_tone = miss_noise = 0
    flags_seen, looping = set(), 0
    for rid in REQUEST_IDS:
        d = make_driver(rom)
        d.trace()
        d.request(rid)
        n = 0
        for n in range(updates):
            d.call(0x4000)
            if not any(d.mem[b] & 0x80 for b in CHANNELS):
                break
        else:
            looping += 1
        miss_tone += len(d.tone - tone)
        miss_noise += len(d.noise - noise)
        flags_seen |= d.flags
    return OrderedDict([
        ("updates_per_request", updates), ("requests_still_playing_at_the_limit", looping),
        ("tone_fetches_outside_the_static_walk", miss_tone), ("noise_fetches_outside_the_static_walk", miss_noise),
        ("dispatched_flags", [hex(f) for f in sorted(flags_seen)]),
        ("dispatched_flags_outside_the_static_set", [hex(f) for f in sorted(flags_seen - flags)]),
        ("consistent", miss_tone == miss_noise == 0 and not (flags_seen - flags))])
