"""Finite expansion contracts and E1-specific fail-fast controls."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2'),str(ROOT/'tests')]
from test_m5a2 import synthetic
from m5a2.bank import pack,unpack
from m5a2.decoder import DecodeError,Decoder as OldDecoder
from m5a2b1.decoder import Decoder


def report(name):return json.loads((ROOT/'data/m5-a2b1'/name).read_text())


class E1Controls(unittest.TestCase):
    def test_signed_fine_pitch_without_song_constants(self):
        for value,signed in ((1,1),(255,-1),(128,-128)):
            b=synthetic((0xE1,value,0x81,2,0xF2,0));m=Decoder(unpack(pack(b)));m.direct(0x81);m.tick()
            self.assertEqual(m.ch[0][37],value)
            self.assertEqual(m.psg.tone[0],0x234+signed)

    def test_old_decoder_rejects_extension(self):
        m=OldDecoder(synthetic((0xE1,1,0x81,2)));m.direct(0x81)
        with self.assertRaises(DecodeError):m.tick()

    def test_truncated_E1_is_not_silence(self):
        m=Decoder(synthetic((0xE1,)));m.direct(0x81)
        with self.assertRaises(DecodeError):m.tick()

    def test_other_unverified_commands_still_fail(self):
        for op in (0xE2,0xE8,0xED,0xF4,0xFA,0xFD):
            m=Decoder(synthetic((op,0)));m.direct(0x81)
            with self.assertRaises(DecodeError):m.tick()


class BatchEvidence(unittest.TestCase):
    def test_twelve_preflight_exact_scope(self):
        rows=report('preflight.json')['rows']
        self.assertEqual([r['request_id'] for r in rows],[0x84,0x85,0x86,0x87,0x89,0x8A,0x8E,0x94,0x96,0x97,0x98,0x9A])
        for r in rows:
            self.assertEqual(r['original_inactive_tick'],r['inherited_inactive_tick'])
            self.assertFalse(r['coverage_promotion'])
            self.assertEqual(r['new_PCM_renders'],0)
            self.assertEqual(r['static']['unclassified_opcodes'],[])
            self.assertTrue(all(e['known_control'] for e in r['table_envelope_preflight']))

    def test_every_new_and_regression_tick_exact(self):
        gate=report('emission.json')
        self.assertEqual(len(gate['cases']),33)
        for c in gate['cases'].values():
            self.assertEqual(c['status'],'PASS');self.assertEqual(c['failures'],[])
            self.assertEqual(c['ticks'],c['compared_ticks'])
        self.assertEqual(sum(c['ticks'] for c in gate['cases'].values()),16137)
        self.assertEqual(sum(c['ordered_bytes'] for c in gate['cases'].values()),79380)
        for path,digest in gate['source_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes().replace(b'\r\n',b'\n')).hexdigest(),digest)

    def test_all_six_authentic_terminations_and_post_windows(self):
        facts=report('facts.json')
        for key,end in {'84':1088,'85':432,'86':300,'87':408,'89':242,'8A':179}.items():
            r=facts['termination'][key]
            self.assertEqual(r['inactive_tick'],end)
            self.assertEqual(r['post_completion_ticks'],32)
            self.assertEqual(r['post_completion_port_bytes'],0)
            self.assertTrue(r['all_slot_flags_inactive'])
        tail=facts['original_8A_terminal']
        self.assertEqual(tail['prior_data_latch_register'],5)
        self.assertEqual(tail['restore_tick'],1)
        self.assertEqual(tail['post_completion_PCM']['candidate']['constant_signed16'],8192)
        self.assertEqual(tail['post_completion_PCM']['reference']['AC_standard_deviation'],0)

    def test_PCM_separate_new_measurements_and_regressions(self):
        pcm=report('pcm.json');self.assertEqual(len(pcm['cases']),13);self.assertEqual(len(pcm['regressions']),20)
        for c in pcm['cases'].values():
            self.assertEqual(c['register_counter_LFSR_failures'],[])
            self.assertTrue(c['partition_invariant'])
            self.assertLessEqual(c['max_over_mix_and_voices'],5)
            self.assertEqual(len(c['voices']),4)
        self.assertTrue(all(c['PCM_identical_to_accepted_A2'] for c in pcm['regressions'].values()))

    def test_six_separate_ROM_free_reloads(self):
        data=report('isolation.json')
        self.assertEqual(set(data['cases']),{'84','85','86','87','89','8A'})
        self.assertTrue(all(c['fresh_process'] and c['PCM_identical'] and c['ROM_and_oracle_access_forbidden'] for c in data['cases'].values()))

    def test_horizon_and_previous_bank_compatibility(self):
        data=report('emission.json')
        self.assertEqual(data['SCSP_version'],1);self.assertEqual(data['horizon'],4200)
        self.assertTrue(data['previous_nine_headers_and_data_unchanged'])
        self.assertEqual(data['packed_bytes'],6065)
        self.assertEqual(data['incremental_packed_bytes'],1780)

    def test_precise_coverage_and_deferred_scope(self):
        data=report('coverage.json')
        self.assertEqual(len(data['entries']),70)
        self.assertEqual(data['counts'],{'fully-decoded-in-tested-scope':15,'partially-decoded':0,
           'format-understood-but-unverified':6,'unsupported-or-unknown':42,'empty-or-control':7})
        self.assertEqual(data['extracted_unique_headers'],15)

    def test_negative_data_termination_and_priority_controls(self):
        facts=report('facts.json')
        self.assertEqual(facts['E1_previous_decoder_rejection']['tick'],1)
        self.assertEqual(facts['wrong_pitch_data_detected_tick'],1)
        self.assertEqual(facts['missing_terminal_writes_detected_tick'],939)
        self.assertTrue(all(c['lower_priority_rejected'] for c in facts['interaction_rejections'].values()))


if __name__=='__main__':unittest.main()
