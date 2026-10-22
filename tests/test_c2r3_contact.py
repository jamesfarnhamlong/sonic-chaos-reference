"""C2-R3 evidence checks; no ROM or GameMaker required."""
import gzip,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
class C2R3Evidence(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.routes=json.loads(gzip.decompress((ROOT/'data/c2r3/natural-attempts.json.gz').read_bytes()))['routes']
  cls.special=read('data/c2r3/special-cases.json')
  cls.analysis=read('data/c2r3/analysis.json')
 def test_exact_parent_scope(self):
  r=read('data/c2r3/fidelity-register.json')
  self.assertEqual(r['researchParent'],'02a586ffa133f40d93566a4a5bec7241d8236dcf')
  self.assertEqual(r['poc'],'4eb684911c5785667181b9d3f940b1dc820e66d1')
  self.assertFalse(r['newRomExecution']);self.assertFalse(r['windowsAcceptance'])
  self.assertFalse(any(f['status']=='proven-gap' for f in r['findings']))
 def test_unchanged_mapped_springs(self):
  expected=sorted((r['world_x'],r['world_y']) for r in read('data/rom-cache/spring-interaction.json')['type26_placements']['thz1'])
  for r in self.routes:
   self.assertEqual(sorted((x,y) for n,x,y in r['objects'] if 'spring_26' in n),expected)
   self.assertEqual(r['start'],[142,654]);self.assertIsNone(r['error'])
 def test_live_route_bounce(self):
  r=next(r for r in self.routes if r['width']==348 and r['policy']=='jump-at-760')
  b=[t for t in r['trace'] if any(w['writer']=='SCR_chaos_type21_top_bounce' for w in t['writers'])]
  self.assertEqual([t['frame'] for t in b],[325,326,327,328])
  self.assertTrue(all(t['after']['next']==11 and t['after']['vy']==-1728 for t in b))
  self.assertEqual(sum(a['mappedSpringLaunches'] for a in self.analysis['routes']),0)
 def test_width_difference_is_spike_contact(self):
  d=self.analysis['widthDifference'];self.assertEqual((d['firstPlayerDifference'],d['firstSpikeDifference']),(354,288))
  self.assertEqual([w['writer'] for w in d['at256']['writers']],['chaos_spike1b_contact'])
  self.assertEqual(d['at256']['after']['damage_request'],255)
  self.assertEqual(d['at348']['after']['damage_request'],0)
 def test_crumble_timeline_and_canonical_rows(self):
  for s in self.special['sez']:
   self.assertEqual(s['trace'][14]['spawns'],1)
   self.assertEqual(s['trace'][30]['cell'],175)
   self.assertEqual(s['trace'][31]['cell'],176)
   self.assertTrue(any(not c['actual']['hold'] for c in s['controls']))
 def test_threshold_and_detach_controls(self):
  a=self.special['aqz']
  self.assertTrue(any(r['vector']['vx']==-1023 and r['actual']['vy']==-768 for r in a))
  self.assertTrue(all(r['actual']['vy']==0 for r in a if r['vector']['vx']==1023))
  for r in self.special['eez']:
   self.assertEqual(r['actual'],r['expectedPlayer']);self.assertEqual(r['actor'],r['expectedActor'])
  self.assertEqual(self.special['checks'],168)
 def test_runtime_replay_and_open_history(self):
  self.assertEqual(read('data/c2r3/replay-check.json')['checks'],16254)
  f=read('data/c2r3/fidelity-register.json')['findings']
  self.assertEqual(next(r for r in f if r['id']=='C2R2-HISTORICAL-VISIBLE-OSCILLATION')['status'],'unresolved')
if __name__=='__main__':unittest.main()
