"""M2-R3: private ROM in; numeric evidence/hashes out. No asset publication.

Original Z80 routine controls are synthetic, not natural Windows gameplay.
Optional --package reads the frozen private B extraction without changing it.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import rom as R
import level_package as L
import aqz_enemies as E
import aqz_water as W
import g2e_score as G
import mghz_object_census as C
import thz1_object_assets as A
import u5a_opening as O
from oracle import Oracle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/m2r3'
BASE = 'd6f2fafcda7903c0fc7082b2a9cbf4fed6e0bf98'
H = lambda b: hashlib.sha256(b).hexdigest()


def dumps(v,depth=0):
    """Readable metadata with scalar table rows kept on one line."""
    pad='  '*depth;child='  '*(depth+1)
    if isinstance(v,dict):
        return '{\n'+',\n'.join(child+json.dumps(k)+': '+dumps(x,depth+1) for k,x in v.items())+'\n'+pad+'}' if v else '{}'
    if isinstance(v,list) and any(isinstance(x,(dict,list)) for x in v):
        return '[\n'+',\n'.join(child+dumps(x,depth+1) for x in v)+'\n'+pad+']'
    return json.dumps(v)


def source(r, bank, start, end):
    off = start if start < 0x8000 else bank*0x4000+start-0x8000
    return dict(bank=bank, cpu=start, end=end, file=off,
                sha256=H(r[off:off+end-start]), instructions=G.disasm(r,bank,start,end))


def palettes(r):
    modes = W.raster(r)
    sources = modes['palette_modes']
    frames = []
    for character in (1,2):
        ptrs=A.mapping_frame_pointers(r,A.object_mapping(r,character)['mapping_cpu'],128)
        # Tails' 88 valid nonblank imported mappings; invalid $5E excluded explicitly.
        ids=range(1,89) if character==2 else (1,10,11,28,56,57,58)
        for f in ids:
            fr=A.parse_frame_record(r,ptrs[f]);raw=O.player_tiles(r,character,f)
            vram=bytearray(16384);vram[:len(raw)]=raw
            identity=[(0,0,0,0)]+[(i,0,0,255) for i in range(1,16)]
            w,h,pix,meta=A.render_frame(vram,fr,0,scale=1,margin=0,palette=identity)
            indices=bytes(pix[i] if pix[i+3] else 0 for i in range(0,len(pix),4))
            used=sorted(set(indices)-{0})
            colors={}
            for mode,key in [('above','above_water_cram'),('split','split_irq_cram'),('full','fully_submerged_cram')]:
                pal=sources[key][16:]
                colors[mode]={str(i):list(A.sms_color(pal[i])) for i in used}
            stage_equal=all(A.palette_rgba(r,p)[i]==A.palette_rgba(r,10)[i] for p in range(6,12) for i in used)
            if character==2: assert stage_equal
            frames.append(dict(character=character,frame=f,canvas=[w,h],index_sha256=H(indices),
                opaque_indices=used,opaque_stage6_to11_equal=stage_equal,colors=colors))
    # Execute the original IRQ palette writer using the SMS harness's VDP ports,
    # but no scheduler/interrupt injection: explicit subroutine controls.
    from sms_frame_harness import SMS
    cram=[]
    for character,water,raster in itertools.product((1,2),(0,255),(96,255)):
        s=SMS(r);m=s.mem;c=s.cpu;c.set_breakpoint(0x0100)
        m[0xD500]=character;m[0xD443]=water;m[0xD132]=raster
        before=bytes([21]*32);s.cram[:]=before
        def call(pc):
            c.pc=pc;c.sp=0xDFE0;s.w16(c.sp+(6 if pc==0x0652 else 0),0x0100)
            for _ in range(20):
                c.ticks_to_stop=100000;c.run()
                if c.pc==0x0100:return
            raise AssertionError(hex(c.pc))
        call(0x0652)
        copied=raster!=255 or water!=0
        assert bytes(s.cram)==(r[0x688:0x6A8] if copied else before)
        irq=H(bytes(s.cram))
        m[0xD472:0xD492]=bytes(sources['above_water_cram'])
        m[0xD496]=128 # explicit restore control, including the skipped-IRQ case
        call(0x1CBD)
        assert bytes(s.cram)==bytes(sources['above_water_cram'])
        cram.append(dict(character=character,water=water,raster=raster,copied=copied,
                         irq_cram_sha256=irq,restored_sha256=H(bytes(s.cram))))
    return dict(sources=sources,boundaries=modes['boundary_vectors'],frames=frames,cram_controls=cram,
        sources_code=[source(r,*v) for v in [(0,0x0652,0x0688),(0,0x1CBD,0x1CD3),(12,0x9DED,0x9E55)]])


def inventory(r):
    out={};blocks={}
    for act in (0,1):
        key=f'aqz{act+1}';a=L.build_act(r,key,dict(zone=4,act=act,name=key))
        cells=a['cells'][:a['runtime_cells']];rows=[]
        # Full terrain type5 census plus visual cross ornaments (04/29).
        for i,b in enumerate(cells):
            if b not in (4,41) and all(R.header(r,b,p)['flags']&31!=5 for p in (0,1)):continue
            headers=[R.header(r,b,p) for p in (0,1)]
            mp=L.block_mapping(r,a['descriptor']['header']['block_mapping_rom'],b)
            blocks[f'{key}:{b:02X}']=dict(headers=headers,mapping=mp,
                entries=[dict(tile=x&511,hflip=bool(x&512),vflip=bool(x&1024),palette=(x>>11)&1,priority=bool(x&4096)) for x in mp['attributes']])
            cx,cy=i%a['width'],i//a['width']
            rows.append(dict(index=i,block=b,cell=[cx,cy],world=[cx*32,cy*32],
                classification='terrain spike bed' if headers[0]['flags']&31==5 else 'cross masonry, not hazard callback',
                headers_key=f'{key}:{b:02X}',neighbors={n:cells[j] if 0<=j<len(cells) else None for n,j in [('left',i-1),('right',i+1),('above',i-a['width']),('below',i+a['width'])]}))
        recs=[x for x in E.placements(r) if x['act']==act and x['type_id']=='0x3C']
        spears=[]
        for rec in recs:
            b=(int(rec['aux0'],16),int(rec['aux1'],16))
            geometry=[]
            for frame in (1,2):
                d=C.frame_record(r,60,frame,*b,bytes(a['vram']),flips=(False,))
                ps=d['images'][0]['pieces'];opaque=[]
                for p in ps:
                    for y,row in enumerate(p['pixels']):
                        for x,c in enumerate(row):
                            if c:opaque.append((p['x']+x,p['y']+y))
                geometry.append(dict(frame=frame,extent=d['extent_x_y'],
                    opaque_bounds=[min(x for x,y in opaque),min(y for x,y in opaque),max(x for x,y in opaque),max(y for x,y in opaque)],
                    index_composition_sha256=d['images'][0]['composed_index_sha256']))
            clean={k:v for k,v in rec.items() if k!='raw_bytes'}
            spears.append(dict(placement=clean,geometry=geometry,collision_plane='object overlap; no terrain plane',
                orientation='up/frame1' if int(rec['parameter'],16)==0 else 'down/frame2; initialY+12',
                callback=0x9284,damage_chain=[0x0434,0x630B,0x6328,0x48BC,0x48F7]))
        out[key]=dict(width=a['width'],runtime_cells=a['runtime_cells'],terrain=rows,spears=spears,
                      layout_sha256=H(bytes(cells)),other_objects=[{k:x[k] for k in ('index','type_id','world_x','world_y','parameter')} for x in a['records']])
    return dict(acts=out,blocks=blocks)


def spear_controls(r):
    rows=[]
    for rec in (x for x in E.placements(r) if x['type_id']=='0x3C'):
        q=E.Lab(r,rec);o,m=q.o,q.m
        # Actual script owns extents/frame; creator and init retained in separate inventory.
        q.m[E.S+1]=q.m[E.S+2]=1 if int(rec['parameter'],16)==0 else 5
        q.m[E.S+14]=q.m[E.S+15]=0;q.engine()
        assert (m[E.S+44],m[E.S+45])==(3,13)
        for character,water,plane,(dx,dy),clock,sleep,flags,power in itertools.product(
            (1,2),(0,255),(0,1),((0,0),(-11,0),(11,0),(12,0),(0,-13),(0,-14),(0,24),(0,25)),
            (0,1),(0,64),(0,2,64,128),(0,6)):
            q.reset();m[0xD500]=character;m[0xD2C8]=character;m[0xD443]=water;m[0xD525]=plane
            m[E.S+44]=3;m[E.S+45]=13;m[E.S+4]=sleep;m[0xD12F]=clock
            q.player(q.ox+dx,q.oy+dy,flags,power);m[0xD501]=m[0xD502]=5;m[0xD29A]=0x32
            o.word(0xD516,123);o.word(0xD518,77)
            q.call(0x9284);request=m[0xD3B0];ox,oy=o.word(0xD511),o.word(0xD514)
            o.cpu.ix=0xD500;o.call(0x48BC)
            hit=not sleep and clock==0 and not flags&64 and abs(dx)<=11 and -13<=dy<=24
            hurt=hit and not flags&128 and power!=6
            assert request==(255 if hit else 0)
            assert m[0xD502]==(30 if hurt else 5)
            assert (ox,oy)==(q.ox+dx,q.oy+dy) # no solid-object projection
            rows.append([rec['act'],rec['index'],character,water,plane,dx,dy,clock,sleep,flags,power,request,m[0xD502],o.word(0xD511)-ox,o.word(0xD514)-oy])
    return dict(columns=['act','placement','character','water','plane','dx','dy','clock','sleep','flags','power','damage_request','requested_state','damage_dx','damage_dy'],rows=rows)


def motion_controls(r):
    out=[]
    for rec in (x for x in E.placements(r) if x['type_id']=='0x3C'):
        q=E.Lab(r,rec);rows=[]
        for u in range(180):
            sleep=64 if 40<=u<80 else 0
            q.m[E.S+4]=sleep;q.m[0xD12F]=u&255;q.step()
            d=E.state(q)
            rows.append(dict(u=u,clock=u&255,sleep=sleep,expected=[d[k] for k in ('current','requested','frame','x','y')]+d['extent']))
        out.append(dict(placement={k:v for k,v in rec.items() if k!='raw_bytes'},rows=rows))
    return out


def terrain_controls(r,inv):
    from platform_spike_collision import TerrainLab
    out=[]
    approaches=[('land',16,-2,0,256,133),('rise',16,-2,0,-256,133),
        ('left_high',-5,0,512,0,0),('left_low',-5,16,512,0,0),
        ('right_low',36,16,-512,0,0),('ceiling',16,35,0,-512,133)]
    for act in (0,1):
        key=f'aqz{act+1}';a=L.build_act(r,key,dict(zone=4,act=act,name=key))
        t=TerrainLab(r);t.m[0xC001:0xD000]=bytes(4095)
        t.m[0xC001:0xC001+a['runtime_cells']]=bytes(a['cells'][:a['runtime_cells']])
        t.o.word(0xD16A,-a['width'])
        for row in range(128):t.o.word(0xD800+row*2,row*a['width'])
        # All real spike beds, and the first cross ornament as a negative visual control.
        candidates=[x for x in inv['acts'][key]['terrain'] if x['block'] not in (4,41)]
        candidates+=next(([x] for x in inv['acts'][key]['terrain'] if x['block']==4),[])
        for cell,character,water,plane,ap in itertools.product(candidates,(1,2),(0,255),(0,1),approaches):
            name,dx,dy,vx,vy,prev=ap;x,y=cell['world'];x+=dx;y+=dy
            t.m[0xD500]=character;t.m[0xD443]=water
            d=t.run_terrain(x,y,vx=vx,vy=vy,prev=prev,cur=10,req=10,f3=1,plane=plane)
            out.append(dict(act=act,index=cell['index'],block=cell['block'],character=character,water=water,plane=plane,
                approach=name,input=[x,y,vx,vy,prev],output=d))
    return out


def package_checks(r,package,palette):
    """All frame pixels are compared privately; emit counts/hashes only."""
    from PIL import Image
    import zipfile
    archive=package.with_suffix('.zip')
    assert H(archive.read_bytes())=='3ee8ed903df63ceedd6de2298df936bd41ef357f1598311c5a48bd64cd5f68a3'
    z=zipfile.ZipFile(archive)
    checked=set()
    def original_file(p):
        rel=p.relative_to(package).as_posix();b=p.read_bytes()
        assert z.read(package.name+'/'+rel)==b,rel
        checked.add(rel);return b
    evidence=dict(files={},frames=[],archive_sha256=H(archive.read_bytes()),shader_equation='proxy alpha byte minus1; indexed RGB red byte minus1')
    files=['shaders/SHD_chaos_aqz_palette/SHD_chaos_aqz_palette.fsh','verification/m2_assets.py','verification/chaos_world_harness.js']
    files += [f'scripts/{n}/{n}.gml' for n in ('SCR_chaos_aqz_environment','SCR_chaos_aqz_enemy','SCR_chaos_core','SCR_chaos_core_data','SCR_chaos_attack','SCR_chaos_box_contact','SCR_chaos_tails_frames','SCR_chaos_aqz_data','SCR_chaos_aqz_environment_data')]
    for rel in files:
        evidence['files'][rel]=H(original_file(package/rel))
    shader=(package/files[0]).read_text()
    draw=(package/'scripts/SCR_chaos_aqz_environment/SCR_chaos_aqz_environment.gml').read_text()
    assert 'proxy ? floor(col.a*255.0+0.5)-1.0 : floor(col.r*255.0+0.5)-1.0' in shader
    assert '(cp_base != cp_o.sprite_index || (global.player==2 && chaos_tails_indexed(cp_base))) ? 1 : 0' in draw
    ptrs=A.mapping_frame_pointers(r,A.object_mapping(r,2)['mapping_cpu'],128)
    for f in range(1,89):
        fr=A.parse_frame_record(r,ptrs[f]);raw=O.player_tiles(r,2,f);vram=bytearray(16384);vram[:len(raw)]=raw
        palettes=[('normal',A.palette_rgba(r,7)),('indexed',[(0,0,0,0)]+[(17+i,1,1,255) for i in range(1,16)])]
        for label,pal in palettes:
            name=f'SPR_chaos_m2_tails_{"idx_" if label=="indexed" else ""}{f:02X}'
            folder=package/'sprites'/name;meta=json.loads(original_file(folder/(name+'.yy')).decode('utf-8-sig'))
            png=folder/(meta['frames'][0]['name']+'.png');im=Image.open(png).convert('RGBA')
            w,h,pix,_=A.render_frame(vram,fr,0,scale=1,margin=0,palette=pal)
            assert im.size==(w,h) and im.tobytes()==bytes(pix)
            opaque=sorted(set(im.get_flattened_data())-{(0,0,0,0)})
            evidence['frames'].append(dict(frame=f,format=label,png_sha256=H(original_file(png)),rgba_sha256=H(im.tobytes()),opaque_colors=len(opaque),alpha_values=sorted(set(c[3] for c in opaque)),wrong_proxy_indices=sorted(set(c[3]-1 for c in opaque)) if label=='indexed' else []))
    a=L.build_act(r,'aqz1',dict(zone=4,act=0,name='AQZ1'))
    folder=package/'sprites/SPR_chaos_aqz_enemy_3c'
    meta=json.loads(original_file(folder/'SPR_chaos_aqz_enemy_3c.yy').decode('utf-8-sig'))
    assert [meta['width'],meta['height'],meta['sequence']['xorigin'],meta['sequence']['yorigin']]==[64,64,31,14]
    evidence['spear_art']=[]
    for frame in (1,2):
        d=C.frame_record(r,60,frame,106,106,bytes(a['vram']),flips=(False,))
        expected=Image.new('RGBA',(64,64))
        for piece in reversed(d['images'][0]['pieces']):
            tile=Image.new('RGBA',(8,len(piece['pixels'])))
            tile.putdata([(17+c,1,1,255) if c else (0,0,0,0) for row in piece['pixels'] for c in row])
            expected.alpha_composite(tile,(32+piece['x'],32+piece['y']))
        png=folder/(meta['frames'][frame]['name']+'.png');actual=Image.open(png).convert('RGBA')
        assert actual.tobytes()==expected.tobytes()
        bbox=actual.getbbox()
        evidence['spear_art'].append(dict(frame=frame,png_sha256=H(original_file(png)),origin=[31,14],registration=[1,18],
            opaque_bounds_relative_draw=[bbox[0]-31,bbox[1]-14,bbox[2]-32,bbox[3]-15]))
    # A deterministic equation control; GLSL execution/GPU compilation is not claimed.
    evidence['decoder_controls']=[]
    for i in range(1,16):
        encoded=(17+i,1,1,255);bad_idx=encoded[3]-1;good_idx=encoded[0]-1
        assert bad_idx==254 and good_idx==16+i
        for mode,key in [('above','above_water_cram'),('split','split_irq_cram'),('full','fully_submerged_cram')]:
            evidence['decoder_controls'].append(dict(index=i,mode=mode,current_proxy_index=bad_idx,current_rgb=list(encoded[:3]),correct_cram_index=good_idx,correct_rgba=list(A.sms_color(palette['sources'][key][good_idx]))))
    evidence['archive_files_verified']=len(checked);z.close();return evidence


def build(r,package=None):
    p=palettes(r);inv=inventory(r);controls=spear_controls(r)
    v=dict(rom_sha256=R.SHA256,base=BASE,canonical_instructions='main@5c95e9e',
        independent_m2r2='cd417c16b9e4ae614a3592f5b851a351af786afa; read only, not merged',
        evidence_kind='decoded data + controlled original Z80 routines; not natural input-only gameplay or Windows',
        palette=p,inventory=inv,spears=controls,
        terrain_controls=terrain_controls(r,inv),
        code=[source(r,*x) for x in [(30,0x9251,0x9291),(0,0x630B,0x631A),(0,0x6328,0x640B),(0,0x48BC,0x49C3),(0,0x0603,0x0607),(0,0x6ACE,0x6AE3),(0,0x7306,0x736B),(0,0x74E7,0x752D)]])
    if package:v['private_package']=package_checks(r,package,p)
    return v


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('--package',type=Path);p.add_argument('--check',action='store_true');a=p.parse_args()
    v=build(R.load(a.rom),a.package);OUT.mkdir(parents=True,exist_ok=True)
    text=dumps(v)+'\n';dest=OUT/'evidence.json'
    if a.check:assert dest.read_text()==text
    else:dest.write_text(text)
    motion=dumps(motion_controls(R.load(a.rom)))+'\n'
    if a.check:assert (OUT/'motion.json').read_text()==motion
    else:(OUT/'motion.json').write_text(motion)
    print(json.dumps(dict(spear_controls=len(v['spears']['rows']),palette_frames=len(v['palette']['frames']),spears={k:len(x['spears']) for k,x in v['inventory']['acts'].items()},package_frames=len(v.get('private_package',{}).get('frames',[])))))


if __name__=='__main__':main()
