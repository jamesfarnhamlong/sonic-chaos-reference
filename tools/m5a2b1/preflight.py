"""Twelve finite candidates: bounded structural scan + original execution, no PCM."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2')]
import audio1_psg_trace as T
from m5a2.proof import save,sha

OUT=ROOT.parent/'private-research/m5-a2b1'
PUB=ROOT/'data/m5-a2b1'
IDS=(0x84,0x85,0x86,0x87,0x89,0x8A,0x8E,0x94,0x96,0x97,0x98,0x9A)
BATCH=IDS[:6]
SUPPORTED={0xE0,0xE6,0xE7,0xF0,0xF2,0xF3,0xF5,0xF6,0xF7,0xF8,0xF9,0xFB}
# Lengths recovered from original dispatch handlers, not inferred from song data.
LENGTH={0xE0:6,0xE1:2,0xE2:2,0xE4:2,0xE5:2,0xE6:2,0xE7:1,0xE8:2,0xED:2,
        0xF0:5,0xF2:1,0xF3:2,0xF4:2,0xF5:2,0xF6:3,0xF7:5,0xF8:3,0xF9:1,0xFA:2,0xFB:2,0xFD:2}


def structural(rom,header):
    def byte(p):
        if not 0x4800<=p<0xC000:raise ValueError('stream outside bounded data')
        return rom[p+0x4000]
    def word(p):return byte(p)|byte(p+1)<<8
    seen=set();commands=Counter();unknown=set();calls=loops=jumps=ends=0;maxstack=0
    todo=[(s['stream_cpu'],i==3,(),False) for i,s in enumerate(header['channels'])]
    while todo:
        p,noise,stack,raw=todo.pop();key=(p,noise,stack,raw)
        if key in seen:continue
        seen.add(key)
        if len(seen)>20000:raise ValueError('static work bound')
        a=byte(p)
        if a>=0xE0:
            commands[a]+=1
            if a not in LENGTH:unknown.add(a);continue
            q=p+LENGTH[a]
            if a==0xF2:ends+=1;continue
            if a==0xF6:jumps+=1;todo.append((word(p+1),noise,stack,raw));continue
            if a==0xF7:
                loops+=1;todo.append((word(p+3),noise,stack,raw))
            if a==0xF8:
                calls+=1
                if len(stack)>=3:raise ValueError('static call stack bound')
                maxstack=max(maxstack,len(stack)+1)
                todo.append((word(p+1),noise,stack+(q,),raw));continue
            if a==0xF9:
                if not stack:raise ValueError('static return underflow')
                todo.append((stack[-1],noise,stack[:-1],raw));continue
            if a==0xFD:raw=byte(p+1)==1
        elif not noise and raw:q=p+3
        elif a<128 or not noise and a>=0xD8:q=p+1
        else:q=p+1+(byte(p+1)<128)
        todo.append((q,noise,stack,raw))
    return dict(nodes=len(seen),potential_opcodes=[f'{x:02X}' for x in sorted(commands)],
        unclassified_opcodes=[f'{x:02X}' for x in sorted(unknown)],call_sites=calls,
        counted_loop_sites=loops,jump_sites=jumps,termination_sites=ends,max_call_depth=maxstack,
        qualification='structural overapproximation of counted-loop branches with bounded call contexts; not arbitrary corrupt-data reachability')


def run(rom):
    old={r['request_id']:r for r in json.loads((ROOT/'data/m5/catalogue.json').read_text())['entries']}
    rows=[]
    for rid in IDS:
        header=T.header_facts(rom,rid);scan=structural(rom,header)
        d=T.Driver(rom);ops=Counter();envs=set();pitch=set();gate=set();modes=set();iy_reads=Counter();fine=Counter();adsr_states=Counter()
        def command(q):
            ops[q.cpu.a]+=1
            if q.cpu.a==0xE1:
                v=q.mem[q.cpu.de];fine['negative' if v&128 else 'positive' if v else 'zero']+=1
        d.hook(0x46D9,command)
        d.hook(0x4546,lambda q:envs.add(q.mem[q.cpu.ix+8]))
        d.hook(0x42AF,lambda q:pitch.add(q.mem[q.cpu.ix+7]))
        d.hook(0x42F6,lambda q:iy_reads.update([q.cpu.iy]))
        d.hook(0x45E6,lambda q:gate.add(q.mem[q.cpu.ix+8]))
        d.hook(0x4292,lambda q:modes.add(q.mem[q.cpu.ix+30]))
        d.hook(0x454E,lambda q:adsr_states.update([q.mem[q.cpu.ix+29]&0xF8]))
        d.request(rid);end=None
        for t in range(1,1501):
            d.tick()
            if not d.active():end=t;break
        if end is None:raise ValueError(f'{rid:02X} exceeded short finite preflight budget')
        newops=set(ops)-SUPPORTED
        table_pitch=any(0<x<128 for x in pitch)
        envelopes=[]
        for selector in sorted(x for x in envs if 0<x<128):
            base=T.u16(rom,0x49FD+0x4000+2*(selector-1));n=0
            for n in range(256):
                control=rom[base+0x4000+n]
                if control>=128:break
            else:raise ValueError('envelope scan bound')
            envelopes.append(dict(selector=selector,ordinary_steps_before_control=n,
                                  first_control=f'{control:02X}',known_control=control in (0x80,0x81,0x82)))
        sufficient=not newops and not table_pitch and header['envelope_table_cpu']==0x49FD
        row=dict(request_id=rid,label=old[rid]['friendly_name'],authorised_implementation=rid in BATCH,
            header=header,original_inactive_tick=end,inherited_inactive_tick=old[rid]['execution']['finite_inactive_tick'],
            reached_opcodes={f'{x:02X}':v for x,v in sorted(ops.items())},static=scan,
            reached_envelope_selectors=sorted(envs),reached_pitch_selectors=sorted(pitch),reached_ADSR_modes=sorted(modes),
            table_envelope_preflight=envelopes,algorithmic_envelope_state_visits={f'{k:02X}':v for k,v in sorted(adsr_states.items())},
            E1_signed_operand_classes=dict(fine),
            unverified_stream_opcodes=[f'{x:02X}' for x in sorted(newops)],
            table_pitch_required=table_pitch,volume_envelope_class='algorithmic and/or table; selectors listed, internal table control branches not yet independently verified',
            M5A2_stream_whitelist_sufficient=sufficient,
            complexity='low: existing reached command/pitch classes; full state still requires candidate gate' if sufficient else 'focused original-language extension required',
            coverage_promotion=False,new_PCM_renders=0,unverified_paths=['context-dependent interference','internal envelope table controls not yet candidate-checked']+
            ([] if sufficient else ['new opcode, pitch class or envelope base']),
            original_final_attenuation=list(d.psg.att))
        rows.append(row)
        print(f'{rid:02X}',end,row['reached_opcodes'],'pitch',sorted(pitch),'env',sorted(envs),'sufficient',sufficient)
    save(PUB/'preflight.json',dict(ROM_sha256=T.ROM_SHA256,rows=rows,static_algorithm='bounded syntax/control-flow scan; both counted-loop outcomes; call/return contexts',
        execution='unmodified original Z80 driver until all slots inactive; no PCM; no decoder expansion before this inventory',
        scope='all twelve preflight only; exactly six authorised for implementation'))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('rom');a=p.parse_args();run(T.load_rom(a.rom))
