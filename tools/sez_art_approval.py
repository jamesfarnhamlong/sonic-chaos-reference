#!/usr/bin/env python3
"""Build the ignored SEZ visual-approval input (build/sez-approval/preview-input.json).

Pixels never enter the committed cache: they are written to the ignored ``build/`` folder
and rendered to PNG boards by ``sez_art_previews.py`` (needs Pillow).  The committed
``data/rom-cache/sez/art-approval.json`` records only subjects, sources and hashes, and
the approval state (PENDING until James reviews the PNGs in-thread).  Compositions are
recomposed from ROM mappings/SAT data through the original render oracle, never hand edited.

    .venv/Scripts/python.exe tools/sez_art_approval.py "../source/Sonic Chaos (Europe).sms"
    <python with Pillow> tools/sez_art_previews.py
"""
import argparse
import hashlib
import json
from pathlib import Path

import level_package as L
import thz1_type18_dynamic_graphics as D
import mghz_art_approval as AA
import mghz_foundation as MF
import sez_foundation as F
import sez_object_census as C

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/sez-approval'
CACHE = ROOT / 'data/rom-cache/sez/art-approval.json'
REGISTRATION = AA.REGISTRATION
NEW_SUBJECTS = {0x20: ('SEZ enemy candidate (script-set bit4)', 'sez1'), 0x23: ('SEZ enemy candidate', 'sez1'), 0x28: ('platform, SEZ art', 'sez1'),
                0x2F: ('Spring Shoes pickup, SEZ base $94', 'sez1'), 0x54: ('SEZ3 boss + $55 child', 'sez3')}
SHARED_SUBJECTS = {0x10: 'monitor', 0x1B: 'moving spike', 0x26: 'mapped spring', 0x07: 'breakable/crumble shard (base 0)'}
SPECIAL_CATEGORIES = ('crumble_0C', 'booster_1A', 'breakable_0D', 'ramp_12', 'floor_break_16', 'upright_spring', 'horizontal_spring', 'diagonal_spring', 'static_floor_spikes')
PRIMARY_TILES = range(0xC0, 0xC0 + 239)


def effect_variants(r, act, desc):
    """VRAM images for each terrain-ring frame and each effect-5 frame."""
    vram = bytes(act['vram'])
    src = MF.bank_file(0x1D, desc['ring_frames_source_cpu'])
    ring = []
    for i in range(4):
        v = bytearray(vram)
        dst = desc['ring_frames_vram_destination']
        v[dst:dst + 128] = r[src + 128 * i:src + 128 * (i + 1)]
        ring.append(bytes(v))
    strip = []
    for cpu in (0x8DDD, 0x8DFD):
        v = bytearray(vram)
        off = MF.bank_file(0x1D, cpu)
        v[0x2B00:0x2B20] = r[off:off + 32]
        strip.append(bytes(v))
    return vram, ring, strip


def build(r):
    if AA.digest(r) != L.ROM_SHA256:
        raise ValueError('Expected canonical Europe v1.2 ROM')
    recs = C.decode_records(r)
    acts = {k: C.vram_for_act(r, i) for i, k in enumerate(recs)}
    a1 = acts['sez1']
    d = a1['descriptor']
    bg = AA.pal(r, d['palette']['background_index'])
    sp = AA.pal(r, d['palette']['sprite_index'])
    boss_pal = AA.pal(r, 14)
    manifest = json.loads(F.OUTPUT.read_text(encoding='utf-8'))
    all_blocks, maps = {}, {}
    for k, a in acts.items():
        blocks = {b['block_id'] for b in manifest['acts'][k]['blocks']}
        maps[k] = AA.block_maps(r, a, a['vram'], blocks)
        for b in blocks:
            all_blocks.setdefault(b, {'pixels': maps[k][b]})
    block_meta = {}
    for k in acts:
        for b in manifest['acts'][k]['blocks']:
            m = block_meta.setdefault(b['block_id'], {'surface': b['surface'], 'priority_tiles': b['priority_tiles'], 'palette1_tiles': b['palette1_tiles'],
                                                      'cells': {}, 'flags': b['headers'][0]['flags'], 'tile_ids': b['tile_ids']})
            m['cells'][k] = b['cell_count']
    terrain = {'palettes': {'background': bg, 'sprite': sp}, 'blocks': {str(b): dict(block_meta[b], pixels=all_blocks[b]['pixels']) for b in sorted(block_meta)},
               'tiles': {str(t): AA.tile_rows(a1['vram'], t) for t in PRIMARY_TILES}}
    acts_json = {}
    for k, a in acts.items():
        start = a['descriptor']['start']
        acts_json[k] = {'width': a['width'], 'height': a['height'], 'runtime_cells': a['runtime_cells'], 'cells': a['cells'],
                        'start_camera': [start['ram_d2d6'], start['ram_d2d8']], 'start_player': [start['ram_d511'], start['ram_d514']],
                        'objects': [{'type': x['type_id'], 'parameter': x['parameter'], 'x': x['world_x'], 'y': x['world_y'], 'index': x['index']} for x in recs[k]['records']],
                        'terrain_rings': [[g['world_x'], g['world_y']] for g in manifest['acts'][k]['rings']['terrain']]}
    start_crops = {k: {'camera': a['descriptor']['start']['ram_d2d6'],
                       'crop': AA.crop(maps[k], a, a['descriptor']['start']['ram_d2d6'], a['descriptor']['start']['ram_d2d8'], bg, sp),
                       'player': [a['descriptor']['start']['ram_d511'], a['descriptor']['start']['ram_d514']]} for k, a in acts.items()}
    special_crops = {}
    for k, a in acts.items():
        for cat, rows in manifest['acts'][k]['terrain_interactions'].items():
            if cat in SPECIAL_CATEGORIES:
                cell = rows[len(rows) // 2]
                left = max(0, min(cell['world_x'] - 112, a['width'] * 32 - 256))
                top = max(0, min(cell['world_y'] - 96, a['height'] * 32 - 224))
                special_crops[f'{k}:{cat}'] = {'cell': cell, 'camera': [left, top], 'crop': AA.crop(maps[k], a, left, top, bg, sp)}
    # --- animated terrain
    desc = MF.ring_art_descriptor(r, F.ZONE, 0)
    base_vram, ring_frames, strip = effect_variants(r, a1, desc)
    booster_blocks = [int(x, 16) for x in manifest['acts']['sez2']['animated_terrain_blocks']['0x158']]
    animated = {'ring_frames': [AA.block_maps(r, a1, v, {0x40})[0x40] for v in ring_frames],
                'ring_blocks_frame0': {str(b): AA.block_maps(r, a1, ring_frames[0], {b})[b] for b in (0x40, 0x41, 0x42, 0x43, 0x44, 0x45)},
                'effect5_blocks': {str(b): [AA.block_maps(r, a1, v, {b})[b] for v in strip] for b in booster_blocks},
                'effect5_tiles': [AA.tile_rows(v, 0x158) for v in strip],
                'ring_tiles': [[AA.tile_rows(v, 0x14D + i) for i in range(4)] for v in ring_frames]}
    subjects = {}
    for t, (label, act_key) in NEW_SUBJECTS.items():
        if t == 0x54:
            continue
        a = acts[act_key]
        if t == 0x28:
            platform = next(x for x in recs['sez1']['records'] if x['type_id'] == '0x28' and x['parameter'] == '0x83')
            bases = (int(platform['aux0'], 16), int(platform['aux1'], 16))
            f = C.C.frame_record(r, 0x28, 1, bases[0], bases[1], bytes(a['vram']), flips=(False,))
            subj = {'type': t, 'act': act_key, 'palette_index': d['palette']['sprite_index'], 'palette': sp, 'bases': list(bases),
                    'frames': [{'frame': 1, 'piece_count': f['piece_count'], 'extent_x_y': f['extent_x_y'], 'images': f['images']}],
                    'raw_tiles': AA.raw_tiles([f], bytes(a['vram'])),
                    'placement': {'x': platform['world_x'], 'y': platform['world_y'], 'parameter': platform['parameter'], 'flags': platform['flags']}}
        elif t == 0x2F:
            subj = AA.subject(r, acts, recs, t, act_key, d['palette']['sprite_index'], flips=(False,))
        else:
            subj = AA.subject(r, acts, recs, t, act_key, d['palette']['sprite_index'], flips=(False, True))
        subj['label'] = label
        sets_bit4 = C.C.state_scripts(r, t)['sets_bit4']
        if sets_bit4:                       # canonical (script-set bit4=1) image first so context overlays use it
            for f in subj['frames']:
                f['images'].sort(key=lambda im: not im['mirror'])
        subj['mirror_rule'] = ('runtime uses bit4 (script-set in every visible state): the bit4=1 image is the canonical one' if sets_bit4 else
                               'unmirrored runtime art only; bit4=1 images are forced diagnostics and NOT approved')
        px, py = subj['placement']['x'], subj['placement']['y']
        left = max(0, min(px - 128, a['width'] * 32 - 256))
        top = max(0, min(py - 112, a['height'] * 32 - 224))
        subj['context'] = {'camera': [left, top], 'anchor': [px - left, py - top], 'crop': AA.crop(maps[act_key], a, left, top, bg, sp)}
        subjects[str(t)] = subj
    # shared objects under the SEZ sprite palette (compositions proven identical in sez_object_census)
    shared = {}
    for t, label in SHARED_SUBJECTS.items():
        if t == 0x07:
            f = C.C.frame_record(r, 0x07, 15, 0, 0, bytes(a1['vram']), flips=(False,))
            shared[str(t)] = {'type': t, 'label': label, 'act': 'sez1', 'palette_index': d['palette']['sprite_index'], 'palette': sp, 'bases': [0, 0],
                              'frames': [{'frame': 15, 'piece_count': f['piece_count'], 'extent_x_y': f['extent_x_y'], 'images': f['images']}],
                              'raw_tiles': AA.raw_tiles([f], bytes(a1['vram'])), 'mirror_rule': 'unmirrored'}
            continue
        key = next(k for k in recs for x in recs[k]['records'] if int(x['type_id'], 16) == t)
        s = AA.subject(r, acts, recs, t, key, d['palette']['sprite_index'], flips=(False,))
        s['label'] = label
        s['mirror_rule'] = 'compositions identical to the accepted zone (sez_object_census shared_reuse_proof); shown only for the SEZ sprite palette'
        shared[str(t)] = s
    # --- boss + child
    a3 = acts['sez3']
    dyn_cpu, dyn = D.dynamic_list_for_selector(r, 0x15)
    boss_vram = bytearray(a3['vram'])
    D.apply_dynamic_entries(boss_vram, r, dyn)
    boss_maps = AA.block_maps(r, a3, bytes(boss_vram), {b['block_id'] for b in manifest['acts']['sez3']['blocks']})
    boss_frames = sorted(set(C.C.state_scripts(r, 0x54)['frames']) | set(C.C.state_scripts(r, 0x55)['frames']))
    boss = {'type': 0x54, 'act': 'sez3', 'palette_index': 14, 'palette': boss_pal, 'bases': [0, 0], 'label': 'SEZ3 boss and $55 child (frames of both)', 'frames': [], 'raw_tiles': []}
    fr = []
    for fi in boss_frames:
        f = C.C.frame_record(r, 0x54, fi, 0, 0, bytes(boss_vram), flips=(False, True))
        fr.append(f)
        boss['frames'].append({'frame': fi, 'piece_count': f['piece_count'], 'extent_x_y': f['extent_x_y'], 'images': f['images']})
    boss['raw_tiles'] = AA.raw_tiles(fr, bytes(boss_vram))
    boss['dynamic_loads'] = [{'tile_base': e['tile_base'], 'tile_count': e['tile_count'], 'vram_destination': e['vram_destination']} for e in dyn]
    rec = next(x for x in recs['sez3']['records'] if x['type_id'] == '0x54')
    boss['placement'] = {'x': rec['world_x'], 'y': rec['world_y']}
    row = C.C.boss_tables(r)['rows'][F.ZONE]
    target = (rec['world_x'] + row['camera_x_offset'] - 1, rec['world_y'] + row['camera_y_offset'])
    for label, (left, top) in (('arena_target', target), ('approach', (max(0, rec['world_x'] - 128 - 256), max(0, rec['world_y'] - 112)))):
        boss.setdefault('contexts', {})[label] = {'camera': [left, top], 'anchor': [rec['world_x'] - left, rec['world_y'] - top],
                                                  'crop': AA.crop(boss_maps, a3, left, top, boss_pal, boss_pal)}
    boss['mirror_rule'] = 'bank $1E never sets bit4 and the record flags are 0: unmirrored only; bit4=1 images are forced diagnostics, NOT approved'
    subjects['84'] = boss
    return {'format': 1, 'registration': REGISTRATION, 'palettes': {'background': bg, 'sprite': sp, 'boss': boss_pal}, 'terrain': terrain, 'acts': acts_json,
            'start_crops': start_crops, 'special_crops': special_crops, 'animated': animated, 'subjects': subjects, 'shared': shared,
            'object_colours': {'0x20': [255, 90, 90], '0x23': [255, 140, 40], '0x28': [120, 180, 255], '0x10': [255, 255, 80], '0x26': [80, 255, 140],
                               '0x2F': [160, 255, 80], '0x54': [255, 255, 255], '0x1B': [255, 120, 200], '0x18': [90, 255, 255]}}


def manifest_for(full):
    def entry(s):
        return {'label': s['label'], 'act': s['act'], 'palette_index': s['palette_index'], 'bases': [f'0x{v:02X}' for v in s['bases']],
                'frames': [f['frame'] for f in s['frames']], 'raw_tile_count': len(s['raw_tiles']), 'mirror_rule': s['mirror_rule'],
                'frame_hashes': {str(f['frame']): [im['composed_index_sha256'] for im in f['images']] for f in s['frames']}}
    return {'format': 1, 'approval': 'PENDING (James reviews the PNG boards in-thread before any POC import)',
            'generator': 'tools/sez_art_approval.py + tools/sez_art_previews.py', 'rom_sha256': L.ROM_SHA256, 'png_folder': 'build/sez-approval (git-ignored)',
            'boards': ['terrain-tiles.png', 'terrain-blocks.png', 'terrain-special-surfaces.png', 'terrain-context-sez1.png', 'terrain-context-sez2.png',
                       'terrain-context-sez3.png', 'map-sez1.png', 'map-sez2.png', 'map-sez3.png', 'animated-terrain.png', 'type-20-approval.png', 'type-23-approval.png',
                       'type-28-approval.png', 'type-2f-approval.png', 'type-54-approval.png', 'shared-objects-sez-palette.png'],
            'subjects': {f"0x{int(k):02X}": entry(s) for k, s in full['subjects'].items()},
            'shared_subjects_identical_to_accepted_zone': {f"0x{int(k):02X}": entry(s) for k, s in full['shared'].items()},
            'approved_runtime_candidates': 'none until approved; canonical orientation images only (bit4=0 for $23/$28/$2F/$54, script-set bit4=1 for $20); forced/diagnostic mirrors are never candidates',
            'policy': 'Existing unchanged shared compositions ($10/$1B/$26/$2F frames, $07 shard) are proven identical to accepted zones in sez_object_census; '
                      'they are shown once under the SEZ sprite palette. New compositions are the SEZ terrain, platform $28 art, $20, $23, $54/$55.'}


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
            raise SystemExit('SEZ art approval manifest differs')
        print('approval manifest ok')
        return
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'preview-input.json').write_text(json.dumps(full, separators=(',', ':')) + '\n', encoding='utf-8')
    CACHE.write_text(text, encoding='utf-8')
    print(json.dumps({'preview_input': str(OUT / 'preview-input.json'), 'subjects': list(full['subjects'])}))


if __name__ == '__main__':
    main()
