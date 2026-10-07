"""AQZ A3 original routines and complete-state natural scheduler regression locks."""
import json
import os
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import aqz_platform_3f as A
import aqz_platform_game as G
import aqz_foundation as F
import level_package as L
ROM=Path(os.environ.get('SONIC_CHAOS_ROM',str(ROOT.parent/'source/Sonic Chaos (Europe).sms')))

class Platform(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.r=L.load_rom(ROM);cls.v=A.build(cls.r);cls.g=G.build(cls.r)
    def test_rom_sources_and_reproducibility(self):
        self.assertEqual(L.sha256(self.r),L.ROM_SHA256)
        self.assertEqual(A.OUTPUT.read_text(encoding='utf-8'),F.dumps(self.v))
        self.assertEqual(G.OUTPUT.read_text(encoding='utf-8'),F.dumps(self.g))
        for source in self.v['source_regions'].values():self.assertEqual(L.sha256(self.r[source['file']:source['file']+source['length']]),source['sha256'])
    def test_complete_placements_creator_and_alias(self):
        self.assertEqual([(x['placement']['rom_offset'],x['placement']['parameter']) for x in self.v['creators']],[('0x713E5','0x86'),('0x713EE','0x83'),('0x7152A','0x8B')])
        self.assertEqual(len(self.v['reuse']),2)
        self.assertTrue(all(x['updates']==1649 for x in self.v['reuse']))
    def test_state13_predicate(self):
        rows=self.v['gate_vectors'];self.assertEqual(len(rows),1620)
        self.assertTrue(any(x['param']==5 and x['zone']==4 and x['act']==1 and x['requested']==14 for x in rows))
        self.assertTrue(all(x['zone']==4 and x['act']==1 and x['vy']>=0 and not x['sleep'] for x in rows if x['requested']==14))
    def test_complete_state14_script_and_route(self):
        script=self.v['scripts']['states'][14]['ops']
        self.assertEqual([x['duration'] for x in script if x['op']=='record'],[160,64,96,128,128,224])
        for name,scale in [('awake',1),('asleep',2)]:
            row=self.v['route'][name][575];self.assertEqual((row['x'],row['y']),(2096+256*scale,669-192*scale))
            self.assertEqual(row['state'],14)
        rows=self.v['route']['awake'];self.assertEqual((rows[655]['timer'],rows[656]['fall'],rows[657]['vy']),(0,255,48))
    def test_support_geometry_velocity_owner_and_carry(self):
        self.assertEqual(self.v['assertions']['shared_geometry'],41976)
        self.assertEqual(len(self.v['callback_support']),2646)
        self.assertEqual(len(self.v['support_vectors']),147)
        self.assertEqual(self.v['assertions']['fall_sign_only_gate'],2)
        self.assertTrue(any(x['owner_in']==8 and x['owner_out']==8 for x in self.v['callback_support']))
    def test_aux_counter_and_delay(self):
        rows=self.v['variants'][0]['rows'];self.assertEqual((rows[799]['x'],rows[1599]['x']),(2928,2128))
        self.assertEqual(rows[1599]['latch'],0)
        rows=self.v['variants'][1]['rows'];self.assertEqual((rows[81]['fall'],rows[82]['vy']),(255,48))
    def test_lifecycle_water_and_approved_art(self):
        spent=self.v['route']['spent'];self.assertEqual(spent['occupancy'],1)
        self.assertEqual(self.v['scripts']['frames_used'],[0,1])
        self.assertEqual(self.v['assertions']['water_callback_identical'],3)
        self.assertEqual(self.v['contracts']['unresolved'],[])
    def test_natural_scheduler_and_complete_snapshot_replay(self):
        self.assertEqual(self.g['row_count'],2982)
        for p in self.g['placements']:
            self.assertTrue(p['replay_equal'])
            rows=p['traces']['delete_recreate'];self.assertTrue(any(not x['o'] for x in rows[30:48]))
            self.assertTrue(any(x['o'] for x in rows[75:]))
        rows=self.g['placements'][2]['traces']['rider']
        self.assertTrue(any(x['o'] and x['o'][0]['fall']==255 and x['water']==255 for x in rows))

def tearDownModule():
    v=json.loads(A.OUTPUT.read_text(encoding='utf-8'));g=json.loads(G.OUTPUT.read_text(encoding='utf-8'))
    print('AQZ A3 original-routine assertions:',v['assertion_total'],'whole-game rows:',g['row_count'])
if __name__=='__main__':unittest.main()
