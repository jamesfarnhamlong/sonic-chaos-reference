"""Fresh finite completion and representative interactions, with frozen A2 regressions."""
import argparse
import copy
import json
from pathlib import Path
import statistics
import sys
import time
import tracemalloc

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2')]
import audio1_psg_trace as T
import m5a2.proof as A2
from m5a2.bank import pack,unpack,records,canonical
from m5a2b1.decoder import Decoder
from m5a2b1.preflight import OUT,PUB,BATCH
save,sha=A2.save,A2.sha
OLD=ROOT.parent/'private-research/m5-a2'
CASES={
    **{f'solo-{rid:02X}':(rid,{},end+32) for rid,end in zip(BATCH,(1088,432,300,408,242,179))},
    'THZ-to-invincibility':(0x81,{60:[('request',0x84)]},1180),
    'invincibility-SFX':(0x84,{30:[('request',0xAC)],35:[('request',0xBC)],40:[('request',0xA3)],
                              100:[('request',0xB6)]},1120),
    'rocket-SFX':(0x85,{30:[('request',0xB6)],35:[('request',0xA0)],60:[('request',0xA3)],
                        65:[('request',0xBC)]},464),
    'finite-replace-restart':(0x84,{80:[('request',0x85)],160:[('request',0x85)],250:[('request',0x87)]},700),
    'finite-fade-fresh':(0x84,{30:[('request',0xAC)],40:[('fade',[12,1,2])],80:[('request',0x86)]},412),
    'finite-F8-fresh':(0x85,{40:[('request',0xF8)],70:[('request',0x89)]},350),
    'finite-three-mailboxes':(0x87,{30:[('mailbox',[0xB6,0]),('mailbox',[0xA3,1]),('mailbox',[0xAC,2])]},440),
}


def candidate(bank,case):
    rid,events,ticks=case;m=Decoder(bank);m.direct(rid);rows=[];times=[];work=[]
    for t in range(1,ticks+1):
        for k,v in events.get(t,[]):A2.apply(m,k,v)
        start=time.perf_counter_ns();m.tick();times.append(time.perf_counter_ns()-start)
        row=m.snapshot();row.update(channel_bytes=[list(c) for c in m.ch],shared_IY=m.iy,
            globals=[*m.tempo,m.selected,*m.mail,*m.fade,m.last_sfx,m.noise_offset,m.fade_noise_volume])
        rows.append(row);work.append(m.ops)
    return m,rows,times,work


def run(rom):
    assert sha((OLD/'programs.scsp').read_bytes())=='c0118830a4f7779b8d53d4b6cefd129487633689532e52500cddcd6f4dddfaf1'
    pre=json.loads((PUB/'preflight.json').read_text())
    assert len(pre['rows'])==12 and pre['rows'][:6][0]['request_id']==0x84
    allcases={**{'regression-'+k:v for k,v in A2.CASES.items()},**CASES}
    # Reuse the accepted extraction method, directing its NEW output to this bank.
    oldcases,oldids,olddecoder=A2.CASES,A2.IDS,A2.Decoder
    try:
        A2.CASES=allcases;A2.IDS=oldids+BATCH;A2.Decoder=Decoder
        bank=A2.extract(rom)
    finally:A2.CASES,A2.IDS,A2.Decoder=oldcases,oldids,olddecoder
    blob=pack(bank);OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'programs.scsp').write_bytes(blob);save(OUT/'source-records.json',records(bank))
    bank=unpack(blob);oldbank=unpack((OLD/'programs.scsp').read_bytes())
    assert all(bank['data'][k]==v for k,v in oldbank['data'].items())
    assert all(bank['programs'][k]==v for k,v in oldbank['programs'].items())
    report={}
    for name,case in allcases.items():
        m,rows,times,work=candidate(bank,case)
        # Candidate completed with no oracle execution or expected timeline input.
        rid,events,ticks=case;d=T.Driver(rom);d.request(rid);original=[];fail=[];transfers=[];restores=[]
        def transfer(q):transfers.append((q.update,T.CHANNELS.index(q.cpu.ix),q.mem[q.cpu.de]|q.mem[q.cpu.de+1]<<8))
        d.hook(0x47B4,transfer);d.hook(0x481C,transfer)
        d.hook(0x47F3,lambda q:restores.append(dict(tick=q.update,channel=T.CHANNELS.index(q.cpu.ix),
                                                  data_latch=q.psg.latch//16,byte=q.cpu.a)))
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
            original.append(o)
            fail.extend(dict(tick=t,field=k) for k in o if o[k]!=rows[t-1][k])
            if fail:break
        if not fail and transfers!=[(t,i,q) for t,i,p,q in m.loops]:fail.append(dict(tick=0,field='control-transfers'))
        if name.startswith('regression-'):
            old=json.loads((OLD/(name[11:]+'.json')).read_text())['candidate']
            if len(rows)!=len(old) or any(any(canonical(r[k])!=canonical(x[k]) for k in x) for r,x in zip(rows,old)):
                fail.append(dict(tick=0,field='accepted-A2-private-rows'))
        save(OUT/(name+'.json'),dict(candidate=rows,original=original,failures=fail,case=case,saved_noise_restores=restores))
        inactive=next((i+1 for i,r in enumerate(rows) if not any(x&128 for x in r['channels'])),None)
        report[name]=dict(ticks=ticks,compared_ticks=len(original),status='PASS' if not fail else 'FAIL',failures=fail,
            ordered_bytes=sum(len(r['ports']) for r in rows),max_port_bytes_per_tick=max(len(r['ports']) for r in rows),
            max_stream_operations_per_tick=max(work),opcodes={f'{k:02X}':v for k,v in sorted(m.opcodes.items())},
            first_inactive_tick=inactive,median_decoder_ns=statistics.median(times),max_decoder_ns=max(times))
        print(name,report[name]['status'],fail[:3],flush=True)
    save(PUB/'emission.json',dict(cases=report,zero_tolerance=True,ROM_sha256=T.ROM_SHA256,
        candidate_independent_of_oracle=True,source_sha256={p.relative_to(ROOT).as_posix():sha(p.read_bytes().replace(b'\r\n',b'\n'))
             for p in [Path(__file__),Path(__file__).with_name('decoder.py')]},
        SCSP_version=1,horizon=bank['horizon'],packed_bytes=len(blob),packed_sha256=sha(blob),
        previous_packed_bytes=4285,incremental_packed_bytes=len(blob)-4285,
        data_bytes=len(bank['data']),incremental_data_bytes=len(bank['data'])-len(oldbank['data']),
        header_bytes=sum(p['header_length'] for p in bank['programs'].values()),
        segments=len(records(bank)['segments']),record_json_bytes=len(canonical(records(bank))),
        previous_nine_headers_and_data_unchanged=True))
    assert all(r['status']=='PASS' for r in report.values()),'exact differential failure'


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('rom');a=p.parse_args();run(T.load_rom(a.rom))
