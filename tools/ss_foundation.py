"""SS-A1: Special Stage foundation (indexing, entry/exit contract, five-stage metadata, census).

Decoded data and original loaders only.  Terrain/object runtime closure is in the later SS-A2..A5 packages.
"""
import argparse
import json
from collections import Counter
from pathlib import Path
import level_package as L
import rom as R
import aqz_foundation as A
import mghz_foundation as M
import mghz_object_census as C
import sez_foundation as S
from oracle import Oracle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/rom-cache/special-stages'
BASE = 'c4c389c28fe686713d9371fb925f60eb4014191c'
STAGES = {f'ss{i}': dict(zone=7 + i, act=0, name=f'Special Stage {i}', index=i, completion_bit=1 << (i - 1)) for i in range(1, 6)}

# Static facts, each BYTE-VERIFIED by the listed ROM address (see docs/special-stages-foundation-audit.md).
ENTRY = dict(
    gate=dict(routine='$178F', checks=['player character $D2C8 == 1 (Sonic)', 'current zone $D297 < 6', '$D2CC & $1F != $1F'],
              effects=['$D294 := $88', '$D2CD := 1', 'timer-run flag $D2BE := 0']),
    callers=dict(ring_counter='$3138 -> BCD wrap of $D29A to $00 -> $3104 (extra life, cap 99) -> $178F',
                 ring_monitor_plus10='$4AC0: $D29A += $10 (BCD); if result < $10 -> $3104 -> JP $178F'),
    zone_select='$187B: saved zone $D296 := $D297; $D297 := 8 + number of consecutive set bits of $D2CC starting at bit 0 (max 4)',
    sequence=['$1762 (mode bit3) -> $17B0', 'sound $8A, 30 frames', '$1CEB clear', 'palette fade flags $D492/$D494, 150 frames', '$187B', '$4FCE clear $D15E..$D28F',
              '$2934 level load (clears $D300..$DBBF)', '$3116/$314A HUD', 'timer $D2BF:$D2C0 := $0059', '$285C/$189B/$794F', '$1758 timer-run $D2BE := $FF', 'mode bit3 cleared'])
EXIT = dict(
    success='object type $31 (bank $1E:$9489): D2A6 := D2BF<<8; D2CC |= param; D2CD := $FF; slot type $FF; D294 |= $40; D2C3 := (D2C3+1)&$7F',
    failure=['death request $4984 -> $49A0: zone >= 8 -> D294 |= $20 (no D293 bit2, no life lost)', 'timer underflow $2826..$2846 -> D294 |= $20'],
    common='$1815/$183F: sound $8A wait; $1869: D294 := 0; D297 := D296; D293 |= $20 -> act-clear sequence $14AE (results $32F9, D298 += 1, D293 bit1 -> level load)')


def loader(r, a):
    z, act = a['descriptor']['zone'], a['descriptor']['act']
    o = Oracle(r)
    o.mem[0xD297], o.mem[0xD298] = z, act
    o.call(0x4E57)
    start = {hex(p): o.word(p) for p in (0xD2D6, 0xD2D8, 0xD511, 0xD514)}
    o.call(0x4FDC)
    header = {hex(p): o.word(p) for p in (0xD164, 0xD166, 0xD168, 0xD16A, 0xD280, 0xD282, 0xD27C, 0xD27E)}
    h = a['descriptor']['header']
    o.bank(2, h['layout_bank'])
    o.mem[0xC001:0xD002] = bytes([165]) * 4097
    o.cpu.hl = h['layout_cpu']; o.cpu.pc = 0x4DBE; o.cpu.set_breakpoint(0x4DFB)
    for _ in range(20):
        o.cpu.ticks_to_stop = 100000; o.cpu.run()
        if o.cpu.pc == 0x4DFB:
            break
    assert o.cpu.pc == 0x4DFB
    data = bytes(o.mem[0xC001:o.cpu.de])
    assert data == bytes(a['cells'][:a['runtime_cells']])
    return dict(start=start, header=header, cells_checked=len(data), sha256=L.sha256(data))


def zone_tables(r):
    """Every zone-indexed table the loaders consume, for zones 6..12 (raw ROM words/bytes)."""
    u = lambda o: int.from_bytes(r[o:o + 2], 'little')
    t = {}
    t['start_table_zone_ptr'] = {z: hex(u(0x4E98 + 2 * z)) for z in range(13)}
    t['header_zone_ptr'] = {z: hex(u(0x5082 + 2 * z)) for z in range(16)}
    t['effects_zone_ptr_2A9A'] = {z: hex(u(0x2A9A + 2 * z)) for z in range(13)}
    t['music_by_zone_act_18BA'] = {z: [r[0x18BA + z * 3 + a] for a in range(3)] for z in range(13)}
    t['palette_select_7F3C'] = {z: list(r[0x7F3C + 2 * z * 3:0x7F3C + 2 * z * 3 + 2]) for z in range(13)}
    t['object_list_ptr_1C8546'] = {z: hex(u(0x70546 + 2 * z)) for z in range(13)}
    return t


def graphics_sharing(r, acts):
    """For every art stream a stage loads: which ordinary acts (zones 0..6) load the identical ROM stream."""
    ordinary = {}
    for z in range(7):
        for a in range(3):
            art = L.art_entry(r, z, a)
            for s in [art['primary']] + art['supplemental']:
                ordinary.setdefault(s['stream_rom'], []).append(f'zone{z}_act{a}')
    out = {}
    for key, a in acts.items():
        art = a['descriptor']['art']
        out[key] = [dict(id=s['id'], stream_rom=s['stream_rom'], vram_destination=s['vram_destination'],
                         shared_with=sorted(set(ordinary.get(s['stream_rom'], [])))) for s in [art['primary']] + art['supplemental']]
    return out


def build(r):
    assert L.sha256(r) == L.ROM_SHA256
    acts = {k: L.build_act(r, k, v) for k, v in STAGES.items()}
    m = dict(format=1, rom_sha256=L.ROM_SHA256, research_base=BASE,
             evidence='decoded data, byte-verified assembly and controlled original loaders; runtime contracts remain separate',
             stage='SS-A1 foundation', indexing=dict(
                 stage_count=5, zones={k: v['zone'] for k, v in STAGES.items()}, order_rule=ENTRY['zone_select'],
                 completion_bits={k: v['completion_bit'] for k, v in STAGES.items()},
                 non_stage_zone_7='zone 7 has its own single-act record and one type $1F object; it is NOT selected by $187B (excluded from the five)',
                 acts_per_stage=1, act_records_shared='each stage zone points all three act slots at one 22-byte record'),
             entry=ENTRY, exit=EXIT, stages={}, surfaces={}, unresolved=[
                 'New art approval is pending James; no approval is inherited from other zones.'],
             validation_limits=['Approximate SMS harness; controlled boundary fixtures are not input-only playthroughs unless stated.'])
    census = dict(format=1, rom_sha256=L.ROM_SHA256, stages={}, types={})
    consumers, floor, right, left, ceiling = M.surface_consumers(r)
    for key, a in acts.items():
        d = a['descriptor']; h = d['header']; cells = a['cells'][:a['runtime_cells']]
        counts = Counter(cells)
        blocks = []
        for b in sorted(counts):
            hd = R.header(r, b)
            mp = L.block_mapping(r, h['block_mapping_rom'], b)
            s = hd['flags'] & 31
            blocks.append(dict(id=b, cells=counts[b], surface=s, headers=[R.header(r, b, p) for p in (0, 1)], mapping=mp))
            row = m['surfaces'].setdefault(str(s), dict(blocks=[], cells={}, floor_handler=floor[s]))
            if b not in row['blocks']:
                row['blocks'].append(b)
            row['cells'][key] = row['cells'].get(key, 0) + counts[b]
        m['stages'][key] = dict(
            descriptor=d, dimensions_cells=[a['width'], a['height']], dimensions_pixels=[a['width'] * 32, a['height'] * 32],
            layout=dict(encoded_cells=len(a['cells']), runtime_written_cells=a['runtime_cells'], runtime_sha256=L.sha256(bytes(cells)),
                        rows=[a['cells'][i:i + a['width']] for i in range(0, len(a['cells']), a['width'])]),
            blocks=blocks, rings=dict(terrain=a['terrain_rings'], object09=L.object_rings(a), tables=a['semantics']),
            graphics=dict(loads=a['vram_loads'], vram_sha256=L.sha256(a['vram']),
                          palettes={n: dict(index=d['palette'][n + '_index'], file=d['palette'][n + '_rom'],
                                            cram=list(r[d['palette'][n + '_rom']:d['palette'][n + '_rom'] + 16])) for n in ('background', 'sprite')}),
            mapping_check=A.mapping_check(r, h), original_loaders=loader(r, a))
        ptr = L.object_list_pointer(r, d['zone'], d['act'])
        rows, term = L.decode_object_list(r, ptr['list_rom'])
        for rec in rows:
            t = int(rec['type_id'], 16)
            rec.update(stage=key, original_creator=A.placement_creator(r, rec))
            row = census['types'].setdefault(rec['type_id'], dict(placements=0, stages={}, parameters={}, scripts=C.public_script(C.state_scripts(r, t))))
            row['placements'] += 1
            row['stages'][key] = row['stages'].get(key, 0) + 1
            row['parameters'][rec['parameter']] = row['parameters'].get(rec['parameter'], 0) + 1
        census['stages'][key] = dict(pointer=ptr, count=len(rows), terminator_file=term, records=rows,
                                     type_counts=dict(sorted(Counter(x['type_id'] for x in rows).items())))
    m['graphics_sharing'] = graphics_sharing(r, acts)
    m['zone_tables'] = zone_tables(r)
    m['surface_consumers'] = consumers
    return m, census, acts


def dumps(v):
    return json.dumps(v, indent=2) + '\n'


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('rom', type=Path); p.add_argument('--check', action='store_true')
    args = p.parse_args()
    m, c, _ = build(L.load_rom(args.rom)); OUT.mkdir(parents=True, exist_ok=True)
    for name, value in [('implementation-manifest.json', m), ('object-census.json', c)]:
        if args.check:
            assert (OUT / name).read_text(encoding='utf-8') == dumps(value), name
        else:
            (OUT / name).write_text(dumps(value), encoding='utf-8')
    print({k: (v['dimensions_cells'], len(v['rings']['terrain']), c['stages'][k]['count']) for k, v in m['stages'].items()})


if __name__ == '__main__':
    main()
