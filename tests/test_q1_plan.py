"""Q1 plan consistency only; no game, emulator or Windows execution."""
import csv,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Q1Plan(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.p=json.loads((ROOT/'data/q1/coverage-register.json').read_text())
 def test_authorised_baselines_and_target(self):
  self.assertEqual(self.p['poc'],'4eb684911c5785667181b9d3f940b1dc820e66d1')
  self.assertEqual(self.p['research_parent'],'715ab1b1aa22f723690d042fae2c2117e9a16b6f')
  self.assertEqual(self.p['target'],{'width':348,'height':196,'runner':'GameMaker F5'})
  self.assertFalse(self.p['windows_executed']);self.assertTrue(self.p['plan_only'])
 def test_18_acts_and_destinations(self):
  a=self.p['acts'];self.assertEqual(len(a),18);self.assertEqual(len({x['room'] for x in a}),18)
  self.assertEqual([x['id'] for x in a],[z+str(n) for z in ['THZ','GPZ','SEZ','MGHZ','AQZ','EEZ'] for n in [1,2,3]])
  for x,y in zip(a,a[1:]):self.assertEqual(x['expected_destination'],y['name'])
  self.assertEqual(a[-1]['expected_destination'],'Sonic ending, then title')
 def test_no_inherited_q1_passes(self):
  self.assertFalse(self.p['historical_acceptance_is_q1_pass'])
  for a in self.p['acts']:
   for k in ['individual_act','normal_transition','continuous_visit']:self.assertEqual(a[k]['status'],'NOT TESTED')
  for item in self.p['smoke']+self.p['optional_specials']+self.p['optional_endings']+[self.p['continuous_run']]:self.assertEqual(item['status'],'NOT TESTED')
  self.assertEqual(set(self.p['status_values']),{'PASS','FAIL','NOT TESTED','BLOCKED'})
 def test_priority_and_open_findings(self):
  e=next(i for i in self.p['issues'] if i['id']=='EEZ3-FULLCHAIN-F5');self.assertEqual(e['priority'],0)
  self.assertIn('PRES-ENTRY-MGHZ3',[i['id'] for i in self.p['issues']])
  self.assertEqual(len(self.p['issues']),7)
  for i in self.p['issues']:
   self.assertEqual(i['state'],'OPEN');self.assertFalse(i['auto_fails_unrelated_tests']);self.assertFalse(i['correction_authorised'])
 def test_every_expected_transition_has_source(self):
  for a in self.p['acts']:
   self.assertTrue(a['source_refs'])
   self.assertTrue(all(r in self.p['sources'] for r in a['source_refs']))
  for r in self.p['sources'].values():
   self.assertGreater(r['line'],0);self.assertEqual(len(r['sha256']),64)
   self.assertIn('/blob/'+self.p['poc']+'/',r['url'])
 def test_optional_paths_and_continuity_separate(self):
  self.assertEqual([s['id'] for s in self.p['optional_specials']],['SS1','SS2','SS3','SS4','SS5'])
  self.assertEqual(len(self.p['optional_endings']),2)
  self.assertEqual(self.p['continuous_run']['origin'],'TITLE_NEW_GAME')
  self.assertFalse(self.p['continuous_run']['shortcut_used'])
  self.assertTrue(all(a['special_detour_return'] is None for a in self.p['acts'] if a['id'].endswith('3')))
 def test_csv_and_markdown_match_register(self):
  with (ROOT/'data/q1/18-act-coverage.csv').open(newline='') as f:rows=list(csv.DictReader(f))
  self.assertEqual([r['Act'] for r in rows],[a['name'] for a in self.p['acts']])
  text=(ROOT/'docs/q1-18-act-coverage.md').read_text()
  for a in self.p['acts']:self.assertIn('| '+a['name']+' |',text)
if __name__=='__main__':unittest.main()
