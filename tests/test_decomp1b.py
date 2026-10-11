#!/usr/bin/env python3
"""DECOMP-1B tests: hardware-vector reachability, recovered engine callers, dependency map.

Tests that need the canonical ROM skip without SONIC_CHAOS_ROM or ../source/Sonic Chaos (Europe).sms;
the rest read only committed metadata or tiny synthetic images.
"""
import hashlib
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import decomp1b_callers as B  # noqa: E402
import rom_flow as F  # noqa: E402
import rom_ledger as RL  # noqa: E402

CALLERS = ROOT / "data" / "decomp1b" / "callers.json"
LEDGER = ROOT / "data" / "rom-ledger" / "ledger.json"
REGIONS = ROOT / "asm" / "recovered" / "regions.json"
ROM_PATH = Path(os.environ.get("SONIC_CHAOS_ROM", str(RL.DEFAULT_ROM)))
DECOMP1A_REVIEWED_BYTES = 794       # reviewed CODE bytes before DECOMP-1B (docs/decomp-1a-existing-evidence.md)


def canonical_rom():
    if ROM_PATH.is_file():
        data = ROM_PATH.read_bytes()
        if len(data) == RL.ROM_SIZE and hashlib.sha256(data).hexdigest() == RL.ROM_SHA256:
            return data
    return None


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def image(blobs):
    rom = bytearray(0x10000)
    for at, blob in blobs.items():
        rom[at:at + len(blob)] = blob
    return bytes(rom)


class VectorDescentTests(unittest.TestCase):
    def test_roots_are_closed_in_order_and_chains_use_transfers(self):
        rom = image({
            0x0000: bytes([0xC3, 0x00, 0x01]),                  # reset: JP 0100
            0x0100: bytes([0xCD, 0x10, 0x01, 0xC9]),            # CALL 0110 ; RET
            0x0110: bytes([0x3C, 0x00, 0xC9]),                  # INC A ; NOP ; RET
            0x0038: bytes([0xC3, 0x10, 0x01]),                  # IM 1: JP 0110 (already reached from reset)
            0x0066: bytes([0xED, 0x45]),                        # NMI: RETN
        })
        ins, parent, indirect, invalid = B.vector_descent(rom)
        self.assertEqual(sorted(ins), [0x0000, 0x0038, 0x0066, 0x0100, 0x0103, 0x0110, 0x0111, 0x0112])
        self.assertEqual((indirect, invalid), ([], []))
        self.assertEqual(B.chain(parent, 0x0110), [(0x0000, "vector"), (0x0100, "JP at $0000"), (0x0110, "CALL at $0100")])
        self.assertEqual(parent[0x0110], (0x0100, "CALL"))      # explained by reset, not by the later IM 1 jump

    def test_indirect_jumps_and_slot2_calls_are_not_followed(self):
        rom = image({
            0x0000: bytes([0xCD, 0x00, 0x90, 0xE9]),            # CALL 9000 (slot 2: ambiguous) ; JP (HL)
        })
        ins, _, indirect, _ = B.vector_descent(rom)
        self.assertIn(0x0003, ins)
        self.assertNotIn(0x9000, ins)
        self.assertEqual(indirect, [0x0003])

    def test_prove_region_flags_unreached_bytes(self):
        class Classes:
            @staticmethod
            def at(_):
                return "UNKNOWN"

        # JP 0105 ; NOP ; NOP ; RET : the two NOPs are decodable but never reached from the entry
        rom = image({0x0100: bytes([0xC3, 0x05, 0x01, 0x00, 0x00, 0xC9])})
        proof = B.prove_region(rom, [], Classes, "t", 0x100, 0x106, (0x100,))
        self.assertFalse(proof["every_byte_reached_from_entries"])
        self.assertEqual(proof["unreached_instruction_offsets"], [0x103, 0x104])
        rom = image({0x0100: bytes([0x3C, 0xC9])})
        proof = B.prove_region(rom, [], Classes, "t", 0x100, 0x102, (0x100,))
        self.assertTrue(proof["every_byte_reached_from_entries"])
        self.assertTrue(proof["final_instruction_is_terminal"])
        self.assertFalse(proof["fall_through_off_end"])
        proof = B.prove_region(image({0x0100: bytes([0x3C, 0x00])}), [], Classes, "t", 0x100, 0x102, (0x100,))
        self.assertTrue(proof["fall_through_off_end"])


class CommittedEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load(CALLERS)
        cls.regions = {r["name"]: r for r in load(REGIONS)}
        cls.ledger = load(LEDGER)

    def test_recovered_callers_are_proved_and_registered(self):
        self.assertEqual([r["name"] for r in self.doc["recovered_callers"]], [c[0] for c in B.RECOVERED])
        for r in self.doc["recovered_callers"]:
            name = r["name"]
            self.assertNotIn("error", r, name)
            self.assertTrue(r["registered"], name)
            reg = self.regions[name]
            self.assertEqual((reg["start"], reg["end"], reg["kind"], reg["bytes"]), (r["bounds"][0], r["bounds"][1], "code", r["bytes"]))
            self.assertEqual(reg["instructions"], r["instructions"], name)
            self.assertTrue(r["every_byte_reached_from_entries"], name)       # no embedded table or dead bytes
            self.assertEqual(r["unreached_instruction_offsets"], [], name)
            self.assertTrue(r["final_instruction_is_terminal"], name)
            self.assertFalse(r["fall_through_off_end"], name)
            self.assertEqual(r["touches_recovered_data"], [], name)
            self.assertEqual(r["table_loads_inside_region"], [], name)
            self.assertTrue(r["internal_targets_are_instruction_starts"], name)
            for e in r["entry_support"]:
                self.assertTrue(e["reached_from_hardware_vector"], (name, e["entry"]))
                self.assertEqual(e["transfer_chain_from_vector"][0]["via"], "vector")
                self.assertEqual(e["transfer_chain_from_vector"][-1]["to"], e["entry"])

    def test_recovered_regions_are_recovered_code_in_the_ledger(self):
        segs = self.ledger["segments"]
        for r in self.doc["recovered_callers"]:
            lo, hi = r["bounds"]
            covering = [s for s in segs if s["start"] < hi and lo < s["end"]]
            self.assertEqual(covering[0]["start"] <= lo and covering[-1]["end"] >= hi, True)
            for s in covering:
                self.assertEqual(s["primary"], "CODE")
                self.assertEqual(s["recovery"], "recovered")

    def test_combined_simulation_matches_the_ledger(self):
        combined = self.doc["candidates"]["selected_combined"]
        self.assertEqual(self.doc["candidates"]["baseline_code_bytes_claimed"], DECOMP1A_REVIEWED_BYTES)
        self.assertEqual(DECOMP1A_REVIEWED_BYTES + combined["new_code_bytes_classified"], self.ledger["reviewed"]["code_bytes"])
        self.assertEqual(combined["unresolved_unknown_bytes_after"], self.ledger["reviewed"]["unresolved_unknown_bytes"])
        self.assertEqual(combined["unresolved_clusters_after"], self.ledger["reviewed"]["unresolved_clusters"])

    def test_priority_ranges_and_documented_remainder(self):
        ranges = self.ledger["unclassified_range_claims"]["ranges"]
        status = {}
        for r in ranges:
            status[(r["start"], r["end"])] = r["status"]
        for key in ((0x4C90, 0x4CB0), (0x4CB0, 0x4CF7), (0x4CF7, 0x4D3E), (0x4D3E, 0x4D5D), (0x5832, 0x5935),
                    (0x5935, 0x5956), (0x361D, 0x3657), (0x4FDC, 0x5082)):
            self.assertEqual(status[key], "classified", key)
        # the player callback wrappers are reached only through script-vector data: still documented, not claimed
        for key in ((0x3901, 0x393B), (0x3A37, 0x3A48)):
            self.assertEqual(status[key], "unresolved", key)

    def test_dependency_map_lists_every_priority_entry(self):
        entries = {e["entry"]: (r["name"], e) for r in self.doc["dependency_map"] for e in r["entries"]}
        wanted = [e for _, _, _, es in B.PRIORITY for e in es]
        self.assertEqual(sorted(entries), sorted(wanted))
        for entry in (0x4C90, 0x4CB0, 0x4CF7, 0x4D3E, 0x5832, 0x5935, 0x361D, 0x4FDC):
            self.assertTrue(entries[entry][1]["reached_from_hardware_vector"], hex(entry))
            self.assertTrue(entries[entry][1]["direct_callers"], hex(entry))
            self.assertFalse(any(c["site_is_recovered_assembly"] for c in entries[entry][1]["direct_callers"]), hex(entry))
        for entry, stub, state in ((0x3901, 0x3B3, 0x0A), (0x3A37, 0x3AD, 0x0E), (0x3A48, 0x3F8, 0x14)):
            e = entries[entry][1]
            self.assertFalse(e["reached_from_hardware_vector"], hex(entry))
            self.assertEqual(e["direct_callers"], [], hex(entry))
            self.assertEqual(e["jp_stub_entries"], [stub], hex(entry))
            self.assertEqual({(x["type"], x["state"]) for x in e["stub_word_in_state_scripts"]}, {(1, state), (2, state)})


@unittest.skipUnless(canonical_rom(), "canonical Sonic Chaos ROM not available")
class RomBackedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = canonical_rom()

    def test_builder_reproduces_the_committed_file(self):
        doc = B.build(self.rom)
        self.assertEqual(json.dumps(doc, indent=1) + "\n", CALLERS.read_bytes().replace(RL.CRLF, RL.LF).decode("utf-8"))

    def test_hardware_vectors_reach_the_main_loop_and_the_priority_callees(self):
        ins, parent, indirect, invalid = B.vector_descent(self.rom)
        self.assertEqual(invalid, [])
        self.assertEqual(indirect, [0x5E6F, 0x5E9A, 0x6695, 0x6972, 0x77EC])
        for entry in (0x1333, 0x16B8, 0x4C90, 0x361D, 0x4FDC, 0x5832, 0x5935, 0x59B3):
            self.assertIn(entry, ins, hex(entry))
        for entry in (0x3901, 0x3A37, 0x3A48):
            self.assertNotIn(entry, ins, hex(entry))
        steps = B.chain(parent, 0x1333)
        self.assertEqual(steps[0], (0x0000, "vector"))
        self.assertIn((0x0476, "JP at $0035"), steps)
        self.assertEqual(steps[-1][0], 0x1333)

    def test_main_loop_dispatch_and_frame_update_facts(self):
        rom = self.rom
        self.assertEqual(rom[0x135D:0x1365].hex(), "cdb816cd3f1718ce")       # CALL 16B8 ; CALL 173F ; JR 1333
        self.assertEqual(rom[0x1333:0x1336].hex(), "cd2d06")                    # CALL 062D (frame wait)
        self.assertEqual(rom[0x16CA:0x16D0].hex(), "cd904ccd1d36")              # CALL 4C90 ; CALL 361D
        self.assertEqual(rom[0x16FA:0x16FD].hex(), "cd904c")
        self.assertEqual(rom[0x1702:0x1705].hex(), "cd1d36")

    def test_player_callback_dispatch_chain(self):
        rom = self.rom
        self.assertEqual(rom[0x364D:0x3650].hex(), "cd915e")                    # player update: CALL 5E91
        self.assertEqual(rom[0x5E91:0x5E9B].hex(), "dd6e0cdd660d7cb5c8e9")      # LD L,(IX+12) ; LD H,(IX+13) ; ... ; RET z ; JP (HL)
        self.assertEqual(rom[0x5E9A], 0xE9)
        self.assertEqual(rom[0x67AC:0x67B4].hex(), "dd770c237edd770d")         # command 05 stores the vector in +$0C / +$0D
        scripts = B.player_state_scripts(rom)
        self.assertEqual(scripts[(1, 0x0A)][0], 0x8142)
        self.assertEqual(rom[0x30142:0x30148].hex(), "ff05768fb303")            # FF 05 selector $8F76, vector $03B3
        self.assertEqual(rom[0x3B3:0x3B6].hex(), "c30139")                      # stub $03B3 -> JP $3901


if __name__ == "__main__":
    unittest.main()
