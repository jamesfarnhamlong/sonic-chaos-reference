"""One bounded carrier/context proof: plan -> exact emission gate -> private PCM.

Never publishes timelines/audio. No GameMaker writes, synthesis engine or bulk
rendering. Existing P0/P1 and P0R packages/caches are read-only inputs.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import time
import audio1_psg_trace as T
from m5p0r_emission import EmissionModel
from m5p0r_probe import Trace
import m5p0r_proof as P0R
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/m5-p1c'
PUBLIC=ROOT/'data/m5-p1c'
P0P1=ROOT.parent/'sonic-chaos-reference-m5-proof/build/m5-proof'
P0R_ROOT=ROOT.parent/'sonic-chaos-reference-m5-p0r'
OLD=P0R_ROOT/'build/m5-p0r'
M4=ROOT.parent/'sonic-chaos-reference-m4/build/m4/production'
PIN='36821f4cfb6a1b6e386f1b468504245c21c6e24a2cbb0cba4b268703c96334a0'
CASES={
 'fixed-hold':dict(initial=0x81,events={30:[('request',0xB8)],35:[('request',0xBC)]},ticks=210,reuse='P0R B8 carrier and original P0/P1 continuous reference'),
 'coupled-steal-recover':dict(initial=0xA3,events={6:[('request',0xBC)]},ticks=90,reuse=None),
 'clock-switch-with-live-tone2':dict(initial=0xBF,events={3:[('request',0xB8)],8:[('request',0xA3)]},ticks=90,reuse=None),
 'periodic-retrigger':dict(initial=0xBF,events={2:[('request',0xB7)]},ticks=50,reuse=None),
 'music-context-B6':dict(initial=0x81,events={30:[('request',0xB6)],35:[('request',0xA0)]},ticks=180,reuse='P0R B6 corrected context and prior reference'),
 'music-context-BA':dict(initial=0x81,events={30:[('request',0xBA)],36:[('request',0xAC)]},ticks=180,reuse='P0R BA corrected context and prior reference'),
 'isolated-context-B6':dict(initial=0xB6,events={},ticks=47,reuse='P0/P1 isolated B6 library'),
 'off-then-fresh':dict(initial=0xB8,events={3:[('request',0xF8)],5:[('request',0xA3)]},ticks=90,reuse=None),
 'finite-fade':dict(initial=0x88,events={30:[('request',0xAC)],35:[('request',0xA0)],40:[('fade',(12,1,2))]},ticks=90,reuse='P0/P1 existing finite88 stems; new short interaction only')}

def sha(data):return hashlib.sha256(data).hexdigest()
def save(path,x):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def load(path):return json.loads(path.read_text())

def preservation():
    arcs=[(ROOT.parent/'sonic-chaos-reference-m4/build/m4/SonicChaos_M4_AUDIO_20261024_PRIVATE.zip','a5a636ade42a48526b76cf85abb7783f0d9cf50e6817a39b37aec4cbba4a53b9'),
        (P0P1/'SonicChaos_M5_P0P1_20261024_PROOF_PRIVATE.zip','3adf174848e83fc40644a7e12142dbd44062c25c5dff674d09df031fe4b9881f'),
        (P0R_ROOT/'build/SonicChaos_M5_P0R_20261024_DIAGNOSTIC_PRIVATE.zip','89949f3720b396c2deea0e6883cb7007dbdb1457a5771679826b8dbb9a29382f')]
    for path,expected in arcs:
        if sha(path.read_bytes())!=expected:raise ValueError('earlier private package changed')
    assets=load(P0P1/'package/M4-preservation.json')['sha256']
    assert all(sha(Path(p).read_bytes())==v for p,v in assets.items())
    return dict(private_archives=[dict(name=p.name,sha256=h,unchanged=True) for p,h in arcs],M4_assets_checked=len(assets),M4_unchanged=True)

def plan():
    catalogue=load(ROOT/'data/m5/catalogue.json')['entries'];bank=load(P0P1/'dry-event-bank.json')
    rows=[];groups={}
    for r in catalogue:
        if r['category']!='sfx':continue
        rid=r['request_id'];p=bank['programs'][str(rid)]
        f3=[e[1] for s in p['events'] for es in s.values() for e in es if e[0]=='f3']
        modes=sorted(set(v&7 for v in f3));slots=[s['latch'] for s in r['driver_header']['streams']]
        if not f3:kind='tone2-only'
        elif modes==[5]:kind='fixed-white-noise'
        elif modes==[3]:kind='tone2-periodic-noise-retrigger'
        elif len(slots)>1:kind='tone1-plus-coupled-white-noise'
        elif len(f3)>1:kind='coupled-white-noise-retrigger'
        else:kind='coupled-white-noise-single-F3'
        groups.setdefault(kind,[]).append(rid)
        rows.append(dict(id=rid,label=r['friendly_name'],class_id=kind,header_rom=r['driver_header']['header_rom'],slots=slots,
            priority=r['priority']['table_byte'],noise_modes=modes,F3_count=len(f3),release_ticks=r['execution']['release_ticks'],
            physical_tone2_clock_dependency=any(v&3==3 for v in f3),saved_DE11_dependency=bool(f3),
            data_latch_context='F2 restore is an ordinary PSG byte; zero is data to the current latch' if f3 else 'no own noise F2; can inhibit/resume another noise slot',
            coexistence='fixed noise allows tone2; coupled F3 suppresses/owns tone2; tone2 init may suppress coupled noise',
            held_or_off='F2 own-off differs from target write inhibition; envelope off independent of stream end',
            baked_PCM='context-scoped only; no universal sufficiency claim',carrier='requires clock-history compatibility and authenticated finite source lifetime'))
    OUT.mkdir(parents=True,exist_ok=True)
    budget=dict(free_bytes=shutil.disk_usage(OUT).free,max_scratch_bytes=1024**3,max_archive_bytes=128*1024**2,
        max_target_ticks=240,max_unique_new_targets=30,rendering_started=False)
    assert budget['free_bytes']>4*1024**3
    save(PUBLIC/'coverage.json',dict(source='accepted70-ID catalogue and existing complete solo F3 metadata; no new wholesale scan',
        total_catalogue=70,sfx_count=37,classes=groups,entries=rows,
        selected_cases={k:dict(v,natural_gameplay_observation=False,meaning='seeded original-driver response; not a natural game route') for k,v in CASES.items()},
        budget=budget,preservation=preservation()))
    print('coverage before rendering:',{k:len(v) for k,v in groups.items()})

def gate(rom):
    assert (PUBLIC/'coverage.json').exists(),'plan first'
    bank=load(OLD/'dry-emission-bank.json')
    # Add only finite88 intrinsic output data; all other programs are reused.
    bank=P0R.export(rom,ids=[0x88],initial_bank=bank,output_path=OUT/'dry-emission-bank.json')
    result={}
    for name,c in CASES.items():
        d=Trace(rom);d.request(c['initial']);m=EmissionModel(bank);m.direct(c['initial']);rows=[];fail=[];nbytes=0
        for tick in range(1,c['ticks']+1):
            for kind,value in c['events'].get(tick,[]):
                if kind=='request':d.request(value);m.direct(value)
                elif kind=='fade':d.mem[0xDE09:0xDE0C]=bytes(value);m.fade=list(value)
            start=len(d.writes);d.tick();m.tick();ports=[b for _,b in d.writes[start:]];nbytes+=len(ports)
            original=dict(registers=d.psg.state(),latch=d.psg.latch//16,saved_noise=d.mem[0xDE11],
                channels=[d.mem[a]&0xD4 for a in T.CHANNELS],priority=d.mem[0xDE0F])
            predicted=dict(registers=m.psg.snapshot(),latch=m.psg.latch,saved_noise=m.saved_noise,
                channels=m.emission_snapshot()['channel_state'],priority=m.priority)
            if ports!=m.writes:fail.append(dict(tick=tick,field='ordered-port-writes'))
            for field in original:
                if original[field]!=predicted[field]:fail.append(dict(tick=tick,field=field))
            rows.append(dict(tick=tick,original=original,predicted=predicted,ports=ports,model_ports=m.writes,
                channel_sources=[dict(id=ch.rid,age=ch.age,flags=ch.flags,waiting=ch.waiting,generation=ch.generation) for ch in m.channels],audit=m.audit))
        save(OUT/f'{name}-gate.json',dict(case=c,rows=rows,port_trace=d.port_trace,failures=fail))
        result[name]=dict(ticks=c['ticks'],ordered_bytes=nbytes,status='PASS' if not fail else 'FAIL',failures=fail)
        print(name,result[name]['status'],fail[:4],flush=True)
    save(PUBLIC/'emission-gate.json',dict(rom_sha256=T.ROM_SHA256,cases=result,
        saved_DE11_compared=True,full_registers_and_latch_compared=True,all_off_states_compared=True,
        status='PASS' if all(x['status']=='PASS' for x in result.values()) else 'HOLD',new_intrinsic_export_ids=[0x88],new_matrix_pair_captures=0))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['plan','gate']);p.add_argument('--rom');a=p.parse_args()
    plan() if a.mode=='plan' else gate(T.load_rom(a.rom))
