#!/usr/bin/env python3
"""DECOMP-1D tests: bank-aware proof of ``CALL $8000``-style transfers, the bank-$1C entry and ledger integration.

Synthetic tests use tiny images and never need the ROM. Tests that need the canonical ROM skip without
SONIC_CHAOS_ROM or ../source/Sonic Chaos (Europe).sms; the rest read only committed metadata.
"""
import copy
import hashlib
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import decomp1a_review as RV  # noqa: E402
import decomp1b_callers as B1  # noqa: E402
import decomp1c_callbacks as C1  # noqa: E402
import decomp1d_banked_flow as D  # noqa: E402
import rom_flow as F  # noqa: E402
import rom_ledger as RL  # noqa: E402

EVIDENCE = ROOT / "data" / "decomp1d" / "banked-flow.json"
LEDGER = ROOT / "data" / "rom-ledger" / "ledger.json"
REGIONS = ROOT / "asm" / "recovered" / "regions.json"
ROM_PATH = Path(os.environ.get("SONIC_CHAOS_ROM", str(RL.DEFAULT_ROM)))

SETTER = bytes([0x32, 0x2B, 0xD1, 0x32, 0xFF, 0xFF, 0xC9])          # LD ($D12B),A / LD ($FFFF),A / RET
OK_INTERRUPTS = {"supported": True, "reasons": [], "irq": {"exit_restore_stores": [0x610]}}


def canonical_rom():
    if ROM_PATH.is_file():
        data = ROM_PATH.read_bytes()
        if len(data) == RL.ROM_SIZE and hashlib.sha256(data).hexdigest() == RL.ROM_SHA256:
            return data
    return None


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def same_text(a, b):
    return a.replace(b"\r\n", b"\n") == b.replace(b"\r\n", b"\n")


def image(blobs, size=0x10000):
    rom = bytearray(size)
    for at, blob in blobs.items():
        rom[at:at + len(blob)] = blob
    return bytes(rom)


def region(name, start, end, kind="code"):
    return {"name": name, "start": start, "end": end, "bank": start // 0x4000, "kind": kind,
            "bytes": end - start, "instructions": 0, "file": name + ".asm"}


def frame(bank, call=(0xCD, 0x00, 0x80)):
    """LD A,bank / CALL $1C6F / CALL $8000 / RET."""
    return bytes([0x3E, bank, 0xCD, 0x6F, 0x1C]) + bytes(call) + bytes([0xC9])


def prepared(blobs, size=0x10000, interrupts=OK_INTERRUPTS):
    rom = image({0x1C6F: SETTER, **blobs}, size)
    D.Facts.of(rom).interrupt = interrupts              # the interrupt model of a synthetic image is injected
    return rom


class SyntheticBankResolution(unittest.TestCase):
    ctx = D.Context([])

    def test_bank_comes_from_the_immediate_and_names_the_file_offset(self):
        rom = prepared({0x0200: frame(5)})
        rec = D.prove_banked_call(rom, [region("a", 0x200, 0x209)], 0x205, self.ctx)
        self.assertEqual((rec["status"], rec["reasons"]), ("supported", []))
        self.assertEqual(rec["bank_selection"]["value"], 5)
        self.assertEqual(rec["bank_selection"]["setter"]["shadow"], 0xD12B)
        self.assertEqual(rec["mapper_state_at_call"]["slot2_bank"], 5)
        self.assertEqual(rec["destination"], {"bank": 5, "cpu": 0x8000, "file_offset": 5 * 0x4000,
                                              "rule": "bank * $4000 + (cpu - $8000)"})
        self.assertTrue(rec["follow_safely"])
        self.assertEqual(rec["residual_assumptions"], ["R1", "R2", "R3", "R4"])

    def test_target_offset_inside_the_bank(self):
        rom = prepared({0x0200: frame(7, (0xCD, 0x34, 0x92))})
        rec = D.prove_banked_call(rom, [region("a", 0x200, 0x209)], 0x205, self.ctx)
        self.assertEqual(rec["destination"]["file_offset"], 7 * 0x4000 + 0x1234)

    def test_same_cpu_address_with_two_banks_gives_two_destinations(self):
        rom = prepared({0x0200: frame(5), 0x0300: frame(6)})
        regions = [region("a", 0x200, 0x209), region("b", 0x300, 0x309)]
        found = D.supported_entries(rom, regions, self.ctx)
        self.assertEqual(sorted(found), [5 * 0x4000, 6 * 0x4000])
        seeds = D.seed_support(rom, regions, self.ctx)
        self.assertIn(5 * 0x4000, seeds)
        self.assertIn(6 * 0x4000, seeds)

    def test_unproven_direct_register_write_is_not_an_entry(self):
        # LD A,6 / LD ($FFFF),A / CALL $8000 : the bank is visible, but no shadow-based proof and no setter
        rom = prepared({0x0200: frame(5), 0x0300: bytes([0x3E, 0x06, 0x32, 0xFF, 0xFF, 0xCD, 0x00, 0x80, 0xC9])})
        regions = [region("a", 0x200, 0x209), region("b", 0x300, 0x309)]
        rec = D.prove_banked_call(rom, regions, 0x305, self.ctx)
        self.assertEqual(rec["status"], "unresolved")
        self.assertEqual(rec["unproven_bank_hint"]["bank"], 6)
        self.assertEqual(sorted(D.seed_support(rom, regions, self.ctx)), [5 * 0x4000])

    def test_caller_outside_recovered_code_is_unresolved(self):
        rom = prepared({0x0200: frame(5)})
        rec = D.prove_banked_call(rom, [], 0x205, self.ctx)
        self.assertEqual(rec["reasons"], ["caller_not_in_byte_verified_recovered_code"])

    def test_target_must_be_slot_2_and_call(self):
        rom = prepared({0x0200: frame(5, (0xCD, 0x00, 0x40)), 0x0300: frame(5, (0xC3, 0x00, 0x80))})
        regions = [region("a", 0x200, 0x209), region("b", 0x300, 0x309)]
        self.assertIn("target_not_in_slot_2", D.prove_banked_call(rom, regions, 0x205, self.ctx)["reasons"])
        self.assertIn("not_a_direct_call", D.prove_banked_call(rom, regions, 0x305, self.ctx)["reasons"])


class SyntheticUnknownBankState(unittest.TestCase):
    ctx = D.Context([])

    def prove(self, code, caller, setter=SETTER):
        rom = image({0x1C6F: setter, 0x0200: code})
        D.Facts.of(rom).interrupt = OK_INTERRUPTS
        return D.prove_banked_call(rom, [region("a", 0x200, 0x200 + len(code))], caller, self.ctx)

    def test_call_without_any_setup(self):
        rec = self.prove(bytes([0xCD, 0x00, 0x80, 0xC9]), 0x200)
        self.assertEqual((rec["status"], rec["reasons"]), ("unresolved", ["no_bank_setup_before_call"]))

    def test_bank_not_an_immediate(self):
        rec = self.prove(bytes([0x7E, 0xCD, 0x6F, 0x1C, 0xCD, 0x00, 0x80, 0xC9]), 0x204)
        self.assertEqual(rec["status"], "unresolved")
        self.assertIn("bank_value_not_an_immediate", rec["reasons"])

    def test_something_between_the_setter_and_the_call(self):
        rec = self.prove(bytes([0x3E, 0x05, 0xCD, 0x6F, 0x1C, 0x00, 0xCD, 0x00, 0x80, 0xC9]), 0x206)
        self.assertEqual((rec["status"], rec["reasons"]), ("unresolved", ["no_bank_setup_before_call"]))

    def test_callee_that_is_not_a_mapper_setter(self):
        order_swapped = bytes([0x32, 0xFF, 0xFF, 0x32, 0x2B, 0xD1, 0xC9])      # register first: unsafe against an interrupt
        no_ret = bytes([0x32, 0x2B, 0xD1, 0x32, 0xFF, 0xFF, 0x00])
        shadow_in_rom = bytes([0x32, 0x2B, 0x41, 0x32, 0xFF, 0xFF, 0xC9])       # not a RAM shadow
        for setter in (order_swapped, no_ret, shadow_in_rom):
            rec = self.prove(frame(5), 0x205, setter)
            self.assertIn("callee_is_not_a_recognised_mapper_setter", rec["reasons"], setter.hex())
            self.assertEqual(rec["status"], "unresolved")

    def test_bank_outside_the_rom(self):
        rec = self.prove(frame(0x20), 0x205)
        self.assertIn("bank_value_outside_the_rom", rec["reasons"])
        self.assertEqual(rec["status"], "unresolved")

    def test_setter_shape_check(self):
        rom = image({0x1C6F: SETTER})
        self.assertEqual(D.mapper_setter(rom, 0x1C6F)["shadow"], 0xD12B)
        self.assertIsNone(D.mapper_setter(rom, 0x1C70))
        self.assertIsNone(D.mapper_setter(image({0x1C6F: bytes([0x32, 0x2B, 0xD1, 0x32, 0xFE, 0xFF, 0xC9])}), 0x1C6F))


class SyntheticConflictingPaths(unittest.TestCase):
    def prove(self, extra, claims=(), blobs=None):
        rom = prepared({0x0200: frame(5), **(blobs or {})})
        regions = [region("a", 0x200, 0x209)] + extra
        return D.prove_banked_call(rom, regions, 0x205, D.Context(list(claims)))

    def test_branch_into_the_setter_call_is_a_conflicting_path(self):
        # JP NZ,$0202 (the setter call) in recovered code: A is whatever the other path left in it
        rec = self.prove([region("b", 0x300, 0x303)], blobs={0x0300: bytes([0xC2, 0x02, 0x02])})
        self.assertEqual(rec["status"], "unresolved")
        self.assertIn("something_can_enter_the_sequence_midway", rec["reasons"])
        self.assertEqual(rec["sequence_integrity"]["entries_into_sequence"][0]["site"], 0x300)

    def test_relative_branch_into_the_banked_call(self):
        # JR $0205 : displacement from 0x302 is 0x205 - 0x302 = -0xFD, so use a nearby site instead
        rec = self.prove([region("b", 0x203 + 0x20, 0x203 + 0x22)],
                         blobs={0x0223: bytes([0x18, 0xE0])})                 # JR $0205
        self.assertIn("something_can_enter_the_sequence_midway", rec["reasons"])

    def test_branch_to_the_load_itself_is_allowed(self):
        rec = self.prove([region("b", 0x300, 0x303)], blobs={0x0300: bytes([0xC3, 0x00, 0x02])})
        self.assertEqual(rec["status"], "supported")

    def test_unexplained_address_literal_blocks(self):
        rec = self.prove([], blobs={0x0500: bytes([0x05, 0x02])})            # a $0205 word in unclassified bytes
        self.assertIn("something_can_enter_the_sequence_midway", rec["reasons"])
        self.assertEqual(rec["sequence_integrity"]["entries_into_sequence"][0]["class"], "unexplained")

    def test_literal_in_independent_data_is_inert(self):
        claim = {"start": 0x500, "end": 0x510, "primary": "DATA"}
        rec = self.prove([], [claim], blobs={0x0500: bytes([0x05, 0x02])})
        self.assertEqual(rec["status"], "supported")
        self.assertEqual(rec["sequence_integrity"]["inert_literals"][0]["ledger_class"], "DATA")

    def test_literal_in_a_code_claim_is_not_inert(self):
        claims = [{"start": 0x500, "end": 0x510, "primary": "DATA"}, {"start": 0x500, "end": 0x510, "primary": "CODE"}]
        rec = self.prove([], claims, blobs={0x0500: bytes([0x05, 0x02])})
        self.assertEqual(rec["status"], "unresolved")

    def test_literal_operand_of_decoded_code_blocks(self):
        # LD HL,$0205 in recovered code: a pointer to the middle of the sequence
        rec = self.prove([region("b", 0x300, 0x303)], blobs={0x0300: bytes([0x21, 0x05, 0x02])})
        classes = {b["class"] for b in rec["sequence_integrity"]["entries_into_sequence"]}
        self.assertEqual(classes, {"literal_operand"})

    def test_missing_structural_context_is_a_blocker_not_a_pass(self):
        rom = prepared({0x0200: frame(5)})
        rec = D.prove_banked_call(rom, [region("a", 0x200, 0x209)], 0x205, D.Context(None))
        self.assertEqual(rec["status"], "unresolved")


class SyntheticInterruptModel(unittest.TestCase):
    def test_image_without_mapper_aware_interrupt_handlers_is_unresolved(self):
        rom = image({0x1C6F: SETTER, 0x0200: frame(5)})          # no vectors: nothing proves interrupts leave slot 2 alone
        D.Facts.of(rom).interrupt = None                          # (the image is shared with tests that inject a model)
        rec = D.prove_banked_call(rom, [region("a", 0x200, 0x209)], 0x205, D.Context([]))
        self.assertEqual(rec["status"], "unresolved")
        self.assertIn("irq_exit_contract_not_proven", rec["reasons"])

    def test_handler_that_restores_from_the_shadow_is_accepted(self):
        irq = bytes([0xF3, 0xF5,                                   # DI / PUSH AF
                     0x3E, 0x03, 0x32, 0xFF, 0xFF,                # remap slot 2
                     0x3A, 0x2B, 0xD1, 0x32, 0xFF, 0xFF,          # LD A,(shadow) / LD ($FFFF),A
                     0xF1, 0xFB, 0xC9])                           # POP AF / EI / RET
        rom = image({0x1C6F: SETTER, 0x0038: irq, 0x0066: bytes([0xED, 0x45])})
        model = D.interrupt_model(rom)
        self.assertTrue(model["irq"]["exit_contract_holds"])
        self.assertTrue(model["nmi"]["leaves_mapper_untouched"])
        self.assertTrue(model["supported"], model["reasons"])

    def test_handler_that_leaves_slot_2_remapped_is_rejected(self):
        irq = bytes([0xF3, 0xF5, 0x3E, 0x03, 0x32, 0xFF, 0xFF, 0xF1, 0xFB, 0xC9])
        rom = image({0x1C6F: SETTER, 0x0038: irq, 0x0066: bytes([0xED, 0x45])})
        model = D.interrupt_model(rom)
        self.assertFalse(model["supported"])
        self.assertIn("irq_exit_contract_not_proven", model["reasons"])

    def test_handler_that_writes_the_shadow_is_rejected(self):
        irq = bytes([0xF3, 0xF5, 0x3E, 0x03, 0xCD, 0x6F, 0x1C,    # a call to the setter changes the shadow
                     0x3A, 0x2B, 0xD1, 0x32, 0xFF, 0xFF, 0xF1, 0xFB, 0xC9])
        rom = image({0x1C6F: SETTER, 0x0038: irq, 0x0066: bytes([0xED, 0x45])})
        model = D.interrupt_model(rom)
        self.assertFalse(model["supported"])
        self.assertIn("shadow_store_or_unmodelled_edge_in_irq_closure", model["reasons"])

    def test_nmi_that_touches_the_mapper_is_rejected(self):
        rom = image({0x1C6F: SETTER, 0x0038: bytes([0xF3, 0xFB, 0xC9]), 0x0066: bytes([0x32, 0xFF, 0xFF, 0xED, 0x45])})
        self.assertFalse(D.interrupt_model(rom)["nmi"]["leaves_mapper_untouched"])

    def test_shadow_store_in_banked_rom_is_rejected(self):
        rom = image({0x1C6F: SETTER, 0x0038: bytes([0xF3, 0xFB, 0xC9]), 0x0066: bytes([0xED, 0x45]),
                     0x9000: bytes([0x32, 0x2B, 0xD1])}, size=0x10000)
        model = D.interrupt_model(rom)
        self.assertEqual(model["shadow_store_patterns"]["outside_resident_engine"], [0x9000])
        self.assertIn("shadow_store_pattern_in_banked_rom", model["reasons"])


class SyntheticBankTables(unittest.TestCase):
    FETCH = bytes([0x7E, 0x23, 0x66, 0x6F, 0xE9])        # LD A,(HL) / INC HL / LD H,(HL) / LD L,A / JP (HL)
    PREFIX = bytes([0x21, 0x10, 0x80, 0x85, 0x6F, 0x3E, 0x00, 0x8C, 0x67])   # LD HL,$8010 / ADD A,L / LD L,A / LD A,0 / ADC A,H / LD H,A

    def rom(self, code=None, table=None):
        code = code if code is not None else self.PREFIX + self.FETCH
        table = table if table is not None else bytes([0x20, 0x80, 0x20, 0x80, 0x21, 0x80, 0x00, 0x00])
        return image({0x8000: code, 0x8010: table, 0x8020: bytes([0xC9, 0xC9])}, size=0xC000)

    def closure(self, rom):
        return F.descend(rom, [0x8000], 0x8000, 0xC000)[0]

    def test_table_found_and_extent_stops_at_the_first_invalid_word(self):
        rom = self.rom()
        tables = D.find_tables(rom, self.closure(rom))
        self.assertEqual([(t["table"], t["words"], t["load_site"], t["consumer"]) for t in tables],
                         [(0x8010, 3, 0x8000, 0x8000 + len(self.PREFIX) + 4)])
        self.assertEqual(D.table_word_target(rom, 0x8010, 2), 0x8021)

    def test_no_table_without_the_word_fetch(self):
        rom = self.rom(code=self.PREFIX + bytes([0xE9]))
        self.assertEqual(D.find_tables(rom, self.closure(rom)), [])

    def test_branch_into_the_sequence_disqualifies_the_table(self):
        code = bytes([0x20, 0x07]) + self.PREFIX + self.FETCH         # JR NZ,$8009 : lands inside the sequence
        code = bytes([0x20, 0x04]) + self.PREFIX + self.FETCH
        rom = self.rom(code=code)
        self.assertEqual(D.find_tables(rom, self.closure(rom)), [])

    def test_resident_table_loads_are_not_bank_tables(self):
        rom = image({0x1000: self.PREFIX + self.FETCH, 0x8010: bytes([0x20, 0x80])}, size=0xC000)
        self.assertEqual(D.find_tables(rom, F.descend(rom, [0x1000], 0x1000, 0x2000)[0]), [])

    def test_extent_stops_at_known_code(self):
        rom = self.rom(table=bytes([0x20, 0x80] * 8))
        self.assertEqual(D.table_extent(rom, 0x8010, set()), 8)
        self.assertEqual(D.table_extent(rom, 0x8010, {0x8014}), 2)


class SyntheticLedgerRules(unittest.TestCase):
    """Stale, contradictory or unsupported banked claims are refused when the ledger re-verifies them."""
    ctx = D.Context([])

    def setUp(self):
        self.rom = prepared({0x0200: frame(5)})
        self.regions = [region("a", 0x200, 0x209)]
        self.via = {"banked_transfer": {"caller": 0x205, "bank": 5, "cpu": 0x8000}}

    def test_good_claim_verifies(self):
        self.assertTrue(D.verify_seed(self.rom, self.regions, 5 * 0x4000, self.via, self.ctx))

    def test_stale_bank_is_rejected(self):
        via = {"banked_transfer": {"caller": 0x205, "bank": 6, "cpu": 0x8000}}
        with self.assertRaisesRegex(ValueError, "stale"):
            D.verify_seed(self.rom, self.regions, 5 * 0x4000, via, self.ctx)

    def test_wrong_offset_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "stale"):
            D.verify_seed(self.rom, self.regions, 6 * 0x4000, self.via, self.ctx)

    def test_unsupported_caller_is_rejected(self):
        via = {"banked_transfer": {"caller": 0x200, "bank": 5, "cpu": 0x8000}}
        with self.assertRaisesRegex(ValueError, "not a supported banked transfer"):
            D.verify_seed(self.rom, self.regions, 5 * 0x4000, via, self.ctx)

    def test_rom_change_invalidates_the_claim(self):
        changed = bytearray(self.rom)
        changed[0x201] = 0x06                                   # the immediate now selects bank 6
        D.Facts.of(bytes(changed)).interrupt = OK_INTERRUPTS
        with self.assertRaisesRegex(ValueError, "stale"):
            D.verify_seed(bytes(changed), self.regions, 5 * 0x4000, self.via, self.ctx)

    def test_unknown_seed_kind(self):
        with self.assertRaises(ValueError):
            D.verify_seed(self.rom, self.regions, 0, {"mystery": 1}, self.ctx)

    def test_unregistered_banked_region_is_rejected(self):
        rogue = [region("banked_rogue", 0x300, 0x303)]
        with self.assertRaisesRegex(ValueError, "not a registered DECOMP-1D banked region"):
            D.verify_registered_regions(self.rom, rogue, self.ctx)

    def test_registered_region_with_moved_bounds_is_rejected(self):
        moved = [region("banked_entry_70000", 0x70000, 0x700CA)]
        with self.assertRaises(ValueError):
            D.verify_registered_regions(self.rom, moved, self.ctx)

    def test_bank_table_claim_without_a_supported_entry_is_rejected(self):
        via = {"bank_table": {"table": 0x8010, "words": 3, "load_site": 0x8000, "consumer": 0x800D, "index": 0}}
        with self.assertRaisesRegex(ValueError, "no dispatch table"):
            D.verify_seed(self.rom, self.regions, 0x8020, via, self.ctx)


@unittest.skipUnless(canonical_rom() is not None, "canonical ROM not available (set SONIC_CHAOS_ROM)")
class CanonicalRomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = canonical_rom()
        cls.regions = load(REGIONS)
        cls.ledger = load(LEDGER)
        cls.evidence = load(EVIDENCE)
        cls.ctx = D.Context(cls.ledger["claims"])

    def test_both_established_callers_prove_bank_1c(self):
        for caller, interior in ((0x16E7, [0x16E4, 0x16E7]), (0x1737, [0x1734, 0x1737])):
            rec = D.prove_banked_call(self.rom, self.regions, caller, self.ctx)
            self.assertEqual((rec["status"], rec["reasons"]), ("supported", []), hex(caller))
            self.assertEqual(rec["region"], "gameplay_frame_update")
            self.assertEqual(rec["bank_selection"]["value"], 0x1C)
            self.assertEqual(rec["bank_selection"]["instruction"], caller - 5)
            self.assertEqual(rec["bank_selection"]["setter"]["entry"], 0x1C6F)
            self.assertEqual(rec["bank_selection"]["shadow"], 0xD12B)
            self.assertEqual(rec["destination"]["file_offset"], 0x70000)
            self.assertEqual(rec["sequence_integrity"]["interior_addresses"], interior)
            self.assertEqual(rec["sequence_integrity"]["entries_into_sequence"], [])

    def test_mapper_routine_is_exactly_shadow_then_register(self):
        self.assertEqual(self.rom[0x1C6F:0x1C76].hex(), "322bd1" "32ffff" "c9")
        self.assertEqual(D.mapper_setter(self.rom, 0x1C6F)["register"], 0xFFFF)

    def test_cpu_to_file_conversion(self):
        self.assertEqual(D.file_offset(0x1C, 0x8000), 0x70000)
        self.assertEqual(D.file_offset(0x1C, 0xBFFF), 0x73FFF)

    def test_interrupt_model_facts(self):
        m = D.interrupt_model(self.rom)
        self.assertTrue(m["supported"], m["reasons"])
        self.assertEqual({e["offset"] for e in m["irq"]["exits"]}, {0x0626, 0x0687})
        self.assertTrue(all(e["slot2_matches_shadow"] for e in m["irq"]["exits"]))
        self.assertEqual(m["irq"]["exit_restore_stores"], [0x0610])
        self.assertEqual(m["irq"]["resident_closure"]["shadow_store_sites"], [])
        self.assertEqual(m["irq"]["resident_closure"]["restart_edges"], [0x2492])
        self.assertEqual(m["shadow_store_patterns"]["outside_resident_engine"], [])
        self.assertTrue(m["nmi"]["leaves_mapper_untouched"])
        # the handler itself calls $8000 under bank $1D: the CPU address alone proves nothing
        self.assertIn({"call_site": 0x05C6, "cpu_target": 0x8000, "mapping": "slot2", "file_offset": None},
                      [dict(x) for x in m["irq"]["banked_callees"]])

    def test_handler_call_with_bank_1d_is_not_claimed(self):
        by = self.evidence["ambiguity"]["slot2_transfers_by_cpu_address"]["$8000"]
        rows = {r["caller"]: r for r in by}
        self.assertEqual(rows[0x05C6]["status"], "unresolved")
        self.assertEqual(rows[0x05C6]["unproven_bank_hint"], 0x1D)
        self.assertEqual(self.evidence["ambiguity"]["banks_seen_for_cpu_8000"], [0x1C, 0x1D])
        entries = D.seed_support(self.rom, self.regions, self.ctx)
        self.assertNotIn(0x74000, entries)

    def test_every_slot2_call_from_resident_code_is_accounted_for(self):
        facts = D.Facts.of(self.rom)
        sites = {s for s in D.slot2_calls(self.rom, self.regions, facts) if s < F.RESIDENT_END}
        self.assertEqual(sites, {t["caller"] for t in self.evidence["banked_transfers"]})
        supported = {t["caller"] for t in self.evidence["banked_transfers"] if t["status"] == "supported"}
        self.assertEqual(supported, {0x16E7, 0x1737})

    def test_eight_bytes_are_dispatch_targets_not_data(self):
        self.assertEqual(self.rom[0x7013E:0x70146].hex(), "c9" "eb235e2356eb" "e9")
        table = self.evidence["dispatch_tables"][0]
        self.assertEqual((table["table"], table["end"], table["words"]), (0x700CB, 0x700EB, 16))
        self.assertEqual((table["load_site"], table["consumer"]), (0x700BD, 0x700CA))
        targets = [w["file_offset"] for w in table["words_resolved"]]
        self.assertEqual(targets, [0x7013F] + [0x7013E] * 15)
        self.assertEqual(table["next_word_after_table"], 0xCDC5)          # the bytes after the table are code (PUSH BC / CALL)
        self.assertEqual(self.rom[0x700EB], 0xC5)
        reached, notes = F.descend(self.rom, [0x7013E, 0x7013F], 0x7013E, 0x70146)
        self.assertEqual(F.runs(reached), [(0x7013E, 0x70146)])
        self.assertEqual(notes, [("indirect", 0x70145)])

    def test_seeds_are_keyed_by_file_offset(self):
        seeds = D.seed_support(self.rom, self.regions, self.ctx)
        self.assertEqual(sorted(seeds), [0x70000, 0x7013E, 0x7013F])
        self.assertEqual(seeds[0x70000]["banked_transfer"], {"caller": 0x16E7, "bank": 0x1C, "cpu": 0x8000})
        for off, via in seeds.items():
            self.assertTrue(D.verify_seed(self.rom, self.regions, off, via, self.ctx))

    def test_registered_regions_prove_out(self):
        self.assertTrue(D.verify_registered_regions(self.rom, self.regions, self.ctx))
        for r in self.evidence["registered_regions"]:
            self.assertTrue(r["every_byte_reached"] and r["last_instruction_terminal"])
            self.assertTrue(r["internal_targets_are_instruction_starts"])
            self.assertFalse(r["touches_recovered_data"])
            self.assertTrue(all(u["kind"] == "indirect" for u in r["unresolved_exits"]))
        names = {r["name"]: (r["start"], r["end"]) for r in self.regions if r["name"].startswith("banked_")}
        self.assertEqual(names, {"banked_entry_70000": (0x70000, 0x700CB), "banked_dispatch_7013E": (0x7013E, 0x70146)})

    def test_exits_of_the_entry_routine_land_on_recovered_instructions(self):
        proof = next(r for r in self.evidence["registered_regions"] if r["name"] == "banked_entry_70000")
        recovered = set()
        for r in F.code_regions(self.regions):
            recovered.update(p for p, _, _ in F.region_instructions(self.rom, r))
        for e in proof["exits"]:
            if e["target"] is not None:
                self.assertIn(e["target"], recovered, hex(e["site"]))

    def test_committed_evidence_is_reproduced_exactly(self):
        doc = D.build(self.rom)
        self.assertEqual(json.loads(json.dumps(doc)), self.evidence)
        self.assertTrue(same_text((json.dumps(doc, indent=1) + "\n").encode(), EVIDENCE.read_bytes()))

    def test_residual_assumptions_are_recorded(self):
        self.assertEqual([a["id"] for a in self.evidence["residual_assumptions"]], ["R1", "R2", "R3", "R4"])
        self.assertIn("not an execution trace", self.evidence["evidence_tier"])

    def test_ledger_effect_and_zero_contradictions(self):
        eff = self.evidence["ledger_effect"]
        self.assertEqual(eff["before"]["unknown_bytes"] - eff["after"]["unknown_bytes"], 8)
        self.assertEqual(eff["after"]["recovered_bytes"] - eff["before"]["recovered_bytes"], 211)
        self.assertEqual(eff["after"]["independent_structural_bytes"], eff["before"]["independent_structural_bytes"])
        self.assertEqual(eff["contradictory_pairs"], 0)
        self.assertEqual(self.ledger["overlaps"]["stats"]["contradictory_pairs"], 0)
        self.assertEqual(self.ledger["totals"]["unknown_bytes"], eff["after"]["unknown_bytes"])
        self.assertEqual([c["name"] for c in eff["audit_ranges_changed"]], ["placement_scan"])
        seg = next(s for s in self.ledger["segments"] if s["start"] <= 0x7013E < s["end"])
        self.assertEqual((seg["primary"], seg["recovery"]), ("CODE", "recovered"))
        self.assertEqual(seg["regions"], ["banked_dispatch_7013E"])

    def test_code_data_distinctions_are_preserved(self):
        banked = {"banked_entry_70000", "banked_dispatch_7013E"}
        before = RL.build_ledger(self.rom, ROOT, drop_regions=banked)
        after = RL.build_ledger(self.rom, ROOT)

        def classes(ledger):
            out = bytearray(len(self.rom))
            for s in ledger["segments"]:
                out[s["start"]:s["end"]] = bytes([RL.CATEGORIES.index(s["primary"])]) * s["length"]
            return out

        b, a = classes(before), classes(after)
        diff = [o for o in range(len(self.rom)) if b[o] != a[o]]
        self.assertEqual(diff, list(range(0x7013E, 0x70146)))
        self.assertTrue(all(RL.CATEGORIES[b[o]] == "UNKNOWN" and RL.CATEGORIES[a[o]] == "CODE" for o in diff))
        # the 32-byte table stays inside the audit CODE claim: a contradictory DATA claim was deliberately not made
        self.assertEqual(RL.CATEGORIES[a[0x700CB]], "CODE")
        self.assertEqual(self.evidence["findings"][0]["id"], "F1")
        self.assertEqual(self.evidence["findings"][0]["table"], [0x700CB, 0x700EB])

    def test_default_review_matches_the_committed_file_and_gains_only_the_banked_cluster(self):
        with_banked = RV.build(self.rom, banked_seeds=True)
        without = RV.build(self.rom, banked_seeds=False)
        committed = load(ROOT / RL.REVIEWED)
        self.assertEqual(json.loads(json.dumps(with_banked)), committed)
        self.assertEqual(without["code_flow_reviews"], with_banked["code_flow_reviews"])
        extra = [u for u in without["unresolved"] if u not in with_banked["unresolved"]]
        self.assertEqual([u["bounds"] for u in extra], [[0x70000, 0x70146]])
        self.assertEqual(extra[0]["unknown_runs"], [[0x7013E, 0x70146]])
        self.assertEqual(len(without["unresolved"]), len(with_banked["unresolved"]) + 1)

    def test_banked_seeds_classify_the_tail_when_the_region_is_not_registered(self):
        """Evidence rules alone (no recovered region) give the same bytes as a reviewed flow claim."""
        doc = RV.build(self.rom, drop_regions={"banked_entry_70000", "banked_dispatch_7013E"}, banked_seeds=True)
        review = next(r for r in doc["code_flow_reviews"] if r["bounds"] == [0x70000, 0x70146])
        self.assertEqual([(c["start"], c["end"]) for c in review["claims"]], [(0x7013E, 0x70146)])
        kinds = sorted(next(iter(s["via"])) for s in review["seeds"])
        self.assertEqual(kinds, ["bank_table", "bank_table", "banked_transfer", "site"])

    def test_importer_rejects_a_tampered_banked_seed(self):
        import tempfile
        doc = RV.build(self.rom, drop_regions={"banked_entry_70000", "banked_dispatch_7013E"}, banked_seeds=True)
        base_regions = [r for r in self.regions if not r["name"].startswith("banked_")]
        raw = RL.build_ledger(self.rom, ROOT, reviewed=False, drop_regions={"banked_entry_70000", "banked_dispatch_7013E"})["claims"]

        def run(mutate):
            d = copy.deepcopy(doc)
            mutate(next(r for r in d["code_flow_reviews"] if r["bounds"] == [0x70000, 0x70146]))
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / "data" / "rom-ledger").mkdir(parents=True)
                (root / "data" / "rom-ledger" / "reviewed-ranges.json").write_text(json.dumps(d), encoding="utf-8")
                return RL.import_reviewed(self.rom, root, base_regions, raw)

        claims, summary = run(lambda r: None)
        self.assertIn((0x7013E, 0x70146), [(c["start"], c["end"]) for c in claims])

        def stale_bank(r):
            next(s for s in r["seeds"] if "banked_transfer" in s["via"])["via"]["banked_transfer"]["bank"] = 0x1D

        def wrong_caller(r):
            next(s for s in r["seeds"] if "banked_transfer" in s["via"])["via"]["banked_transfer"]["caller"] = 0x16E4

        def wrong_word(r):
            next(s for s in r["seeds"] if "bank_table" in s["via"])["via"]["bank_table"]["index"] = 0

        def wrong_extent(r):
            next(s for s in r["seeds"] if "bank_table" in s["via"])["via"]["bank_table"]["words"] = 15

        for mutate in (stale_bank, wrong_caller, wrong_word, wrong_extent):
            with self.assertRaises(ValueError, msg=mutate.__name__):
                run(mutate)

    def test_historical_generators_still_reproduce_their_committed_output(self):
        b1 = json.dumps(B1.build(self.rom), indent=1) + "\n"
        self.assertTrue(same_text(b1.encode(), (ROOT / "data" / "decomp1b" / "callers.json").read_bytes()))
        c1 = C1.build(self.rom)
        self.assertTrue(same_text((json.dumps(c1, indent=1) + "\n").encode(),
                                  (ROOT / "data" / "decomp1c" / "callbacks.json").read_bytes()))
        self.assertTrue(same_text(C1.derived_region_doc(c1).encode(),
                                  (ROOT / "data" / "decomp1c" / "derived-regions.json").read_bytes()))

    def test_vector_descent_agrees_with_decomp1b(self):
        self.assertEqual(D.resident_descent(self.rom), B1.vector_descent(self.rom)[0])

    def test_slot1_edges_finding_is_quantified(self):
        f2 = next(f for f in self.evidence["findings"] if f["id"] == "F2")
        self.assertEqual(f2["instructions_reached_only_through_these_edges"], 1227)
        self.assertEqual(f2["bytes_reached_only_through_these_edges"], 2732)


class DocumentationTests(unittest.TestCase):
    def test_doc_exists_and_names_the_key_facts(self):
        text = (ROOT / "docs" / "decomp-1d-banked-entry.md").read_text(encoding="utf-8")
        for needle in ("$1C6F", "$70000", "$16E7", "$1737", "$7013E", "R1", "not an execution trace"):
            self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main()
