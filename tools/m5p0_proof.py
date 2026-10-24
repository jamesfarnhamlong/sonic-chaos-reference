"""Export PRIVATE dry event metadata, compare independent ownership model.

python tools/m5p0_proof.py PRIVATE_ROM
No PCM. Public output is aggregate assertions/failure diagnostics, not timelines.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import audio1_psg_trace as T
from m5p0_model import Model
ROOT=Path(__file__).resolve().parents[1]
PRIVATE=ROOT/'build/m5-proof'
PUBLIC=ROOT/'data/m5-proof'

def save(path,x):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def bank(rom):
    result=dict(rom_sha256=T.ROM_SHA256,priority={str(r):T.priority_byte(rom,r) for r in list(range(0x81,0xC5))+[0xF8]},programs={})
    catalogue={r['request_id']:r for r in json.loads((ROOT/'data/m5/catalogue.json').read_text())['entries']}
    for rid in range(0x81,0xC5):
        d=T.Driver(rom);h=T.header_facts(rom,rid);events=[{} for _ in range(4 if rid<0xA0 else h['stream_count'])]
        addresses=list(T.MUSIC_CH) if rid<0xA0 else [dict(A0=0xDF00,C0=0xDF30,E0=0xDF60)[s['latch'][2:].upper()] for s in h['streams']]
        def record(kind,value=0):
            ix=d.cpu.ix
            if ix in addresses:events[addresses.index(ix)].setdefault(str(d.update),[]).append([kind,value])
        d.hook(0x4341,lambda q:record('read'));d.hook(0x4650,lambda q:record('read'))
        d.hook(0x47C8,lambda q:record('f2'))
        d.hook(0x4753,lambda q:record('f3',q.mem[q.cpu.de]))
        d.hook(0x4882,lambda q:record('tempo',q.cpu.a))
        d.request(rid)
        terminal=catalogue[rid]['execution']['finite_inactive_tick']
        limit=15000 if rid in (0x81,0x82) else max(1400,(terminal or 0)+5) if rid<0xA0 else 200
        for _ in range(limit):
            d.tick()
            if not d.active(T.MUSIC_CH if rid<0xA0 else T.SFX_CH):break
        result['programs'][str(rid)]=dict(events=events,channel_count=h.get('channel_count',0),tempo=[h.get('tempo_byte',0)]*2,
            streams=[dict(latch=int(s['latch'],16),flags=rom[h['header_rom']+4+6*n]) for n,s in enumerate(h.get('streams',[]))],coverage_ticks=d.update)
    save(PRIVATE/'dry-event-bank.json',result);return result

def model_timeline(b,events,ticks):
    m=Model(b);m.direct(0x81);rows=[];previous=None
    for t in range(1,ticks+1):
        for rid in events.get(t,[]):m.direct(rid)
        m.tick();snap=m.snapshot()
        if snap!=previous:rows.append(dict(tick=t,**snap));previous=snap
    return rows

def original_transfer(d):
    # Execute the actual original IRQ prefix at its original addresses, stop
    # before mapper writes. No rewritten helper is used as the transfer oracle.
    d.cpu.set_breakpoint(0x5D6);d.cpu.pc=0x5C9
    while d.cpu.pc!=0x5D6:d.cpu.ticks_to_stop=10000;d.cpu.run()
    d.cpu.clear_breakpoint(0x5D6)

def compare_case(rom,b,music,events,ticks):
    m=Model(b);m.direct(music);d=T.Driver(rom);d.request(music)
    failures=[];recover_model=[];recover_actual=[]
    for tick in range(1,ticks+1):
        for kind,value in events.get(tick,[]):
            if kind=='request':m.direct(value);d.request(value)
            elif kind=='game':m.game(value);d.mem[0xD4A4]=value
            elif kind=='irq':m.transfer();original_transfer(d)
            elif kind=='fade':m.fade=list(value);d.mem[0xDE09:0xDE0C]=bytes(value)
            elif kind=='pause':m.paused=bool(value);d.mem[0xDE08]=128 if value else 0
            elif kind=='stop':m.stop();d.call(0x43E5);d.mem[0xD4A4]=0
            else:raise ValueError(kind)
        before=[d.mem[a] for a in T.MUSIC_CH]
        m.tick();d.tick()
        want=dict(flags=[d.mem[a]&0xC4 for a in T.CHANNELS],priority=d.mem[0xDE0F])
        if m.snapshot()!=want:failures.append(dict(tick=tick,model=m.snapshot(),original=want))
        # Match independently meaningful output-recovery events in R1 predicates.
        for ch,a in enumerate(T.MUSIC_CH):
            if before[ch]&16 and not d.mem[a]&20 and d.mem[a]&128:recover_actual.append((tick,ch))
        for kind,ch,rid,age in m.events:
            if kind=='recover' and ch<4:recover_model.append((tick,ch))
        if m.tempo!=list(d.mem[0xDE01:0xDE03]):failures.append(dict(tick=tick,field='tempo',model=m.tempo,original=list(d.mem[0xDE01:0xDE03])))
        if m.mail!=list(d.mem[0xDE04:0xDE07]):failures.append(dict(tick=tick,field='mailbox'))
        if m.fade!=list(d.mem[0xDE09:0xDE0C]):failures.append(dict(tick=tick,field='fade',model=m.fade,original=list(d.mem[0xDE09:0xDE0C])))
    return dict(ticks=ticks,failures=failures,model_recovery=recover_model,original_bit4_clear= recover_actual)

def run(rom):
    start=time.perf_counter();PRIVATE.mkdir(parents=True,exist_ok=True);b=bank(rom)
    old=json.loads((ROOT/'data/m5/interactions.json').read_text())
    failures=[];scenarios=0;compares=0
    for name,case in old['scenarios'].items():
        got=model_timeline(b,{int(k):v for k,v in case['events'].items()},case['ticks'])
        want=case['transitions'];scenarios+=1;compares+=case['ticks']*8
        if got!=want:
            first=next((i for i in range(min(len(got),len(want))) if got[i]!=want[i]),min(len(got),len(want)))
            failures.append(dict(case=name,index=first,model=got[first] if first<len(got) else None,original=want[first] if first<len(want) else None))
    arbitration=0
    for rid in list(range(0xA0,0xC5))+[0xF8]:
        for priority in range(128):
            m=Model(b);m.priority=priority;m.direct(rid);m.arbitration()
            d=T.Driver(rom);d.mem[0xDE0F]=priority;d.request(rid);d.call(0x407F)
            arbitration+=1
            if (m.selected,m.priority)!=(d.mem[0xDE03],d.mem[0xDE0F]):failures.append(dict(case='arbitration',id=rid,priority=priority))
    report=dict(rom_sha256=T.ROM_SHA256,method='independent event-driven ownership model; dry stream timing from original solo driver; combined oracle never drives model',
        status_scope='bounded ownership/dispatch projection only; complete P0 output acceptance is governed by gate.json',
        compared_fields='seven active/suppression/fixed-noise flags (maskC4), global priority; scalar arbitration selected ID/priority',
        scenarios=scenarios,scalar_comparisons=compares,arbitration_assertions=arbitration,failures=failures,
        elapsed_seconds=time.perf_counter()-start,status='PASS' if not failures else 'FAIL')
    extended={};recovery_matches=0;recovery_assertions=0
    for row in json.loads((ROOT/'data/m5/extensions.json').read_text())['recovery']:
        rid=row['id'];at=row['request_tick'];name=f'recovery-{rid:02X}-{at}'
        x=compare_case(rom,b,0x81,{at:[('request',rid)]},at+299)
        for ch in row['channels']:
            if ch['release_tick']:
                recovery_assertions+=1
                ok=(ch['recovery_tick'],ch['channel']) in x['model_recovery']
                recovery_matches+=ok
                if not ok:x['failures'].append(dict(field='recovery',expected=ch))
        extended[name]=x
    for music in (0x90,0x99,0x82,0x81):
        for rid in (0xBF,0xA6):
            for at in range(100,124):extended[f'm4-{music:02X}-{rid:02X}-{at}']=compare_case(rom,b,music,{at:[('request',rid)]},at+150)
    for music,cut,p in ((0x81,1311,2688),(0x82,1879,6912)):
        for rid in (0xBF,0xA6):
            at=cut+p-10;extended[f'wrap-{music:02X}-{rid:02X}']=compare_case(rom,b,music,{at:[('request',rid)]},at+200)
    extras={
        'staggered':(0x81,{30:[('request',0xAC)],35:[('request',0xA0)],79:[('request',0xA6)]},180),
        'fixed-noise':(0x81,{30:[('request',0xB8)],35:[('request',0xBC)]},210),
        'coupled-noise':(0x81,{30:[('request',0xBF)],35:[('request',0xA3)],51:[('request',0xBF)]},180),
        'fade-multislot':(0x81,{30:[('request',0xAC)],35:[('request',0xA0)],40:[('fade',(12,1,2))]},100),
        'terminal-fade-selection':(0x81,{35:[('fade',(12,1,2))],57:[('request',0x99)],58:[('request',0x88)]},300),
        'fade-same-tick-sfx':(0x81,{35:[('fade',(12,1,2)),('request',0xA0)]},100),
        'fade-same-tick-music':(0x81,{35:[('fade',(12,1,2)),('request',0x88)]},270),
        'deferred-zero':(0x81,{30:[('request',0xA0),('game',0),('irq',0)]},150),
        'deferred-nonzero':(0x81,{30:[('request',0xA0),('game',0xBF),('irq',0)]},150),
        'direct-zero':(0x81,{30:[('request',0xA0),('request',0),('irq',0)]},150),
        'direct-zero-deferred':(0x81,{30:[('game',0xA0),('request',0),('irq',0)]},150),
        'pause-pending':(0x81,{30:[('pause',1)],35:[('request',0xA0)],40:[('pause',0)]},150),
        'administrative-stop':(0x81,{30:[('request',0xA0)],35:[('stop',0)]},80),
        'late-finite':(0x99,{1180:[('request',0xA6)]},1300),
        'same-id-music':(0x88,{30:[('request',0x88)]},270)}
    for name,(music,ev,n) in extras.items():extended[name]=compare_case(rom,b,music,ev,n)
    for name,x in extended.items():
        failures.extend(dict(case=name,**e) for e in x['failures'])
    save(PRIVATE/'extended-comparisons.json',extended)
    report.update(extended_scenarios=len(extended),recovery_cases=111,recovery_assertions=recovery_assertions,recovery_matches=recovery_matches,
        m4_interruption_controls=192,m4_loop_controls=4,extra_controls=list(extras),
        extended_scalar_comparisons=sum(x['ticks']*16 for x in extended.values()),
        extended_compared_fields='seven flags maskedC4, priority, two tempo counters, three pending bytes, three fade counters',
        failures=failures,status='PASS' if not failures else 'FAIL',elapsed_seconds=time.perf_counter()-start)
    save(PUBLIC/'p0-result.json',report);print(json.dumps(dict(status=report['status'],failures=len(failures),first=failures[:5],seconds=report['elapsed_seconds']),indent=2))
    return b,report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('rom');a=p.parse_args();run(T.load_rom(a.rom))
