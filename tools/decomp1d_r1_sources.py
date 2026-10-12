"""DECOMP-1D-R1: supporting evidence for the two dispatchers whose index comes from game state, not from stream data.

Site B (ROM ``$08137``) dispatches on the sound-request byte ``$DE03``; site C (ROM ``$74027``) on the first byte of
four 8-byte slot records at ``$D452``. Both guards admit values the tables do not cover, so these dispatchers are
**proven only if the index provably never takes those values**. This module collects, from the ROM, every writer of the
index that can be enumerated, and states exactly which routes it cannot bound. It proves nothing by itself and never
widens a ``data_domain``: an unbounded route keeps the dispatcher partial.

Evidence tiers used below:

* ``enumerated``  an absolute store or immediate found by scanning every encoding in the ROM;
* ``bounded``     the value set is fixed by the ROM bytes that feed it;
* ``open``        the route exists and its value set is not bounded here (the reason is given).
"""
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import decomp1d_banked_flow as D  # noqa: E402
import rom_flow as F  # noqa: E402

MAILBOX = 0xDE04
LATCH = 0xD4A4
SOUND_TEST = 0xD2BF
FORBIDDEN = (0xC5, 0xD3)                 # request ids that reach site B's out-of-table words (inclusive)
ZONE, ACT = 0xD297, 0xD298
SLOTS = tuple(0xD452 + 8 * k for k in range(4))
MUSIC_TABLE = 0x18BA
RECORD_TABLE = 0x2A9A
FF_SUBCOMMAND_TABLE = 0x6696
OPERAND_WRITER = 0x67D5


def hx2(v):
    return "$%02X" % v


def hit(v, lo=FORBIDDEN[0], hi=FORBIDDEN[1]):
    return lo <= v <= hi


def prev_immediate(rom, off):
    """``LD A,n`` directly before the store at ``off`` (alignment-checked by decode), else None."""
    d = F.decode(rom, off - 2)
    if not F.is_invalid(d) and d.len == 2 and D.imm_load_a(d) is not None:
        return D.imm_load_a(d)
    return None


# routes whose A is not an `LD A,n` directly before the store: the bytes that must precede the store opcode (checked)
DYNAMIC_ROUTES = OrderedDict([
    (0x05CF, ("irq_forward", "3aa4d4b72807")),                             # LD A,($D4A4) / OR A / JR Z,+7
    (0x0C33, ("sound_test", "3abfd2")),                                      # LD A,($D2BF)
    (0x18B3, ("zone_music_table", "7e")),                                    # LD A,(HL) with HL = $18BA + 3*zone + act
    (0x48A3, ("boss_clear_music", "79")),                                    # LD A,C with C = $89 or $97
    (0x67E3, ("script_operand", "dd6e0edd660f7e23dd750edd740f")),            # LD A,(script pointer); INC pointer
    (0x67E6, ("script_operand_repeat", "3204de")),                           # the same store a second time
])
LATCH_ROUTES = OrderedDict([
    (0x05D3, ("latch_clear", "af")),                                         # XOR A: the latch is cleared
    (0x18B6, ("zone_music_table", "3204de")),                                # the table byte, stored to both
    (0x79AB0, ("boss_music", "3e8c3204de")),                                 # LD A,$8C / LD ($DE04),A
])


def _route_checks(rom, sites, routes):
    out = OrderedDict()
    for site in sites:
        entry = routes.get(site)
        if entry is None:
            out[site] = "unclassified"
            continue
        name, prefix = entry
        want = bytes.fromhex(prefix)
        out[site] = name if bytes(rom[site - len(want):site]) == want else "pattern_mismatch:" + name
    return out


def request_sources(rom, ledger_ids=None):
    sites = [(o, k) for o, k in D.store_pattern_sites(rom, MAILBOX, 1)]
    wide = [(o, k) for o, k in D.store_pattern_sites(rom, MAILBOX, 2) if k != "LD (nn),A"]   # stores at $DE03/$DE04
    latch = [(o, k) for o, k in D.store_pattern_sites(rom, LATCH, 1)]
    immediates, dynamic = OrderedDict(), []
    for o, k in sorted(sites):
        v = prev_immediate(rom, o)
        if v is None:
            dynamic.append(o)
        else:
            immediates.setdefault(v, []).append(o)
    latch_imm, latch_dyn = OrderedDict(), []
    for o, k in sorted(latch):
        v = prev_immediate(rom, o)
        (latch_imm.setdefault(v, []).append(o) if v is not None else latch_dyn.append(o))
    checks = _route_checks(rom, dynamic, DYNAMIC_ROUTES)
    latch_checks = _route_checks(rom, latch_dyn, LATCH_ROUTES)
    out = OrderedDict()
    out["mailbox"] = MAILBOX
    out["absolute_store_sites"] = len(sites)
    out["wide_store_sites"] = [o for o, _ in wide]
    out["immediate_values"] = [hx2(v) for v in sorted(immediates)]
    out["immediate_sites"] = sum(len(v) for v in immediates.values())
    out["immediate_values_in_forbidden_range"] = [hx2(v) for v in sorted(immediates) if hit(v)]
    out["immediate_values_missing_from_audio0_ledger"] = (
        [hx2(v) for v in sorted(immediates) if v not in ledger_ids and v != 0] if ledger_ids is not None else None)
    out["dynamic_sites"] = [OrderedDict([("offset", s), ("route", checks[s])]) for s in dynamic]
    out["latch_sites"] = OrderedDict([("offsets", [o for o, _ in latch]),
                                      ("immediate_values", [hx2(v) for v in sorted(latch_imm)]),
                                      ("dynamic", [OrderedDict([("offset", s), ("route", latch_checks[s])]) for s in latch_dyn])])
    # zone music table: contents for the indices the table defines, and where the table ends
    table = list(rom[MUSIC_TABLE:MUSIC_TABLE + 39])
    nxt = rom[MUSIC_TABLE + 39:MUSIC_TABLE + 42]
    out["zone_music_table"] = OrderedDict([
        ("base", MUSIC_TABLE), ("entries", 39), ("values", [hx2(v) for v in sorted(set(table))]),
        ("in_forbidden_range", [hx2(v) for v in sorted(set(table)) if hit(v)]),
        ("first_bytes_after_the_table", nxt.hex()),
        ("index", "L = 3*$D297 + $D298 (8-bit), so bytes past the 39th are code bytes unless zone and act are bounded")])
    # script operand route
    ff06 = []
    i = rom.find(b"\xff\x06")
    while i != -1:
        if i + 2 < len(rom):
            ff06.append(rom[i + 2])
        i = rom.find(b"\xff\x06", i + 1)
    sub6 = rom[FF_SUBCOMMAND_TABLE + 12] | rom[FF_SUBCOMMAND_TABLE + 13] << 8
    out["script_operand_route"] = OrderedDict([
        ("subcommand_table_word_6", sub6), ("handler", OPERAND_WRITER), ("handler_is_subcommand_6", sub6 == OPERAND_WRITER),
        ("ff06_sequences_in_rom", len(ff06)), ("operands_in_forbidden_range", sorted(hx2(v) for v in set(ff06) if hit(v))),
        ("rule", "the handler reads the byte after the FF 06 pair, so a forbidden id needs FF 06 followed by it in the ROM")])
    # boss-clear route
    out["boss_clear_route"] = OrderedDict([("values", [hx2(rom[0x4897 + 1]), hx2(rom[0x48A0 + 1])]),
                                           ("sites", [0x4897, 0x48A0])])
    return out


def sound_test_clamp(rom):
    """The sound-test selection routine clamps its value before storing it; report the stores and the clamp bytes."""
    clamp = bytes(rom[0x0BBA:0x0BCC])
    return OrderedDict([("stores_to_d2bf", [o for o, _ in D.store_pattern_sites(rom, SOUND_TEST, 1)]),
                        ("clamp_code", clamp.hex()),
                        ("stored_range", "$80-$C4 and $FF: CP $FF / JP Z; CP $C5 / JP C store; $C5 -> $FF, above -> $C4")])


def slot_type_sources(rom):
    stores = []
    for a in SLOTS:
        stores += [(o, a) for o, k in D.store_pattern_sites(rom, a, 1)]
        stores += [(o, a) for o, k in D.store_pattern_sites(rom, a, 2) if k != "LD (nn),A"]   # 16-bit stores at a-1 and a
    first = [rom[RECORD_TABLE + 2 * i] | rom[RECORD_TABLE + 2 * i + 1] << 8 for i in range(16)]
    records = sorted({rom[s + 2 * j] | rom[s + 2 * j + 1] << 8 for s in first for j in range(3)})
    types = sorted({t for r in records for t in rom[r + 6:r + 10]})
    callers = []
    i = rom.find(b"\xcd\x74\x03")
    while i != -1:
        callers.append((i, rom[i - 1] if rom[i - 2] == 0x0E else None))
        i = rom.find(b"\xcd\x74\x03", i + 1)
    direct = rom.find(b"\xcd\xd3\x1c")
    return OrderedDict([
        ("slot_bytes", ["$%04X" % a for a in SLOTS]),
        ("absolute_stores", [OrderedDict([("offset", o), ("slot", "$%04X" % a)]) for o, a in sorted(set(stores))]),
        ("record_table", OrderedDict([("first_level_words", 16), ("records", len(records)),
                                      ("record_addresses", ["$%04X" % r for r in records]),
                                      ("types_in_records", types),
                                      ("record_fetch_requires", "zone $D297 <= 15 and act $D298 <= 2 when the level loader runs")])),
        ("allocator", OrderedDict([
            ("entry", 0x1CD3), ("vector", 0x0374),
            ("direct_call_sites", [OrderedDict([("offset", direct), ("c", rom[direct - 1])])]),
            ("vector_call_sites", [OrderedDict([("offset", o), ("c", c)]) for o, c in callers]),
            ("c_values_at_direct_sites", sorted({rom[direct - 1]} | {c for _, c in callers if c is not None})),
            ("other_ways_to_reach_the_vector", "the 16-bit value $0374 also occurs as data; callback stubs can enter "
                                              "it with whatever C the caller holds, so its C values are not enumerated")]))])
