import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import eez_foundation as F
import eez_allocations as A
import eez_reuse as R
import level_package as L

class Reuse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.r=L.load_rom(ROOT.parent/'source/Sonic Chaos (Europe).sms')
    def test_allocation_reward(self):
        v=A.build(self.r);self.assertEqual(v['assertions'],574)
        self.assertEqual((F.OUT/'allocation-checks.json').read_text(encoding='utf-8'),F.dumps(v))
    def test_shared_reuse(self):
        v=R.build(self.r);self.assertEqual(v['assertions'],44)
        self.assertEqual((F.OUT/'shared-reuse.json').read_text(encoding='utf-8'),F.dumps(v))

if __name__=='__main__':unittest.main()
