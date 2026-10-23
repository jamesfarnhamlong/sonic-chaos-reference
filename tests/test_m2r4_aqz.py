"""Evidence integrity and discriminating original/C controls; no Windows claim."""
import json,unittest
from pathlib import Path
D=Path(__file__).resolve().parents[1]/'data/m2r4'
def read(n):return json.loads((D/n).read_text())
class Audit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.o=read('original-game.json');cls.c=read('package-comparison.json')
        cls.p=read('palette-original.json');cls.a=read('private-checks.json')
    def test_both_acts_characters_and_directions(self):
        self.assertEqual({(f['act'],f['character'],f['direction']) for f in self.o['cases']},
            {(a,c,d) for a in (1,2) for c in (1,2) for d in (-1,1)})
        self.assertTrue(all(len(f['rows'])==len(f['starts'])==100 for f in self.o['cases']))
    def test_skim_signed_high_byte_positive_negative_controls(self):
        for r in self.p['skim_controls']:
            gate=r['dy']>=0 and r['vy']>=0 and r['attack'] and abs(r['vx']>>8)>=4
            self.assertEqual(r['result_vy'],-768 if gate else r['vy'])
            self.assertEqual(r['result_vx'],r['vx'])
        self.assertTrue(any(r['vx']==-1023 and r['result_vy']==-768 for r in self.p['skim_controls']))
        self.assertFalse(any(r['vx']==1023 and r['result_vy']==-768 for r in self.p['skim_controls']))
    def test_every_movement_phase_is_paired(self):
        for f,cf in zip(self.o['cases'],self.c['shared']):
            self.assertEqual(f['id'],cf['id']);original={(r[0],r[1]):r for r in f['phases']}
            for s in cf['comparisons']:
                for r in s['phases']:self.assertEqual(r,original[(r[0],r[1])])
    def test_post_terrain_mismatches_remain_visible(self):
        differences=[r for f in self.c['shared'] for r in f['comparisons'] if r['differences']]
        self.assertTrue(differences)
        self.assertFalse(any('vx' in r['differences'] or 'vy' in r['differences'] for r in differences))
    def test_actual_archive_and_expected_decoder(self):
        self.assertEqual(self.a['archive_sha256'],'321bcd86b2daa5539485f17107f037c843a7902267db514b16d22864ef556964')
        for r in self.c['palette']:self.assertEqual(r['decoder'],0 if r['character']==2 else 1)
    def test_palette_not_identical_for_tails(self):
        self.assertEqual(len(self.a['tails']),88)
        self.assertTrue(all(x['changed_from_above_pixels']['split']>x['opaque_count']/2 for x in self.a['tails']))
        self.assertNotEqual(self.p['sources']['split_irq_cram'],self.p['sources']['fully_submerged_cram'])
    def test_cut_rows_and_modes(self):
        for r in self.c['palette']:
            if 0<r['delta']<=192:
                self.assertEqual(r['mode'],2);self.assertEqual(r['cut'],r['delta']+1)
                for y in r['rows']:self.assertEqual(y['lookup'],'split' if y['screen_y']>=r['cut'] else 'above')
            elif r['prior']:
                self.assertEqual(r['mode'],1 if r['delta']==0 else 0)
        self.assertEqual(self.c['aqz3']['mode'],0)
    def test_real_sprite_straddle_and_bottom_clipping(self):
        crossing=self.a['actual_sprite_crossings']
        self.assertEqual({x['character'] for x in crossing},{1,2})
        self.assertTrue(any('above' in x['selected_opaque_rows'] and 'split' in x['selected_opaque_rows'] for x in crossing))
        for r in crossing:
            if r['delta'] in (191,192):self.assertEqual(r['visible_opaque_pixels']['192'].get('split',0),0)
    def test_complete_and_divergent_source_runs_are_separate(self):
        self.assertEqual({f['width'] for f in self.c['free_runs']},{256,348})
        self.assertTrue(any(f['first_difference'] for f in self.c['free_runs']))
        self.assertTrue(all(not f['first_difference'] for f in self.c['free_runs'] if f['id'].startswith('a2-')))
    def test_original_irq_restores_saved_cram(self):
        controls=self.p['original_irq_restore']
        self.assertEqual(len(controls),8)
        self.assertEqual(len({r['restored_sha256'] for r in controls}),1)
        self.assertEqual({r['copied'] for r in controls},{True,False})
    def test_full_to_split_history_difference_is_not_hidden(self):
        for f in self.c['palette_histories']:
            diff=[r for r in f['rows'] if r['different']]
            self.assertEqual(len(diff),1)
            self.assertEqual([diff[0]['delta'],diff[0]['upper'],diff[0]['C_upper']],[1,'full','above'])
        self.assertEqual(len(self.p['full_saved_restore']),2)
if __name__=='__main__':unittest.main()
