"""GPZ alternate loop: decoded gates and deterministic original-routine fixtures.

No POC code, replacement physics or modified ROM instructions are executed.
The Z80 oracle supplies RAM/layouts, a return stack and controller RAM explicitly.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import isometric_platform as I
from rom import load, header, s16, SHA256

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'data/rom-cache/gpz-loop-route.json'


def invoke(o, address, watches=(), nested=False):
    """Real instructions, with breakpoints only; two returns model abandoned caller."""
    c, m = o.cpu, o.mem
    hit = []
    terminal = (0x0100, 0x0101) if nested else (0x0100,)
    for p in (*terminal, *watches):
        c.set_breakpoint(p)
    c.pc, c.sp = address, 0xDFE0
    o.word(c.sp, terminal[-1])
    if nested:
        o.word(c.sp + 2, terminal[0])
    for _ in range(1000):
        c.ticks_to_stop = 100000
        c.run()
        if c.pc in terminal:
            for p in (*terminal, *watches):
                c.clear_breakpoint(p)
            c.set_breakpoint(o.RETURN)
            return {'calls': hit, 'return': c.pc}
        if c.pc in watches:
            p = c.pc
            hit.append(p)
            c.clear_breakpoint(p)
            c.ticks_to_stop = 1
            c.run()
            c.set_breakpoint(p)
    raise RuntimeError(f'original routine failed to return at {c.pc:04X}')


def record(lab):
    m, o = lab.m, lab.o
    return dict(current=m[0xD501], requested=m[0xD502], x=o.word(0xD511),
                y=o.word(0xD514), vx=s16(o.word(0xD516)), vy=s16(o.word(0xD518)),
                plane=m[0xD525], flags=m[0xD503], floor=bool(m[0xD522] & 2),
                progress_16_8=m[0xD39D] | m[0xD39E] << 8 | m[0xD39F] << 16,
                origin=[o.word(0xD53A), o.word(0xD53C)],
                previous_block=m[0xD36B], previous_surface=m[0xD36C])


def gates(rom):
    out = []
    for act in ('gpz1', 'gpz2', 'gpz3'):
        d = I.act_data(rom, act)
        for i, b in enumerate(d['cells'][:4095]):
            if b == 0x57:
                assert d['cells'][i + 1] == 0x52
                x, y = i % d['width'], i // d['width']
                out.append({'act': act, 'previous_cell': [x, y],
                            'previous_block': 0x57, 'gate_cell': [x + 1, y],
                            'gate_block': 0x52, 'gate_world': [(x + 1)*32, y*32],
                            'map_width': d['width'], 'layout_index': i+1})
    return out


def entry(rom, gate, vx=1024, attack=False):
    lab = I.TerrainLab(rom, gate['act'])
    o, m = lab.o, lab.m
    # Initialize a genuine walking script before the synthetic floor boundary.
    o.bank(2, 12)
    m[0xD12B] = 12
    o.call(0x64FA)
    m[0xD36B] = 0x57
    lab.base = bytes(m[0xC000:0xE000])
    x, y = gate['gate_world']
    before = {'x': x+2, 'y': y+1, 'vx': vx, 'vy': 1792,
              'current': 5, 'requested': 5, 'plane': 0,
              'previous_block': 0x57, 'previous_surface': 0x90, 'floor': True}
    lab.run(x+2, y+1, vx=vx, vy=1792, prev=0x90, state=5,
            floor=True, attack=attack)
    assert m[0xD502] == 0x13
    return lab, before, record(lab)


def update(lab, pad=0, pressed=0):
    o, m = lab.o, lab.m
    o.bank(2, 12)
    m[0xD12B], m[0xD137], m[0xD147] = 12, pad, pressed
    invoke(o, 0x64FA)
    return invoke(o, 0x5E91, (0x690B, 0x7666, 0x3CFC, 0x4680))


def traversal(rom, gate, vx=1024, pad=0, attack=False, pressed=0):
    lab, before, entered = entry(rom, gate, vx, attack)
    rows = []
    for frame in range(1, 400):
        events = update(lab, pad, pressed)
        rows.append({'update': frame, **record(lab), 'routine_calls': events['calls']})
        if lab.m[0xD502] != 0x13:
            break
    else:
        raise AssertionError('route did not exit')
    # A camera RAM reference keeps the next ordinary update in the SMS viewport;
    # no camera update is included in this isolated player-routine fixture.
    lab.o.word(0xD174, max(0, lab.o.word(0xD511)-104))
    events = update(lab, pad, pressed)
    restored = {**record(lab), 'routine_calls': events['calls']}
    before.update(held_input=pad, pressed_input=pressed, attack=attack)
    return {'gate': gate, 'input': before, 'entry': entered, 'updates': rows,
            'ordinary_update_after_exit': restored,
            'first_plane1_update': next((r['update'] for r in rows if r['plane']), None)}


def contact_matrix(rom):
    lab = I.TerrainLab(rom, 'gpz3')
    out = []
    for current in (0x51, 0x52, 0x57):
        for prev in (0, 0x51, 0x52, 0x57):
            for plane in (0, 1):
                for floor in (False, True):
                    for vx in (-1024, 0, 1024):
                        for state in (1, 5, 9, 0x0A):
                            lab.m[0xC000:0xE000] = lab.base
                            m, o = lab.m, lab.o
                            o.position(770, 194)
                            o.word(0xD516, vx)
                            m[0xD501] = m[0xD502] = state
                            m[0xD525], m[0xD522] = plane, 2 if floor else 0
                            m[0xD36B], m[0xD497] = current, prev
                            got = invoke(o, 0x6C82, nested=True)
                            out.append({'current_block': current, 'previous_block': prev,
                                        'plane': plane, 'floor': floor, 'vx': vx,
                                        'state': state, 'requested': m[0xD502],
                                        'after': record(lab), 'return': got['return']})
    return out


def progress_boundaries(rom):
    out=[]
    for progress in (143*256,144*256-11,144*256-10,144*256,415*256,416*256):
        for vx in (0,9,10,11):
            lab, _, _ = entry(rom,gates(rom)[-1],vx)
            m,o=lab.m,lab.o
            m[0xD501]=0x13
            m[0xD39D],m[0xD39E],m[0xD39F]=progress&255,(progress>>8)&255,progress>>16
            events=invoke(o,0x3CFC,watches=(0x4680,))
            out.append({'progress_before_16_8':progress,'vx_before':vx,
                        'after':record(lab),'routine_calls':events['calls']})
    return out


def build(rom):
    gs = gates(rom)
    rows = [traversal(rom, g) for g in gs]
    controls = [traversal(rom, gs[-1], vx, pad, attack)
                for vx, pad, attack in ((0, 0, False), (10, 0, False),
                    (853, 0, False), (854, 0, False), (1024, 4, False),
                    (1024, 8, False), (1024, 16, False), (1024, 0, True))]
    controls.append(traversal(rom, gs[-1], pressed=0x30))
    profiles = [{**header(rom, b, p)} for b in (0x57, 0x52) for p in (0, 1)]
    # Decoded profile data is already canonical in shared research caches.
    routines = [(0x6C82,0x6CE5), (0x3C1B,0x3EFD), (0x301AE,0x301C6),
                (0x34DDC,0x35140), (0x35140,0x35484)]
    return {'rom_sha256': SHA256, 'evidence': ['decoded data', 'source-traced behavior',
            'controlled routine result'], 'scope': 'GPZ alternate loop only; isolated player/terrain routines',
            'gates': gs, 'profiles': profiles,
            'routine_sha256': {f'{s:05X}..{e:05X}':hashlib.sha256(rom[s:e]).hexdigest() for s,e in routines},
            'contact_matrix': contact_matrix(rom), 'traversal_fixtures': rows,
            'control_fixtures': controls, 'progress_boundary_fixtures':progress_boundaries(rom),
            'limits': 'No original-game rendered observation or full interrupt/object/camera schedule; deterministic RAM-controlled original routines.'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('rom', type=Path)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    text = json.dumps(build(load(args.rom)), indent=2) + '\n'
    if args.check:
        assert OUTPUT.read_text() == text, 'cache differs; regenerate'
    else:
        OUTPUT.write_text(text)
    print('GPZ loop: four complete original-routine routes, 576 entry controls, nine traversal controls')


if __name__ == '__main__':
    main()
