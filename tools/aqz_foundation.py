"""Fresh AQZ A1 extraction from verified ROM; reconnaissance is not a runtime contract.

No historical AQZ exports are read. Pixels remain in ignored build/.
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
import level_package as L
import rom as R
import mghz_foundation as M
import mghz_object_census as C
import sez_foundation as S
import sez_object_census as SC
import block_mapping_audit as BM
from oracle import Oracle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/rom-cache/aqz'
BASE = '53e9095ae2d807be8cd67f8ed572caead09094d9'
ACTS = {f'aqz{i+1}': dict(zone=4, act=i, name=f'Aqua Planet Act {i+1}') for i in range(3)}
CLASSES = ['SHARED_RECOVERED', 'SHARED_WITH_AQZ_DATA', 'AQZ_SPECIFIC_RECOVERED', 'AQZ_SPECIFIC_NEEDS_AUDIT', 'BOSS_SUPPORT', 'UNRESOLVED']
CONTRACTS = {9: 'docs/object-09.md', 16: 'docs/object-10.md; docs/powerup-shoes-audit.md',
             24: 'docs/object-18-act-clear.md',48:'docs/spring-interaction-audit.md; original type30/type26 share state table $8212; mapped parameter0 strong path'}
SURFACES = dict(S.SURFACES)
SURFACES.update({12: ('crumble', 'ACCEPTED_SHARED', 'docs/sez-surfaces-0c-13-1a-audit.md', None),
                 26: ('booster', 'ACCEPTED_SHARED', 'docs/sez-surfaces-0c-13-1a-audit.md', None),
                 4: ('no floor effect: RET', 'SHARED_WITH_AQZ_DATA', '$6CE6 RET; shared collision probes still apply', None),
                 16: ('shared loop/plane gate block family', 'SHARED_WITH_AQZ_DATA', 'docs/gpz-loop-route-audit.md; docs/thz1-final-runtime-closure.md; shared $6C82 dispatch and collision headers; AQZ route layout newly decoded', None),
                 30: ('no floor effect: RET', 'SHARED_WITH_AQZ_DATA', '$6D42 RET; shared collision probes still apply', None)})
digest = L.sha256

def source(r, bank, start, end):
    off = start if bank == 0 else L.bank_cpu_to_rom(bank, start)
    return dict(bank=bank, cpu=start, file=off, length=end-start, sha256=digest(r[off:off+end-start]))

def mapping_check(r, h):
    o = Oracle(r)
    o.bank(2, h['block_mapping_bank'])
    checks = bad = old = 0
    for b in range(256):
        mp = L.block_mapping(r, h['block_mapping_rom'], b)
        for vertical in (False, True):
            cpu = BM.original_pointer(o, h['block_mapping_cpu'], b, vertical)
            checks += 1
            bad += cpu != mp['cpu'] or bytes(o.mem[cpu:cpu+32]) != r[mp['rom']:mp['rom']+32]
        wrong = h['block_mapping_rom'] + mp['cpu'] - 0x8000
        old += r[wrong:wrong+32] != r[mp['rom']:mp['rom']+32]
    assert bad == 0
    return dict(bank=h['block_mapping_bank'], table_cpu=h['block_mapping_cpu'], table_file=h['block_mapping_rom'],
                original_consumer_checks=checks, mismatches=bad, historical_error_bytes=h['block_mapping_rom']%0x4000,
                historical_different_blocks=old, formula='bank * 0x4000 + pointer - 0x8000')

def loader_check(r, act):
    o = Oracle(r)
    o.mem[0xD297], o.mem[0xD298] = 4, act['descriptor']['act']
    o.call(0x4E57)
    start = {hex(p): o.word(p) for p in (0xD2D6,0xD2D8,0xD511,0xD514)}
    o.call(0x4FDC)
    header = {hex(p): o.word(p) for p in (0xD164,0xD166,0xD168,0xD16A,0xD280,0xD282,0xD27C,0xD27E)}
    h=act['descriptor']['header'];o.bank(2,h['layout_bank'])
    o.mem[0xC001:0xD002]=bytes([0xA5])*0x1001
    o.cpu.hl=h['layout_cpu'];o.cpu.pc=0x4DBE;o.cpu.set_breakpoint(0x4DFB)
    for _ in range(20):
        o.cpu.ticks_to_stop=100000;o.cpu.run()
        if o.cpu.pc==0x4DFB:break
    assert o.cpu.pc==0x4DFB
    loaded=bytes(o.mem[0xC001:o.cpu.de]);expect=bytes(act['cells'][:act['runtime_cells']])
    assert loaded==expect
    assert bytes(o.mem[o.cpu.de:o.cpu.de+2])==bytes([0xA5])*2
    return dict(evidence='controlled original loader execution; RLE stopped at $4DFB before renderer', start=start, header=header,
        layout_cells_checked=len(loaded),layout_sha256=digest(loaded),end_de=o.cpu.de,unwritten_sentinel_intact=True)

def placement_creator(r, rec):
    o=Oracle(r);o.bank(2,28);o.cpu.iy=o.cpu.ix=C.SLOT;o.cpu.hl=0xDA00
    o.mem[0xDA00:0xDA09]=bytes.fromhex(rec['raw_bytes']);o.mem[C.SLOT:C.SLOT+64]=bytes(64)
    o.call(0x80EB,bc=0xD400+rec['zero_based_index'])
    b=o.cpu.iy
    value=dict(x=o.word(b+17),y=o.word(b+20),token=o.mem[b+62],flags=o.mem[b+4],parameter=o.mem[b+63],art_bases=[o.mem[b+8],o.mem[b+9]])
    assert (value['x'],value['y'],value['token'])==(rec['world_x']&65535,rec['world_y']&65535,rec['index'])
    return value

def initialization(r,act,rec):
    o,m,step,_=C.object_lab_init(r,act,rec)
    m[0xD297],m[0xD298]=4,act['descriptor']['act']
    step();step();b=C.SLOT
    return dict(zone=4,act=m[0xD298],current_state=m[b+1],requested_state=m[b+2],callback=o.word(b+12),
        x=o.word(b+17),y=o.word(b+20),vx_8_8=C.s16(o.word(b+22)),vy_8_8=C.s16(o.word(b+24)),
        flags=m[b+4],parameter=m[b+63],extent=[m[b+44],m[b+45]])

def child5c_frames(r):
    o=Oracle(r);o.bank(2,30);o.cpu.ix=C.SLOT;results=[]
    for angle in range(256):
        for direction in (2,254):
            for parity in (0,1):
                o.mem[C.SLOT+10]=angle;o.mem[C.SLOT+0x38]=direction;o.mem[C.SLOT+0x1E]=parity
                o.call(0xAE5B)
                expect=(20 if angle>=88 else 22) if direction&128 else (16 if angle<168 else 18)
                assert o.mem[C.SLOT+6]==expect+parity
                results.append(o.mem[C.SLOT+6])
    return dict(routine=source(r,30,0xAE5B,0xAE88),checks=len(results),frames=sorted(set(results)),
        result_sha256=digest(bytes(results)),contract='presentation selector only; complete child runtime remains A5')

def environment(r):
    # Complete gate sweep: avoid RNG/bubble allocation by staying above D450.
    gates = []
    for z in range(6):
        for a in range(3):
            o=Oracle(r); o.cpu.ix=0xD500
            o.mem[0xD297],o.mem[0xD298]=z,a
            o.word(0xD514,99);o.word(0xD450,100);o.mem[0xD443]=255;o.mem[0xD445]=7
            o.call(0x4B46)
            gates.append(dict(zone=z,act=a,water=o.mem[0xD443],timer=o.mem[0xD445]))
    boundary=[]
    for y in (0,99,100,101,65535):
        o=Oracle(r);o.cpu.ix=0xD500;o.word(0xD450,100);o.word(0xD514,y);o.mem[0xD443]=255
        o.call(0x4BC0)
        boundary.append(dict(player_y=y,water=o.mem[0xD443]))
    return dict(evidence='byte-verified assembly and controlled original routines', gates=gates, boundary=boundary,
        water_flag='AQZ1/2 only: $4B46 gates zone==4, act<2; $4BC0 compares unsigned player WORLD(Y) >= WORLD($D450), sets $D443=$FF, otherwise zero',
        physics='Movement core and player state setters read $D443; water physics exists. Transitions, control/gravity coverage and drowning require A2.',
        waterline_producer='$2A2E initializes WORLD(Y)=768 and creates two type $0D objects, parameters 0/1. Type0D callback $9DDD writes object Y to $D450; $9DED derives screen line $D132 from waterline-cameraY and controls $D131/VDP vector $040A.',
        waterline_initializers={'aqz1':568,'aqz2':788,'source':'$0C:$9DAD selects $0238 for act0, $0314 otherwise; no waterline controllers in AQZ3'},
        waterline_visible_span='CENTER/EDGE: $9DED enables scanline when cameraY < waterline <= cameraY+192; IRQ scanline is waterline-cameraY. Fully above/below disables line IRQ.',
        waterline_palettes={'above':[25,10],'below':[48,49],'source':'$9E17/$9E39 queue background/sprite palette commands; IRQ $0652 copies 32 fixed CRAM bytes from $0688',
            'irq_cram':list(r[0x688:0x6A8]),'records':{str(i):dict(file=L.PALETTE_DATA+i*16,cram=list(r[L.PALETTE_DATA+i*16:L.PALETTE_DATA+i*16+16])) for i in (48,49)}},
        waterline_animation='Two type0D instances use tile base $A0. $9EFE increments modulo16 each callback and selects cameraX-relative X from tables $9F2B (parameter0) / $9F4B (parameter1); no art inferred from scenery.',
        timer='Underwater $D444 increments; every 120 calls resets and increments $D445. At 11 creates type $32; at 17 requests player $1F. Leaving water resets $D445.',
        dynamic_support=['0x0C (bubble)', '0x0D (waterline controller)', '0x0E (entry effect)', '0x32 (countdown)'],
        visual_water='Two camera-relative type0D strips and waterline IRQ/palette switching are distinct from effect11 terrain animation. Do not substitute a synthetic water plane.',
        camera='Header bounds decoded. Parallax, waterline screen effect and camera coupling remain reconnaissance below, not widescreen contracts.',
        viewport=[dict(kind='WORLD',value='$D450',use='waterline compare'),dict(kind='WORLD',value=238,use='boss helper $ABF2: Y>238'),
                  dict(kind='EDGE',value=[48,208],use='boss $AA6C cached screen-X stops horizontal velocity')])

def build(r):
    assert digest(r)==L.ROM_SHA256
    acts={k:L.build_act(r,k,v) for k,v in ACTS.items()}
    consumers,floor,right,left,ceiling=M.surface_consumers(r)
    manifest=dict(format=1,rom_sha256=L.ROM_SHA256,research_base=BASE,zone=4,
        evidence='fresh decoded data + original routines; unresolved reconnaissance is not an implementation contract',
        source_policy='No old AQZ exports. No canonical anchor changes or widescreen design.', acts={}, surfaces={}, effects={})
    census=dict(format=1,rom_sha256=L.ROM_SHA256,research_base=BASE,classifications=CLASSES,acts={},types={})
    alltypes=set()
    for k,a in acts.items():
        d=a['descriptor'];h=d['header'];cells=a['cells'][:a['runtime_cells']];counts=Counter(cells)
        blocks=[]
        replacements={b for table in a['semantics']['tables'].values() for b in table['replacement_blocks']}
        for b in sorted(set(cells)|replacements):
            mp=L.block_mapping(r,h['block_mapping_rom'],b);hd=R.header(r,b)
            blocks.append(dict(id=b,cells=counts[b],headers=[R.header(r,b,p) for p in (0,1)],surface=hd['flags']&31,
                solid=bool(hd['flags']&128),one_way=bool(hd['flags']&64),mapping=mp,
                mapping_sha256=digest(b''.join(x.to_bytes(2,'little') for x in mp['attributes']))))
        rings=dict(terrain=a['terrain_rings'],object09=L.object_rings(a),tables=a['semantics'],
            contract='docs/terrain-ring-collection.md; docs/object-09.md; unchanged canonical parity probe and strict type09 proximity')
        manifest['acts'][k]=dict(descriptor=d,dimensions_cells=[a['width'],a['height']],dimensions_pixels=[a['width']*32,a['height']*32],
            layout=dict(rows=[a['cells'][i:i+a['width']] for i in range(0,len(a['cells']),a['width'])],
                encoded_cells=len(a['cells']),runtime_written_cells=a['runtime_cells'],runtime_sha256=digest(bytes(cells)),
                unloaded_cells=[dict(index=i,block=a['cells'][i]) for i in range(a['runtime_cells'],len(a['cells']))]),
            blocks=blocks,rings=rings,graphics=dict(loads=a['vram_loads'],vram_sha256=digest(a['vram']),
                palettes={n:dict(index=d['palette'][n+'_index'],file=d['palette'][n+'_rom'],cram=list(r[d['palette'][n+'_rom']:d['palette'][n+'_rom']+16])) for n in ('background','sprite')}),
            mapping_check=mapping_check(r,h),original_loaders=loader_check(r,a))
        for b,n in counts.items():
            s=R.header(r,b)['flags']&31
            if str(s) not in manifest['surfaces']:
                row=SURFACES.get(s,('numeric surface, needs audit','AQZ_SPECIFIC_NEEDS_AUDIT',None,None))
                manifest['surfaces'][str(s)]=dict(meaning=row[0],status=row[1],contract=row[2],floor_handler=floor[s],
                    side_consumer=s in {x for x,_ in right+left} or s==10,ceiling_consumer=s in {x for x,_ in ceiling},blocks=[],cells={})
            v=manifest['surfaces'][str(s)]
            if b not in v['blocks']:v['blocks'].append(b)
            v['cells'][k]=v['cells'].get(k,0)+n
        ptr=L.object_list_pointer(r,4,d['act']);rows,term=L.decode_object_list(r,ptr['list_rom'])
        for rec in rows:
            t,p=int(rec['type_id'],16),int(rec['parameter'],16);alltypes.add(t)
            cx,cy=rec['world_x']//32,rec['world_y']//32;ix=cy*a['width']+cx
            rec.update(act=k,anchor_cell=[cx,cy],anchor_block=cells[ix] if 0<=cx<a['width'] and 0<=ix<len(cells) else None,
                placement_token=rec['index'],classification='SHARED_WITH_AQZ_DATA' if t in CONTRACTS else 'BOSS_SUPPORT' if t==89 else 'AQZ_SPECIFIC_NEEDS_AUDIT',
                contract=CONTRACTS.get(t),parameter_status='known reward' if t==16 and p in (1,2,3,4,6) else 'shared record format' if t in (9,24) else 'strong spring parameter0' if t==48 and p==0 else 'needs path audit')
            rec['original_creator']=placement_creator(r,rec)
            if t==12:rec.update(classification='AQZ_SPECIFIC_RECOVERED',contract='docs/aqz-water-environment-audit.md; water-runtime.json contracts.bubbles',parameter_status='parameter0 emitter, states0/1; emits parameters1/2')
            if t==16 and p not in (1,2,3,4,6):rec.update(classification='UNRESOLVED',contract=None)
        census['acts'][k]=dict(pointer=ptr,terminator_file=term,records_sha256=digest(r[ptr['list_rom']:term]),count=len(rows),records=rows,
            type_counts=dict(sorted(Counter(x['type_id'] for x in rows).items())),parameter_counts=dict(sorted(Counter(x['type_id']+'/'+x['parameter'] for x in rows).items())))
    # Static state counts are table entries, not proven gameplay reachability.
    support={13,14,50,90,91,92,93,15,52,10,18,19,6,3,7}
    for t in sorted(alltypes|support):
        sc=C.state_scripts(r,t)
        scan=SC.scan_code(r,sc['bank'],[x for x in sc['callbacks']+sc['calls'] if 0x8000<=x<0xC000],f'aqz_type_{t:02x}')
        census['types'][f'0x{t:02X}']=dict(script=C.public_script(sc),code_scan=scan,
            placements=sum(x['type_id']==f'0x{t:02X}' for a in census['acts'].values() for x in a['records']),
            reachability='table states decoded; callback-driven state reachability requires dedicated audit',
            motion_constants=[dict(state=s['state'],x=op['x'],y=op['y']) for s in sc['states'] for op in s['ops'] if op['op']=='velocity_8_8'],
            classification='BOSS_SUPPORT' if t>=89 else 'SHARED_WITH_AQZ_DATA' if t in CONTRACTS else 'AQZ_SPECIFIC_NEEDS_AUDIT' if t in alltypes|{13,14,50} else 'SHARED_RECOVERED')
        if t in (12,13,14,50):census['types'][f'0x{t:02X}'].update(classification='AQZ_SPECIFIC_RECOVERED',reachability='A2 source-traced paths and original-routine/whole-game fixtures',contract='water-runtime.json contracts; docs/aqz-water-environment-audit.md')
    census['controlled_initialization_recon']=[]
    seen=set()
    for k,a in census['acts'].items():
        for rec in a['records']:
            sig=tuple(rec[x] for x in ('type_id','parameter','flags','aux0','aux1'))
            if sig in seen:continue
            seen.add(sig)
            census['controlled_initialization_recon'].append(dict(act=k,index=rec['index'],signature=list(sig),
                after_two_scheduler_callbacks=initialization(r,acts[k],rec),
                evidence='controlled original callbacks on act terrain; synthetic far-away player, no full lifecycle manager; not a gameplay reachability proof'))
    # Parameter matching is evidence only; new callbacks remain blocked even when
    # a type shares scripts. $3F and $28 genuinely point to the same state table.
    accepted=[]
    for z in (0,1,2,3):
        for i in range(3):
            rows,_=L.decode_object_list(r,L.object_list_pointer(r,z,i)['list_rom'])
            accepted.extend((f'{C.ZONE_NAMES[z]}{i+1}',x) for x in rows)
    for k,a in census['acts'].items():
        for rec in a['records']:
            rec['accepted_parameter_matches']=[dict(act=key,index=x['index'],file=x['rom_offset']) for key,x in accepted
                if (x['type_id'],x['parameter'])==(rec['type_id'],rec['parameter'])]
    platform28=C.state_scripts(r,40);platform3f=C.state_scripts(r,63)
    census['platform_reuse_recon']=dict(table28=platform28['state_table_cpu'],table3f=platform3f['state_table_cpu'],
        tables_identical=platform28['state_script_cpus']==platform3f['state_script_cpus'],
        aqz2_override='$8617 zone==4 and act==1 requests state14; must audit before reusing $28 parameter $8B',
        contract_status='AQZ_SPECIFIC_NEEDS_AUDIT despite shared scripts')
    spring26=C.state_scripts(r,38);spring30=C.state_scripts(r,48)
    assert spring26['states']==spring30['states']
    census['spring30_reuse']=dict(table26=spring26['state_table_cpu'],table30=spring30['state_table_cpu'],
        scripts_callbacks_identical=True,mapped_parameters=[0],path=[0,7,1,2,5,7],
        source='same state/callback pointers; $825A adds12 to object Y, param0 selects state7; $82AF selects strong -7.375 launch and state1; states2/5 restore Y',
        contract='docs/spring-interaction-audit.md mapped type26 fixed strong; AQZ mapping $941A/base$86 differs',
        anchor_policy='stored/world anchor unchanged; recovered runtime adds12 to objectY, not an empirical presentation offset',
        unplaced_paths='weak frame3 path is absent from type30 mapping; no type30 nonzero parameter placed in AQZ')
    census['shared_systems']={}
    for name,path in SC.SYSTEM_CACHES.items():
        doc=json.loads((ROOT/'data/rom-cache'/path).read_text(encoding='utf-8'))
        regions=SC.cache_regions(doc)
        bad=[g['name'] for g in regions if digest(r[g['file']:g['file']+g['length']])!=g['sha256']]
        assert not bad
        census['shared_systems'][name]=dict(cache='data/rom-cache/'+path,regions_checked=len(regions),hash_mismatches=bad,
            interpretation='same canonical ROM bytes; water/zone gates require the explicit AQZ environment audit, not blanket exact reuse')
    census['system_presence']={name:dict(mapped=sum(x['type_id']==f'0x{t:02X}' for a in census['acts'].values() for x in a['records']),
        contract=CONTRACTS.get(t),status='not mapped' if t not in alltypes else 'see per-placement classification')
        for name,t in [('rings09',9),('monitors10',16),('sign18',24),('spring26',38),('platform28',40),('spike1b',27),('spring_shoes2f',47)]}
    census['system_presence']['rocket_shoes']=dict(mapped=sum(x['type_id']=='0x10' and x['parameter']=='0x04' for a in census['acts'].values() for x in a['records']),
        contract='docs/powerup-shoes-audit.md',water_path='A2 closed: natural AQZ1 mapped reward and controlled crossing in water-game-checks.json; shared powerup-shoes contract')
    desc=M.ring_art_descriptor(r,4,0)
    manifest['ring_animation']=dict(M.terrain_ring_animation(r,desc),descriptor=desc)
    for eid in sorted(set(desc['effect_ids'])-{0}):
        pal=acts['aqz1']['descriptor']['palette']
        events=S.run_effect(r,eid,192,zone=4,bg_palette=pal['background_index'],sprite_palette=pal['sprite_index'])
        paused=S.run_effect(r,eid,192,zone=4,d44e=1,bg_palette=pal['background_index'],sprite_palette=pal['sprite_index'])
        manifest['effects'][str(eid)]=dict(events=events,boss_active_events=paused,observed_updates=192,
            routine_cpu=M.u16(r,M.bank_file(29,M.EFFECT_JUMP_TABLE)+eid*2),
            cadence=sorted(set(b['update']-a['update'] for a,b in zip(events,events[1:]))),
            unique_copies=list({(c['source_cpu'],c['vram'],c['length']):c for e in events for c in e['vram_copies']}.values()))
    manifest['environment']=environment(r)
    manifest['surface_consumers']=consumers
    manifest['tool_hash_policy']='UTF-8 source normalized to LF before hashing; stable across Git CRLF checkouts'
    manifest['extraction_tool_sha256']={p:digest((ROOT/'tools'/p).read_text(encoding='utf-8').encode('utf-8')) for p in
        ('aqz_foundation.py','aqz_art_approval.py','aqz_art_previews.py','aqz_original_checks.py','aqz_water.py','aqz_water_game.py',
         'level_package.py','rom.py','oracle.py','block_mapping_audit.py','mghz_foundation.py',
         'mghz_object_census.py','sez_foundation.py','sez_object_census.py','sez_surfaces_rig.py','sms_frame_harness.py')}
    manifest['zone_sites']=M.zone_sites(r)['sites']
    for x in manifest['zone_sites']:x.pop('mghz_relevance',None)
    manifest['source_regions']={n:source(r,*v) for n,v in dict(water=(0,0x4B46,0x4C02),start=(0,0x4E57,0x4E98),header=(0,0x4FDC,0x5082),
        placement_creator=(28,0x8000,0x813C),effect5=(29,0x81BF,0x8259),effect11=(29,0x8166,0x81BF),
        waterline_init=(0,0x2A2E,0x2A4F),waterline_controller=(12,0x9DAD,0x9F6B),
        boss_init=(30,0xA9A5,0xA9E0),boss_world_y=(30,0xABF2,0xAC08)).items()}
    manifest['packages']=[dict(id='A2',scope='water physics/drowning, types $0C/$0D/$0E/$32 and background/camera palette effects; AQZ loop-layout integration uses shared contracts'),
        dict(id='A3',scope='type $3F platform parameter paths $83/$86/$8B, shared $28 comparison including AQZ2 override'),
        dict(id='A4',scope='enemies $3C/$3D parameter 0/1 and 0/4/8: contact, movement, lifecycle'),
        dict(id='A5',scope='boss $59 and children $5A/$5B/$5C/$5D, arena and clear; shared support reuse')]
    from aqz_water import contracts
    manifest['water_runtime']=dict(cache='data/rom-cache/aqz/water-runtime.json',whole_game_cache='data/rom-cache/aqz/water-game-checks.json',audit='docs/aqz-water-environment-audit.md',contracts=contracts(r),status='A2_RECOVERED_REVIEW_PENDING')
    manifest['packages'][0]['status']='RECOVERED_REVIEW_PENDING'
    manifest['unresolved']=[
        'Type3F parameter path reuse is not assumed from the shared state scripts (A3)',
        'Callback reachability and boss clear gates are not yet audited (A4/A5)', 'Results graphics/audio remain deferred']
    manifest['poc_ready']='decoded terrain/placements only after Manager review; A1 art approved by James 2026-10-07 and Manager technical review passed; unresolved mechanics omitted explicitly'
    census['boss']=dict(type='0x59',placement=[x for x in census['acts']['aqz3']['records'] if x['type_id']=='0x59'],
        children=['0x5A','0x5B','0x5C','0x5D'],support=['0x12','0x34','0x0F','0x0A'],dynamic_selector=23,
        clear='shared callback $81BD in state4 and explosion state5; precise floor/position gates need A5',
        sign_present=False,source_evidence='decoded script spawns and byte-verified $A9A5 selector; not full behavior audit')
    census['boss']['framework_row']=C.boss_tables(r)['rows'][4]
    census['boss']['child5c_frame_selector']=child5c_frames(r)
    return manifest,census,acts

def dumps(v):return json.dumps(v,indent=2)+'\n'

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('--check',action='store_true');a=p.parse_args()
    manifest,census,_=build(L.load_rom(a.rom));OUT.mkdir(parents=True,exist_ok=True)
    for name,value in [('implementation-manifest.json',manifest),('object-census.json',census)]:
        if a.check:assert (OUT/name).read_text(encoding='utf-8')==dumps(value),name
        else:(OUT/name).write_text(dumps(value),encoding='utf-8')
    print({k:(v['dimensions_cells'],len(v['rings']['terrain']),census['acts'][k]['count']) for k,v in manifest['acts'].items()})

if __name__=='__main__':main()
