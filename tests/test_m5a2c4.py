"""Single-F3 class boundaries and retained exact/phase-sensitive evidence contracts."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


def report(name):return json.loads((ROOT/'data/m5-a2c4'/name).read_text())


class SingleF3Evidence(unittest.TestCase):
    def test_original_only_preflight_and_names(self):
        d=report('preflight.json');self.assertFalse(d['candidate_PCM_rendered']);self.assertFalse(d['candidate_promoted'])
        self.assertEqual({r['request_id'] for r in d['rows']},{0xAF,0xB1,0xB9})
        for r in d['rows']:
            self.assertEqual(r['label'],f"Unknown ${r['request_id']:02X}")
            self.assertEqual(r['output_class'],'tone2-clocked white noise');self.assertEqual(r['SFX_slots_used'],[2])
            self.assertEqual(r['priority']['stored'],72);self.assertEqual(r['maximum_simultaneous_SFX_slots'],1)

    def test_actual_language_and_reader_boundary(self):
        rows={r['request_id']:r for r in report('preflight.json')['rows']}
        self.assertEqual(set(rows[0xAF]['reached_opcodes']),{'E0','F0','F2','F3','F5'})
        self.assertEqual(set(rows[0xB1]['reached_opcodes']),{'E0','F0','F2','F3'})
        self.assertEqual(rows[0xB1]['header']['stream_initial_flags'],[136])
        self.assertEqual(rows[0xB9]['reached_opcodes']['F8'],6);self.assertEqual(rows[0xB9]['reached_opcodes']['F9'],6)
        self.assertEqual(rows[0xB9]['reached_opcodes']['F7'],5)
        for r in rows.values():
            self.assertEqual(r['unverified_opcodes'],[]);self.assertNotIn('FD',r['reached_opcodes'])
            self.assertFalse(r['table_pitch_required'])

    def test_all_118_exact_original_cases_and_source_receipts(self):
        d=report('emission.json');self.assertEqual(len(d['cases']),118)
        self.assertEqual(sum(r['ticks'] for r in d['cases'].values()),35704)
        self.assertEqual(sum(r['ordered_bytes'] for r in d['cases'].values()),170201)
        self.assertTrue(d['independent_candidate']);self.assertTrue(d['zero_tolerance']);self.assertEqual(d['decoder_language_changes'],0)
        self.assertEqual(sum(n.startswith('C3-') for n in d['cases']),99)
        for r in d['cases'].values():
            self.assertEqual(r['status'],'PASS');self.assertEqual(r['failures'],[]);self.assertEqual(r['compared_ticks'],r['ticks'])
        for p,h in d['source_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes().replace(b'\r\n',b'\n')).hexdigest(),h)

    def test_finite_and_post_completion_physical_output(self):
        d=report('facts.json')['termination']
        for rid,end in [('AF',68),('B1',22),('B9',31)]:
            r=d[rid];self.assertEqual(r['inactive_tick'],end);self.assertEqual(r['candidate_post_ticks'],32)
            self.assertEqual(r['original_preflight_post_ticks'],128);self.assertEqual(r['post_writes'],0)
            self.assertEqual(r['final_attenuation'],[15]*4);self.assertEqual(r['PCM_samples'],(end+32)*735)

    def test_single_F3_measured_not_multiplied(self):
        for rid in ['AF','B1','B9']:
            d=report('facts.json')['native_diagnostics']['solo-'+rid]
            self.assertEqual(d['F3_count'],1);self.assertEqual(d['F3_ticks'],[1]);self.assertEqual(d['F3_modes'],[7])

    def test_phase_retriggers_reset_LFSR_preserve_countdown(self):
        d=report('facts.json')
        for rid,ticks in [('AF',[30,32,57,140]),('B1',[30,33,45,90]),('B9',[30,32,47,100])]:
            name=rid+'-retrigger';self.assertEqual(d['admissions'][name],[[t,int(rid,16)] for t in ticks])
            c=d['F3_controls'][name];self.assertEqual([x['tick'] for x in c],ticks)
            self.assertGreater(len({x['RNG_before'] for x in c}),1)
            self.assertTrue(all(x['RNG_after']==32768 and x['noise_counter_before']==x['noise_counter_after'] for x in c))

    def test_blocked_requests_are_not_claimed_as_replacement(self):
        d=report('facts.json')['admissions']
        self.assertEqual(d['B1-block-ring'],[[1,0xB1],[30,0xBF]])
        self.assertEqual(d['AF-to-A7'],[[30,0xAF]])
        self.assertEqual(d['B1-to-B0'],[[30,0xB1]])
        self.assertEqual(d['AF-tone2-interrupt'],[[30,0xAF],[40,0xA4]])

    def test_authentic_noise_replacement_and_concurrent_tone1(self):
        d=report('facts.json');self.assertEqual(d['admissions']['B9-to-B7'],[[30,0xB9],[45,0xB7]])
        self.assertEqual(d['native_diagnostics']['B9-to-B7']['F3_ticks'],[30,45,48])
        self.assertEqual(d['native_diagnostics']['B9-to-B7']['F3_modes'],[7,3,3])
        self.assertEqual(d['admissions']['BA-to-B9'],[[30,0xBA],[32,0xB9]])
        self.assertEqual(d['native_diagnostics']['BA-to-B9']['maximum_simultaneous_SFX_slots'],2)

    def test_next_read_recovery_and_DE11_current_latch(self):
        d=report('facts.json');r=d['music_recovery']
        self.assertEqual(r['THZ-AF-music2']['next_read'],109);self.assertEqual(r['THZ-AF-music3']['next_read'],103)
        self.assertEqual(r['THZ-B9-music2']['next_read'],61);self.assertEqual(r['THZ-late-B9-music2']['next_read'],109)
        self.assertEqual(d['DE11_restore_contexts']['solo-B1'],[dict(tick=22,channel=6,data_latch=7,byte=0)])
        self.assertEqual(d['DE11_restore_contexts']['THZ-B1'],[dict(tick=51,channel=6,data_latch=0,byte=228)])
        self.assertEqual(d['DE11_restore_contexts']['THZ-AF'],[dict(tick=97,channel=6,data_latch=3,byte=228)])

    def test_native_continuity_all_new_contexts(self):
        d=report('facts.json')['native_diagnostics'];self.assertEqual(len(d),19)
        for r in d.values():
            self.assertTrue(r['core_state_reference_exact']);self.assertTrue(r['instant_F3_states_exact'])
            self.assertTrue(r['all_F3_preserve_noise_countdown'])
        self.assertGreater(d['AF-tone2-interrupt']['RNG_changes_across_muted_frame_pairs'],0)

    def test_C3_dedup_negative_is_fresh_and_unchanged(self):
        d=report('facts.json')['C3_duplicate_control_negative'];self.assertEqual(set(d),{'B0','B7'})
        for r in d.values():
            self.assertEqual(r['LFSR_mismatching_ticks'],36);self.assertEqual(r['max_signed16_error'],16384)
            self.assertEqual(r['second_F3']['RNG_after'],32768)
            self.assertEqual(r['second_F3']['noise_counter_before'],21);self.assertEqual(r['second_F3']['noise_counter_after'],21)

    def test_single_control_and_terminal_negatives_fail(self):
        d=report('facts.json')['negative_controls']
        for rid,end in [('AF',68),('B1',22),('B9',31)]:
            self.assertEqual(d[rid]['missing_F3_detected_tick'],1);self.assertEqual(d[rid]['missing_terminal_detected_tick'],end)

    def test_PCM_four_voices_and_99_frozen_outputs(self):
        d=report('pcm.json');self.assertEqual(len(d['cases']),19);self.assertEqual(len(d['regressions']),99)
        self.assertFalse(d['thresholds_changed'])
        for r in d['cases'].values():
            self.assertLessEqual(r['max_over_mix_and_voices'],5);self.assertEqual(r['register_counter_LFSR_failures'],[])
            self.assertEqual(set(r['voices']),{'0','1','2','3'});self.assertTrue(r['partition_invariant'])
            self.assertEqual(r['samples'],735*r['ticks']);self.assertTrue(r['attenuation_register_and_driver_envelope_state_exact'])
        self.assertTrue(all(r['PCM_identical_to_accepted_parent'] and r['partition_invariant'] for r in d['regressions'].values()))

    def test_all_19_fresh_process_replays(self):
        d=report('isolation.json');self.assertEqual(len(d['cases']),19)
        self.assertTrue({'solo-AF','solo-B1','solo-B9'}<=set(d['cases']))
        for r in d['cases'].values():self.assertTrue(r['fresh_process'] and r['ROM_and_oracle_access_forbidden'] and r['PCM_identical'])

    def test_SCSP_v1_horizon_old_programs_and_measured_expansion(self):
        d=report('emission.json');self.assertEqual(d['SCSP_version'],1);self.assertEqual(d['horizon'],4200)
        self.assertTrue(d['previous_30_headers_and_data_unchanged']);self.assertEqual(d['packed_bytes'],9352)
        self.assertEqual(d['incremental_packed_bytes'],410);self.assertEqual(d['incremental_data_bytes'],88)
        self.assertEqual(d['segments'],59)

    def test_complete_catalogue_actual_counts_and_unknown_names(self):
        d=report('coverage.json');self.assertEqual(len(d['entries']),70);self.assertEqual(d['extracted_unique_headers'],33)
        self.assertEqual(d['counts'],{'fully-decoded-in-tested-scope':33,'partially-decoded':0,'format-understood-but-unverified':0,'unsupported-or-unknown':30,'empty-or-control':7})
        for rid in [0xAF,0xB1,0xB9]:self.assertEqual(next(r['friendly_name'] for r in d['entries'] if r['request_id']==rid),f'Unknown ${rid:02X}')

    def test_remaining_classes_do_not_promote_unexecuted_ids(self):
        d=report('coverage.json');r=d['remaining_original_classes']
        self.assertEqual(r['counts']['tone2-only'],16);self.assertEqual(r['counts']['coupled-white-noise-single-F3'],3)
        self.assertEqual(sum(r['counts'].values()),19);self.assertEqual(r['remaining_music'],11)
        self.assertEqual(r['classes']['coupled-white-noise-single-F3'],['BB','BE','C4'])
        for b in d['expansion_batches']:self.assertTrue(b['proposal_only'])


if __name__=='__main__':unittest.main()
