"""S4 contracts and original-ROM regression oracles; no POC writes."""
import json
import os
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import sez_enemies_20_23 as A
import rom as R
D=json.loads(A.OUTPUT.read_text(encoding='utf-8'))
ROM=Path(os.environ.get('SONIC_CHAOS_ROM',str(ROOT.parent/'source/Sonic Chaos (Europe).sms')))

class Contracts(unittest.TestCase):
    def test_rom_and_coverage(self):
        self.assertEqual(D['rom_sha256'],R.SHA256)
        self.assertEqual(D['rom_bytes'],524288)
        ids=[(p['act'],p['index']) for p in D['placements']]
        self.assertEqual(ids,[('sez1',i) for i in range(31,39)]+[('sez2',i) for i in range(26,33)])
        self.assertEqual([(p['act'],p['index']) for p in D['whole_game']],ids)
        self.assertEqual(D['assertion_total'],sum(D['assertions'].values()))
        self.assertGreater(D['assertion_total'],65000)
        self.assertEqual(D['contract']['unresolved'],[])

    def test_frame_dependent_geometry(self):
        for key,x,y in (('0x20',15,20),('0x23',17,26),('0x23_frame2',15,20)):
            c=D['contact'][key]
            self.assertEqual(c['normal_box'],dict(x=[-x,x],y=[-y,24]))
            self.assertEqual(c['state_0f_box'],dict(x=[-x-1,x+1],y=[-y,24]))
            for v in c['reactions']:
                expected=15 if not v['f3']&64 and (v['f3']&2 or v['d532']==6) else int(key[:4],16)
                self.assertEqual(v['type'],expected)
                if expected==15:self.assertEqual((v['token'],v['score_bcd']),(0,[16,0,0]))
        rest=next(v for v in D['motion_terrain']['animation_vectors'] if v['type']==35 and v['state']==2)
        self.assertEqual(rest['extents'][:12],[[7,20]]*12)
        self.assertEqual(rest['extents'][12:16],[[9,26]]*4)

    def test_parameter_timer_and_probe(self):
        m=D['motion_terrain']
        self.assertEqual(m['parameter_equivalence']['parameters'],list(range(256)))
        self.assertEqual(D['assertions']['terrain_trigger'],512)
        for v in m['timer_vectors']:
            self.assertEqual(v['output']['timer'],(v['input']-1)&255)
            self.assertEqual(v['output']['requested'],4 if v['input']==1 else 3)
        self.assertEqual([v['block'] for v in m['trigger_vectors'] if v['trigger']],[71,246,247])
        self.assertEqual(len(m['landing_blocks']),256)
        self.assertEqual(len(m['unusual_terrain_floor']),256)

    def test_terrain_prevents_one_signature(self):
        c=D['natural_signature_comparison']
        self.assertFalse(c['0x20']['coordinate_independent'])
        self.assertFalse(c['0x23']['coordinate_independent'])
        self.assertEqual(sorted(len(v) for v in c['0x23']['groups'].values()),[1,1,6])
        unusual=next(v for v in D['controlled_placements'] if v['act']=='sez2' and v['index']==31)
        self.assertEqual([(v['u'],v['y']) for v in unusual['transitions'][3:5]],[(168,240),(191,240)])

    def test_lifecycle_and_conversion(self):
        self.assertFalse(D['lifecycle']['keepalive'])
        self.assertFalse(D['lifecycle']['player_distance_removal'])
        for v in D['lifecycle']['vectors']:
            self.assertEqual(v['type_after'],254 if not -96<=v['relative']<352 else v['type'])
            self.assertEqual(v['asleep'],not -32<=v['relative']<288)
        self.assertEqual(D['interaction']['shared_player_handler']['model_mismatches'],0)
        for v in D['interaction']['smoke']:
            self.assertEqual((v['timeline'][-1]['u'],v['timeline'][-1]['type']),(40,255))
        self.assertEqual(D['assertions']['restore_history_independence'],2)
        self.assertEqual(D['assertions']['whole_recreated'],2)
        self.assertEqual(D['assertions']['whole_defeated_not_recreated'],2)

    def test_first_movement_and_order(self):
        for p in D['whole_game']:
            initial=p['first']['enemy']
            rows={v['u']:v for v in p['vectors']}
            first_move=5 if initial['type']==32 else 4
            self.assertEqual(rows[first_move-1]['enemy']['x'],initial['x'])
            self.assertLess(rows[first_move]['enemy']['x'],initial['x'])
            events=rows[first_move]['events']
            cb='20walk' if initial['type']==32 else '23leap'
            self.assertLess(events.index('objects'),events.index('enemy_engine'))
            self.assertLess(events.index('enemy_engine'),events.index(cb))

    def test_manifest_current(self):
        d=json.loads((ROOT/'data/rom-cache/sez/implementation-manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(next(v for v in d['implementation_packages'] if v['id']=='S4')['research_status'],'CLOSED')
        self.assertEqual(d['enemy_runtime']['placements'],15)

@unittest.skipUnless(ROM.is_file(),'local-only ROM unavailable')
class OriginalRom(unittest.TestCase):
    def test_controlled_regeneration(self):
        fresh=A.build(R.load(ROM),include_game=False)
        for k,v in fresh.items():
            if k not in ('assertions','assertion_total'):self.assertEqual(json.loads(json.dumps(v)),D[k],k)
        print('S4 controlled assertions:',fresh['assertion_total'])

if __name__=='__main__':unittest.main()
