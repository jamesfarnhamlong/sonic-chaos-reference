"""Render ignored ROM approval input to labelled PNG sheets (Python + Pillow)."""
import argparse,json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/gpz-enemy-approval'
FONT=ImageFont.load_default(size=14)
BG=(38,45,56,255)

def caption(im,text,xy=(8,8)):
    ImageDraw.Draw(im).text(xy,text,font=FONT,fill=(240,240,244))

def piece_image(piece,palette):
    im=Image.new('RGBA',(8,len(piece['pixels'])))
    im.putdata([tuple(palette[c]) for row in piece['pixels'] for c in row])
    return im

def composed(row,palette,registration=False):
    im=Image.new('RGBA',(128,112));ax,ay=64,56
    # SAT priority: first sprite wins nontransparent overlaps.
    for p in reversed(row['pieces']):
        im.alpha_composite(piece_image(p,palette),(ax+p['x']+(1 if registration else 0),ay+p['y']+(18 if registration else 0)))
    return im

def cross(im,x,y):
    d=ImageDraw.Draw(im);d.line((x-3,y,x+3,y),fill=(255,80,220));d.line((x,y-3,x,y+3),fill=(255,80,220))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,default=OUT/'preview-input.json');a=p.parse_args()
    data=json.loads(a.input.read_text());out=a.input.parent
    for key,t in data['types'].items():
        pal=data['palette'][key]['rgba'];typeid=int(key);ims=t['images']
        if not ims:continue
        raw=Image.new('RGBA',(512,56+48*((len(t['raw_tiles'])+15)//16)),BG)
        caption(raw,f'Type ${typeid:02X}: raw VRAM 8x8 tiles | palette ${data["palette"][key]["index"]:02X}')
        for n,tile in enumerate(t['raw_tiles']):
            x,y=(n%16)*32,(n//16)*48+48
            raw.alpha_composite(piece_image(tile,pal).resize((32,32),Image.Resampling.NEAREST),(x,y))
            caption(raw,f'{tile["tile"]:02X}',(x+5,y+32))
        raw.save(out/f'type-{typeid:02x}-raw.png')
        frames=sorted({v['frame'] for v in ims})
        sheet=Image.new('RGBA',(768,56+len(frames)*240),BG)
        caption(sheet,f'Type ${typeid:02X} | palette ${data["palette"][key]["index"]:02X} | magenta = anchor')
        for n,frame in enumerate(frames):
            for flip in (False,True):
                row=next(v for v in ims if v['frame']==frame and v['mirror']==flip)
                stage=Image.new('RGBA',(128,112),(65,72,84));stage.alpha_composite(composed(row,pal,True));cross(stage,64,56)
                stage=stage.resize((256,224),Image.Resampling.NEAREST)
                # Keep rows comfortably separated; no crop of source pixels.
                sheet.alpha_composite(stage,(256*int(flip),56+n*240))
                label=f'frame {frame} | bit4={int(flip)}'
                if typeid!=0x25 and flip:
                    label=f'frame {frame} | UNUSED mirror'
                caption(sheet,label,(256*int(flip)+8,56+n*240+8))
                rawframe=composed(row,pal)
                rawframe.save(out/f'type-{typeid:02x}-frame-{frame:02d}-bit4-{int(flip)}.png')
            # Third column separates SAT source pieces in exact mapping order.
            row=next(v for v in ims if v['frame']==frame and not v['mirror'])
            caption(sheet,'SAT pieces (uncomposed)',(520,64+n*240))
            for j,piece in enumerate(row['pieces']):
                x,y=520+(j%10)*24,88+n*240+(j//10)*42
                sheet.alpha_composite(piece_image(piece,pal).resize((16,32),Image.Resampling.NEAREST),(x,y))
        sheet.save(out/f'type-{typeid:02x}-sheet.png')
    for key,ctx in data['contexts'].items():
        t=data['types'][key];pal=data['palette'][key]['rgba'];im=Image.new('RGBA',(256,224))
        im.putdata([tuple(c) for row in ctx['pixels'] for c in row])
        row=next(v for v in t['images'] if v['frame']==(ctx['head_frame'] if int(key)==0x51 else 1) and not v['mirror'])
        x,y=ctx['anchor']
        for piece in reversed(row['pieces']):
            im.alpha_composite(piece_image(piece,pal),(x+piece['x']+1,y+piece['y']+18))
        if int(key)==0x51:
            # Original scheduler-captured head-above-balls composition.
            for child in ctx.get('children',[]):
                cr=next(v for v in t['images'] if v['frame']==child['frame'] and not v['mirror'])
                for piece in reversed(cr['pieces']):
                    im.alpha_composite(piece_image(piece,pal),(x+child['dx']+piece['x']+1,y+child['dy']+piece['y']+18))
        cross(im,x,y)
        im=im.resize((768,672),Image.Resampling.NEAREST)
        result=Image.new('RGBA',(768,708),BG);result.alpha_composite(im,(0,36))
        caption(result,f'Type ${int(key):02X} | {ctx["act"].upper()} canonical terrain crop | anchor {ctx["world_anchor"]}')
        result.save(out/f'type-{int(key):02x}-context.png')
    # Compact approval boards include raw tiles, actual frames and canonical context.
    for key in data['contexts']:
        tid=int(key);prefix=f'type-{tid:02x}'
        raw=Image.open(out/f'{prefix}-raw.png').convert('RGBA')
        context=Image.open(out/f'{prefix}-context.png').convert('RGBA')
        if tid!=0x51:
            frames=Image.open(out/f'{prefix}-sheet.png').convert('RGBA')
        else:
            ims=[v for v in data['types'][key]['images'] if not v['mirror']]
            frames=Image.new('RGBA',(768,56+((len(ims)+3)//4)*188),BG)
            caption(frames,'$51 normal art | frames10/11: landing dust child | no forced mirrors')
            pal=data['palette'][key]['rgba']
            for n,row in enumerate(ims):
                cell=Image.new('RGBA',(128,112),(65,72,84));cell.alpha_composite(composed(row,pal,True));cross(cell,64,56)
                cell=cell.resize((192,168),Image.Resampling.NEAREST)
                frames.alpha_composite(cell,((n%4)*192,56+(n//4)*188))
                label=f'frame {row["frame"]}'
                if row['frame']>=10:label+=' (landing dust)'
                caption(frames,label,((n%4)*192+6,56+(n//4)*188))
        board=Image.new('RGBA',(768,raw.height+frames.height+context.height+16),BG)
        board.alpha_composite(raw,(128,0));board.alpha_composite(frames,(0,raw.height+8))
        board.alpha_composite(context,(0,raw.height+frames.height+16))
        board.save(out/f'{prefix}-approval.png')
    support=Image.new('RGBA',(768,880),BG)
    caption(support,'Boss support | palette $0D | runtime bit4=0 | raw tiles + composed frames')
    for col,key in enumerate(('52','10','15')):
        pal=data['palette'][key]['rgba'];t=data['types'][key]
        caption(support,f'${int(key):02X}: {t["name"]}',(col*256+8,40))
        for n,tile in enumerate(t['raw_tiles']):
            x,y=col*256+8+(n%12)*20,70+(n//12)*28
            support.alpha_composite(piece_image(tile,pal).resize((16,16),Image.Resampling.NEAREST),(x,y))
        for n,row in enumerate(v for v in t['images'] if not v['mirror']):
            cell=Image.new('RGBA',(128,112),(65,72,84));cell.alpha_composite(composed(row,pal,True));cross(cell,64,56)
            support.alpha_composite(cell.resize((192,168),Image.Resampling.NEAREST),(col*256+24,170+n*172))
            caption(support,f'frame {row["frame"]}',(col*256+32,174+n*172))
    caption(support,'$12 slides the existing HUD SAT; no standalone sprite is invented.',(8,858))
    support.save(out/'support-approval.png')
    pngs=sorted(out.glob('*.png'))
    manifest={'approval':'PENDING','generator':'gpz_enemy_approval.py + gpz_enemy_previews.py','images':[
              {'file':v.name,'sha256':hashlib.sha256(v.read_bytes()).hexdigest(),'size':list(Image.open(v).size)} for v in pngs]}
    manifest['import_candidates_pending_approval']=[v.name for v in pngs if '-frame-' in v.name and
                ('type-25-' in v.name or '-bit4-0.png' in v.name)]
    manifest['excluded']='Sheets, context composites and forced mirrors outside type $25 are review diagnostics, not runtime assets.'
    (out/'png-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'{len(pngs)} PNGs rendered in {out}')

if __name__=='__main__':main()
