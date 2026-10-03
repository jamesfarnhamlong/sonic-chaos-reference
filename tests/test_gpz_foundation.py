"""Focused GPZ package locks and original-ROM checks; never touches POC."""
import hashlib
import json
import os
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import gpz_foundation as F
import level_package as L
import isometric_platform as I
import platform_spike_collision as P
import rom as R
from oracle import Oracle

EXPECTED={
 'gpz1':((160,24),(110,384),(0,272),61,84,40,'4fa45495a1206795879d973bf2cfa3b882e5eac8eb36a0cc4038f88faeac651d','48c4698ef5f9bf87782489f6bf5ca89ea2442aa487f43e680721d4d607b9ae41'),
 'gpz2':((128,32),(110,448),(0,336),62,239,30,'d028fa9594db49952f16d40287a89b2e6c666d42d8d1876b90a6f10c33a7164d','bd90b0815c3a7064c55c531f8d56ebb163c5fda52a11dca1b46995a64343f0e5'),
 'gpz3':((80,16),(187,352),(75,240),9,4,5,'c2b32c511dc8450ac47a8ab83f8ff24c7b9cd8ed05d89de7df429bc00c9a8909','737a6e2521f5ddf4219d6bfc0e3cd0b72039cf0ef93ead97cbd7293ab1a0a82d')}

class PackageTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.x=json.loads(F.OUTPUT.read_text(encoding='utf-8'))
 def test_dimensions_starts_strides(self):
  for k,e in EXPECTED.items():
   a=self.x['acts'][k];self.assertEqual(a['dimensions_pixels'],[v*32 for v in e[0]])
   self.assertEqual(a['start']['player_anchor'],list(e[1]));self.assertEqual(a['start']['camera'],list(e[2]))
   self.assertEqual(a['descriptor']['row_table']['stride'],e[0][0]);self.assertTrue(all(a['descriptor']['consistency'].values()))
 def test_exact_layout_hashes(self):
  for k,e in EXPECTED.items():
   a=self.x['acts'][k];flat=bytes(b for row in a['layout']['rows'] for b in row)
   self.assertEqual(hashlib.sha256(flat).hexdigest(),e[6]);self.assertEqual(a['layout']['encoded_cells_sha256'],e[6])
   self.assertEqual(a['layout']['runtime_written_cells'],min(len(flat),4095))
 def test_complete_objects(self):
  for k,e in EXPECTED.items():
   a=self.x['acts'][k];self.assertEqual(len(a['objects']),e[3]);self.assertEqual(a['object_records_sha256'],e[7])
   raw=b''.join(bytes.fromhex(r['raw_bytes']) for r in a['objects']);self.assertEqual(F.digest(raw),e[7])
   for n,r in enumerate(a['objects'],1):
    self.assertEqual(r['index'],n);self.assertEqual((r['world_x'],r['world_y']),(r['stored_x']-256,r['stored_y']-256))
    self.assertIn(r['status'],F.STATUSES)
 def test_rings(self):
  for k,e in EXPECTED.items():
   a=self.x['acts'][k];self.assertEqual(len(a['rings']['terrain']),e[4]);self.assertEqual(len(a['rings']['object09']),e[5])
   for ring in a['rings']['terrain']:
    self.assertEqual(a['layout']['rows'][ring['cell_y']][ring['cell_x']],int(ring['block_id'],16))
    ox,oy=ring['quadrant_origin']
    self.assertEqual((ring['world_x'],ring['world_y']),(ring['cell_x']*32+ox+8,ring['cell_y']*32+oy+8))
   self.assertEqual(a['rings']['coordinate_sha256'],L.coordinate_hash(L.ring_hash_rows(a['rings']['terrain']+a['rings']['object09'])))
 def test_springs(self):
  counts=[(5,1,1,0,5,0),(7,0,19,6,2,15),(0,0,0,0,2,0)]
  for (k,a),e in zip(self.x['acts'].items(),counts):
   actual=(sum(r['type_id']=='0x26' for r in a['objects']),)+tuple(a['census']['terrain_interactions'][s] for s in ('upright','diagonal_right','diagonal_left','horizontal','ceiling'))
   self.assertEqual(actual,e)
  spans=[r for a in self.x['acts'].values() for r in a['objects'] if r.get('spring',{}).get('form')=='hidden_span']
  self.assertEqual([(r['world_x'],r['spring']['span_pixels'],r['spring']['weak']) for r in spans],[(4112,112,True),(2288,96,True)])
 def test_hazards(self):
  self.assertEqual([a['census']['terrain_interactions']['static_spikes'] for a in self.x['acts'].values()],[16,5,0])
  rows=[r for a in self.x['acts'].values() for r in a['objects'] if r['type_id']=='0x1B']
  self.assertEqual([(r['world_x'],r['world_y'],r['parameter']) for r in rows],[(208,672,'0x00')])
 def test_monitors(self):
  expected=[{'0x06':2,'0x03':1,'0x02':1},{'0x01':2,'0x06':2,'0x03':4,'0x04':1,'0x02':1},{'0x01':1,'0x06':1}]
  from collections import Counter
  for a,e in zip(self.x['acts'].values(),expected):
   self.assertEqual(dict(Counter(r['parameter'] for r in a['objects'] if r['type_id']=='0x10')),e)
   self.assertTrue(all(r['reward']!='UNRESOLVED' for r in a['objects'] if r['type_id']=='0x10'))
 def test_platform_placements(self):
  expected=[[(1648,320,'0x89',10),(2896,448,'0x89',10)],[(1632,800,'0x05',13),(1584,384,'0x83',4),(2512,640,'0x0A',11)],[(912,80,'0x89',10)]]
  for a,e in zip(self.x['acts'].values(),expected):
   self.assertEqual([(r['world_x'],r['world_y'],r['parameter'],r['initial_state']) for r in a['objects'] if r['type_id']=='0x28'],e)
 def test_surface1c(self):
  self.assertEqual([a['census']['terrain_interactions']['surface1c'] for a in self.x['acts'].values()],[212,116,90])
  for a in self.x['acts'].values():
   for b in a['blocks']:
    if b['surface']==28:self.assertEqual(b['nonzero_pixels'],0);self.assertEqual(b['headers'][0]['flags'],0x9C)
 def test_mutation_mappings(self):
  for a in self.x['acts'].values():
   blocks={b['block_id'] for b in a['blocks']};self.assertTrue({0x46,0x9D}<=blocks)
   for t in a['rings']['presence_and_replacement_tables']['tables'].values():self.assertTrue(set(t['replacement_blocks'])<=blocks)
 def test_exact_terrain_interaction_cells(self):
  for a in self.x['acts'].values():
   width=a['descriptor']['layout']['width_cells']
   for category,rows in a['terrain_interactions'].items():
    for row in rows:
     i=row['layout_index'];self.assertEqual(row,F.cell_record(i,a['layout']['rows'][i//width][i%width],width))
 def test_safe_instantiation_partition(self):
  for a in self.x['acts'].values():
   f=a['foundation'];groups=[set(f[n]) for n in ('instantiate_indices','integrate_before_instantiating_indices','deliberately_skip_indices')]
   self.assertEqual(set.union(*groups),set(range(1,len(a['objects'])+1)))
   self.assertEqual(sum(map(len,groups)),len(a['objects']))
   self.assertTrue(all(r['type_id'] not in ('0x25','0x2C','0x51') for r in a['objects'] if r['index'] in groups[0]))
 def test_boss_census(self):
  b=self.x['gpz3_boss'];self.assertEqual(b['type'],0x51)
  self.assertEqual({x['type'] for x in b['explicit_script_spawns']},{'0x51','0x34'})
  self.assertEqual(self.x['acts']['gpz3']['foundation']['deliberately_skip_indices'],[9])
 def test_dependency_integrity(self):
  for d in self.x['dependencies']: self.assertEqual(F.cache_ref(d['path']),d)

class RomTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  p=Path(os.environ.get('SONIC_CHAOS_ROM',str(ROOT.parent/'source/Sonic Chaos (Europe).sms')))
  if not p.is_file():raise unittest.SkipTest('canonical local ROM unavailable')
  cls.r=L.load_rom(p);cls.x=json.loads(F.OUTPUT.read_text(encoding='utf-8'))
 def test_fresh_regeneration(self):self.assertEqual(F.dumps(F.build(self.r)),F.OUTPUT.read_text(encoding='utf-8'))
 def test_independent_decoded_census(self):
  for k,a in self.x['acts'].items():
   raw=I.act_data(self.r,k);self.assertEqual(raw['cells'],[b for row in a['layout']['rows'] for b in row])
   self.assertEqual(raw['objects'],[{key:r[key] for key in raw['objects'][0]} for r in a['objects']])
   for b in a['blocks']:
    for plane in (0,1):self.assertEqual(b['headers'][plane],R.header(self.r,b['block_id'],plane))
 def test_original_start_loader(self):
  for act,(k,a) in enumerate(self.x['acts'].items()):
   o=Oracle(self.r);o.mem[0xD297]=1;o.mem[0xD298]=act;o.call(0x4E57)
   self.assertEqual([o.word(v) for v in (0xD2D6,0xD2D8)],a['start']['camera'])
   self.assertEqual([o.word(v) for v in (0xD511,0xD514)],a['start']['player_anchor'])
 def test_original_platform_initializers(self):
  for a in self.x['acts'].values():
   for rec in a['objects']:
    if rec['type_id']!='0x28':continue
    lab=P.platform_lab(self.r,int(rec['parameter'],16),int(rec['aux1'],16),world=(rec['world_x'],rec['world_y']))
    self.assertEqual(lab.m[P.SLOT+1],rec['initial_state'])
    if rec['parameter']=='0x05':self.assertEqual(lab.m[P.SLOT+0x36],6)
 def test_original_surface19_writes(self):
  o=Oracle(self.r);o.cpu.ix=0xD500;o.mem[0xD524]=0x80;o.mem[0xD3BC]=7;o.call(0x6B23)
  self.assertEqual(o.mem[0xD524],0x81);self.assertEqual(o.mem[0xD3BC],8)
 def test_source_and_asset_hashes(self):
  for v in self.x['source_regions'].values():self.assertEqual(F.digest(self.r[v['rom']:v['rom']+v['length']]),v['sha256'])
  for k,a in self.x['acts'].items():
   live=L.build_act(self.r,k,F.ACTS[k]);self.assertEqual(live['vram_loads'],a['graphics']['static_vram_loads'])
   self.assertEqual(F.digest(live['vram']),a['graphics']['vram_sha256'])
if __name__=='__main__':unittest.main()
