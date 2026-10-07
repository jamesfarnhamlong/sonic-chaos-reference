"""Render canonical AQZ review PNGs from ignored preview input (Pillow only)."""
import hashlib
import json
from pathlib import Path
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/aqz-approval'

def indexed(rows,bg,sp=None):
    im=Image.new('RGBA',(len(rows[0]),len(rows)))
    im.putdata([tuple((sp if c&16 and sp else bg)[c&15]) if c&15 else tuple(bg[0][:3])+ (255,) for row in rows for c in row])
    return im

def canvas(w,h,title):
    im=Image.new('RGBA',(w,h),(24,28,36,255));ImageDraw.Draw(im).text((8,8),title+' | PENDING JAMES REVIEW',fill='white');return im

def main():
    d=json.loads((OUT/'preview-input.json').read_text(encoding='utf-8'))
    for k,a in d['acts'].items():
        bg,sp=a['background'],a['sprite'];blocks={int(b):indexed(px,bg,sp) for b,px in a['blocks'].items()}
        im=canvas(a['width']*32,a['height']*32+24,f'{k.upper()} decoded map; unloaded final cell blank; raster effects omitted')
        for i,b in enumerate(a['cells'][:a['runtime_cells']]):im.alpha_composite(blocks[b],((i%a['width'])*32,(i//a['width'])*32+24))
        im.save(OUT/f'{k}-map.png')
        ids=sorted(blocks);sheet=canvas(12*76,((len(ids)+11)//12)*88+32,k.upper()+' blocks; palette/flip/priority attributes retained in cache')
        draw=ImageDraw.Draw(sheet)
        for n,b in enumerate(ids):
            x,y=(n%12)*76,(n//12)*88+32;sheet.alpha_composite(blocks[b].resize((64,64),Image.Resampling.NEAREST),(x,y));draw.text((x,y+65),f'${b:02X}',fill='white')
        sheet.save(OUT/f'{k}-blocks.png')
        if 'underwater_palettes' in a:
            pal=a['underwater_palettes'];under=canvas(12*76,((len(ids)+11)//12)*88+32,k.upper()+' underwater palette48/49 variants; raster timing omitted')
            drawu=ImageDraw.Draw(under)
            for n,b in enumerate(ids):
                x,y=n%12*76,n//12*88+32
                under.alpha_composite(indexed(a['blocks'][str(b)],pal['background'],pal['sprite']).resize((64,64),Image.Resampling.NEAREST),(x,y));drawu.text((x,y+65),f'${b:02X}',fill='white')
            under.save(OUT/f'{k}-underwater-blocks.png')
        crop=im.crop((a['camera'][0],a['camera'][1]+24,a['camera'][0]+256,a['camera'][1]+248));crop.resize((768,672),Image.Resampling.NEAREST).save(OUT/f'{k}-start.png')
    for key,s in d['subjects'].items():
        frames=s['frames'];sheet=canvas(8*144,((len(frames)*2+7)//8)*144+40,s['label']);draw=ImageDraw.Draw(sheet)
        for n,f in enumerate(frames):
            for j,img in enumerate(f['images']):
                q=n*2+j;x,y=q%8*144,q//8*144+40
                for p in reversed(img['pieces']):
                    rows=p['pixels'];piece=Image.new('RGBA',(8,len(rows)));piece.putdata([tuple(s['palette'][c]) if c else (0,0,0,0) for row in rows for c in row])
                    sheet.alpha_composite(piece,(x+64+p['x'],y+56+p['y']))
                draw.line((x+60,y+56,x+68,y+56),fill='cyan');draw.line((x+64,y+52,x+64,y+60),fill='cyan')
                draw.text((x,y+120),f'f{f["frame"]:02X} bit4={int(img["mirror"])}',fill='white')
        sheet.save(OUT/f'object-{key}.png')
    a=d['acts']['aqz1']
    for name,variants in d['animated'].items():
        height=sum(40+((len(v['tiles'])+15)//16)*40+((len(v['blocks'])+11)//12)*72 for v in variants)+32
        sheet=canvas(960,height,f'AQZ {name}: original VRAM writes');draw=ImageDraw.Draw(sheet);y=32
        for i,v in enumerate(variants):
            draw.text((8,y),f'frame{i} source ${v["copy"]["source_cpu"]:04X} -> VRAM ${v["copy"]["vram"]:04X}',fill='white');y+=24
            for n,(t,px) in enumerate(v['tiles'].items()):sheet.alpha_composite(indexed(px,a['background'],a['sprite']).resize((32,32),Image.Resampling.NEAREST),(n%16*44,y+n//16*40))
            y+=((len(v['tiles'])+15)//16)*40
            for n,(b,px) in enumerate(v['blocks'].items()):sheet.alpha_composite(indexed(px,a['background'],a['sprite']).resize((64,64),Image.Resampling.NEAREST),(n%12*76,y+n//12*72))
            y+=((len(v['blocks'])+11)//12)*72+16
        sheet.save(OUT/f'animated-{name}.png')
    rows={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob('*.png'))}
    index=['# AQZ A1 visual review','', 'Approved by James 2026-10-07. All images are decoded from the verified Europe v1.2 ROM.',
        'Forced bit4 mirrors are diagnostics; approve canonical compositions only. Static maps omit water raster timing.', '',
        'Review terrain, animation, new objects, palette variants and boss/children. Report any composition that needs correction.', '']
    index += [f'- [{name}]({(OUT/name).as_posix()})' for name in rows]
    (OUT/'REVIEW.md').write_text('\n'.join(index)+'\n',encoding='utf-8')
    (OUT/'boards-sha256.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8');print('Rendered',len(rows),'boards')

if __name__=='__main__':main()
