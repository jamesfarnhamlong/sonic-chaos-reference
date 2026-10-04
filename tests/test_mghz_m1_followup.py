"""MGHZ M1 Windows follow-up audit: cache locks plus ROM-backed re-execution of the original routines.

Cache classes run without a ROM.  ROM classes need the verified ROM (SONIC_CHAOS_ROM or ../source/Sonic Chaos (Europe).sms) and skip otherwise.
Never touches POC.
"""
import hashlib
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import mghz_m1_followup as T
import level_package as L

ROM_SHA = 'eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607'
D = json.loads(T.OUTPUT.read_text(encoding='utf-8'))
A, B, C = D['part_a'], D['part_b'], D['part_c']


def load_rom():
    candidates = []
    if os.environ.get('SONIC_CHAOS_ROM'):
        candidates.append(Path(os.environ['SONIC_CHAOS_ROM']))
    candidates += [ROOT.parent / 'source/Sonic Chaos (Europe).sms', ROOT.parent / 'Sonic Chaos (Europe).sms']
    for p in candidates:
        if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest() == ROM_SHA:
            return L.load_rom(p)
    return None


ROM = load_rom()
rom_only = unittest.skipIf(ROM is None, 'verified ROM not available')


class CacheIdentity(unittest.TestCase):
    def test_identity_and_scope(self):
        self.assertEqual(D['rom_sha256'], ROM_SHA)
        self.assertTrue(D['research_only'] and D['poc_untouched'])
        self.assertIn('boss $56', D['scope']['out'])


class PartACache(unittest.TestCase):
    fx = A['fixtures']

    def test_only_four_vertical_movers_meet_overhead_terrain(self):
        hits = {(act, r['record_index']): [h['block'] for h in r['overhead_hits']] for act, rows in A['placements'].items() for r in rows if r['overhead_hits']}
        self.assertEqual(sorted(hits), [('mghz1', 10), ('mghz1', 11), ('mghz2', 12), ('mghz2', 13)])
        self.assertEqual(hits[('mghz1', 10)], ['0xF9'])
        self.assertEqual(hits[('mghz2', 12)], ['0x9C'] * 8 + ['0xF9'])
        self.assertEqual(hits[('mghz2', 13)], ['0x9C'] * 5 + ['0xF9'])
        # no ordinary solid (bit 7, non-$0D) ceiling on any vertical mover path
        for rows in A['placements'].values():
            for r in rows:
                for hit in r['overhead_hits']:
                    self.assertIn(hit['surface_type'], ('0x0D', '0x01'))
                    self.assertTrue(hit['block'] in ('0x9C', '0xF9'))

    def test_first_fatal_platform_y_rule(self):
        m12 = [r for r in A['placements']['mghz2'] if r['record_index'] == 12][0]
        self.assertEqual(m12['overhead_hits'][0]['platform_y_first'], 531)
        m13 = [r for r in A['placements']['mghz2'] if r['record_index'] == 13][0]
        self.assertEqual(m13['overhead_hits'][0]['platform_y_first'], 435)

    def test_ride_death_fixtures(self):
        d = self.fx['mghz2_12_ride_into_breakable_0d']
        for k in ('rings_0', 'rings_5'):
            r = d[k]
            self.assertEqual((r['support_claim_update'], r['death_update'], r['platform_y_at_start_of_death_update'], r['player_y_in_death_pass']), (11, 104, 531, 517))
            self.assertEqual(r['events_in_death_update'][-2:], ['ceiling_surface_0d', 'crush_death_4984'])
            self.assertEqual((r['player_state_after']['req'], r['player_state_after']['vy']), (0x1F, -1280))
            self.assertTrue(r['platform_frozen_after_death'])
        self.assertEqual(d['rings_0']['player_state_after']['rings'], 0)
        self.assertEqual(d['rings_5']['player_state_after']['rings'], 5)
        r13 = self.fx['mghz2_13_ride_into_breakable_0d']['rings_0']
        self.assertEqual((r13['support_claim_update'], r13['death_update'], r13['platform_y_at_start_of_death_update'], r13['player_y_in_death_pass']), (11, 136, 435, 421))

    def test_jump_window_and_break(self):
        runs = self.fx['mghz2_12_jump_window']['outcome_runs']
        self.assertEqual([(r['outcome'], r['from'], r['to']) for r in runs], [('death', 20, 51), ('break', 52, 102), ('death', 103, 109)])
        b = self.fx['mghz2_12_break_by_jump']
        self.assertEqual((b['jump_update'], b['break_update'], b['player_y_in_break_pass'], b['vy_in_break_update'], b['d3c0_in_break_update']), (60, 75, 517, -464, 0))
        self.assertIn('break_7898', b['events'])

    def test_one_way_snap(self):
        for k, (u, y0, y1, depth) in {'mghz1_10_one_way_snap_natural': (194, 217, 206, 11), 'mghz1_11_one_way_snap_natural': (450, 377, 366, 11)}.items():
            r = self.fx[k]
            self.assertTrue(r['snapped'])
            self.assertEqual((r['snap_update'], r['player_y_in_pass'], r['player_y_after'], r['feet_depth_in_block'], r['support_after'], r['floor_flag_after']), (u, y0, y1, depth, 0, 2))
            self.assertEqual(r['player_y_after'], r['standing_anchor'])
        sw = self.fx['mghz1_10_one_way_depth_sweep']
        self.assertTrue(sw['matches_model'])
        self.assertEqual([t['feet_depth_in_block'] for t in sw['rows']], [8, 9, 10, 11, 11, 12, 13, 15])
        self.assertEqual({t['player_y_after'] for t in sw['rows']}, {206})

    def test_update_order(self):
        seq = A['update_order']['events_in_one_update_while_riding']
        self.assertEqual(seq, ['player_update', 'x_integration', 'y_integration', 'terrain_pass', 'terrain_floor', 'terrain_sides', 'terrain_ceiling', 'object_move',
                               'platform_support', 'overlap_6328', 'platform_carry'])

    def test_synthetic_control_is_labelled_and_pops(self):
        c = self.fx['synthetic_solid_control']
        self.assertEqual(c['ceiling_bounce_updates'], list(range(104, 110)))
        self.assertEqual(c['first_pop_update'], 129)

    def test_assembly_listing_contains_the_branch(self):
        text = '\n'.join(A['assembly']['ceiling_0d_7464'])
        self.assertIn('JP z,0x7898', text)
        self.assertIn('JP 0x4984', text)


class PartBCache(unittest.TestCase):
    def test_only_d2_d3_consume_the_tiles(self):
        for tile, per in B['consumers']['tile_to_blocks_all_256_blocks'].items():
            self.assertEqual(per, {'mghz1': ['0xD2', '0xD3'], 'mghz2': ['0xD2', '0xD3'], 'mghz3': ['0xD2', '0xD3']})
        self.assertFalse(B['consumers']['sprite_pattern_consumers']['any_object_uses_vram_tile_1a8_1a9'])

    def test_block_mapping(self):
        m = B['consumers']['block_mapping']
        self.assertEqual(m['0xD2']['tile_ids'], [192] * 12 + [424, 424, 425, 425])
        self.assertEqual(m['0xD3']['tile_ids'], [192] * 12 + [425, 425, 424, 424])
        self.assertEqual(m['0xD2']['h_flip'][12:], [False, True, False, True])
        self.assertEqual((m['0xD2']['surface'], m['0xD2']['priority_tiles']), (0, 0))

    def test_cells(self):
        cells = B['consumers']['layout_cells']
        self.assertEqual([cells[k]['count'] for k in ('mghz1', 'mghz2', 'mghz3')], [37, 44, 22])
        self.assertEqual(sum(1 for k in ('mghz1', 'mghz2', 'mghz3') for c in cells[k]['cells']), 103)
        self.assertEqual(cells['mghz2']['twist_cells_surface_17'], 28)
        self.assertEqual([c[:2] for c in cells['mghz3_boss_area']['cells_with_x_ge_boss_x_minus_256']], [[105, 11], [109, 11], [113, 11], [114, 11], [118, 11]])

    def test_frame_schedule_and_overlap(self):
        e = B['effect_14']
        self.assertEqual(e['schedule_updates_zero_based'][:4], [[3, '0x8E3D'], [7, '0x8E1D'], [11, '0x8E3D'], [15, '0x8E1D']])
        t = B['tiles']
        self.assertEqual(t['initial']['0x1A8']['sha256'], t['source_B_8E1D']['0x1A8']['sha256'])
        self.assertEqual(t['source_A_8E3D']['0x1A8']['sha256'], t['initial']['0x1A9']['sha256'])   # sliding window X0 X1 X2 with X0 == X2
        self.assertEqual(t['source_A_8E3D']['0x1A9']['sha256'], t['initial']['0x1A8']['sha256'])

    def test_no_horizontal_line_in_rom_art(self):
        self.assertTrue(B['tile_c0_all_zero'])
        for state, blocks in B['thin_line_audit'].items():
            for blk, a in blocks.items():
                self.assertEqual(a['horizontal_line_rows'], [], (state, blk))
                self.assertEqual(a['rows_fully_nonzero'], [], (state, blk))
                self.assertLess(a['widest_row_nonzero_run'], 16)
        for state, blocks in B['block_art_hashes'].items():
            for blk, a in blocks.items():
                self.assertTrue(a['top_24_rows_all_zero'])
                self.assertEqual(a['rows_with_any_nonzero'], list(range(24, 32)))
        self.assertTrue(B['emulated_nametable']['tile_above_each_is_c0'] and B['emulated_nametable']['all_in_bottom_row_of_a_4_row_group'])
        self.assertFalse(B['emulated_nametable']['sprite_pattern_register_r6_bit2'])


class PartCCache(unittest.TestCase):
    def test_intact_blocks_have_no_animated_art(self):
        for blk in ('0x9B', '0x9C'):
            for per in C['blocks'][blk].values():
                self.assertEqual(per['uses_animated_tile'], [])
                self.assertEqual(per['uses_cycled_palette_entry_4_or_11'], [])
                self.assertEqual((per['surface'], per['header_flags']), (13, '0x8D'))
        self.assertEqual(C['blocks']['0x9D']['mghz1']['uses_cycled_palette_entry_4_or_11'], [4, 11])
        self.assertFalse(C['answer']['animation_before_destruction'] or C['answer']['frame_change_during_destruction'])

    def test_break_routine_and_fragments(self):
        text = '\n'.join(C['break_routine_7898']['assembly'])
        self.assertIn('LD A,0x9d', text)
        self.assertEqual(sum(1 for line in C['break_routine_7898']['assembly'] if 'CALL 0x5e9c' in line or 'JP 0x5e9c' in line), 4)
        f = C['fragment_object_07']
        self.assertEqual([s['ops'][0].get('sound') for s in f['state_scripts'][:1]], [163])
        self.assertEqual(f['frames']['0']['piece_count'], 0)
        self.assertEqual(f['frames']['15']['piece_count'], 1)
        ge, lt = f['offset_tables']['player_x_speed_ge_0_table_9b75'], f['offset_tables']['player_x_speed_lt_0_table_9b95']
        self.assertEqual([(q['x_offset'], q['y_offset'], q['x_speed'], q['y_speed']) for q in ge], [(4, 0, -512, -1024), (20, 0, 128, -768), (4, 20, -512, -256), (20, 20, 128, -512)])
        self.assertEqual([(q['x_offset'], q['y_offset'], q['x_speed'], q['y_speed']) for q in lt], [(4, 0, -128, -768), (20, 0, 512, -1024), (4, 20, -128, -512), (20, 20, 512, -256)])

    def test_emulated_floor_break(self):
        e = C['emulated_floor_break']
        self.assertEqual((e['break_update'], e['break_row']['broken_cell'], e['break_row']['broken_cell_after'], e['break_row']['vy']), (12, [76, 23], '0x9D', -1088))
        self.assertEqual([ (f['x'], f['y'], f['vx'], f['vy']) for f in e['break_row']['fragments']], [(2436, 736, -512, -1024), (2452, 736, 128, -768), (2436, 756, -512, -256), (2452, 756, 128, -512)])
        l = C['emulated_floor_break_moving_left']
        self.assertEqual([(f['vx'], f['vy']) for f in l['break_row']['fragments']], [(-128, -768), (512, -1024), (-128, -512), (512, -256)])
        self.assertEqual(e['fragment_vy_track_q0'][:3], [-1024, -832, -640])    # +192 per update


@rom_only
class RomReexecution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rig2 = T.Rig(ROM, 'mghz2')
        cls.rig1 = T.Rig(ROM, 'mghz1')

    def test_static_scan_matches_cache(self):
        self.assertEqual(json.loads(json.dumps(T.platform_scan(ROM))), A['placements'])

    def test_ride_death_reexecuted(self):
        self.assertEqual(json.loads(json.dumps(T.ride_death(self.rig2, 2768, 624, 15, 0))), A['fixtures']['mghz2_12_ride_into_breakable_0d']['rings_0'])
        self.assertEqual(json.loads(json.dumps(T.ride_death(self.rig2, 3024, 560, 12, 0))), A['fixtures']['mghz2_13_ride_into_breakable_0d']['rings_0'])

    def test_jump_boundaries_reexecuted(self):
        rig = self.rig2
        for j, want in ((51, 'death'), (52, 'break'), (102, 'break'), (103, 'death')):
            rows = rig.ride(2768, 585, j + 90, jump=(j, j + 1, j + 2), until=lambda r, rs: 'crush_death_4984' in r['ev'] or 'break_7898' in r['ev'])
            got = 'break' if 'break_7898' in rows[-1]['ev'] else 'death' if 'crush_death_4984' in rows[-1]['ev'] else 'none'
            self.assertEqual(got, want, j)

    def test_one_way_snap_reexecuted(self):
        self.assertEqual(json.loads(json.dumps(T.one_way_snap(self.rig1, 2768, 414, 7))), A['fixtures']['mghz1_10_one_way_snap_natural'])
        r = T.one_way_snap(self.rig1, 2768, 414, 7, retained=0)
        self.assertEqual((r['feet_depth_in_block'], r['player_y_after']), (8, 206))

    def test_break_by_jump_reexecuted(self):
        self.assertEqual(json.loads(json.dumps(T.break_by_jump(self.rig2, 2768, 624, 60))), A['fixtures']['mghz2_12_break_by_jump'])

    def test_floor_break_reexecuted(self):
        self.assertEqual(json.loads(json.dumps(T.hole_run(self.rig1, 76, 23, 70, 0x300, 0x0A, 3))), C['emulated_floor_break'])

    def test_static_b_c_match_cache(self):
        b = T.part_b(ROM, static_only=True)
        for k in ('consumers', 'tiles', 'effect_14', 'block_art_hashes', 'thin_line_audit'):
            self.assertEqual(json.loads(json.dumps(b[k])), B[k], k)
        c = T.part_c(ROM, None, True)
        for k in ('blocks', 'triggers', 'break_routine_7898', 'fragment_object_07'):
            self.assertEqual(json.loads(json.dumps(c[k])), C[k], k)

    def test_nametable_scan_reexecuted(self):
        self.assertEqual(T.emulated_nametable(ROM), B['emulated_nametable'])


if __name__ == '__main__':
    unittest.main()
