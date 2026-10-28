"""Public-safe acceptance contracts for private original/PSG/PCM batch receipts."""
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
PUB=ROOT/'data/m5-c7-batch'
def load(name):return json.loads((PUB/name).read_text())

class BatchEvidence(unittest.TestCase):
    def test_independent_id_coverage(self):
        v=load('verdict.json')
        self.assertEqual(set(v['new_scoped_Research_GO']),{'92','8F','A8','AB','AD','AE','B2','B3','B5','C0','C1','C3','BB','BE','C4'})
        self.assertEqual(set(v['HOLD']),{'91','93','95','82','8B','8C','8D','90'})
        self.assertEqual(v['baseline_F2_playable'],39);self.assertEqual(v['new_native_F2'],0)
        self.assertTrue(all(not r['native_F2_playable'] for r in v['per_ID'].values()))
    def test_holds_preserve_first_rejection(self):
        v=load('verdict.json')['per_ID']
        for rid,tick,pointer in [('91',1732,'4634'),('93',293,'4634'),('95',4068,'4630'),('8B',121,'4632'),('90',2471,'4634')]:
            self.assertEqual(v[rid]['blocker']['tick'],tick)
            self.assertIn(pointer,v[rid]['blocker']['message'])
            self.assertEqual(v[rid]['exact_solo_ticks'],tick-1)
    def test_exact_native_receipts_cover_every_compared_tick(self):
        emissions={};pcms={}
        for p in PUB.glob('emission-*.json'):emissions.update(json.loads(p.read_text())['cases'])
        for p in PUB.glob('pcm-*.json'):pcms.update(json.loads(p.read_text())['cases'])
        self.assertEqual(set(emissions),set(pcms))
        for name,e in emissions.items():
            p=pcms[name];self.assertEqual(e['failure_count'],0);self.assertEqual(p['ticks'],e['ticks'])
            self.assertEqual(p['samples'],735*e['ticks']);self.assertEqual(p['PCM_mismatches'],0)
            self.assertEqual(p['native_before_after_state_mismatching_ticks'],0)
            self.assertTrue(p['partition_exact'] and p['isolated_process_exact'] and p['three_access_guards_tested'])
    def test_alias_lifecycle_not_separate_loop_storage(self):
        s=load('source.json')['alias92']
        self.assertEqual(s['stale_counter_cases_exact'],256);self.assertEqual(s['alias_cursors'],[48])
        self.assertEqual(s['tone2_offset43_stack_writes'],0)
        self.assertEqual(s['reused_original_loop']['period_ticks'],3648)
    def test_renewal_scope_and_negative_controls(self):
        c=load('continuation-certificates.json');self.assertEqual(set(c),{'92','8F'})
        for r in c.values():self.assertLessEqual(r['repeat_tick'],4200)
        n=load('negative.json');self.assertTrue(n['all_detected']);self.assertGreaterEqual(len(n['cases']),24)
        for rid in ('92','8F'):
            for event in ('request','fade','state'):self.assertTrue(n['cases'][rid+'-renew-revoked-'+event]['detected'])
    def test_finite_sfx_original_release_and_silence(self):
        pre=load('preflight.json')['cases']
        for rid in ('A8','AB','AD','AE','B2','B3','B5','C0','C1','C3','BB','BE','C4'):
            r=pre[rid+'-solo'];self.assertGreater(r['release_tick'],0);self.assertLess(r['release_tick'],600)
            self.assertEqual(r['final_attenuations'],[15]*4)

if __name__=='__main__':unittest.main()
