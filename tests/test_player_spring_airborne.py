"""Shared player spring / airborne state closure: cache locks plus ROM-backed re-execution of the original routines.

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
import player_spring_airborne as T
import level_package as L

ROM_SHA = 'eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607'
D = json.loads(T.OUTPUT.read_text(encoding='utf-8'))
COL = {name: i for i, name in enumerate(T.COLUMNS)}


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


def scenario(group, sid):
    return next(s for s in D[group]['scenarios'] if s['id'] == sid)


def segs(sc, state):
    return [s for s in sc['state_segments'] if s['state'] == state]


def col(sc, name):
    return [r[COL[name]] for r in sc['rows']]


def frames_of(seg):
    return [(f['frame'], f['updates']) for f in seg['frames']]


class CacheIdentity(unittest.TestCase):
    def test_identity_and_scope(self):
        self.assertEqual(D['rom_sha256'], ROM_SHA)
        self.assertFalse(D['static_only'])
        self.assertTrue(D['research_only'])
        self.assertTrue(D['poc_untouched'])
        self.assertIn('UNRESOLVED', D['evidence_classes'])

    def test_no_rom_bytes_or_pixels_in_cache(self):
        text = T.OUTPUT.read_text(encoding='utf-8')
        self.assertNotIn('"raw"', text)
        self.assertNotIn('"rgba"', text)


class ScriptDecode(unittest.TestCase):
    def test_state_0B_both_branches(self):
        s = D['state_scripts']['0x0B']
        weak, strong = s['play_order_d448_bit0_clear'], s['play_order_d448_bit0_set']
        self.assertEqual(weak['cycle_updates'], 82)
        self.assertEqual([c['frame'] for c in weak['frame_cadence'][:6]], ['0x1C', '0x1D', '0x1E', '0x1F', '0x20', '0x21'])
        self.assertEqual({c['updates'] for c in weak['frame_cadence'][:12]}, {4})
        self.assertEqual([c['updates'] for c in weak['frame_cadence'][12:]], [4, 4, 6, 6, 6, 8])
        self.assertEqual(strong['frame_cadence'], [{'frame': '0x61', 'updates': 4}])
        # the FF 08 condition routine is the only $D448 reader
        self.assertEqual(s['program'][0]['condition_routine'], '0x818F')
        self.assertEqual(s['program'][0]['target_if_carry'], '0x8189')

    def test_other_states(self):
        sc = D['state_scripts']
        self.assertEqual(sc['0x1C']['play_order']['cycle_updates'], 48)
        self.assertEqual({c['updates'] for c in sc['0x1C']['play_order']['frame_cadence']}, {8})
        self.assertEqual({c['updates'] for c in sc['0x14']['play_order']['frame_cadence']}, {4})
        self.assertEqual([c['frame'] for c in sc['0x14']['play_order']['frame_cadence']], ['0x1C', '0x1D', '0x1E', '0x1F', '0x20', '0x21'])
        e = sc['0x0E']['play_order']
        self.assertEqual(e['cycle_updates'], 232)
        self.assertEqual({c['updates'] for c in e['frame_cadence']}, {8})
        self.assertEqual([c['frame'] for c in e['frame_cadence'][:7]], ['0x02', '0x03', '0x04', '0x05', '0x06', '0x01', '0x02'])
        self.assertEqual(len(e['frame_cadence']), 29)
        for st, sel, cb in (('0x09', '0x8F76', '0x03C5'), ('0x0A', '0x8F76', '0x03B3'), ('0x1B', '0x8F76', '0x03C8')):
            prog = sc[st]['program']
            self.assertEqual((prog[0]['selector'], prog[0]['callback']), (sel, cb), st)

    def test_callback_vectors_jump_to_the_wrappers(self):
        v = {x['vector']: x['jp_target'] for x in D['callback_vectors']}
        self.assertEqual(v['0x039E'], '0x393B')
        self.assertEqual(v['0x03B6'], '0x3955')
        self.assertEqual(v['0x03AD'], '0x3A37')
        self.assertEqual(v['0x03B3'], '0x3901')
        self.assertEqual(v['0x03C5'], '0x38C5')
        self.assertEqual(v['0x03C8'], '0x38D1')

    def test_frame_consumers(self):
        f = D['frame_consumers']['families']
        self.assertEqual([x['state'] for x in f['$0E_fall_set_frames_1_to_6']], ['0x0E'])
        self.assertEqual([x['state'] for x in f['tumble_set_frames_1C_to_21']], ['0x0B', '0x14', '0x1C'])
        self.assertIn('0x0B', [x['state'] for x in f['tall_pose_frame_61']])

    def test_selector_tables(self):
        t = D['selector_frame_tables']
        self.assertEqual(len(t['frame_table_object_type_1']), 20)
        self.assertEqual(t['sonic_frame_ids'], ['0x25', '0x26', '0x27', '0x28', '0x29'])
        self.assertEqual(t['air_duration'], 3)
        self.assertEqual(t['floor_duration_table_8FE0'][:6], [10, 8, 6, 5, 4, 3])

    def test_movement_tables(self):
        m = D['movement_tables']['states']
        self.assertEqual(m['0x0B']['dry_nonnegative']['first_8_8'], -64)
        self.assertEqual(m['0x0E']['dry_nonnegative'], {'first_8_8': -16, 'second_8_8': 16, 'file_offset': '0x042D5'})
        self.assertEqual(m['0x1C']['no_direction']['first_8_8'], 0)
        self.assertEqual(m['0x1B']['no_direction']['first_8_8'], 2)
        self.assertEqual(m['0x0E']['no_direction']['first_8_8'], 16)


class Frames(unittest.TestCase):
    def test_frame_sources(self):
        fr = D['frames']['frames']
        self.assertEqual(fr['0x61']['mapping_frame_cpu'], '0x85AC')
        self.assertEqual(fr['0x61']['graphics_transfer']['bank'], '0x05')
        self.assertEqual((fr['0x61']['canvas_width'], fr['0x61']['canvas_height']), (16, 48))
        self.assertEqual((fr['0x1C']['gamemaker_origin_x'], fr['0x1C']['gamemaker_origin_y']), (12, 32))
        self.assertEqual([fr[k]['graphics_transfer']['source_cpu'] for k in ('0x1C', '0x1D', '0x1E', '0x1F', '0x20', '0x21')],
                         ['0xA800', '0xA980', '0xAB00', '0xAC80', '0xAE00', '0xAF80'])
        # every frame has a distinct tile payload
        self.assertEqual(len({f['tile_bytes_sha256'] for f in fr.values()}), len(fr))

    def test_board_recorded(self):
        self.assertEqual((D['approval_board']['width'], D['approval_board']['height']), (860, 706))


class EmulatedFlights(unittest.TestCase):
    def test_weak_type26_free_arc(self):
        sc = scenario('emulated_flights_thz', 't26_weak_fixed')
        ascent = segs(sc, '0x0B')[0]
        self.assertEqual(ascent['updates'], 54)
        self.assertEqual(ascent['d503_values'], [1])
        self.assertEqual(frames_of(ascent)[:6], [('0x1C', 4), ('0x1D', 4), ('0x1E', 4), ('0x1F', 4), ('0x20', 4), ('0x21', 4)])
        self.assertEqual(ascent['enter']['d448'], '0x00')
        self.assertEqual(ascent['enter']['vy'], -1256)
        self.assertEqual(segs(sc, '0x0E')[1]['frames'][0], {'frame': '0x02', 'updates': 8})

    def test_strong_type26_and_terrain_upright(self):
        s = scenario('emulated_flights_thz', 't26_strong_fixed')
        a = segs(s, '0x0B')[0]
        self.assertEqual((a['updates'], frames_of(a), a['enter']['d448'], a['enter']['vy']), (79, [('0x61', 79)], '0xFF', -1864))
        t = scenario('emulated_flights_thz', 'terrain_upright')
        b = segs(t, '0x0B')[0]
        self.assertEqual((b['updates'], frames_of(b), b['enter']['d448'], b['enter']['vy']), (80, [('0x61', 80)], '0xFF', -1896))

    def test_boss_bounce_shares_the_weak_program(self):
        boss = scenario('stomp_and_boss', 'type50_boss_top_bounce')
        weak = scenario('emulated_flights_thz', 't26_weak_fixed')
        b = segs(boss, '0x0B')[0]
        w = segs(weak, '0x0B')[0]
        self.assertEqual(frames_of(b)[:8], frames_of(w)[:8])
        self.assertEqual((b['enter']['d448'], b['enter']['vy'], b['updates']), ('0x00', -1000, 43))
        self.assertEqual(b['d503_values'], [1])
        # the fixture preset D448 = $FF before the bounce: the bounce itself stores 0
        self.assertEqual(boss['rows'][0][COL['d448']], 255)
        self.assertEqual(boss['rows'][1][COL['d448']], 0)
        self.assertEqual(boss['rows'][1][COL['req']], 11)
        self.assertEqual(boss['rows'][1][COL['vy']], -1024)

    def test_type21_stomp_is_strong_path(self):
        sc = scenario('stomp_and_boss', 'type21_top_stomp')
        a = segs(sc, '0x0B')[0]
        self.assertEqual((a['enter']['d448'], frames_of(a), a['enter']['vy']), ('0xFF', [('0x61', 72)], -1704))
        self.assertEqual(sc['rows'][5][COL['events']][1], 'sp_up(HL=F940)')

    def test_diagonal_arc(self):
        for sid in ('terrain_diag_right', 'terrain_diag_left'):
            sc = scenario('emulated_flights_thz', sid)
            a = segs(sc, '0x1C')[0]
            self.assertEqual(a['updates'], 38, sid)
            self.assertEqual(a['d503_values'], [3, 1], sid)       # attack posture set until the apex request clears it
            self.assertEqual([f['updates'] for f in a['frames']][:4], [8, 8, 8, 8], sid)
            self.assertEqual(a['enter']['vy'], -1744, sid)
            self.assertEqual(sc['request_changes'][0]['requested_after'], '0x1C')

    def test_horizontal_spring_state_9(self):
        sc = scenario('emulated_flights_thz', 'terrain_horizontal_run_left')
        ch = [c for c in sc['request_changes'] if c['requested_after'] == '0x09']
        self.assertEqual(len(ch), 1)
        row = next(r for r in sc['rows'] if r[0] == ch[0]['update'])
        self.assertEqual((row[COL['f3']], row[COL['vx']]), (2, 1536))   # thrown back away from the block Sonic ran into

    def test_jump_lands_on_upright_spring(self):
        sc = scenario('emulated_flights_thz', 'jump_lands_on_terrain_upright')
        ch = [c for c in sc['request_changes'] if c['requested_after'] == '0x0B'][0]
        self.assertEqual(ch['executing_state'], '0x0A')
        row = next(r for r in sc['rows'] if r[0] == ch['update'])
        self.assertEqual(row[COL['f3']], 1)   # the launch clears the attack posture of the jump


class ApexOrdering(unittest.TestCase):
    def test_launch_wins_over_apex(self):
        up = next(s for s in D['apex_ordering']['scenarios'] if s['id'].startswith('0B_apex_update_on_upright'))
        self.assertEqual(up['rows'][0][COL['req']], 11)
        self.assertEqual(up['rows'][0][COL['vy']], -1920)
        self.assertEqual(up['rows'][0][COL['d448']], 255)
        self.assertNotIn('apex', up['rows'][0][COL['events']])
        # the weak script keeps running although D448 is now $FF (it is re-read only at a script restart)
        self.assertEqual([r[COL['frame']] for r in up['rows'][:5]], [28, 28, 28, 28, 29])
        dg = next(s for s in D['apex_ordering']['scenarios'] if s['id'].startswith('1C_apex_update_on_diagonal'))
        self.assertEqual((dg['rows'][0][COL['req']], dg['rows'][0][COL['f3']], dg['rows'][0][COL['vy']]), (28, 3, -1408))
        ctl = next(s for s in D['apex_ordering']['scenarios'] if s['id'].endswith('control_no_spring'))
        self.assertEqual((ctl['rows'][0][COL['req']], ctl['rows'][0][COL['vy']]), (14, 256))
        self.assertIn('apex', ctl['rows'][0][COL['events']])


class WrapperSweeps(unittest.TestCase):
    def test_apex_rule(self):
        a = D['wrapper_sweeps']['apex_wrapper']
        self.assertEqual(a['$0B']['first_start_vy_that_requests_0E'], -24)
        self.assertEqual(a['$1C']['first_start_vy_that_requests_0E'], -48)
        s = D['wrapper_sweeps']['setters_called_directly']['rows']
        self.assertEqual(s['$463C_apex_or_fall'], {'request': '0x0E', 'd503_after': 1, 'vy_after': 256, 'speed_cap': '0x0700'})
        self.assertEqual(s['$463C_from_$0A_returns_at_once']['request'], '0x0A')
        for k, v in s.items():
            if k.startswith('$45CE'):
                self.assertEqual((v['request'], v['d503_after'], v['speed_cap']), ('0x05', 0, '0x0400'), k)

    def test_0E_has_no_apex_test(self):
        self.assertTrue(all(req == '0x0E' for vy, req in D['wrapper_sweeps']['wrapper_0E_has_no_apex_test']))

    def test_gate_matrix(self):
        rows = D['spring_gate_matrix']['rows']
        for r in rows:
            fires = r['gate'] in ('terrain_upright_$6A75', 'terrain_diag_$6A90')
            self.assertEqual(r['fired'], fires, r)
        self.assertEqual(sorted({r['executing_state'] for r in rows}), ['0x09', '0x0A', '0x0B', '0x0E', '0x14', '0x1B', '0x1C'])

    def test_breakable_matrix(self):
        brk = {(r['state'], r['handler']): r['breaks_and_bounces'] for r in D['breakable_matrix']['rows']}
        for st in ('0x09', '0x0A', '0x1B', '0x1C'):
            self.assertTrue(brk[(st, 'type_0D_$6B2C')] and brk[(st, 'type_16_$6AE3')], st)
        for st in ('0x0B', '0x0E', '0x14'):
            self.assertFalse(brk[(st, 'type_0D_$6B2C')] or brk[(st, 'type_16_$6AE3')], st)

    def test_jump_hold(self):
        rows = {(r['buttons_d137'], r['counter_before'], r['water']): r for r in D['jump_hold_state_0A']['rows']}
        self.assertEqual(rows[(16, 12, 0)]['vy_after'], -1088 + 48)
        self.assertEqual(rows[(16, 13, 0)]['vy_after'], -256 + 48)
        self.assertEqual(rows[(16, 12, 1)]['vy_after'], -832 + 24)   # water gravity of $0A is $18
        self.assertEqual(rows[(0, 12, 0)]['counter_after'], 32)


class FreeFlight(unittest.TestCase):
    def fx(self, state, vx, inp, face=0):
        return next(f for f in D['free_flight']['fixtures'] if (f['state'], f['start_vx'], f['input'], f['start_facing']) == (state, vx, inp, face))

    def test_gravity_per_state(self):
        expect = {'0x0B': 24, '0x0E': 48, '0x1C': 48, '0x1B': 36, '0x0A': 48}
        for st, g in expect.items():
            vy = self.fx(st, 0, 'none')['vy'][:6]
            self.assertEqual({vy[i + 1] - vy[i] for i in range(len(vy) - 1)}, {g}, st)
        water = {w['state']: w['vy_delta_per_update'] for w in D['free_flight_water_and_cap']['water_gravity']}
        self.assertEqual(water, {'0x0B': [12], '0x0E': [24], '0x1C': [24], '0x1B': [18], '0x0A': [24]})
        self.assertEqual(D['free_flight_water_and_cap']['dry_terminal_fall']['max_vy'], 1792)

    def test_horizontal_control(self):
        # $0B / $0A brake hard against the motion (64), the others only +/-16; $1C has no drag, $1B 2, the rest 16
        self.assertEqual(self.fx('0x0B', 512, 'left')['vx'][2:5], [416, 352, 288])
        self.assertEqual(self.fx('0x0A', 512, 'left')['vx'][2:5], [416, 352, 288])
        self.assertEqual(self.fx('0x0E', 512, 'left')['vx'][2:5], [464, 448, 432])
        self.assertEqual(self.fx('0x1C', 512, 'left')['vx'][2:5], [496, 480, 464])
        self.assertEqual(self.fx('0x1C', 512, 'none')['vx'], [512] * 14)
        self.assertEqual(self.fx('0x1B', 512, 'none')['vx'][:3], [510, 508, 506])
        self.assertEqual(self.fx('0x0E', 512, 'none')['vx'][:3], [496, 480, 464])
        self.assertEqual(self.fx('0x0E', 512, 'right')['vx'][2:5], [496, 512, 528])

    def test_facing_owners(self):
        # $0B follows Left every update; $0E and $1C never update facing
        self.assertEqual(self.fx('0x0B', 0, 'left')['facing'][2:], [1] * 12)
        for st in ('0x0E', '0x1C'):
            self.assertEqual(set(self.fx(st, 0, 'left')['facing']), {0}, st)
            self.assertEqual(set(self.fx(st, 0, 'right', 1)['facing']), {1}, st)
        self.assertEqual(self.fx('0x0B', 0, 'right', 1)['facing'][-1], 0)

    def test_speed_cap(self):
        for c in D['free_flight_water_and_cap']['right_held_from_high_speed']:
            self.assertEqual(c['vx'][-1], 1024)
            self.assertEqual(c['speed_cap_d373'], 0x0400)


class AqzChains(unittest.TestCase):
    def test_aqz3_natural_run_sequence(self):
        sc = scenario('aqz_chains', 'aqz3_natural_run')
        order = [s['state'] for s in sc['state_segments'] if s['first_update'] >= 125]
        self.assertEqual(order[:15], ['0x1C', '0x0E', '0x1B', '0x1C', '0x0E', '0x1B', '0x1C', '0x0E', '0x1C', '0x0E', '0x1C', '0x1B', '0x0E', '0x0B', '0x0E'])
        starts = [(s['state'], s['first_update']) for s in sc['state_segments'] if s['first_update'] >= 125][:6]
        self.assertEqual(starts, [('0x1C', 126), ('0x0E', 140), ('0x1B', 143), ('0x1C', 158), ('0x0E', 172), ('0x1B', 175)])

    def test_ceiling_spring_replaces_a_rising_request(self):
        sc = scenario('aqz_chains', 'aqz3_natural_run')
        ch = next(c for c in sc['request_changes'] if c['update'] == 278)
        self.assertEqual((ch['executing_state'], ch['requested_before'], ch['requested_after']), ('0x1C', '0x1C', '0x1B'))
        self.assertLess(ch['vy_before'], 0)
        self.assertEqual(ch['vy_after'], 1408)
        row = next(r for r in sc['rows'] if r[0] == 278)
        self.assertEqual((row[COL['vx']], row[COL['f3']]), (1024, 3))

    def test_horizontal_spring_in_flight_becomes_state_9_then_0A(self):
        sc = scenario('aqz_chains', 'aqz3_left_diag_horizontal_ceiling')
        r15 = next(r for r in sc['rows'] if r[0] == 15)
        self.assertEqual((r15[COL['cur']], r15[COL['req']], r15[COL['f3']], r15[COL['vx']], r15[COL['vy']]), (28, 9, 2, 1536, -736))
        r16 = next(r for r in sc['rows'] if r[0] == 16)
        self.assertEqual((r16[COL['cur']], r16[COL['vy']], r16[COL['f3']]), (9, 736, 2))
        r17 = next(r for r in sc['rows'] if r[0] == 17)
        self.assertEqual((r17[COL['cur']], r17[COL['req']], r17[COL['vy']], r17[COL['f3']]), (9, 10, 0, 3))
        self.assertEqual(next(r for r in sc['rows'] if r[0] == 18)[COL['cur']], 10)

    def test_breakable_block_with_1B_attack_posture(self):
        sc = scenario('aqz_chains', 'aqz3_natural_run')
        ev = next(e for e in sc['events'] if e['event'] == 'brk0D')
        self.assertEqual((ev['update'], ev['state_executing'], ev['d503_after'], ev['vy']), (294, '0x1B', 3, -1088))

    def test_type30_strong_spring_and_ledge_fall(self):
        sc = scenario('aqz_chains', 'aqz3_natural_run')
        up = next(e for e in sc['events'] if e['event'].startswith('sp_up'))
        self.assertEqual((up['update'], up['event'], up['state_executing']), (365, 'sp_up(HL=F8A0)', '0x0E'))
        fall = next(e for e in sc['events'] if e['event'] == 'apex' and e['state_executing'] == '0x1B')
        self.assertEqual(fall['update'], 344)    # a grounded $1B running off a ledge: $463C from the empty-floor pass

    def test_aqz2_shaft_alternates_diagonals(self):
        sc = scenario('aqz_chains', 'aqz2_diagonal_shaft')
        launches = [e for e in sc['events'] if e['event'].startswith('sp_diag')]
        self.assertGreaterEqual(len(launches), 5)
        self.assertEqual({e['state_executing'] for e in launches[1:]}, {'0x0E'})
        xs = [e['x'] for e in launches]
        self.assertEqual(sorted({x // 100 for x in xs}), [29, 31])

    def test_handoff_matrix(self):
        rows = {(r['executing_state'], r['mechanism'], r['requested_state']) for r in D['handoff_matrix']['rows']}
        for key in (('0x0E', 'diagonal setter $482D', '0x1C'), ('0x0E', '$1B setter $47FB (ceiling spring / ramp)', '0x1B'), ('0x1B', 'diagonal setter $482D', '0x1C'),
                    ('0x1C', '$1B setter $47FB (ceiling spring / ramp)', '0x1B'), ('0x1C', 'horizontal setter $4849/$4868', '0x09'), ('0x1C', 'fall setter $463C', '0x0E'),
                    ('0x0B', 'fall setter $463C', '0x0E'), ('0x1B', 'fall setter $463C', '0x0E'), ('0x0A', 'upright setter $480C', '0x0B'), ('0x0E', 'upright setter $480C', '0x0B')):
            self.assertIn(key, rows, key)
        # no upright / diagonal launch is ever accepted while the executing state is still rising ($0B or $1C)
        for r in D['handoff_matrix']['rows']:
            if r['executing_state'] in ('0x0B', '0x1C') and ('upright' in r['mechanism'] or 'diagonal' in r['mechanism']):
                self.assertIn('rejected', r['mechanism'])

    def test_d448_on_every_entry(self):
        strong = {'t26_strong_fixed', 'terrain_upright', 'type21_top_stomp'}
        for r in D['d448_on_entry_to_0B']['rows']:
            if r['scenario'] in strong:
                self.assertEqual((r['d448'], r['first_frame']), ('0xFF', '0x61'), r)
            elif r['scenario'] in ('t26_weak_fixed', 't26_span_weak', 'type50_boss_top_bounce', 'terrain_diag_left'):
                self.assertEqual((r['d448'], r['first_frame']), ('0x00', '0x1C'), r)


class CeilingSpring(unittest.TestCase):
    def test_ring_probe_path_fires_without_a_y_speed_gate(self):
        f = D['ceiling_spring_windows']['fixtures']
        for label in ('falling_from_above_state_0E', 'falling_from_above_state_1C'):
            for r in f[label]:
                self.assertEqual(r['columns_dx_0_to_31_fired'], '.' * 9 + 'X' * 23, label)
                self.assertEqual(r['fire_at_dx_16_[update,y,vy,vx,d503,request]'][1:], [238, 1408, 1024, 3, '0x1B'], label)
        for label in ('rising_from_below_state_0B', 'rising_from_below_state_1C'):
            for r in f[label]:
                self.assertEqual(r['columns_dx_0_to_31_fired'], 'X' * 32, label)
                self.assertEqual(r['fire_at_dx_16_[update,y,vy,vx,d503,request]'][2:], [1408, 1024, 3, '0x1B'], label)

    def test_natural_trace_has_a_falling_ceiling_spring_launch(self):
        sc = scenario('aqz_chains', 'aqz3_natural_run')
        row141 = next(r for r in sc['rows'] if r[0] == 141)
        row142 = next(r for r in sc['rows'] if r[0] == 142)
        self.assertGreater(row141[COL['vy']], 0)            # falling
        self.assertEqual(row141[COL['cur']], 14)             # state $0E
        self.assertEqual((row142[COL['req']], row142[COL['vy']], row142[COL['vx']]), (27, 1408, 1024))

    def test_correction_recorded(self):
        self.assertEqual(D['corrections'][0]['id'], 'C1')
        self.assertIn('POC DIVERGENCE', D['corrections'][0]['class'])
        names = {r['name'] for r in D['regions']}
        self.assertTrue({'ring_probe_753E', 'ceiling_pass_73C9', 'terrain_pass_order_690B'} <= names)


class SameStateHorizontal(unittest.TestCase):
    def test_controlled(self):
        c = {r['case']: r for r in D['same_state_horizontal_spring']['controlled']}
        self.assertEqual(c['no_input']['after_rolling_suffix_37F4']['req'], '0x09')
        o = c['opposing_left_vs_vx_plus']
        self.assertEqual((o['after_setter']['req'], o['after_setter']['d503'], o['after_setter']['vx']), ('0x09', 2, 1536))
        self.assertEqual((o['after_rolling_suffix_37F4']['req'], o['after_rolling_suffix_37F4']['d503']), ('0x07', 0))

    def test_emulated(self):
        e = {r['case']: r for r in D['same_state_horizontal_spring']['emulated']}
        self.assertEqual(e['opposing_left']['setter_exit_snapshot'][0]['executing'], 9)
        self.assertEqual(e['opposing_left']['setter_exit_snapshot'][0]['req'], '0x09')
        r0 = e['opposing_left']['rows_from_contact'][0]
        self.assertEqual((r0['executing'], r0['requested'], r0['d503'], r0['vx']), ('0x09', '0x07', 0, 1536))
        self.assertEqual(e['opposing_left']['rows_from_contact'][1]['executing'], '0x07')
        self.assertEqual(e['no_input']['rows_from_contact'][0]['requested'], '0x09')
        self.assertEqual(D['same_state_horizontal_spring']['classification'], 'CANONICAL - preserve it')


class Callers(unittest.TestCase):
    def test_upright_launch_callers(self):
        c = D['setter_callers']['callers']
        self.assertEqual([x['site'] for x in c['$035F upright-launch vector (-> $5F17 -> $480C)']], ['bank $0C:B2D2', 'bank $1E:82FB', 'bank $1E:8423', 'bank $1E:99D0'])
        self.assertEqual([x['site'] for x in c['$480C upright setter']], ['bank $01:5F21', 'bank $01:6A8D'])
        self.assertEqual([x['site'] for x in c['$482D diagonal setter']], ['bank $01:6ACB'])
        self.assertEqual([x['site'] for x in c['$03BF $1B vector (-> $47FB)']], ['bank $0C:9204'])
        self.assertEqual(len(c['$463C fall setter']), 7)


class Contract(unittest.TestCase):
    def test_transition_table_columns(self):
        for row in D['transition_table']:
            self.assertEqual(set(row), {'source_mechanism', 'state', 'd448', 'd503_on_entry', 'animation', 'next_canonical_transition', 'note'})
        self.assertEqual([r['state'] for r in D['transition_table']], ['$0B', '$0B', '$1C', '$09', '$1B', '$0E', '$0A', '$14'])

    def test_poc_contract(self):
        c = D['poc_contract']['state_to_presentation']
        self.assertEqual(c[1]['frames'], [{'frame': '0x61', 'updates': 4}])
        self.assertEqual(len(c[0]['frames']), 18)
        self.assertEqual(sum(f['updates'] for f in c[0]['frames']), 82)
        self.assertEqual(sum(f['updates'] for f in c[4]['frames']), 232)

    def test_poc_facts_are_read_only_citations(self):
        self.assertEqual(D['poc_source_facts']['poc_commit'], '5d99a38d1f439ac02cd9d3010d09f70cc57aa575')
        self.assertIn('POC SOURCE (READ-ONLY)', D['poc_source_facts']['evidence'])


@rom_only
class RomBackedStatic(unittest.TestCase):
    def test_scripts_regenerate(self):
        self.assertEqual(T.state_scripts(ROM), D['state_scripts'])
        self.assertEqual(T.frame_consumers(ROM), D['frame_consumers'])
        self.assertEqual(T.selector_frame_tables(ROM), D['selector_frame_tables'])
        self.assertEqual(T.region_table(ROM), D['regions'])

    def test_frames_regenerate(self):
        self.assertEqual(T.frame_table(ROM), D['frames'])

    def test_contract_and_transitions_regenerate(self):
        self.assertEqual(T.poc_contract(ROM), D['poc_contract'])
        self.assertEqual(T.transition_table(), D['transition_table'])

    def test_callers_regenerate(self):
        self.assertEqual(T.setter_callers(ROM), D['setter_callers'])

    def test_apex_rule_full_sweep_against_the_original_wrappers(self):
        lab = T.lab_empty(ROM)
        for name, addr, cur, f3, grav in (('b', 0x393B, 0x0B, 1, 24), ('c', 0x3955, 0x1C, 3, 48)):
            for vy in range(-300, 301):
                r = T.run_wrapper(lab, addr, cur, f3, vy)
                self.assertEqual(r['req'] == '0x0E', vy + grav >= 0, (name, vy))
                if r['req'] == '0x0E':
                    self.assertEqual((r['vy'], r['d503']), (256, 1), (name, vy))
        for vy in range(-300, 301):
            self.assertEqual(T.run_wrapper(lab, 0x3A37, 0x0E, 1, vy)['req'], '0x0E')

    def test_gate_and_breakable_matrices_regenerate(self):
        self.assertEqual(T.spring_gate_matrix(ROM), D['spring_gate_matrix'])
        self.assertEqual(T.breakable_matrix(ROM), D['breakable_matrix'])
        self.assertEqual(T.jump_hold(ROM), D['jump_hold_state_0A'])
        self.assertEqual(T.wrapper_sweeps(ROM), D['wrapper_sweeps'])


@rom_only
class RomBackedWholeGame(unittest.TestCase):
    def test_weak_spring_scenario_regenerates(self):
        g = T.rig(ROM, 0, 0)
        got = T.scenario(g, 't26_weak_fixed', 'm', {}, dict(x=1912, y=846, vy=0x0100, cur=0x0E, f3=1, floor=False, width=128,
                                                              patch=T.clear_cells(1912 - 64, 1912 + 64, 0, 832)), 150)
        self.assertEqual(got['rows'], scenario('emulated_flights_thz', 't26_weak_fixed')['rows'])

    def test_apex_ordering_regenerates(self):
        self.assertEqual(T.apex_ordering(ROM), D['apex_ordering'])

    def test_boss_and_stomp_regenerate(self):
        self.assertEqual(T.stomp_and_boss(ROM), D['stomp_and_boss'])

    def test_aqz_chains_regenerate(self):
        self.assertEqual(T.aqz_chains(ROM), D['aqz_chains'])

    def test_same_state_horizontal_regenerates(self):
        self.assertEqual(T.same_state_horizontal(ROM), D['same_state_horizontal_spring'])

    def test_ceiling_spring_windows_regenerate(self):
        self.assertEqual(T.ceiling_spring_windows(ROM), D['ceiling_spring_windows'])

    def test_free_flight_regenerates(self):
        self.assertEqual(T.free_flight(ROM), D['free_flight'])
        self.assertEqual(T.free_flight_water_and_cap(ROM), D['free_flight_water_and_cap'])


if __name__ == '__main__':
    unittest.main()
