import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import eez_foundation as F
import eez_terrain_closure as T
import eez_boss as B
import eez_ending as E
import level_package as L

class Closure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.r=L.load_rom(ROOT.parent/'source/Sonic Chaos (Europe).sms')
    def test_surface_replacement_effects(self):
        v=T.build(self.r);self.assertEqual(v['checks'],202)
        self.assertEqual((F.OUT/'terrain-effects.json').read_text(encoding='utf-8'),F.dumps(v))
    def test_boss_boundaries_endgame(self):
        v=B.build(self.r);self.assertEqual(v['assertions'],357532)
        self.assertEqual((F.OUT/'boss-endgame-recon.json').read_text(encoding='utf-8'),F.dumps(v))
    def test_complete_ending_scripts(self):
        v=E.build(self.r)
        self.assertEqual((F.OUT/'ending-scripts.json').read_text(encoding='utf-8'),F.dumps(v))
        self.assertTrue(all(s['cleanly_terminated'] for sc in v['scripts'].values() for s in sc['states']))
        self.assertGreater(len(v['scripts']['0x01']['states'][0]['ops']),80)

if __name__=='__main__':unittest.main()
