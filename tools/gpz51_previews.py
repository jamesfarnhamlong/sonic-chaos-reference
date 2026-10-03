"""Render corrected $51-only ROM approval sheets; approved siblings untouched."""
import hashlib
import json
from pathlib import Path
from PIL import Image,ImageDraw
from gpz_enemy_previews import BG,caption,cross,piece_image,composed

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/gpz51-correction'

def main():
    data=json.loads((OUT/'preview-input.json').read_text())
    palette=data['palette']['rgba'];boss=data['boss']
    frames={v['frame']:v for v in boss['images'] if not v['mirror']}
    terrain=Image.new('RGBA',(256,192));terrain.putdata([tuple(c) for line in data['terrain'] for c in line])
    foreground=Image.new('RGBA',(256,192));foreground.putdata([tuple(c) for line in data['foreground'] for c in line])
    def render(row, marks=False, canvas=None, offset=(1665,113)):
        im=terrain.copy() if canvas is None else canvas.copy()
        # Ascending slot order has first-sprite priority; preserve that for overlaps.
        for v in reversed(row['slots']):
            if v['frame'] not in frames:continue
            x,y=v['x']-offset[0],v['y']-offset[1]
            for p in reversed(frames[v['frame']]['pieces']):
                im.alpha_composite(piece_image(p,palette),(x+p['x']+1,y+p['y']+18))
        if canvas is None:im.alpha_composite(foreground)
        if marks:
            for v in row['slots']:
                if v['frame'] in frames:cross(im,v['x']-offset[0],v['y']-offset[1])
        return im
    raw=Image.new('RGBA',(768,60+((len(boss['raw_tiles'])+23)//24)*44),BG)
    caption(raw,'$51 raw VRAM tiles | palette $0D | dynamic selector $14 | NO pixel reversal')
    for n,t in enumerate(boss['raw_tiles']):
        x,y=(n%24)*32,48+(n//24)*44
        raw.alpha_composite(piece_image(t,palette).resize((24,24),Image.Resampling.NEAREST),(x,y))
        caption(raw,f'{t["tile"]:02X}',(x,y+25))
    raw.save(OUT/'51-raw-tiles.png')
    sheet=Image.new('RGBA',(768,52+3*230),BG)
    caption(sheet,'$51 canonical frames | pink = gameplay anchor | presentation (+1,+18)')
    for n,(f,row) in enumerate(frames.items()):
        x,y=(n%4)*192,52+(n//4)*230
        im=Image.new('RGBA',(128,112),(65,72,84));im.alpha_composite(composed(row,palette,True));cross(im,64,56)
        sheet.alpha_composite(im.resize((192,168),Image.Resampling.NEAREST),(x,y))
        role='head hit' if f==1 else 'head' if f==2 else 'ball' if f<10 else 'landing dust'
        caption(sheet,f'{f}: {role}',(x+4,y+168))
        # Raw mapping-ordered 8x16 SAT pieces below each composed frame.
        for j,p in enumerate(row['pieces']):
            sheet.alpha_composite(piece_image(p,palette).resize((16,32),Image.Resampling.NEAREST),(x+4+j*20,y+190))
        composed(row,palette).save(OUT/f'51-frame-{f:02d}.png')
    sheet.save(OUT/'51-composed-registration.png')
    samples=data['samples']
    # Context sequence: eleven original-scheduler snapshots, no guessed positions.
    seq=Image.new('RGBA',(1536,56+4*430),BG)
    caption(seq,'$51 ROM scheduler sequence | head above THREE balls | actual linked slots, including detached balls/dust')
    for n,row in enumerate(samples):
        x,y=(n%3)*512,56+(n//3)*430
        seq.alpha_composite(render(row).resize((512,384),Image.Resampling.NEAREST),(x,y+42))
        caption(seq,f'{n+1}. {row["label"]}',(x+8,y))
        caption(seq,f'tick {row["tick"]} | attached {row["attached_parameters"]}',(x+8,y+19))
        render(row).save(OUT/f'51-context-{row["tick"]:03d}.png')
    seq.save(OUT/'51-sequence-context.png')
    summary=Image.new('RGBA',(1536,56+2*430),BG)
    caption(summary,'$51 normal sequence | head + 3 -> head + 2 -> head + 1 -> head only -> regrow -> head + 3')
    for n,t in enumerate((232,357,471,601,670,704)):
        row=next(v for v in samples if v['tick']==t);x,y=(n%3)*512,56+(n//3)*430
        caption(summary,row['label'],(x+8,y))
        caption(summary,f'tick {t} | attached {row["attached_parameters"]}',(x+8,y+19))
        summary.alpha_composite(render(row).resize((512,384),Image.Resampling.NEAREST),(x,y+42))
    summary.save(OUT/'51-sequence-summary.png')
    # Unclipped rising-stack diagnostic exposes newly allocated balls below floor.
    reg=Image.new('RGBA',(960,640),BG)
    caption(reg,'Registration / regrowth | pink anchors; yellow floor | below-floor slots deliberately visible')
    for n,t in enumerate((232,602,630,704)):
        row=next(v for v in samples if v['tick']==t)
        stage=Image.new('RGBA',(160,260),(48,54,67))
        stage=render(row,True,stage,(1740,140))
        ImageDraw.Draw(stage).line((0,288-140,159,288-140),fill=(255,225,60))
        reg.alpha_composite(stage.resize((240,390),Image.Resampling.NEAREST),(n*240,70))
        caption(reg,f'tick {t}',(n*240+8,48))
        caption(reg,'frame / parameter / anchor',(n*240+8,470))
        for j,v in enumerate(row['slots']):
            if v['parameter'] not in (0,1,2,3) or v['state'] in (11,15,19,20):continue
            caption(reg,f'f{v["frame"]} p{v["parameter"]} ({v["x"]},{v["y"]})',(n*240+8,493+j*20))
    reg.save(OUT/'51-stack-registration.png')
    variants=Image.new('RGBA',(1024,470),BG)
    caption(variants,'ROM variants: mode2 FOUR balls (not default) | rightward throw uses same art, no bitmap flip')
    for n,(row,label) in enumerate(((data['mode2'],'Mode2, head + FOUR balls'),(data['right'],'Mode1, rightward bottom throw'))):
        caption(variants,label,(n*512+8,52))
        variants.alpha_composite(render(row).resize((512,384),Image.Resampling.NEAREST),(n*512,80))
    variants.save(OUT/'51-mode-direction.png')
    files=sorted(OUT.glob('*.png'))
    manifest=dict(approval='CORRECTED $51 APPROVED BY USER 2026-10-03',rom_sha256=data['rom_sha256'],
        generator='gpz51_composition.py + gpz51_previews.py',
        images=[dict(file=v.name,sha256=hashlib.sha256(v.read_bytes()).hexdigest(),size=list(Image.open(v).size)) for v in files],
        frame_candidates=[f'51-frame-{f:02d}.png' for f in frames],
        anchor=[64,56],canvas=[128,112],presentation=[1,18],
        excluded='Context/sequence/raw/registration sheets are review-only; no forced mirrors. No POC authorization.')
    (OUT/'png-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'{len(files)} corrected $51 PNGs:',OUT)

if __name__=='__main__':main()
