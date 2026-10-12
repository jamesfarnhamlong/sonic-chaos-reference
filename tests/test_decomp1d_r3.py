#!/usr/bin/env python3
"""DECOMP-1D-R3 tests: special-stage completion (U1) and invalid-record reachability (U3).

Synthetic tests build tiny images with hand-assembled Z80 and never need the ROM. Tests that need the canonical ROM skip without
SONIC_CHAOS_ROM or ../source/Sonic Chaos (Europe).sms; the controlled-execution tests also skip without the z80 core. Every verdict
is recomputed by the generator under test; the committed JSON is compared with a fresh run, never trusted.
"""
import hashlib
import json
import os
import sys
import unittest
from collections import OrderedDict
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import decomp1d_r2_zone_act as R2  # noqa: E402
import decomp1d_r3_special_stage as R3  # noqa: E402
import rom_flow as F  # noqa: E402
import rom_ledger as RL  # noqa: E402

EVIDENCE = ROOT / "data" / "decomp1d" / "r3-special-stage-reachability.json"
DOC = ROOT / "docs" / "decomp-1d-r3-special-stage-reachability.md"
ROM_PATH = Path(os.environ.get("SONIC_CHAOS_ROM", str(RL.DEFAULT_ROM)))
D293, D294 = R3.STATE_FLAGS, R3.SPECIAL_FLAGS


def canonical_rom():
    if ROM_PATH.is_file():
        data = ROM_PATH.read_bytes()
        if len(data) == RL.ROM_SIZE and hashlib.sha256(data).hexdigest() == RL.ROM_SHA256:
            return data
    return None


def harness_available():
    try:
        R3._harness()
        return True
    except R3.HarnessUnavailable:
        return False


# --- a tiny assembler -------------------------------------------------------------------------------------------------
def w(v):
    return bytes([v & 0xFF, v >> 8])


def ld_a_mem(a):
    return b"\x3A" + w(a)


def st_a(a):
    return b"\x32" + w(a)


def ld_a(n):
    return bytes([0x3E, n])


def ld_hl(v):
    return b"\x21" + w(v)


def jp(a):
    return b"\xC3" + w(a)


def jp_c(a):
    return b"\xDA" + w(a)


def call(a):
    return b"\xCD" + w(a)


RET, RLCA, SET4_HL, SET5_HL, RES4_HL = b"\xC9", b"\x07", b"\xCB\xE6", b"\xCB\xEE", b"\xCB\xA6"
CODE = 0x0100


def image(blobs, size=0x10000):
    rom = bytearray(size)
    for at, blob in blobs.items():
        rom[at:at + len(blob)] = blob
    return bytes(rom)


# A miniature of the main-loop dispatch: D294 bit 7 selects stage mode; in stage mode D294 bit 6 pre-empts, then D293 bits 5, 4;
# bits 7..6 and 3..0 are ignored. Entry points are RET stubs.
S_SUCCESS, S_ACT, S_ZONE, S_STAGE, S_NORMAL, S_ZONE_N = 0x0200, 0x0210, 0x0220, 0x0230, 0x0240, 0x0250
SYN_STOPS = (S_SUCCESS, S_ACT, S_ZONE, S_STAGE, S_NORMAL, S_ZONE_N)


def synthetic_dispatcher():
    ss = 0x0120
    start = (ld_a_mem(D294) + RLCA + jp_c(ss) + ld_a_mem(D293) + RLCA + RLCA + RLCA + RLCA + jp_c(S_ZONE_N) + jp(S_NORMAL))
    stage = (RLCA + jp_c(S_SUCCESS) + ld_a_mem(D293) + RLCA + RLCA + RLCA + jp_c(S_ACT) + RLCA + jp_c(S_ZONE) + jp(S_STAGE))
    blobs = {CODE: start, ss: stage}
    for a in SYN_STOPS:
        blobs[a] = RET
    return image(blobs)


def syn_dispatch(rom, d294, d293):
    return R3.dispatch_target(rom, d294, d293, start=CODE, stops=SYN_STOPS)


# --- the interpreter extension ----------------------------------------------------------------------------------------
class Interp3Tests(unittest.TestCase):
    def run_code(self, code, ram=None, **kw):
        rom = image({CODE: code})
        m = R3.Interp3(rom, ram=ram, **kw)
        why = m.run(CODE)
        return m, why

    def test_index_registers_address_ram_with_displacement(self):
        code = b"\xFD\x21" + w(0xC100) + b"\xFD\x7E\x03" + st_a(0xC200) + RET     # LD IY,$C100 / LD A,(IY+3) / LD ($C200),A
        m, _ = self.run_code(code, ram={0xC103: 0x5A})
        self.assertEqual(m.ram[0xC200], 0x5A)

    def test_store_through_ix_displacement(self):
        code = b"\xDD\x21" + w(0xC100) + ld_a(0x77) + b"\xDD\x77\x04" + RET       # LD IX,$C100 / LD A,$77 / LD (IX+4),A
        m, _ = self.run_code(code)
        self.assertEqual(m.ram[0xC104], 0x77)

    def test_push_pop_moves_a_pointer_into_iy(self):
        code = ld_hl(0xC180) + b"\xE5\xFD\xE1" + b"\xFD\x7E\x00" + st_a(0xC200) + RET   # PUSH HL / POP IY / LD A,(IY)
        m, _ = self.run_code(code, ram={0xC180: 9})
        self.assertEqual(m.ram[0xC200], 9)

    def test_unsupplied_ram_through_ix_raises(self):
        with self.assertRaises(R2.Unmodelled):
            self.run_code(b"\xDD\x21" + w(0xC100) + b"\xDD\x7E\x00" + RET)

    def test_bank_register_is_taken_modulo_the_bank_count(self):
        rom = bytearray(32 * 0x4000)
        rom[1 * 0x4000 + 5] = 0xAB
        rom[18 * 0x4000 + 5] = 0xCD
        m = R3.Interp3(bytes(rom), slot1=1, slot2=33)             # 33 mod 32 = 1
        self.assertEqual(m.read(0x8005), 0xAB)
        m = R3.Interp3(bytes(rom), slot1=1, slot2=50)             # 50 mod 32 = 18
        self.assertEqual(m.read(0x8005), 0xCD)

    def test_unverified_slot_still_raises(self):
        m = R3.Interp3(bytes(0x20000), slot1=None, slot2=None)
        with self.assertRaises(R2.Unmodelled):
            m.read(0x4000)
        with self.assertRaises(R2.Unmodelled):
            m.read(0x8000)

    def test_unsupported_instruction_and_computed_jump_raise(self):
        with self.assertRaises(R2.Unmodelled):
            self.run_code(b"\xE9")                                # JP (HL)
        with self.assertRaises(R2.Unmodelled):
            self.run_code(b"\xED\xB0")                            # LDIR is not whitelisted

    def test_step_limit_is_an_error(self):
        with self.assertRaises(R2.Unmodelled):
            self.run_code(jp(CODE))


class ReadAndPointers(unittest.TestCase):
    def test_read_cpu_resolves_each_window_under_its_mapper_state(self):
        rom = bytearray(0x10000)
        rom[0x10] = 1
        rom[0x4000 + 0x10] = 2
        rom[0x8000 + 0x10] = 3
        rom = bytes(rom)
        self.assertEqual(R3.read_cpu(rom, 0x0010, 1, 2), 1)
        self.assertEqual(R3.read_cpu(rom, 0x4010, 1, 2), 2)
        self.assertEqual(R3.read_cpu(rom, 0x8010, 1, 2), 3)

    def test_unknown_bank_and_ram_are_unresolved_not_guessed(self):
        rom = bytes(0x10000)
        with self.assertRaises(R3.Unresolved):
            R3.read_cpu(rom, 0x4000, None, 2)
        with self.assertRaises(R3.Unresolved):
            R3.read_cpu(rom, 0x8000, 1, None)
        with self.assertRaises(R3.Unresolved):
            R3.read_cpu(rom, 0xC000, 1, 2)

    def test_list_parse_stops_at_the_terminator(self):
        rom = image({0x8000: bytes([0x10, 1, 0, 2, 0, 0, 0, 0, 0, 0x31, 3, 0, 4, 0, 0, 0, 0, 0, 0xFF])}, 0x10000)
        lst = R3.parse_list(rom, 0x8000, 1, 2)
        self.assertTrue(lst["terminated"])
        self.assertEqual([e["type"] for e in lst["entries"]], [0x10, 0x31])
        self.assertEqual((lst["entries"][1]["x"], lst["entries"][1]["y"]), (3, 4))

    def test_list_pointing_into_ram_is_unresolved(self):
        lst = R3.parse_list(bytes(0x10000), 0xD003, 1, 2)
        self.assertFalse(lst["terminated"])
        self.assertIn("RAM", lst["error"])

    def test_list_without_terminator_stops_at_the_entry_limit(self):
        rom = bytes(0x10000)                                       # all zero bytes: type 0 entries forever
        lst = R3.parse_list(rom, 0x1000, 1, 2, limit=50)
        self.assertFalse(lst["terminated"])
        self.assertEqual(len(lst["entries"]), 50)

    def test_pointer_classes(self):
        verified = {0x2AF6}
        self.assertEqual(R3.classify_pointer(0x2AF6, verified, 5), "verified record")
        self.assertEqual(R3.classify_pointer(0x2260, verified, 5), "bank 0 (fixed)")
        self.assertEqual(R3.classify_pointer(0x5028, verified, 5), "slot 1 (bank 1 by premise)")
        self.assertEqual(R3.classify_pointer(0x8000, verified, 0x1B), "slot 2 (bank $1B)")
        self.assertEqual(R3.classify_pointer(0x8000, verified, None), "slot 2 (bank unresolved)")
        self.assertEqual(R3.classify_pointer(0xD003, verified, 5), "RAM")

    def test_destination_classes(self):
        rom = bytearray(0x10000)
        rom[0x0401] = 0xC3
        rom[0x0410] = 0x00
        rom = bytes(rom)
        sup = {0x8052}
        self.assertEqual(R3.classify_destination(rom, 0x8052, sup), "supported handler")
        self.assertEqual(R3.classify_destination(rom, 0x0401, sup), "resident jump stub")
        self.assertEqual(R3.classify_destination(rom, 0x0410, sup), "resident stub area (not a stub start)")
        self.assertEqual(R3.classify_destination(rom, 0x2000, sup), "resident code")
        self.assertEqual(R3.classify_destination(rom, 0xCD00, sup), "RAM")
        self.assertEqual(R3.classify_destination(rom, 0x9000, sup), "bank $1D code/data outside the handler list")


# --- the main-loop dispatch: priority, masking, survival of a raised flag -----------------------------------------------
class DispatchLogic(unittest.TestCase):
    def setUp(self):
        self.rom = synthetic_dispatcher()

    def test_callback_that_raises_bit_4_in_stage_mode_is_dispatched(self):
        rom = image({CODE: ld_hl(D293) + SET4_HL + RET})
        m = R3.Interp3(rom, ram={D293: 0x00}, slot1=1, slot2=None)
        m.run(CODE)
        self.assertEqual(m.ram[D293], 0x10)
        self.assertEqual(syn_dispatch(self.rom, 0x80, m.ram[D293]), S_ZONE)

    def test_the_same_flag_in_normal_mode_takes_the_normal_zone_route(self):
        self.assertEqual(syn_dispatch(self.rom, 0x00, 0x10), S_ZONE_N)

    def test_bit_5_outranks_bit_4_in_stage_mode(self):
        self.assertEqual(syn_dispatch(self.rom, 0x80, 0x30), S_ACT)

    def test_stage_mode_flags_preempt_the_state_flags(self):
        self.assertEqual(syn_dispatch(self.rom, 0xC0, 0x10), S_SUCCESS)         # D294 bit 6

    def test_ignored_bits_reach_the_frame_update(self):
        for bit in (7, 6, 3, 2, 1, 0):
            self.assertEqual(syn_dispatch(self.rom, 0x80, 1 << bit), S_STAGE, bit)

    def test_flag_survival_reports_the_handler(self):
        table = {0x80: [syn_dispatch(self.rom, 0x80, v) for v in range(256)]}
        ok, where = R3.flag_survives(table, 0x80, 0x10)
        self.assertTrue(ok)
        self.assertEqual(where, R3.hx(S_ZONE))

    def test_a_flag_cleared_before_the_dispatcher_looks_does_not_survive(self):
        table = {0x80: [syn_dispatch(self.rom, 0x80, v) for v in range(256)]}
        ok, why = R3.flag_survives(table, 0x80, 0x10, intervening_clears=(0x10,))
        self.assertFalse(ok)
        self.assertIn("cleared", why)

    def test_a_flag_the_stage_dispatcher_ignores_does_not_survive_to_a_handler(self):
        table = {0x80: [syn_dispatch(self.rom, 0x80, v) for v in range(256)]}
        self.assertEqual(table[0x80][0x01], S_STAGE)            # the synthetic stage frame; the real one is $1786 (tested below)
        ok, _ = R3.flag_survives({0x80: [0x1786] * 256}, 0x80, 0x01)
        self.assertFalse(ok)

    def test_mutated_branch_changes_the_derived_target(self):
        rom = bytearray(self.rom)
        # the stage-mode bit-4 test is the second JP c in the stage block: turn it into JP nc
        i = bytes(rom).index(bytes([0xDA]) + w(S_ZONE))
        rom[i] = 0xD2
        self.assertNotEqual(syn_dispatch(bytes(rom), 0x80, 0x10), S_ZONE)


class RouteLogic(unittest.TestCase):
    def test_trigger_type_in_the_closure_is_present_not_excluded(self):
        st, why = R3.route_status([0x50], [1, 2, 0x50], [], [])
        self.assertEqual(st, "present")
        self.assertIn("$50", why)

    def test_callback_that_exists_but_is_not_in_the_closure_is_excluded(self):
        st, _ = R3.route_status([0x61], [1, 2, 0x10], [], [])
        self.assertEqual(st, "excluded")

    def test_unknown_predecessor_prevents_an_exclusion_claim(self):
        st, why = R3.route_status([0x61], [1, 2, 0x10], [], ["$314F4"])
        self.assertEqual(st, "excluded_so_far")
        self.assertIn("$314F4", why)
        st, _ = R3.route_status([0x61], [1, 2], [{"src": 1, "file_offset": 5}], [])
        self.assertEqual(st, "excluded_so_far")

    def test_verdict_needs_every_route_excluded_for_proven_excluded(self):
        e = {"status": "excluded"}
        self.assertEqual(R3.u1_verdict([e, e]), "PROVEN EXCLUDED")
        self.assertEqual(R3.u1_verdict([e, {"status": "excluded_so_far"}]), "PARTIAL")
        self.assertEqual(R3.u1_verdict([e, {"status": "present"}]), "PARTIAL")
        self.assertEqual(R3.u1_verdict([{"status": "open"}]), "UNPROVEN")
        self.assertEqual(R3.u1_verdict([]), "UNPROVEN")

    def test_reachable_needs_a_grounded_route(self):
        self.assertEqual(R3.u1_verdict([{"status": "reachable", "grounded": False}, {"status": "excluded"}]), "PARTIAL")
        self.assertEqual(R3.u1_verdict([{"status": "reachable", "grounded": True}]), "PROVEN REACHABLE")

    def test_a_conditional_emerald_mask_is_not_grounded_without_proof(self):
        self.assertEqual(R3.route_grounding(["U2", "U6"]), ("conditional", ["U2", "U6"]))
        self.assertEqual(R3.route_grounding(["U2", "U6"], discharged=["U6"]), ("conditional", ["U2"]))
        self.assertEqual(R3.route_grounding(["U2"], discharged=["U2"]), ("grounded", []))
        self.assertEqual(R3.route_grounding([]), ("grounded", []))

    def test_cycles_terminate_without_a_bound(self):
        g = {"edges": [{"src": 1, "dst": 2}, {"src": 2, "dst": 3}, {"src": 3, "dst": 1}, {"src": 3, "dst": 3}]}
        self.assertEqual(R3.closure_from(g, [1]), [1, 2, 3])
        self.assertEqual(R3.closure_from(g, [3]), [1, 2, 3])

    def test_extra_edges_extend_the_closure(self):
        g = {"edges": [{"src": 1, "dst": 2}]}
        self.assertEqual(R3.closure_from(g, [1], extra=[{"src": 2, "dst": 9}]), [1, 2, 9])

    def test_transient_pairs_between_the_two_stores(self):
        self.assertEqual(R3.transient_pairs((8, 5), [("act", 0), ("zone", 9)]),
                         [("initial", (8, 5)), ("after_store_1", (8, 0)), ("final", (9, 0))])
        self.assertEqual(R3.transient_pairs((8, 5), [("zone", 9), ("act", 0)]),
                         [("initial", (8, 5)), ("after_store_1", (9, 5)), ("final", (9, 0))])


# --- creation sites ---------------------------------------------------------------------------------------------------
class CreationSites(unittest.TestCase):
    def sites(self, code):
        rom = image({CODE: code})
        reached, _notes = F.descend(rom, [CODE], 0, 0x2000)
        return R3.type_creation_sites(rom, reached), reached

    def test_pool_allocator_takes_the_type_from_c(self):
        rows, _ = self.sites(b"\x0E\x07" + b"\x26\x00" + call(0x5E9C) + RET)         # LD C,7 / LD H,0 / CALL $5E9C
        self.assertEqual([(r["kind"], r["value"]) for r in rows], [("allocator $5E9C", 7)])

    def test_pool_allocator_b_form(self):
        rows, _ = self.sites(b"\x06\x0F\x0E\x40" + jp(0x5EB7))                        # LD B,15 / LD C,$40 / JP $5EB7
        self.assertEqual([(r["kind"], r["value"]) for r in rows], [("allocator $5EB7", 15)])

    def test_two_calls_with_one_load_keep_the_value(self):
        rows, _ = self.sites(b"\x0E\x07\x26\x00" + call(0x5E9C) + b"\x26\x01" + call(0x5E9C) + RET)
        self.assertEqual([r["value"] for r in rows], [7, 7])

    def test_an_intervening_call_to_unknown_code_makes_the_type_unresolved(self):
        rows, _ = self.sites(b"\x0E\x07" + call(0x0500) + call(0x5E9C) + RET)
        alloc = [r for r in rows if r["kind"].startswith("allocator")]
        self.assertEqual([r["value"] for r in alloc], [None])

    def test_a_forked_chain_makes_the_type_unresolved(self):
        # JR Z skips the LD C,7 on one path: two predecessors reach the call
        code = b"\x0E\x07" + b"\x28\x02" + b"\x0E\x09" + call(0x5E9C) + RET
        rows, _ = self.sites(code)
        alloc = [r for r in rows if r["kind"].startswith("allocator")]
        self.assertEqual([r["value"] for r in alloc], [None])

    def test_destroy_marker_and_conversion_are_told_apart(self):
        rows, _ = self.sites(b"\xDD\x36\x00\xFF" + b"\xDD\x36\x00\x0F" + RET)
        self.assertEqual([(r["kind"], r["value"]) for r in rows], [("destroy marker", 0xFF), ("conversion", 0x0F)])

    def test_a_register_store_whose_register_is_an_immediate_is_resolved(self):
        rows, _ = self.sites(ld_a(0xFF) + b"\xDD\x77\x00" + RET)                      # LD A,$FF / LD (IX),A
        self.assertEqual([(r["kind"], r["value"]) for r in rows], [("destroy marker", 0xFF)])

    def test_a_register_store_with_a_computed_register_stays_unresolved(self):
        rows, _ = self.sites(ld_a_mem(0xC000) + b"\x3C" + b"\xDD\x77\x00" + RET)      # LD A,($C000) / INC A / LD (IX),A
        self.assertEqual([(r["kind"], r["value"]) for r in rows], [("register store", None)])

    def test_unverified_iy_store_is_not_dismissed(self):
        rows, _ = self.sites(b"\xFD\x71\x00" + RET)                                    # LD (IY),C outside every allowlisted region
        self.assertEqual([(r["kind"], r["value"]) for r in rows], [("register store", None)])

    def test_graph_closure_through_a_conversion_chain(self):
        g = {"edges": [{"src": 5, "dst": 6, "kind": "conversion"}, {"src": 6, "dst": 0x61, "kind": "FF 04 child"}]}
        self.assertIn(0x61, R3.closure_from(g, [5]))
        self.assertNotIn(0x61, R3.closure_from(g, [7]))


class CallbackReach(unittest.TestCase):
    """reach_map follows the callbacks the way the scheduler pages them in: confined to the type's bank."""

    def setUp(self):
        code = ld_hl(D293) + SET4_HL + RET
        # bank 2 occupies file offsets $8000-$BFFF; its CPU address is $8000 + offset % $4000
        self.rom = image({0x8000: code, 0x8100: ld_a(1) + RET}, 0x10000)
        cb = [{"vector": 0x8000, "selector": None}]
        self.uni = OrderedDict([(5, {"bank": 2, "states": [{"callbacks": cb, "steps": {}, "notes": []}]}),
                                (6, {"bank": 2, "states": [{"callbacks": [{"vector": 0x8100, "selector": None}], "steps": {}, "notes": []}]})])

    def test_syntactic_reach_finds_the_callback_that_contains_the_site(self):
        site = 0x8000 + 3
        reach = R3.reach_map(self.rom, self.uni, [site])
        self.assertEqual([(x["type"], x["states"]) for x in reach[site]], [(5, [0])])

    def test_a_callback_elsewhere_in_the_bank_does_not_reach_it(self):
        reach = R3.reach_map(self.rom, self.uni, [0x8003])
        self.assertNotIn(6, [x["type"] for x in reach[0x8003]])

    def test_code_that_exists_is_not_scheduled_unless_a_creation_edge_reaches_its_type(self):
        trig = [5]
        graph = {"edges": [{"src": 7, "dst": 6, "kind": "FF 04 child"}]}
        closure = R3.closure_from(graph, [7, 1])
        self.assertEqual(R3.route_status(trig, closure, [], [])[0], "excluded")
        graph["edges"].append({"src": 6, "dst": 5, "kind": "FF 04 child"})
        self.assertEqual(R3.route_status(trig, R3.closure_from(graph, [7, 1]), [], [])[0], "present")


# --- computed-jump specifications --------------------------------------------------------------------------------------
class JumpSpecs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = canonical_rom()
        if cls.rom is None:
            raise unittest.SkipTest("canonical ROM not available")

    def test_specified_jumps_resolve(self):
        for site in R3.JUMP_SPECS:
            res = R3.jump_destinations(self.rom, site)
            self.assertTrue(res["destinations"], hex(site))

    def test_a_bytes_mismatch_is_refused(self):
        rom = bytearray(self.rom)
        rom[0x6962] ^= 0x01                   # inside the 'AND 0x1f' that bounds the $6972 index
        with self.assertRaises(ValueError):
            R3.jump_destinations(bytes(rom), 0x6972)

    def test_a_table_word_change_changes_the_destinations(self):
        before = R3.jump_destinations(self.rom, 0x311BB)["destinations"]
        rom = bytearray(self.rom)
        off = R3.slot2_off(12, 0x91BC)
        rom[off], rom[off + 1] = 0x34, 0x92
        after = R3.jump_destinations(bytes(rom), 0x311BB)["destinations"]
        self.assertNotEqual(before, after)

    def test_a_bound_wider_than_the_table_reports_non_code_words(self):
        res = R3.jump_destinations(self.rom, 0x77EC)
        self.assertEqual(res["invalid"], [0xDDC9])
        self.assertEqual(res["bound"], "AND 0x1f")

    def test_unspecified_site_is_not_guessed(self):
        self.assertIsNone(R3.jump_destinations(self.rom, 0x6C98))


# --- entry routes and verdicts ----------------------------------------------------------------------------------------
def synthetic_world():
    level_end = {a: (0x20 if a < 2 else 0x10) for a in range(256)}
    return SimpleNamespace(
        level_end=level_end, act_complete={a: ((a + 1) & 0xFF, 0x60) for a in range(256)},
        zone_complete={z: (z + 1, 0, 0x15E8 if z + 1 >= 6 else 0x15DE) for z in range(256)},
        guard={"armed_only_when_character_1_zone_lt_6_emeralds_not_full": True},
        ss_exit={z: (z, True, 0, 0x60) for z in range(16)},
        ss_zones={8: [0], 9: [1], 10: [3], 11: [7], 12: [15]})


class EntryRoutes(unittest.TestCase):
    def test_a_repeated_special_stage_increases_the_act(self):
        routes = R3.entry_routes(None, synthetic_world(), cap=12)
        self.assertEqual(routes[(8, 2)][0], 0)
        self.assertEqual(routes[(8, 5)][0], 3)              # three failed entries at acts 2, 3, 4 before the entry at act 5
        names = [n for n, _s in routes[(8, 5)][1]]
        self.assertEqual(names.count("special_stage_failed"), 3)

    def test_a_higher_stage_needs_the_earlier_stage_to_have_succeeded(self):
        routes = R3.entry_routes(None, synthetic_world(), cap=12)
        names = [n for n, _s in routes[(9, 3)][1]]
        self.assertIn("special_stage_succeeded", names)

    def test_success_is_a_modelled_choice_not_a_grounded_fact(self):
        routes = R3.entry_routes(None, synthetic_world(), cap=12)
        self.assertEqual(R3.route_grounding(["U2", "U6"]), ("conditional", ["U2", "U6"]))
        self.assertTrue(any(n == "special_stage_succeeded" for n, _s in routes[(12, 6)][1]))

    def test_the_search_stops_at_the_act_cap(self):
        routes = R3.entry_routes(None, synthetic_world(), cap=5)
        self.assertTrue(all(a <= 5 for (_z, a) in routes))

    def test_route_text_lists_the_events(self):
        txt = R3.route_text([("new_game", (0, 0, 0)), ("act_complete", (0, 1, 0))])
        self.assertEqual(txt, "new_game(0, 0, 0) -> act_complete(0, 1, 0)")


def static_row(**kw):
    row = {"class": "slot 2 (bank $1B)", "slot2_bank": 27, "slot_targets": [{"class": "supported handler"}] * 4, "error": None}
    row.update(kw)
    return row


def case_row(**kw):
    c = {"exit_frame": 300, "active_frame": 240, "ram_execution_samples": [], "saved_zone": 0, "final": {"zone": 0}, "loader_calls": [{}],
         "iff1_at_end": True, "pc_pages_last_200_frames": [0x10, 0x40]}
    c.update(kw)
    return c


class U3Verdicts(unittest.TestCase):
    def test_in_domain_rows_are_not_verdict_rows(self):
        self.assertEqual(R3.u3_row_verdict({"class": "verified record"}, None), "IN DOMAIN")

    def test_resolved_chain_and_two_returning_runs_prove_the_return(self):
        self.assertEqual(R3.u3_row_verdict(static_row(), case_row(), case_row()), "PROVEN RETURNABLE")

    def test_the_accelerated_run_alone_does_not_prove_it(self):
        self.assertEqual(R3.u3_row_verdict(static_row(), case_row(), None), "PARTIAL")
        self.assertEqual(R3.u3_row_verdict(static_row(), case_row(), case_row(exit_frame=None)), "PARTIAL")
        self.assertEqual(R3.u3_row_verdict(static_row(), case_row(), case_row(final={"zone": 9})), "PARTIAL")

    def test_without_a_controlled_run_a_resolved_record_is_partial(self):
        self.assertEqual(R3.u3_row_verdict(static_row(), None), "PARTIAL")

    def test_a_readable_record_whose_stage_cannot_be_proved_returnable_is_partial(self):
        self.assertEqual(R3.u3_row_verdict(static_row(), case_row(exit_frame=None), case_row()), "PARTIAL")
        self.assertEqual(R3.u3_row_verdict(static_row(), case_row(active_frame=None), case_row()), "PARTIAL")

    def test_ram_execution_forbids_the_proof(self):
        ram = case_row(ram_execution_samples=[[1288, 0xCD00, 29]])
        self.assertEqual(R3.u3_row_verdict(static_row(), ram, case_row()), "PARTIAL")
        self.assertEqual(R3.u3_row_verdict(static_row(), case_row(), ram), "PARTIAL")

    def test_an_unsupported_slot_handler_forbids_the_proof_even_if_the_runs_returned(self):
        tg = [{"class": "supported handler"}, {"class": "resident code"}, {"class": "supported handler"}, {"class": "supported handler"}]
        self.assertEqual(R3.u3_row_verdict(static_row(slot_targets=tg), case_row(), case_row()), "PARTIAL")

    def test_a_stub_destination_is_acceptable(self):
        tg = [{"class": "resident jump stub"}] + [{"class": "supported handler"}] * 3
        self.assertEqual(R3.u3_row_verdict(static_row(slot_targets=tg), case_row(), case_row()), "PROVEN RETURNABLE")

    def test_an_unresolved_slot_2_mapping_is_unproven(self):
        self.assertEqual(R3.u3_row_verdict(static_row(**{"slot2_bank": None, "class": "slot 2 (bank unresolved)"}), case_row(), case_row()), "UNPROVEN")

    def test_a_record_pointer_in_ram_is_unproven(self):
        self.assertEqual(R3.u3_row_verdict({"class": "RAM", "slot2_bank": 3}, case_row(), case_row()), "UNPROVEN")

    def test_an_error_during_resolution_is_unproven(self):
        self.assertEqual(R3.u3_row_verdict(static_row(error="read beyond the ROM"), case_row(), case_row()), "UNPROVEN")

    def test_a_stall_before_the_loader_is_partial_whatever_the_record_is(self):
        stall = case_row(active_frame=None, exit_frame=None, loader_calls=[], iff1_at_end=False, pc_pages_last_200_frames=[0x25], final={"zone": 12})
        self.assertEqual(R3.u3_row_verdict({"class": "RAM", "slot2_bank": None}, stall), "PARTIAL")
        self.assertEqual(R3.u3_row_verdict(static_row(), stall, stall), "PARTIAL")
        # the same stall after the loader ran says nothing about the record being unreachable: unresolved pointers stay unproven
        late = dict(stall, loader_calls=[{}])
        self.assertEqual(R3.u3_row_verdict({"class": "RAM", "slot2_bank": None}, late), "UNPROVEN")

    def test_the_stage_not_restoring_the_zone_is_not_a_return(self):
        self.assertEqual(R3.u3_row_verdict(static_row(), case_row(final={"zone": 7}), case_row()), "PARTIAL")

    def test_outcome_words(self):
        self.assertEqual(R3.controlled_outcome(None), "not run")
        self.assertEqual(R3.controlled_outcome(case_row()), "returned")
        self.assertEqual(R3.controlled_outcome(case_row(active_frame=None, exit_frame=None)), "stage never active")
        self.assertEqual(R3.controlled_outcome(case_row(exit_frame=None)), "stage active, no exit")
        ram = case_row(active_frame=None, exit_frame=None, ram_execution_samples=[[1, 2, 3]], final={"zone": 7})
        self.assertEqual(R3.controlled_outcome(ram), "executed RAM, then reset to title")

    def test_stuck_stages_are_told_apart(self):
        base = case_row(active_frame=None, exit_frame=None, iff1_at_end=False, pc_pages_last_200_frames=[0x25], final={"zone": 12})
        self.assertEqual(R3.stuck_kind(base), "interrupts disabled, pc confined to $2500-$25FF")
        self.assertEqual(R3.stuck_kind(dict(base, final={"zone": 7})), "restarted at the title")
        self.assertEqual(R3.stuck_kind(dict(base, iff1_at_end=True)), "no progress within the bound")
        self.assertEqual(R3.stuck_kind(dict(base, pc_pages_last_200_frames=[0x10, 0x40, 0x7A])), "no progress within the bound")
        self.assertIsNone(R3.stuck_kind(dict(base, ram_execution_samples=[[1, 2, 3]])))
        self.assertIsNone(R3.stuck_kind(case_row(iff1_at_end=True, pc_pages_last_200_frames=[1])))

    def test_collapse_merges_adjacent_equal_acts_only(self):
        rows = [{"zone": 8, "act": a, "k": k} for a, k in enumerate("aabaa")]
        runs = R3.collapse(rows, lambda r: r["k"], ["k"])
        self.assertEqual([(r["acts"], r["k"]) for r in runs], [([0, 1], "a"), ([2, 2], "b"), ([3, 4], "a")])

    def test_thresholds_report_the_first_exit_and_the_return(self):
        rows = [{"zone": 8, "act": a, "ok": a < 3 or a >= 5} for a in range(8)]
        t = R3.thresholds(rows, lambda r: r["ok"])
        self.assertEqual(t["8"]["first_out_of_domain_act"], 3)
        self.assertEqual(t["8"]["in_domain_again_at"], [5, 6, 7])

    def test_ranges(self):
        self.assertEqual(R3._ranges([1, 2, 3, 7, 9, 10]), [[1, 3], [7, 7], [9, 10]])


# --- the canonical ROM ------------------------------------------------------------------------------------------------
_BUILT = {}


def built():
    if "b" not in _BUILT:
        rom = canonical_rom()
        doc, ctx = R3.build(rom)
        _BUILT["b"] = (doc, ctx, rom)
    return _BUILT["b"]


class CanonicalRom(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if canonical_rom() is None:
            raise unittest.SkipTest("canonical ROM not available")
        cls.doc, cls.ctx, cls.rom = built()

    # the three setters -------------------------------------------------------------------------------------------------
    def test_the_three_bit_4_setters_are_decoded_in_place(self):
        rows = {r["file_offset"]: r for r in self.doc["setter_sites"]}
        self.assertEqual(sorted(rows), [0x303ED, 0x7BB2A, 0x7BB6E])
        self.assertEqual((rows[0x303ED]["bank"], rows[0x303ED]["cpu"], rows[0x303ED]["asm"]), (12, 0x83ED, "SET 4,(HL)"))
        for off in (0x7BB2A, 0x7BB6E):
            self.assertEqual((rows[off]["bank"], rows[off]["asm"], rows[off]["feeder_asm"]), (0x1E, "LD (0xd293),A", "LD A,0x50"))
        self.assertEqual(rows[0x7BB2A]["cpu"], 0xBB2A)
        self.assertEqual(rows[0x7BB6E]["cpu"], 0xBB6E)
        self.assertTrue(all(r["raises_bit_4"] for r in rows.values()))
        self.assertEqual((rows[0x303ED]["d293_after_from_zero"], rows[0x7BB2A]["d293_after_from_zero"]), (0x10, 0x50))

    def test_the_setters_agree_with_the_r2_census(self):
        r2 = json.loads((ROOT / "data" / "decomp1d" / "r2-zone-act-invariants.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(r["file_offset"] for r in self.doc["setter_sites"]),
                         sorted(int(x[1:], 16) for x in r2["flow_facts"]["d293_bit4_setters"]))

    def test_the_level_end_flag_depends_only_on_the_act(self):
        flags = {a: R2.level_end_flag(self.rom)[a] for a in (0, 1, 2, 3, 255)}
        self.assertEqual((flags[0] & 0x30, flags[1] & 0x30), (0x20, 0x20))
        self.assertTrue(all(flags[a] & 0x30 == 0x10 for a in (2, 3, 255)))
        self.assertTrue(self.doc["provenance"]["player_state_20_callback"]["act_ge_2_always_sets_bit4"])

    def test_the_setters_belong_to_exactly_these_callbacks(self):
        reach = self.doc["provenance"]["sites_reached_by"]
        self.assertEqual([(x["type"], x["states"], x["vector"], x["bank"]) for x in reach["$303ED"]],
                         [(1, [32], "$83A6", 12), (2, [32], "$83A6", 12)])
        self.assertEqual([(x["type"], x["states"], x["vector"]) for x in reach["$7BB2A"]], [(0x61, [5], "$BB1A")])
        self.assertEqual([(x["type"], x["states"], x["vector"]) for x in reach["$7BB6E"]], [(0x61, [7], "$BB61")])

    def test_state_20_is_entered_only_through_the_level_clear_routine(self):
        psw = self.doc["provenance"]["player_state_writers"]
        sixes = [x for x in psw["absolute_d502_stores_in_image"] if x["value"] == 0x20]
        self.assertEqual([x["file_offset"] for x in sixes], [0x4894])
        self.assertEqual([x for x in psw["ix_plus_2_writers"] if x["value"] == 0x20], [])
        self.assertEqual(sorted(self.doc["provenance"]["script_state_changes_FF03_players"]), ["1", "2"])
        for vals in self.doc["provenance"]["script_state_changes_FF03_players"].values():
            self.assertNotIn(0x20, vals)

    def test_level_clear_callers_and_their_types(self):
        callers = [c["file_offset"] for c in self.doc["provenance"]["level_clear"]["callers"] if c["file_offset"] > 0x8000]
        self.assertEqual(sorted(callers), [0x32B9B, 0x781DF, 0x79D55])
        a = self.doc["provenance"]["level_clear"]["trigger_types_A"]
        self.assertEqual(a[:2], [0x19, 0x33])
        self.assertIn(0x50, a)
        self.assertEqual(self.doc["provenance"]["type_61"]["trigger_types_B"], [0x61])
        self.assertEqual(self.doc["provenance"]["level_clear"]["script_vectors_naming_the_routine"], [])

    def test_type_61_creates_its_children_and_is_created_by_type_60(self):
        kids = self.doc["creation"]["ff04_children"]
        self.assertIn(0x61, kids["96"])
        self.assertEqual(kids["97"], [10, 98])

    def test_every_script_parses_and_the_type_table_has_99_entries(self):
        u = self.doc["object_universe"]
        self.assertEqual((u["types"], u["script_parse_notes"]), (99, 0))

    # the natural universe ----------------------------------------------------------------------------------------------
    def test_special_stage_lists_place_only_four_object_types(self):
        placed = set()
        for key, v in self.doc["placement"]["natural_closure"].items():
            placed |= set(v["placed_types"])
        self.assertEqual(sorted(placed), [0x10, 0x26, 0x2F, 0x31])

    def test_no_trigger_type_is_in_the_natural_closure(self):
        for key, v in self.doc["placement"]["natural_closure"].items():
            self.assertEqual(v["trigger_types_in_closure"], [], key)

    def test_the_natural_closure_changes_when_a_list_is_changed(self):
        # mutation: point the zone 8 act 0 list at a list that places type $50 (the THZ boss list)
        uni, _ = R3.object_universe(self.rom)
        graph = R3.creation_graph(self.rom, uni)
        frame = R3.frame_creation_sites(self.rom)
        declared = R3.declared_edges(self.rom)
        base = R3.natural_closure(self.rom, uni, graph, frame, [0x10, 0x31], declared)
        mutated = R3.natural_closure(self.rom, uni, graph, frame, [0x10, 0x31, 0x50], declared)
        self.assertNotIn(0x50, base)
        self.assertIn(0x50, mutated)

    def test_out_of_domain_lists_name_trigger_types(self):
        p = self.doc["placement"]
        self.assertGreater(p["out_of_domain_rows_with_trigger_types"], 900)
        self.assertEqual(p["trigger_type_row_counts"]["61"], 24)

    def test_the_only_unresolved_creation_site_is_the_character_conversion(self):
        offs = {u["file_offset"] for u in self.doc["creation"]["unresolved_sites"]}
        self.assertEqual(offs, {R3.CHARACTER_CONVERSION})
        self.assertEqual(self.doc["creation"]["declared_edges"][0]["character_domain"], [0, 1, 2])

    def test_pool_allocations_resolve_to_immediates(self):
        edges = [e for e in self.doc["creation"]["non_placement_edges"] if e["kind"].startswith("allocator")]
        self.assertEqual(sorted({e["dst"] for e in edges}), [3, 5, 6, 7, 10, 15, 17, 18, 19, 25, 55, 58])
        # the level-clear object (type $19) is created by type $18 through the pool allocator; neither is in a special-stage list
        self.assertIn((24, 25), {(e["src"], e["dst"]) for e in edges})
        self.assertNotIn(25, {t for v in self.doc["placement"]["natural_closure"].values() for t in v["closure"]})

    def test_the_loop_allocation_is_resolved_by_its_own_instructions(self):
        edges = [e for e in self.doc["creation"]["non_placement_edges"] if e.get("file_offset") == 0x492F]
        self.assertEqual({e["dst"] for e in edges}, {6})
        rom = bytearray(self.rom)
        rom[0x492B] = 0x07                                       # LD C,7 instead of LD C,6: the loop check must now refuse the old value
        uni, _ = R3.object_universe(bytes(rom))
        reached, _n = F.descend(bytes(rom), [0x4929], 0, 0x8000)
        rows = [r for r in R3.type_creation_sites(bytes(rom), reached) if r["file_offset"] == 0x492F]
        self.assertEqual([r["value"] for r in rows], [None])

    def test_sprite_buffer_stores_are_allowlisted_by_their_bytes(self):
        reached, _ = F.descend(self.rom, [0x2280], 0, 0x8000)
        rows = R3.type_creation_sites(self.rom, reached)
        self.assertTrue(any(r["kind"] == "not a type store" for r in rows))
        rom = bytearray(self.rom)
        for o in range(0x22AC, 0x22B0):
            rom[o] = 0                                         # remove the 'INC IY' the allowlist depends on
        with self.assertRaises(ValueError):
            reached, _ = F.descend(bytes(rom), [0x2280], 0, 0x8000)
            R3.type_creation_sites(bytes(rom), reached)

    def test_open_computed_jumps_are_reported_for_the_closure(self):
        routes = self.doc["verdicts"]["U1"]["routes"]
        self.assertIn("$314F4", routes[0]["basis"])
        self.assertIn("$77EC", routes[0]["basis"])

    # the dispatcher ----------------------------------------------------------------------------------------------------
    def test_stage_mode_dispatch_honours_bit_4_with_priority_5_4_2_0(self):
        f = self.doc["dispatch"]["facts"]
        self.assertEqual(f["d293_bit4_in_stage_mode"], "$1543")
        self.assertEqual(f["d293_priority_in_stage_mode"], [5, 4, 2, 0])
        self.assertEqual(f["bit4_with_bit5_in_stage_mode"], "$14AE")
        self.assertEqual(self.doc["dispatch"]["stage_mode_ignored_d293_bits"], [1, 3, 6, 7])

    def test_nothing_removes_the_raised_bit_before_the_dispatcher_looks(self):
        s = self.doc["dispatch"]["facts"]["bit4_survives_to_the_dispatcher_in_stage_mode"]
        self.assertEqual((s["survives"], s["handler"]), (True, "$1543"))
        c = s["clearing_writers"]
        self.assertEqual(c["in_frame_update_closure"] + c["in_stage_object_closures"] + c["in_im1_closure"], [])
        self.assertEqual([w["file_offset"] for w in c["bit4_clearing_writers"] if w["op"] == "RES 4,(HL)"], [0x1383, 0x15E1, 0x15EB])
        self.assertEqual(self.doc["dispatch"]["interrupt_closure_writers"]["d293_writers_inside"], [])
        self.assertEqual([w["file_offset"] for w in self.doc["dispatch"]["interrupt_closure_writers"]["d294_writers_inside"]], [0x2849])

    def test_stage_flags_preempt_the_zone_complete_flag(self):
        f = self.doc["dispatch"]["facts"]
        self.assertEqual(f["d294_preempts_d293"], {"bit6": "$183F", "bit5": "$1815", "bit3": "$17B0"})
        self.assertEqual((f["bit4_with_d294_bit5"], f["bit4_with_d294_bit6"], f["bit4_with_d294_bit3"]), ("$1815", "$183F", "$17B0"))

    def test_dispatch_is_recomputed_from_the_bytes(self):
        rom = bytearray(self.rom)
        i = 0x1779                                              # JP c,$1543 in the stage-mode chain
        self.assertEqual(bytes(rom[i:i + 3]), bytes([0xDA, 0x43, 0x15]))
        rom[i] = 0xD2                                           # JP nc
        self.assertNotEqual(R3.dispatch_target(bytes(rom), 0x80, 0x10), 0x1543)

    def test_zone_complete_in_a_stage_executes_the_skip_and_the_increment(self):
        for z, row in self.doc["dispatch"]["zone_complete_in_stage"].items():
            self.assertTrue(row["results_screen_skipped"])
            self.assertEqual((row["zone_after"], row["act_after"], row["branch"]), (int(z) + 1, 0, "$15E8"))
            self.assertEqual(row["d293_after_from_0x50"], 0xC0)
            self.assertFalse(row["d294_written"])
        self.assertEqual(self.doc["dispatch"]["zone_complete_in_stage"]["12"]["zone_after"], 13)

    def test_the_stage_return_restores_the_saved_zone_and_raises_bit_5(self):
        m, _ = R2.execute(self.rom, 0x1869, {R3.SAVED_ZONE: 3, R3.ZONE: 10, R3.ACT: 77, R3.SPECIAL_FLAGS: 0x80, R3.STATE_FLAGS: 0x40},
                          stops=(0x1333,))
        self.assertEqual((m.ram[R3.ZONE], m.ram[R3.ACT], m.ram[R3.SPECIAL_FLAGS], m.ram[R3.STATE_FLAGS]), (3, 77, 0, 0x60))

    def test_a_surviving_bit_7_sends_the_return_to_the_end_path(self):
        self.assertEqual(self.doc["dispatch"]["return_after_zone_complete"]["d293_at_return"], 0xE0)
        self.assertEqual(self.doc["dispatch"]["return_after_zone_complete"]["normal_dispatch_target"], "$1365")

    def test_interrupts_are_enabled_between_the_zone_complete_stores(self):
        w_ = self.doc["interrupt_window"]
        self.assertTrue(w_["ei_at_15C8"])
        self.assertFalse(w_["di_in_window"])
        over = [p for p in w_["pairs"] if not p["inside_music_table"]]
        self.assertEqual([(p["zone"], p["act"], p["music_index"], p["byte_read"]) for p in over], [(13, 0, 39, 0x21)])
        mid = [p for p in w_["pairs"] if p["state"] == "after_store_1"]
        self.assertEqual({(p["zone"] - 0, p["act"]) for p in mid}, {(z, 0) for z in R3.SS_ZONES})

    # the loader --------------------------------------------------------------------------------------------------------
    def test_record_pointer_thresholds_are_rederived(self):
        t = self.doc["loader"]["thresholds"]["loader_record"]
        self.assertEqual({z: t[z]["first_out_of_domain_act"] for z in t}, {"8": 9, "9": 9, "10": 6, "11": 9, "12": 6})
        self.assertEqual(t["8"]["in_domain_again_at"][:3], [51, 128, 129])        # act 128 wraps to 0 (8-bit)

    def test_the_first_out_of_domain_record_is_the_start_of_bank_1b(self):
        rows = {(r[0], r[1]): r for r in self.doc["loader"]["rows"]}
        row = rows[(8, 9)]
        cols = self.doc["loader"]["columns"]
        d = dict(zip(cols, row))
        self.assertEqual((d["record_pointer"], d["slot2_bank"], d["slot_types"]), ("$8000", 27, "60 82 80 82"))
        self.assertEqual((d["first_pointer"], d["second_read_at"], d["record_physical"]), ("$2AE4", "$2AF6", "$6C000"))
        self.assertEqual(d["slot_target_classes"], "jsss")

    def test_the_record_is_read_from_the_bank_the_header_names_not_from_a_guessed_bank(self):
        for z in (8, 9, 10, 11, 12):
            hdr, d162, _d163, err = R3.header_chain(self.rom, z, 0)
            self.assertIsNone(err)
            self.assertEqual(d162, 0x1B)
        # the bytes the loader consumes come from that bank
        row = R3.loader_record(self.rom, 8, 9, set(), set(R3.slot_dispatch_words(self.rom)))
        base = 0x1B * 0x4000
        self.assertEqual(row["slot_types"], [self.rom[base + 6], self.rom[base + 7], self.rom[base + 8], self.rom[base + 9]])
        self.assertEqual(row["record"]["D2E0"], self.rom[base] | self.rom[base + 1] << 8)

    def test_mapper_context_facts(self):
        c = self.doc["loader"]["context_facts"]
        self.assertEqual(c["mapper_helper_1C6F"], ["LD (0xd12b),A", "LD (0xffff),A"])
        calls = [(x["file_offset"], x.get("prev")) for x in c["mapper_writes_reachable_from_4DAD"] if "prev" in x]
        self.assertEqual(calls, [(0x4DB5, "LD A,(IX+5)"), (0x4E22, "LD A,(0xd162)")])
        self.assertEqual((c["d162_writer"], c["d162_source"]), ("LD (IX+4),A", "LD A,(IY)"))
        self.assertEqual(c["leaves_resident_range_from_4DAD"], [])

    def test_mapper_context_changes_when_the_slot_2_source_is_changed(self):
        rom = bytearray(self.rom)
        self.assertEqual(bytes(rom[0x4E1F:0x4E22]), bytes([0x3A, 0x62, 0xD1]))
        rom[0x4E20] = 0x63                                     # LD A,($D163) instead of ($D162)
        c = R3.loader_context_facts(bytes(rom))
        calls = [x.get("prev") for x in c["mapper_writes_reachable_from_4DAD"] if "prev" in x]
        self.assertNotIn("LD A,(0xd162)", calls)

    def test_a_pointer_into_slot_2_is_not_resolved_without_a_bank(self):
        verified = set(R2.loader_tables(self.rom)[1])
        m = R3.Interp3(self.rom, ram={R3.ZONE: 8, R3.ACT: 9}, slot1=1, slot2=None)
        with self.assertRaises(R2.Unmodelled):
            m.run(R3.LOADER)
        self.assertNotIn(0x8000, verified)

    def test_a_lookup_that_stays_inside_the_verified_set(self):
        verified = set(R2.loader_tables(self.rom)[1])
        for a in range(9):
            row = R3.loader_record(self.rom, 8, a, verified, set(R3.slot_dispatch_words(self.rom)))
            self.assertEqual(row["class"], "verified record", a)

    def test_a_lookup_that_selects_code_bytes_rather_than_record_data(self):
        rows = {(r[0], r[1]): dict(zip(self.doc["loader"]["columns"], r)) for r in self.doc["loader"]["rows"]}
        d = rows[(8, 11)]
        self.assertEqual((d["record_pointer"], d["class"]), ("$2260", "bank 0 (fixed)"))
        ptr = 0x2260
        # the 'record' is the instruction stream at that address: it decodes as code
        first = F.decode(self.rom, ptr)
        self.assertFalse(F.is_invalid(first))
        self.assertEqual(d["slot_types"], " ".join("%02X" % b for b in self.rom[ptr + 6:ptr + 10]))

    def test_a_threshold_changes_when_the_pointer_table_is_changed(self):
        sup = set(R3.slot_dispatch_words(self.rom))
        verified = set(R2.loader_tables(self.rom)[1])
        before = R3.loader_record(self.rom, 8, 9, verified, sup)
        self.assertNotEqual(before["class"], "verified record")
        rom = bytearray(self.rom)
        i = R2.ZONE_TABLE + 2 * 8
        self.assertEqual(rom[i] | rom[i + 1] << 8, 0x2AE4)
        rom[i], rom[i + 1] = 0xBA, 0x2A                         # zone 8 now uses zone 0's first-level pointer: act 9 lands in a verified record
        mutated = bytes(rom)
        after = R3.loader_record(mutated, 8, 9, set(R2.loader_tables(mutated)[1]), set(R3.slot_dispatch_words(mutated)))
        self.assertEqual(after["class"], "verified record")
        self.assertEqual(R3.thresholds([R3.loader_record(mutated, 8, a, verified, sup) | {"zone": 8, "act": a} for a in range(40)],
                                       lambda r: r["class"] == "verified record")["8"]["first_out_of_domain_act"], 30)

    def test_the_slot_types_are_executed_from_the_interrupt_handler(self):
        c = self.doc["loader"]["slot_dispatch_caller"]
        self.assertEqual(c["sequence"][-1], "CALL 0x8000")
        self.assertIn("LD A,0x1d", c["sequence"])
        rom = bytearray(self.rom)
        rom[0x5C2] = 0x1E                                       # LD A,$1E instead of $1D
        with self.assertRaises(ValueError):
            R3.slot_dispatch_caller(bytes(rom))

    def test_the_graphics_row_table_has_42_rows_and_its_threshold_matches_the_other_tables(self):
        g = self.doc["graphics_table"]
        self.assertEqual((g["address"], g["row_length"], g["rows"]), ("$7CED", 7, 42))
        t = self.doc["loader"]["thresholds"]["graphics_rows"]
        self.assertEqual({z: t[z]["first_out_of_domain_act"] for z in t}, {"8": 18, "9": 15, "10": 12, "11": 9, "12": 6})
        # first row past the table is not a copy of a row: its first bytes are the start of the data the table points at
        rows = R3.graphics_table_rows(self.rom)
        self.assertEqual(rows[0][5] | rows[0][6] << 8, R3.GRAPHICS_ROW_TABLE + 7 * len(rows))

    def test_the_graphics_table_extent_changes_with_its_pointers(self):
        rom = bytearray(self.rom)
        rom[0x7CED + 5], rom[0x7CED + 6] = 0x00, 0x7E          # the first row now points at $7E00: rows start below it, so the table has 40 rows
        self.assertEqual(len(R3.graphics_table_rows(bytes(rom))), 40)
        self.assertEqual(R3.graphics_threshold(bytes(rom), 8), 16)

    def test_slot_type_destinations_are_executed(self):
        self.assertEqual(R3.slot_type_target(self.rom, 0x60), 0x0401)
        self.assertEqual(R3.slot_type_target(self.rom, 0x82), R3.slot_type_target(self.rom, 0x02))
        self.assertEqual(R3.slot_type_target(self.rom, 0xC0), 0xCD00)                  # a jump into RAM

    def test_type_5_beside_a_special_stage_zone_is_outside_the_nested_table(self):
        rows = self.doc["loader"]["type5_rows"]
        self.assertTrue(rows)
        self.assertTrue(all(not r["inside_table"] and r["zone"] >= 8 for r in rows))
        self.assertEqual(self.doc["loader"]["nested_table_end"], "$820A")

    def test_the_return_reload_leaves_the_verified_records_for_high_acts(self):
        rr = self.doc["loader"]["return_reload"]
        self.assertEqual(rr["0"]["entry_acts_whose_reload_is_out_of_domain"][0], [29, 70])
        self.assertEqual(rr["5"]["entry_acts_whose_reload_is_out_of_domain"][0], [14, 55])

    def test_zone_complete_pairs_select_verified_records(self):
        pairs = self.doc["interaction"]["Q2_zone_complete_selecting_an_unverified_record"]["new_pairs"]
        self.assertEqual([p[2] for p in pairs], ["verified record"] * 5)

    def test_entry_routes_name_the_assumptions(self):
        e = self.doc["entry_routes"]
        self.assertIn("U6", e["assumes"])
        self.assertIn("U2", e["assumes"])
        self.assertEqual(e["fewest_prior_entries"]["8/9"]["entries"], 7)
        self.assertEqual(e["fewest_prior_entries"]["12/6"]["entries"], 4)

    # the generated evidence --------------------------------------------------------------------------------------------
    def test_baseline_figures_are_unchanged(self):
        b = self.doc["baseline"]
        self.assertEqual((b["structurally_classified_bytes"], b["recovered_assembly_bytes"], b["recovered_regions"], b["unknown_bytes"]),
                         (156887, 13988, 113, 367401))
        self.assertFalse(b["changed_by_r3"])

    def test_propositions_keep_their_r2_status(self):
        p = self.doc["propositions"]
        self.assertEqual((p["A"]["r2_status"], p["B"]["r2_status"], p["C"]["r2_status"]), ("PARTIAL", "DISPROVEN", "PARTIAL"))
        self.assertEqual(p["R1"]["status"], "PARTIALLY CLOSED (unchanged)")

    def test_u1_is_partial_and_not_grounded(self):
        u1 = self.doc["verdicts"]["U1"]
        self.assertEqual(u1["verdict"], "PARTIAL")
        self.assertEqual(u1["verdict"], R3.u1_verdict(u1["routes"]))
        self.assertFalse(any(r["grounded"] for r in u1["routes"]))

    def test_the_doc_block_is_a_function_of_the_evidence(self):
        doc = self.doc
        a, b = R3.render_block(doc), R3.render_block(doc)
        self.assertEqual(a, b)
        self.assertTrue(a.startswith(R3.BEGIN) and a.endswith(R3.END_MARK))

    def test_dumps_is_ascii_and_newline_terminated(self):
        text = R3.dumps(self.doc)
        self.assertTrue(text.endswith("\n"))
        text.encode("ascii")


class CommittedEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if canonical_rom() is None:
            raise unittest.SkipTest("canonical ROM not available")
        if not EVIDENCE.is_file():
            raise unittest.SkipTest("evidence not generated yet")
        cls.doc, cls.ctx, cls.rom = built()
        cls.committed = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_the_static_evidence_matches_a_fresh_run(self):
        self.assertEqual(R3.static_view(self.doc), R3.static_view(self.committed))

    def test_the_u3_verdicts_are_recomputed_from_the_committed_runs(self):
        cols = self.committed["loader"]["columns"]
        counts = {}
        for r in self.committed["loader"]["rows"]:
            d = dict(zip(cols, r))
            if d["verdict"] != "IN DOMAIN":
                counts[d["verdict"]] = counts.get(d["verdict"], 0) + 1
        self.assertEqual(counts, self.committed["verdicts"]["U3"]["counts"])

    def test_every_proven_returnable_row_has_two_controlled_returns_and_supported_targets(self):
        cols = self.committed["loader"]["columns"]
        n = 0
        for r in self.committed["loader"]["rows"]:
            d = dict(zip(cols, r))
            if d["verdict"] == "PROVEN RETURNABLE":
                n += 1
                self.assertEqual((d["outcome"], d["natural_outcome"]), ("returned", "returned"))
                self.assertTrue(set(d["slot_target_classes"]) <= set("sj"))
                self.assertIsNone(d["ram_pc"])
        self.assertGreater(n, 0)

    def test_the_committed_doc_block_matches_the_evidence(self):
        self.assertEqual(R3.doc_block(DOC), R3.render_block(self.committed))

    def test_no_row_is_proven_blocked_without_a_rom_supported_guard(self):
        self.assertNotIn("PROVEN BLOCKED", self.committed["verdicts"]["U3"]["counts"])

    def test_static_slot_2_derivation_agrees_with_the_observed_mapper(self):
        c = self.committed["controlled"]
        self.assertEqual(c["static_slot2_vs_observed"]["mismatch_count"], 0)
        self.assertEqual(c["static_slot_types_vs_observed"]["mismatch_count"], 0)

    def test_a_stall_with_interrupts_disabled_needs_a_graphics_row_outside_the_table(self):
        c = self.committed["controlled"]["graphics_row_vs_outcome"]
        self.assertNotIn("stalled with interrupts disabled", c["graphics row in table"])
        self.assertGreater(c["graphics row outside the table"]["stalled with interrupts disabled"], 1000)
        # a row outside the table does not always stall: the five rows with index 142 decompress to an end and the stage runs
        rows = [dict(zip(self.committed["loader"]["columns"], r)) for r in self.committed["loader"]["rows"]]
        outside_returned = [(r["zone"], r["act"]) for r in rows if ((3 * r["zone"] + r["act"]) & 0xFF) >= 42 and r["outcome"] == "returned"]
        self.assertEqual(outside_returned, [(8, 118), (9, 115), (10, 112), (11, 109), (12, 106)])

    def test_the_stage_loads_stall_exactly_where_the_graphics_table_ends(self):
        for z, v in self.committed["controlled"]["first_interrupts_disabled_stall_vs_graphics_threshold"].items():
            self.assertEqual(v["first_stalled_act"], v["graphics_table_threshold"], z)

    def test_a_natural_run_that_differs_from_the_accelerated_one_is_recorded_and_not_proven(self):
        c = self.committed["controlled"]["natural_vs_accelerated"]
        self.assertGreater(c["compared"], 0)
        cols = self.committed["loader"]["columns"]
        rows = {(r[0], r[1]): dict(zip(cols, r)) for r in self.committed["loader"]["rows"]}
        for zone, act, nat, acc in c["outcome_differences"]:
            self.assertEqual(rows[(zone, act)]["natural_outcome"], nat)
            self.assertEqual(rows[(zone, act)]["outcome"], acc)
            self.assertNotEqual(rows[(zone, act)]["verdict"], "PROVEN RETURNABLE")
        self.assertTrue(any(z == 9 and a == 9 for z, a, _n, _c in c["outcome_differences"]))

    def test_the_u1_injection_shows_the_stage_continuing_in_the_next_zone(self):
        for run in self.committed["controlled"]["u1_flag_injection"]:
            self.assertTrue(run["reached_zone_plus_one"], run["ss_zone"])
            self.assertEqual(run["d293_during_limbo"], [0xC0])
            self.assertEqual(run["d293_at_exit"], 0xE0)


# --- controlled execution ---------------------------------------------------------------------------------------------
@unittest.skipUnless(harness_available(), "the z80 core is not installed")
class ControlledExecution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = canonical_rom()
        if cls.rom is None:
            raise unittest.SkipTest("canonical ROM not available")

    def test_an_in_domain_stage_activates_and_returns_restoring_the_zone(self):
        c = R3.controlled_stage_case(self.rom, 8, 0)
        self.assertIsNotNone(c["active_frame"])
        self.assertIsNotNone(c["exit_frame"])
        self.assertEqual(c["final"]["zone"], 0)
        self.assertEqual(c["ram_execution_samples"], [])
        self.assertEqual(c["loader_calls"][0]["slot2_bank"], 0x1B)
        self.assertEqual(c["loader_results"][0]["slot_types"], [12, 0, 0, 0])

    def test_the_observed_slot_2_matches_the_static_derivation(self):
        c = R3.controlled_stage_case(self.rom, 8, 9)
        hdr, d162, _d163, err = R3.header_chain(self.rom, 8, 9)
        self.assertIsNone(err)
        self.assertEqual(c["loader_calls"][0]["slot2_bank"], d162 % 32)

    def test_an_out_of_domain_record_with_supported_targets_returns(self):
        c = R3.controlled_stage_case(self.rom, 8, 9)
        self.assertEqual(c["loader_results"][0]["slot_types"], [0x60, 0x82, 0x80, 0x82])
        self.assertIsNotNone(c["exit_frame"])
        self.assertEqual(c["ram_execution_samples"], [])
        self.assertEqual(c["final"]["zone"], 0)

    def test_a_slot_type_that_jumps_into_ram_executes_ram_and_the_stage_never_activates(self):
        c = R3.controlled_stage_case(self.rom, 8, 10)
        self.assertEqual(c["loader_results"][0]["slot_types"], [0, 0xC0, 0, 0x13])
        self.assertTrue(c["ram_execution_samples"])
        self.assertEqual(c["ram_execution_samples"][0][1], 0xCD00)
        self.assertIsNone(c["active_frame"])
        self.assertIsNone(c["exit_frame"])

    def test_injecting_the_zone_complete_flag_in_a_stage_continues_the_stage_in_the_next_zone(self):
        c = R3.controlled_stage_case(self.rom, 12, 0, injections=[(0, D293, 0x10)], post_return=40, max_frames=2400,
                                     watch=R3.U1_WATCH)
        s = R3._u1_summary(c)
        self.assertTrue(s["reached_zone_plus_one"])
        self.assertEqual(s["d293_during_limbo"], [0xC0])
        self.assertEqual(s["stage_flag_during_limbo"], [0xA0])                       # the accelerated timer's failure flag
        self.assertEqual(c["final"]["zone"], 0)
        self.assertEqual(c["exit_info"]["d293"], 0xE0)

    def test_the_state_20_callback_raises_bit_4_when_its_position_test_passes(self):
        inj = [(30, 0xD502, 0x20, "set"), (30, 0xD511, R3._player_x_low, "set"), (30, 0xD512, R3._player_x_high, "set")]
        c = R3.controlled_stage_case(self.rom, 8, 2, accelerate=False, injections=inj, exit_bound=300, watch=(D293, R3.ZONE))
        writes = c["watched_writes"][R3.hx(D293)]
        self.assertIn(0x50, [v for _f, v in writes])                      # the callback's store: bit 4 raised on top of bit 6
        self.assertIn(9, [v for _f, v in c["watched_writes"][R3.hx(R3.ZONE)]])        # the stage continues at zone + 1
        self.assertEqual(len(c["injected"]), 3)

    def test_state_20_alone_does_not_raise_the_flag(self):
        c = R3.controlled_stage_case(self.rom, 8, 2, accelerate=False, injections=[(30, 0xD502, 0x20, "set")], exit_bound=300, watch=(D293,))
        self.assertNotIn(0x50, [v for _f, v in c["watched_writes"][R3.hx(D293)]])

    def test_a_garbage_stage_load_can_stall_with_interrupts_disabled(self):
        c = R3.controlled_stage_case(self.rom, 12, 6)
        self.assertIsNone(c["active_frame"])
        self.assertEqual(R3.stuck_kind(c), "interrupts disabled, pc confined to $2500-$25FF")
        self.assertFalse(c["iff1_at_end"])
        self.assertEqual(c["bound_hit"], "entry")
        self.assertLess(c["last_iff1_frame"], 200)

    def test_an_exit_records_which_flag_ended_the_stage(self):
        c = R3.controlled_stage_case(self.rom, 8, 0)
        self.assertEqual(c["exit_info"]["d294_before"], 0xA0)                 # the timer's failure flag
        self.assertEqual(c["exit_info"]["d293"], 0x60)                        # bit 5: the act-complete path follows

    def test_an_injection_is_labelled_as_injected(self):
        c = R3.controlled_stage_case(self.rom, 8, 0, injections=[(0, D293, 0x10)], max_frames=900)
        self.assertEqual(len(c["injected"]), 1)
        self.assertEqual(c["injected"][0]["address"], D293)

    def test_the_sweep_runs_each_case_from_the_same_state(self):
        a = R3.controlled_sweep(self.rom, [(8, 0)], workers=1)[0]
        b = R3.controlled_sweep(self.rom, [(8, 0)], workers=1)[0]
        self.assertEqual(R3.case_summary(a), R3.case_summary(b))


if __name__ == "__main__":
    unittest.main()
