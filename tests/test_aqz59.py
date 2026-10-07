"""AQZ3 boss original routines, complete fight/replay and approved frame coverage."""
import json,os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import aqz59_runtime as A
import aqz59_game as G
import aqz_foundation as F
import level_package as L
ROM=Path(os.environ.get('SONIC_CHAOS_ROM',str(ROOT.parent/'source/Sonic Chaos (Europe).sms')))
class Boss(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.r=L.load_rom(ROM);cls.v=A.build(cls.r);cls.g=G.build(cls.r)
 def test_rom_sources_and_reproduction(self):
  self.assertEqual(L.sha256(self.r),L.ROM_SHA256)
  for p,v in ((A.OUTPUT,self.v),(G.OUTPUT,self.g)):self.assertEqual(p.read_text(encoding='utf-8'),F.dumps(v))
  for v in self.v['source_hashes'].values():self.assertEqual(L.sha256(self.r[v['file']:v['file']+v['length']]),v['sha256'])
 def test_placement_state_graph_and_natural_reachability(self):
  p=self.v['placement'];self.assertEqual((p['rom_offset'],p['world_x'],p['world_y'],p['parameter'],p['placement_token']),('0x71630',1856,238,'0x00',1))
  self.assertEqual([self.v['state_graphs'][f'0x{t:02X}']['state_count'] for t in range(89,94)],[21,5,2,6,2])
  for c in self.g['cases']:
   if c['name'].startswith('fight'):self.assertEqual(c['states'],sorted(set(range(21))-{4}))
 def test_eleven_hits_and_separate_rebound(self):
  self.assertEqual(self.v['contracts']['boss']['damaging_contacts'],11)
  for c in self.g['cases']:
   if c['name'].startswith('fight'):self.assertEqual([v['hp'] for v in c['marks'] if v['event']=='hp_hit'],list(range(10,-1,-1)))
  for v in self.v['contacts']['posture']:
   if v['attack'] and not v['hurt'] and tuple(v['point'])==(0,-64) and v['cooldown']==16:
    self.assertEqual(v['result']['hp'],v['hp']);self.assertEqual(v['result']['player']['requested'],27)
 def test_child_parameter6_adjacent_data_and_six_completion_gate(self):
  ps=self.v['boundaries']['5c_parameters'];self.assertEqual([v['wait'] for v in ps],[16,48,80,112,144,176,208])
  self.assertEqual((ps[6]['camera_offsets'],ps[6]['initial_angle'],ps[6]['angle_step']),([-400,-400],217,-82))
  for c in self.g['cases']:
   if c['name'].startswith('fight'):
    self.assertEqual({v['parameter'] for v in c['marks'] if v['event']=='5c_delay_setup'},set(range(7)))
    self.assertEqual({v['parameter'] for v in c['marks'] if v['event']=='5c_complete'},set(range(6)))
 def test_allocator_exhaustion_is_not_repaired(self):
  c=next(c for c in self.g['cases'] if c['name']=='exhaustion');self.assertTrue(any(v['event']=='allocation_failure' for v in c['marks']));self.assertEqual(c['rows'][-1]['o'][0]['state'],7)
  self.assertEqual(self.v['camera_clear']['hud_allocator'][-1]['stored_pointer'],0xD940)
 def test_camera_clear_and_progression(self):
  for c in self.g['cases']:
   if c['name'].startswith('fight'):
    v=c['rows'][-1];self.assertEqual((v['zone'],v['act'],v['cur'],v['d174'],v['d176']),(5,0,5,126,752))
    arena=next(v for v in c['rows'] if v['u']==500);self.assertEqual([arena['d174'],arena['d176']],[1727,78])
  self.assertEqual(self.v['camera_clear']['next_start'],[238,864,126,752])
 def test_complete_restore_and_posture_fixtures(self):
  self.assertTrue(self.g['replay_identical']);self.assertGreater(self.g['complete_cpu_state_bytes'],30)
  for c in self.g['cases']:
   if c['name'] in ('nonattack','invincibility','hurt'):self.assertFalse(any(v['event']=='hp_hit' for v in c['marks']))
   if c['name']=='blink':self.assertTrue(any(v['event']=='hp_hit' for v in c['marks']))
 def test_approved_compositions_cover_live_frames(self):
  art=json.loads((F.OUT/'art-approval.json').read_text());approved={v['type']:{f['frame'] for f in v['frames']} for v in art['subjects'].values() if v['type']>=89}
  for c in self.g['cases']:
   for row in c['rows']:
    for o in row['o']:
     if o['type'] in approved:self.assertIn(o['frame'],approved[o['type']])
  self.assertEqual(art['status'],'APPROVED')
def tearDownModule():print('AQZ A5 original-routine assertions:',sum(A.COUNTS.values()))
if __name__=='__main__':unittest.main()
