"""Audit all normal-act block pointers against original ROM render consumers."""
import argparse
import json
from pathlib import Path

import level_package as L
from oracle import Oracle

OUTPUT = L.ROOT / 'data/rom-cache/gpz/block-mapping-audit.json'
ZONES = ('thz', 'gpz', 'sez', 'mghz', 'apz', 'eez')


def original_pointer(o, table_cpu, block, vertical=False):
    """Execute original pointer lookup; stop before render-row selection."""
    o.word(0xD164, table_cpu)
    if vertical:
        start, stop = 0x53DF, 0x53E9
        o.cpu.de = block
    else:
        start, stop = 0x5316, 0x5323
        o.mem[0xD900] = block
        o.cpu.hl = 0xD900
    o.cpu.set_breakpoint(stop)
    o.cpu.pc = start
    for _ in range(20):
        o.cpu.ticks_to_stop = 10000
        o.cpu.run()
        if o.cpu.pc == stop:
            break
    o.cpu.clear_breakpoint(stop)
    if o.cpu.pc != stop:
        raise AssertionError(f'pointer consumer stopped at {o.cpu.pc:04X}')
    return o.cpu.de


def build(r):
    out = {'rom_sha256': L.sha256(r),
           'formula': 'bank*0x4000 + raw_pointer_word - 0x8000; table offset only indexes the pointer word',
           'consumers': {name: {'rom': a, 'length': b-a, 'sha256': L.sha256(r[a:b])}
                         for name, a, b in (('header_loader', 0x4FDC, 0x5038),
                                            ('mapper', 0x1C6F, 0x1C76),
                                            ('horizontal_pointer', 0x5316, 0x5323),
                                            ('vertical_pointer', 0x53DF, 0x53E9))},
           'acts': {}, 'gpz_fixtures': {}}
    o = Oracle(r)
    for zone, name in enumerate(ZONES):
        for act in range(3):
            h = L.act_header(r, zone, act)
            o.mem[0xD297], o.mem[0xD298] = zone, act
            o.call(0x4FDC)
            if (o.mem[0xD162], o.word(0xD164)) != (h['block_mapping_bank'], h['block_mapping_cpu']):
                raise AssertionError((zone, act, 'header loader'))
            o.cpu.a = o.mem[0xD162]
            o.call(0x1C6F)
            pointers, attrs = [], bytearray()
            for block in range(256):
                m = L.block_mapping(r, h['block_mapping_rom'], block)
                for vertical in (False, True):
                    cpu = original_pointer(o, h['block_mapping_cpu'], block, vertical)
                    if cpu != m['cpu']:
                        raise AssertionError((zone, act, block, cpu, m))
                    if bytes(o.mem[cpu:cpu+32]) != r[m['rom']:m['rom']+32]:
                        raise AssertionError((zone, act, block, 'bank conversion'))
                pointers.append(m['rom'])
                attrs.extend(r[m['rom']:m['rom']+32])
            out['acts'][f'{name}{act+1}'] = {
                'bank': h['block_mapping_bank'], 'bank_base_rom': h['block_mapping_bank']*0x4000,
                'table_cpu': h['block_mapping_cpu'], 'table_rom': h['block_mapping_rom'],
                'old_address_error': h['block_mapping_rom'] % 0x4000,
                'original_consumer_checks': 512,
                'resolved_offsets_sha256': L.sha256(b''.join(p.to_bytes(4, 'little') for p in pointers)),
                'mapping_attributes_sha256': L.sha256(attrs)}
    vram, _ = L.build_vram(r, L.art_entry(r, 1, 0))
    chosen = (0, 0x3C, *range(0x8C, 0x98))
    pixels = L.block_pixel_maps(r, vram, only=chosen, mapping_rom=0x45640)
    for b in chosen:
        m = L.block_mapping(r, 0x45640, b)
        old = m['rom'] + 0x1640
        flat = bytes(v for row in pixels[b] for v in row)
        out['gpz_fixtures'][L.hx(b, 2)] = {
            'raw_pointer_word': m['cpu'], 'pointer_entry_rom': m['pointer_entry_rom'],
            'bank': 0x11, 'cpu': m['cpu'], 'rom': m['rom'], 'old_wrong_rom': old,
            'old_attributes_all_ffff': r[old:old+32] == b'\xff'*32,
            'mapping_sha256': L.sha256(r[m['rom']:m['rom']+32]),
            'palette_index_sha256': L.sha256(flat), 'nonzero_pixels': sum(bool(v) for v in flat)}
    return out


def dumps(value):
    return json.dumps(value, indent=2) + '\n'


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('rom', type=Path)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    s = dumps(build(L.load_rom(args.rom)))
    if args.check:
        if OUTPUT.read_text(encoding='utf-8') != s:
            raise SystemExit('block mapping audit cache differs')
    else:
        OUTPUT.write_text(s, encoding='utf-8')
    print('Verified 18 acts x 256 blocks x 2 original consumers (9216 checks).')
