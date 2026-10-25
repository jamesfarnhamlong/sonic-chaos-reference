"""Common SFX: three authorised programs, unchanged B1 decoder, independent oracle."""
import argparse
import json
from pathlib import Path
import statistics
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2')]
import audio1_psg_trace as T
import m5a2.proof as A2
import m5a2b1.proof as B1
import m5a2b2.proof as B2
from m5a2.bank import pack,unpack,records,canonical
from m5a2b1.decoder import Decoder

OUT=ROOT.parent/'private-research/m5-a2c1'
PUB=ROOT/'data/m5-a2c1'
OLD=B1.OLD
B1OLD=ROOT.parent/'private-research/m5-a2b1'
B2OLD=ROOT.parent/'private-research/m5-a2b2'
BATCH=(0xA4,0xA6,0xBF)
ENDS=(82,41,21)
save,sha=A2.save,A2.sha
CASES={
 **{f'solo-{rid:02X}':(rid,{},end+32) for rid,end in zip(BATCH,ENDS)},
 'THZ-ring':(0x81,{30:[('request',0xBF)]},180),
 'THZ-spring':(0x81,{30:[('request',0xA6)]},180),
 'hurt-recent':(0x81,{30:[('request',0xBF)],56:[('request',0xA4)]},180),
 'hurt-concurrent':(0x81,{30:[('request',0xAC)],35:[('request',0xA4)]},180),
 'ring-repeats':(0x81,{30:[('request',0xBF)],32:[('request',0xBF)],48:[('request',0xBF)],80:[('request',0xBF)]},160),
 'spring-repeats':(0x81,{30:[('request',0xA6)],33:[('request',0xA6)],60:[('request',0xA6)],100:[('request',0xA6)]},200),
 'replacement-rejection':(0x81,{30:[('request',0xA6)],40:[('request',0xA4)],45:[('request',0xBF)],50:[('request',0xA6)],55:[('request',0xBC)]},180),
 'coupled-ring':(0xA3,{6:[('request',0xBC)],35:[('request',0xBF)]},100),
 'fixed-noise-spring':(0xB8,{6:[('request',0xBC)],35:[('request',0xA6)]},180),
 'hurt-held-noise':(0x81,{30:[('request',0xB8)],35:[('request',0xBC)],65:[('request',0xA4)]},210),
 'fade-ring-fresh':(0x81,{30:[('request',0xA4)],40:[('fade',[12,1,2])],80:[('request',0xBF)]},130),
 'reset-spring-fresh':(0x81,{30:[('request',0xBF)],45:[('request',0xF8)],70:[('request',0xA6)]},150),
 'finite-common-SFX':(0x84,{30:[('request',0xBF)],60:[('request',0xA6)],100:[('request',0xA4)]},210),
}


def allcases():
    return {**{'B2-'+k:v for k,v in B2.allcases().items()},**CASES}


def prior_path(name):
    return (B2OLD,name[3:]) if name.startswith('B2-') else None


def prior_pcm_path(name):
    prior=prior_path(name)
    if not prior:return None
    folder,oldname=prior
    earlier=B2.prior_path(oldname)
    return earlier if earlier else prior


def run(rom):
    assert sha((B2OLD/'programs.scsp').read_bytes())=='00f89cee32b1a9c31f887504182dfbed724e32ebab659f3eb7e1c923db4bc74c'
    assert len(json.loads((PUB/'preflight.json').read_text())['rows'])==6
    cases=allcases();original_configuration=A2.CASES,A2.IDS,A2.Decoder
    try:
        A2.CASES=cases;A2.IDS=A2.IDS+B1.BATCH+B2.BATCH+BATCH;A2.Decoder=Decoder
        bank=A2.extract(rom)
    finally:A2.CASES,A2.IDS,A2.Decoder=original_configuration
    oldbank=unpack((B2OLD/'programs.scsp').read_bytes())
    assert all(bank['data'][k]==v for k,v in oldbank['data'].items())
    assert all(bank['programs'][k]==v for k,v in oldbank['programs'].items())
    blob=pack(bank);OUT.mkdir(parents=True,exist_ok=True);(OUT/'programs.scsp').write_bytes(blob)
    save(OUT/'source-records.json',records(bank));bank=unpack(blob);report={}
    for name,case in cases.items():
        m,rows,times,work=B1.candidate(bank,case)
        # The candidate finishes before this oracle exists.
        rid,events,ticks=case;d=T.Driver(rom);d.request(rid);original=[];fail=[];transfers=[];restores=[];admissions=[]
        def transfer(q):transfers.append((q.update,T.CHANNELS.index(q.cpu.ix),q.mem[q.cpu.de]|q.mem[q.cpu.de+1]<<8))
        d.hook(0x47B4,transfer);d.hook(0x481C,transfer)
        d.hook(0x41A7,lambda q:admissions.append([q.update,q.cpu.a]))
        d.hook(0x47F3,lambda q:restores.append(dict(tick=q.update,channel=T.CHANNELS.index(q.cpu.ix),data_latch=q.psg.latch//16,byte=q.cpu.a)))
        for t in range(1,ticks+1):
            for k,v in events.get(t,[]):
                if k=='request':d.request(v)
                elif k=='mailbox':d.mem[0xDE04+v[1]]=v[0]
                elif k=='fade':d.mem[0xDE09:0xDE0C]=bytes(v)
            start=len(d.writes);d.tick()
            o=dict(ports=[v for _,v in d.writes[start:]],registers=d.psg.state(),latch=d.psg.latch//16,
                saved_noise=d.mem[0xDE11],channels=[d.mem[a]&0xD4 for a in T.CHANNELS],priority=d.mem[0xDE0F],
                channel_bytes=[list(d.mem[a:a+48]) for a in T.CHANNELS],shared_IY=d.cpu.iy,
                globals=[d.mem[a] for a in (0xDE01,0xDE02,0xDE03,0xDE04,0xDE05,0xDE06,0xDE09,0xDE0A,0xDE0B,0xDE0D,0xDE15,0xDE16)])
            original.append(o);fail.extend(dict(tick=t,field=k) for k in o if o[k]!=rows[t-1][k])
            if fail:break
        targets=[(t,i,q) for t,i,p,q in m.loops]
        if not fail and targets!=transfers:fail.append(dict(tick=0,field='control-transfers'))
        prior=prior_path(name)
        if prior:
            folder,oldname=prior;previous=json.loads((folder/(oldname+'.json')).read_text())['candidate']
            if len(rows)!=len(previous) or any(any(canonical(r[k])!=canonical(x[k]) for k in x) for r,x in zip(rows,previous)):
                fail.append(dict(tick=0,field='frozen-prior-candidate'))
        save(OUT/(name+'.json'),dict(candidate=rows,original=original,failures=fail,case=case,
            original_transfers=transfers,candidate_transfers=targets,saved_noise_restores=restores,SFX_admissions=admissions))
        inactive=next((i+1 for i,r in enumerate(rows) if not any(f&128 for f in r['channels'])),None)
        report[name]=dict(ticks=ticks,compared_ticks=len(original),status='FAIL' if fail else 'PASS',failures=fail,
            first_inactive_tick=inactive,ordered_bytes=sum(len(r['ports']) for r in rows),
            control_transfers=len(targets),control_transfer_sha256=sha(canonical(targets)),
            max_port_bytes_per_tick=max(len(r['ports']) for r in rows),max_stream_operations_per_tick=max(work),
            opcodes={f'{k:02X}':v for k,v in sorted(m.opcodes.items())},
            median_decoder_ns=statistics.median(times),max_decoder_ns=max(times))
        print(name,report[name]['status'],fail[:2],flush=True)
    sourcepaths=[Path(__file__),ROOT/'tools/m5a2/decoder.py',ROOT/'tools/m5a2/bank.py',ROOT/'tools/m5a2b1/decoder.py']
    save(PUB/'emission.json',dict(cases=report,ROM_sha256=T.ROM_SHA256,zero_tolerance=True,
        independent_candidate=True,decoder_language_changes=0,previous_21_headers_and_data_unchanged=True,
        source_sha256={p.relative_to(ROOT).as_posix():sha(p.read_bytes().replace(b'\r\n',b'\n')) for p in sourcepaths},
        SCSP_version=1,horizon=bank['horizon'],packed_bytes=len(blob),packed_sha256=sha(blob),
        previous_packed_bytes=7759,incremental_packed_bytes=len(blob)-7759,data_bytes=len(bank['data']),
        incremental_data_bytes=len(bank['data'])-len(oldbank['data']),segments=len(records(bank)['segments']),
        header_bytes=sum(p['header_length'] for p in bank['programs'].values()),record_json_bytes=len(canonical(records(bank)))))
    assert all(c['status']=='PASS' for c in report.values()),'exact original-driver gate failed'


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('rom');a=p.parse_args();run(T.load_rom(a.rom))
