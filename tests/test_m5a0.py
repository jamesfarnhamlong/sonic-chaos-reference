"""M5-A0 public receipts plus optional live native integration controls."""
import ast,inspect,json,os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def data():return json.loads((ROOT/'data/m5-a0/results.json').read_text())
class StatefulReceipts(unittest.TestCase):
 def test_exact_emission_and_complete_control_set(self):
  d=data();self.assertEqual((len(d['cases']),d['total_ticks'],d['total_ordered_bytes']),(12,5587,32512))
  for c in d['cases'].values():
   self.assertEqual(c['emission'],'PASS');self.assertEqual(c['emission_failures'],[]);self.assertEqual(c['counter_lfsr_reference_diagnostic_failures'],[])
 def test_sample_exact_with_reference_callback_segmentation(self):
  for c in data()['cases'].values():self.assertEqual(c['pcm']['reference_callback_alignment']['nonzero_error_samples'],0)
 def test_queue_block_residual_is_retained(self):
  errors=[c['pcm']['sample_max_error_lsb'] for c in data()['cases'].values()]
  self.assertEqual(max(errors),3);self.assertTrue(any(errors));self.assertEqual(data()['segmentation']['block735_vs100plus635_max_error_lsb'],2)
 def test_clock_history_counterexample_closed(self):
  d=data()['history'];self.assertEqual(d['muted_ticks'],28);self.assertEqual(d['counter_lfsr_differences_from_uninterrupted_solo'],28)
  self.assertEqual(d['changed_LFSR_boundaries'],27);self.assertNotEqual(d['state33_noise_lfsr'],d['solo33_noise_lfsr'])
  self.assertGreater(d['resumed_noise_correlation'],.999999);self.assertFalse(d['resumed_source_reset'])
  old=json.loads((ROOT/'data/m5-p1c/diagnostics.json').read_text())['coupled_segments']['resumed_noise']['correlation']
  with self.assertRaises(AssertionError):self.assertGreater(old,.999999)
 def test_held_fade_has_no_missing_tail_or_padding(self):
  d=data()['held_fade'];self.assertEqual(d['reference_nonzero_samples'],5880);self.assertEqual(d['candidate_nonzero_samples'],5880)
  self.assertFalse(d['source_padding']);self.assertEqual(d['max_error_lsb'],1)
 def test_core_and_logical_initialization_differ_explicitly(self):
  c=data()['cases']['coupled-steal-recover'];self.assertEqual(c['physical_chip_register_failures'],[]);self.assertEqual(c['unwritten_core_vs_logical_initial_defaults'],180)
 def test_no_combined_oracle_in_candidate_interface(self):
  tree=ast.parse((ROOT/'tools/m5a0/backend.py').read_text());f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='candidate')
  self.assertEqual([a.arg for a in f.args.args],['bank','case','dll','split','reference_chunks'])
  names={n.id for n in ast.walk(tree) if isinstance(n,ast.Name)};self.assertFalse(names&{'Trace','original','oracle'})
 def test_preservation_and_no_new_reference_render(self):
  d=data();self.assertEqual(d['preservation_before'],d['preservation_after']);self.assertEqual(d['preservation_after']['M4_assets_checked'],47)
  self.assertEqual(d['new_original_reference_renders'],0);self.assertTrue(d['pause_no_advance'])
 def test_license_gate_not_blanket_permission(self):
  d=json.loads((ROOT/'data/m5-a0/source-license-audit.json').read_text());self.assertTrue(d['needed_sources_clean']);self.assertIn('CONDITIONAL',d['redistribution'])
  self.assertEqual(next(f for f in d['files'] if f['path']=='emu/cores/sn76496.c')['declared_license'],'BSD-3-Clause')
  self.assertEqual(next(f for f in d['files'] if f['path']=='emu/Resampler.c')['declared_license'],'not declared in file header')

@unittest.skipUnless(os.environ.get('M5A0_NATIVE')=='1','requires built private native adapter and NumPy')
class NativeCore(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  sys.path[:0]=[str(ROOT/'tools/m5a0'),str(ROOT/'tools')]
  from backend import PSG
  cls.PSG=PSG;cls.dll=ROOT/'build/m5-a0/psg-a0.dll'
 def test_repeated_noise_writes_reset_lfsr_not_volume_writes(self):
  with self.PSG(self.dll) as p:
   p.write([0xC4,0x01,0xD0,0xE7,0xF2]);p.render();self.assertNotEqual(p.state()[21],32768)
   before=p.state()[21];p.write([0xF3]);self.assertEqual(p.state()[21],before)
   for _ in range(2):
    p.write([0xE7]);self.assertEqual(p.state()[21],32768);p.render();self.assertNotEqual(p.state()[21],32768)
 def test_silent_attenuation_keeps_oscillators_advancing(self):
  import numpy as np
  with self.PSG(self.dll) as p:
   p.write([0xC4,0x01,0xD0,0xE7,0xF2]);p.render();p.write([0x9F,0xBF,0xDF,0xFF]);p.render()
   before=p.state();out=p.render();after=p.state()
   self.assertEqual(np.count_nonzero(out),0);self.assertNotEqual(before[13:22],after[13:22])
 def test_data_latch_and_no_advance_pause(self):
  with self.PSG(self.dll) as p:
   p.write([0xB4,0]);self.assertEqual(p.state()[3]&15,0);state=p.state();self.assertEqual(p.state(),state)
 def test_invalid_block_size_is_rejected(self):
  with self.PSG(self.dll) as p:
   with self.assertRaises(AssertionError):p.render(736)
if __name__=='__main__':unittest.main()
