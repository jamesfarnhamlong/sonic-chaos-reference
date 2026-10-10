"""Regression locks for whole-game natural hurt and controlled boundary traces."""
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def cache(name):return json.loads((ROOT/'data/rom-cache'/name).read_text())
class NaturalHurt(unittest.TestCase):
 def test_free_player_and_original_callbacks(self):
  d=cache('natural-lost-ring-hurt.json');e=d['events']
  h=next(v for v in e if v['tag']=='hurt_entry')
  init=next(v for v in e if v['tag']=='after_objects' and v['u']==h['u'])
  self.assertEqual(init['player'][2:4],[-256,-1024]);self.assertEqual(init['player'][-1],0)
  self.assertEqual(len(init['rings']),1)
  ring=init['rings'][0];self.assertEqual([ring['x'],ring['y'],ring['vx'],ring['vy']],[init['player'][0],init['player'][1]-16,0,-1280])
  eligible=next(v for v in e if v['tag']=='pickup_eligible')
  self.assertEqual(eligible['u']-h['u'],17);self.assertEqual(eligible['player'][0],init['player'][0]-17)
  self.assertFalse(any(v['tag']=='pickup' for v in e))
 def test_original_flat_and_arena(self):
  d=cache('natural-lost-ring-controls.json')
  for case in d['cases']:
   rows=case['rows'];h=next(v for v in rows if v['req']==30)
   self.assertEqual(h['rings'],0)
   if case['x'] in (1000,1856):
    self.assertTrue(all(v['rings']==0 for v in rows if v['u']>=h['u']))
    bounce=next(v for v in rows if v['u']>h['u']+40 and any(o[1]==6 and o[6]==-896 for o in v['o']))
    self.assertEqual(bounce['u']-h['u'],83)
   else:
    changes=[(v['u'],v['rings']) for i,v in enumerate(rows) if i and v['rings']!=rows[i-1]['rings']]
    self.assertEqual(changes,[(3,0),(84,1),(133,0),(214,1)])
 def test_shipped_poc_same_boundary_exception(self):
  d=cache('natural-lost-ring-poc.json')
  for case in d:
   pickups=[v['u'] for i,v in enumerate(case['rows']) if i and v['rings']>case['rows'][i-1]['rings']]
   self.assertEqual(pickups,[81,211] if not case['flat'] and case['x']<=1750 else [])
if __name__=='__main__':unittest.main()
