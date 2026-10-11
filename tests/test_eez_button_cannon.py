import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import eez_foundation as F
import eez_button_cannon as B
import rom as R

class ButtonCannon(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.r=R.load(ROOT.parent/'source/Sonic Chaos (Europe).sms')
    def test_cache_reproduces_from_original_rom(self):
        v,_=B.build(self.r);self.assertEqual((F.OUT/'button-cannon.json').read_text(encoding='utf-8'),F.dumps(v))
    def test_no_rearm(self):
        v=json.loads((F.OUT/'button-cannon.json').read_text())
        self.assertEqual(v['S1_stand']['alloc16'],1);self.assertEqual(v['S1_stand']['cell0_after'],'0xb2')
        self.assertEqual(len(v['S2_offscreen_return']['floor_hits']),2)
        self.assertEqual(v['S4_reload']['cell0_after_loader'],'0xb1')

if __name__=='__main__':unittest.main()
