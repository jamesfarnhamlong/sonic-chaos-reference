"""Operation-level candidate/original gate; diagnostic subclass changes no semantics."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2')]
import audio1_psg_trace as T
from m5a2.bank import unpack,canonical
from m5a2c2.decoder import Decoder
from m5a2c6.proof import OUT,PUB,CASES,save,sha

OPS={0xE6,0xF0,0xF5,0xF7,0xF8,0xF9,0xFB}


class TraceDecoder(Decoder):
    def __init__(self,bank):
        self.commands=[];self.pitches=[];self.reloads=[];self.entries=[];self.in_envelope=None
        super().__init__(bank)

    def command(self,i,op,p):
        if i!=5 or op not in OPS:return super().command(i,op,p)
        before=dict(tick=self.tick_number,opcode=op,pointer=p,channel=list(self.ch[i]),IY=self.iy)
        result=super().command(i,op,p)
        self.commands.append(dict(before=before,after=dict(pointer=result,channel=list(self.ch[i]),IY=self.iy)))
        return result

    def pitch(self,c):
        if c is not self.ch[5]:return super().pitch(c)
        before=dict(tick=self.tick_number,channel=list(c),IY=self.iy)
        reload=bool(c[7]&128 and c[20]==1 and c[23]==1)
        step=c[22];result=super().pitch(c)
        self.pitches.append(dict(before=before,after=dict(frequency=result,channel=list(c),IY=self.iy)))
        if reload:self.reloads.append(dict(tick=self.tick_number,source=self.iy+3,value=c[23],step_before=step))
        return result

    def env(self,c):
        previous=self.in_envelope
        if c is self.ch[5] and 0<c[8]<128:self.in_envelope=(c[8],self.word(0x49FD+2*(c[8]-1)))
        else:self.in_envelope=None
        try:return super().env(c)
        finally:self.in_envelope=previous

    def byte(self,p):
        value=super().byte(p)
        if self.in_envelope:
            selector,base=self.in_envelope;c=self.ch[5]
            if p==base+c[31]:self.entries.append(dict(tick=self.tick_number,selector=selector,index=c[31],address=p,value=value))
        return value


def run(rom):
    bank=unpack((OUT/'programs.scsp').read_bytes());results={}
    for name,(rid,events,ticks) in CASES.items():
        m=TraceDecoder(bank);m.direct(rid)
        for tick in range(1,ticks+1):
            for kind,value in events.get(tick,[]):
                if kind=='request':m.direct(value)
                elif kind=='fade':m.fade=list(value)
            m.tick()
        # All candidate operations completed before independent original hooks exist.
        d=T.Driver(rom);commands=[];pitches=[];reloads=[];entries=[];pending_command=None;pending_pitch=None
        def command(q):
            nonlocal pending_command
            if q.cpu.ix==T.CHANNELS[5] and q.cpu.a in OPS:
                pending_command=dict(tick=q.update,opcode=q.cpu.a,pointer=q.cpu.de,channel=list(q.mem[q.cpu.ix:q.cpu.ix+48]),IY=q.cpu.iy)
        def command_return(q):
            nonlocal pending_command
            if pending_command is not None:
                commands.append(dict(before=pending_command,after=dict(pointer=(q.cpu.de+1)&65535,channel=list(q.mem[q.cpu.ix:q.cpu.ix+48]),IY=q.cpu.iy)));pending_command=None
        def pitch(q):
            nonlocal pending_pitch
            if q.cpu.ix==T.CHANNELS[5]:pending_pitch=dict(tick=q.update,channel=list(q.mem[q.cpu.ix:q.cpu.ix+48]),IY=q.cpu.iy)
        def pitch_return(q):
            nonlocal pending_pitch
            if pending_pitch is not None:
                pitches.append(dict(before=pending_pitch,after=dict(frequency=q.cpu.hl,channel=list(q.mem[q.cpu.ix:q.cpu.ix+48]),IY=q.cpu.iy)));pending_pitch=None
        def reload(q):
            if q.cpu.ix==T.CHANNELS[5]:reloads.append(dict(tick=q.update,source=q.cpu.iy+3,value=q.mem[q.cpu.iy+3],step_before=q.mem[q.cpu.ix+22]))
        def entry(q):
            if q.cpu.ix!=T.CHANNELS[5]:return
            selector=q.mem[q.cpu.ix+8];index=q.mem[q.cpu.ix+31]
            base=q.mem[0x49FD+2*(selector-1)]|q.mem[0x49FE+2*(selector-1)]<<8
            entries.append(dict(tick=q.update,selector=selector,index=index,address=base+index,value=q.cpu.a))
        for address,callback in [(0x46D9,command),(0x46E9,command_return),(0x42AF,pitch),(0x4502,pitch_return),(0x42F6,reload),(0x4610,entry)]:d.hook(address,callback)
        d.request(rid)
        for tick in range(1,ticks+1):
            for kind,value in events.get(tick,[]):
                if kind=='request':d.request(value)
                elif kind=='fade':d.mem[0xDE09:0xDE0C]=bytes(value)
            d.tick()
        original=dict(commands=commands,pitches=pitches,reloads=reloads,entries=entries)
        candidate=dict(commands=m.commands,pitches=m.pitches,reloads=m.reloads,entries=m.entries)
        save(OUT/(name+'-operations.json'),dict(original=original,candidate=candidate))
        for key in original:
            if original[key]!=candidate[key]:
                pair=next(((i,a,b) for i,(a,b) in enumerate(zip(original[key],candidate[key])) if a!=b),None)
                raise AssertionError((name,key,len(original[key]),len(candidate[key]),pair))
        results[name]=dict(status='PASS',command_operations=len(commands),pitch_operations=len(pitches),reload_operations=len(reloads),envelope_entries=len(entries),
            command_counts={f'{k:02X}':v for k,v in sorted(Counter(x['before']['opcode'] for x in commands).items())},
            operation_sha256=sha(canonical(original)),reload_sources={f'{k:04X}':v for k,v in sorted(Counter(x['source'] for x in reloads).items())},
            table_envelope_visits={str(selector):dict(visits=sum(e['selector']==selector for e in entries),indices=sorted({e['index'] for e in entries if e['selector']==selector}),controls=sorted({f"{e['value']:02X}" for e in entries if e['selector']==selector and e['value']>=128})) for selector in sorted({e['selector'] for e in entries})})
        print(name,'operation gate PASS',flush=True)
    solo={}
    for name in ['solo-B4','solo-BD','solo-C2']:
        r=json.loads((OUT/(name+'-operations.json')).read_text())['original']
        loops=[x for x in r['commands'] if x['before']['opcode']==0xF7]
        transposes=[x for x in r['commands'] if x['before']['opcode']==0xFB]
        solo[name]=dict(reload_ticks=[x['tick'] for x in r['reloads']],reload_values=sorted({x['value'] for x in r['reloads']}),
            F7_ticks=[x['before']['tick'] for x in loops],FB_ticks=[x['before']['tick'] for x in transposes],
            F7_return_targets={f"{k:04X}":v for k,v in sorted(Counter(x['after']['pointer'] for x in loops).items())},
            counted_branches_taken=sum(x['after']['pointer']!=x['before']['pointer']+4 for x in loops),
            counted_fallthroughs=sum(x['after']['pointer']==x['before']['pointer']+4 for x in loops),
            transpose_updates_exact=True,command_channel_before_after_exact=True,pitch_channel_before_after_exact=True,
            qualification='complete detailed per-operation channel states and source values retained privately; summaries do not publish sound-program payload')
    save(PUB/'operations.json',dict(cases=results,solo=solo,zero_tolerance=True,independent_candidate_first=True,decoder_semantics_changed=False,
        hooks=dict(command_entry='46D9',after_handler_before_caller_increment='46E9',pitch_entry='42AF',pitch_return='4502',shared_IY_reload='42F6',volume_table_value='4610'),
        diagnostic_source_sha256=sha(Path(__file__).read_bytes().replace(b'\r\n',b'\n'))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('rom');a=p.parse_args();run(T.load_rom(a.rom))
