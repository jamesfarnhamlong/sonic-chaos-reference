#!/usr/bin/env python3
"""SEZ1-3 object census, six-zone reuse census, proven-reuse comparisons, enemy/boss reconnaissance and viewport classification.

Census only: decoded records, state-table structure, art/palette sources, static code scans and controlled
original-routine initialisation/trace results.  It is not a behaviour audit: every type that needs one is
classified and listed.  No ROM bytes or pixels are emitted (hashes only).
"""
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import level_package as L
import rom as R
import thz1_animation_reach as A
import thz1_object_assets as G
import thz1_type18_dynamic_graphics as D
import thz3_boss_support as B
import mghz_object_census as C
import sez_foundation as F
from oracle import Oracle
from platform_spike_collision import SLOT

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'data/rom-cache/sez/object-census.json'
ZONE_NAMES = C.ZONE_NAMES
CLASSES = ('SHARED_RECOVERED', 'SHARED_WITH_SEZ_DATA', 'SEZ_SPECIFIC_NEEDS_AUDIT', 'BOSS_SUPPORT', 'UNRESOLVED')
ACCEPTED_ZONES = ('thz', 'gpz', 'mghz')          # Windows-accepted runtime zones
POC_COMMIT = '472c7b9'
digest, hexb, u16, s16 = C.digest, C.hexb, C.u16, C.s16
REWARDS = C.REWARDS

# type -> (category, classification, identification, canonical research, POC at 472c7b9 read-only)
REGISTRY = {
    0x10: ('monitor', 'SHARED_RECOVERED', 'monitor (parameters 1/2/4/6 are accepted rewards)', 'docs/object-10.md; docs/powerup-shoes-audit.md', 'implemented (all four SEZ parameters accepted)'),
    0x18: ('support', 'SHARED_RECOVERED', 'goal sign (SEZ1/SEZ2 only)', 'docs/object-18-act-clear.md', 'implemented (THZ/GPZ/MGHZ ordinary sign clear)'),
    0x1B: ('hazard', 'SHARED_RECOVERED', 'moving spike', 'docs/platform-spike-collision-audit.md', 'implemented'),
    0x20: ('enemy', 'SEZ_SPECIFIC_NEEDS_AUDIT', 'ground walker that hops (numeric identity only)', None, 'absent'),
    0x23: ('enemy', 'SEZ_SPECIFIC_NEEDS_AUDIT', 'repeated left-moving leaper (numeric identity only)', None, 'absent'),
    0x26: ('spring', 'SHARED_RECOVERED', 'mapped spring', 'docs/spring-interaction-audit.md', 'implemented'),
    0x28: ('platform', 'SHARED_WITH_SEZ_DATA', 'platform (state selected by parameter)', 'docs/platform-spike-collision-audit.md; docs/isometric-platform-audit.md', 'implemented for THZ $0A/$84 and GPZ/MGHZ $83/$89/$05'),
    0x2F: ('footwear', 'SHARED_WITH_SEZ_DATA', 'Spring Shoes pickup (SEZ art base $94)', 'docs/powerup-shoes-audit.md; docs/spring-shoes-presentation-audit.md', 'implemented (MGHZ art base $AC)'),
    0x54: ('boss', 'BOSS_SUPPORT', 'SEZ3 boss/controller (numeric identity only)', None, 'absent'),
}
SHARED_TYPES = (0x10, 0x18, 0x1B, 0x26, 0x28, 0x2F)
SEZ_ONLY_TYPES = (0x20, 0x23, 0x54)
PLATFORM_PARAMS = {0x0A: ('THZ lift family', 'accepted'), 0x83: ('state 4 sag/delay/fall', 'accepted (GPZ/MGHZ)'),
                   0x84: ('state 5 weight sag, axis flag +$25 = $FF', 'accepted (THZ)'), 0x89: ('state 10 horizontal reversal', 'accepted (GPZ)'),
                   0x05: ('state 13 -> 6 touch-start vertical mover', 'accepted (GPZ/MGHZ)'),
                   0x04: ('state 5 with weight sag disabled', 'RESEARCHED: state 5 fixed support; POC acceptance pending'),
                   0x86: ('state 7 contact-started right-and-return mover', 'RESEARCHED: platform-28-runtime.json; POC acceptance pending'),
                   0x8B: ('state 12/vertical mover without reversal (EEZ)', 'not an SEZ parameter')}


def platform_state(p):
    return 13 if p & 127 in (5, 11) else (p & 63) + 1


# --- code scan -------------------------------------------------------------------------
RAM_NAMES = {0xD174: 'cameraX', 0xD176: 'cameraY', 0xD284: 'cameraTargetX', 0xD286: 'cameraTargetY', 0xD2DA: 'panTargetX', 0xD2DC: 'panTargetY',
             0xD280: 'cameraLimitLeft', 0xD27C: 'cameraLimitTop', 0xD282: 'cameraLimitRight', 0xD27E: 'cameraLimitBottom',
             0xD511: 'playerX', 0xD514: 'playerY', 0xD516: 'playerVx', 0xD518: 'playerVy', 0xD501: 'playerState', 0xD503: 'playerAttackFlags',
             0xD3B3: 'dynamicArtSelector', 0xD44E: 'bossActive', 0xD494: 'spritePaletteControl', 0xD495: 'spritePaletteIndex',
             0xD353: 'sampledBlock', 0xD12F: 'frameCounter', 0xD532: 'powerupSelector', 0xD520: 'hurtRequest', 0xD523: 'contactBits'}
VIEWPORT_RAM = {'cameraX', 'cameraY', 'cameraTargetX', 'cameraTargetY', 'panTargetX', 'panTargetY', 'cameraLimitLeft', 'cameraLimitTop',
                'cameraLimitRight', 'cameraLimitBottom'}


def scan_code(r, bank, entries, name):
    """Static instruction scan of the reachable code of a callback set: RAM references, IX fields, vector calls, flag writes."""
    from z80dis import z80
    fr = B.flow_ranges(r, bank, sorted(entries))
    img = r[0:0x8000] + r[bank * 0x4000:(bank + 1) * 0x4000]
    refs, ix_read, ix_write, vectors, flags4, banks_out = Counter(), Counter(), Counter(), Counter(), [], Counter()
    count = 0
    for a, b in fr['ranges']:
        pc = a
        while pc < b:
            d = z80.decode(img[pc:pc + 4], pc)
            text = z80.disasm(d)
            ln = d.len or 1
            count += 1
            for m in re.finditer(r'0x([0-9a-f]{4})', text):
                v = int(m.group(1), 16)
                if v in RAM_NAMES:
                    refs[RAM_NAMES[v]] += 1
                if text.startswith(('CALL', 'JP')) and 0x0300 <= v < 0x0400:
                    vectors[hexb(v, 4) + '->' + hexb(u16(r, v + 1) if r[v] == 0xC3 else 0, 4)] += 1
            mm = re.search(r'\(IX\+(0x[0-9a-f]+|\d+)\)', text)
            if mm:
                off = int(mm.group(1), 0)
                store = text.startswith('LD (IX') or text.startswith(('SET', 'RES', 'INC (IX', 'DEC (IX'))
                (ix_write if store else ix_read)[hexb(off)] += 1
                if off == 4 and text.startswith(('SET 4', 'RES 4')):
                    flags4.append({'cpu': hexb(pc, 4), 'instruction': text})
            pc += ln
    return {'name': name, 'bank': bank, 'entries': [hexb(e, 4) for e in sorted(entries)], 'instruction_count': count,
            'ram_references': dict(sorted(refs.items())), 'viewport_ram_references': {k: v for k, v in sorted(refs.items()) if k in VIEWPORT_RAM},
            'ix_fields_read': dict(sorted(ix_read.items())), 'ix_fields_written': dict(sorted(ix_write.items())),
            'vector_calls': dict(sorted(vectors.items())), 'flag_bit4_writes': flags4,
            'external_calls': [hexb(t, 4) for t in fr['external_targets']],
            'code_regions': B.region_record(r, bank, sorted(entries), name)['regions']}


def type_scan(r, t):
    sc = C.state_scripts(r, t)
    entries = [x for x in sc['callbacks'] + sc['calls'] if 0x8000 <= x < 0xC000]
    return sc, (scan_code(r, sc['bank'], entries, f'type_{t:02x}') if entries else None)


# --- records ----------------------------------------------------------------------------
def decode_records(r):
    out = {}
    for act in range(3):
        ptr = L.object_list_pointer(r, F.ZONE, act)
        rows, term = L.decode_object_list(r, ptr['list_rom'])
        out[f'sez{act + 1}'] = {'pointer': ptr, 'records': rows, 'terminator_rom': term, 'records_sha256': digest(r[ptr['list_rom']:term])}
    return out


def vram_for_act(r, i):
    return L.build_act(r, f'sez{i + 1}', F.ACTS[f'sez{i + 1}'])


def classify(rec):
    t, p = int(rec['type_id'], 16), int(rec['parameter'], 16)
    cat, klass, ident, research, poc = REGISTRY[t]
    detail = {}
    if t == 0x10:
        detail['reward'] = REWARDS.get(p, 'UNRESOLVED')
        if p == 4:
            cat, detail['footwear'] = 'footwear', 'Rocket Shoes reward monitor'
    if t == 0x28:
        fam = PLATFORM_PARAMS.get(p, ('UNRESOLVED', 'UNRESOLVED'))
        detail.update(platform_family=fam[0], platform_acceptance=fam[1], initial_state=platform_state(p))
        if p in (0x04, 0x86):
            klass = 'SHARED_WITH_SEZ_DATA'
            research = 'docs/sez-platform-28-audit.md'
    if t == 0x26:
        detail['span_mode'] = bool(p & 0x80)
        detail['span_pixels'] = (p & 0x7F) * 16 if p & 0x80 else None
    return dict(category=cat, classification=klass, identification=ident, canonical_research_exists=research is not None, canonical_research=research,
                poc_status=poc, sez_only=t in SEZ_ONLY_TYPES, **detail)


# --- shared-reuse proof -----------------------------------------------------------------
recs_all = {}


def all_records(r):
    out = {}
    for z in range(6):
        for a in range(3):
            ptr = L.object_list_pointer(r, z, a)
            rows, _ = L.decode_object_list(r, ptr['list_rom'])
            out[f'{ZONE_NAMES[z]}{a + 1}'] = {'records': rows}
    return out


def zone_vrams(r):
    out = {}
    for z in range(6):
        for a in range(3):
            key = f'{ZONE_NAMES[z]}{a + 1}'
            out[key] = L.build_act(r, key, {'zone': z, 'act': a, 'name': key})
    return out


def sprite_palette(r, act):
    i = act['descriptor']['palette']['sprite_index']
    return i, list(r[L.PALETTE_DATA + i * 16:L.PALETTE_DATA + i * 16 + 16])


def accepted_candidates(t):
    out = []
    for zone in ACCEPTED_ZONES:
        for n in range(3):
            key = f'{zone}{n + 1}'
            out.extend((key, x) for x in recs_all[key]['records'] if int(x['type_id'], 16) == t)
    return out


def pick_reference(t, pair):
    cands = accepted_candidates(t)
    for key, x in cands:
        if (int(x['aux0'], 16), int(x['aux1'], 16)) == pair:
            return key, x, 'same_base_pair'
    for key, x in cands:
        if int(x['aux0'], 16) == pair[0]:
            return key, x, 'same_aux0'
    return (cands[0][0], cands[0][1], 'different_base') if cands else (None, None, None)


def reuse_proof(r, t, sez_acts, zvram):
    """Compare the type's runtime tables/code and frame compositions in SEZ against accepted-zone placements.

    A composition is a rendered, palette-index image from the zone's static VRAM; the SAT geometry comes from the
    shared mapping (zone independent), so identical hashes prove identical art at the placement base.
    """
    sc, scan = type_scan(r, t)
    out = {'type': t, 'bank': sc['bank'], 'type_table_entry_rom': hexb(A.ANIM_TYPE_TABLE_ROM + (t - 1) * 2, 5), 'state_table_cpu': hexb(sc['state_table_cpu'], 4),
           'state_count': sc['state_count'], 'zone_independent_dispatch': True,
           'state_script_and_callback_regions_sha256': digest(json.dumps(scan['code_regions'] if scan else [], sort_keys=True).encode()),
           'ix_fields_read': scan['ix_fields_read'] if scan else {}, 'zone_2_code_gates': 'none (implementation-manifest zone_dependent_code)'}
    flips = (False, True) if sc['sets_bit4'] else (False,)
    pairs = sorted({(int(x['aux0'], 16), int(x['aux1'], 16)) for k in ('sez1', 'sez2', 'sez3') for x in recs_all[k]['records'] if int(x['type_id'], 16) == t})
    comparisons = []
    for pair in pairs:
        key = next(k for k in ('sez1', 'sez2', 'sez3') for x in recs_all[k]['records'] if int(x['type_id'], 16) == t and (int(x['aux0'], 16), int(x['aux1'], 16)) == pair)
        ref_key, ref_rec, how = pick_reference(t, pair)
        entry = {'sez_act': key, 'sez_bases': [hexb(v) for v in pair], 'reference_act': ref_key, 'reference_match': how}
        if ref_rec is None:
            entry['frames'] = None
            comparisons.append(entry)
            continue
        ref_pair = (int(ref_rec['aux0'], 16), int(ref_rec['aux1'], 16))
        rows = []
        for fi in sc['frames']:
            a = C.frame_record(r, t, fi, pair[0], pair[1], bytes(sez_acts[key]['vram']), flips=flips)
            b = C.frame_record(r, t, fi, ref_pair[0], ref_pair[1], bytes(zvram[ref_key]['vram']), flips=flips)
            ha, hb = [i['composed_index_sha256'] for i in a['images']], [i['composed_index_sha256'] for i in b['images']]
            rows.append({'frame': fi, 'piece_count': a['piece_count'], 'sez_images': ha, 'reference_images': hb, 'composition_identical': ha == hb})
        si, spal = sprite_palette(r, sez_acts[key])
        ri, rpal = sprite_palette(r, zvram[ref_key])
        entry.update(reference_bases=[hexb(v) for v in ref_pair], frames=rows, all_compositions_identical=all(x['composition_identical'] for x in rows),
                     sprite_palette={'sez_index': si, 'reference_index': ri, 'cram_identical': spal == rpal})
        comparisons.append(entry)
    out['comparisons'] = comparisons
    out['all_compositions_identical'] = all(c.get('all_compositions_identical') for c in comparisons if c.get('frames') is not None)
    out['art_verdict'] = ('IDENTICAL index compositions to the accepted zone' if out['all_compositions_identical'] else
                          'SEZ art differs from the accepted zone at the placement base: shared behaviour, new composition -> visual approval required')
    return out


def fragment_art_proof(r, zvram):
    """Type $07/$13 debris frame 15 (base 0): identical composition in all 18 acts => zone-independent art."""
    hashes = {}
    for key, a in zvram.items():
        f = C.frame_record(r, 0x07, 15, 0, 0, bytes(a['vram']), flips=(False,))
        hashes[key] = f['images'][0]['composed_index_sha256']
    sc7 = C.state_scripts(r, 0x07)
    sc13 = C.state_scripts(r, 0x13)
    frame = C.frame_record(r, 0x07, 15, 0, 0, bytes(zvram['sez1']['vram']), flips=(False,))
    return {'frame': 15, 'pieces': [{'x': p['x'], 'y': p['y'], 'tile': p['tile']} for p in frame['images'][0]['pieces']],
            'composition_hashes_all_acts': hashes, 'identical_in_all_18_acts': len(set(hashes.values())) == 1,
            'source_stream': 'common object stream $23340 -> tile $10 (90 tiles), decoded hash identical in every zone',
            'type_07_frames': sc7['frames'], 'type_13_frames': sc13['frames'], 'mapping_shared': 'types $07, $0F and $13 all use mapping $8C71',
            'sprite_palette_index_sez': zvram['sez1']['descriptor']['palette']['sprite_index']}


# --- shared-system proofs ---------------------------------------------------------------------
SYSTEM_CACHES = {'terrain_ring_collection': 'terrain-ring-collection.json', 'player_hurt_ring_scatter': 'player-hurt-ring-scatter.json',
                 'spring_interaction': 'spring-interaction.json', 'platform_spike_collision': 'platform-spike-collision.json',
                 'player_attack_badnik': 'player-attack-badnik.json', 'powerup_shoes': 'powerup-shoes.json', 'player_fall_control': 'player-fall-control.json',
                 'object_18_act_clear': 'object-18-act-clear.json'}


def cache_regions(doc):
    rows = doc.get('routines', doc.get('regions', []))
    items = rows.items() if isinstance(rows, dict) else ((x.get('name'), x) for x in rows)
    out = []
    for name, x in items:
        off = next((x[k] for k in ('rom_offset', 'file', 'rom') if k in x), None)
        n = next((x[k] for k in ('length', 'bytes') if k in x), None)
        sha = x.get('sha256')
        if off is None or n is None or sha is None:
            continue
        out.append({'name': name, 'file': int(off, 16), 'length': int(n), 'sha256': sha})
    return out


def zone_site_file(site):
    cpu = int(site['cpu'], 16)
    return cpu if site['region'] == 'fixed' else int(site['region'][4:], 16) * 0x4000 + cpu - 0x8000


def shared_system_proofs(r, sites):
    """Each accepted system's recorded routine regions: ROM bytes unchanged and no zone-indexed code site inside."""
    out = {}
    site_rows = [(zone_site_file(s), s) for s in sites['sites']]
    for system, name in SYSTEM_CACHES.items():
        doc = json.loads((ROOT / 'data/rom-cache' / name).read_text(encoding='utf-8'))
        regions = cache_regions(doc)
        mismatches, inside = [], []
        for g in regions:
            if digest(r[g['file']:g['file'] + g['length']]) != g['sha256']:
                mismatches.append(g['name'])
            for off, s in site_rows:
                if g['file'] <= off < g['file'] + g['length']:
                    inside.append({'region': g['name'], 'cpu': s['cpu'], 'kind': s['kind'], 'constant': s['constant'], 'applies_to_sez': s['applies_to_sez'], 'note': s['note']})
        out[system] = {'cache': f'data/rom-cache/{name}', 'regions_checked': len(regions), 'hash_mismatches': mismatches, 'zone_sites_inside_regions': inside,
                       'verdict': 'EXACT REUSE: routine bytes unchanged and no zone-2 gate' if not mismatches and not any(x['applies_to_sez'] for x in inside) else 'REVIEW'}
    return out


def support_art_proof(r, zvram):
    """Support/effect object frames drawn at base 0: identical in all 18 acts => zone-independent static art."""
    rows = {}
    for t, frames in ((0x0F, [7, 8, 9]), (0x34, [1, 2, 3, 4]), (0x0A, [5, 6]), (0x06, [1, 2, 3, 4, 5, 6]), (0x03, [1, 2]), (0x07, [15]), (0x13, [15])):
        per_frame = {}
        for fi in frames:
            hashes = {k: C.frame_record(r, t, fi, 0, 0, bytes(a['vram']), flips=(False,))['images'][0]['composed_index_sha256'] for k, a in zvram.items()}
            per_frame[str(fi)] = {'identical_in_all_18_acts': len(set(hashes.values())) == 1, 'sha256': hashes['sez1']}
        rows[hexb(t)] = per_frame
    return {'types': rows, 'all_identical': all(f['identical_in_all_18_acts'] for t in rows.values() for f in t.values()),
            'meaning': '$0F smoke, $34 puff, $0A sparkle, $06 lost ring, $03 sparkle and $07/$13 shard use static common-stream art at base 0'}


def spring_placements(r, acts, recs):
    out = []
    for key, v in recs.items():
        for x in v['records']:
            if x['type_id'] != '0x26':
                continue
            created, after = init_detail(r, acts[key], x)
            p = int(x['parameter'], 16)
            out.append({'act': key, 'index': x['index'], 'parameter': x['parameter'], 'aux0': x['aux0'], 'aux1': x['aux1'], 'world_x': x['world_x'], 'world_y': x['world_y'],
                        'span_mode': bool(p & 0x80), 'span_pixels': (p & 0x7F) * 16 if p & 0x80 else None, 'initial_state_after_2_updates': after['requested_state_02'],
                        'latch_3f': after['latch_3f'], 'extent_2c_2d': after['extent_2c_2d']})
    accepted = {x['parameter'] for k, a in recs_all.items() if k[:-1] in ACCEPTED_ZONES for x in a['records'] if x['type_id'] == '0x26'}
    new = sorted({x['parameter'] for x in out} - accepted)
    return {'placements': out, 'sez_parameters': sorted({x['parameter'] for x in out}), 'parameters_not_in_accepted_zones': new,
            'rule': 'accepted: bit 7 = span mode, span = (p & $7F) * 16 (docs/spring-interaction-audit.md); the new value follows the same rule, no new state is entered'}


# --- placement init (original creator) ----------------------------------------------------
def init_detail(r, act, rec):
    o, m, step, (ox, oy) = C.object_lab_init(r, act, rec)
    created = {'base0': m[SLOT + 8], 'base1': m[SLOT + 9], 'flags_04': hexb(m[SLOT + 4]), 'param_3f': m[SLOT + 0x3F], 'state_01': m[SLOT + 1],
               'requested_state_02': m[SLOT + 2], 'axis_flag_25': m[SLOT + 0x25], 'field_36': m[SLOT + 0x36], 'counter_1e': m[SLOT + 0x1E],
               'initial_x': ox, 'initial_y': oy, 'placement_token_3e': m[SLOT + 0x3E]}
    step()
    step()
    after = C.init_after_two_updates(r, act, rec)
    after = dict(after, axis_flag_25=m[SLOT + 0x25], field_36=m[SLOT + 0x36], counter_1e=m[SLOT + 0x1E])
    return created, after


def trace(r, act, rec, updates=420):
    """Controlled original-routine trace (player parked far away) of a SEZ-specific mover on the act's own layout."""
    o, m, step, (ox, oy) = C.object_lab_init(r, act, rec)
    log, prev = [], None
    xs, ys = [ox], [oy]
    for u in range(1, updates + 1):
        m[SLOT + 4] &= 0xBF            # the lab has no lifecycle manager: force the object awake (+$04 bit 6 clear)
        step()
        if m[SLOT] == 0xFF or m[SLOT] == 0:
            log.append({'update': u, 'event': 'object slot released', 'type_byte': m[SLOT]})
            break
        st = m[SLOT + 2]
        x, y = o.word(SLOT + 0x11), o.word(SLOT + 0x14)
        xs.append(x)
        ys.append(y)
        key = (m[SLOT + 1], st)
        if key != prev:
            log.append({'update': u, 'state_01': m[SLOT + 1], 'requested_state_02': st, 'x': x, 'y': y, 'vx_8_8': s16(o.word(SLOT + 0x16)), 'vy_8_8': s16(o.word(SLOT + 0x18))})
            prev = key
    return {'updates_traced': updates, 'transition_count': len(log), 'transitions_first_14': log[:14], 'x_range': [min(xs), max(xs)], 'y_range': [min(ys), max(ys)],
            'final': {'x': xs[-1], 'y': ys[-1]}}


# --- enemies / platform -------------------------------------------------------------------
def enemy_recon(r, acts, recs):
    out = {}
    first = {}
    for key, v in recs.items():
        for rec in v['records']:
            first.setdefault(rec['type_id'], (key, rec))
    sprite_idx = acts['sez1']['descriptor']['palette']['sprite_index']
    for t in (0x20, 0x23):
        key, rec = first[f'0x{t:02X}']
        act = acts[key]
        sc, scan = type_scan(r, t)
        m, fps = C.frame_pointers(r, t)
        b0, b1 = int(rec['aux0'], 16), int(rec['aux1'], 16)
        sets_bit4 = bool(scan['flag_bit4_writes']) or sc['sets_bit4']
        frames = []
        for fi in sc['frames']:
            fr = C.strip_pixels(C.frame_record(r, t, fi, b0, b1, act['vram'], flips=(False, True)))
            for im in fr['images']:
                im['script_sets_bit4'] = sc['sets_bit4']
                im['canonical_orientation'] = im['mirror'] == sc['sets_bit4'] if fi else True
                im['approved_runtime_candidate'] = False
            frames.append(fr)
        placements = [{'act': k, 'index': x['index'], 'parameter': x['parameter'], 'flags': x['flags'], 'aux0': x['aux0'], 'aux1': x['aux1'],
                       'world_x': x['world_x'], 'world_y': x['world_y']} for k, v in recs.items() for x in v['records'] if x['type_id'] == f'0x{t:02X}']
        traces = []
        for k, v in recs.items():
            for x in v['records']:
                if x['type_id'] == f'0x{t:02X}':
                    created, after = init_detail(r, acts[k], x)
                    traces.append({'act': k, 'index': x['index'], 'created_fields': created, 'after_two_updates': after, 'trace': trace(r, acts[k], x), 'trace_note': 'controlled lab: +$04 bit 6 cleared every update (awake), player parked far away, act layout loaded'})
        out[hexb(t)] = {
            'type': t, 'classification': 'ENEMY_SEZ_SPECIFIC_NEEDS_AUDIT', 'placements': placements,
            'mapping': {'pointer_entry_rom': hexb(G.POINTER_TABLE_ROM_BASE + t * 2, 5), 'mapping_cpu': hexb(m['mapping_cpu'], 4), 'mapping_rom': hexb(m['mapping_rom'], 5),
                        'frame_count': len(fps), 'frame_pointers': [hexb(x, 4) for x in fps]},
            'art': {'placement_bases': [hexb(b0), hexb(b1)], 'covering_loads': C.art_sources(act, b0, b1, sc['sets_bit4']),
                    'sprite_palette_index': sprite_idx, 'sprite_palette_cram': list(r[L.PALETTE_DATA + sprite_idx * 16:L.PALETTE_DATA + sprite_idx * 16 + 16])},
            'state_machine': C.public_script(sc), 'visible_frames': sc['frames'], 'visible_frame_count': len(sc['frames']),
            'orientation': {'scripts_set_bit4': sc['sets_bit4'], 'scripts_clear_bit4': sc['clears_bit4'], 'callback_bit4_writes': scan['flag_bit4_writes'],
                            'rule': ('every visible state ORs +$04 bit 4: the runtime composition is the bit4=1 image (script-set), never a whole-bitmap flip applied by the port'
                                     if sc['sets_bit4'] else 'bit4 is never set: unmirrored only; bit4=1 images in the PNG package are diagnostics, NOT approved')},
            'frames': frames, 'code_scan': scan, 'placement_parameter_read': '0x3F' in scan['ix_fields_read'],
            'controlled_traces': traces}
    return out


def platform_parameter_sweep(r, act):
    """Exhaustive original-creator sweep of the type-$28 parameter byte (every value whose state lies inside the 15-state table)."""
    o, m, step, _ = C.object_lab_init(r, act, {'type_id': '0x28', 'raw_bytes': '28 10 04 80 02 00 83 6A 6A'})
    rows, skipped = {}, []
    for p in range(256):
        if platform_state(p) > 14:
            skipped.append(p)
            continue
        m[SLOT:SLOT + 0x40] = bytes(0x40)
        m[0xDA06] = p
        o.cpu.ix = SLOT
        o.cpu.iy = SLOT
        o.cpu.hl = 0xDA00
        o.bank(2, 0x1C)
        o.call(0x80EB, bc=0xD418)
        step()
        step()
        rows[p] = {'state': m[SLOT + 1], 'requested': m[SLOT + 2], 'axis_flag_25': m[SLOT + 0x25], 'callback': hexb(m[SLOT + 0xC] | m[SLOT + 0xD] << 8, 4),
                   'vx_8_8': s16(o.word(SLOT + 0x16)), 'vy_8_8': s16(o.word(SLOT + 0x18))}
    return {'parameters_run': len(rows), 'parameters_out_of_table': len(skipped), 'formula': 'state = 13 if (p & $7F) in (5, 11) else (p & $3F) + 1; axis flag +$25 = $FF iff p bit 7',
            'formula_matches_original_for_all_run': all(v['state'] == platform_state(p) and (v['axis_flag_25'] == (255 if p & 128 else 0)) for p, v in rows.items()),
            'by_parameter': {hexb(p): v for p, v in sorted(rows.items())},
            'evidence': 'CONTROLLED ROUTINE RESULT: original placement creator $80EB + two object updates for every parameter value 0..255'}


def platform_recon(r, acts, recs):
    out = {'platforms': [], 'parameters': {}}
    for key, v in recs.items():
        for x in v['records']:
            if x['type_id'] != '0x28':
                continue
            p = int(x['parameter'], 16)
            created, after = init_detail(r, acts[key], x)
            out['platforms'].append({'act': key, 'index': x['index'], 'parameter': x['parameter'], 'aux0': x['aux0'], 'aux1': x['aux1'], 'world_x': x['world_x'],
                                     'world_y': x['world_y'], 'initial_state': platform_state(p), 'created_fields': created,
                                     'after_two_updates': after, 'acceptance': PLATFORM_PARAMS.get(p, ('UNRESOLVED', 'UNRESOLVED'))[1]})
    for p in sorted({int(x['parameter'], 16) for x in out['platforms']}):
        out['parameters'][hexb(p)] = {'family': PLATFORM_PARAMS.get(p, ('UNRESOLVED',))[0], 'initial_state': platform_state(p),
                                      'count': sum(1 for x in out['platforms'] if int(x['parameter'], 16) == p)}
    out['parameter_sweep'] = platform_parameter_sweep(r, acts['sez1'])
    sc, scan = type_scan(r, 0x28)
    state7 = scan_code(r, sc['bank'], [0x87E2], 'type_28_state_7')
    out['state_7_scan'] = {k: state7[k] for k in ('entries', 'instruction_count', 'ix_fields_read', 'ix_fields_written', 'vector_calls', 'viewport_ram_references', 'code_regions')}
    out['state_7_evidence'] = 'CONTROLLED ROUTINE RESULT + EMULATED ORIGINAL UPDATE: dedicated audit docs/sez-platform-28-audit.md and cache data/rom-cache/sez/platform-28-runtime.json supersede initial reconnaissance.'
    return out


# --- boss ------------------------------------------------------------------------------------
def boss_recon(r, acts, recs):
    rec = next(x for x in recs['sez3']['records'] if x['type_id'] == '0x54')
    sc, scan = type_scan(r, 0x54)
    child_sc, child_scan = type_scan(r, 0x55)
    support = {}
    for t in (0x34, 0x0F, 0x0A, 0x12):
        support[hexb(t)] = C.public_script(C.state_scripts(r, t))
    t50, t51, t56 = (C.state_table(r, x) for x in (0x50, 0x51, 0x56))
    own = [n for n, p in enumerate(sc['state_script_cpus']) if p > sc['state_table_cpu']]
    shared50 = {str(n): p in t50['state_script_cpus'] for n, p in enumerate(sc['state_script_cpus'])}
    shared56 = {str(n): p in t56['state_script_cpus'] for n, p in enumerate(sc['state_script_cpus'])}
    dyn_cpu, dyn = D.dynamic_list_for_selector(r, 0x15)
    boss_vram = bytearray(acts['sez3']['vram'])
    D.apply_dynamic_entries(boss_vram, r, dyn)
    m, fps = C.frame_pointers(r, 0x54)
    frames = []
    for fi in sorted(set(sc['frames']) | set(child_sc['frames'])):
        frames.append(C.strip_pixels(C.frame_record(r, 0x54, fi, 0, 0, bytes(boss_vram))))
    tables = C.boss_tables(r)
    row = tables['rows'][F.ZONE]
    hdr = acts['sez3']['descriptor']['header']
    ax, ay = rec['world_x'], rec['world_y']
    init = {'callback': '0xA291 (state 3)', 'effects': 'D3B3 = $15 (dynamic art selector); $D494 bit 5 set, $D495 = 14 (sprite palette index 14); requests state 6; health +$26 = 8; '
            'clears +$34/+$35/+$36/+$0A/+$1E and velocities; position moved by (-$40, -$C0) from the placement; Y speed = +$00C0',
            'evidence': 'BYTE-VERIFIED ASSEMBLY $1E:$A291..$A2E9', 'health_field_26': 8, 'selector': 0x15, 'sprite_palette_index': 14,
            'shared_state0_callback': '0x974C (shared boss init: $D44E = zone+1 = 3, $D4A5 = 0, CALL $81A6/$8199, request state 1)'}
    return {
        'type': 0x54, 'placement': {k: rec[k] for k in ('index', 'rom_offset', 'bank', 'cpu', 'raw_bytes', 'type_id', 'parameter', 'flags', 'aux0', 'aux1', 'world_x', 'world_y')},
        'placement_within_map': 0 <= ax < acts['sez3']['width'] * 32 and 0 <= ay < acts['sez3']['height'] * 32,
        'state_machine': C.public_script(sc), 'state_count': sc['state_count'], 'own_states': own,
        'state_scripts_also_in_type_50_table': shared50, 'state_scripts_also_in_type_56_table': shared56,
        'state_table': {'type_table_entry_rom': hexb(A.ANIM_TYPE_TABLE_ROM + 0x53 * 2, 5), 'cpu': hexb(sc['state_table_cpu'], 4), 'bank': sc['bank']},
        'sibling_tables': {'0x50': hexb(t50['state_table_cpu'], 4), '0x51': hexb(t51['state_table_cpu'], 4), '0x56': hexb(t56['state_table_cpu'], 4)},
        'initialisation': init,
        'children': {'0x55': C.public_script(child_sc)}, 'spawns_by_boss': sc['spawns'],
        'support_types': support,
        'support_dependencies': {'0x12': 'HUD slide-away (shared; allocated from the shared boss init)', '0x34': 'explosion puff, parameter 4 (state 4 shared script $95CC)',
                                 '0x0A': 'act-clear bonus/sparkle chain (shared; THZ3 audit)', '0x0F': 'defeat smoke poof (shared)', '0x55': 'boss-specific child spawned by state 7 at (-16,-36)'},
        'art': {'dynamic_selector': 0x15, 'dynamic_list_cpu': hexb(dyn_cpu, 4),
                'dynamic_loads': [dict(e, source_sha256=digest(r[e['source_rom']:e['source_rom'] + e['tile_count'] * 32])) for e in dyn],
                'sprite_palette_index': 14, 'sprite_palette_cram': list(r[L.PALETTE_DATA + 14 * 16:L.PALETTE_DATA + 15 * 16]),
                'placement_art_bases': [0, 0], 'mapping_pointer_entry_rom': hexb(G.POINTER_TABLE_ROM_BASE + 0x54 * 2, 5), 'mapping_cpu': hexb(m['mapping_cpu'], 4),
                'mapping_rom': hexb(m['mapping_rom'], 5), 'mapping_frame_count': len(fps), 'frames_used_boss': sc['frames'], 'frames_used_child_55': child_sc['frames']},
        'frames': frames, 'code_scan_boss': scan, 'code_scan_child_55': child_scan,
        'arena_and_camera': tables,
        'arena_derivation': {'anchor': [ax, ay], 'camera_target_nominal': [ax + row['camera_x_offset'], ay + row['camera_y_offset']],
                             'camera_header_limits': {'d27c_min_y': hdr['ram_d27c'], 'd282_max_x': hdr['ram_d282'], 'd27e_max_y': hdr['ram_d27e']},
                             'note': 'shared framework: the right limit is exclusive so earlier boss audits settle one pixel short on X; not executed here'},
        'completion': {'defeat_script': 'state 4 uses shared script $95CC (spawns five $34 puffs, calls $9A1E/$9A29 and, for this table, $9A2F)',
                       'no_sign': 'SEZ3 places no type $18 sign; act clear is the boss chain',
                       'status': 'UNRESOLVED: dedicated boss task must confirm the clear gate/camera release for SEZ3; do not copy THZ/GPZ/MGHZ constants'},
        'hit_points': {'initial_health_byte': 8, 'status': 'UNRESOLVED: hits-to-defeat not derived (MGHZ lesson: the byte decrements through zero), needs the boss audit'},
        'poc': 'absent'}


def prize_table_by_zone(r):
    """Execute the original sign prize-table selector ($0C:$A909) for every zone."""
    out = {}
    for z in range(6):
        o = Oracle(r)
        o.bank(2, 0x0C)
        o.mem[0xD12B] = 0x0C
        o.mem[0xD297] = z
        o.cpu.pc, o.cpu.sp = 0xA909, 0xDFE0
        o.word(o.cpu.sp, o.RETURN)
        o.cpu.set_breakpoint(0xA913)
        o.cpu.set_breakpoint(0xA95C)
        for _ in range(5):
            o.cpu.ticks_to_stop = 10000
            o.cpu.run()
            if o.cpu.pc in (0xA913, 0xA95C):
                break
        out[f'zone{z}'] = hexb(o.cpu.hl, 4)
    base = 0x0C * 0x4000 - 0x8000
    return {'selector_routine': '0x0C:0xA909', 'table_cpu_by_zone': out,
            'tables_sha256': {'0xA919': digest(r[base + 0xA919:base + 0xA919 + 0x49]), '0xA962': digest(r[base + 0xA962:base + 0xA962 + 0x49])},
            'evidence': 'CONTROLLED ROUTINE RESULT (selector executed for zones 0..5)'}


def act_clear(r, acts, recs):
    signs = []
    for key in ('sez1', 'sez2'):
        a = acts[key]
        h = a['descriptor']['header']
        for x in recs[key]['records']:
            if x['type_id'] == '0x18':
                signs.append({'act': key, 'index': x['index'], 'world_x': x['world_x'], 'world_y': x['world_y'], 'raw_bytes': x['raw_bytes'],
                              'pan_target': [x['world_x'] - 128, x['world_y'] - 153], 'camera_limits_max': [h['ram_d282'], h['ram_d27e']],
                              'pan_target_inside_limits': 0 <= x['world_x'] - 128 < h['ram_d282'] and h['ram_d27c'] <= x['world_y'] - 153 < h['ram_d27e']})
    boss = next(x for x in recs['sez3']['records'] if x['type_id'] == '0x54')
    return {'sez1_sez2': 'ordinary type $18 sign clear (EDGE(RIGHT,+33) = playerX - cameraX >= $121), shared with THZ/GPZ/MGHZ',
            'signs': signs, 'prize_table': prize_table_by_zone(r),
            'sez3': {'sign_present': any(x['type_id'] == '0x18' for x in recs['sez3']['records']), 'boss_type': '0x54', 'boss_world': [boss['world_x'], boss['world_y']],
                     'clear_path': 'boss chain: shared $0A/$0F support + player state $20; SEZ3 gate/camera release not yet audited'}}


# --- viewport classification -----------------------------------------------------------------
def viewport_table(scans):
    """Explicit classification of every recovered camera/spawn/removal/screen-coordinate rule SEZ touches."""
    def refs(name):
        s = scans.get(name)
        return s['viewport_ram_references'] if s else {}
    return [
        {'id': 'player_start_camera', 'subject': 'act start camera/player', 'classification': 'WORLD', 'rule': 'direct word copies from the start record (no adapter offset)',
         'widescreen_candidate': None, 'evidence': 'SOURCE-TRACED loader $4E57'},
        {'id': 'camera_limits', 'subject': 'camera limits D280/D27C/D282/D27E', 'classification': 'WORLD', 'rule': 'left/top inclusive, right/bottom exclusive (3840/784 in every SEZ act)',
         'widescreen_candidate': 'right limit = worldWidth - viewportWidth is an explicit adapter, not ROM intent (as accepted for GPZ3/MGHZ3)', 'evidence': 'DECODED DATA + header loader'},
        {'id': 'mapped_lifecycle', 'subject': 'generic mapped-object create/sleep/delete (all SEZ placements incl. $20/$23/$26/$28/$10/$1B/$2F/$18)',
         'classification': 'EDGE', 'rule': 'visible band [LEFT,RIGHT), awake margin 32, create/sleep band 96..32 outside each edge, vertical bands unchanged',
         'widescreen_candidate': 'reuse the accepted post-wake horizontal retention adapter max(0, viewport_width - 256); vertical bands and PLAYER_DIST rules are not widened',
         'evidence': 'docs/viewport-semantics-audit.md; the placement creator $80EB and sleeping bit +$04 bit 6 are the same machinery for every SEZ type (static scans confirm +$04 bit 6 reads)'},
        {'id': 'sign_clear', 'subject': 'type $18 sign act clear (SEZ1/SEZ2)', 'classification': 'EDGE', 'rule': 'EDGE(RIGHT,+33): playerX - cameraX >= $121; sign pan target CENTER-relative (signX-128, signY-153)',
         'widescreen_candidate': 'preserve the edge relationship (accepted adapter)', 'evidence': 'docs/object-18-act-clear.md; docs/viewport-semantics-audit.md'},
        {'id': 'sign_wake_conversion', 'subject': 'type $18 wake with Spring Shoes state $12 -> $0E', 'classification': 'EDGE', 'rule': 'EDGE(RIGHT,+32) (screen X < 288 at 256 px)',
         'widescreen_candidate': 'preserve the edge relationship (accepted adapter)', 'evidence': 'docs/spring-shoes-presentation-audit.md'},
        {'id': 'boss_trigger', 'subject': 'type $54 boss trigger', 'classification': 'PLAYER_DIST', 'rule': 'strict abs(dx) < 160 and abs(dy) < 304 (framework row zone+$D4A5 = 2)',
         'widescreen_candidate': None, 'evidence': 'DECODED DATA: table $1E:$97A1; not widened'},
        {'id': 'boss_camera_lock', 'subject': 'type $54 camera target', 'classification': 'LOCKED_CAMERA', 'rule': 'target = anchor + (-224,-160) = (2976,462) nominal, pan 1 px/update, exclusive right limit stops 1 px short',
         'widescreen_candidate': 'explicit boss-composition adapter (as MGHZ3/GPZ3) belongs to the dedicated boss package; Research chooses no policy here',
         'evidence': 'DECODED DATA table $1E:$9808 + shared framework (not executed for SEZ3)'},
        {'id': 'crumble_object_13_left_edge', 'subject': 'type $13 dynamic child of surface $0C (callback $A36A)', 'classification': 'EDGE',
         'rule': 'object X minus cameraX < 0 (16-bit carry) takes the removal branch: EDGE(LEFT,0)', 'widescreen_candidate': 'left edge is unchanged by widening; only the unaudited rest of the routine may matter',
         'evidence': 'BYTE-VERIFIED ASSEMBLY $0C:$A370..$A37D (LD DE,($D174); SBC HL,DE; JR C); unaudited', 'scan_refs': refs('type_13')},
        {'id': 'enemy_20_23', 'subject': 'types $20/$23 callbacks', 'classification': 'PLAYER_DIST/WORLD', 'rule': 'static scan: no camera/screen RAM references; movement, contact and terrain probes are world/player relative',
         'widescreen_candidate': None, 'evidence': 'static code scan (see enemies.*.code_scan.viewport_ram_references)', 'scan_refs': {'0x20': refs('type_20'), '0x23': refs('type_23')}},
        {'id': 'platform_state_7', 'subject': 'type $28 state 7 (parameter $86, 3 SEZ platforms)', 'classification': 'WORLD', 'rule': 'static scan of $87E2 shows no camera RAM reference; travel limits come from placement aux1',
         'widescreen_candidate': None, 'evidence': 'static code scan (platform.state_7_scan)', 'scan_refs': refs('type_28_state_7')},
        {'id': 'boss_object_54', 'subject': 'type $54 internal screen/camera references', 'classification': 'UNRESOLVED', 'rule': 'camera RAM references listed in code_scan_boss; the dedicated boss audit must classify each',
         'widescreen_candidate': None, 'evidence': 'static code scan', 'scan_refs': refs('type_54')},
        {'id': 'player_edge_clamp', 'subject': 'player screen-edge clamp (camera+16..+247)', 'classification': 'EDGE', 'rule': 'SMS low-byte wrap is an artifact; accepted adapters already exist', 'widescreen_candidate': 'accepted adapter',
         'evidence': 'docs/viewport-semantics-audit.md'},
        {'id': 'effect_5_pause', 'subject': 'effect 5 (tile $158 animation) pause', 'classification': 'WORLD', 'rule': 'paused while $D44E != 0 (boss active); no viewport dependence', 'widescreen_candidate': None,
         'evidence': 'CONTROLLED ROUTINE RESULT (implementation-manifest level_effects)'}]


# --- footwear ----------------------------------------------------------------------------------
def footwear(r, acts, recs, mghz_vram, mghz_pal):
    f = C.footwear(r, acts, recs, None)
    old = json.loads((ROOT / 'data/rom-cache/powerup-shoes.json').read_text(encoding='utf-8'))['placements']['acts']
    f['cross_check'] = 'data/rom-cache/powerup-shoes.json placements zone 2'
    f['cross_check_counts_match'] = all(f['counts'][f'sez{a["act"] + 1}'] == {'rocket_shoes_monitors': a['rocket_shoes'], 'spring_shoes': a['spring_shoes']} for a in old if a['zone'] == 2)
    sez = acts['sez1']
    sload = next(x for x in sez['vram_loads'] if int(x['tile_base'], 16) == 0x94)
    mload = next(x for x in mghz_vram['vram_loads'] if int(x['tile_base'], 16) == 0xAC)
    spring = {'sez_load': sload, 'mghz_load': mload,
              'decoded_stream_identical': sload['decoded_sha256'] == mload['decoded_sha256'], 'same_rom_stream': sload['stream_rom'] == mload['stream_rom']}
    frames = []
    base_sez, base_mghz = 0x94, 0xAC
    for fi in range(5):
        a = C.frame_record(r, 0x2F, fi, base_sez, base_sez, bytes(sez['vram']), flips=(False,))
        b = C.frame_record(r, 0x2F, fi, base_mghz, base_mghz, bytes(mghz_vram['vram']), flips=(False,))
        frames.append({'frame': fi, 'sez_composition': [i['composed_index_sha256'] for i in a['images']], 'mghz_composition': [i['composed_index_sha256'] for i in b['images']],
                       'identical': [i['composed_index_sha256'] for i in a['images']] == [i['composed_index_sha256'] for i in b['images']]})
    si = sez['descriptor']['palette']['sprite_index']
    spring.update(frames=frames, all_frames_identical=all(x['identical'] for x in frames), sprite_palette={'sez_index': si, 'mghz_index': mghz_pal[0], 'cram_identical': sez_pal(r, si) == mghz_pal[1]})
    f['art'] = {'spring_shoes': spring,
                'rocket_shoes': 'type $10 parameter $04 monitor; monitor art and dynamic selector unchanged (zone independent)'}
    return f


def sez_pal(r, i):
    return list(r[L.PALETTE_DATA + i * 16:L.PALETTE_DATA + i * 16 + 16])


# --- six-zone census -----------------------------------------------------------------------------
def six_zone(r, graph):
    six = C.six_zone_census(r)
    out = {}
    all_types = sorted({int(x['type_id'], 16) for a in recs_all.values() for x in a['records']} & {int(x['type_id'], 16) for k, a in recs_all.items() if k.startswith('sez') for x in a['records']})
    for t in all_types + [0x55, 0x13, 0x07]:
        e = six.get(t, {'total': 0, 'acts': {}, 'parameters': Counter()})
        zones = sorted({k[:-1] for k in e['acts']})
        out[hexb(t)] = {'total_placements_all_zones': e['total'], 'placements_by_act': dict(sorted(e['acts'].items())), 'zones': zones,
                        'parameters': dict(sorted(e['parameters'].items())), 'sez_only': zones == ['sez'] or not zones,
                        'spawned_by_types': sorted(hexb(x) for x in graph.get(t, ())),
                        'buys_other_zone_coverage': [z for z in zones if z != 'sez']}
    return out


def build(r):
    if digest(r) != L.ROM_SHA256:
        raise ValueError('Expected canonical Europe v1.2 ROM')
    global recs_all
    recs_all = all_records(r)
    recs = decode_records(r)
    acts = {k: vram_for_act(r, i) for i, k in enumerate(recs)}
    zvram = zone_vrams(r)
    out = {'format': 1, 'rom_sha256': L.ROM_SHA256, 'research_base': F.RESEARCH_BASE,
           'scope': 'SEZ1-3 object census + reuse proofs + reconnaissance; not a behaviour audit', 'poc_inspected_read_only': POC_COMMIT,
           'classification_vocabulary': {'SHARED_RECOVERED': 'accepted runtime exists; only SEZ placement/art-base data to generate',
                                         'SHARED_WITH_SEZ_DATA': 'accepted runtime exists; SEZ adds parameters/art/placements that need audit-light verification',
                                         'SEZ_SPECIFIC_NEEDS_AUDIT': 'new runtime or an unaccepted state/parameter; dedicated audit required',
                                         'BOSS_SUPPORT': 'boss/controller', 'UNRESOLVED': 'not established'},
           'acts': {}}
    for key, v in recs.items():
        a = acts[key]
        rows = []
        for rec in v['records']:
            cx, cy = rec['world_x'] // 32, rec['world_y'] // 32
            inside = 0 <= rec['world_x'] < a['width'] * 32 and 0 <= rec['world_y'] < a['height'] * 32
            idx = cy * a['width'] + cx
            rows.append(dict(rec, inside_map=inside, anchor_cell=[cx, cy], anchor_block=a['cells'][idx] if inside and idx < a['runtime_cells'] else None, **classify(rec),
                             evidence='DECODED DATA; behaviour evidence in the referenced research'))
        out['acts'][key] = {'object_list': v['pointer'], 'terminator_rom': v['terminator_rom'], 'record_count': len(rows), 'records_sha256': v['records_sha256'],
                            'records': rows, 'type_counts': dict(sorted(Counter(x['type_id'] for x in rows).items())),
                            'category_counts': dict(sorted(Counter(x['category'] for x in rows).items())),
                            'classification_counts': dict(sorted(Counter(x['classification'] for x in rows).items())),
                            'off_map_records': [x['index'] for x in rows if not x['inside_map']]}
    graph = C.spawn_graph(r, sorted(set(C.six_zone_census(r)) | {0x07, 0x13, 0x55, 0x57, 0x58, 0x2E, 0x34, 0x12, 0x0F, 0x0A}))
    out['six_zone_reuse_census'] = {'types': six_zone(r, graph),
                                    'sez_only_types': [hexb(t) for t in SEZ_ONLY_TYPES],
                                    'dynamic_children_not_placed': {'0x55': 'spawned by $54 state 7 at (-16,-36)', '0x13': 'spawned by surface $0C handler $6B79 and by $13 state 1 (parameters 3/8/5/1)',
                                                                    '0x07': 'breakable-block fragments spawned by $7898 (surface $0D), base 0 art', '0x34/0x0F/0x0A/0x12': 'shared boss/defeat support'},
                                    'conclusion': 'types $20, $23, $54 (and children $55, $13) appear in no other zone: researching them buys SEZ coverage only; $26/$28/$10/$18/$1B/$2F are shared across zones'}
    # shared reuse proof
    proof = {}
    for t in SHARED_TYPES:
        if t == 0x18:
            sc, scan = type_scan(r, t)
            proof[hexb(t)] = {'type': t, 'sez_acts': ['sez1', 'sez2'], 'bank': sc['bank'], 'state_table_cpu': hexb(sc['state_table_cpu'], 4), 'state_count': sc['state_count'],
                              'dynamic_art': {'selector': '$12 (zone independent list)', 'list': [{k: e[k] for k in ('tile_base', 'tile_count', 'vram_destination')} for e in D.dynamic_list_for_selector(r, 0x12)[1]]},
                              'prize_table': 'zone 2 -> first table $A919 (same parity as THZ)', 'frame_comparison': None,
                              'state_script_and_callback_regions_sha256': digest(json.dumps(scan['code_regions'], sort_keys=True).encode())}
        else:
            proof[hexb(t)] = reuse_proof(r, t, acts, zvram)
    out['shared_reuse_proof'] = proof
    out['act_clear'] = act_clear(r, acts, recs)
    out['fragment_art_proof'] = fragment_art_proof(r, zvram)
    out['support_art_proof'] = support_art_proof(r, zvram)
    out['springs'] = spring_placements(r, acts, recs)
    out['shared_system_proofs'] = shared_system_proofs(r, F.zone_sites(r))
    out['platform'] = platform_recon(r, acts, recs)
    out['footwear'] = footwear(r, acts, recs, zvram['mghz1'], (zvram['mghz1']['descriptor']['palette']['sprite_index'], sez_pal(r, zvram['mghz1']['descriptor']['palette']['sprite_index'])))
    out['enemies'] = enemy_recon(r, acts, recs)
    out['boss'] = boss_recon(r, acts, recs)
    scans = {'type_13': type_scan(r, 0x13)[1], 'type_20': out['enemies']['0x20']['code_scan'], 'type_23': out['enemies']['0x23']['code_scan'],
             'type_28_state_7': scan_code(r, 0x1E, [0x87E2], 'x'), 'type_54': out['boss']['code_scan_boss']}
    out['crumble_object_13'] = {'state_machine': C.public_script(C.state_scripts(r, 0x13)), 'code_scan': scans['type_13'],
                                'evidence': 'DECODED DATA + BYTE-VERIFIED ASSEMBLY; spawn site and dedup are CONTROLLED ROUTINE RESULTS (implementation-manifest)'}
    out['viewport_classification'] = viewport_table(scans)
    out['support_art_dependencies'] = {'platform_28': 'placement aux0 $6A; VRAM load $26370 -> tile $6A (8 tiles) in SEZ ($26470 in MGHZ): different stream, compared in shared_reuse_proof',
                                       'breakable_fragments_type_07': 'type $07 (and the crumble child $13), created by $5E9C with base 0 (no placement bases): mapping frame 15 is one 8x16 piece at tile $66/$67 of the common object stream; see fragment_art_proof',
                                       'sign_18': 'dynamic selector $12 overwrites VRAM tiles $6A..$A9 at act clear (original behaviour; keep sprite atlases separate): in SEZ this covers the platform/$26/$23/$2F art loads',
                                       'monitor_10': 'static art base from the common stream ($23340 -> $10, 90 tiles); item icons are dynamic selectors independent of the zone'}
    out['unresolved'] = ['Human-facing names of $20/$23/$54 are not proven; community labels are leads only.',
                         'Types $20/$23 gameplay (contact, defeat, hop timing) is not audited; traces are controlled initialisation/movement only.',
                         'Platform parameters $86/$04 are ROM-audited in platform-28-runtime.json; POC implementation/Windows acceptance pending.',
                         'Boss $54: hit count, state behaviour, arena clamp, camera release and clear gate are census-level only.',
                         'Type $13 crumble object and surface $0C, surface $1A booster: dedicated audit (see implementation manifest).',
                         'Fragment art is resolved (common-stream tile $66/$67, zone independent); only the visual sign-off of the shard in the SEZ sprite palette remains (shared board).']
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
            raise SystemExit('SEZ object census differs')
    else:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(text, encoding='utf-8')
    v = json.loads(text)
    print(json.dumps({k: x['type_counts'] for k, x in v['acts'].items()}, indent=1))


if __name__ == '__main__':
    main()
