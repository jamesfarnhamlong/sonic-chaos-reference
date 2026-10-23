"""Cross-layer regression gates for the character interaction contract."""
import json
import os
import sys
import unittest
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import m2r2_interactions as A

class Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads((ROOT/'data/m2r2/evidence.json').read_text())
        cls.m=json.loads((ROOT/'data/m2r2/character-interaction-matrix.json').read_text())

    def test_matrix_chains_and_evidence_classes(self):
        ids=[x['id'] for x in self.m['entries']]
        self.assertEqual(len(ids),len(set(ids)))
        for row in self.m['entries']:
            for key in ('placement','conversion','artwork','activation','reward','effects','cancellation','source_refs','unresolved'):
                self.assertIn(key,row)
            self.assertIn(row['classification'],self.m['classification_values'])
            for ref in row['source_refs']:
                if ref.startswith(('docs/','tools/','asm/')):self.assertTrue((ROOT/ref).exists(),ref)

    def test_placement_inventory(self):
        mon=[x for x in self.d['placements'] if x['type']==16]
        self.assertEqual(Counter(x['parameter'] for x in mon if x['zone']<6),{1:16,2:12,3:9,4:11,6:21})
        self.assertEqual(Counter(x['parameter'] for x in mon if x['zone']>=8),{4:6,5:5,6:7})
        self.assertEqual(sum(x['type']==47 and x['zone']<6 for x in self.d['placements']),16)

    def test_substitution_precedes_art_and_reward(self):
        rows=self.d['controls']['monitors']
        ring=next(x for x in rows if x['character']==2 and x['placement_parameter']==1)
        tail=next(x for x in rows if x['character']==2 and x['placement_parameter']==4)
        self.assertEqual(tail['effective_parameter'],1)
        self.assertEqual(tail['art_layers'],ring['art_layers'])
        self.assertEqual(tail['reward'],ring['reward'])
        self.assertEqual(tail['queued'],1)

    def test_life_art_only_other_monitor_difference(self):
        rows={(x['character'],x['placement_parameter']):x for x in self.d['controls']['monitors']}
        for p in (1,3,5,6):self.assertEqual(rows[1,p]['art_layers'],rows[2,p]['art_layers'])
        self.assertNotEqual(rows[1,2]['art_layers'],rows[2,2]['art_layers'])
        self.assertEqual(rows[1,2]['reward']['lives'],rows[2,2]['reward']['lives'])

    def test_gameplay_maps_to_same_static_placement(self):
        for c in (1,2):
            run=next(x for x in self.d['gameplay'] if x['character']==c and x['setup'].startswith('ARRIVAL'))
            events=run['events'];names=[e['event'] for e in events]
            self.assertLess(names.index('init_before'),names.index('init_after'))
            self.assertLess(names.index('init_after'),names.index('art'))
            self.assertLess(names.index('art'),names.index('break'))
            self.assertLess(names.index('break'),names.index('reward'))
            self.assertEqual(next(e for e in events if e['event']=='art')['selector'],4 if c==1 else 1)
            self.assertEqual(next(e for e in events if e['event']=='reward')['queue'],8 if c==1 else 1)
            if c==2:
                self.assertEqual(next(e for e in events if e['event']=='ring_awarded')['rings'],0x12)
                self.assertNotIn('rocket_setup',names)
            else:self.assertIn('rocket_setup',names)

    def test_nonbreaking_controls_both_characters(self):
        self.assertEqual(Counter(x['character'] for x in self.d['controls']['negative_contact']),{1:5,2:5})
        for x in self.d['controls']['negative_contact']:self.assertEqual(x['result']['object_type_after'],'0x10')

    def test_spring_scheduled_character_art_and_shared_owner(self):
        for s in self.d['spring_gameplay']:
            active=[r for r in s['rows'] if r['state']==18]
            self.assertEqual({r['frame'] for r in active},{11 if s['character']==1 else 10})
            self.assertEqual({tuple(r['extent']) for r in active},{(8,24)})
            b=[r['step'] for r in active if r['shoe_state']==3 and r['shoe_frame']==3]
            self.assertEqual(b[:3],[17,98,179])
            self.assertTrue(any(r['step']==181 and r['requested']==10 and r['shoe_state']==5 for r in active))

    def test_timer_zero_not_generic_expiry(self):
        for row in self.d['controls']['timer_edges']:
            self.assertEqual(row['timer_after'],(row['timer_before']-1)&65535)
            self.assertEqual(row['selector_after'],0 if row['timer_before']==1 and row['selector_before'] in (4,6) else row['selector_before'])

    def test_sign_face_character_difference_only(self):
        rows=self.d['controls']['sign_rewards'];lookup={(r['character'],r['zone'],r['rings_before']):r['result'] for r in rows}
        for r in rows:
            if r['character']!=1:continue
            a=r['result'];b=lookup[2,r['zone'],r['rings_before']]
            for key in ('cls','lives','cont','rings','state'):self.assertEqual(a[key],b[key])
            if a['cls'] in (1,3):self.assertEqual({a['art'],b['art']},{27,29})
            else:self.assertEqual(a['art'],b['art'])

    def test_wrap_preserves_reward_but_changes_scene(self):
        a,b=self.d['controls']['ring_wrap']
        self.assertEqual((a['rings'],a['lives']),(b['rings'],b['lives']))
        self.assertEqual((a['mode'],b['mode']),(136,0))

    def test_unresolved_cases_remain_visible(self):
        reg=json.loads((ROOT/'data/m2r2/fidelity-register.json').read_text())
        self.assertFalse(reg['windows_acceptance'])
        self.assertTrue(any(x['id']=='M2R1-FRAME5E-NATURAL' and x['classification']=='unresolved' for x in reg['findings']))

    @unittest.skipUnless(os.environ.get('SONIC_CHAOS_ROM'),'private ROM required for original-code replay')
    def test_reexecute_original_source_and_controls(self):
        r=A.R.load(os.environ['SONIC_CHAOS_ROM'])
        self.assertEqual(A.controls(r),self.d['controls'])
        self.assertEqual(A.source(r),self.d['source'])
        self.assertEqual(A.placements(r),self.d['placements'])

if __name__=='__main__':unittest.main()
