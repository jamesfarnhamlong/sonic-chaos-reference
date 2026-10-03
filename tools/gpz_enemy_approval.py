"""Research-only GPZ enemy/boss extraction. Art stays in ignored build/.

Run with the canonical ROM; optionally render with gpz_enemy_previews.py (Pillow).
No POC imports, commits, or gameplay claims from static screenshots.
"""
import argparse
import hashlib
import json
from pathlib import Path
import rom as R
import level_package as L
import thz1_animation_reach as A
import thz1_object_assets as G
import thz1_type18_dynamic_graphics as D
import mapped_object_registration as M
from oracle import Oracle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'build/gpz-enemy-approval'
CACHE = ROOT/'data/rom-cache/gpz/enemy-art-approval.json'
TYPES = (0x25, 0x2C, 0x51, 0x34, 0x0A, 0x0F, 0x12)
NAMES = {0x25:'ground patrol',0x2C:'flying enemy',0x51:'boss and segmented children',
         0x34:'explosion puff',0x0A:'bonus sparkle',0x0F:'enemy defeat smoke',0x12:'HUD slide controller'}

def script(r, bank, start):
    """Decode bounded script control flow; retain loop counts, don't unroll them."""
    pc, seen, out = start, set(), []
    lengths={0:0,1:2,2:4,3:1,4:6,5:4,6:1,7:2,9:2,11:2,12:2,14:1,15:2}
    while pc not in seen:
        seen.add(pc); off=A.cpu_to_rom(bank,pc); row={'cpu':pc,'rom':off}
        if r[off] != 255:
            row.update(op='record',duration=r[off],frame=r[off+1],callback=R.u16(r,off+2));pc+=4
        else:
            c=r[off+1]
            if c not in lengths: raise ValueError((hex(pc),c))
            args=list(r[off+2:off+2+lengths[c]])
            row.update(op='command',command=c,args=args);pc+=2+lengths[c]
            if c in (0,3): out.append(row);break
            if c==7: pc=args[0]|args[1]<<8
        out.append(row)
        if len(out)>256: raise ValueError('script limit')
    return out

def states(r,t):
    tab=A.animation_state_table(r,t)
    return {'table':tab,'states':[{'state':n,'script':script(r,tab['bank'],p)}
           for n,p in enumerate(tab['state_script_cpus'])]}

def placements(r):
    out={}
    for zone in range(6):
        for act in range(3):
            key=('thz','gpz','mghz','sez','aqz','eez')[zone]+str(act+1)
            ptr=L.object_list_pointer(r,zone,act)
            rows,_=L.decode_object_list(r,ptr['list_rom'])
            out[key]=[v for v in rows if int(v['type_id'],16) in (0x25,0x2C,0x51)]
    return out

def oracle_sat(r,t,i,base0,base1,flip):
    o=M.RenderOracle(r)
    got=o.render(type_id=t,frame_index=i,obj_x=128,obj_y=96,cam_x=0,cam_y=0,
                 flags=16 if flip else 0,art0=base0,art1=base1)
    return [{'x':x-128,'y':y-96,'tile':tile,'pattern':tile&254}
            for x,y,tile in zip(got['sat_x'],got['sat_y'],got['sat_tile'])]

def base_oracle(r,t,row):
    """Original mapped allocator, then original initial callback where applicable."""
    from platform_spike_collision import ObjectLab,SLOT
    lab=ObjectLab(r,t,bytes.fromhex(row['raw_bytes']),A.animation_bank(t),int(row['flags'],16))
    m=lab.m
    return {'base0':m[SLOT+8],'base1':m[SLOT+9],'extent_x':m[SLOT+0x2C],
            'extent_y':m[SLOT+0x2D],'requested_state':m[SLOT+2],
            'vx':R.s16(lab.obj16(0x16)),'vy':R.s16(lab.obj16(0x18))}

def contacts(r,t,ex,ey):
    """Closed-box exhaustive overlap grid on the original helper + hurt/attack helper."""
    o=Oracle(r);m=o.mem;o.cpu.ix=0xD700;m[0xD700]=t
    m[0xD72C],m[0xD72D]=ex,ey;m[0xD52C],m[0xD52D]=8,24
    o.word(0xD711,1000);o.word(0xD714,500)
    tested=mismatches=0;bounds=[]
    for dy in range(-ey-26,27):
        for dx in range(-ex-10,ex+11):
            m[0xD503]=m[0xD703]=m[0xD721]=0
            o.position(1000+dx,500+dy);o.call(0x6328)
            got=bool(m[0xD721]&15)
            want=abs(dx)<=ex+8 and -ey<=dy<=24
            tested+=1;mismatches+=got!=want
            if got: bounds.append((dx,dy))
    cases=[]
    for posture in (0,1,2,3,0x40,0x80):
        for inv in (0,6):
            for dx,dy in ((0,-10),(0,10),(-10,0),(10,0)):
                m[0xD700]=t;m[0xD703]=0;m[0xD721]=0
                m[0xD503]=posture;m[0xD532]=inv;m[0xD520]=m[0xD521]=m[0xD3B0]=0
                m[0xD73E]=7;m[0xD406]=t;m[0xD501]=5
                o.position(1000+dx,500+dy);o.call(0x6328)
                if m[0xD721]&15:o.call(0x0323)
                cases.append({'posture':posture,'invincibility':inv,'dx':dx,'dy':dy,
                              'type_after':m[0xD700],'D520':m[0xD520],'D521':m[0xD521],
                              'placement_token':m[0xD73E],'occupancy':m[0xD406]})
    return {'evidence':'CONTROLLED ROUTINE RESULT','grid_cases':tested,'grid_mismatches':mismatches,
            'bounds':[min(x for x,y in bounds),max(x for x,y in bounds),min(y for x,y in bounds),max(y for x,y in bounds)],
            'reaction_cases':cases,'scope':'Overlap + shared enemy reaction helper; not whole-update replay'}

def movement_checks(r):
    o=Oracle(r);m=o.mem;o.cpu.ix=0xD700;o.bank(2,12)
    failures=0
    for param in range(256):
        m[0xD73F]=param;o.word(0xD711,5000);o.call(0xB535)
        failures+=o.word(0xD737)!=(5000-param*16)&65535
        failures+=R.s16(o.word(0xD716))!=-128 or o.word(0xD718)!=512 or m[0xD73F]!=0
    o.bank(2,30);triggers=[];removals=[]
    for distance in (-65,-64,-63,0,63,64,65):
        m[0xD700]=0x2C;m[0xD704]=0;m[0xD702]=1
        m[0xD710]=m[0xD713]=0
        m[0xD72C],m[0xD72D]=12,16;o.word(0xD711,1000);o.word(0xD714,500)
        o.word(0xD716,-640);o.word(0xD718,0);o.position(997-distance,1000)
        o.call(0x89AC)
        triggers.append({'post_move_dx':distance,'requested_state':m[0xD702],'keep_alive':bool(m[0xD704]&2)})
        assert (m[0xD702]==2)==(abs(distance)<64),triggers[-1]
    for distance in (-385,-384,-383,383,384,385):
        m[0xD700]=0x2C;m[0xD704]=0;o.word(0xD711,1000);o.word(0xD714,500)
        o.position(1000-distance,1000);o.call(0x8A29)
        removals.append({'pre_move_dx':distance,'type_after':m[0xD700]})
        assert (m[0xD700]==0xFE)==(abs(distance)>=384)
    assert failures==0
    return {'evidence':'CONTROLLED ROUTINE RESULT','patrol_initializers':256,'mismatches':failures,
            'type2c_trigger':triggers,'type2c_removal':removals}

def build(r,out=OUT):
    out.mkdir(parents=True,exist_ok=True)
    rows=placements(r)
    gpz={k:L.build_act(r,k,{'zone':1,'act':n,'name':k.upper()}) for n,k in enumerate(('gpz1','gpz2','gpz3'))}
    cache={'format':1,'rom_sha256':R.SHA256,'canonical_base':'08fb38c','approval':'PENDING HUMAN VISUAL REVIEW',
           'placements':rows,'types':{},'unresolved':['Human common enemy/boss names are not proven by ROM tables.',
           'Static PNG composites are not original-game observations.','GPZ3 full boss collision/phase/clear oracle remains a separate rollout gate.']}
    cache['controlled_movement']=movement_checks(r)
    art={'types':{},'contexts':{},'palette':{}}
    boss_states=states(r,0x51)
    # Collect code only from instruction control flow, never disassemble scripts as code.
    from z80dis import z80
    import thz3_boss_support as B
    lines=[]
    for t in TYPES:
        st=states(r,t);bank=st['table']['bank'];entries=set()
        for s in st['states']:
            for v in s['script']:
                if v['op']=='record':entries.add(v['callback'])
                if v.get('command') in (1,5):entries.add(v['args'][0]|v['args'][1]<<8)
        flow=B.flow_ranges(r,bank,entries)
        for start,end in flow['ranges']:
            pc=start
            while pc<end:
                off=bank*0x4000+pc-0x8000;d=z80.decode(r[off:off+4],pc)
                if not d.len:raise ValueError(hex(pc))
                lines.append(f'{bank:02X}:{pc:04X} file {off:05X} {z80.disasm(d)}');pc+=d.len
        cache.setdefault('source_regions',{})[str(t)]=dict(flow,bank=bank,
            hashes=[{'start':a,'end':b,'sha256':hashlib.sha256(r[bank*0x4000+a-0x8000:bank*0x4000+b-0x8000]).hexdigest()}
                    for a,b in flow['ranges']])
    (out/'source-trace.txt').write_text('\n'.join(lines)+'\n')
    for t in TYPES:
        st=boss_states if t==0x51 else states(r,t)
        used=sorted({v['frame'] for s in st['states'] for v in s['script'] if v['op']=='record'})
        gpz_rows=[dict(act=k,**v) for k,vs in rows.items() if k.startswith('gpz') for v in vs if int(v['type_id'],16)==t]
        info={'type':t,'identity':NAMES[t],'evidence':'DECODED DATA + CONTROLLED RENDERER RESULT',
              'animation':st,'gpz_placements':gpz_rows,'all_script_frames':used}
        if t in (0x25,0x2C):
            info['init']=base_oracle(r,t,gpz_rows[0]);bases=(info['init']['base0'],info['init']['base1'])
            info['contact']=contacts(r,t,info['init']['extent_x'],info['init']['extent_y'])
            assert info['contact']['grid_mismatches']==0
            act=gpz['gpz1'];vram=act['vram'];loads=act['vram_loads']
            active=used
        else:
            act=gpz['gpz3'];vram=bytearray(act['vram']);loads=act['vram_loads']
            bases=(0,0)
            if t==0x34:
                bases=(r[30*0x4000+0x8C98-0x8000+1],)*2
            active=used if t in (0x51,0x34) else ([5,6] if t==0x0A else ([7,8,9] if t==0x0F else []))
            if t in (0x51,0x34,0x0A,0x0F):
                # Selector is established by the init callback's LD A,$14 / LD ($D3B3),A.
                list_cpu,entries=D.dynamic_list_for_selector(r,0x14)
                D.apply_dynamic_entries(vram,r,entries)
                info['dynamic_load']={'selector':0x14,'list_cpu':list_cpu,'entries':[
                    dict(e,source_sha256=hashlib.sha256(r[e['source_rom']:e['source_rom']+e['tile_count']*32]).hexdigest())
                    for e in entries]}
        info['bases']={'normal':bases[0],'mirrored':bases[1]}
        info['vram_loads']=loads
        info['preview_frames']=active
        if t==0x51:
            info['source_traced_frame_candidates']=list(range(1,12))
            info['unresolved_frame_usage']={'frames':[], 'reason':'$51/$11 child activation is now traced through floor-tail $9C0F and parameter+1 initialization.'}
            info['composition_manifest']='data/rom-cache/gpz/boss-51-composition.json'
        info['mirror_rule']='original coordinate mirror table + alternate art base; never whole-bitmap flip'
        if t not in (0x25,0x2C):info['mirror_rule']='bit4=0 runtime art only; forced bit4=1 is a diagnostic and NOT an approved import candidate'
        info['registration']='SAT-relative pixels; terrain-relative presentation = (+1,+18), separate from gameplay anchor'
        palette_index=act['descriptor']['palette']['sprite_index'] if t in (0x25,0x2C,0x12) else 0x0D
        pal=G.palette_rgba(r,palette_index)
        info['palette_index']=palette_index
        art['palette'][str(t)]={'index':palette_index,'rgba':pal}
        mapinfo=G.object_mapping(r,t)
        frameptrs=G.mapping_frame_pointers(r,mapinfo['mapping_cpu'])
        info['mapping']={k:v for k,v in mapinfo.items() if k!='pointer_raw'}
        info['mapping']['frame_count']=len(frameptrs)
        images=[];framedata=[]
        for i in active:
            f=G.parse_frame_record(r,frameptrs[i]);framedata.append(G.serialise_frame(f))
            if not f['piece_count']:continue
            for flip in (False,True):
                sat=oracle_sat(r,t,i,*bases,flip)
                model=M.model_slot(r,obj_x=128,obj_y=96,cam_x=0,cam_y=0,frame_cpu=frameptrs[i],
                                   flags=16 if flip else 0,art0=bases[0],art1=bases[1])
                assert [(p['x'],p['y'],p['tile']) for p in sat]==[(p['sat_x']-128,p['sat_y']-96,p['tile']) for p in model]
                pieces=[]
                for p in sat:
                    pix=G.tile_pixels(vram,p['pattern'])+G.tile_pixels(vram,p['pattern']+1)
                    pieces.append(dict(**p,pixels=pix))
                images.append({'frame':i,'mirror':flip,'pieces':pieces,'model':model})
        info['frames']=framedata
        if t==0x0F:
            colors=sorted({c for im in images for p in im['pieces'] for line in p['pixels'] for c in line})
            p7,p13=G.palette_rgba(r,7),G.palette_rgba(r,13)
            info['palette7_vs13']={'used_indices':colors,'used_colors_identical':all(p7[c]==p13[c] for c in colors)}
        info['required_spawns']=[{'state':s['state'],'type':v['args'][0],
                'dx':R.s16(v['args'][1]|v['args'][2]<<8),'dy':R.s16(v['args'][3]|v['args'][4]<<8),
                'parameter':v['args'][5],'script_cpu':v['cpu']}
                for s in st['states'] for v in s['script'] if v.get('command')==4]
        if t==0x51:
            info['required_spawns'].append({'state':9,'type':81,'dx':10,'dy':0,
                'parameter':17,'script_cpu':0x9C0F,'activation':'$9F14 installs the inline landing tail; init requests state18'})
        cache['types'][str(t)]=info
        art['types'][str(t)]={'name':NAMES[t],'images':images,'frames':active,'bases':bases}
        # Recovered tiles in VRAM order, distinct from assembled SAT pieces.
        patterns=sorted({p['pattern']+j for im in images for p in im['pieces'] for j in (0,1)})
        art['types'][str(t)]['raw_tiles']=[{'tile':p,'pixels':G.tile_pixels(vram,p)} for p in patterns]
    for t,actkey in ((0x25,'gpz1'),(0x2C,'gpz1'),(0x51,'gpz3')):
        act=gpz[actkey];row=next(v for v in rows[actkey] if int(v['type_id'],16)==t)
        x,y=row['world_x'],row['world_y']
        if t==0x25:
            # Show the original terrain-projected runtime anchor, not the raw spawn Y.
            o=Oracle(r);m=o.mem;o.cpu.ix=0xD700;m[0xD700]=t
            m[0xD72C],m[0xD72D]=7,17
            m[0xC001:0xD000]=bytes((act['cells']+[0]*4095)[:4095])
            o.word(0xD168,act['descriptor']['header']['row_offset_table_cpu'])
            o.word(0xD16A,-act['width']);o.word(0xD711,x);o.word(0xD714,y);o.word(0xD718,512)
            o.bank(2,14);m[0xD12B]=14;o.call(0x77CB)
            y=o.word(0xD714)
            cache['types']['37']['controlled_context']={'evidence':'CONTROLLED ROUTINE RESULT',
                'placement_anchor':[row['world_x'],row['world_y']],'projected_anchor':[x,y],
                'routine':0x77CB,'floor_flags':m[0xD722]}
        if t==0x51:x=0x740 # original init $9AB3, not a changed placement
        left=max(0,x-128);top=max(0,y-(176 if t==0x51 else 112))
        maps=L.block_pixel_maps(r,act['vram'],mapping_rom=act['descriptor']['header']['block_mapping_rom'])
        pixels=[]
        palettes=[G.palette_rgba(r,act['descriptor']['palette'][k]) for k in ('background_index','sprite_index')]
        if t==0x51:palettes[1]=G.palette_rgba(r,13)
        for yy in range(224):
            line=[]
            for xx in range(256):
                wx,wy=left+xx,top+yy;idx=(wy//32)*act['width']+wx//32
                c=maps[act['cells'][idx]][wy%32][wx%32] if idx<act['runtime_cells'] and wx<act['width']*32 else 0
                color=list(palettes[bool(c&16)][c&15]);color[3]=255;line.append(color)
            pixels.append(line)
        art['contexts'][str(t)]={'act':actkey,'camera_crop':[left,top],'anchor':[x-left,y-top],
                                'world_anchor':[x,y],'pixels':pixels}
        if t==0x51:
            import gpz51_composition as B
            row=B.replay(r,ticks=233)[232];chain=B.linked(row);head=chain[0]
            x,y=head['x'],head['y']
            ctx=art['contexts'][str(t)]
            ctx['world_anchor']=[x,y];ctx['anchor']=[x-left,y-top];ctx['head_frame']=head['frame']
            children=[dict(parameter=v['parameter'],frame=v['frame'],dx=v['x']-x,dy=v['y']-y) for v in chain[1:]]
            ctx['children']=children
            cache['types']['81']['controlled_composition']={'evidence':'CONTROLLED ORIGINAL OBJECT SCHEDULER',
                'parent_anchor':[x,y],'parent_frame':head['frame'],'tick':232,'children':children,
                'scope':'Normal mode1; head parameter0, three balls parameters1/2/3; lower support pointer +$34'}
    cache['approval']='APPROVED BY USER 2026-10-03; CORRECTED $51 SUPERSEDES PRIOR BOARD'
    cache['subject_approvals']={'37':'APPROVED BY USER','44':'APPROVED BY USER',
        'support':'APPROVED BY USER','81':'CORRECTED PNGS APPROVED BY USER',
        '52':'APPROVED BY USER','10':'APPROVED BY USER','15':'APPROVED BY USER'}
    (out/'preview-input.json').write_text(json.dumps(art,separators=(',',':'))+'\n')
    return cache

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom');p.add_argument('--check',action='store_true')
    args=p.parse_args();r=R.load(args.rom);data=build(r);serialized=json.dumps(data,indent=2)+'\n'
    if args.check:assert CACHE.read_text()==serialized,'cache differs'
    else:CACHE.write_text(serialized)
    print(json.dumps({'rom_verified':True,'cache':str(CACHE),'types':list(data['types']),'approval':data['approval']}))

if __name__=='__main__':main()
