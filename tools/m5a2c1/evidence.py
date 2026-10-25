"""Observed SFX completion, admissions, held output, negative controls and scope."""
import copy
import gc
import json
from pathlib import Path
import statistics
import sys
import time
import tracemalloc

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2')]
from m5a2.bank import pack,unpack
from m5a2.decoder import DecodeError
from m5a2b1.decoder import Decoder
from m5a2b1.proof import candidate
from m5a2c1.proof import OUT,PUB,B2OLD,BATCH,ENDS,CASES,save,sha


def load(name):return json.loads((OUT/(name+'.json')).read_text())


def run():
    blob=(OUT/'programs.scsp').read_bytes();bank=unpack(blob);termination={}
    preflight=json.loads((PUB/'preflight.json').read_text())
    for rid,end in zip(BATCH,ENDS):
        r=load(f'solo-{rid:02X}');rows=r['original']
        assert next(i+1 for i,x in enumerate(rows) if not any(f&128 for f in x['channels']))==end
        assert len(rows)-end==32 and all(not x['ports'] and not any(f&128 for f in x['channels']) for x in rows[end:])
        assert all(x['registers']==rows[end-1]['registers'] for x in rows[end:])
        assert rows[-1]['registers'][2]==[15]*4
        original=next(p for p in preflight['rows'] if p['request_id']==rid)
        assert original['post_inactive_physically_enabled_ticks']==0 and original['post_completion_observed_ticks']==128
        termination[f'{rid:02X}']=dict(inactive_tick=end,candidate_post_ticks=32,original_preflight_post_ticks=128,
           post_completion_port_bytes=0,final_attenuation=rows[-1]['registers'][2],PCM_samples=len(rows)*735,
           original_output_class=original['output_class'],F3_commands=0,owns='tone2',own_DE11_restore=False)
    repeats={}
    for name,rid,ticks in [('ring-repeats',0xBF,[30,32,48,80]),('spring-repeats',0xA6,[30,33,60,100])]:
        expected=[[t,rid] for t in ticks];assert load(name)['SFX_admissions']==expected
        repeats[name]=dict(original_admissions=expected,all_activations_admitted=True)
    rejected=load('replacement-rejection')['SFX_admissions']
    assert rejected==[[30,0xA6],[40,0xA4]]
    recovery={}
    for name in ['THZ-ring','THZ-spring']:
        rows=load(name)['original'];suppressed=[i+1 for i,r in enumerate(rows) if r['channels'][2]&4]
        resume=next(i+1 for i,r in enumerate(rows) if i+1>max(suppressed) and r['channels'][2]&128 and not r['channels'][2]&20)
        recovery[name]=dict(suppression_interval=[min(suppressed),max(suppressed)],suppressed_ticks=len(suppressed),music_tone2_next_read_recovery_tick=resume)
    held={}
    for name,interval,off,release in [('fixed-noise-spring',[34,137],138,139),('hurt-held-noise',[63,166],167,168)]:
        rows=load(name)['original']
        ticks=[i+1 for i,r in enumerate(rows) if r['channels'][6]&128 and r['channels'][6]&16 and r['registers'][2][3]<15]
        assert ticks==list(range(interval[0],interval[1]+1))
        assert rows[off-1]['registers'][2][3]==15 and rows[off-1]['channels'][6]&128
        assert not rows[release-1]['channels'][6]&128
        held[name]=dict(held_noise_ticks=len(ticks),interval=interval,terminal_off_tick=off,stream_release_tick=release,
                       role='previously verified noise partner; new target is tone-only')
    live=load('hurt-concurrent')['original'][34]
    assert all(f&128 for f in live['channels'][4:])
    assert load('coupled-ring')['SFX_admissions']==[[1,0xA3],[6,0xBC],[35,0xBF]]
    # Mutated authentic data, omitted terminal output and missing pointers fail.
    bad=copy.deepcopy(bank)
    for k in bad['data']:
        if 0x4436<=int(k)<0x44C2 and int(k)%2==0:bad['data'][k]^=1
    _,wrong,_,_=candidate(unpack(pack(bad)),CASES['solo-A4']);correct=load('solo-A4')['candidate']
    badtick=next(i+1 for i,(a,b) in enumerate(zip(wrong,correct)) if a['ports']!=b['ports'])
    class MissingTerminal(Decoder):
        def release(self,i):self.ch[i][0]=0
    m=MissingTerminal(bank);m.direct(0xA4);terminal=None
    for t in range(1,115):
        m.tick()
        if m.writes!=correct[t-1]['ports']:terminal=t;break
    assert terminal is not None
    incomplete=copy.deepcopy(bank);p=incomplete['programs'][str(0xA4)]['streams'][0]['pointer'];del incomplete['data'][str(p)]
    m=Decoder(incomplete);m.direct(0xA4)
    try:m.tick()
    except DecodeError:missing=True
    else:raise AssertionError('missing program data accepted')
    timings=[]
    for _ in range(30):
        for rid in BATCH:
            m=Decoder(bank);m.direct(rid)
            for _ in range(CASES[f'solo-{rid:02X}'][2]):
                start=time.perf_counter_ns();m.tick();timings.append(time.perf_counter_ns()-start)
    memory={}
    for name,b in [('previous',(B2OLD/'programs.scsp').read_bytes()),('expanded',blob)]:
        gc.collect();tracemalloc.start();x=unpack(b);m=Decoder(x);m.direct(0x81)
        for _ in range(4200):m.tick()
        current,peak=tracemalloc.get_traced_memory();tracemalloc.stop();memory[name]=dict(current_bytes=current,peak_bytes=peak)
    save(PUB/'facts.json',dict(termination=termination,retrigger_admissions=repeats,
        replacement_priority=dict(original_admitted=rejected,rejected_requests=[[45,0xBF],[50,0xA6],[55,0xBC]]),
        music_recovery=recovery,held_noise=held,concurrent_effect_slots=3,coupled_ring_admitted=True,
        wrong_pitch_data_detected_tick=badtick,missing_terminal_writes_detected_tick=terminal,missing_program_rejected=missing,
        performance=dict(measured_ticks=len(timings),median_ns=statistics.median(timings),p99_ns=sorted(timings)[int(.99*len(timings))],max_ns=max(timings),memory=memory,
             scope='Python decoder/sparse bank with bounded diagnostic flow log; excludes interpreter baseline and PCM; NOT GameMaker performance')))
    coverage=json.loads((ROOT/'data/m5-a2b2/coverage.json').read_text())
    for r in coverage['entries']:
        rid=r['request_id']
        if rid in BATCH:
            r['decoder_status']='fully-decoded-in-tested-scope'
            r['tested_scope']='complete solo +32 ticks; original-only +128 physical check; selected music/noise/retrigger/priority contexts; fresh ROM-free replay'
        if rid in (0xA1,0xA2,0xA7):
            original=next(p for p in preflight['rows'] if p['request_id']==rid)
            r['C1_preflight_only']=dict(output_class=original['output_class'],unverified_opcodes=original['unverified_opcodes'],runtime_record_extracted=False)
    coverage['counts']={s:sum(r['decoder_status']==s for r in coverage['entries']) for s in
        ('fully-decoded-in-tested-scope','partially-decoded','format-understood-but-unverified','unsupported-or-unknown','empty-or-control')}
    coverage['extracted_unique_headers']=24
    coverage['format_understood_but_unverified_note']='A1/A2/A7 original-only C1 preflight; no promotion or runtime records. A2 reaches unsupported FD.'
    coverage['expansion_batches']=[dict(order=1,proposal_only=True,ids=['A1','A2','A7'],
        purpose='Manager-selected focused tone2/raw-frequency FD and coupled-white-noise class proof; do not implement until authorised'),
        dict(order=2,proposal_only=True,ids=['remaining SFX'],purpose='stratify fixed-rate, periodic-noise, tone2-coupled and multi-slot effects, with class-specific context gates'),
        dict(order=3,proposal_only=True,ids=['remaining music'],purpose='separate long/loop and unsupported language/horizon research')]
    save(PUB/'coverage.json',coverage)


if __name__=='__main__':run()
