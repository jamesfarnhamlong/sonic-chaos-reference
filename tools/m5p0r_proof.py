"""Focused P0R dry-intent export and exact original-versus-model emission gate.

New traces and dry intents are PRIVATE below build/m5-p0r. Public output keeps
only counts, failures, bounded blocker facts and source hashes, never streams.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import time
import audio1_psg_trace as T
from m5p0r_probe import Trace,OUT,PRIOR,capture
from m5p0r_emission import EmissionModel
ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'data/m5-p0r'

def save(path,x):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')

class Dry(Trace):
    def _out(self,port,value):
        if port&255 in (0x7E,0x7F) and self.cpu.pc in (0x451E,0x4528,0x46D4):
            self.record('music-noise-control' if self.cpu.pc==0x46D4 else 'port',value if self.cpu.pc==0x46D4 else [value,self.cpu.ix in self.read_channels])
        super()._out(port,value)

def export(rom):
    bank=copy.deepcopy(json.loads((PRIOR/'dry-event-bank.json').read_text()))
    ids=list(range(0xA0,0xC5))+[0x81,0x82,0x90,0x99]
    for rid in ids:
        d=Dry(rom);h=T.header_facts(rom,rid);old=bank['programs'][str(rid)]
        addresses=list(T.MUSIC_CH) if rid<0xA0 else [{0xA0:0xDF00,0xC0:0xDF30,0xE0:0xDF60}[int(s['latch'],16)] for s in h['streams']]
        events=[{} for _ in addresses];epochs=[0]*len(addresses);sequences=[{} for _ in addresses];inside={}
        d.read_channels=set()
        def record(kind,value=0):
            if d.cpu.ix in addresses:events[addresses.index(d.cpu.ix)].setdefault(str(d.update),[]).append([kind,value])
        d.record=record
        def on_read(q):d.read_channels.add(q.cpu.ix);record('read')
        d.hook(0x4341,on_read);d.hook(0x4650,on_read)
        for pc,kind in ((0x47C8,'f2'),):
            d.hook(pc,lambda q,k=kind:record(k))
        def epoch(q):
            if q.cpu.ix in addresses:
                i=addresses.index(q.cpu.ix);epochs[i]+=1;record('envelope-epoch',epochs[i])
        d.hook(0x43BE,epoch);d.hook(0x42A3,epoch)
        def envelope(q):
            if q.cpu.ix not in addresses:return
            i=addresses.index(q.cpu.ix);ep=str(epochs[i]);step={}
            sequences[i].setdefault(ep,[]).append(step);inside[q.cpu.ix]=step;record('envelope-step',epochs[i])
        def envelope_done(q):
            if q.cpu.ix in inside:
                inside.pop(q.cpu.ix).update(value=q.cpu.a,inhibit=bool(q.mem[q.cpu.ix]&16))
        def off(q):
            if q.cpu.ix in inside:inside[q.cpu.ix].update(off=True,inhibit=True)
            else:record('off')
        def inhibit(q):
            if q.cpu.ix in inside:inside[q.cpu.ix]['inhibit']=True
            else:record('inhibit')
        d.hook(0x4546,envelope);d.hook(0x452B,envelope_done);d.hook(0x4639,off);d.hook(0x462F,inhibit)
        d.hook(0x4753,lambda q:record('f3',q.mem[q.cpu.de]))
        d.hook(0x4882,lambda q:record('tempo',q.cpu.a))
        d.hook(0x4535,lambda q:record('attenuation',q.cpu.a))
        d.hook(0x4366,lambda q:record('volume-absolute',q.mem[q.cpu.ix+6]))
        d.hook(0x4734,lambda q:record('volume-relative',q.cpu.a))
        d.hook(0x46C6,lambda q:record('volume-absolute',q.mem[q.cpu.ix+6]))
        d.request(rid);limit=1400 if rid<0xA0 else 200
        for _ in range(limit):
            d.read_channels.clear()
            d.tick()
            inside.clear()
            if not d.active(T.MUSIC_CH if rid<0xA0 else T.SFX_CH):break
        old.update(events=events,coverage_ticks=d.update,envelope_sequences=sequences,initial_volumes=[s['volume'] for s in h.get('channels',h.get('streams',[]))])
    bank['emission_coverage_ids']=ids
    save(OUT/'dry-emission-bank.json',bank);return bank

CASES={
 'B8-BC':{30:[('request',0xB8)],35:[('request',0xBC)]},
 'BC-B8':{30:[('request',0xBC)],35:[('request',0xB8)]},
 'B6-A0':{30:[('request',0xB6)],35:[('request',0xA0)]},
 'BA-partial':{30:[('request',0xBA)],36:[('request',0xAC)]},
 'BF-A3':{30:[('request',0xBF)],35:[('request',0xA3)]},
 'A3-BF':{30:[('request',0xA3)],35:[('request',0xBF)]},
 'AC-A0':{30:[('request',0xAC)],35:[('request',0xA0)]},
 'B6-noise-release':{30:[('request',0xB6)]},
 'explicit-F8':{30:[('request',0xBF)],35:[('request',0xF8)]},
 'fade-multiple':{30:[('request',0xAC)],35:[('request',0xA0)],40:[('fade',(12,1,2))]}}

def compare(rom,bank,events,ticks=210,music=0x81,private_name=None):
    d=Trace(rom);d.request(music);m=EmissionModel(bank);m.direct(music)
    failures=[];rows=[];writes=0
    for tick in range(1,ticks+1):
        for kind,value in events.get(tick,[]):
            if kind=='request':d.request(value);m.direct(value)
            elif kind=='fade':d.mem[0xDE09:0xDE0C]=bytes(value);m.fade=list(value)
        start=len(d.writes);d.tick();m.tick();actual=[b for _,b in d.writes[start:]];writes+=len(actual)
        physical=d.psg.state();projected=m.psg.snapshot()
        channel=[d.mem[a]&0xD4 for a in T.CHANNELS];state=m.emission_snapshot()
        if actual!=m.writes:failures.append(dict(tick=tick,field='ordered-port-bytes',original=actual,model=m.writes))
        if physical!=projected:failures.append(dict(tick=tick,field='complete-registers',original=physical,model=projected))
        if d.psg.latch//16!=m.psg.latch:failures.append(dict(tick=tick,field='PSG-latch',original=d.psg.latch//16,model=m.psg.latch))
        if channel!=state['channel_state']:failures.append(dict(tick=tick,field='active-suppression-inhibit-fixed',original=channel,model=state['channel_state']))
        if d.mem[0xDE0F]!=m.priority:failures.append(dict(tick=tick,field='priority'))
        rows.append(dict(tick=tick,original=physical,model=projected,ports=actual,emitted=m.writes,channels=channel,audit=m.audit))
    if private_name:save(OUT/f'{private_name}-comparison.json',dict(events=events,rows=rows,ports=d.port_trace,failures=failures))
    return dict(ticks=ticks,ordered_port_bytes=writes,failures=failures,status='PASS' if not failures else 'FAIL')

def run(rom):
    start=time.perf_counter();OUT.mkdir(parents=True,exist_ok=True);bank=export(rom)
    results={name:compare(rom,bank,events,private_name=name) for name,events in CASES.items()}
    results['B6-solo-context']=compare(rom,bank,{},ticks=70,music=0xB6,private_name='B6-solo-context')
    results['B8-matched-entry']=compare(rom,bank,{6:[('request',0xBC)]},ticks=159,music=0xB8,private_name='B8-matched-entry')
    # Reuse the accepted combined ownership observations; no1369 pair recapture.
    cached=json.loads((ROOT/'data/m5/interactions.json').read_text());state_failures=[]
    for name,case in cached['scenarios'].items():
        m=EmissionModel(bank);m.direct(0x81);previous=None;observed=[]
        for tick in range(1,case['ticks']+1):
            for rid in case['events'].get(str(tick),[]):m.direct(rid)
            m.tick();state=m.snapshot()
            if state!=previous:observed.append(dict(tick=tick,**state));previous=state
        if observed!=case['transitions']:state_failures.append(name)
    recovery=json.loads((ROOT/'data/m5/extensions.json').read_text())['recovery'];matched=0;total=0;recovery_failures=[]
    for row in recovery:
        m=EmissionModel(bank);m.direct(0x81);got=[]
        for tick in range(1,row['request_tick']+300):
            if tick==row['request_tick']:m.direct(row['id'])
            m.tick()
            got.extend((tick,ch) for kind,ch,rid,age in m.events if kind=='recover' and ch<4)
        for ch in row['channels']:
            if ch['release_tick']:
                total+=1;ok=(ch['recovery_tick'],ch['channel']) in got;matched+=ok
                if not ok:recovery_failures.append(dict(id=row['id'],request_tick=row['request_tick'],channel=ch['channel']))
    report=dict(rom_sha256=T.ROM_SHA256,scope='private dry intrinsic intents; independent combined emission/latch state; no PCM',
        cases=results,focused_original_cases=len(results),cached_ownership_cases=len(cached['scenarios']),cached_ownership_failures=state_failures,new_full_matrix_pair_captures=0,
        recovery_cases=len(recovery),recovery_facts=total,recovery_matches=matched,recovery_failures=recovery_failures,
        status='PASS' if all(x['status']=='PASS' for x in results.values()) and not state_failures and not recovery_failures else 'FAIL',seconds=time.perf_counter()-start)
    # Future failures must not leak reconstructive port streams into Research.
    safe=copy.deepcopy(report)
    for result in safe['cases'].values():
        result['failures']=[dict(tick=f['tick'],field=f['field'],
            original_sha256=hashlib.sha256(json.dumps(f.get('original')).encode()).hexdigest(),
            model_sha256=hashlib.sha256(json.dumps(f.get('model')).encode()).hexdigest()) for f in result['failures']]
    save(PUBLIC/'emission-results.json',safe)
    print(json.dumps({k:dict(status=v['status'],failures=len(v['failures']),first=v['failures'][:2]) for k,v in results.items()},indent=2))
    return bank,report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('rom');a=p.parse_args();run(T.load_rom(a.rom))
