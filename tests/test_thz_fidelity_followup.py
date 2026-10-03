"""Regression locks for the original THZ visual and grounded-contact path."""
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import thz_fidelity_followup as tool
D=json.loads(tool.OUTPUT.read_text())

class FidelityFollowup(unittest.TestCase):
    def test_identity_and_vram(self):
        self.assertEqual(D['rom_sha256'],tool.b.ROM_SHA256)
        self.assertTrue(D['research_only'] and D['poc_untouched'])
        self.assertTrue(D['bee']['runtime_vram_equal'])
        self.assertTrue(D['bee']['remap_is_bit_reversal'])
        self.assertEqual(D['bee']['runtime_registers'][1]&2,2)
        self.assertEqual(D['bee']['runtime_registers'][6]&4,0)

    def test_original_sat_piece_order(self):
        for r in D['bee']['rows']:
            self.assertEqual(r['record']['piece_count'],3)
            self.assertEqual([p['x'] for p in r['sat']],[4,-4,-12] if r['mirror'] else [-12,-4,4])
            self.assertEqual([p['y'] for p in r['sat']],[-16]*3)
            self.assertEqual([p['sat_tile'] for p in r['sat']],
                             [170,172,174] if r['frame']==1 else [176,178,174])
        self.assertEqual([r['poc_vs_original_pixels'] for r in D['bee']['poc_comparison']],[198,202])
        self.assertEqual([r['poc_import_vs_research_normal_pixels'] for r in D['bee']['poc_comparison']],[0,0])

    def test_grounded_actual_call_and_next_update(self):
        run=D['boss'][0]
        before=next(r for r in run['events'] if r['stage']=='at_8105')
        after=next(r for r in run['events'] if r['stage']=='after_8105')
        self.assertEqual([before[k] for k in ('current','requested','flags','floor','vx','vy','bits')],
                         [9,9,2,2,979,1792,8])
        self.assertEqual([after[k] for k in ('current','requested','flags','floor','vx','vy')],
                         [9,27,2,2,-1536,-1792])
        terrain=next(r for r in run['events'] if r['stage']=='terrain' and r['update']==before['update']+1)
        self.assertEqual([terrain[k] for k in ('flags','floor','y','vy')],[2,2,245,1792])
        # Floor projection returns to anchor 238 without an aerial ascent.
        following=[r for r in run['rows'][before['update']+1:before['update']+10]]
        self.assertTrue(all(r['y']==238 for r in following))

    def test_airborne_and_exact_top(self):
        for run,want in zip(D['boss'][1:3],((864,-864),(-672,672))):
            before=next(r for r in run['events'] if r['stage']=='at_8105')
            after=next(r for r in run['events'] if r['stage']=='after_8105')
            self.assertEqual((before['vy'],after['vy']),want)
            self.assertEqual((after['flags'],after['floor'],after['bits']),(3,0,8))
        top=D['boss'][3]
        call=next(r for r in top['events'] if r['stage']=='top_setter')
        self.assertEqual((call['y']-call['boss_y'],call['bits'],call['vy']),(-48,1,48))
        after=top['rows'][1]
        self.assertEqual((after['requested'],after['flags'],after['floor'],after['vy']),(11,1,0,-1024))
        self.assertFalse(any(r['stage']=='at_8105' for r in top['events']))

    def test_grounded_velocity_boundaries_and_flag_control(self):
        self.assertEqual(D['grounded_sweep']['cases'],6144)
        self.assertEqual(D['grounded_sweep']['mismatches'],[])
        self.assertEqual([r['vy_after'] for r in D['flag_control']],[1792,-1756])
        self.assertEqual([r['y'] for r in D['flag_control']],[245,231])

    def test_original_rom_replay(self):
        rom=ROOT.parent/'source/Sonic Chaos (Europe).sms'
        if not rom.exists():self.skipTest('local canonical ROM unavailable')
        out=ROOT/'build/thz-fidelity-followup-test';out.mkdir(parents=True,exist_ok=True)
        self.assertEqual(tool.build(rom.read_bytes(),out),D)

if __name__=='__main__':unittest.main()
