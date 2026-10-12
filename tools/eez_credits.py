"""ROM-backed ending credits: ASCII/control stream, glyph descriptors and timing.

No ROM/pixel payload is emitted to the tracked cache. --trace also executes the
accepted controlled original boss-to-title path and writes local review PNGs.
"""
import argparse
import json
from pathlib import Path
import level_package as L
from oracle import Oracle
from tile_decompress import decompress_tile_stream, extract_command, _expand_sparse_tile
import mghz_object_census as C

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/rom-cache/eez'
LOCAL = ROOT / 'build/eez-credits'
BANK = 26
START = 0xB0F0

def offset(bank, cpu):
    return cpu if cpu < 0x8000 else bank * 0x4000 + cpu - 0x8000

def source(r, bank, lo, hi):
    a, b = offset(bank, lo), offset(bank, hi)
    return dict(bank=bank, cpu_start=lo, cpu_end_exclusive=hi,
                file_start=a, file_end_exclusive=b, sha256=L.sha256(r[a:b]))

def stream(r):
    p = START
    commands = []
    while True:
        a = r[offset(BANK, p)]
        if a in (0, 1, 2, 255):
            commands.append(dict(cpu=p, control=a))
            p += 1
            if a == 255:
                break
        else:
            lo = p
            while 32 <= r[offset(BANK, p)] < 127:
                p += 1
            text = r[offset(BANK, lo):offset(BANK, p)].decode('ascii')
            if len(text) != 11:
                raise ValueError(f'non-eleven-character row at {lo:04X}')
            commands.append(dict(cpu=lo, stored_ascii=text,
                                 displayed=text.replace('$', '\u2665'), length=11))
    return commands, p

def compressed(r, bank, cpu, destination):
    off = offset(bank, cpu)
    count = L.u16(r, off + 2)
    cp = off + L.u16(r, off + 4)
    dp = off + 6
    for i in range(count):
        cmd = extract_command(r, cp, i)
        if cmd == 1:
            dp += 32
        elif cmd in (2, 3):
            _, dp = _expand_sparse_tile(r, dp)
    end = max(dp, cp + (count + 3) // 4)
    decoded = decompress_tile_stream(r, off)
    return dict(source=source(r, bank, cpu, cpu + end - off),
                tile_count=count, vram_destination=destination,
                decoded_sha256=L.sha256(decoded), remap=False), decoded

def timing(r, pal=False, verify=True):
    """Independent scheduler model checked at EVERY call against original $1B88."""
    o = Oracle(r)
    emitted, latch, address = [], [None], [0]
    def output(port, value):
        if port & 255 == 0xBF:
            if latch[0] is None: latch[0] = value
            else:
                address[0] = ((value & 63) << 8) | latch[0]; latch[0] = None
        elif port & 255 == 0xBE:
            emitted.append((address[0], value)); address[0] = (address[0]+1) & 16383
    o.cpu.set_output_callback(output)
    m = o.mem
    m[0xD12D] = int(pal)
    o.word(0xD174, 0); o.word(0xD176, 0)
    o.call(0x1B5E)
    ptr, delay, heading, shifted, remaining, right, left = START, 0, 0, 0, 11, 31, 4
    lines, controls, writes = [], [], []
    current = None
    for tick in range(1, 20000):
        a = r[offset(BANK, ptr)]
        expected_writes = []
        if not delay and a not in (0, 1, 2, 255):
            dest = (0x3C00 if heading else 0x3D00) + right*2 - (2 if shifted else 0)
            glyph = L.u16(r, offset(BANK, 0xB070+(a-32)*2)) + (0x204 if heading else 0)
            for target, src in ((dest, glyph), (dest+4, 0xB4E5)):
                for row in range(3):
                    base = target + row*64
                    for j in range(4):
                        vaddr = (base & ~63) | ((base+j) & 63)
                        expected_writes.append((vaddr, r[offset(BANK, src)+row*4+j]))
        if delay:
            delay -= 1
        elif a == 0:
            controls.append(dict(call=tick, cpu=ptr, control=0))
            delay = 76 if pal else 32
            heading = 0
            ptr += 1
        elif a == 1:
            controls.append(dict(call=tick, cpu=ptr, control=1))
            heading = 1; ptr += 1
        elif a == 2:
            controls.append(dict(call=tick, cpu=ptr, control=2))
            shifted = 255; ptr += 1
        elif a == 255:
            controls.append(dict(call=tick, cpu=ptr, control=255))
        else:
            if current is None:
                current = dict(cpu=ptr, first_call=tick, heading=bool(heading),
                               x=32 if shifted else 40, y=128 if heading else 160)
            # Includes the redundant right-side glyph and blank eraser on every call.
            writes.append((tick, ptr, a, heading, shifted, right))
            right -= 1
            if right == left:
                right = 31; left += 2; ptr += 1; remaining -= 1
                if not remaining:
                    current['last_call'] = tick
                    lines.append(current); current = None
                    remaining, right, left, shifted = 11, 31, 4, 0
        if verify:
            emitted.clear()
            o.call(0x1B88)
            assert emitted == expected_writes, ('VDP writes', tick, emitted, expected_writes)
            expected = (ptr, delay, heading, shifted, remaining, right, left)
            actual = (o.word(0xD834), m[0xD838], m[0xD824], m[0xD82C],
                      m[0xD81A], m[0xD81E], m[0xD81F])
            assert actual == expected, (tick, actual, expected)
        if a == 255 and not delay:
            assert not verify or m[0xD3C1] == 255
            return dict(region='PAL' if pal else 'NTSC', total_calls=tick,
                        line_states=lines, controls=controls,
                        glyph_write_calls=len(writes),
                        glyph_write_trace_sha256=L.sha256(json.dumps(writes).encode()))
    raise AssertionError('credits did not finish')

def build(r):
    assert L.sha256(r) == L.ROM_SHA256
    commands, end = stream(r)
    chars = sorted(set(''.join(x.get('stored_ascii', '') for x in commands)))
    assets = {}
    decoded = {}
    for key, bank, cpu, dst in [('font', 26, 0x95DC, 0xC00),
                                ('full_scene', 9, 0xBD90, 0x200),
                                ('partial_scene', 9, 0xB600, 0x200),
                                ('end_card', 14, 0xB23A, 0x200),
                                ('try_again', 22, 0xB1E4, 0x1800)]:
        assets[key], decoded[key] = compressed(r, bank, cpu, dst)
    glyphs = {}
    for char in chars:
        entry = 0xB070 + (ord(char) - 32) * 2
        cpu = L.u16(r, offset(BANK, entry))
        variants = {}
        for label, delta in [('name', 0), ('heading', 0x204)]:
            p = cpu + delta
            words = [L.u16(r, offset(BANK, p) + j * 2) for j in range(6)]
            variants[label] = dict(source=source(r, BANK, p, p + 12),
                tiles=[dict(pattern=w & 511, hflip=bool(w & 512),
                            vflip=bool(w & 1024), palette=(w >> 11) & 1,
                            priority=bool(w & 4096)) for w in words])
        glyphs[char] = dict(codepoint=ord(char), displayed='\u2665' if char == '$' else char,
                           pointer_source=source(r, BANK, entry, entry + 2), variants=variants)
    vram = bytearray(0x4000)
    vram[0x200:0x200+len(decoded['end_card'])] = decoded['end_card']
    frames = [C.strip_pixels(C.frame_record(r, 21, i, 16, 0, vram)) for i in range(1, 5)]
    return dict(format=1, rom_sha256=L.ROM_SHA256,
        evidence='decoded data; source-traced renderer; every-call original routine oracle; controlled original-frame trace separately',
        stream_source=source(r, BANK, START, end), commands=commands,
        text_rows=sum('stored_ascii' in c for c in commands),
        nonblank_rows=sum(bool(c.get('stored_ascii', '').strip()) for c in commands),
        renderer_source=source(r, 0, 0x1B5E, 0x1C6F),
        audio_fade_source=source(r, 0, 0x18E1, 0x18ED),
        try_again_map_source=source(r, 22, 0xB6B0, 0xB6F0),
        presentation_source=source(r, 0, 0x18ED, 0x1B5E),
        palettes={str(i): dict(source=source(r, 14, 0xB64D+i*16, 0xB65D+i*16),
                              sms_colours=list(r[0x3B64D+i*16:0x3B65D+i*16]))
                  for i in (7, 0x25, 0x29, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F)},
        pointer_table_source=source(r, BANK, 0xB070, 0xB0F0),
        initial_scene_map=source(r, BANK, 0xB6F5, 0xB7D1),
        assets=assets, glyphs=glyphs, timings=[timing(r), timing(r, True)],
        end_card=dict(displayed='END.', representation='four original sprite frames, type $15 parameters 0..3; no literal text string',
                      script_source=source(r, 12, 0xA412, 0xA51E),
                      scripts=C.public_script(C.state_scripts(r, 21)),
                      initial_anchors=[dict(parameter=i, x=r[offset(12, 0xA51A)+i], y=0)
                                       for i in range(4)], frames=frames),
        routes=dict(full_sonic='credits, palette selectors $2A..$2F, END., title',
                    partial_sonic='no contributor credits or END.; partial scene then TRY AGAIN then title',
                    shared='common cleanup/fade/title return; no shared contributor pages between Sonic routes'),
        audio=dict(full=0x8D, partial=0x9A, partial_try_again=0x98,
                   end_card_sfx=[0xA6, 0xBA],
                   note='Additional events are traced; request $00 is never interpreted as silence.'))


def trace(r, flags):
    """Reuse accepted boundary-controlled fight; leave ending entirely unmodified."""
    import eez_boss_game as B
    from sez_surfaces_rig import ZoneGame
    from PIL import Image, ImageDraw
    route = 'full' if flags == 63 else 'partial'
    dest = LOCAL / route; dest.mkdir(parents=True, exist_ok=True)
    events, pictures = [], []
    active, start, calls = [False], [None], [0]
    class TracedGame(ZoneGame):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            q = self.s
            original_write = q._write
            def write(address, value):
                if active[0] and address == 0xDE04 and value:
                    events.append(dict(kind='audio_request', frame=q.frame-start[0],
                                       pc=q.cpu.pc, bank=q.slot[2], request=value))
                original_write(address, value)
            q.cpu.set_write_callback(write)
            def snapshot(label):
                if route == 'full' and label == '1c21':
                    font = decompress_tile_stream(r, offset(26, 0x95DC))
                    assert bytes(q.vram[0xC00:0xC00+len(font)]) == font
                rgb = q.render()[0]
                raw = bytes(c for row in rgb for px in row for c in px)
                name = f'{len(pictures):03d}-{label}.png'
                im = Image.new('RGB', (256, 192))
                im.putdata([tuple(px) for row in rgb for px in row]); im.save(dest/name)
                pictures.append(dict(file=name, frame=q.frame-start[0], calls=calls[0],
                                     rgb_sha256=L.sha256(raw), cram=list(q.cram),
                                     scroll=[q.reg[8], q.reg[9]], sat=q.sat(),
                                     actors=[dict(slot=b, type=q.mem[b], state=q.mem[b+1],
                                                  frame=q.mem[b+6], x=L.u16(q.mem, b+17), y=L.u16(q.mem, b+20))
                                             for b in range(0xD500, 0xDA00, 64)
                                             if q.mem[b] not in (0, 255)]))
            def hook(mm):
                pc = mm.cpu.pc
                if pc in (0x18FF, 0x1A42):
                    active[0] = True; start[0] = mm.frame
                if not active[0]: return
                if pc == 0x1B88:
                    calls[0] += 1; return
                if pc == 0x1AA3 and mm.frame-start[0] not in (128, 512, 1024): return
                if pc == 0x1C21 and mm.mem[0xD81A] != 1: return
                events.append(dict(kind='pc', pc=pc, frame=mm.frame-start[0],
                                   calls=calls[0], bank=mm.slot[2], hl=mm.cpu.hl,
                                   de=mm.cpu.de, bc=mm.cpu.bc, vdp_address=mm.addr))
                if pc in (0x1C21, 0x1BE2, 0x1A25, 0x3507): snapshot(f'{pc:04x}')
                if pc == 0x1AA3 and mm.frame-start[0] in (128, 512, 1024): snapshot('partial-scene')
                if pc == 0x1A16 and (mm.frame-start[0]) % 16 == 0: snapshot('end-animation')
                if pc in (0x1947, 0x1957, 0x1965, 0x1973, 0x1981, 0x198F, 0x1ABB): snapshot('scene')
            for pc in (0x18FF, 0x1A42, 0x1B88, 0x1BBE, 0x1BE2, 0x1A25, 0x1C21,
                       0x24C2, 0x1947, 0x1957, 0x1965, 0x1973, 0x1981,
                       0x198F, 0x34D4, 0x3507, 0x1ABB, 0x1374, 0x18E1, 0x1AA3):
                q.add_pc_hook(pc, hook)
            def end_loop(mm):
                if active[0] and (mm.frame-start[0]) % 16 == 0: snapshot('end-animation')
            q.add_pc_hook(0x1A16, end_loop)
    old = B.ZoneGame
    try:
        B.ZoneGame = TracedGame
        result = B.build(r, flags=flags)
    finally:
        B.ZoneGame = old
    # Local contact sheet contains every completed text row and END animation.
    board = Image.new('RGB', (1024, ((len(pictures)+3)//4)*216))
    draw = ImageDraw.Draw(board)
    for i, p in enumerate(pictures):
        x, y = i % 4 * 256, i // 4 * 216
        board.paste(Image.open(dest/p['file']), (x, y))
        draw.text((x, y+192), f"{p['file']} f{p['frame']}", fill='white')
    board.save(dest/'board.png')
    return dict(rom_sha256=L.ROM_SHA256, route=route, evidence=B.__doc__,
                events=events, pictures=pictures, terminal_trace=result['terminal_trace'],
                returned_to_title=result['returned_to_title'])


def dumps(v): return json.dumps(v, indent=2, ensure_ascii=False) + '\n'

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom', type=Path)
    p.add_argument('--check', action='store_true')
    p.add_argument('--trace', action='store_true')
    a = p.parse_args(); r = L.load_rom(a.rom)
    outputs = {'ending-credits.json': build(r)}
    if a.trace:
        outputs.update({f'ending-credits-trace-{label}.json': trace(r, flags)
                        for label, flags in [('full', 63), ('partial', 0)]})
    for name, value in outputs.items():
        target = OUT/name; rendered = dumps(value)
        if a.check:
            assert target.read_text(encoding='utf-8') == rendered, name
        else: target.write_text(rendered, encoding='utf-8')
    print({name: L.sha256(dumps(v).encode()) for name, v in outputs.items()})

if __name__ == '__main__': main()
