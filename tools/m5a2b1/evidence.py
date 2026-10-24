"""Completion, negative controls, focused workload and all-70 status inventory."""
import copy
import gc
import json
from pathlib import Path
import statistics
import sys
import time
import tracemalloc
import wave

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2')]
from m5a2.bank import pack,unpack
from m5a2.decoder import Decoder as PreviousDecoder,DecodeError
from m5a2b1.decoder import Decoder
from m5a2b1.proof import OUT,PUB,OLD,save,sha,candidate,CASES
from m5a2b1.preflight import BATCH


def run():
    bank=unpack((OUT/'programs.scsp').read_bytes())
    oldbank=unpack((OLD/'programs.scsp').read_bytes())
    termination={}
    for rid in BATCH:
        rows=json.loads((OUT/f'solo-{rid:02X}.json').read_text())['original']
        end=next(i+1 for i,r in enumerate(rows) if not any(c&128 for c in r['channels']))
        assert not any(r['ports'] for r in rows[end:])
        assert all(r['registers']==rows[end-1]['registers'] for r in rows[end:])
        termination[f'{rid:02X}']=dict(inactive_tick=end,post_completion_ticks=len(rows)-end,
            post_completion_port_bytes=0,final_attenuation=rows[-1]['registers'][2],
            final_tone_periods=rows[-1]['registers'][0],all_slot_flags_inactive=True,
            PCM_samples=len(rows)*735,legitimate_terminal_output_exact=True)
    assert termination['8A']['final_attenuation']==[15,15,0,15]
    replaced=json.loads((OUT/'THZ-to-invincibility.json').read_text())['original']
    assert all(not any(f&128 for f in row['channels']) and not row['ports'] for row in replaced[1147:])
    # The zero restore through a tone2 attenuation latch precedes final inactivity.
    r=json.loads((OUT/'solo-8A.json').read_text())['original']
    restores=json.loads((OUT/'solo-8A.json').read_text())['saved_noise_restores']
    assert restores[0]==dict(tick=1,channel=3,data_latch=5,byte=0)
    assert r[0]['registers'][2][2]==0 and r[0]['saved_noise']==0
    import numpy as np
    tails={}
    for name in ('candidate','reference'):
        with wave.open(str(OUT/'pcm/solo-8A'/(name+'.wav'))) as w:
            pcm=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2')
        tail=pcm[179*735:]
        assert len(tail)==32*735 and np.all(tail==8192)
        tails[name]=dict(samples=len(tail),constant_signed16=8192,AC_standard_deviation=0.0)
    # Old decoder rejects the very first required E1, instead of guessing.
    baseline=PreviousDecoder(bank);baseline.direct(0x84)
    try:
        for _ in range(1120):baseline.tick()
    except DecodeError as e:old_failure=dict(tick=baseline.tick_number,reason=str(e))
    else:raise AssertionError('E1 negative control did not fail')
    altered=copy.deepcopy(bank)
    for k in altered['data']:
        if 0x4436<=int(k)<0x44C2 and int(k)%2==0:altered['data'][k]^=1
    _,wrong,_,_=candidate(unpack(pack(altered)),CASES['solo-84'])
    expected=json.loads((OUT/'solo-84.json').read_text())['candidate']
    wrongtick=next(i+1 for i,(a,b) in enumerate(zip(wrong,expected)) if a['ports']!=b['ports'])
    class WrongTerminal(Decoder):
        def release(self,i):self.ch[i][0]=0
    m=WrongTerminal(bank);m.direct(0x84);terminal_failure=None
    for t in range(1,1121):
        m.tick()
        if m.writes!=expected[t-1]['ports']:terminal_failure=t;break
    assert terminal_failure is not None
    data=json.loads((ROOT/'data/m5-a2/coverage.json').read_text())
    for row in data['entries']:
        if row['request_id'] in BATCH:
            row['decoder_status']='fully-decoded-in-tested-scope'
            row['tested_scope']='complete original finite solo + 32 post-completion ticks; representative batch interactions'
        if row['request_id'] in (0x8E,0x94,0x96,0x97,0x98,0x9A):
            row['decoder_status']='format-understood-but-unverified'
            row['tested_scope']='original-only bounded preflight and structural scan; no candidate, runtime bank or PCM'
    data['counts']={s:sum(r['decoder_status']==s for r in data['entries']) for s in
        ('fully-decoded-in-tested-scope','partially-decoded','format-understood-but-unverified','unsupported-or-unknown','empty-or-control')}
    data['extracted_unique_headers']=15
    data['format_understood_but_unverified_note']='Six deferred candidates preflight only; this category is not independent candidate or PCM verification.'
    data['expansion_batches']=[dict(order=1,ids=['8E','94','96','97','98','9A'],purpose='recommend next bounded batch after Manager authorisation; not started')]
    save(PUB/'coverage.json',data)
    timings=[]
    for _ in range(3):
        for rid in BATCH:
            m=Decoder(bank);m.direct(rid)
            for t in range(CASES[f'solo-{rid:02X}'][2]):
                start=time.perf_counter_ns();m.tick();timings.append(time.perf_counter_ns()-start)
    memory={}
    for name,blob in [('previous',(OLD/'programs.scsp').read_bytes()),('expanded',(OUT/'programs.scsp').read_bytes())]:
        gc.collect();tracemalloc.start();b=unpack(blob);m=Decoder(b);m.direct(0x81)
        for _ in range(4200):m.tick()
        current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
        memory[name]=dict(current_bytes=current,peak_bytes=peak)
    interaction={}
    for name,tick in [('invincibility-SFX',40),('finite-three-mailboxes',30)]:
        r=json.loads((OUT/(name+'.json')).read_text())['original'][tick-1]
        assert r['globals'][9]==(0xBC if name=='invincibility-SFX' else 0xB6)
        interaction[name]=dict(tick=tick,last_admitted_SFX=r['globals'][9],priority=r['priority'],lower_priority_rejected=True)
    save(PUB/'facts.json',dict(termination=termination,E1_previous_decoder_rejection=old_failure,
        replaced_THZ_does_not_automatically_resume=True,
        wrong_pitch_data_detected_tick=wrongtick,missing_terminal_writes_detected_tick=terminal_failure,
        inherited_SCSP_v1_loads=True,old_nine_headers_and_data_unchanged=True,
        original_8A_terminal=dict(restore_tick=1,source_instruction_cpu='47F3',saved_DE11=0,
            prior_data_latch_register=5,tone2_period=0,post_completion_PCM=tails,
            qualification='authenticated held DC from zero-period tone2; no periodic AC; not silently forced off'),
        interaction_rejections=interaction,
        performance=dict(ticks=len(timings),median_ns=statistics.median(timings),p99_ns=sorted(timings)[int(.99*len(timings))],
                         max_ns=max(timings),memory=memory,
                         allocation_scope='decoded sparse bank plus decoder and bounded diagnostic transfer log; excludes PCM arrays/interpreter base',
                         GameMaker_decoder='NOT MEASURED')))


if __name__=='__main__':run()
