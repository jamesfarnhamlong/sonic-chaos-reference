#!/usr/bin/env python3
"""DECOMP-1D-R1 tests: bounded proofs for computed jumps in the IM 1 handler's banked callees.

Synthetic tests build tiny ROM images with hand-assembled Z80 and never need the ROM. Tests that need the canonical
ROM skip without SONIC_CHAOS_ROM or ../source/Sonic Chaos (Europe).sms.
"""
import hashlib
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import decomp1d_banked_flow as D  # noqa: E402
import decomp1d_r1_closure as R  # noqa: E402
import decomp1d_r1_streams as ST  # noqa: E402
import rom_ledger as RL  # noqa: E402
import z80_exec as X  # noqa: E402

EVIDENCE = ROOT / "data" / "decomp1d" / "r1-interrupt-closure.json"
ROM_PATH = Path(os.environ.get("SONIC_CHAOS_ROM", str(RL.DEFAULT_ROM)))
SHADOW = 0xD12B


def canonical_rom():
    if ROM_PATH.is_file():
        data = ROM_PATH.read_bytes()
        if len(data) == RL.ROM_SIZE and hashlib.sha256(data).hexdigest() == RL.ROM_SHA256:
            return data
    return None


# --- a tiny assembler: only what the synthetic images need ---------------------------------------------------
def w(v):
    return bytes([v & 0xFF, v >> 8])


def ld_a_mem(addr):
    return b"\x3A" + w(addr)


def st_a(addr):
    return b"\x32" + w(addr)


def ld_a(n):
    return bytes([0x3E, n])


def and_n(n):
    return bytes([0xE6, n])


def sub_n(n):
    return bytes([0xD6, n])


def cp_n(n):
    return bytes([0xFE, n])


def jp(addr):
    return b"\xC3" + w(addr)


def jp_c(addr):
    return b"\xDA" + w(addr)


def jp_nc(addr):
    return b"\xD2" + w(addr)


def ld_de(addr):
    return b"\x11" + w(addr)


ADD_A_A = b"\x87"
LD_L_A = b"\x6F"
LD_H_0 = b"\x26\x00"
ADD_HL_DE = b"\x19"
FETCH = b"\x5E\x23\x56\xEB"          # LD E,(HL) / INC HL / LD D,(HL) / EX DE,HL
JP_HL = b"\xE9"
RET = b"\xC9"
FREE_LOAD_ASM = "LD A,(0xc100)"


def block(table, prelude=b""):
    """Index in A -> JP (HL) through the word table at CPU address ``table``."""
    return prelude + ADD_A_A + LD_L_A + LD_H_0 + ld_de(table) + ADD_HL_DE + FETCH + JP_HL


def words(*targets):
    return b"".join(w(t) for t in targets)


def image(blobs, size=0x10000):
    rom = bytearray(size)
    for at, blob in blobs.items():
        rom[at:at + len(blob)] = blob
    return bytes(rom)


class Facts:
    """Stands in for D.Facts: the resolver only reads the reset-walk's CPU contexts from it."""
    walk = {"cpu_at": {}}


def start_walk(rom, roots=((0x0100, 1, 3),), dispatch=None):
    return D.state_walk(rom, list(roots), SHADOW, dispatch=dispatch)


def universe_for(rom, roots=((0x0100, 1, 3),)):
    walk = start_walk(rom, roots)
    return R.Universe(rom, R.contexts_from(rom, [], walk), entries={D._mapped(r[0], r[1], r[2]) for r in roots}), walk


def prove(rom, site, roots=((0x0100, 1, 3),), s1=1, s2=3, data_domain=None):
    uni, _ = universe_for(rom, roots)
    return R.prove_dispatch(rom, site, uni, s1, s2, data_domain=data_domain)


def handlers(base, count, body=RET):
    """``count`` back-to-back handlers of ``body`` from ``base``; returns (blob, addresses)."""
    blob, addrs = b"", []
    for _ in range(count):
        addrs.append(base + len(blob))
        blob += body
    return blob, addrs


class ExecutorArithmetic(unittest.TestCase):
    def one(self, code, a0, start=0x0100):
        rom = image({start: code})
        return X.run(rom, 1, 3, start, start + len(code) - 1, a0)

    def test_add_a_a_drops_the_carry_so_the_index_wraps(self):
        # ADD A,A of $90 is $20 with carry set; the carry never reaches L, so $90 and $10 name the same table word
        code = ADD_A_A + LD_L_A + LD_H_0 + ld_de(0x0200) + ADD_HL_DE + JP_HL
        for a0, expect in ((0x10, 0x0220), (0x90, 0x0220), (0x7F, 0x02FE), (0xFF, 0x02FE)):
            r = self.one(code, a0)
            self.assertEqual((r.outcome, r.machine.get16("HL")), ("site", expect), hex(a0))

    def test_sub_sets_carry_and_the_conditional_jump_follows_it(self):
        code = sub_n(0xE0) + jp_c(0x0300) + b"\x00" + JP_HL           # leaves at 0x0300 when A < $E0
        rom = image({0x0100: code})
        chain = {0x0100, 0x0102, 0x0105, 0x0106}
        taken = X.run(rom, 1, 3, 0x0100, 0x0106, 0xDF, chain=chain)
        fell = X.run(rom, 1, 3, 0x0100, 0x0106, 0xE0, chain=chain)
        self.assertEqual((taken.outcome, fell.outcome), ("off_chain", "site"))

    def test_eight_bit_arithmetic_wraps_in_both_directions(self):
        up = self.one(b"\x3C" + b"\x6F" + LD_H_0 + JP_HL, 0xFF)       # INC A -> 0
        down = self.one(b"\x3D" + b"\x6F" + LD_H_0 + JP_HL, 0x00)     # DEC A -> $FF
        self.assertEqual((up.machine.get16("HL"), down.machine.get16("HL")), (0x0000, 0x00FF))

    def test_an_unknown_flag_fails_closed(self):
        rom = image({0x0100: b"\x3A" + w(0xC000) + jp_c(0x0300) + JP_HL})   # A is a RAM byte: the branch is undecidable
        r = X.run(rom, 1, 3, 0x0100, 0x0106, 0, chain={0x0100, 0x0103, 0x0106})
        self.assertEqual(r.outcome, "unmodelled")

    def test_a_mapper_write_is_refused(self):
        rom = image({0x0100: ld_a(5) + st_a(0xFFFF) + JP_HL})
        r = X.run(rom, 1, 3, 0x0100, 0x0105, 0)
        self.assertEqual(r.outcome, "unmodelled")
        self.assertIn("mapper", r.detail)

    def test_the_mirror_of_the_mapper_register_is_refused_too(self):
        rom = image({0x0100: ld_a(5) + st_a(0xFFFE) + JP_HL})
        self.assertEqual(X.run(rom, 1, 3, 0x0100, 0x0105, 0).outcome, "unmodelled")

    def test_rom_reads_follow_the_bank_mapping(self):
        code = b"\x21" + w(0x8000) + b"\x7E\x6F\x26\x00" + JP_HL
        rom = image({0x0100: code, 5 * 0x4000: b"\x34", 6 * 0x4000: b"\x56"}, size=8 * 0x4000)
        a = X.run(rom, 1, 5, 0x0100, 0x0107, 0)
        b = X.run(rom, 1, 6, 0x0100, 0x0107, 0)
        self.assertEqual((a.machine.get16("HL"), b.machine.get16("HL")), (0x0034, 0x0056))

    def test_ram_is_never_read_as_a_known_value(self):
        r = self.one(ld_a_mem(0xC123) + LD_L_A + LD_H_0 + JP_HL, 0x55)
        self.assertEqual((r.outcome, r.hl), ("site", None))           # the site is reached but HL stays unknown

    def test_a_pushed_return_address_is_reported_with_its_origin(self):
        rom = image({0x0100: b"\x21" + w(0x0200) + b"\xE5" + b"\x21" + w(0x0300) + JP_HL})
        r = X.run(rom, 1, 3, 0x0100, 0x0107, 0)
        self.assertEqual(r.machine.stack, [(0x0200, "push")])


def masked_table(guard=b"", count=4, mask=3, table_at=0x0160):
    """Free load of A from RAM, optional guard, optional mask, then the word dispatch over ``count`` handlers; four
    more valid-looking handlers follow the table. Returns (rom, site, handler addresses)."""
    pre = ld_a_mem(0xC100) + guard + (and_n(mask) if mask is not None else b"")
    code = block(table_at, pre)
    site = 0x0100 + len(code) - 1
    blob, addrs = handlers(table_at + 2 * count, count + 4)
    rom = image({0x0100: code, table_at: words(*addrs[:count]), table_at + 2 * count: blob, 0x0038: jp(0x0100)})
    return rom, site, addrs


try:
    import z80 as Z80CORE
except ImportError:                                  # the pinned core is in requirements.txt; skip rather than fail without it
    Z80CORE = None


@unittest.skipUnless(Z80CORE, "z80 core not installed")
class ExecutorMatchesTheCore(unittest.TestCase):
    """The executor's arithmetic and flags against the pinned Z80 core, for every value of A."""
    PROGRAMS = {
        "ADD A,$5C": b"\xC6\x5C", "ADD A,A": b"\x87", "SUB $E0": b"\xD6\xE0", "SUB $01": b"\xD6\x01", "CP $80": b"\xFE\x80",
        "CP $00": b"\xFE\x00", "AND $03": b"\xE6\x03", "AND $F0": b"\xE6\xF0", "OR $81": b"\xF6\x81", "XOR $FF": b"\xEE\xFF",
        "INC A": b"\x3C", "DEC A": b"\x3D", "OR A": b"\xB7", "XOR A": b"\xAF", "ADD A,B": b"\x80",
    }

    def core(self, code, a0, b0=0x37):
        cpu = Z80CORE.Z80Machine()
        cpu.memory[0x0100:0x0100 + len(code)] = code
        cpu.pc, cpu.a, cpu.b, cpu.f = 0x0100, a0, b0, 0
        cpu.set_breakpoint(0x0100 + len(code))
        cpu.ticks_to_stop = 1000
        cpu.run()
        return cpu.a, bool(cpu.f & 0x01), bool(cpu.f & 0x40), bool(cpu.f & 0x80)

    def test_alu_results_and_c_z_s_flags_match_for_every_a(self):
        rom = image({})
        for name, code in self.PROGRAMS.items():
            for a0 in range(256):
                m = X.Machine(rom, 1, 3)
                m.reg["A"], m.reg["B"] = a0, 0x37
                d = X.z80.decode(code + b"\x00\x00", 0x0100)
                m.step(d, 0x0100)
                want = self.core(code, a0)
                got = (m.reg["A"], bool(m.flag["C"]), bool(m.flag["Z"]), bool(m.flag["S"]))
                if name in ("INC A", "DEC A"):
                    want = (want[0], got[1], want[2], want[3])           # INC/DEC leave carry alone: compare the rest
                self.assertEqual(got, want, "%s with A=%02X" % (name, a0))

    def test_sixteen_bit_add_and_conditional_branches_match(self):
        rom = image({})
        for hl, de in ((0x0000, 0x0000), (0x7FFF, 0x0001), (0xFFFF, 0x0001), (0x1234, 0xEDCC), (0x8000, 0x8000), (0x00FE, 0x0102)):
            m = X.Machine(rom, 1, 3)
            m.set16("HL", hl)
            m.set16("DE", de)
            m.step(X.z80.decode(b"\x19\x00\x00", 0x0100), 0x0100)      # ADD HL,DE
            cpu = Z80CORE.Z80Machine()
            cpu.memory[0x0100] = 0x19
            cpu.pc, cpu.hl, cpu.de, cpu.f = 0x0100, hl, de, 0
            cpu.set_breakpoint(0x0101)
            cpu.ticks_to_stop = 100
            cpu.run()
            self.assertEqual((m.get16("HL"), bool(m.flag["C"])), (cpu.hl, bool(cpu.f & 1)), (hex(hl), hex(de)))


class BoundedTables(unittest.TestCase):
    def build(self, **kw):
        return masked_table(**kw)

    def test_a_mask_bounds_a_table_exactly(self):
        rom, site, addrs = self.build()
        p = prove(rom, site)
        self.assertEqual(p["status"], "proven", p["reasons"])
        self.assertEqual(p["supported_targets"], sorted(addrs[:4]))
        self.assertEqual(p["table"]["words_read"], 4)
        self.assertEqual(p["domain"]["count"], 256)               # every start value reaches the jump, only 4 words are read

    def test_words_beyond_the_mask_are_never_destinations(self):
        # four more valid-looking handlers follow the table; the mask makes them unreachable, so the walk never visits them
        rom, site, addrs = self.build()
        spec = R.dispatch_spec(prove(rom, site), include_partial=False)
        walk = start_walk(rom, dispatch={site: spec})
        for decoy in addrs[4:]:
            self.assertNotIn(decoy, walk["visited"])
        for good in addrs[:4]:
            self.assertIn(good, walk["visited"])

    def test_a_compare_guard_bounds_the_domain_before_the_wrap_can_matter(self):
        # CP 8 / JP NC,exit: only 0..7 reach the jump even though ADD A,A would wrap larger values
        rom, site, addrs = self.build(guard=cp_n(8) + jp_nc(0x0900), count=8, mask=None)
        p = prove(rom, site)
        self.assertEqual(p["status"], "proven", p["reasons"])
        self.assertEqual(p["domain"]["ranges"], ["$00-$07"])
        self.assertEqual(p["supported_targets"], sorted(addrs[:8]))

    def test_a_guard_that_admits_one_value_too_many_is_not_proven(self):
        rom, site, addrs = self.build(guard=cp_n(9) + jp_nc(0x0900), count=8, mask=None)
        p = prove(rom, site)
        self.assertEqual(p["domain"]["ranges"], ["$00-$08"])
        self.assertEqual(p["status"], "partial")
        self.assertEqual(p["unsupported_in_effective_domain"], ["$08"])

    def test_an_unguarded_index_aliases_values_128_apart_and_is_partial(self):
        rom, site, _ = self.build(mask=None, count=4)
        p = prove(rom, site)
        self.assertEqual(p["status"], "partial")
        self.assertEqual(p["domain"]["count"], 256)
        first = p["table"]["entries"][0]
        self.assertEqual(first["values"], ["$00", "$80"])            # the index and index+128 name the same word
        self.assertTrue(first["supported"])

    def test_valid_looking_words_outside_the_extent_are_unsupported(self):
        # words after the table are really handler bytes; they decode as code but lie inside the code region
        rom, site, _ = self.build(mask=None, count=4)
        entries = prove(rom, site)["table"]["entries"]
        past = [e for e in entries if e["word_cpu"] >= 0x0168]
        self.assertTrue(past)
        self.assertTrue(any(e["descent_ok"] for e in past), "the decoy words must at least look like code")
        self.assertTrue(all(not e["supported"] for e in past))
        self.assertTrue(all(not e["in_table_region"] for e in past))

    def test_a_partial_dispatch_never_becomes_a_complete_edge(self):
        rom, site, _ = self.build(mask=None)
        p = prove(rom, site)
        self.assertEqual(p["status"], "partial")
        self.assertIsNone(R.dispatch_spec(p, include_partial=False))
        spec = R.dispatch_spec(p, include_partial=True)
        self.assertFalse(spec["complete"])
        self.assertIn(("partial_dispatch", site), start_walk(rom, dispatch={site: spec})["open_edges"])

    def test_an_unlisted_computed_jump_stays_an_open_edge(self):
        rom, site, _ = self.build()
        walk = start_walk(rom)
        self.assertIn(("indirect_jump", site), walk["open_edges"])
        self.assertEqual(walk["indirect"], [site])

    def test_a_proven_dispatch_closes_the_edge(self):
        rom, site, _ = self.build()
        spec = R.dispatch_spec(prove(rom, site), include_partial=False)
        self.assertTrue(spec["complete"])
        walk = start_walk(rom, dispatch={site: spec})
        self.assertEqual([e for e in walk["open_edges"] if e[0] in ("indirect_jump", "partial_dispatch")], [])


class UnreachableJumps(unittest.TestCase):
    def test_a_guard_that_can_never_pass_makes_the_jump_unreachable(self):
        # A & 1 is at most 1, so CP 5 / JP NC never takes the branch into the dispatch block
        entry = ld_a_mem(0xC100) + and_n(1) + cp_n(5)
        body = block(0x0200)
        block_at = 0x0140
        rom = image({0x0100: entry + jp_nc(block_at) + RET, block_at: body, 0x0200: words(0x0210), 0x0210: RET})
        p = prove(rom, block_at + len(body) - 1)
        self.assertEqual(p["status"], "unreachable")
        self.assertEqual(p["supported_targets"], [])
        spec = R.dispatch_spec(p, include_partial=False)
        self.assertEqual(spec, {"targets": [], "complete": True})

    def test_the_same_jump_with_a_reachable_guard_is_not_unreachable(self):
        entry = ld_a_mem(0xC100) + and_n(7) + cp_n(5)
        body = block(0x0200, and_n(0))
        block_at = 0x0140
        rom = image({0x0100: entry + jp_nc(block_at) + RET, block_at: body, 0x0200: words(0x0210), 0x0210: RET})
        p = prove(rom, block_at + len(body) - 1)
        self.assertNotEqual(p["status"], "unreachable")
        self.assertEqual(p["domain"]["count"], 96)                      # start values whose low three bits are 5, 6 or 7


class ContradictoryBounds(unittest.TestCase):
    def table(self, entries, mask=3, extra=b""):
        code = block(0x0160, ld_a_mem(0xC100) + and_n(mask))
        site = 0x0100 + len(code) - 1
        blob, addrs = handlers(0x0170, 6)
        rom = image({0x0100: code, 0x0160: words(*entries(addrs)), 0x0170: blob, 0x0038: jp(0x0100)})
        return rom, site, addrs

    def test_a_destination_inside_its_own_table_shrinks_the_extent(self):
        # word 2 points at the table's own word 3: a table cannot extend into the code it points to, so the fourth
        # word is no longer a table word and the masked dispatcher (which can select it) cannot be proven
        rom, site, addrs = self.table(lambda a: [a[0], a[1], 0x0166, a[3]])
        p = prove(rom, site)
        self.assertEqual(p["status"], "partial")
        self.assertEqual(p["table"]["region_end"], 0x0166)
        self.assertEqual([e["supported"] for e in p["table"]["entries"]], [True, True, True, False])

    def test_a_destination_in_ram_is_unsupported(self):
        rom, site, addrs = self.table(lambda a: [a[0], 0xC123, a[2], a[3]])
        p = prove(rom, site)
        self.assertEqual(p["status"], "partial")
        bad = [e for e in p["table"]["entries"] if not e["supported"]]
        self.assertEqual([e["target_cpu"] for e in bad], [0xC123])
        self.assertFalse(bad[0]["descent_ok"])
        self.assertEqual(p["supported_targets"], sorted([addrs[0], addrs[2], addrs[3]]))

    def test_a_destination_that_decodes_to_nothing_is_unsupported(self):
        junk = 0x0300                       # ED 00 is not an instruction
        rom = image({0x0100: block(0x0160, ld_a_mem(0xC100) + and_n(1)), 0x0160: words(0x0170, junk),
                     0x0170: RET, junk: b"\xED\x00", 0x0038: jp(0x0100)})
        site = 0x0100 + len(block(0x0160, ld_a_mem(0xC100) + and_n(1))) - 1
        p = prove(rom, site)
        self.assertEqual(p["status"], "partial")
        self.assertEqual(p["table"]["entries"][1]["descent_problems"][0][0], "invalid")

    def test_a_loop_through_the_dispatcher_terminates_deterministically(self):
        pre = ld_a_mem(0xC100) + and_n(1)
        code = block(0x0160, pre)
        # both handlers jump back to the start of the dispatcher: the closure is a cycle
        rom = image({0x0100: code, 0x0160: words(0x0170, 0x0173), 0x0170: jp(0x0100), 0x0173: jp(0x0100), 0x0038: jp(0x0100)})
        first = R.resolve(rom, [], Facts(), None, SHADOW, False)
        second = R.resolve(rom, [], Facts(), None, SHADOW, False)
        self.assertEqual(sorted(first[0]["visited"]), sorted(second[0]["visited"]))
        self.assertEqual(first[2][0x0100 + len(code) - 1]["status"], "proven")
        self.assertEqual(first[0]["open_edges"], [])
        self.assertIn(0x0173, first[0]["visited"])

    def test_an_undecidable_loop_before_the_index_load_does_not_block_a_proof_after_it(self):
        # the early loop has RAM-dependent flags (undecidable); the dispatcher's own index load follows it
        early = ld_a_mem(0xC200) + b"\xB7" + b"\x28\xFA"                  # LD A,(nn) / OR A / JR Z,<back to the load>
        late = block(0x0160, ld_a_mem(0xC100) + and_n(3))
        rom = image({0x0100: early + late, 0x0160: words(0x0170, 0x0171, 0x0172, 0x0173), 0x0170: RET * 4, 0x0038: jp(0x0100)})
        p = prove(rom, 0x0100 + len(early + late) - 1)
        self.assertEqual(p["status"], "proven", p["reasons"])
        self.assertEqual(p["entry_integrity"]["collapsed_starts"][0]["cpu"], 0x0100)
        self.assertEqual(p["starts"][0]["cpu"], 0x0106)

    def test_an_index_that_depends_on_two_unknown_loads_is_not_decided(self):
        # A comes from RAM, is copied, a second RAM byte replaces it unless it is zero: the merged index is unknown
        code = (ld_a_mem(0xC100) + b"\x47" + ld_a_mem(0xC300) + b"\xB7" + b"\x28\x01" + b"\x78" + ADD_A_A + LD_L_A + LD_H_0 +
                ld_de(0x0200) + ADD_HL_DE + FETCH + JP_HL)
        rom = image({0x0100: code, 0x0200: words(0x0210, 0x0211), 0x0210: RET * 2, 0x0038: jp(0x0100)})
        p = prove(rom, 0x0100 + len(code) - 1)
        self.assertNotEqual(p["status"], "proven")


class DataDomains(unittest.TestCase):
    def setUp(self):
        self.rom, self.site, self.addrs = masked_table(mask=None, count=4)

    def domain(self, values, loads=(FREE_LOAD_ASM,)):
        return {"values": set(values), "applies_to_unknown_loads": list(loads), "evidence": {"synthetic": True}}

    def test_a_data_domain_inside_the_table_promotes_a_partial_dispatcher(self):
        p = prove(self.rom, self.site, data_domain=self.domain({0, 1, 2, 3, 128, 129}))
        self.assertEqual(p["status"], "proven", p["reasons"])
        self.assertEqual(p["unsupported_in_effective_domain"], [])
        self.assertEqual(p["domain"]["count"], 256)                   # the code-defined domain is still reported in full

    def test_one_value_outside_the_table_keeps_it_partial(self):
        p = prove(self.rom, self.site, data_domain=self.domain({0, 1, 2, 3, 4}))
        self.assertEqual(p["status"], "partial")
        self.assertEqual(p["unsupported_in_effective_domain"], ["$04"])

    def test_a_data_domain_is_ignored_when_one_start_is_not_an_unknown_load(self):
        # a second entry reaches the block with A set from an immediate: that start has no data meaning
        block_at = 0x0140
        body = ADD_A_A + LD_L_A + LD_H_0 + ld_de(0x0200) + ADD_HL_DE + FETCH + JP_HL
        site = block_at + len(body) - 1
        blob, addrs = handlers(0x0208, 4)
        rom = image({0x0100: ld_a_mem(0xC100) + jp(block_at), 0x0120: ld_a(2) + jp(block_at), block_at: body,
                     0x0200: words(*addrs), 0x0208: blob})
        p = prove(rom, site, roots=((0x0100, 1, 3), (0x0120, 1, 3)),
                  data_domain=self.domain({0, 1, 2, 3}, loads=("LD A,(0xc100)",)))
        self.assertEqual(p["status"], "partial")
        self.assertIn("data_domain_ignored", p)

    def test_a_data_domain_for_another_load_is_ignored(self):
        p = prove(self.rom, self.site, data_domain=self.domain({0}, loads=("LD A,(DE)",)))
        self.assertEqual(p["status"], "partial")
        self.assertIn("data_domain_ignored", p)
        self.assertNotIn("data_domain", p)


class EntryIntegrity(unittest.TestCase):
    def test_a_second_entry_with_no_guard_widens_the_domain(self):
        # path 1 guards with CP 4, path 2 reaches the same dispatch block after its own free load and no guard
        block_at = 0x0140
        body = block(0x0200)
        site = block_at + len(body) - 1
        path1 = ld_a_mem(0xC100) + cp_n(4) + jp_nc(0x0900) + jp(block_at)
        path2 = ld_a_mem(0xC200) + jp(block_at)
        blob, addrs = handlers(0x0208, 8)
        rom = image({0x0100: path1, 0x0120: path2, block_at: body, 0x0200: words(*addrs[:4]), 0x0208: blob})
        guarded_only = image({0x0100: path1, block_at: body, 0x0200: words(*addrs[:4]), 0x0208: blob})
        tight = prove(guarded_only, site)
        wide = prove(rom, site, roots=((0x0100, 1, 3), (0x0120, 1, 3)))
        self.assertEqual(tight["status"], "proven", tight["reasons"])
        self.assertEqual(tight["domain"]["count"], 4)
        self.assertEqual(wide["domain"]["count"], 256)                  # the unguarded entry admits every value
        self.assertEqual(wide["status"], "partial")

    def test_a_decoded_literal_naming_a_block_instruction_is_an_entry(self):
        code = ld_a_mem(0xC100) + and_n(3)
        tail = ADD_A_A + LD_L_A + LD_H_0 + ld_de(0x0200) + ADD_HL_DE + FETCH + JP_HL
        entry = 0x0100 + len(code)
        rom = image({0x0100: code + tail, 0x0200: words(0x0210, 0x0211, 0x0212, 0x0213), 0x0210: RET * 4,
                     0x0500: b"\x21" + w(entry)})                       # LD HL,<the ADD A,A>
        walk = start_walk(rom, roots=((0x0100, 1, 3), (0x0500, 1, 3)))
        uni = R.Universe(rom, R.contexts_from(rom, [], walk))
        decoded, _ = uni.literals(entry, entry)
        self.assertEqual([r["asm"] for r in decoded], ["LD HL,0x%x" % entry])

    def test_a_literal_that_is_not_an_operand_is_not_an_entry(self):
        # `40 01` spells $0140 but is the end of LD B,B and the opcode of LD BC,$1234, not an operand
        rom = image({0x0140: RET, 0x0200: bytes([0x40, 0x01, 0x34, 0x12, 0xC9])})
        walk = start_walk(rom, roots=((0x0200, 1, 3),))
        uni = R.Universe(rom, R.contexts_from(rom, [], walk))
        self.assertIn(0x0200, uni.ins)
        self.assertEqual(uni.literals(0x0140, 0x0140), ([], []))


class BankMapping(unittest.TestCase):
    def test_the_same_cpu_address_in_two_banks_gives_two_file_offsets(self):
        # one slot-2 dispatcher at CPU $8000 and one word table at $8100 in each of banks 5 and 6
        code = ld_a_mem(0xC100) + and_n(1) + block(0x8100)
        rom = bytearray(8 * 0x4000)
        expected = {}
        for bank, off in ((5, 0x20), (6, 0x40)):
            base = bank * 0x4000
            rom[base:base + len(code)] = code
            rom[base + 0x100:base + 0x104] = words(0x8200 + off, 0x8201 + off)
            rom[base + 0x200 + off:base + 0x202 + off] = RET * 2
            expected[bank] = base + 0x200 + off
        rom = bytes(rom)
        got = {}
        for bank in (5, 6):
            walk = D.state_walk(rom, [(0x8000, 1, bank)], SHADOW)
            uni = R.Universe(rom, R.contexts_from(rom, [], walk), entries={bank * 0x4000})
            p = R.prove_dispatch(rom, bank * 0x4000 + len(code) - 1, uni, 1, bank)
            self.assertEqual(p["status"], "proven", p["reasons"])
            self.assertEqual((p["bank"], p["slot"]), (bank, 2))
            self.assertEqual(p["table"]["entries"][0]["word_file"], bank * 0x4000 + 0x100)
            got[bank] = p["table"]["entries"][0]["target_file"]
        self.assertEqual(got, expected)
        self.assertNotEqual(got[5], got[6])

    def test_a_slot_one_dispatcher_reads_its_own_bank(self):
        # bank 2 mapped in slot 1: the same CPU table address $4100 reads bank 2, not the resident bank 1
        code = ld_a_mem(0xC100) + and_n(1) + block(0x4100)
        rom = bytearray(8 * 0x4000)
        rom[2 * 0x4000:2 * 0x4000 + len(code)] = code
        rom[2 * 0x4000 + 0x100:2 * 0x4000 + 0x104] = words(0x4200, 0x4201)
        rom[1 * 0x4000 + 0x100:1 * 0x4000 + 0x104] = words(0x4300, 0x4301)       # decoy in bank 1
        rom[2 * 0x4000 + 0x200:2 * 0x4000 + 0x202] = RET * 2
        rom = bytes(rom)
        walk = D.state_walk(rom, [(0x4000, 2, 3)], SHADOW)
        uni = R.Universe(rom, R.contexts_from(rom, [], walk))
        p = R.prove_dispatch(rom, 2 * 0x4000 + len(code) - 1, uni, 2, 3)
        self.assertEqual(p["status"], "proven", p["reasons"])
        self.assertEqual(p["supported_targets"], [0x4200, 0x4201])
        self.assertEqual(p["table"]["entries"][0]["word_file"], 2 * 0x4000 + 0x100)


class ShadowAndMapperEffects(unittest.TestCase):
    def closure(self, handler, count=2):
        """A masked dispatcher whose every handler runs ``handler`` and returns; resolved and walked to a fixed point."""
        pre = ld_a_mem(0xC100) + and_n(count - 1)
        code = block(0x0160, pre)
        body = handler + RET
        blob, addrs = handlers(0x0170, count, body)
        rom = image({0x0100: code, 0x0160: words(*addrs), 0x0170: blob, 0x0038: jp(0x0100)})
        walk, disp, proofs, uni = R.resolve(rom, [], Facts(), None, SHADOW, False)
        return rom, walk, proofs

    def test_a_clean_destination_leaves_no_shadow_store(self):
        rom, walk, proofs = self.closure(ld_a(1) + st_a(0xC200))
        self.assertEqual(R.write_audit(rom, walk)["absolute_store_hits_shadow"], [])
        self.assertEqual(walk["open_edges"], [])

    def test_a_destination_that_writes_the_shadow_is_found(self):
        rom, walk, proofs = self.closure(ld_a(1) + st_a(SHADOW))
        audit = R.write_audit(rom, walk)
        self.assertEqual([h["address"] for h in audit["absolute_store_hits_shadow"]], [SHADOW, SHADOW])
        self.assertTrue(any(a == SHADOW for _, a in walk["stores"]))

    def test_the_ram_mirror_of_the_shadow_is_the_shadow(self):
        rom, walk, proofs = self.closure(ld_a(1) + st_a(SHADOW + 0x2000))
        self.assertEqual(len(R.write_audit(rom, walk)["absolute_store_hits_shadow"]), 2)

    def test_a_sixteen_bit_store_covering_either_shadow_byte_is_found(self):
        # LD (nn),HL writes nn and nn+1; $D12A is the slot-1 shadow and $D12B the slot-2 shadow, one hit per handler
        for target, hits in ((0xD129, 2), (0xD12A, 2), (0xD12B, 2), (0xD12C, 0), (0xD128, 0)):
            rom, walk, proofs = self.closure(b"\x22" + w(target))
            n = len(R.write_audit(rom, walk)["absolute_store_hits_shadow"])
            self.assertEqual(n, hits, hex(target))

    def test_a_destination_that_changes_the_slot2_register_is_found(self):
        rom, walk, proofs = self.closure(ld_a(7) + st_a(0xFFFF))
        audit = R.write_audit(rom, walk)
        self.assertEqual(len(audit["mapper_register_store_sites"]), 2)
        self.assertEqual(audit["absolute_store_hits_shadow"], [])

    def test_a_wide_store_to_the_mapper_registers_is_found(self):
        rom, walk, proofs = self.closure(b"\x22" + w(0xFFFE))          # LD ($FFFE),HL writes $FFFE and $FFFF
        self.assertTrue(R.write_audit(rom, walk)["mapper_register_store_sites"])

    def test_register_addressed_writes_are_counted_not_ignored(self):
        rom, walk, proofs = self.closure(b"\x77")                       # LD (HL),A
        audit = R.write_audit(rom, walk)
        self.assertEqual(audit["register_addressed"].get("hl"), 2)
        self.assertEqual(audit["absolute_store_hits_shadow"], [])

    def test_a_restart_instruction_in_a_destination_is_reported_and_blocks_closure(self):
        rom, walk, proofs = self.closure(b"\xFF")                       # RST $38 re-enters the interrupt handler
        audit = R.write_audit(rom, walk)
        self.assertEqual(len(audit["rst_instructions"]), 2)
        v = R.derive_verdict(walk, audit, walk, audit, proofs, proofs)
        self.assertTrue(v["restart_instructions_in_followed_closure"])
        self.assertNotEqual(v["r1"], "CLOSED")

    def test_the_verdict_is_open_when_a_followed_destination_writes_the_shadow(self):
        rom, walk, proofs = self.closure(ld_a(1) + st_a(SHADOW))
        audit = R.write_audit(rom, walk)
        v = R.derive_verdict(walk, audit, walk, audit, proofs, proofs)
        self.assertEqual(v["r1"], "OPEN")
        self.assertTrue(v["shadow_store_in_followed_closure"])


class VerdictRules(unittest.TestCase):
    def resolved(self, mask):
        pre = ld_a_mem(0xC100) + (and_n(mask) if mask is not None else b"")
        code = block(0x0160, pre)
        blob, addrs = handlers(0x0170, 4)
        rom = image({0x0100: code, 0x0160: words(*addrs), 0x0170: blob, 0x0038: jp(0x0100)})
        return rom, R.resolve(rom, [], Facts(), None, SHADOW, False), R.resolve(rom, [], Facts(), None, SHADOW, True)

    def verdict(self, rom, off, con):
        return R.derive_verdict(off[0], R.write_audit(rom, off[0]), con[0], R.write_audit(rom, con[0]), con[2], off[2])

    def test_closed_only_when_every_computed_jump_is_proven(self):
        v = self.verdict(*self.resolved(3))
        self.assertEqual(v["r1"], "CLOSED")
        self.assertEqual(v["official_walk_open_edges"], 0)

    def test_an_unbounded_index_cannot_close(self):
        v = self.verdict(*self.resolved(None))
        self.assertEqual(v["r1"], "PARTIALLY CLOSED")
        self.assertGreater(v["official_walk_open_edges"], 0)
        self.assertEqual(v["partial"], 1)

    def test_an_unresolvable_computed_jump_in_a_destination_prevents_closure(self):
        # the only handler jumps through HL loaded from RAM, so its index is never bounded
        code = block(0x0160, ld_a_mem(0xC100) + and_n(0))
        handler = b"\x2A" + w(0xC300) + JP_HL                            # LD HL,($C300) / JP (HL)
        rom = image({0x0100: code, 0x0160: words(0x0170), 0x0170: handler, 0x0038: jp(0x0100)})
        off = R.resolve(rom, [], Facts(), None, SHADOW, False)
        con = R.resolve(rom, [], Facts(), None, SHADOW, True)
        v = self.verdict(rom, off, con)
        self.assertNotEqual(v["r1"], "CLOSED")
        self.assertTrue(any(e[0] == "indirect_jump" for e in off[0]["open_edges"]))
        self.assertEqual(sorted(v["computed_jump_sites"].values()), ["proven", "unproven"])

    def test_nested_dispatchers_are_all_followed_to_a_fixed_point(self):
        inner = block(0x0300, ld_a_mem(0xC200) + and_n(1))
        outer = block(0x0160, ld_a_mem(0xC100) + and_n(1))
        h_blob, h = handlers(0x0400, 2)
        rom = image({0x0100: outer, 0x0160: words(0x0170, 0x0170), 0x0170: inner, 0x0300: words(*h), 0x0400: h_blob,
                     0x0038: jp(0x0100)})
        off = R.resolve(rom, [], Facts(), None, SHADOW, False)
        self.assertEqual(sorted(p["status"] for p in off[2].values()), ["proven", "proven"])
        self.assertEqual(off[0]["open_edges"], [])
        self.assertIn(0x0400, off[0]["visited"])

    def test_a_partial_outer_dispatcher_hides_the_inner_one_from_the_official_walk(self):
        inner = block(0x0300, ld_a_mem(0xC200) + and_n(1))
        outer = block(0x0160, ld_a_mem(0xC100))                         # no mask: partial
        h_blob, h = handlers(0x0400, 2)
        rom = image({0x0100: outer, 0x0160: words(0x0170, 0x0170), 0x0170: inner, 0x0300: words(*h), 0x0400: h_blob,
                     0x0038: jp(0x0100)})
        off = R.resolve(rom, [], Facts(), None, SHADOW, False)
        con = R.resolve(rom, [], Facts(), None, SHADOW, True)
        self.assertEqual(len(off[2]), 1)                                 # the inner jump is not even discovered
        self.assertEqual(len(con[2]), 2)                                 # the conditional walk finds both
        self.assertNotIn(0x0400, off[0]["visited"])


class StreamGrammar(unittest.TestCase):
    """The token walk over synthetic streams (file offset = pointer + $4000, pointers $4000-$BFFF)."""
    SEMANTICS = {0xF2: "stop", 0xF6: "jump", 0xF7: "loop", 0xF8: "call", 0xF9: "return", 0xFD: "note_mode"}

    def operands(self):
        ops = {f: 1 for f in range(0xE0, 0x100)}
        ops.update({0xE0: 5, 0xE7: 0, 0xF0: 4})
        return ops

    def walk(self, stream, grammar="tone", mode=0, at=0x5000):
        rom = bytearray(0x10000)
        rom[at + ST.FILE_FROM_PTR:at + ST.FILE_FROM_PTR + len(stream)] = stream
        fetched, flags, problems = ST.walk_stream(bytes(rom), at, grammar, mode, self.SEMANTICS, self.operands())
        return fetched, flags, problems

    def test_an_operand_byte_is_not_a_command(self):
        # E1 takes one operand, so the $EF after it is data; the stream then stops
        _, flags, problems = self.walk(bytes([0xE1, 0xEF, 0xF2]))
        self.assertEqual((sorted(flags), problems), ([0xE1, 0xF2], []))

    def test_bytes_after_a_stop_are_not_walked(self):
        _, flags, _ = self.walk(bytes([0xF2, 0xEF, 0xF1]))
        self.assertEqual(sorted(flags), [0xF2])

    def test_a_note_consumes_an_optional_duration_but_not_a_following_command(self):
        # note, duration ($10), note, then a command directly (no duration): the command byte must be seen as a command
        _, flags, _ = self.walk(bytes([0x90, 0x10, 0x91, 0xE7, 0xF2]))
        self.assertEqual(sorted(flags), [0xE7, 0xF2])

    def test_a_duration_byte_below_80_is_consumed_with_its_note(self):
        _, flags, _ = self.walk(bytes([0x90, 0x10, 0xF2]))
        self.assertEqual(sorted(flags), [0xF2])

    def test_a_flag_operand_with_five_bytes_is_skipped_whole(self):
        _, flags, _ = self.walk(bytes([0xE0, 0xEF, 0xF1, 0xEF, 0xF1, 0xF1, 0xF2]))
        self.assertEqual(sorted(flags), [0xE0, 0xF2])

    def test_custom_note_mode_reads_three_byte_tokens(self):
        # in mode 3 a note is high, low, duration: $90 $EF $05 hides the $EF; in mode 0 it would not
        mode3 = self.walk(bytes([0x90, 0xEF, 0x05, 0xF2]), mode=3)[1]
        mode0 = self.walk(bytes([0x90, 0xEF, 0x05, 0xF2]), mode=0)[1]
        self.assertEqual(sorted(mode3), [0xF2])
        self.assertEqual(sorted(mode0), [0xEF, 0xF2])

    def test_the_mode_flag_switches_the_grammar_for_what_follows(self):
        _, flags, _ = self.walk(bytes([0xFD, 0x01, 0x90, 0xEF, 0x05, 0xF2]))
        self.assertEqual(sorted(flags), [0xF2, 0xFD])

    def test_the_noise_routine_never_uses_the_custom_note_mode(self):
        # the noise channel has no BIT 3 test, so even with the mode bit set $EF after a note is still a command
        stream = bytes([0x90, 0xEF, 0x05, 0xF2])
        self.assertEqual(sorted(self.walk(stream, grammar="tone", mode=3)[1]), [0xF2])
        self.assertEqual(sorted(self.walk(stream, grammar="noise", mode=3)[1]), [0xEF, 0xF2])

    def test_a_jump_follows_its_pointer_and_skips_what_it_jumps_over(self):
        stream = bytes([0xF6]) + w(0x5010) + bytes([0xEF, 0xEF]) + bytes(11) + bytes([0xF2])
        _, flags, _ = self.walk(stream)
        self.assertEqual(sorted(flags), [0xF2, 0xF6])

    def test_a_loop_explores_the_back_edge_and_the_fall_through(self):
        # E1 x / loop(count idx, count, ptr back to start) / fall through into E7 then stop
        stream = bytes([0xE1, 0x00, 0xF7, 0x00, 0x03]) + w(0x5000) + bytes([0xE7, 0xF2])
        _, flags, _ = self.walk(stream)
        self.assertEqual(sorted(flags), [0xE1, 0xE7, 0xF2, 0xF7])
        self.assertEqual(sorted(flags[0xE1]), [0x5000])                 # the back edge revisits the start, nothing new

    def test_a_call_continues_after_its_pointer_and_a_return_ends_the_callee(self):
        stream = bytes([0xF8]) + w(0x5010) + bytes([0xF2]) + bytes(12) + bytes([0xE1, 0x00, 0xF9, 0xEF])
        _, flags, _ = self.walk(stream)
        self.assertEqual(sorted(flags), [0xE1, 0xF2, 0xF8, 0xF9])        # the $EF after the return is never reached

    def test_a_pointer_outside_the_stream_window_is_a_problem_not_a_guess(self):
        _, _, problems = self.walk(bytes([0xF6]) + w(0x1000))
        self.assertEqual(problems, [("out_of_window", 0x1000)])

    def test_an_unmeasured_flag_stops_the_walk_with_a_problem(self):
        ops = self.operands()
        ops[0xE2] = None
        rom = bytearray(0x10000)
        rom[0x9000:0x9003] = bytes([0xE2, 0x00, 0xF2])
        _, flags, problems = ST.walk_stream(bytes(rom), 0x5000, "tone", 0, self.SEMANTICS, ops)
        self.assertEqual(problems, [("unmeasured_flag", 0xE2, 0x5000)])

    def test_handler_signatures_must_match_the_rom(self):
        handlers_ = {0xE0 + i: 0x4800 + 0x20 * i for i in range(32)}
        with self.assertRaises(ST.FlagSemanticsError):
            ST.classify_handlers(bytes(0x10000), handlers_)


@unittest.skipUnless(canonical_rom(), "canonical ROM not available")
class CanonicalStreams(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = canonical_rom()
        cls.result = ST.analyse(cls.rom)

    def test_control_handlers_are_identified_by_their_code_bytes(self):
        self.assertEqual(self.result["control_flags"], {"0xf2": "stop", "0xf6": "jump", "0xf7": "loop", "0xf8": "call",
                                                        "0xf9": "return", "0xfd": "note_mode"})

    def test_operand_lengths_are_measured_from_the_original_handlers(self):
        ops = self.result["operand_bytes"]
        self.assertEqual((ops["0xe0"], ops["0xe7"], ops["0xf0"], ops["0xe1"], ops["0xff"]), (5, 0, 4, 1, 1))
        for control in ("0xf2", "0xf6", "0xf7", "0xf8", "0xf9"):
            self.assertNotIn(control, ops)

    def test_every_request_yields_its_streams_from_the_original_init(self):
        self.assertEqual(self.result["requests"], [0x81, 0xC4])
        self.assertEqual(self.result["stream_start_states"], 164)

    def test_ef_and_f1_never_reach_the_dispatcher(self):
        flags = set(self.result["flags_reaching_the_dispatcher"])
        self.assertTrue({"0xef", "0xf1"}.isdisjoint(flags))
        self.assertEqual(flags, {"0xe0", "0xe1", "0xe6", "0xe7", "0xf0", "0xf2", "0xf3", "0xf5", "0xf6", "0xf7", "0xf8",
                                 "0xf9", "0xfb", "0xfd"})
        self.assertEqual(self.result["walk_problems"], [])

    def test_the_controlled_run_of_the_real_driver_agrees_with_the_static_walk(self):
        dyn = self.result["dynamic_cross_check"]
        self.assertTrue(dyn["consistent"])
        self.assertEqual((dyn["tone_fetches_outside_the_static_walk"], dyn["noise_fetches_outside_the_static_walk"]), (0, 0))
        self.assertEqual(dyn["dispatched_flags_outside_the_static_set"], [])
        self.assertEqual(dyn["dispatched_flags"], self.result["flags_reaching_the_dispatcher"])

    def test_an_incomplete_proof_yields_the_whole_flag_range(self):
        # the domain only narrows when the proof is complete
        self.assertTrue(self.result["complete"])
        self.assertEqual(sorted(self.result["values"]), [int(x, 16) for x in self.result["flags_reaching_the_dispatcher"]])


@unittest.skipUnless(canonical_rom(), "canonical ROM not available")
class CanonicalSources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import decomp1d_r1_sources as SRC
        cls.SRC = SRC
        cls.rom = canonical_rom()
        ledger = ROOT / "data" / "rom-cache" / "audio" / "request-ledger.json"
        ids = {r["request_id"] for r in json.loads(ledger.read_text(encoding="utf-8"))["requests"]}
        cls.requests = SRC.request_sources(cls.rom, ids)
        cls.slots = SRC.slot_type_sources(cls.rom)

    def test_no_immediate_request_is_in_the_out_of_table_range(self):
        self.assertEqual(self.requests["immediate_values_in_forbidden_range"], [])
        self.assertEqual(self.requests["immediate_values_missing_from_audio0_ledger"], [])
        self.assertEqual(self.requests["wide_store_sites"], [])

    def test_every_non_immediate_request_store_is_a_known_route(self):
        routes = {d["route"] for d in self.requests["dynamic_sites"]}
        self.assertEqual(routes, {"irq_forward", "sound_test", "zone_music_table", "boss_clear_music", "script_operand",
                                  "script_operand_repeat"})
        self.assertEqual({d["route"] for d in self.requests["latch_sites"]["dynamic"]},
                         {"latch_clear", "zone_music_table", "boss_music"})

    def test_the_script_route_cannot_name_an_out_of_table_id(self):
        r = self.requests["script_operand_route"]
        self.assertTrue(r["handler_is_subcommand_6"])
        self.assertEqual(r["operands_in_forbidden_range"], [])

    def test_the_music_table_is_safe_only_inside_its_39_entries(self):
        t = self.requests["zone_music_table"]
        self.assertEqual((t["entries"], t["in_forbidden_range"], t["first_bytes_after_the_table"]), (39, [], "2109de"))

    def test_slot_types_come_from_nine_records_and_a_few_enumerated_callers(self):
        rec = self.slots["record_table"]
        self.assertEqual((rec["first_level_words"], rec["records"]), (16, 9))
        self.assertEqual(rec["types_in_records"], [0, 1, 2, 3, 4, 5, 6, 8, 11, 12, 13, 14])
        self.assertEqual(self.slots["allocator"]["c_values_at_direct_sites"], [7, 9, 16])
        self.assertEqual([s["offset"] for s in self.slots["absolute_stores"]],
                         [0x1CEC, 0x1CEF, 0x1CF2, 0x1CF5, 0x2A86, 0x2A8B, 0x2A90, 0x2A95])


@unittest.skipUnless(canonical_rom(), "canonical ROM not available")
class CanonicalRom(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = canonical_rom()
        cls.doc = R.build(cls.rom, data_domains=R.data_domains(cls.rom))
        cls.by_site = {d["site"]: d for d in cls.doc["dispatchers"]}

    def test_the_three_task_sites_are_rederived_from_the_rom(self):
        t = self.doc["task_sites_rederived"]
        self.assertTrue(t["matches_task_table"])
        self.assertEqual([s["instruction"] for s in t["sites"]], ["JP (HL)"] * 3)
        by = {s["file_offset"]: s for s in t["sites"]}
        self.assertEqual((by[0x086E8]["bank"], by[0x086E8]["cpu"]), (2, 0x46E8))
        self.assertEqual((by[0x08137]["bank"], by[0x08137]["cpu"]), (2, 0x4137))
        self.assertEqual((by[0x74027]["bank"], by[0x74027]["cpu"]), (0x1D, 0x8027))

    def test_site_a_is_bounded_by_its_compare_guards_to_the_flag_range(self):
        a = self.by_site[0x086E8]
        self.assertEqual(a["domain"]["ranges"], ["$E0-$FF"])
        self.assertEqual((a["table"]["base"], a["table"]["words_read"], a["table"]["region_end"]), (0x46ED, 32, 0x472D))
        self.assertEqual(a["pushed_continuations"], [0x4671, 0x46E9])        # both entries push a return address
        self.assertEqual({u["asm"] for s in a["starts"] for u in s["unknown_load"]}, {"LD A,(DE)"})

    def test_site_a_has_two_flags_that_lead_into_a_data_table(self):
        a = self.by_site[0x086E8]
        self.assertEqual(a["code_domain"]["unsupported_values"], ["$EF", "$F1"])
        bad = [e for e in a["table"]["entries"] if not e["supported"]]
        self.assertEqual([e["values"] for e in bad], [["$EF"], ["$F1"]])
        self.assertEqual({e["target_cpu"] for e in bad}, {0x48AC})
        self.assertEqual(bad[0]["descent_problems"][0][0], "ram_target")

    def test_site_a_is_proven_only_through_the_stream_data(self):
        a = self.by_site[0x086E8]
        self.assertEqual(a["status"], "proven")
        self.assertEqual(a["unsupported_in_effective_domain"], [])
        self.assertEqual(a["data_domain"]["values"], ["$E0-$E1", "$E6-$E7", "$F0", "$F2-$F3", "$F5-$F9", "$FB", "$FD"])
        self.assertEqual(a["domain"]["ranges"], ["$E0-$FF"])                   # the code-defined domain is still all of it

    def test_site_b_guard_admits_values_outside_its_three_word_table(self):
        b = self.by_site[0x08137]
        self.assertEqual(b["domain"]["ranges"], ["$C5-$D3"])
        self.assertEqual((b["table"]["base"], b["table"]["region_end"]), (0x4138, 0x4140))
        self.assertEqual(b["code_domain"]["supported_values"], ["$D0-$D2"])
        self.assertEqual(b["code_domain"]["unsupported_values"], ["$C5-$CF", "$D3"])
        self.assertEqual(b["status"], "partial")
        self.assertEqual([u["asm"] for s in b["starts"] for u in s["unknown_load"]], ["LD A,(0xde03)"])
        self.assertEqual(b["supported_targets"], [0x4140, 0x4150, 0x43E5])

    def test_site_b_value_d3_names_song_data_not_code(self):
        # the fourth word of the "table" is the padding word 00 70; $7000 is inside a stream the driver plays
        entries = {tuple(e["values"]): e for e in self.by_site[0x08137]["table"]["entries"]}
        d3 = entries[("$D3",)]
        self.assertEqual((d3["word_cpu"], d3["target_cpu"], d3["ledger_non_code"], d3["supported"]),
                         (0x413E, 0x7000, "SOUND_STREAM", False))
        self.assertTrue(d3["in_table_region"])
        self.assertEqual(self.rom[0x813E:0x8140], bytes([0x00, 0x70]))

    def test_site_b_cannot_be_promoted_by_the_stream_proof(self):
        self.assertNotIn("data_domain", self.by_site[0x08137])

    def test_site_c_index_wraps_and_aliases_values_128_apart(self):
        c = self.by_site[0x74027]
        self.assertEqual(c["domain"]["ranges"], ["$00-$FF"])
        self.assertEqual((c["table"]["base"], c["table"]["region_end"]), (0x8028, 0x8052))
        self.assertEqual(c["code_domain"]["supported_values"], ["$00-$14", "$80-$94"])
        self.assertEqual(c["table"]["entries"][0]["values"], ["$00", "$80"])
        self.assertEqual(c["status"], "partial")

    def test_the_routine_behind_site_c_adds_four_more_computed_jumps(self):
        sites = self.doc["verdict"]["computed_jump_sites"]
        self.assertEqual(sites, {"$8137": "partial", "$86E8": "proven", "$74027": "partial", "$7407F": "proven",
                                 "$741F1": "partial", "$74285": "proven", "$744CB": "proven"})

    def test_masked_sub_dispatchers_have_exactly_their_mask_width(self):
        for site, count in ((0x7407F, 4), (0x74285, 2), (0x744CB, 4)):
            p = self.by_site[site]
            self.assertEqual((p["status"], p["table"]["words_read"]), ("proven", count))
            self.assertEqual(p["unsupported_in_effective_domain"], [])

    def test_the_zone_indexed_jump_is_partial_with_its_own_table_extent(self):
        z = self.by_site[0x741F1]
        self.assertEqual(z["status"], "partial")
        self.assertEqual(z["table"]["region_end"] - z["table"]["base"], 24)       # 12 words: six zones, two acts each

    def test_the_official_walk_follows_site_a_and_nothing_unproven(self):
        ow = self.doc["official_walk"]
        sites = {e[1] for e in ow["open_edges"] if e[0] == "indirect_jump"}
        self.assertEqual(sites, {0x8137, 0x74027})
        self.assertEqual([e for e in ow["open_edges"] if e[0] == "partial_dispatch"], [])
        base = self.doc["baseline_walk"]["instructions"]
        self.assertGreater(ow["instructions"], base)
        self.assertGreater(self.doc["conditional_walk"]["instructions"], ow["instructions"])

    def test_no_followed_destination_stores_to_the_shadow_or_a_mapper_register(self):
        v = self.doc["verdict"]
        self.assertFalse(v["shadow_store_in_followed_closure"])
        self.assertFalse(v["undecodable_in_followed_closure"])
        base = self.doc["baseline_walk"]["write_audit"]["mapper_register_store_sites"]
        for key in ("official_walk", "conditional_walk"):
            audit = self.doc[key]["write_audit"]
            self.assertEqual(audit["absolute_store_hits_shadow"], [])
            self.assertEqual(audit["mapper_register_store_sites"], base)
        new = self.doc["newly_reachable_code"]
        self.assertEqual(new["stores_to_mapper_registers_or_shadow_by_ld_nn_a"], [])
        self.assertGreater(new["newly_reachable_instructions"], 0)

    def test_register_addressed_writes_in_new_code_remain_visible(self):
        regs = self.doc["newly_reachable_code"]["register_addressed_writes_in_new_code"]
        self.assertGreater(sum(regs.values()), 0)

    def test_no_new_entry_into_the_bank_selection_sequence(self):
        self.assertTrue(self.doc["expanded_sequence_integrity"]["clean"])

    def test_no_restart_instruction_and_no_shadow_store_pattern_outside_the_resident_engine(self):
        for key in ("official_walk", "conditional_walk"):
            self.assertEqual(self.doc[key]["write_audit"]["rst_instructions"], [])
        scan = self.doc["mirror_alias_scan"]
        self.assertEqual(scan["shadow"]["outside_resident_engine"], [])
        self.assertEqual(scan["slot1_shadow"]["outside_resident_engine"], [])
        self.assertEqual(len(scan["shadow"]["store_encodings"]), 15)
        self.assertEqual(len(scan["slot1_shadow"]["store_encodings"]), 3)

    def test_no_encoding_in_the_rom_stores_to_the_shadow_mirror(self):
        scan = self.doc["mirror_alias_scan"]
        self.assertEqual([e for e in scan["shadow"]["store_encodings"] if e["address"] == SHADOW + 0x2000], [])
        self.assertEqual([e for e in scan["slot1_shadow"]["store_encodings"] if e["address"] == 0xD12A + 0x2000], [])

    def test_open_conditions_name_the_lemmas_that_would_close_the_rest(self):
        oc = {c["site"]: c for c in self.doc["open_conditions"]}
        self.assertEqual(sorted(oc), [0x08137, 0x74027, 0x741F1])
        for c in oc.values():
            self.assertTrue(c["lemmas_that_would_discharge_it"])

    def test_the_sound_test_route_is_reported_open(self):
        st = self.doc["supporting_evidence"]["site_b_request_byte"]["sound_test"]
        self.assertEqual(st["writers_inside_the_sound_test_loop_closure"], [0x0BCC])
        self.assertGreater(len(st["loop_closure_open_edges"]), 0)
        self.assertTrue(st["conclusion"].startswith("open"))

    def test_no_instruction_writes_the_slot_type_inside_the_bank_1d_closure(self):
        self.assertEqual(self.doc["supporting_evidence"]["site_c_slot_type"]["stores_to_iy_plus_0_in_bank_1d_closure"], [])

    def test_verdict_is_partially_closed_with_the_residual_assumptions_visible(self):
        v = self.doc["verdict"]
        self.assertEqual(v["r1"], "PARTIALLY CLOSED")
        self.assertEqual((v["proven_or_unreachable"], v["partial"], v["unproven"]), (4, 3, 0))
        ids = [a["id"] for a in self.doc["residual_assumptions"]]
        for need in ("R1", "R2", "R3", "R4"):
            self.assertIn(need, ids)

    def test_the_accepted_ledger_is_untouched(self):
        self.assertFalse(self.doc["ledger_effect"]["changed"])

    def test_committed_evidence_regenerates_identically(self):
        text = (json.dumps(self.doc, indent=1) + "\n").encode("utf-8")
        committed = EVIDENCE.read_bytes() if EVIDENCE.is_file() else b""
        self.assertEqual(committed.replace(b"\r\n", b"\n"), text)


class CommittedEvidence(unittest.TestCase):
    """Checks on the committed JSON that need no ROM."""

    @classmethod
    def setUpClass(cls):
        if not EVIDENCE.is_file():
            raise unittest.SkipTest("evidence not generated yet")
        cls.doc = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_the_evidence_holds_no_rom_bytes_beyond_short_instruction_strings(self):
        text = EVIDENCE.read_text(encoding="utf-8")
        self.assertLess(len(text), 2_000_000)
        self.assertEqual(self.doc["rom_sha256"], RL.ROM_SHA256)

    def test_the_document_embeds_exactly_the_committed_destination_list(self):
        self.assertEqual(R.doc_block(R.DOC_PATH), json.loads(json.dumps(R.destinations_block(self.doc))))

    def test_the_document_states_the_same_verdict_as_the_evidence(self):
        text = R.DOC_PATH.read_text(encoding="utf-8")
        self.assertIn("**R1 is %s.**" % self.doc["verdict"]["r1"], text)
        for site in self.doc["verdict"]["computed_jump_sites"]:
            self.assertIn("`$%05X`" % int(site[1:], 16), text, site)

    def test_every_dispatcher_reports_why_it_is_not_proven_when_it_is_not(self):
        for d in self.doc["dispatchers"]:
            if d["status"] == "partial":
                self.assertTrue(d["reasons"] or d["unsupported_in_effective_domain"])


if __name__ == "__main__":
    unittest.main()
