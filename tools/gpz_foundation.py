#!/usr/bin/env python3
"""Deterministic GPZ1-3 foundation package; no ROM/art dumps are emitted."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
import level_package as L
import rom as R
import thz1_animation_reach as A
import thz1_object_assets as G
import platform_spike_collision as P
import thz3_boss_support as B
import object_18 as O18

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'data/rom-cache/gpz/implementation-manifest.json'
ACTS = {f'gpz{n+1}': {'zone': 1, 'act': n, 'name': f'Gigalopolis Zone Act {n+1}'} for n in range(3)}
STATUSES = ('REUSED_SUPPORTED', 'REUSED_NEEDS_DATA', 'NEW_NEEDS_RESEARCH', 'BOSS', 'PRESENTATION_ONLY', 'UNRESOLVED')
REWARDS = {1: 'ten rings', 2: 'life counter +1 (BCD D299)', 3: 'speed power selector 3; 900 updates', 4: 'Rocket Shoes', 6: 'invincibility'}
NEW_SURFACES = {0x16: 'breakable + bounce; replacement $46 and ring reward ($7857)', 0x19: 'sets player +$24 bit 0 and increments $D3BC ($6B23); consumers unresolved'}
REQUIREMENTS = [
    {'id': 'platform_state4', 'status': 'REUSED_NEEDS_DATA', 'contract': '$28/$83: accepted isometric-platform audit; sag/recover 8, delay 80, gravity 48/256, post-move support, permanently consumed after triggered removal'},
    {'id': 'platform_state10', 'status': 'REUSED_NEEDS_DATA', 'contract': '$28/$89: horizontal reversal mover, initial vx=256/256, period 16*aux1; bit7 sag, X carry, keep-alive $8908; scripts/callbacks included'},
    {'id': 'platform_state13', 'status': 'REUSED_NEEDS_DATA', 'contract': '$28/$05: stationary contact trigger -> +$36 (initialized to 6); state6 vertical touch mover; not THZ state5 sag'},
    {'id': 'non_thz_diagonal', 'status': 'REUSED_NEEDS_DATA', 'contract': 'zone D297 != 0 selects vy=-1408/256 (-5.5), not THZ -1792/256 (-7.0); vx remains +/-1024/256'},
    {'id': 'ceiling_spring', 'status': 'REUSED_NEEDS_DATA', 'contract': 'GPZ2 has 15 block $3A cells; existing spring audit ceiling contract $749D (vx=1024, vy=1408, requested state $1B); POC ceiling currently rejects surface $14'},
    {'id': 'surface16', 'status': 'REUSED_NEEDS_DATA', 'contract': 'floor $6AE3 break/bounce/reward is absent in POC; preserve attack/state/velocity gates; do not replace with monitor overlap'},
    {'id': 'surface19', 'status': 'UNRESOLVED', 'contract': '$85/$87 cells run $6B23; numeric writes proven, downstream +$24/$D3BC consumers need bounded follow-up before claiming faithful traversal'},
    {'id': 'surface1c_ceiling', 'status': 'REUSED_NEEDS_DATA', 'contract': 'POC floor bit6 special case and side profiles exist; ceiling currently rejects type28; reconcile with accepted isometric underside results rather than treating all $1C as data-only'},
]

def digest(data):
    return hashlib.sha256(data).hexdigest()

def stable(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()

def cache_ref(path):
    value = json.loads((ROOT / path).read_text(encoding='utf-8'))
    if value['rom_sha256'] != L.ROM_SHA256:
        raise ValueError(path)
    return {'path': path, 'canonical_json_sha256': digest(stable(value))}

def classify(rec):
    t, p = int(rec['type_id'], 16), int(rec['parameter'], 16)
    if t == 0x51:
        return 'BOSS', 'GPZ boss/controller type $51', False
    if t in (0x25, 0x2C):
        return 'NEW_NEEDS_RESEARCH', f'Numeric type ${t:02X}; enemy/contact candidate; human identity unresolved', False
    names = {9: 'object ring', 0x10: 'monitor', 0x18: 'goal sign', 0x1B: 'moving spike', 0x26: 'upright mapped spring', 0x28: 'platform'}
    if t == 0x28 and p != 0x0A:
        return 'REUSED_NEEDS_DATA', names[t], False
    if t in names:
        return 'REUSED_SUPPORTED', names[t], True
    return 'UNRESOLVED', 'Numeric identity only', False

def cell_record(index, block, width):
    return {'layout_index': index, 'cell_x': index % width, 'cell_y': index // width,
            'world_x': index % width * 32, 'world_y': index // width * 32, 'block_id': block}

def region(r, bank, a, b):
    off = a if a < 0x8000 else bank * 0x4000 + a - 0x8000
    return {'bank': bank, 'cpu': a, 'rom': off, 'length': b-a, 'sha256': digest(r[off:off+b-a])}

def boss_census(r):
    t = A.animation_state_table(r, 0x51)
    # Census only: explicit script spawns; do not infer a full runtime graph.
    scripts = {str(n): B.decode_script(r, t['bank'], t['state_script_cpus'][n]) for n in (1, 2, 3, 4, 14, 17)}
    spawns = [dict(state=int(n), **e) for n, script in scripts.items() for e in script if e.get('op') == 'spawn']
    return {'type': 0x51, 'name': 'GPZ boss/controller (numeric identity proven; design name unresolved)',
            'state_table': t, 'explicit_script_spawns': spawns,
            'shared_support': [{'type': 0x12, 'source': 'state0 script call $81A6 (shared HUD allocator)'},
                               {'type': 0x34, 'source': 'explicit scripts: parameters 8 and 4'}],
            'completion_dependencies': 'UNRESOLVED: $0A/$0F must not be assumed from THZ; full boss audit deferred',
            'foundation_policy': 'skip mapped $51 and all its dynamic children; no arena lock, boss HUD removal or invented completion',
            'evidence': 'DECODED DATA (scripts/type table); census only'}

def build(r):
    if digest(r) != L.ROM_SHA256:
        raise ValueError('Expected canonical Europe v1.2 ROM')
    out = {'format': 1, 'rom_sha256': L.ROM_SHA256, 'research_base': '3141c9a',
           'scope': 'GPZ1-3 non-enemy foundation; decoded metadata, not a ROM/art dump',
           'coordinate_policy': 'mapped anchor = stored-256; terrain origin = cell*32; presentation never changes collision anchor',
           'status_definitions': {s: {'REUSED_SUPPORTED': 'current POC gameplay exists; zone art/data still must be generated',
                'REUSED_NEEDS_DATA': 'canonical prior research exists; importer/runtime integration missing',
                'NEW_NEEDS_RESEARCH': 'deliberately skipped next-pass type', 'BOSS': 'exclude boss and its entire dynamic chain',
                'PRESENTATION_ONLY': 'no foundation collision', 'UNRESOLVED': 'insufficient established evidence'}[s] for s in STATUSES},
           'dependencies': [cache_ref(p) for p in ('data/rom-cache/isometric-platform.json', 'data/rom-cache/spring-interaction.json',
                'data/rom-cache/platform-spike-collision.json', 'data/rom-cache/powerup-shoes.json')],
           'runtime_requirements': REQUIREMENTS, 'gpz3_boss': boss_census(r), 'acts': {}}
    accepted_iso = json.loads((ROOT / 'data/rom-cache/isometric-platform.json').read_text(encoding='utf-8'))
    out['surface1c_contract'] = {'blocks': accepted_iso['terrain_blocks'],
        'floor_special_case': 'previous surface low5=$1C AND sampled vertical bit6 -> effective height32; raw $54 must not become20',
        'side_underside': 'accepted docs/isometric-platform-audit.md section2 and dependency boundary sweeps; retain ordinary side/ceiling probes'}
    out['poc_read_only'] = {'commit': '42aaa5032cef385284a00d0c1b7a0e7714747b4b',
        'worktree': 'SonicChaos_POC_thz1_cleanup', 'clean_at_inspection': True,
        'reusable': ['variable width lookup', 'terrain raw profiles and $1C floor bit6 rule', 'both ring pipelines',
                     'mapped fixed/span strong/weak springs', 'static $3C spikes and $1B', 'monitor selectors1/2/3/4/6',
                     '$28 support/ownership/carry and $0A lift', 'ordinary sign completion', 'viewport/lifecycle helpers'],
        'scope_note': 'THZ-specific act selection/data/art wiring must become zone-aware; foundation is not yet runtime-ready'}
    for k, meta in ACTS.items():
        a = L.build_act(r, k, meta)
        d = a['descriptor']; h = d['header']; start = d['start']; width = a['width']
        cells = a['cells'][:a['runtime_cells']]
        records = []
        for row in a['records']:
            status, name, now = classify(row)
            rec = dict(row, status=status, identification=name, instantiate_current_runtime=now,
                       evidence='DECODED DATA; behavior evidence in dependency caches')
            t = int(row['type_id'], 16); p = int(row['parameter'], 16)
            if t == 0x10:
                rec['reward'] = REWARDS.get(p, 'UNRESOLVED')
                rec['reward_evidence'] = 'docs/object-10.md; docs/thz2-thz3-object-deltas.md; docs/powerup-shoes-audit.md'
            if t == 0x26:
                span = bool(p & 128)
                rec['spring'] = {'form': 'hidden_span' if span else 'fixed', 'span_pixels': (p & 127)*16 if span else None,
                    'weak': int(row['aux1'],16) != 0 if span else p != 0, 'runtime_rest_y': row['world_y']+12}
            if t == 0x28:
                rec['initial_state'] = 13 if p & 127 in (5,11) else (p & 63)+1
            records.append(rec)
        block_defs = []
        counts = Counter(cells)
        replacement_blocks = {0x46, 0x9D}
        for table in a['semantics']['tables'].values():
            replacement_blocks.update(table['replacement_blocks'])
        block_set = sorted(set(cells) | replacement_blocks)
        pix = L.block_pixel_maps(r, a['vram'], only=block_set, mapping_rom=h['block_mapping_rom'])
        for block in block_set:
            count = counts[block]
            hd = R.header(r,block); surface = hd['flags'] & 31
            mapping = L.block_mapping(r,h['block_mapping_rom'],block)
            status = 'SURFACE_1C' if surface == 28 else ('NEW_OR_UNRESOLVED' if surface in NEW_SURFACES else 'THZ_SUPPORTED')
            block_defs.append({'block_id':block, 'cell_count':count, 'surface':surface, 'status':status,
                'runtime_note':NEW_SURFACES.get(surface, 'shared profile/probe path; see explicit runtime requirements'),
                'headers': [R.header(r,block,plane) for plane in (0,1)], 'mapping':mapping,
                'mapping_sha256':digest(b''.join(v.to_bytes(2,'little') for v in mapping['attributes'])),
                'decoded_palette_index_sha256':digest(bytes(v for row in pix[block] for v in row)),
                'nonzero_pixels':sum(bool(v) for row in pix[block] for v in row)})
        terrains = {'upright': [], 'diagonal_right': [], 'diagonal_left': [], 'horizontal': [], 'ceiling': [], 'static_spikes': [],
                    'surface1c': [], 'breakable16': [], 'surface19': []}
        for i,b in enumerate(cells):
            category = ('upright' if b in (0x30,0x31) else 'diagonal_right' if b in (0x36,0x37) else
                        'diagonal_left' if b in (0x38,0x39) else 'horizontal' if b in (0x32,0x33,0x34,0x35) else
                        'ceiling' if b in (0x3A,0x3B) else 'static_spikes' if R.header(r,b)['flags']&31 == 5 else
                        'surface1c' if R.header(r,b)['flags']&31 == 28 else 'breakable16' if R.header(r,b)['flags']&31 == 22 else
                        'surface19' if R.header(r,b)['flags']&31 == 25 else None)
            if category: terrains[category].append(cell_record(i,b,width))
        rings = {'terrain':a['terrain_rings'], 'object09':L.object_rings(a), 'presence_and_replacement_tables':a['semantics'],
                 'collection_contract': 'unchanged THZ point probe + parity / strict type09 anchor proximity; preserve bounded runtime cells'}
        rings['coordinate_sha256'] = L.coordinate_hash(L.ring_hash_rows(rings['terrain']+rings['object09']))
        out['acts'][k] = {'descriptor':d, 'dimensions_pixels':[width*32,a['height']*32],
            'start':{'player_anchor':[start['ram_d511'],start['ram_d514']], 'camera':[start['ram_d2d6'],start['ram_d2d8']],
                     'evidence':'SOURCE-TRACED loader $4E57; direct word copies, no inferred offsets'},
            'bounds': {'camera_min_words':[h['ram_d280'],h['ram_d27c']], 'camera_max_words':[h['ram_d282'],h['ram_d27e']],
                       'source':'header +12/+14/+16/+18 -> D280/D27C/D282/D27E; SMS values, widescreen adapter explicit'},
            'layout':{'rows':[a['cells'][i:i+width] for i in range(0,len(a['cells']),width)],
                      'runtime_written_cells':a['runtime_cells'], 'encoded_cells_sha256':digest(bytes(a['cells'])),
                      'runtime_cells_sha256':digest(bytes(cells)), 'last_cell_policy':'index >= runtime_written_cells is not ROM-loaded terrain'},
            'blocks':block_defs,'terrain_interactions':terrains,'rings':rings,'objects':records,
            'object_terminator_rom':a['object_terminator_rom'],
            'object_records_sha256':digest(r[d['objects']['list_rom']:a['object_terminator_rom']]),
            'census':{'types':dict(sorted(Counter(x['type_id'] for x in records).items())),
                      'statuses':dict(sorted(Counter(x['status'] for x in records).items())),
                      'terrain_rings':len(rings['terrain']), 'object_ring_parameters':dict(Counter(x['parameter'] for x in rings['object09'])),
                      'terrain_interactions':{n:len(v) for n,v in terrains.items()}},
            'foundation':{'instantiate_indices':[x['index'] for x in records if x['instantiate_current_runtime']],
                          'integrate_before_instantiating_indices':[x['index'] for x in records if x['status']=='REUSED_NEEDS_DATA'],
                          'deliberately_skip_indices':[x['index'] for x in records if x['status'] in ('NEW_NEEDS_RESEARCH','BOSS','UNRESOLVED')]},
            'act_clear':{'ordinary_sign_indices':[x['index'] for x in records if x['type_id']=='0x18'],
                         'contract':'shared $18 -> $19 -> player $20; no zone branch in sign contact' if k!='gpz3' else 'no sign; skip boss completion in foundation'},
            'graphics':{'static_vram_loads':a['vram_loads'], 'vram_sha256':digest(a['vram']),
                        'palettes':{n:{'rom':d['palette'][n+'_rom'], 'index':d['palette'][n+'_index'],
                            'cram':list(r[d['palette'][n+'_rom']:d['palette'][n+'_rom']+16])} for n in ('background','sprite')},
                        'registration':'shared 32px cell -> 4x4 8px mappings; palette/flip/priority attributes retained; transparent $1C cells remain collision-only',
                        'background_policy':'static ROM tilemap presentation reconstructed from layout/mappings; dynamic palette/scroll changes unresolved, no fabricated parallax',
                        'extraction':'level_package build_vram/block_pixel_maps and level_maps render accept explicit GPZ descriptors; local PNGs optional, not canonical cache content'}}
    out['platform_scripts'] = P.platform_modes(r)['states']
    out['ordinary_sign_prize_tables'] = O18.prize_tables(r)
    out['object_mappings'] = {str(t):G.object_mapping(r,t) for t in (9,0x10,0x18,0x1B,0x26,0x28)}
    # Mapping helper returns bytes; replace by descriptive numeric coordinates.
    for m in out['object_mappings'].values():
        m['pointer_raw'] = m['pointer_raw'].hex()
    out['source_regions'] = {n:region(r,*v) for n,v in {
        'start_loader':(1,0x4E57,0x4E98),'surface16':(1,0x6AE3,0x6B14),'surface19':(1,0x6B23,0x6B2C),
        'diagonal_zone_gate':(1,0x6A90,0x6ACE),'platform_state10':(30,0x8662,0x86A1),
        'platform_state13':(30,0x85FE,0x8628)}.items()}
    out['unresolved'] = ['Human enemy names and complete $25/$2C hazard/child behavior deferred.',
        'Surface $19 downstream state/terrain-animation consumers require follow-up; numeric writes established.',
        'Dynamic GPZ palette/background animation and scroll registration require presentation verification.',
        'GPZ3 boss full dependency/completion graph deferred; no inherited THZ completion assumption.']
    return out

def dumps(value):
    return json.dumps(value,indent=2)+'\n'

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('--output',type=Path,default=OUTPUT);p.add_argument('--check',action='store_true');a=p.parse_args()
    value=build(L.load_rom(a.rom));s=dumps(value)
    if a.check:
        if a.output.read_text(encoding='utf-8')!=s: raise SystemExit('GPZ cache differs')
    else:
        a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(s,encoding='utf-8')
    print(json.dumps({k:v['census'] for k,v in value['acts'].items()},indent=2))
if __name__=='__main__': main()
