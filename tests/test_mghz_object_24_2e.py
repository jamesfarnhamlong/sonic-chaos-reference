"""MGHZ object $24 / $2E audit: cache locks plus ROM-backed re-execution of the original routines.

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
import mghz_object_24_2e as T
import level_package as L

ROM_SHA = 'eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607'
D = json.loads(T.OUTPUT.read_text(encoding='utf-8'))
O24, O2E = D['object_24'], D['object_2e']


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
needs_rom = unittest.skipUnless(ROM, 'matching ROM not available (set SONIC_CHAOS_ROM)')


class CacheIdentity(unittest.TestCase):
    def test_identity_and_scope(self):
        self.assertEqual(D['rom_sha256'], ROM_SHA)
        self.assertTrue(D['research_only'] and D['poc_untouched'])
        self.assertEqual(D['scope']['in'], ['$24', '$2E'])
        self.assertEqual(D['research_base'], '4149f84')
        self.assertFalse(D['art']['new_visual_approval_required'])

    def test_no_descriptive_name_adopted(self):
        for t in ('0x24', '0x2E'):
            self.assertIn('no descriptive name adopted', D['identity'][t]['name_status'])

    def test_placements_complete_and_mghz_only(self):
        p = D['placements']
        self.assertEqual(p['lists_scanned'], 18)
        self.assertEqual(p['total_matching_records'], 14)
        self.assertEqual(p['by_act'], {'mghz1': 9, 'mghz2': 5})
        self.assertEqual(p['later_zone_placements'], [])
        self.assertEqual(D['census_cross_check']['census_placement_counts'], {'0x24': 12, '0x2E': 2})
        self.assertEqual(D['census_cross_check']['this_audit_counts'], {'0x24': 12, '0x2E': 2})

    def test_placement_records_exact(self):
        got = [(r['act'], r['index_1based'], r['type'], r['world_x'], r['world_y'], r['parameter'], r['aux0'], r['aux1'], r['flags']) for r in D['placements']['records']]
        expected = [
            ('mghz1', 26, '0x24', 456, 112, '0x01', '0xA0', '0xA0', '0x00'), ('mghz1', 27, '0x24', 472, 112, '0x00', '0xA0', '0xA0', '0x00'),
            ('mghz1', 28, '0x24', 2120, 112, '0x01', '0xA0', '0xA0', '0x00'), ('mghz1', 29, '0x24', 2136, 112, '0x00', '0xA0', '0xA0', '0x00'),
            ('mghz1', 30, '0x24', 2664, 112, '0x01', '0xA0', '0xA0', '0x00'), ('mghz1', 31, '0x24', 2680, 112, '0x00', '0xA0', '0xA0', '0x00'),
            ('mghz1', 32, '0x24', 3080, 48, '0x01', '0xA0', '0xA0', '0x00'), ('mghz1', 33, '0x24', 3096, 48, '0x00', '0xA0', '0xA0', '0x00'),
            ('mghz1', 34, '0x2E', 1352, 780, '0x00', '0x72', '0x13', '0x00'),
            ('mghz2', 38, '0x24', 808, 48, '0x01', '0xA0', '0xA0', '0x00'), ('mghz2', 39, '0x24', 824, 48, '0x00', '0xA0', '0xA0', '0x00'),
            ('mghz2', 40, '0x24', 2888, 112, '0x01', '0xA0', '0xA0', '0x00'), ('mghz2', 41, '0x24', 2904, 112, '0x00', '0xA0', '0xA0', '0x00'),
            ('mghz2', 42, '0x2E', 232, 908, '0x00', '0x72', '0x1B', '0x00')]
        self.assertEqual(got, expected)

    def test_pairs_and_families(self):
        r24 = [r for r in D['placements']['records'] if r['type'] == '0x24']
        for a, b in zip(r24[0::2], r24[1::2]):
            self.assertEqual((a['parameter'], b['parameter']), ('0x01', '0x00'))
            self.assertEqual((b['world_x'] - a['world_x'], b['world_y'] - a['world_y']), (16, 0))
            self.assertEqual((a['fall_vx_8_8'], b['fall_vx_8_8']), (-128, 128))
        for r in D['placements']['records']:
            self.assertEqual(r['creation_flags_04'], '0x40')
            self.assertEqual(r['occupancy_token'], r['index_1based'])
        strips = [r for r in D['placements']['records'] if r['type'] == '0x2E']
        self.assertEqual([(r['strip_x_exclusive_left'], r['strip_x_inclusive_right']) for r in strips], [(1352, 1656), (232, 664)])

    def test_creators_and_alias(self):
        c = D['creators']
        self.assertEqual(c['state_table_alias_groups_containing_24_or_2E'], {'0x8A45': ['0x2D', '0x2E']})
        self.assertEqual(c['type_2D_placements_in_the_18_lists'], [])
        self.assertTrue(all(not v for v in c['immediate_type_load_patterns_FD3600nn_and_3Ennfd77'].values()))
        spawners = {x['spawned_by_type'] for x in c['state_script_spawn_commands_for_24_2E_over_types_01_5F']['0x2E']}
        self.assertEqual(spawners, {'0x2D', '0x2E'})
        self.assertNotIn('0x24', c['state_script_spawn_commands_for_24_2E_over_types_01_5F'])

    def test_creator_init_in_cache(self):
        for r in D['creator_init']:
            self.assertEqual(r['after_creator']['flags_04'], '0x40')
            self.assertEqual(r['after_creator']['state'], 0)
            self.assertEqual(r['after_creator']['x'], r['after_creator']['origin_x'])
            self.assertEqual(r['after_creator']['y'], r['after_creator']['origin_y'])
        t24 = [r for r in D['creator_init'] if r['after_creator']['type'] == 0x24]
        self.assertTrue(all(r['after_two_updates']['state'] == 1 and r['callback_after_two_updates'] == '0xB49A' for r in t24))
        self.assertEqual({(r['after_two_updates']['ex'], r['after_two_updates']['ey']) for r in t24}, {(4, 11)})
        t2e = [r for r in D['creator_init'] if r['after_creator']['type'] == 0x2E]
        self.assertTrue(all(r['callback_after_two_updates'] == '0x8AE5' for r in t2e))


class StaticFacts(unittest.TestCase):
    def test_state_tables(self):
        s = D['static']['state_tables']
        self.assertEqual(s['0x24']['state_script_cpus'], ['0xB44D', '0xB453', '0xB461', '0xB482'])
        self.assertEqual(s['0x24']['callbacks'], ['0xB490', '0xB49A', '0xB4C5', '0xB4D1', '0xB4F0'])
        self.assertEqual(s['0x2E']['state_script_cpus'], ['0x8A4D', '0x8A53', '0x8A59', '0x8A7A'])
        self.assertEqual(s['0x2E']['callbacks'], ['0x032F', '0x034A', '0x8A8A', '0x8AE5', '0x8B10'])
        self.assertEqual(s['0x24']['bank'], '0x0C')
        self.assertEqual(s['0x2E']['bank'], '0x1E')
        self.assertFalse(s['0x24']['sets_bit4'] or s['0x2E']['sets_bit4'] or s['0x24']['clears_bit4'] or s['0x2E']['clears_bit4'])
        self.assertEqual([x['type'] for x in s['0x2E']['spawns']], ['0x2E'] * 3)
        self.assertEqual([(x['dx'], x['dy'], x['parameter']) for x in s['0x2E']['spawns']], [(4, 0, 1), (0, -2, 2), (-4, -4, 3)])
        self.assertEqual(s['0x24']['spawns'], [])

    def test_24_script_records(self):
        st = D['static']['state_tables']['0x24']['states']
        self.assertEqual([(o['duration'], o['frame']) for o in st[1]['ops'] if o['op'] == 'record'], [(8, 1), (8, 2), (8, 3)])
        ops2 = st[2]['ops']
        self.assertEqual([o['op'] for o in ops2], ['set_loop_counter', 'velocity_8_8', 'record', 'velocity_8_8', 'record', 'loop_jump', 'record', 'restart_state'])
        self.assertEqual([(o.get('x'), o.get('y')) for o in ops2 if o['op'] == 'velocity_8_8'], [(512, 0), (-512, 0)])
        self.assertEqual(ops2[0]['count'], 4)
        self.assertEqual([(o['duration'], o['frame'], o['callback']) for o in ops2 if o['op'] == 'record'], [(2, 1, '0xB4C5'), (2, 2, '0xB4C5'), (4, 3, '0xB4D1')])
        self.assertEqual([(o['duration'], o['frame']) for o in st[3]['ops'] if o['op'] == 'record'], [(4, 1), (4, 2), (4, 3)])

    def test_2e_script_records(self):
        st = D['static']['state_tables']['0x2E']['states']
        self.assertEqual([(o['duration'], o['frame'], o['callback']) for o in st[2]['ops'] if o['op'] == 'record'], [(4, 4, '0x032F')])
        self.assertEqual(st[2]['ops'][-1], {'cpu': '0x8A75', 'command': 3, 'op': 'request_state', 'state': 1})
        self.assertEqual([(o['duration'], o['frame'], o['callback']) for o in st[3]['ops'] if o['op'] == 'record'], [(4, 1, '0x8B10'), (4, 2, '0x8B10'), (4, 3, '0x8B10'), (224, 3, '0x034A')])

    def test_frame_headers(self):
        fh = D['static']['frame_headers']
        self.assertEqual([(f['extent_x'], f['extent_y']) for f in fh['0x24']], [(0, 0), (4, 11), (4, 11), (4, 11)])
        self.assertEqual([(f['extent_x'], f['extent_y']) for f in fh['0x2E']], [(0, 0), (4, 16), (4, 16), (4, 16), (8, 16)])
        self.assertEqual([f['piece_count'] for f in fh['0x2E']], [0, 1, 1, 1, 2])

    def test_callbacks_use_only_expected_helpers(self):
        refs = D['static']['callback_helper_references']
        self.assertEqual(refs['0x24']['calls_and_jumps'], ['CALL 0x0434', 'CALL 0x0383', 'CALL 0x0434', 'CALL 0x0338', 'CALL 0x0434', 'CALL 0x0338', 'CALL 0x0431', 'CALL 0x037a', 'JP 0x033e'])
        self.assertEqual(refs['0x2E']['calls_and_jumps'], ['CALL 0x0386', 'CALL 0x0338', 'CALL 0x0431'])
        self.assertEqual(refs['0x24']['reads_of_extents_2c_2d'] + refs['0x2E']['reads_of_extents_2c_2d'], [])
        self.assertEqual(D['static']['extent_readers']['inside_the_24_or_2E_callback_ranges'], [])
        self.assertEqual(D['static']['extent_readers']['total_matches'], 18)

    def test_vectors_resolve(self):
        v = D['static']['code']['vectors']
        self.assertEqual(v['0x0434']['vector_jp_target'], '0x630B')
        self.assertEqual(v['0x033E']['vector_jp_target'], '0x5F54')
        self.assertEqual(v['0x037A']['vector_jp_target'], '0x614E')
        self.assertEqual(v['0x034A']['vector_jp_target'], '0x64F0')
        self.assertEqual(v['0x032F']['vector_jp_target'], '0x6065')

    def test_mapping_and_art(self):
        m = D['static']['mapping_and_art_from_census']
        self.assertEqual(m['0x24']['mapping']['mapping_rom'], '0x3D169')
        self.assertEqual(m['0x2E']['mapping']['mapping_rom'], '0x3D24C')
        self.assertEqual(m['0x24']['art']['placement_bases'], ['0xA0', '0xA0'])
        self.assertEqual(m['0x2E']['art']['placement_bases'], ['0x72', '0x13'])
        self.assertEqual(m['0x24']['art']['sprite_palette_index'], 9)


class Object24Cache(unittest.TestCase):
    def test_trigger_rule(self):
        for k, t in O24['trigger'].items():
            self.assertEqual(t['dx_that_fire_vx0'], [-47, 47])
            self.assertEqual(t['vx_that_fire_dx0'], [-255, 255])
            self.assertEqual(t['dy_dependence'], 'none')
            self.assertFalse(t['asleep_flag_0x40_fires'])
            c = t['corner_cases']
            self.assertTrue(c['dx=47,vx=255'] and c['dx=-47,vx=-255'])
            self.assertFalse(c['dx=48,vx=255'] or c['dx=47,vx=256'] or c['dx=-47,vx=-256'])
            self.assertTrue(all(not v for v in t['vx_extremes_fire'].values()))

    def test_shake_and_fall_template(self):
        for prm, sign in (('0', 1), ('1', -1)):
            t = O24['shake_and_fall_templates_by_parameter'][prm]
            self.assertEqual((t['trigger_update'], t['first_state3_update'], t['shake_updates']), (0, 18, 17))
            rows = t['rows_from_trigger']
            x0 = rows[0][4]
            offs = [r[4] - x0 for r in rows[1:17]]
            self.assertEqual(offs, [2, 4, 2, 0] * 4)
            self.assertEqual([r[3] for r in rows[1:17]], [1, 1, 2, 2] * 4)
            self.assertTrue(all(r[1] == 2 for r in rows[1:18]))
            self.assertEqual((rows[17][1], rows[17][2], rows[17][3], rows[17][8], rows[17][9]), (2, 3, 3, 128 * sign, 0))
            self.assertEqual(rows[17][4], x0)

    def test_fall_first_rows_exact(self):
        r = O24['shake_and_fall_templates_by_parameter']['1']['rows_from_trigger']
        self.assertEqual([(x[4], x[5], x[6], x[7], x[9]) for x in r[18:24]], [(455, 128, 112, 0, 16), (455, 0, 112, 16, 32), (454, 128, 112, 48, 48), (454, 0, 112, 96, 64), (453, 128, 112, 160, 80), (453, 0, 112, 240, 96)])

    def test_landing_table_controlled(self):
        lt = O24['landing_table_controlled']
        self.assertEqual(len(lt), 12)
        self.assertTrue(O24['landing_all_match_model'])
        for r in lt:
            self.assertTrue(r['converted'] and r['model_matches_lab'])
            self.assertEqual(r['fall_updates_to_conversion'], 56)
            self.assertEqual(r['slot_after_conversion']['type'], 0x0F)
            self.assertEqual(r['slot_after_conversion']['y'], r['y'] + 96)
            self.assertEqual(r['slot_after_conversion']['x'], r['x'] + (28 if r['parameter'] == 0 else -28))
            self.assertEqual(r['model']['block'], 1)
            self.assertEqual(r['model']['block_header_flags'], '0x81')
            self.assertEqual(r['trigger_update'], 0)
            self.assertEqual(r['first_fall_update'], 18)

    def test_contact_boxes(self):
        c = O24['contact']
        self.assertEqual(c['object_extents'], [4, 11])
        self.assertEqual(c['mismatch_with_closed_interval_model'], 0)
        v = c['variants']
        self.assertEqual(v['ordinary_8x24']['hit_rects_dx0_dx1_dy0_dy1'], [[-12, 12, -11, 24]])
        self.assertEqual(v['state_0F_9x24']['hit_rects_dx0_dx1_dy0_dy1'], [[-13, 13, -11, 24]])
        self.assertEqual(v['attack_bit1']['hit_rects_dx0_dx1_dy0_dy1'], [[-12, 12, -11, 24]])
        self.assertEqual(v['invincible_d532_6']['hit_rects_dx0_dx1_dy0_dy1'], [[-12, 12, -11, 24]])
        self.assertEqual(v['player_bit6']['hit_cells'], 0)
        self.assertEqual(v['player_bit7_blink']['flag_20_set_in_hits'], [0])
        self.assertEqual(v['ordinary_8x24']['d520_in_hits'], [9])
        self.assertTrue(all(x['mismatch'] == 0 for x in v.values()))

    def test_whole_game_timeline_and_pair(self):
        p = O24['whole_game']['pair_fixture_mghz1_index26_27']
        a = p['stand_beside_A_only']
        self.assertEqual((a['A']['events']['trigger_request'], a['A']['events']['state3_loaded'], a['A']['events']['converted_to_0F']), (5, 23, 78))
        self.assertEqual(a['A']['events']['converted_to_0F'] - a['A']['events']['trigger_request'], 73)
        self.assertEqual(a['A']['fall_engine_passes_state3_to_conversion'], 55)
        self.assertNotIn('trigger_request', a['B']['events'])
        self.assertEqual(a['score_after_150_frames_bcd'], '000010')
        self.assertEqual(a['occupancy_A'], '0x24')
        b = p['stand_beside_B_only']
        self.assertNotIn('trigger_request', b['A']['events'])
        self.assertIn('trigger_request', b['B']['events'])
        both = p['stand_between_both']
        self.assertEqual(both['score_after_150_frames_bcd'], '000020')
        self.assertEqual(both['A']['events']['trigger_request'], both['B']['events']['trigger_request'])
        t = O24['timeline']['lab']
        self.assertEqual((t['shake_updates_T_plus'], t['init_update_sets_fall_velocity_T_plus'], t['first_falling_update_T_plus']), ([1, 16], 17, 18))

    def test_whole_game_landings_match_controlled(self):
        wl = O24['whole_game']['landing_all_12_placements']
        self.assertEqual(len(wl), 12)
        for r in wl:
            self.assertTrue(r['matches_lab'], r)
            self.assertEqual(r['fall_engine_passes_state3_to_conversion'], 55)
            self.assertEqual(r['converted_row_xy'], r['lab_conversion_xy'])

    def test_run_through_and_slow_entry(self):
        rt = O24['whole_game']['run_through_and_slow_entry']
        self.assertEqual(rt['run_right_from_300']['triggered_at_frame'], {})
        self.assertEqual(rt['start_inside_window_hold_right']['triggered_at_frame'], {'26': 5})
        self.assertEqual(rt['run_left_from_620']['triggered_at_frame'], {})

    def test_contact_outcomes_whole_game(self):
        v = O24['whole_game']['contact_outcomes']['variants']
        for name in ('ordinary_10_rings', 'rolling_state9_attack_bit1', 'jump_state0A_attack_bit1', 'above', 'side_right', 'side_left'):
            self.assertEqual(v[name]['hurt_frames'], [1], name)
            self.assertEqual((v[name]['rings_after'], v[name]['state_after']), (0, 30), name)
            self.assertEqual(v[name]['first_d3b0_frame'], 0, name)
        self.assertEqual(v['zero_rings']['state_after'], 31)
        for name in ('invincible_d532_6', 'blinking_bit7_d3b1_120', 'hurt_state_1E_bit6'):
            self.assertEqual(v[name]['hurt_frames'], [], name)
            self.assertEqual(v[name]['rings_after'], 10, name)
        self.assertEqual(v['invincible_d532_6']['first_d3b0_frame'], 0)
        self.assertEqual(v['blinking_bit7_d3b1_120']['first_d3b0_frame'], 0)
        self.assertIsNone(v['hurt_state_1E_bit6']['first_d3b0_frame'])
        for name in ('below', 'just_outside_below'):
            self.assertEqual(v[name]['hurt_frames'], [], name)
        # every model-disagreeing end-of-frame row is a held request or the dead player, never a missed contact
        for name, x in v.items():
            for f in x['rows_where_end_of_frame_d3b0_differs_from_model']:
                row = x['rows'][f]
                self.assertTrue(row[6] != 0 and row[11] == 0, (name, f))
        # the first frame of each hurting variant: the wrapper saw the fork object (slot 7) overlapping per the closed-interval model
        fork_slot = O24['whole_game']['contact_outcomes']['fork_object_row']['slot']
        for name in ('ordinary_10_rings', 'above', 'side_right', 'side_left'):
            seen = [o for o in v[name]['rows'][0][10] if o[0] == fork_slot]
            self.assertTrue(seen and seen[0][3] == 1, name)

    def test_lifecycle_whole_game(self):
        lf = O24['whole_game']['lifecycle_mghz1']
        self.assertEqual(lf['window']['object_minus_camera_x'], {'created_range': [-96, 348], 'awake_range': [-32, 284]})
        wr = lf['walk_right']['transitions_[frame,object_minus_camera_x,player_x]']
        self.assertEqual(sorted(wr), ['None->asleep', 'asleep->None', 'asleep->awake', 'awake->asleep'])
        self.assertEqual(wr['None->asleep'][0][1], 347)
        self.assertEqual(wr['asleep->awake'][0][1], 283)
        self.assertEqual(wr['awake->asleep'][0][1], -33)
        self.assertLessEqual(wr['asleep->None'][0][1], -97)
        b = lf['leave_before_trigger']
        self.assertFalse(b['A_present_after_leaving'])
        self.assertEqual(b['occupancy_A_after_leaving'], 0)
        self.assertEqual(b['A_row_after_return_[state,x,y,flags_04]'], [1, 456, 112, 0])
        m = lf['leave_mid_fall']
        self.assertFalse(m['A_present_after_leaving'])
        self.assertEqual(m['score_after_leaving'], '000000')
        self.assertEqual(m['A_row_after_return_[state,x,y,flags_04,req]'], [1, 456, 112, 0, 1])
        z = lf['asleep_mid_fall']
        rows = z['rows_[x,y,vy,flags_04,frame_idx]_over_12_frames']
        self.assertEqual(len({tuple(r[:3]) for r in rows}), 1)
        self.assertTrue(all(r[3] == 0x40 for r in rows))
        self.assertGreater(len({r[4] for r in rows}), 1)
        self.assertEqual(z['after_returning_[x,y,vy,flags_04,frame_idx]'][0][3], 0)
        self.assertGreater(z['after_returning_[x,y,vy,flags_04,frame_idx]'][1][2], rows[0][2])
        d = lf['leave_after_landing']
        self.assertEqual((d['A_recreated_after_backtrack'], d['B_recreated_after_backtrack']), (False, True))
        self.assertEqual((d['occupancy_A_after_return'], d['occupancy_A_after_landing']), ('0x24', '0x24'))

    def test_replacement_0f(self):
        r = O24['replacement_effect_0F']
        self.assertEqual(r['score_added_bcd_bytes'], '10 00 00')
        self.assertEqual(r['whole_game_lifetime_frames_from_conversion_to_slot_clear'], 41)
        self.assertEqual(r['vram_tiles_36_to_45_sha256']['mghz1_act_vram'], r['vram_tiles_36_to_45_sha256']['thz1_act_vram'])
        self.assertEqual(r['state_table']['frames_used'], [0, 7, 8, 9])


class Object2eCache(unittest.TestCase):
    def test_strip_rule(self):
        for act, (lo, hi) in (('mghz1', (1353, 1656)), ('mghz2', (233, 664))):
            s = O2E['strip_trigger'][act]
            self.assertEqual(s['x_that_fire'], [lo, hi])
            self.assertEqual(s['x_count'], hi - lo + 1)
            self.assertEqual(s['y_that_fire_dy'], [-2, 2])
            self.assertEqual(s['y_count'], 5)
            self.assertTrue(all(s['player_variants_fire_at_mid_strip'].values()))
            self.assertEqual(s['after_init_callback']['flags_04'], '0x42')
            self.assertEqual(s['after_init_callback']['range_end_34_35'], hi)

    def test_children_model_and_lifetime(self):
        cases = O2E['splash_burst_controlled']['mghz1']['cases']
        for face, sign in ((0, -1), (1, 1)):
            c = cases[f'face_bit4={face}']
            self.assertEqual(c['model_matches_lab'], {'1': True, '2': True, '3': True})
            for prm, vx in (('1', 176), ('2', 192), ('3', 208)):
                rows = c['child_rows_first_16'][prm]
                self.assertEqual(rows[0][7], sign * vx)
                self.assertEqual(rows[0][8], -256)
                self.assertEqual(rows[0][2], 0)
                self.assertEqual([r[4] for r in rows[:13]][:1], [0])
                life = c['child_lifetimes'][prm]
                self.assertEqual((life['passes_as_type_2E'], life['marked_FE_rel'], life['marked_FF_rel'], life['slot_zeroed_rel']), (13, 13, 14, 15))
        first = cases['face_bit4=0']['child_rows_first_16']
        self.assertEqual([(first[p][0][5], first[p][0][6]) for p in '123'], [(1396, 780), (1392, 778), (1388, 776)])
        self.assertEqual(cases['face_bit4=0']['child_rows_last_3']['1'][0][5:7], [1387, 772])

    def test_cadence_and_pool(self):
        c = O2E['retrigger_cadence']
        self.assertEqual(c['periods'], [5])
        self.assertEqual(c['spawn_passes'][:3], [5, 10, 15])
        self.assertEqual({k: v['children_parameters_created'] for k, v in O2E['slot_pool_exhaustion'].items()},
                         {'0': [], '1': [1], '2': [1, 2], '3': [1, 2, 3], '10': [1, 2, 3]})

    def test_whole_game_walk_ins(self):
        w1 = O2E['whole_game']['mghz1_walk_in_from_left_rim']
        self.assertEqual(w1['parent_first_seen_frame'], 2)
        self.assertGreaterEqual(w1['spawn_pass_count'], 5)
        self.assertEqual(w1['parent_state_changes'][0][:4], [2, 'parent_state', None, 0])
        self.assertEqual(w1['parent_state_changes'][2][:4], [64, 'parent_state', 1, 2])
        self.assertTrue(w1['children_in_a_slot_below_the_parent_get_their_first_update_one_frame_late_[frame,slot,param]'])
        w2 = O2E['whole_game']['mghz2_walk_in_from_left_rim']
        self.assertGreaterEqual(w2['spawn_pass_count'], 3)
        self.assertTrue(w2['children_in_a_slot_below_the_parent_get_their_first_update_one_frame_late_[frame,slot,param]'])
        left = O2E['whole_game']['facing_left_burst']
        self.assertTrue(left['all_child_vx_positive'])
        self.assertEqual(left['player_face_bit4_values'], [1])

    def test_persistence_keep_alive(self):
        p = O2E['whole_game']['persistence']
        self.assertEqual(p['near_left_end']['flags_04'], '0x02')
        self.assertTrue(p['after_leaving_1400px_right']['parent_present'])
        self.assertEqual(p['after_leaving_1400px_right']['flags_04'], '0x42')
        self.assertFalse(p['fresh_load_far_right']['parent_present'])
        self.assertFalse(p['fresh_load_inside_strip_right_end']['parent_present'])

    def test_no_contact(self):
        n = O2E['whole_game']['no_contact']
        self.assertGreater(n['frames_with_geometric_overlap_of_a_2E_box_and_sonic'], 100)
        self.assertFalse(n['any_helper_hit_with_a_2E_slot'])
        self.assertEqual(n['frames_with_d3b0_or_d520_set'], [])
        self.assertNotIn(0x2E, n['contact_helper_hits_by_slot_type_decimal'])


class ArtAndChecklist(unittest.TestCase):
    def test_runtime_art_matches_approved_board(self):
        for key in ('runtime_check_0x24', 'runtime_check_0x2E'):
            a = D['art'][key]
            self.assertEqual(a['unapproved_compositions'], [])
            self.assertEqual(a['missed'], 0)
            self.assertEqual(a['palette_frames_checked'], a['palette_frames_equal_to_approved_row'])
            for k, v in a['per_type_frame'].items():
                self.assertEqual(v['seen'], v['hash_matches_approved'], k)
        self.assertEqual(sorted(D['art']['runtime_check_0x24']['per_type_frame']), ['24:1', '24:2', '24:3'])
        self.assertEqual(sorted(D['art']['runtime_check_0x2E']['per_type_frame']), ['2E:1', '2E:2', '2E:3', '2E:4'])
        self.assertFalse(D['art']['new_visual_approval_required'])

    def test_classification_vocabulary(self):
        names = {c['class'].split('(')[0].strip() for c in D['lifecycle']['classification']}
        self.assertTrue(names <= {'WORLD', 'EDGE', 'PLAYER_DIST', 'CENTER', 'LOCKED_CAMERA', 'WORLD '})
        self.assertTrue(any('REQUIRED DECISION' in c['adapter'] for c in D['lifecycle']['classification']))

    def test_fixture_index(self):
        idx = {f['name']: f for f in D['poc_fixture_index']}
        self.assertEqual(len(idx), 10)
        self.assertTrue(idx['all_12_landings']['headline']['all_match_controlled_lab'])
        self.assertTrue(idx['mghz1_pair_26_27_stand_beside_left_piece']['headline']['right_piece_untouched'])
        self.assertTrue(idx['mghz1_pair_26_27_stand_between']['headline']['both_trigger_same_frame'])
        self.assertTrue(idx['mghz1_pair_26_27_stand_beside_right_piece']['headline']['only_right_piece_triggers'])
        self.assertEqual(idx['lifecycle_leave_and_return']['headline'], {'before_trigger_recreated': True, 'mid_fall_recreated_fresh': True, 'after_landing_recreated': False})
        for f in idx.values():
            node = D
            for part in f['path'].split('.'):
                node = node[part]

    def test_deliverables_present(self):
        self.assertGreaterEqual(len(D['poc_checklist']), 10)
        self.assertGreaterEqual(len(D['agents_candidate_updates']), 5)
        self.assertEqual(len(D['corrections_to_object_census']), 5)
        self.assertTrue((ROOT / 'docs/mghz-object-24-2e-audit.md').is_file())
        self.assertIn('4149f84', (ROOT / 'docs/mghz-object-24-2e-audit.md').read_text(encoding='utf-8'))


@needs_rom
class RomBackedReexecution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM
        scan = T.scan_all_zones(ROM)
        cls.rows = T.placement_rows(ROM, scan)
        cls.r24 = T.mghz_rows(cls.rows, 0x24)
        cls.r2e = T.mghz_rows(cls.rows, 0x2E)

    def test_placement_rows_equal_cache(self):
        self.assertEqual(json.loads(json.dumps(self.rows)), D['placements']['records'])

    def test_static_part_equals_cache(self):
        fresh = json.loads(json.dumps(T.build(ROM, static_only=True)))
        for k in ('identity', 'placements', 'creators', 'static', 'creator_init', 'corrections_to_object_census', 'extent_resolution_2E'):
            self.assertEqual(fresh[k], D[k], k)

    def test_trigger_boundaries_against_original_routine(self):
        lab = T.Lab(ROM, 'mghz1', self.r24[0]['raw_bytes'], player=(60000, 0), flags4=0)
        for dx, vx, want in ((47, 255, True), (48, 0, False), (-47, -255, True), (-48, 0, False), (0, 256, False), (0, -256, False), (0, 255, True), (0, -0x8000, False)):
            lab.reset()
            lab.player(lab.ox + dx, lab.oy + 30, vx=vx)
            lab.update()
            self.assertEqual(lab.m[T.SLOT + 2] == 2, want, (dx, vx))
        lab.reset()
        lab.m[T.SLOT + 4] = 0x40
        lab.player(lab.ox, lab.oy + 30)
        lab.update()
        self.assertEqual(lab.m[T.SLOT + 2], 1)

    def test_contact_wrapper_against_closed_interval_model(self):
        lab = T.Lab(ROM, 'mghz1', self.r24[0]['raw_bytes'], player=(60000, 0), flags4=0)
        for dx in range(-15, 16):
            for dy in range(-14, 28):
                for pex in (8, 9):
                    got = T.contact_call(lab, dx, dy, pex=pex)[0] != 0
                    self.assertEqual(got, T.overlap_model(dx, dy, 4, 11, pex, 24), (dx, dy, pex))

    def test_landing_table_equals_cache(self):
        self.assertEqual(json.loads(json.dumps(T.landing_table(ROM, self.r24))), O24['landing_table_controlled'])

    def test_model_fall_independent_of_lab(self):
        for r in self.r24:
            m = T.model_fall(ROM, r['act'], r['world_x'], r['world_y'], int(r['parameter'], 16))
            self.assertEqual(m['fall_updates'], 56)
            self.assertEqual((m['x'], m['y']), (r['world_x'] + (28 if r['parameter'] == '0x00' else -28), r['world_y'] + 96))

    def test_strip_and_children_equal_cache(self):
        for r in self.r2e:
            self.assertEqual(json.loads(json.dumps(T.strip_trigger_sweep(ROM, r))), O2E['strip_trigger'][r['act']])
        got = T.splash_summary(ROM, self.r2e[0])
        self.assertEqual(json.loads(json.dumps(got)), O2E['splash_burst_controlled']['mghz1'])

    def test_child_model_is_independent_translation(self):
        rows = T.child_model(1392, 780, 0, 1, 780)
        self.assertEqual(rows[0][1:3], [1396, 780])
        self.assertEqual(rows[12][1:3], [1387, 772])

    def test_whole_game_pair_fixture_equals_cache(self):
        g = T.Game(ROM, 'mghz1')
        got = T.pair_fixture(g, self.r24[0], self.r24[1])
        self.assertEqual(json.loads(json.dumps(got)), O24['whole_game']['pair_fixture_mghz1_index26_27'])

    def test_full_cache_regenerates(self):
        self.assertEqual(T.dumps(T.build(ROM)), T.OUTPUT.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
