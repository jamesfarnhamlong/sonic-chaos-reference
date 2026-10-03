"""Replay the original $51 linked-slot scheduler; no synthetic stack placement.

ROM pixels remain in ignored build/. Metadata/cache contains no tile dumps.
Ticks are zero-based object-scheduler calls, not recording timestamps.
"""
import argparse
import hashlib
import json
from pathlib import Path
import rom as R
from oracle import Oracle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/gpz51-correction'
CACHE = ROOT / 'data/rom-cache/gpz/boss-51-composition.json'
VIDEO_SHA256 = '20dde156f3ed224e71efee5ae863edb8a38a47d659983a1665a84a4fb0aa5d89'
SAMPLES = [(232,'Initial: head + 3 balls'),(333,'Bottom ball launches'),
           (357,'Head + 2; landing dust'),(447,'Second ball slides away'),
           (471,'Head + 1; landing dust'),(579,'Last ball launches'),
           (601,'Head only, on floor'),(602,'Regrow: create below floor'),
           (630,'Regrow: bottom rises'),(670,'Regrow: stack rises'),
           (704,'Restored: head + 3 balls')]

def linked(row):
    """+$34 is lower support; detached attack slots are not attached balls."""
    slots = {v['slot']:v for v in row['slots']}
    chain=[]; p=0xD700
    while p in slots and p not in [v['slot'] for v in chain]:
        v=slots[p]
        if v['parameter']==17 or v['state'] in (11,15,19,20): break
        chain.append(v);p=v['lower_support']
    return chain

def replay(r, player_y=160, player_x=1500, ticks=800):
    o=Oracle(r); m=o.mem
    m[0xD540:0xDA00]=bytes(0x4C0)
    o.position(player_x,player_y);o.word(0xD174,1664);o.word(0xD176,96);m[0xD297]=1
    m[0xDB34:0xDB40]=bytes([16]*4+[32]*4+[0]*4)
    o.bank(2,28)
    # Canonical GPZ3 mapped record at bank $1C:$8DF6, not a fabricated placement.
    m[0xDA00:0xDA09]=r[0x70DF6:0x70DFF]
    o.cpu.hl=0xDA00;o.cpu.iy=0xD700;o.call(0x80EB,bc=0xD418)
    rows=[]
    for tick in range(ticks):
        o.call(0x5DD1)
        slots=[]
        for b in range(0xD540,0xDA00,64):
            if m[b]!=0x51:continue
            slots.append(dict(slot=b,parameter=m[b+63],state=m[b+1],requested_state=m[b+2],
                frame=m[b+6],x=o.word(b+17),y=o.word(b+20),
                vx=R.s16(o.word(b+22)),vy=R.s16(o.word(b+24)),
                lower_support=o.word(b+52),upper_predecessor=o.word(b+54),
                phase=m[b+31],mode=m[b+50],health=m[b+38]))
        row=dict(tick=tick,slots=slots)
        row['attached_parameters']=[v['parameter'] for v in linked(row)]
        rows.append(row)
    return rows

def events(rows):
    out=[];prev=None
    for row in rows:
        sig=[(v['slot'],v['parameter'],v['state'],v['requested_state']) for v in row['slots']]
        if sig!=prev:out.append(row)
        prev=sig
    return out

def build(r):
    OUT.mkdir(parents=True,exist_ok=True)
    video=ROOT.parent/'Screen Recording 2026-10-03 131035.mp4'
    if video.exists():
        assert hashlib.sha256(video.read_bytes()).hexdigest()==VIDEO_SHA256,'reviewed video changed'
    runs={str(y):replay(r,y) for y in (64,160,256)}
    runs['right']=replay(r,160,2200,450)
    for k,rows in runs.items():
        (OUT/f'scheduler-{k}.json').write_text(json.dumps(rows,separators=(',',':'))+'\n')
    main=runs['160']
    samples=[dict(label=label,**main[tick]) for tick,label in SAMPLES]
    source={}
    for name,cpu,size in [('linker',0xA141,19),('mode_gate',0x9B91,12),
                          ('floor_tail',0x9C0F,10),('follow_lower',0x9E4B,100)]:
        off=30*0x4000+cpu-0x8000
        source[name]=dict(bank=30,cpu=cpu,file_offset=off,length=size,
                          sha256=hashlib.sha256(r[off:off+size]).hexdigest())
    result=dict(format=1,rom_sha256=R.SHA256,approval='CORRECTED $51 APPROVED BY USER 2026-10-03',
        evidence='SOURCE-TRACED + CONTROLLED ORIGINAL OBJECT SCHEDULER + ORIGINAL-GAME OBSERVATION',
        scheduler=0x5DD1,camera=[1664,96],presentation=[1,18],terrain_view_origin=[1665,113],
        fixture=dict(player_x=1500,player_y=160,ticks=800,
            limits='Static player, original object scheduler/allocator/scripts; no full player/VDP/IRQ replay. Sample ticks do not synchronize to recording.'),
        pointers=dict(lower_support=0x34,upper_predecessor=0x36),
        normal_order=[0,1,2,3],mode2_order=[0,1,2,3,4],throw_order=[3,2,1],
        regrow_order=[1,2,3],normal_head_state=7,normal_head_frame=2,body_frames=list(range(3,10)),
        dust=dict(type=81,parameter=17,state=18,frames=[10,11],spawn_script=0x9C0F,
                  activation='floor callback $9F14 installs $9C0F; child initializer requests parameter+1'),
        frame_usage=dict(blank=[0],head_source_traced_hit=[1],head_scheduler_observed=[2],
                         body_scheduler_observed=list(range(3,10)),dust_scheduler_observed=[10,11],
                         table_only_unresolved=[]),
        source_regions=source,samples=samples,
        modes={k:dict(max_attached=max(len(v['attached_parameters']) for v in rows),
            observed_frames=sorted({v['frame'] for row in rows for v in row['slots']}),events=events(rows))
            for k,rows in runs.items()},
        previous_board=dict(status='REJECTED / SUPERSEDED',
            errors=['Reversed support link: +$34 points below, not above.',
                    'Assigned frame2 head to parameter1 instead of controller parameter0.',
                    'Forced parameter4 despite mode0/1 gate.',
                    'Omitted parameter17 landing dust and misclassified frames10/11.']),
        video=dict(path=r'E:\AI\Codex\Sonic Chaos\Screen Recording 2026-10-03 131035.mp4',
                   sha256=VIDEO_SHA256,
                   duration_seconds=11.5,observations=[
                       {'second':1,'visible':'Head above three balls'},
                       {'second':3,'visible':'Head above two balls'},
                       {'second':5,'visible':'Head above one ball'},
                       {'second':6,'visible':'Head only near floor; detached thrown ball overhead'},
                       {'second':7,'visible':'Regrowing stack entering from below floor'},
                       {'second':9,'visible':'Head above three balls restored'}],
                   limits='Visual cross-check of composition, not frame-exact scheduler/time synchronization. Mode2 is ROM-only here.'))
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom');p.add_argument('--check',action='store_true')
    a=p.parse_args();r=R.load(a.rom);data=build(r);s=json.dumps(data,indent=2)+'\n'
    if a.check:assert CACHE.read_text()==s,'composition cache differs'
    else:CACHE.write_text(s)
    import level_package as L
    import thz1_object_assets as G
    act=L.build_act(r,'gpz3',{'zone':1,'act':2,'name':'GPZ3'})
    maps=L.block_pixel_maps(r,act['vram'],mapping_rom=act['descriptor']['header']['block_mapping_rom'])
    palettes=[G.palette_rgba(r,act['descriptor']['palette']['background_index']),G.palette_rgba(r,13)]
    attrs={b:L.block_mapping(r,act['descriptor']['header']['block_mapping_rom'],b)['attributes'] for b in set(act['cells'])}
    pixels=[];foreground=[]
    for yy in range(192):
        line=[];front=[]
        for xx in range(256):
            # Original VDP background pixel observes camera+(1,17), while SAT
            # rows have the +1 hardware convention. Terrain-space art uses +18.
            wx,wy=1665+xx,113+yy;idx=(wy//32)*act['width']+wx//32
            c=maps[act['cells'][idx]][wy%32][wx%32]
            color=list(palettes[bool(c&16)][c&15]);color[3]=255;line.append(color)
            attr=attrs[act['cells'][idx]][((wy%32)//8)*4+(wx%32)//8]
            front.append(color if attr&0x1000 and c&15 else [0,0,0,0])
        pixels.append(line);foreground.append(front)
    old=json.loads((ROOT/'build/gpz-enemy-approval/preview-input.json').read_text())
    inp=dict(rom_sha256=R.SHA256,boss=old['types']['81'],palette=old['palette']['81'],
             terrain=pixels,foreground=foreground,samples=data['samples'],
             mode2=json.loads((OUT/'scheduler-256.json').read_text())[280],
             right=json.loads((OUT/'scheduler-right.json').read_text())[333])
    (OUT/'preview-input.json').write_text(json.dumps(inp,separators=(',',':'))+'\n')
    print('Verified ROM; captured three modes, both throw directions, dust and regrowth:',CACHE)

if __name__=='__main__':main()
