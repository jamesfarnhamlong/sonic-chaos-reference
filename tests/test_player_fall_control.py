"""Shared player fall / control audit: cache locks plus ROM-backed re-execution of the original routines.

Cache classes run without a ROM.  ROM classes need the verified ROM (SONIC_CHAOS_ROM or ../source/Sonic Chaos (Europe).sms) and skip otherwise.
Never touches POC.
"""
import hashlib
import json
import os
import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import player_fall_control as T
import level_package as L

ROM_SHA = 'eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607'
D = json.loads(T.OUTPUT.read_text(encoding='utf-8'))
A, B, C = D['part_a_state_14'], D['part_b_monitor_wall'], D['part_c_fall_support']
SCEN = A['strip_scenarios']['scenarios']
GPZ = A['gpz2_strip_scenarios']['scenarios']


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


def calls(row):
    return row['calls']


class CacheIdentity(unittest.TestCase):
    def test_identity_and_scope(self):
        self.assertEqual(D['rom_sha256'], ROM_SHA)
        self.assertFalse(D['static_only'])
        self.assertIn('Research only', D['scope'])
        self.assertIn('UNRESOLVED', D['evidence_classes'])

    def test_classification_is_complete_and_labelled(self):
        ids = [c['id'] for c in D['classification']]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual({c['class'] for c in D['classification']}, {'CANONICAL', 'POC DIVERGENCE', 'EXPLICIT ADAPTER CANDIDATE', 'UNRESOLVED'})
        by = {c['id']: c['class'] for c in D['classification']}
        for k in ('A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'B1', 'B3', 'B5', 'B6', 'B8', 'C1', 'C2', 'C3', 'C4'):
            self.assertEqual(by[k], 'CANONICAL', k)
        for k in ('B2', 'B4'):
            self.assertEqual(by[k], 'POC DIVERGENCE', k)
        self.assertEqual(by['B7'], 'EXPLICIT ADAPTER CANDIDATE')
        self.assertEqual(by['D1'], 'EXPLICIT ADAPTER CANDIDATE')
        self.assertEqual({k for k, v in by.items() if v == 'UNRESOLVED'}, {'A10', 'C5'})
        self.assertEqual(len(D['agents_candidates']), 5)

    def test_poc_facts_are_read_only_references(self):
        self.assertEqual(len(D['poc_source_read_only']['files']), 3)
        self.assertIn('not projected', D['poc_source_read_only']['facts'][0])


class StaticTables(unittest.TestCase):
    t = A['input_tables']

    def test_state_14_has_no_input_or_friction_at_all(self):
        row = self.t['states']['0x14']
        for name in ('dry_vx_nonneg', 'dry_vx_neg', 'friction', 'water_vx_nonneg', 'water_vx_neg'):
            self.assertEqual(row[name], [0, 0], name)

    def test_state_0e_has_control_and_friction(self):
        row = self.t['states']['0x0E']
        self.assertEqual((row['dry_vx_nonneg'], row['dry_vx_neg'], row['friction'], row['water_vx_nonneg']), ([-16, 16], [-16, 16], [16, -16], [-4, 4]))

    def test_zero_lists(self):
        self.assertEqual(self.t['states_with_zero_input_acceleration'], ['0x00', '0x01', '0x02', '0x03', '0x04', '0x0C', '0x0D', '0x0F', '0x13', '0x14', '0x15', '0x17', '0x19', '0x1D'])
        self.assertIn('0x14', self.t['states_with_all_tables_zero'])
        self.assertNotIn('0x0E', self.t['states_with_all_tables_zero'])
        self.assertEqual(self.t['surface_delta_first_word'], 0)

    def test_no_other_fixed_bank_state_14_comparison_besides_callback_and_gate(self):
        roles = {s['cpu']: s['role'] for s in A['cp14_sites']}
        self.assertIn('callback', roles['0x3A4E'])
        self.assertIn('one-way', roles['0x6FC4'])
        self.assertIn('SURFACE TYPE $14', roles['0x7402'])
        self.assertIn('SURFACE TYPE $14', roles['0x7569'])
        self.assertEqual({s['cpu'] for s in A['cp14_sites'] if 'bank' not in s}, {'0x3A4E', '0x6FC4', '0x7402', '0x7569'})

    def test_single_entry(self):
        w = A['writers']
        self.assertEqual([c['cpu'] for c in w['callers_of_4663']], ['0x37C3'])
        self.assertEqual([s['cpu'] for s in w['ld_ix_plus2_14_sites']], ['0x4663', '0x9FCD', '0xAAF4'])


class SweepsAndFixtures(unittest.TestCase):
    def test_horizontal_and_vertical_sweeps(self):
        h, v = A['horizontal_sweep'], A['vertical_sweep']
        self.assertEqual((h['cases'], h['mismatches_vs_model'], h['state14_nonzero_input_delta_cases']), (5296, 0, 0))
        self.assertEqual((v['cases'], v['mismatches_vs_model']), (1400, 0))

    def test_state_14_air_fixtures(self):
        fx = A['air_fixtures']['cases']
        for name in ('hold_right', 'hold_left', 'neutral', 'alternate_8_updates'):
            rows = fx[f'0x14_vx256_{name}']
            self.assertEqual({r['vx'] for r in rows}, {256}, name)
            self.assertEqual({r['d375'] for r in rows}, {0})
            self.assertEqual([r['x'] for r in rows[:5]], [3400, 3401, 3402, 3403, 3404])
        rows = fx['0x14_vx-1024_hold_right']
        self.assertEqual({r['vx'] for r in rows}, {-1024})
        self.assertEqual({r['vx'] for r in fx['0x14_vx1024_hold_left']}, {1024})
        self.assertEqual({r['vx'] for r in fx['0x14_vx0_hold_right']}, {0})

    def test_ordinary_fall_0e_does_have_control_and_friction(self):
        fx = A['air_fixtures']['cases']
        self.assertEqual([r['vx'] for r in fx['0x0E_vx256_hold_right'][:5]], [256, 272, 288, 304, 320])
        self.assertEqual([r['vx'] for r in fx['0x0E_vx256_hold_left'][:5]], [256, 240, 224, 208, 192])
        self.assertEqual([r['vx'] for r in fx['0x0E_vx256_neutral'][:5]], [256, 240, 224, 208, 192])
        rows = fx['0x0E_vx0_hold_right']
        self.assertEqual([r['vx'] for r in rows[:3]], [0, 32, 64])            # the increment is doubled while |vx|+$80 < $100
        self.assertEqual(rows[-1]['vx'], 320)

    def test_gravity_is_identical_for_both_states(self):
        fx = A['air_fixtures']['cases']
        for name in ('hold_right', 'neutral'):
            self.assertEqual([(r['y'], r['vy']) for r in fx[f'0x14_vx256_{name}']], [(r['y'], r['vy']) for r in fx[f'0x0E_vx256_{name}']])
        self.assertEqual(fx['0x14_vx256_neutral'][0]['vy'], 256)
        self.assertEqual(fx['0x14_vx256_neutral'][1]['vy'], 304)

    def test_edge_clamp_applies_to_both_states(self):
        rows = {(r['state'], r['screen_x_before']): r for r in A['edge_clamp']['rows']}
        for st in ('0x14', '0x0E'):
            self.assertEqual((rows[(st, 8)]['screen_x_after'], rows[(st, 8)]['vx_after']), (18, 0))
            self.assertEqual((rows[(st, 12)]['screen_x_after'], rows[(st, 12)]['vx_after']), (18, 0))
            self.assertEqual((rows[(st, 248)]['screen_x_after'], rows[(st, 248)]['vx_after']), (245, 0))
            self.assertNotEqual(rows[(st, 240)]['vx_after'], 0)

    def test_setter_facts(self):
        s = A['setter_diff']
        self.assertEqual(s['cases'], 240)
        self.assertIn('p24', s['summary']['0x463C']['fields_ever_changed'])
        self.assertNotIn('p24', s['summary']['0x4663']['fields_ever_changed'])
        pair = s['marker_difference_cases']
        self.assertEqual(pair[0]['changed']['p24'], [1, 0])
        self.assertNotIn('p24', pair[1]['changed'])
        self.assertEqual((pair[0]['changed']['req'], pair[1]['changed']['req']), ([5, 14], [5, 20]))
        self.assertEqual(pair[1]['changed']['vy'], [-1024, 256])

    def test_marker_matrix(self):
        m = A['surface_marker_matrix']
        self.assertEqual((m['types_that_set_bit0'], m['types_that_clear_bit0'], m['types_tested']), (['0x19'], ['0x00'], 26))
        self.assertEqual(m['after_by_type_and_before']['0x19'], {'0': 1, '1': 1, '2': 3, '3': 3})
        self.assertEqual(m['after_by_type_and_before']['0x00'], {'0': 0, '1': 0, '2': 0, '3': 0})
        self.assertEqual(m['after_by_type_and_before']['0x1B'], {'0': 2, '1': 3, '2': 2, '3': 3})
        self.assertEqual(m['after_by_type_and_before']['0x01'], {'0': 0, '1': 1, '2': 2, '3': 3})

    def test_one_way_gate_only_binds_requested_14_and_marker_on_one_way_blocks(self):
        g = A['one_way_gate_matrix']['blocks']
        self.assertEqual(g['one_way_0D']['states_whose_projection_differs_with_marker_set'], ['0x14'])
        self.assertEqual(g['strip_85']['states_whose_projection_differs_with_marker_set'], ['0x14'])
        self.assertEqual(g['solid_01']['states_whose_projection_differs_with_marker_set'], [])
        self.assertEqual(g['deck_8C']['states_whose_projection_differs_with_marker_set'], [])
        self.assertEqual(g['strip_85']['y_delta_marker_set']['0x14'], 0)
        self.assertEqual(g['strip_85']['y_delta_marker_clear']['0x14'], -3)

    def test_exits(self):
        c = A['exit_fixtures']['cases']
        for st in ('0x14', '0x0E'):
            self.assertEqual((c[f'landing_on_solid_{st}']['req'], c[f'landing_on_solid_{st}']['f3'], c[f'landing_on_solid_{st}']['f22']), (5, 0, 2))
            self.assertEqual((c[f'damage_request_{st}_with_rings']['req'], c[f'damage_request_{st}_with_rings']['vy'], c[f'damage_request_{st}_with_rings']['vx'], c[f'damage_request_{st}_with_rings']['f3']), (0x1E, -1024, -256, 0xC1))
            self.assertEqual((c[f'damage_request_{st}_no_rings']['req'], c[f'damage_request_{st}_no_rings']['vy']), (0x1F, -1280))
            self.assertEqual(c[f'screen_y_death_{st}']['req'], 0x1F)
            self.assertEqual(c[f'screen_y_just_above_death_{st}']['req'], int(st, 16))
            self.assertEqual(c[f'jump_press_{st}']['req'], int(st, 16))
        self.assertEqual({k: v['request_0B_update'] for k, v in A['spring_exit']['cases'].items()}, {'0x14': 27, '0x0E': 27})

    def test_strip_census(self):
        c = A['strip_census']
        self.assertEqual((c['run_count'], c['acts_with_strips']), (13, ['gpz1', 'gpz2', 'mghz1', 'mghz2', 'mghz3']))
        low = [r for r in c['runs']['mghz1'] if r['row'] == 27][0]
        self.assertEqual((low['cells_x'], low['first_cell_below_by_class']), ([95, 109], {'level_bottom': 15}))


class WholeGameStrips(unittest.TestCase):
    def test_walkoff_enters_14_at_once_and_holds_speed(self):
        for nm, vxs in (('right', [0, 272]), ('left', [240]), ('neutral', [236])):
            m = SCEN[f'upper_strip_walkoff_{nm}']['milestones']
            self.assertEqual((m['first_request_14_update'], m['first_current_14_update']), (1, 1), nm)
            self.assertEqual(m['vx_values_while_14_after_first'], vxs, nm)
            self.assertEqual(m['input_delta_values_while_14'], [0], nm)

    def test_second_strip_is_passed_through_and_the_pit_kills(self):
        m = SCEN['upper_strip_walkoff_right']['milestones']
        self.assertEqual(m['foot_surface_19_update_runs'], [[1, 14], [83, 87]])
        self.assertEqual(m['marker_changes_u_value'], [[1, 1], [15, 0], [83, 1], [88, 0]])
        self.assertEqual((m['state_14_updates'], m['death_request_update'], m['death_request_y'], m['camera_y_at_death']), (104, 104, 987, 777))
        for nm in ('left', 'neutral'):
            mm = SCEN[f'upper_strip_walkoff_{nm}']['milestones']
            self.assertEqual((mm['foot_surface_19_update_runs'], mm['death_request_update']), ([[1, 14], [83, 87]], 104))

    def test_ordinary_fall_lands_on_the_strip_then_hops_into_14(self):
        n = SCEN['ordinary_fall_onto_lower_strip_neutral']['milestones']
        self.assertEqual((n['first_request_14_update'], n['foot_surface_19_update_runs'], n['death_request_update']), (72, [[70, 85]], 107))
        tr = {t['u']: t for t in SCEN['ordinary_fall_onto_lower_strip_neutral']['transitions']}
        self.assertEqual((tr[71]['cur'], tr[71]['req'], tr[71]['f22'], tr[71]['y']), (14, 5, 2, 846))
        self.assertEqual((tr[72]['cur'], tr[72]['req'], tr[72]['p24']), (5, 20, 1))
        r = SCEN['ordinary_fall_onto_lower_strip_right']['milestones']
        self.assertEqual(r['first_request_14_update'], 83)            # full speed 4.0 crosses the strip until the wall
        self.assertEqual(SCEN['ordinary_fall_over_lower_strip_with_marker_set']['milestones']['first_request_14_update'], 72)

    def test_injected_14_passes_through_the_strip(self):
        m = SCEN['special_fall_injected_over_lower_strip']['milestones']
        self.assertEqual((m['foot_surface_19_update_runs'], m['vx_values_while_14_after_first'], m['death_request_update']), ([[70, 74]], [256], 91))

    def test_gpz2_route(self):
        for nm in ('right', 'left', 'neutral'):
            m = GPZ[f'strip_walkoff_{nm}']['milestones']
            self.assertEqual((m['first_request_14_update'], m['landing_row']['y'], m['landing_row']['cur'], m['landing_row']['req']), (1, 878, 5, 5))
        fast = GPZ['strip_fast_run_right']['milestones']
        self.assertEqual((fast['first_request_14_update'], fast['state_14_updates']), (None, 0))

    def test_pass_trace(self):
        u = A['pass_trace']['updates']
        self.assertEqual([c for c in calls(u['0x14']['mid_air']) if c != 'callback_strip_fall_14'], [c for c in calls(u['0x0E']['mid_air']) if c != 'callback_fall_0E'])
        for need in ('terrain_floor', 'terrain_sides', 'terrain_ceiling', 'terrain_rings', 'damage_gate_48BC', 'input_tables', 'x_integration', 'y_integration'):
            self.assertIn(need, calls(u['0x14']['mid_air']))
        by = calls(u['0x14']['update_after_first_strip_sample'])
        sup = calls(u['0x0E']['update_after_first_strip_sample'])
        self.assertEqual(by[by.index('one_way_gate_6FBB') + 1], 'surface19_6B23')           # no projection merge: bypassed
        self.assertEqual(sup[sup.index('one_way_gate_6FBB') + 1], 'merge_64CB')            # projection ran
        self.assertIn('landing_45CE', sup)
        self.assertIn('landing_45CE', calls(u['landing_from_14_on_solid_floor_GPZ2']))
        self.assertIn('solid_projection_6F6D', calls(u['landing_from_14_on_solid_floor_GPZ2']))

    def test_marker_lifetime(self):
        ml = A['marker_lifetime']
        w = ml['marker_cleared_by_walk_or_run_frame_selector_on_a_non_19_surface']
        self.assertEqual([r['p24'] for r in w['walk_on_ordinary_floor_marker_set']['rows']][:2], [0, 0])
        self.assertEqual([r['p24'] for r in w['run_on_ordinary_floor_marker_set']['rows']][:2], [0, 0])
        self.assertEqual({r['p24'] for r in w['idle_on_ordinary_floor_marker_set']['rows']}, {1})
        j = ml['jump_from_strip_clears_marker_and_landing_sets_it_again']['run_+4.0_on_strip_then_jump']['transitions']
        self.assertTrue(any(t['cur'] == 6 and t['req'] == 10 and t['p24'] == 0 for t in j))
        self.assertTrue(any(t['cur'] == 10 and t['p24'] == 1 for t in j))


class MonitorWall(unittest.TestCase):
    def test_guard_matrix(self):
        rows = B['solid_guard_matrix']['rows']
        get = lambda cl, bit, cam: next(r for r in rows if r['classification'] == cl and r['d523_bit_already_set'] == bit and r['camera_case'].startswith(cam))
        for cl in ('above', 'below', 'right', 'left'):
            self.assertTrue(any(get(cl, False, c)['x_moved'] or get(cl, False, c)['y_moved'] for c in ('normal', 'right of', 'at or left')), cl)
            for cam in ('normal', 'right of', 'at or left'):
                r = get(cl, True, cam)
                self.assertFalse(r['x_moved'] or r['y_moved'], (cl, cam))
        self.assertEqual((get('right', False, 'normal')['new_x'], get('right', False, 'right of')['x_moved'], get('right', False, 'at or left')['x_moved']), (3003, False, True))
        self.assertEqual((get('left', False, 'normal')['new_x'], get('left', False, 'right of')['x_moved'], get('left', False, 'at or left')['x_moved']), (2997, True, False))
        self.assertEqual(get('above', False, 'normal')['new_y'], 496)

    def test_natural_arrivals_stand_on_the_monitor_top(self):
        n = B['natural_monitor_falls']
        for nm in ('right', 'neutral'):
            r = n[f'poc_route_from_upper_strip_{nm}']
            self.assertTrue(r['standing_on_monitor_top'], nm)
            self.assertEqual((r['final_rows'][-1]['x'], r['final_rows'][-1]['y'], r['final_rows'][-1]['f23']), (3575, 790, 6))
            self.assertEqual((r['rows_with_both_wall_flags'], r['max_x']), (0, 3575))
        self.assertFalse(n['poc_route_from_upper_strip_left']['standing_on_monitor_top'])

    def test_natural_sweep_never_enters_the_snag(self):
        s = B['natural_fall_sweep']
        self.assertEqual((s['cases'], s['cases_with_both_wall_flags_f23_bits_2_and_3'], s['cases_with_player_x_ge_3584']), (120, 0, 0))
        self.assertEqual((s['outcome_counts']['standing_on_monitor_top'], s['outcome_counts']['x_oscillation_cases']), (63, 0))

    def test_wedge_fixture_order_and_flags(self):
        c = B['wedge_fixtures']['cases']['synthetic_push_into_wall_then_terrain_return']
        rows = {r['u']: r for r in c['rows']}
        self.assertEqual(rows[6]['monitor_5FA0'], [{'player_before_push': [3572, 812], 'd523_at_call': 0, 'classification': 4}])
        self.assertEqual((rows[6]['x'], rows[6]['f21']), (3586, 128))          # pushed INTO the wall (monitorX + 18), mirrored nibble written
        self.assertEqual((rows[7]['x'], rows[7]['f22'], rows[7]['f23']), (3575, 4, 12))   # terrain pushes back; terrain right + mirrored left merge
        self.assertEqual(rows[7]['monitor_5FA0'][0]['d523_at_call'], 12)       # guard bit set -> no second push
        self.assertEqual((rows[8]['vx'], rows[8]['d375']), (0, 0))             # $402A blocked branch zeroes vx and the input delta
        self.assertEqual(rows[6]['order'][-1], 'solid_object_5FA0')            # the monitor runs AFTER the player's terrain pass
        self.assertLess(rows[6]['order'].index('terrain_sides'), rows[6]['order'].index('solid_object_5FA0'))
        self.assertEqual((c['x_max'], c['final']['x'], c['final']['y'], c['final']['f23']), (3586, 3575, 814, 14))
        self.assertEqual(c['first_update_with_both_wall_flags'], 7)
        self.assertEqual(B['wedge_fixtures']['cases']['synthetic_same_in_special_fall']['final'], c['final'])
        self.assertEqual(B['wedge_fixtures']['cases']['synthetic_guard_skips_push']['x_max'], 3575)
        self.assertTrue(B['wedge_fixtures']['monitor']['slot_present'])

    def test_floor_line_push_pops_up_and_settles_on_the_monitor_top(self):
        c = B['wedge_fixtures']['cases']['synthetic_floor_line_push_pops_to_monitor_top']
        rows = {r['u']: r for r in c['rows']}
        self.assertEqual((rows[6]['x'], rows[6]['y'], rows[6]['monitor_5FA0'][0]['classification']), (3586, 814, 4))
        self.assertEqual((rows[7]['x'], rows[7]['y'], rows[7]['f22'], rows[7]['f23']), (3575, 782, 6, 14))      # floor projection reads the wall column: -32 px
        self.assertEqual((rows[9]['monitor_5FA0'][0]['classification'], rows[9]['f21']), (1, 32))               # top contact projects Y = 790
        self.assertEqual((c['final']['x'], c['final']['y'], c['final']['f23']), (3575, 790, 6))
        self.assertEqual({(r['x'], r['y']) for r in c['rows'][-3:]}, {(3575, 790)})

    def test_chamber_grid_always_settles(self):
        g = B['chamber_grid']['summary']
        self.assertEqual((g['cases'], g['pushed_into_wall_first_frame'], g['ended_stable'], g['ended_with_both_wall_flags']), (192, 30, 182, 10))
        # both fall states give the same outcome rows
        cells = B['chamber_grid']['cells']
        a = [c[1:] for c in cells if c[0] == '0x0E']
        b = [c[1:] for c in cells if c[0] == '0x14']
        self.assertEqual(a, b)
        for c in cells:                       # never persistently outside the wall column: every pushed case ends at the wall face
            if c[4]:
                self.assertEqual(c[6], 3575)


class FallSupport(unittest.TestCase):
    m = C['support_matrix']
    S = m['summary']

    def test_fall_states_acquire_one_way_deck_and_platform(self):
        for st in ('0x0A', '0x0B', '0x0E', '0x14', '0x1B', '0x1C', '0x11'):
            for surface in ('one_way_41', 'solid_control', 'deck_1C', 'platform_28'):
                self.assertIn(st, self.S[surface]['retained_support_states'], (st, surface))
        for surface in ('one_way_41', 'solid_control', 'deck_1C', 'platform_28'):
            self.assertIn('0x12', self.S[surface]['acquired_support_at_any_update_states'])
            self.assertNotIn('0x12', self.S[surface]['retained_support_states'])        # Spring Shoes relaunch

    def test_strip_is_never_acquired_by_14_and_not_kept_by_the_others(self):
        s = self.S['strip_19']
        self.assertIn('0x14', s['never_acquired_states'])
        for st in ('0x05', '0x06', '0x0A', '0x0B', '0x0E', '0x1C'):
            self.assertIn(st, s['acquired_but_not_retained_states'] if st != '0x06' else s['acquired_support_at_any_update_states'])
        self.assertEqual(s['retained_support_states'], ['0x00', '0x01', '0x02', '0x0C', '0x0D', '0x0F', '0x13', '0x19', '0x1B', '0x21'])

    def test_loop_and_act_clear_states_never_acquire_terrain_support(self):
        for st in ('0x16', '0x17', '0x18', '0x20', '0x23'):
            for surface in ('one_way_41', 'solid_control', 'deck_1C'):
                self.assertIn(st, self.S[surface]['never_acquired_states'])
        for st in ('0x0C', '0x0D', '0x13'):
            self.assertIn(st, self.S['solid_control']['never_acquired_states'])

    def test_marker_set_variants(self):
        v = self.m['marker_set_variants_SYNTHETIC']['per_surface']
        self.assertEqual({k: r['outcome'] for k, r in v['one_way_41'].items()}, {'0x0A': 'supported', '0x0E': 'supported', '0x14': 'not_supported', '0x0B': 'supported'})
        self.assertEqual({r['outcome'] for r in v['deck_1C'].values()}, {'supported'})

    def test_platform_support_for_14(self):
        r = self.m['per_state']['platform_28']['0x14']
        self.assertEqual((r['outcome'], r['owner_seen'], r['final_y']), ('supported', 9, 370))


@rom_only
class RomBackedControlled(unittest.TestCase):
    def test_tables_regenerate(self):
        self.assertEqual(T.input_tables(ROM), A['input_tables'])
        self.assertEqual(T.fixed_bank_cp14_sites(ROM), A['cp14_sites'])
        self.assertEqual(T.state14_writers(ROM), A['writers'])

    def test_horizontal_model_random_cases(self):
        air = T.Air(ROM)
        rng = random.Random(0x14)
        for _ in range(600):
            state, pad, water = rng.choice((0x0E, 0x14)), rng.choice((0, 4, 8, 12)), rng.choice((0, 1))
            vx = rng.randrange(-1500, 1501)
            r = air.update(state, pad=pad, vx=vx, water=water)
            self.assertEqual(r['vx'], T.model_x_update(ROM, state, pad, vx, water), (state, pad, water, vx))
            if state == 0x14:
                self.assertEqual(r['d375'], 0)
            vy = rng.randrange(-2200, 2200)
            self.assertEqual(air.update(state, vy=vy, water=water)['vy'], T.model_y_update(vy, water))

    def test_air_fixtures_regenerate(self):
        self.assertEqual(T.air_fixtures(ROM), A['air_fixtures'])

    def test_setters_and_markers_regenerate(self):
        self.assertEqual(T.setter_diff(ROM), A['setter_diff'])
        self.assertEqual(T.surface_marker_matrix(ROM), A['surface_marker_matrix'])
        self.assertEqual(T.one_way_gate_matrix(ROM), A['one_way_gate_matrix'])
        self.assertEqual(T.exit_fixtures(ROM), A['exit_fixtures'])
        self.assertEqual(T.edge_clamp_fixture(ROM), A['edge_clamp'])
        self.assertEqual(T.strip_census(ROM), A['strip_census'])

    def test_guard_matrix_regenerates(self):
        self.assertEqual(T.solid_guard_matrix(ROM), B['solid_guard_matrix'])

    def test_region_hashes(self):
        self.assertEqual(T.region_hashes(ROM), D['regions'])


@rom_only
class RomBackedWholeGame(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mg = T.Lab(ROM, 'mghz', 0)

    def test_strip_scenarios_regenerate(self):
        self.assertEqual(T.strip_scenarios(ROM), A['strip_scenarios'])

    def test_monitor_fixtures_regenerate(self):
        self.assertEqual(T.natural_monitor_falls(ROM, self.mg), B['natural_monitor_falls'])
        self.assertEqual(T.wedge_fixtures(ROM, self.mg), B['wedge_fixtures'])
        self.assertEqual(T.monitor_chamber_grid(ROM, self.mg), B['chamber_grid'])

    def test_spring_pass_trace_marker_regenerate(self):
        self.assertEqual(T.spring_exit_fixture(ROM), A['spring_exit'])
        self.assertEqual(T.pass_trace(ROM), A['pass_trace'])
        self.assertEqual(T.marker_lifetime(ROM), A['marker_lifetime'])

    def test_support_matrix_spot_checks(self):
        labs = {'mghz1': self.mg, 'gpz2': T.Lab(ROM, 'gpz', 1)}
        for surface in ('one_way_41', 'strip_19', 'deck_1C', 'platform_28'):
            lab = labs[T.SUPPORT_SURFACES[surface][0]]
            for st in (0x0E, 0x14, 0x0B):
                self.assertEqual(T.support_run(lab, surface, st), C['support_matrix']['per_state'][surface][f'0x{st:02X}'], (surface, st))


if __name__ == '__main__':
    unittest.main()
