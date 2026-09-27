#!/usr/bin/env python3
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("thz1_object_09", ROOT / "tools/thz1_object_09.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
CACHE = json.loads((ROOT / "data/rom-cache/thz1/object-09.json").read_text(encoding="utf-8"))


class Object09Tests(unittest.TestCase):
    def test_all_24_records_and_one_to_one_runtime_count(self):
        self.assertEqual(CACHE["raw_record_count"], 24)
        self.assertEqual(CACHE["runtime_entity_count"], 24)
        self.assertEqual(len(CACHE["placements"]), 24)
        self.assertEqual(CACHE["parameter_counts"], {"0x00": 11, "0x01": 13})
        self.assertEqual([x["index"] for x in CACHE["placements"]],
                         list(range(14, 22)) + list(range(37, 53)))

    def test_parameter_behavior(self):
        init = CACHE["controlled_original_routine_fixtures"]["initialization"]
        self.assertEqual([(x["requested_state"], x["renderer_flags_04"]) for x in init],
                         [(1, "0x00"), (3, "0x80")])
        phase = CACHE["controlled_original_routine_fixtures"]["hidden_frame_phase"]
        self.assertTrue(phase[0]["collected"])
        self.assertFalse(phase[1]["collected"])
        self.assertEqual(phase[0]["object_type_after"], "0xFF")

    def test_strict_interaction_boundaries_and_effect(self):
        rows = CACHE["controlled_original_routine_fixtures"]["overlap_boundaries"]
        self.assertEqual([x["collected"] for x in rows],
                         [True, False, True, False, True, False, True, False])
        hit = CACHE["controlled_original_routine_fixtures"]["counter_increment"]
        self.assertEqual((hit["ring_counter_d29a_bcd"], hit["sound_request"]),
                         ("0x10", "0xBF"))
        self.assertTrue(m.strict_overlap(11, -11))
        self.assertFalse(m.strict_overlap(12, 0))
        self.assertFalse(m.strict_overlap(0, -12))

    def test_sparkle_and_lifetime(self):
        self.assertEqual(CACHE["sparkle_timeline"]["updates"], 32)
        self.assertEqual(CACHE["sparkle_timeline"]["frames_by_record"], [5, 6] * 4)
        life = CACHE["controlled_original_routine_fixtures"]["lifetime"]
        self.assertEqual(life["offscreen"]["object_type_after"], "0xFE")
        self.assertEqual(life["cleanup"]["occupancy_after"], "0x00")
        self.assertTrue(life["cleanup"]["slot_is_zero"])

    def test_layout_ring_population_is_separate(self):
        link = CACHE["layout_ring_relationship"]
        self.assertFalse(link["same_source_population"])
        self.assertFalse(link["type_09_generates_layout_rings"])
        self.assertEqual(link["layout_population_count"], 142)


if __name__ == "__main__":
    unittest.main(verbosity=2)
