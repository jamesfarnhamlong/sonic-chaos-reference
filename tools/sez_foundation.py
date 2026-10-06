#!/usr/bin/env python3
"""Deterministic SEZ1-3 (Sleeping Egg Zone) level foundation manifest; no ROM/art dumps are emitted.

SEZ is ROM zone index 2 (THZ 0, GPZ 1, SEZ 2, MGHZ 3, AQZ 4, EEZ 5).  The object
census, enemy/boss reconnaissance and footwear placements live in ``sez_object_census.py``;
this module owns terrain, surfaces, rings, graphics, level-animation effects and the
corrected bank-relative block-mapping proof (SEZ's table is *not* bank aligned, so unlike
THZ/MGHZ the old table-relative decoder would be wrong here by $2A40).
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import level_package as L
import rom as R
import block_mapping_audit as BM
import mghz_foundation as F
from oracle import Oracle

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'data/rom-cache/sez/implementation-manifest.json'
ZONE = 2
ACTS = {f'sez{n + 1}': {'zone': ZONE, 'act': n, 'name': f'Sleeping Egg Zone Act {n + 1}'} for n in range(3)}
RESEARCH_BASE = 'e0f42f89a6ecabd6ed504ef318ea8170ce1a3f1f'
EFFECT_ID = 5
EFFECT_TILE = 0x158          # VRAM $2B00 / 32

# Evidence-backed surface registry.  'status' vocabulary:
#   ACCEPTED_SHARED   handler/consumer already researched and Windows-accepted in THZ/GPZ/MGHZ runtime
#   RESEARCHED_DATA   researched behaviour, POC core supports it, SEZ needs data/art integration
#   NEW_NEEDS_AUDIT   consumer found in ROM, no accepted research for this usage -> dedicated follow-up
SURFACES = {
    0x00: ('empty/background block', 'ACCEPTED_SHARED', 'docs/collision.md; $6C45', None),
    0x01: ('ordinary solid', 'ACCEPTED_SHARED', 'docs/collision.md; floor handler $6A5D returns unless zone == 5 (EEZ only)', None),
    0x02: ('ordinary solid (profile variants)', 'ACCEPTED_SHARED', 'docs/collision.md; handler $6A5B RET', None),
    0x03: ('slope/profile solid (modifier byte)', 'ACCEPTED_SHARED', 'docs/collision-geometry-audit.md; handler $6A5C RET', None),
    0x05: ('static floor spikes, block $3D (SEZ3 only): floor probe $6ACE', 'ACCEPTED_SHARED',
           'docs/platform-spike-collision-audit.md covers blocks $3C/$3D; $3D also occurs in THZ1/2 and AQZ2; ceiling spikes $3E/$3F are absent from SEZ', None),
    0x07: ('terrain ring blocks (probe $753E)', 'ACCEPTED_SHARED', 'docs/terrain-ring-collection.md; data/rom-cache/terrain-ring-collection.json', None),
    0x09: ('upright terrain spring', 'ACCEPTED_SHARED', 'docs/spring-interaction-audit.md; $6A75', None),
    0x0A: ('horizontal terrain spring (side path post-projection test)', 'ACCEPTED_SHARED', 'docs/spring-interaction-audit.md; $71FC/$7283', None),
    0x0C: ('crumbling-ledge candidate: handler $6B79 spawns type $13 at the probed cell (one-way block $AF, flags $4C)', 'NEW_NEEDS_AUDIT',
           'docs/platform-spike-collision-audit.md only lists THZ1/2 block $AF as a one-way surface (1 cell each); handler $6B79 and object $13 were never audited',
           'dedicated audit: $6B79 spawn dedup via $D356, object $13 states 0..3, rider capture $A344, falling pieces $A31B, cell restoration $A36A, SEZ 36 cells'),
    0x0D: ('breakable block $9B/$9C -> $9D + four type $07 fragments (attack posture required)', 'RESEARCHED_DATA',
           'docs/spring-interaction-audit.md row H; docs/mghz-m1-windows-followup.md; $6B2C -> $7898; side $72B6/$72DD; ceiling $7464',
           'POC surface-13 break adapter is Windows accepted in MGHZ; SEZ is dominated by it (253 cells) and its shard art is the zone-independent common-stream tile $66/$67 (sez_object_census fragment_art_proof)'),
    0x12: ('ramp-launch surface ($69B2), blocks $1F/$23', 'ACCEPTED_SHARED',
           'docs/spring-interaction-audit.md ("ramp launch ($69B2)"); same block IDs and cell semantics as THZ1/2, GPZ1/3, AQZ2', None),
    0x14: ('diagonal terrain spring, block $36 (SEZ3 x1; zone != 0 -> Y launch -5.5)', 'ACCEPTED_SHARED', 'docs/gpz-foundation-audit.md section 4; $6A90', None),
    0x16: ('floor break/bounce/reward surface, block $47 ($6AE3)', 'ACCEPTED_SHARED',
           'GPZ foundation runtime (surface $16 handling, Windows accepted) and THZ1 block $47 (docs/thz1-final-runtime-closure.md); identical collision header',
           'confirm SEZ art/palette of block $47 visually (board)'),
    0x1A: ('terrain "booster" probe surface, block $A7: needs floor bit, sets speed word $0700, state $10, sound $BD (dispatched only by the $753E probe)',
           'NEW_NEEDS_AUDIT', 'docs/terrain-ring-collection.md names surface $1A as a probe-dispatched type with unresolved name; never audited',
           'dedicated audit: direction/sign of $D373/$D516, requested state $10, probe parity/states that skip $753E, SEZ2 x2, SEZ3 x2 cells; block $A7 is the only block that draws the effect-5 animated tile $158 (arrow/pad scenery candidate, identity unproven)'),
}
CATEGORY_BLOCKS = {0x30: 'upright_spring', 0x31: 'upright_spring', 0x32: 'horizontal_spring', 0x33: 'horizontal_spring',
                   0x36: 'diagonal_spring', 0x3D: 'static_floor_spikes'}
CATEGORY_SURFACE = {0x0C: 'crumble_0C', 0x0D: 'breakable_0D', 0x12: 'ramp_12', 0x16: 'floor_break_16', 0x1A: 'booster_1A', 0x07: 'terrain_ring'}
EFFECT_DESCRIPTION = ('bank-$1D effect 5 ($81BF): zone-indexed VRAM tile animation. For zone 2 the two table entries copy 32 bytes from '
                      '$1D:$8DDD / $1D:$8DFD to VRAM $2B00 (tile $158), alternating every 3 updates; zones 0/1/3 are RET stubs; '
                      'zone 4 uses $2E20, zone 5 uses $3020; paused while $D44E != 0 (boss active)')

# canonical data -> original runtime -> possible GameMaker adapter, per SEZ-specific mechanic (no behaviour is invented)
SPECIAL_MECHANICS = [
    {'id': 'crumble_0C', 'status': 'NEW_NEEDS_AUDIT', 'surface': 0x0C, 'blocks': ['0xAF'], 'cells': {'sez1': 19, 'sez2': 16, 'sez3': 1},
     'canonical_data': 'block $AF: flags $4C (one-way, surface $0C), replacement block $B0 (flags 0); also THZ1/2 x1, AQZ, EEZ',
     'original_runtime': ['floor handler $6B79 (skipped when player +$19 bit 7 is set) spawns type $13 at the probed position ($D358,$D35A), once per distinct probed cell pointer ($D354 vs $D356) [CONTROLLED]',
                          'type $13 state 0 ($A2DD): snaps X to cell+14, Y to cell+24 and remembers the cell; state 1: 16-update callback $A344 lifts/holds the player at Y-40 while it stands on it, then $A36A restores cell via vector $0428 -> $6C1F with block $B0 (empty) unless asleep/left of camera X, plus four shard children $13 (parameters 3/8/5/1) that fall with +2.0 gravity and the common shard art [DECODED + BYTE-VERIFIED ASSEMBLY, not audited]'],
     'gamemaker_adapter_candidate': 'terrain-cell replacement + dynamic object; the POC already has a surface-13 cell-replacement adapter and a generic dynamic-object allocator',
     'package': 'S2'},
    {'id': 'booster_1A', 'status': 'NEW_NEEDS_AUDIT', 'surface': 0x1A, 'blocks': ['0xA7'], 'cells': {'sez1': 0, 'sez2': 2, 'sez3': 2},
     'canonical_data': 'block $A7: flags $9A (solid, surface $1A, priority tiles), draws effect-5 animated tile $158 (two frames, 3 updates each)',
     'original_runtime': ['only dispatched by the terrain probe $753E (the same probe as terrain rings): if player +$22 bit 1 (floor) is set: $D373 = $D516 = $0700, +$03 bit 1 set / bit 0 clear, requested state $10, sound $BD [CONTROLLED, exhaustive over +$22]',
                          'probe parity/states: the accepted $753E state-reach tables apply (loop $0C/$0D/$13, twist $22, act-clear $20 do not probe)'],
     'gamemaker_adapter_candidate': 'terrain-probe interaction in the existing ring-probe slot; effect-5 as a two-frame tile animation (VRAM $2B00)',
     'package': 'S2'},
    {'id': 'breakable_0D', 'status': 'RESEARCHED_DATA', 'surface': 0x0D, 'blocks': ['0x9B', '0x9C', '0x9D'], 'cells': {'sez1': 145, 'sez2': 100, 'sez3': 8},
     'canonical_data': 'blocks $9B/$9C (flags $8D) -> replacement $9D (flags 0); shard art = common-stream tile $66/$67 (zone independent)',
     'original_runtime': ['$6B2C -> $7898: block becomes $9D and four type $07 fragments are emitted in one update (docs/mghz-m1-windows-followup.md)'],
     'gamemaker_adapter_candidate': 'accepted MGHZ surface-13 break adapter; SEZ makes it the dominant terrain, so exercise it first', 'package': 'S1'},
    {'id': 'ramp_12', 'status': 'ACCEPTED_SHARED', 'surface': 0x12, 'blocks': ['0x1F', '0x23'], 'cells': {'sez1': 2, 'sez2': 6, 'sez3': 2},
     'canonical_data': 'blocks $1F/$23 flags $92', 'original_runtime': ['ramp-launch handler $69B2 (docs/spring-interaction-audit.md; THZ first curve)'],
     'gamemaker_adapter_candidate': 'existing THZ ramp launch', 'package': 'S1'},
    {'id': 'floor_break_16', 'status': 'ACCEPTED_SHARED', 'surface': 0x16, 'blocks': ['0x47'], 'cells': {'sez1': 5, 'sez2': 18, 'sez3': 4},
     'canonical_data': 'block $47 (flags $96): terrain monitor picture', 'original_runtime': ['$6AE3 floor break/bounce/reward (GPZ foundation; THZ block $47 reward)'],
     'gamemaker_adapter_candidate': 'existing GPZ/THZ block-$47 reward handling', 'package': 'S1'},
    {'id': 'effect_5_tile_158', 'status': 'ACCEPTED_ADAPTER_PATTERN', 'surface': None, 'blocks': ['0xA7'], 'cells': {},
     'canonical_data': 'two 32-byte frames $1D:$8DFD / $1D:$8DDD to VRAM $2B00 (tile $158)',
     'original_runtime': ['bank-$1D effect 5 ($81BF): every 3 updates, alternating, paused while $D44E != 0 [CONTROLLED]'],
     'gamemaker_adapter_candidate': 'same two-frame strip pattern as the accepted MGHZ $1A8/$1A9 strip; pause during the SEZ3 boss', 'package': 'S1'},
]
IMPLEMENTATION_PACKAGES = [
    {'id': 'S1', 'name': 'SEZ three-act foundation', 'scope': 'terrain/art/palettes (visual package approved 2026-10-05), 4095-cell ceiling, rings (terrain only, no $09), springs ($09/$0A/$14 terrain, $26 mapped incl. new span $8C), '
     'monitors ($10 params 1/2/4/6), ordinary sign clear (SEZ1/2), Spring Shoes ($2F, base $94) and Rocket Shoes, platform $28 params $83/$84, breakable $0D, ramp $12, block $47, static spikes $3D, '
     'effect 5 tile animation, shared support ($0F/$34/$0A/$06/$03/$07)', 'blocked_by': [], 'omits': ['$20', '$23', '$28 params $86/$04', 'surfaces $0C/$1A', '$54 boss']},
    {'id': 'S2', 'name': 'SEZ terrain mechanics audit', 'scope': 'surface $0C/$13 crumble and surface $1A booster (small oracle audits, 36+4 cells)', 'blocked_by': []},
    {'id': 'S3', 'name': 'SEZ platform state 7', 'scope': 'type $28 parameter $86 (3 placements) and parameter $04 no-sag variant (1 placement)',
     'research_status': 'CLOSED', 'poc_status': 'pending implementation and Windows acceptance',
     'runtime_contract': 'data/rom-cache/sez/platform-28-runtime.json', 'blocked_by': []},
    {'id': 'S4', 'name': 'SEZ enemies $20/$23', 'scope': 'contact/defeat/hop timing, art orientation (bit4), lifecycle (15 placements; SEZ only)', 'blocked_by': []},
    {'id': 'S5', 'name': 'SEZ3 boss $54/$55', 'scope': 'dedicated boss audit: 13-state table (own states 3,6..12), selector $15, palette 14, health byte 8, child $55, arena/camera row 2, clear gate; '
     'support types $12/$34/$0F/$0A are shared', 'blocked_by': ['S1 for the SEZ3 act to exist']},
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def hexb(v, n=2):
    return f'0x{v:0{n}X}'


# --- level effects (zone-aware variant of mghz_foundation.run_effect) ----------------
def run_effect(r, effect_id, updates, zone=ZONE, d44e=0, bg_palette=23, sprite_palette=8):
    """Execute the original bank-$1D effect routine on one slot and record palette/VRAM writes."""
    o = Oracle(r)
    m, cpu = o.mem, o.cpu
    o.bank(2, 0x1D)
    m[0xD12B] = 0x1D
    m[0xD297] = zone
    m[0xD492], m[0xD44E] = 0, d44e
    slot = F.EFFECT_SLOTS[0]
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
    jump = [F.u16(r, F.bank_file(0x1D, F.EFFECT_JUMP_TABLE) + 2 * i) for i in range(0x12)]
    ids = sorted(set(desc['effect_ids']) - {0})
    out = {'dispatcher': {'bank': 0x1D, 'cpu': 0x8000, 'rom': F.bank_file(0x1D, 0x8000), 'gate': '$D492 (BGPalleteControlByte) must be zero',
                          'slots': [f'0x{s:04X}' for s in F.EFFECT_SLOTS], 'slot_stride': 8, 'jump_table_cpu': F.EFFECT_JUMP_TABLE},
           'descriptor_effect_ids': desc['effect_ids'], 'effects': {}}
    for eid in ids:
        running = run_effect(r, eid, 48)
        paused = run_effect(r, eid, 48, d44e=1)
        entry = {'routine_cpu': f'0x{jump[eid]:04X}', 'description': EFFECT_DESCRIPTION, 'first_events': running[:8],
                 'events_in_48_updates': len(running), 'events_with_D44E_nonzero_in_48_updates': len(paused),
                 'update_period': [b['update'] - a['update'] for a, b in zip(running, running[1:])][:4]}
        table = F.bank_file(0x1D, 0x81F2)
        entry['zone_table'] = {f'zone{z}': [f'0x{F.u16(r, table + 4 * z + 2 * k):04X}' for k in range(2)] for z in range(6)}
        entry['zone_gating_events_in_48_updates'] = {f'zone{z}': len(run_effect(r, eid, 48, zone=z)) for z in range(6)}
        entry['frames'] = [{'source_cpu': c['source_cpu'], 'sha256': c['sha256'], 'vram': c['vram'], 'length': c['length']} for c in
                           (running[0]['vram_copies'] + running[1]['vram_copies'])] if len(running) >= 2 else []
        out['effects'][str(eid)] = entry
    out['phase_note'] = 'slot counters start at 0 when the act loads; absolute phase against the global clock is not claimed'
    return out


# --- act package --------------------------------------------------------------
def terrain_categories(r, cells, width):
    cats = {}
    for i, b in enumerate(cells):
        s = R.header(r, b)['flags'] & 31
        if b in CATEGORY_BLOCKS:
            c = CATEGORY_BLOCKS[b]
        elif s in CATEGORY_SURFACE:
            c = CATEGORY_SURFACE[s]
        else:
            continue
        cats.setdefault(c, []).append(F.cell_record(i, b, width))
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
    in_layout = set(cells)
    effect_blocks = sorted(f'0x{b["block_id"]:02X}' for b in blocks if EFFECT_TILE in b['tile_ids'] and b['block_id'] in in_layout)
    rings = {'terrain': a['terrain_rings'], 'object09': L.object_rings(a), 'presence_and_replacement_tables': a['semantics'],
             'collection_contract': 'accepted THZ/GPZ/MGHZ terrain pipeline unchanged ($753E anchor + parity probe); SEZ places no type $09 rings'}
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
                       'unloaded_cells': [F.cell_record(i, a['cells'][i], width) for i in range(a['runtime_cells'], len(a['cells']))]},
            'blocks': blocks, 'terrain_interactions': inter, 'rings': rings,
            'animated_terrain_blocks': {f'0x{EFFECT_TILE:03X}': effect_blocks},
            'census': {'distinct_layout_blocks': len(in_layout),
                       'surface_cell_counts': {f'0x{s:02X}': n for s, n in sorted(Counter(R.header(r, b)['flags'] & 31 for b in cells).items())},
                       'terrain_rings': len(rings['terrain']), 'object09_rings': len(rings['object09']),
                       'priority_blocks_in_layout': sorted({f"0x{b['block_id']:02X}" for b in blocks if b['priority_tiles'] and b['in_initial_layout']}),
                       'terrain_interactions': {k: len(v) for k, v in inter.items()}},
            'graphics': {'static_vram_loads': a['vram_loads'], 'vram_sha256': digest(a['vram']),
                         'palettes': {n: {'rom': d['palette'][n + '_rom'], 'index': d['palette'][n + '_index'],
                                          'cram': list(r[d['palette'][n + '_rom']:d['palette'][n + '_rom'] + 16])} for n in ('background', 'sprite')}}}


def mapping_pointer_check(r):
    """SEZ table sits at $11:$AA40 (file $46A40), 0x2A40 into its bank: the GPZ decoder mistake would apply."""
    out = {'zone': ZONE, 'acts': {}}
    pointers_all = {}
    for act in range(3):
        h = L.act_header(r, ZONE, act)
        bank = h['block_mapping_bank']
        o = Oracle(r)
        o.mem[0xD297], o.mem[0xD298] = ZONE, act
        o.call(0x4FDC)
        loader = [o.mem[0xD162], o.word(0xD164)]
        o.cpu.a = o.mem[0xD162]
        o.call(0x1C6F)
        checked = mismatches = old_differs = 0
        pointers, old_wrong = [], []
        attrs = bytearray()
        table_rel = h['block_mapping_rom'] % 0x4000
        for block in range(256):
            m = L.block_mapping(r, h['block_mapping_rom'], block)
            for vertical in (False, True):
                cpu = BM.original_pointer(o, h['block_mapping_cpu'], block, vertical)
                checked += 1
                mismatches += cpu != m['cpu'] or bytes(o.mem[cpu:cpu + 32]) != r[m['rom']:m['rom'] + 32]
            wrong = h['block_mapping_rom'] + m['cpu'] - 0x8000          # the historical (GPZ) decoder formula
            old_wrong.append(wrong)
            old_differs += r[wrong:wrong + 32] != r[m['rom']:m['rom'] + 32]
            pointers.append(m['rom'])
            attrs.extend(r[m['rom']:m['rom'] + 32])
        pointers_all[act] = pointers
        out['acts'][f'sez{act + 1}'] = {
            'bank': bank, 'bank_file_base': bank * 0x4000, 'table_cpu': h['block_mapping_cpu'], 'table_rom': h['block_mapping_rom'],
            'table_offset_inside_bank': table_rel, 'old_table_relative_error_bytes': table_rel,
            'masked_by_alignment': table_rel == 0, 'loader_registers_d162_d164': loader,
            'original_consumer_checks': checked, 'original_consumer_mismatches': mismatches,
            'blocks_where_historical_formula_reads_different_bytes': old_differs,
            'resolved_offsets_sha256': digest(b''.join(p.to_bytes(4, 'little') for p in pointers)),
            'historical_wrong_offsets_sha256': digest(b''.join(p.to_bytes(4, 'little') for p in old_wrong)),
            'mapping_attributes_sha256': digest(attrs)}
    out['tables_identical_across_acts'] = len({a['table_rom'] for a in out['acts'].values()}) == 1
    out['formula'] = 'mappingFile = bank*$4000 + raw_pointer_word - $8000 (word is an absolute CPU address inside the bank)'
    out['verdict'] = ('SEZ does NOT inherit the GPZ decoder mistake: shared L.block_mapping is bank-relative and agrees with both original '
                      'consumers ($5316 horizontal, $53DF vertical) for all 256 blocks in all three acts; the table is NOT bank aligned '
                      '(+$2A40), so the old table-relative formula would be wrong for SEZ and is shown here only as a contrast hash')
    return out


def collision_table_check(r):
    """Collision headers are zone independent: every zone/act points at bank $0E:$8000 (file $38000)."""
    rows = []
    for z in range(6):
        for a in range(3):
            d = F.ring_art_descriptor(r, z, a)
            rows.append(d['collision_table_cpu'])
    return {'collision_table_cpu_all_zones': sorted(set(f'0x{v:04X}' for v in rows)), 'header_table_rom': '0x38000',
            'consequence': 'a block ID has the same surface/profile in every zone; SEZ reuse of a surface rests on the block ID plus the shared handler tables'}


# --- zone-dependent code ---------------------------------------------------------------
SITE_NOTES = {
    '0x2A53': 'LoadRingArtPointers: zone -> descriptor ($2A9A): SEZ row = ring frames VRAM $29A0, effect IDs [5,0,0,0]',
    '0x78E5': 'level art table (zone*3+act): SEZ rows decoded in the act descriptors',
    '0x794F': 'palette selector table (zone*3+act): SEZ background palette 23, sprite palette 8',
    '0x4E57': 'player/camera start loader (SEZ rows executed by tests)', '0x4FDC': 'act header loader (SEZ rows executed by tests)',
    '0x8000': 'object list pointer table (bank $1C), SEZ rows decoded', '0x81E0': 'effect 5 zone table: SEZ = tile $158 two-frame animation',
    '0x83D8': 'effect 7 palette table (zone*4+..): not an SEZ effect (SEZ effect IDs are [5])',
    '0xA909': 'ordinary sign prize table: (zone+1) bit0: zone 2 -> 3 -> carry set -> first table $A919 (THZ/SEZ parity), MGHZ/GPZ use $A962',
    '0x9750': 'boss framework init: stores zone+1 = 3 in $D44E (SEZ3 boss $54 shares it)', '0x9777': 'boss framework state 1 trigger thresholds: row zone+$D4A5 (SEZ row 2)',
    '0x97C9': 'boss framework state 2 camera-target offsets: row zone+$D4A5 (SEZ row 2)',
    '0x2D5B': 'act-3 end table $2D84 (zone-indexed word; SEZ = $0096): results/transition value, semantics deferred with the results screen',
    '0x322E': 'results-screen object table $32CA (zone-indexed pointer; SEZ = $B29F): presentation, deferred with results screen',
    '0x79FE': 'zone-indexed presentation pointer table $A3A0 (card/results art): deferred presentation',
    '0x18A0': 'zone*3+act index (continue/select/title bookkeeping)', '0x187B': 'zone copy for save/continue bookkeeping',
    '0x6AB9': 'diagonal terrain spring: zone != 0 -> Y launch -5.5 (applies to SEZ block $36)', '0x6A5D': 'surface-1 handler: acts only for zone 5',
    '0x9AA4': 'THZ3 boss init (type $50): zone+1 into $D44E', '0xB015': 'boss framework init variant', '0xBA53': 'boss framework init variant (selector $1A)'}


def zone_sites(r):
    from z80dis import z80
    out = []
    base = F.zone_sites(r)
    for s in base['sites']:
        cpu = int(s['cpu'], 16)
        region = s['region']
        off = cpu if region == 'fixed' else int(region[4:], 16) * 0x4000 + cpu - 0x8000
        cpu0, pos, const, kind = cpu, off, None, 'table_or_copy'
        for _ in range(5):
            d = z80.decode(r[pos:pos + 4], cpu0)
            text = z80.disasm(d)
            parts = text.replace(',', ' ').split()
            if parts[0].upper() == 'CP' and len(parts) == 2:
                try:
                    const, kind = int(parts[1], 0), 'compare'
                except ValueError:
                    pass
                break
            if parts[0].upper() == 'OR' and parts[1].upper() == 'A':
                const, kind = 0, 'zero_test'
                break
            pos += d.len
            cpu0 += d.len
        applies = None
        if kind in ('compare', 'zero_test'):
            applies = const == ZONE
        site = {'region': region, 'cpu': s['cpu'], 'instruction': s['instruction'], 'kind': kind, 'constant': const,
                'applies_to_sez': applies, 'note': SITE_NOTES.get(s['cpu'])}
        if kind in ('compare', 'zero_test') and site['note'] is None:
            site['note'] = f'zone gate against {const}: SEZ (2) falls through' if not applies else 'ZONE 2 GATE'
        out.append(site)
    return {'method': base['method'] + '; each site then classified by its first CP/OR A or marked a table lookup',
            'sites': out, 'zone_2_gates': [s['cpu'] for s in out if s['applies_to_sez']],
            'conclusion': 'no code site tests zone == 2: SEZ differs from the shared engine only through zone-indexed tables '
                          '(art/palette/object lists, ring+effect descriptor, effect-5 frames, boss tables, prize-table parity) and through block data'}


def surface_oracle(r):
    """Controlled original-routine results for the two new surface handlers."""
    out = {}
    # $6B79 (surface $0C): spawn type $13 at the probed cell, deduplicated by $D354/$D356.
    o = Oracle(r)
    m = o.mem
    o.cpu.ix = 0xD500
    m[0xD519] = 0
    o.word(0xD354, 0xC123)
    o.word(0xD356, 0xC122)
    o.word(0xD358, 0x0234)
    o.word(0xD35A, 0x00C8)
    for i in range(16):
        m[0xD540 + i * 0x40] = 0
    o.call(0x6B79)
    slot = next((i for i in range(16) if m[0xD540 + i * 0x40]), None)
    first = None if slot is None else {'slot': slot, 'type': m[0xD540 + slot * 0x40], 'parameter_3f': m[0xD540 + slot * 0x40 + 0x3F],
                                       'x': o.word(0xD540 + slot * 0x40 + 0x11), 'y': o.word(0xD540 + slot * 0x40 + 0x14)}
    spawned_after_first = sum(1 for i in range(16) if m[0xD540 + i * 0x40])
    d518_after_first = o.word(0xD518)
    o.call(0x6B79)
    spawned_after_second = sum(1 for i in range(16) if m[0xD540 + i * 0x40])
    m[0xD519] = 0x80
    o.word(0xD354, 0xC124)
    o.call(0x6B79)
    spawned_with_bit7 = sum(1 for i in range(16) if m[0xD540 + i * 0x40])
    out['surface_0c_handler_6b79'] = {'first_call': first, 'objects_after_first_call': spawned_after_first, 'objects_after_repeat_same_cell': spawned_after_second,
                                     'objects_after_new_cell_with_player_+19_bit7_set': spawned_with_bit7,
                                     'stored_cell_pointer_d356': o.word(0xD356), 'player_d518_after_first_call': d518_after_first,
                                     'evidence': 'CONTROLLED ROUTINE RESULT ($6B79 executed on the original ROM)'}
    # $7646 (surface $1A): needs +$22 bit 1.
    results = {}
    for flag in (0, 2):
        o = Oracle(r)
        m = o.mem
        o.cpu.ix = 0xD500
        m[0xD522] = flag
        m[0xD503] = 0x01
        m[0xD502] = 0x05
        o.call(0x7646)
        results[f'floor_bit_{"set" if flag else "clear"}'] = {'d373': o.word(0xD373), 'd516': o.word(0xD516), 'requested_state_02': m[0xD502],
                                                               'player_03': m[0xD503], 'sound_de04': m[0xDE04]}
    out['surface_1a_handler_7646'] = dict(results, evidence='CONTROLLED ROUTINE RESULT ($7646 executed); caller is the $753E terrain probe only')
    return out


def build(r):
    if digest(r) != L.ROM_SHA256:
        raise ValueError('Expected canonical Europe v1.2 ROM')
    consumers, floor, right, left, ceiling = F.surface_consumers(r)
    out = {'format': 1, 'rom_sha256': L.ROM_SHA256, 'research_base': RESEARCH_BASE,
           'scope': 'SEZ1-3 level foundation: terrain, surfaces, rings, graphics and level animation; decoded metadata, not a ROM/art dump',
           'zone': {'index': ZONE, 'evidence': 'object list $70E00 (bank $1C) / layout $54000 / mapping $46A40 (bank $11) / art $60000 match the community offsets table; '
                    'tools/block_mapping_audit.py names zones thz,gpz,sez,mghz,apz,eez'},
           'coordinate_policy': 'mapped anchor = stored-256; terrain origin = cell*32; presentation never changes the collision anchor',
           'status_vocabulary': {'ACCEPTED_SHARED': 'researched and Windows-accepted THZ/GPZ/MGHZ runtime path',
                                 'RESEARCHED_DATA': 'researched behaviour; SEZ needs data/art/integration only',
                                 'NEW_NEEDS_AUDIT': 'consumer located in ROM; no accepted research for this usage'},
           'acts': {}}
    for key, meta in ACTS.items():
        out['acts'][key] = build_act(r, key, meta)
    out['mapping_pointer'] = mapping_pointer_check(r)
    descs = [F.ring_art_descriptor(r, ZONE, a) for a in range(3)]
    out['terrain_ring_animation'] = dict(F.terrain_ring_animation(r, descs[0]), descriptor=descs[0],
                                         per_act_descriptors_identical=all((d['descriptor_rom'], d['raw']) == (descs[0]['descriptor_rom'], descs[0]['raw']) for d in descs))
    out['level_effects'] = level_effects(r, descs[0])
    out['collision_table'] = collision_table_check(r)
    surf = Counter()
    for a in out['acts'].values():
        for k, v in a['census']['surface_cell_counts'].items():
            surf[k] += v
    out['surface_census'] = {
        'consumers': consumers,
        'sez_surfaces': {f'0x{s:02X}': {'cells': {k: a['census']['surface_cell_counts'].get(f'0x{s:02X}', 0) for k, a in out['acts'].items()},
                                        'blocks': sorted({f"0x{b['block_id']:02X}" for a in out['acts'].values() for b in a['blocks'] if b['surface'] == s and b['in_initial_layout']}),
                                        'floor_handler': f'0x{floor[s]:04X}', 'side_consumer': s in {x for x, _ in right + left} or s == 0x0A,
                                        'ceiling_consumer': s in {x for x, _ in ceiling},
                                        'meaning': SURFACES[s][0] if s in SURFACES else 'UNRESOLVED',
                                        'status': SURFACES[s][1] if s in SURFACES else 'UNRESOLVED',
                                        'evidence': SURFACES[s][2] if s in SURFACES else None, 'follow_up': SURFACES[s][3] if s in SURFACES else None}
                         for s in sorted(int(k, 16) for k in surf)},
        'six_zone_cell_counts': F.six_zone_surfaces(r),
        'absent_from_sez': 'twist $17, strip $19, oil $1B, isometric $1C, ceiling-spike blocks $3E/$3F, mapped-plane-switch blocks (no block has a different alternate-plane header)',
        'controlled_handlers': surface_oracle(r)}
    out['zone_dependent_code'] = zone_sites(r)
    out['environment'] = {'water': 'not present: the water-timer code ($4B46) and the $D443 consumers gate on zone 4 acts 0-1; none of the SEZ zone-gates fire',
                          'camera_triggers_or_locks': 'none in the level header; only the shared boss framework (SEZ3 $54) locks the camera',
                          'loop_or_plane_switching': 'none: no SEZ block has a distinct alternate-plane header; surface $0C is not a loop surface (see surface census)'}
    out['source_regions'] = {n: F.region(r, *v) for n, v in {
        'start_loader': (0, 0x4E57, 0x4E98), 'header_loader': (0, 0x4FDC, 0x5038),
        'surface_0c_handler': (0, 0x6B79, 0x6BAA), 'surface_1a_handler': (0, 0x7646, 0x7666), 'surface_12_handler': (0, 0x69B2, 0x6A18),
        'breakable_handlers': (0, 0x7857, 0x78E1), 'object_spawner_5eb7': (0, 0x5EB7, 0x5EE1), 'effect_spawner_5e9c': (0, 0x5E9C, 0x5EB7),
        'ring_animation': (0x1D, 0x850A, 0x8555), 'effect_dispatcher': (0x1D, 0x8000, 0x8052), 'effect_5': (0x1D, 0x81BF, 0x8259),
        'object_13_callbacks': (0x0C, 0xA2DD, 0xA3B0)}.items()}
    out['special_mechanics'] = SPECIAL_MECHANICS
    out['implementation_packages'] = IMPLEMENTATION_PACKAGES
    out['platform_runtime'] = {'status': 'RESEARCHED_DATA', 'parameters': ['0x86', '0x04'],
                               'cache': 'data/rom-cache/sez/platform-28-runtime.json',
                               'audit': 'docs/sez-platform-28-audit.md',
                               'summary': '$86: contact-triggered timed right-and-return excursion, aux1*16 px per leg; $04: state5 with weight sag disabled, not an axis swap.',
                               'poc_acceptance': 'pending'}
    out['unresolved'] = [
        'Surface $0C / block $AF crumbling-ledge semantics (spawn $6B79 confirmed; object $13 behaviour is decoded, not audited).',
        'Surface $1A / block $A7 booster semantics (handler $7646 executed; block $A7 carries the effect-5 animated tile; direction rule and states that skip the $753E probe are open).',
        'Type $07/$13 shard art is the common-stream tile $66/$67 (zone independent); only its SEZ sprite-palette sign-off remains (shared art board).',
        'Effect-5 tile $158 (VRAM $2B00) animation: which scenery blocks show it is listed; effect phase vs the global clock is not claimed.',
        'Zone-indexed results/act-3 tables ($2D84, $32CA, $A3A0) belong to the deferred results-screen presentation.']
    return out


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
            raise SystemExit('SEZ foundation cache differs')
    else:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(text, encoding='utf-8')
    value = json.loads(text)
    print(json.dumps({k: v['census'] for k, v in value['acts'].items()}, indent=2))


if __name__ == '__main__':
    main()

