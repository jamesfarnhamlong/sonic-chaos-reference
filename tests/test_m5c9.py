"""Public-safe C9 source/coverage/emission certificates; no private fixtures."""
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2')]
PUB=ROOT/'data/m5-c9'
def load(name):return json.loads((PUB/name).read_text())

class C9(unittest.TestCase):
    def test_each_original_is_independently_scoped(self):
        p=load('reader-policy.json')
        self.assertEqual(set(p),{'91','93','95','8B','90','82','8C','8D'})
        self.assertEqual({k:len(v['pair_hashes']) for k,v in p.items()},{'91':2,'93':1,'95':2,'8B':1,'90':1,'82':0,'8C':0,'8D':0})
        self.assertEqual(len({v['programme_sha256'] for v in p.values()}),8)
        for rid,r in p.items():
            o=load(rid+'-solo.json');self.assertTrue(o['original_only']);self.assertEqual(r['reader_scopes'],o['reader_scopes'])
            for slot,transpose,address,index in r['reader_scopes']:
                self.assertEqual(address,0x4436+2*index);self.assertIn(str(address),r['pair_hashes'])
    def test_extended_original_periods_are_complete(self):
        for rid,period in [('91',32256),('93',3000),('95',4032),('8B',3456),('90',19768),('82',6912),('8C',80640)]:
            o=load(rid+'-solo.json');r=o['recurrence']
            self.assertEqual(r['period_ticks'],period);self.assertEqual(o['ticks'],r['first_tick']+2*period)
            self.assertTrue(r['original400_state_period_exact'] and r['ordered_write_period_exact'])
    def test_finite_end_is_not_a_music_loop(self):
        o=load('8D-solo.json');c=load('capabilities.json')['8D'];v=load('8D-solo-verified.json')
        self.assertIsNone(o['recurrence']);self.assertEqual(o['finite_release_tick'],10432)
        self.assertEqual(o['final_active_slots'],[]);self.assertEqual(o['final_attenuations'],[15]*4)
        self.assertEqual(c['finite_proof_end'],11968);self.assertEqual(v['finite_completed_at'],10432)
        self.assertEqual(v['renewals'],0)
    def test_all_exact_receipts_and_isolation(self):
        verified=list(PUB.glob('*-verified.json'));self.assertEqual(len(verified),10)
        for p in verified:
            r=json.loads(p.read_text());self.assertEqual(r['status'],'PASS');self.assertEqual(r['samples'],735*r['ticks'])
            for k in ('sample_mismatches','native_before_after_mismatching_ticks','partition_mismatching_ticks','state_PSG_transfer_mismatches','chip_resets_at_windows_or_loops'):self.assertEqual(r[k],0)
            self.assertEqual(r['PCM_sha256'],r['original_PCM_sha256']);self.assertTrue(r['isolated_process_exact'])
            self.assertEqual(r['access_guards_tested'],3)
    def test_checkpoint_and_negative_coverage_per_id(self):
        n=load('negative.json');self.assertTrue(n['all_detected']);self.assertEqual(n['count'],len(n['cases']))
        for rid,c in load('capabilities.json').items():
            self.assertIn('4200',c['checkpoints'])
            for kind in ('ordinary4201','constructor4201','checkpoint-state','continuation-bank','late-request','revoke-same-request','revoke-other-request','revoke-fade'):
                self.assertTrue(n['cases'][rid+'-'+kind]['detected'])
    def test_contexts_and_no_native_promotion(self):
        r=load('90-contexts.json');self.assertFalse(r['natural_scene_timing_qualified']);self.assertFalse(r['short_M4_PCM_used'])
        self.assertEqual({x['context'] for x in r['writer_cases']},{'opening','EEZ3'})
        for c in r['writer_cases']:self.assertEqual(c['request_written'],0x90 if c['D4A3']==0 else 0)
        v=load('verdict.json');self.assertEqual(v['new_Research_GO'],8);self.assertEqual(v['Research_HOLD'],[])
        self.assertEqual(v['baseline_native_F2'],39);self.assertEqual(v['new_native_F2'],0)
        self.assertFalse(v['original83_scope_changed']);self.assertFalse(v['global4200_changed'])
    def test_actual_loader_rejects_synthetic_noncontainers(self):
        from m5c9.contract import unpack
        for b in (b'',b'not-an-scsp',bytes(128)):
            with self.assertRaises(ValueError):unpack(b)

if __name__=='__main__':unittest.main()
