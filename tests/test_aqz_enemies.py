"""AQZ A4 original enemy routines, all-placement scheduler and restore checks."""
import json
import os
import sys
import unittest
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import aqz_enemies as E
import aqz_enemies_game as G
import aqz_foundation as F
import level_package as L
ROM=Path(os.environ.get('SONIC_CHAOS_ROM',str(ROOT.parent/'source/Sonic Chaos (Europe).sms')))

class Enemies(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.r=L.load_rom(ROM);cls.v=E.build(cls.r);cls.g=G.build(cls.r)
    def test_rom_sources_and_reproducible_caches(self):
        self.assertEqual(L.sha256(self.r),L.ROM_SHA256)
        for path,value in [(E.OUTPUT,self.v),(G.OUTPUT,self.g)]:self.assertEqual(path.read_text(encoding='utf-8'),F.dumps(value))
        for x in self.v['source_regions'].values():self.assertEqual(L.sha256(self.r[x['file']:x['file']+x['length']]),x['sha256'])
    def test_authoritative_census_and_all_natural_loader_coverage(self):
        expected=E.placements(self.r);self.assertEqual([x['placement'] for x in self.v['placements']],expected)
        self.assertEqual([x['placement'] for x in self.g['placements']],expected)
        self.assertEqual(Counter((x['act'],x['type_id'],x['parameter']) for x in expected),Counter({(0,'0x3C','0x00'):7,(0,'0x3C','0x01'):1,(1,'0x3C','0x00'):2,(1,'0x3C','0x01'):1,(0,'0x3D','0x00'):3,(0,'0x3D','0x04'):3,(0,'0x3D','0x08'):3,(1,'0x3D','0x00'):5,(1,'0x3D','0x04'):3,(1,'0x3D','0x08'):2}))
    def test_3c_integer_legs_dwell_and_parameter_offset(self):
        for p in self.v['placements']:
            if p['placement']['type_id']!='0x3C':continue
            rows=p['rows'];rec=p['placement'];base=rec['world_y']+(12 if rec['parameter']=='0x01' else 0)
            self.assertEqual(rows[4]['y'],base+(16 if rec['parameter']=='0x01' else -16))
            self.assertEqual(rows[72]['y'],base)
            self.assertTrue(all(x['fractions']==[0,0] and x['vx']==0 and x['vy']==0 for x in rows))
    def test_contact_cadence_and_asleep_order(self):
        rows=self.v['boundaries']['3c_parity_sleep'];self.assertEqual(len(rows),24)
        for x in rows:self.assertEqual(x['output']['D3B0'],255 if not x['sleep'] and not x['clock']%2 else 0)
        self.assertEqual(self.v['assertions']['3c_motion_before_gate'],1536)
    def test_3d_initializer_delays_and_origin_counter(self):
        self.assertEqual(len(self.v['boundaries']['3d_parameter_init']),256)
        self.assertEqual(len(self.v['boundaries']['3d_origin_counter']),980)
        for parameter,request_u in [('0x00',1),('0x04',5),('0x08',9)]:
            p=next(x for x in self.v['placements'] if x['placement']['type_id']=='0x3D' and x['placement']['parameter']==parameter)
            self.assertEqual(next(x['u'] for x in p['rows'] if x['requested']==1),request_u)
    def test_frame_extents_and_approved_mapping_frames(self):
        self.assertEqual(self.v['animation']['3C_frame_extents'],[dict(frame=0,extent=[0,0]),dict(frame=1,extent=[3,13]),dict(frame=2,extent=[3,13])])
        self.assertEqual(self.v['animation']['3D_frame_extents'],[dict(frame=0,extent=[0,0])]+[dict(frame=i,extent=[3,21]) for i in range(1,5)])
        meta=json.loads((F.OUT/'art-approval.json').read_text(encoding='utf-8'));self.assertEqual(meta['status'],'APPROVED')
    def test_contact_damage_defeat_rebound_and_spent_occupancy(self):
        self.assertEqual(self.v['assertions']['contact_type'],27648)
        self.assertEqual(self.v['assertions']['player_damage_request'],8192)
        rows=self.v['player_outcomes']
        self.assertTrue(any(x['type']==60 and x['f3']==3 and x['requested']==30 for x in rows))
        self.assertTrue(any(x['type']==61 and x['f3']==3 and x['current']==9 and x['dy']<0 and x['vy']==-768 for x in rows))
        for c in self.g['cases']:
            if c['placement']['type_id']=='0x3D':self.assertFalse(any(o['type']==61 for x in c['cases']['defeat_backtrack'][80:] for o in x['o']))
    def test_waterline_and_raster_independence(self):
        self.assertEqual(self.v['assertions']['water_visual_independence'],512)
        self.assertEqual(self.v['code_scans']['3D']['ram_references'],{})
        self.assertEqual(self.v['code_scans']['3C']['ram_references'],{'frameCounter':1})
        self.assertEqual(sum('waterline_probe' in x['cases'] for x in self.g['cases']),6)
    def test_natural_cases_complete_restore_and_review_status(self):
        self.assertEqual(self.g['row_count'],15032);self.assertEqual(self.g['complete_snapshot_replay_acts'],[0,1])
        self.assertEqual(len(self.g['cases']),10)
        manifest,census,_=F.build(self.r);self.assertEqual(manifest['enemies_runtime']['status'],'A4_ACCEPTED')
        for act in census['acts'].values():
            for rec in act['records']:
                if rec['type_id'] in ('0x3C','0x3D'):self.assertEqual(rec['classification'],'AQZ_SPECIFIC_RECOVERED')

def tearDownModule():
    v=json.loads(E.OUTPUT.read_text(encoding='utf-8'));g=json.loads(G.OUTPUT.read_text(encoding='utf-8'))
    print('AQZ A4 original-routine assertions',v['assertion_total'],'whole-game rows',g['row_count'])
if __name__=='__main__':unittest.main()
