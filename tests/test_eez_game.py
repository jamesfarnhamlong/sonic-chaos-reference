"""Opt-in original full-game cache reproduction for milestone batch validation."""
import os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import eez_foundation as F
import eez_boss_game as B
import eez_system_game as S
import eez_transport_game as T
import level_package as L

@unittest.skipUnless(os.environ.get('SONIC_CHAOS_FULL_EEZ')=='1','set SONIC_CHAOS_FULL_EEZ=1 for original whole-game batch')
class Game(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.r=L.load_rom(ROOT.parent/'source/Sonic Chaos (Europe).sms')
    def test_boss_chain_sonic_partial(self):self.compare('boss-game-checks.json',B.build(self.r))
    def test_boss_chain_sonic_full(self):self.compare('boss-game-flags-31.json',B.build(self.r,31))
    def test_other_character_ending(self):self.compare('boss-game-character2.json',B.build(self.r,character=2))
    def test_second_parent_both_escape_routes(self):
        for angle in (0,1):self.compare(f'boss-game-delay2000-angle{angle}.json',B.build(self.r,delay=2000,angle=angle))
    def test_system_scheduler(self):self.compare('system-game-checks.json',S.build(self.r))
    def test_transport_update_order(self):self.compare('transport-game-checks.json',T.build(self.r))
    def compare(self,name,value):self.assertEqual((F.OUT/name).read_text(encoding='utf-8'),F.dumps(value))

if __name__=='__main__':unittest.main()
