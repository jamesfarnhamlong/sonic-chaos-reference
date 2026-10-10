"""Special Stage power-up census and overrides."""
import json, os, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'tools'))
import ss_powerups as T
import rom as R
ROM = Path(os.environ.get('SONIC_CHAOS_ROM', str(ROOT.parent / 'source/Sonic Chaos (Europe).sms')))


class Powerups(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.loads(T.OUT.read_text(encoding='utf-8'))

    def test_regeneration(self):
        self.assertEqual(T.OUT.read_text(encoding='utf-8'), json.dumps(T.build(R.load(ROM)), indent=2) + '\n')

    def test_census(self):
        p = self.d['placements']
        self.assertEqual(p['0x10/0x04'], {'ss1': 1, 'ss4': 5}); self.assertEqual(p['0x10/0x05'], {'ss2': 1, 'ss4': 1, 'ss5': 3})
        self.assertEqual(p['0x10/0x06'], {'ss3': 7}); self.assertEqual(p['0x2F/0x00'], {'ss2': 7})
        self.assertEqual(p['0x26/0x00'], {'ss4': 2}); self.assertEqual(p['0x26/0x01'], {'ss4': 3})

    def test_only_rocket_shoes_depend_on_zone(self):
        sw = self.d['monitor_sweep']
        self.assertEqual(sw['3']['zone0']['power_timer'], 300)
        self.assertEqual(sw['3']['deviations'], {'8': {'power_timer': [300, 6000], 'power_copy': [300, 6000], 'sound': [133, 0]}})
        for bit in ('1', '2', '4', '5'):
            self.assertEqual(sw[bit]['deviations'], {}, bit)
        self.assertEqual(sorted(sw['0']['deviations']), ['10', '11', '12', '6', '7', '8', '9'])    # 100-ring entry gate only below zone 6
        self.assertEqual(sw['4']['zone0']['clock_pause'], 11)

    def test_whole_game(self):
        c = self.d['clock_monitor_param5']
        self.assertEqual([t['d3c4'] for t in c['ticks']], list(range(11, -1, -1)))
        self.assertEqual(c['timer_frozen_at'], 0x58)
        r = self.d['rocket_shoes']
        self.assertEqual((r['ss1']['power_copy'], r['ss4']['power_copy'], r['ss4']['left_state']), (6000, 300, 0x0E))
        self.assertEqual(self.d['spring_shoes_ss2']['relaunch_vy'][0], -1920)
        s = self.d['springs_ss4']
        self.assertEqual((s['param0_1616']['d448'], s['param1_1424']['d448']), (255, 0))


if __name__ == '__main__':
    unittest.main()
