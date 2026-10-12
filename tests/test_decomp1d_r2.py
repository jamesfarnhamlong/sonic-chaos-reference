#!/usr/bin/env python3
"""DECOMP-1D-R2 tests: the zone/act invariant proof for the music, loader and nested-dispatcher consumers.

Synthetic tests build tiny ROM images with hand-assembled Z80 and never need the ROM. Tests that need the canonical ROM skip
without SONIC_CHAOS_ROM or ../source/Sonic Chaos (Europe).sms. Every verdict is recomputed by the generator under test; the
committed JSON is compared with a fresh run, never trusted.
"""
import hashlib
import json
import os
import sys
import unittest
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import decomp1d_r2_zone_act as R  # noqa: E402
import rom_ledger as RL  # noqa: E402

EVIDENCE = ROOT / "data" / "decomp1d" / "r2-zone-act-invariants.json"
DOC = ROOT / "docs" / "decomp-1d-r2-zone-act-invariants.md"
R1_EVIDENCE = ROOT / "data" / "decomp1d" / "r1-interrupt-closure.json"
ROM_PATH = Path(os.environ.get("SONIC_CHAOS_ROM", str(RL.DEFAULT_ROM)))
ZONE, ACT = R.ZONE, R.ACT


def canonical_rom():
    if ROM_PATH.is_file():
        data = ROM_PATH.read_bytes()
        if len(data) == RL.ROM_SIZE and hashlib.sha256(data).hexdigest() == RL.ROM_SHA256:
            return data
    return None


# --- a tiny assembler: only what the synthetic images need ----------------------------------------------------
def w(v):
    return bytes([v & 0xFF, v >> 8])


def ld_a_mem(addr):
    return b"\x3A" + w(addr)


def st_a(addr):
    return b"\x32" + w(addr)


def st_hl(addr):
    return b"\x22" + w(addr)


def ld_a(n):
    return bytes([0x3E, n])


def ld_hl(v):
    return b"\x21" + w(v)


def ld_de(v):
    return b"\x11" + w(v)


def ld_bc(v):
    return b"\x01" + w(v)


XOR_A, INC_A, RET = b"\xAF", b"\x3C", b"\xC9"
LD_B_A, ADD_A_A, ADD_A_B, LD_L_A = b"\x47", b"\x87", b"\x80", b"\x6F"
LD_H_0, ADD_HL_DE, LD_A_HL, LD_HL_A = b"\x26\x00", b"\x19", b"\x7E", b"\x77"
LDIR, LD_HL_0 = b"\xED\xB0", b"\x36\x00"
INC_HL = b"\x23"
CP_N = lambda n: bytes([0xFE, n])  # noqa: E731
CODE = 0x0100


def image(blobs, size=0x10000):
    rom = bytearray(size)
    for at, blob in blobs.items():
        rom[at:at + len(blob)] = blob
    return bytes(rom)


def universe(rom, root=CODE):
    return R.Code(rom, roots=[(root, 1, 3)])


def music_like(table, entries, zone_addr=ZONE, act_addr=ACT):
    """3*zone + act (8-bit) -> table, ending at the read; returns (code, read_pc)."""
    code = (ld_a_mem(zone_addr) + LD_B_A + ADD_A_A + ADD_A_B + LD_B_A + ld_a_mem(act_addr) + ADD_A_B + LD_L_A + LD_H_0
            + ld_de(table) + ADD_HL_DE)
    return code, CODE + len(code)


def synthetic_consumer(entries=4, table=0x0300):
    code, read_pc = music_like(table, entries)
    rom = image({CODE: code + LD_A_HL + RET, table: bytes(range(0x81, 0x81 + entries)), table + entries: b"\xC9"})
    return rom, R.Consumer(rom, "syn", CODE, read_pc, table, 2, entries)


# --- the interpreter ---------------------------------------------------------------------------------------------
class InterpreterTests(unittest.TestCase):
    def run_code(self, code, ram=None, **kw):
        rom = image({CODE: code})
        m = R.Interp(rom, ram=ram, **kw)
        why = m.run(CODE)
        return m, why

    def test_add_wraps_modulo_256_and_sets_carry(self):
        m, _ = self.run_code(ld_a(0xF0) + b"\xC6\x20" + st_a(0xC100) + RET)
        self.assertEqual(m.ram[0xC100], 0x10)
        self.assertTrue(m.c)

    def test_cp_sets_zero_and_carry_like_the_z80(self):
        m, _ = self.run_code(ld_a(5) + CP_N(5) + RET)
        self.assertTrue(m.z)
        self.assertFalse(m.c)
        m, _ = self.run_code(ld_a(4) + CP_N(5) + RET)
        self.assertTrue(m.c)
        self.assertFalse(m.z)

    def test_conditional_jump_follows_the_flag(self):
        # LD A,3 / CP 3 / JR NZ,+2 / LD A,9 / LD (C100),A / RET
        code = ld_a(3) + CP_N(3) + b"\x20\x02" + ld_a(9) + st_a(0xC100) + RET
        m, _ = self.run_code(code)
        self.assertEqual(m.ram[0xC100], 9)

    def test_call_and_conditional_return_use_a_stack(self):
        sub = CODE + 0x20
        rom = image({CODE: b"\xCD" + w(sub) + st_a(0xC100) + RET, sub: ld_a(7) + b"\xC8" + ld_a(8) + RET})
        m = R.Interp(rom)
        m.run(CODE)
        self.assertEqual(m.ram[0xC100], 8)         # RET Z not taken (Z clear), so LD A,8 runs

    def test_unsupplied_ram_read_raises_instead_of_inventing_a_value(self):
        with self.assertRaises(R.Unmodelled):
            self.run_code(ld_a_mem(0xC123) + RET)

    def test_ram_mirror_reads_the_same_byte(self):
        m, _ = self.run_code(ld_a_mem(0xE123) + st_a(0xC100) + RET, ram={0xC123: 0x55})
        self.assertEqual(m.ram[0xC100], 0x55)

    def test_store_to_rom_or_mapper_raises(self):
        with self.assertRaises(R.Unmodelled):
            self.run_code(ld_a(1) + st_a(0xFFFF) + RET)
        with self.assertRaises(R.Unmodelled):
            self.run_code(ld_a(1) + st_a(0x1000) + RET)

    def test_unsupported_instruction_raises(self):
        with self.assertRaises(R.Unmodelled):
            self.run_code(b"\x27" + RET)           # DAA

    def test_unverified_slot_raises(self):
        rom = image({CODE: ld_a_mem(0x8000) + RET})
        m = R.Interp(rom, slot2=None)
        with self.assertRaises(R.Unmodelled):
            m.run(CODE)

    def test_wide_store_writes_both_bytes(self):
        m, _ = self.run_code(ld_hl(0x1234) + st_hl(0xC100) + RET)
        self.assertEqual((m.ram[0xC100], m.ram[0xC101]), (0x34, 0x12))

    def test_bit_operations_on_hl_memory(self):
        m, _ = self.run_code(ld_hl(0xC200) + b"\xCB\xEE" + b"\xCB\xA6" + RET, ram={0xC200: 0x10})
        self.assertEqual(m.ram[0xC200], 0x20)       # SET 5 then RES 4

    def test_step_limit_is_an_error_not_a_result(self):
        rom = image({CODE: b"\x18\xFE"})           # JR $-0
        with self.assertRaises(R.Unmodelled):
            R.Interp(rom).run(CODE, limit=50)


# --- bank selection ------------------------------------------------------------------------------------------------
class BankSelection(unittest.TestCase):
    def test_slot_two_bank_selects_the_physical_bytes(self):
        rom = image({0x8000: b"\x11", 0xC000: b"\x22", CODE: ld_a_mem(0x8000) + st_a(0xC100) + RET})
        for bank, want in ((2, 0x11), (3, 0x22)):
            m = R.Interp(rom, slot2=bank)
            m.run(CODE)
            self.assertEqual(m.ram[0xC100], want)

    def test_slot_one_bank_selects_the_physical_bytes(self):
        rom = image({0x4000: b"\x33", 0x8000: b"\x44", CODE: ld_a_mem(0x4000) + st_a(0xC100) + RET})
        for bank, want in ((1, 0x33), (2, 0x44)):
            m = R.Interp(rom, slot1=bank)
            m.run(CODE)
            self.assertEqual(m.ram[0xC100], want)

    def test_file_offset_arithmetic(self):
        m = R.Interp(bytes(0x10000), slot1=1, slot2=3)
        self.assertEqual((m.file_of(0x0123), m.file_of(0x4001), m.file_of(0x8002)), (0x123, 0x4001, 0xC002))

    def test_a_consumer_table_in_a_banked_slot_depends_on_the_bank(self):
        table = 0x8000
        code, read_pc = music_like(table, 4)
        rom = image({CODE: code + LD_A_HL + RET, 0x8000: bytes([1, 2, 3, 4]), 0xC000: bytes([9, 9, 9, 9])})
        c2 = R.Consumer(rom, "x", CODE, read_pc, table, 2, 4)
        c3 = R.Consumer(rom, "x", CODE, read_pc, table, 3, 4)
        self.assertEqual(c2.address(0, 1), c3.address(0, 1))           # the address is the same ...
        m = R.Interp(rom, ram={ZONE: 0, ACT: 1}, slot2=3)               # ... the byte read is not
        m.run(CODE)
        self.assertEqual(m.reg["A"], 9)
        m = R.Interp(rom, ram={ZONE: 0, ACT: 1}, slot2=2)
        m.run(CODE)
        self.assertEqual(m.reg["A"], 2)


# --- consumers: valid / invalid, off-by-one, wrapping --------------------------------------------------------------
class ConsumerIndex(unittest.TestCase):
    def test_valid_and_invalid_combinations(self):
        _rom, c = synthetic_consumer(entries=4)
        self.assertTrue(c.valid(0, 0))
        self.assertTrue(c.valid(1, 0))              # 3
        self.assertFalse(c.valid(1, 1))             # 4 is one past the table
        self.assertFalse(c.valid(2, 0))

    def test_off_by_one_at_the_last_entry(self):
        _rom, c = synthetic_consumer(entries=7)
        self.assertEqual(c.index(2, 0), 6)
        self.assertTrue(c.valid(2, 0))
        self.assertEqual(c.index(2, 1), 7)
        self.assertFalse(c.valid(2, 1))
        self.assertFalse(c.valid(0, 7))

    def test_index_is_eight_bit(self):
        _rom, c = synthetic_consumer(entries=4)
        self.assertEqual(c.index(100, 0), 300 - 256)         # 3*100 wraps
        self.assertEqual(c.index(0, 255), 255)
        self.assertEqual(c.index(1, 255), 258 - 256)          # 3 + 255 wraps to 2
        self.assertTrue(c.valid(1, 255))                       # a wrapped index is "valid" arithmetic, reported as such

    def test_valid_ranges_report_the_wrapped_runs(self):
        _rom, c = synthetic_consumer(entries=4)
        ranges = R.valid_ranges(c, [0, 1])
        self.assertEqual(ranges[0], [[0, 3]])
        self.assertEqual(ranges[1], [[0, 0], [253, 255]])

    def test_table_extent_is_bounded_by_the_first_call_target_above_the_base(self):
        table = 0x0300
        rom = image({CODE: b"\xCD" + w(table + 4) + RET, table: bytes(4), table + 4: RET})
        self.assertEqual(R.table_extent_by_code_entry(rom, table), 4)

    def test_no_code_target_means_no_extent(self):
        rom = image({CODE: RET, 0x0300: bytes(8)})
        self.assertIsNone(R.table_extent_by_code_entry(rom, 0x0300))


# --- the census ----------------------------------------------------------------------------------------------------
class Census(unittest.TestCase):
    def assess(self, code, extra=None):
        blobs = {CODE: code + RET}
        blobs.update(extra or {})
        rom = image(blobs)
        return rom, R.writer_assessment(rom, universe(rom))

    def test_clean_constant_writers_close_the_set(self):
        _rom, wa = self.assess(XOR_A + st_a(ZONE) + ld_a(2) + st_a(ACT))
        self.assertTrue(wa["closed"])
        kinds = {c["kind"] for rows in wa["classes"].values() for _, c in rows}
        self.assertEqual(kinds, {"const"})

    def test_values_are_derived_from_the_feeding_instruction(self):
        _rom, wa = self.assess(ld_a(7) + st_a(ZONE) + st_a(ACT))
        zone = wa["classes"]["zone"][0][1]
        act = wa["classes"]["act"][0][1]
        self.assertEqual((zone["kind"], zone["value"]), ("const", 7))
        self.assertEqual((act["kind"], act["value"]), ("const", 7))      # a store after a store still sees LD A,7

    def test_increment_is_recognised_and_is_not_a_bound(self):
        _rom, wa = self.assess(ld_a_mem(ACT) + INC_A + st_a(ACT))
        self.assertEqual(wa["classes"]["act"][0][1]["kind"], "increment")

    def test_copy_and_table_derived_values(self):
        _rom, wa = self.assess(ld_a_mem(R.SAVED_ZONE) + st_a(ZONE) + ld_hl(0x0300) + LD_A_HL + st_a(ACT))
        self.assertEqual(wa["classes"]["zone"][0][1]["kind"], "copy")
        self.assertEqual(wa["classes"]["act"][0][1]["kind"], "computed")

    def test_ret_nz_after_or_a_proves_a_zero_store(self):
        code = ld_a_mem(0xC400) + b"\xB7" + b"\xC0" + st_a(ZONE)
        _rom, wa = self.assess(code)
        c = wa["classes"]["zone"][0][1]
        self.assertEqual((c["kind"], c["value"]), ("const", 0))

    def test_mirror_alias_store_is_found(self):
        _rom, wa = self.assess(ld_a(9) + st_a(ZONE + 0x2000))
        sites = wa["census"]["zone"]
        self.assertEqual([s["mirror_alias"] for s in sites], [True])

    def test_wide_store_covering_the_byte_is_found_and_keeps_the_set_open(self):
        _rom, wa = self.assess(ld_hl(0x0102) + st_hl(ZONE - 1))          # writes zone-1 and zone (the high byte)
        forms = [s["form"] for s in wa["census"]["zone"]]
        self.assertIn("LD (nn),HL", forms)
        self.assertFalse(wa["closed"])
        self.assertTrue(wa["unclassified"])

    def test_wide_store_at_the_act_covers_the_zone_byte_only_as_the_low_byte_of_the_next(self):
        _rom, wa = self.assess(ld_hl(0x0102) + st_hl(ACT))
        self.assertEqual([s["form"] for s in wa["census"]["act"]], ["LD (nn),HL"])
        self.assertEqual(wa["census"]["zone"], [])

    def test_index_register_store_is_a_writer_hit(self):
        _rom, wa = self.assess(b"\xDD\x21\x02\x01" + b"\xDD\x22" + w(ZONE))
        self.assertIn("LD (nn),IX", [s["form"] for s in wa["census"]["zone"]])
        self.assertFalse(wa["closed"])

    def test_pointer_to_the_zone_with_a_store_through_it_is_resolved_and_touches(self):
        _rom, wa = self.assess(ld_hl(ZONE) + ld_a(3) + LD_HL_A)
        hit = [p for p in wa["pointers"] if p["value"] == ZONE][0]
        self.assertEqual(hit["status"], "resolved")
        self.assertTrue(hit["touches_targets"])
        self.assertFalse(wa["closed"])

    def test_pointer_walked_by_inc_hl_reaches_the_act(self):
        _rom, wa = self.assess(ld_hl(ZONE) + INC_HL + ld_a(3) + LD_HL_A)
        hit = [p for p in wa["pointers"] if p["value"] == ZONE][0]
        self.assertTrue(hit["touches_targets"])

    def test_pointer_with_arithmetic_is_unresolved(self):
        _rom, wa = self.assess(ld_hl(ZONE) + ld_de(1) + ADD_HL_DE + ld_a(3) + LD_HL_A)
        hit = [p for p in wa["pointers"] if p["value"] == ZONE][0]
        self.assertEqual(hit["status"], "unresolved")
        self.assertFalse(wa["closed"])

    def test_a_pointer_to_a_neighbouring_flag_does_not_touch(self):
        _rom, wa = self.assess(ld_hl(R.STATE_FLAGS) + b"\xCB\xEE")        # SET 5,(HL) on $D293
        hit = [p for p in wa["pointers"] if p["value"] == R.STATE_FLAGS][0]
        self.assertEqual(hit["status"], "resolved")
        self.assertFalse(hit["touches_targets"])
        self.assertTrue(wa["closed"] or not wa["unresolved_pointers"])

    def test_block_move_over_the_bytes_is_a_writer_unless_it_is_a_zero_fill(self):
        fill = ld_hl(0xD000) + ld_de(0xD001) + ld_bc(0x0400) + LD_HL_0 + LDIR
        _rom, wa = self.assess(fill)
        site = [b for b in wa["block_moves"] if b["status"] == "resolved"][0]
        self.assertTrue(site["touches_targets"])
        self.assertTrue(site["fill_zero"])
        copy = ld_hl(0x0300) + ld_de(0xD000) + ld_bc(0x0400) + LDIR
        _rom, wa = self.assess(copy)
        site = [b for b in wa["block_moves"] if b["status"] == "resolved"][0]
        self.assertTrue(site["touches_targets"])
        self.assertFalse(site["fill_zero"])
        self.assertFalse(wa["closed"])

    def test_block_move_short_of_the_bytes_does_not_touch(self):
        _rom, wa = self.assess(ld_hl(0x0300) + ld_de(0xD000) + ld_bc(0x0010) + LDIR)
        site = [b for b in wa["block_moves"] if b["status"] == "resolved"][0]
        self.assertFalse(site["touches_targets"])

    def test_block_move_with_register_destination_is_unresolved(self):
        _rom, wa = self.assess(LDIR)
        self.assertEqual(wa["block_moves"][0]["status"], "unresolved")
        self.assertFalse(wa["closed"])

    def test_a_store_outside_the_discovered_code_is_reported_not_dismissed(self):
        rom = image({CODE: RET, 0x0400: ld_a(1) + st_a(ZONE)})
        wa = R.writer_assessment(rom, universe(rom))
        c = wa["classes"]["zone"][0][1]
        self.assertEqual((c["kind"], c["value"], c["in_discovered_code"]), ("const", 1, False))
        self.assertFalse(wa["closed"])                      # a writer the model cannot place keeps the set open

    def test_mapper_stores_are_split_into_code_and_data(self):
        rom = image({CODE: XOR_A + st_a(0xFFFD) + RET, 0x0500: st_a(0xFFFD)})
        res = R.slot0_mapper_stores(rom, universe(rom))
        self.assertEqual([r["value"] for r in res["in_discovered_code"]], [0])
        self.assertEqual(res["outside_discovered_code"], [0x0500])
        self.assertTrue(res["slot0_is_bank_0_in_code"])
        rom = image({CODE: ld_a(5) + st_a(0xFFFD) + RET})
        self.assertFalse(R.slot0_mapper_stores(rom, universe(rom))["slot0_is_bank_0_in_code"])


# --- adjacent stores: order and the transient pair ----------------------------------------------------------------
class IntermediateStates(unittest.TestCase):
    def pairs(self, code):
        rom = image({CODE: code + RET})
        return R.adjacent_pairs(rom, R.store_census(rom))

    def test_zone_before_act(self):
        p = self.pairs(ld_a(5) + st_a(ZONE) + XOR_A + st_a(ACT))[0]
        self.assertEqual(p["first"], "zone")
        self.assertFalse(p["call_or_ei_between"])

    def test_act_before_zone(self):
        p = self.pairs(XOR_A + st_a(ACT) + ld_a_mem(ZONE) + INC_A + st_a(ZONE))[0]
        self.assertEqual(p["first"], "act")
        self.assertEqual(p["between"], ["LD A,(0xd297)", "INC A"])

    def test_a_call_between_the_stores_is_flagged(self):
        p = self.pairs(ld_a(5) + st_a(ZONE) + b"\xCD" + w(0x0200) + XOR_A + st_a(ACT))[0]
        self.assertTrue(p["call_or_ei_between"])

    def test_an_ei_between_the_stores_is_flagged(self):
        p = self.pairs(ld_a(5) + st_a(ZONE) + b"\xFB" + XOR_A + st_a(ACT))[0]
        self.assertTrue(p["call_or_ei_between"])

    def test_a_branch_between_the_stores_ends_the_pair(self):
        self.assertEqual(self.pairs(ld_a(5) + st_a(ZONE) + b"\x18\x00" + XOR_A + st_a(ACT)), [])


# --- the model: reachability, grounded edges, counterexamples ------------------------------------------------------
def counter_step(limit_guard=None):
    """A toy machine: state (zone, act, mode, saved). 'bump' increments the act (optionally guarded), 'jump' raises the zone."""
    def step(s):
        z, a, mode, saved = s
        out = []
        if limit_guard is None or a < limit_guard:
            out.append(("bump", (z, a + 1, mode, saved), True, []))
        if z < 2:
            out.append(("zone", (z + 1, 0, mode, saved), True, [(z, 0)]))
        return out
    return step


class Model(unittest.TestCase):
    start = [((0, 0, "play", 0), True)]

    def test_guarded_increment_has_a_bound_and_no_cut(self):
        seen, cut, _ = R.explore(self.start, counter_step(limit_guard=2), cap=10)
        self.assertEqual(max(s[1] for s in seen), 2)
        self.assertEqual(cut, [])

    def test_unguarded_increment_reaches_the_cap_and_reports_it(self):
        seen, cut, _ = R.explore(self.start, counter_step(), cap=5)
        self.assertEqual(max(s[1] for s in seen), 5)
        self.assertTrue(cut)

    def test_intermediate_pairs_are_collected_with_the_event(self):
        _, _, inter = R.explore(self.start, counter_step(limit_guard=1), cap=10)
        self.assertEqual(inter[(0, 0)], "zone")

    def test_zone_before_act_and_act_before_zone_produce_different_transients(self):
        def zone_first(s):
            z, a, m, sv = s
            return [("zf", (5, 0, m, sv), True, [(5, a)])] if z == 0 else []

        def act_first(s):
            z, a, m, sv = s
            return [("af", (5, 0, m, sv), True, [(z, 0)])] if z == 0 else []
        start = [((0, 9, "play", 0), True)]
        self.assertIn((5, 9), R.explore(start, zone_first)[2])
        self.assertIn((0, 0), R.explore(start, act_first)[2])
        self.assertNotIn((5, 9), R.explore(start, act_first)[2])

    def test_a_second_path_with_a_weaker_bound_is_found(self):
        def step(s):
            z, a, m, sv = s
            out = []
            if a < 2:                                     # path 1: guarded
                out.append(("guarded", (z, a + 1, m, sv), True, []))
            if z == 1:                                    # path 2: unguarded, from another entry
                out.append(("unguarded", (z, a + 1, m, sv), True, []))
            if z == 0 and a == 2:
                out.append(("enter", (1, a, m, sv), True, []))
            return out
        tabs = {"any": R.explore(self.start, step, cap=8)}
        tabs["grounded"] = R.explore(self.start, step, cap=8, grounded_only=True)
        every, grounded, witness = R.find_violations(tabs, lambda s: s[1] > 2)
        self.assertTrue(every)
        self.assertTrue(grounded)
        self.assertIn("unguarded", [p["via"] for p in witness])

    def test_a_value_valid_in_one_mode_is_invalid_in_another(self):
        def step(s):
            z, a, mode, sv = s
            if mode == "play" and z == 0:
                return [("to_ss", (9, a, "ss", 0), True, [])]
            return []
        tabs = {"any": R.explore([((0, 0, "play", 0), True)], step)}
        tabs["grounded"] = tabs["any"]
        valid_by_mode = {"play": range(0, 6), "ss": range(8, 13)}
        bad = lambda s: s[0] not in valid_by_mode[s[2]]                    # noqa: E731
        self.assertEqual(R.find_violations(tabs, bad)[0], [])              # zone 9 is fine in a special stage
        self.assertTrue(R.find_violations(tabs, lambda s: s[0] not in valid_by_mode["play"])[0])   # but not in play

    def test_ungrounded_edges_do_not_give_a_counterexample(self):
        def step(s):
            z, a, m, sv = s
            return [("maybe", (z, a + 1, m, sv), False, [])] if a < 3 else []
        tabs = {"any": R.explore(self.start, step), "grounded": R.explore(self.start, step, grounded_only=True)}
        every, grounded, witness = R.find_violations(tabs, lambda s: s[1] > 2)
        self.assertTrue(every)
        self.assertEqual(grounded, [])
        self.assertIsNone(witness)

    def test_skipped_event_classes_are_not_taken(self):
        def step(s):
            return [("menu", (3, 0, "play", 0), True, [])] if s[0] == 0 else []
        seen, _, _ = R.explore(self.start, step, classes={"menu": "hidden_menu"}, skip_classes=("hidden_menu",))
        self.assertEqual(list(seen), [(0, 0, "play", 0)])

    def test_type_5_slot_surviving_a_zone_transition_is_detected(self):
        types = {(2, 0, "play", 0): (5, 0, 0, 0), (7, 0, "play", 0): (5, 0, 0, 0), (3, 0, "play", 0): (1, 0, 0, 0)}
        states = list(types)
        bad = R.survivors(states, lambda s: types[s], zone_ok={0, 1, 2, 3, 4, 5})
        self.assertEqual(bad, [(7, 0, "play", 0)])
        self.assertEqual(R.survivors(states, lambda s: None, zone_ok=set()), [])

    def test_path_to_replays_the_events(self):
        seen, _, _ = R.explore(self.start, counter_step(limit_guard=2), cap=10)
        chain = R.path_to(seen, (0, 2, "play", 0))
        self.assertEqual([c["via"] for c in chain], ["initial", "bump", "bump"])


class StatusDerivation(unittest.TestCase):
    def test_a_grounded_counterexample_outranks_everything(self):
        self.assertEqual(R.derive_status(True, True, True), "DISPROVEN")
        self.assertEqual(R.derive_status(True, False, False), "DISPROVEN")

    def test_proven_needs_a_closed_argument(self):
        self.assertEqual(R.derive_status(False, True, True), "PROVEN")

    def test_unresolved_writers_prevent_promotion(self):
        rom = image({CODE: ld_a(1) + st_hl(ZONE - 1) + RET})
        wa = R.writer_assessment(rom, universe(rom))
        self.assertFalse(wa["closed"])
        self.assertEqual(R.derive_status(False, wa["closed"], True), "PARTIAL")

    def test_without_any_proven_part_the_status_is_unproven(self):
        self.assertEqual(R.derive_status(False, False, False), "UNPROVEN")

    def test_absence_of_a_counterexample_is_not_a_proof(self):
        rom = image({CODE: XOR_A + st_a(ZONE) + st_a(ACT) + ld_hl(0x0300) + LDIR + RET})
        wa = R.writer_assessment(rom, universe(rom))
        self.assertFalse(wa["closed"])                       # an unresolved block move
        self.assertEqual(R.derive_status(False, wa["closed"], True), "PARTIAL")


# --- the rest of the module's generic pieces ------------------------------------------------------------------------
class DispatchChains(unittest.TestCase):
    def test_rlca_chain_maps_bits_to_targets(self):
        code = b"\x07\xDA" + w(0x0200) + b"\x07\xD2" + w(0x0300) + b"\x07\xDA" + w(0x0400)
        rom = image({CODE: code})
        chain = R.rlca_chain(rom, CODE)
        self.assertEqual(chain, OrderedDict([(7, ("c", 0x0200)), (6, ("nc", 0x0300)), (5, ("c", 0x0400))]))

    def test_rlca_chain_skips_unbranched_rotations(self):
        code = b"\x07\x07\xDA" + w(0x0200)
        self.assertEqual(R.rlca_chain(image({CODE: code}), CODE), OrderedDict([(6, ("c", 0x0200))]))

    def test_bit_effects_read_the_feeding_immediate(self):
        rom = image({CODE: ld_a(0x50) + st_a(R.STATE_FLAGS) + RET})
        code = universe(rom)
        rows = R.bit_effects(rom, code, R.flag_setters(rom, code, R.STATE_FLAGS))
        self.assertEqual(rows[0]["assigns"], 0x50)
        self.assertEqual(R.setters_of_bit(rows, 4), [rows[0]["file_offset"]])
        self.assertEqual(R.setters_of_bit(rows, 5), [])

    def test_a_store_with_an_unknown_feeder_may_set_any_bit(self):
        rom = image({CODE: ld_a_mem(0xC400) + st_a(R.STATE_FLAGS) + RET})
        code = universe(rom)
        rows = R.bit_effects(rom, code, R.flag_setters(rom, code, R.STATE_FLAGS))
        self.assertIsNone(rows[0]["assigns"])
        self.assertEqual(R.setters_of_bit(rows, 5), [rows[0]["file_offset"]])

    def test_hl_bit_ops_after_a_flag_pointer_are_collected(self):
        rom = image({CODE: ld_hl(R.STATE_FLAGS) + b"\xCB\xEE" + b"\xCB\xA6" + RET})
        code = universe(rom)
        rows = R.bit_effects(rom, code, R.flag_setters(rom, code, R.STATE_FLAGS))
        self.assertEqual([r.get("sets") or r.get("clears") for r in rows], [[5], [4]])


class OutputFormat(unittest.TestCase):
    def test_render_block_is_stable_and_framed(self):
        doc = OrderedDict([
            ("propositions", OrderedDict((k, OrderedDict([("title", "t"), ("status", "PARTIAL"),
                                                          ("grounded_counterexample", None)])) for k in "ABC")),
            ("census", OrderedDict([("absolute_store_sites", {"zone": 1, "act": 2, "saved_zone": 3}),
                                    ("wide_or_index_register_store_hits", []), ("mirror_alias_store_hits", [])])),
            ("transition_model", OrderedDict([("act_cap", 4), ("states", {"any": 1, "grounded": 1, "normal": 1})])),
            ("verdict", OrderedDict([("supported_bounds", {"music_index_in_table_iff": "x", "nested_dispatcher_zones": [0]})]))])
        a, b = R.render_block(doc), R.render_block(doc)
        self.assertEqual(a, b)
        self.assertTrue(a.startswith(R.BEGIN) and a.endswith(R.END_MARK))

    def test_dumps_is_newline_terminated_and_ascii(self):
        text = R.dumps(OrderedDict([("a", 1), ("b", "é")]))
        self.assertTrue(text.endswith("\n"))
        text.encode("ascii")


# --- the canonical ROM ------------------------------------------------------------------------------------------------
_CACHE = {}


def built():
    if "doc" not in _CACHE:
        rom = canonical_rom()
        doc, ctx = R.build(rom)
        _CACHE["doc"], _CACHE["ctx"], _CACHE["rom"] = doc, ctx, rom
    return _CACHE["doc"], _CACHE["ctx"], _CACHE["rom"]


class CanonicalRom(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if canonical_rom() is None:
            raise unittest.SkipTest("canonical ROM not available")
        cls.doc, cls.ctx, cls.rom = built()

    # census -----------------------------------------------------------------------------------------------------------
    def test_writer_sets_are_exactly_the_derived_absolute_stores(self):
        w_ = self.doc["writers"]
        self.assertEqual([x["file_offset"] for x in w_["zone"]],
                         [0x6CD, 0x7CF, 0x821, 0x15D6, 0x1870, 0x1897, 0x2A27, 0x2BE8, 0x2C55])
        self.assertEqual([x["file_offset"] for x in w_["act"]],
                         [0x6D1, 0x7D2, 0x826, 0x1538, 0x15CF, 0x2A2A, 0x2BEB, 0x2C6E])
        self.assertEqual([x["file_offset"] for x in w_["saved_zone"]], [0x187E])

    def test_no_wide_index_or_mirror_writer_exists(self):
        c = self.doc["census"]
        self.assertEqual((c["wide_or_index_register_store_hits"], c["mirror_alias_store_hits"]), ([], []))

    def test_every_absolute_writer_is_classified_and_in_discovered_code(self):
        self.assertEqual(self.doc["census"]["unclassified_or_undiscovered_store_sites"], [])
        kinds = {x["file_offset"]: x["kind"] for rows in self.doc["writers"].values() for x in rows}
        self.assertEqual(kinds[0x15D6], "increment")
        self.assertEqual(kinds[0x1538], "increment")
        self.assertEqual(kinds[0x1870], "copy")
        self.assertEqual(kinds[0x6CD], "const")

    def test_literal_writers_have_their_values(self):
        by = {x["file_offset"]: x for x in self.doc["writers"]["zone"]}
        self.assertEqual(by[0x6CD]["value"], 7)
        for off in (0x7CF, 0x2A27, 0x2BE8):
            self.assertEqual(by[off]["value"], 0)

    def test_boot_and_restart_clear_the_bytes(self):
        clears = self.doc["census"]["boot_and_restart_ram_clear"]
        self.assertEqual([c["file_offset"] for c in clears], [0x29, 0x462])
        self.assertTrue(all(c["writes_value_zero"] for c in clears))

    def test_no_resolved_pointer_or_block_move_writes_a_target_apart_from_the_zero_fills(self):
        c = self.doc["census"]
        self.assertEqual(c["pointer_materialisations"]["resolved_hits_that_write_a_target"], [])
        self.assertEqual(c["block_moves"]["resolved_that_touch_a_target"], ["$0029", "$0462"])

    def test_unresolved_block_moves_are_listed_not_hidden(self):
        self.assertTrue(self.doc["census"]["block_moves"]["unresolved_in_discovered_code"])

    def test_slot_zero_is_bank_zero_in_discovered_code(self):
        m = self.doc["census"]["slot0_mapper_register_stores"]
        self.assertTrue(m["slot0_is_bank_0_in_code"])
        self.assertEqual(m["outside_discovered_code"], ["$4FE4C"])

    def test_every_reader_of_zone_and_act_is_listed_with_the_assigned_ones_marked(self):
        readers = self.doc["census"]["all_readers"]
        assigned = {r["file_offset"]: r["assigned"] for r in readers if r["assigned"]}
        self.assertEqual(sorted(assigned), [0x18A0, 0x18A7, 0x2A53, 0x2A61, 0x741E0])
        self.assertGreater(len(readers), 30)

    # executed value domains ---------------------------------------------------------------------------------------
    def test_level_select_pairs_are_the_eighteen_zone_act_combinations(self):
        self.assertEqual(self.doc["value_domains"]["zone"]["level_select_pairs"],
                         [[z, a] for z in range(6) for a in range(3)])
        self.assertEqual(self.doc["value_domains"]["zone"]["level_select_index_domain"], [0, 17])

    def test_rotation_rows_write_zones_0_1_2_with_act_0(self):
        rows = self.doc["value_domains"]["zone"]["rotation_rows_zone_act_character"]
        self.assertEqual(rows, [[0, 0, 1], [1, 0, 2], [2, 0, 1]])

    def test_special_stage_zone_is_8_to_12_and_depends_only_on_the_emerald_byte(self):
        counts = self.doc["value_domains"]["zone"]["special_stage_zone_emerald_byte_counts"]
        self.assertEqual(sorted(int(k) for k in counts), [8, 9, 10, 11, 12])
        self.assertEqual(sum(counts.values()), 256)

    # flow ---------------------------------------------------------------------------------------------------------
    def test_state_dispatch_maps_bits_to_the_act_and_zone_complete_handlers(self):
        d = self.doc["flow_facts"]["state_dispatch_d293"]
        self.assertEqual(d["5"], ["c", "$14AE"])
        self.assertEqual(d["4"], ["c", "$1543"])
        self.assertEqual(self.doc["flow_facts"]["special_dispatch_d294"], {"8": ["c", "$1762"]})

    def test_bit5_setters_include_the_special_stage_return_and_the_act_below_two_trigger(self):
        s = self.doc["flow_facts"]["d293_bit5_setters"]
        self.assertIn("$1876", s)
        self.assertIn("$303E7", s)

    def test_special_stage_is_armed_only_at_one_site_and_ignores_the_act(self):
        fx = self.doc["flow_facts"]
        self.assertEqual(fx["d294_bit3_setters"], ["$17A7"])
        self.assertFalse(self.doc["transition_model"]["special_stage_entry_guard"]["reads_act"])
        for k, v in fx["ring_paths_to_special_stage"].items():
            self.assertFalse(v["reads_act"], k)

    def test_conditional_callers_of_the_music_routine_are_in_the_census(self):
        kinds = {c["file_offset"]: c["kind"] for c in self.doc["flow_facts"]["callers_music_189B"]}
        self.assertEqual(kinds[0x2853], "JP cc")
        self.assertEqual(kinds[0x17F7], "CALL")

    def test_the_act_increment_is_straight_line_code(self):
        self.assertEqual(self.doc["flow_facts"]["act_increment_chain_14AE_to_1538"]["branches_between"], [])
        self.assertTrue(self.doc["transition_model"]["act_growth_mechanism"]["increment_unguarded"])

    def test_level_end_flag_depends_on_the_act(self):
        lf = self.doc["transition_model"]["level_end_flag_by_act"]
        self.assertEqual((lf["act_0_1"], lf["act_2_to_255"]), ("$0020", "$0010"))

    # consumers --------------------------------------------------------------------------------------------------------
    def test_music_consumer_geometry(self):
        c = R.music_consumer(self.rom)
        self.assertEqual((c.base, c.extent), (0x18BA, 39))
        self.assertEqual(c.index(12, 2), 38)
        self.assertEqual(c.index(12, 3), 39)
        self.assertTrue(c.valid(12, 2))
        self.assertFalse(c.valid(12, 3))
        self.assertEqual(c.index(5, 255), (15 + 255) & 0xFF)

    def test_music_index_matches_the_arithmetic_for_every_pair(self):
        c = R.music_consumer(self.rom)
        for z in range(0, 256, 5):
            for a in range(256):
                self.assertEqual(c.index(z, a), (3 * z + a) & 0xFF)

    def test_loader_selects_nine_records_for_the_proposed_domain(self):
        recs = self.doc["propositions"]["B"]["records_selected_by_proposed_domain"]
        self.assertEqual(recs, ["$2AF6", "$2B00", "$2B0A", "$2B14", "$2B1E", "$2B28", "$2B32", "$2B3C", "$2B46"])

    def test_loader_slot_types_come_from_the_record(self):
        types = self.doc["propositions"]["B"]["slot_types_by_record"]
        self.assertEqual(types["$2B0A"], [5, 0, 0, 0])
        self.assertEqual(types["$2B28"], [5, 6, 8, 13])

    def test_loader_safe_act_bounds(self):
        safe = self.doc["propositions"]["B"]["safe_act_bound_by_zone"]
        self.assertEqual((safe["0"], safe["5"], safe["8"], safe["10"], safe["14"]), (29, 14, 8, 5, 2))

    def test_loader_uses_eight_bit_act_doubling(self):
        ptr_ok = R.loader_run(self.rom, 0, 128)          # 2*128 wraps to 0 -> the first pointer again
        self.assertEqual(ptr_ok[0], R.loader_run(self.rom, 0, 0)[0])

    def test_garbage_record_pointers_are_unresolved_not_interpreted(self):
        rec, types, err = R.loader_run(self.rom, 8, 9)
        self.assertIsNone(rec)
        self.assertIn("unverified", err)

    def test_nested_dispatcher_table_geometry(self):
        entries, end = R.nested_table(self.rom)
        self.assertEqual((len(entries), end), (12, 0x820A))
        for z in range(6):
            for b in (0, 1):
                self.assertLess(R.nested_word_address(self.rom, z, b) + 1, end)
        self.assertGreaterEqual(R.nested_word_address(self.rom, 6, 0), end)

    def test_nested_dispatcher_reads_through_bank_1d(self):
        t = R.nested_target(self.rom, 2, 1)
        off = 0x1D * 0x4000 + (0x81F2 + 2 * ((2 * 2 + 1))) - 0x8000
        self.assertEqual(t, self.rom[off] | self.rom[off + 1] << 8)
        with self.assertRaises(R.Unmodelled):
            R.Interp(self.rom, ram={ZONE: 2}, slot2=None, regs={"B": 1}).run(R.NESTED_START, stops=(R.NESTED_JP,))

    def test_nested_dispatcher_reads_only_the_zone(self):
        m = R.Interp(self.rom, ram={ZONE: 3}, slot1=1, slot2=R.NESTED_BANK, regs={"B": 0})
        m.run(R.NESTED_START, stops=(R.NESTED_JP,))
        self.assertEqual(sorted(set(m.reads)), [ZONE])

    def test_type_5_records_belong_to_zones_2_4_5(self):
        p = self.doc["propositions"]["C"]
        self.assertEqual(p["records_with_a_type_5_slot"], ["$2B0A", "$2B1E", "$2B28"])
        self.assertEqual(p["zones_whose_own_acts_select_a_type_5_record"], [2, 4, 5])
        self.assertEqual(p["zones_inside_table_exhaustive"][:6], [0, 1, 2, 3, 4, 5])

    # the model ------------------------------------------------------------------------------------------------------------
    def test_normal_play_reaches_act_three_through_a_special_stage(self):
        ex = self.doc["propositions"]["B"]["grounded_counterexample"]
        self.assertEqual(ex["path_class"], "normal")
        vias = [s["via"] for s in ex["path"]]
        self.assertEqual(vias, ["initial", "act_complete", "act_complete", "special_stage_enter", "special_stage_return"])
        self.assertEqual(ex["path"][-1]["state"][:3], [0, 3, "play"])

    def test_the_counterexample_uses_no_hidden_menu_or_demo_event(self):
        ex = self.doc["propositions"]["B"]["grounded_counterexample"]
        self.assertNotIn("level_select", [s["via"] for s in ex["path"]])
        self.assertNotIn("rotation_demo", [s["via"] for s in ex["path"]])

    def test_grounded_states_are_the_expected_small_set(self):
        sm = self.doc["transition_model"]["summary_grounded"]
        self.assertEqual(sm["play"]["zones"], [0, 1, 2, 3, 4, 5])
        self.assertEqual(sm["ss"], {"zones": [8], "acts": [0, 8]})
        self.assertEqual(sm["play"]["acts"], [0, 9])

    def test_the_model_cut_at_the_act_cap_is_reported(self):
        self.assertGreater(self.doc["transition_model"]["states_cut_at_act_cap"]["any"], 0)

    # verdicts --------------------------------------------------------------------------------------------------------------
    def test_verdicts(self):
        P = self.doc["propositions"]
        self.assertEqual((P["A"]["status"], P["B"]["status"], P["C"]["status"]), ("PARTIAL", "DISPROVEN", "PARTIAL"))

    def test_proposition_a_has_no_grounded_violation_but_has_violations_on_ungrounded_paths(self):
        A = self.doc["propositions"]["A"]
        self.assertEqual(A["state_violations_grounded"], 0)
        self.assertEqual(A["intermediate_violations_grounded"], 0)
        self.assertGreater(A["state_violations_any_path"], 0)
        self.assertGreater(A["violations_in_forbidden_request_range"], 0)
        self.assertEqual(A["first_violating_act_by_special_stage_zone"], {"8": 15, "9": 12, "10": 9, "11": 6, "12": 3})

    def test_proposition_a_names_the_forbidden_range_witness(self):
        w_ = self.doc["propositions"]["A"]["first_forbidden_witness"]
        self.assertTrue(w_["in_forbidden_range"])
        self.assertFalse(w_["grounded"])
        self.assertTrue(0xC5 <= w_["byte"] <= 0xD3)

    def test_proposition_a_music_routine_is_inside_the_interrupt_closure(self):
        iv = self.doc["intermediate_states"]["interrupt_view"]
        self.assertTrue(iv["consumer_entries_inside_closure"]["music_189B"])
        self.assertTrue(iv["consumer_entries_inside_closure"]["nested_741E0"])
        self.assertFalse(iv["consumer_entries_inside_closure"]["loader_2A4F"])
        self.assertEqual(iv["music_callers_inside_closure"], ["$2853"])
        self.assertEqual(iv["loader_callers_inside_closure"], [])
        self.assertEqual(iv["writer_sites_inside_closure"], [])

    def test_proposition_b_sufficiency_and_the_act_counterexample(self):
        B = self.doc["propositions"]["B"]
        self.assertEqual(B["states_beyond_proposed_bounds_normal_play"] > 0, True)
        self.assertTrue(B["sub_claims"]["act_le_2_whenever_the_loader_runs"].startswith("DISPROVEN"))
        self.assertTrue(B["sub_claims"]["sufficiency_of_zone_le_15_and_act_le_2"].startswith("PROVEN"))
        self.assertTrue(B["sub_claims"]["zone_le_15_whenever_the_loader_runs"].startswith("PARTIAL"))

    def test_proposition_c_has_no_grounded_counterexample_and_keeps_unresolved_states(self):
        C = self.doc["propositions"]["C"]
        self.assertEqual(C["states_outside_table_zone_with_type_5_grounded"], 0)
        self.assertGreater(C["states_outside_table_zone_with_unresolved_record"], 0)

    def test_r1_is_not_promoted_and_each_dispatcher_reports_open_items_separately(self):
        rel = self.doc["r1_relationship"]
        self.assertEqual(rel["r1_overall"], "PARTIALLY CLOSED (unchanged)")
        self.assertEqual(sorted(rel["dispatchers"]), ["$08137", "$74027", "$741F1"])
        for d in rel["dispatchers"].values():
            self.assertEqual(sorted(d), ["closed_by_r2", "other_dependencies", "still_open"])
        self.assertFalse(self.doc["verdict"]["r1_overall_changes"])
        self.assertIn("SOUND TEST", rel["dispatchers"]["$08137"]["still_open"])

    def test_every_unresolved_dependency_is_named(self):
        ids = [u["id"] for u in self.doc["unresolved_dependencies"]]
        self.assertEqual(ids, ["U1", "U2", "U3", "U4", "U5", "U6"])

    def test_the_ledger_is_untouched(self):
        self.assertFalse(self.doc["ledger_effect"]["changed"])

    # the generator, not the JSON ---------------------------------------------------------------------------------
    def test_committed_evidence_regenerates_identically(self):
        committed = EVIDENCE.read_bytes() if EVIDENCE.is_file() else b""
        self.assertEqual(committed.replace(b"\r\n", b"\n"), R.dumps(self.doc).encode("utf-8"))

    def test_a_second_build_is_byte_identical(self):
        again, _ = R.build(self.rom)
        self.assertEqual(R.dumps(again), R.dumps(self.doc))

    def test_the_document_block_matches_the_evidence(self):
        if not DOC.is_file():
            self.skipTest("document not written yet")
        self.assertEqual(R.doc_block(DOC), R.render_block(self.doc))

    def test_r1_evidence_is_unchanged_in_the_facts_r2_relies_on(self):
        r1 = json.loads(R1_EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(r1["verdict"]["r1"], "PARTIALLY CLOSED")
        self.assertEqual((r1["verdict"]["proven_or_unreachable"], r1["verdict"]["partial"]), (4, 3))
        self.assertEqual(sorted(c["site"] for c in r1["open_conditions"]), [0x08137, 0x74027, 0x741F1])


class Rederivation(unittest.TestCase):
    """Mutate the ROM and re-run the generator's own stages: a verdict must follow the code, not a stored string."""

    @classmethod
    def setUpClass(cls):
        cls.rom = canonical_rom()
        if cls.rom is None:
            raise unittest.SkipTest("canonical ROM not available")

    def mutated(self, offset, new):
        rom = bytearray(self.rom)
        rom[offset:offset + len(new)] = new
        return bytes(rom)

    def world_violations(self, rom):
        world = R.World(rom)
        tabs = R.explore_world(world)
        return world, tabs, R.find_violations(tabs, lambda s: s[1] > 2 or s[0] > 15)

    def test_canonical_act_growth_is_found_by_the_generator(self):
        _w, _t, (every, grounded, witness) = self.world_violations(self.rom)
        self.assertTrue(grounded)
        self.assertIsNotNone(witness)

    def test_changing_the_special_stage_return_flag_removes_the_act_growth(self):
        # SET 5,(HL) at $1876 -> SET 4,(HL): the return no longer takes the act-complete path
        rom = self.mutated(0x1876, b"\xCB\xE6")
        world, _t, (every, grounded, witness) = self.world_violations(rom)
        self.assertEqual(grounded, [])
        self.assertEqual([s for s in every if s[1] > 2 and s[2] == "play" and s[0] <= 5], [])

    def test_removing_the_act_increment_removes_the_act_growth(self):
        rom = self.mutated(0x1537, b"\x00")            # INC A -> NOP
        _w, _t, (every, grounded, witness) = self.world_violations(rom)
        self.assertEqual(grounded, [])

    def test_removing_the_zone_guard_in_the_special_stage_entry_is_detected(self):
        rom = self.mutated(0x1799, b"\x00")            # RET NC -> NOP
        guard = R.special_stage_entry_guard(rom)
        self.assertFalse(guard["armed_only_when_character_1_zone_lt_6_emeralds_not_full"])

    def test_the_special_stage_guard_is_what_the_code_says(self):
        guard = R.special_stage_entry_guard(self.rom)
        self.assertTrue(guard["armed_only_when_character_1_zone_lt_6_emeralds_not_full"])
        self.assertTrue(guard["armed_for_all_sampled_such_inputs"])
        self.assertFalse(guard["reads_act"])

    def test_dropping_the_act_doubling_in_the_loader_changes_the_safe_bounds(self):
        rom = self.mutated(0x2A64, b"\x00")            # ADD A,A -> NOP
        _ptr, _recs, safe = R.loader_tables(rom)
        _ptr0, _recs0, safe0 = R.loader_tables(self.rom)
        self.assertNotEqual(safe, safe0)

    def test_changing_the_music_table_end_changes_the_extent(self):
        rom = self.mutated(0x14D8 + 1, b"\xC0\x18")    # CALL $18E1 -> CALL $18C0 (a nearer code target)
        self.assertEqual(R.table_extent_by_code_entry(rom, 0x18BA), 6)

    def test_removing_the_set_in_the_act_complete_flag_changes_the_level_end_flag(self):
        rom = self.mutated(0x303E7, b"\xCB\xE6")       # SET 5,(HL) -> SET 4,(HL)
        self.assertEqual(R.level_end_flag(rom)[0], 0x10)

    def test_zone_complete_branch_follows_the_compare(self):
        rom = self.mutated(0x15D9, b"\xFE\x07")        # CP 6 -> CP 7
        self.assertEqual(R.zone_complete_effect(rom)[5][2], 0x15DE)
        self.assertEqual(R.zone_complete_effect(self.rom)[5][2], 0x15E8)

    def test_the_special_stage_zone_follows_the_emerald_loop(self):
        zones = R.special_stage_zone(self.rom)
        self.assertEqual(sorted(zones), [8, 9, 10, 11, 12])
        rom = self.mutated(0x1881, b"\x06\x09")        # LD B,8 -> LD B,9
        self.assertEqual(sorted(R.special_stage_zone(rom)), [9, 10, 11, 12, 13])


if __name__ == "__main__":
    unittest.main()
