"""Carrier-only canonical correction and original scheduler regression locks."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import eez_carrier as C
import eez_carrier_game as G
import eez_foundation as F
import level_package as L


class CarrierContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = L.load_rom(ROOT.parent/'source/Sonic Chaos (Europe).sms')
        cls.value = C.build(cls.raw)

    def test_cache_is_original_rom_reproduction(self):
        self.assertEqual((F.OUT/'carrier-17.json').read_text(encoding='utf-8'), F.dumps(self.value))
        self.assertEqual(self.value['legacy_assertions'], 32470)
        self.assertEqual(self.value['checks'], 124524)

    def test_correction_coverage(self):
        groups = self.value['correction_validation']['groups']
        self.assertEqual(groups['screen_death'], 65536)
        self.assertEqual(groups['copy'], 13728)
        self.assertEqual(groups['attached_callback'], 5376)
        self.assertEqual(groups['bounce'], 1600)
        self.assertEqual(set(groups), {'copy', 'attached_callback', 'attached_screen_death',
            'player16', 'screen_death', 'bounce', 'hurt_gate', 'invalid_owner', 'lifecycle',
            'capture_cooldown', 'capture_token', 'motion_paths', 'continuation', 'sleep',
            'gravity_sleep', 'cleanup', 'terrain_ring', 'placements'})

    def test_distinct_hurt_and_owner_lifetime_contracts(self):
        samples = self.value['correction_validation']['samples']
        self.assertEqual(samples['bounce'][0], dict(rings_bcd=0, requested=30, flags=3, immunity_ticks=37))
        self.assertEqual([r['occupancy_after_cleanup'] for r in samples['lifecycle']], [255, 0])
        self.assertEqual([r['slot_type'] for r in samples['invalid_owner']], [0, 254, 255, 40])
        self.assertTrue(all(r['retained_owner'] for r in samples['invalid_owner']))
        self.assertEqual([r['collected_rings'] for r in samples['terrain_ring']], [1, 1])

    def test_all_natural_placements_original_scheduler(self):
        v = G.build(self.raw)
        self.assertEqual((F.OUT/'carrier-game-checks.json').read_text(encoding='utf-8'), F.dumps(v))
        self.assertEqual(v['assertions'], 265)
        self.assertEqual(len(v['cases']), 10)
        self.assertEqual(sorted({(r['act'], r['index']) for r in v['cases']}),
                         [('eez1', 17), ('eez1', 18), ('eez2', 9), ('eez2', 10), ('eez3', 3)])
        self.assertEqual({r['button'] for r in v['cases']}, {16, 32})


if __name__ == '__main__':
    unittest.main()
