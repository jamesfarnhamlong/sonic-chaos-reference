"""SEZ3 boss ROM contracts and independent original-routine regression locks."""
import json
import os
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import rom as R
import sez54_runtime as A
import sez54_fullgame as G
D=json.loads(A.OUTPUT.read_text(encoding='utf-8'))
W=json.loads(G.OUTPUT.read_text(encoding='utf-8'))
ROM=Path(os.environ.get('SONIC_CHAOS_ROM',str(ROOT.parent/'source/Sonic Chaos (Europe).sms')))

class Contracts(unittest.TestCase):
    def test_placement(self):
        p=D['static']['placement']
        self.assertEqual((p['index'],p['rom_offset'],p['world_x'],p['world_y']),(5,'0x710AE',3200,622))
        self.assertEqual([p[k] for k in ('flags','parameter','aux0','aux1')],['0x00']*4)
        self.assertEqual(D['rom_sha256'],R.SHA256)

    def test_scripts_and_reachability(self):
        self.assertEqual(D['static']['scripts']['0x54']['state_count'],13)
        self.assertEqual(D['static']['scripts']['0x55']['state_count'],4)
        self.assertEqual(D['contract']['state_graph']['boss_reachable'],list(range(13)))
        self.assertEqual(D['contract']['state_graph']['child_unreachable'],[1])
        self.assertEqual(D['static']['art']['new_approval_required'],False)

    def test_frame_geometry(self):
        for v in D['contact']['geometry']:
            oy=64 if v['frame'] in (15,16) else 80
            self.assertEqual(v['extent'],[20,oy])
            self.assertEqual(v['sonic_normal_box'],[-28,28,-oy,24])
            self.assertEqual(v['sonic_0f_box'],[-29,29,-oy,24])

    def test_hp_is_not_attack_gated(self):
        vectors=[v for v in D['contact']['posture_boundary_vectors'] if v['point']==[0,-80] and
            not v['hurt'] and not v['drop'] and v['cooldown']<=1]
        self.assertTrue(vectors)
        self.assertEqual({v['attack'] for v in vectors},{0,2})
        self.assertTrue(all(v['result']['hp']==7 for v in vectors))

    def test_zero_and_cooldown(self):
        health=D['contact']['health']
        self.assertEqual(health[0]['result']['hp'],255)
        self.assertEqual(health[0]['result']['requested'],7)
        self.assertEqual(health[1]['result']['requested'],4)
        hits=[v['hp_before'] for v in W['fight']['marks'] if v['event']=='hp_decrement']
        self.assertEqual(hits,list(range(8,0,-1)))

    def test_entry_and_escape_contact(self):
        rows=D['contact']['immune_state_vectors']
        self.assertEqual(len(rows),96)
        for v in rows:
            b=next(b for b in v['after']['slots'] if b['slot']==A.S)
            self.assertEqual(b['hp'],8)
            expected=255 if v['state']==6 and not v['attack'] and not v['hurt'] else 0
            self.assertEqual(v['after']['player']['damage'],expected)

    def test_final_hit_arbitration(self):
        rows=D['boundaries']['callback_order_final_hit']
        requests=set()
        for v in rows:
            if v['hp_before']==1 and v['state'] in (7,8,9,10):
                b=next(b for b in v['after']['slots'] if b['slot']==A.S)
                self.assertEqual((b['hp'],b['defeated']),(0,255));requests.add(b['requested'])
        self.assertEqual(requests,{4,5,7})

    def test_child_contract(self):
        self.assertEqual(D['child']['velocity_8_8'],[-768,704])
        self.assertEqual(D['child']['extents'],[2,4])
        self.assertEqual(D['child']['sonic_boxes']['normal'],[-10,10,-4,24])
        self.assertEqual(D['child']['gravity'],0)
        self.assertEqual(W['fight']['max_children'],3)
        self.assertTrue(W['fight']['children_after_final_hit'])

    def test_arena_trigger_and_camera(self):
        b=D['arena']['baseline']
        self.assertEqual(b['target'],[2976,462]);self.assertEqual(b['settled'],[2975,462])
        self.assertEqual(b['camera_right_saved'],3840)
        for dx,dy,req in D['arena']['trigger_vectors']:
            self.assertEqual(req,2 if abs(dx)<160 and abs(dy)<304 else 1)
        self.assertIsNone(b['clear_world_x_gate'])

    def test_lifecycle_and_allocator(self):
        d=D['lifecycle_feedback_allocator']
        self.assertEqual(d['allocator'][0]['boss'],d['allocator'][1]['boss'])
        self.assertEqual([v['requested'] for v in d['hud_failure']],[3,2])
        for v in d['lifecycle']:
            self.assertEqual(v['asleep'],not -32<=v['relative']<288)
            if v['keepalive']:self.assertEqual(v['after_type'],v['type'])

    def test_whole_game_completion(self):
        self.assertTrue(W['guarded_replay_identical'])
        self.assertEqual(len(W['contact_cases']),64)
        self.assertEqual([W['fight']['last'][k] for k in ('zone','act','cur')],[3,0,5])
        self.assertEqual(len([s for s in W['fight']['spawns'] if s['type']==52]),5)
        self.assertTrue(any(v['event']=='act_loader' and v['zone']==3 for v in W['fight']['marks']))

    def test_assertions_and_unresolved(self):
        self.assertEqual(D['assertion_total'],sum(D['assertions'].values()))
        self.assertGreater(D['assertion_total'],448000)
        self.assertEqual(D['contract']['unresolved'],[])

@unittest.skipUnless(ROM.exists(),'verified local-only ROM unavailable')
class OriginalROM(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.r=R.load(ROM)
    def test_regenerate_runtime(self):self.assertEqual(json.loads(json.dumps(A.build(self.r))),D)
    def test_regenerate_guarded_game(self):self.assertEqual(json.loads(json.dumps(G.build(self.r))),W)

if __name__=='__main__':unittest.main()
