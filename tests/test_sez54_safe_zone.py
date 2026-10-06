"""Focused locks for SEZ3 cached selector and original-game right-clamp reachability."""
import json
import os
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import rom as R
import sez54_safe_zone as A
D=json.loads(A.OUTPUT.read_text())
ROM=Path(os.environ.get('SONIC_CHAOS_ROM',str(ROOT.parent/'source/Sonic Chaos (Europe).sms')))

class Contracts(unittest.TestCase):
    def test_right_clamp_natural_escape(self):
        for target in ('right','rightwait','rightmaxwait',3222):
            run=next(v for v in D['runs'] if v['target']==target)
            e=run['escapes'][0]
            self.assertEqual(e['camera'],[2975,462])
            self.assertEqual(e['boss'],[3187,623])
            self.assertEqual(e['boss_cache'][0],212)
            self.assertGreaterEqual(e['player_cache'][0],212)
            self.assertTrue({11,12}.issubset(run['states']))
            self.assertEqual(run['first_hurt'],598)
        run=next(v for v in D['runs'] if v['target']=='rightmaxwait')
        self.assertEqual(run['escapes'][0]['player'],[3222,622])

    def test_refresh_provenance(self):
        run=next(v for v in D['runs'] if v['target']=='rightmaxwait')
        e=next(e for e in run['selector_evidence'] if e['cached_would_escape'])
        self.assertEqual((e['boss_cache_age'],e['player_cache_age']),(1,1))
        self.assertEqual(e['boss_last_refresh']['boss_cache'][0],212)
        self.assertEqual(e['player_last_refresh']['player_cache'][0],247)
        self.assertTrue(e['fresh_would_escape'])
        for run in D['runs']:
            for e in run['selector_evidence']:
                self.assertEqual(e['fresh_would_escape'],e['cached_would_escape'])

    def test_left_comparison(self):
        for target in ('left','leftwait'):
            run=next(v for v in D['runs'] if v['target']==target)
            self.assertEqual(run['escapes'],[])
            self.assertIsNotNone(run['first_hurt'])

    def test_actual_renderer_gate(self):
        self.assertEqual([v['after'] for v in D['controlled_oracle']['renderer_vectors']],[212,199,199,199])
        self.assertEqual(D['controlled_oracle']['selector_cases'],1536)

    def test_exhaustive_stationary_sweep(self):
        sweep=json.loads((ROOT/'data/rom-cache/sez/boss-54-stationary-sweep.json').read_text())
        self.assertEqual([v['target'] for v in sweep['runs']],list(range(2991,3223)))
        self.assertTrue(all(v['first_hurt'] is not None for v in sweep['runs']))
        self.assertEqual(sweep['rom_sha256'],R.SHA256)

@unittest.skipUnless(ROM.exists(),'verified local ROM unavailable')
class OriginalROM(unittest.TestCase):
    def test_controlled_original_callbacks(self):
        self.assertEqual(A.oracle(R.load(ROM)),D['controlled_oracle'])

    def test_natural_guarded_replay(self):
        runs=json.loads(json.dumps(A.build(R.load(ROM),['rightmaxwait','leftwait','rightmaxwait'])))['runs']
        self.assertEqual(runs[0],runs[2])
        self.assertEqual(runs[0],next(v for v in D['runs'] if v['target']=='rightmaxwait'))
        self.assertEqual(runs[1],next(v for v in D['runs'] if v['target']=='leftwait'))

    def test_stationary_boundary_replay(self):
        sweep=json.loads((ROOT/'data/rom-cache/sez/boss-54-stationary-sweep.json').read_text())
        runs=json.loads(json.dumps(A.build(R.load(ROM),[2991,3215,3216,3222],sweep=True)))['runs']
        for run in runs:
            self.assertEqual(run,next(v for v in sweep['runs'] if v['target']==run['target']))

if __name__=='__main__':unittest.main()
