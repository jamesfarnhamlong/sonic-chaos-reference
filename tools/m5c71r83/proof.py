"""Original-first one-ID oracle, extraction and exact independent comparisons."""
import argparse
from collections import Counter
import copy
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2')]
import audio1_psg_trace as T
from m5c71.research import save,load,sha,canonical,snapshot,key,action
from m5c71r83.contract import Decoder,pack,unpack,PAIR_SHA256,PROGRAM_SHA256
from m5a2.proof import ExtractionData
from m5a2.bank import records
OUT=ROOT.parent/'private-research/m5-c7-1r83'
PUB=ROOT/'data/m5-c7-1r83'
C6=ROOT.parent/'private-research/m5-a2c6'
CASES={
 'solo':(0x83,{},4200),
 'boundary-steals':(0x83,{2770:[('request',0xBF)],2780:[('request',0xA6)],3000:[('request',0xB8)],3010:[('request',0xB4)],3400:[('request',0xBA)]},4200),
 'boundary-priority':(0x83,{2770:[('request',0xB4)],2771:[('request',0xBD)],2772:[('request',0xC2)],2820:[('request',0xBD)],2860:[('request',0xC2)]},4200),
 'boundary-retrigger':(0x83,{2783:[('request',0x83)],3593:[('request',0x83)]},4200),
 'boundary-fade-reset':(0x83,{2770:[('fade',[12,1,2])],2810:[('request',0x83)],3300:[('request',0xF8)],3320:[('request',0x83)]},4200),
 'boundary-bridge':(0x83,{2770:[('request',0x96)],2870:[('request',0x88)],3120:[('request',0x83)]},4200),
 'solo-long':(0x83,{},13000),
}

def csnapshot(m):
    r=m.snapshot();r.update(channel_bytes=[list(c) for c in m.ch],shared_IY=m.iy,
        globals=[*m.tempo,m.selected,*m.mail,*m.fade,m.last_sfx,m.noise_offset,m.fade_noise_volume]);return r

def original(path):
    rom=T.load_rom(path);report={}
    for name,(rid,events,ticks) in CASES.items():
        d=T.Driver(rom);rows=[];notes=[];transfers=[];ops=Counter();active_note=False;note_before=None;note_record=None
        def begin(q):
            nonlocal active_note,note_before,note_record
            active_note=True;note_record=None;note_before=dict(tick=q.update,slot=T.CHANNELS.index(q.cpu.ix),note_byte=q.cpu.a,transpose=q.mem[q.cpu.ix+5],channel=list(q.mem[q.cpu.ix:q.cpu.ix+48]),DE=q.cpu.de,IY=q.cpu.iy)
        def end(q):
            nonlocal active_note
            if note_record is not None:
                note_record['returned_word']=q.cpu.hl
                assert q.cpu.hl==note_record['word']
            active_note=False
        def read(q):
            nonlocal note_record
            if active_note and not 0x4436<=q.cpu.hl<0x44C2:
                note_record=dict(before=note_before,index=q.cpu.bc,address=q.cpu.hl,source_bytes=list(q.mem[q.cpu.hl:q.cpu.hl+2]),word=q.mem[q.cpu.hl]|q.mem[q.cpu.hl+1]<<8)
                notes.append(note_record)
        def upper(q):
            if active_note and note_record is not None:
                note_record['actual_upper_read_address']=q.cpu.hl
                assert q.cpu.hl==note_record['address']+1
        def stored(q):
            if note_record is not None and note_record['before']['tick']==q.update:
                note_record['channel_after_frequency_store']=list(q.mem[q.cpu.ix:q.cpu.ix+48])
                assert q.mem[q.cpu.ix+11]|q.mem[q.cpu.ix+12]<<8==note_record['word']
        def transfer(q):transfers.append([q.update,T.CHANNELS.index(q.cpu.ix),q.mem[q.cpu.de]|q.mem[q.cpu.de+1]<<8])
        d.hook(0x4415,begin);d.hook(0x4426,end);d.hook(0x4422,read);d.hook(0x4424,upper);d.hook(0x4382,stored)
        d.hook(0x47B4,transfer);d.hook(0x481C,transfer);d.hook(0x46D9,lambda q:ops.update([q.cpu.a]))
        d.request(rid);states=[]
        for t in range(1,ticks+1):
            for kind,v in events.get(t,[]):action(d,kind,v)
            start=len(d.writes);d.tick();rows.append(snapshot(d,start));states.append(sha(key(d)))
        assert set(ops)<={0xE0,0xE1,0xE6,0xE7,0xF0,0xF2,0xF3,0xF5,0xF6,0xF7,0xF8,0xF9,0xFB,0xFD},'new original operation: STOP'
        assert all(n['address']==0x4634 and n['index']==255 and n['before']['slot']==1 for n in notes),'new source region: STOP'
        assert all(sha(bytes(n['source_bytes']))==PAIR_SHA256 for n in notes)
        assert all(n['actual_upper_read_address']==0x4635 and 'channel_after_frequency_store' in n for n in notes)
        private=dict(rows=rows,notes=notes,transfers=transfers,states=states);save(OUT/(name+'-original.json'),private)
        report[name]=dict(ticks=ticks,capture_sha256=sha(canonical(private)),ordered_bytes=sum(len(r['ports']) for r in rows),
            pitch_pair_ticks=[n['before']['tick'] for n in notes],pitch_pair_slots=sorted({n['before']['slot'] for n in notes}),
            actual_addresses=[0x4634,0x4635] if notes else [],opcodes={f'{k:02X}':v for k,v in sorted(ops.items())})
        print(name,'original',ticks,report[name]['pitch_pair_ticks'],flush=True)
    h=T.header_facts(rom,0x83);base=0x4634
    save(PUB/'original.json',dict(ROM_sha256=T.ROM_SHA256,original_only=True,cases=report,minimum_region=dict(address=base,length=2,ROM_offset=base+0x4000,sha256=PAIR_SHA256),header=h,
        instruction_receipt=sha(rom[0x8415:0x8427]),parent_recurrence=dict(first_tick=522,repeat_tick=3594,period_ticks=3072)))

def candidate(path):
    rom=T.load_rom(path);pre=load(PUB/'original.json')
    # New extraction starts with accepted C6, adds ONLY83; never promote/import92.
    oldblob=(C6/'programs.scsp').read_bytes();old=unpack(oldblob);bank=copy.deepcopy(old)
    h=T.header_facts(rom,0x83);p=h['header_rom'];n=6+4*h['channel_count']
    bank['programs']['131']=dict(streams=[dict(latch=int(s['latch'],16),pointer=s['stream_cpu'],transpose=s['transpose'],volume=s['volume'],flags=128) for s in h['channels']],
        multiplier=h['duration_multiplier'],tempo=h['tempo_byte'],source_offset=p,header_length=n,header_sha256=sha(rom[p:p+n]))
    assert sha(canonical(bank['programs']['131']))==PROGRAM_SHA256
    class Data(ExtractionData):
        def __missing__(self,k):
            if int(k) in (0x4634,0x4635):
                assert sha(rom[0x8634:0x8636])==PAIR_SHA256
                self[k]=rom[int(k)+0x4000];return self[k]
            return super().__missing__(k)
    data=Data(rom);data.update(bank['data']);bank['data']=data
    for name,(rid,events,ticks) in CASES.items():
        if ticks>4200:continue
        m=Decoder(bank);m.direct(rid)
        for t in range(1,ticks+1):
            for kind,v in events.get(t,[]):apply(m,kind,v)
            m.tick() # Any new unsupported operation stops, not swallowed.
    bank['data']=dict(data)
    for s in records(bank)['segments']:
        a,n=s['address'],s['length'];assert sha(rom[a+0x4000:a+0x4000+n])==s['sha256']
    blob=pack(bank);OUT.mkdir(parents=True,exist_ok=True);(OUT/'programs.scsp').write_bytes(blob);save(OUT/'records.json',records(bank));bank=unpack(blob)
    results={}
    for name,(rid,events,ticks) in CASES.items():
        if ticks>4200:continue
        m=Decoder(bank);m.direct(rid);rows=[]
        for t in range(1,ticks+1):
            for kind,v in events.get(t,[]):apply(m,kind,v)
            m.tick();rows.append(csnapshot(m))
        results[name]=compare(name,m,rows,pre)
    solo=Decoder(bank);solo.direct(0x83);visited=set();read_byte=solo.byte
    def observed_byte(p):visited.add(p);return read_byte(p)
    solo.byte=observed_byte
    for _ in range(4200):solo.tick()
    per83=dict(header=bank['programs']['131'],data=sorted((p,bank['data'][str(p)]) for p in visited))
    save(OUT/'83-source-records.json',per83)
    save(PUB/'emission.json',dict(cases=results,horizon=4200,SCSP_version=1,bank_bytes=len(blob),bank_sha256=sha(blob),bank_canonical_sha256=sha(canonical(bank)),
        old_C6_unchanged=sha(oldblob)==sha((C6/'programs.scsp').read_bytes()),old_records_retained=all(bank['data'][k]==v for k,v in old['data'].items()) and all(bank['programs'][k]==v for k,v in old['programs'].items()),
        header_sha256=bank['programs']['131']['header_sha256'],special_region_sha256=PAIR_SHA256,complete83_record_sha256=sha(canonical(per83)),solo_demand_source_bytes=len(visited)))

def apply(m,kind,v):
    if kind=='request':m.direct(v)
    elif kind=='fade':m.fade=list(v)
    else:raise ValueError(kind)

def compare(name,m,rows,pre,transfers=None):
    o=load(OUT/(name+'-original.json'));assert sha(canonical(o))==pre['cases'][name]['capture_sha256']
    failures=[dict(tick=t,field=k) for t,(a,b) in enumerate(zip(rows,o['rows']),1) for k in b if canonical(a[k])!=canonical(b[k])]
    if (transfers if transfers is not None else [[t,i,q] for t,i,p,q in m.loops])!=o['transfers']:failures.append(dict(tick=0,field='transfers'))
    save(OUT/(name+'-candidate.json'),dict(rows=rows,failures=failures))
    result=dict(ticks=len(rows),ordered_bytes=sum(len(r['ports']) for r in rows),failures=failures[:10],failure_count=len(failures),status='PASS' if not failures else 'FAIL')
    print(name,result,flush=True);assert not failures,'exact original comparison failed'
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['original','candidate']);p.add_argument('rom');a=p.parse_args();globals()[a.phase](a.rom)
