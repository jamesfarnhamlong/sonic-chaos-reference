#!/usr/bin/env python3
"""MGHZ1-3 object census, six-zone reuse census, footwear placements, enemy and boss reconnaissance.

Census only: decoded records, state-table structure, art/palette sources and controlled
original-routine initialisation results.  It is not a behaviour audit; every type that
needs one is classified and listed.  No ROM bytes or pixels are emitted (hashes only).
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import level_package as L
import rom as R
import thz1_animation_reach as A
import thz1_object_assets as G
import thz1_type18_dynamic_graphics as D
import thz3_boss_support as B
import mapped_object_registration as M
import mghz_foundation as F
from oracle import Oracle
from platform_spike_collision import SLOT

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'data/rom-cache/mghz/object-census.json'
ZONE_NAMES = ('thz', 'gpz', 'sez', 'mghz', 'aqz', 'eez')
STATUSES = ('REUSED_SUPPORTED', 'REUSED_NEEDS_DATA', 'NEW_ART_REUSED_RUNTIME', 'NEW_NEEDS_RESEARCH', 'BOSS', 'UNRESOLVED')
CMD_LEN = {0: 0, 1: 2, 2: 4, 3: 1, 4: 6, 5: 4, 6: 1, 7: 2, 9: 2, 11: 2, 12: 2, 14: 1, 15: 2}
REWARDS = {1: 'ten rings', 2: 'life counter +1', 4: 'Rocket Shoes', 6: 'invincibility'}
POC_COMMIT = '84c3e10'

# type -> (category, status, identification, canonical research, POC at 84c3e10 read-only)
REGISTRY = {
    0x09: ('collectible', 'REUSED_SUPPORTED', 'object ring (visible)', 'docs/thz1-final-runtime-closure.md; data/rom-cache/thz1/object-09.json', 'implemented (accepted THZ/GPZ)'),
    0x10: ('monitor', 'REUSED_SUPPORTED', 'monitor', 'docs/object-10.md; docs/thz2-thz3-object-deltas.md; docs/powerup-shoes-audit.md', 'implemented; Rocket Shoes reward (param 4) lacks player state $11'),
    0x18: ('support', 'REUSED_SUPPORTED', 'goal sign', 'docs/object-18-act-clear.md', 'implemented (THZ1/2, GPZ1/2)'),
    0x1B: ('hazard', 'REUSED_SUPPORTED', 'moving spike', 'docs/platform-spike-collision-audit.md', 'implemented'),
    0x21: ('enemy', 'NEW_ART_REUSED_RUNTIME', 'ground patrol robot with spring top (numeric identity only)', 'docs/object-21.md; docs/thz1-visual-anchor-closure.md',
           'partial: THZ states 3/4 only; MGHZ records use flags $10 = states 5/6 and new art'),
    0x24: ('enemy', 'NEW_NEEDS_RESEARCH', 'proximity-triggered horizontal mover (numeric identity only)', None, 'absent'),
    0x28: ('platform', 'REUSED_SUPPORTED', 'platform', 'docs/platform-spike-collision-audit.md; docs/isometric-platform-audit.md', 'implemented for THZ $0A and GPZ $83/$89/$05'),
    0x2E: ('hazard', 'NEW_NEEDS_RESEARCH', 'self-spawning splash/effect object, zero contact extents (numeric identity only)', None, 'absent'),
    0x2F: ('footwear', 'REUSED_NEEDS_DATA', 'Spring Shoes pickup', 'docs/powerup-shoes-audit.md', 'absent (footwear package deferred)'),
    0x56: ('boss', 'BOSS', 'MGHZ3 boss/controller', None, 'absent'),
}
REUSED_FROM = {0x09: 'THZ/GPZ/AQZ/EEZ', 0x10: 'all six zones', 0x18: 'all six zones', 0x1B: 'THZ/GPZ/SEZ', 0x21: 'THZ (same ROM runtime, different art/flags)',
               0x28: 'THZ/GPZ/SEZ/EEZ', 0x2F: 'SEZ (shared footwear research)'}
PLATFORM_PARAMS = {0x0A: 'THZ lift family (accepted)', 0x83: 'state 4 sag/delay/fall (GPZ accepted; MGHZ art = 8 tiles at $6A)',
                   0x89: 'state 10 horizontal reversal (GPZ accepted)', 0x05: 'state 13 -> 6 touch-start vertical mover (GPZ accepted)'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def u16(r, pos):
    return r[pos] | r[pos + 1] << 8


def s16(v):
    return v - 0x10000 if v & 0x8000 else v


def hexb(v, n=2):
    return f'0x{v:0{n}X}'


# --- state tables and scripts -------------------------------------------------
def state_table(r, t):
    bank = A.animation_bank(t)
    cpu = u16(r, A.ANIM_TYPE_TABLE_ROM + (t - 1) * 2)
    off = A.cpu_to_rom(bank, cpu)
    words = []
    while len(words) < 64:
        w = u16(r, off + 2 * len(words))
        if not 0x8000 <= w <= 0xBFFF:
            break
        words.append(w)
        own = [x for x in words if x > cpu]
        if own and cpu + 2 * len(words) >= min(own):
            break
    return {'type_id': t, 'type_table_entry_rom': A.ANIM_TYPE_TABLE_ROM + (t - 1) * 2, 'bank': bank, 'state_table_cpu': cpu,
            'state_table_rom': off, 'state_count': len(words), 'state_script_cpus': words}


def decode_script(r, bank, start, stop_cpu=None, limit=80):
    """Static script walk; returns (ops, cleanly_terminated)."""
    pc, seen, ops = start, set(), []
    while len(ops) < limit:
        if stop_cpu is not None and pc >= stop_cpu:
            return ops, False
        if pc in seen:
            ops.append({'cpu': pc, 'op': 'loops_back'})
            return ops, True
        seen.add(pc)
        o = A.cpu_to_rom(bank, pc)
        b = r[o]
        if b != 0xFF:
            ops.append({'cpu': pc, 'op': 'record', 'duration': b, 'frame': r[o + 1], 'callback': u16(r, o + 2)})
            pc += 4
            continue
        c = r[o + 1]
        if c not in CMD_LEN:
            ops.append({'cpu': pc, 'op': 'unknown', 'command': c})
            return ops, False
        a = list(r[o + 2:o + 2 + CMD_LEN[c]])
        w = lambda i: a[i] | a[i + 1] << 8
        e = {'cpu': pc, 'command': c}
        pc += 2 + CMD_LEN[c]
        if c == 0:
            e['op'] = 'restart_state'
            ops.append(e)
            return ops, True
        if c == 3:
            e.update(op='request_state', state=a[0])
            ops.append(e)
            return ops, True
        if c == 1:
            e.update(op='call', target=w(0))
        elif c == 2:
            e.update(op='velocity_8_8', x=s16(w(0)), y=s16(w(2)))
        elif c == 4:
            e.update(op='spawn', type=a[0], dx=s16(w(1)), dy=s16(w(3)), parameter=a[5])
        elif c == 5:
            e.update(op='call_and_set_callback', target=w(0), callback=w(2))
        elif c == 6:
            e.update(op='sound', sound=a[0])
        elif c == 7:
            e.update(op='jump', target=w(0))
            pc = w(0)
            stop_cpu = None             # a jump leaves the back-to-back script area
        elif c == 9:
            e.update(op='set_field', offset=a[0], value=a[1])
        elif c == 11:
            e.update(op='and_field', offset=a[0], mask=a[1])
        elif c == 12:
            e.update(op='or_field', offset=a[0], mask=a[1])
        elif c == 14:
            e.update(op='set_loop_counter', count=a[0])
        elif c == 15:
            e.update(op='loop_jump', target=w(0))
        ops.append(e)
    return ops, False


def state_scripts(r, t):
    """Decode every state script.

    Each script is bounded by the next-higher state start (scripts are laid out back to back).
    The highest script may end without a terminator (it relies on a delete callback); it is
    bounded by the lowest callback/call target of the other states that lies above its start.
    """
    tab = state_table(r, t)
    bank = tab['bank']
    starts = tab['state_script_cpus']
    first = [decode_script(r, bank, p)[0] for p in starts]
    states = []
    for n, p in enumerate(starts):
        above = sorted({q for q in starts if q > p})
        stop = above[0] if above else None
        if stop is None:
            others = [x['callback'] for m, ops in enumerate(first) if m != n for x in ops if x['op'] in ('record', 'call_and_set_callback') and x['callback'] > p]
            others += [x['target'] for m, ops in enumerate(first) if m != n for x in ops if x['op'] in ('call', 'call_and_set_callback') and x['target'] > p]
            stop = min(others) if others else None
        ops, ok = decode_script(r, bank, p, stop_cpu=stop)
        states.append({'state': n, 'script_cpu': p, 'cleanly_terminated': ok, 'bounded_by_cpu': stop, 'ops': ops})
    callbacks = sorted({x['callback'] for s in states for x in s['ops'] if x['op'] == 'record'} |
                       {x['callback'] for s in states for x in s['ops'] if x['op'] == 'call_and_set_callback'})
    calls = sorted({x['target'] for s in states for x in s['ops'] if x['op'] in ('call', 'call_and_set_callback')})
    return dict(tab, states=states, callbacks=callbacks, calls=calls,
                frames=sorted({x['frame'] for s in states for x in s['ops'] if x['op'] == 'record'}),
                spawns=[dict(state=s['state'], type=x['type'], dx=x['dx'], dy=x['dy'], parameter=x['parameter']) for s in states
                        for x in s['ops'] if x['op'] == 'spawn'],
                sets_bit4=any(x['op'] == 'or_field' and x['offset'] == 4 and x['mask'] & 0x10 for s in states for x in s['ops']),
                clears_bit4=any(x['op'] == 'and_field' and x['offset'] == 4 and not x['mask'] & 0x10 for s in states for x in s['ops']))


def public_script(sc):
    """JSON-ready script summary with hex CPU addresses."""
    states = []
    for s in sc['states']:
        ops = []
        for x in s['ops']:
            y = {k: (hexb(v, 4) if k in ('cpu', 'callback', 'target') else v) for k, v in x.items()}
            ops.append(y)
        states.append({'state': s['state'], 'script_cpu': hexb(s['script_cpu'], 4), 'cleanly_terminated': s['cleanly_terminated'],
                       'bounded_by_cpu': s['bounded_by_cpu'] and hexb(s['bounded_by_cpu'], 4), 'ops': ops})
    return {'bank': sc['bank'], 'type_table_entry_rom': sc['type_table_entry_rom'], 'state_table_cpu': hexb(sc['state_table_cpu'], 4),
            'state_table_rom': hexb(sc['state_table_rom'], 5), 'state_count': sc['state_count'],
            'state_script_cpus': [hexb(x, 4) for x in sc['state_script_cpus']],
            'callbacks': [hexb(x, 4) for x in sc['callbacks']], 'calls': [hexb(x, 4) for x in sc['calls']], 'frames_used': sc['frames'],
            'spawns': [dict(s, type=hexb(s['type'])) for s in sc['spawns']], 'sets_bit4': sc['sets_bit4'], 'clears_bit4': sc['clears_bit4'],
            'states': states}


def code_regions(r, sc):
    bank = sc['bank']
    entries = sorted(set(x for x in sc['callbacks'] + sc['calls'] if x >= 0x8000))
    return B.region_record(r, bank, entries, f"type_{sc['type_id']:02x}") if entries else None


# --- records ----------------------------------------------------------------------
def decode_records(r):
    out = {}
    for act in range(3):
        ptr = L.object_list_pointer(r, F.ZONE, act)
        rows, term = L.decode_object_list(r, ptr['list_rom'])
        out[f'mghz{act + 1}'] = {'pointer': ptr, 'records': rows, 'terminator_rom': term,
                                 'records_sha256': digest(r[ptr['list_rom']:term])}
    return out


def six_zone_census(r):
    table = {}
    for z in range(6):
        for a in range(3):
            ptr = L.object_list_pointer(r, z, a)
            rows, _ = L.decode_object_list(r, ptr['list_rom'])
            for x in rows:
                t = int(x['type_id'], 16)
                e = table.setdefault(t, {'total': 0, 'acts': {}, 'parameters': Counter()})
                key = f'{ZONE_NAMES[z]}{a + 1}'
                e['total'] += 1
                e['acts'][key] = e['acts'].get(key, 0) + 1
                e['parameters'][x['parameter']] += 1
    return table


def spawn_graph(r, types):
    graph = {}
    for t in types:
        try:
            sc = state_scripts(r, t)
        except Exception:
            continue
        for s in sc['spawns']:
            graph.setdefault(s['type'], set()).add(t)
    return graph


def classify(rec, act_key, cell):
    t, p = int(rec['type_id'], 16), int(rec['parameter'], 16)
    cat, status, ident, research, poc = REGISTRY[t]
    detail = {}
    if t == 0x10:
        detail['reward'] = REWARDS.get(p, 'UNRESOLVED')
        if p == 4:
            cat = 'footwear'
            detail['footwear'] = 'Rocket Shoes reward monitor'
            status = 'REUSED_NEEDS_DATA'
    if t == 0x28:
        detail['platform_family'] = PLATFORM_PARAMS.get(p, 'UNRESOLVED')
        detail['initial_state'] = 13 if p & 127 in (5, 11) else (p & 63) + 1
    if t == 0x21:
        detail['orientation'] = 'flags bit4 set at placement: init requests state 5, clears +$04 bit4, latch +$3F = 1 (never reachable in THZ)'
    return dict(category=cat, status=status, identification=ident, canonical_research_exists=research is not None,
                canonical_research=research, poc_status=poc, reused_from=REUSED_FROM.get(t), new_to_mghz=t in (0x24, 0x2E, 0x56), **detail)


# --- art helpers -----------------------------------------------------------------
def vram_for_act(r, act_index):
    return L.build_act(r, f'mghz{act_index + 1}', F.ACTS[f'mghz{act_index + 1}'])


def frame_pointers(r, t):
    m = G.object_mapping(r, t)
    return m, G.mapping_frame_pointers(r, m['mapping_cpu'])


def sat_pieces(r, t, frame, base0, base1, flip):
    o = M.RenderOracle(r)
    got = o.render(type_id=t, frame_index=frame, obj_x=128, obj_y=96, cam_x=0, cam_y=0, flags=16 if flip else 0, art0=base0, art1=base1)
    return [{'x': x - 128, 'y': y - 96, 'tile': tile, 'pattern': tile & 254} for x, y, tile in zip(got['sat_x'], got['sat_y'], got['sat_tile'])]


def frame_record(r, t, frame, base0, base1, vram, flips=(False,)):
    m, fps = frame_pointers(r, t)
    fr = G.parse_frame_record(r, fps[frame])
    out = {'frame': frame, 'frame_cpu': hexb(fps[frame], 4), 'frame_rom': hexb(fr['frame_rom'], 5), 'piece_count': fr['piece_count'],
           'y_origin': fr['y_origin'], 'x_origin': fr['x_origin'], 'extent_word': hexb(fr['raw_word_1'], 4),
           'extent_x_y': [fr['raw_word_1'] & 255, fr['raw_word_1'] >> 8], 'tile_offsets': fr['tile_offsets'], 'images': []}
    for flip in flips:
        pieces = sat_pieces(r, t, frame, base0, base1, flip)
        model = M.model_slot(r, obj_x=128, obj_y=96, cam_x=0, cam_y=0, frame_cpu=fps[frame], flags=16 if flip else 0, art0=base0, art1=base1)
        assert [(p['x'], p['y'], p['tile']) for p in pieces] == [(p['sat_x'] - 128, p['sat_y'] - 96, p['tile']) for p in model]
        for p in pieces:
            p['pixels'] = G.tile_pixels(vram, p['pattern']) + G.tile_pixels(vram, p['pattern'] + 1)
        out['images'].append({'mirror': flip, 'pieces': pieces, 'composed_index_sha256': composed_hash(pieces)})
    return out


def composed_hash(pieces):
    canvas = {}
    for p in reversed(pieces):
        for yy, row in enumerate(p['pixels']):
            for xx, c in enumerate(row):
                if c:
                    canvas[(p['x'] + xx, p['y'] + yy)] = c
    return digest(json.dumps(sorted(canvas.items())).encode())


def strip_pixels(frame):
    out = dict(frame)
    out['images'] = [dict(mirror=i['mirror'], composed_index_sha256=i['composed_index_sha256'],
                          sat_pieces=[{k: v for k, v in p.items() if k != 'pixels'} for p in i['pieces']]) for i in frame['images']]
    return out


def art_sources(act, base0, base1, uses_bit4):
    covering = []
    for load in act['vram_loads']:
        lo = int(load['tile_base'], 16)
        hi = lo + load['tile_count']
        roles = ((base0, 'normal'), (base1, 'mirrored')) if uses_bit4 else ((base0, 'normal'),)
        for base, label in roles:
            if lo <= base < hi:
                covering.append({'role': label, 'base': base, 'load': load})
    return covering


def object_lab_init(r, act, rec):
    """Original placement creator + two engine/callback frames on the act's own layout."""
    t = int(rec['type_id'], 16)
    o = Oracle(r)
    m = o.mem
    h = act['descriptor']['header']
    m[0xC001:0xD000] = bytes((act['cells'] + [0] * 4095)[:4095])
    o.word(0xD168, h['row_offset_table_cpu'])
    o.word(0xD16A, -act['width'])
    o.bank(2, 0x1C)
    m[0xDA00:0xDA09] = bytes.fromhex(rec['raw_bytes'].replace(' ', ''))
    m[SLOT:SLOT + 0x40] = bytes(0x40)
    o.cpu.ix = SLOT
    o.cpu.iy = SLOT
    o.cpu.hl = 0xDA00
    o.call(0x80EB, bc=0xD418)
    ox, oy = o.word(SLOT + 0x11), o.word(SLOT + 0x14)
    o.word(0xD174, max(ox - 100, 0))
    o.word(0xD176, max(oy - 100, 0))
    m[0xD500] = 1
    m[0xD52C], m[0xD52D] = 8, 24
    far = ox - 3000 if ox > 3000 else ox + 3000
    o.position(far, 0)
    bank = A.animation_bank(t)

    def step():
        o.bank(2, bank)
        m[0xD12B] = bank
        o.cpu.ix = SLOT
        o.call(0x64FA)
        cb = m[SLOT + 0xC] | m[SLOT + 0xD] << 8
        if cb:
            o.bank(2, bank)
            m[0xD12B] = bank
            o.cpu.ix = SLOT
            o.call(cb)
        m[0xD12F] = (m[0xD12F] + 1) & 255
    return o, m, step, (ox, oy)


def init_fields(r, act, rec):
    o, m, step, (ox, oy) = object_lab_init(r, act, rec)
    return {'base0': m[SLOT + 8], 'base1': m[SLOT + 9], 'placement_token': m[SLOT + 0x3E], 'initial_x': ox, 'initial_y': oy,
            'record_flags_after_creator': hexb(m[SLOT + 4]), 'param_field_3f': m[SLOT + 0x3F]}


def init_after_two_updates(r, act, rec):
    o, m, step, (ox, oy) = object_lab_init(r, act, rec)
    step()
    step()
    cb = m[SLOT + 0xC] | m[SLOT + 0xD] << 8
    return {'requested_state_02': m[SLOT + 2], 'current_state_01': m[SLOT + 1], 'callback': hexb(cb, 4), 'vx_8_8': s16(o.word(SLOT + 0x16)),
            'vy_8_8': s16(o.word(SLOT + 0x18)), 'flags_04': hexb(m[SLOT + 4]), 'latch_3f': m[SLOT + 0x3F], 'extent_2c_2d': [m[SLOT + 0x2C], m[SLOT + 0x2D]],
            'bank_hint': A.animation_bank(int(rec['type_id'], 16))}


def patrol_trace(r, act, rec, updates=720):
    """Controlled original-routine trace of the type-$21 patrol on the MGHZ layout (player far away)."""
    o, m, step, _ = object_lab_init(r, act, rec)
    prev, log = None, []
    for u in range(1, updates + 1):
        step()
        st = m[SLOT + 2]
        if st != prev:
            log.append({'update': u, 'requested_state': st, 'x': o.word(SLOT + 0x11), 'y': o.word(SLOT + 0x14), 'vx_8_8': s16(o.word(SLOT + 0x16))})
            prev = st
    reversals = [e for e in log[1:] if e['requested_state'] in (5, 6, 3, 4)]
    return {'span_pixels': int(rec['parameter'], 16) * 16, 'state_log': log[:7], 'updates_traced': updates,
            'reversal_count': len(reversals), 'first_reversal_update': reversals[0]['update'] if reversals else None}


# --- footwear ---------------------------------------------------------------------
def terrain_window(act, wx, wy, rx=3, ry=2):
    cells, width = act['cells'], act['width']
    cx, cy = wx // 32, wy // 32
    rows = []
    for yy in range(cy - ry, cy + ry + 1):
        row = []
        for xx in range(cx - rx, cx + rx + 1):
            ok = 0 <= yy < act['height'] and 0 <= xx < width and yy * width + xx < act['runtime_cells']
            row.append(cells[yy * width + xx] if ok else None)
        rows.append(row)
    return {'center_cell': [cx, cy], 'rows_blocks': rows}


def footwear(r, acts, recs, found):
    out = []
    shoes = []
    for key, a in acts.items():
        start = (a['descriptor']['start']['ram_d511'], a['descriptor']['start']['ram_d514'])
        for rec in recs[key]['records']:
            t, p = int(rec['type_id'], 16), int(rec['parameter'], 16)
            if not (t == 0x2F or (t == 0x10 and p == 4)):
                continue
            wx, wy = rec['world_x'], rec['world_y']
            near = []
            for other in recs[key]['records']:
                if other is rec:
                    continue
                dx, dy = other['world_x'] - wx, other['world_y'] - wy
                if abs(dx) <= 256 and abs(dy) <= 160:
                    near.append({'index': other['index'], 'type_id': other['type_id'], 'parameter': other['parameter'], 'dx': dx, 'dy': dy})
            cx, cy = wx // 32, wy // 32
            block_here = a['cells'][cy * a['width'] + cx] if cy * a['width'] + cx < a['runtime_cells'] else None
            # first ground-like cell (surface 1/2/3 with bit7 solid) at or below the anchor cell
            ground = None
            for yy in range(cy, a['height']):
                i = yy * a['width'] + cx
                if i >= a['runtime_cells']:
                    break
                b = a['cells'][i]
                hd = R.header(r, b)
                if hd['flags'] & 0x80 and hd['flags'] & 31 in (1, 2, 3, 5, 0x13, 0x19):
                    ground = {'cell': [cx, yy], 'block_id': b, 'surface': hd['flags'] & 31, 'drop_pixels': yy * 32 - wy}
                    break
            shoes.append({'act': key, 'index': rec['index'], 'type_id': rec['type_id'], 'parameter': rec['parameter'], 'kind': 'Rocket Shoes monitor' if t == 0x10 else 'Spring Shoes',
                          'world_x': wx, 'world_y': wy, 'rom_offset': rec['rom_offset'], 'raw_bytes': rec['raw_bytes'], 'aux0': rec['aux0'], 'aux1': rec['aux1'],
                          'distance_from_start_x': wx - start[0], 'anchor_cell': [cx, cy], 'anchor_block': block_here,
                          'ground_below': ground, 'terrain_window_blocks_7x5': terrain_window(a, wx, wy), 'objects_within_256x160': near})
    return {'placements': shoes, 'counts': {k: {'rocket_shoes_monitors': sum(1 for s in shoes if s['act'] == k and s['type_id'] == '0x10'),
                                                 'spring_shoes': sum(1 for s in shoes if s['act'] == k and s['type_id'] == '0x2F')} for k in acts},
            'cross_check': 'data/rom-cache/powerup-shoes.json placements zone 3 (rocket 1/1/0, spring 1/2/0)',
            'art': {'spring_shoes': 'placement aux $AC/$AC; VRAM load $26840 -> tile $AC (16 tiles); behaviour/graphics shared with SEZ (docs/powerup-shoes-audit.md)',
                    'rocket_shoes': 'type $10 parameter $04 monitor; monitor art and dynamic selector unchanged'}}


# --- boss ----------------------------------------------------------------------------
def boss_tables(r):
    """Zone-indexed shared boss-framework tables (bank $1E): trigger thresholds and camera offsets."""
    base = A.cpu_to_rom(0x1E, 0x97A1)
    cam = A.cpu_to_rom(0x1E, 0x9808)
    out = []
    for idx in range(0, 7):
        tx, ty = u16(r, base + idx * 4), u16(r, base + idx * 4 + 2)
        cx, cy = s16(u16(r, cam + idx * 4)), s16(u16(r, cam + idx * 4 + 2))
        out.append({'index': idx, 'trigger_dx_lt': tx, 'trigger_dy_lt': ty, 'camera_x_offset': cx, 'camera_y_offset': cy})
    return {'index_rule': 'index = zone ($D297) + $D4A5 (starts 0); state 1 trigger table $1E:$97A1 (strict dx/dy distance), state 2 camera-target offset table $1E:$9808',
            'rows': out, 'mghz_row': out[F.ZONE], 'thz_row_cross_check': 'index 0 gives (160,256) and (-256,-160): reproduces accepted THZ3 trigger and camera target (1680,78)'}


def boss_recon(r, acts, recs, vrams):
    rec = next(x for x in recs['mghz3']['records'] if x['type_id'] == '0x56')
    sc = state_scripts(r, 0x56)
    children = {t: state_scripts(r, t) for t in (0x57, 0x58)}
    m, fps = frame_pointers(r, 0x56)
    dyn_cpu, dyn = D.dynamic_list_for_selector(r, 0x16)
    boss_vram = bytearray(vrams['mghz3']['vram'])
    D.apply_dynamic_entries(boss_vram, r, dyn)
    support = {}
    for t in (0x34, 0x0F, 0x0A, 0x12):
        try:
            support[hexb(t)] = public_script(state_scripts(r, t))
        except Exception as e:  # pragma: no cover - census tolerant
            support[hexb(t)] = {'error': str(e)}
    frames = []
    for fi in sorted(set(sc['frames']) | set(children[0x57]['frames']) | set(children[0x58]['frames'])):
        frames.append(strip_pixels(frame_record(r, 0x56, fi, 0, 0, bytes(boss_vram))))
    shared = {}
    for n, p in enumerate(sc['state_script_cpus']):
        shared[n] = 'own' if p > sc['state_table_cpu'] else 'shared with other boss tables'
    t50 = state_table(r, 0x50)
    tables = boss_tables(r)
    hdr = acts['mghz3']['descriptor']['header']
    shared_equal = {n: p in t50['state_script_cpus'] for n, p in enumerate(sc['state_script_cpus'])}
    return {
        'type': 0x56, 'placement': {k: rec[k] for k in ('index', 'rom_offset', 'bank', 'cpu', 'raw_bytes', 'type_id', 'parameter', 'flags', 'aux0', 'aux1', 'world_x', 'world_y')},
        'placement_within_map': 0 <= rec['world_x'] < acts['mghz3']['width'] * 32 and 0 <= rec['world_y'] < acts['mghz3']['height'] * 32,
        'state_machine': public_script(sc), 'state_ownership': {str(k): v for k, v in shared.items()},
        'state_scripts_also_in_type_50_table': {str(k): v for k, v in shared_equal.items()},
        'own_states': [n for n, v in shared.items() if v == 'own'], 'state_count': sc['state_count'],
        'initialisation': {'state_3_callback': '0xA576', 'effects': 'D3B3 = $16 (dynamic art selector); $D494 bit5 set + $D495 = 15 (sprite palette index 15); CALL $81A6 (HUD allocator, type $12); +$26 = 10 (health); requests state 11',
                           'evidence': 'BYTE-VERIFIED ASSEMBLY $1E:$A576..$A596', 'health_field_26': 10,
                           'shared_state0_callback': '0x974C (shared boss init: $D44E = zone+1, $D4A5 = 0, CALL $81A6/$8199, request state 1)'},
        'children': {hexb(t): public_script(c) for t, c in children.items()},
        'support_types': support,
        'support_dependencies': {'0x12': 'HUD slide-away (shared; allocated by $81A6 from state 0 and state 3)', '0x34': 'explosion puff, parameter 4 (state 4 shared script)',
                                 '0x0A': 'act-clear bonus/sparkle chain (shared; THZ3 audit)', '0x0F': 'defeat smoke poof (shared)'},
        'art': {'dynamic_selector': 0x16, 'dynamic_list_cpu': hexb(dyn_cpu, 4),
                'dynamic_loads': [dict(e, source_sha256=digest(r[e['source_rom']:e['source_rom'] + e['tile_count'] * 32])) for e in dyn],
                'sprite_palette_index': 15, 'sprite_palette_cram': list(r[L.PALETTE_DATA + 15 * 16:L.PALETTE_DATA + 16 * 16]),
                'placement_art_bases': [0, 0], 'mapping_pointer_entry_rom': hexb(G.POINTER_TABLE_ROM_BASE + 0x56 * 2, 5),
                'mapping_cpu': hexb(m['mapping_cpu'], 4), 'mapping_rom': hexb(m['mapping_rom'], 5), 'mapping_frame_count': len(fps),
                'child_mapping_shared': 'types $56/$57/$58 all use mapping $9861',
                'community_label_lead': 'ROM $17680 listed as "MGHZ pole climber boss" art (community table; lead only)'},
        'frames': frames, 'mirror_policy': 'bank $1E code never sets +$04 bit 4 and the record flags are 0: runtime art is unmirrored; forced bit4=1 is diagnostic only',
        'arena_and_camera': tables,
        'arena_derivation': {
            'anchor': [rec['world_x'], rec['world_y']],
            'camera_target_nominal': [rec['world_x'] + tables['mghz_row']['camera_x_offset'], rec['world_y'] + tables['mghz_row']['camera_y_offset']],
            'note': 'THZ3 audit: X limit is exclusive so the pan ends 1 px short; the same shared routine is used. Not executed for MGHZ in this census.',
            'camera_header_limits': {'d27c_min_y': hdr['ram_d27c'], 'd282_max_x': hdr['ram_d282'], 'd27e_max_y': hdr['ram_d27e']}},
        'completion': {'shared_defeat_script': 'state 4 uses script $95CC identical to the THZ boss table (spawns $34 puffs, calls $9A1E/$9A29)',
                       'expected': 'converges on shared $0A/$0F objects and player state $20 as in THZ3, but THZ3-specific constants are unverified for MGHZ3',
                       'no_sign': 'MGHZ3 has no type $18 sign; act clear depends on the boss chain',
                       'status': 'UNRESOLVED: dedicated boss task must confirm; do not copy THZ/GPZ completion'},
        'dependencies_summary': ['dynamic art selector $16 (64 tiles + 12 shared explosion tiles)', 'sprite palette 15', 'shared boss framework tables indexed by zone',
                                 'children $57 (params 0/1) and $58 (params 0/1)', 'HUD $12, explosion $34, bonus $0A, smoke $0F',
                                 'camera lock/pan + player arena clamp via shared EDGE rules', 'player state $20 handoff'],
        'poc': 'absent'}


# --- enemy recon -----------------------------------------------------------------
def enemy_recon(r, acts, recs, vrams):
    out = {}
    first = {}
    for key, v in recs.items():
        for rec in v['records']:
            first.setdefault(rec['type_id'], (key, rec))
    sprite_idx = acts['mghz1']['descriptor']['palette']['sprite_index']
    for t, klass in ((0x21, 'ENEMY_CLASS_2_NEW_ART_REUSED_RUNTIME'), (0x24, 'ENEMY_CLASS_3_NEW_RUNTIME_AUDIT'), (0x2E, 'ENEMY_CLASS_3_NEW_RUNTIME_AUDIT')):
        key, rec = first[f'0x{t:02X}']
        act = vrams[key]
        sc = state_scripts(r, t)
        m, fps = frame_pointers(r, t)
        b0, b1 = int(rec['aux0'], 16), int(rec['aux1'], 16)
        used = sc['frames']
        frames = []
        for fi in used:
            fr = frame_record(r, t, fi, b0, b1, act['vram'], flips=(False, True))
            fr = strip_pixels(fr)
            for im in fr['images']:
                im['canonical_orientation'] = (not im['mirror']) or t == 0x21
                im['forced_diagnostic_mirror'] = im['mirror'] and t != 0x21
                im['approved_runtime_candidate'] = False
            frames.append(fr)
        placements = [{'act': k, 'index': x['index'], 'parameter': x['parameter'], 'flags': x['flags'], 'aux0': x['aux0'], 'aux1': x['aux1'],
                       'world_x': x['world_x'], 'world_y': x['world_y']} for k, v in recs.items() for x in v['records'] if x['type_id'] == f'0x{t:02X}']
        info = {'type': t, 'classification': klass, 'placements': placements,
                'mapping': {'pointer_entry_rom': hexb(G.POINTER_TABLE_ROM_BASE + t * 2, 5), 'mapping_cpu': hexb(m['mapping_cpu'], 4),
                            'mapping_rom': hexb(m['mapping_rom'], 5), 'frame_count': len(fps), 'frame_pointers': [hexb(x, 4) for x in fps]},
                'art': {'placement_bases': [hexb(b0), hexb(b1)], 'covering_loads': art_sources(act, b0, b1, t == 0x21),
                        'sprite_palette_index': sprite_idx, 'sprite_palette_cram': list(r[L.PALETTE_DATA + sprite_idx * 16:L.PALETTE_DATA + sprite_idx * 16 + 16])},
                'state_machine': public_script(sc), 'visible_frames': used, 'visible_frame_count': len(used),
                'orientation': {'runtime_uses_bit4': t == 0x21, 'mirror_rule': ('original coordinate mirror table + alternate art base (bit4 states 3/6 vs 4/5), never a whole-bitmap flip' if t == 0x21
                                else 'bit4 never set by scripts or placement flags: unmirrored only; bit4=1 images in the PNG package are diagnostics, NOT approved')},
                'frames': frames, 'code': code_regions(r, sc), 'init_fields': init_fields(r, act, rec),
                'init_after_two_updates_first_record': init_after_two_updates(r, act, rec)}
        if t == 0x21:
            info['controlled_patrol_traces'] = [{'act': k, 'index': x['index'], 'parameter': x['parameter'], **patrol_trace(r, vrams[k], x)}
                                                for k, v in recs.items() for x in v['records'] if x['type_id'] == '0x21']
            info['reuse'] = ('same ROM state table/callbacks as THZ type $21 (type table entry $065FA, state table $0C:$B1C4); MGHZ differences: art bases $7C/$8E, '
                             'all 15 records carry flags $10 (alternate states 5/6), parameter span up to $16*16 = 352 px')
        if t == 0x24:
            info['behaviour_notes'] = ['state 1 callback $B49A: sleeps while +$04 bit6 set; when player |dx| < $30 and |player vx| < $100 requests state 2',
                                       'state 2 script sets X velocity and animates, callback $B4D1 selects vx = +$0080 for parameter 0 else -$0080, clears Y velocity, requests state 3',
                                       'state 3 callback $B4F0 integrates motion, calls contact helper $0434/$0431, deletes itself when $037A reports off-screen/blocked',
                                       'records come in pairs 16 px apart with parameters 1 then 0 (opposite directions); all at Y 48/112']
            info['behaviour_evidence'] = 'BYTE-VERIFIED ASSEMBLY $0C:$B490..$B50D read; no oracle audit'
        if t == 0x2E:
            info['behaviour_notes'] = ['placed once per act; extents (0,0) -> no contact box',
                                       'state 2 script spawns three type $2E children with parameters 1/2/3 and offsets (4,0), (0,-2), (-4,-4) then requests state 1',
                                       'state 3 animates frames 1..3 (callback $8B10) and ends with callback $034A (generic delete)',
                                       'art: VRAM base $72 (10 tiles from ROM $26780); aux1 $13/$1B differs by act and is not a mirror base (bit4 never set)']
            info['behaviour_evidence'] = 'DECODED DATA (scripts) + controlled initialiser result; callbacks unaudited'
            info['community_label_lead'] = 'ROM $26780 is listed as "oil splash (MGHZ)" (community table; lead only, identity unresolved)'
        out[hexb(t)] = info
    return out


# --- build --------------------------------------------------------------------------
def build(r):
    if digest(r) != L.ROM_SHA256:
        raise ValueError('Expected canonical Europe v1.2 ROM')
    recs = decode_records(r)
    vrams = {k: vram_for_act(r, i) for i, k in enumerate(recs)}
    acts = vrams
    out = {'format': 1, 'rom_sha256': L.ROM_SHA256, 'research_base': F.RESEARCH_BASE,
           'scope': 'MGHZ1-3 object census + reconnaissance; not a behaviour audit', 'poc_inspected_read_only': POC_COMMIT,
           'status_vocabulary': {'REUSED_SUPPORTED': 'accepted runtime exists; MGHZ data/art/zone gating still to generate',
                                 'REUSED_NEEDS_DATA': 'researched; runtime or integration missing in POC',
                                 'NEW_ART_REUSED_RUNTIME': 'same ROM runtime as an accepted type; new art/placement variant needs audit-light verification',
                                 'NEW_NEEDS_RESEARCH': 'new runtime; dedicated audit required', 'BOSS': 'boss/controller', 'UNRESOLVED': 'not established'},
           'acts': {}}
    six = six_zone_census(r)
    for key, v in recs.items():
        a = acts[key]
        rows = []
        for rec in v['records']:
            cx, cy = rec['world_x'] // 32, rec['world_y'] // 32
            inside = 0 <= rec['world_x'] < a['width'] * 32 and 0 <= rec['world_y'] < a['height'] * 32
            idx = cy * a['width'] + cx
            c = classify(rec, key, None)
            rows.append(dict(rec, inside_map=inside, anchor_cell=[cx, cy], anchor_block=a['cells'][idx] if inside and idx < a['runtime_cells'] else None,
                             **c, evidence='DECODED DATA; behaviour evidence in the referenced research'))
        types = Counter(x['type_id'] for x in rows)
        out['acts'][key] = {'object_list': v['pointer'], 'terminator_rom': v['terminator_rom'], 'record_count': len(rows), 'records_sha256': v['records_sha256'],
                            'records': rows, 'type_counts': dict(sorted(types.items())),
                            'category_counts': dict(sorted(Counter(x['category'] for x in rows).items())),
                            'status_counts': dict(sorted(Counter(x['status'] for x in rows).items())),
                            'off_map_records': [x['index'] for x in rows if not x['inside_map']]}
    all_types = sorted({int(x['type_id'], 16) for a in out['acts'].values() for x in a['records']})
    graph = spawn_graph(r, sorted(set(six) | {0x07, 0x57, 0x58, 0x2E, 0x34, 0x12, 0x0F, 0x0A}))
    census = {}
    for t in all_types + [0x07, 0x57, 0x58]:
        e = six.get(t, {'total': 0, 'acts': {}, 'parameters': Counter()})
        zones = sorted({k[:-1] for k in e['acts']})
        census[hexb(t)] = {'total_placements_all_zones': e['total'], 'placements_by_act': dict(sorted(e['acts'].items())), 'zones': zones,
                           'parameters': dict(sorted(e['parameters'].items())), 'mghz_only': zones == ['mghz'] or not zones,
                           'spawned_by_types': sorted(hexb(x) for x in graph.get(t, ())),
                           'buys_other_zone_coverage': [z for z in zones if z != 'mghz'] or ([] if t not in (0x07,) else ['unplaced dynamic child'])}
    out['six_zone_reuse_census'] = {'types': census,
                                    'newly_encountered_types': [hexb(t) for t in (0x24, 0x2E, 0x56)],
                                    'dynamic_children_not_placed': {'0x57': 'spawned by $56 states 8/9 (params 0/1)', '0x58': 'spawned by $57 state 3 (params 0/1)',
                                                                    '0x07': 'breakable-block fragments spawned by $7898 (surface $0D)'},
                                    'conclusion': 'types $24, $2E, $56 (and children $57/$58) appear in no other zone: researching them buys MGHZ coverage only; '
                                                  '$21 research (shared with THZ) and $2F footwear research (SEZ) already pay off beyond MGHZ'}
    out['footwear'] = footwear(r, acts, recs, None)
    out['enemies'] = enemy_recon(r, acts, recs, vrams)
    out['boss'] = boss_recon(r, acts, recs, vrams)
    out['support_art_dependencies'] = {'platform_28': 'placement aux0 $6A; VRAM load $26470 -> tile $6A (8 tiles); mapping $9217 frame 1 (docs/isometric-platform-audit.md section 3)',
                                       'breakable_fragments_type_07': 'type $07 mapping $8C71 (24 frames); fragment art source not extracted here',
                                       'sign_18': 'dynamic selector $12 overwrites VRAM tiles $6A..$A9 at act clear (original behaviour; keep sprite atlases separate)'}
    out['unresolved'] = ['Human-facing names of $21/$24/$2E/$56 are not proven; community labels are leads only.',
                         'Type $24 and $2E gameplay (hazard/contact/damage) is not audited.',
                         'Boss $56 completion/arena/camera numbers are census-level; no whole-update replay was run.',
                         'Type $07 fragment art for MGHZ breakables.']
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
            raise SystemExit('MGHZ object census differs')
    else:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(text, encoding='utf-8')
    v = json.loads(text)
    print(json.dumps({k: x['type_counts'] for k, x in v['acts'].items()}, indent=1))


if __name__ == '__main__':
    main()
