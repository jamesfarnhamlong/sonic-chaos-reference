"""Source-backed FD gate BEFORE adding A2 to the expanded real runtime bank.

Actual A2 uses original program bytes. Synthetic transition tests execute the
unmodified original driver against explicitly seeded research-only stream data.
"""
import argparse
import copy
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2')]
import audio1_psg_trace as T
import m5a2.proof as A2
from m5a2.bank import canonical
from m5a2.decoder import DecodeError
from m5a2c2.decoder import Decoder

OUT=ROOT.parent/'private-research/m5-a2c2'
PUB=ROOT/'data/m5-a2c2'
save,sha=A2.save,A2.sha


def snapshot(m):
    r=m.snapshot();r.update(channel_bytes=[list(c) for c in m.ch],shared_IY=m.iy,
      globals=[*m.tempo,m.selected,*m.mail,*m.fade,m.last_sfx,m.noise_offset,m.fade_noise_volume])
    return r


def oracle_snapshot(d,start):
    return dict(ports=[v for _,v in d.writes[start:]],registers=d.psg.state(),latch=d.psg.latch//16,
      saved_noise=d.mem[0xDE11],channels=[d.mem[a]&0xD4 for a in T.CHANNELS],priority=d.mem[0xDE0F],
      channel_bytes=[list(d.mem[a:a+48]) for a in T.CHANNELS],shared_IY=d.cpu.iy,
      globals=[d.mem[a] for a in (0xDE01,0xDE02,0xDE03,0xDE04,0xDE05,0xDE06,0xDE09,0xDE0A,0xDE0B,0xDE0D,0xDE15,0xDE16)])


def compare(rom,bank,ticks,seed=None):
    m=Decoder(bank);rows=[]
    if seed:
        m.ch[5][:]=seed['channel'];m.owners[5]=0xA2
    else:m.direct(0xA2)
    for _ in range(ticks):m.tick();rows.append(snapshot(m))
    # No oracle existed during candidate generation.
    d=T.Driver(rom);fd=[];next_reads=[];raw=[]
    if seed:
        d.mem[0xDF30:0xDF60]=bytes(seed['channel'])
        d.mem[seed['pointer']:seed['pointer']+len(seed['stream'])]=bytes(seed['stream'])
    else:d.request(0xA2)
    def before(q):fd.append(dict(tick=q.update,operand=q.cpu.a,DE=q.cpu.de,before=list(q.mem[q.cpu.ix:q.cpu.ix+48])))
    def after(q):
        if fd and 'after' not in fd[-1]:fd[-1].update(after=list(q.mem[q.cpu.ix:q.cpu.ix+48]),handler_return_DE=q.cpu.de)
    d.hook(0x47BA,before);d.hook(0x46E9,after)
    d.hook(0x434F,lambda q:next_reads.append((q.update,q.cpu.de)))
    d.hook(0x43C7,lambda q:raw.append(dict(tick=q.update,first_byte_pointer=q.cpu.de-1,channel=q.cpu.ix)))
    failures=[];original=[]
    for t in range(1,ticks+1):
        start=len(d.writes);d.tick();o=oracle_snapshot(d,start);original.append(o)
        failures.extend(dict(tick=t,field=k) for k in o if o[k]!=rows[t-1][k])
    for event in fd:
        a=event['operand'];before=event['before'];after=event['after']
        expected=before.copy();expected[0]=before[0]|8 if a==1 else before[0]&~8
        assert after==expected and event['handler_return_DE']==event['DE']
        assert (event['tick'],event['DE']+1) in next_reads
    return dict(status='FAIL' if failures else 'PASS',ticks=ticks,failures=failures,FD_events=fd,raw_reads=raw,candidate=rows,original=original)


def run(rom):
    config=A2.CASES,A2.IDS,A2.Decoder
    try:
        A2.CASES={'FD-actual-A2':(0xA2,{},67)};A2.IDS=(0xA2,);A2.Decoder=Decoder
        bank=A2.extract(rom)
    finally:A2.CASES,A2.IDS,A2.Decoder=config
    actual=compare(rom,bank,67);save(OUT/'FD-actual-A2.json',actual)
    assert actual['status']=='PASS' and len(actual['FD_events'])==1
    # Direct handler edge controls check preserved bits and lack of other writes.
    edges=0
    for flags in (0x80,0x88,0xA4,0xFF):
        for operand in (0,1,2,255):
            d=T.Driver(rom);d.cpu.ix=0xDF30;d.cpu.a=operand;d.cpu.de=0xB800
            before=bytes([flags])+bytes(range(1,48));d.mem[0xDF30:0xDF60]=before
            d.call(0x47BA);expected=bytearray(before);expected[0]=flags|8 if operand==1 else flags&~8
            assert bytes(d.mem[0xDF30:0xDF60])==expected and d.cpu.de==0xB800 and not d.writes
            edges+=1
    # Synthetic ordinary->raw->ordinary transitions, with signed transpose,
    # duration multiplication and algorithmic modulation. These are NOT songs.
    probes={}
    for transpose in (-1,0,1):
        for multiplier in (1,2):
            stream=[0xF0,1,1,1,4,0x81,2,0xFD,1,1,32,3,0xFD,0,0x82,2,0xF2,0]
            data=A2.ExtractionData(rom);data.update({str(0xB800+i):v for i,v in enumerate(stream)})
            p=dict(streams=[dict(latch=0xC0,pointer=0xB800,transpose=transpose,volume=0,flags=128)],multiplier=multiplier,tempo=0)
            b=dict(version=1,horizon=4200,priority=bank['priority'],programs={str(0xA2):p},data=data)
            c=bytearray(48);c[:11]=bytes([128,0xC0,multiplier,0,0xB8,transpose&255,0,0,0,48,1])
            # Demand extraction with seeded data precedes the independent oracle.
            mm=Decoder(b);mm.ch[5][:]=c
            for _ in range(24):mm.tick()
            b['data']=dict(data)
            key=f'transpose{transpose}-multiplier{multiplier}'
            result=compare(rom,b,24,dict(channel=list(c),pointer=0xB800,stream=stream))
            save(OUT/('FD-seeded-'+key+'.json'),result)
            assert result['status']=='PASS' and len(result['FD_events'])==2 and result['raw_reads']
            probes[key]=dict(status='PASS',ticks=24,FD_transitions=2,provenance='synthetic seeded stream; original driver code unchanged; not naturally reached game data')
    # Strict negative behavior: no operand, invalid next pointer, or unverified reader.
    bad=copy.deepcopy(bank);p=0xB900;bad['data'][str(p)]=0xFD
    bad['programs'][str(0xA2)]['streams'][0]['pointer']=p
    m=Decoder(bad);m.direct(0xA2)
    try:m.tick()
    except DecodeError:truncated=True
    else:raise AssertionError('truncated FD accepted')
    bad['data'][str(p+1)]=1
    m=Decoder(bad);m.direct(0xA2)
    try:m.tick()
    except DecodeError:invalid_next=True
    else:raise AssertionError('invalid post-FD data pointer accepted')
    m=Decoder(bank)
    try:m.command(3,0xFD,next(iter(map(int,bank['data']))))
    except DecodeError:unsupported=True
    else:raise AssertionError('unverified reader transition accepted')
    safe=dict(status='PASS',ROM_sha256=T.ROM_SHA256,
       source_sha256={p.relative_to(ROOT).as_posix():sha(p.read_bytes().replace(b'\r\n',b'\n')) for p in [Path(__file__),Path(__file__).with_name('decoder.py')]},
       actual_A2=dict(status='PASS',ticks=67,FD_executions=1,
       opcode_bytes_including_operand=2,only_flag_bit3_changed=True,caller_consumption_exact=True,
       raw_reader_visits=len(actual['raw_reads']),source_sha256={f'{a:04X}-{b:04X}':sha(rom[a+0x4000:b+0x4000]) for a,b in
       ((0x47BA,0x47C8),(0x46D5,0x46ED),(0x43C7,0x43E5),(0x41F6,0x422B))}),
       direct_original_handler_edges=edges,seeded_transition_probes=probes,
       truncated_operand_rejected=truncated,invalid_next_pointer_rejected=invalid_next,unsupported_reader_rejected=unsupported,
       gate_boundary='FD enabled only for SFX tone2, selected actual A2 plus explicit synthetic transition controls; no catalogue promotion in this gate')
    save(PUB/'fd-gate.json',safe);print(json.dumps(safe,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('rom');a=p.parse_args();run(T.load_rom(a.rom))
