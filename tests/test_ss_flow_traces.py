"""Special Stage entry/exit whole-game traces: determinism and invariants."""
import json, os, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'tools'))
import ss_flow_traces as T
import rom as R
ROM = Path(os.environ.get('SONIC_CHAOS_ROM', str(ROOT.parent / 'source/Sonic Chaos (Europe).sms')))


class Traces(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.loads(T.OUT.read_text(encoding='utf-8'))

    def test_regeneration(self):
        self.assertEqual(T.OUT.read_text(encoding='utf-8'), json.dumps(T.build(R.load(ROM)), indent=2) + '\n')

    def test_success(self):
        t = self.d['stage1_exits']['success']['trace']
        self.assertEqual((t[1]['mode'], t[1]['emeralds'], t[1]['card'], t[1]['continues']), (0xC0, 1, 255, 1))
        self.assertEqual(t[1]['d2a6'], t[0]['timer'][1] << 8)
        self.assertEqual((t[-1]['zone'], t[-1]['act'], t[-1]['lives'], t[-1]['emeralds']), (0, 1, 4, 1))

    def test_failures_cost_nothing_and_advance_act(self):
        for k in ('death', 'timeout'):
            t = self.d['stage1_exits'][k]['trace']
            self.assertTrue(any(x['mode'] == 0xA0 for x in t))
            self.assertEqual((t[-1]['zone'], t[-1]['act'], t[-1]['lives'], t[-1]['emeralds'], t[-1]['continues']), (0, 1, 4, 0, 0))

    def test_act_index_three_alias(self):
        q = self.d['origin_act_index_quirk']
        self.assertEqual([q[k]['final']['act'] for k in q], [1, 3, 3, 3])
        self.assertEqual([q[k]['final']['zone'] for k in q], [0, 0, 1, 5])


if __name__ == '__main__':
    unittest.main()
