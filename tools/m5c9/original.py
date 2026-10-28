"""C9 original-only source/lifecycle oracles. No candidate decoder is imported."""
import argparse
from collections import Counter
import gzip
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools')]
import audio1_psg_trace as T
from m5c71.research import save,load,sha,canonical,snapshot,key,action
OUT=ROOT.parent/'private-research/m5-c9'
PUB=ROOT/'data/m5-c9'
IDS=(0x91,0x93,0x95,0x8B,0x90,0x82,0x8C,0x8D)
LIMIT=120000

def fingerprint(row):return sha(canonical({k:v for k,v in row.items() if k!='ports'}))

def capture(rom,rid,name,events=None,end=None,discover=True,writer=None):
    events=events or {};OUT.mkdir(parents=True,exist_ok=True)
    d=T.Driver(rom);ops=Counter();loops=Counter();notes=[];pending=None;reading=False;transfers=[];rows_hash=[];states=[];writes=[];seen={};rec=None;release=None;checkpoints={};admissions=[]
    def begin(q):
        nonlocal pending,reading
        reading=True;pending=dict(tick=q.update,slot=T.CHANNELS.index(q.cpu.ix),note=q.cpu.a,transpose=q.mem[q.cpu.ix+5],channel=list(q.mem[q.cpu.ix:q.cpu.ix+48]))
    def read(q):
        if reading and not 0x4436<=q.cpu.hl<0x44C2:
            assert pending is not None
            n=dict(pending,index=q.cpu.bc,address=q.cpu.hl,word=q.mem[q.cpu.hl]|q.mem[q.cpu.hl+1]<<8,source=list(q.mem[q.cpu.hl:q.cpu.hl+2]))
            notes.append(n)
    def upper(q):
        if reading and notes and notes[-1]['tick']==q.update and notes[-1]['slot']==T.CHANNELS.index(q.cpu.ix):
            notes[-1]['upper_address']=q.cpu.hl
    def stop(q):
        nonlocal reading
        if reading and notes and notes[-1]['tick']==q.update and notes[-1]['slot']==T.CHANNELS.index(q.cpu.ix):
            notes[-1]['returned_word']=q.cpu.hl
        reading=False
    def edge(q):transfers.append([q.update,T.CHANNELS.index(q.cpu.ix),q.mem[q.cpu.de]|q.mem[q.cpu.de+1]<<8])
    d.hook(0x4415,begin);d.hook(0x4422,read);d.hook(0x4424,upper);d.hook(0x4426,stop)
    d.hook(0x46D9,lambda q:ops.update([q.cpu.a]));d.hook(0x4849,lambda q:loops.update([(T.CHANNELS.index(q.cpu.ix),q.cpu.a,q.mem[q.cpu.ix+9])]))
    d.hook(0x47B4,edge);d.hook(0x481C,edge);d.hook(0x41A7,lambda q:admissions.append([q.update,q.cpu.a]))
    if writer is None:d.request(rid)
    else:
        d.mem[0xD297],d.mem[0xD298]=writer;d.mem[0xD4A3]=0;d.call(0x189B)
        assert d.mem[0xDE04]==rid and d.mem[0xD4A4]==rid
    target=end;digest=__import__('hashlib').sha256();path=OUT/(name+'-original.jsonl.gz')
    with gzip.open(path,'wb') as f:
        for t in range(1,(end or LIMIT*2)+1):
            for kind,v in events.get(t,[]):action(d,kind,v)
            start=len(d.writes);nt=len(transfers);d.tick();r=snapshot(d,start);s=sha(key(d))
            encoded=canonical(dict(row=r,state400=s,transfers=transfers[nt:]))+b'\n';f.write(encoded);digest.update(encoded)
            states.append(s);writes.append(sha(canonical(r['ports'])))
            if t%4200==0:checkpoints[str(t)]=fingerprint(r)
            if discover:
                if rid==0x8D and release is None and not d.music_active():release=t;target=t+1536
                if rec is None and release is None and s in seen:
                    a=seen[s];rec=dict(first_tick=a,repeat_tick=t,period_ticks=t-a);target=t+(t-a)
                seen.setdefault(s,t)
            if target is not None and t>=target:break
            if discover and target is None and t>=LIMIT:break
    if rec:
        a,b,p=rec['first_tick'],rec['repeat_tick'],rec['period_ticks']
        assert states[a:b]==states[b:b+p] and writes[a:b]==writes[b:b+p]
        def edges(lo):return [[t-lo,*rest] for t,*rest in transfers if lo<t<=lo+p]
        assert edges(a)==edges(b)
        rec.update(original400_state_period_exact=True,ordered_write_period_exact=True,edges_per_period=len(edges(a)),edge_sha256=sha(canonical(edges(a))))
    for n in notes:
        assert n['index']==(((n['note']&127)+n['transpose'])&255)
        assert n['address']==0x4436+2*n['index'] and n['upper_address']==n['address']+1
        assert n['word']==n['returned_word']
    h=T.header_facts(rom,rid);p=h['header_rom'];n=6+4*h['channel_count']
    programme=dict(streams=[dict(latch=int(s['latch'],16),pointer=s['stream_cpu'],transpose=s['transpose'],volume=s['volume'],flags=128) for s in h['channels']],multiplier=h['duration_multiplier'],tempo=h['tempo_byte'],source_offset=p,header_length=n,header_sha256=sha(rom[p:p+n]))
    readers=sorted({(n['slot'],n['transpose'],n['address'],n['index']) for n in notes})
    pairs={str(a):sha(rom[a+0x4000:a+0x4002]) for _,_,a,_ in readers}
    contracts=dict(programme=programme,programme_sha256=sha(canonical(programme)),readers=readers,pairs=pairs)
    save(OUT/(name+'-notes.json'),notes)
    save(OUT/(name+'-contract.json'),contracts)
    result=dict(request_id=rid,ticks=d.update,original_capture_sha256=digest.hexdigest(),original_capture_file_sha256=sha(path.read_bytes()),recurrence=rec,finite_release_tick=release,final_active_slots=[i for i,a in enumerate(T.CHANNELS) if d.mem[a]&128],final_attenuations=d.psg.att,checkpoint_fingerprints=checkpoints,header_sha256=programme['header_sha256'],programme_sha256=contracts['programme_sha256'],reader_scopes=readers,pair_hashes=pairs,note_read_count=len(notes),private_notes_sha256=sha(canonical(notes)),opcodes={f'{k:02X}':v for k,v in sorted(ops.items())},F7_scopes=[dict(slot=i,index=j,cursor=k,count=v) for (i,j,k),v in sorted(loops.items())],ordered_bytes=len(d.writes),SFX_admissions=admissions,original_only=True)
    save(PUB/(name+'.json'),result)
    print(name,'ticks',d.update,'loop',rec,'finite',release,'readers',readers,flush=True)
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('rom');p.add_argument('ids',nargs='*');a=p.parse_args();rom=T.load_rom(a.rom)
    for rid in (tuple(int(i,16) for i in a.ids) or IDS):capture(rom,rid,f'{rid:02X}-solo')

if __name__=='__main__':main()
