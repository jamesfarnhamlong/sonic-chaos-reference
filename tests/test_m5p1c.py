"""Public numerical regressions; optional original-driver reproduction is separate."""
import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(n):return json.loads((ROOT/'data/m5-p1c'/n).read_text())
class CarrierProof(unittest.TestCase):
 def test_complete_sfx_partition(self):
  d=read('coverage.json');ids=[i for v in d['classes'].values() for i in v]
  self.assertEqual((d['total_catalogue'],len(ids),len(set(ids)),len(d['classes'])),(70,37,37,6))
 def test_exact_gate_includes_physical_and_saved_context(self):
  d=read('emission-gate.json');self.assertEqual(d['status'],'PASS');self.assertEqual(len(d['cases']),9)
  self.assertEqual(sum(c['ticks'] for c in d['cases'].values()),1027)
  self.assertTrue(d['saved_DE11_compared'] and d['full_registers_and_latch_compared'] and d['all_off_states_compared'])
  self.assertTrue(all(not c['failures'] for c in d['cases'].values()))
 def test_hidden_clock_history_is_not_ignored(self):
  d=read('pcm-feasibility.json')['cases']['coupled-steal-recover']
  self.assertEqual(d['compatibility']['hidden_noise_clock_differences'],dict(count=28,first_tick=6))
  self.assertEqual(d['compatibility']['audible_clock_differences']['count'],0)
  self.assertIn('HOLD',d['status'])
 def test_incorrect_history_independent_claim_fails(self):
  s=read('diagnostics.json')['coupled_segments'];self.assertGreater(s['matched_entry']['correlation'],.99999)
  with self.assertRaises(AssertionError):self.assertGreater(s['resumed_noise']['correlation'],.99999)
  self.assertGreater(s['resumed_noise']['sign_disagreement_fraction'],.48)
 def test_fade_not_excused_by_generic_phase(self):
  d=read('pcm-feasibility.json')['cases']['finite-fade']['compatibility']
  self.assertEqual(d['unsupported_sources'],dict(count=8,first_tick=40));self.assertEqual(d['audible_clock_differences']['count'],24)
 def test_no_invalid_source_lifetime_extension(self):
  d=read('pcm-feasibility.json')
  for c in d['cases'].values():
   if 'compatibility' in c:self.assertEqual(c['compatibility']['source_lifetime_overruns']['count'],0)
 def test_explicit_off_gates_all_candidates(self):
  for c in read('pcm-feasibility.json')['cases'].values():
   for t in c.get('metrics',{}).get('timing',[]):self.assertEqual(t['candidate_nonzero_after_logical_off_samples'],0)
 def test_no_blanket_pcm_pass(self):
  d=read('pcm-feasibility.json');self.assertEqual(d['overall'],'HOLD for architecture decision')
  self.assertEqual(set(d['blocking_cases']),{'coupled-steal-recover','finite-fade'})
 def test_render_budget_and_reuse(self):
  d=read('pcm-feasibility.json');self.assertEqual(d['new_process_count'],30);self.assertEqual(d['analysis_followup_new_processes'],0)
  self.assertLessEqual(d['all_targets_at_most_ticks'],90);self.assertFalse(d['new_synthesis'] or d['full_library_rendered'])
 def test_prior_assets_immutable(self):
  d=read('pcm-feasibility.json');self.assertEqual(d['preservation_before'],d['preservation_after'])
  self.assertEqual(d['preservation_after']['M4_assets_checked'],47);self.assertTrue(d['preservation_after']['M4_unchanged'])
  self.assertTrue(all(a['unchanged'] for a in d['preservation_after']['private_archives']))
 def test_private_package(self):
  d=read('private-package-receipt.json');self.assertEqual(d['crc_and_member_hashes'],'PASS');self.assertLess(d['bytes'],128*1024**2)
if __name__=='__main__':unittest.main()
