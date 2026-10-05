"""Spring Shoes presentation / act-clear / detach audit: cache locks plus ROM-backed re-execution of the original routines.

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
import spring_shoes_presentation as T
import level_package as L

ROM_SHA = 'eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607'
D = json.loads(T.OUTPUT.read_text(encoding='utf-8'))
A, B, C = D['part_a_presentation'], D['part_b_act_clear'], D['part_c_detach']
TR = A['traces']


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
    def test_identity(self):
        self.assertEqual(D['rom_sha256'], ROM_SHA)
        self.assertFalse(D['static_only'])
        self.assertIn('Research only', D['scope'])

    def test_classification(self):
        ids = [c['id'] for c in D['classification']]
        self.assertEqual(len(ids), len(set(ids)))
        by = {c['id']: c['class'] for c in D['classification']}
        for k in ('P1', 'P2', 'P3', 'P4', 'P5', 'B1', 'B2', 'B4', 'B5', 'B6', 'B8', 'C1', 'C2', 'C3', 'C5', 'C6', 'C7'):
            self.assertEqual(by[k], 'CANONICAL', k)
        self.assertEqual(by['C4'], 'POC DIVERGENCE')
        self.assertEqual(by['B3'], 'EXPLICIT ADAPTER CANDIDATE')
        self.assertEqual({k for k, v in by.items() if v == 'UNRESOLVED'}, {'P6', 'B7'})
        self.assertEqual(len(D['agents_candidates']), 4)
        self.assertIn('SCR_chaos_spring', ' '.join(D['poc_source_read_only']['files']))


class StaticDecode(unittest.TestCase):
    def test_object_scripts(self):
        st = A['object_scripts']['states']
        self.assertEqual([(r['duration'], r['frame'], r['callback']) for r in st['1']['records'][:2]], [(8, 1, '0x8B64'), (8, 2, '0x8B64')])
        self.assertEqual([(r.get('duration'), r.get('frame'), r.get('callback'), r.get('state')) for r in st['3']['records'][:2]], [(12, 3, '0x8BC3', None), (None, None, None, 4)])
        self.assertEqual([(r['duration'], r['frame']) for r in st['4']['records'][:1]], [(4, 4)])
        self.assertEqual([(r['duration'], r['frame'], r['callback']) for r in st['5']['records'][:2]], [(1, 4, '0x8BCE'), (8, 4, '0x8BD7')])
        self.assertEqual(st['5']['records'][2]['command'], '07 jump')

    def test_mapping_frames(self):
        f = A['mapping_frames']['frames']
        for k in ('1', '2'):
            self.assertEqual((f[k]['pieces'], f[k]['extent_x'], f[k]['extent_y'], f[k]['x_origin']), (2, 8, 16, 0))
        for k in ('3', '4'):
            self.assertEqual((f[k]['pieces'], f[k]['extent_x'], f[k]['extent_y'], f[k]['x_origin']), (2, 12, 48, 4))
        self.assertEqual(f['3']['coords_cpu'], f['4']['coords_cpu'])
        self.assertEqual([p['tile_offset'] for p in f['3']['piece_list']], [8, 10])
        self.assertEqual([p['tile_offset'] for p in f['4']['piece_list']], [12, 14])
        pl = A['mapping_frames']['player_frame_0B']
        self.assertEqual((pl['pieces'], pl['extent_x'], pl['extent_y']), (5, 8, 24))

    def test_player_script_is_one_frame(self):
        r = A['player_state_12_script']['records']
        self.assertEqual([(x.get('duration'), x.get('frame'), x.get('callback')) for x in r[:1]], [(4, 11, '0x03B0')])
        self.assertEqual(r[1]['command'], '00 restart/hold state')

    def test_opcode_scans(self):
        f = A['static_facts']
        self.assertEqual([s['cpu'] for s in f['requested_state_compare_12_sites']], ['0xA882', '0x9765'])
        self.assertEqual([s['cpu'] for s in f['d3a4_operand_sites']], ['0x3B82', '0x3B90', '0x3B9F', '0x3BAC', '0x8B85'])

    def test_registration_rule(self):
        r = A['registration']
        self.assertEqual((r['shoe_frame_3_compressed']['shoe_anchor_dy_from_sonic_anchor'], r['shoe_frame_4_held']['shoe_anchor_dy_from_sonic_anchor']), (16, 11))
        self.assertEqual(r['shoe_frame_4_held']['piece_rows_rel_sonic_anchor'], [-5, 10])
        self.assertEqual(r['shoe_frame_3_compressed']['piece_rows_rel_sonic_anchor'], [0, 15])
        self.assertEqual(r['sonic_frame_0B_rows_rel_anchor'], [-32, -1])
        self.assertEqual(r['shoe_frame_4_held']['piece_cols_rel_sonic_anchor'], [-8, 7])


class PresentationTraces(unittest.TestCase):
    def test_cadence(self):
        t = TR['mghz1_plain']
        self.assertEqual((t['state_12_first_update'], t['contact_updates'], t['bounce_period_updates']), (12, [12, 93, 174, 255], [81, 81, 81]))
        runs = [(r['state'], r['frame'], r['first_u'], r['length']) for r in t['shoe_frame_runs']]
        self.assertEqual(runs[:6], [(0, 0, 3, 2), (1, 1, 5, 7), (3, 3, 12, 12), (4, 4, 24, 69), (3, 3, 93, 12), (4, 4, 105, 69)])
        self.assertEqual(t['player_frame_values_in_state_12'], [11])
        self.assertEqual(t['player_timer_cycle_first_12'], [4, 3, 2, 1] * 3)
        self.assertEqual(t['frame_changes_after_pickup'], 7)

    def test_follow_offsets(self):
        t = TR['mghz1_plain']
        self.assertEqual(t['follow_offsets']['values'], [11, 16])
        self.assertEqual(t['follow_offsets']['offset_16_updates_per_bounce_relative_to_contact'], list(range(1, 13)))
        rel = t['follow_offset_rel_second_contact']
        self.assertEqual({k: v['offset_y'] for k, v in rel.items() if int(k) <= 0}, {'-2': 11, '-1': 11, '0': 11})
        self.assertEqual(rel['12']['owner_frame_at_call'], 3)
        self.assertEqual(rel['13']['offset_y'], 11)

    def test_sat_equals_model_except_pickup(self):
        s = TR['mghz1_plain']['sat_checks']
        self.assertEqual((s['frames_checked'], s['mismatch_updates']), (289, [13]))

    def test_mirroring(self):
        t = TR['mghz1_left_right']
        self.assertEqual((t['player_f4_values'], t['shoe_f4_values'], t['shoe_f3_values']), ([0, 16], [0], [128]))
        self.assertEqual(t['player_frame_values_in_state_12'], [11])

    def test_sez_matches(self):
        self.assertTrue(TR['cadence_identical_between_zones'])
        self.assertEqual(TR['sez1_plain']['bounce_period_updates'], [81, 81, 81])
        self.assertEqual(TR['sez1_plain']['follow_offsets']['values'], [11, 16])

    def test_art_bounds(self):
        b = TR['art_bounds_mghz']
        self.assertEqual({k: v['opaque_rows_rel_anchor'] for k, v in b.items()}, {'1': [2, 17], '2': [2, 17], '3': [2, 17], '4': [7, 17]})
        self.assertEqual(TR['art_bounds_sez'], b)


class ActClear(unittest.TestCase):
    def test_activation_boundary_and_timeline(self):
        a = B['activation']
        self.assertEqual(a['conversion_screen_x_range'], [271, 287])
        self.assertTrue(all(not r['converted_within_10_frames'] for r in a['horizontal_sweep'] if r['sign_screen_x'] >= 288))
        tl = a['timeline']
        self.assertEqual((tl['request_update'], tl['requested'], tl['current_replaced_update'], tl['shoe_state5_first_update'], tl['shoe_removed_update'], tl['activation_callback_hits']), (3, 14, 4, 5, 36, 1))
        w = tl['writes']
        self.assertEqual((w[0]['what'], w[0]['value'], w[0]['pc']), ('D502', 14, '0xA88D'))
        self.assertFalse(any(x['what'] == 'D3A4' for x in w))
        self.assertTrue(any(x['what'] == 'shoe_slot' and x['value'] == 254 and x['pc'] == '0x625F' for x in w))
        self.assertTrue(any(x['what'] == 'shoe_slot' and x['value'] == 47 for x in w))          # re-created from the placement

    def test_chains(self):
        c = B['chains']
        n = c['natural_conversion_then_walk_into_sign']['events_frame_index']
        self.assertEqual((n['left_12_request'], n['sign_contact'], n['request_20'], n['act_clear_flag']), (2, 38, 316, 346))
        s = c['synthetic_prewoken_sign_top_contact_stalls']
        self.assertNotIn('request_20', s['events_frame_index'])
        self.assertEqual((s['end']['final_player_state'], s['end']['child_state_at_end'], s['end']['shoe_present'], s['end']['level_timer_d2be'], s['end']['frames_run']), (0x12, [4], True, 0, 1500))
        j = c['synthetic_prewoken_sign_top_contact_then_jump']['events_frame_index']
        self.assertEqual((j['left_12_request'], j['request_20'], j['act_clear_flag']), (225, 315, 385))
        sd = c['synthetic_prewoken_sign_side_contact']['events_frame_index']
        self.assertEqual((sd['sign_contact'], sd['hurt_requested'], sd['request_20'], sd['act_clear_flag']), (4, 4, 282, 320))

    def test_callback_matrix_invariant(self):
        rows = {r['case']: r for r in B['callback_12_matrix']['cases']}
        self.assertEqual({r['d522_floor_bit1_after'] for r in rows.values()}, {0})
        fc = rows['floor_contact']
        self.assertEqual((fc['requested_after'], fc['vy_after'], fc['owner_requested_state'], fc['sound_request_de04']), (18, -1920, 3, 0xC2))
        j = rows['floor_contact_jump_press']
        self.assertEqual((j['requested_after'], j['vy_after'], j['owner_requested_state'], j['f3_after']), (10, -1088, 5, 3))
        w = rows['side_wall_right']
        self.assertEqual((w['requested_after'], w['owner_requested_state'], w['rings_after'], w['invulnerability_timer_d3b1'], w['f3_after'], w['vx_after'], w['vy_after']), (30, 5, 5, 0, 1, -256, -1024))


class Detach(unittest.TestCase):
    cases = C['cases']

    def test_manual_jump(self):
        for k in ('manual_jump_rising', 'manual_jump_falling', 'manual_jump_floor_contact'):
            c = self.cases[k]
            self.assertEqual((c['successor_requested'], c['request_update'], c['shoe_state5_first_update'], c['current_state_replaced_update']), (10, c['request_update'], c['request_update'], c['request_update'] + 1), k)
            self.assertEqual(c['at_replacement']['vy'], -1040)

    def test_stomp(self):
        c = self.cases['type21_top_stomp']
        self.assertEqual((c['successor_requested'], c['current_state_replaced_update'] - c['request_update'], c['shoe_state5_first_update'] - c['request_update']), (11, 1, 2))
        self.assertEqual(c['at_replacement']['vy'], -1704)

    def test_side_contact_damage(self):
        c = self.cases['type21_side_contact_with_rings']
        self.assertEqual((c['successor_requested'], c['at_replacement']['rings'], c['at_replacement']['f3'], c['at_replacement']['d3b1']), (30, 0, 0xC1, 119))
        self.assertEqual(c['shoe_state5_first_update'] - c['request_update'], 2)

    def test_wall_branch_has_no_damage_side_effects(self):
        c = self.cases['terrain_wall_side_branch_with_rings']
        self.assertEqual((c['successor_requested'], c['shoe_state5_first_update'], c['request_update']), (30, c['request_update'], c['request_update']))
        self.assertEqual((c['at_replacement']['rings'], c['at_replacement']['d3b1'], c['at_replacement']['f3']), (5, 0, 1))
        m = C['object_mirrored_side_contact_monitor']
        self.assertEqual((m['successor_requested'], m['at_replacement']['d3b1'], m['at_replacement']['f3']), (30, 0, 1))
        self.assertGreaterEqual(m['at_replacement']['rings'], 5)          # no ring loss

    def test_terrain_spring(self):
        c = self.cases['terrain_upright_spring']
        self.assertEqual((c['successor_requested'], c['at_replacement']['vy'], c['shoe_state5_first_update'] - c['request_update']), (11, -1896, 2))

    def test_owner_pointer_never_cleared(self):
        for k, c in self.cases.items():
            self.assertFalse(c['owner_pointer_changed_by_any_write'], k)
            self.assertEqual(c['owner_pointer_after'], '0xD700', k)

    def test_mapped_springs_are_inert(self):
        m = C['mapped_spring']
        self.assertEqual((m['controls_that_launch'], m['spring_launches_with_shoes']), (3, 0))
        for r in m['springs']:
            self.assertEqual(r['control_request_state_0E'], 11)
            for c in r['with_shoes']:
                self.assertEqual(c['spring_requests'], [])
            self.assertTrue(all(c['rebounds'] >= 1 for c in r['with_shoes']))


@rom_only
class RomBacked(unittest.TestCase):
    def test_static_regenerates(self):
        self.assertEqual(T.object_scripts(ROM), A['object_scripts'])
        self.assertEqual(T.mapping_frames(ROM), A['mapping_frames'])
        self.assertEqual(T.player_state12_script(ROM), A['player_state_12_script'])
        self.assertEqual(T.static_facts(ROM), A['static_facts'])
        self.assertEqual(T.derived_registration(ROM), A['registration'])
        self.assertEqual(T.callback_12_matrix(ROM), B['callback_12_matrix'])

    def test_presentation_regenerates(self):
        self.assertEqual(T.presentation_section(ROM), TR)

    def test_act_clear_regenerates(self):
        self.assertEqual(T.act_clear_section(ROM), {k: v for k, v in B.items()})

    def test_detach_regenerates(self):
        d = T.detach_section(ROM)
        d['object_mirrored_side_contact_monitor'] = T.monitor_side_case(ROM)
        self.assertEqual(d, C)


if __name__ == '__main__':
    unittest.main()
