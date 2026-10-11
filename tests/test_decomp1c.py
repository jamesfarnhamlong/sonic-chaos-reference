#!/usr/bin/env python3
"""DECOMP-1C tests: player script parser, callback/stub support, derived regions and ledger integration.

Tests that need the canonical ROM skip without SONIC_CHAOS_ROM or ../source/Sonic Chaos (Europe).sms;
the rest read only committed metadata or tiny synthetic images.
"""
import copy
import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import decomp1a_review as RV  # noqa: E402
import decomp1c_callbacks as C  # noqa: E402
import player_scripts as PS  # noqa: E402
import rom_flow as F  # noqa: E402
import rom_ledger as RL  # noqa: E402

CALLBACKS = ROOT / "data" / "decomp1c" / "callbacks.json"
DERIVED = ROOT / "data" / "decomp1c" / "derived-regions.json"
REGIONS = ROOT / "asm" / "recovered" / "regions.json"
LEDGER = ROOT / "data" / "rom-ledger" / "ledger.json"
REVIEWED = ROOT / RL.REVIEWED
ROM_PATH = Path(os.environ.get("SONIC_CHAOS_ROM", str(RL.DEFAULT_ROM)))


def canonical_rom():
    if ROM_PATH.is_file():
        data = ROM_PATH.read_bytes()
        if len(data) == RL.ROM_SIZE and hashlib.sha256(data).hexdigest() == RL.ROM_SHA256:
            return data
    return None


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def bank12(blobs):
    """Synthetic image whose bank 12 (file $30000) holds the given {cpu address: bytes}."""
    rom = bytearray(0x40000)
    for cpu, blob in blobs.items():
        off = PS.file_offset(cpu)
        rom[off:off + len(blob)] = blob
    return bytes(rom)


# commands as derive_commands reports them (outcomes: [kind, [next|jump, n] or None])
CMDS = {
    0: {"outcomes": [["restart", None]], "selector_operand": None, "callback_operand": None},
    5: {"outcomes": [["frame_set", ["next", 4]]], "selector_operand": 0, "callback_operand": 2},
    7: {"outcomes": [["next_record", ["jump", 0]]], "selector_operand": None, "callback_operand": None},
    15: {"outcomes": [["next_record", ["next", 2]], ["next_record", ["jump", 0]]], "selector_operand": None,
         "callback_operand": None},
}


class ParserSyntheticTests(unittest.TestCase):
    def parse(self, blob, start=0x8100):
        rom = bank12({start: blob})
        notes = []
        steps, cbs = PS.parse_script(rom, start, CMDS, notes)
        return steps, cbs, notes

    def test_records_and_ff05_expose_only_real_callback_fields(self):
        # record dur=$AD frame=$03 cb=$0000: the bytes AD 03 look like a stub address but are not a callback field
        # FF 05 selector $8F76 callback $03B3 ; record dur 4 frame 1 cb $03AD ; FF 00
        blob = bytes([0xAD, 0x03, 0x00, 0x00, 0xFF, 0x05, 0x76, 0x8F, 0xB3, 0x03, 0x04, 0x01, 0xAD, 0x03, 0xFF, 0x00])
        steps, cbs, notes = self.parse(blob)
        self.assertEqual(notes, [])
        self.assertEqual([(c["kind"], c["vector"]) for c in cbs], [("record", 0), ("FF 05", 0x3B3), ("record", 0x3AD)])
        self.assertEqual(cbs[1]["operand_cpu"], 0x8108)
        self.assertEqual(cbs[1]["selector"], 0x8F76)
        self.assertEqual(sorted(steps), [0x8100, 0x8104, 0x810A, 0x810E])

    def test_conditional_loop_terminates_and_both_branches_are_explored(self):
        # FF 0F: jump to $8100 or skip 2 operand bytes ; then a record ; FF 00
        blob = bytes([0xFF, 0x0F, 0x00, 0x81, 0x02, 0x02, 0x34, 0x12, 0xFF, 0x00])
        steps, cbs, notes = self.parse(blob)
        self.assertEqual(notes, [])
        self.assertEqual([c["vector"] for c in cbs], [0x1234])

    def test_unknown_command_and_window_exit_are_reported_not_invented(self):
        steps, cbs, notes = self.parse(bytes([0xFF, 0x77]))
        self.assertEqual(notes, [("unknown_command", 0x8100)])
        steps, cbs, notes = self.parse(bytes([0xFF, 0x07, 0x00, 0xC0]))        # jump out of slot 2
        self.assertEqual(notes, [("leaves_bank_window", 0xC000)])

    def test_state_table_ends_where_its_first_script_starts(self):
        rom = bytearray(bank12({0x8000: bytes([0x08, 0x80, 0x0A, 0x80, 0x08, 0x80, 0x0A, 0x80,
                                               0xFF, 0x00, 0xFF, 0x00, 0x20, 0x00])}))
        rom[PS.TYPE_TABLE:PS.TYPE_TABLE + 4] = bytes([0x00, 0x80, 0x00, 0x80])
        base, scripts = PS.state_tables(bytes(rom))[1]
        self.assertEqual((base, scripts), (0x8000, [0x8008, 0x800A, 0x8008, 0x800A]))

    def test_target_offset_rules(self):
        self.assertEqual(PS.target_offset(0x03B3), 0x03B3)
        self.assertEqual(PS.target_offset(0x8142), 0x30142)
        self.assertIsNone(PS.target_offset(0))
        self.assertIsNone(PS.target_offset(0xC000))


@unittest.skipUnless(canonical_rom(), "canonical Sonic Chaos ROM not available")
class RomBackedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = canonical_rom()
        cls.doc = PS.parse_scripts(cls.rom)

    def test_engine_facts_are_verified_and_a_changed_engine_is_refused(self):
        self.assertEqual(set(self.doc["engine_facts"]), set(PS.ENGINE_SEQUENCES))
        for start in (0x5E91, 0x653D, 0x6680):
            tampered = bytearray(self.rom)
            tampered[start] ^= 0x01
            with self.assertRaises(ValueError):
                PS.engine_facts(bytes(tampered))

    def test_handler_semantics_are_derived_from_the_handlers(self):
        c = self.doc["commands"]
        self.assertEqual(c[5]["outcomes"], [["frame_set", ["next", 4]]])
        self.assertEqual((c[5]["selector_operand"], c[5]["callback_operand"]), (0, 2))
        self.assertEqual((c[13]["selector_operand"], c[13]["callback_operand"]), (None, 3))
        self.assertEqual(c[0]["outcomes"], [["restart", None]])
        self.assertEqual(c[7]["outcomes"], [["next_record", ["jump", 0]]])
        self.assertEqual([o[1] for o in c[15]["outcomes"]], [["next", 2], ["jump", 0]])
        self.assertEqual([c[i]["outcomes"][0][1][1] for i in (2, 3, 4, 6, 9, 10, 11, 12, 14)], [4, 1, 6, 1, 2, 3, 2, 2, 1])

    def test_all_player_scripts_parse_without_ambiguity(self):
        self.assertEqual(self.doc["notes"], [])
        self.assertEqual([(t["type"], t["states"]) for t in self.doc["tables"]], [(1, 55), (2, 54)])
        self.assertEqual(len(self.doc["states"]), 109)

    def test_priority_chains_are_recomputed_from_the_rom(self):
        rows = {}
        for r in self.doc["callbacks"]:
            rows.setdefault((r["type"], r["state"]), []).append(r)
        for ty in (1, 2):
            a = [r for r in rows[(ty, 0x0A)] if r["vector"] == 0x03B3]
            self.assertEqual(len(a), 1)
            self.assertEqual((a[0]["kind"], a[0]["selector"], a[0]["bank"]), ("FF 05", 0x8F76, 12))
            self.assertEqual(a[0]["operand_offset"], a[0]["operand_cpu"] - 0x8000 + 0x30000)
            self.assertIn(0x03AD, {r["vector"] for r in rows[(ty, 0x0E)]})
            self.assertIn(0x03F8, {r["vector"] for r in rows[(ty, 0x14)]})
        r = [x for x in rows[(1, 0x0A)] if x["vector"] == 0x03B3][0]
        self.assertEqual((r["script_cpu"], r["operand_cpu"]), (0x8142, 0x8146))
        self.assertEqual(self.rom[0x30142:0x30148].hex(), "ff05768fb303")
        for stub, dest in ((0x3B3, 0x3901), (0x3AD, 0x3A37), (0x3F8, 0x3A48)):
            self.assertEqual(self.rom[stub], 0xC3)
            self.assertEqual(self.rom[stub + 1] | self.rom[stub + 2] << 8, dest)

    def test_callback_rows_sit_at_the_engine_derived_fields(self):
        for r in self.doc["callbacks"]:
            if r["kind"] == "record":
                self.assertEqual(r["operand_cpu"], r["at"] + 2)
            else:
                sem = self.doc["commands"][int(r["kind"].split()[1], 16)]
                if r["vector"]:
                    self.assertEqual(r["operand_cpu"], r["at"] + 2 + sem["callback_operand"])
                if r["selector"]:
                    self.assertEqual(r["selector_operand_cpu"], r["at"] + 2 + sem["selector_operand"])

    def test_dispatch_seeds_verify_and_reject_tampering(self):
        seeds = PS.dispatch_seeds(self.rom)
        self.assertIn(0x300D9, seeds)
        for off, via in list(seeds.items())[:20]:
            self.assertTrue(PS.seed_supported(self.rom, off, via))
        bad = dict(seeds[0x300D9])
        bad["operand_offset"] += 1
        self.assertFalse(PS.seed_supported(self.rom, 0x300D9, bad))
        self.assertFalse(PS.seed_supported(self.rom, 0x300DA, seeds[0x300D9]))


class CommittedEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load(CALLBACKS)
        cls.derived = load(DERIVED)
        cls.regions = {r["name"]: r for r in load(REGIONS)}
        cls.ledger = load(LEDGER)

    def test_derived_regions_are_registered_exactly(self):
        for d in self.derived:
            r = self.regions[d["name"]]
            self.assertEqual((r["start"], r["end"], r["kind"]), (d["start"], d["end"], "code"))
        names = {d["name"] for d in self.derived}
        self.assertEqual({n for n in self.regions if n.startswith((C.STUB_PREFIX, C.HANDLER_PREFIX))}, names)

    def test_only_supported_stubs_are_recovered(self):
        supported = {s["stub"] for s in self.doc["stubs"] if s["supported"]}
        recovered = set()
        for r in self.doc["stub_regions"]:
            recovered.update(range(r["start"], r["end"], 3))
        self.assertEqual(recovered, supported)
        for s in self.doc["stubs"]:
            if s["supported"]:
                self.assertTrue(s["script_callback_refs"] or s["script_executed_refs"] or s["direct_callers"])
            else:
                self.assertEqual((s["script_callback_refs"], s["script_executed_refs"], s["direct_callers"]), (0, 0, []))
        for a in self.doc["stub_table"]["unsupported"]:
            seg = next(x for x in self.ledger["segments"] if x["start"] <= a < x["end"])
            self.assertEqual(seg["primary"], "UNKNOWN", hex(a))

    def test_priority_stubs_and_wrappers(self):
        stubs = {s["stub"]: s for s in self.doc["stubs"]}
        for stub, dest, state in ((0x3B3, 0x3901, 0x0A), (0x3AD, 0x3A37, 0x0E), (0x3F8, 0x3A48, 0x14)):
            self.assertTrue(stubs[stub]["supported"])
            self.assertEqual(stubs[stub]["destination"], dest)
            self.assertIn([1, state], [list(x) for x in stubs[stub]["state_scripts"]])
            self.assertIn([2, state], [list(x) for x in stubs[stub]["state_scripts"]])
        status = {(r["start"], r["end"]): r["status"] for r in self.ledger["unclassified_range_claims"]["ranges"]}
        for key in ((0x3901, 0x393B), (0x3A37, 0x3A48), (0x3A48, 0x3A59)):
            self.assertEqual(status[key], "classified", key)

    def test_stub_table_geometry_is_a_structural_fact_only(self):
        t = self.doc["stub_table"]
        self.assertEqual(t["stubs"], (t["bounds"][1] - t["bounds"][0]) // 3)
        self.assertGreater(len(t["unsupported"]), 0)
        self.assertEqual(t["supported"] + len(t["unsupported"]), t["stubs"])
        self.assertIn("not entry evidence", t["structure"])

    def test_evidence_tier_is_static(self):
        self.assertIn("no execution trace", self.doc["evidence_tier"])

    def test_ledger_metrics_stay_separate(self):
        t = self.ledger["totals"]
        self.assertEqual(t["recovered_bytes"], self.ledger["recovered_manifest"]["bytes"])
        self.assertLess(t["recovered_bytes"], t["classified_bytes"])
        self.assertEqual(t["classified_bytes"], t["independent_structural_bytes"] + t["classified_by_recovery_only_bytes"])


@unittest.skipUnless(canonical_rom(), "canonical Sonic Chaos ROM not available")
class RegenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = canonical_rom()

    def test_tool_reproduces_the_committed_files(self):
        doc = C.build(self.rom)
        self.assertEqual(json.dumps(doc, indent=1) + "\n", CALLBACKS.read_bytes().replace(RL.CRLF, RL.LF).decode("utf-8"))
        self.assertEqual(C.derived_region_doc(doc), DERIVED.read_bytes().replace(RL.CRLF, RL.LF).decode("utf-8"))

    def test_regions_pass_the_strict_boundary_proof(self):
        for r in load(REGIONS):
            if not r["name"].startswith((C.STUB_PREFIX, C.HANDLER_PREFIX)):
                continue
            insns = C.B1.decode_all(self.rom, r["start"], r["end"])
            self.assertIsNotNone(insns, r["name"])
            self.assertEqual(len(insns), r["instructions"], r["name"])
            self.assertTrue(F.is_terminal(list(insns.values())[-1]), r["name"])
            if r["name"].startswith(C.STUB_PREFIX):
                for p, d in insns.items():
                    self.assertEqual(d.op, F.OP.JP)
                    self.assertEqual((p - r["start"]) % 3, 0)
            else:
                for p, d in insns.items():
                    if d.op in (F.OP.JR, F.OP.DJNZ):
                        self.assertIn(F.resolve_target(p, F._addr_operand(d)), insns, r["name"])

    def test_default_review_has_script_seeds_and_the_override_removes_them(self):
        committed = load(REVIEWED)
        self.assertEqual(json.loads(json.dumps(RV.build(self.rom))), committed)
        kinds = {list(s["via"])[0] for r in committed["code_flow_reviews"] for s in r["seeds"]}
        self.assertIn("player_script", kinds)
        without = RV.build(self.rom, script_seeds=False)
        self.assertLess(len(without["code_flow_reviews"]), len(committed["code_flow_reviews"]))

    def test_stale_script_seed_is_rejected_by_the_ledger(self):
        doc = copy.deepcopy(load(REVIEWED))
        review = next(r for r in doc["code_flow_reviews"] if "player_script" in r["seeds"][0]["via"])
        review["seeds"][0]["via"]["player_script"]["operand_offset"] += 1
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "data" / "rom-ledger").mkdir(parents=True)
            (root / "asm" / "recovered").mkdir(parents=True)
            shutil.copy(REGIONS, root / "asm" / "recovered" / "regions.json")
            (root / RL.REVIEWED).write_text(json.dumps(doc), encoding="utf-8")
            with self.assertRaises(ValueError):
                RL.import_reviewed(self.rom, root, load(REGIONS))


if __name__ == "__main__":
    unittest.main()
