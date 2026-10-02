#!/usr/bin/env python3
"""Cache locks plus focused ROM-backed footwear boundary checks."""
import hashlib
import importlib.util
import json
import os
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM_SHA = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
CACHE = ROOT / "data" / "rom-cache" / "powerup-shoes.json"
D = json.loads(CACHE.read_text(encoding="utf-8"))
spec = importlib.util.spec_from_file_location("powerup_shoes", ROOT / "tools" / "powerup_shoes.py")
ps = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ps)


def matching_rom():
    candidates = []
    if os.environ.get("SONIC_CHAOS_ROM"):
        candidates.append(Path(os.environ["SONIC_CHAOS_ROM"]))
    candidates += [ROOT.parent / "source" / "Sonic Chaos (Europe).sms", ROOT / "Sonic Chaos (Europe).sms"]
    for path in candidates:
        if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == ROM_SHA:
            return path
    return None


ROM_PATH = matching_rom()


class CacheTests(unittest.TestCase):
    def test_identity(self):
        self.assertEqual(D["rom_sha256"], ROM_SHA)
        self.assertEqual(D["identities"]["rocket_shoes"], {
            "object": "0x10", "parameter": "0x04", "reward_mask": "0x08",
            "selector_d532": "0x04", "player_state": "0x11",
            "timer": "D44C", "duration_copy": "D3A1",
        })
        spring = D["identities"]["spring_shoes"]
        self.assertEqual((spring["object"], spring["parameter"], spring["player_state"]), ("0x2F", "0x00", "0x12"))
        self.assertIsNone(spring["timer"])
        self.assertIsNone(spring["selector_d532"])

    def test_placement_totals_and_variants(self):
        self.assertEqual(D["placements"]["totals"], {"rocket_shoes": 11, "spring_shoes": 16})
        self.assertEqual(len(D["placements"]["acts"]), 18)
        self.assertEqual({r["parameter"] for r in D["placements"]["rocket_shoes"]}, {"0x04"})
        self.assertEqual({r["parameter"] for r in D["placements"]["spring_shoes"]}, {"0x00"})
        self.assertEqual({r["aux0"] for r in D["placements"]["spring_shoes"]}, {"0x94", "0xAC"})

    def test_rocket_control_and_ring_contract(self):
        self.assertIn("ORs held Left/Right", D["rocket_shoes"]["movement"]["horizontal"])
        self.assertIn("oscillate", D["rocket_shoes"]["movement"]["vertical_sweep"]["rule"])
        self.assertIn("state-independent", D["rocket_shoes"]["rings"]["type_09"])
        self.assertIn("26-state", D["rocket_shoes"]["rings"]["terrain"])
        self.assertEqual(D["rocket_shoes"]["rings"]["fixtures"]["model_mismatches"], 0)

    def test_spring_shoes_are_attachment_not_timed_reward(self):
        self.assertIn("No timer", D["spring_shoes"]["duration"])
        self.assertIn("inherit", D["spring_shoes"]["attack_and_hazards"])
        self.assertIn("No multiplication/addition", D["spring_shoes"]["canonical_springs"])
        floor = [r for r in D["spring_shoes"]["movement"]["bounce_sweep"]["rows"] if r["contact_bits"] == "0x02"]
        self.assertTrue(floor)
        self.assertTrue(all(r["vy"] == -0x780 and r["sound"] == "0xC2" for r in floor))

    def test_monitor_order_classification(self):
        self.assertTrue(D["monitor_spin_dash"]["classification"].startswith("D:"))
        rows = D["monitor_spin_dash"]["rows"]
        top_spin = [r for r in rows if r["requested_state"] == "0x10" and r["edge"] == "top" and r["vy"] == 256]
        side_spin = [r for r in rows if r["requested_state"] == "0x10" and r["edge"] == "side" and r["vy"] == 256]
        self.assertEqual(top_spin[0]["object_type_after"], "0x10")
        self.assertEqual(side_spin[0]["object_type_after"], "0x0F")

    def test_replacement_matrix(self):
        rows = {r["case"]: r for r in D["coexistence"]["fixtures"]["rows"]}
        self.assertEqual((rows["rocket_over_invincibility"]["selector"], rows["rocket_over_invincibility"]["timer"]), ("0x04", 300))
        self.assertEqual((rows["invincibility_over_rocket"]["selector"], rows["invincibility_over_rocket"]["requested_state"]), ("0x06", "0x11"))
        self.assertEqual((rows["spring_shoes_over_rocket"]["selector"], rows["spring_shoes_over_rocket"]["requested_state"]), ("0x04", "0x12"))

    def test_counts_and_routine_hashes(self):
        self.assertEqual(D["counts"]["controlled_routine_cases"], 132)
        self.assertEqual(D["counts"]["model_mismatches"], 0)
        for row in D["routines"].values():
            self.assertEqual(len(row["sha256"]), 64)
            self.assertLessEqual(len(row["first_16_bytes"]), 32)


@unittest.skipUnless(ROM_PATH, "canonical ROM not found")
class RomBackedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM_PATH.read_bytes()

    def test_full_cache_regeneration(self):
        self.assertEqual(D, ps.build(self.rom))

    def test_unseen_vertical_boundaries(self):
        for pad, before, expected in ((0, 0x0010, -0x10), (0, 0xFFF0, 0x10), (1, 0xFC01, -0x400), (2, 0x03FF, 0x400)):
            from oracle import Oracle
            o = Oracle(self.rom)
            o.mem[0xD137] = pad
            o.word(0xD518, before)
            o.call(0x3AC1)
            self.assertEqual(ps.s16(o.word(0xD518)), expected)

    def test_placement_regeneration(self):
        fresh = ps.placement_census(self.rom)
        self.assertEqual(fresh["totals"], {"rocket_shoes": 11, "spring_shoes": 16})
        self.assertEqual(fresh, D["placements"])


if __name__ == "__main__":
    unittest.main()
