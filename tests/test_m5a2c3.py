"""Noise-reset and multi-slot original-driver expansion contracts."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


def report(name):return json.loads((ROOT/'data/m5-a2c3'/name).read_text())


class NoiseAndOwnership(unittest.TestCase):
    def test_original_preflight_classes_not_hypotheses(self):
        d=report('preflight.json');self.assertFalse(d['candidate_PCM_rendered']);self.assertFalse(d['candidate_promoted'])
        rows={r['request_id']:r for r in d['rows']};self.assertEqual(set(rows),{0xB0,0xB7,0xBA})
        for rid,mode,count,slots in [(0xB0,7,2,[2]),(0xB7,3,2,[2]),(0xBA,7,1,[0,2])]:
            r=rows[rid];self.assertEqual(r['F3_control_modes'],[mode]);self.assertEqual(r['F3_executions'],count)
            self.assertEqual(r['SFX_slots_used'],slots);self.assertEqual(r['unverified_opcodes'],[])
            self.assertNotIn('FD',r['reached_opcodes']);self.assertEqual(r['label'],f'Unknown ${rid:02X}')

    def test_all_99_original_differential_cases(self):
        d=report('emission.json');self.assertEqual(len(d['cases']),99)
        self.assertEqual(sum(r['ticks'] for r in d['cases'].values()),32531)
        self.assertEqual(sum(r['ordered_bytes'] for r in d['cases'].values()),154221)
        self.assertEqual(d['decoder_language_changes'],0)
        for r in d['cases'].values():
            self.assertEqual(r['status'],'PASS');self.assertEqual(r['failures'],[]);self.assertEqual(r['ticks'],r['compared_ticks'])
        for path,digest in d['source_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes().replace(b'\r\n',b'\n')).hexdigest(),digest)

    def test_finite_and_post_physical_output(self):
        data=report('facts.json')['termination']
        for rid,end in [('B0',7),('B7',7),('BA',25)]:
            r=data[rid];self.assertEqual(r['inactive_tick'],end);self.assertEqual(r['candidate_post_ticks'],32)
            self.assertEqual(r['original_preflight_post_ticks'],128);self.assertEqual(r['post_writes'],0)
            self.assertEqual(r['final_attenuation'],[15]*4);self.assertEqual(r['PCM_samples'],(end+32)*735)

    def test_repeated_F3_resets_LFSR_but_not_noise_countdown(self):
        data=report('facts.json')['F3_reset_evidence']
        for rid,mode in [('B0',7),('B7',3)]:
            r=data[rid];self.assertEqual(r['F3_ticks'],[1,4]);self.assertEqual(r['modes'],[mode,mode])
            self.assertTrue(r['original_and_decoded_instant_core_states_equal'])
            second=r['second_write'];self.assertEqual(second['RNG_after'],32768)
            self.assertNotEqual(second['RNG_before'],second['RNG_after'])
            self.assertEqual(second['noise_counter_before'],21);self.assertEqual(second['noise_counter_after'],21)
        self.assertEqual(data['BA']['F3_ticks'],[1])

    def test_duplicate_control_negative_is_detected(self):
        for r in report('facts.json')['duplicate_control_negative'].values():
            self.assertEqual(r['LFSR_mismatching_ticks'],36);self.assertEqual(r['max_signed16_error'],16384)

    def test_independent_BA_slots_and_concurrent_hurt(self):
        d=report('facts.json');self.assertEqual(d['BA_simultaneous_solo_slots'],2)
        self.assertEqual(d['BA_noise_slot_release_tick'],5);self.assertEqual(d['BA_tone1_release_tick'],25)
        self.assertEqual(d['BA_with_hurt_simultaneous_slots'],3);self.assertEqual(d['BA_missing_terminal_detected_tick'],5)

    def test_admitted_retriggers_and_actual_F3_counts(self):
        d=report('facts.json')
        self.assertEqual(d['F3_counts']['B0-retrigger'],7);self.assertEqual(d['F3_counts']['B7-retrigger'],6)
        self.assertEqual(d['F3_counts']['BA-retrigger'],4)
        self.assertEqual(d['admissions']['B7-block-ring'],[[1,0xB7],[8,0xBF]])
        self.assertEqual(d['admissions']['BA-priority-noise-replace'],[[30,0xBA],[33,0xB7]])

    def test_DE11_and_next_read_recovery(self):
        d=report('facts.json');r=d['DE11_restore_contexts']
        self.assertEqual(r['solo-B0'],[dict(tick=7,channel=6,data_latch=7,byte=0)])
        self.assertEqual(r['solo-BA'],[dict(tick=5,channel=6,data_latch=3,byte=0)])
        self.assertEqual(r['THZ-BA'],[dict(tick=34,channel=6,data_latch=3,byte=0xE4)])
        self.assertEqual(d['music_recovery']['THZ-BA-music1']['next_read'],61)
        self.assertEqual(d['music_recovery']['THZ-BA-music2']['next_read'],37)

    def test_music_clock_observation_is_muted_and_genuine(self):
        d=report('facts.json');self.assertTrue(d['music_clock']['noise_muted'])
        self.assertEqual(d['music_clock']['noise_mode'],3);self.assertGreater(len(d['music_clock']['music_tone2_periods']),1)
        for r in d['native_interference'].values():
            self.assertTrue(r['core_state_reference_exact']);self.assertGreater(r['RNG_changes_across_muted_frame_pairs'],0)

    def test_new_PCM_voices_and_81_frozen_outputs(self):
        d=report('pcm.json');self.assertEqual(len(d['cases']),18);self.assertEqual(len(d['regressions']),81)
        for r in d['cases'].values():
            self.assertLessEqual(r['max_over_mix_and_voices'],5);self.assertEqual(r['register_counter_LFSR_failures'],[])
            self.assertTrue(r['partition_invariant']);self.assertEqual(len(r['voices']),4)
        self.assertTrue(all(r['PCM_identical_to_accepted_parent'] for r in d['regressions'].values()))

    def test_three_fresh_SCSP_reloads(self):
        d=report('isolation.json');self.assertEqual(set(d['cases']),{'B0','B7','BA'})
        self.assertTrue(all(r['fresh_process'] and r['PCM_identical'] and r['ROM_and_oracle_access_forbidden'] for r in d['cases'].values()))

    def test_SCSP_v1_horizon_and_old_data_preserved(self):
        d=report('emission.json');self.assertEqual(d['SCSP_version'],1);self.assertEqual(d['horizon'],4200)
        self.assertTrue(d['previous_27_headers_and_data_unchanged']);self.assertEqual(d['packed_bytes'],8942)
        self.assertEqual(d['incremental_data_bytes'],93)

    def test_all_70_catalogue_rows_and_original_names(self):
        d=report('coverage.json');self.assertEqual(len(d['entries']),70)
        self.assertEqual(d['counts'],{'fully-decoded-in-tested-scope':30,'partially-decoded':0,
           'format-understood-but-unverified':0,'unsupported-or-unknown':33,'empty-or-control':7})
        self.assertEqual(d['extracted_unique_headers'],30)
        for rid in (0xB0,0xB7,0xBA):
            r=next(r for r in d['entries'] if r['request_id']==rid);self.assertEqual(r['friendly_name'],f'Unknown ${rid:02X}')


if __name__=='__main__':unittest.main()
