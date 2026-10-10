"""Extract new final-zone terrain and numeric object compositions for review.

Known shared object families are omitted. Boss VRAM uses original selector loads.
Only metadata/hashes committed; all pixel arrays remain in ignored build/.
"""
import argparse,json
from pathlib import Path
import eez_foundation as F
import level_package as L
import mghz_object_census as C
import mghz_art_approval as A
import thz1_type18_dynamic_graphics as D
import mghz_foundation as M

def main():
    p=argparse.ArgumentParser();p.add_argument('rom',type=Path);args=p.parse_args()
    r=L.load_rom(args.rom);m,c,acts=F.build(r)
    out=F.ROOT/'build/eez-approval';out.mkdir(parents=True,exist_ok=True)
    data=dict(acts={},subjects={},animated={});meta=dict(status='PENDING_JAMES_REVIEW',rom_sha256=L.ROM_SHA256,
        composition='original SAT piece offsets, reverse SAT precedence; no bitmap reflection/redraw',subjects={},terrain={},
        evidence='Source-traced mappings and dynamic selector loads; original whole-chain SAT/CRAM/raster observations in boss-game caches. Pending James visual approval.')
    # Shared compositions are compared by decoded pixel indices, not by name.
    prior=set()
    for zone in range(5):
        for act in range(3):
            a=L.build_act(r,'prior',dict(zone=zone,act=act,name='prior'))
            px=A.block_maps(r,a,a['vram'],range(256))
            prior.update(L.sha256(bytes(c for row in p for c in row)) for p in px.values())
    for k,a in acts.items():
        d=a['descriptor'];v=bytearray(a['vram'])
        ring=m['ring_animation'];off=L.bank_cpu_to_rom(29,ring['descriptor']['ring_frames_source_cpu']);dst=ring['vram_destination'];v[dst:dst+128]=r[off:off+128]
        seen_dest=set()
        for effect in m['effects'].values():
            for cp in effect['unique_copies']:
                if cp['vram'] in seen_dest:continue
                seen_dest.add(cp['vram']);off=L.bank_cpu_to_rom(29,cp['source_cpu']);dst=cp['vram'];n=cp['length'];v[dst:dst+n]=r[off:off+n]
        blocks=A.block_maps(r,a,bytes(v),{b['id'] for b in m['acts'][k]['blocks']})
        blocks={b:px for b,px in blocks.items() if L.sha256(bytes(c for row in px for c in row)) not in prior}
        data['acts'][k]=dict(width=a['width'],height=a['height'],runtime_cells=a['runtime_cells'],cells=a['cells'],
            blocks={str(b):px for b,px in blocks.items()},background=A.pal(r,26),sprite=A.pal(r,11),
            camera=[d['start']['ram_d2d6'],d['start']['ram_d2d8']])
        meta['terrain'][k]={str(b):L.sha256(bytes(v for row in px for v in row)) for b,px in blocks.items()}
    for t in (0x17,0x36,0x38):
        k,rec=next((k,x) for k,a in c['acts'].items() for x in a['records'] if int(x['type_id'],16)==t)
        bases=[int(rec['aux0'],16),int(rec['aux1'],16)]
        frames=[C.frame_record(r,t,fi,*bases,bytes(acts[k]['vram']),flips=(False,)) for fi in C.state_scripts(r,t)['frames']]
        key=f'{t:02X}'
        data['subjects'][key]=dict(frames=frames,palette=A.pal(r,11),label=f'zone5 type ${t:02X}; original mapping origins and script frames')
        meta['subjects'][key]=dict(bases=bases,frames=[C.strip_pixels(f) for f in frames])
    a=acts['eez3']
    for selector,types in [(24,{94:[0,1,2,3,4,5,20],95:[0]+list(range(10,20))}),
                           (25,{96:list(range(16))}),
                           (26,{97:list(range(8)),98:[0,8,9]}),
                           (33,{99:list(range(8))})]:
        _,entries=D.dynamic_list_for_selector(r,selector);v=bytearray(a['vram']);D.apply_dynamic_entries(v,r,entries)
        for t,ids in types.items():
            key=f'{t:02X}-selector{selector}'
            frames=[C.frame_record(r,t,fi,0,0,bytes(v),flips=(False,)) for fi in ids]
            assert set(C.state_scripts(r,t)['frames'])<=set(ids),(t,ids)
            data['subjects'][key]=dict(frames=frames,palette=A.pal(r,17),label=f'${t:02X} selector{selector}; script plus callback-selected frames')
            meta['subjects'][key]=dict(bases=[0,0],selector=selector,loads=entries,frames=[C.strip_pixels(f) for f in frames],status='PENDING_JAMES_REVIEW')
    for t,parent,base in [(55,54,None),(55,None,124),(57,56,None),(58,None,146)]:
        rec=next(x for a in c['acts'].values() for x in a['records'] if int(x['type_id'],16)==(parent or 54))
        bases=[int(rec['aux0'],16),int(rec['aux1'],16)] if base is None else [base,base]
        frames=[C.frame_record(r,t,fi,*bases,bytes(acts['eez1']['vram']),flips=(False,)) for fi in C.state_scripts(r,t)['frames']]
        key=f'{t:02X}-support'+(f'-base{base:02X}' if base is not None else '')
        data['subjects'][key]=dict(frames=frames,palette=A.pal(r,11),label=f'${t:02X} support; original mappings')
        meta['subjects'][key]=dict(bases=bases,frames=[C.strip_pixels(f) for f in frames],status='PENDING_JAMES_REVIEW')
    # Unique original effect states, affected terrain blocks only. Palette8
    # variations are retained even when indexed pixels are identical.
    for eid,effect in m['effects'].items():
        variants=[];seen=set();a=acts['eez1'];base=bytearray(a['vram'])
        for event in effect['events']:
            v=bytearray(base);bg=A.pal(r,26)
            affected=set()
            for cp in event['vram_copies']:
                dst,n=cp['vram'],cp['length'];off=L.bank_cpu_to_rom(29,cp['source_cpu']);v[dst:dst+n]=r[off:off+n]
                affected.update(range(dst//32,(dst+n+31)//32))
            for pwrite in event['palette_writes']:
                c=pwrite['after'];bg[pwrite['cram_index']]=[(c&3)*85,((c>>2)&3)*85,((c>>4)&3)*85,255]
            identity=L.sha256(bytes(v)+bytes(c for rgba in bg for c in rgba))
            if identity in seen:continue
            seen.add(identity)
            ids=[]
            for b in m['acts']['eez1']['blocks']:
                words=b['mapping'].get('words',[])
                # Decode all blocks and retain by changed indexed pixels when
                # effect modifies VRAM; palette effects retain indices14/15.
                ids.append(b['id'])
            before=A.block_maps(r,a,bytes(base),ids);after=A.block_maps(r,a,bytes(v),ids)
            changed={str(b):px for b,px in after.items() if (px!=before[b] if affected else any(c&15 in (14,15) for row in px for c in row))}
            if not changed:continue
            variants.append(dict(update=event['update'],blocks=changed,background=bg,sprite=A.pal(r,11),copies=event['vram_copies'],palette_writes=event['palette_writes']))
        data['animated'][eid]=variants
        meta.setdefault('animated',{})[eid]=[dict(update=x['update'],blocks=list(x['blocks']),copies=x['copies'],palette_writes=x['palette_writes']) for x in variants]
    (out/'preview-input.json').write_text(F.dumps(data),encoding='utf-8')
    (F.OUT/'art-approval.json').write_text(F.dumps(meta),encoding='utf-8')
    print(out/'preview-input.json')

if __name__=='__main__':main()
