"""MGHZ surface $1B (oil) and ceiling-spike ($3E/$3F) audit: cache locks plus ROM-backed re-execution of the original routines.

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
import mghz_surface_ceiling as M
import level_package as L
import rom as R

ROM_SHA = 'eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607'
D = json.loads(M.OUTPUT.read_text(encoding='utf-8'))


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


class CacheIdentity(unittest.TestCase):
    def test_identity_and_scope(self):
        self.assertEqual(D['rom_sha256'], ROM_SHA)
        self.assertTrue(D['research_only'] and D['poc_untouched'])
        self.assertEqual(D['scope']['out'], ['$24', '$2E', 'footwear', 'boss $56'])
        self.assertGreater(D['counts']['controlled_cases_total'], 590000)


class StaticFacts(unittest.TestCase):
    s = D['static']

    def test_dispatch_and_chain(self):
        t = self.s['floor_dispatch_table_6973']
        self.assertEqual((t['surface_$1B'], t['surface_$00'], t['surface_$06'], t['surface_$07'], t['surface_$05']), ('0x6B14', '0x6C45', '0x6C4D', '0x6C4D', '0x6ACE'))
        self.assertEqual(self.s['ceiling_dispatch_chain'][-1], ['0x05', '0x74E7'])

    def test_blocks(self):
        h = self.s['block_headers']
        self.assertEqual((h['0xA0']['flags'], h['0xA0']['modifier'], h['0xA0']['vertical_profile_runs_by_x'], h['0xA0']['horizontal_profile_runs_by_y']),
                         ('0x5B', 0, [[0, 31, '0x20']], [[0, 31, '0x40']]))
        for b in ('0x3E', '0x3F'):
            self.assertEqual((h[b]['flags'], h[b]['vertical_profile_runs_by_x'], h[b]['horizontal_profile_runs_by_y']), ('0x85', [[0, 31, '0x58']], [[0, 15, '0x60'], [16, 31, '0x40']]))
        self.assertTrue(all(self.s['blocks_3e_3f_header_fields_identical'].values()))
        self.assertTrue(self.s['oil_block_is_the_only_surface_1b_block'])
        art = self.s['block_art_attribute_words']
        self.assertNotEqual(art['0x3E'], art['0x3F'])

    def test_sink_branch_B_register(self):
        b = self.s['sink_branch_B_register']
        self.assertEqual(b['oil_block_B'], 146)
        self.assertGreaterEqual(b['min_over_all_256_blocks'], 128)
        self.assertEqual(b['min_over_bit6_only_blocks'], 146)

    def test_bit_and_counter_sites(self):
        s = self.s['bit_and_counter_sites']
        self.assertEqual([(x['op'], x['cpu']) for x in s['plus24_bit_instructions']['bit1']], [('SET 1,(IX+$24)', '0x6B14'), ('RES 1,(IX+$24)', '0x6C49'), ('BIT 1,(IX+$24)', '0x6FC7')])
        self.assertEqual(len(s['d3bc_operands']), 9)
        self.assertTrue(all(x['role'] != 'UNCLASSIFIED' for x in s['d3bc_operands']))
        self.assertEqual([x['cpu'] for x in s['d3bc_operands'] if 'ONLY numeric read' in x['role']], ['0x703E'])

    def test_foot_probe(self):
        f = self.s['foot_probe']
        self.assertTrue(f['bytes_match_expected_pattern'])
        self.assertEqual(f['extra_y_by_current_state'], {'0x21': -14, '0x12': 8})


class SurfaceModelLocks(unittest.TestCase):
    s = D['surface_1b']

    def test_parity_and_gate(self):
        self.assertEqual((self.s['sink_parity']['cases'], self.s['sink_parity']['projected_cases'], self.s['sink_parity']['mismatches']), (88560, 42456, 0))
        self.assertEqual(len(self.s['sink_parity']['per_block']), 24)
        self.assertEqual((self.s['gate_matrix']['cases'], self.s['gate_matrix']['model_mismatches']), (336, 0))
        sm = self.s['gate_matrix']['summary']
        self.assertEqual(sm['prev=0x5B p24=2 req=0x05']['sink_branch_reached_in'], 6)
        self.assertEqual(sm['prev=0x5B p24=2 req=0x14']['model'], 'sink')
        self.assertEqual(sm['prev=0x5B p24=3 req=0x14']['model'], 'strip_fall_no_support')
        self.assertEqual(sm['prev=0x81 p24=2 req=0x05']['sink_branch_reached_in'], 0)
        self.assertEqual(sm['prev=0x5B p24=0 req=0x05']['sink_branch_reached_in'], 0)

    def test_steady_state_and_runaway(self):
        c = self.s['steady_state']['cases']
        self.assertEqual(c['integration_7']['first_runaway_counter'], 25)
        self.assertEqual(c['integration_9']['first_runaway_counter'], 23)
        self.assertEqual(c['integration_7']['anchor_y_after_projection_by_counter_0_to_24'], list(range(778, 803)))
        rows = c['integration_7']['rows_around_runaway_[counter,anchor_before,anchor_after,step,floor]']
        self.assertIn([25, 803, 835, 32, True], rows)

    def test_stale_bit(self):
        r = self.s['stale_bit_one_way']['results']
        for blk in ('0x0D', '0x0F', '0xF9'):
            f = r[blk]['final_anchor_y_minus_surface_anchor']
            self.assertEqual(f['bit1_clear'], [-3, 0, 0, 0, 0, 20])
            self.assertEqual(f['bit1_set_k0'], [-3, -4, -4, -4, -4, -4])
            self.assertEqual(f['bit1_set_k10'], [-3, 6, 6, 6, 6, 6])
            self.assertEqual(f['bit1_set_k25'], [-3, 21, 21, 21, 21, 21])

    def test_whole_game_fixtures(self):
        w = self.s['whole_game']
        f1, f2 = w['fall_in']['mghz1'], w['fall_in']['mghz2']
        self.assertEqual((f1['first_oil_handler_update'], f1['plunge_update'], f1['plunge_counter'], f1['death_request_update']), (25, 129, 25, 133))
        self.assertEqual(f1['plunge_y_path'], [803, 835, 867, 899, 932, 932])
        self.assertEqual(f1['death_screen_y_before'], 220)
        self.assertEqual([r['y'] for r in f1['landing_rows'][1:3]], [783, 778])
        self.assertEqual((f2['first_oil_handler_update'], f2['plunge_counter'], f2['plunge_y_path'][:3]), (26, 25, [931, 963, 995]))
        for r in w['walk_in']['mghz1'] + w['walk_in']['mghz2']:
            self.assertEqual(r['plunge_counter'], 25, r['label'])
            self.assertTrue(r['counter_increment_d12f_low2_all_zero'], r['label'])
        for f in (f1, f2):
            self.assertTrue(f['counter_increment_d12f_low2_all_zero'])
            self.assertTrue(all(g % 4 == 0 for g in f['counter_increment_d12f_gaps_first8']))
        for v in w['speed_control'].values():
            self.assertTrue(v['vx_identical_first40'] and v['x_identical_first40'])
        for v in w['direction_independence'].values():
            self.assertEqual(v['plunge_counter'], 25)
        self.assertEqual(w['roll_on_oil']['states_seen'], ['0x09'])
        self.assertEqual(w['roll_on_oil']['f3_values_seen'], ['0x02'])
        self.assertEqual(w['after_death']['at_death'], {'counter': 26, 'plus24': 2, 'state': 31})
        self.assertEqual((w['after_death']['after_restart']['counter'], w['after_death']['after_restart']['plus24']), (0, 0))

    def test_jump_and_escape(self):
        w = self.s['whole_game']
        for j in w['jump_cycle']:
            self.assertTrue(j['jump_taken'] and j['counter_reset_by_jump_setter'])
            self.assertEqual((j['rise_px'], j['f3_first']), (46, 3))
        esc = {e['counter_at_jump']: e['reached_far_rim'] for e in w['escape_over_far_rim']}
        self.assertTrue(all(esc[k] for k in (0, 8, 14, 18, 20, 22, 23)))
        self.assertFalse(esc[24] or esc[26])

    def test_state_coverage(self):
        scan = self.s['whole_game']['state_scan_first_update']
        got = sorted(int(k, 16) for k, v in scan.items() if v['oil_handler'])
        self.assertEqual(got, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 14, 15, 16, 17, 18, 20, 21, 25, 26, 27, 28, 29, 30, 34])
        for s in (0x0C, 0x0D, 0x13, 0x1F, 0x20):
            self.assertFalse(scan[f'0x{s:02X}']['oil_handler'])


class CeilingLocks(unittest.TestCase):
    c = D['ceiling_spikes']

    def test_gate_rule(self):
        g = self.c['gate_summary']
        self.assertTrue(g['rule_holds_for_every_combination_and_both_blocks'])
        self.assertTrue(g['blocks_3e_and_3f_give_identical_results_in_every_combination'])
        self.assertEqual(g['damage_rectangle_anchor_relative_to_cell_origin'], {'x': [0, 31], 'y': [6, 30]})
        self.assertEqual(self.c['gate_sweep']['cases'], 408576)
        hit = self.c['gate_sweep']['results']['0x3F']
        self.assertEqual(hit['vy=rising_-1.0|floor=0|owner=0|invulnerable=0|state=0x0A']['hurt'], [[0, 31, 6, 30]])
        self.assertEqual(hit['vy=rising_-1.0|floor=0|owner=0|invulnerable=1|state=0x0A']['hurt'], [])
        self.assertEqual(hit['vy=rising_-1.0|floor=0|owner=0|invulnerable=1|state=0x0A']['ordinary_bounce_path'], [[0, 31, 6, 30]])
        self.assertEqual(hit['vy=zero|floor=0|owner=0|invulnerable=0|state=0x0A']['hurt'], [])
        self.assertEqual(hit['vy=rising_-1.0|floor=1|owner=0|invulnerable=0|state=0x0A']['hurt'], [])
        self.assertEqual(hit['vy=zero|floor=1|owner=9|invulnerable=0|state=0x0A']['hurt'], [[0, 31, 6, 30]])
        self.assertEqual(hit['vy=rising_-1/256|floor=0|owner=0|invulnerable=0|state=0x1E']['hurt'], [])

    def test_real_runs(self):
        self.assertEqual(len(self.c['real_runs_check']['results']), 4)
        self.assertTrue(all(v['matches'] for v in self.c['real_runs_check']['results'].values()))
        runs = D['placements']['ceiling_spike_runs']
        self.assertEqual([(r['block'], r['cells']) for r in runs['mghz1']], [('0x3E', [4, 6, 15])])
        self.assertEqual([(r['block'], r['cells']) for r in runs['mghz2']], [('0x3F', [27, 43, 11]), ('0x3F', [87, 87, 16]), ('0x3F', [107, 113, 21])])
        self.assertEqual(runs['mghz3'], [])
        self.assertEqual(sum(r['count'] for r in runs['mghz2']), 25)
        self.assertTrue(all(r['above_is_solid'] and r['below_is_air'] for a in runs.values() for r in a))

    def test_foot_and_side(self):
        f = self.c['foot_sweep']
        self.assertTrue(f['blocks_3e_3f_identical'])
        self.assertEqual(f['results']['prev=solid_81|floor=0|vy=zero']['hurt'], [[0, 31, 8, 31]])
        self.assertEqual(f['results']['prev=none_00|floor=0|vy=zero']['hurt'], [])
        self.assertEqual(f['results']['prev=solid_81|floor=0|vy=rising_-1.0']['hurt'], [])
        self.assertEqual(f['results']['prev=none_00|floor=1|vy=zero']['hurt'], [[0, 31, 0, 31]])
        s = self.c['side_sweep']
        self.assertTrue(s['blocks_3e_3f_identical'])
        self.assertEqual(s['results']['0x3F']['side_damage_cases'], 0)
        self.assertEqual(s['results']['0x3F']['right_probe_pushes_[dx,dx,probe_row,probe_row]'], [[-8, 11, 0, 15]])
        self.assertEqual(self.c['full_pass_versus_isolated']['only_in_isolated_pass'], [[0, 31, 6, 9]])
        self.assertEqual(self.c['full_pass_versus_isolated']['only_in_full_pass'], [])

    def test_whole_game(self):
        w = self.c['whole_game']
        five = [r for r in w['hit_5_rings']['rows_around_hurt'] if 'hurt' in r['ev']][0]
        self.assertEqual((five['u'], five['y'], five['vy'], five['vx'], five['req'], five['rings'], five['d3b1'], five['f22']), (7, 382, 256, -256, 30, 0, 119, 1))
        zero = [r for r in w['hit_0_rings']['rows_around_hurt'] if 'hurt' in r['ev']][0]
        self.assertEqual((zero['y'], zero['vy'], zero['req']), (382, -1280, 31))
        self.assertTrue(w['hit_with_power_up_invincibility']['hurt_reached'])
        inv = w['hit_while_invulnerable']
        self.assertFalse(inv['hurt_reached'])
        self.assertEqual((inv['bounce_update'], inv['anchor_y_at_bounce']), (7, 382))
        self.assertEqual([r['vy'] for r in inv['rows_around_bounce'] if 'bounce' in r['ev']], [256])
        nm = w['near_miss']
        self.assertEqual((nm['apex_y'], nm['head_probe_rows_at_apex'], nm['type5_tail_updates'], nm['hurt'], nm['ceiling_bounce']), (383, 25, 8, False, False))
        self.assertFalse(w['falling_through']['hurt'])
        st = w['stomp_bounce_state_0b_launch']
        self.assertEqual((st['hurt_update'], st['anchor_y_at_hurt'], st['rise_px_before_hurt']), (37, 382, 184))

    def test_state_scan(self):
        scan = self.c['whole_game']['state_scan_three_updates']
        ran = sorted(int(k, 16) for k, v in scan.items() if v['ceiling_type5_reached_in_state'])
        self.assertEqual(ran, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 14, 15, 16, 17, 18, 20, 21, 25, 26, 27, 28, 29, 30])
        self.assertFalse(scan['0x1E']['hurt_in_state'])
        self.assertTrue(scan['0x1A']['ordinary_bounce_in_state'])
        self.assertTrue(scan['0x11']['hurt_in_state'])
        for s in (0x0C, 0x0D, 0x13, 0x22, 0x20):
            self.assertFalse(scan[f'0x{s:02X}']['ceiling_type5_reached_in_state'])


class PlacementsAndExamples(unittest.TestCase):
    def test_oil_pits(self):
        o = D['placements']['oil']
        self.assertEqual((o['mghz1']['oil_cells'], o['mghz2']['oil_cells'], o['mghz3']['oil_cells']), (70, 42, 0))
        p1, p2 = o['mghz1']['pits'][0], o['mghz2']['pits'][0]
        self.assertEqual((p1['cells'], p1['world_rect'], p1['oil_top_world_y'], p1['anchor_y_standing_at_counter_0']), ([42, 51, 25, 31], [1344, 800, 1663, 1023], 800, 778))
        self.assertEqual((p2['cells'], p2['world_rect'], p2['oil_top_world_y'], p2['anchor_y_standing_at_counter_0']), ([7, 20, 29, 31], [224, 928, 671, 1023], 928, 906))
        for p in (p1, p2):
            self.assertEqual(p['blocks_in_row_above_oil'], ['0x9E'])
            self.assertEqual(p['row_above_oil_collision'], ['0x00'])
            self.assertEqual(p['roof_cells_in_row_above'], [])

    def test_examples(self):
        e = D['examples']
        self.assertEqual(e['oil']['mghz1']['fixtures'][0]['place'], {'x': 1503, 'y': 722, 'state': '0x0E'})
        self.assertEqual(e['oil']['mghz1']['fixtures'][0]['expect']['plunge_anchor_y_path'][:3], [803, 835, 867])
        self.assertEqual(e['ceiling_spikes']['mghz2'][0]['hazard_anchor_x'], [864, 1407])
        self.assertEqual(e['ceiling_spikes']['mghz2'][0]['hazard_anchor_y'], [358, 382])
        self.assertEqual(e['ceiling_spikes']['mghz1'][0]['hazard_anchor_y'], [486, 510])

    def test_neighbours(self):
        n = D['placements']['hazard_neighbour_objects']['results']
        pit1 = [r for r in n['mghz1'] if r['kind'] == 'oil_pit'][0]
        self.assertIn({'type': '0x28', 'parameter': '0x89', 'world': [1360, 750]}, pit1['nearby_objects'])
        run = [r for r in n['mghz2'] if r['kind'] == 'ceiling_spike_run'][0]
        self.assertEqual(sorted(o['world'] for o in run['nearby_objects'] if o['type'] == '0x21'), [[1040, 590], [1232, 590]])


@unittest.skipIf(ROM is None, 'canonical local ROM unavailable')
class RomBackedStatic(unittest.TestCase):
    def test_static_facts_match_cache(self):
        self.assertEqual(json.loads(json.dumps(M.static_facts(ROM))), D['static'])

    def test_regions_and_bytes(self):
        self.assertEqual(ROM[0x6B14:0x6B23].hex(), 'ddcb24ce3a2fd1e603c021bcd334c9')
        self.assertEqual(ROM[0x6C45:0x6C4D].hex(), 'ddcb2486ddcb248e')
        self.assertEqual(ROM[0x73E0:0x73E3].hex(), '11e8ff')
        self.assertEqual(ROM[0x6FC7:0x6FCE].hex(), 'ddcb244ec21070')

    def test_placements_match_cache(self):
        self.assertEqual(json.loads(json.dumps(M.oil_pits(ROM))), D['placements']['oil'])
        self.assertEqual(json.loads(json.dumps(M.ceiling_runs(ROM))), D['placements']['ceiling_spike_runs'])


@unittest.skipIf(ROM is None, 'canonical local ROM unavailable')
class RomBackedControlled(unittest.TestCase):
    def test_sink_model_parity(self):
        self.assertEqual(json.loads(json.dumps(M.sink_parity(ROM))), D['surface_1b']['sink_parity'])

    def test_gate_and_steady(self):
        self.assertEqual(json.loads(json.dumps(M.gate_matrix(ROM))), D['surface_1b']['gate_matrix'])
        self.assertEqual(json.loads(json.dumps(M.steady_state(ROM))), D['surface_1b']['steady_state'])
        self.assertEqual(json.loads(json.dumps(M.stale_bit_one_way(ROM))), D['surface_1b']['stale_bit_one_way'])

    def test_ceiling_rule_and_blocks_identical(self):
        sweep = M.ceiling_gate_sweep(ROM)
        summ = M.ceiling_gate_summary(sweep)
        self.assertEqual(json.loads(json.dumps(summ)), D['ceiling_spikes']['gate_summary'])
        self.assertTrue(summ['rule_holds_for_every_combination_and_both_blocks'])

    def test_real_runs_and_foot_side(self):
        self.assertEqual(json.loads(json.dumps(M.ceiling_real_runs_check(ROM))), D['ceiling_spikes']['real_runs_check'])
        self.assertEqual(json.loads(json.dumps(M.ceiling_foot_sweep(ROM))), D['ceiling_spikes']['foot_sweep'])
        self.assertEqual(json.loads(json.dumps(M.ceiling_side_sweep(ROM))), D['ceiling_spikes']['side_sweep'])


@unittest.skipIf(ROM is None, 'canonical local ROM unavailable')
class RomBackedWholeGame(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g1 = M.GameLab(ROM, 'mghz1')
        cls.g2 = M.GameLab(ROM, 'mghz2')

    def test_oil_fall_in(self):
        self.assertEqual(json.loads(json.dumps(M.scenario_fall_in(self.g1))), D['surface_1b']['whole_game']['fall_in']['mghz1'])

    def test_oil_speed_control_and_roll(self):
        self.assertEqual(json.loads(json.dumps(M.scenario_speed_control(self.g1))), D['surface_1b']['whole_game']['speed_control'])
        self.assertEqual(json.loads(json.dumps(M.scenario_roll_on_oil(self.g1))), D['surface_1b']['whole_game']['roll_on_oil'])

    def test_escape_threshold(self):
        got = {k: M.scenario_escape(self.g1, k)['reached_far_rim'] for k in (22, 23, 24)}
        self.assertEqual(got, {22: True, 23: True, 24: False})

    def test_ceiling_hits(self):
        w = D['ceiling_spikes']['whole_game']
        self.assertEqual(json.loads(json.dumps(M.scenario_ceiling_hit(self.g2, 5, '5 rings (BCD 05)'))), w['hit_5_rings'])
        self.assertEqual(json.loads(json.dumps(M.scenario_ceiling_hit(self.g2, 0, '0 rings'))), w['hit_0_rings'])
        self.assertEqual(json.loads(json.dumps(M.scenario_ceiling_near_miss(self.g2))), w['near_miss'])
        self.assertEqual(json.loads(json.dumps(M.scenario_ceiling_spring_launch(self.g2))), w['stomp_bounce_state_0b_launch'])


if __name__ == '__main__':
    unittest.main()
