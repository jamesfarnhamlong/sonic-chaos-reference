"""Extract AQZ-only review input; original renderer SAT composition, never synthetic art.

Pixels/PNG stay in ignored build/aqz-approval. Committed manifest contains hashes.
Run aqz_art_previews.py with bundled Pillow Python after extraction.
"""
import argparse
import json
from pathlib import Path
import aqz_foundation as F
import level_package as L
import mghz_object_census as C
import mghz_art_approval as A
import thz1_type18_dynamic_graphics as D
import thz1_object_assets as G
import player_state_11_graphics as PG

OUT=F.ROOT/'build/aqz-approval'
CACHE=F.OUT/'art-approval.json'

def build(r):
    manifest,census,acts=F.build(r)
    data=dict(rom_sha256=L.ROM_SHA256,status='APPROVED',acts={},subjects={},animated={})
    meta=dict(format=1,rom_sha256=L.ROM_SHA256,research_base=F.BASE,status='APPROVED',approved_by="James", approval_date="2026-10-07", approval_statement="all AQZ A1 boards approved", approval_base="d1661de8b44b7904dd1c250c6fa53b8f4c24b735",
        output_directory='build/aqz-approval',composition='original ROM renderer SAT pieces; reverse SAT precedence, no extra bitmap flip; diagnostic forced mirrors labelled',
        subjects={},terrain={},animated={},reproduction=['tools/aqz_foundation.py ROM','tools/aqz_art_approval.py ROM','tools/aqz_art_previews.py'],
        limitations=['James approved all A1 boards on 2026-10-07; forced mirrors remain diagnostics.', 'Static maps do not simulate waterline raster IRQ or parallax.',
            'Boss selector23 and palette16 traced to initializer; children use their own mappings.',
            'Script frames include invisible/init frames; gameplay reachability belongs to later audits.'])
    for k,a in acts.items():
        d=a['descriptor'];bg=A.pal(r,d['palette']['background_index']);sp=A.pal(r,d['palette']['sprite_index'])
        blocks={b['id'] for b in manifest['acts'][k]['blocks']}
        pix=A.block_maps(r,a,a['vram'],blocks)
        data['acts'][k]=dict(width=a['width'],height=a['height'],runtime_cells=a['runtime_cells'],cells=a['cells'],
            blocks={str(b):px for b,px in pix.items()},background=bg,sprite=sp,
            start=[d['start']['ram_d511'],d['start']['ram_d514']],camera=[d['start']['ram_d2d6'],d['start']['ram_d2d8']])
        if k!='aqz3':data['acts'][k]['underwater_palettes']=dict(background=A.pal(r,48),sprite=A.pal(r,49))
        meta['terrain'][k]=dict(blocks={str(b):L.sha256(bytes(c for row in px for c in row)) for b,px in pix.items()},
            palettes=manifest['acts'][k]['graphics']['palettes'],loads=a['vram_loads'])
    # Deduplicate exact type/base pairs. The AQZ palette differs, so shared objects
    # receive a palette-variant board only when visible under this palette.
    seen=set()
    _,dynamic=D.dynamic_list_for_selector(r,23)
    meta['boss_dynamic_loads']=dynamic
    for k,a in acts.items():
        for rec in census['acts'][k]['records']:
            t=int(rec['type_id'],16);bases=(int(rec['aux0'],16),int(rec['aux1'],16))
            tag=(t,bases)
            if tag in seen:continue
            seen.add(tag)
            sc=C.state_scripts(r,t)
            vram=bytearray(a['vram']);palette=a['descriptor']['palette']['sprite_index']
            if t==89:
                D.apply_dynamic_entries(vram,r,dynamic);palette=16;bases=(0,0)
            elif t in (12,48):
                # Initialization callback overrides art bases; execute instead of guessing.
                o,m,step,_=C.object_lab_init(r,a,rec);m[0xD297],m[0xD298]=4,a['descriptor']['act'];step();bases=(m[C.SLOT+8],m[C.SLOT+9])
            key=f'{t:02X}-{bases[0]:02X}-{bases[1]:02X}'
            # $30 parameter0 follows strong states7->1->2->5->7. Frame3
            # belongs to the unplaced weak path (states3/4/6), not this mapping.
            used=[fi for fi in sc['frames'] if not (t==48 and fi==3)]
            frames=[C.frame_record(r,t,fi,*bases,bytes(vram),flips=(False,True)) for fi in used]
            data['subjects'][key]=dict(type=t,act=k,bases=bases,palette=A.pal(r,palette),frames=frames,
                label=f'type ${t:02X} bases ${bases[0]:02X}/${bases[1]:02X}; original SAT, forced mirror diagnostic',
                flags=rec['flags'],parameter=rec['parameter'])
            meta['subjects'][key]=dict(type=t,act=k,bases=bases,palette_index=palette,
                palette_file=L.PALETTE_DATA+palette*16,placement_file=rec['rom_offset'],frames=[C.strip_pixels(x) for x in frames],status='APPROVED')
    a=acts['aqz3'];v=bytearray(a['vram']);D.apply_dynamic_entries(v,r,dynamic)
    for t in (90,91,92,93):
        sc=C.state_scripts(r,t);used=set(sc['frames'])
        if t==92:used.update(census['boss']['child5c_frame_selector']['frames'])
        frames=[C.frame_record(r,t,fi,0,0,bytes(v),flips=(False,True)) for fi in sorted(used)]
        key=f'{t:02X}-child'
        data['subjects'][key]=dict(type=t,act='aqz3',bases=[0,0],palette=A.pal(r,16),frames=frames,
            label=f'boss child ${t:02X}; selector23/palette16; base override reachability needs A5')
        meta['subjects'][key]=dict(type=t,frames=[C.strip_pixels(x) for x in frames],status='APPROVED',
            caveat='dynamic art bases0 inherited from boss command-4 spawns; initializer callbacks do not write art bases; behavior reachability remains A5')
    # Waterline/controller art is dynamically created, not part of mapped census.
    sc=C.state_scripts(r,13);a=acts['aqz1']
    frames=[C.frame_record(r,13,fi,0xA0,0,bytes(a['vram']),flips=(False,)) for fi in sc['frames']]
    data['subjects']['0D-waterline']=dict(type=13,act='aqz1',bases=[160,0],palette=A.pal(r,10),frames=frames,label='type $0D camera-relative waterline strip; original unmirrored SAT')
    meta['subjects']['0D-waterline']=dict(type=13,frames=[C.strip_pixels(x) for x in frames],status='APPROVED',source='$0C:$9DAD initializer sets base $A0')
    for t,bases,label in [(14,(0xA4,0),'water-entry effect; initializer $9FAA/base$A4'),(50,(0,0),'water countdown; initializer $9500/base0')]:
        sc=C.state_scripts(r,t);frames=[C.frame_record(r,t,fi,*bases,bytes(a['vram']),flips=(False,)) for fi in sc['frames']]
        key=f'{t:02X}-water-support'
        data['subjects'][key]=dict(type=t,act='aqz1',bases=bases,palette=A.pal(r,10),frames=frames,label=label)
        meta['subjects'][key]=dict(type=t,bases=bases,frames=[C.strip_pixels(x) for x in frames],status='APPROVED',source=label)
    # Rocket Shoes are present in AQZ1; show the shared player graphics under
    # AQZ's sprite palette rather than duplicating the already-approved art.
    player_frames=[]
    mapping=G.object_mapping(r,1)
    fps=G.mapping_frame_pointers(r,mapping['mapping_cpu'],128)
    for fi in PG.FRAME_IDS:
        src=PG.dynamic_source(r,fi);v=bytearray(a['vram']);v[:len(src['raw'])]=src['raw']
        fr=G.parse_frame_record(r,fps[fi]);images=[]
        for flip in (False,True):
            pieces=C.sat_pieces(r,1,fi,0,0,flip)
            for p in pieces:p['pixels']=G.tile_pixels(v,p['pattern'])+G.tile_pixels(v,p['pattern']+1)
            images.append(dict(mirror=flip,pieces=pieces,composed_index_sha256=C.composed_hash(pieces)))
        player_frames.append(dict(frame=fi,frame_cpu=hex(fps[fi]),frame_rom=hex(fr['frame_rom']),images=images,
            source={key:value for key,value in src.items() if key!='raw'}))
    data['subjects']['01-rocket-palette']=dict(type=1,act='aqz1',bases=[0,0],palette=A.pal(r,10),frames=player_frames,label='Rocket Shoes shared player frames38-3A; AQZ palette10 variant')
    meta['subjects']['01-rocket-palette']=dict(type=1,palette_index=10,frames=[dict(frame=f['frame'],source=f['source'],
        compositions=[im['composed_index_sha256'] for im in f['images']]) for f in player_frames],status='APPROVED')
    a=acts['aqz1'];d=manifest['ring_animation']['descriptor']
    for name,copies in [('ring',[dict(source_cpu=d['ring_frames_source_cpu']+128*i,vram=d['ring_frames_vram_destination'],length=128) for i in range(4)])]+[
        (f'effect{eid}',e['unique_copies']) for eid,e in manifest['effects'].items()]:
        variants=[];summaries=[]
        for cp in copies:
            v=bytearray(a['vram']);off=L.bank_cpu_to_rom(29,cp['source_cpu']);dst=cp['vram'];n=cp['length'];v[dst:dst+n]=r[off:off+n]
            touched=set(range(dst//32,(dst+n)//32))
            blocks={b['id'] for b in manifest['acts']['aqz1']['blocks'] if any((x&511) in touched for x in b['mapping']['attributes'])}
            px=A.block_maps(r,a,bytes(v),blocks)
            variants.append(dict(copy=cp,tiles={str(t):A.tile_rows(v,t) for t in sorted(touched)},blocks={str(b):p for b,p in px.items()}))
            summaries.append(dict(copy=cp,file=off,sha256=L.sha256(r[off:off+n]),affected_blocks=sorted(blocks)))
        data['animated'][name]=variants;meta['animated'][name]=summaries
    return meta,data

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('--check',action='store_true');args=p.parse_args()
    meta,data=build(L.load_rom(args.rom));OUT.mkdir(parents=True,exist_ok=True)
    if args.check:assert CACHE.read_text(encoding='utf-8')==F.dumps(meta)
    else:CACHE.write_text(F.dumps(meta),encoding='utf-8')
    (OUT/'preview-input.json').write_text(F.dumps(data),encoding='utf-8')
    print('Approved subjects:',list(meta['subjects']))

if __name__=='__main__':main()
