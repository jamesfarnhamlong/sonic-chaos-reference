"""Original-first exact interaction continuation certificates; private captures only.

Certificates qualify exact schedules/banks, never arbitrary event phases.
No old solo certificate, reader relaxation or physical PSG reset is used.
"""
import argparse
import gzip
import hashlib
import json
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2'),str(ROOT/'tools/m5a0')]
from m5g1r import canonical,sha,load,save
from m5c9.runtime import state,fingerprint
from m5a2.decoder import DecodeError
OUT=ROOT.parent/'private-research/m5-g1r2'
PUB=ROOT/'data/m5-g1r2'
BASE=ROOT.parent/'private-research/m5-g1r'
DLL=ROOT.parent/'sonic-chaos-reference-m5-a1l/build/m5-a1l/psg-a1l.dll'

def schedules():
    out={}
    for rid in (0x83,0x93,0x8F):
        for effect in (0xBF,0xA6,0xC4):
            for phase in (30,211):
                out[f'{rid:02X}-{effect:02X}-{phase}']=dict(initial=rid,events={str(phase):[['request',effect]]})
        out[f'{rid:02X}-competing']=dict(initial=rid,events={'30':[['request',0xBF]],'35':[['request',0xA6]],'36':[['request',0xC4]],'211':[['request',0xBF]],'4190':[['request',0xA6]],'4300':[['request',0xC4]]})
        out[f'{rid:02X}-epoch']=dict(initial=rid,events={'30':[['request',0xA6]],'250':[['request',rid]],'451':[['request',0xBF]]})
    out['8F-clock']=dict(initial=0x8F,events={'30':[['request',0xF8]],**{str(30+60*i):[['request',0xB5]] for i in range(1,11)},'690':[['request',0x8F]],'901':[['request',0xBF]]})
    return out

def bounded(bank,rid):
    if rid==0x83:from m5c71r83.contract import Decoder
    elif rid==0x93:from m5c9.contract import Decoder
    else:from m5a2c2.decoder import Decoder
    return Decoder

def bank(rid):
    blob=(BASE/f'{rid:02X}.scsp').read_bytes()
    if rid==0x83:from m5c71r83.contract import unpack
    elif rid==0x93:from m5c9.contract import unpack
    else:from m5a2.bank import unpack
    return unpack(blob)

def original(rompath,prefix=''):
    import audio1_psg_trace as T
    from m5c71.research import snapshot,key
    rom=T.load_rom(rompath);OUT.mkdir(parents=True,exist_ok=True)
    for name,s in schedules().items():
        if not name.startswith(prefix):continue
        d=T.Driver(rom);d.request(s['initial']);seen={};states=[];writes=[];edges=[];rec=None;checkpoints={};epochs=[];admissions=[];releases=[];suppressed=set();progress=set();previous=None;target=None
        d.hook(0x41A7,lambda q:admissions.append([q.update,q.cpu.a]))
        d.hook(0x43E5,lambda q:epochs.append(q.update))
        d.hook(0x47C8,lambda q:releases.append([q.update,T.CHANNELS.index(q.cpu.ix)]))
        def edge(q):edges.append([q.update,T.CHANNELS.index(q.cpu.ix),q.mem[q.cpu.de]|q.mem[q.cpu.de+1]<<8])
        d.hook(0x47B4,edge);d.hook(0x481C,edge)
        last=max(map(int,s['events']));digest=hashlib.sha256()
        with gzip.open(OUT/(name+'-original.jsonl.gz'),'wb') as f:
            for t in range(1,24001):
                for kind,v in s['events'].get(str(t),[]):
                    assert kind=='request';d.request(v)
                start=len(d.writes);ne=len(edges);d.tick();r=snapshot(d,start);k=sha(key(d))
                # Reconstructing all400 independently catches omitted nonzero RAM.
                from m5g1r_evidence import fullkey
                assert fullkey(r)==k
                row=dict(row=r,state400=k,transfers=edges[ne:]);encoded=canonical(row)+b'\n';f.write(encoded);digest.update(encoded)
                states.append(k);writes.append(sha(canonical(r['ports'])))
                suppressed.update(i for i,c in enumerate(r['channels'][:4]) if c&4)
                if previous:
                    progress.update(i for i in range(4) if r['channel_bytes'][i][2:5]!=previous['channel_bytes'][i][2:5])
                previous=r
                if t%4200==0:checkpoints[str(t)]=sha(canonical({a:b for a,b in r.items() if a!='ports'}))
                if t>last and rec is None:
                    if k in seen:
                        a=seen[k];rec=dict(first_tick=a,repeat_tick=t,period_ticks=t-a,state400_sha256=k,fingerprint=sha(canonical({a:b for a,b in r.items() if a!='ports'})))
                        target=max(8401,t+2*(t-a))
                    seen.setdefault(k,t)
                if target and t>=target:break
        assert rec is not None,(name,'no recurrence within search')
        a,b,p=rec['first_tick'],rec['repeat_tick'],rec['period_ticks']
        assert states[a:b]==states[b:b+p] and writes[a:b]==writes[b:b+p]
        def period_edges(lo):return [[tick-lo,*rest] for tick,*rest in edges if lo<tick<=lo+p]
        assert period_edges(a)==period_edges(b)
        music_epochs=[[1,s['initial']]]+[[int(tick),rid] for tick,actions in s['events'].items() for kind,rid in actions if 0x80<rid<0xA0 and int(tick) in epochs]
        cert=dict(schedule=s,bank_canonical_sha256=sha(canonical(bank(s['initial']))),recurrence=rec,checkpoints=checkpoints,ticks=t,original_capture_sha256=digest.hexdigest(),ROM_sha256=T.ROM_SHA256,original_state_write_transfer_period_exact=True,admissions=admissions,reset_ticks=epochs,accepted_music_epochs=music_epochs,release_events=releases,suppressed_music_slots=sorted(suppressed),progressing_music_slots=sorted(progress),state400_shadow_ticks=t)
        save(PUB/(name+'.json'),cert);print(name,'original frozen',t,'period',p,flush=True)

class Capability:
    """Wrap unchanged bounded engine. Proof position can move; state never does."""
    def __init__(self,name):
        self.cert=load(PUB/(name+'.json'));self.schedule=self.cert['schedule'];self.bank=bank(self.schedule['initial'])
        if sha(canonical(self.bank))!=self.cert['bank_canonical_sha256']:raise DecodeError('interaction bank mismatch')
        owner=self
        class Observed(bounded(self.bank,self.schedule['initial'])):
            def init(self,rid):
                result=super().init(rid)
                if rid<0xA0:owner.epochs.append([owner.absolute+1,rid])
                return result
        self.m=Observed(self.bank)
        if self.m.limit!=4200:raise DecodeError('requires unchanged4200 engine')
        self.absolute=self.position=self.renewals=self.extensions=0;self.pending=[];self.epochs=[]
        self.m.direct(self.schedule['initial'])
    def request(self,rid):self.pending.append(['request',rid])
    def tick(self):
        expected=self.schedule['events'].get(str(self.absolute+1),[]) if self.renewals==0 else []
        if self.pending!=expected:raise DecodeError('unqualified host action/phase')
        rec=self.cert['recurrence']
        if self.position==rec['repeat_tick']:
            if fingerprint(self.m)!=rec['fingerprint']:raise DecodeError('interaction recurrence state mismatch')
            self.position=rec['first_tick'];self.renewals+=1
        if self.position and self.position%4200==0:
            if fingerprint(self.m)!=self.cert['checkpoints'].get(str(self.position)):raise DecodeError('interaction checkpoint mismatch')
            self.extensions+=1
        for kind,rid in self.pending:self.m.direct(rid)
        self.pending=[]
        # Only an original-frozen exact checkpoint/recurrence permits the next
        # bounded engine window. Absolute sample/PSG clocks are never rewound.
        self.m.tick_number=self.position%4200;n=len(self.m.loops)
        self.m.tick();self.position+=1;self.absolute+=1;self.m.tick_number=self.absolute
        for j in range(n,len(self.m.loops)):
            _,i,p,q=self.m.loops[j];self.m.loops[j]=(self.absolute,i,p,q)
        if len(self.m.loops)>64:del self.m.loops[:-64]

def candidate(name,compare=True):
    from backend import PSG
    import numpy as np
    cap=Capability(name);cert=cap.cert;s=cap.schedule;pcm=hashlib.sha256();native=hashlib.sha256();emission=hashlib.sha256();capture=hashlib.sha256();count=0
    assert sha(DLL.read_bytes())=='47e15c47e255900b819847e0ddefd7e3f0751dcc8f75dff3a1690f7e76adcf65'
    oracle=gzip.open(OUT/(name+'-original.jsonl.gz'),'rt') if compare else None
    with PSG(DLL) as chip,PSG(DLL) as ref,PSG(DLL) as split:
        for t in range(1,cert['ticks']+1):
            for kind,rid in s['events'].get(str(t),[]):cap.request(rid)
            cap.tick();r=state(cap.m)
            if compare:
                o=json.loads(next(oracle));capture.update(canonical(o)+b'\n')
                assert canonical(r)==canonical(o['row']),(name,t,'state/PSG')
                actual=[[tick,i,q] for tick,i,p,q in cap.m.loops if tick==t]
                assert actual==o['transfers'],(name,t,'transfers')
            chip.write(r['ports']);split.write(r['ports']);before=chip.state();a=chip.render();c=np.concatenate([split.render(100),split.render(635)])
            assert np.array_equal(a,c) and chip.state()==split.state(),(name,t,'partition')
            if compare:
                ref.write(o['row']['ports']);assert before==ref.state();b=ref.render()
                assert np.array_equal(a,b) and chip.state()==ref.state(),(name,t,'continuous PCM/native')
            pcm.update(a.tobytes());native.update(canonical([before,chip.state()]));emission.update(canonical(r));count=t
    if oracle:
        oracle.close();assert capture.hexdigest()==cert['original_capture_sha256']
    assert cap.renewals>=1 and cap.epochs==cert['accepted_music_epochs']
    return dict(ticks=count,samples=count*735,PCM_sha256=pcm.hexdigest(),native_sha256=native.hexdigest(),state_PSG_sha256=emission.hexdigest(),renewals=cap.renewals,extensions=cap.extensions)

def negatives():
    import copy
    results={}
    def rejected(name,fn):
        try:fn()
        except DecodeError as e:results[name]=dict(detected=True,reason=str(e))
        else:raise AssertionError('missed negative '+name)
    for rid in (0x83,0x93,0x8F):
        name=f'{rid:02X}-BF-30'
        def advance(cap,end):
            while cap.absolute<end:
                for kind,v in cap.schedule['events'].get(str(cap.absolute+1),[]):cap.request(v)
                cap.tick()
        cap=Capability(name);cap.request(0xBF);rejected(f'{rid:02X}-wrong-phase',cap.tick)
        cap=Capability(name);advance(cap,29);rejected(f'{rid:02X}-missing-event',cap.tick)
        cap=Capability(name);advance(cap,29);cap.request(0xA6);rejected(f'{rid:02X}-wrong-ID',cap.tick)
        cap=Capability(name);advance(cap,31);cap.request(0xBF);rejected(f'{rid:02X}-extra-event',cap.tick)
        cap=Capability(name);advance(cap,4200 if rid==0x93 else cap.cert['recurrence']['repeat_tick'])
        for label,mutate in [('channel',lambda m:m.ch[0].__setitem__(3,m.ch[0][3]^1)),('IY',lambda m:setattr(m,'iy',m.iy^1)),('priority',lambda m:setattr(m,'priority',m.priority^1)),('latch',lambda m:setattr(m.psg,'latch',m.psg.latch^1))]:
            broken=copy.deepcopy(cap);mutate(broken.m);rejected(f'{rid:02X}-{label}-boundary-corruption',broken.tick)
        broken=Capability(name);broken.cert['bank_canonical_sha256']='0'*64
        # Construction bank substitution is checked before engine creation.
        original_bank=globals()['bank']
        def mutated_bank(request):
            b=original_bank(request);b['priority']['191']^=1;return b
        try:
            globals()['bank']=mutated_bank;rejected(f'{rid:02X}-changed-bank',lambda:Capability(name))
        finally:globals()['bank']=original_bank
    save(PUB/'negatives.json',results);print(len(results),'negatives caught',flush=True)

def verify(prefix=''):
    from m5c71r83.pcm import GUARD
    for name in schedules():
        if not name.startswith(prefix):continue
        r=candidate(name);target=OUT/(name+'-isolated.json')
        guard=GUARD.replace("'-original.json'","'-original.json', '-original.jsonl.gz'")
        proc=subprocess.run([sys.executable,'-c',guard,str(Path(__file__).resolve()),'isolated',name,str(target)],capture_output=True,text=True)
        if proc.returncode:raise RuntimeError(proc.stderr)
        assert r==load(target)
        save(PUB/(name+'-verified.json'),dict(r,status='PASS',isolated_exact=True,access_guards_tested=3,state_PSG_transfer_PCM_native_partition_mismatches=0,A1L_sha256='47e15c47e255900b819847e0ddefd7e3f0751dcc8f75dff3a1690f7e76adcf65',physical_PSG_resets_at_events_checkpoints_recurrences=0))
        print(name,'gated continuous state/PSG/PCM PASS',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['original','verify','isolated','negatives']);p.add_argument('args',nargs='*');a=p.parse_args()
    if a.mode=='original':original(*a.args)
    elif a.mode=='verify':verify(*a.args)
    elif a.mode=='negatives':negatives()
    else:save(Path(a.args[1]),candidate(a.args[0],False))
