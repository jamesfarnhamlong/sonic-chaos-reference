"""SEZ S3 contract locks and re-execution of original ROM oracles."""
import json
import os
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import sez_platform_28 as A
import rom as R

D=json.loads(A.OUTPUT.read_text(encoding='utf-8'))
ROM=Path(os.environ.get('SONIC_CHAOS_ROM',str(ROOT.parent/'source/Sonic Chaos (Europe).sms')))


class ContractTests(unittest.TestCase):
    def test_identity_and_counts(self):
        self.assertEqual(D['rom_sha256'],R.SHA256)
        self.assertEqual(D['rom_bytes'],524288)
        self.assertEqual(D['assertion_total'],sum(D['assertions'].values()))
        self.assertGreater(D['assertion_total'],190000)

    def test_exact_natural_placements(self):
        rows=[(r['act'],r['index'],r['world_x'],r['world_y'],r['aux1']) for r in D['placements'] if r['parameter']=='0x86']
        self.assertEqual(rows,[('sez1',4,1584,96,'0x18'),('sez1',5,2128,576,'0x30'),('sez2',2,1776,960,'0x1C')])
        self.assertEqual([(r['world_x'],r['world_y']) for r in D['placements'] if r['parameter']=='0x04'],[(1264,320)])

    def test_counter_reversal_and_restart(self):
        for row in D['movement_oracles']:
            n=row['leg_updates'];v={v['u']:v for v in row['vectors']}
            self.assertEqual(v[n]['x'],1024+n)
            self.assertEqual((v[n]['vx'],v[n]['latch']),(-256,2))
            self.assertEqual((v[2*n]['x'],v[2*n]['vx'],v[2*n]['latch']),(1024,256,0))
            self.assertEqual(v[2*n+1]['x'],1024)

    def test_trigger_differs_from_support(self):
        self.assertEqual(D['contract']['state7']['trigger']['y_inclusive'],[-16,24])
        v=next(v for v in D['trigger_oracles']['vectors'] if v['input']==dict(dx=24,dy=0,vy=0))
        self.assertEqual((v['output']['x'],v['output']['owner']),(1025,0))
        v=next(v for v in D['trigger_oracles']['vectors'] if v['input']==dict(dx=0,dy=-14,vy=-1))
        self.assertEqual((v['output']['x'],v['output']['owner']),(1025,0))

    def test_no_sag_is_not_axis_swap(self):
        traces=D['state5_comparison']['traces']
        self.assertEqual(traces['04/6A'],[0]*21)
        self.assertEqual(traces['84/6A'][:17],[1,2,3,4,5,6,7,8,8,7,6,5,4,3,2,1,0])
        for aux in ('00','18','1C','30','FF'):
            self.assertEqual(traces['04/'+aux],traces['04/6A'])
            self.assertEqual(traces['84/'+aux],traces['84/6A'])

    def test_all_natural_variants_whole_game(self):
        natural=[r for r in D['whole_game'] if 'act' in r]
        self.assertEqual([(r['act'],r['index']) for r in natural],[('sez1',2),('sez1',4),('sez1',5),('sez2',1),('sez2',2)])
        self.assertEqual([r['whole_cycle']['leg_updates'] for r in natural if 'whole_cycle' in r],[384,768,448])
        for r in natural:
            event=r['natural_first_callback']['ev']
            self.assertLess(event.index('terrain'),event.index('objects'))
            self.assertLess(event.index('objects'),event.index('s7' if r['parameter']==134 else 's5'))
        self.assertEqual(D['assertions']['restore_history_independence'],3)

    def test_lifecycle_and_viewport(self):
        self.assertEqual(D['lifecycle']['camera_scan']['viewport_ram_references'],{})
        for v in D['lifecycle']['keepalive_vectors']:
            lim=640 if v['axis']=='x' else 672
            self.assertEqual(v['type'],254 if abs(v['distance'])>=lim else 40)
        self.assertEqual({r['scenario'] for r in D['whole_game'] if 'scenario' in r},
                         {'natural_jump_off','sleep_during_motion','delete_and_recreate'})

    def test_manifest_and_census_are_current(self):
        m=json.loads((ROOT/'data/rom-cache/sez/implementation-manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(m['platform_runtime']['status'],'RESEARCHED_DATA')
        s3=next(p for p in m['implementation_packages'] if p['id']=='S3')
        self.assertEqual(s3['research_status'],'CLOSED')
        c=json.loads((ROOT/'data/rom-cache/sez/object-census.json').read_text(encoding='utf-8'))
        for r in c['platform']['platforms']:
            if r['parameter'] in ('0x04','0x86'):self.assertTrue(r['acceptance'].startswith('RESEARCHED'))


@unittest.skipUnless(ROM.is_file(),'local ROM unavailable')
class OriginalRoutineTests(unittest.TestCase):
    def test_regenerate_controlled_sections(self):
        fresh=A.build(R.load(ROM),include_game=False)
        for k,v in fresh.items():
            if k not in ('whole_game','assertions','assertion_total'):self.assertEqual(v,D[k],k)
        print('SEZ S3 controlled assertions:',fresh['assertion_total'])

    def test_regenerate_whole_game_with_restore_guard(self):
        A.COUNTS.clear()
        self.assertEqual(A.whole_game(R.load(ROM)),D['whole_game'])
        print('SEZ S3 whole-game assertions:',sum(A.COUNTS.values()))


if __name__=='__main__':unittest.main()
