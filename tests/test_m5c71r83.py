"""Public-safe contract tests; no ROM/programme payload or private library."""
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2')]
from m5c71r83.contract import unpack,pack,Decoder,DecodeError
from m5a2.bank import ROM_HASH
def load(name):return json.loads((ROOT/'data/m5-c7-1r83'/name).read_text())

class R83(unittest.TestCase):
    def test_exact_minimal_region(self):
        o=load('original.json');r=o['minimum_region']
        self.assertEqual((r['address'],r['length'],r['ROM_offset']),(0x4634,2,0x8634))
        self.assertEqual(o['cases']['solo']['pitch_pair_ticks'],[2784,3040])
    def test_complete_boundary_comparison(self):
        e=load('emission.json');self.assertEqual(len(e['cases']),6)
        for c in e['cases'].values():self.assertEqual((c['ticks'],c['failure_count'],c['status']),(4200,0,'PASS'))
    def test_exact_song_specific_continuation(self):
        c=load('continuation.json');self.assertEqual(c['renewal_ticks'],[3594,6666,9738,12810])
        self.assertEqual(c['case']['ticks'],13000);self.assertEqual(c['case']['failure_count'],0)
        self.assertEqual(c['period_ticks'],3072);self.assertFalse(c['global_guard_changed']);self.assertFalse(c['driver_or_PSG_state_reset'])
        self.assertTrue(c['complete_candidate_period_exact']);self.assertGreater(c['log_entries_dropped'],0)
    def test_continuous_pcm_native_and_isolation(self):
        cases=load('pcm.json')['cases'];self.assertEqual(len(cases),7)
        for c in cases.values():
            self.assertEqual(c['PCM_mismatches'],0);self.assertEqual(c['native_before_after_state_mismatching_ticks'],0)
            self.assertEqual(c['samples'],c['ticks']*735);self.assertTrue(c['partition_exact']);self.assertTrue(c['isolated_process_exact'])
            self.assertEqual(c['PCM_sha256'],c['original_PCM_sha256'])
    def test_negative_controls_all_detected(self):
        n=load('negatives.json');self.assertEqual(n['total'],30)
        self.assertTrue(all(c['detected'] for c in n['controls'].values()))
    def test_frozen_C6_preserved(self):
        p=load('preservation.json');self.assertEqual(len(p['C6_cases']),158);self.assertEqual(p['C6_ticks'],42075)
        self.assertFalse(p['new92_support']);self.assertTrue(p['old_bank_new_loader_identical'])
        self.assertEqual(p['C6_bank_sha256'],'677e65cc6038bb193e9813b5890b2127dfa7d5b0b71f0553867995659d2ba5a6')
    def test_partial_region_forgery_is_rejected_without_private_data(self):
        b=dict(version=1,horizon=4200,source_sha256=ROM_HASH,priority={},programs={},data={str(0x4634):0})
        with self.assertRaises(DecodeError):unpack(pack(b))
        b['data']={str(0x4636):0}
        with self.assertRaises(DecodeError):unpack(pack(b))
    def test_unknown_language_and_F7_scope_still_rejected(self):
        b=dict(version=1,horizon=4200,source_sha256=ROM_HASH,priority={},programs={},data={str(0xB800):4})
        m=Decoder(b)
        with self.assertRaises(DecodeError):m.command(0,0xE2,0xB800)
        with self.assertRaises(DecodeError):m.command(2,0xF7,0xB800)
    def test_horizon_remains4200(self):
        b=dict(version=1,horizon=4200,source_sha256=ROM_HASH,priority={},programs={},data={})
        with self.assertRaises(DecodeError):Decoder(b,horizon=4201)
        m=Decoder(b)
        for _ in range(4200):m.tick()
        with self.assertRaises(DecodeError):m.tick()
    def test_complete_source_receipts(self):
        e=load('emission.json');self.assertEqual(e['SCSP_version'],1);self.assertEqual(e['horizon'],4200)
        self.assertTrue(e['old_records_retained']);self.assertTrue(e['old_C6_unchanged'])
        self.assertEqual(e['solo_demand_source_bytes'],1467)
        self.assertEqual(e['header_sha256'],'307b8461133deabd7649dceeb62547d785440e2f748bb9e5558731dd502b5272')

if __name__=='__main__':unittest.main()
