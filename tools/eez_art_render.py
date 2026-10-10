"""Render final-zone review input with bundled Pillow Python."""
import json
from pathlib import Path
from PIL import Image,ImageDraw
from aqz_art_previews import indexed,canvas
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/eez-approval'

def main():
    d=json.loads((OUT/'preview-input.json').read_text())
    seen=set()
    unique=[]
    for a in d['acts'].values():
        for b,px in a['blocks'].items():
            identity=(b,json.dumps(px))
            if identity in seen:continue
            seen.add(identity);unique.append((b,px,a))
    im=canvas(912,((len(unique)+11)//12)*88+32,'Zone5 terrain; decoded tile attributes')
    draw=ImageDraw.Draw(im)
    for i,(b,px,a) in enumerate(unique):
        x,y=i%12*76,i//12*88+32
        im.alpha_composite(indexed(px,a['background'],a['sprite']).resize((64,64),Image.Resampling.NEAREST),(x,y))
        draw.text((x,y+65),f'${int(b):02X}',fill='white')
    im.save(OUT/'terrain.png')
    for key,s in d['subjects'].items():
        im=canvas(max(320,len(s['frames'])*144),184,s['label']);draw=ImageDraw.Draw(im)
        for i,f in enumerate(s['frames']):
            x,y=i*144+64,88
            for p in reversed(f['images'][0]['pieces']):
                px=Image.new('RGBA',(8,len(p['pixels'])))
                px.putdata([tuple(s['palette'][c]) if c else (0,0,0,0) for row in p['pixels'] for c in row])
                im.alpha_composite(px,(x+p['x'],y+p['y']))
            draw.line((x-4,y,x+4,y),fill='cyan');draw.line((x,y-4,x,y+4),fill='cyan')
            draw.text((i*144,150),f'frame ${f["frame"]:02X}',fill='white')
        im.save(OUT/f'object-{key}.png')
    for eid,variants in d['animated'].items():
        entries=[(v,b,px) for v in variants for b,px in v['blocks'].items()]
        im=canvas(912,((len(entries)+11)//12)*88+32,f'Effect {eid}; original routine states')
        draw=ImageDraw.Draw(im)
        for i,(v,b,px) in enumerate(entries):
            x,y=i%12*76,i//12*88+32
            im.alpha_composite(indexed(px,v['background'],v['sprite']).resize((64,64),Image.Resampling.NEAREST),(x,y))
            draw.text((x,y+65),f'{v["update"]}: ${int(b):02X}',fill='white')
        im.save(OUT/f'effect-{eid}.png')
    for path in OUT.glob('ending-flags*-delay0-angleNone-char*.json'):
        frames=json.loads(path.read_text());im=canvas(1040,((len(frames)+1)//2)*420+32,'Original ending scene samples; approximate harness raster')
        draw=ImageDraw.Draw(im)
        for i,f in enumerate(frames):
            px=Image.new('RGB',(256,192));px.putdata([tuple(c) for row in f['rgb'] for c in row])
            x,y=(i%2)*520,(i//2)*420+32
            im.paste(px.resize((512,384),Image.Resampling.NEAREST),(x,y))
            draw.text((x,y+386),f'elapsed {f["meta"]["elapsed"]}; player {f["meta"]["player"]}',fill='white')
        im.save(OUT/(path.stem+'.png'))
    print(f'Rendered terrain, {len(d["subjects"])} numeric compositions and original effect states; pending review')

if __name__=='__main__':main()
