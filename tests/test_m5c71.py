"""Public-safe assertions: evidence cannot promote a prefix to a complete song."""
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(name):return json.loads((ROOT/'data/m5-c7-1'/name).read_text())

class C71(unittest.TestCase):
    def test_separate_hold_verdicts(self):
        v=load('verdict.json');self.assertEqual(set(v['per_ID']),{'83','92'})
        for c in v['per_ID'].values():
            self.assertEqual(c['verdict'],'HOLD');self.assertFalse(c['full_song_GameMaker_eligible'])
    def test_independent_original_recurrences(self):
        b=load('boundaries.json')['per_ID']
        for rid,expected in [('83',(522,3594,3072,17)),('92',(511,4159,3648,95))]:
            r=b[rid]['loop'];self.assertEqual(tuple(r[k] for k in ['first_tick','repeat_tick','period_ticks','edges_per_period']),expected)
            self.assertEqual(r['full_period_state_mismatching_ticks'],0);self.assertEqual(r['full_period_write_mismatching_ticks'],0)
            self.assertTrue(r['transfer_edges_identical']);self.assertFalse(r['candidate_renewal_eligible'])
    def test_rejections_are_not_passes(self):
        e=load('emission.json')['cases']
        for rid,t in [('83',2784),('92',3266)]:
            c=e[rid+'-solo'];self.assertEqual(c['status'],'HOLD');self.assertEqual(c['rejection']['tick'],t);self.assertEqual(c['ticks'],t-1)
    def test_no_differences_hidden_by_hold(self):
        e=load('emission.json')['cases']
        self.assertEqual(len(e),13)
        for c in e.values():self.assertEqual(c['failure_count'],0)
        self.assertEqual(sum(c['status']=='PASS' for c in e.values()),11)
    def test_pcm_is_exact_only_for_compared_windows(self):
        e=load('emission.json')['cases'];p=load('pcm.json')['cases']
        self.assertEqual(set(p),set(e))
        for n,c in p.items():
            self.assertEqual(c['samples'],e[n]['ticks']*735);self.assertEqual(c['PCM_mismatches'],0)
            self.assertEqual(c['native_state_mismatching_ticks'],0);self.assertTrue(c['partition_exact'])
            self.assertEqual(c['PCM_sha256'],c['original_A1L_PCM_sha256'])
    def test_partial_receipts_cannot_claim_full_extraction(self):
        e=load('emission.json');self.assertEqual(e['horizon'],4200);self.assertFalse(e['decoder_modified'])
        self.assertTrue(e['prior_bank_unchanged']);self.assertTrue(e['prior_records_retained'])
        for r in e['per_ID'].values():self.assertFalse(r['complete_within_4200']);self.assertIsNotNone(r['extraction_error'])
    def test_original_blockers_are_causal(self):
        b=load('boundaries.json')['per_ID'];p=b['83']['first_out_of_validated_pitch_read']
        self.assertEqual((p['tick'],p['slot'],p['index'],p['address']),(2784,1,255,0x4634))
        f=b['92']['first_unsupported_F7'];self.assertEqual((f['tick'],f['index'],f['channel_offset']),(3266,4,43))
    def test_all_negative_controls_detected(self):
        n=load('verdict.json')['negatives'];self.assertEqual(len(n),10)
        self.assertTrue(all(c['rejected'] for c in n.values()))

if __name__=='__main__':unittest.main()
