"""SS-A5 visual package: approval boards for NEW Special Stage compositions only (needs Pillow).

Pixels are written only to the ignored `build/ss-approval/`; the committed `data/rom-cache/special-stages/art-approval.json` records subjects, sources,
hashes, deduplication verdicts and the approval state (PENDING until James reviews the boards).  Object compositions use the exact original mapping records
(`mghz_object_census.frame_record`, asserted against the original SAT model) over the VRAM that the original loader produced in the stage; monitor icons,
results/HUD and effects are EMULATED ORIGINAL FRAME crops.  No redraw, no invented animation.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw
import level_package as L
import rom as R
import thz1_object_assets as G
import mghz_object_census as C
from ss_rig import SSRig, PAD
import ss_foundation as F
import ss_maps as SM
from ss_search import restore

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/ss-approval'
CACHE = ROOT / 'data/rom-cache/special-stages/art-approval.json'


def pal(r, index):
    return [tuple(c[:3]) for c in G.palette_rgba(r, index)]


def compose(frame_image, palette):
    """RGBA image of one composed frame (SAT piece order: earlier pieces on top) and its origin offset."""
    pieces = frame_image['pieces']
    xs = [p['x'] for p in pieces]; ys = [p['y'] for p in pieces]
    x0, y0 = min(xs), min(ys)
    w = max(p['x'] + 8 for p in pieces) - x0
    h = max(p['y'] + len(p['pixels']) for p in pieces) - y0
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = im.load()
    for p in reversed(pieces):
        for yy, row in enumerate(p['pixels']):
            for xx, c in enumerate(row):
                if c:
                    px[p['x'] - x0 + xx, p['y'] - y0 + yy] = palette[c] + (255,)
    return im, (-x0, -y0)


def digest(b):
    return hashlib.sha256(b).hexdigest()


def canvas(w, h, title):
    im = Image.new('RGBA', (w, h), (24, 24, 32, 255))
    ImageDraw.Draw(im).text((8, 6), title, fill='white')
    return im


def build(r, acts):
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = dict(format=1, rom_sha256=R.SHA256, research_base=F.BASE, approval='PENDING James; nothing here is approved or inherited', boards=[], dedup=[])
    # --- 1. maps (five) -------------------------------------------------------------------------------------------------------
    for n in range(1, 6):
        a = acts[f'ss{n}']
        im = SM.render_map(r, a)
        if im.size[0] > 4096:
            for i in range(im.size[0] // 4096):
                im.crop((i * 4096, 0, (i + 1) * 4096, im.size[1])).save(OUT / f'map-ss{n}-part{i + 1}.png')
        else:
            im.save(OUT / f'map-ss{n}.png')
        manifest['boards'].append(dict(id=f'map-ss{n}', kind='terrain map', stage=n, size=list(im.size), sha256=digest(im.tobytes()),
                                       palettes=[a['descriptor']['palette']['background_index'], a['descriptor']['palette']['sprite_index']]))
    # --- 2. terrain block sets per art family --------------------------------------------------------------------------------
    for fam, keys in (('outdoor', ['ss1', 'ss2', 'ss4']), ('interior', ['ss3', 'ss5'])):
        seen, tiles = set(), []
        for k in keys:
            a = acts[k]
            maps = L.block_pixel_maps(r, a['vram'], only=sorted(set(a['cells'][:a['runtime_cells']])), mapping_rom=a['descriptor']['header']['block_mapping_rom'])
            bg = pal(r, a['descriptor']['palette']['background_index']); sp = pal(r, a['descriptor']['palette']['sprite_index'])
            for b, pixels in maps.items():
                ident = (b, digest(json.dumps(pixels).encode()), tuple(bg), tuple(sp))
                if ident in seen:
                    continue
                seen.add(ident); tiles.append((k, b, pixels, bg, sp))
        im = canvas(12 * 76 + 12, ((len(tiles) + 11) // 12) * 88 + 34, f'Special Stage terrain blocks ({fam}); decoded tile attributes, static VRAM')
        d = ImageDraw.Draw(im)
        for i, (k, b, pixels, bg, sp) in enumerate(tiles):
            x, y = 6 + i % 12 * 76, 28 + i // 12 * 88
            t = Image.new('RGB', (32, 32))
            t.putdata([bg[0] if (c & 15) == 0 else (sp if c & 16 else bg)[c & 15] for row in pixels for c in row])
            im.paste(t.resize((64, 64), Image.Resampling.NEAREST), (x, y))
            d.text((x, y + 65), f'{k[2:]}:${b:02X}', fill='white')
        im.save(OUT / f'terrain-{fam}.png')
        manifest['boards'].append(dict(id=f'terrain-{fam}', kind='terrain blocks', stages=keys, unique_block_images=len(tiles)))
    # --- 3. objects from emulator VRAM -----------------------------------------------------------------------------------------
    rigs = {n: SSRig(r, n) for n in range(1, 6)}
    ref = {}
    # reference compositions already approved elsewhere (MGHZ1 type $2F, THZ1 $10/$26) for pixel-identity deduplication
    for key, zone, types in (('mghz1', 3, (0x2F,)), ('thz1', 0, (0x10, 0x26))):
        a = L.build_act(r, key, dict(zone=zone, act=0, name=key)) if key not in acts else acts[key]
        recs, _ = L.decode_object_list(r, a['descriptor']['objects']['list_rom'])
        for t in types:
            rec = next(x for x in recs if int(x['type_id'], 16) == t)
            b0, b1 = int(rec['aux0'], 16), int(rec['aux1'], 16)
            ref[t] = {fi: C.frame_record(r, t, fi, b0, b1, bytes(a['vram']), flips=(False,))['images'][0]['composed_index_sha256'] for fi in C.state_scripts(r, t)['frames']}
    subjects = {}
    census = json.loads((F.OUT / 'object-census.json').read_text(encoding='utf-8'))
    for st in range(1, 6):
        vram = bytes(rigs[st].s.vram)
        sp_index = acts[f'ss{st}']['descriptor']['palette']['sprite_index']
        for t in (0x31, 0x2F, 0x26):
            rec = next((x for x in census['stages'][f'ss{st}']['records'] if int(x['type_id'], 16) == t), None)
            if rec is None:
                continue
            b0, b1 = int(rec['aux0'], 16), int(rec['aux1'], 16)
            frames = [f for f in C.state_scripts(r, t)['frames'] if f]
            comp = {fi: C.frame_record(r, t, fi, b0, b1, vram, flips=(False,)) for fi in frames}
            hashes = {fi: c['images'][0]['composed_index_sha256'] for fi, c in comp.items()}
            identical = t in ref and all(ref[t].get(fi) == h for fi, h in hashes.items())
            manifest['dedup'].append(dict(type=t, stage=st, bases=[b0, b1], frame_hashes={str(k): v[:16] for k, v in hashes.items()}, pixel_identical_to_approved_zone_art=identical))
            if identical:
                continue
            subjects[(t, st)] = (comp, sp_index, (b0, b1))
    # board: new object compositions (one cell per (type, stage, frame))
    cells = [(t, st, fi, c) for (t, st), (comp, sp, bases) in sorted(subjects.items()) for fi, c in comp.items()]
    if cells:
        im = canvas(max(480, 6 * 150), ((len(cells) + 5) // 6) * 130 + 34, 'Special Stage objects not pixel-identical to approved art: exact mapping records over stage VRAM')
        d = ImageDraw.Draw(im)
        for i, (t, st, fi, c) in enumerate(cells):
            x, y = 8 + i % 6 * 150, 30 + i // 6 * 130
            sp_index = subjects[(t, st)][1]
            img, origin = compose(c['images'][0], pal(r, sp_index))
            im.alpha_composite(img.resize((img.size[0] * 3, img.size[1] * 3), Image.Resampling.NEAREST), (x, y))
            d.text((x, y + 100), f'type ${t:02X} SS{st} frame ${fi:02X} pal {sp_index}', fill='white')
        im.save(OUT / 'objects-new.png')
        manifest['boards'].append(dict(id='objects-new', kind='object compositions', cells=[dict(type=t, stage=st, frame=fi, sha256=c['images'][0]['composed_index_sha256'])
                                                                                             for t, st, fi, c in cells]))
    # --- 4. emulated original frames: monitors, goal ring in situ, HUD/results ---------------------------------------------
    def frame(g):
        rgb = g.s.render()[0]
        img = Image.new('RGB', (256, 192)); img.putdata([tuple(px) for row in rgb for px in row])
        return img

    mon_cells, ring_frames = [], []
    for st in range(1, 6):
        g = rigs[st]
        for rec in census['stages'][f'ss{st}']['records']:
            t_ = int(rec['type_id'], 16)
            if t_ == 0x10 and st in (1, 3, 5) and not any(c[0] == st for c in mon_cells):
                restore(g, g.e.base)
                g.s.pad = 0
                strip = []
                for k in range(24):
                    g.s.run_frame()
                    if k % 2 == 0:
                        slot = next((o for o in g.objs((0x10,)) if o['x'] == rec['world_x']), None)
                        if slot:
                            sx, sy = slot['x'] - g.s.u16(0xD174), slot['y'] - g.s.u16(0xD176)
                            box = (max(0, sx - 20), max(0, sy - 36), min(256, sx + 20), min(192, sy + 14))
                            if box[2] - box[0] >= 8 and box[3] - box[1] >= 8:
                                strip.append(frame(g).crop(box))
                if strip:
                    mon_cells.append((st, int(rec['parameter'], 16), strip))
            if t_ == 0x31:
                mx, my = rec['world_x'], rec['world_y']
                restore(g, g.e.base)
                g.begin(mx - 90, my - 40, cur=0x0E, f3=1, floor=False, rings=0)
                for _ in range(8):
                    g.s.pad = 0; g.s.run_frame()
                ring_frames.append((st, frame(g)))
    if mon_cells:
        im = canvas(12 * 90 + 16, len(mon_cells) * 130 + 36, 'Monitor icon animation by parameter, every 2nd frame (EMULATED ORIGINAL FRAME crops, 2x)')
        d = ImageDraw.Draw(im)
        for i, (st, par, strip) in enumerate(mon_cells):
            for k, c in enumerate(strip[:12]):
                im.paste(c.resize((c.size[0] * 2, c.size[1] * 2), Image.Resampling.NEAREST), (8 + k * 90, 28 + i * 130))
            d.text((8, 28 + i * 130 + 104), f'SS{st} monitor parameter {par}', fill='white')
        im.save(OUT / 'monitors-emulated.png')
        manifest['boards'].append(dict(id='monitors-emulated', kind='emulated crops', cells=[dict(stage=s_, parameter=p_, frames=len(c), sha256=digest(b''.join(x.tobytes() for x in c)))
                                                                                              for s_, p_, c in mon_cells]))
    if ring_frames:
        im = canvas(256 * 3 + 16, 192 * 2 + 40, 'Goal ring in situ, each stage (EMULATED ORIGINAL FRAMES, 1x)')
        d = ImageDraw.Draw(im)
        for i, (st, f) in enumerate(ring_frames):
            x, y = 8 + (i % 3) * 256, 28 + (i // 3) * 196
            im.paste(f, (x, y)); d.text((x + 4, y + 4), f'SS{st}', fill='yellow')
        im.save(OUT / 'goal-ring-in-situ.png')
        manifest['boards'].append(dict(id='goal-ring-in-situ', kind='emulated frames', cells=[dict(stage=s_, sha256=digest(f.tobytes())) for s_, f in ring_frames]))
    # results screens (success and failure) from the SS1 flows
    res = []
    for kind in ('success', 'death'):
        g = rigs[1]
        restore(g, g.e.base)
        if kind == 'success':
            g.begin(15248, 118, cur=0x0E, f3=1, floor=False, rings=0)
        else:
            g.begin(300, 130, cur=0x0E, f3=1, floor=False, rings=0)
        shots = []
        for f in range(1500):
            g.s.pad = 0; g.s.run_frame()
            if g.m[0xD297] == 0 and g.m[0xD293] == 0x60 and g.m[0xD500] == 0 and len(shots) < 2 and f % 60 == 0 and g.m[0xD2CD] == 0 and f > 250:
                shots.append(frame(g))
            if len(shots) == 2:
                break
        res.append((kind, shots))
    im = canvas(256 * 2 + 16, 192 * 2 + 40, 'Special Stage results screens (EMULATED ORIGINAL FRAMES): success row, failure row')
    for i, (kind, shots) in enumerate(res):
        for j, f in enumerate(shots):
            im.paste(f, (8 + j * 256, 28 + i * 196))
    im.save(OUT / 'results.png')
    manifest['boards'].append(dict(id='results', kind='emulated frames', cells=[dict(kind=k, frames=len(s_)) for k, s_ in res]))
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('rom', type=Path); p.add_argument('--no-cache', action='store_true'); a = p.parse_args()
    r = L.load_rom(a.rom)
    acts = {k: L.build_act(r, k, v) for k, v in F.STAGES.items()}
    manifest = build(r, acts)
    CACHE.write_text(json.dumps(manifest, indent=2) + chr(10), encoding='utf-8')
    print({k: (len(v) if isinstance(v, list) else v) for k, v in manifest.items()})


if __name__ == '__main__':
    main()
