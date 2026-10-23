"""Focused metadata and original-execution witness checks, no ROM needed.

Run m2r1_frame5e.py PRIVATE_ROM --check to repeat original-code execution.
"""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import rom as R

def validate(d):
    assert d['rom_sha256']==R.SHA256
    tails=next(x for x in d['mapping'] if x['character']==2)
    assert (tails['table_bank'],tails['table_cpu'],tails['entry_cpu'],tails['pointer_cpu'],tails['pointer_effective_rom_offset'])==(15,0x85BF,0x867B,0x0785,0x0785)
    for r in d['controlled_routines']:
        assert r['frame']==(94 if r['contact']&12 else 2)
        assert r['callback']==0x83A6
        assert r['callback_result']['requested']==32
        assert r['callback_result']['contact_after']==r['contact']
        assert r['selector_phase']==(0 if r['contact']&12 else 1)
    return True

class Frame5e(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads((ROOT/'data/m2r1/frame5e-evidence.json').read_text())
        cls.s={s['label']:s for s in cls.d['sessions']}

    def test_pointer_and_all_control_predicates(self):
        self.assertTrue(validate(self.d))
        self.assertEqual(len(self.d['controlled_routines']),16)

    def test_bad_pointer_and_wrong_bank_rejected(self):
        for key,value in [('pointer_cpu',0x858B),('table_bank',12)]:
            d=copy.deepcopy(self.d)
            next(x for x in d['mapping'] if x['character']==2)[key]=value
            with self.assertRaises(AssertionError):validate(d)

    def test_malformed_header_and_duration(self):
        for r in self.d['controlled_routines']:
            if r['character']==2 and r['contact']&12:
                self.assertEqual((r['mapping_count'],r['extent'],r['piece_pointer'],r['origin_pointer'],r['duration']),
                                 (230,[32,40],0x1103,0x078A,2))
        self.assertEqual([(r['flags'],r['frame'],r['mapping_count']) for r in self.d['hidden_controls']],
                         [(0,94,230),(8,94,0)])

    def test_setter_and_boss_gate_do_not_clear_side(self):
        self.assertEqual(len(self.d['setter_controls']),12)
        self.assertEqual(len(self.d['boss_gate_controls']),8)
        for r in self.d['setter_controls']:
            self.assertEqual(r['contact_before'],r['contact_after'])
            self.assertEqual(r['request'],32)
        for r in self.d['boss_gate_controls']:
            self.assertEqual(r['request'],32 if r['background']&2 else 5)
            self.assertEqual(r['contact'],r['contact_after'])

    def test_execution_reads_resident_code_not_census_fallback(self):
        r=self.s['tails-side']['rows'][0]
        self.assertEqual((r['mapping_read_cpu'],r['mapping_read_bank_slots'],r['selected']),
                         (0x0785,[0,1,15],94))
        t=self.s['tails-side']['tile_transfers'][0]
        self.assertEqual((t['mapper_bank'],t['source_cpu'],t['blocks64'],t['length_bytes']),
                         (19,0xDA07,174,11136))
        self.assertTrue(t['source_is_ram'])

    def test_render_and_progression_positive_negative_controls(self):
        side=self.s['tails-side'];clear=self.s['tails-clear'];sonic=self.s['sonic-side']
        self.assertEqual([len(s['callbacks']) for s in (side,clear,sonic)],[1,63,63])
        self.assertEqual({r['selected'] for r in sonic['rows']},{94})
        self.assertTrue(all(r['count']==6 for r in sonic['rows']))
        self.assertTrue(all(r['selected'] in range(1,7) for r in clear['rows']))
        self.assertNotEqual(side['screenshots'][-1]['vram_sha256'],clear['screenshots'][-1]['vram_sha256'])

    def test_sign_routes_are_arrival_fixtures_and_clear_side(self):
        for name in ('tails-sign','tails-sign-backtrack-act1','tails-sign-backtrack-act2'):
            s=self.s[name]
            self.assertIsNone(s['injected_state_contact'])
            self.assertTrue(s['setup'].startswith('ARRIVAL'))
            self.assertGreater(len(s['rows']),0)
            self.assertTrue(all(not r['contact']&12 for r in s['rows']))
            self.assertEqual(s['end']['act'],s['act']+1)

    def test_raw_branch_is_not_silently_closed(self):
        self.assertTrue(self.d['conclusion'].startswith('UNRESOLVED'))
        d=copy.deepcopy(self.d)
        next(r for r in d['controlled_routines'] if r['contact']==4)['frame']=0x55
        with self.assertRaises(AssertionError):validate(d)

    def test_payload_boundary(self):
        self.assertEqual([p.suffix for p in (ROOT/'data/m2r1').iterdir()],['.json'])
        self.assertTrue((ROOT/'docs/m2r1-tails-act-clear-frame5e.md').is_file())

if __name__=='__main__':unittest.main()
