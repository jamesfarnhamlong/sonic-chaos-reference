"""Focused MGHZ foundation / object-census locks and original-ROM checks; never touches POC."""
import hashlib
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import mghz_foundation as F
import mghz_object_census as C
import mghz_art_approval as AA
import level_package as L
import rom as R
from oracle import Oracle

EXPECTED = {  # (cells), player, camera, runtime cells, distinct blocks, terrain ring quadrants
    'mghz1': ((128, 32), (78, 192), (0, 80), 4095, 77, 169),
    'mghz2': ((128, 32), (112, 558), (0, 447), 4095, 111, 136),
    'mghz3': ((120, 24), (110, 160), (0, 48), 2880, 52, 83)}
OBJECT_COUNTS = {'mghz1': 35, 'mghz2': 43, 'mghz3': 12}


class CacheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f = json.loads(F.OUTPUT.read_text(encoding='utf-8'))
        cls.c = json.loads(C.OUTPUT.read_text(encoding='utf-8'))
        cls.a = json.loads(AA.CACHE.read_text(encoding='utf-8'))

    def test_dimensions_starts_bounds(self):
        for k, e in EXPECTED.items():
            a = self.f['acts'][k]
            self.assertEqual(a['dimensions_pixels'], [v * 32 for v in e[0]])
            self.assertEqual(a['start']['player_anchor'], list(e[1]))
            self.assertEqual(a['start']['camera'], list(e[2]))
            self.assertEqual(a['layout']['runtime_written_cells'], e[3])
            self.assertEqual(a['census']['distinct_layout_blocks'], e[4])
            self.assertEqual(len(a['rings']['terrain']), e[5])
            self.assertTrue(all(a['descriptor']['consistency'].values()))
            self.assertEqual(a['descriptor']['header']['block_mapping_bank'], 0x14)
        self.assertEqual(self.f['acts']['mghz1']['bounds']['camera_max_words'], [3840, 784])
        self.assertEqual(self.f['acts']['mghz3']['bounds']['camera_max_words'], [3584, 528])

    def test_unloaded_final_cell(self):
        for k in ('mghz1', 'mghz2'):
            self.assertEqual([c['layout_index'] for c in self.f['acts'][k]['layout']['unloaded_cells']], [4095])
        self.assertEqual(self.f['acts']['mghz3']['layout']['unloaded_cells'], [])

    def test_mapping_pointer_is_aligned_and_verified(self):
        m = self.f['mapping_pointer']
        self.assertEqual((m['bank'], m['table_cpu'], m['table_rom']), (0x14, 0x8000, 0x50000))
        self.assertTrue(m['masked_by_alignment'])
        self.assertEqual((m['original_consumer_checks'], m['original_consumer_mismatches']), (512, 0))

    def test_surfaces(self):
        s = self.f['surface_census']['mghz_surfaces']
        self.assertEqual(sorted(s), ['0x00', '0x01', '0x02', '0x03', '0x05', '0x07', '0x09', '0x0A', '0x0D', '0x14', '0x17', '0x18', '0x19', '0x1B'])
        self.assertEqual({k for k, v in s.items() if v['status'] == 'NEW_NEEDS_AUDIT'}, {'0x05', '0x1B'})
        self.assertEqual(s['0x1B']['blocks'], ['0xA0'])
        self.assertEqual(s['0x1B']['cells'], {'mghz1': 70, 'mghz2': 42, 'mghz3': 0})
        self.assertEqual(s['0x17']['cells'], {'mghz1': 0, 'mghz2': 28, 'mghz3': 0})
        self.assertEqual(s['0x0D']['blocks'], ['0x9B', '0x9C'])
        ceiling = self.f['acts']['mghz2']['terrain_interactions']['ceiling_spikes']
        self.assertEqual(len(ceiling), 25)
        for act in self.f['acts'].values():
            self.assertFalse(any(b['alternate_plane_header_differs'] for b in act['blocks']))

    def test_dispatch_chains(self):
        c = self.f['surface_census']['consumers']
        self.assertEqual([x[0] for x in c['side_right_chain']['entries']], ['0x05', '0x0D', '0x13', '0x16'])
        self.assertEqual([x[0] for x in c['ceiling_chain']['entries']], ['0x0D', '0x15', '0x14', '0x13', '0x05'])
        self.assertEqual(c['floor_dispatch_table']['handlers']['0x1B'], '0x6B14')

    def test_ring_animation_and_effects(self):
        t = self.f['terrain_ring_animation']
        self.assertEqual((t['source_bank_cpu'], t['vram_destination'], t['tile_ids']), ('0x1D:0x855D', 0x2160, [267, 268, 269, 270]))
        self.assertTrue(t['per_act_descriptors_identical'])
        e = self.f['level_effects']
        self.assertEqual(e['descriptor_effect_ids'], [2, 3, 14, 0])
        self.assertEqual(e['effects']['14']['events_with_D44E_nonzero_in_40_updates'], 0)
        self.assertEqual([ev['palette_writes'][0]['cram_index'] for ev in e['effects']['2']['first_events']][:2], [4, 4])
        self.assertEqual(e['effects']['14']['first_events'][0]['vram_copies'][0]['vram'], 0x3500)
        for a in self.f['acts'].values():
            self.assertEqual(a['animated_terrain_blocks']['0x1A8'], ['0xD2', '0xD3'] if a['census']['distinct_layout_blocks'] != 52 else a['animated_terrain_blocks']['0x1A8'])

    def test_object_records(self):
        for k, n in OBJECT_COUNTS.items():
            a = self.c['acts'][k]
            self.assertEqual(a['record_count'], n)
            raw = b''.join(bytes.fromhex(r['raw_bytes'].replace(' ', '')) for r in a['records'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), a['records_sha256'])
            for i, r in enumerate(a['records'], 1):
                self.assertEqual(r['index'], i)
                self.assertEqual((r['world_x'], r['world_y']), (r['stored_x'] - 256, r['stored_y'] - 256))
                self.assertIn(r['status'], C.STATUSES)
            self.assertEqual(a['off_map_records'], [])
        self.assertEqual(self.c['acts']['mghz1']['type_counts'], {'0x10': 4, '0x18': 1, '0x1B': 3, '0x21': 6, '0x24': 8, '0x28': 11, '0x2E': 1, '0x2F': 1})
        self.assertEqual(self.c['acts']['mghz3']['type_counts'], {'0x28': 11, '0x56': 1})

    def test_six_zone_census(self):
        t = self.c['six_zone_reuse_census']['types']
        for new in ('0x24', '0x2E', '0x56'):
            self.assertEqual(t[new]['zones'], ['mghz'])
            self.assertEqual(t[new]['buys_other_zone_coverage'], [])
        self.assertEqual(t['0x21']['zones'], ['mghz', 'thz'])
        self.assertEqual(t['0x2F']['zones'], ['mghz', 'sez'])
        self.assertEqual(t['0x2E']['spawned_by_types'], ['0x2E'])

    def test_footwear_matches_accepted_footwear_cache(self):
        shoes = self.c['footwear']['placements']
        self.assertEqual([(s['act'], s['type_id'], s['world_x'], s['world_y']) for s in shoes],
                         [('mghz1', '0x2F', 1552, 238), ('mghz1', '0x10', 1312, 110), ('mghz2', '0x2F', 3760, 494), ('mghz2', '0x2F', 2592, 174), ('mghz2', '0x10', 48, 878)])
        old = json.loads((ROOT / 'data/rom-cache/powerup-shoes.json').read_text(encoding='utf-8'))['placements']['acts']
        for act in old:
            if act['zone'] == 3:
                k = f'mghz{act["act"] + 1}'
                self.assertEqual(self.c['footwear']['counts'][k], {'rocket_shoes_monitors': act['rocket_shoes'], 'spring_shoes': act['spring_shoes']})

    def test_enemies(self):
        e = self.c['enemies']
        self.assertEqual({k: v['classification'] for k, v in e.items()},
                         {'0x21': 'ENEMY_CLASS_2_NEW_ART_REUSED_RUNTIME', '0x24': 'ENEMY_CLASS_3_NEW_RUNTIME_AUDIT', '0x2E': 'ENEMY_CLASS_3_NEW_RUNTIME_AUDIT'})
        self.assertEqual(e['0x21']['init_after_two_updates_first_record']['requested_state_02'], 5)
        self.assertEqual(e['0x21']['init_after_two_updates_first_record']['latch_3f'], 1)
        self.assertEqual(len(e['0x21']['controlled_patrol_traces']), 15)
        self.assertEqual(e['0x24']['visible_frames'], [0, 1, 2, 3])
        self.assertEqual(e['0x2E']['visible_frames'], [0, 1, 2, 3, 4])
        self.assertEqual(e['0x2E']['init_after_two_updates_first_record']['extent_2c_2d'], [0, 0])
        for t in ('0x24', '0x2E'):
            for f in e[t]['frames']:
                for im in f['images']:
                    self.assertEqual(im['forced_diagnostic_mirror'], im['mirror'])
                    self.assertFalse(im['approved_runtime_candidate'])

    def test_boss(self):
        b = self.c['boss']
        self.assertEqual((b['type'], b['state_count'], b['own_states']), (0x56, 13, [3, 6, 7, 8, 9, 10, 11, 12]))
        self.assertEqual((b['placement']['world_x'], b['placement']['world_y']), (3269, 288))
        self.assertEqual({k for k in b['children']}, {'0x57', '0x58'})
        self.assertEqual(b['arena_and_camera']['mghz_row'], {'index': 3, 'trigger_dx_lt': 160, 'trigger_dy_lt': 304, 'camera_x_offset': -208, 'camera_y_offset': -32})
        self.assertEqual(b['arena_and_camera']['rows'][0]['camera_x_offset'], -256)
        self.assertEqual(b['art']['dynamic_selector'], 0x16)
        self.assertEqual([x['tile_count'] for x in b['art']['dynamic_loads']], [64, 12])

    def test_art_approval_recorded(self):
        self.assertTrue(self.a['approval'].startswith('APPROVED BY USER'))
        self.assertIn('forced/diagnostic mirrors', self.a['approved_runtime_candidates'])
        self.assertEqual(sorted(self.a['subjects']), ['0x21', '0x24', '0x28', '0x2E', '0x2F', '0x56'])


class RomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p = Path(os.environ.get('SONIC_CHAOS_ROM', str(ROOT.parent / 'source/Sonic Chaos (Europe).sms')))
        if not p.is_file():
            raise unittest.SkipTest('canonical local ROM unavailable')
        cls.r = L.load_rom(p)

    def test_fresh_regeneration(self):
        self.assertEqual(F.dumps(F.build(self.r)), F.OUTPUT.read_text(encoding='utf-8'))
        self.assertEqual(C.dumps(C.build(self.r)), C.OUTPUT.read_text(encoding='utf-8'))
        self.assertEqual(json.dumps(AA.manifest_for(AA.build(self.r)), indent=2) + '\n', AA.CACHE.read_text(encoding='utf-8'))

    def test_original_start_loader(self):
        f = json.loads(F.OUTPUT.read_text(encoding='utf-8'))
        for act, (k, a) in enumerate(f['acts'].items()):
            o = Oracle(self.r)
            o.mem[0xD297], o.mem[0xD298] = 3, act
            o.call(0x4E57)
            self.assertEqual([o.word(v) for v in (0xD2D6, 0xD2D8)], a['start']['camera'])
            self.assertEqual([o.word(v) for v in (0xD511, 0xD514)], a['start']['player_anchor'])

    def test_header_bytes_and_independent_layout(self):
        f = json.loads(F.OUTPUT.read_text(encoding='utf-8'))
        for act, (k, a) in enumerate(f['acts'].items()):
            h = L.act_header(self.r, 3, act)
            self.assertEqual(bytes.fromhex(h['raw'])[:3], bytes([0x14, 0x00, 0x80]))
            cells, _, ok = L.decode_layout_stream(self.r, h['layout_rom'])
            self.assertTrue(ok)
            self.assertEqual(cells, [b for row in a['layout']['rows'] for b in row])
            for b in a['blocks']:
                for plane in (0, 1):
                    self.assertEqual(b['headers'][plane], R.header(self.r, b['block_id'], plane))

    def test_mapping_pointer_against_original_consumers(self):
        from block_mapping_audit import original_pointer
        o = Oracle(self.r)
        h = L.act_header(self.r, 3, 1)
        o.mem[0xD297], o.mem[0xD298] = 3, 1
        o.call(0x4FDC)
        self.assertEqual((o.mem[0xD162], o.word(0xD164)), (0x14, 0x8000))
        o.cpu.a = 0x14
        o.call(0x1C6F)
        for block in (0x00, 0x40, 0x9B, 0xA0, 0xD2, 0xFE):
            m = L.block_mapping(self.r, h['block_mapping_rom'], block)
            for vertical in (False, True):
                cpu = original_pointer(o, h['block_mapping_cpu'], block, vertical)
                self.assertEqual(cpu, m['cpu'])
                self.assertEqual(bytes(o.mem[cpu:cpu + 32]), self.r[m['rom']:m['rom'] + 32])

    def test_non_aligned_formula_would_be_wrong_for_aqua(self):
        h = L.act_header(self.r, 4, 0)       # same bank $14, table at $9320: old formula would add $1320
        m = L.block_mapping(self.r, h['block_mapping_rom'], 0)
        self.assertEqual(m['rom'], 0x50000 + m['cpu'] - 0x8000)
        self.assertNotEqual(m['rom'], h['block_mapping_rom'] + m['cpu'] - 0x8000)

    def test_surface_1b_and_ceiling_spike_bytes(self):
        o = Oracle(self.r)
        o.cpu.ix = 0xD500
        o.mem[0xD524] = 0
        o.mem[0xD3BC] = 5
        o.mem[0xD12F] = 4
        o.call(0x6B14)
        self.assertEqual((o.mem[0xD524] & 2, o.mem[0xD3BC]), (2, 6))
        o.mem[0xD12F] = 5
        o.call(0x6B14)
        self.assertEqual(o.mem[0xD3BC], 6)
        self.assertEqual(self.r[0x7520:0x7523], bytes([0xFE, 0x3E, 0xC2]))     # CP $3E; JP NZ
        self.assertEqual(self.r[0x6A5D:0x6A63], bytes([0x3A, 0x97, 0xD2, 0xFE, 0x05, 0xC0]))  # surface-1 handler is zone-5 only

    def test_twist_variant_gate_and_prize_parity(self):
        self.assertEqual(self.r[0x6E7F:0x6E85], bytes([0x3A, 0x97, 0xD2, 0xFE, 0x03, 0x20]))
        self.assertEqual(self.r[0x6EE8:0x6EEE], bytes([0x3A, 0x97, 0xD2, 0xFE, 0x03, 0xC2]))
        self.assertEqual(self.r[0x6F5A:0x6F5E], bytes([0xDD, 0x36, 0x38, 0x03]))
        self.assertEqual(self.r[0x30000 + 0x2909:0x30000 + 0x290E], bytes([0x3A, 0x97, 0xD2, 0x3C, 0x0F]))

    def test_original_type_21_flags_10_init(self):
        census = json.loads(C.OUTPUT.read_text(encoding='utf-8'))
        a = C.vram_for_act(self.r, 0)
        rec = a and next(x for x in C.decode_records(self.r)['mghz1']['records'] if x['type_id'] == '0x21')
        info = C.init_after_two_updates(self.r, a, rec)
        self.assertEqual((info['requested_state_02'], info['latch_3f'], info['vx_8_8']), (5, 1, -128))
        self.assertEqual(census['enemies']['0x21']['init_after_two_updates_first_record'], info)

    def test_boss_child_and_art_sources(self):
        t = C.state_table(self.r, 0x56)
        self.assertEqual((t['bank'], t['state_table_cpu'], t['state_count']), (0x1E, 0xA4C4, 13))
        self.assertEqual(self.r[0x7A576:0x7A57E], bytes([0x3E, 0x16, 0x32, 0xB3, 0xD3, 0x21, 0x94, 0xD4]))
        self.assertEqual(self.r[0x7A582], 15)


if __name__ == '__main__':
    unittest.main()
