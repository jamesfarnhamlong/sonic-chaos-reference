"""Enumerate natural spring/bounce applications; reuse closed runtime contracts.

No emulator sweeps, POC writes, ROM bytes or graphics are emitted.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

import level_package as L
import rom as R

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/rom-cache/spring-application-census.json'
BASE = '81b82941e7f44865e0d551484bee82d28d600d43'
ZONES = ('thz', 'gpz', 'sez', 'mghz', 'aqz')
EVIDENCE = ['docs/spring-interaction-audit.md',
            'docs/player-spring-airborne-state-closure.md',
            'docs/powerup-shoes-audit.md', 'docs/movement.md']


def contract(mechanism, vx, vy, state, d448, bits, family, **extra):
    return dict(mechanism=mechanism, launch_vx=vx, launch_vy=vy,
                requested_player_state=state, d448_write=d448,
                expected_d503=dict(low_bits=bits, other_bits='preserved'),
                expected_animation_family=family, **extra)


def upright(mechanism, vy, strong):
    return contract(mechanism, 'preserved', vy, 11, 255 if strong else 0,
                    1, 'tall_61' if strong else 'tumble_1C_21',
                    strength='strong' if strong else 'weak')


def diagonal(zone, block):
    return contract('terrain diagonal', -4 if block >= 0x38 else 4,
                    -7 if zone == 0 else -5.5, 28, 0, 3, 'tumble_1C_21',
                    strength='not applicable', path='$691A -> $6A90 -> $482D')


def terrain_contracts(zone, block, surface):
    if surface == 9:
        return [upright('terrain upright', -7.5, True)]
    if surface == 10:
        return [contract('terrain horizontal', {'right_probe': -6, 'left_probe': 6},
                         'preserved', 9, 'preserved', 2, 'spin_25_29',
                         solid_half='left' if block < 0x34 else 'right')]
    if surface == 20:
        rows = [diagonal(zone, block)]
        if block in (0x3A, 0x3B):
            rows.append(contract('ceiling $3A/$3B', 4, 5.5, 27, 'preserved',
                                 3, 'spin_25_29',
                                 path='$73C9 and unconditional $753E tail -> $749D',
                                 note='Includes falling contact through terrain-ring probe; floor dispatch is separately listed.'))
        return rows
    if surface in (13, 22):
        return [contract('breakable bounce', 'preserved', -4.25, 'preserved',
                         'preserved', 3, 'executing script preserved',
                         gate='attack required; see closed type $0D/$16 contact gates')]
    if surface == 18:
        return [contract('terrain ramp', 'preserved', '-(abs(vx_8_8) + floor(abs(vx_8_8)/2))/256',
                         27, 'preserved', 3, 'spin_25_29',
                         gate='eligible nonzero previous modifier branch; asymmetric contact gates at $69B2',
                         alternatives='zero previous modifier may first request $09 with vx +/-4; see docs/movement.md')]
    if surface == 21:
        return [contract('terrain type $15 ceiling bounce', 'preserved', 7.5, 27,
                         'preserved', 3, 'spin_25_29')]
    return []


def object_contracts(rec):
    t, p, aux = (int(rec[k], 16) for k in ('type_id', 'parameter', 'aux1'))
    if t in (0x26, 0x30):
        strong = aux == 0 if p & 128 else p == 0
        c = upright('mapped $%02X' % t, -7.375 if strong else -5, strong)
        c.update(form='span' if p & 128 else 'fixed',
                 span_width=(p & 127)*16 if p & 128 else None,
                 rest_y=rec['world_y']+12)
        return [c]
    if t in (0x21, 0x50):
        return [upright('type $21 stomp' if t == 0x21 else 'type $50 boss bounce',
                        -6.75 if t == 0x21 else -4, t == 0x21)]
    if t == 0x2F:
        return [contract('type $2F Spring Shoes automatic bounce', 'preserved', -7.5,
                         18, 'preserved', 'airborne set; attack preserved',
                         'shoe_0B', note='Pickup has no velocity write; row describes subsequent floor rebound while attached.')]
    return []


def build(rom):
    acts, occurrences = {}, []
    for zone, name in enumerate(ZONES):
        for act in range(3):
            key = name + str(act+1)
            h = L.act_header(rom, zone, act)
            cells, end, _ = L.decode_layout_stream(rom, h['layout_rom'], 4095)
            recs, obj_end = L.decode_object_list(rom, L.object_list_pointer(rom, zone, act)['list_rom'])
            acts[key] = dict(zone_id=zone, act=act+1, width_cells=h['width_cells'],
                             runtime_cells=len(cells), layout_rom=h['layout_rom'],
                             layout_end=end, layout_sha256=L.sha256(bytes(cells)),
                             object_terminator_rom=obj_end)
            for index, block in enumerate(cells):
                hd = R.header(rom, block)
                applications = terrain_contracts(zone, block, hd['flags'] & 31)
                if applications:
                    occurrences.append(dict(id=f'{key}:cell:{index}', zone=name,
                        act=act+1, act_key=key, source='terrain cell', cell_index=index,
                        world_x=index % h['width_cells']*32,
                        world_y=index // h['width_cells']*32, block_id=block,
                        surface_type=hd['flags'] & 31, collision_header_rom=hd['address'],
                        applications=applications))
            for rec in recs:
                applications = object_contracts(rec)
                if applications:
                    # Numeric identities and original record provenance, no raw byte dump.
                    occurrences.append(dict(id=f'{key}:object:{rec["index"]}',
                        zone=name, act=act+1, act_key=key, source='mapped placement',
                        world_x=rec['world_x'], world_y=rec['world_y'],
                        placement_index=rec['index'], placement_rom=int(rec['rom_offset'],16),
                        placement_bank=int(rec['bank'],16), placement_cpu=int(rec['cpu'],16),
                        **{k:int(rec[k],16) for k in ('type_id','flags','parameter','aux0','aux1')},
                        applications=applications))
    counts = Counter(c['mechanism'] for o in occurrences for c in o['applications'])
    return dict(format=1, rom_sha256=L.ROM_SHA256, research_base=BASE,
        evidence='decoded data; source-traced behavior; accepted controlled routine results',
        evidence_sources=EVIDENCE, scope='15 implemented normal acts; no special stages or Electric Egg',
        accepted_cache_sha256={name:hashlib.sha256((ROOT/'data/rom-cache'/name).read_bytes()).hexdigest()
                               for name in ('spring-interaction.json','player-spring-airborne.json','powerup-shoes.json')},
        conventions=dict(coordinates='WORLD: terrain cell top-left or mapped initial placement; moving objects contact at current anchor',
                         velocities='pixels/update; preserved means no write, not zero',
                         states='numeric byte IDs; setter exit, before remaining player wrapper logic',
                         flags='low bits 0/1 only; all other D503 bits preserved',
                         animation='family selected on state/script entry; same-state request does not restart current script'),
        acts=acts, counts=dict(sorted(counts.items())), occurrences=occurrences,
        unresolved=['Ramp response depends on previous modifier, direction and contact flags; occurrence alone does not select one launch.',
                    'No natural surface type $15 in these acts; synthetic controls excluded.',
                    'Census covers closed spring/bounce mechanisms, not all enemy-hit/monitor/boss damage responses.'])


def poc_crosscheck(census, poc, rom):
    """Read generated literal tables. Absence of a recognized table is unresolved."""
    texts = {str(p.relative_to(poc)):p.read_text(encoding='utf-8-sig')
             for p in (poc/'scripts').glob('*/*.gml')}
    functions = {}
    for path, text in texts.items():
        for m in re.finditer(r'function\s+(\w+)\(\)\s*\{\s*return\s*(\[.*?\]);\s*\}', text, re.S):
            try:
                literal = re.sub(r'\$([0-9A-Fa-f]+)', lambda h:str(int(h[1],16)), m[2])
                literal = re.sub(r',\s*([\]}])', r'\1', literal)
                functions[m[1]] = (path, json.loads(literal))
            except ValueError:
                pass
    checks, mismatches, unresolved = [], [], []
    motion_path = 'scripts\\SCR_chaos_motion_data\\SCR_chaos_motion_data.gml'
    motion = texts.get(motion_path, '')
    match = re.search(r'global\.chaosTileIds\s*=\s*(\[.*?\]);', motion, re.S)
    if match:
        functions['SCR_chaos_thz1_tile_ids'] = (motion_path, json.loads(match[1]))
    for key in census['acts']:
        own = [o for o in census['occurrences'] if o['act_key'] == key]
        for suffix, source in (('tile_ids', 'terrain cell'), ('objects', 'mapped placement')):
            fn = 'SCR_chaos_'+key+'_'+suffix
            if fn not in functions:
                if key == 'thz1' and source == 'mapped placement':
                    room_path = poc/'rooms/ROM_chaos_thz1/ROM_chaos_thz1.yy'
                    room_text = room_path.read_text(encoding='utf-8')
                    room = json.loads(re.sub(r',\s*([\]}])', r'\1', room_text))
                    relevant = [o for o in own if o['source']==source]
                    expected = []
                    for o in relevant:
                        if o['type_id']==0x26:
                            c=o['applications'][0]
                            tag='span' if c['form']=='span' else ('normal' if c['strength']=='strong' else 'weak')
                            obj='OBJ_chaos_object_spring_26_'+tag
                        else:
                            obj='OBJ_chaos_object_21'
                        expected.append((obj,o['world_x'],o['world_y']))
                    actual = [(i['objectId']['name'],i['x'],i['y']) for l in room['layers'] for i in l.get('instances',[])
                              if i['objectId']['name'].startswith('OBJ_chaos_object_spring_26_') or i['objectId']['name']=='OBJ_chaos_object_21']
                    if Counter(expected)!=Counter(actual):
                        mismatches.append(dict(act=key, expected_instances=expected,actual_instances=actual))
                    checks.append(dict(act=key,table='room-authored spring/stomp instances',path=str(room_path.relative_to(poc)),sha256=hashlib.sha256(room_text.encode()).hexdigest()))
                    continue
                unresolved.append(dict(act=key, table=fn, reason='literal table not found; requires separate room/legacy-table inspection'))
                continue
            path, data = functions[fn]
            checks.append(dict(act=key, table=fn, path=path, sha256=hashlib.sha256(texts[path].encode()).hexdigest()))
            expected = {o['cell_index']:o for o in own if o['source']==source} if source=='terrain cell' else {o['placement_index']:o for o in own if o['source']==source}
            if source == 'terrain cell':
                actual = {i:b for i,b in enumerate(data) if terrain_contracts(census['acts'][key]['zone_id'], b, R.header(rom,b)['flags']&31)}
                for i in sorted(set(expected)|set(actual)):
                    want = expected[i]['block_id'] if i in expected else None
                    if actual.get(i) != want:
                        mismatches.append(dict(act=key, cell_index=i, expected_block=want, actual_block=actual.get(i)))
            else:
                actual = {r[0]:r for r in data if r[3] in (0x26,0x30,0x21,0x50,0x2F)}
                for i in sorted(set(expected)|set(actual)):
                    o = expected.get(i)
                    want = [i,o['world_x'],o['world_y'],o['type_id'],o['flags'],o['parameter'],o['aux0'],o['aux1']] if o else None
                    got = actual[i][:8] if i in actual else None
                    if want != got:
                        mismatches.append(dict(act=key, placement_index=i, expected=want, actual=got))
    runtime_names=('SCR_chaos_level','SCR_chaos_spring','SCR_chaos_core','SCR_chaos_boss')
    runtime_hashes={p:hashlib.sha256(t.encode()).hexdigest() for p,t in texts.items()
                    if any(p.endswith(n+'.gml') for n in runtime_names)}
    return dict(scope='generated literal terrain and placement tables; runtime handlers reviewed separately in documentation',
                runtime_source_sha256=runtime_hashes,
                tables_checked=checks, mismatches=mismatches, unresolved=unresolved)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom')
    p.add_argument('--check', action='store_true')
    p.add_argument('--poc', type=Path)
    a = p.parse_args()
    rom = L.load_rom(a.rom)
    result = build(rom)
    text = json.dumps(result, indent=2)+'\n'
    if a.check:
        assert OUT.read_text(encoding='utf-8') == text, 'census stale'
    else:
        OUT.write_text(text, encoding='utf-8')
    if a.poc:
        report = poc_crosscheck(result, a.poc, rom)
        (ROOT/'reports/spring-application-poc-crosscheck.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        print('POC tables:',len(report['tables_checked']),'mismatches:',len(report['mismatches']),'unresolved tables:',len(report['unresolved']))
    print(len(result['occurrences']), 'occurrences;', result['counts'])


if __name__ == '__main__':
    main()
