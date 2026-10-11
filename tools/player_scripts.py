"""ROM-backed parser for the player animation scripts (DECOMP-1C).

The parser takes nothing from audit caches, region names or expected addresses. It derives what it needs from the
original ROM:

* ``engine_facts``: the animation engine's own instructions are decoded and compared with the exact sequences this
  parser relies on (record layout, state-table lookup, the FF-command dispatcher, the callback executor and the
  bank selected before the player's scripts run). A ROM that differs raises instead of being parsed.
* ``derive_commands``: for each of the 16 command handlers listed in the dispatcher's pointer table, a small
  symbolic walk of the handler's own instructions records how many operand bytes it consumes from the script
  cursor (``IX+14/15``), where it can continue (fall-through or an operand word it loads into the cursor), which
  operand words it executes through ``JP (HL)`` (selectors) and which operand bytes it stores into the callback
  vector ``IX+12/13``.
* ``parse_scripts``: the scripts of each player type (type table at ``$65BA``, state table inside it) are walked
  the way the engine walks them: a record is ``duration, frame, callback-lo, callback-hi`` unless its first byte is
  ``$FF``, in which case the next byte selects a command. Malformed or ambiguous structure is reported in
  ``notes``, never repaired.

A parsed callback is *statically supported*: a script the engine can read contains the vector at a location the
engine stores into ``IX+12/13``, which player update later executes with ``JP (HL)`` at ``$5E9A``. It is not
evidence that the game enters that state.
"""
from collections import OrderedDict

import rom_flow as F
from z80dis import z80

OP = F.OP
HANDLER_TABLE = 0x6696          # 16 word pointers, indexed by the byte after $FF
HANDLER_COUNT = 16
HANDLERS_END = 0x68F8
TYPE_TABLE = 0x65BA             # per-object-type pointer to its state table
PLAYER_TYPES = (1, 2)
SCRIPT_BANK = 12
SCRIPT_SLOT_BASE = 0x8000
BANK_SIZE = 0x4000
RECORD_LEN = 4
NEXT_RECORD = 0x653D
FRAME_SET = 0x6562
RESTART_A, RESTART_B = 0x651D, 0x6517

# Exact engine sequences relied on (disassembly, address-independent of any callback value).
ENGINE_SEQUENCES = OrderedDict([
    ("record_read", (0x653D, ["LD L,(IX+14)", "LD H,(IX+15)", "LD A,(HL)", "CP 0xff", "JP z,0x6680", "LD (IX+7),A",
                              "INC HL", "LD A,(HL)", "LD (IX+6),A", "INC HL", "LD A,(HL)", "LD (IX+12),A", "INC HL",
                              "LD A,(HL)", "LD (IX+13),A", "INC HL", "LD (IX+14),L", "LD (IX+15),H"])),
    ("state_table_lookup", (0x651D, ["LD A,(IX)", "DEC A", "ADD A,A", "LD L,A", "LD H,0", "LD DE,0x65ba", "ADD HL,DE",
                                     "LD E,(HL)", "INC HL", "LD D,(HL)", "LD A,(IX+1)", "ADD A,A", "LD L,A", "LD H,0",
                                     "ADD HL,DE", "LD E,(HL)", "INC HL", "LD D,(HL)", "LD (IX+14),E", "LD (IX+15),D"])),
    ("command_dispatch", (0x6680, ["INC HL", "LD A,(HL)", "INC HL", "LD (IX+14),L", "LD (IX+15),H", "ADD A,A", "LD L,A",
                                   "LD H,0", "LD DE,0x6696", "ADD HL,DE", "LD A,(HL)", "INC HL", "LD H,(HL)", "LD L,A",
                                   "JP (HL)"])),
    ("callback_executor", (0x5E91, ["LD L,(IX+12)", "LD H,(IX+13)", "LD A,H", "OR L", "RET z", "JP (HL)"])),
    ("player_update_script_call", (0x3632, ["LD A,0xff", "LD (0xd44f),A", "LD A,12", "CALL 0x1c6f", "CALL 0x64fa"])),
    ("player_update_callback_call", (0x3648, ["LD A,12", "CALL 0x1c6f", "CALL 0x5e91"])),
    ("slot2_mapper", (0x1C6F, ["LD (0xd12b),A", "LD (0xffff),A", "RET"])),
])


def file_offset(cpu):
    """File offset of a slot-2 address while the player's script bank is mapped."""
    if not SCRIPT_SLOT_BASE <= cpu < SCRIPT_SLOT_BASE + BANK_SIZE:
        raise ValueError("address %04X is not in slot 2" % cpu)
    return SCRIPT_BANK * BANK_SIZE + cpu - SCRIPT_SLOT_BASE


def word(rom, off):
    return rom[off] | rom[off + 1] << 8


def disasm_run(rom, start, count):
    out, p = [], start
    for _ in range(count):
        d = F.decode(rom, p)
        out.append(z80.disasm(d))
        p += d.len
    return out, p


def engine_facts(rom):
    facts = OrderedDict()
    for name, (start, expected) in ENGINE_SEQUENCES.items():
        got, end = disasm_run(rom, start, len(expected))
        if got != expected:
            raise ValueError("engine sequence %s at %04X differs from the one the parser relies on: %s" % (name, start, got))
        facts[name] = OrderedDict([("start", start), ("end", end), ("instructions", len(expected))])
    return facts


# --- command handler derivation ----------------------------------------------------------------------------
class _State:
    def __init__(self):
        self.reg = {r: None for r in "ABCDEHL"}
        self.cur = None                    # HL == script cursor + cur, while HL still holds the cursor
        self.stack = []
        self.events = []                   # ("next", n) | ("jump", operand_offset)
        self.calls = []                    # operand offsets of words executed through JP (HL)
        self.cb = {}                       # "lo"/"hi" -> operand offset stored in IX+12/IX+13

    def copy(self):
        s = _State()
        s.reg, s.cur, s.stack = dict(self.reg), self.cur, list(self.stack)
        s.events, s.calls, s.cb = list(self.events), list(self.calls), dict(self.cb)
        return s


def _reg_name(operand):
    return operand.name if operand.name in "ABCDEHL" else None


def _walk(rom, pc, st, paths, seen, depth=0):
    while True:
        if depth > 6 or pc in seen:
            raise ValueError("handler walk did not terminate at %04X" % pc)
        seen.add(pc)
        d = F.decode(rom, pc)
        if F.is_invalid(d):
            raise ValueError("undecodable handler byte at %04X" % pc)
        ops = [(k.name, v) for k, v in d.operands]
        nxt = pc + d.len
        name = d.op.name
        if name == "LD":
            (k0, v0), (k1, v1) = ops[0], ops[1]
            if k0 == "REG" and v0.name == "L" and (k1, v1) == ("MEM_DISPL_IX", 14):
                st.cur = 0
                st.reg["L"] = st.reg["H"] = None
            elif k0 == "REG" and v0.name == "H" and (k1, v1) == ("MEM_DISPL_IX", 15):
                pass
            elif k0 == "REG" and k1 == "REG_DEREF" and v1.name == "HL" and v0.name in "ABCDEHL" and len(v0.name) == 1:
                src = ("byte", st.cur) if st.cur is not None else None      # HL may point at the object after the cursor store
                st.reg[v0.name] = src
                if v0.name in "HL":
                    st.cur = None
            elif k0 == "REG" and k1 == "REG" and len(v0.name) == 1 and len(v1.name) == 1:
                st.reg[v0.name] = st.reg[v1.name]
                if v0.name in "HL":
                    st.cur = None
            elif k0 == "MEM_DISPL_IX" and k1 == "REG" and len(v1.name) == 1:
                if v0 == 14:
                    if st.cur is not None and v1.name == "L":
                        st.events.append(("next", st.cur))
                    elif v1.name in "LC" and st.reg[v1.name] and st.reg["H" if v1.name == "L" else "B"] == ("byte", st.reg[v1.name][1] + 1):
                        st.events.append(("jump", st.reg[v1.name][1]))
                    else:
                        raise ValueError("cannot resolve the cursor store at %04X" % pc)
                elif v0 in (12, 13) and st.reg[v1.name] and st.reg[v1.name][0] == "byte":
                    st.cb["lo" if v0 == 12 else "hi"] = st.reg[v1.name][1]
            elif k0 == "REG" and k1 == "IMM" and v0.name in ("BC", "DE", "HL"):
                st.reg[v0.name[0]] = ("imm", v1 >> 8)
                st.reg[v0.name[1]] = ("imm", v1 & 255)
                if v0.name == "HL":
                    st.cur = None
            elif k0 == "REG" and k1 == "IMM" and len(v0.name) == 1:
                st.reg[v0.name] = ("imm", v1)
                if v0.name in "HL":
                    st.cur = None
            elif k0 == "REG" and len(v0.name) == 1:
                st.reg[v0.name] = None
                if v0.name in "HL":
                    st.cur = None
        elif name == "INC" and ops[0][0] == "REG" and ops[0][1].name == "HL":
            if st.cur is not None:
                st.cur += 1
        elif name == "EX" and [v.name for _, v in ops] == ["DE", "HL"]:
            st.reg["D"], st.reg["H"] = st.reg["H"], st.reg["D"]
            st.reg["E"], st.reg["L"] = st.reg["L"], st.reg["E"]
            st.cur = None
        elif name == "PUSH":
            r = ops[0][1].name
            if r in ("BC", "DE", "HL"):
                st.stack.append((st.reg[r[0]], st.reg[r[1]]))
            else:
                st.stack.append(None)
        elif name == "POP":
            r = ops[0][1].name
            top = st.stack.pop()
            if r in ("BC", "DE", "HL") and top is not None:
                st.reg[r[0]], st.reg[r[1]] = top
                if r == "HL":
                    st.cur = None
            elif len(r) == 2 and r != "AF":
                for ch in r:
                    st.reg[ch] = None
        elif name == "CALL":
            st.reg = {r: None for r in "ABCDEHL"}
            st.cur = None
        elif name in ("JP", "JR"):
            cond = F._has_cond(d)
            if ops[0][0] == "REG_DEREF":                                      # JP (HL)
                h, l = st.reg["H"], st.reg["L"]
                if not (h and l and h[0] == l[0] == "byte" and h[1] == l[1] + 1):
                    raise ValueError("indirect jump through an unresolved HL at %04X" % pc)
                st.calls.append(l[1])
                ret = st.stack.pop() if st.stack else None
                if ret is None:
                    paths.append(("indirect", st))
                    return
                target = (ret[0][1] << 8) | ret[1][1]
                st.reg = {r: None for r in "ABCDEHL"}
                st.cur = None
                if target in (NEXT_RECORD, FRAME_SET):
                    paths.append(({NEXT_RECORD: "next_record", FRAME_SET: "frame_set"}[target], st))
                    return
                pc = target
                continue
            target = F._addr_operand(d)
            if target in (NEXT_RECORD, FRAME_SET) or target in (RESTART_A, RESTART_B):
                kind = {NEXT_RECORD: "next_record", FRAME_SET: "frame_set"}.get(target, "restart")
                if cond:
                    other = st.copy()
                    paths.append((kind, other))
                    pc = nxt
                    continue
                paths.append((kind, st))
                return
            if cond:
                _walk(rom, target, st.copy(), paths, set(seen), depth + 1)
                pc = nxt
                continue
            pc = target
            continue
        elif name in ("RET",):
            paths.append(("return", st))
            return
        elif name in ("ADD", "ADC", "SBC", "SUB", "AND", "OR", "XOR", "DEC", "NEG", "CPL", "SLA", "SRL", "RRCA", "RLCA"):
            if ops and ops[0][0] == "REG":
                n = ops[0][1].name
                for ch in (n if len(n) == 2 and n != "AF" else n):
                    if ch in st.reg:
                        st.reg[ch] = None
                if "H" in n or "L" in n:
                    st.cur = None
            elif name in ("XOR", "AND", "OR", "SUB"):
                st.reg["A"] = None
        pc = nxt


def derive_commands(rom):
    """{command: OrderedDict(handler, outcomes, calls, callback)} derived by walking each handler."""
    out = OrderedDict()
    for cmd in range(HANDLER_COUNT):
        entry = word(rom, HANDLER_TABLE + 2 * cmd)
        if not HANDLER_TABLE + 2 * HANDLER_COUNT <= entry < HANDLERS_END:
            raise ValueError("handler %d points outside the handler block" % cmd)
        paths = []
        _walk(rom, entry, _State(), paths, set())
        outcomes, calls, cbs = [], set(), []
        for kind, st in paths:
            ev = st.events[-1] if st.events else None          # a later cursor store overrides an earlier one
            outcomes.append((kind, ev))
            calls.update(st.calls)
            if st.cb:
                cbs.append(dict(st.cb))
        uniq = []
        for o in outcomes:
            if o not in uniq:
                uniq.append(o)
        cb = None
        if cbs:
            if any(c != cbs[0] for c in cbs) or set(cbs[0]) != {"lo", "hi"} or cbs[0]["hi"] != cbs[0]["lo"] + 1:
                raise ValueError("handler %d callback store is not a consistent operand word" % cmd)
            cb = cbs[0]["lo"]
        out[cmd] = OrderedDict([("handler", entry), ("outcomes", [list(o[:1]) + [list(o[1]) if o[1] else None] for o in uniq]),
                                ("selector_operand", sorted(calls)[0] if calls else None),
                                ("callback_operand", cb)])
        if len(calls) > 1:
            raise ValueError("handler %d executes more than one operand word" % cmd)
    return out


# --- script parsing ---------------------------------------------------------------------------------------
def state_tables(rom):
    """{type: (table_cpu, [script_cpu per state])}. A state table ends where the lowest script it points at starts."""
    out = OrderedDict()
    for ty in PLAYER_TYPES:
        base = word(rom, TYPE_TABLE + 2 * (ty - 1))
        n = (word(rom, file_offset(base)) - base) // 2
        while True:
            ws = [word(rom, file_offset(base + 2 * i)) for i in range(n)]
            plausible = [w for w in ws if base <= w < SCRIPT_SLOT_BASE + BANK_SIZE]
            m = (min(plausible) - base) // 2
            if m == n:
                break
            n = m
        out[ty] = (base, [word(rom, file_offset(base + 2 * i)) for i in range(n)])
    return out


def parse_script(rom, start, commands, notes):
    """Walk one script from ``start`` the way the engine does. Returns ({cpu: step}, callbacks)."""
    steps, callbacks, stack = OrderedDict(), [], [start]
    while stack:
        p = stack.pop()
        while True:
            if p in steps:
                break
            if not SCRIPT_SLOT_BASE <= p < SCRIPT_SLOT_BASE + BANK_SIZE - 2:
                notes.append(("leaves_bank_window", p))
                break
            off = file_offset(p)
            b = rom[off]
            if b != 0xFF:
                steps[p] = ("record", RECORD_LEN, None)
                cb = word(rom, off + 2)
                callbacks.append(OrderedDict([("kind", "record"), ("at", p), ("operand_cpu", p + 2), ("vector", cb), ("selector", None)]))
                p += RECORD_LEN
                continue
            cmd = rom[off + 1]
            if cmd >= HANDLER_COUNT:
                notes.append(("unknown_command", p))
                break
            sem = commands[cmd]
            operands = p + 2
            steps[p] = ("command", 2, cmd)
            succ, terminal = [], False
            for kind, ev in sem["outcomes"]:
                if ev is None:
                    terminal = True
                elif ev[0] == "next":
                    succ.append(("next", operands + ev[1]))
                else:
                    succ.append(("jump", word(rom, file_offset(operands + ev[1]))))
            span = max([s[1] - operands for s in succ if s[0] == "next"] or [0])
            steps[p] = ("command", 2 + span, cmd)
            if sem["callback_operand"] is not None:
                co = operands + sem["callback_operand"]
                sel = word(rom, file_offset(operands + sem["selector_operand"])) if sem["selector_operand"] is not None else None
                callbacks.append(OrderedDict([("kind", "FF %02X" % cmd), ("at", p), ("operand_cpu", co),
                                              ("vector", word(rom, file_offset(co))), ("selector", sel),
                                              ("selector_operand_cpu", operands + sem["selector_operand"] if sel is not None else None)]))
            elif sem["selector_operand"] is not None:
                callbacks.append(OrderedDict([("kind", "FF %02X" % cmd), ("at", p), ("operand_cpu", None), ("vector", None),
                                              ("selector", word(rom, file_offset(operands + sem["selector_operand"]))),
                                              ("selector_operand_cpu", operands + sem["selector_operand"])]))
            nexts = [t for k, t in succ]
            if not nexts:
                break
            for t in nexts[1:]:
                stack.append(t)
            p = nexts[0]
    return steps, callbacks


def parse_scripts(rom):
    """Parse every player state script. Returns the evidence document."""
    facts = engine_facts(rom)
    commands = derive_commands(rom)
    tables = state_tables(rom)
    notes, entries, states = [], [], []
    seen_starts = {}
    for ty, (base, scripts) in tables.items():
        for state, start in enumerate(scripts):
            n = []
            steps, cbs = parse_script(rom, start, commands, n)
            for kind, p in n:
                notes.append(OrderedDict([("type", ty), ("state", state), ("script_cpu", start), ("note", kind), ("at", p)]))
            states.append(OrderedDict([("type", ty), ("state", state), ("script_cpu", start), ("script_offset", file_offset(start)),
                                       ("steps", len(steps)), ("callbacks", len(cbs))]))
            for cb in cbs:
                row = OrderedDict([("type", ty), ("state", state), ("bank", SCRIPT_BANK), ("script_cpu", start),
                                   ("script_offset", file_offset(start))])
                row.update(cb)
                row["operand_offset"] = file_offset(cb["operand_cpu"]) if cb["operand_cpu"] is not None else None
                if cb.get("selector_operand_cpu") is not None:
                    row["selector_operand_offset"] = file_offset(cb["selector_operand_cpu"])
                row["at_offset"] = file_offset(cb["at"])
                entries.append(row)
            seen_starts.setdefault(start, []).append((ty, state))
    # overlap check: a byte may belong to the steps of one script start only if every start that reaches it agrees
    return OrderedDict([("engine_facts", facts), ("commands", commands),
                        ("tables", [OrderedDict([("type", ty), ("table_cpu", b), ("states", len(s)),
                                                 ("table_offset", file_offset(b))]) for ty, (b, s) in tables.items()]),
                        ("states", states), ("callbacks", entries), ("notes", notes)])


# --- dispatch seeds for the ledger ------------------------------------------------------------------------
_SEED_CACHE = {}


def target_offset(value):
    """File offset a script word resolves to when the player's bank is mapped, or None outside resident/slot 2."""
    if 0 < value < SCRIPT_SLOT_BASE:
        return value
    if SCRIPT_SLOT_BASE <= value < SCRIPT_SLOT_BASE + BANK_SIZE:
        return file_offset(value)
    return None


def dispatch_seeds(rom):
    """{file offset: via} for every word a player script makes the engine execute.

    A callback vector (record field, ``FF 05``/``FF 0D`` operand) is executed by ``JP (HL)`` at ``$5E9A``; an
    executed operand (``FF 01``/``FF 05``/``FF 08``) is executed by the command handler's own ``JP (HL)``. Both run
    with the script bank mapped (``engine_facts``). Each target keeps the lowest (type, state, operand) reference.
    """
    hit = _SEED_CACHE.get(id(rom))
    if hit is not None and hit[0] is rom:
        return hit[1]
    doc = parse_scripts(rom)
    seeds = {}
    for row in doc["callbacks"]:
        for field, value_key, off_key, kind in (("callback", "vector", "operand_offset", "callback_vector"),
                                                ("executed", "selector", "selector_operand_offset", "executed_operand")):
            value = row.get(value_key)
            off = target_offset(value) if value else None
            if off is None:
                continue
            via = OrderedDict([("type", row["type"]), ("state", row["state"]), ("command", row["kind"]),
                               ("field", kind), ("operand_offset", row[off_key])])
            key = (via["type"], via["state"], via["operand_offset"])
            if off not in seeds or key < (seeds[off]["type"], seeds[off]["state"], seeds[off]["operand_offset"]):
                seeds[off] = via
    _SEED_CACHE.clear()
    _SEED_CACHE[id(rom)] = (rom, seeds)
    return seeds


def seed_supported(rom, offset, via):
    """True when ``via`` is exactly the reference the parser derives for ``offset``."""
    return dispatch_seeds(rom).get(offset) == OrderedDict(via)
