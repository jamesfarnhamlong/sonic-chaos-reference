#!/usr/bin/env python3
"""Build the ignored MGHZ visual-approval input (build/mghz-approval/preview-input.json).

Pixels never enter the committed cache: they are written to the ignored ``build/`` folder
and rendered to PNG boards by ``mghz_art_previews.py`` (needs Pillow).  The committed
``data/rom-cache/mghz/art-approval.json`` records only subjects, sources and hashes, and
the approval state (PENDING until James reviews the PNGs in-thread).

    .venv/Scripts/python.exe tools/mghz_art_approval.py "../source/Sonic Chaos (Europe).sms"
    <python with Pillow> tools/mghz_art_previews.py
"""
import argparse
import hashlib
import json
from pathlib import Path

import level_package as L
import rom as R
import thz1_object_assets as G
import thz1_type18_dynamic_graphics as D
import mghz_foundation as F
import mghz_object_census as C

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/mghz-approval'
CACHE = ROOT / 'data/rom-cache/mghz/art-approval.json'
REGISTRATION = {'x': 1, 'y': 18}      # accepted terrain-relative presentation of SAT-relative pixels (docs/gpz-enemy-audit.md)
SUBJECTS = {
    0x21: ('ordinary enemy (flags $10 variant)', 'mghz1'), 0x24: ('ordinary enemy candidate', 'mghz1'), 0x2E: ('splash/effect object', 'mghz1'),
    0x2F: ('Spring Shoes pickup', 'mghz1'), 0x28: ('platform, MGHZ art', 'mghz1'), 0x56: ('MGHZ3 boss + children', 'mghz3')}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pal(r, index):
    return [list(c) for c in G.palette_rgba(r, index)]


def tile_rows(vram, tile):
    return G.tile_pixels(vram, tile) if tile < 256 else G.decode_mode4_tile(vram[tile * 32:tile * 32 + 32])


def block_maps(r, act, vram, blocks):
    return L.block_pixel_maps(r, vram, only=sorted(blocks), mapping_rom=act['descriptor']['header']['block_mapping_rom'])


def colour(c, bg, sp):
    """Terrain pixel -> rgba; index 0 is the backdrop colour in both palette halves."""
    idx = c & 15
    if idx == 0:
        return bg[0][:3] + [255]
    return (sp if c & 16 else bg)[idx][:3] + [255]


def crop(maps, act, left, top, bg, sp, w=256, h=224):
    out = []
    cells, width = act['cells'], act['width']
    for yy in range(h):
        row = []
        for xx in range(w):
            wx, wy = left + xx, top + yy
            i = (wy // 32) * width + wx // 32
            if wy < 0 or wx < 0 or wx >= width * 32 or i >= act['runtime_cells']:
                row.append(bg[0][:3] + [255])
            else:
                row.append(colour(maps[cells[i]][wy % 32][wx % 32], bg, sp))
        out.append(row)
    return out


def frames_for(r, t, frames, b0, b1, vram, flips):
    out = []
    for fi in frames:
        rec = C.frame_record(r, t, fi, b0, b1, vram, flips=flips)
        out.append(rec)
    return out


def raw_tiles(frames, vram):
    patterns = sorted({p['pattern'] + j for f in frames for im in f['images'] for p in im['pieces'] for j in (0, 1)})
    return [{'tile': p, 'pixels': tile_rows(vram, p)} for p in patterns]


def subject(r, acts, recs, t, act_key, palette_index, vram=None, bases=None, frames=None, flips=(False, True), context=None):
    a = acts[act_key]
    vram = vram if vram is not None else a['vram']
    rec = next(x for x in recs[act_key]['records'] if int(x['type_id'], 16) == t)
    b0, b1 = bases if bases else (int(rec['aux0'], 16), int(rec['aux1'], 16))
    sc = C.state_scripts(r, t)
    used = frames if frames is not None else sc['frames']
    fr = frames_for(r, t, used, b0, b1, bytes(vram), flips)
    return {'type': t, 'act': act_key, 'palette_index': palette_index, 'palette': pal(r, palette_index), 'bases': [b0, b1],
            'frames': [{'frame': f['frame'], 'piece_count': f['piece_count'], 'extent_x_y': f['extent_x_y'], 'images': f['images']} for f in fr],
            'raw_tiles': raw_tiles(fr, bytes(vram)), 'placement': {'x': rec['world_x'], 'y': rec['world_y'], 'parameter': rec['parameter'], 'flags': rec['flags']}}


def effect_variants(r, acts, desc):
    """VRAM images for each ring frame / effect-14 frame, and palette cycle colour sequences."""
    a = acts['mghz1']
    vram = bytes(a['vram'])
    ring_src = F.bank_file(0x1D, desc['ring_frames_source_cpu'])
    ring_frames = []
    for i in range(4):
        v = bytearray(vram)
        dst = desc['ring_frames_vram_destination']
        v[dst:dst + 128] = r[ring_src + 128 * i:ring_src + 128 * (i + 1)]
        ring_frames.append(bytes(v))
    strip = []
    for cpu in (0x8E3D, 0x8E1D):
        v = bytearray(vram)
        off = F.bank_file(0x1D, cpu)
        v[0x3500:0x3500 + 64] = r[off:off + 64]
        strip.append(bytes(v))
    return vram, ring_frames, strip


def palette_cycles(r, bg_index):
    base = list(r[L.PALETTE_DATA + bg_index * 16:L.PALETTE_DATA + bg_index * 16 + 16])
    out = {}
    for eid, cram in ((2, 4), (3, 11)):
        events = F.run_effect(r, eid, 200 if eid == 2 else 220)
        seq, cur = [base[cram]], base[cram]
        for e in events:
            for w in e['palette_writes']:
                if w['cram_index'] == cram:
                    seq.append(w['after'])
        out[str(eid)] = {'cram_index': cram, 'initial': base[cram], 'sequence_cram_bytes': seq,
                         'sequence_rgba': [list(G.sms_color(v))[:3] + [255] for v in seq]}
    return out


def build(r):
    if digest(r) != L.ROM_SHA256:
        raise ValueError('Expected canonical Europe v1.2 ROM')
    recs = C.decode_records(r)
    acts = {k: C.vram_for_act(r, i) for i, k in enumerate(recs)}
    a1 = acts['mghz1']
    d = a1['descriptor']
    bg = pal(r, d['palette']['background_index'])
    sp = pal(r, d['palette']['sprite_index'])
    boss_pal = pal(r, 15)
    manifest = json.loads(F.OUTPUT.read_text(encoding='utf-8'))
    # --- terrain
    all_blocks = {}
    maps = {}
    for k, a in acts.items():
        blocks = {b['block_id'] for b in manifest['acts'][k]['blocks']}
        maps[k] = block_maps(r, a, a['vram'], blocks)
        for b in blocks:
            all_blocks.setdefault(b, {'pixels': maps[k][b]})
    block_meta = {}
    for k in acts:
        for b in manifest['acts'][k]['blocks']:
            m = block_meta.setdefault(b['block_id'], {'surface': b['surface'], 'priority_tiles': b['priority_tiles'], 'palette1_tiles': b['palette1_tiles'],
                                                      'cells': {}, 'flags': b['headers'][0]['flags'], 'tile_ids': b['tile_ids']})
            m['cells'][k] = b['cell_count']
    terrain = {'palettes': {'background': bg, 'sprite': sp}, 'blocks': {str(b): dict(block_meta[b], pixels=all_blocks[b]['pixels']) for b in sorted(block_meta)},
               'tiles': {str(t): tile_rows(a1['vram'], t) for t in range(0xC0, 0xC0 + 250)}}
    acts_json = {}
    for k, a in acts.items():
        start = a['descriptor']['start']
        acts_json[k] = {'width': a['width'], 'height': a['height'], 'runtime_cells': a['runtime_cells'], 'cells': a['cells'],
                        'start_camera': [start['ram_d2d6'], start['ram_d2d8']], 'start_player': [start['ram_d511'], start['ram_d514']],
                        'objects': [{'type': x['type_id'], 'parameter': x['parameter'], 'x': x['world_x'], 'y': x['world_y'], 'index': x['index']} for x in recs[k]['records']],
                        'terrain_rings': [[g['world_x'], g['world_y']] for g in manifest['acts'][k]['rings']['terrain']]}
    start_crops = {k: {'camera': a['descriptor']['start']['ram_d2d6'], 'crop': crop(maps[k], a, a['descriptor']['start']['ram_d2d6'], a['descriptor']['start']['ram_d2d8'], bg, sp),
                       'player': [a['descriptor']['start']['ram_d511'], a['descriptor']['start']['ram_d514']]} for k, a in acts.items()}
    # special terrain contexts: first cell of each special category in each act
    special_crops = {}
    for k, a in acts.items():
        for cat, rows in manifest['acts'][k]['terrain_interactions'].items():
            if cat in ('oil_1B', 'twist_17', 'ceiling_spikes', 'breakable_0D', 'strip_19', 'upward_spikes', 'upright_spring', 'horizontal_spring', 'diagonal_spring_left'):
                cell = rows[len(rows) // 2]
                left = max(0, min(cell['world_x'] - 112, a['width'] * 32 - 256))
                top = max(0, min(cell['world_y'] - 96, a['height'] * 32 - 224))
                special_crops[f'{k}:{cat}'] = {'cell': cell, 'camera': [left, top], 'crop': crop(maps[k], a, left, top, bg, sp)}
    # --- animated terrain
    desc = F.ring_art_descriptor(r, F.ZONE, 0)
    base_vram, ring_frames, strip = effect_variants(r, acts, desc)
    ring_block = 0x40
    animated = {'ring_frames': [block_maps(r, a1, v, {0x40, 0x42, 0x44})[0x40] for v in ring_frames],
                'ring_blocks_frame0': {str(b): block_maps(r, a1, ring_frames[0], {b})[b] for b in (0x40, 0x41, 0x42, 0x43, 0x44, 0x45)},
                'strip_blocks': {str(b): [block_maps(r, a1, v, {b})[b] for v in strip] for b in (0xD2, 0xD3)},
                'strip_tiles': [[tile_rows(v, 0x1A8), tile_rows(v, 0x1A9)] for v in strip],
                'ring_tiles': [[tile_rows(v, 0x10B + i) for i in range(4)] for v in ring_frames],
                'palette_cycles': palette_cycles(r, d['palette']['background_index'])}
    use = {}
    for b, m in all_blocks.items():
        colours = {c & 15 for row in m['pixels'] for c in row if not c & 16}
        for ci in (4, 11):
            if ci in colours:
                use.setdefault(ci, []).append(b)
    animated['palette_index_blocks'] = {str(ci): sorted(v) for ci, v in use.items()}
    animated['palette_cycle_demo_blocks'] = {str(ci): sorted(v)[:4] for ci, v in use.items()}
    # --- objects
    subjects = {}
    mirrors = {0x21: (False, True)}
    for t, (label, act_key) in SUBJECTS.items():
        if t == 0x56:
            continue
        a = acts[act_key]
        if t == 0x28:
            platform = next(x for x in recs['mghz1']['records'] if x['type_id'] == '0x28' and x['parameter'] == '0x83')
            bases = (int(platform['aux0'], 16), int(platform['aux1'], 16))
            fr = [1]
            subj = {'type': t, 'act': act_key, 'palette_index': d['palette']['sprite_index'], 'palette': sp, 'bases': list(bases),
                    'frames': [], 'raw_tiles': [], 'placement': {'x': platform['world_x'], 'y': platform['world_y'], 'parameter': platform['parameter'], 'flags': platform['flags']}}
            f = C.frame_record(r, 0x28, 1, bases[0], bases[1], bytes(a['vram']), flips=(False,))
            subj['frames'] = [{'frame': 1, 'piece_count': f['piece_count'], 'extent_x_y': f['extent_x_y'], 'images': f['images']}]
            subj['raw_tiles'] = raw_tiles([f], bytes(a['vram']))
        elif t == 0x2F:
            subj = subject(r, acts, recs, t, act_key, d['palette']['sprite_index'], flips=(False,))
        else:
            subj = subject(r, acts, recs, t, act_key, d['palette']['sprite_index'], flips=(False, True))
        subj['label'] = label
        subj['mirror_rule'] = ('runtime uses bit4 (states 3/6 vs 4/5): both orientations are canonical' if t == 0x21 else
                               'unmirrored runtime art only; bit4=1 images are forced diagnostics and NOT approved')
        # terrain context at the first placement
        px, py = subj['placement']['x'], subj['placement']['y']
        left = max(0, min(px - 128, a['width'] * 32 - 256))
        top = max(0, min(py - 112, a['height'] * 32 - 224))
        subj['context'] = {'camera': [left, top], 'anchor': [px - left, py - top], 'crop': crop(maps[act_key], a, left, top, bg, sp)}
        subjects[str(t)] = subj
    # --- boss
    a3 = acts['mghz3']
    dyn_cpu, dyn = D.dynamic_list_for_selector(r, 0x16)
    boss_vram = bytearray(a3['vram'])
    D.apply_dynamic_entries(boss_vram, r, dyn)
    boss_maps = block_maps(r, a3, bytes(boss_vram), {b['block_id'] for b in manifest['acts']['mghz3']['blocks']})
    boss_frames = sorted(set(C.state_scripts(r, 0x56)['frames']) | {11, 12, 13, 14, 15})
    boss = {'type': 0x56, 'act': 'mghz3', 'palette_index': 15, 'palette': boss_pal, 'bases': [0, 0], 'label': 'MGHZ3 boss and $57/$58 children',
            'frames': [], 'raw_tiles': []}
    fr = []
    for fi in boss_frames:
        f = C.frame_record(r, 0x56, fi, 0, 0, bytes(boss_vram), flips=(False, True))
        fr.append(f)
        boss['frames'].append({'frame': fi, 'piece_count': f['piece_count'], 'extent_x_y': f['extent_x_y'], 'images': f['images']})
    boss['raw_tiles'] = raw_tiles(fr, bytes(boss_vram))
    boss['dynamic_loads'] = [{'tile_base': e['tile_base'], 'tile_count': e['tile_count'], 'vram_destination': e['vram_destination']} for e in dyn]
    rec = next(x for x in recs['mghz3']['records'] if x['type_id'] == '0x56')
    boss['placement'] = {'x': rec['world_x'], 'y': rec['world_y']}
    tab = C.boss_tables(r)['mghz_row']
    target = (rec['world_x'] + tab['camera_x_offset'] - 1, rec['world_y'] + tab['camera_y_offset'])
    for label, (left, top) in (('arena_target', target), ('approach', (max(0, rec['world_x'] - 128 - 256), max(0, rec['world_y'] - 112)))):
        boss.setdefault('contexts', {})[label] = {'camera': [left, top], 'anchor': [rec['world_x'] - left, rec['world_y'] - top],
                                                  'crop': crop(boss_maps, a3, left, top, boss_pal, boss_pal)}
    boss['mirror_rule'] = 'bank $1E never sets bit4 and the record flags are 0: unmirrored only; bit4=1 images are forced diagnostics, NOT approved'
    subjects['86'] = boss
    full = {'format': 1, 'registration': REGISTRATION, 'palettes': {'background': bg, 'sprite': sp, 'boss': boss_pal}, 'terrain': terrain, 'acts': acts_json,
            'start_crops': start_crops, 'special_crops': special_crops, 'animated': animated, 'subjects': subjects,
            'object_colours': {'0x28': [120, 180, 255], '0x10': [255, 255, 80], '0x21': [255, 90, 90], '0x24': [255, 140, 40], '0x2E': [200, 90, 255],
                               '0x2F': [80, 255, 140], '0x56': [255, 255, 255], '0x1B': [255, 120, 200], '0x09': [255, 215, 0], '0x18': [90, 255, 255]}}
    return full


def manifest_for(full):
    subjects = {}
    for key, s in full['subjects'].items():
        subjects[f"0x{int(key):02X}"] = {'label': s['label'], 'act': s['act'], 'palette_index': s['palette_index'], 'bases': [f'0x{v:02X}' for v in s['bases']],
                                         'frames': [f['frame'] for f in s['frames']], 'raw_tile_count': len(s['raw_tiles']), 'mirror_rule': s['mirror_rule'],
                                         'frame_hashes': {str(f['frame']): [im['composed_index_sha256'] for im in f['images']] for f in s['frames']}}
    return {'format': 1, 'approval': 'APPROVED BY USER 2026-10-04 (foundation checkpoint, all boards)', 'generator': 'tools/mghz_art_approval.py + tools/mghz_art_previews.py',
            'rom_sha256': L.ROM_SHA256, 'png_folder': 'build/mghz-approval (git-ignored)',
            'boards': ['terrain-tiles.png', 'terrain-blocks.png', 'terrain-special-surfaces.png', 'terrain-context-mghz1.png', 'terrain-context-mghz2.png',
                       'terrain-context-mghz3.png', 'map-mghz1.png', 'map-mghz2.png', 'map-mghz3.png', 'animated-terrain.png', 'type-21-approval.png',
                       'type-24-approval.png', 'type-2e-approval.png', 'type-2f-approval.png', 'type-28-approval.png', 'type-56-approval.png'],
            'subjects': subjects,
            'approved_runtime_candidates': 'canonical orientation images of every subject (bit4=0; both orientations for $21); forced/diagnostic mirrors of $24/$2E/$2F/$28/$56 are never candidates',
            'policy': 'James approved the PNG boards in-thread (incl. flat $A0 oil and animated/twisty scenery); the boards remain git-ignored review diagnostics.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom', type=Path)
    p.add_argument('--check', action='store_true')
    a = p.parse_args()
    r = L.load_rom(a.rom)
    full = build(r)
    text = json.dumps(manifest_for(full), indent=2) + '\n'
    if a.check:
        if CACHE.read_text(encoding='utf-8') != text:
            raise SystemExit('MGHZ art approval manifest differs')
        print('approval manifest ok')
        return
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'preview-input.json').write_text(json.dumps(full, separators=(',', ':')) + '\n', encoding='utf-8')
    CACHE.write_text(text, encoding='utf-8')
    print(json.dumps({'preview_input': str(OUT / 'preview-input.json'), 'subjects': list(full['subjects'])}))


if __name__ == '__main__':
    main()
