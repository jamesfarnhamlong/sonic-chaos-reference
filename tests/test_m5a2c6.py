"""C6 full-state and operation-level evidence contracts, no private fixture requirement."""
import hashlib
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def report(n):return json.loads((ROOT/'data/m5-a2c6'/n).read_text())
class C6Proof(unittest.TestCase):
    def test_original_preflight_three_only(self):
        d=report('preflight.json');self.assertFalse(d['candidate_PCM_rendered']);self.assertFalse(d['candidate_promoted'])
        self.assertEqual({r['request_id'] for r in d['rows']},{0xB4,0xBD,0xC2})
        for r in d['rows']:
            self.assertEqual(r['SFX_slots_used'],[1]);self.assertEqual(r['F3_executions'],0);self.assertEqual(r['FD_executions'],[])
            self.assertEqual(r['post_completion_observed_ticks'],128);self.assertEqual(r['post_inactive_physically_enabled_ticks'],0)
    def test_headers_and_lifetimes(self):
        for r in report('preflight.json')['rows']:
            priority,end={0xB4:(120,31),0xBD:(88,23),0xC2:(64,46)}[r['request_id']]
            self.assertEqual(r['priority']['stored'],priority);self.assertEqual(r['original_inactive_tick'],end)
            self.assertEqual(r['header']['stream_initial_flags'],[128]);self.assertEqual(r['header']['streams'][0]['latch'],'0xc0')
            self.assertEqual(r['unverified_opcodes'],[])
    def test_all_158_full_state_cases(self):
        d=report('emission.json');self.assertEqual(len(d['cases']),158);self.assertEqual(sum(n.startswith('C5-') for n in d['cases']),138)
        self.assertEqual(sum(x['ticks'] for x in d['cases'].values()),42075);self.assertEqual(sum(x['ordered_bytes'] for x in d['cases'].values()),196084)
        self.assertTrue(d['zero_tolerance']);self.assertTrue(d['independent_candidate']);self.assertEqual(d['decoder_language_changes'],0)
        for r in d['cases'].values():self.assertEqual((r['status'],r['failures'],r['compared_ticks']),('PASS',[],r['ticks']))
        for p,h in d['source_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes().replace(b'\r\n',b'\n')).hexdigest(),h)
    def test_operation_gate_all_new_contexts(self):
        d=report('operations.json');self.assertEqual(len(d['cases']),20);self.assertTrue(d['zero_tolerance'] and d['independent_candidate_first'])
        self.assertFalse(d['decoder_semantics_changed']);self.assertTrue(all(x['status']=='PASS' for x in d['cases'].values()))
        self.assertEqual(hashlib.sha256((ROOT/'tools/m5a2c6/operations.py').read_bytes().replace(b'\r\n',b'\n')).hexdigest(),d['diagnostic_source_sha256'])
    def test_B4_shared_IY_reload_actual_transitions(self):
        d=report('operations.json');r=d['cases']['solo-B4'];s=d['solo']['solo-B4']
        self.assertEqual(r['pitch_operations'],30);self.assertEqual(r['reload_sources'],{'DE06':6})
        self.assertEqual(s['reload_ticks'],[5,10,15,20,25,30]);self.assertEqual(s['reload_values'],[0]);self.assertTrue(s['pitch_channel_before_after_exact'])
    def test_BD_visited_envelope_not_static_length(self):
        d=report('operations.json')['cases']['solo-BD'];self.assertEqual(d['command_counts'],{'E6':2,'F0':4,'F5':4,'F8':2,'F9':2})
        self.assertEqual(d['table_envelope_visits'],{'13':dict(visits=18,indices=[0,1,2,3,4,5],controls=[])})
    def test_C2_counted_branches_transpose_timing_targets(self):
        d=report('operations.json');r=d['cases']['solo-C2'];s=d['solo']['solo-C2']
        self.assertEqual(r['command_counts']['F7'],9);self.assertEqual(r['command_counts']['FB'],9)
        self.assertEqual(s['F7_ticks'],[26,30,30,34,38,38,42,46,46]);self.assertEqual(s['FB_ticks'],s['F7_ticks'])
        self.assertEqual(s['F7_return_targets'],{'A3EF':5,'A400':3,'A40B':1});self.assertEqual((s['counted_branches_taken'],s['counted_fallthroughs']),(5,4))
        self.assertTrue(s['transpose_updates_exact'] and s['command_channel_before_after_exact'])
    def test_wrong_reload_detected_by_state_even_if_writes_match(self):
        r=report('facts.json')['operation_negatives']['saved_pointer_reload'];self.assertEqual(r['first_channel_state_difference'],5);self.assertIsNone(r['first_ordered_write_difference'])
    def test_omitted_loop_and_transpose_fail(self):
        d=report('facts.json')['operation_negatives']
        for n in ['omitted_counted_branch','omitted_transpose']:self.assertEqual(d[n],dict(first_channel_state_difference=26,first_ordered_write_difference=26))
    def test_actual_terminal_and_post_window(self):
        d=report('facts.json')['termination']
        for rid,end in [('B4',31),('BD',23),('C2',46)]:
            r=d[rid];self.assertEqual(r['inactive_tick'],end);self.assertEqual(r['candidate_post_ticks'],32);self.assertEqual(r['post_writes'],0)
            self.assertEqual(r['final_attenuation'],[15]*4);self.assertEqual(r['PCM_samples'],(end+32)*735)
    def test_priority_chain_and_rejected_reset(self):
        a=report('facts.json')['admissions'];self.assertEqual(a['tone2-priority-chain'],[[30,0xC2],[40,0xBD],[42,0xB4],[80,0xC2]])
        self.assertEqual(a['B4-block-lower'],[[1,0xB4],[40,0xBD]]);self.assertEqual(a['B4-rejected-reset'],[[1,0xB4],[40,0xC2]])
    def test_retriggers_without_invented_F3(self):
        d=report('facts.json')
        for rid,ticks in [('B4',[30,32,50,100]),('BD',[30,34,43,90]),('C2',[30,34,60,130])]:
            n=rid+'-retrigger';self.assertEqual(d['admissions'][n],[[t,int(rid,16)] for t in ticks]);self.assertEqual(d['F3_controls'][n],[])
    def test_concurrent_slots_and_fixed_held_output(self):
        d=report('facts.json')['noise_interactions'];r=d['fixed-B8-with-B4']
        self.assertEqual(r['physical_tone2_and_noise_enabled_ticks'],30);self.assertEqual(r['noise_write_inhibited_but_enabled_ticks'],102)
        self.assertEqual(r['noise_write_inhibited_but_enabled_range'],[36,137]);self.assertEqual(d['B4-BA-concurrent']['maximum_simultaneous_SFX_slots'],3)
    def test_current_latch_DE11(self):
        r=report('facts.json')['DE11_restore_contexts'];self.assertEqual(r['fixed-B8-with-B4'],[dict(tick=139,channel=6,data_latch=7,byte=0)])
        self.assertEqual(r['B4-BA-concurrent'],[dict(tick=34,channel=6,data_latch=5,byte=228)])
        self.assertEqual(r['solo-B4'],[])
    def test_actual_music_next_read(self):
        d=report('facts.json')['music_recovery']
        for n,s,e,t in [('THZ-B4',30,59,61),('THZ-BD',30,51,61),('THZ-C2',30,74,97)]:self.assertEqual(d[n],dict(suppression=[s,e],next_read=t))
    def test_all_new_native_states(self):
        d=report('facts.json')['native_diagnostics'];self.assertEqual(len(d),20)
        self.assertTrue(all(r['core_state_reference_exact'] and r['instant_F3_states_exact'] and r['all_F3_preserve_noise_countdown'] for r in d.values()))
    def test_C3_dedup_negative_preserved(self):
        d=report('facts.json')['C3_duplicate_control_negative'];self.assertEqual(set(d),{'B0','B7'})
        for r in d.values():
            self.assertEqual((r['LFSR_mismatching_ticks'],r['max_signed16_error']),(36,16384));self.assertEqual(r['second_F3']['RNG_after'],32768)
            self.assertEqual((r['second_F3']['noise_counter_before'],r['second_F3']['noise_counter_after']),(21,21))
    def test_new_failure_controls(self):
        d=report('facts.json');self.assertTrue(d['corrupt_SCSP_rejected'])
        for rid,end in [('B4',31),('BD',23),('C2',46)]:
            r=d['negative_controls'][rid];self.assertEqual(r['missing_terminal_detected_tick'],end)
            self.assertTrue(r['missing_required_byte']['rejected'] and r['unsupported_command_E2']['rejected'])
    def test_PCM_and_all_138_frozen_outputs(self):
        d=report('pcm.json');self.assertEqual(len(d['cases']),20);self.assertEqual(len(d['regressions']),138);self.assertFalse(d['thresholds_changed'])
        for r in d['cases'].values():
            self.assertLessEqual(r['max_over_mix_and_voices'],3);self.assertEqual(r['register_counter_LFSR_failures'],[])
            self.assertEqual(set(r['voices']),{'0','1','2','3'});self.assertTrue(r['partition_invariant']);self.assertEqual(r['samples'],r['ticks']*735)
        self.assertTrue(all(r['PCM_identical_to_accepted_parent'] and r['partition_invariant'] for r in d['regressions'].values()))
    def test_twenty_fresh_process_replays(self):
        d=report('isolation.json');self.assertEqual(len(d['cases']),20)
        self.assertTrue({'solo-B4','solo-BD','solo-C2'}<=set(d['cases']))
        self.assertTrue(all(r['fresh_process'] and r['ROM_and_oracle_access_forbidden'] and r['PCM_identical'] for r in d['cases'].values()))
    def test_SCSP_integrity_scope_and_storage(self):
        d=report('emission.json');self.assertEqual((d['SCSP_version'],d['horizon']),(1,4200));self.assertTrue(d['previous_36_headers_and_data_unchanged'])
        self.assertEqual((d['packed_bytes'],d['incremental_packed_bytes'],d['incremental_data_bytes'],d['segments']),(10234,567,131,67))
        self.assertEqual(max(r['max_stream_operations_per_tick'] for r in d['cases'].values()),26)
    def test_full_catalogue_and_remaining_counts(self):
        d=report('coverage.json');self.assertEqual(len(d['entries']),70);self.assertEqual(d['extracted_unique_headers'],39)
        self.assertEqual(d['counts'],{'fully-decoded-in-tested-scope':39,'partially-decoded':0,'format-understood-but-unverified':0,'unsupported-or-unknown':24,'empty-or-control':7})
        r=d['remaining_original_classes'];self.assertEqual(r['counts']['tone2-only'],10);self.assertEqual(r['counts']['coupled-white-noise-single-F3'],3);self.assertEqual(r['remaining_music'],11)
        for rid in [0xB4,0xBD,0xC2]:self.assertNotIn('original_only_preflight',next(r for r in d['entries'] if r['request_id']==rid))
    def test_strategic_gate_is_planning_only(self):
        d=report('planning.json');self.assertTrue(d['planning_only']);self.assertFalse(d['implementation_started'])
        self.assertEqual(len(d['A_further_catalogue']['remaining_tone2']),10);self.assertEqual(len(d['A_further_catalogue']['parked_single_F3']),3)
        self.assertEqual(len(d['A_further_catalogue']['remaining_music']),11);self.assertTrue(d['recommendation'].startswith('B:'))
        self.assertIn('original stream interpreter',d['B_native_feasibility']['A1P_did_not_prove'])
if __name__=='__main__':unittest.main()
