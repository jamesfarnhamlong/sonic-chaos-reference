"""Common SFX scope, class, exact gate, held-output and ROM-free contracts."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


def report(name):return json.loads((ROOT/'data/m5-a2c1'/name).read_text())


class CommonSFX(unittest.TestCase):
    def test_six_classifications_and_three_only_scope(self):
        data=report('preflight.json');self.assertFalse(data['PCM_rendered']);self.assertFalse(data['candidate_promoted'])
        rows={r['request_id']:r for r in data['rows']}
        self.assertEqual(set(rows),{0xA4,0xA6,0xBF,0xA1,0xA2,0xA7})
        for rid,end in ((0xA4,82),(0xA6,41),(0xBF,21)):
            r=rows[rid];self.assertTrue(r['implementation_authorised']);self.assertEqual(r['original_inactive_tick'],end)
            self.assertEqual(r['output_class'],'tone-only');self.assertEqual(r['F3_executions'],0)
            self.assertEqual(r['SFX_slots_used'],[1]);self.assertEqual(r['post_inactive_physically_enabled_ticks'],0)
        self.assertEqual(rows[0xA2]['unverified_opcodes'],['FD'])
        self.assertEqual(rows[0xA7]['F3_control_modes'],[7])
        for rid in (0xA1,0xA2,0xA7):self.assertFalse(rows[rid]['implementation_authorised'])

    def test_every_emission_state_and_source_is_exact(self):
        d=report('emission.json');self.assertEqual(len(d['cases']),62)
        self.assertEqual(sum(c['ticks'] for c in d['cases'].values()),27327)
        self.assertEqual(sum(c['ordered_bytes'] for c in d['cases'].values()),130481)
        self.assertEqual(d['decoder_language_changes'],0)
        for c in d['cases'].values():
            self.assertEqual(c['status'],'PASS');self.assertEqual(c['failures'],[])
            self.assertEqual(c['ticks'],c['compared_ticks'])
        for path,h in d['source_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes().replace(b'\r\n',b'\n')).hexdigest(),h)

    def test_solo_terminal_and_post_windows(self):
        for rid,end in [('A4',82),('A6',41),('BF',21)]:
            r=report('facts.json')['termination'][rid]
            self.assertEqual(r['inactive_tick'],end);self.assertEqual(r['candidate_post_ticks'],32)
            self.assertEqual(r['original_preflight_post_ticks'],128);self.assertEqual(r['post_completion_port_bytes'],0)
            self.assertEqual(r['final_attenuation'],[15]*4);self.assertEqual(r['PCM_samples'],(end+32)*735)

    def test_retrigger_admission_and_priority_rejections(self):
        d=report('facts.json')
        self.assertEqual(d['retrigger_admissions']['ring-repeats']['original_admissions'],[[30,0xBF],[32,0xBF],[48,0xBF],[80,0xBF]])
        self.assertEqual(d['retrigger_admissions']['spring-repeats']['original_admissions'],[[30,0xA6],[33,0xA6],[60,0xA6],[100,0xA6]])
        self.assertEqual(d['replacement_priority']['original_admitted'],[[30,0xA6],[40,0xA4]])
        self.assertEqual(len(d['replacement_priority']['rejected_requests']),3)

    def test_real_noise_holds_and_concurrent_ownership(self):
        d=report('facts.json')
        for name,end,off,release in [('fixed-noise-spring',137,138,139),('hurt-held-noise',166,167,168)]:
            r=d['held_noise'][name];self.assertEqual(r['held_noise_ticks'],104)
            self.assertEqual(r['interval'][1],end);self.assertEqual(r['terminal_off_tick'],off)
            self.assertEqual(r['stream_release_tick'],release)
        self.assertEqual(d['concurrent_effect_slots'],3);self.assertTrue(d['coupled_ring_admitted'])

    def test_each_PCM_voice_partition_and_state(self):
        d=report('pcm.json');self.assertEqual(len(d['cases']),16)
        self.assertEqual(d['cases']['hurt-concurrent']['continuous_mix']['max_lsb'],5)
        self.assertEqual(d['cases']['hurt-held-noise']['continuous_mix']['max_lsb'],5)
        for c in d['cases'].values():
            self.assertLessEqual(c['max_over_mix_and_voices'],5);self.assertEqual(c['register_counter_LFSR_failures'],[])
            self.assertTrue(c['partition_invariant']);self.assertEqual(len(c['voices']),4)

    def test_all_46_frozen_PCM_outputs_unchanged(self):
        d=report('pcm.json')['regressions'];self.assertEqual(len(d),46)
        self.assertTrue(all(c['PCM_identical_to_accepted_parent'] for c in d.values()))

    def test_three_fresh_ROM_free_replays(self):
        d=report('isolation.json');self.assertEqual(set(d['cases']),{'A4','A6','BF'})
        self.assertTrue(all(c['fresh_process'] and c['ROM_and_oracle_access_forbidden'] and c['PCM_identical'] for c in d['cases'].values()))

    def test_previous_bank_and_guards_preserved(self):
        d=report('emission.json');self.assertEqual(d['SCSP_version'],1);self.assertEqual(d['horizon'],4200)
        self.assertTrue(d['previous_21_headers_and_data_unchanged']);self.assertEqual(d['packed_bytes'],8156)
        self.assertEqual(d['incremental_data_bytes'],120)
        f=report('facts.json');self.assertTrue(f['missing_program_rejected'])
        self.assertEqual(f['wrong_pitch_data_detected_tick'],1);self.assertEqual(f['missing_terminal_writes_detected_tick'],82)

    def test_all_70_rows_and_deferred_requests_preserved(self):
        d=report('coverage.json');self.assertEqual(len(d['entries']),70)
        self.assertEqual(d['counts'],{'fully-decoded-in-tested-scope':24,'partially-decoded':0,
             'format-understood-but-unverified':0,'unsupported-or-unknown':39,'empty-or-control':7})
        self.assertEqual(d['extracted_unique_headers'],24)
        for rid in (0xA1,0xA2,0xA7):
            r=next(x for x in d['entries'] if x['request_id']==rid)
            self.assertEqual(r['decoder_status'],'unsupported-or-unknown')
            self.assertFalse(r['C1_preflight_only']['runtime_record_extracted'])


if __name__=='__main__':unittest.main()
