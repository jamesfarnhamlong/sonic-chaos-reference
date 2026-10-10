"""Special Stage goal ring (type $31)."""
import json, os, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'tools'))
import ss_goal_ring as T
import rom as R
ROM = Path(os.environ.get('SONIC_CHAOS_ROM', str(ROOT.parent / 'source/Sonic Chaos (Europe).sms')))


class GoalRing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.loads(T.OUT.read_text(encoding='utf-8'))

    def test_regeneration(self):
        self.assertEqual(T.OUT.read_text(encoding='utf-8'), json.dumps(T.build(R.load(ROM)), indent=2) + '\n')

    def test_contact_box(self):
        c = self.d['contact_sweep']
        for k in ('normal_8x24', 'hurt_blink_d503_40', 'invincible_d503_80'):
            self.assertEqual((c[k]['dx'], c[k]['dy'], c[k]['full_rectangle']), ([-16, 16], [-16, 24], True), k)
        self.assertEqual(c['state0F_9x24']['dx'], [-17, 17])
        self.assertTrue(c['asleep_or_hidden_ix4_bit6_blocks_collection'] and c['ix3_bit6_blocks_collection'])

    def test_effects(self):
        e = self.d['collection_effects']
        self.assertEqual([e[k]['post']['emeralds'] for k in e], [1, 3, 7, 15, 31])
        self.assertEqual(e['param4']['post']['continues'], 0)       # (0x7F+1)&0x7F
        self.assertEqual(e['param8']['post']['continues'], 1)       # bit7 cleared
        self.assertEqual(e['param16']['post']['mode'], 0xE0)
        self.assertTrue(all(v['post']['card'] == 255 and v['post']['slot_type'] == 255 for v in e.values()))

    def test_success_wins_over_simultaneous_failure(self):
        w = self.d['whole_game']['success_and_failure_flags_together']
        self.assertEqual((w['emeralds'], w['card'], w['continues']), (1, 255, 1))


if __name__ == '__main__':
    unittest.main()
