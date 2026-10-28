"""Grouped original-first catalogue verification. Payloads are private, per-ID gates independent."""
import argparse
import copy
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2'),str(ROOT/'tools/m5a0')]
from m5c71.research import save,load,sha,canonical,snapshot,key,action,schedule
OUT=ROOT.parent/'private-research/m5-c7-batch'
PUB=ROOT/'data/m5-c7-batch'
MUSIC=(0x91,0x93,0x95,0x82,0x8B,0x8C,0x8D,0x8F,0x90)
SFX=(0xA8,0xAB,0xAD,0xAE,0xB2,0xB3,0xB5,0xC0,0xC1,0xC3,0xBB,0xBE,0xC4)

def cases(ids):
    result={}
    for rid in ids:
        tag=f'{rid:02X}'
        if rid==0x92:
            result[tag+'-solo']=(rid,{},4200)
            result[tag+'-steals']=(rid,{3250:[('request',0xBF)],3260:[('request',0xA6)],3300:[('request',0xB8)],3500:[('request',0xB4)],4000:[('request',0xBA)]},4200)
            result[tag+'-priority']=(rid,{3250:[('request',0xB4)],3251:[('request',0xBD)],3252:[('request',0xC2)],3300:[('request',0xBD)],3340:[('request',0xC2)]},4200)
            result[tag+'-restart']=(rid,{3267:[('request',rid)],4033:[('request',rid)]},4200)
            result[tag+'-bridge']=(rid,{3267:[('request',0x96)],3370:[('request',0x88)],3620:[('request',rid)]},4200)
            result[tag+'-fade-reset']=(rid,{3267:[('fade',[12,1,2])],3300:[('request',rid)],3600:[('request',0xF8)],3620:[('request',rid)]},4200)
        elif rid<0xA0:
            result[tag+'-solo']=(rid,{},4200)
            result[tag+'-steals']=(rid,{30:[('request',0xBF)],60:[('request',0xA6)],90:[('request',0xB8)],100:[('request',0xB4)],250:[('request',0xBA)]},600)
            result[tag+'-priority']=(rid,{30:[('request',0xB4)],31:[('request',0xBD)],32:[('request',0xC2)],70:[('request',0xBD)],100:[('request',0xC2)]},300)
            result[tag+'-restart']=(rid,{100:[('request',rid)],300:[('request',rid)]},600)
            result[tag+'-bridge']=(rid,{100:[('request',0x96)],200:[('request',0x88)],450:[('request',rid)]},700)
            result[tag+'-fade-reset']=(rid,{50:[('fade',[12,1,2])],100:[('request',rid)],200:[('request',0xF8)],220:[('request',rid)]},500)
        else:
            # Actual F2 SFX context: original81 actively playing; solo diagnostic separate.
            result[tag+'-over81']=(0x81,{30:[('request',rid)]},600)
            result[tag+'-solo']=(rid,{},600)
            result[tag+'-retrigger']=(0x81,{30:[('request',rid)],32:[('request',rid)],100:[('request',rid)]},600)
            result[tag+'-replace']=(0x81,{30:[('request',rid)],35:[('request',0xBF)],100:[('request',rid)],110:[('request',0xB4)]},600)
            result[tag+'-fade-reset']=(0x81,{30:[('request',rid)],40:[('fade',[12,1,2])],100:[('request',0xF8)],120:[('request',0x81)],150:[('request',rid)]},600)
    return result

def original(path,ids):
    if ids==(0x92,) or all(i>=0xA0 for i in ids):return original_sfx(path,ids)
    # Reuse the completed original-only capture/loop method, never the old programme list.
    import m5c71.research as prior
    prior.IDS=ids;prior.CASES=cases(ids);prior.OUT=OUT;prior.PUB=PUB
    # Preserve useful groups independently rather than overwriting earlier results.
    old=load(PUB/'preflight.json') if (PUB/'preflight.json').exists() else None
    manifest=load(OUT/'oracle-manifest.json') if (OUT/'oracle-manifest.json').exists() else {}
    prior.original(path)
    new=load(PUB/'preflight.json');newman=load(OUT/'oracle-manifest.json')
    if old:new['cases']={**old['cases'],**new['cases']}
    save(PUB/'preflight.json',new);save(OUT/'oracle-manifest.json',{**manifest,**newman})

def original_sfx(path,ids):
    import audio1_psg_trace as T
    from collections import Counter
    rom=T.load_rom(path);report=load(PUB/'preflight.json');manifest=load(OUT/'oracle-manifest.json')
    for name,case in cases(ids).items():
        if name=='92-solo':
            prior=ROOT.parent/'private-research/m5-c7-1'
            private=load(prior/(name+'-original.json'));save(OUT/(name+'-original.json'),private)
            manifest[name]=sha(canonical(private))
            report['cases'][name]=load(ROOT/'data/m5-c7-1/preflight.json')['cases'][name+'']
            assert manifest[name]==report['cases'][name]['capture_sha256']
            continue
        rid,events,ticks=case;d=T.Driver(rom);rows=[];transfers=[];ops=Counter();f3=[];fd=[]
        d.hook(0x46D9,lambda q:ops.update([q.cpu.a]))
        def edge(q):transfers.append([q.update,T.CHANNELS.index(q.cpu.ix),q.mem[q.cpu.de]|q.mem[q.cpu.de+1]<<8])
        d.hook(0x47B4,edge);d.hook(0x481C,edge)
        d.hook(0x4753,lambda q:f3.append([q.update,T.CHANNELS.index(q.cpu.ix),q.mem[q.cpu.de]]))
        d.hook(0x47BA,lambda q:fd.append([q.update,T.CHANNELS.index(q.cpu.ix),q.cpu.a]))
        d.request(rid);ended=None
        for t in range(1,ticks+1):
            for kind,v in events.get(t,[]):action(d,kind,v)
            start=len(d.writes);d.tick();rows.append(snapshot(d,start))
            if name.endswith('-solo') and not d.active() and ended is None:ended=t
        private=dict(rows=rows,transfers=transfers,schedule=schedule(case),F3=f3,FD=fd)
        save(OUT/(name+'-original.json'),private);manifest[name]=sha(canonical(private))
        report['cases'][name]=dict(ticks=ticks,capture_sha256=manifest[name],ordered_bytes=sum(len(r['ports']) for r in rows),opcodes={f'{k:02X}':v for k,v in sorted(ops.items())},F3_count=len(f3),F3_values=sorted({x[2] for x in f3}),FD_count=len(fd),release_tick=ended,final_attenuations=d.psg.att)
        print(name,'original',ended,flush=True)
    save(PUB/'preflight.json',report);save(OUT/'oracle-manifest.json',manifest)

def candidate(path,ids):
    import audio1_psg_trace as T
    from m5a2.proof import ExtractionData,apply
    from m5a2.bank import pack,unpack,records
    if ids==(0x92,):from m5c7batch.alias92 import Decoder
    else:from m5a2c2.decoder import Decoder
    from m5c71r83.proof import csnapshot
    rom=T.load_rom(path);manifest=load(OUT/'oracle-manifest.json')
    oldblob=(ROOT.parent/'private-research/m5-a2c6/programs.scsp').read_bytes()
    assert sha(oldblob)=='677e65cc6038bb193e9813b5890b2127dfa7d5b0b71f0553867995659d2ba5a6'
    base=unpack(oldblob);bank=copy.deepcopy(base);bank['data']=ExtractionData(rom);bank['data'].update(base['data'])
    for rid in ids:
        h=T.header_facts(rom,rid);p=h['header_rom'];n=6+4*h['channel_count'] if rid<0xA0 else 4+6*h['stream_count']
        # Same established header extraction; initial SFX flags come from ROM.
        if rid<0xA0:
            streams=[dict(latch=int(s['latch'],16),pointer=s['stream_cpu'],transpose=s['transpose'],volume=s['volume'],flags=128) for s in h['channels']]
        else:
            streams=[dict(latch=int(s['latch'],16),pointer=s['stream_cpu'],transpose=s['transpose'],volume=s['volume'],flags=rom[p+4+6*i]) for i,s in enumerate(h['streams'])]
        bank['programs'][str(rid)]=dict(streams=streams,multiplier=h['duration_multiplier'],tempo=h.get('tempo_byte',0),source_offset=p,header_length=n,header_sha256=sha(rom[p:p+n]))
    def run(bank,case):
        rid,events,ticks=case;m=Decoder(bank);m.direct(rid);rows=[];reject=None
        for t in range(1,ticks+1):
            for kind,v in events.get(t,[]):apply(m,kind,v)
            try:m.tick()
            except ValueError as e:reject=dict(tick=t,error=type(e).__name__,message=str(e));break
            rows.append(csnapshot(m))
        return m,rows,reject
    for case in cases(ids).values():run(bank,case)
    bank['data']=dict(bank['data'])
    for s in records(bank)['segments']:
        p,n=s['address'],s['length'];assert sha(rom[p+0x4000:p+0x4000+n])==s['sha256']
    blob=pack(bank);tag='-'.join(f'{i:02X}' for i in ids);(OUT/(tag+'.scsp')).write_bytes(blob);bank=unpack(blob)
    results={}
    for name,case in cases(ids).items():
        o=load(OUT/(name+'-original.json'));assert sha(canonical(o))==manifest[name]
        m,rows,reject=run(bank,case);bad=[]
        for t,(c,r) in enumerate(zip(rows,o['rows']),1):
            for k in r:
                if canonical(c[k])!=canonical(r[k]):bad.append(dict(tick=t,field=k))
        targets=[[t,i,q] for t,i,p,q in m.loops if t<=len(rows)]
        if targets!=[r for r in o['transfers'] if r[0]<=len(rows)]:bad.append(dict(tick=0,field='transfers'))
        save(OUT/(name+'-candidate.json'),dict(rows=rows,rejection=reject,schedule=schedule(case)))
        results[name]=dict(status='FAIL' if bad else 'HOLD' if reject else 'PASS',ticks=len(rows),requested_ticks=case[2],rejection=reject,failure_count=len(bad),failures=bad[:10],ordered_bytes=sum(len(r['ports']) for r in rows))
        print(name,results[name],flush=True)
    save(PUB/('emission-'+tag+'.json'),dict(cases=results,SCSP_sha256=sha(blob),SCSP_bytes=len(blob),bank=tag+'.scsp',prior_records_retained=all(bank['data'][k]==v for k,v in base['data'].items()),horizon=4200))
    assert not any(r['failure_count'] for r in results.values())

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['original','candidate']);p.add_argument('rom');p.add_argument('ids',nargs='+');a=p.parse_args()
    globals()[a.phase](a.rom,tuple(int(i,16) for i in a.ids))
