#!/usr/bin/env python3
"""DECOMP-1D-R4A tests: residual object-dispatch closure ($314F4, $6972, $77EC, $6C98).

Synthetic tests build tiny images and never need the ROM. Tests that need the canonical ROM skip without SONIC_CHAOS_ROM or
../source/Sonic Chaos (Europe).sms. Every verdict is recomputed by the generator under test; the committed JSON is compared with a
fresh run, never trusted.
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

import decomp1d_r3_special_stage as R3  # noqa: E402
import decomp1d_r4a_object_dispatch as R4  # noqa: E402
import rom_ledger as RL  # noqa: E402

EVIDENCE = ROOT / "data" / "decomp1d" / "r4a-object-dispatch-closure.json"
DOC = ROOT / "docs" / "decomp-1d-r4a-object-dispatch-closure.md"
RECON = ROOT / "docs" / "decomp-1d-r4a-reconciliation.md"
SS = ROOT / "data" / "rom-cache" / "special-stages"
ROM_PATH = Path(os.environ.get("SONIC_CHAOS_ROM", str(RL.DEFAULT_ROM)))


def canonical_rom():
    if ROM_PATH.is_file():
        data = ROM_PATH.read_bytes()
        if len(data) == RL.ROM_SIZE and hashlib.sha256(data).hexdigest() == RL.ROM_SHA256:
            return data
    return None


def image(chunks, size=0x8000):
    b = bytearray(size)
    for off, data in chunks.items():
        b[off:off + len(data)] = data
    return bytes(b)


def w(v):
    return bytes([v & 0xFF, v >> 8])


# --- synthetic ------------------------------------------------------------------------------------------------------
class AbsoluteReferences(unittest.TestCase):
    def test_every_access_form_is_classified(self):
        rom = image({0x100: b"\x3A" + w(0xD364) + b"\x32" + w(0xD364) + b"\xED\x53" + w(0xD364) + b"\xED\x5B" + w(0xD364) + b"\x21" + w(0xD364)})
        rows = R4.absolute_references(rom, 0xD364)
        self.assertEqual([(r["file_offset"], r["kind"]) for r in rows],
                         [(0x100, "read"), (0x103, "write"), (0x106, "write"), (0x10A, "read"), (0x10E, "address constant")])

    def test_a_bare_address_with_no_instruction_before_it_is_not_a_reference(self):
        rom = image({0x100: b"\x00\x00" + w(0xD364) + b"\x00"})
        self.assertEqual(R4.absolute_references(rom, 0xD364), [])

    def test_writer_census_separates_reads_and_writes(self):
        rom = image({0x10: b"\x3A" + w(0xD353) + b"\x32" + w(0xD353)})
        refs = R4.absolute_references(rom, 0xD353)
        self.assertEqual([r["kind"] for r in refs], ["read", "write"])


class HitClassification(unittest.TestCase):
    def test_start_inside_and_outside(self):
        known = {0x10: 3, 0x20: 3}
        self.assertTrue(R4.classify_hit(known, 0x10).startswith("instruction start"))
        self.assertTrue(R4.classify_hit(known, 0x11).startswith("inside"))
        self.assertTrue(R4.classify_hit(known, 0x12).startswith("inside"))
        self.assertTrue(R4.classify_hit(known, 0x13).startswith("outside"))
        self.assertTrue(R4.classify_hit(known, 0x40).startswith("outside"))

    def test_transfers_into_finds_call_jp_and_conditional_forms(self):
        rom = image({0x10: b"\xCD" + w(0x6C90) + b"\xC3" + w(0x6C82) + b"\xCA" + w(0x6C98) + b"\xCD" + w(0x6C99)})
        rows = R4.transfers_into(rom, 0x6C82, 0x6C98, known={})
        self.assertEqual([r["file_offset"] for r in rows], [0x10, 0x13, 0x16])
        self.assertTrue(all(r["class"].startswith("outside") for r in rows))

    def test_entry_facts_flags_a_known_hit_at_an_unexpected_target(self):
        rom = image({0x10: b"\xCD" + w(0x6950), 0x20: b"\xCD" + w(0x690B)})
        known = {0x10: 3, 0x20: 3}
        f = R4.entry_facts(rom, known, 0x6900, 0x6972, (0x690B, 0x691A))
        self.assertFalse(f["known_code_hits_only_at_expected_entries"])
        self.assertEqual(f["targets_of_known_code_hits"], [0x690B, 0x6950])


class ClosureOf(unittest.TestCase):
    def test_follows_calls_and_a_listed_computed_jump_but_leaves_an_unlisted_one_open(self):
        rom = image({0x100: b"\xCD" + w(0x120) + b"\xC9",            # CALL $120 / RET
                     0x120: b"\xE9",                                  # JP (HL)  (site $120)
                     0x200: b"\xCD" + w(0x300) + b"\xC9", 0x300: b"\xC9"})
        reached, left, _ = R4.closure_of(rom, [0x100], {}, {"$0120": []})
        self.assertIn(0x120, reached)
        self.assertEqual(left, [])                                    # listed with no destinations: followed, nothing added
        reached2, left2, _ = R4.closure_of(rom, [0x100], {}, {})
        self.assertEqual(left2, ["$0120"])
        self.assertNotIn(0x300, reached2)
        reached3, left3, _ = R4.closure_of(rom, [0x100], {}, {"$0120": [(None, [0x200])]})
        self.assertIn(0x300, reached3)
        self.assertEqual(left3, [])

    def test_creation_scan_reads_an_allocator_type_and_ignores_a_destroy_marker(self):
        rom = image({0x100: b"\x0E\x3A" + b"\xCD" + w(0x5E9C) + b"\xDD\x36\x00\xFF" + b"\xC9"})     # LD C,$3A / CALL $5E9C / LD (IX),$FF / RET
        reached, _l, _s = R4.closure_of(rom, [0x100], {}, {})
        scan = R4.creation_scan(rom, reached)
        self.assertEqual([(s["kind"], s["value"]) for s in scan["creation_sites"]], [("allocator $5E9C", 0x3A)])
        self.assertEqual(scan["destroy_markers"], 1)

    def test_trigger_reach_sees_a_call_to_the_level_clear_routine(self):
        rom = image({0x100: b"\xCD" + w(0x4892) + b"\xC9"})
        reached, _l, _s = R4.closure_of(rom, [0x100], {}, {})
        self.assertEqual(R4.trigger_reach(rom, reached)["calls_to_level_clear"], ["$0100"])
        rom2 = image({0x100: b"\xC9"})
        self.assertEqual(R4.trigger_reach(rom2, {0x100: 1})["calls_to_level_clear"], [])


class DestinationChecks(unittest.TestCase):
    def test_a_word_outside_the_window_or_undecodable_is_flagged(self):
        rom = image({0x10: b"\xC9"})
        rows = R4.destination_checks(rom, None, [0x10, 0xDDC9])
        self.assertEqual([(r["cpu"], r["in_window"], r["decodes"]) for r in rows], [(0x10, True, True), (0xDDC9, False, False)])


class C98Semantics(unittest.TestCase):
    def table_rom(self):
        words = [0x6CB9] * 8 + [0x6CBA] * 2 + [0x6CCD] + [0x6CE5] * 5
        return image({0x6C99: b"".join(w(x) for x in words) + w(0xDDC9)}, 0x8000)

    def test_ids_below_the_base_return_and_the_special_id_branches_first(self):
        rom = self.table_rom()
        self.assertIsNone(R4.c98_destination(rom, 0x47))
        self.assertEqual(R4.c98_destination(rom, 0x83), 0x6CB9)
        self.assertEqual(R4.c98_destination(rom, 0x48), 0x6CB9)
        self.assertEqual(R4.c98_destination(rom, 0x52), 0x6CCD)
        self.assertEqual(R4.c98_destination(rom, 0x57), 0x6CE5)

    def test_id_58_reads_the_word_after_the_table_and_the_offset_wraps_at_c8(self):
        rom = self.table_rom()
        self.assertEqual(R4.c98_destination(rom, 0x58), 0xDDC9)
        self.assertEqual(R4.c98_destination(rom, 0xC8), R4.c98_destination(rom, 0x48))


# --- canonical ROM ---------------------------------------------------------------------------------------------------------
_BUILT = {}


def built():
    if "doc" not in _BUILT:
        rom = canonical_rom()
        _BUILT["rom"] = rom
        _BUILT["doc"] = R4.build(rom)
    return _BUILT["doc"], _BUILT["rom"]


class CanonicalRom(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if canonical_rom() is None:
            raise unittest.SkipTest("canonical ROM not available")
        cls.doc, cls.rom = built()

    def test_rom_and_base(self):
        self.assertEqual(self.doc["rom_sha256"], "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607")
        self.assertEqual(self.doc["base_commit"], "8af1f0366a3620d20b0a1341017d272968c5cfbb")

    def test_the_only_writers_of_the_feeder_variables(self):
        f = self.doc["feeders"]
        for name in ("D364", "D353", "D36B", "D2E0"):
            self.assertEqual(f["writer_census"][name]["writes"], f["expected"][name], name)
            self.assertEqual(f["writer_census"][name]["address_constants"], [], name)

    def test_d2e0_is_the_rom_table_in_every_verified_record(self):
        d = self.doc["feeders"]["d2e0"]
        self.assertTrue(d["all_equal"])
        self.assertEqual(set(d["verified_record_values"].values()), {0x8000})
        self.assertEqual(d["writer"]["asm"], "LD (0xd2e0),DE")
        self.assertEqual(d["table_physical"], 0x38000)

    def test_surface_31_is_in_no_block_header_in_either_plane(self):
        dom = R4.header_domain(self.rom)
        self.assertNotIn(31, dom["surfaces_present"])
        for r in dom["rows"]:
            for f in r["flags"]:
                self.assertNotEqual(f & 0x1F, 0x1F)
        self.assertEqual(dom["surfaces_absent"], [6, 8, 15, 17, 21, 31])

    def test_the_out_of_table_words_are_what_r3_found(self):
        self.assertEqual(R4._table(self.rom, 0x6973, 33)[31], 0xDDC9)
        self.assertEqual(R4._table(self.rom, 0x77ED, 33)[31], 0xDDC9)
        self.assertEqual(self.doc["jumps"]["$6C98"]["word_after_table"], 0xDDC9)
        for site in ("$6972", "$77EC"):
            self.assertFalse(self.doc["jumps"][site]["index_31_reached"])
            self.assertEqual(self.doc["jumps"][site]["words_past_the_table"][0], 0xDDC9)

    def test_c98_domain_is_exactly_its_table_plus_the_special_id(self):
        j = self.doc["jumps"]["$6C98"]
        self.assertEqual(j["table_entries"], 16)
        self.assertEqual(j["surface_16_block_ids"], list(range(0x48, 0x58)) + [0x83])
        self.assertTrue(j["all_ids_inside_table_or_special_case"])
        self.assertEqual(j["interpreter_mismatches"], [])
        self.assertEqual(j["destinations"], [0x6CB9, 0x6CBA, 0x6CCD, 0x6CE5])
        for b in range(0x48, 0x58):
            self.assertEqual(j["destination_by_block_id"][b], R4._table(self.rom, 0x6C99, 16)[b - 0x48])

    def test_c98_id_58_belongs_to_surface_23_not_16(self):
        dom = R4.header_domain(self.rom)
        self.assertIn(0x58, dom["ids_by_surface"][23])
        self.assertNotIn(0x58, dom["ids_by_surface"][16])

    def test_314f4_gate_ids_fill_the_sub_table_exactly(self):
        j = self.doc["jumps"]["$314F4"]
        self.assertEqual(j["gate_block_ids"], list(range(0x58, 0x74)))
        self.assertTrue(j["all_ids_inside_sub_table"])
        self.assertEqual(j["invalid_destinations"], [])
        self.assertEqual(j["transfers_between"], [])
        self.assertEqual(len(j["spec"]["destinations"]), 45)
        for d in j["destinations"]:
            self.assertTrue(0x8000 <= d < 0xC000)

    def test_314f4_ids_with_other_surface_bytes_never_pass_the_gate(self):
        gate = {b for r in R4.header_domain(self.rom)["rows"] for f in r["flags"] if f & 0x3F == 0x17 for b in (r["id"],)}
        self.assertEqual(sorted(gate), list(range(0x58, 0x74)))

    def test_no_lookup_or_writer_between_a_lookup_and_its_jump(self):
        f = self.doc["feeders"]
        for key in ("between_lookup_and_6972", "between_lookup_and_77EC"):
            self.assertEqual(f[key]["writer_instructions_reached"], [], key)
            self.assertEqual(f[key]["calls_a_lookup_entry"], [], key)
            self.assertEqual(f[key]["computed_jumps_not_followed"], [], key)
        self.assertEqual(f["interrupt_reach"]["writers_lookups_or_d2e0_store_inside"], [])

    def test_known_code_entries_into_the_dispatchers_are_the_expected_ones(self):
        f = self.doc["feeders"]
        self.assertTrue(f["entry_6972"]["known_code_hits_only_at_expected_entries"])
        self.assertTrue(f["entry_77EC"]["known_code_hits_only_at_expected_entries"])
        self.assertEqual(f["entry_6972"]["targets_of_known_code_hits"], [0x690B, 0x691A])
        self.assertEqual(self.doc["jumps"]["$6C98"]["entry_points"]["jump_table_6972_entry_16"], 0x6C82)

    def test_every_destination_decodes_in_its_window(self):
        for site, rows in self.doc["creation"]["destination_checks"].items():
            self.assertTrue(all(r["in_window"] and r["decodes"] for r in rows), site)

    def test_the_four_sites_add_no_type_beyond_r3_and_reach_no_trigger(self):
        c = self.doc["creation"]
        self.assertEqual(c["site_values_not_in_r3_closure"], [])
        for key in ("$6C98_and_$5E6F_destinations", "$314F4_destinations", "$6972_and_$77EC_destinations"):
            self.assertEqual(c[key]["trigger_reach"], {"setters_or_callers_reached": [], "calls_to_level_clear": []}, key)
            self.assertEqual(c[key]["computed_jumps_left_open"], [], key)
        self.assertEqual(c["$6C98_and_$5E6F_destinations"]["reach"]["creation_sites"], [])
        self.assertEqual(c["$314F4_destinations"]["reach"]["creation_sites"], [])
        for z, v in self.doc["natural_closure"].items():
            self.assertTrue(v["unchanged"], z)
            self.assertEqual(v["trigger_types_in_closure"], [], z)

    def test_77ec_handlers_create_nothing_and_stage_creation_is_limited_to_four_surfaces(self):
        m = self.doc["creation"]["surface_creation_map"]
        self.assertTrue(all(v["created_types"] == [] for v in m["$77EC"].values()))
        stage = self.doc["creation"]["stage_surface_creation"]
        self.assertEqual({s: v["created_types"] for s, v in stage.items() if v["created_types"]},
                         {"1": [0x3A], "12": [0x13], "13": [0x07], "22": [0x0F]})

    def test_stage_floor_handlers_equal_the_accepted_manifest(self):
        manifest = json.loads((SS / "implementation-manifest.json").read_text(encoding="utf-8"))
        for s, v in self.doc["creation"]["stage_surface_creation"].items():
            self.assertEqual(v["floor_handler"], manifest["surfaces"][s]["floor_handler"], s)
        self.assertNotIn("16", manifest["surfaces"])
        self.assertNotIn("23", manifest["surfaces"])

    def test_reconciliation_agrees_with_the_accepted_census(self):
        r = self.doc["reconciliation"]
        self.assertTrue(r["object_universe"]["all_stage_lists_equal"])
        self.assertEqual(r["object_universe"]["accepted_placed_types"], [0x10, 0x26, 0x2F, 0x31])
        a = r["act3"]["accepted_census"]
        self.assertEqual(a["act_index2_maximum_rings"]["zone3_act2"], 83)
        self.assertFalse(a["any_act_index2_reaches_100"])
        self.assertTrue(all(v < 100 for v in a["act_index2_maximum_rings"].values()))

    def test_verdicts_stay_conservative(self):
        v = self.doc["verdicts"]
        self.assertTrue(v["all_four_bounded"])
        self.assertEqual(v["object_creation_closure"]["status"], "PARTIAL")
        self.assertEqual(v["u1"]["r4a"], "PARTIAL")
        self.assertEqual(v["u1"]["route_A_status"], "excluded_so_far")
        self.assertEqual(v["u1"]["route_B_status"], "excluded_so_far")
        self.assertIn("$5E9A", v["u1"]["route_A_why"])
        self.assertIn("$6695", v["u1"]["route_A_why"])
        for site in ("$6972", "$77EC", "$6C98", "$314F4"):
            self.assertTrue(v[site]["verdict"].startswith("CLOSED (premise-conditional"))

    def test_the_other_resident_jumps_in_r3_evidence_are_recorded(self):
        a = self.doc["adjacent_resident_jumps"]
        self.assertEqual(a["not_named_in_r3_open_list"], ["$5E6F", "$5E9A", "$6695"])
        self.assertEqual(a["$5E6F"]["destinations"], [0x5E90, 0x5EF8, 0x626D])
        self.assertTrue(a["$5E9A"]["status"].startswith("OPEN"))
        self.assertTrue(a["$6695"]["status"].startswith("OPEN"))

    def test_the_stage_interface_names_no_competing_manifest(self):
        si = self.doc["stage_interface"]
        self.assertIn("implementation-manifest.json", si["source_of_truth"])
        self.assertFalse(si["residual_dispatchers_affecting_ordinary_implementation"])
        self.assertEqual(si["newly_established_object_creation_behaviour"], "none")

    def test_the_baseline_is_unchanged(self):
        b = self.doc["baseline"]
        self.assertEqual((b["structurally_classified_bytes"], b["recovered_assembly_bytes"], b["recovered_regions"], b["unknown_bytes"], b["contradictory_claims"]),
                         (156887, 13988, 113, 367401, 0))
        self.assertFalse(b["changed_by_r4a"])

    def test_a_changed_byte_fails_the_specification(self):
        rom = bytearray(self.rom)
        rom[0x6C85] = 0x84                                              # CP $83 -> CP $84
        with self.assertRaises(ValueError):
            R4.jump_6c98(bytes(rom), R4.header_domain(self.rom), {})
        rom2 = bytearray(self.rom)
        rom2[0x695E] = 0x00
        with self.assertRaises(ValueError):
            R4.jump_6972(bytes(rom2), R4.header_domain(self.rom))


class CommittedEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if canonical_rom() is None:
            raise unittest.SkipTest("canonical ROM not available")
        if not EVIDENCE.is_file():
            raise unittest.SkipTest("evidence not generated yet")
        cls.doc, cls.rom = built()
        cls.committed = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_the_evidence_matches_a_fresh_run_byte_for_byte(self):
        self.assertEqual(EVIDENCE.read_text(encoding="utf-8"), R4.dumps(self.doc))

    def test_the_generated_doc_block_matches(self):
        self.assertEqual(R4.doc_block(DOC), R4.render_block(self.committed))

    def test_the_narrative_numbers_match_the_evidence(self):
        text = DOC.read_text(encoding="utf-8")
        d = self.committed
        self.assertEqual(d["feeders"]["between_lookup_and_6972"]["instructions"], 212)
        self.assertEqual(d["feeders"]["between_lookup_and_77EC"]["instructions"], 139)
        self.assertEqual(d["feeders"]["interrupt_reach"]["closure_instructions"], 3584)
        self.assertEqual(len(d["jumps"]["$314F4"]["instructions_between_gate_and_d353_read"]), 11)
        self.assertEqual(len(d["creation"]["$6972_and_$77EC_destinations"]["reach"]["creation_sites"]), 9)
        for needle in ("212 instructions", "(139)", "3,584 instructions", "eleven straight instructions", "nine allocator calls", "45 distinct"):
            self.assertIn(needle, text)
        self.assertEqual(d["header_domain"]["surfaces_absent"], [6, 8, 15, 17, 21, 31])

    def test_the_reconciliation_document_states_the_three_levels(self):
        text = RECON.read_text(encoding="utf-8")
        for needle in ("Syntactically permitted", "Reachable under forced state", "Reachable through original gameplay", "MGHZ3 **83**", "not** rewritten"):
            self.assertIn(needle, text)

    def test_only_this_milestones_files_are_new_and_the_ledger_is_untouched(self):
        import subprocess
        out = subprocess.run(["git", "status", "--porcelain"], cwd=str(ROOT), capture_output=True, text=True).stdout.split("\n")
        changed = {line[3:] for line in out if line.strip()}
        allowed = {"tools/decomp1d_r4a_object_dispatch.py", "tests/test_decomp1d_r4a.py", "docs/decomp-1d-r4a-object-dispatch-closure.md",
                   "docs/decomp-1d-r4a-reconciliation.md", "data/decomp1d/r4a-object-dispatch-closure.json"}
        self.assertLessEqual(changed, allowed)


if __name__ == "__main__":
    unittest.main()
