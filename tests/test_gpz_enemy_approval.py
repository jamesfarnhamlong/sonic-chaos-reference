"""ROM/cache regressions, including exhaustive overlap and patrol initialization."""
import json,os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import gpz_enemy_approval as G
import rom as R
import gpz_approval_manifest as P

class ApprovalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cache=json.loads(G.CACHE.read_text())
        path=os.environ.get('SONIC_CHAOS_ROM')
        cls.rom=R.load(path) if path else None

    def test_placements_and_reuse(self):
        counts={k:[sum(int(v['type_id'],16)==t for v in rows) for t in (0x25,0x2C,0x51)]
                for k,rows in self.cache['placements'].items()}
        self.assertEqual([counts[k] for k in ('gpz1','gpz2','gpz3')],[[5,4,0],[7,3,0],[0,0,1]])
        self.assertEqual(counts['eez1'][1],1);self.assertEqual(counts['eez2'][1],8)

    def test_boxes_and_attack_airborne_distinction(self):
        for key,bounds in (('37',[-15,15,-17,24]),('44',[-20,20,-16,24])):
            result=self.cache['types'][key]['contact']
            self.assertEqual(result['grid_mismatches'],0);self.assertEqual(result['bounds'],bounds)
            for row in result['reaction_cases']:
                want=(row['posture']&0x40)==0 and (row['posture']&2 or row['invincibility']==6)
                self.assertEqual(row['type_after']==0x0F,bool(want))
                if want:self.assertEqual(row['placement_token'],0)
                self.assertEqual(row['occupancy'],int(key))

    def test_sources_palette_frames_and_chain(self):
        ts=self.cache['types'];self.assertEqual(ts['37']['mapping']['frame_count'],3)
        self.assertEqual(ts['44']['mapping']['frame_count'],3)
        self.assertEqual(ts['81']['mapping']['frame_count'],12)
        self.assertEqual(ts['81']['palette_index'],13)
        self.assertEqual(ts['81']['dynamic_load']['selector'],20)
        self.assertEqual([e['tile_count'] for e in ts['81']['dynamic_load']['entries']],[104,12])
        self.assertEqual(ts['52']['bases']['normal'],150)
        self.assertEqual([v['type'] for v in ts['81']['required_spawns'][:4]],[81]*4)
        self.assertEqual(len(ts['81']['controlled_composition']['children']),3)
        self.assertEqual(ts['81']['controlled_composition']['parent_frame'],2)
        self.assertEqual(ts['37']['controlled_context']['placement_anchor'],[848,334])
        self.assertEqual(ts['37']['controlled_context']['projected_anchor'],[848,302])

    def test_live_boundary_oracles(self):
        if self.rom is None:self.skipTest('set SONIC_CHAOS_ROM for live original routines')
        got=G.movement_checks(self.rom)
        self.assertEqual(got,self.cache['controlled_movement'])
        for t in (37,44):
            info=self.cache['types'][str(t)]
            self.assertEqual(G.contacts(self.rom,t,info['init']['extent_x'],info['init']['extent_y']),info['contact'])

    def test_regenerated_cache(self):
        if self.rom is None:self.skipTest('set SONIC_CHAOS_ROM for live original routines')
        self.assertEqual(G.build(self.rom),self.cache)

    def test_final_approval_and_frozen_manifest(self):
        d=json.loads(P.CACHE.read_text())
        self.assertEqual(d['approved_types'],['$25','$2C','$51','$34','$0A','$0F'])
        self.assertEqual(len(d['images']),69)
        self.assertEqual(len(d['approved_runtime_frames']),26)
        self.assertEqual(len(d['superseded_boss_images']),26)
        self.assertEqual(sum(v['path'].startswith('build/gpz-enemy-approval/') for v in d['images']),41)
        self.assertTrue(all(P.eligible(v) for v in d['approved_runtime_frames']))
        self.assertTrue(all(not v.startswith('build/gpz-enemy-approval/type-51-') for v in d['approved_runtime_frames']))
        self.assertTrue(all(self.cache['subject_approvals'][k].endswith('APPROVED BY USER') for k in ('37','44','81','52','10','15')))

if __name__=='__main__':unittest.main(verbosity=2)
