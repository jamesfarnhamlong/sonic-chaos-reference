"""Original-first bounded interaction research. Captures and banks stay private.

No continuation implementation: every candidate uses the unchanged 4200 bound.
"""
import argparse
import gzip
import hashlib
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2'),str(ROOT/'tools/m5a0')]
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def sha(x):return hashlib.sha256(x).hexdigest()
def load(p):return json.loads(p.read_text())
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
PRIVATE=ROOT.parent/'private-research'
OUT=PRIVATE/'m5-g1r'
PUB=ROOT/'data/m5-g1r'
MUSIC=(0x81,0x83,0x91,0x92,0x93,0x95,0x90,0x8F,0x8B,0x8C)

def cases():
    r={}
    def add(name,rid,events,end,group):r[name]=dict(initial=rid,events={str(t):v for t,v in events.items()},ticks=end,group=group)
    for rid in MUSIC:
        for effect in (0xBF,0xA6,0xA3,0xB8,0xBA,0xB4):
            for phase in (30,211):
                add(f'{rid:02X}-{effect:02X}-{phase}',rid,{phase:[['request',effect]]},550,'steal-recover')
        add(f'{rid:02X}-multi',rid,{30:[['request',0xBF]],35:[['request',0xA3]],60:[['request',0xB4]],100:[['request',0xBA]],150:[['request',0xC4]]},550,'arbitration')
        add(f'{rid:02X}-death-card',rid,{30:[['request',0xBA]],35:[['request',0x96]],200:[['request',0x88]],400:[['request',rid]]},700,'replacement')
        add(f'{rid:02X}-power',rid,{30:[['request',0x84]],100:[['request',0xBF]],631:[['request',rid]],700:[['request',0x85]],1001:[['request',rid]]},1400,'power-restart')
        add(f'{rid:02X}-fade',rid,{30:[['request',0xBA]],35:[['fade',[12,1,2]]],100:[['request',rid]],200:[['request',0xF8]],250:[['request',rid]]},550,'fade-reset')
        add(f'{rid:02X}-same',rid,{30:[['request',0xBA]],35:[['request',rid]]},550,'same-restart')
        add(f'clear-{rid:02X}',rid,{30:[['request',0xBF]],100:[['request',0x89]],250:[['request',0x97]],450:[['request',rid]]},750,'clear-replacement')
        add(f'zone-{rid:02X}',rid,{100:[['request',0x81]],300:[['request',rid]]},750,'zone-replacement')
    add('8F-clock',0x8F,{30:[['request',0xF8]],**{30+60*i:[['request',0xB5]] for i in range(1,11)},690:[['request',0x8F]]},1100,'clock')
    add('8F-success',0x8F,{300:[['request',0x8A]],500:[['request',0x86]]},1200,'SS-success')
    add('8F-failure',0x8F,{300:[['fade',[12,1,2]]]},650,'SS-failure')
    add('81-terminal-fade-selection',0x81,{35:[['fade',[12,1,2]]],57:[['request',0x99]]},150,'fade-boundary')
    add('81-fade-dispatch',0x81,{35:[['fade',[12,1,2]],['request',0x84]]},250,'fade-boundary')
    add('81-F8-blocked',0x81,{30:[['request',0xA3]],31:[['request',0xF8]]},250,'reset-priority')
    add('81-mail-overwrite',0x81,{30:[['request',0xBF],['request',0xA9]]},250,'mailbox')
    add('81-zero-cancel',0x81,{30:[['request',0xBF],['request',0]]},250,'mailbox')
    add('81-aux-order',0x81,{30:[['mail',[0xBF,0xA6,0xA3]]]},250,'controlled-aux-mailboxes')
    if (PUB/'writer-schedules.json').exists():r.update(load(PUB/'writer-schedules.json'))
    return r

def original(path,prefix=''):
    import audio1_psg_trace as T
    from m5c71.research import snapshot,key
    rom=T.load_rom(path);OUT.mkdir(parents=True,exist_ok=True);reports=load(PUB/'original.json')['cases'] if prefix else {}
    for name,s in cases().items():
        if not name.startswith(prefix):continue
        d=T.Driver(rom);d.request(s['initial']);reads=[];admit=[];resets=[];transfers=[];release=[]
        d.hook(0x4341,lambda q:reads.append([q.update,T.CHANNELS.index(q.cpu.ix)]))
        d.hook(0x4650,lambda q:reads.append([q.update,T.CHANNELS.index(q.cpu.ix)]))
        d.hook(0x41A7,lambda q:admit.append([q.update,q.cpu.a]))
        d.hook(0x43E5,lambda q:resets.append(q.update))
        d.hook(0x47C8,lambda q:release.append([q.update,T.CHANNELS.index(q.cpu.ix)]))
        def edge(q):transfers.append([q.update,T.CHANNELS.index(q.cpu.ix),q.mem[q.cpu.de]|q.mem[q.cpu.de+1]<<8])
        d.hook(0x47B4,edge);d.hook(0x481C,edge)
        digest=hashlib.sha256();recovery=[];pending={};suppressed=set();active=set();nports=0
        with gzip.open(OUT/(name+'-original.jsonl.gz'),'wb') as f:
            for t in range(1,s['ticks']+1):
                for k,v in s['events'].get(str(t),[]):
                    if k=='request':d.request(v)
                    elif k=='fade':d.mem[0xDE09:0xDE0C]=bytes(v)
                    elif k=='mail':d.mem[0xDE04:0xDE07]=bytes(v)
                    else:raise ValueError(k)
                start=len(d.writes);nt=len(transfers);nr=len(reads);before=[d.mem[a] for a in T.CHANNELS];d.tick();row=snapshot(d,start)
                if resets and resets[-1]==t:pending.clear()
                for i,c in enumerate(row['channels']):
                    if c&4:suppressed.add(i)
                    if c&128:active.add(i)
                    if i<4 and before[i]&4 and not c&4 and not (resets and resets[-1]==t):pending[i]=t
                for _,i in reads[nr:]:
                    if i in pending:
                        recovery.append(dict(slot=i,suppression_clear_tick=pending.pop(i),eligible_reader_tick=t,flags_after=d.mem[T.CHANNELS[i]]&0xD4))
                item=dict(row=row,state400=sha(key(d)),transfers=transfers[nt:]);b=canonical(item)+b'\n';f.write(b);digest.update(b);nports+=len(row['ports'])
        reports[name]=dict(ticks=s['ticks'],group=s['group'],capture_sha256=digest.hexdigest(),ordered_bytes=nports,SFX_admissions=admit,reset_ticks=resets,release_events=release,recovery=recovery,active_slots=sorted(active),suppressed_slots=sorted(suppressed),final_active_slots=[i for i,a in enumerate(T.CHANNELS) if d.mem[a]&128],final_priority=d.mem[0xDE0F],final_attenuations=d.psg.att)
        print(name,'original frozen',flush=True)
    save(PUB/'original.json',dict(ROM_sha256=T.ROM_SHA256,cases=reports,natural_gameplay=False))
    save(OUT/'schedules.json',cases())

def bank_for(rid):
    from m5a2.bank import unpack as legacy
    from m5c9.contract import unpack as c9
    from m5c71r83.contract import unpack as r83
    if rid in (0x91,0x93,0x95,0x90,0x8B,0x8C):p=PRIVATE/'m5-c9'/f'{rid:02X}.scsp';return p,c9(p.read_bytes()),'c9'
    if rid==0x83:p=PRIVATE/'m5-c7-1r83/programs.scsp';return p,r83(p.read_bytes()),'r83'
    if rid==0x92:p=PRIVATE/'m5-c7-batch/92.scsp';return p,legacy(p.read_bytes()),'92'
    if rid==0x8F:p=PRIVATE/'m5-c7-batch/82-8B-8C-8D-8F-90.scsp';return p,legacy(p.read_bytes()),'legacy'
    p=PRIVATE/'m5-a2c6/programs.scsp';return p,legacy(p.read_bytes()),'legacy'

def prepare():
    # Exact compatible union of previously authenticated private records only.
    # New hashes have NO solo continuation capability. Ordinary bound unchanged.
    from m5a2.bank import unpack,pack
    supplement=PRIVATE/'m5-c7-batch/A8-AB-AD-AE-B2-B3-B5-C0-C1-C3-BB-BE-C4.scsp'
    extra=unpack(supplement.read_bytes());manifest={}
    for rid in MUSIC:
        source,b,kind=bank_for(rid)
        for field in ('programs','data','priority'):
            for k,v in extra[field].items():
                if k in b[field]:assert b[field][k]==v,(field,k)
                else:b[field][k]=v
        blob=pack(b);p=OUT/f'{rid:02X}.scsp';p.write_bytes(blob)
        manifest[f'{rid:02X}']=dict(source=source.name,source_sha256=sha(source.read_bytes()),supplement_sha256=sha(supplement.read_bytes()),bank_sha256=sha(blob),kind=kind,continuation_authorised=False)
    save(PUB/'banks.json',manifest)

def candidate(name,s,dll,compare=True):
    from backend import PSG
    import numpy as np
    from m5c9.runtime import state
    from m5a2.bank import unpack
    kind=load(PUB/'banks.json')[f'{s["initial"]:02X}']['kind']
    if kind=='c9':from m5c9.contract import unpack,Decoder
    elif kind=='r83':from m5c71r83.contract import unpack,Decoder
    elif kind=='92':from m5c7batch.alias92 import Decoder
    else:from m5a2c2.decoder import Decoder
    blob=(OUT/f'{s["initial"]:02X}.scsp').read_bytes();assert sha(blob)==load(PUB/'banks.json')[f'{s["initial"]:02X}']['bank_sha256']
    m=Decoder(unpack(blob));assert m.limit==4200;m.direct(s['initial'])
    pcm=hashlib.sha256();native=hashlib.sha256();emission=hashlib.sha256();captured=hashlib.sha256();bad=[];samplebad=nativebad=partitionbad=0;count=0
    oracle=gzip.open(OUT/(name+'-original.jsonl.gz'),'rt') if compare else None
    with PSG(dll) as chip,PSG(dll) as ref,PSG(dll) as split:
        for t in range(1,s['ticks']+1):
            for k,v in s['events'].get(str(t),[]):
                if k=='request':
                    if v:m.direct(v)
                    else:m.mail[0]=0  # original direct-zero cancellation; not a sound ID
                elif k=='fade':m.fade=list(v)
                elif k=='mail':m.mail=list(v)
                else:raise ValueError(k)
            ne=len(m.loops);m.tick();r=state(m);edges=[[a,i,q] for a,i,p,q in m.loops[ne:]];o=json.loads(next(oracle)) if compare else None
            if compare:
                captured.update(canonical(o)+b'\n')
                for k,v in o['row'].items():
                    if canonical(r[k])!=canonical(v):bad.append(dict(tick=t,field=k))
                if edges!=o['transfers']:bad.append(dict(tick=t,field='transfers'))
            emission.update(canonical(r));chip.write(r['ports']);split.write(r['ports']);before=chip.state();a=chip.render();c=np.concatenate([split.render(100),split.render(635)])
            partitionbad+=not np.array_equal(a,c) or chip.state()!=split.state()
            if compare:
                ref.write(o['row']['ports']);refbefore=ref.state();b=ref.render();samplebad+=int(np.count_nonzero(a!=b));nativebad+=before!=refbefore or chip.state()!=ref.state()
            pcm.update(a.tobytes());native.update(canonical([before,chip.state()]));count=t
    if oracle:oracle.close()
    assert not bad and not samplebad and not nativebad and not partitionbad,(name,bad[:3],samplebad,nativebad,partitionbad)
    receipt=dict(ticks=count,samples=count*735,PCM_sha256=pcm.hexdigest(),native_sha256=native.hexdigest(),state_PSG_sha256=emission.hexdigest(),partition_mismatches=partitionbad)
    if compare:
        assert captured.hexdigest()==load(PUB/'original.json')['cases'][name]['capture_sha256']
        receipt.update(state_PSG_transfer_mismatches=len(bad),PCM_mismatches=samplebad,native_mismatching_ticks=nativebad,original_capture_sha256=captured.hexdigest(),status='PASS')
    return receipt

def verify(prefix=''):
    from m5c71r83.pcm import DLL,GUARD
    import subprocess
    assert sha(DLL.read_bytes())=='47e15c47e255900b819847e0ddefd7e3f0751dcc8f75dff3a1690f7e76adcf65'
    reports=load(PUB/'verified.json')['cases'] if prefix else {}
    for name,s in cases().items():
        if not name.startswith(prefix):continue
        r=candidate(name,s,DLL)
        target=OUT/(name+'-isolated.json')
        guard=GUARD.replace("'-original.json'","'-original.json', '-original.jsonl.gz'")
        proc=subprocess.run([sys.executable,'-c',guard,str(Path(__file__).resolve()),'isolated',name,str(DLL),str(target)],capture_output=True,text=True)
        if proc.returncode:raise RuntimeError(proc.stderr)
        isolated=load(target);assert all(r[k]==v for k,v in isolated.items());r['isolated_exact']=True;r['access_guards_tested']=3
        reports[name]=r;save(PUB/'verified.json',dict(A1L_sha256=sha(DLL.read_bytes()),cases=reports));print(name,'state/PSG/PCM/isolation PASS',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['original','prepare','verify','isolated']);p.add_argument('args',nargs='*');a=p.parse_args()
    if a.mode=='original':original(a.args[0],a.args[1] if len(a.args)>1 else '')
    elif a.mode=='prepare':prepare()
    elif a.mode=='verify':verify(a.args[0] if a.args else '')
    else:save(Path(a.args[2]),candidate(a.args[0],cases()[a.args[0]],a.args[1],False))
