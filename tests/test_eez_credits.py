import json
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import eez_credits as E
import eez_ending
import eez_foundation as F
import level_package as L

class Credits(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = L.load_rom(ROOT.parent/'source/Sonic Chaos (Europe).sms')
        cls.v = E.build(cls.r)

    def test_deterministic_cache_and_hash_gate(self):
        self.assertEqual((E.OUT/'ending-credits.json').read_text(encoding='utf-8'), E.dumps(self.v))
        with self.assertRaises(AssertionError): E.build(self.r[:-1]+bytes([self.r[-1]^1]))

    def test_exact_display_order_and_heart(self):
        rows = [c for c in self.v['commands'] if 'stored_ascii' in c]
        expected = ['CAST','SONIC','MILES POWER','ROBOTNIK','GAME DESIGN','M.SHIMA',
                    'RAY','500ZO','ART','7LY.BIGKING','GEN♥','NOBURIN','EAST',
                    'SOUND','MIX','NAGAO N.GEE','PROGRAM','KOKO','HIRO 777',
                    'TOSHIYAN','TOMOYAN','THANKS TO','HITMEN','THE HASE','KENSAN',
                    'GADAI','MIKARIN','LLG','J.S','K.DASH','HASUWO','YOKOYAMASAN',
                    'TOMOZO','AND YOU.']
        self.assertEqual([x['displayed'].strip() for x in rows if x['displayed'].strip()], expected)
        self.assertEqual((len(rows), self.v['nonblank_rows']), (41,34))
        self.assertTrue(all(len(x['stored_ascii']) == 11 for x in rows))
        self.assertEqual(next(c for c in rows if '$' in c['stored_ascii'])['stored_ascii'], '    GEN$   ')
        self.assertEqual(self.v['stream_source']['cpu_end_exclusive'], 0xB2ED)
        self.assertEqual(self.v['commands'][-1], dict(cpu=0xB2EC, control=255))

    def test_every_call_oracle_and_position_boundaries(self):
        ntsc, pal = self.v['timings']
        self.assertEqual([t['total_calls'] for t in (ntsc,pal)], [8909,10537])
        self.assertEqual([t['glyph_write_calls'] for t in (ntsc,pal)], [7667,7667])
        self.assertTrue(all(x['last_call']-x['first_call'] == 186 for t in (ntsc,pal) for x in t['line_states']))
        self.assertEqual([(x['first_call'],x['last_call']) for x in ntsc['line_states'][:2]], [(3,189),(223,409)])
        self.assertEqual([(x['x'],x['y']) for x in ntsc['line_states'][:4]], [(32,128),(40,160),(40,160),(32,160)])
        self.assertEqual([x['cpu'] for x in ntsc['line_states']], [x['cpu'] for x in pal['line_states']])

    def test_rom_glyph_sources_and_compressed_bounds(self):
        self.assertEqual(len(self.v['glyphs']),29)
        for g in self.v['glyphs'].values():
            a,b = g['variants']['name'],g['variants']['heading']
            self.assertEqual(b['source']['cpu_start']-a['source']['cpu_start'],0x204)
            for variant in (a,b):
                self.assertEqual(len(variant['tiles']),6)
                self.assertTrue(all(96 <= t['pattern'] < 435 for t in variant['tiles']))
        self.assertEqual(self.v['assets']['font']['source']['cpu_end_exclusive'],0xB06F)
        self.assertEqual(self.v['assets']['end_card']['tile_count'],26)
        self.assertEqual([x['x'] for x in self.v['end_card']['initial_anchors']],[112,128,144,156])
        self.assertEqual([f['piece_count'] for f in self.v['end_card']['frames']],[4,4,4,1])

    def test_original_route_and_audio_observations(self):
        full = json.loads((E.OUT/'ending-credits-trace-full.json').read_text())
        partial = json.loads((E.OUT/'ending-credits-trace-partial.json').read_text())
        self.assertTrue(full['returned_to_title'] and partial['returned_to_title'])
        self.assertEqual(max(e.get('calls',0) for e in full['events']),8909)
        self.assertEqual(max(e.get('calls',0) for e in partial['events']),0)
        self.assertEqual([e['request'] for e in full['events'] if e['kind']=='audio_request'],[0x8D]+[0xA6]*8+[0xBA]*2)
        self.assertEqual([e['request'] for e in partial['events'] if e['kind']=='audio_request'],[0x9A,0x98])
        self.assertTrue(all(p['scroll']==[0,0] for x in (full,partial) for p in x['pictures']))
        self.assertEqual(len([e for e in full['events'] if e.get('pc')==0x1BBE]),37)
        for x in (full,partial):
            final=x['terminal_trace'][-1]
            self.assertEqual(final['pc'],0x04B4)
        a = next(e['frame'] for e in full['events'] if e.get('pc')==0x1A25)
        end_pictures=[p for p in full['pictures'] if 'end-animation' in p['file']]
        self.assertTrue(end_pictures)
        self.assertEqual(a,9647)
        self.assertEqual(len([e for e in full['events'] if e.get('pc')==0x1C21]),41)

    def test_existing_complete_scripts_stay_reproducible(self):
        self.assertEqual((F.OUT/'ending-scripts.json').read_text(encoding='utf-8'), F.dumps(eez_ending.build(self.r)))

if __name__ == '__main__': unittest.main()
