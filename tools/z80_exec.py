"""A deliberately small, fail-closed Z80 executor for straight-line dispatch blocks (DECOMP-1D-R1).

This is not an emulator. It runs a handful of ALU/load/branch instructions over *concrete* register values read from the
ROM image under a given slot-1 / slot-2 bank mapping, so that the exact destination of a computed jump such as::

    LD A,(IY) / ADD A,A / LD L,A / LD H,0 / LD DE,$8028 / ADD HL,DE / LD E,(HL) / INC HL / LD D,(HL) / EX DE,HL / JP (HL)

can be computed for every possible value of the index register instead of being guessed from neighbouring data words.

Rules (any violation raises ``Unmodelled`` so a proof can never silently rest on a guess):

* a register is either a concrete byte or unknown (``None``); using an unknown value as an address, a branch condition
  or a stored mapper value raises;
* memory reads succeed only for ROM addresses ($0000-$BFFF, through the supplied bank mapping); RAM reads give an unknown
  value, RAM writes are ignored (their effect on later RAM reads is therefore never assumed: such reads are unknown);
* writes to the mapper registers ($FFFC-$FFFF) raise;
* flags are tracked only as C, Z and S; an instruction whose flag outcome cannot be computed exactly clears them, and a
  conditional branch on a cleared flag raises;
* 8-bit arithmetic wraps modulo 256 and sets the carry exactly like the Z80 (``ADD A,A`` of $90 is $20 with carry set).
"""

from z80dis import z80

OP = z80.OP
R8 = tuple("ABCDEHL")
PAIRS = {"BC": "BC", "DE": "DE", "HL": "HL"}
FLAGS = ("C", "Z", "S")


class Unmodelled(Exception):
    """The executor cannot decide this step exactly."""


def _kind(operand):
    return operand[0].name


def _name(operand):
    return getattr(operand[1], "name", None)


class Machine:
    def __init__(self, rom, slot1_bank, slot2_bank):
        self.rom = rom
        self.slot1, self.slot2 = slot1_bank, slot2_bank
        self.reg = dict.fromkeys(R8)
        self.flag = dict.fromkeys(FLAGS)
        self.stack = []
        self.rom_reads = []          # (cpu address, file offset) of every ROM read
        self.ram_writes = []         # (kind, cpu address or None) of every ignored RAM write
        self.path = []               # file offsets of executed instructions, in order
        self.free_value = None       # mode 1: the value taken by the first load of an unknown byte into A
        self.free_taken = False
        self.free_at = None          # CPU address of the instruction that took it
        self.pc = None

    # --- memory ------------------------------------------------------------------------------------
    def file_of(self, cpu):
        if cpu < 0x4000:
            return cpu
        if cpu < 0x8000:
            return None if not isinstance(self.slot1, int) else self.slot1 * 0x4000 + cpu - 0x4000
        if cpu < 0xC000:
            return None if not isinstance(self.slot2, int) else self.slot2 * 0x4000 + cpu - 0x8000
        return None

    def read_byte(self, cpu):
        """ROM byte, or None for RAM (unknown)."""
        cpu &= 0xFFFF
        if cpu >= 0xC000:
            return None
        f = self.file_of(cpu)
        if f is None or f >= len(self.rom):
            raise Unmodelled("unmapped read $%04X" % cpu)
        self.rom_reads.append((cpu, f))
        return self.rom[f]

    # --- registers ---------------------------------------------------------------------------------
    def get16(self, name):
        if name in PAIRS:
            hi, lo = self.reg[name[0]], self.reg[name[1]]
            return None if hi is None or lo is None else hi << 8 | lo
        if name in ("SP", "IX", "IY", "AF"):
            return None
        raise Unmodelled("pair " + str(name))

    def set16(self, name, value):
        if name in PAIRS:
            if value is None:
                self.reg[name[0]] = self.reg[name[1]] = None
            else:
                self.reg[name[0]], self.reg[name[1]] = (value >> 8) & 0xFF, value & 0xFF
        elif name in ("SP", "IX", "IY"):
            pass                      # never used as an address by the supported blocks
        else:
            raise Unmodelled("pair " + str(name))

    def src8(self, operand):
        kind = _kind(operand)
        if kind == "REG":
            n = _name(operand)
            if n in R8:
                return self.reg[n]
            raise Unmodelled("8-bit source " + str(n))
        if kind == "IMM":
            return operand[1] & 0xFF
        if kind == "REG_DEREF":
            n = _name(operand)
            if n in PAIRS:
                addr = self.get16(n)
                return None if addr is None else self.read_byte(addr)      # unknown address: unknown value
            raise Unmodelled("read through " + str(n))
        if kind in ("MEM_DISPL_IX", "MEM_DISPL_IY"):
            return None
        if kind == "ADDR_DEREF":
            return self.read_byte(operand[1])
        raise Unmodelled("operand kind " + kind)

    def unknown_a(self):
        """A just received a value the executor cannot know. In free-load mode the first such event takes the enumerated
        value (an arbitrary byte); every other unknown stays unknown."""
        if self.free_value is not None and not self.free_taken:
            self.free_taken = True
            self.free_at = self.pc
            return self.free_value
        return None

    def need(self, value, what):
        if value is None:
            raise Unmodelled("unknown " + what)
        return value

    def set_flags(self, c=None, z=None, s=None):
        self.flag["C"], self.flag["Z"], self.flag["S"] = c, z, s

    def clear_flags(self):
        self.set_flags()

    # --- arithmetic --------------------------------------------------------------------------------
    def alu(self, op, rhs, carry_in=0):
        a = self.reg["A"]
        if a is None or rhs is None:
            if op != OP.CP:
                self.reg["A"] = self.unknown_a()
            self.clear_flags()
            return
        if op in (OP.ADD, OP.ADC):
            total = a + rhs + (carry_in if op == OP.ADC else 0)
            res, c = total & 0xFF, int(total > 0xFF)
        elif op in (OP.SUB, OP.SBC, OP.CP):
            total = a - rhs - (carry_in if op == OP.SBC else 0)
            res, c = total & 0xFF, int(total < 0)
        elif op == OP.AND:
            res, c = a & rhs, 0
        elif op == OP.OR:
            res, c = a | rhs, 0
        elif op == OP.XOR:
            res, c = a ^ rhs, 0
        else:
            raise Unmodelled("alu " + op.name)
        if op != OP.CP:
            self.reg["A"] = res
        self.set_flags(c, int(res == 0), res >> 7)

    # --- one instruction ---------------------------------------------------------------------------
    def condition(self, name):
        table = {"C": ("C", 1), "NOT_C": ("C", 0), "Z": ("Z", 1), "NOT_Z": ("Z", 0), "M": ("S", 1), "P": ("S", 0)}
        if name not in table:
            raise Unmodelled("condition " + str(name))
        flag, want = table[name]
        return self.need(self.flag[flag], "flag " + flag) == want

    def step(self, d, cpu):
        """Execute ``d`` at ``cpu``; returns ('next',) | ('goto', cpu) | ('site',) | ('return', cpu)."""
        op, ops = d.op, d.operands
        nxt = (cpu + d.len) & 0xFFFF
        if op in (OP.NOP, OP.DI, OP.EI, OP.OUT):
            return ("next",)
        if op == OP.LD:
            dst, src = ops
            dk, dn = _kind(dst), _name(dst)
            if dk == "REG" and dn in R8:
                value = self.src8(src)
                if value is None and dn == "A":
                    value = self.unknown_a()
                self.reg[dn] = value
            elif dk == "REG" and dn in PAIRS:
                if _kind(src) == "IMM":
                    self.set16(dn, src[1] & 0xFFFF)
                elif _kind(src) == "ADDR_DEREF":
                    lo, hi = self.read_byte(src[1]), self.read_byte(src[1] + 1)
                    self.set16(dn, None if lo is None or hi is None else hi << 8 | lo)
                else:
                    raise Unmodelled("16-bit load source")
            elif dk == "REG" and dn in ("SP", "IX", "IY"):
                pass
            elif dk == "ADDR_DEREF":
                if dst[1] >= 0xFFFC:
                    raise Unmodelled("mapper/mirror store $%04X" % dst[1])
                self.ram_writes.append(("abs", dst[1]))
            elif dk == "REG_DEREF":
                addr = self.get16(dn) if dn in PAIRS else None
                if addr is not None and addr >= 0xFFFC:
                    raise Unmodelled("mapper store")
                self.ram_writes.append(("reg", addr))
            elif dk in ("MEM_DISPL_IX", "MEM_DISPL_IY"):
                self.ram_writes.append(("index", dst[1]))
            else:
                raise Unmodelled("load form")
            return ("next",)
        if op in (OP.INC, OP.DEC):
            t = ops[0]
            delta = 1 if op == OP.INC else -1
            if _kind(t) == "REG" and _name(t) in R8:
                v = self.reg[_name(t)]
                if v is None:
                    self.flag["Z"] = self.flag["S"] = None
                else:
                    v = (v + delta) & 0xFF
                    self.reg[_name(t)] = v
                    self.flag["Z"], self.flag["S"] = int(v == 0), v >> 7
            elif _kind(t) == "REG" and _name(t) in PAIRS:
                v = self.get16(_name(t))
                self.set16(_name(t), None if v is None else (v + delta) & 0xFFFF)
            elif _kind(t) == "REG" and _name(t) in ("SP", "IX", "IY"):
                pass
            elif _kind(t) in ("MEM_DISPL_IX", "MEM_DISPL_IY", "REG_DEREF"):
                self.ram_writes.append(("rmw", None))
                self.flag["Z"] = self.flag["S"] = None
            else:
                raise Unmodelled("inc/dec form")
            return ("next",)
        if op in (OP.ADD, OP.ADC, OP.SBC, OP.SUB, OP.AND, OP.OR, OP.XOR, OP.CP):
            if len(ops) == 2 and _kind(ops[0]) == "REG" and _name(ops[0]) in ("HL",):
                hl = self.get16("HL")
                rr = _name(ops[1])
                other = self.get16(rr) if rr in PAIRS else None
                if rr not in PAIRS:
                    raise Unmodelled("16-bit ALU source " + str(rr))
                if hl is None or other is None:
                    self.set16("HL", None)
                    self.flag["C"] = self.flag["Z"] = self.flag["S"] = None
                    return ("next",)
                if op == OP.ADD:
                    total = hl + other
                    self.set16("HL", total & 0xFFFF)
                    self.flag["C"] = int(total > 0xFFFF)          # ADD HL,rr leaves Z and S alone
                elif op in (OP.ADC, OP.SBC):
                    carry = self.need(self.flag["C"], "carry")
                    total = hl + other + carry if op == OP.ADC else hl - other - carry
                    res = total & 0xFFFF
                    self.set16("HL", res)
                    self.set_flags(int(total > 0xFFFF) if op == OP.ADC else int(total < 0), int(res == 0), res >> 15)
                else:
                    raise Unmodelled("16-bit ALU op")
                return ("next",)
            rhs_operand = ops[-1]
            carry = self.flag["C"] if op in (OP.ADC, OP.SBC) else 0
            if op in (OP.ADC, OP.SBC) and carry is None:
                self.reg["A"] = self.unknown_a()
                self.clear_flags()
                return ("next",)
            if len(ops) == 2 and not (_kind(ops[0]) == "REG" and _name(ops[0]) == "A"):
                raise Unmodelled("ALU destination")
            self.alu(op, self.src8(rhs_operand), carry or 0)
            return ("next",)
        if op == OP.BIT:
            bit, target = ops
            v = self.src8(target) if _kind(target) in ("REG", "REG_DEREF", "MEM_DISPL_IX", "MEM_DISPL_IY") else None
            if v is None:
                self.flag["Z"] = None
            else:
                self.flag["Z"] = int(not (v >> bit[1]) & 1)
            self.flag["S"] = None
            return ("next",)
        if op in (OP.SET, OP.RES):
            bit, target = ops
            if _kind(target) == "REG" and _name(target) in R8:
                v = self.reg[_name(target)]
                if v is not None:
                    m = 1 << bit[1]
                    self.reg[_name(target)] = (v | m) if op == OP.SET else (v & ~m & 0xFF)
            else:
                self.ram_writes.append(("rmw", None))
            return ("next",)
        if op == OP.EX:
            names = {_name(o) for o in ops}
            if names == {"DE", "HL"}:
                de, hl = self.get16("DE"), self.get16("HL")
                self.set16("DE", hl)
                self.set16("HL", de)
                return ("next",)
            raise Unmodelled("EX form")
        if op == OP.PUSH:
            self.stack.append((self.get16(_name(ops[0])) if _name(ops[0]) in PAIRS else None, "push"))
            return ("next",)
        if op == OP.POP:
            if not self.stack:
                raise Unmodelled("POP with an empty modelled stack")
            v = self.stack.pop()[0]
            if _name(ops[0]) in PAIRS:
                self.set16(_name(ops[0]), v)
            elif _name(ops[0]) == "AF":
                self.reg["A"] = self.unknown_a()
                self.clear_flags()
            return ("next",)
        if op == OP.CALL:
            cond = [o for o in ops if _kind(o) == "COND"]
            if cond and not self.condition(_name(cond[0])):
                return ("next",)
            self.stack.append((nxt, "call"))
            return ("goto", [o for o in ops if _kind(o) == "ADDR"][0][1])
        if op == OP.RET:
            cond = [o for o in ops if _kind(o) == "COND"]
            if cond and not self.condition(_name(cond[0])):
                return ("next",)
            if not self.stack:
                return ("return", None)
            target = self.stack.pop()[0]
            if target is None:
                raise Unmodelled("RET to an unknown address")
            return ("goto", target)
        if op in (OP.JP, OP.JR):
            cond = [o for o in ops if _kind(o) == "COND"]
            addr = [o for o in ops if _kind(o) == "ADDR"]
            if not addr:                                  # JP (HL)
                return ("site",)
            if cond and not self.condition(_name(cond[0])):
                return ("next",)
            return ("goto", addr[0][1])
        if op == OP.DJNZ:
            b = self.need(self.reg["B"], "B")
            b = (b - 1) & 0xFF
            self.reg["B"] = b
            return ("goto", ops[0][1]) if b else ("next",)
        raise Unmodelled("instruction " + op.name)


class Run:
    """Result of executing from ``start`` for one initial value of the index register."""

    def __init__(self, outcome, detail, machine):
        self.outcome, self.detail, self.machine = outcome, detail, machine

    @property
    def hl(self):
        return self.machine.get16("HL")


def run(rom, slot1, slot2, start_cpu, site_cpu, a0, chain=None, limit=400, setup=None, free=False, cache=None):
    """Execute from ``start_cpu`` with A = ``a0`` until the ``JP (HL)`` at ``site_cpu`` (not executed).

    Outcomes: ``site`` (reached, ``Run.hl`` is the destination), ``off_chain`` (``chain`` is the set of CPU addresses the
    dominating chain occupies; a taken transfer, fall-through or return that leaves it at call depth 0 means this value
    does not reach the site in this activation) and ``unmodelled`` (cannot be decided exactly; never "does not reach").
    ``free`` selects mode 1 (see :meth:`Machine.unknown_a`)."""
    m = Machine(rom, slot1, slot2)
    if free:                        # mode 1: A is unknown at the start; the first unknown load of A takes ``a0``
        m.free_value = a0
    else:                           # mode 0: A holds ``a0`` at the start
        m.reg["A"] = a0
    for k, v in (setup or {}).items():
        m.reg[k] = v
    cpu, depth = start_cpu, 0
    for _ in range(limit):
        f = m.file_of(cpu)
        if f is None:
            return Run("unmodelled", "unmapped pc $%04X" % cpu, m)
        d = None if cache is None else cache.get((f, cpu))
        if d is None:
            d = z80.decode(bytes(rom[f:f + 4]), cpu)
            if cache is not None:
                cache[(f, cpu)] = d
        if not d.len or d.op == OP.NONI:
            return Run("unmodelled", "undecodable at $%04X" % cpu, m)
        if cpu == site_cpu:
            if not (d.op == OP.JP and not any(_kind(o) == "ADDR" for o in d.operands)):
                return Run("unmodelled", "site is not a computed jump", m)
            m.path.append(f)
            return Run("site", None, m)
        m.path.append(f)
        m.pc = cpu
        try:
            action = m.step(d, cpu)
        except Unmodelled as e:
            return Run("unmodelled", "%s at $%04X" % (e, cpu), m)
        if action[0] == "next":
            new = (cpu + d.len) & 0xFFFF
        elif action[0] == "goto":
            new = action[1]
            if d.op == OP.CALL:
                depth += 1
            elif d.op == OP.RET:
                depth -= 1
        elif action[0] == "return":
            return Run("off_chain" if chain is not None else "returned", "return", m)
        else:
            return Run("unmodelled", "another computed jump at $%04X" % cpu, m)
        if chain is not None and depth <= 0 and new not in chain:
            return Run("off_chain", "left the chain at $%04X" % new, m)
        cpu = new
    return Run("unmodelled", "step limit", m)
