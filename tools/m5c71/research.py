"""Two-ID original-first music gate. All programme/state/audio payloads stay private.

Run original ROM before candidate ROM, then pcm (no ROM). Python 3.13 + z80/numpy.
No accepted decoder, bank format, guard or native implementation is modified.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'tools/m5a2'), str(ROOT/'tools/m5a0')]
PUB = ROOT/'data/m5-c7-1'
OUT = ROOT.parent/'private-research/m5-c7-1'
IDS = (0x83, 0x92)
GLOBALS = (0xDE01,0xDE02,0xDE03,0xDE04,0xDE05,0xDE06,0xDE09,0xDE0A,0xDE0B,0xDE0D,0xDE15,0xDE16)
CASES = {}
for rid in IDS:
    tag = f'{rid:02X}'
    CASES[tag+'-solo'] = (rid, {}, 4200)
    CASES[tag+'-steals'] = (rid, {30:[('request',0xBF)],60:[('request',0xA6)],90:[('request',0xB8)],100:[('request',0xB4)],250:[('request',0xBA)]}, 600)
    CASES[tag+'-priority'] = (rid, {30:[('request',0xB4)],31:[('request',0xBD)],32:[('request',0xC2)],70:[('request',0xBD)],100:[('request',0xC2)]}, 300)
    CASES[tag+'-restart'] = (rid, {100:[('request',rid)],300:[('request',rid)]}, 600)
    CASES[tag+'-bridge'] = (rid, {100:[('request',0x96)],200:[('request',0x88)],450:[('request',rid)]}, 700)
    CASES[tag+'-fade-reset'] = (rid, {50:[('fade',[12,1,2])],100:[('request',rid)],200:[('request',0xF8)],220:[('request',rid)]}, 500)
CASES['83-to-92'] = (0x83,{200:[('request',0x92)],400:[('request',0x83)]},700)

def canonical(x): return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def sha(x): return hashlib.sha256(x).hexdigest()
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def load(p): return json.loads(p.read_text())
def schedule(case):
    rid,events,ticks=case
    return dict(initial=rid,events={str(k):v for k,v in events.items()},ticks=ticks)
def action(d,kind,v):
    if kind=='request': d.request(v)
    elif kind=='fade': d.mem[0xDE09:0xDE0C]=bytes(v)
    else: raise ValueError(kind)
def snapshot(d,start):
    import audio1_psg_trace as T
    return dict(ports=[v for _,v in d.writes[start:]],registers=d.psg.state(),latch=d.psg.latch//16,
        saved_noise=d.mem[0xDE11],channels=[d.mem[a]&0xD4 for a in T.CHANNELS],priority=d.mem[0xDE0F],
        channel_bytes=[list(d.mem[a:a+48]) for a in T.CHANNELS],shared_IY=d.cpu.iy,globals=[d.mem[a] for a in GLOBALS])
def key(d):
    # Include every driver RAM byte, shared IY, logical PSG/data latch. Chip
    # counters/LFSR intentionally are NOT reset or claimed to recur.
    return bytes(d.mem[0xDE00:0xDF90])+d.cpu.iy.to_bytes(2,'little')+canonical([d.psg.state(),d.psg.latch])

def original(rompath):
    import audio1_psg_trace as T
    rom=T.load_rom(rompath); reports={}; manifests={}
    for name,case in CASES.items():
        rid,events,ticks=case;d=T.Driver(rom);rows=[];ops=Counter();transfers=[];env=set();pitch=set();reload=Counter();controls=Counter();raw=[];tables=Counter();admissions=[]
        d.hook(0x46D9,lambda q:ops.update([q.cpu.a]))
        def transfer(q): transfers.append([q.update,T.CHANNELS.index(q.cpu.ix),q.mem[q.cpu.de]|q.mem[q.cpu.de+1]<<8])
        d.hook(0x47B4,transfer);d.hook(0x481C,transfer)
        d.hook(0x4546,lambda q:env.add(q.mem[q.cpu.ix+8]))
        d.hook(0x42AF,lambda q:pitch.add(q.mem[q.cpu.ix+7]))
        d.hook(0x42F6,lambda q:reload.update([q.cpu.iy+3]))
        d.hook(0x454E,lambda q:controls.update([q.mem[q.cpu.ix+29]&0xF8]))
        d.hook(0x43C7,lambda q:raw.append(q.update))
        d.hook(0x4610,lambda q:tables.update([(q.mem[q.cpu.ix+8],q.mem[q.cpu.ix+31],q.cpu.a)]))
        d.hook(0x41A7,lambda q:admissions.append([q.update,q.cpu.a]))
        d.request(rid);seen={};rec=None;keys=[]
        for t in range(1,ticks+1):
            for kind,v in events.get(t,[]):action(d,kind,v)
            start=len(d.writes);d.tick();rows.append(snapshot(d,start));k=key(d);keys.append(sha(k))
            if name.endswith('-solo'):
                if rec is None and k in seen:rec=dict(first_tick=seen[k],repeat_tick=t,period_ticks=t-seen[k])
                seen.setdefault(k,t)
        private=dict(rows=rows,transfers=transfers,admissions=admissions,schedule=schedule(case),state_hashes=keys)
        save(OUT/(name+'-original.json'),private)
        manifest=sha(canonical(private));manifests[name]=manifest
        r=dict(ticks=ticks,ordered_bytes=sum(len(r['ports']) for r in rows),capture_sha256=manifest,
            reached_opcodes={f'{k:02X}':v for k,v in sorted(ops.items())},volume_selectors=sorted(env),pitch_selectors=sorted(pitch),
            shared_IY_reload_sources={f'{k:04X}':v for k,v in sorted(reload.items())},algorithmic_envelope_states={f'{k:02X}':v for k,v in sorted(controls.items())},
            table_reads=sum(tables.values()),table_selectors=sorted({a for a,b,c in tables}),table_control_values=sorted({c for a,b,c in tables if c>=128}),
            table_visits={str(s):dict(reads=sum(v for (a,b,c),v in tables.items() if a==s),indices=sorted({b for a,b,c in tables if a==s}),controls=sorted({c for a,b,c in tables if a==s and c>=128})) for s in sorted({a for a,b,c in tables})},
            raw_reader_visits=len(raw),transfers=len(transfers),transfer_sha256=sha(canonical(transfers)),SFX_admissions=admissions,
            active_slots=sorted({i for row in rows for i,c in enumerate(row['channels']) if c&128}),
            suppressed_slots=sorted({i for row in rows for i,c in enumerate(row['channels']) if c&4}),
            priorities=sorted({r['priority'] for r in rows}))
        if name.endswith('-solo'):
            h=T.header_facts(rom,rid);n=6+4*h['channel_count'];r['header']=h;r['header_sha256']=sha(rom[h['header_rom']:h['header_rom']+n])
            # Song-specific original-only extension: bounded to 24000 ticks search,
            # then ONE period (max24000) verification. Candidate horizon stays4200.
            search_limit=24000
            while rec is None and d.update<search_limit:
                d.tick();k=key(d)
                if k in seen:rec=dict(first_tick=seen[k],repeat_tick=d.update,period_ticks=d.update-seen[k])
                seen.setdefault(k,d.update)
            if rec:
                a,b,p=rec['first_tick'],rec['repeat_tick'],rec['period_ticks'];boundary=key(d)
                # If found during the initial capture, replay from a fresh original
                # to the actual repeat boundary; never use the end of4200 instead.
                if d.update!=b:
                    d=T.Driver(rom);d.request(rid)
                    for _ in range(b):d.tick()
                    boundary=key(d)
                w1=[(t-a,v) for t,v in d.writes if a<t<=b];start=len(d.writes)
                for _ in range(p):d.tick()
                w2=[(t-b,v) for t,v in d.writes[start:]]
                rec.update(next_period_state_identical=boundary==key(d),next_period_writes_identical=w1==w2,writes_per_period=len(w1),state_sha256=sha(boundary),original_proof_ticks=b+p,
                    candidate_continuation_authorised=False,scope='original driver recurrence; persistent chip phase is not a loop cut or reset permission')
                save(OUT/(name+'-loop-private.json'),dict(certificate=rec,writes=d.writes))
            r['recurrence']=rec;r['original_search_ticks']=d.update
        reports[name]=r;print(name,'original',ticks,'recurrence',r.get('recurrence'),flush=True)
    save(PUB/'preflight.json',dict(ROM_sha256=T.ROM_SHA256,original_only=True,candidate_executed=False,cases=reports))
    save(OUT/'oracle-manifest.json',manifests)

def candidate(rompath):
    import audio1_psg_trace as T
    import m5a2.proof as A
    from m5a2.bank import pack,unpack,records
    from m5a2c2.decoder import Decoder
    from m5a2c2.proof import candidate as run_candidate
    rom=T.load_rom(rompath);pre=load(PUB/'preflight.json');manifest=load(OUT/'oracle-manifest.json');boundaries=load(PUB/'boundaries.json')
    assert set(pre['cases'])==set(CASES)
    assert set(boundaries['per_ID'])=={'83','92'} and boundaries['candidate_decoder_imported'] is False
    oldpath=ROOT.parent/'private-research/m5-a2c6/programs.scsp';oldblob=oldpath.read_bytes()
    assert sha(oldblob)=='677e65cc6038bb193e9813b5890b2127dfa7d5b0b71f0553867995659d2ba5a6'
    old=unpack(oldblob);bank=dict(old);bank['programs']=dict(old['programs']);bank['data']=A.ExtractionData(rom);bank['data'].update(old['data'])
    for rid in IDS:
        h=T.header_facts(rom,rid);p=h['header_rom'];n=6+4*h['channel_count']
        bank['programs'][str(rid)]=dict(streams=[dict(latch=int(s['latch'],16),pointer=s['stream_cpu'],transpose=s['transpose'],volume=s['volume'],flags=128) for s in h['channels']],
            multiplier=h['duration_multiplier'],tempo=h['tempo_byte'],source_offset=p,header_length=n,header_sha256=sha(rom[p:p+n]))
    # Extraction is candidate-demand only; original rows never supply records.
    failures={}
    for name,case in CASES.items():
        try:run_candidate(bank,case)
        except Exception as e: failures[name]=dict(error=type(e).__name__,message=str(e))
    bank['data']=dict(bank['data'])
    for s in records(bank)['segments']:
        p,n=s['address'],s['length'];assert sha(rom[p+0x4000:p+0x4000+n])==s['sha256']
    blob=pack(bank);(OUT/'programs.scsp').write_bytes(blob);save(OUT/'source-records.json',records(bank));bank=unpack(blob)
    results={}
    for name,case in CASES.items():
        original=load(OUT/(name+'-original.json'));assert sha(canonical(original))==manifest[name]
        rejection=None
        if name in failures:
            from m5a2c2.fd_gate import snapshot as csnapshot
            from m5a2.proof import apply
            rid,events,ticks=case;m=Decoder(bank);m.direct(rid);rows=[];work=[]
            for t in range(1,ticks+1):
                for kind,v in events.get(t,[]):apply(m,kind,v)
                try:m.tick()
                except Exception as e:
                    rejection=dict(tick=t,error=type(e).__name__,message=str(e),extraction_failure=failures[name]);break
                rows.append(csnapshot(m));work.append(m.ops)
            assert rejection is not None
        else:m,rows,times,work=run_candidate(bank,case)
        mismatches=[]
        for t,(c,o) in enumerate(zip(rows,original['rows']),1):
            for k in o:
                if canonical(c[k])!=canonical(o[k]):mismatches.append(dict(tick=t,field=k))
        targets=[[t,i,q] for t,i,p,q in m.loops if t<=len(rows)]
        if targets!=[r for r in original['transfers'] if r[0]<=len(rows)]:mismatches.append(dict(tick=0,field='transfers'))
        save(OUT/(name+'-candidate.json'),dict(rows=rows,schedule=schedule(case),failures=mismatches,rejection=rejection))
        results[name]=dict(status='FAIL' if mismatches else 'HOLD' if rejection else 'PASS',ticks=len(rows),requested_ticks=case[2],rejection=rejection,ordered_bytes=sum(len(r['ports']) for r in rows),failures=mismatches[:20],failure_count=len(mismatches),max_stream_operations=max(work),max_writes=max(len(r['ports']) for r in rows))
        print(name,results[name],flush=True)
    receipts={}
    for rid in IDS:
        p=bank['programs'][str(rid)];solo=Decoder(bank);solo.direct(rid);visited=set();basebyte=solo.byte
        def read(addr):visited.add(addr);return basebyte(addr)
        solo.byte=read;error=None
        try:
            for _ in range(4200):solo.tick()
        except Exception as e:error=str(e)
        pairs=[[a,bank['data'][str(a)]] for a in sorted(visited) if str(a) in bank['data']]
        save(OUT/f'{rid:02X}-records.json',dict(header=p,data=pairs))
        receipts[f'{rid:02X}']=dict(header_sha256=p['header_sha256'],record_sha256=sha(canonical(dict(header=p,data=pairs))),source_bytes=len(pairs),extraction_error=error,complete_within_4200=error is None)
    save(PUB/'emission.json',dict(cases=results,per_ID=receipts,SCSP_sha256=sha(blob),SCSP_bytes=len(blob),horizon=bank['horizon'],decoder_modified=False,prior_bank_unchanged=sha(oldpath.read_bytes())==sha(oldblob),prior_records_retained=all(bank['data'][k]==v for k,v in old['data'].items()) and all(bank['programs'][k]==v for k,v in old['programs'].items()),original_oracles_frozen_before_candidate=True))
    assert not any(c['failure_count'] for c in results.values()),'unexpected state/emission difference'
    assert {n:c['rejection']['tick'] for n,c in results.items() if c['rejection']}=={'83-solo':2784,'92-solo':3266},'changed guard boundary'

def pcm():
    import numpy as np
    from backend import PSG
    from m5a2.bank import unpack
    from m5a2c2.runtime import render,wav
    dll=ROOT.parent/'sonic-chaos-reference-m5-a1l/build/m5-a1l/psg-a1l.dll'
    assert sha(dll.read_bytes())=='47e15c47e255900b819847e0ddefd7e3f0751dcc8f75dff3a1690f7e76adcf65'
    bank=unpack((OUT/'programs.scsp').read_bytes());reports={}
    for name,c in load(PUB/'emission.json')['cases'].items():
        if c['status']=='FAIL':continue
        sch=schedule(CASES[name]);sch['ticks']=c['ticks'];audio,states=render(bank,sch,dll);split,splitstates=render(bank,sch,dll,split=True)
        original=load(OUT/(name+'-original.json'));blocks=[];refstates=[]
        with PSG(dll) as chip:
            for row in original['rows'][:c['ticks']]:
                chip.write(row['ports']);blocks.append(chip.render());refstates.append(chip.state())
        ref=np.concatenate(blocks);bad=int(np.count_nonzero(audio!=ref));statebad=sum(a!=b for a,b in zip(states,refstates))
        wav(OUT/(name+'-candidate.wav'),audio);wav(OUT/(name+'-original-A1L.wav'),ref)
        reports[name]=dict(samples=len(audio),PCM_mismatches=bad,native_state_mismatching_ticks=statebad,partition_exact=np.array_equal(audio,split) and states==splitstates,PCM_sha256=sha(audio.tobytes()),original_A1L_PCM_sha256=sha(ref.tobytes()),status='PASS' if not bad and not statebad and np.array_equal(audio,split) and states==splitstates else 'FAIL')
        print(name,reports[name],flush=True)
    save(PUB/'pcm.json',dict(cases=reports,A1L_sha256=sha(dll.read_bytes()),clock_hz=3546893,rate=44100,samples_per_tick=735,comparison='exact original-Z80 writes through same accepted persistent A1L; not MAME waveform equality or hardware timing'))
    assert all(r['status']=='PASS' for r in reports.values()),'exact PCM/native/partition gate failed'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['original','candidate','pcm']);p.add_argument('rom',nargs='?');a=p.parse_args()
    if a.phase=='pcm':pcm()
    else:globals()[a.phase](a.rom)
