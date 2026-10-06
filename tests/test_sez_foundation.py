"""Focused SEZ foundation / object-census locks and original-ROM checks; never touches POC.

Boundary-dependent mechanics are swept exhaustively against the original routines (counted in CHECKS).
"""
import hashlib
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import sez_foundation as F
import sez_object_census as C
import sez_art_approval as AA
import level_package as L
import rom as R
from oracle import Oracle

CHECKS = {}


def tally(name, n=1):
    CHECKS[name] = CHECKS.get(name, 0) + n


def tearDownModule():
    print('\nSEZ exhaustive/boundary checks:', json.dumps(CHECKS, sort_keys=True), 'total', sum(CHECKS.values()))


EXPECTED = {  # (cells), player, camera, runtime cells, distinct blocks, terrain ring quadrants
    'sez1': ((128, 32), (110, 718), (0, 608), 4095, 57, 54),
    'sez2': ((128, 32), (110, 846), (0, 742), 4095, 56, 180),
    'sez3': ((128, 32), (110, 821), (0, 702), 4095, 53, 42)}
OBJECT_COUNTS = {'sez1': 39, 'sez2': 33, 'sez3': 5}
ROM_PATH = Path(os.environ.get('SONIC_CHAOS_ROM', str(ROOT.parent / 'source/Sonic Chaos (Europe).sms')))
VIEWPORT_CLASSES = {'WORLD', 'EDGE', 'CENTER', 'PLAYER_DIST', 'LOCKED_CAMERA', 'PLAYER_DIST/WORLD', 'UNRESOLVED'}


class CacheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f = json.loads(F.OUTPUT.read_text(encoding='utf-8'))
        cls.c = json.loads(C.OUTPUT.read_text(encoding='utf-8'))
        cls.a = json.loads(AA.CACHE.read_text(encoding='utf-8'))

    def test_rom_hash_and_scope(self):
        for d in (self.f, self.c, self.a):
            self.assertEqual(d['rom_sha256'], 'eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607')
        self.assertEqual(self.f['research_base'], 'e0f42f89a6ecabd6ed504ef318ea8170ce1a3f1f')
        self.assertEqual(self.f['zone']['index'], 2)

    def test_dimensions_starts_bounds(self):
        for k, e in EXPECTED.items():
            a = self.f['acts'][k]
            self.assertEqual(a['dimensions_pixels'], [v * 32 for v in e[0]])
            self.assertEqual(a['start']['player_anchor'], list(e[1]))
            self.assertEqual(a['start']['camera'], list(e[2]))
            self.assertEqual(a['layout']['runtime_written_cells'], e[3])
            self.assertEqual(a['census']['distinct_layout_blocks'], e[4])
            self.assertEqual(len(a['rings']['terrain']), e[5])
            self.assertEqual(a['census']['object09_rings'], 0)
            self.assertTrue(all(a['descriptor']['consistency'].values()))
            self.assertEqual(a['descriptor']['header']['block_mapping_bank'], 0x11)
            self.assertEqual(a['bounds']['camera_max_words'], [3840, 784])
            self.assertEqual(a['bounds']['camera_min_words'], [0, 8])
            tally('act_metadata', 8)

    def test_unloaded_final_cell_in_every_act(self):
        for k in EXPECTED:
            self.assertEqual([c['layout_index'] for c in self.f['acts'][k]['layout']['unloaded_cells']], [4095])
            self.assertEqual(self.f['acts'][k]['layout']['encoded_cells'], 4096)

    def test_mapping_pointer_is_not_aligned_and_verified(self):
        m = self.f['mapping_pointer']
        for k, a in m['acts'].items():
            self.assertEqual((a['bank'], a['table_cpu'], a['table_rom']), (0x11, 0xAA40, 0x46A40))
            self.assertEqual(a['table_offset_inside_bank'], 0x2A40)
            self.assertFalse(a['masked_by_alignment'])
            self.assertEqual((a['original_consumer_checks'], a['original_consumer_mismatches']), (512, 0))
            self.assertEqual(a['blocks_where_historical_formula_reads_different_bytes'], 256)
            self.assertNotEqual(a['resolved_offsets_sha256'], a['historical_wrong_offsets_sha256'])
        self.assertTrue(m['tables_identical_across_acts'])
        self.assertIn('does NOT inherit', m['verdict'])

    def test_every_exported_block_uses_bank_relative_mapping(self):
        for k, act in self.f['acts'].items():
            for b in act['blocks']:
                mp = b['mapping']
                self.assertEqual(mp['rom'], 0x44000 + mp['cpu'] - 0x8000)
                self.assertEqual(mp['pointer_entry_rom'], 0x46A40 + 2 * b['block_id'])
                self.assertEqual(len(mp['attributes']), 16)
                self.assertNotEqual(b['mapping_sha256'], hashlib.sha256(bytes(64)).hexdigest())
                tally('block_bank_relative')

    def test_surfaces(self):
        s = self.f['surface_census']['sez_surfaces']
        self.assertEqual(sorted(s), ['0x00', '0x01', '0x02', '0x03', '0x05', '0x07', '0x09', '0x0A', '0x0C', '0x0D', '0x12', '0x14', '0x16', '0x1A'])
        self.assertEqual({k for k, v in s.items() if v['status'] == 'NEW_NEEDS_AUDIT'}, {'0x0C', '0x1A'})
        self.assertEqual(s['0x0C']['blocks'], ['0xAF'])
        self.assertEqual(s['0x0C']['cells'], {'sez1': 19, 'sez2': 16, 'sez3': 1})
        self.assertEqual(s['0x1A']['blocks'], ['0xA7'])
        self.assertEqual(s['0x1A']['cells'], {'sez1': 0, 'sez2': 2, 'sez3': 2})
        self.assertEqual(s['0x0D']['cells'], {'sez1': 145, 'sez2': 100, 'sez3': 8})
        self.assertEqual(s['0x05']['blocks'], ['0x3D'])
        self.assertEqual(s['0x16']['blocks'], ['0x47'])
        self.assertEqual(s['0x12']['blocks'], ['0x1F', '0x23'])
        for act in self.f['acts'].values():
            self.assertFalse(any(b['alternate_plane_header_differs'] for b in act['blocks']))
        absent = self.f['surface_census']['six_zone_cell_counts']
        for gone in ('0x17', '0x19', '0x1B', '0x1C', '0x13'):
            self.assertFalse(any(k.startswith('sez') for k in absent.get(gone, {})), gone)

    def test_dispatch_chains(self):
        c = self.f['surface_census']['consumers']
        self.assertEqual([x[0] for x in c['side_right_chain']['entries']], ['0x05', '0x0D', '0x13', '0x16'])
        self.assertEqual([x[0] for x in c['ceiling_chain']['entries']], ['0x0D', '0x15', '0x14', '0x13', '0x05'])
        h = c['floor_dispatch_table']['handlers']
        self.assertEqual((h['0x0C'], h['0x12'], h['0x16'], h['0x1A']), ('0x6B79', '0x69B2', '0x6AE3', '0x69B1'))

    def test_collision_table_is_zone_independent(self):
        self.assertEqual(self.f['collision_table']['collision_table_cpu_all_zones'], ['0x8000'])

    def test_ring_animation_and_effect_5(self):
        t = self.f['terrain_ring_animation']
        self.assertEqual((t['source_bank_cpu'], t['vram_destination'], t['tile_ids']), ('0x1D:0x855D', 0x29A0, [333, 334, 335, 336]))
        self.assertTrue(t['per_act_descriptors_identical'])
        e = self.f['level_effects']
        self.assertEqual(e['descriptor_effect_ids'], [5, 0, 0, 0])
        x = e['effects']['5']
        self.assertEqual((x['routine_cpu'], x['events_in_48_updates'], x['events_with_D44E_nonzero_in_48_updates']), ('0x81BF', 16, 0))
        self.assertEqual(x['update_period'], [3, 3, 3, 3])
        self.assertEqual(x['zone_table']['zone2'], ['0x820B', '0x8218'])
        self.assertEqual(x['zone_gating_events_in_48_updates'], {'zone0': 0, 'zone1': 0, 'zone2': 16, 'zone3': 0, 'zone4': 16, 'zone5': 16})
        self.assertEqual([f['vram'] for f in x['frames']], [0x2B00, 0x2B00])
        for k, a in self.f['acts'].items():
            self.assertEqual(a['animated_terrain_blocks']['0x158'], [] if k == 'sez1' else ['0xA7'])

    def test_zone_dependent_code_has_no_zone_2_gate(self):
        z = self.f['zone_dependent_code']
        self.assertEqual(z['zone_2_gates'], [])
        gates = {s['cpu']: s['constant'] for s in z['sites'] if s['kind'] == 'compare'}
        self.assertTrue(gates)
        self.assertNotIn(2, gates.values())
        self.assertEqual(gates['0x6A5D'], 5)
        tally('zone_gate_sites', len(z['sites']))

    def test_controlled_handlers_recorded(self):
        h = self.f['surface_census']['controlled_handlers']
        c = h['surface_0c_handler_6b79']
        self.assertEqual((c['first_call']['type'], c['objects_after_first_call'], c['objects_after_repeat_same_cell'],
                          c['objects_after_new_cell_with_player_+19_bit7_set']), (0x13, 1, 1, 1))
        b = h['surface_1a_handler_7646']
        self.assertEqual((b['floor_bit_set']['d373'], b['floor_bit_set']['requested_state_02'], b['floor_bit_set']['sound_de04']), (0x700, 0x10, 0xBD))
        self.assertEqual(b['floor_bit_clear']['requested_state_02'], 5)

    def test_environment_statements(self):
        e = self.f['environment']
        self.assertIn('not present', e['water'])
        self.assertIn('no SEZ block has a distinct alternate-plane header', e['loop_or_plane_switching'])

    def test_object_records(self):
        for k, n in OBJECT_COUNTS.items():
            a = self.c['acts'][k]
            self.assertEqual(a['record_count'], n)
            raw = b''.join(bytes.fromhex(r['raw_bytes'].replace(' ', '')) for r in a['records'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), a['records_sha256'])
            for i, r in enumerate(a['records'], 1):
                self.assertEqual(r['index'], i)
                self.assertEqual((r['world_x'], r['world_y']), (r['stored_x'] - 256, r['stored_y'] - 256))
                self.assertIn(r['classification'], C.CLASSES)
                self.assertTrue(r['inside_map'])
                tally('object_records')
            self.assertEqual(a['off_map_records'], [])
        self.assertEqual(self.c['acts']['sez1']['type_counts'], {'0x10': 6, '0x18': 1, '0x1B': 2, '0x20': 4, '0x23': 4, '0x26': 9, '0x28': 5, '0x2F': 8})
        self.assertEqual(self.c['acts']['sez2']['type_counts'], {'0x10': 5, '0x18': 1, '0x1B': 2, '0x20': 3, '0x23': 4, '0x26': 12, '0x28': 2, '0x2F': 4})
        self.assertEqual(self.c['acts']['sez3']['type_counts'], {'0x10': 2, '0x26': 1, '0x2F': 1, '0x54': 1})

    def test_classification_counts(self):
        cc = {k: v['classification_counts'] for k, v in self.c['acts'].items()}
        self.assertEqual(cc['sez3'], {'BOSS_SUPPORT': 1, 'SHARED_RECOVERED': 3, 'SHARED_WITH_SEZ_DATA': 1})
        self.assertEqual(cc['sez1'].get('SEZ_SPECIFIC_NEEDS_AUDIT'), 8)        # $20 x4, $23 x4; platform S3 closed
        self.assertEqual(cc['sez2'].get('SEZ_SPECIFIC_NEEDS_AUDIT'), 7)        # $20 x3, $23 x4; platform S3 closed

    def test_six_zone_census(self):
        t = self.c['six_zone_reuse_census']['types']
        for new in ('0x20', '0x23', '0x54'):
            self.assertEqual(t[new]['zones'], ['sez'])
            self.assertEqual(t[new]['buys_other_zone_coverage'], [])
        self.assertEqual(t['0x2F']['zones'], ['mghz', 'sez'])
        self.assertEqual(t['0x26']['zones'], ['eez', 'gpz', 'sez', 'thz'])
        self.assertEqual(t['0x13']['spawned_by_types'], ['0x13'])
        self.assertEqual(t['0x55']['spawned_by_types'], ['0x54'])

    def test_shared_reuse_proof(self):
        p = self.c['shared_reuse_proof']
        for t in ('0x10', '0x1B', '0x26', '0x2F'):
            self.assertTrue(p[t]['all_compositions_identical'], t)
        self.assertFalse(p['0x28']['all_compositions_identical'])
        self.assertIn('visual approval required', p['0x28']['art_verdict'])
        for t in ('0x10', '0x1B', '0x26', '0x28', '0x2F'):
            for cm in p[t]['comparisons']:
                self.assertFalse(cm['sprite_palette']['cram_identical'])          # zone sprite palettes differ: colours are new data
                self.assertEqual(cm['frames'][0]['composition_identical'], True)  # frame 0 is the empty frame
        self.assertEqual([cm['reference_match'] for cm in p['0x2F']['comparisons']], ['different_base'])
        self.assertEqual(p['0x2F']['comparisons'][0]['reference_bases'], ['0xAC', '0xAC'])
        self.assertEqual(p['0x18']['prize_table'], 'zone 2 -> first table $A919 (same parity as THZ)')
        fr = self.c['fragment_art_proof']
        self.assertTrue(fr['identical_in_all_18_acts'])
        self.assertEqual(fr['pieces'], [{'x': -4, 'y': -16, 'tile': 0x66}])

    def test_act_clear_and_prize_table(self):
        a = self.c['act_clear']
        self.assertEqual([(s['act'], s['world_x'], s['world_y']) for s in a['signs']], [('sez1', 3960, 558), ('sez2', 3960, 398)])
        self.assertTrue(all(s['pan_target_inside_limits'] for s in a['signs']))
        self.assertEqual(a['prize_table']['table_cpu_by_zone'], {'zone0': '0xA919', 'zone1': '0xA962', 'zone2': '0xA919', 'zone3': '0xA962', 'zone4': '0xA919', 'zone5': '0xA962'})
        self.assertFalse(a['sez3']['sign_present'])
        self.assertEqual(a['sez3']['boss_world'], [3200, 622])

    def test_platform_parameters(self):
        p = self.c['platform']
        self.assertEqual({k: v['count'] for k, v in p['parameters'].items()}, {'0x04': 1, '0x83': 2, '0x84': 1, '0x86': 3})
        sweep = p['parameter_sweep']
        self.assertEqual((sweep['parameters_run'], sweep['parameters_out_of_table']), (56, 200))
        self.assertTrue(sweep['formula_matches_original_for_all_run'])
        self.assertEqual(sweep['by_parameter']['0x86'], dict(state=7, requested=7, axis_flag_25=255, callback='0x87E2', vx_8_8=256, vy_8_8=0))
        self.assertEqual(sweep['by_parameter']['0x04']['axis_flag_25'], 0)
        tally('platform_parameter_sweep', 56)
        self.assertEqual({x['parameter']: x['acceptance'][:3] for x in p['platforms']}, {'0x83': 'acc', '0x04': 'RES', '0x86': 'RES', '0x84': 'acc'})
        self.assertEqual(p['state_7_scan']['viewport_ram_references'], {})

    def test_footwear_matches_accepted_footwear_cache(self):
        shoes = self.c['footwear']['placements']
        self.assertEqual(self.c['footwear']['counts'], {'sez1': {'rocket_shoes_monitors': 1, 'spring_shoes': 8},
                                                       'sez2': {'rocket_shoes_monitors': 1, 'spring_shoes': 4}, 'sez3': {'rocket_shoes_monitors': 0, 'spring_shoes': 1}})
        self.assertTrue(self.c['footwear']['cross_check_counts_match'])
        self.assertEqual(len(shoes), 15)
        sp = self.c['footwear']['art']['spring_shoes']
        self.assertTrue(sp['decoded_stream_identical'] and sp['same_rom_stream'] and sp['all_frames_identical'])
        self.assertEqual((sp['sez_load']['tile_base'], sp['mghz_load']['tile_base']), ('0x94', '0xAC'))
        self.assertFalse(sp['sprite_palette']['cram_identical'])

    def test_enemies(self):
        e = self.c['enemies']
        self.assertEqual(sorted(e), ['0x20', '0x23'])
        self.assertEqual(e['0x20']['visible_frames'], [0, 1, 2])
        self.assertTrue(e['0x20']['orientation']['scripts_set_bit4'])
        self.assertFalse(e['0x23']['orientation']['scripts_set_bit4'])
        for t in e.values():
            self.assertFalse(t['placement_parameter_read'])
            self.assertEqual(t['code_scan']['viewport_ram_references'], {})
            for f in t['frames']:
                for im in f['images']:
                    self.assertFalse(im['approved_runtime_candidate'])
        t23 = e['0x23']['controlled_traces'][0]['trace']
        self.assertEqual([x['update'] for x in t23['transitions_first_14'][:6]], [1, 2, 66, 67, 89, 90])
        self.assertEqual(t23['transitions_first_14'][2]['requested_state_02'], 2)
        t20 = e['0x20']['controlled_traces'][0]['trace']
        self.assertEqual([x['update'] for x in t20['transitions_first_14'][:5]], [1, 2, 6, 7, 53])
        self.assertEqual(e['0x20']['controlled_traces'][0]['after_two_updates']['vx_8_8'], -128)

    def test_boss(self):
        b = self.c['boss']
        self.assertEqual((b['type'], b['state_count'], b['own_states']), (0x54, 13, [3, 6, 7, 8, 9, 10, 11, 12]))
        self.assertEqual((b['placement']['world_x'], b['placement']['world_y']), (3200, 622))
        self.assertEqual(b['placement']['raw_bytes'], '54 80 0D 6E 03 00 00 00 00')
        self.assertTrue(b['placement_within_map'])
        self.assertEqual([k for k, v in b['state_scripts_also_in_type_56_table'].items() if v], ['0', '1', '2', '4', '5'])
        self.assertEqual({k for k in b['children']}, {'0x55'})
        self.assertEqual(b['arena_and_camera']['rows'][2], {'index': 2, 'trigger_dx_lt': 160, 'trigger_dy_lt': 304, 'camera_x_offset': -224, 'camera_y_offset': -160})
        self.assertEqual(b['arena_derivation']['camera_target_nominal'], [2976, 462])
        self.assertEqual((b['art']['dynamic_selector'], b['art']['sprite_palette_index']), (0x15, 14))
        self.assertEqual(b['initialisation']['health_field_26'], 8)
        self.assertEqual([x['type'] for x in b['spawns_by_boss']], [52] * 5 + [85])
        self.assertEqual(b['art']['mapping_cpu'], '0x962D')
        self.assertIn('UNRESOLVED', b['completion']['status'])

    def test_viewport_classification_is_explicit(self):
        v = self.c['viewport_classification']
        self.assertEqual(len({x['id'] for x in v}), len(v))
        for x in v:
            self.assertIn(x['classification'], VIEWPORT_CLASSES)
            self.assertTrue(x['rule'] and x['evidence'])
        ids = {x['id']: x['classification'] for x in v}
        self.assertEqual((ids['sign_clear'], ids['boss_trigger'], ids['boss_camera_lock'], ids['mapped_lifecycle']), ('EDGE', 'PLAYER_DIST', 'LOCKED_CAMERA', 'EDGE'))
        self.assertEqual(ids['boss_object_54'], 'UNRESOLVED')

    def test_art_approval_recorded(self):
        self.assertTrue(self.a['approval'].startswith('APPROVED BY USER 2026-10-05'))
        self.assertEqual(self.a['approval_date'], '2026-10-05')
        self.assertEqual(sorted(self.a['subjects']), ['0x20', '0x23', '0x28', '0x2F', '0x54'])
        self.assertEqual(sorted(self.a['shared_subjects_identical_to_accepted_zone']), ['0x07', '0x10', '0x1B', '0x26'])
        self.assertEqual(len(self.a['boards']), 16)


class RomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not ROM_PATH.is_file():
            raise unittest.SkipTest('canonical local ROM unavailable')
        cls.r = L.load_rom(ROM_PATH)

    def test_fresh_regeneration(self):
        self.assertEqual(F.dumps(F.build(self.r)), F.OUTPUT.read_text(encoding='utf-8'))
        self.assertEqual(C.dumps(C.build(self.r)), C.OUTPUT.read_text(encoding='utf-8'))
        self.assertEqual(json.dumps(AA.manifest_for(AA.build(self.r)), indent=2) + '\n', AA.CACHE.read_text(encoding='utf-8'))

    def test_original_start_loader_and_layout_ceiling(self):
        f = json.loads(F.OUTPUT.read_text(encoding='utf-8'))
        for act, (k, a) in enumerate(f['acts'].items()):
            o = Oracle(self.r)
            o.mem[0xD297], o.mem[0xD298] = 2, act
            o.call(0x4E57)
            self.assertEqual([o.word(v) for v in (0xD2D6, 0xD2D8)], a['start']['camera'])
            self.assertEqual([o.word(v) for v in (0xD511, 0xD514)], a['start']['player_anchor'])
            h = a['descriptor']['header']
            ld = Oracle(self.r)
            ld.bank(2, h['layout_bank'])
            ld.mem[0xC001:0xD000] = bytes(4095)
            ld.mem[0xD000] = 0xA5
            ld.cpu.iy, ld.cpu.de, ld.cpu.pc = h['layout_cpu'], 0xC001, 0x4DC4
            ld.cpu.set_breakpoint(0x4DFB)
            for _ in range(20):
                ld.cpu.ticks_to_stop = 100000
                ld.cpu.run()
                if ld.cpu.pc == 0x4DFB:
                    break
            self.assertEqual((ld.cpu.pc, ld.cpu.de), (0x4DFB, 0xD000))
            self.assertEqual(ld.mem[0xD000], 0xA5)            # the 4096th cell is never written
            runtime = [b for row in a['layout']['rows'] for b in row][:4095]
            self.assertEqual(bytes(ld.mem[0xC001:0xD000]), bytes(runtime))
            tally('original_layout_loader_cells', 4095)

    def test_header_bytes_and_independent_layout(self):
        f = json.loads(F.OUTPUT.read_text(encoding='utf-8'))
        for act, (k, a) in enumerate(f['acts'].items()):
            h = L.act_header(self.r, 2, act)
            self.assertEqual(bytes.fromhex(h['raw'])[:3], bytes([0x11, 0x40, 0xAA]))
            cells, _, ok = L.decode_layout_stream(self.r, h['layout_rom'])
            self.assertTrue(ok)
            self.assertEqual(cells, [b for row in a['layout']['rows'] for b in row])
            for b in a['blocks']:
                for plane in (0, 1):
                    self.assertEqual(b['headers'][plane], R.header(self.r, b['block_id'], plane))
                    tally('block_header_planes')

    def test_mapping_pointer_all_blocks_all_acts_against_original_consumers(self):
        from block_mapping_audit import original_pointer
        for act in range(3):
            o = Oracle(self.r)
            h = L.act_header(self.r, 2, act)
            o.mem[0xD297], o.mem[0xD298] = 2, act
            o.call(0x4FDC)
            self.assertEqual((o.mem[0xD162], o.word(0xD164)), (0x11, 0xAA40))
            o.cpu.a = 0x11
            o.call(0x1C6F)
            for block in range(256):
                m = L.block_mapping(self.r, h['block_mapping_rom'], block)
                for vertical in (False, True):
                    cpu = original_pointer(o, h['block_mapping_cpu'], block, vertical)
                    self.assertEqual(cpu, m['cpu'])
                    self.assertEqual(bytes(o.mem[cpu:cpu + 32]), self.r[m['rom']:m['rom'] + 32])
                    self.assertEqual(m['rom'], 0x44000 + cpu - 0x8000)
                    tally('mapping_original_consumer')
        # the table-relative formula is demonstrably wrong for SEZ
        m = L.block_mapping(self.r, L.act_header(self.r, 2, 0)['block_mapping_rom'], 0)
        self.assertNotEqual(m['rom'], 0x46A40 + m['cpu'] - 0x8000)

    def test_surface_0c_handler_exhaustive(self):
        """$6B79: spawn iff player +$19 bit 7 is clear and the probed cell pointer changed; D356 follows only on a spawn."""
        for flag in range(256):
            for same in (False, True):
                o = Oracle(self.r)
                m = o.mem
                o.cpu.ix = 0xD500
                m[0xD519] = flag
                cur = 0xC123
                o.word(0xD354, cur)
                o.word(0xD356, cur if same else cur ^ 1)
                o.word(0xD358, 0x0234)
                o.word(0xD35A, 0x00C8)
                for i in range(16):
                    m[0xD540 + i * 0x40] = 0
                o.call(0x6B79)
                spawned = sum(1 for i in range(16) if m[0xD540 + i * 0x40])
                expect = int(not flag & 0x80 and not same)
                self.assertEqual(spawned, expect, (flag, same))
                self.assertEqual(o.word(0xD356), cur if expect or same else cur ^ 1)
                if expect:
                    self.assertEqual((m[0xD540], m[0xD540 + 0x3F]), (0x13, 0))
                tally('surface_0c_cases')
        # allocator full: nothing is created but the dedup pointer still advances (original behaviour)
        o = Oracle(self.r)
        o.cpu.ix = 0xD500
        o.word(0xD354, 0xC200)
        o.word(0xD356, 0xC1FF)
        for i in range(16):
            o.mem[0xD540 + i * 0x40] = 0x07
        o.call(0x6B79)
        self.assertEqual(o.word(0xD356), 0xC200)
        self.assertEqual(sum(1 for i in range(16) if o.mem[0xD540 + i * 0x40] == 0x13), 0)
        tally('surface_0c_cases')

    def test_surface_1a_handler_exhaustive(self):
        """$7646: fires iff player +$22 bit 1 is set; effect values are constant."""
        for flag in range(256):
            o = Oracle(self.r)
            o.cpu.ix = 0xD500
            o.mem[0xD522] = flag
            o.mem[0xD503] = 0x01
            o.mem[0xD502] = 0x05
            o.word(0xD373, 0x0123)
            o.word(0xD516, 0x0005)
            o.call(0x7646)
            if flag & 2:
                self.assertEqual((o.word(0xD373), o.word(0xD516), o.mem[0xD502], o.mem[0xD503], o.mem[0xDE04]), (0x700, 0x700, 0x10, 0x02, 0xBD), flag)
            else:
                self.assertEqual((o.word(0xD373), o.word(0xD516), o.mem[0xD502], o.mem[0xD503]), (0x123, 0x0005, 0x05, 0x01), flag)
            tally('surface_1a_cases')

    def test_effect_5_cadence_pause_and_zones(self):
        ev = F.run_effect(self.r, 5, 300)
        self.assertEqual([e['update'] for e in ev], list(range(2, 300, 3)))
        sources = [e['vram_copies'][0]['source_cpu'] for e in ev]
        self.assertEqual(sources, [0x8DFD, 0x8DDD] * 50)
        self.assertEqual({e['vram_copies'][0]['vram'] for e in ev}, {0x2B00})
        tally('effect5_updates', 300)
        for d44e in range(1, 256):
            self.assertEqual(F.run_effect(self.r, 5, 6, d44e=d44e), [], d44e)
            tally('effect5_pause_values')
        for z in range(6):
            self.assertEqual(len(F.run_effect(self.r, 5, 6, zone=z)) > 0, z in (2, 4, 5), z)
            tally('effect5_zone_rows')

    def test_zone_site_bytes(self):
        r = self.r
        self.assertEqual(r[0x6A5D:0x6A63], bytes([0x3A, 0x97, 0xD2, 0xFE, 0x05, 0xC0]))
        self.assertEqual(r[0x6AB9:0x6ABD], bytes([0x3A, 0x97, 0xD2, 0xB7]))
        self.assertEqual(r[0x30000 + 0x2909:0x30000 + 0x290E], bytes([0x3A, 0x97, 0xD2, 0x3C, 0x0F]))
        self.assertEqual(r[0x7A291:0x7A296], bytes([0x3E, 0x15, 0x32, 0xB3, 0xD3]))            # $54 init: dynamic art selector $15
        self.assertEqual(r[0x7A29C:0x7A29E], bytes([0x36, 14]))                                # sprite palette index 14
        self.assertEqual(r[0x7A2A2:0x7A2A6], bytes([0xDD, 0x36, 0x26, 0x08]))                  # health byte 8
        self.assertEqual(r[0x7A29E:0x7A2A2], bytes([0xDD, 0x36, 0x02, 0x06]))                  # requests state 6
        tally('zone_site_bytes', 7)

    def test_prize_table_selector_by_zone(self):
        c = json.loads(C.OUTPUT.read_text(encoding='utf-8'))['act_clear']['prize_table']['table_cpu_by_zone']
        got = C.prize_table_by_zone(self.r)['table_cpu_by_zone']
        self.assertEqual(c, got)
        for z in range(6):
            self.assertEqual(got[f'zone{z}'], '0xA919' if (z + 1) & 1 == 1 else '0xA962')
            tally('prize_table_zones')

    def test_platform_creator_sweep_matches_formula(self):
        a = C.vram_for_act(self.r, 0)
        sweep = C.platform_parameter_sweep(self.r, a)
        self.assertTrue(sweep['formula_matches_original_for_all_run'])
        self.assertEqual(sweep['parameters_run'], 56)
        tally('platform_creator_sweep', 56)

    def test_boss_framework_tables(self):
        t = C.C.boss_tables(self.r)
        self.assertEqual(t['rows'][2], {'index': 2, 'trigger_dx_lt': 160, 'trigger_dy_lt': 304, 'camera_x_offset': -224, 'camera_y_offset': -160})
        st = C.C.state_table(self.r, 0x54)
        self.assertEqual((st['bank'], st['state_table_cpu'], st['state_count']), (0x1E, 0xA1DC, 13))


if __name__ == '__main__':
    unittest.main()
