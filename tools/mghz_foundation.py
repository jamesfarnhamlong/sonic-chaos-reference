#!/usr/bin/env python3
"""Deterministic MGHZ1-3 level foundation manifest; no ROM/art dumps are emitted.

MGHZ is ROM zone index 3 (THZ 0, GPZ 1, SEZ 2, MGHZ 3, APZ 4, EEZ 5).  The
object census, enemy/boss reconnaissance and footwear placements live in
``mghz_object_census.py``; this module owns terrain, surfaces, rings, graphics
and level-animation effects.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import level_package as L
import rom as R
import block_mapping_audit as BM
from oracle import Oracle

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'data/rom-cache/mghz/implementation-manifest.json'
ZONE = 3
ACTS = {f'mghz{n + 1}': {'zone': ZONE, 'act': n, 'name': f'Mecha Green Hill Zone Act {n + 1}'} for n in range(3)}
RESEARCH_BASE = '399f95b'
MAPPING_BANK = 0x14

# --- engine tables, all byte-verified against the ROM by the tests ----------
RING_ART_TABLE = 0x2A9A            # LoadRingArtPointers: zone -> act -> 10-byte descriptor
EFFECT_DISPATCHER = (0x1D, 0x8000)  # bank $1D:$8000, four 8-byte slots at $D452
EFFECT_JUMP_TABLE = 0x8028
EFFECT_SLOTS = (0xD452, 0xD45A, 0xD462, 0xD46A)
FLOOR_DISPATCH_CSV = ROOT / 'data/floor-dispatch.csv'
# (chain start, chain end) of 'CP n / JP Z,target' surface dispatch inside the collision routines
SIDE_RIGHT_CHAIN = (0x717E, 0x7196)
SIDE_LEFT_CHAIN = (0x7223, 0x723B)
CEILING_CHAIN = (0x73F8, 0x7413)

EFFECT_NAMES = {
    0: 'inactive slot', 1: 'effect 1 (THZ; not used by MGHZ)',
    2: 'background-palette cycle, CRAM entry 4 (copy of $D476), 6 steps x 10 updates',
    3: 'background-palette cycle, CRAM entry 11 (copy of $D47D), 10 steps x 10 updates',
    14: 'two-tile VRAM strip animation: 64 bytes to VRAM $3500 (tiles $1A8/$1A9), 2 frames x 4 updates, paused while $D44E != 0',
}

# Evidence-backed surface registry.  'status' vocabulary:
#   ACCEPTED_SHARED   handler/consumer already researched and Windows-accepted in THZ/GPZ runtime
#   RESEARCHED_DATA   researched behaviour, POC core supports it, MGHZ needs data/art integration
#   NEW_NEEDS_AUDIT   consumer found in ROM, no accepted research for this usage -> dedicated follow-up
SURFACES = {
    0x00: ('empty/background block (sets/clears nothing but clears +$24 bits 0/1)', 'ACCEPTED_SHARED', 'docs/collision.md; $6C45', None),
    0x01: ('ordinary solid', 'ACCEPTED_SHARED', 'docs/collision.md; floor handler $6A5D returns unless zone == 5 (EEZ only)', None),
    0x02: ('ordinary solid (profile variants)', 'ACCEPTED_SHARED', 'docs/collision.md; handler $6A5B RET', None),
    0x03: ('slope/profile solid (modifier byte)', 'ACCEPTED_SHARED', 'docs/collision-geometry-audit.md; handler $6A5C RET', None),
    0x05: ('spikes: floor probe $6ACE, side wall without damage ($7306/$7329), ceiling hurt only for blocks $3E/$3F ($74E7)',
           'NEW_NEEDS_AUDIT', 'docs/platform-spike-collision-audit.md covers blocks $3C/$3D only',
           'ceiling-spike blocks $3E/$3F ($74E7..$752C: hurt when the sampled block & $FE == $3E) are not covered by an accepted audit'),
    0x07: ('terrain ring blocks (probe $753E)', 'ACCEPTED_SHARED', 'docs/terrain-ring-collection.md; data/rom-cache/terrain-ring-collection.json', None),
    0x09: ('upright terrain spring', 'ACCEPTED_SHARED', 'docs/spring-interaction-audit.md; $6A75', None),
    0x0A: ('horizontal terrain spring (side path post-projection test)', 'ACCEPTED_SHARED', 'docs/spring-interaction-audit.md; $71FC/$7283', None),
    0x0D: ('breakable block $9B/$9C -> $9D + four type $07 fragments (attack posture required)', 'RESEARCHED_DATA',
           'docs/spring-interaction-audit.md row H; $6B2C -> $7898; side $72B6/$72DD; ceiling $7464',
           'fragment art/palette for MGHZ must come from the MGHZ dynamic art path; POC core already has a surface-13 break adapter'),
    0x14: ('diagonal terrain spring (zone != 0 -> Y launch -5.5)', 'ACCEPTED_SHARED', 'docs/gpz-foundation-audit.md section 4; $6A90', None),
    0x17: ('twist strip (state $22); zone 3 selects variants 2/3', 'RESEARCHED_DATA', 'docs/twist.md; data/twist-dispatch.csv; $6E56, $6E7F/$6EE8/$6F52',
           'tables for variants 2/3 exist in the CSV; MGHZ2 has the only 28-cell strip'),
    0x18: ('solid, no dedicated consumer found (floor handler $69B1 = RET)', 'ACCEPTED_SHARED',
           'also used by THZ1-3 blocks $8A/$8B; no CP $18 surface consumer in the fixed collision routines', 'confirm visually that blocks $8A/$8B need no special rule'),
    0x19: ('speed-strip surface: sets +$24 bit 0, fall request $14', 'ACCEPTED_SHARED', 'docs/gpz-surface19-audit.md; $6B23', None),
    0x1B: ('oil/sinking surface: +$24 bit 1, $D3BC += 1 every 4th $D12F update, one-way sinking projection $7010', 'NEW_NEEDS_AUDIT',
           'docs/gpz-surface19-audit.md only records the $D3BC increment; no gameplay audit of the sinking branch',
           'dedicated audit: entry/exit, sink depth cap, stale +$24 bit1 on non-zero surfaces, state interactions, death/escape'),
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def stable(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def u16(r, pos):
    return r[pos] | r[pos + 1] << 8


def bank_file(bank, cpu):
    return bank * 0x4000 + cpu - 0x8000


def region(r, bank, a, b):
    off = a if a < 0x8000 else bank_file(bank, a)
    return {'bank': bank, 'cpu': a, 'rom': off, 'length': b - a, 'sha256': digest(r[off:off + b - a])}


def cell_record(index, block, width):
    return {'layout_index': index, 'cell_x': index % width, 'cell_y': index // width,
            'world_x': index % width * 32, 'world_y': index // width * 32, 'block_id': block}


# --- surface dispatch chains --------------------------------------------------
def dispatch_chain(r, start, stop):
    """Decode a run of 'CP n / JP Z,target' pairs; returns [(surface, target_cpu)]."""
    from z80dis import z80
    out, pos, pending = [], start, None
    while pos < stop:
        d = z80.decode(r[pos:pos + 4], pos)
        text = z80.disasm(d)
        parts = text.replace(',', ' ').split()
        if parts[0].upper() == 'CP' and len(parts) == 2:
            try:
                pending = int(parts[1], 0)
            except ValueError:
                pending = None
        elif parts[0].upper() == 'JP' and parts[1].lower() == 'z' and pending is not None:
            out.append((pending, int(parts[2], 0)))
            pending = None
        pos += d.len
    return out


def surface_consumers(r):
    with FLOOR_DISPATCH_CSV.open(encoding='utf-8', newline='') as fh:
        floor = {int(row['type_hex'], 16): int(row['handler_cpu'], 16) for row in csv.DictReader(fh)}
    right = dispatch_chain(r, *SIDE_RIGHT_CHAIN)
    left = dispatch_chain(r, *SIDE_LEFT_CHAIN)
    ceiling = dispatch_chain(r, *CEILING_CHAIN)
    return {'floor_dispatch_table': {'cpu': 0x6973, 'csv': 'data/floor-dispatch.csv', 'handlers': {f'0x{k:02X}': f'0x{v:04X}' for k, v in sorted(floor.items())}},
            'side_right_chain': {'range': [f'0x{v:04X}' for v in SIDE_RIGHT_CHAIN], 'entries': [[f'0x{s:02X}', f'0x{t:04X}'] for s, t in right]},
            'side_left_chain': {'range': [f'0x{v:04X}' for v in SIDE_LEFT_CHAIN], 'entries': [[f'0x{s:02X}', f'0x{t:04X}'] for s, t in left]},
            'ceiling_chain': {'range': [f'0x{v:04X}' for v in CEILING_CHAIN], 'entries': [[f'0x{s:02X}', f'0x{t:04X}'] for s, t in ceiling]},
            'post_projection_horizontal_spring': 'right $71FC / left $7283: CP $0A after $64CB (surface $0A)'}, floor, right, left, ceiling


def six_zone_surfaces(r):
    names = ('thz', 'gpz', 'sez', 'mghz', 'aqz', 'eez')
    table = {}
    for z in range(6):
        for a in range(3):
            d = L.build_descriptor(r, 'x', {'zone': z, 'act': a, 'name': 'x'})
            cells, _, _ = L.decode_layout_stream(r, d['header']['layout_rom'], L.LAYOUT_RAM_LIMIT_CELLS)
            per = Counter()
            for block, n in Counter(cells).items():
                per[R.header(r, block, 0)['flags'] & 31] += n
            for s, n in per.items():
                table.setdefault(f'0x{s:02X}', {})[f'{names[z]}{a + 1}'] = n
    return dict(sorted(table.items()))


# --- terrain-ring animation and level effects -------------------------------------
def ring_art_descriptor(r, zone, act):
    zp = u16(r, RING_ART_TABLE + zone * 2)
    dp = u16(r, zp + act * 2)
    raw = r[dp:dp + 10]
    return {'zone_pointer_rom': RING_ART_TABLE + zone * 2, 'act_pointer_rom': zp + act * 2, 'descriptor_rom': dp,
            'raw': raw.hex().upper(), 'collision_table_cpu': u16(raw, 0), 'ring_frames_source_cpu': u16(raw, 2),
            'ring_frames_vram_destination': u16(raw, 4), 'effect_ids': list(raw[6:10])}


def terrain_ring_animation(r, desc):
    src = bank_file(0x1D, desc['ring_frames_source_cpu'])
    frames = [{'frame': i, 'source_rom': src + 128 * i, 'bytes': 128, 'sha256': digest(r[src + 128 * i:src + 128 * (i + 1)])} for i in range(4)]
    tile0 = desc['ring_frames_vram_destination'] // 32
    return {'routine': {'bank': 0x1D, 'cpu': 0x850A, 'rom': bank_file(0x1D, 0x850A)},
            'source_bank_cpu': '0x1D:0x%04X' % desc['ring_frames_source_cpu'], 'frames': frames,
            'vram_destination': desc['ring_frames_vram_destination'], 'tile_ids': [tile0 + i for i in range(4)],
            'period_updates_per_frame': 8, 'frame_count': 4,
            'rule': 'return unless $D12F & 7 == 0; $D351 = ($D351 + 1) mod 4; copy 128 bytes $D399 + $D351*128 to VRAM $D39B',
            'hud_note': 'the same routine also writes the HUD ring-icon sprite tile bytes $DBB5/$DBB7 from table $1D:$8555 (HUD, not terrain)',
            'evidence': 'BYTE-VERIFIED ASSEMBLY ($1D:$850A) + DECODED DATA (descriptor)'}


def run_effect(r, effect_id, updates, d44e=0, bg_palette=24, sprite_palette=9):
    """Execute the original bank-$1D effect routine on one slot and record palette/VRAM writes."""
    o = Oracle(r)
    m, cpu = o.mem, o.cpu
    o.bank(2, 0x1D)
    m[0xD12B] = 0x1D
    m[0xD492], m[0xD44E] = 0, d44e
    slot = EFFECT_SLOTS[0]
    for i in range(8):
        m[slot + i] = 0
    m[slot] = effect_id
    pal = L.PALETTE_DATA
    m[0xD472:0xD482] = r[pal + bg_palette * 16:pal + bg_palette * 16 + 16]
    m[0xD482:0xD492] = r[pal + sprite_palette * 16:pal + sprite_palette * 16 + 16]
    events = []
    for update in range(updates):
        before = bytes(m[0xD472:0xD492])
        m[0xD496] = 0
        cpu.iy = slot
        cpu.pc, cpu.sp = 0x8018, 0xDFE0
        o.word(cpu.sp, o.RETURN)
        cpu.set_breakpoint(0x0401)
        copies = []
        for _ in range(40):
            cpu.ticks_to_stop = 100000
            cpu.run()
            if cpu.pc == 0x0401:
                hl, de, bc = cpu.hl, cpu.de, cpu.bc
                copies.append({'source_cpu': hl, 'vram': de, 'length': bc, 'sha256': digest(bytes(m[hl:hl + bc]))})
                cpu.pc = m[cpu.sp] | m[cpu.sp + 1] << 8
                cpu.sp += 2
            elif cpu.pc == o.RETURN:
                break
        cpu.clear_breakpoint(0x0401)
        after = bytes(m[0xD472:0xD492])
        pal_writes = [{'cram_index': i, 'before': before[i], 'after': after[i]} for i in range(32) if before[i] != after[i]]
        if pal_writes or copies:
            events.append({'update': update, 'palette_writes': pal_writes, 'palette_dirty_flag': m[0xD496], 'vram_copies': copies})
    return events


def level_effects(r, desc):
    jump = [u16(r, bank_file(0x1D, EFFECT_JUMP_TABLE) + 2 * i) for i in range(0x12)]
    out = {'dispatcher': {'bank': 0x1D, 'cpu': 0x8000, 'rom': bank_file(0x1D, 0x8000),
                          'gate': '$D492 (BGPalleteControlByte) must be zero',
                          'slots': [f'0x{s:04X}' for s in EFFECT_SLOTS], 'slot_stride': 8,
                          'jump_table_cpu': EFFECT_JUMP_TABLE},
           'descriptor_effect_ids': desc['effect_ids'],
           'main_loop_call': 'archive/continuation-01/overlay/SonicChaos.asm line 483 (every gameplay frame)', 'effects': {}}
    for eid in sorted(set(desc['effect_ids']) - {0}):
        runs = {'paused_flag_clear': run_effect(r, eid, 200 if eid != 14 else 40)}
        entry = {'routine_cpu': f'0x{jump[eid]:04X}', 'description': EFFECT_NAMES[eid], 'first_events': runs['paused_flag_clear'][:12],
                 'event_count_in_window': len(runs['paused_flag_clear'])}
        if eid == 14:
            paused = run_effect(r, eid, 40, d44e=1)
            entry['events_with_D44E_nonzero_in_40_updates'] = len(paused)
            entry['source_cpus'] = ['0x%04X' % u16(r, bank_file(0x1D, 0x832A) + 2 * i) for i in range(2)]
        out['effects'][str(eid)] = entry
    out['phase_note'] = 'slot counters start at 0 when the act loads; absolute phase against the global clock is not claimed'
    return out


# --- act package --------------------------------------------------------------
def terrain_categories(r, cells, width):
    names = {0x30: 'upright_spring', 0x31: 'upright_spring', 0x32: 'horizontal_spring', 0x34: 'horizontal_spring', 0x35: 'horizontal_spring',
             0x36: 'diagonal_spring_right', 0x38: 'diagonal_spring_left', 0x3C: 'upward_spikes', 0x3E: 'ceiling_spikes', 0x3F: 'ceiling_spikes'}
    cats = {}
    for i, b in enumerate(cells):
        hd = R.header(r, b)
        s = hd['flags'] & 31
        if b in names:
            c = names[b]
        elif s == 0x0D:
            c = 'breakable_0D'
        elif s == 0x17:
            c = 'twist_17'
        elif s == 0x19:
            c = 'strip_19'
        elif s == 0x1B:
            c = 'oil_1B'
        elif s == 0x18:
            c = 'surface_18'
        elif s == 7:
            c = 'terrain_ring'
        elif hd['flags'] & 0x40 and s == 1:
            c = 'one_way_bit6'
        else:
            continue
        cats.setdefault(c, []).append(cell_record(i, b, width))
    return dict(sorted(cats.items()))


def block_definitions(r, act, mapping_rom, vram):
    cells = act['cells'][:act['runtime_cells']]
    counts = Counter(cells)
    replacements = {0x46, 0x9D}
    for table in act['semantics']['tables'].values():
        replacements.update(table['replacement_blocks'])
    block_set = sorted(set(cells) | replacements)
    pix = L.block_pixel_maps(r, vram, only=block_set, mapping_rom=mapping_rom)
    defs = []
    for block in block_set:
        mp = L.block_mapping(r, mapping_rom, block)
        hd = R.header(r, block)
        s = hd['flags'] & 31
        defs.append({'block_id': block, 'cell_count': counts[block], 'in_initial_layout': block in counts, 'surface': s,
                     'surface_status': SURFACES[s][1] if s in SURFACES else 'UNRESOLVED',
                     'headers': [R.header(r, block, plane) for plane in (0, 1)],
                     'alternate_plane_header_differs': R.header(r, block, 0)['address'] != R.header(r, block, 1)['address'],
                     'mapping': mp,
                     'mapping_sha256': digest(b''.join(v.to_bytes(2, 'little') for v in mp['attributes'])),
                     'tile_ids': sorted({a & 0x1FF for a in mp['attributes']}),
                     'priority_tiles': sum(bool(a & 0x1000) for a in mp['attributes']),
                     'palette1_tiles': sum(bool(a & 0x0800) for a in mp['attributes']),
                     'h_flip_tiles': sum(bool(a & 0x0200) for a in mp['attributes']),
                     'v_flip_tiles': sum(bool(a & 0x0400) for a in mp['attributes']),
                     'decoded_palette_index_sha256': digest(bytes(v for row in pix[block] for v in row)),
                     'nonzero_pixels': sum(bool(v) for row in pix[block] for v in row)})
    return defs


def build_act(r, key, meta):
    a = L.build_act(r, key, meta)
    d, h, width = a['descriptor'], a['descriptor']['header'], a['width']
    cells = a['cells'][:a['runtime_cells']]
    mapping_rom = h['block_mapping_rom']
    blocks = block_definitions(r, a, mapping_rom, a['vram'])
    effects_used = {}
    block_tiles = {b['block_id']: set(b['tile_ids']) for b in blocks}
    for tile in (0x1A8, 0x1A9):
        effects_used[f'0x{tile:03X}'] = sorted({f'0x{b:02X}' for b, t in block_tiles.items() if tile in t and b in set(cells)})
    rings = {'terrain': a['terrain_rings'], 'object09': L.object_rings(a), 'presence_and_replacement_tables': a['semantics'],
             'collection_contract': 'accepted THZ/GPZ pipelines unchanged: terrain $753E (anchor + parity probe) and strict type $09 anchor proximity'}
    rings['coordinate_sha256'] = L.coordinate_hash(L.ring_hash_rows(rings['terrain'] + rings['object09']))
    start = d['start']
    inter = terrain_categories(r, cells, width)
    return {'descriptor': d, 'dimensions_pixels': [width * 32, a['height'] * 32],
            'start': {'player_anchor': [start['ram_d511'], start['ram_d514']], 'camera': [start['ram_d2d6'], start['ram_d2d8']],
                      'evidence': 'SOURCE-TRACED loader $4E57; direct word copies, no adapter offsets'},
            'bounds': {'camera_min_words': [h['ram_d280'], h['ram_d27c']], 'camera_max_words': [h['ram_d282'], h['ram_d27e']],
                       'source': 'header +12/+14/+16/+18 -> D280/D27C/D282/D27E; SMS values (right limit exclusive)'},
            'layout': {'rows': [a['cells'][i:i + width] for i in range(0, len(a['cells']), width)],
                       'encoded_cells': len(a['cells']), 'runtime_written_cells': a['runtime_cells'],
                       'encoded_cells_sha256': digest(bytes(a['cells'])), 'runtime_cells_sha256': digest(bytes(cells)),
                       'last_cell_policy': 'index >= runtime_written_cells is not ROM-loaded terrain',
                       'unloaded_cells': [cell_record(i, a['cells'][i], width) for i in range(a['runtime_cells'], len(a['cells']))]},
            'blocks': blocks, 'terrain_interactions': inter, 'rings': rings,
            'animated_terrain_blocks': effects_used,
            'census': {'distinct_layout_blocks': len(set(cells)), 'surface_cell_counts': {f'0x{s:02X}': n for s, n in sorted(
                           Counter(R.header(r, b)['flags'] & 31 for b in cells).items())},
                       'terrain_rings': len(rings['terrain']), 'object09_rings': len(rings['object09']),
                       'priority_blocks_in_layout': sorted({f"0x{b['block_id']:02X}" for b in blocks if b['priority_tiles'] and b['in_initial_layout']}),
                       'terrain_interactions': {k: len(v) for k, v in inter.items()}},
            'graphics': {'static_vram_loads': a['vram_loads'], 'vram_sha256': digest(a['vram']),
                         'palettes': {n: {'rom': d['palette'][n + '_rom'], 'index': d['palette'][n + '_index'],
                                          'cram': list(r[d['palette'][n + '_rom']:d['palette'][n + '_rom'] + 16])} for n in ('background', 'sprite')}}}


def mapping_pointer_check(r, acts):
    """MGHZ table sits at a bank boundary, so the table-relative and bank-relative formulas coincide."""
    h = acts['mghz1']['descriptor']['header']
    bank = h['block_mapping_bank']
    table_rel = h['block_mapping_rom'] % 0x4000
    o = Oracle(r)
    o.mem[0xD297], o.mem[0xD298] = ZONE, 0
    o.call(0x4FDC)
    loader = [o.mem[0xD162], o.word(0xD164)]
    o.cpu.a = o.mem[0xD162]
    o.call(0x1C6F)
    checked, mismatches = 0, 0
    pointers = []
    for block in range(256):
        m = L.block_mapping(r, h['block_mapping_rom'], block)
        for vertical in (False, True):
            cpu = BM.original_pointer(o, h['block_mapping_cpu'], block, vertical)
            checked += 1
            mismatches += cpu != m['cpu'] or bytes(o.mem[cpu:cpu + 32]) != r[m['rom']:m['rom'] + 32]
        pointers.append(m['rom'])
    wrong = [(h['block_mapping_rom'] + (L.u16(r, h['block_mapping_rom'] + 2 * b)) - 0x8000) for b in range(256)]
    return {'bank': bank, 'bank_file_base': bank * 0x4000, 'table_cpu': h['block_mapping_cpu'], 'table_rom': h['block_mapping_rom'],
            'table_offset_inside_bank': table_rel, 'old_table_relative_error_bytes': table_rel,
            'masked_by_alignment': table_rel == 0, 'loader_registers_d162_d164': loader,
            'formula': 'mappingFile = bank*$4000 + raw_pointer_word - $8000 (word is an absolute CPU address inside the bank)',
            'original_consumer_checks': checked, 'original_consumer_mismatches': mismatches,
            'old_formula_agrees_for_all_256_blocks': wrong == pointers,
            'resolved_offsets_sha256': digest(b''.join(p.to_bytes(4, 'little') for p in pointers)),
            'warning': 'agreement of the old formula is an alignment accident; Aqua/EEZ tables in the same bank are not aligned'}


def build(r):
    if digest(r) != L.ROM_SHA256:
        raise ValueError('Expected canonical Europe v1.2 ROM')
    consumers, floor, right, left, ceiling = surface_consumers(r)
    out = {'format': 1, 'rom_sha256': L.ROM_SHA256, 'research_base': RESEARCH_BASE,
           'scope': 'MGHZ1-3 level foundation: terrain, surfaces, rings, graphics and level animation; decoded metadata, not a ROM/art dump',
           'zone': {'index': ZONE, 'evidence': 'object list $710B8 / layout $559D4 / mapping $50000 / art $619F0 match the community offsets table; '
                    'tools/block_mapping_audit.py names zones thz,gpz,sez,mghz,apz,eez; tools/gpz_enemy_approval.py `placements` labels index 2 as mghz '
                    '(naming slip in that tool; it only filters numeric types and is not an accepted fact)'},
           'coordinate_policy': 'mapped anchor = stored-256; terrain origin = cell*32; presentation never changes the collision anchor',
           'status_vocabulary': {'ACCEPTED_SHARED': 'researched and Windows-accepted THZ/GPZ runtime path',
                                 'RESEARCHED_DATA': 'researched behaviour; MGHZ needs data/art/integration only',
                                 'NEW_NEEDS_AUDIT': 'consumer located in ROM; no accepted research for this usage'},
           'acts': {}}
    acts_raw = {}
    for key, meta in ACTS.items():
        out['acts'][key] = build_act(r, key, meta)
        acts_raw[key] = out['acts'][key]
    out['mapping_pointer'] = mapping_pointer_check(r, acts_raw)
    desc = ring_art_descriptor(r, ZONE, 0)
    descs = [ring_art_descriptor(r, ZONE, a) for a in range(3)]
    out['terrain_ring_animation'] = dict(terrain_ring_animation(r, desc), per_act_descriptors_identical=all((d['descriptor_rom'], d['raw']) == (descs[0]['descriptor_rom'], descs[0]['raw']) for d in descs),
                                         descriptor=desc)
    out['level_effects'] = level_effects(r, desc)
    surf = Counter()
    for a in out['acts'].values():
        for k, v in a['census']['surface_cell_counts'].items():
            surf[k] += v
    out['surface_census'] = {
        'consumers': consumers,
        'mghz_surfaces': {f'0x{s:02X}': {'cells': {k: a['census']['surface_cell_counts'].get(f'0x{s:02X}', 0) for k, a in out['acts'].items()},
                                         'blocks': sorted({f"0x{b['block_id']:02X}" for a in out['acts'].values() for b in a['blocks']
                                                           if b['surface'] == s and b['in_initial_layout']}),
                                         'floor_handler': f'0x{floor[s]:04X}', 'side_consumer': s in {x for x, _ in right + left} or s == 0x0A,
                                         'ceiling_consumer': s in {x for x, _ in ceiling},
                                         'meaning': SURFACES[s][0], 'status': SURFACES[s][1], 'evidence': SURFACES[s][2], 'follow_up': SURFACES[s][3]}
                          for s in sorted(int(k, 16) for k in surf)},
        'six_zone_cell_counts': six_zone_surfaces(r),
        'one_way_bit6_blocks': 'blocks with flags bit 6 and surface 1 ($0D/$0F/$F9) follow the accepted one-way projection; flag-bit-6 variants of surfaces $09/$14/$17/$19/$1B are listed under their surface'}
    out['zone_dependent_code'] = zone_sites(r)
    out['source_regions'] = {n: region(r, *v) for n, v in {
        'start_loader': (0, 0x4E57, 0x4E98), 'header_loader': (0, 0x4FDC, 0x5038),
        'surface_1b_handler': (0, 0x6B14, 0x6B23), 'surface_1b_sinking_branch': (0, 0x7010, 0x7056),
        'twist_variant_gate': (0, 0x6E7F, 0x6F60), 'ceiling_spike_branch': (0, 0x74E7, 0x752F),
        'ring_animation': (0x1D, 0x850A, 0x8555), 'effect_dispatcher': (0x1D, 0x8000, 0x8052),
        'effect_2_3': (0x1D, 0x832E, 0x8392), 'effect_14': (0x1D, 0x82F7, 0x832E)}.items()}
    out['unresolved'] = [
        'Surface $1B (oil/sinking) gameplay semantics: only the numeric handler and one-way sinking projection are located; needs a dedicated audit.',
        'Ceiling spikes (blocks $3E/$3F): ceiling hurt path $74E7 is located but not audited; POC support unknown.',
        'Effect slot absolute phase relative to the global clock is not established; relative cadence is exact.',
        'Which effect-14 tile pair is visually which scenery object requires PNG review (blocks $D2/$D3 reference tiles $1A8/$1A9).',
        'Surface $18 blocks $8A/$8B: no special consumer found; visual check pending.',
        'Fragment art for breakable blocks (type $07) in MGHZ is not extracted in this pass.']
    return out


def zone_sites(r):
    from z80dis import z80
    lo, hi = 0x97, 0xD2
    found = []
    regions = [('fixed', 0, 0x8000, 0)] + [(f'bank{b:02X}', b * 0x4000, 0x4000, 0x8000) for b in (0x0C, 0x1C, 0x1D, 0x1E)]
    for label, base, size, cpu0 in regions:
        off = 0
        while off < size:
            d = z80.decode(r[base + off:base + off + 4], cpu0 + off)
            n = d.len or 1
            raw = r[base + off:base + off + n]
            if n >= 3 and raw[-2] == lo and raw[-1] == hi and raw[0] in (0x3A, 0x32):
                found.append({'region': label, 'cpu': f'0x{cpu0 + off:04X}', 'instruction': z80.disasm(d)})
            off += n
    notes = {
        '0x6E7F': 'twist entry: zone 3 selects variant 2/3 (MGHZ)', '0x6EE8': 'twist: zone 3 sets +$38 = 2', '0x6F52': 'twist: zone 3 sets +$38 = 3',
        '0x6AB9': 'diagonal terrain spring: zone != 0 -> Y launch -5.5 (applies to MGHZ)', '0x6A5D': 'surface-1 handler: acts only for zone 5',
        '0x2A53': 'LoadRingArtPointers descriptor lookup (effects + ring art)', '0x78E5': 'level art table', '0x794F': 'palette selector table',
        '0x4E57': 'player/camera start loader', '0x4FDC': 'act header loader', '0x8000': 'object list pointer table (bank $1C)',
        '0xA909': 'ordinary sign prize table: odd zone -> $A962 (MGHZ = zone 3)', '0x9750': 'boss framework init: stores zone+1 in $D44E',
        '0x9777': 'boss framework state 1: trigger thresholds by zone+$D4A5', '0x97C9': 'boss framework state 2: camera target offsets by zone+$D4A5',
        '0x9AA4': 'THZ3 boss init (type $50)', '0xB015': 'boss framework init variant', '0xBA53': 'boss framework init variant'}
    for f in found:
        f['mghz_relevance'] = notes.get(f['cpu'], 'zone != 3 specific or unrelated; not exercised by MGHZ terrain/objects')
    return {'method': 'linear instruction sweep of fixed ROM and banks $0C/$1C/$1D/$1E for LD A,($D297)/LD ($D297),A; unannotated sites were read and are zone 4/5/6/8-specific or table lookups',
            'sites': found}


def dumps(value):
    return json.dumps(value, indent=2) + '\n'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom', type=Path)
    p.add_argument('--output', type=Path, default=OUTPUT)
    p.add_argument('--check', action='store_true')
    a = p.parse_args()
    text = dumps(build(L.load_rom(a.rom)))
    if a.check:
        if a.output.read_text(encoding='utf-8') != text:
            raise SystemExit('MGHZ foundation cache differs')
    else:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(text, encoding='utf-8')
    value = json.loads(text)
    print(json.dumps({k: v['census'] for k, v in value['acts'].items()}, indent=2))


if __name__ == '__main__':
    main()
