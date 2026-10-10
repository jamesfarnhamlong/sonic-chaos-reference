"""Special Stage terrain/tube reuse contracts."""
import json, os, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'tools'))
import ss_traversal as T
import rom as R
ROM = Path(os.environ.get('SONIC_CHAOS_ROM', str(ROOT.parent / 'source/Sonic Chaos (Europe).sms')))


class Traversal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.loads(T.OUT.read_text(encoding='utf-8'))

    def test_regeneration(self):
        self.assertEqual(T.OUT.read_text(encoding='utf-8'), json.dumps(T.build(R.load(ROM)), indent=2) + '\n')

    def test_surface_set(self):
        self.assertEqual(sorted(map(int, self.d['surfaces'])), [0, 1, 2, 3, 7, 9, 10, 12, 13, 19, 20, 22, 29])
        self.assertEqual(self.d['surfaces']['19']['handler'], '0x6D43')
        self.assertEqual(set(self.d['surfaces']['19']['cells']), {'ss3', 'ss5'})

    def test_tube_router_is_zone_independent(self):
        self.assertEqual(self.d['route_zone_independence'], {str(z): 15360 for z in range(8, 13)})

    def test_natural_traversal_matches_model(self):
        for k, v in self.d['natural_traversal'].items():
            self.assertTrue(v['all_match_model'], k)
            self.assertGreater(v['route_decisions'], 10, k)
            self.assertIn(33, [s['state'] for s in v['state_changes']], k)


if __name__ == '__main__':
    unittest.main()
