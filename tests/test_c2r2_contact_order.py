import gzip,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class ContactOrderEvidence(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.d=json.loads(gzip.decompress((ROOT/'data/c2r2/traces.json.gz').read_bytes()))
 def test_authorised_source(self):
  self.assertEqual(self.d['baseline'],'4eb684911c5785667181b9d3f940b1dc820e66d1')
  self.assertEqual(self.d['researchParent'],'1e34a2a666a83e107942678fe0c0497fffb3ff05')
 def test_real_interactions_and_limits(self):
  self.assertEqual(len(self.d['rows']),96)
  self.assertTrue(all(r['error'] is None for r in self.d['rows']))
  self.assertEqual(sum(bool(r['launches']) for r in self.d['rows']),30)
  self.assertEqual(sum(bool(r['stomps']) for r in self.d['rows']),30)
  self.assertTrue(all('synthetic' in r['placementClass'] for r in self.d['rows'] if r['id']=='combined-overlay'))
 def test_width_pair(self):
  for r in self.d['rows'][:48]:
   other=next(s for s in self.d['rows'] if s['width']==348 and (s['id'],s['vx'],s['control'])==(r['id'],r['vx'],r['control']))
   self.assertEqual([t['after'] for t in r['trace']],[t['after'] for t in other['trace']])
 def test_cycle_amplitude_facing_and_fall(self):
  r=next(r for r in self.d['rows'] if (r['id'],r['width'],r['control'],r['vx'])==('mapped-spring',256,'none',256))
  self.assertEqual([t['after']['xu'] for t in r['trace'][12:15]],[177840,177856,177840])
  self.assertEqual([t['published']['drawFacing'] for t in r['trace'][12:15]],[1,1,1])
  self.assertEqual((r['trace'][80]['after']['next'],r['trace'][81]['after']['state']),(14,14))
 def test_controls_and_gate(self):
  self.assertTrue(all(r['worldFlips']==0 for r in self.d['rows'] if r['control']=='none' and r['vx']==0))
  self.assertEqual(json.loads((ROOT/'data/c2r2/canonical-controls.json').read_text())['checks'],758)
  self.assertTrue(all(r['status']==0 for r in json.loads((ROOT/'data/c2r2/gate/results.json').read_text())))
if __name__=='__main__':unittest.main()
