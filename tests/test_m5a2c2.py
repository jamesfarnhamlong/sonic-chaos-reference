"""FD prerequisite, bounded reader policy, and coupled-noise expansion contracts."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2'),str(ROOT/'tests')]
from test_m5a2 import synthetic
from m5a2.decoder import DecodeError
from m5a2c2.decoder import Decoder


def report(name):return json.loads((ROOT/'data/m5-a2c2'/name).read_text())


def effect(stream):
    b=synthetic(stream);p=b['programs'].pop('129');p['streams'][0]['latch']=0xC0
    b['programs']['162']=p;b['priority']['162']=56
    return b


class FDControls(unittest.TestCase):
    def test_only_mode_bit_changes_and_operand_consumed(self):
        for flags in (0x80,0x88,0xA4,0xFF):
            for operand in (0,1,2,255):
                b=effect((operand,));m=Decoder(b);m.ch[5][:]=bytes([flags,0xC0])+bytes(range(2,48))
                before=bytes(m.ch[5]);p=m.command(5,0xFD,0x5200)
                expected=bytearray(before);expected[0]=flags|8 if operand==1 else flags&~8
                self.assertEqual(bytes(m.ch[5]),expected);self.assertEqual(p,0x5201);self.assertEqual(m.writes,[])

    def test_truncated_FD_and_invalid_next_pointer_rejected(self):
        for stream in ((0xFD,),(0xFD,1)):
            m=Decoder(effect(stream));m.direct(0xA2)
            with self.assertRaises(DecodeError):m.tick()

    def test_unverified_reader_transitions_not_enabled(self):
        for index in (0,1,2,3,4,6):
            m=Decoder(effect((1,)));before=[bytes(c) for c in m.ch]
            with self.assertRaises(DecodeError):m.command(index,0xFD,0x5200)
            self.assertEqual([bytes(c) for c in m.ch],before)

    def test_no_other_unverified_opcode_enabled(self):
        for op in (0xE2,0xE4,0xE5,0xE8,0xED,0xF4,0xFA):
            m=Decoder(effect((op,0)));m.direct(0xA2)
            with self.assertRaises(DecodeError):m.tick()

    def test_original_FD_prerequisite_source_and_state(self):
        d=report('fd-gate.json');self.assertEqual(d['status'],'PASS');self.assertEqual(d['actual_A2']['FD_executions'],1)
        self.assertEqual(d['actual_A2']['opcode_bytes_including_operand'],2)
        self.assertTrue(d['actual_A2']['only_flag_bit3_changed']);self.assertTrue(d['actual_A2']['caller_consumption_exact'])
        self.assertEqual(d['direct_original_handler_edges'],16)
        self.assertEqual(len(d['seeded_transition_probes']),6)
        self.assertTrue(all(r['status']=='PASS' and r['FD_transitions']==2 for r in d['seeded_transition_probes'].values()))
        for path,h in d['source_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes().replace(b'\r\n',b'\n')).hexdigest(),h)


class RemainingEffects(unittest.TestCase):
    def test_all_81_exact_cases_and_source_receipts(self):
        d=report('emission.json');self.assertEqual(len(d['cases']),81)
        self.assertEqual(sum(c['ticks'] for c in d['cases'].values()),29905)
        self.assertEqual(sum(c['ordered_bytes'] for c in d['cases'].values()),142263)
        for c in d['cases'].values():
            self.assertEqual(c['status'],'PASS');self.assertEqual(c['failures'],[]);self.assertEqual(c['ticks'],c['compared_ticks'])
        for path,h in d['source_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes().replace(b'\r\n',b'\n')).hexdigest(),h)

    def test_actual_completions_and_post_output(self):
        for rid,end in [('A1',30),('A2',35),('A7',7)]:
            d=report('facts.json')['termination'][rid];self.assertEqual(d['inactive_tick'],end)
            self.assertEqual(d['post_ticks'],32);self.assertEqual(d['post_writes'],0)
            self.assertEqual(d['final_attenuation'],[15]*4);self.assertEqual(d['PCM_samples'],(end+32)*735)

    def test_FD_is_not_noop_and_replacement_clears_mode(self):
        d=report('facts.json');self.assertEqual(d['actual_A2_FD_tick'],2);self.assertEqual(d['FD_noop_detected_tick'],2)
        self.assertTrue(d['FD_release_clears_mode']);self.assertTrue(d['FD_replacement_initial_flags_restored'])
        self.assertTrue(d['missing_program_rejected']);self.assertEqual(d['missing_A7_terminal_detected_tick'],7)

    def test_one_F3_per_admitted_A7_invocation(self):
        d=report('facts.json');self.assertEqual(d['A7_retrigger_admissions'],[[30,0xA7],[32,0xA7],[36,0xA7],[60,0xA7]])
        self.assertEqual(report('emission.json')['cases']['A7-retrigger']['opcodes']['F3'],4)
        self.assertTrue(d['blocked_A7_by_A1_at32']);self.assertTrue(d['blocked_A7_by_A3_at4'])
        for c in d['A7_noise'].values():self.assertEqual(c['F3_mode'],7);self.assertEqual(c['F3_executions'],1)

    def test_original_DE11_restore_context_and_persistent_LFSR(self):
        d=report('facts.json');self.assertEqual(d['A7_solo_restore'],dict(tick=7,channel=6,data_latch=7,byte=0))
        for c in d['A7_noise'].values():self.assertEqual(c['DE11_restore']['byte'],0xE4)
        self.assertEqual(d['noise_native_state']['solo-A7']['LFSR_changes_in_observed_post_or_run_window'],31)
        self.assertEqual(d['music_recovery']['THZ-A7-later-music2']['next_eligible_read_tick'],97)
        self.assertEqual(d['music_recovery']['THZ-A7-later-music3']['next_eligible_read_tick'],85)

    def test_new_PCM_and_all_62_frozen_comparisons(self):
        d=report('pcm.json');self.assertEqual(len(d['cases']),19);self.assertEqual(len(d['regressions']),62)
        for c in d['cases'].values():
            self.assertLessEqual(c['max_over_mix_and_voices'],5);self.assertEqual(c['register_counter_LFSR_failures'],[])
            self.assertTrue(c['partition_invariant']);self.assertEqual(len(c['voices']),4)
        self.assertTrue(all(c['PCM_identical_to_accepted_parent'] for c in d['regressions'].values()))

    def test_three_fresh_ROM_free_replays(self):
        d=report('isolation.json');self.assertEqual(set(d['cases']),{'A1','A2','A7'})
        self.assertTrue(all(c['fresh_process'] and c['PCM_identical'] and c['ROM_and_oracle_access_forbidden'] for c in d['cases'].values()))

    def test_format_horizon_and_old_24_records_unchanged(self):
        d=report('emission.json');self.assertEqual(d['SCSP_version'],1);self.assertEqual(d['horizon'],4200)
        self.assertTrue(d['previous_24_headers_and_data_unchanged']);self.assertEqual(d['packed_bytes'],8559)
        self.assertEqual(d['incremental_data_bytes'],54)

    def test_catalogue_counts_and_unknown_names(self):
        d=report('coverage.json');self.assertEqual(len(d['entries']),70)
        self.assertEqual(d['counts'],{'fully-decoded-in-tested-scope':27,'partially-decoded':0,
              'format-understood-but-unverified':0,'unsupported-or-unknown':36,'empty-or-control':7})
        self.assertEqual(d['extracted_unique_headers'],27)
        for rid in (0xA1,0xA2,0xA7):
            r=next(x for x in d['entries'] if x['request_id']==rid)
            self.assertEqual(r['friendly_name'],f'Unknown ${rid:02X}');self.assertNotIn('C1_preflight_only',r)


if __name__=='__main__':unittest.main()
