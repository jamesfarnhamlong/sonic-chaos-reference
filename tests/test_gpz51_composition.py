"""Regression locks for observed $51 composition, rather than a guessed pose."""
import json,os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import gpz51_composition as B
import rom as R
from oracle import Oracle

class CompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(B.CACHE.read_text())
        cls.rom=R.load(os.environ['SONIC_CHAOS_ROM']) if os.environ.get('SONIC_CHAOS_ROM') else None

    def test_head_and_stack_order(self):
        d=self.data
        self.assertEqual([d['modes'][k]['max_attached'] for k in ('64','160','256')],[4,4,5])
        row=d['samples'][0];chain=B.linked(row)
        self.assertEqual([v['parameter'] for v in chain],[0,1,2,3])
        self.assertEqual(chain[0]['frame'],2)
        self.assertEqual([v['y'] for v in chain],[180,209,239,270])
        for a,b in zip(chain,chain[1:]):
            self.assertEqual(a['lower_support'],b['slot']);self.assertEqual(b['upper_predecessor'],a['slot'])

    def test_throw_shrink_and_regrow(self):
        samples={v['tick']:v for v in self.data['samples']}
        self.assertEqual([samples[t]['attached_parameters'] for t in (232,357,471,601,704)],
                         [[0,1,2,3],[0,1,2],[0,1],[0],[0,1,2,3]])
        events=self.data['modes']['160']['events']
        launches=[]
        for parameter in (3,2,1):
            e,v=next((e,v) for e in events for v in e['slots']
                     if v['parameter']==parameter and v['state'] in (11,19))
            launches.append((e['tick'],v['parameter'],v['state']))
        self.assertEqual(launches,[(333,3,19),(447,2,11),(579,1,19)])
        self.assertEqual(len([v for v in samples[602]['slots'] if v['parameter']==1]),2)
        self.assertEqual(B.linked(samples[602])[1]['state'],0) # New child, not old thrown ball.

    def test_landing_dust_is_live(self):
        for mode in ('64','160','256'):
            self.assertTrue({10,11}.issubset(self.data['modes'][mode]['observed_frames']))
        dust=[v for v in next(s for s in self.data['samples'] if s['tick']==357)['slots'] if v['parameter']==17]
        self.assertEqual([(v['state'],v['frame']) for v in dust],[(18,10)])
        self.assertEqual(self.data['frame_usage']['table_only_unresolved'],[])

    def test_original_initializer_all_low_bytes(self):
        if self.rom is None:self.skipTest('set SONIC_CHAOS_ROM')
        o=Oracle(self.rom);o.bank(2,30);o.cpu.ix=0xD700
        for y in range(256):
            o.mem[0xD700:0xD740]=bytes(64);o.mem[0xD700]=81;o.position(1500,y)
            o.call(0x9A99)
            expected=0 if 16<=y<144 else 1 if 144<=y<240 else 2
            self.assertEqual(o.mem[0xD732],expected,(y,expected))
            self.assertEqual(o.mem[0xD726],(5,8,10)[expected])
            o.mem[0xD702]=4;o.call(0x9B91)
            self.assertEqual(o.mem[0xD702],4 if expected==2 else 6)

    def test_original_scheduler_regeneration(self):
        if self.rom is None:self.skipTest('set SONIC_CHAOS_ROM')
        for y in (64,160,256):
            rows=B.replay(self.rom,y)
            self.assertEqual(B.events(rows),self.data['modes'][str(y)]['events'])
        rows=B.replay(self.rom,160,2200,450)
        self.assertEqual(B.events(rows),self.data['modes']['right']['events'])
        right=next(v for v in rows[333]['slots'] if v['parameter']==3)
        self.assertEqual(right['state'],20);self.assertGreater(right['vx'],0)

if __name__=='__main__':unittest.main(verbosity=2)
