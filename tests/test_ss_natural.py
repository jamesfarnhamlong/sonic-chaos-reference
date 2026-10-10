"""Special Stage input-only natural completions and failure/return routes."""
import json, os, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'tools'))
import ss_natural as T
import rom as R
ROM = Path(os.environ.get('SONIC_CHAOS_ROM', str(ROOT.parent / 'source/Sonic Chaos (Europe).sms')))


class Natural(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.loads(T.OUT.read_text(encoding='utf-8'))

    def test_regeneration(self):
        self.assertEqual(T.OUT.read_text(encoding='utf-8'), json.dumps(T.build(R.load(ROM)), indent=2) + '\n')

    def test_completed_stages_set_exactly_their_bit_and_return_to_next_act(self):
        done = [k for k, v in self.d['stages'].items() if v['completed']]
        self.assertGreaterEqual(len(done), 3)
        for k in done:
            v = self.d['stages'][k]
            self.assertTrue(v['emerald_bits'] & v['bit_expected'])
            self.assertEqual((v['result_card'], v['continues'] >= 1), (255, True))
            self.assertEqual(v['returned_zone_act'], [0, 1])

    def test_every_stage_has_timeout_and_pit_failure_without_life_loss(self):
        for k, v in self.d['stages'].items():
            f = v['failure_routes']
            self.assertEqual((f['idle_from_start']['frame'], f['idle_from_start']['mode'], f['idle_from_start']['lives']), (3510, '0xa0', 4), k)
            self.assertEqual(f['pit_death_controlled_placement']['mode'], '0xa0', k)


if __name__ == '__main__':
    unittest.main()
