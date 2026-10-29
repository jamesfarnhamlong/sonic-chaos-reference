"""Public evidence consistency and acceptance-boundary regression checks."""
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(name):return json.loads((ROOT/'data/m5-g1r'/name).read_text())

class Interactions(unittest.TestCase):
    def test_frozen_original_and_independent_replay(self):
        original=load('original.json')['cases'];verified=load('verified.json')['cases']
        self.assertEqual(set(original),set(verified));self.assertEqual(len(verified),204)
        for name,r in verified.items():
            self.assertEqual(r['original_capture_sha256'],original[name]['capture_sha256'])
            self.assertEqual(r['ticks'],original[name]['ticks'])
            self.assertEqual(r['samples'],r['ticks']*735)
            self.assertEqual(r['status'],'PASS');self.assertTrue(r['isolated_exact'])
            for field in ('PCM_mismatches','native_mismatching_ticks','partition_mismatches','state_PSG_transfer_mismatches'):self.assertEqual(r[field],0)

    def test_global_fade_and_numeric_reset_boundaries(self):
        r=load('original.json')['cases']
        self.assertEqual(r['81-F8-blocked']['reset_ticks'],[1])
        self.assertEqual(r['81-terminal-fade-selection']['reset_ticks'],[1,57])
        self.assertEqual(r['81-terminal-fade-selection']['final_active_slots'],[])
        self.assertEqual(r['81-fade-dispatch']['reset_ticks'],[1,35])
        for rid in ('81','83','91','92','93','95','90','8F','8B','8C'):
            self.assertIn(57,r[rid+'-fade']['reset_ticks'])

    def test_source_driven_power_and_silent_sneakers(self):
        p=load('writers.json')['power_cases']
        self.assertEqual(p['inv']['writes'][0]['delivered'],0x84)
        self.assertEqual(p['inv']['selector_expiry_tick'],630)
        self.assertEqual(p['rocket']['selector_expiry_tick'],330)
        self.assertEqual(p['ss1-rocket']['writes'],[])
        self.assertEqual(p['ss4-rocket']['writes'][-1]['delivered'],0x8F)
        self.assertIsNone(p['inv-sneakers']['selector_expiry_tick'])
        self.assertEqual(p['inv-sneakers']['first_music_inactive'],1117)
        self.assertEqual(p['inv-sneakers']['final_selector'],3)

    def test_source_gates_and_zone_table(self):
        rows=load('writers.json')['level_writer'];self.assertEqual(len(rows),39)
        for row in rows:
            if row['gate']:self.assertEqual((row['direct'],row['deferred']),(0,0))
            else:
                self.assertEqual(row['direct'],row['deferred'])
                if row['zone']>=8:self.assertEqual(row['direct'],0x8F)
                if (row['zone'],row['act']) in ((5,2),(7,0)):self.assertEqual(row['direct'],0x90)

    def test_epoch_is_driver_restart_not_chip_reset(self):
        report=load('epochs.json');self.assertFalse(report['solo_certificate_reused']);self.assertFalse(report['new_candidate_epoch_implemented'])
        self.assertEqual(len(report['cases']),10)
        self.assertTrue(any(r['full400_IY_logical_PSG_mismatching_ticks'] for r in report['cases'].values()))
        for r in report['cases'].values():
            self.assertEqual(r['driver400_mismatching_ticks'],0);self.assertEqual(r['IY_mismatching_ticks'],0)
            self.assertEqual(r['ordered_write_mismatching_ticks'],0)
            self.assertGreater(r['persistent_vs_fresh_chip_PCM_differing_samples'],0)
            self.assertIsNone(r['pre_reset_first_full_state_rejoin'])

    def test_clock_has_ten_nonzero_tick_effects(self):
        r=load('original.json')['cases']['8F-clock']
        self.assertEqual(r['SFX_admissions'],[[t,0xB5] for t in range(90,631,60)])
        self.assertEqual(r['reset_ticks'],[1,30,690])

    def test_no_continuation_upgrade_and_full400_totals(self):
        e=load('evidence.json');self.assertEqual(e['cases'],204);self.assertEqual(e['ticks'],130350)
        self.assertEqual(e['samples'],95807250);self.assertEqual(e['full400_shadow_ticks'],e['ticks'])
        self.assertFalse(e['continuation_granted']);self.assertFalse(e['native_GameMaker_tested'])
        self.assertEqual(len(e['negative_controls']),37)
        self.assertTrue(all(r['detected'] for r in e['negative_controls'].values()))
        self.assertTrue(all(not r['continuation_authorised'] for r in load('banks.json').values()))

if __name__=='__main__':unittest.main()
