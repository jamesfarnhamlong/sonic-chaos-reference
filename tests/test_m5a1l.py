"""A1L licensing/closure checks and optional native helper regression controls."""
import json,os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name):return json.loads((ROOT/'data/m5-a1l'/name).read_text())
class LicensingClosure(unittest.TestCase):
 def test_all_fourteen_pinned_hashes_are_reconciled(self):
  old=json.loads((ROOT/'data/m5-a0/source-license-audit.json').read_text());new=load('license-matrix.json')
  self.assertEqual({r['path']:r['sha256'] for r in new['entries']},{r['path']:r['sha256'] for r in old['files']})
  self.assertEqual(len(new['entries']),14)
 def test_missing_declaration_not_automatically_no_license(self):
  d=load('license-matrix.json');self.assertTrue(all(e['absence_is_not_proof_of_no_license'] for e in d['entries']))
  self.assertFalse(d['formal_legal_clearance_claimed']);self.assertFalse(d['upstream_contact'])
  self.assertEqual(sum(e['explicit_file_grant'] is not None for e in d['entries']),1)
 def test_dependency_reduction_and_platform_imports(self):
  d=load('dependency-manifest.json');self.assertEqual(len(d['compiled_source_closure']),4);self.assertEqual(len(d['removed_A0_dependency_files']),13)
  self.assertFalse(d['linked_C_runtime'] or d['full_libvgm_linked'] or d['full_MAME_linked'])
  self.assertEqual(d['binary_imports'],{'KERNEL32.dll':['GetProcessHeap','HeapAlloc','HeapFree']})
 def test_retained_core_not_rewritten(self):
  b=load('dependency-manifest.json')['build'];self.assertEqual(b['retained_body_sha256'],'fe45270980c6389ed337b0cbacde4211cb3a4069751e42dbc095173853158b25')
  self.assertEqual(b['core_source_sha256'],'91e6d92121bd94466c6971c6a3b52adb2016930cc29fa38caa2fdf9a49e98ab3')
 def test_source_dep_lists_have_no_unclear_helpers(self):
  d=load('dependency-manifest.json')['build']['dependencies']
  self.assertTrue(all('libvgm-src' not in s and 'sonic-chaos-reference-m4' not in s for s in d.values()))
 def test_archive_availability_is_distinct_from_binary_contribution(self):
  d=load('dependency-manifest.json');self.assertEqual({a['name'] for a in d['linker_archive_inputs']},{'c.lib','compiler_rt.lib','kernel32.lib'})
  self.assertEqual(len(d['pdb_contributing_modules']),5)
  self.assertFalse(any('compiler_rt' in m['object'] or m['object'].endswith('/c.lib') for m in d['pdb_contributing_modules']))
  self.assertEqual(set(d['unresolved_object_symbols']),{'__imp_GetProcessHeap','__imp_HeapAlloc','__imp_HeapFree'})
 def test_all_twelve_emission_and_core_states(self):
  d=load('comparisons.json');self.assertEqual(len(d['cases']),12);self.assertEqual(d['total_ticks'],5587)
  for c in d['cases'].values():self.assertEqual(c['emission_failures'],[]);self.assertEqual(c['core_register_counter_LFSR_failures'],[])
 def test_new_numerical_discrepancies_are_not_hidden(self):
  d=load('comparisons.json');self.assertEqual(max(c['versus_original_MAME_2048']['max_error_lsb'] for c in d['cases'].values()),5)
  self.assertEqual(max(c['versus_A0_735']['max_error_lsb'] for c in d['cases'].values()),4)
  self.assertFalse(d['thresholds_relaxed']);self.assertIn('HOLD',d['verdict'])
  with self.assertRaises(AssertionError):self.assertEqual(d['cases']['music-context-BA']['callback_aligned_vs_original']['max_error_lsb'],0)
 def test_counterexamples_still_sound_and_new_partition_invariance(self):
  d=load('comparisons.json');self.assertEqual(d['finite_fade_held']['candidate_nonzero_samples'],5880);self.assertEqual(d['finite_fade_held']['reference_nonzero_samples'],5880)
  self.assertGreater(d['history_resumption']['correlation'],.999999);self.assertEqual(d['segmentation']['max_error_lsb'],0)
  self.assertTrue(all(c['fresh_instance_determinism'] and c['new_callback_partition_invariance'] for c in d['cases'].values()))
 def test_notice_and_licence_scope(self):
  text=(ROOT/'tools/m5a1l/LICENSE-MIT.txt').read_text();self.assertIn('Scope: newly authored files',text)
  text=(ROOT/'docs/m5-a1l-THIRD-PARTY-NOTICES.md').read_text();self.assertIn('BSD-3-Clause',text);self.assertIn('Nicola Salmoria',text)

@unittest.skipUnless(os.environ.get('M5A1L_NATIVE')=='1','requires local private build and NumPy')
class NativeHelpers(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  sys.path[:0]=[str(ROOT/'tools/m5a0'),str(ROOT/'tools/m5a1l')]
  from backend import PSG
  cls.PSG=PSG;cls.dll=ROOT/'build/m5-a1l/psg-a1l.dll'
 def test_binary_imports_match_manifest(self):
  from pe import pe_imports
  self.assertEqual(pe_imports(self.dll),load('dependency-manifest.json')['binary_imports'])
 def test_every_volume_entry_matches_original_table(self):
  import ctypes as C
  with self.PSG(self.dll) as p:
   p.lib.a1_volumes.argtypes=[C.c_void_p,C.c_void_p];a=(C.c_int*16)();p.lib.a1_volumes(p.ptr,a)
   self.assertEqual(list(a),[int(8192*2**(-i/3)+.5) for i in range(15)]+[0])
 def test_fresh_starts_pause_and_silence_do_not_freeze_oscillator(self):
  import numpy as np
  def first():
   with self.PSG(self.dll) as p:p.write([0xC4,0x01,0xD0,0xE7,0xF2]);return p.render()
  self.assertTrue(np.array_equal(first(),first()))
  with self.PSG(self.dll) as p:
   p.write([0xC4,0x01,0xD0,0xE7,0xF2]);p.render();snapshot=p.state();self.assertEqual(p.state(),snapshot)
   p.write([0x9F,0xBF,0xDF,0xFF]);p.render();state=p.state();self.assertEqual(np.count_nonzero(p.render()),0);self.assertNotEqual(p.state()[:22],state[:22])
 def test_rational_resampler_is_partition_independent(self):
  import numpy as np
  with self.PSG(self.dll) as a,self.PSG(self.dll) as b:
   a.write([0xC4,0x01,0xD0,0xE7,0xF2]);b.write([0xC4,0x01,0xD0,0xE7,0xF2]);x=a.render();y=np.concatenate([b.render(1),b.render(98),b.render(636)])
   self.assertTrue(np.array_equal(x,y));self.assertEqual(a.state(),b.state())
 def test_repeated_noise_reset_is_preserved(self):
  with self.PSG(self.dll) as p:
   p.write([0xC4,0x01,0xD0,0xE7,0xF2]);p.render()
   for _ in range(2):p.write([0xE7]);self.assertEqual(p.state()[21],32768);p.render();self.assertNotEqual(p.state()[21],32768)
if __name__=='__main__':unittest.main()
