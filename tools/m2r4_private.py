"""Read private C archive/textures; emit hashes/counts/colours only, no pixels."""
import argparse, collections, hashlib, json, re, zipfile
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/m2r4'
H=lambda b:hashlib.sha256(b).hexdigest()
def yy(p):return json.loads(re.sub(r',\s*([}\]])',r'\1',p.read_text()))
def main():
    p=argparse.ArgumentParser();p.add_argument('package',type=Path);p.add_argument('archive',type=Path);a=p.parse_args()
    archive_hash=H(a.archive.read_bytes())
    assert archive_hash=='321bcd86b2daa5539485f17107f037c843a7902267db514b16d22864ef556964'
    files=[];frames=[];crossings=[]
    evidence=json.loads((ROOT/'data/m2r4/palette-original.json').read_text())
    colors={k:[[(x&3)*85,((x>>2)&3)*85,((x>>4)&3)*85] for x in evidence['sources'][v]]
        for k,v in [('above','above_water_cram'),('split','split_irq_cram'),('full','fully_submerged_cram')]}
    with zipfile.ZipFile(a.archive) as z:
        names=z.namelist();prefix=names[0].split('/')[0]+'/'
        assert prefix+'scripts/SCR_chaos_core/SCR_chaos_core.gml' in names
        for folder in ('scripts','shaders','objects'):
            # Source only; no public texture payload.
            for f in (a.package/folder).rglob('*'):
                if f.suffix not in ('.gml','.fsh','.vsh'):continue
                rel=f.relative_to(a.package).as_posix();b=f.read_bytes();assert b==z.read(prefix+rel)
                files.append(dict(path=rel,sha256=H(b)))
        for i in range(1,89):
            n=f'SPR_chaos_m2_tails_idx_{i:02X}';d=a.package/'sprites'/n
            y=yy(d/(n+'.yy'));f=d/(y['frames'][0]['name']+'.png');b=f.read_bytes()
            assert b==z.read(prefix+f.relative_to(a.package).as_posix())
            pix=list(Image.open(f).convert('RGBA').getdata());used=collections.Counter()
            transparent=opaque_black=0
            for red,green,blue,alpha in pix:
                if alpha==0:transparent+=1;continue
                assert alpha==255 and green==blue==1 and 18<=red<=32
                used[red-1]+=1
                if red-1==22:opaque_black+=1
            canonical=evidence['frames'][next(j for j,v in enumerate(evidence['frames']) if v['character']==2 and v['frame']==i)]
            assert sorted(k-16 for k in used)==canonical['opaque_indices']
            changed={mode:sum(n for k,n in used.items() if colors[mode][k]!=colors['above'][k]) for mode in ('split','full')}
            frames.append(dict(frame=i,png_sha256=H(b),opaque_count=sum(used.values()),transparent_count=transparent,
                opaque_black_count=opaque_black,indices=sorted(used),changed_from_above_pixels=changed,
                rgb={mode:{str(k):colors[mode][k] for k in used} for mode in colors}))
            if i==3:
                width,height=Image.open(f).size;origin=y['sequence']['yorigin']
                for delta,anchor_offset in __import__('itertools').product((0,1,191,192,193),(-20,-10,0,10)):
                    mode='full' if delta==0 else 'split' if delta<=192 else 'above'
                    counts=collections.Counter();changed=0;visible={192:collections.Counter(),196:collections.Counter()}
                    for n,(red,green,blue,alpha) in enumerate(pix):
                        if not alpha:continue
                        # World registration +18 and actual sprite origin; sample centres.
                        world_y_relative_line=anchor_offset+18-origin+n//width+0.5
                        selected='full' if mode=='full' else 'split' if mode=='split' and world_y_relative_line>=1 else 'above'
                        counts[selected]+=1;idx=red-1
                        for view_height,counts_visible in visible.items():
                            if 0<=delta+world_y_relative_line<view_height:counts_visible[selected]+=1
                        changed+=colors[selected][idx]!=colors['above'][idx]
                    crossings.append(dict(character=2,frame=3,delta=delta,anchor_minus_line=anchor_offset,
                        origin_y=origin,registered_y_offset=18,selected_opaque_rows=dict(counts),
                        visible_opaque_pixels={str(k):dict(v) for k,v in visible.items()},changed_pixels=changed))
        # Sonic's actual alpha proxies: verify alpha->index and above RGB preservation.
        proxy=json.loads((a.package/'POC_notes/rom-cache/aqz/player-palette-adapter.json').read_text())
        sonic=[]
        for row in proxy['copies']:
            n=row['adapter'];d=a.package/'sprites'/n;y=yy(d/(n+'.yy'))
            opaque=transparent=above_different=0;indices=set()
            for frame in y['frames']:
                f=d/(frame['name']+'.png');b=f.read_bytes();assert b==z.read(prefix+f.relative_to(a.package).as_posix())
                for red,green,blue,alpha in Image.open(f).convert('RGBA').getdata():
                    if not alpha:transparent+=1;continue
                    idx=alpha-1;assert 16<=idx<32;opaque+=1;indices.add(idx)
                    if [red,green,blue]!=colors['above'][idx]:above_different+=1
            sonic.append(dict(resource=n,opaque_count=opaque,transparent_count=transparent,indices=sorted(indices),
                legacy_rgb_differs_from_nearest_palette=above_different,above_route='preserve source RGB; lower/full direct indexed lookup'))
            if row['source']=='SPR_sonic_jump':
                f=d/(y['frames'][0]['name']+'.png');im=Image.open(f).convert('RGBA');width,height=im.size
                pix=list(im.getdata());origin=y['sequence']['yorigin']
                for delta,anchor_offset in __import__('itertools').product((0,1,191,192,193),(-20,-10,0,10)):
                    counts=collections.Counter();visible={192:collections.Counter(),196:collections.Counter()}
                    for n,pixel in enumerate(pix):
                        if not pixel[3]:continue
                        rel=anchor_offset+18-origin+n//width+0.5
                        selected='full' if delta==0 else 'split' if delta<=192 and rel>=1 else 'above'
                        counts[selected]+=1
                        for height,ct in visible.items():
                            if 0<=delta+rel<height:ct[selected]+=1
                    crossings.append(dict(character=1,resource=row['source'],delta=delta,
                        anchor_minus_line=anchor_offset,origin_y=origin,registered_y_offset=18,
                        selected_opaque_rows=dict(counts),visible_opaque_pixels={str(k):dict(v) for k,v in visible.items()}))
    out=dict(archive_sha256=archive_hash,archive_entries=len(names),source_files=files,
        tails=frames,sonic_alpha_proxies=sonic,actual_sprite_crossings=crossings,
        classification='private archive/source/pixel checks; CPU shader equation only; no native GPU',
        vertex_source='v_world_y=in_Position.y; lower row uses interpolated worldY-screen_top>=irq_cut',
        transparent='Tails alpha0 stays0 even if encoded RGB matches; Sonic alpha0 gives invalid index and stays0',
        opaque_black='Tails index22 yields RGB0,0,0 with alpha255 in all three modes')
    (OUT/'private-checks.json').write_text(json.dumps(out,separators=(',',':'))+'\n')
    print('private archive verified; sources',len(files),'Tails',len(frames),'Sonic',len(sonic))
if __name__=='__main__':main()
