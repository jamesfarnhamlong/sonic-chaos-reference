"""SEZ terrain-mechanics audit: surface $0C / block $AF / dynamic $13 (crumble ledge) and surface $1A / block $A7 (booster pad).

Cache classes run without a ROM.  ROM classes need the verified ROM (SONIC_CHAOS_ROM or ../source/Sonic Chaos (Europe).sms) and skip otherwise: they re-execute the original
routines (controlled sweeps) and the whole game (drops / walks) and compare with the committed caches.  Never touches POC.
"""
import hashlib
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import sez_surfaces as S
import level_package as L

ROM_SHA = 'eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607'
D = json.loads(S.OUT_AUDIT.read_text(encoding='utf-8'))
C = json.loads(S.OUT_CONTRACTS.read_text(encoding='utf-8'))
CR, BO = D['crumble'], D['booster']
WGC, WGB = CR['whole_game'], BO['whole_game']
CC, CB = C['crumble_0C_13'], C['booster_1A']


def load_rom():
    candidates = []
    if os.environ.get('SONIC_CHAOS_ROM'):
        candidates.append(Path(os.environ['SONIC_CHAOS_ROM']))
    candidates += [ROOT.parent / 'source/Sonic Chaos (Europe).sms', ROOT.parent / 'Sonic Chaos (Europe).sms']
    for p in candidates:
        if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest() == ROM_SHA:
            return L.load_rom(p)
    return None


def rt(o):
    return json.loads(json.dumps(o))


ROM = load_rom()
needs_rom = unittest.skipUnless(ROM, 'verified ROM not available')


class CacheIdentity(unittest.TestCase):
    def test_identity_scope_and_counts(self):
        self.assertEqual((D['rom_sha256'], C['rom_sha256']), (ROM_SHA, ROM_SHA))
        self.assertTrue(D['research_only'] and D['poc_untouched'] and not D['static_only'])
        self.assertEqual(D['scope']['out'], ['$28/$86', '$20/$23', '$54/$55', 'monitor repair', 'parked presentation defects'])
        n = D['counts']
        self.assertGreater(n['controlled_cases_total'], 330000)
        self.assertEqual(n['controlled_mismatches'], 0)
        self.assertEqual((n['crumble_cells_driven_whole_game'], n['booster_cells_driven_whole_game']), (93, 9))
        self.assertEqual(D['contracts_sha256'], S.sha_json(C))
        self.assertEqual(C['research_base'], 'a200826')


class StaticFacts(unittest.TestCase):
    s = D['static']

    def test_dispatch_and_vectors(self):
        t = self.s['floor_dispatch_table_6973']
        self.assertEqual((t['surface_$0C'], t['surface_$1A'], t['surface_$00']), ('0x6B79', '0x69B1', '0x6C45'))
        self.assertEqual(self.s['vectors'], {'0x0338': '0x60FB', '0x0329': '0x5EE1', '0x0428': '0x6C1F', '0x032C': '0x5E9C'})

    def test_blocks(self):
        b = self.s['block_headers']
        self.assertEqual((b['0xAF']['flags'], b['0xAF']['one_way_bit6'], b['0xAF']['solid_bit7'], b['0xAF']['vertical_profile_by_x'], b['0xAF']['horizontal_profile_distinct']),
                         ('0x4C', True, False, [32] * 32, [96]))
        self.assertEqual((b['0xB0']['flags'], b['0xB0']['vertical_profile_by_x'], b['0xB0']['horizontal_profile_distinct']), ('0x00', [0] * 32, [64]))
        a7 = b['0xA7']
        self.assertEqual((a7['flags'], a7['solid_bit7'], a7['surface_type'], a7['horizontal_profile_distinct']), ('0x9A', True, '0x1A', [64]))
        self.assertEqual(a7['vertical_profile_by_x'], [0] * 8 + [1] * 4 + [2] * 8 + [1] * 4 + [0] * 8)
        self.assertEqual(self.s['surface_0c_blocks_all_zones'], ['0xAF', '0xB9', '0xBA', '0xBB'])
        self.assertEqual(self.s['surface_1a_blocks_all_zones'], ['0xA7'])
        self.assertTrue(all(self.s['siblings_header_identical_to_af'].values()))

    def test_remembered_cell_register_sites(self):
        s = self.s['operand_sites']
        self.assertEqual([r['cpu'] for r in s['D356']], ['0x6B89', '0x6BA1'])
        self.assertEqual(len(s['D354']), 13)
        self.assertTrue(all(r['role'] != 'UNCLASSIFIED' for r in s['D356']))

    def test_level_clear_covers_the_remembered_cell(self):
        lc = self.s['level_clear']
        self.assertEqual(lc['clears_cpu_range'], ['0xD300', '0xDBBF'])
        self.assertTrue(lc['covers_d356'] and lc['covers_slots_d540'] and lc['covers_occupancy_d400'] and lc['covers_effect_state_d452'])
        self.assertFalse(lc['covers_d12f_frame_counter'])
        self.assertEqual(lc['caller_count'], 16)

    def test_type13_scripts(self):
        t = self.s['type13']
        self.assertEqual((t['state_count'], t['state_table_cpu'], t['state_script_cpus']), (4, '0xA28A', ['0xA292', '0xA298', '0xA2C9', '0xA2CF']))
        self.assertEqual(t['callbacks'], ['0xA2DD', '0xA31B', '0xA33F', '0xA344', '0xA36A'])
        self.assertEqual([(x['dx'], x['dy'], x['parameter']) for x in t['spawns']], [(-14, -24, 3), (-6, -24, 8), (2, -24, 5), (10, -24, 1)])
        self.assertEqual(t['frames_used'], [0, 15])
        self.assertFalse(t['state_2_reached_by_code'])
        st1 = t['states'][1]['ops']
        self.assertEqual([(o.get('duration'), o.get('callback')) for o in st1 if o['op'] == 'record'], [(16, '0xA344'), (1, '0xA36A'), (224, '0xA33F')])
        self.assertEqual([o['sound'] for o in st1 if o['op'] == 'sound'], [163])
        self.assertEqual(t['states'][3]['ops'][0], {'cpu': '0xA2CF', 'command': 2, 'op': 'velocity_8_8', 'x': 0, 'y': 512})

    def test_no_contact_no_zone_gate(self):
        self.assertEqual(D['contact_scan']['contact_helper_calls_found'], [])
        self.assertEqual(D['contact_scan']['all_call_targets'], ['0x0338', '0x0428'])
        self.assertEqual(D['zone_gate_scan']['zone_dependent_regions'], ['effect5_81bf'])

    def test_disassembly_of_the_two_handlers(self):
        d = self.s['routines_disassembly']
        h = [x['text'] for x in d['crumble_handler_6b79']]
        self.assertEqual(h[:3], ['BIT 7,(IX+0x19)', 'RET nz', 'LD HL,0'])
        self.assertIn('CALL 0x5eb7', h)
        b = [x['text'] for x in d['booster_handler_7646']]
        self.assertEqual(b[0], 'BIT 1,(IX+0x22)')
        self.assertIn('LD A,0xbd', b)
        self.assertIn('LD (IX+2),0x10', b)

    def test_region_table(self):
        r = {x['name']: x for x in self.s['regions']}
        self.assertEqual(r['crumble_handler_6b79']['length'], 0x6BAA - 0x6B79)
        self.assertEqual(r['type13_callbacks']['bank'], '0x0C')
        self.assertEqual(len({x['sha256'] for x in r.values()}), len(r))


class Census(unittest.TestCase):
    c = D['census']

    def test_counts(self):
        self.assertEqual(self.c['sez_counts'], {'crumble_af': [19, 16, 1], 'booster_a7': [0, 2, 2]})
        self.assertEqual(self.c['other_zone_counts']['crumble_af'], {'thz1': 1, 'thz2': 1, 'aqz1': 32, 'aqz2': 2, 'eez2': 21})
        self.assertEqual(self.c['other_zone_counts']['booster_a7'], {'aqz1': 1, 'aqz2': 2, 'eez1': 1, 'eez2': 1})
        self.assertEqual(self.c['b0_in_initial_layouts'], 0)

    def test_geometry_formulas(self):
        for key in ('sez1', 'sez2', 'sez3'):
            for e in self.c['acts'][key].get('af', []):
                cx, cy = e['cell']
                self.assertEqual(e['object_anchor'], [cx * 32 + 14, cy * 32 + 24])
                self.assertEqual(e['hold_anchor_y'], cy * 32 + 24 - 40)
                self.assertEqual(e['shard_anchors'], [[cx * 32 + o, cy * 32] for o in (0, 8, 16, 24)])
                self.assertEqual(e['cell_pointer_offset_from_c001'], cy * 128 + cx)

    def test_runs(self):
        self.assertEqual(D['crumble_runs']['sez1'][6], {'row': 14, 'cells': [62, 67], 'count': 6})
        self.assertEqual(D['crumble_runs']['sez2'][8], {'row': 18, 'cells': [44, 47], 'count': 4})
        self.assertEqual(sum(r['count'] for r in D['crumble_runs']['sez1']), 19)


class ControlledSweeps(unittest.TestCase):
    def test_zero_mismatches_everywhere(self):
        for s in (CR['trigger_sweep'], CR['posture_independence'], CR['handler_matrix'], CR['init_matrix'], CR['rider_matrix'], CR['break_matrix'], CR['shard_matrix'], CR['lifecycle'],
                  BO['handler_matrix'], BO['probe_sweep'], BO['a7_support']):
            self.assertEqual(s['mismatches'], 0, s['evidence'])
            self.assertGreater(s['cases'], 500)

    def test_case_counts(self):
        self.assertEqual(CR['trigger_sweep']['cases'], 106704)
        self.assertEqual(CR['posture_independence']['cases'], 3072)
        self.assertEqual(CR['handler_matrix']['cases'], 545)
        self.assertEqual(CR['init_matrix']['cases'], 2048)
        self.assertEqual(CR['rider_matrix']['cases'], 14080)
        self.assertEqual(CR['break_matrix']['cases'], 1801)
        self.assertEqual(BO['handler_matrix']['cases'], 65536)
        self.assertEqual(BO['probe_sweep']['cases'], 19200)
        self.assertEqual(BO['a7_support']['cases'], 1024)

    def test_trigger_rule(self):
        t = CR['trigger_sweep']
        self.assertEqual(t['reach_counts']['reached_and_in_cell'], 50688)
        self.assertEqual(t['effect_counts']['vy<0_same_cell=False'], 6336)
        self.assertEqual(CR['posture_independence']['effect'], {'spawned': True, 'd518_after': 0, 'd356_is_cell_pointer': True, 'handler_reached': True})

    def test_handler_pool_semantics(self):
        m = CR['handler_matrix']
        self.assertEqual({k: v for k, v in m['first_free_slot_by_first_k_occupied'].items() if k.isdigit()}, {**{str(k): k for k in range(16)}, '16': None})
        self.assertEqual(m['examples']['full_pool'], {'d518': 0, 'd356': 49988, 'spawn': None, 'slot16_30_31': [68, 195]})
        self.assertEqual(m['examples']['free_pool']['spawn'], {'slot': 0, 'type': 19, 'p3f': 0, 'x': 2160, 'y': 194, 'cell_pointer_30_31': [68, 195]})

    def test_rider_rule(self):
        r = CR['rider_matrix']
        self.assertEqual(r['held_count_by_state_of_256_f3_values']['0x0E'], 256)
        self.assertEqual(r['held_count_by_state_of_256_f3_values']['0x05'], 128)
        self.assertIn('NOT compared', r['rule'])

    def test_break_rule(self):
        self.assertEqual(CR['break_matrix']['outcome_counts'], {'removed': 1280, 'replaced': 512})

    def test_shards(self):
        s = CR['shard_matrix']
        self.assertTrue(s['first_move_pass_equals_parameter_plus_2_for_parameters_1_to_255'])
        rows = s['rows_parameter_1']
        self.assertEqual([r[5] for r in rows[:6]], [192, 192, 196, 202, 210, 220])
        self.assertEqual([S.shard_model(1, n, 192) for n in range(1, 7)], [192, 192, 196, 202, 210, 220])
        self.assertEqual([S.shard_model(3, n, 192) for n in range(1, 8)], [192, 192, 192, 192, 196, 202, 210])

    def test_lifecycle_table(self):
        lc = CR['lifecycle']
        self.assertEqual(len(lc['table_rows_16px_cells']), 32)
        self.assertEqual(S.lifecycle_class(lc['table_rows_16px_cells'], 1000, 600, 1000, 600), 0)
        self.assertEqual(S.lifecycle_class(lc['table_rows_16px_cells'], 1000 + 130, 600 + 288, 1000, 600), 2)
        self.assertEqual(S.lifecycle_class(lc['table_rows_16px_cells'], 1000 + 130, 600 + 352, 1000, 600), 3)
        self.assertEqual(lc['class_counts'], {'0': 12736, '1': 7464, '2': 19224, '3': 15729})

    def test_pools(self):
        p = CR['pools']['children_with_k_free_slots_in_7_to_17']
        self.assertEqual({k: v['children_slots'] for k, v in p.items()}, {'11': [7, 8, 9, 10], '5': [13, 14, 15, 16], '4': [14, 15, 16, 17], '3': [15, 16, 17], '2': [16, 17], '1': [17], '0': []})
        self.assertEqual(p['2']['parameters'], [3, 8])
        low = CR['pools']['child_below_parent_one_update_later']
        self.assertEqual(low['child_slot_7_rows_pass_state_requested_parameter'][:2], [[19, 0, 0, 3], [20, 0, 3, 3]])
        self.assertEqual(low['child_slot_11_above_parent_rows'][:2], [[19, 0, 3, 1], [20, 3, 3, 0]])

    def test_side_and_ceiling(self):
        b = CR['side_ceiling']['per_block']
        self.assertEqual(b['0xAF'], b['0x0D_one_way_reference'])
        self.assertEqual(b['0xAF']['side_pass_pushes_or_flags'], 0)
        self.assertGreater(b['0x01_solid_reference']['side_pass_pushes_or_flags'], 0)

    def test_update_order(self):
        self.assertEqual(CR['update_order']['one_loop_iteration'], ['player_engine_64fa', 'callback_player', 'terrain_pass_690b', 'floor_pass_691a', 'ring_probe_753e', 'object_scheduler_5dd1', 'frame_wait_0606'])

    def test_booster_rules(self):
        self.assertEqual(BO['handler_matrix']['effect_counts'], {'False': 32768, 'True': 32768})
        self.assertEqual((BO['probe_sweep']['reached_inside'], BO['probe_sweep']['reached_outside'], BO['probe_sweep']['effect_cases']), (4096, 0, 2048))
        self.assertEqual(BO['a7_support']['vertical_profile_runs'], [[0, 7, 0], [8, 11, 1], [12, 19, 2], [20, 23, 1], [24, 31, 0]])


class WholeGameCrumble(unittest.TestCase):
    cs = WGC['cell_sweep']

    def test_every_cell_runs_the_same_timeline(self):
        self.assertEqual((self.cs['cell_count'], self.cs['all_ok'], self.cs['distinct_signatures']), (93, True, 1))
        acts = {}
        for c in self.cs['cells']:
            acts[c['act']] = acts.get(c['act'], 0) + 1
            s = c['summary']
            self.assertEqual((s['hold_first_offset'], s['hold_count'], s['break_offset'], s['replace_offset'], s['child_alloc_offset']), (1, 16, 17, 17, 18), c)
            self.assertEqual(s['player_y_held'], [c['hold_anchor_y']])
            self.assertEqual({(x['x_offset'], x['p_at_creation'], x['first_move_offset']) for x in s['shards']}, {(0, 3, 22), (8, 8, 27), (16, 5, 24), (24, 1, 20)})
        self.assertEqual(acts, {'thz1': 1, 'thz2': 1, 'sez1': 19, 'sez2': 16, 'sez3': 1, 'aqz1': 32, 'aqz2': 2, 'eez2': 21})

    def test_drop_reference_rows(self):
        d = WGC['drop_sez1_67_6']
        s = d['summary']
        self.assertEqual((s['spawn_update'], s['break_update'], s['player_y_at_spawn_end'], s['player_y_at_break_update']), (15, 32, 176, 174))
        self.assertEqual(s['player_y_after_break'], [181, 182, 184, 185])
        self.assertEqual(WGC['hold_ordering']['rows'][1:4], [[0, 176, 176], [1, 174, 176], [2, 174, 176]])
        self.assertEqual(WGC['hold_ordering']['rows'][-3], [17, 174, 174])

    def test_walk_off_hover(self):
        w = WGC['walk_off_ledge']
        self.assertEqual((w['spawn_updates'], w['break_updates'], w['hover_count'], w['held_anchor_y']), ([11, 19], [28, 36], 9, 304))
        self.assertEqual(w['hover_updates_left_of_both_cells_with_floor_flag'], list(range(28, 37)))

    def test_removal_branch_is_not_naturally_reachable(self):
        s = WGC['strip_speed_sweep']
        self.assertEqual(s['minimum_margin'], 8)
        for k, v in s['per_speed'].items():
            self.assertEqual(v['cells_replaced'], 6, k)
            self.assertTrue(all(m > 0 for m in v['object_x_minus_camera_x_at_break']), k)

    def test_bridge_and_rise(self):
        s = WGC['strip_run']
        self.assertEqual(s['spawn_to_replace'], [17] * 6)
        self.assertEqual({k: v for k, v in s['cells_60_to_69_after'].items() if k in ('62', '67')}, {'62': '0xB0', '67': '0xB0'})
        r = WGC['jump_up_through']
        self.assertEqual((r['handler_calls_while_rising'], r['spawns_while_rising'], r['first_spawn_update'], r['y_speed_at_spawn_update']), (10, [], 45, 0))

    def test_remembered_cell(self):
        r = WGC['revisit_same_cell']
        self.assertFalse(r['second_object_created'])
        self.assertEqual(r['spawn_updates'], [24])
        a = WGC['a_b_a']
        self.assertEqual((a['spawn_updates'], a['replace_updates']), ([5, 8, 12], [22, 25, 29]))
        self.assertEqual(a['d356_by_update'], {'3': 0, '8': a['cell_pointers']['B'], '12': a['cell_pointers']['A']})

    def test_removal_leaves_the_cell(self):
        for k in ('removed_by_camera', 'removed_asleep'):
            r = WGC[k]
            self.assertEqual((r['replace_events'], r['live_crumble_objects_at_end']), ([], 0), k)
        self.assertEqual(WGC['removed_by_camera']['cell_after_removal'], '0xAF')
        self.assertEqual(WGC['removed_by_camera']['d356_after'], WGC['removed_by_camera']['cell_pointer'])
        self.assertEqual(WGC['removed_by_camera']['new_objects_after_removal'], 0)

    def test_full_pool(self):
        p = WGC['full_pool']
        self.assertEqual((p['replace_events'], p['player_y_after'][:3], p['y_speed_after'], p['cell_after']), ([], [174, 174, 174], [0], '0xAF'))
        self.assertEqual((p['slot16_bytes_30_31_after_failed_spawn'], p['iy_after_failed_spawn']), ([68, 195], 0xD940))

    def test_persistence_and_restart(self):
        p = WGC['persistence']
        self.assertEqual((p['cell_while_far_away'], p['cell_after_return'], p['new_crumble_objects_after_return']), ('0xB0', '0xB0', 0))
        self.assertTrue(p['broken_cell_matches_b0_mapping'] and p['intact_af_neighbour_differs_from_b0'])
        r = WGC['restart_restores']
        self.assertEqual((r['cell_before_death'], r['cell_after_restart'], r['d356_after_restart']), ('0xB0', '0xAF', 0))
        self.assertTrue(r['level_clear_297e_called_at_update'])

    def test_state_scan(self):
        s = WGC['state_scan']
        self.assertEqual(s['handler_reached_states'], ['0x%02X' % x for x in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 14, 15, 16, 17, 18, 20, 21, 25, 26, 27, 28, 29, 30, 34)])
        for st in ('0x0C', '0x0D', '0x13', '0x16', '0x17', '0x18', '0x1F', '0x20', '0x21'):
            self.assertIn(st, s['handler_not_reached_states'])


class WholeGameBooster(unittest.TestCase):
    cs = WGB['cell_sweep']

    def test_every_pad_launches_the_same_way(self):
        self.assertEqual((self.cs['cell_count'], self.cs['all_left_ok'], self.cs['distinct_left_signatures']), (9, True, 1))
        for c in self.cs['cells']:
            self.assertEqual(c['left']['handler_count'], 5)
            self.assertEqual(c['left']['requested_after_first'], '0x10')
            self.assertEqual((c['left']['vx_after_first'], c['left']['d373_after_first'], c['left']['d503_after_first']), (1792, 1792, 2))
            self.assertEqual(c['right']['handler_count'], 1)
            self.assertIn(c['right']['x_offsets_from_cell_left_at_each_handler_update'][0], (30, 31))
            self.assertEqual(c['left']['vx_from_first_to_first_plus_8'][:6], [1792] * 5 + [1788])   # RIGHT held: -4 per update

    def test_placements(self):
        pl = [p for p in WGB['placements'] if p['act'].startswith('sez')]
        self.assertEqual([(p['act'], tuple(p['cell'])) for p in pl], [('sez2', (42, 17)), ('sez2', (84, 24)), ('sez3', (34, 7)), ('sez3', (72, 22))])
        for p in pl:
            self.assertEqual(p['ground_block_below'], '0x08')
            cx, cy = p['cell']
            self.assertEqual(p['trigger_anchor_x'], [cx * 32, cx * 32 + 31])
            self.assertEqual(p['standing_anchor_y_on_flat_ground_below'], cy * 32 + 14)

    def test_speed_table(self):
        t = WGB['speed_table']['entry_x_speed_8_8_to_result']
        self.assertTrue(all(v['handler_count'] == 5 and v['vx_after_first'] == 1792 for k, v in t.items() if int(k) >= 0))
        self.assertTrue(all(v['handler_count'] == 1 and v['vx_after_first'] == 1792 for k, v in t.items() if int(k) < 0))
        st = WGB['speed_table']['standing_start_center']
        self.assertEqual((st['handler_updates'], st['state_after_first'], st['state_next_update']), ([1, 2, 3], '0x05', '0x10'))

    def test_input_scripts_and_exit(self):
        i = WGB['input_scripts']
        for k in ('none', 'down', 'up'):
            self.assertEqual(i[k]['vx_at_updates']['4'], 1787)
        self.assertEqual(i['right']['vx_at_updates']['4'], 1788)
        self.assertEqual(i['left']['state_transitions_u_state_vx_x_y_f3_face'][2][1], '0x07')
        self.assertEqual(i['jump_press_u3_to_u5']['state_transitions_u_state_vx_x_y_f3_face'][2][1:3], ['0x0A', 1761])
        self.assertEqual(i['jump_press_u3_to_u5']['state_transitions_u_state_vx_x_y_f3_face'][2][5], 3)
        e = WGB['state10_exit']['per_input']
        self.assertEqual(e['none'][3][2:], ['0x10', '0x01'])
        self.assertEqual(e['down'][3][2:], ['0x10', '0x04'])
        self.assertEqual(e['left'][1][2:], ['0x10', '0x07'])

    def test_bridge(self):
        b = WGB['bridge']
        self.assertEqual((b['handler_updates'], b['spawn_to_replace'], b['never_fell_below_y']), ([25, 26, 27, 28, 29], [17, 17, 17, 17], 560))
        self.assertEqual(set(b['cells_44_to_47_after'].values()), {'0xB0'})

    def test_footwear(self):
        f = WGB['footwear']
        self.assertEqual(f['state_11_probe_parity_0']['state_sequence_first_6'][:2], ['0x11', '0x10'])
        self.assertEqual(f['state_11_probe_parity_0']['handler_updates'][:2], [1, 2])
        self.assertEqual(f['state_12_probe_parity_0']['handler_updates'], [])
        self.assertEqual(f['state_12_probe_parity_1']['handler_updates'], [1])
        self.assertEqual(f['state_14_probe_parity_0']['launched_updates'][:3], [1, 2, 3])

    def test_state_scan(self):
        s = WGB['state_scan']
        self.assertIn('0x12', s['handler_not_reached_states'])
        self.assertIn('0x22', s['handler_not_reached_states'])
        self.assertEqual(s['effect_applied_states'], ['0x%02X' % x for x in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 14, 15, 16, 20, 25, 26, 27, 28)])

    def test_effect5(self):
        e = WGB['effect5']
        self.assertEqual(e['copy_sequence_first_12'][:4], ['0x8DFD', '0x8DDD', '0x8DFD', '0x8DDD'])
        self.assertEqual((e['paused_while_d44e_nonzero_copies_in_30_frames'], e['resumed_after_clear_copies_in_30_frames']), (0, 10))
        self.assertEqual(e['first_calls_counter_phase_d455_d454'][:6], [[0, 0], [1, 0], [2, 0], [0, 1], [1, 1], [2, 1]])
        a = WGB['art']
        self.assertEqual((a['positions_of_tile_0x158_row_major_index'], a['blocks_that_draw_tile_0x158_in_sez2'], a['images_differ'], a['af_uses_tile_0x158']), (list(range(4, 12)), ['0xA7'], True, False))


class Contracts(unittest.TestCase):
    def test_crumble_contract_numbers(self):
        t = CC['object_13']['timeline_updates_relative_to_spawn_update_T']
        self.assertEqual((t['rider_hold_first'], t['rider_hold_count'], t['break_callback'], t['cell_replaced'], t['sound_a3_children_created_and_remove_callback']), (1, 16, 17, 17, 18))
        self.assertEqual(t['first_shard_move'], {'offset_0_p3': 22, 'offset_8_p8': 27, 'offset_16_p5': 24, 'offset_24_p1': 20})
        self.assertEqual(CC['identity']['replacement_block'], '0xB0')
        self.assertEqual(CC['trigger']['probe']['extra_by_state'], {'0x21': -14, '0x12': 8})
        self.assertEqual(CC['global_runtime']['cells'], 93)
        self.assertEqual(len(CC['cells']), 36)
        self.assertEqual(CC['update_order'][0], 'player_engine_64fa')

    def test_booster_contract_numbers(self):
        self.assertEqual((CB['effect']['x_speed_8_8'], CB['effect']['max_x_speed_d373'], CB['effect']['requested_state'], CB['effect']['sound_request_de04']), (0x700, 0x700, '0x10', '0xBD'))
        self.assertTrue(CB['direction']['fixed_rightward'])
        self.assertEqual(CB['global_runtime']['cells'], 9)
        self.assertEqual(len(CB['placements']), 4)
        self.assertEqual(CB['effect5_animation']['first_copy_image'], '0x8DFD')

    def test_every_viewport_row_is_classified(self):
        for c in (CC, CB):
            for row in c['viewport_classification']:
                self.assertTrue(row['class'])

    def test_table_vectors_match_the_models(self):
        tv = C['oracle_vectors']['table_vectors']
        for v in tv['crumble_handler_6b79']:
            i, e = v['input'], v['expect']
            m = S.handler_model(i['y_speed_high_byte_d519'], i['remembered_cell_equals_probed_cell'], set(i['occupied_slots_0_15']), i['cell_pointer'], 2160, 194, (i['y_speed_high_byte_d519'] << 8) | 0x34,
                                i['cell_pointer'] if i['remembered_cell_equals_probed_cell'] else i['cell_pointer'] - 1)
            self.assertEqual(e['y_speed_8_8'], m['d518'])
            self.assertEqual(e['remembered_cell_after'], m['d356'])
            self.assertEqual(e['spawned_slot'], None if m['spawn'] is None else m['spawn']['slot'])
        for v in tv['crumble_rider_a344']:
            self.assertEqual(v['expect']['hold_applied'], S.rider_model(v['input']['player_state_d501'], v['input']['movement_d503']))
        for v in tv['crumble_break_a36a']:
            i = v['input']
            self.assertEqual(v['expect']['outcome'], S.break_model(i['object_flags_04'], i['object_x'], i['object_x'] + i['camera_x_minus_object_x']))
        for v in tv['crumble_shard_schedule']:
            p = v['input']['parameter']
            self.assertEqual(v['expect']['y_after_each_pass_1_to_16'], [S.shard_model(p, n, 192) for n in range(1, 17)])
            self.assertEqual(v['expect']['first_move_pass'], p + 2)
        for v in tv['booster_handler_7646']:
            on = bool(v['input']['floor_flags_d522'] & 2)
            self.assertEqual(v['expect']['x_speed_8_8'], 0x700 if on else 0x1234)
            self.assertEqual(v['expect']['requested_state'], 0x10 if on else 7)
            self.assertEqual(v['expect']['sound_request_de04'], 0xBD if on else 0)
            self.assertEqual(v['expect']['movement_d503'], 2 if on else 1)
        for v in tv['booster_probe_753e']:
            i = v['input']
            inside_x = 0 <= i['anchor_x_minus_cell_left'] <= 31
            py = i['anchor_y_minus_cell_top'] + (-8 if not i['anim_counter_bit0_plus07'] else 2)
            inside = inside_x and 0 <= py <= 31
            self.assertEqual(v['expect']['handler_reached'], inside)
            self.assertEqual(v['expect']['launched'], inside and i['floor_flag'])
        for v in tv['crumble_trigger_floor_pass']:
            i = v['input']
            ins = 0 <= i['foot_row_in_cell'] <= 31
            self.assertEqual(v['expect']['handler_reached'], ins)
            self.assertEqual(v['expect']['spawned'], ins and i['y_speed_8_8'] >= 0 and not i['remembered_cell_equals_cell'])

    def test_trace_vectors(self):
        tvs = {t['id']: t for t in C['oracle_vectors']['trace_vectors']}
        self.assertEqual(len(tvs), 8)
        for t in tvs.values():
            self.assertTrue(t['rows'])
            self.assertTrue(all(len(r) == len(t['rows_columns']) for r in t['rows']))
        d = tvs['crumble_drop_sez1_67_6']
        evs = {r[0]: r[10] for r in d['rows']}
        self.assertIn('spawn13', evs[15])
        self.assertIn('13break', evs[32])
        self.assertTrue(all('13rider' in evs[u] for u in range(16, 32)))


@needs_rom
class RomRegions(unittest.TestCase):
    def test_region_hashes_match_the_rom(self):
        rows = {r['name']: r for r in S.region_table(ROM)}
        for r in D['static']['regions']:
            self.assertEqual(rows[r['name']]['sha256'], r['sha256'], r['name'])

    def test_static_and_census_regenerate(self):
        self.assertEqual(rt(S.static_facts(ROM)), D['static'])
        self.assertEqual(rt(S.census(ROM, S.all_layouts(ROM))), D['census'])
        self.assertEqual(rt(S.zone_gate_scan(ROM)), D['zone_gate_scan'])
        self.assertEqual(rt(S.contact_scan(ROM)), D['contact_scan'])


@needs_rom
class RomControlled(unittest.TestCase):
    def test_small_sweeps_regenerate(self):
        for fn, key in ((S.handler_matrix, 'handler_matrix'), (S.init_matrix, 'init_matrix'), (S.rider_matrix, 'rider_matrix'), (S.break_matrix, 'break_matrix'), (S.shard_matrix, 'shard_matrix'),
                        (S.lifecycle_check, 'lifecycle')):
            self.assertEqual(rt(fn(ROM)), CR[key], key)

    def test_booster_sweeps_regenerate(self):
        self.assertEqual(rt(S.booster_handler_matrix(ROM)), BO['handler_matrix'])
        self.assertEqual(rt(S.booster_probe_sweep(ROM)), BO['probe_sweep'])
        self.assertEqual(rt(S.block_a7_support(ROM)), BO['a7_support'])

    def test_crumble_trigger_and_posture_regenerate(self):
        self.assertEqual(rt(S.crumble_posture_independence(ROM)), CR['posture_independence'])
        self.assertEqual(rt(S.side_ceiling_sweeps(ROM)), CR['side_ceiling'])
        self.assertEqual(rt(S.crumble_trigger_sweep(ROM)), CR['trigger_sweep'])

    def test_vectors_regenerate(self):
        self.assertEqual(rt(S.table_vectors(ROM)), C['oracle_vectors']['table_vectors'])

    def test_object_pools(self):
        self.assertEqual(rt(S.pool_experiments(ROM)), CR['pools'])


@needs_rom
class RomWholeGame(unittest.TestCase):
    def test_drop_and_hold_reproduce(self):
        g = S.rig(ROM, 'sez1')
        rows = S.drop_on_cell(g, 67, 6, 128)
        self.assertEqual(rt(S.crumble_cell_summary(rows, 67, 6)), WGC['drop_sez1_67_6']['summary'])
        self.assertEqual(rt(S.timeline_signature(rows, 67, 6)), WGC['drop_sez1_67_6']['signature'])
        self.assertEqual(rt(S.compact_rows(rows, 8, 62, with_objs=True)), WGC['drop_sez1_67_6']['rows'])

    def test_history_independent_restore(self):
        """Regression for the hidden z80 prefix state: a run after an unrelated run must equal a fresh run."""
        g = S.rig(ROM, 'sez1')
        fresh = S.scenario_walk_off(g)
        S.drop_on_cell(g, 67, 6, 128)
        self.assertEqual(rt(S.scenario_walk_off(g)), rt(fresh))
        self.assertEqual(fresh['spawn_updates'], WGC['walk_off_ledge']['spawn_updates'])

    def test_named_scenarios_reproduce(self):
        g = S.rig(ROM, 'sez1')
        for key, fn in (('strip_run', S.scenario_strip_run), ('jump_up_through', S.scenario_jump_up_through), ('revisit_same_cell', S.scenario_revisit_same_cell), ('a_b_a', S.scenario_a_b_a), ('strip_speed_sweep', S.scenario_strip_speed_sweep),
                        ('removed_by_camera', S.scenario_removed_by_camera), ('removed_asleep', S.scenario_removed_asleep), ('full_pool', S.scenario_full_pool),
                        ('hold_ordering', S.scenario_hold_ordering)):
            self.assertEqual(rt(fn(g)), WGC[key], key)
        self.assertEqual(rt(S.scenario_restart_restores(g)), WGC['restart_restores'])
        self.assertEqual(rt(S.scenario_persistence(g, ROM)), WGC['persistence'])

    def test_booster_scenarios_reproduce(self):
        g = S.rig(ROM, 'sez2')
        self.assertEqual(rt(S.scenario_booster_bridge(g)), WGB['bridge'])
        self.assertEqual(rt(S.scenario_booster_speed_table(g)), WGB['speed_table'])
        self.assertEqual(rt(S.scenario_booster_input_scripts(g)), WGB['input_scripts'])
        self.assertEqual(rt(S.scenario_state10_exit(g)), WGB['state10_exit'])
        self.assertEqual(rt(S.scenario_booster_footwear(g)), WGB['footwear'])

    def test_one_pad_of_each_act_family(self):
        lays = S.all_layouts(ROM)
        got = S.booster_cell_sweep(ROM, {k: lays[k] for k in ('sez2', 'aqz2')})
        self.assertEqual(got['distinct_left_signatures'], 1)
        want = [c for c in WGB['cell_sweep']['cells'] if c['act'] in ('sez2', 'aqz2')]
        self.assertEqual(rt(got['cells']), want)

    def test_effect5_regenerates(self):
        self.assertEqual(rt(S.effect5_timeline(ROM)), WGB['effect5'])
        self.assertEqual(rt(S.booster_art_facts(ROM)), WGB['art'])
        self.assertEqual(rt(S.update_order_trace(ROM)), CR['update_order'])


if __name__ == '__main__':
    unittest.main()
