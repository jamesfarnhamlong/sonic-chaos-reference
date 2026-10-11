#!/usr/bin/env python3
"""ROM address ledger tests (DECOMP-0).

Most tests read only the committed metadata (no ROM needed). Tests that
regenerate the ledger skip unless the canonical ROM is available through
SONIC_CHAOS_ROM or ../source/Sonic Chaos (Europe).sms.
"""
import hashlib
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import rom_ledger as RL  # noqa: E402

LEDGER = ROOT / "data" / "rom-ledger" / "ledger.json"
SUMMARY = ROOT / "data" / "rom-ledger" / "summary.md"
DOC = ROOT / "docs" / "rom-address-ledger.md"
REGIONS = ROOT / "asm" / "recovered" / "regions.json"
ROM_PATH = Path(os.environ.get("SONIC_CHAOS_ROM", str(RL.DEFAULT_ROM)))


def canonical_rom():
    if ROM_PATH.is_file():
        data = ROM_PATH.read_bytes()
        if len(data) == RL.ROM_SIZE and hashlib.sha256(data).hexdigest() == RL.ROM_SHA256:
            return data
    return None


def lf_text(path):
    """File text with LF newlines (CRLF checkouts compare equal)."""
    return path.read_bytes().replace(RL.CRLF, RL.LF).decode("utf-8")


def claim(start, end, primary, **kw):
    return RL.make_claim(start, end, primary, kw.pop("importer", "test"), kw.pop("source", "test"),
                         kw.pop("evidence", "structure_verified"), **kw)


def resolve_synthetic(claims):
    return RL.resolve(RL.dedupe_claims(claims))


class CommittedLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        cls.segments = cls.ledger["segments"]

    def test_complete_contiguous_accounting(self):
        pos = 0
        for s in self.segments:
            self.assertEqual(s["start"], pos, "gap or overlap before %05X" % s["start"])
            self.assertGreater(s["end"], s["start"])
            self.assertEqual(s["length"], s["end"] - s["start"])
            pos = s["end"]
        self.assertEqual(pos, RL.ROM_SIZE)

    def test_category_sum_is_exactly_the_rom(self):
        by_cat = self.ledger["totals"]["by_category"]
        self.assertEqual(set(by_cat), set(RL.CATEGORIES))
        self.assertEqual(sum(by_cat.values()), 524288)
        recount = {c: 0 for c in RL.CATEGORIES}
        for s in self.segments:
            self.assertIn(s["primary"], RL.CATEGORIES)
            recount[s["primary"]] += s["length"]
        self.assertEqual(recount, by_cat)
        self.assertEqual(self.ledger["totals"]["total_bytes"], 524288)

    def test_bounds_and_bank_splits(self):
        for s in self.segments:
            self.assertTrue(0 <= s["start"] < s["end"] <= RL.ROM_SIZE)
            self.assertEqual(s["bank"], s["start"] // RL.BANK_SIZE)
            self.assertEqual(s["bank"], (s["end"] - 1) // RL.BANK_SIZE, "segment crosses a bank")
            self.assertEqual(s["cpu_paged"], 0x8000 + s["start"] % RL.BANK_SIZE)
            self.assertEqual(s["cpu_resident"], s["start"] if s["bank"] in RL.ENGINE_BANKS else None)
        banks = self.ledger["banks"]
        self.assertEqual([b["bank"] for b in banks], list(range(32)))
        for b in banks:
            self.assertEqual(sum(b["by_category"].values()), RL.BANK_SIZE)
            self.assertEqual(b["end"] - b["start"], RL.BANK_SIZE)
            part = [s for s in self.segments if s["bank"] == b["bank"]]
            self.assertEqual(sum(s["length"] for s in part), RL.BANK_SIZE)
        self.assertEqual(sum(b["recovered_bytes"] for b in banks), self.ledger["totals"]["recovered_bytes"])

    def test_claim_references_and_unknown_fill(self):
        ids = {c["id"] for c in self.ledger["claims"]}
        self.assertEqual(len(ids), len(self.ledger["claims"]))
        for c in self.ledger["claims"]:
            self.assertTrue(0 <= c["start"] < c["end"] <= RL.ROM_SIZE)
            self.assertIn(c["primary"], RL.CATEGORIES)
            self.assertNotEqual(c["primary"], "UNKNOWN")
        for s in self.segments:
            self.assertTrue(set(s["claims"]) <= ids)
            if not s["claims"]:
                self.assertEqual(s["primary"], "UNKNOWN")
                self.assertEqual(s["recovery"], "not_recovered")
            if s["contested"]:
                self.assertEqual(s["primary"], "UNKNOWN")

    def test_recovery_manifest_consistency(self):
        regions = json.loads(REGIONS.read_text(encoding="utf-8"))
        rm = self.ledger["recovered_manifest"]
        self.assertEqual(rm["regions"], len(regions))
        self.assertEqual(rm["bytes"], sum(r["bytes"] for r in regions))
        self.assertEqual(rm["code_bytes"], sum(r["bytes"] for r in regions if r["kind"] == "code"))
        self.assertEqual(rm["data_bytes"], sum(r["bytes"] for r in regions if r["kind"] == "data"))
        recovered = sum(s["length"] for s in self.segments if s["recovery"] == "recovered")
        self.assertEqual(recovered, rm["bytes"])
        self.assertEqual(self.ledger["totals"]["recovered_bytes"], rm["bytes"])
        for r in regions:
            inside = [s for s in self.segments if s["start"] < r["end"] and s["end"] > r["start"]]
            self.assertEqual(sum(min(s["end"], r["end"]) - max(s["start"], r["start"]) for s in inside),
                             r["bytes"])
            for s in inside:
                self.assertEqual(s["recovery"], "recovered", r["name"])
                self.assertIn(r["name"], s["regions"])
                if not s["contested"]:
                    self.assertEqual(s["primary"], r["kind"].upper(), r["name"])
        # recovered code/data split, allowing only reported contested bytes
        contested = sum(s["length"] for s in self.segments if s["contested"] and s["recovery"] == "recovered")
        t = self.ledger["totals"]
        self.assertEqual(t["recovered_code_bytes"] + t["recovered_data_bytes"] + contested, rm["bytes"])

    def test_contradictions_are_reported_not_resolved(self):
        hard = self.ledger["overlaps"]["contradictory"]
        self.assertEqual(self.ledger["overlaps"]["stats"]["contradictory_pairs"], len(hard))
        contested = sum(s["length"] for s in self.segments if s["contested"])
        self.assertEqual(self.ledger["totals"]["contested_bytes"], contested)
        for h in hard:
            lo, hi = h["overlap"]
            self.assertNotEqual(h["classes"][0], h["classes"][1])
            for s in self.segments:
                if s["start"] < hi and s["end"] > lo:
                    self.assertTrue(s["contested"])

    def test_known_proven_regions(self):
        def at(offset):
            return next(s for s in self.segments if s["start"] <= offset < s["end"])

        self.assertEqual(at(0x48000)["primary"], "COMPRESSED")            # THZ1 layout
        self.assertEqual(at(0x48000)["subtype"], "level-layout-rle")
        self.assertEqual(at(0x48000)["start"], 0x48000)
        self.assertEqual(at(0x48BA8)["end"], 0x48BA9)                    # layout end (exclusive) per cache
        self.assertEqual(at(0x705AE)["subtype"], "object-placement-list")
        self.assertEqual(at(0x7078B)["end"], 0x7078C)                    # includes the $FF terminator
        self.assertEqual(at(0x090E1)["subtype"], "sound-track-pointer")
        self.assertEqual(at(0x09168)["end"], 0x09169)
        self.assertEqual(at(0x38000)["subtype"], "collision-header-pointer-table")
        self.assertEqual(at(0x40F9E)["primary"], "COMPRESSED")           # THZ primary tile stream
        self.assertEqual(at(0x40F9E)["start"], 0x40F9E)
        self.assertEqual(at(0x226A)["primary"], "CODE")
        self.assertEqual(at(0x226A)["recovery"], "recovered")
        self.assertEqual(at(0x429D)["primary"], "DATA")
        self.assertEqual(at(0x00000)["primary"], "UNKNOWN")               # reset vector area not claimed

    def test_metadata_only_output(self):
        text = LEDGER.read_text(encoding="utf-8")
        long_hex = [m for m in re.findall(r"[0-9A-Fa-f]{33,}", text) if m.lower() != RL.ROM_SHA256]
        self.assertEqual(long_hex, [], "unexpected long hex payload in ledger")
        self.assertLess(len(text), 8 * 1024 * 1024)
        self.assertEqual(self.ledger["rom"]["sha256"], RL.ROM_SHA256)
        out = LEDGER.parent
        self.assertEqual(sorted(p.name for p in out.iterdir()), ["ledger.json", "summary.md"])
        for p in out.iterdir():
            self.assertNotIn(b"\x00", p.read_bytes()[:4096], "binary data in " + p.name)

    def test_summary_and_doc_match_committed_totals(self):
        t = self.ledger["totals"]
        summary = SUMMARY.read_text(encoding="utf-8")
        for c in RL.CATEGORIES:
            self.assertIn("| %s | %d |" % (c, t["by_category"][c]), summary)
        doc = DOC.read_text(encoding="utf-8")
        for n in (t["unknown_bytes"], t["classified_bytes"], t["recovered_bytes"]):
            self.assertIn("{:,}".format(n), doc, "docs/rom-address-ledger.md is stale for %d" % n)
        self.assertIn("{:,}".format(t["by_category"]["COMPRESSED"]), doc)


class ResolverTests(unittest.TestCase):
    def check_whole(self, segments):
        pos = 0
        for s in segments:
            self.assertEqual(s["start"], pos)
            pos = s["end"]
        self.assertEqual(pos, RL.ROM_SIZE)
        self.assertEqual(sum(s["length"] for s in segments), RL.ROM_SIZE)

    def test_empty_ledger_is_all_unknown_and_split_into_32_banks(self):
        segments, conflicts = resolve_synthetic([])
        self.check_whole(segments)
        self.assertEqual(len(segments), 32)
        self.assertTrue(all(s["primary"] == "UNKNOWN" and s["length"] == RL.BANK_SIZE for s in segments))
        self.assertEqual(conflicts["stats"]["contradictory_pairs"], 0)

    def test_claim_crossing_a_bank_boundary_is_split(self):
        segments, _ = resolve_synthetic([claim(0x3F00, 0x4100, "DATA")])
        self.check_whole(segments)
        data = [s for s in segments if s["primary"] == "DATA"]
        self.assertEqual([(s["start"], s["end"], s["bank"]) for s in data],
                         [(0x3F00, 0x4000, 0), (0x4000, 0x4100, 1)])

    def test_identical_and_nested_overlaps_are_compatible(self):
        claims = RL.dedupe_claims([
            claim(0x100, 0x200, "DATA", subtype="outer", source="a"),
            claim(0x100, 0x200, "DATA", subtype="outer", source="b"),        # exact duplicate
            claim(0x140, 0x160, "DATA", subtype="inner")])
        self.assertEqual(len(claims), 2)
        self.assertEqual(claims[0]["sources"], ["a", "b"])
        segments, conflicts = RL.resolve(claims)
        self.assertEqual(conflicts["stats"]["contradictory_pairs"], 0)
        self.assertEqual(conflicts["stats"]["compatible_nested_pairs"], 1)
        inner = next(s for s in segments if s["start"] == 0x140)
        self.assertEqual((inner["primary"], inner["subtype"], inner["contested"]), ("DATA", "inner", False))
        self.assertEqual(next(s for s in segments if s["start"] == 0x100)["subtype"], "outer")

    def test_partial_overlap_same_class_is_compatible_but_listed(self):
        _, conflicts = resolve_synthetic([claim(0x100, 0x200, "DATA"), claim(0x180, 0x280, "DATA")])
        self.assertEqual(conflicts["stats"]["compatible_partial_overlap_pairs"], 1)
        self.assertEqual(conflicts["partial"][0]["overlap"], [0x180, 0x200])
        self.assertEqual(conflicts["stats"]["contradictory_pairs"], 0)

    def test_contradiction_is_detected_and_not_silently_chosen(self):
        segments, conflicts = resolve_synthetic([claim(0x100, 0x200, "CODE"), claim(0x180, 0x280, "DATA")])
        self.check_whole(segments)
        self.assertEqual(conflicts["stats"]["contradictory_pairs"], 1)
        self.assertEqual(conflicts["contradictory"][0]["overlap"], [0x180, 0x200])
        contested = [s for s in segments if s["contested"]]
        self.assertEqual([(s["start"], s["end"], s["primary"]) for s in contested], [(0x180, 0x200, "UNKNOWN")])
        self.assertEqual(next(s for s in segments if s["start"] == 0x100)["primary"], "CODE")
        self.assertEqual(next(s for s in segments if s["start"] == 0x200)["primary"], "DATA")

    def test_invalid_claims_are_refused(self):
        for args in ((-1, 5, "DATA"), (5, 5, "DATA"), (0, RL.ROM_SIZE + 1, "DATA"), (0, 4, "UNKNOWN"), (0, 4, "BOGUS")):
            with self.assertRaises(ValueError):
                claim(*args)

    def test_recovery_status_is_independent_of_classification(self):
        independent = [claim(0x100, 0x200, "CODE")]
        _, _ = resolve_synthetic(independent)
        before = RL.totals(resolve_synthetic(independent)[0])
        after = RL.totals(resolve_synthetic(independent + [
            claim(0x100, 0x200, "CODE", recovered=True, basis="recovery_manifest",
                  evidence="byte_verified_assembly")])[0])
        self.assertEqual(after["recovered_bytes"] - before["recovered_bytes"], 0x100)
        self.assertEqual(after["classified_bytes"], before["classified_bytes"])
        self.assertEqual(after["independent_structural_bytes"], before["independent_structural_bytes"])
        self.assertEqual(after["by_category"], before["by_category"])
        only_recovery = RL.totals(resolve_synthetic([claim(0x100, 0x200, "CODE", recovered=True,
                                                           basis="recovery_manifest",
                                                           evidence="byte_verified_assembly")])[0])
        self.assertEqual(only_recovery["classified_by_recovery_only_bytes"], 0x100)
        self.assertEqual(only_recovery["independent_structural_bytes"], 0)

    def test_deterministic_resolution(self):
        claims = [claim(0x100, 0x200, "DATA", subtype="b"), claim(0x100, 0x200, "DATA", subtype="a"),
                  claim(0x4100, 0x4200, "CODE")]
        a = RL.dumps(resolve_synthetic(list(claims))[0])
        b = RL.dumps(resolve_synthetic(list(reversed(claims)))[0])
        self.assertEqual(a, b)


class RomBackedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = canonical_rom()
        if cls.rom is None:
            raise unittest.SkipTest("canonical ROM not available (set SONIC_CHAOS_ROM)")

    def test_committed_ledger_is_current_and_deterministic(self):
        first = RL.build_ledger(self.rom)
        second = RL.build_ledger(self.rom)
        self.assertEqual(RL.dumps(first), RL.dumps(second))
        self.assertEqual(RL.dumps(first), lf_text(LEDGER))
        self.assertEqual(RL.summary_markdown(first), lf_text(SUMMARY))

    def test_generate_writes_identical_files_twice(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            RL.generate(ROM_PATH, a)
            RL.generate(ROM_PATH, b)
            for name in ("ledger.json", "summary.md"):
                self.assertEqual((Path(a) / name).read_bytes(), (Path(b) / name).read_bytes())
            _, stale = RL.generate(ROM_PATH, a, check=True)
            self.assertEqual(stale, [])

    def test_rejects_wrong_rom(self):
        with tempfile.TemporaryDirectory() as d:
            bad = Path(d) / "bad.sms"
            bad.write_bytes(self.rom[:-1])
            with self.assertRaises(ValueError):
                RL.load_rom(bad)
            tweaked = bytearray(self.rom)
            tweaked[0x1234] ^= 1
            bad.write_bytes(bytes(tweaked))
            with self.assertRaises(ValueError):
                RL.load_rom(bad)

    def test_imported_extents_agree_with_the_rom(self):
        ledger = RL.build_ledger(self.rom)
        # every compressed layout stream re-decodes to exactly its claimed extent
        for c in ledger["claims"]:
            if c["subtype"] == "level-layout-rle":
                cells, end, term = RL.L.decode_layout_stream(self.rom, c["start"])
                self.assertTrue(term)
                self.assertEqual(end, c["end"])
        # every tile stream is exactly the bytes its decoder consumes
        for c in ledger["claims"]:
            if c["subtype"] == "tile-stream":
                self.assertEqual(RL.tile_stream_extent(self.rom, c["start"])[:2], (c["start"], c["end"]))
        # object lists end with the $FF terminator
        for c in ledger["claims"]:
            if c["subtype"] == "object-placement-list":
                self.assertEqual(self.rom[c["end"] - 1], 0xFF)
                self.assertEqual((c["end"] - 1 - c["start"]) % 9, 0)
        self.assertEqual(ledger["rejected_claims"], [])


if __name__ == "__main__":
    unittest.main()
