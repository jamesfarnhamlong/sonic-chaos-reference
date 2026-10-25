"""Tone2 variation, preflight-only boundaries and exact preservation contracts."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


def report(name):return json.loads((ROOT/'data/m5-a2c5'/name).read_text())


class Tone2Variation(unittest.TestCase):
    def test_six_original_only_preflights_three_implementation_permissions(self):
        d=report('preflight.json');self.assertFalse(d['candidate_PCM_rendered']);self.assertFalse(d['candidate_promoted'])
        self.assertEqual({r['request_id'] for r in d['rows']},{0xA5,0xA9,0xAA,0xB4,0xBD,0xC2})
        self.assertEqual({r['request_id'] for r in d['rows'] if r['implementation_authorised']},{0xA5,0xA9,0xAA})
        for r in d['rows']:
            self.assertEqual(r['output_class'],'tone-only');self.assertEqual(r['SFX_slots_used'],[1]);self.assertEqual(r['F3_executions'],0)
            self.assertEqual(r['post_completion_observed_ticks'],128);self.assertEqual(r['post_inactive_physically_enabled_ticks'],0)

    def test_original_header_priority_lifetime_and_reader(self):
        rows={r['request_id']:r for r in report('preflight.json')['rows']}
        for rid,priority,end in [(0xA5,56,128),(0xA9,120,66),(0xAA,112,5),(0xB4,120,31),(0xBD,88,23),(0xC2,64,46)]:
            r=rows[rid];self.assertEqual(r['priority']['stored'],priority);self.assertEqual(r['original_inactive_tick'],end)
            self.assertEqual(r['header']['stream_initial_flags'],[128]);self.assertEqual(r['header']['duration_multiplier'],1)
            self.assertEqual(r['header']['streams'][0]['latch'],'0xc0');self.assertEqual(r['initial_envelope_base'],0x49FD)
            self.assertEqual(r['FD_executions'],[]);self.assertEqual(r['raw_frequency_reader_visits'],0)

    def test_original_reached_language_and_envelope_variants(self):
        rows={r['request_id']:r for r in report('preflight.json')['rows']}
        self.assertEqual(set(rows[0xA5]['reached_opcodes']),{'E0','F0','F2'})
        self.assertEqual(rows[0xA5]['pitch_selectors'],[128]);self.assertEqual(rows[0xA5]['volume_envelope_selectors'],[128])
        self.assertEqual(rows[0xA9]['reached_opcodes']['F8'],3);self.assertEqual(rows[0xA9]['reached_opcodes']['F9'],3)
        self.assertEqual(set(rows[0xAA]['reached_opcodes']),{'F2','F5'})
        self.assertEqual(rows[0xBD]['volume_envelope_selectors'],[0,13]);self.assertEqual(rows[0xC2]['reached_opcodes']['FB'],9)
        for r in rows.values():
            self.assertEqual(r['unverified_opcodes'],[]);self.assertFalse(r['table_pitch_required'])
            self.assertTrue(all(x['known_control'] and x['first_control']=='82' for x in r['table_envelope_preflight']))

    def test_all_138_exact_cases_and_source_hashes(self):
        d=report('emission.json');self.assertEqual(len(d['cases']),138)
        self.assertEqual(sum(r['ticks'] for r in d['cases'].values()),39319)
        self.assertEqual(sum(r['ordered_bytes'] for r in d['cases'].values()),185185)
        self.assertEqual(sum(n.startswith('C4-') for n in d['cases']),118)
        self.assertEqual(d['decoder_language_changes'],0);self.assertTrue(d['zero_tolerance']);self.assertTrue(d['independent_candidate'])
        for r in d['cases'].values():
            self.assertEqual(r['status'],'PASS');self.assertEqual(r['failures'],[]);self.assertEqual(r['compared_ticks'],r['ticks'])
        for p,h in d['source_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes().replace(b'\r\n',b'\n')).hexdigest(),h)

    def test_authentic_completion_and_32_post_ticks(self):
        d=report('facts.json')['termination']
        for rid,end in [('A5',128),('A9',66),('AA',5)]:
            r=d[rid];self.assertEqual(r['inactive_tick'],end);self.assertEqual(r['candidate_post_ticks'],32)
            self.assertEqual(r['post_writes'],0);self.assertEqual(r['final_attenuation'],[15]*4);self.assertEqual(r['PCM_samples'],(end+32)*735)

    def test_priority_replacement_rejection_later_admission(self):
        a=report('facts.json')['admissions']
        self.assertEqual(a['tone2-priority-chain'],[[30,0xA5],[40,0xAA],[42,0xA9],[110,0xA5]])
        self.assertEqual(a['A9-block-lower'],[[1,0xA9],[70,0xAA]])

    def test_reset_admission_is_priority_sensitive(self):
        a=report('facts.json')['admissions']
        self.assertEqual(a['A9-rejected-reset'],[[1,0xA9],[70,0xAA]])
        self.assertEqual(a['reset-fresh-AA'],[[30,0xA5],[60,0xAA]])
        d=report('emission.json')['cases'];self.assertEqual(d['A9-rejected-reset']['status'],'PASS');self.assertEqual(d['reset-fresh-AA']['status'],'PASS')

    def test_noise_overlap_is_physical_not_only_slot_union(self):
        d=report('facts.json')['noise_interactions'];r=d['fixed-B8-with-A9']
        self.assertEqual(r['simultaneous_tone2_noise_slot_ticks'],65);self.assertEqual(r['physical_tone2_and_noise_enabled_ticks'],62)
        self.assertEqual(r['noise_write_inhibited_but_enabled_ticks'],67);self.assertEqual(r['noise_write_inhibited_but_enabled_range'],[71,137])
        self.assertEqual(d['A9-BA-concurrent']['maximum_simultaneous_SFX_slots'],3)
        for n in ['white-A3-to-A9','periodic-B7-to-AA','coupled-A7-to-A5','noise-B0-over-A5']:
            self.assertGreater(d[n]['simultaneous_tone2_noise_slot_ticks'],0)
            self.assertEqual(d[n]['physical_tone2_and_noise_enabled_ticks'],0)

    def test_DE11_restore_uses_actual_current_latch(self):
        r=report('facts.json')['DE11_restore_contexts']
        for n in ['solo-A5','solo-A9','solo-AA']:self.assertEqual(r[n],[])
        self.assertEqual(r['white-A3-to-A9'],[dict(tick=49,channel=6,data_latch=5,byte=0)])
        self.assertEqual(r['fixed-B8-with-A9'],[dict(tick=139,channel=6,data_latch=7,byte=0)])
        self.assertEqual(r['A9-BA-concurrent'],[dict(tick=34,channel=6,data_latch=5,byte=228)])

    def test_music_next_read_recovery(self):
        r=report('facts.json')['music_recovery']
        for name,bounds,nxt in [('THZ-A5',[30,156],161),('THZ-A9',[30,94],97),('THZ-AA',[30,33],37)]:
            self.assertEqual(r[name],dict(suppression=bounds,next_read=nxt))

    def test_retrigger_counts_do_not_invent_F3(self):
        d=report('facts.json')
        for rid,ticks in [('A5',[30,35,90,240]),('A9',[30,34,80,180]),('AA',[30,32,39,73])]:
            n=rid+'-retrigger';self.assertEqual(d['admissions'][n],[[t,int(rid,16)] for t in ticks])
            self.assertEqual(d['F3_controls'][n],[])
        self.assertEqual(d['native_diagnostics']['periodic-B7-to-AA']['F3_count'],2)

    def test_native_register_counter_LFSR_continuity(self):
        d=report('facts.json')['native_diagnostics'];self.assertEqual(len(d),20)
        for r in d.values():self.assertTrue(r['core_state_reference_exact'] and r['instant_F3_states_exact'] and r['all_F3_preserve_noise_countdown'])

    def test_original_C3_duplicate_negative_remains_explicit(self):
        d=report('facts.json')['C3_duplicate_control_negative'];self.assertEqual(set(d),{'B0','B7'})
        for r in d.values():
            self.assertEqual(r['LFSR_mismatching_ticks'],36);self.assertEqual(r['max_signed16_error'],16384)
            self.assertEqual(r['second_F3']['RNG_after'],32768)
            self.assertEqual(r['second_F3']['noise_counter_before'],21);self.assertEqual(r['second_F3']['noise_counter_after'],21)

    def test_new_data_language_and_terminal_failure_controls(self):
        d=report('facts.json');self.assertTrue(d['corrupt_SCSP_rejected']);self.assertTrue(d['preflight_only_records_absent'])
        for rid,pitch_or_env,end in [('A5',7,128),('A9',33,66),('AA',1,5)]:
            r=d['negative_controls'][rid];self.assertEqual(r['wrong_pitch_or_envelope_detected_tick'],pitch_or_env)
            self.assertEqual(r['missing_terminal_detected_tick'],end)
            self.assertTrue(r['missing_required_byte']['rejected']);self.assertTrue(r['unsupported_command_E2']['rejected'])

    def test_new_PCM_four_voices_and_118_frozen_outputs(self):
        d=report('pcm.json');self.assertEqual(len(d['cases']),20);self.assertEqual(len(d['regressions']),118)
        self.assertFalse(d['thresholds_changed'])
        for r in d['cases'].values():
            self.assertLessEqual(r['max_over_mix_and_voices'],4);self.assertEqual(r['register_counter_LFSR_failures'],[])
            self.assertEqual(set(r['voices']),{'0','1','2','3'});self.assertTrue(r['partition_invariant'])
            self.assertEqual(r['samples'],735*r['ticks'])
        self.assertTrue(all(r['PCM_identical_to_accepted_parent'] and r['partition_invariant'] for r in d['regressions'].values()))

    def test_all_20_fresh_process_SCSP_replays(self):
        d=report('isolation.json');self.assertEqual(len(d['cases']),20)
        self.assertTrue({'solo-A5','solo-A9','solo-AA'}<=set(d['cases']))
        for r in d['cases'].values():self.assertTrue(r['fresh_process'] and r['ROM_and_oracle_access_forbidden'] and r['PCM_identical'])

    def test_SCSP_and_complete_catalogue_counts(self):
        d=report('emission.json');self.assertEqual(d['SCSP_version'],1);self.assertEqual(d['horizon'],4200)
        self.assertTrue(d['previous_33_headers_and_data_unchanged']);self.assertEqual(d['packed_bytes'],9667)
        self.assertEqual(d['incremental_data_bytes'],64);self.assertEqual(d['incremental_packed_bytes'],315);self.assertEqual(d['segments'],61)
        c=report('coverage.json');self.assertEqual(len(c['entries']),70);self.assertEqual(c['extracted_unique_headers'],36)
        self.assertEqual(c['counts'],{'fully-decoded-in-tested-scope':36,'partially-decoded':0,'format-understood-but-unverified':0,'unsupported-or-unknown':27,'empty-or-control':7})
        self.assertEqual(next(r['friendly_name'] for r in c['entries'] if r['request_id']==0xA5),'Unknown $A5')

    def test_preflight_only_does_not_promote_and_remaining_classes(self):
        d=report('coverage.json');r=d['remaining_original_classes']
        self.assertEqual(r['counts']['tone2-only'],13);self.assertEqual(r['counts']['coupled-white-noise-single-F3'],3)
        self.assertEqual(r['fresh_preflight_only'],['B4','BD','C2']);self.assertEqual(len(r['historical_tone2_not_freshly_inspected']),10)
        self.assertEqual(r['remaining_music'],11)
        for rid in [0xB4,0xBD,0xC2]:
            row=next(x for x in d['entries'] if x['request_id']==rid)
            self.assertEqual(row['decoder_status'],'unsupported-or-unknown');self.assertTrue(row['original_only_preflight'])
        for b in d['expansion_batches']:self.assertTrue(b['proposal_only'])


if __name__=='__main__':unittest.main()
