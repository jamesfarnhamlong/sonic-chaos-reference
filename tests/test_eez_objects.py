import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import eez_foundation as F
import eez_objects as O
import eez_carrier as C
import rom as R

class Objects(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.r=R.load(ROOT.parent/'source/Sonic Chaos (Europe).sms')
    def test_ordinary_sweeps(self):
        v=O.build(self.r);self.assertEqual(v['assertions'],10718)
        self.assertEqual((F.OUT/'objects-36-39.json').read_text(encoding='utf-8'),F.dumps(v))
    def test_carrier_sweeps(self):
        v=C.build(self.r);self.assertEqual(v['checks'],32470)
        self.assertEqual((F.OUT/'carrier-17.json').read_text(encoding='utf-8'),F.dumps(v))

if __name__=='__main__':unittest.main()
