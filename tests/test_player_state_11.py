import sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from player_state_11 import build

class State11AndWindowsDiscrepancies(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=build((ROOT.parent/'Sonic Chaos (Europe).sms').read_bytes())
    def test_anchor_path(self):
        rows=self.report['type_10_vertical']['placements']
        self.assertEqual([(r['sprite_top'],r['sprite_bottom']) for r in rows],
                         [(822,853),(470,501),(246,277),(86,117),(662,693)])
    def test_state_11(self):
        p=self.report['player_state_11']
        self.assertEqual([x['frame'] for x in p['script']],['0x38','0x39','0x3A','0x39'])
        self.assertEqual(p['fixtures']['expiry']['requested_state'],'0x0E')
        self.assertEqual([x['after'] for x in p['fixtures']['acceleration']],
                         [224,-224,-64,64,-1024,1024])
    def test_spike_header(self):
        s=self.report['static_spikes']
        self.assertEqual(s['header_flags'],'0x85')
        self.assertEqual(s['floor_profile'],[16]*32)
        self.assertEqual(s['side_profile'],[64]*16+[96]*16)
    def test_overlap_boundaries(self):
        rows={(x['dx'],x['dy']):x['overlap'] for x in self.report['type_21_contact']['boundaries']}
        self.assertFalse(rows[-21,0]);self.assertTrue(rows[-20,0]);self.assertFalse(rows[21,0])
        self.assertFalse(rows[0,-27]);self.assertTrue(rows[0,-26]);self.assertTrue(rows[0,18]);self.assertFalse(rows[0,19])

if __name__=='__main__': unittest.main()
