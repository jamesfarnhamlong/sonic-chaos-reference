"""B2 bounded finite completion, zero divider, flow and PCM evidence contracts."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


def report(name):return json.loads((ROOT/'data/m5-a2b2'/name).read_text())


class RemainingFinite(unittest.TestCase):
    def test_exact_full_state_and_immutable_decoder_sources(self):
        gate=report('emission.json');self.assertEqual(len(gate['cases']),46)
        for c in gate['cases'].values():
            self.assertEqual(c['status'],'PASS');self.assertEqual(c['failures'],[])
            self.assertEqual(c['compared_ticks'],c['ticks'])
        self.assertEqual(sum(c['ticks'] for c in gate['cases'].values()),24847)
        self.assertEqual(sum(c['ordered_bytes'] for c in gate['cases'].values()),117677)
        self.assertEqual(gate['decoder_language_changes'],0)
        for name,digest in gate['source_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest(),digest)

    def test_six_actual_completions_and_post_windows(self):
        data=report('facts.json')['termination']
        for rid,end in {'8E':188,'94':1081,'96':340,'97':274,'98':305,'9A':1153}.items():
            r=data[rid];self.assertEqual(r['inactive_tick'],end)
            self.assertEqual(r['post_completion_ticks'],32);self.assertEqual(r['post_completion_port_bytes'],0)
            self.assertEqual(r['final_attenuation'],[15]*4)
            self.assertEqual(r['PCM_samples'],(end+32)*735)

    def test_original_zero_dividers_and_duration_progression(self):
        data=report('facts.json')['zero_tempo'];self.assertEqual(set(data),{'94','9A'})
        for r in data.values():
            self.assertTrue(r['original_tempo_pair_remains_zero']);self.assertTrue(r['all_duration_bytes_exact'])
            self.assertGreater(r['duration_counter_range'][1],0)

    def test_original_counted_loop_transfers_are_executed(self):
        data=report('facts.json')['counted_loops']
        for rid,count in {'94':4,'98':12,'9A':7}.items():
            self.assertEqual(data[rid]['taken_branches'],count)
            self.assertTrue(data[rid]['original_and_candidate_targets_and_ticks_identical'])
            self.assertEqual(data[rid]['transfer_sha256'],report('emission.json')['cases']['solo-'+rid]['control_transfer_sha256'])

    def test_each_new_mix_voice_and_core_measurement(self):
        data=report('pcm.json');self.assertEqual(len(data['cases']),13)
        for c in data['cases'].values():
            self.assertIn(c['continuous_mix']['max_lsb'],(3,4))
            self.assertEqual(c['register_counter_LFSR_failures'],[])
            self.assertTrue(c['partition_invariant']);self.assertEqual(len(c['voices']),4)
            self.assertLessEqual(c['max_over_mix_and_voices'],5)

    def test_all_33_previous_PCM_outputs_preserved(self):
        data=report('pcm.json')['regressions'];self.assertEqual(len(data),33)
        self.assertTrue(all(r['PCM_identical_to_accepted_parent'] and r['partition_invariant'] for r in data.values()))
        self.assertTrue(report('facts.json')['inherited_8A_held_DC_preserved'])

    def test_six_ROM_free_reloads(self):
        data=report('isolation.json');self.assertEqual(set(data['cases']),{'8E','94','96','97','98','9A'})
        for c in data['cases'].values():
            self.assertTrue(c['fresh_process'] and c['ROM_and_oracle_access_forbidden'] and c['PCM_identical'])

    def test_old_SCSP_records_and_horizon_retained(self):
        d=report('emission.json');self.assertEqual(d['SCSP_version'],1);self.assertEqual(d['horizon'],4200)
        self.assertTrue(d['previous_15_headers_and_data_unchanged'])
        self.assertEqual(d['packed_bytes'],7759);self.assertEqual(d['incremental_packed_bytes'],1694)

    def test_70_rows_and_unknown_name_preserved(self):
        data=report('coverage.json');self.assertEqual(len(data['entries']),70)
        self.assertEqual(data['counts'],{'fully-decoded-in-tested-scope':21,'partially-decoded':0,
            'format-understood-but-unverified':0,'unsupported-or-unknown':42,'empty-or-control':7})
        self.assertEqual(data['extracted_unique_headers'],21)
        self.assertEqual(next(r['friendly_name'] for r in data['entries'] if r['request_id']==0x8E),'Unknown $8E')
        self.assertTrue(all(p['proposal_only'] for p in data['expansion_batches']))

    def test_negative_data_terminal_and_admission_controls(self):
        d=report('facts.json');self.assertTrue(d['missing_required_data_rejected'])
        self.assertGreater(d['wrong_pitch_data_detected_tick'],0)
        self.assertGreater(d['missing_terminal_writes_detected_tick'],0)
        self.assertTrue(all(c['lower_priority_rejected'] for c in d['priority_controls'].values()))
        self.assertTrue(d['THZ_not_automatically_restored'])


if __name__=='__main__':unittest.main()
