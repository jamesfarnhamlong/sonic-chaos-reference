"""Static SMS M1 census. No emulator execution or pixel/audio payload output.

python tools/m1_census.py ROM --poc PATH [--check]
Uses existing mapping/script decoders; records hashes, geometry and provenance.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
import u5a_opening as O
import thz1_object_assets as A
import g2e_score as G
import level_package as L
import tile_decompress as TD

ROOT = Path(__file__).resolve().parents[1]
POC_SHA = '7476affc6ed7626dabf69b446cdab0c9c3d7492e'

def digest(b):
    return hashlib.sha256(b).hexdigest()

def build(rom, poc):
    O.check_rom(rom)
    head = subprocess.check_output(['git', '-C', str(poc), 'rev-parse', 'HEAD'], text=True).strip()
    if head != POC_SHA:
        raise ValueError('POC must be the exact accepted Q3 commit')
    pointers = A.mapping_frame_pointers(rom, A.object_mapping(rom, 2)['mapping_cpu'], 128)
    # Palette indices, never pixel data, are retained by the existing metadata decoder.
    frames = O.dynamic_mapping_frames(rom, 2, range(1, len(pointers)), A.palette_rgba(rom, 7))
    frames['frames']['0'] = {'piece_count': 0, 'mapping_frame_cpu': f'0x{pointers[0]:04X}', 'role': 'blank mapping; no pixel canvas'}
    for f in frames['frames'].values():
        if 'rgba_sha256_opening_sprite_palette' in f:
            f['rgba_sha256_palette7'] = f.pop('rgba_sha256_opening_sprite_palette')
    palettes = {}
    for record in (7, 41):
        rgba = A.palette_rgba(rom, record)
        palettes[str(record)] = digest(bytes(v for c in rgba for v in c))
    states = {f'{i:02X}': O.script_ops(rom, 0x89BB, i) for i in range(0x36)}
    files = []
    for p in sorted((poc / 'sprites').glob('*tails*/*.yy')):
        d = json.loads(re.sub(r',\s*([}\]])', r'\1', p.read_text(encoding='utf-8-sig')))
        files.append(dict(resource=d['name'], metadata_path=p.relative_to(poc).as_posix(),
                          width=d.get('width'), height=d.get('height'), frames=len(d.get('frames', [])),
                          origin=[d.get('sequence', {}).get('xorigin'), d.get('sequence', {}).get('yorigin')],
                          metadata_sha256=digest(p.read_bytes()),
                          provenance=('authenticated imported opening/Continue resource' if d['name'].startswith(('SPR_chaos_continue_tails_', 'SPR_chaos_opening_tails_')) else 'inherited; authenticity not established by name')))
    owners = []
    for p in sorted((poc / 'scripts').glob('*/*.gml')):
        txt = p.read_text(encoding='utf-8-sig')
        refs = sorted(set(re.findall(r'\bSPR_(?:chaos_\w*tails\w*|tails_\w+)\b', txt)))
        if refs:
            owners.append(dict(path=p.relative_to(poc).as_posix(), references=refs))
    ranges = [(0, 0x3713, 0x3759), (0, 0x473C, 0x4775), (0, 0x3EFD, 0x3FC8),
              (12, 0x8C6F, 0x8C82), (12, 0x8CB4, 0x8CEC), (12, 0x8CFC, 0x8D36),
              (0, 0x3065, 0x30E0), (0, 0x3522, 0x3595), (0, 0x0719, 0x0796),
              (0, 0x2F49, 0x2F77), (0, 0x798D, 0x79CB), (0, 0x4ADF, 0x4B02)]
    code = []
    for bank, start, end in ranges:
        offset = start if start < 0x8000 else bank * 0x4000 + start - 0x8000
        code.append(dict(bank=bank, start=f'{start:04X}', end_exclusive=f'{end:04X}',
                         sha256=digest(rom[offset:offset+end-start]),
                         instructions=G.disasm(rom, bank, start, end)))
    stage_palettes = []
    for z in range(6):
        for a in range(3):
            p = L.palette_selection(rom, z, a)
            stage_palettes.append(dict(zone=z, act=a, sprite_record=p['sprite_index'],
                                       palette_sha256=digest(rom[p['sprite_rom']:p['sprite_rom']+16])))
    streams = []
    for label, bank, cpu in [('title', 27, 0x9E00), ('character_choice', 19, 0x8000)]:
        offset = bank * 0x4000 + cpu - 0x8000
        decoded = TD.decompress_tile_stream(rom, offset)
        streams.append(dict(role=label, bank=bank, cpu=f'{cpu:04X}', rom_offset=offset,
                            decoded_tiles=len(decoded)//32, decoded_sha256=digest(decoded)))
    return dict(schema_version=1, evidence='new static private-ROM decode; no new ROM execution or Windows test',
                rom_sha256=O.ROM_SHA256, poc_commit=POC_SHA, tails_mapping=frames,
                palette_rgba_sha256=palettes, tails_state_table='0C:89BB', tails_states=states,
                poc_resources=files, poc_reference_owners=owners,
                code_contracts=code, stage_palettes=stage_palettes, frontend_streams=streams,
                title=O.title_routine(rom), attract=O.attract_table(rom),
                limitations=['Static table entries do not prove natural reachability.',
                             'Script FF08 alternatives and selector-generated frames require callback interpretation.',
                             'All 89 mappings decoded; not all are reachable gameplay poses.',
                             'Palette 7 is Continue; palette 41 is opening. Stage palette variation needs separate binding.'])

def main():
    a = argparse.ArgumentParser()
    a.add_argument('rom'); a.add_argument('--poc', required=True); a.add_argument('--check', action='store_true')
    ns = a.parse_args()
    result = build(Path(ns.rom).read_bytes(), Path(ns.poc))
    path = ROOT / 'data/m1/tails-asset-census.json'
    output = json.dumps(result, indent=2, ensure_ascii=False) + '\n'
    if ns.check:
        assert path.read_text(encoding='utf-8') == output, 'census differs'
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(output, encoding='utf-8')
    print(f"M1 static census: {len(result['tails_mapping']['frames'])} mappings, {len(result['tails_states'])} states, {len(result['poc_resources'])} POC resources")

if __name__ == '__main__':
    main()
