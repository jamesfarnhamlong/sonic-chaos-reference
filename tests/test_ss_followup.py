"""Special Stage follow-up: Large Rings, SS3 final junction, act-index-2 census, Entry Fail mechanism."""
import json, os, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'tools'))
import ss_followup as T
import rom as R
ROM = Path(os.environ.get('SONIC_CHAOS_ROM', str(ROOT.parent / 'source/Sonic Chaos (Europe).sms')))


class Followup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.loads(T.OUT.read_text(encoding='utf-8'))

    def test_regeneration(self):
        self.assertEqual(T.OUT.read_text(encoding='utf-8'), json.dumps(T.build(R.load(ROM)), indent=2) + '\n')

    def test_large_rings(self):
        lr = self.d['large_rings']
        self.assertTrue(all(p == dict(cell=0x46, rings_bcd=0x15, lives=3, mode=0x80) for p in lr['probe_results']))
        self.assertEqual(lr['wrap_past_99']['lives'], 4)
        self.assertEqual(lr['cells_per_stage'], {'ss1': 128, 'ss2': 8, 'ss3': 0, 'ss4': 0, 'ss5': 0})

    def test_ss3_single_junction_requires_up(self):
        j = self.d['ss3_final_junction']
        self.assertEqual((j['junction_block'], j['junction_count_in_stage'], j['natural_route_decisions']), (0x7A, 1, 1))
        self.assertEqual(j['decision']['pad_held'], 1)
        self.assertEqual(j['router_options']['vx=0,vy=64000'], [1, 3, 5, 7, 9, 11, 13, 15])
        self.assertEqual([k for k, v in j['counterfactual'].items() if v['reaches_emerald_room']], ['Up'])
        self.assertEqual(j['invincibility_monitors_broken_on_natural_route'], 5)

    def test_act_index_two_cannot_reach_100_rings(self):
        c = self.d['act_index2_reachability']
        self.assertFalse(c['any_act_index2_reaches_100'])
        self.assertEqual(c['act_index2_maximums'], {'zone0_act2': 19, 'zone1_act2': 19, 'zone2_act2': 42, 'zone3_act2': 83, 'zone4_act2': 14, 'zone5_act2': 0})

    def test_entry_fail_only_for_stale_tick_59(self):
        e = self.d['entry_fail']
        self.assertEqual((e['values_tested'], e['failing_values']), (60, [59]))


if __name__ == '__main__':
    unittest.main()
