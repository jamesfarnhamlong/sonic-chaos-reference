"""Special Stage progression and closure."""
import json, os, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'tools'))
import ss_progression as T
import rom as R
ROM = Path(os.environ.get('SONIC_CHAOS_ROM', str(ROOT.parent / 'source/Sonic Chaos (Europe).sms')))


class Progression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.loads(T.OUT.read_text(encoding='utf-8'))

    def test_regeneration(self):
        self.assertEqual(T.OUT.read_text(encoding='utf-8'), json.dumps(T.build(R.load(ROM)), indent=2) + '\n')

    def test_order_repeat_and_refusal(self):
        s = self.d['sequences']
        self.assertEqual(s['all_succeed']['visited_zones'], [8, 9, 10, 11, 12, None, None]); self.assertEqual(s['all_succeed']['final_bits'], 31)
        self.assertEqual(s['fail_stage2_twice']['visited_zones'], [8, 9, 9, 9, 10, 11, 12, None])
        self.assertEqual(s['fail_stage1_forever']['visited_zones'], [8, 8, 8]); self.assertEqual(s['fail_stage1_forever']['final_bits'], 0)

    def test_persistence(self):
        p = self.d['persistence']
        for k in ('death_with_lives', 'game_over_no_continue', 'game_over_with_continue'):
            self.assertEqual(p[k]['end']['emeralds'], 7, k)
        self.assertIn(7, p['game_over_no_continue']['zones_visited'])          # zone 7 is the game-over screen, not a stage
        self.assertEqual(p['game_over_with_continue']['end']['score'], [0, 0, 0])
        self.assertEqual(p['new_game_reset_2A00'], {'emeralds_after': 0, 'rings_after': 0})


if __name__ == '__main__':
    unittest.main()
