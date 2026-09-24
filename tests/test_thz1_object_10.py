#!/usr/bin/env python3
"""Independent translations and committed metadata checks for type $10."""

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "thz1_object_10.py"
CACHE = ROOT / "data" / "rom-cache" / "thz1" / "object-10.json"
spec = importlib.util.spec_from_file_location("thz1_object_10", TOOL)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class Object10Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cache = json.loads(CACHE.read_text(encoding="utf-8"))

    def test_all_five_placements_exactly(self):
        placements = m.load_placements()
        self.assertEqual(
            [
                (
                    row["rom_offset"], row["world_x"], row["world_y"],
                    row["flags"], row["parameter"], row["aux0"], row["aux1"],
                )
                for row in placements
            ],
            [
                ("0x705F6", 656, 846, "0x00", "0x06", "0x00", "0x00"),
                ("0x705FF", 1712, 494, "0x00", "0x06", "0x00", "0x00"),
                ("0x70608", 336, 270, "0x00", "0x04", "0x00", "0x00"),
                ("0x70611", 1472, 110, "0x00", "0x04", "0x00", "0x00"),
                ("0x7061A", 2688, 686, "0x00", "0x02", "0x00", "0x00"),
            ],
        )
        self.assertEqual(
            m.parameter_distribution(placements),
            {"0x02": 1, "0x04": 2, "0x06": 2},
        )

    def test_parameter_to_reward_mask_translation(self):
        self.assertEqual(m.reward_mask(0x02), 0x02)
        self.assertEqual(m.reward_mask(0x04), 0x08)
        self.assertEqual(m.reward_mask(0x06), 0x20)

    def test_overlap_boundaries_and_side_selection(self):
        self.assertEqual(m.overlap_contact(18, 0), 0x04)
        self.assertEqual(m.overlap_contact(19, 0), 0x04)
        self.assertEqual(m.overlap_contact(20, 0), 0)
        self.assertEqual(m.overlap_contact(0, -23), 0x01)
        self.assertEqual(m.overlap_contact(0, -24), 0x01)
        self.assertEqual(m.overlap_contact(0, -25), 0)
        self.assertEqual(m.overlap_contact(0, 17), 0x02)
        self.assertEqual(m.overlap_contact(0, 18), 0x02)
        self.assertEqual(m.overlap_contact(0, 19), 0)

    def test_complete_animation_metadata(self):
        self.assertTrue(self.cache["placement_bytes_verified"])
        animation = self.cache["animation"]
        self.assertEqual(animation["state_count"], 4)
        self.assertEqual(
            animation["reachable_mapping_frame_indices"],
            ["0x00", "0x0B", "0x0C"],
        )
        self.assertEqual(animation["unresolved_states"], [])
        self.assertEqual([len(x["commands"]) for x in animation["states"]], [1, 1, 1, 1])
        self.assertTrue(all(x["unresolved"] is None for x in animation["states"]))

    def test_contact_and_reward_results(self):
        fixtures = self.cache["controlled_original_routine_fixtures"]
        contact = fixtures["contact"]
        self.assertEqual(contact["ordinary_top_contact"]["object_type_after"], "0x10")
        self.assertEqual(contact["power_up_06_without_attack"]["object_type_after"], "0x10")
        self.assertEqual(contact["top_attack_downward"]["object_type_after"], "0x0F")
        self.assertEqual(contact["side_attack_downward"]["object_type_after"], "0x0F")
        self.assertEqual(contact["bottom_attack_upward"]["requested_object_state"], 3)
        self.assertEqual(contact["bottom_attack_upward"]["object_type_after"], "0x10")
        self.assertEqual(contact["bottom_attack_upward"]["player_y_velocity_8_8"], 512)
        self.assertEqual(contact["bottom_attack_upward"]["object_y_velocity_8_8"], -512)
        self.assertTrue(all(
            row["object_type_after"] == "0x10"
            for row in contact["top_blocked_player_states"].values()
        ))

        reward = fixtures["reward"]
        self.assertEqual([x["table_mask"] for x in reward], ["0x02", "0x08", "0x20"])
        self.assertEqual(reward[0]["after_reward_dispatch"]["counter_d299_bcd"], "0x10")
        self.assertEqual(reward[0]["after_reward_dispatch"]["sound_request_de04"], "0xA9")
        self.assertEqual(reward[1]["after_reward_dispatch"]["power_up_d532"], "0x04")
        self.assertEqual(reward[1]["after_reward_dispatch"]["timer_d44c"], 300)
        self.assertEqual(reward[1]["after_reward_dispatch"]["sound_request_de04"], "0x85")
        self.assertEqual(reward[2]["after_reward_dispatch"]["power_up_d532"], "0x06")
        self.assertEqual(reward[2]["after_reward_dispatch"]["timer_d44c"], 600)
        self.assertEqual(reward[2]["after_reward_dispatch"]["sound_request_de04"], "0x84")
        self.assertEqual(reward[2]["after_reward_dispatch"]["child"]["type"], "0x05")

    def test_lifetime_respawn_distinction(self):
        lifetime = self.cache["controlled_original_routine_fixtures"]["lifetime"]
        self.assertEqual(lifetime["untouched_off_range_before_cleanup"]["object_type"], "0xFE")
        self.assertEqual(lifetime["untouched_after_cleanup"]["occupancy_value"], "0x00")
        self.assertTrue(lifetime["untouched_after_cleanup"]["can_respawn"])
        self.assertEqual(lifetime["consumed_after_conversion"]["placement_token"], 0)
        self.assertEqual(
            lifetime["consumed_after_replacement_cleanup"]["occupancy_value"],
            "0x10",
        )
        self.assertFalse(
            lifetime["consumed_after_replacement_cleanup"]["can_respawn_same_loaded_act"]
        )

    def test_cache_has_stable_format(self):
        text = CACHE.read_text(encoding="utf-8")
        self.assertEqual(text, json.dumps(self.cache, indent=2) + "\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
