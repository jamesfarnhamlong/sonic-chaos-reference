"""Regression locks for the dedicated $51 runtime audit and original oracles."""
import json,os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import gpz51_runtime as B
import gpz51_fullgame as F
import gpz51_composition as C
import rom as R

class RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads(B.CACHE.read_text());cls.f=json.loads(F.OUTPUT.read_text())
        cls.rom=R.load(os.environ['SONIC_CHAOS_ROM']) if os.environ.get('SONIC_CHAOS_ROM') else None

    def test_geometry_all_boundaries_and_classification(self):
        self.assertEqual(self.d['contacts']['extents'],{str(n):[12,32] for n in range(4)})
        frames=self.d['contacts']['approved_frame_metadata']
        self.assertEqual([list(bytes.fromhex(v['raw_11'])[1:3]) for v in frames[1:10]],[[12,32]]*9)
        self.assertEqual(sum(v['cases'] for v in self.d['contacts']['geometry_sweeps']),5922)
        self.assertTrue(all(v['mismatches']==0 for v in self.d['contacts']['geometry_sweeps']))
        self.assertEqual([B.overlap(x,y) for x,y in ((20,0),(21,0),(0,-32),(0,-33),(0,24),(0,25))],
                         [4,0,1,0,2,0])
        # Vertical wins equal penetration; no THZ top-contact special case.
        self.assertEqual(B.overlap(12,-24),1)

    def test_five_slot_contact_mux(self):
        for v in self.d['contacts']['mux']:
            expected=(v['start']+1)%5 if v['parameter']==0 else v['start']
            self.assertEqual(v['end'],expected)
            self.assertEqual(bool(v['contact']),expected==v['parameter'])

    def test_head_vulnerability_and_rebounds(self):
        for v in self.d['head_hits']['cases']:
            hit=v['mux']==4 and bool(v['flags']&2) and not bool(v['flags']&64)
            self.assertEqual(v['contact']['requested']==13,hit)
            self.assertEqual(v['contact']['head_health'],8) # Deferred until script entry.
            if hit:
                self.assertEqual(v['player']['vy'],-1024)
                if not v['flags']&128 and v['power']==0:
                    expected=dict(top=-768,below=128,left=-1024,right=-1024)[v['region']]
                    self.assertEqual(v['after_consumer']['vy'],expected)

    def test_health_modes_and_decrement(self):
        for v in self.d['head_hits']['health_decrements']:
            self.assertEqual(v['after'],v['before']-1)
            self.assertEqual(v['requested'],14 if v['before']==1 else 13)
        for key,hp in (('mode0_left',5),('mode1_left',8),('mode2_left',10)):
            row=self.d['cycles'][key]['events'][0]
            self.assertEqual(next(s['health'] for s in row['slots'] if s['parameter']==0),hp)

    def test_reaction_duration_and_earliest_recontact(self):
        rows=self.d['head_hits']['reaction_rows']
        self.assertEqual([next(s['state'] for s in row['slots'] if s['parameter']==0) for row in rows[:55]],
                         [13]*54+[7])
        self.assertEqual([v['rows'][-1]['tick'] for v in self.d['head_hits']['recontacts']],[55,59,58,57,56])

    def test_detached_attack_still_hurts(self):
        for v in self.d['contacts']['detached_cases']:
            if v['region']!='left':continue
            expect_damage=not bool(v['flags']&64)
            self.assertEqual(v['before_consumer']['damage']==255,expect_damage)
            if expect_damage and v['power']==0 and not v['flags']&128:
                self.assertEqual(v['after_consumer']['requested'],30)
                self.assertEqual(v['after_consumer']['rings'],0)
        for v in self.d['hurt_variants']:
            if not v['detached'] or v['flags']!=2 or v['power']!=0:continue
            p=v['after_consumer']
            if v['rings']==0:
                self.assertEqual(p['requested'],31);self.assertEqual(p['vy'],-1280)
                self.assertEqual(v['consumer_stopped_at'],0x062D)
            else:
                self.assertEqual(p['requested'],30);self.assertEqual(p['invulnerability'],120)
                self.assertEqual(p['vy'],256 if v['ceiling'] else -1024)

    def test_throw_order_directions_and_regrowth(self):
        for key,states in (('mode1_left',[19,11,19]),('mode1_right',[20,15,20])):
            launches=self.d['cycles'][key]['launches'][:3]
            self.assertEqual([v['parameter'] for v in launches],[3,2,1])
            self.assertEqual([v['state'] for v in launches],states)
        self.assertEqual([v['parameter'] for v in self.d['cycles']['mode2_left']['launches'][:4]],[4,3,2,1])
        rows=self.d['cycles']['mode1_left']['rows']
        self.assertEqual([v['tick'] for v in self.d['cycles']['mode1_left']['launches'][:3]],[333,447,579])
        self.assertEqual([s['parameter'] for s in C.linked(rows[704])],[0,1,2,3])
        self.assertEqual(len([s for s in rows[602]['slots'] if s['type']==81 and s['parameter']==1]),2)
        self.assertEqual(len(self.d['throw_sweep']),360)

    def test_camera_ready_gate(self):
        for v in self.d['boundaries']['camera_ready_sweep']:
            x,y=v['camera']
            self.assertEqual(v['timer']==1,abs(x-1664)<4 and abs(y-96)<4)
        settled=self.d['cycles']['mode1_left']['rows'][232]
        self.assertEqual(settled['pan'],[1664,96])

    def test_removal_split_byte_predicates(self):
        self.assertEqual(sum(v['cases'] for v in self.d['detached_removal_sweep']),4096)
        self.assertTrue(all(v['mismatches']==0 for v in self.d['detached_removal_sweep']))
        # A farther coordinate can remain alive: these are not monotonic full words.
        rows=self.d['boundaries']['detached_removal_sweep']
        select=lambda pc,x:next(v for v in rows if v['callback']==pc and v['parameter']==1 and v['x_before']==x)
        self.assertEqual(select(0xA087,1920)['type'],255)
        self.assertEqual(select(0xA087,2048)['type'],81)

    def test_floor_gate_and_defeat_support_cascade(self):
        for v in self.d['boundaries']['floor_gate_sweep']:
            self.assertEqual(v['type']==255,bool(v['floor_flags']&2))
            self.assertEqual(v['timer_running'],255)
            if v['floor_flags']&2:
                self.assertEqual(v['requested'],32);self.assertEqual(v['limits'],[1664,1920,96])
        rows=self.d['defeat']['rows']
        first=lambda param,state:next(v['tick'] for v in rows if any(s['type']==81 and s['parameter']==param and s['state']==state for s in v['slots']))
        self.assertEqual([first(p,16) for p in (1,2,3)],[2,19,36])
        self.assertEqual([first(p,17) for p in (1,2,3)],[18,35,52])
        self.assertTrue(any(s['type']==10 and s['parameter']==0 for s in rows[290]['slots']))

    def test_complete_original_game_results_and_transition(self):
        f=self.f;marks={v['name']:v for v in f['marks']}
        self.assertEqual([v['health'] for v in f['hits']],list(range(10,0,-1)))
        self.assertEqual(marks['floor_clear_gate']['update']-f['hits'][-1]['update'],261)
        self.assertLess(marks['floor_clear_gate']['frame'],marks['state_20_handler_sets_D293_bit4_or_5']['frame'])
        self.assertLess(marks['call_32F9_results_screen']['frame'],marks['level_load_requested_15DE']['frame'])
        self.assertEqual([f['rows'][-1]['zone'],f['rows'][-1]['act']],[2,0])
        self.assertTrue(all(v['timer_running']==255 for v in f['rows'] if v['zone']==1))
        at=next(v for v in f['rows'] if v['update']==1219)
        self.assertEqual(at['limits'],[1663,1920,8,96])

    def test_original_runtime_regeneration(self):
        if self.rom is None:self.skipTest('set SONIC_CHAOS_ROM')
        self.assertEqual(B.build(self.rom),self.d)

    def test_original_fullgame_regeneration(self):
        if self.rom is None:self.skipTest('set SONIC_CHAOS_ROM')
        self.assertEqual(F.build(self.rom),self.f)

if __name__=='__main__':unittest.main(verbosity=2)
