#!/usr/bin/env python3
"""Consistency and ROM-backed regeneration tests for the THZ1 census."""

import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "thz1_object_census.py"
CENSUS = ROOT / "data" / "rom-cache" / "thz1" / "object-census.json"
RECORDS = ROOT / "data" / "rom-cache" / "thz1" / "object-records.json"

spec = importlib.util.spec_from_file_location("thz1_object_census", TOOL)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def matching_rom():
    candidates = []
    if os.environ.get("SONIC_CHAOS_ROM"):
        candidates.append(Path(os.environ["SONIC_CHAOS_ROM"]))
    candidates += [
        ROOT.parent / "Sonic Chaos (Europe).sms",
        ROOT / "Sonic Chaos (Europe).sms",
    ]
    for path in candidates:
        if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == m.EXPECTED_SHA256:
            return path
    return None


class CensusCacheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.census = load(CENSUS)
        cls.source = load(RECORDS)
        cls.objects = {obj["type_id"]: obj for obj in cls.census["objects"]}

    def test_exact_population_and_types(self):
        expected = Counter(row["type_id"] for row in self.source["records"])
        self.assertEqual(self.census["raw_record_count"], 53)
        self.assertEqual(self.census["placed_type_count"], 8)
        self.assertEqual(self.census["type_counts"], dict(sorted(expected.items())))
        self.assertEqual(set(self.objects), set(expected))
        self.assertEqual(
            set(self.objects),
            {"0x09", "0x10", "0x18", "0x1B", "0x21", "0x26", "0x27", "0x28"},
        )

    def test_every_record_once_in_original_order(self):
        flattened = [row for obj in self.census["objects"] for row in obj["records"]]
        by_index = sorted(flattened, key=lambda row: row["record_index"])
        self.assertEqual([row["record_index"] for row in by_index], list(range(1, 54)))
        offsets = [row["rom_offset"] for row in by_index]
        self.assertEqual(len(offsets), len(set(offsets)))
        self.assertEqual(offsets, [row["rom_offset"] for row in self.source["records"]])
        self.assertEqual(
            self.census["record_order"],
            [row["type_id"] for row in self.source["records"]],
        )

    def test_coordinates_and_fields_reproduce_source_cache(self):
        actual = {
            row["record_index"]: row
            for obj in self.census["objects"]
            for row in obj["records"]
        }
        for source in self.source["records"]:
            got = actual[source["index"]]
            self.assertEqual(
                got,
                {
                    "record_index": source["index"],
                    "rom_offset": source["rom_offset"],
                    "world_x": source["world_x"],
                    "world_y": source["world_y"],
                    "flags": source["flags"],
                    "parameter": source["parameter"],
                    "aux0": source["aux0"],
                    "aux1": source["aux1"],
                },
            )

    def test_known_21_and_27_placements_match_dedicated_caches(self):
        for type_id in ("0x21", "0x27"):
            dedicated = load(ROOT / "data" / "rom-cache" / "thz1" / f"object-{type_id[2:]}.json")
            self.assertEqual(self.objects[type_id]["records"], dedicated["placements"])

    def test_known_animation_results_do_not_regress(self):
        expected = {
            "0x09": (["0x00", "0x01", "0x02", "0x03", "0x04", "0x05", "0x06"], []),
            "0x10": (["0x00", "0x0B", "0x0C"], []),
            "0x18": (["0x00", "0x01", "0x02", "0x03", "0x04", "0x05"], []),
            "0x1B": (["0x0E"], []),
            "0x21": (["0x00", "0x01", "0x02"], []),
            "0x26": (["0x00", "0x01", "0x02", "0x03"], []),
            "0x27": (["0x00", "0x01", "0x02"], []),
            "0x28": (["0x00", "0x01"], [4, 12, 14]),
        }
        for type_id, (frames, unresolved) in expected.items():
            animation = self.objects[type_id]["animation"]
            self.assertEqual(animation["reachable_mapping_frames"], frames)
            self.assertEqual(animation["unresolved_states"], unresolved)

    def test_ring_populations_remain_distinct(self):
        layout = load(ROOT / "data" / "rom-cache" / "thz1" / "layout-interactions.json")
        self.assertEqual(self.objects["0x09"]["record_count"], 24)
        self.assertEqual(self.census["separate_layout_ring_position_count"], 142)
        self.assertEqual(len(layout["rings"]), 142)
        self.assertIn("different populations", self.census["ring_count_note"])


class CensusRomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom_path = matching_rom()
        if cls.rom_path is None:
            raise unittest.SkipTest("set SONIC_CHAOS_ROM to run ROM-backed census regeneration")
        cls.rom = cls.rom_path.read_bytes()

    def test_state_and_mapping_metadata_agree_with_verified_tools(self):
        census = m.build_census(self.rom)
        for obj in census["objects"]:
            type_id = int(obj["type_id"], 16)
            trace = m.animation.trace_type(self.rom, type_id)
            mapping = m.assets.object_mapping(self.rom, type_id)
            self.assertEqual(obj["animation"]["state_table_cpu"], f"0x{trace['state_table_cpu']:04X}")
            self.assertEqual(obj["animation"]["state_table_rom"], f"0x{trace['state_table_rom']:05X}")
            self.assertEqual(obj["animation"]["state_count"], trace["state_count"])
            self.assertEqual(obj["mapping"]["mapping_cpu"], f"0x{mapping['mapping_cpu']:04X}")
            self.assertEqual(obj["mapping"]["mapping_rom"], f"0x{mapping['mapping_rom']:05X}")

    def test_committed_json_regenerates_deterministically(self):
        first = m.build_census(self.rom)
        second = m.build_census(self.rom)
        self.assertEqual(first, second)
        self.assertEqual(first, load(CENSUS))
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "census.json"
            m.write_census(output, first)
            self.assertEqual(output.read_bytes(), CENSUS.read_bytes())


if __name__ == "__main__":
    unittest.main(verbosity=2)
