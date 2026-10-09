"""Fresh numeric zone-5 foundation. Runtime closure is deliberately separate."""
import argparse
import json
from collections import Counter
from pathlib import Path
import level_package as L
import rom as R
import aqz_foundation as A
import mghz_foundation as M
import mghz_object_census as C
import sez_foundation as S
from oracle import Oracle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/rom-cache/eez'
BASE = '89641f8093e62401cd81f94e6ac889422f600472'
ACTS = {f'eez{i+1}': dict(zone=5, act=i, name=f'Zone 5 Act {i+1}') for i in range(3)}
CONTRACTS = {9: 'docs/object-09.md', 16: 'docs/object-10.md; docs/powerup-shoes-audit.md',
             24: 'docs/object-18-act-clear.md', 38: 'docs/spring-interaction-audit.md',
             40: 'docs/platform-spike-collision-audit.md; docs/sez-platform-28-audit.md',
             44: 'docs/gpz-enemies-25-2c-audit.md'}

def loader(r, a):
    o = Oracle(r)
    o.mem[0xD297], o.mem[0xD298] = 5, a['descriptor']['act']
    o.call(0x4E57)
    start = {hex(p): o.word(p) for p in (0xD2D6, 0xD2D8, 0xD511, 0xD514)}
    o.call(0x4FDC)
    header = {hex(p): o.word(p) for p in (0xD164,0xD166,0xD168,0xD16A,0xD280,0xD282,0xD27C,0xD27E)}
    h = a['descriptor']['header']; o.bank(2,h['layout_bank'])
    o.mem[0xC001:0xD002] = bytes([165])*4097
    o.cpu.hl=h['layout_cpu'];o.cpu.pc=0x4DBE;o.cpu.set_breakpoint(0x4DFB)
    for _ in range(20):
        o.cpu.ticks_to_stop=100000;o.cpu.run()
        if o.cpu.pc==0x4DFB:break
    assert o.cpu.pc==0x4DFB
    data=bytes(o.mem[0xC001:o.cpu.de])
    assert data==bytes(a['cells'][:a['runtime_cells']])
    assert bytes(o.mem[o.cpu.de:o.cpu.de+2])==bytes([165])*2
    return dict(start=start,header=header,cells_checked=len(data),sha256=L.sha256(data),sentinel=True)

def build(r):
    assert L.sha256(r)==L.ROM_SHA256
    acts={k:L.build_act(r,k,v) for k,v in ACTS.items()}
    m=dict(format=1,rom_sha256=L.ROM_SHA256,research_base=BASE,zone=5,
           evidence='decoded data and controlled original loaders; runtime contracts remain separate',
           stage='A1 foundation',acts={},surfaces={},effects={},unresolved=[
               'Reachable act count and terminal progression require A5 control-flow proof; three table records decoded.',
               'Surface 01 zone5 gate and any new consumers require A2.',
               'Object reuse must be parameter/zone-gate checked in A3/A4.',
               'Types 5E/60 and final completion require A5; identities not inferred from appearance.',
               'New art approval is pending James; no approval inherited from other zones.'])
    census=dict(format=1,rom_sha256=L.ROM_SHA256,acts={},types={})
    consumers,floor,right,left,ceiling=M.surface_consumers(r)
    for key,a in acts.items():
        d=a['descriptor'];h=d['header'];cells=a['cells'][:a['runtime_cells']]
        counts=Counter(cells)
        replacements={b for t in a['semantics']['tables'].values() for b in t['replacement_blocks']}
        blocks=[]
        for b in sorted(set(cells)|replacements):
            hd=R.header(r,b);mp=L.block_mapping(r,h['block_mapping_rom'],b)
            blocks.append(dict(id=b,cells=counts[b],headers=[R.header(r,b,p) for p in (0,1)],mapping=mp))
            if not counts[b]:continue
            s=hd['flags']&31
            row=m['surfaces'].setdefault(str(s),dict(blocks=[],cells={},floor_handler=floor[s],
                earlier_contract=S.SURFACES.get(s),status='NEEDS_ZONE5_GATE_AUDIT' if s==1 else 'REUSE_REQUIRES_CONSUMER_CHECK'))
            if b not in row['blocks']:row['blocks'].append(b)
            row['cells'][key]=row['cells'].get(key,0)+counts[b]
        m['acts'][key]=dict(descriptor=d,dimensions_cells=[a['width'],a['height']],
            dimensions_pixels=[a['width']*32,a['height']*32],layout=dict(encoded_cells=len(a['cells']),
            runtime_written_cells=a['runtime_cells'],runtime_sha256=L.sha256(bytes(cells)),
            rows=[a['cells'][i:i+a['width']] for i in range(0,len(a['cells']),a['width'])],
            unloaded_cells=[dict(index=i,block=a['cells'][i]) for i in range(a['runtime_cells'],len(a['cells']))]),
            blocks=blocks,rings=dict(terrain=a['terrain_rings'],object09=L.object_rings(a),tables=a['semantics']),
            graphics=dict(loads=a['vram_loads'],vram_sha256=L.sha256(a['vram']),
                palettes={n:dict(index=d['palette'][n+'_index'],file=d['palette'][n+'_rom'],
                    cram=list(r[d['palette'][n+'_rom']:d['palette'][n+'_rom']+16])) for n in ('background','sprite')}),
            mapping_check=A.mapping_check(r,h),original_loaders=loader(r,a))
        ptr=L.object_list_pointer(r,5,d['act']);rows,term=L.decode_object_list(r,ptr['list_rom'])
        for rec in rows:
            t=int(rec['type_id'],16)
            rec.update(act=key,original_creator=A.placement_creator(r,rec),
                earlier_contract=CONTRACTS.get(t),status='REUSE_CANDIDATE' if t in CONTRACTS else 'NEEDS_AUDIT')
            row=census['types'].setdefault(rec['type_id'],dict(placements=0,acts={},parameters={},
                scripts=C.public_script(C.state_scripts(r,t)),earlier_contract=CONTRACTS.get(t)))
            row['placements']+=1;row['acts'][key]=row['acts'].get(key,0)+1
            row['parameters'][rec['parameter']]=row['parameters'].get(rec['parameter'],0)+1
        census['acts'][key]=dict(pointer=ptr,count=len(rows),terminator_file=term,records=rows,
            type_counts=dict(sorted(Counter(x['type_id'] for x in rows).items())))
    desc=M.ring_art_descriptor(r,5,0)
    m['ring_animation']=dict(M.terrain_ring_animation(r,desc),descriptor=desc)
    for eid in sorted(set(desc['effect_ids'])-{0}):
        pal=acts['eez1']['descriptor']['palette']
        kwargs=dict(zone=5,bg_palette=pal['background_index'],sprite_palette=pal['sprite_index'])
        events=S.run_effect(r,eid,192,**kwargs)
        m['effects'][str(eid)]=dict(events=events,boss_active_events=S.run_effect(r,eid,192,d44e=1,**kwargs),
            unique_copies=list({(c['source_cpu'],c['vram'],c['length']):c for e in events for c in e['vram_copies']}.values()))
    m['surface_consumers']=consumers
    return m,census,acts

def dumps(v):return json.dumps(v,indent=2)+'\n'

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('--check',action='store_true');args=p.parse_args()
    m,c,_=build(L.load_rom(args.rom));OUT.mkdir(parents=True,exist_ok=True)
    for name,value in [('implementation-manifest.json',m),('object-census.json',c)]:
        if args.check:assert (OUT/name).read_text(encoding='utf-8')==dumps(value),name
        else:(OUT/name).write_text(dumps(value),encoding='utf-8')
    print({k:(v['dimensions_cells'],len(v['rings']['terrain']),c['acts'][k]['count']) for k,v in m['acts'].items()})

if __name__=='__main__':main()
