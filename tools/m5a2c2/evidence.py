"""C2 actual lifetime, FD replacement, F3 admissions and physical-noise evidence."""
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
from m5a2c2.decoder import Decoder
from m5a2c2.proof import OUT,PUB,C1OLD,BATCH,ENDS,CASES,save,sha,candidate


def load(name):return json.loads((OUT/(name+'.json')).read_text())


def run():
    bank=unpack((OUT/'programs.scsp').read_bytes());termination={}
    oldpre=json.loads((ROOT/'data/m5-a2c1/preflight.json').read_text())['rows']
    for rid,end in zip(BATCH,ENDS):
        rows=load(f'solo-{rid:02X}')['original']
        assert next(i+1 for i,r in enumerate(rows) if not any(f&128 for f in r['channels']))==end
        assert len(rows)-end==32 and all(not r['ports'] and not any(f&128 for f in r['channels']) for r in rows[end:])
        assert all(r['registers']==rows[end-1]['registers'] for r in rows[end:])
        assert rows[-1]['registers'][2]==[15]*4
        before=next(r for r in oldpre if r['request_id']==rid)
        assert before['post_inactive_physically_enabled_ticks']==0
        termination[f'{rid:02X}']=dict(inactive_tick=end,post_ticks=32,original_preflight_post_ticks=128,
            final_attenuation=rows[-1]['registers'][2],post_writes=0,PCM_samples=len(rows)*735)
    fd=load('solo-A2')['original'];replace=load('A2-replace-spring')['original']
    assert not fd[0]['channel_bytes'][5][0]&8 and fd[1]['channel_bytes'][5][0]&8 and not fd[34]['channel_bytes'][5][0]&8
    assert replace[32]['channel_bytes'][5][0]&8 and not replace[33]['channel_bytes'][5][0]&8
    gate=json.loads((PUB/'emission.json').read_text());noise={};recover={}
    for name,start in [('THZ-A7-early',30),('THZ-A7-later',73)]:
        r=load(name);rows=r['original'];restores=r['saved_noise_restores']
        assert restores==[dict(tick=start+6,channel=6,data_latch=3,byte=0xE4)]
        assert rows[start-1]['registers'][1]==7
        for i in (2,3):
            suppressed=[t+1 for t,x in enumerate(rows) if x['channels'][i]&4]
            resumed=next(t+1 for t,x in enumerate(rows) if t+1>max(suppressed) and x['channels'][i]&128 and not x['channels'][i]&20)
            recover[f'{name}-music{i}']=dict(suppression=[min(suppressed),max(suppressed)],next_eligible_read_tick=resumed)
        noise[name]=dict(F3_mode=7,F3_executions=gate['cases'][name]['opcodes']['F3'],DE11_restore=restores[0])
    solo=load('solo-A7');assert solo['saved_noise_restores']==[dict(tick=7,channel=6,data_latch=7,byte=0)]
    assert solo['original'][0]['channel_bytes'][6][0]&8
    assert solo['original'][0]['registers'][1]==7 and solo['original'][6]['registers'][2][3]==15
    repeats=load('A7-retrigger')['SFX_admissions'];assert repeats==[[30,0xA7],[32,0xA7],[36,0xA7],[60,0xA7]]
    assert gate['cases']['A7-retrigger']['opcodes']['F3']==4
    assert load('A7-during-A1-blocked')['SFX_admissions']==[[30,0xA1],[65,0xA7]]
    assert load('A7-vs-A3')['SFX_admissions']==[[1,0xA7],[3,0xA3]]
    assert load('A2-retrigger')['SFX_admissions']==[[30,0xA2],[32,0xA2],[50,0xA2]]
    # Direct decoded output drives the persistent PSG; silence does not stop LFSR time.
    from m5a2c2.runtime import render
    from m5a2c2.pcm import DLL
    states={}
    for name in ['solo-A7','A7-retrigger']:
        initial,events,ticks=CASES[name]
        pcm,s=render(bank,dict(initial=initial,events={str(k):v for k,v in events.items()},ticks=ticks),DLL)
        save(OUT/(name+'-native-states.json'),s)
        begin=7 if name=='solo-A7' else 0
        changes=sum(a[21]!=b[21] for a,b in zip(s[begin:-1],s[begin+1:]))
        assert changes>0
        states[name]=dict(LFSR_changes_in_observed_post_or_run_window=changes,noise_core_not_recreated_on_stream_off=True)
    wrong=copy.deepcopy(bank);pointer=wrong['programs'][str(0xA2)]['streams'][0]['pointer'];del wrong['data'][str(pointer)]
    m=Decoder(wrong);m.direct(0xA2)
    try:m.tick()
    except DecodeError:missing=True
    else:raise AssertionError('missing program data accepted')
    class MissingTerminal(Decoder):
        def release(self,i):self.ch[i][0]=0
    m=MissingTerminal(bank);m.direct(0xA7);expected=load('solo-A7')['candidate'];terminal=None
    for t in range(1,40):
        m.tick()
        if m.writes!=expected[t-1]['ports']:terminal=t;break
    assert terminal is not None
    class FDNoOp(Decoder):
        def command(self,i,op,p):return p+1 if op==0xFD else super().command(i,op,p)
    m=FDNoOp(bank);m.direct(0xA2);expected=load('solo-A2')['candidate'];noop=None
    for t in range(1,68):
        m.tick()
        if m.writes!=expected[t-1]['ports']:noop=t;break
    assert noop is not None
    timing=[];active_timing=[];idle_timing=[]
    for _ in range(40):
        for rid in BATCH:
            m=Decoder(bank);m.direct(rid)
            for _ in range(CASES[f'solo-{rid:02X}'][2]):
                active=any(c[0]&128 for c in m.ch) or any(m.mail)
                start=time.perf_counter_ns();m.tick();elapsed=time.perf_counter_ns()-start;timing.append(elapsed)
                (active_timing if active else idle_timing).append(elapsed)
    memory={}
    for name,blob in [('previous',(C1OLD/'programs.scsp').read_bytes()),('expanded',(OUT/'programs.scsp').read_bytes())]:
        gc.collect();tracemalloc.start();b=unpack(blob);m=Decoder(b);m.direct(0x81)
        for _ in range(4200):m.tick()
        current,peak=tracemalloc.get_traced_memory();tracemalloc.stop();memory[name]=dict(current_bytes=current,peak_bytes=peak)
    save(PUB/'facts.json',dict(termination=termination,actual_A2_FD_tick=2,FD_release_clears_mode=True,FD_replacement_initial_flags_restored=True,
        A7_noise=noise,A7_solo_restore=solo['saved_noise_restores'][0],music_recovery=recover,A7_retrigger_admissions=repeats,
        blocked_A7_by_A1_at32=True,blocked_A7_by_A3_at4=True,noise_native_state=states,
        missing_program_rejected=missing,missing_A7_terminal_detected_tick=terminal,FD_noop_detected_tick=noop,
        performance=dict(ticks=len(timing),median_ns=statistics.median(timing),p99_ns=sorted(timing)[int(.99*len(timing))],max_ns=max(timing),memory=memory,
           active_ticks=len(active_timing),active_median_ns=statistics.median(active_timing),idle_post_ticks=len(idle_timing),idle_median_ns=statistics.median(idle_timing),
           scope='Python sparse bank/decoder, bounded log; excludes interpreter base and PCM; NOT GameMaker performance')))
    coverage=json.loads((ROOT/'data/m5-a2c1/coverage.json').read_text())
    for r in coverage['entries']:
        if r['request_id'] in BATCH:
            r['decoder_status']='fully-decoded-in-tested-scope';r['tested_scope']='actual finite +32 post, selected ownership/retrigger/replacement, source-gated FD for A2, fresh ROM-free playback'
            r.pop('C1_preflight_only',None)
    coverage['counts']={s:sum(r['decoder_status']==s for r in coverage['entries']) for s in
        ('fully-decoded-in-tested-scope','partially-decoded','format-understood-but-unverified','unsupported-or-unknown','empty-or-control')}
    coverage['extracted_unique_headers']=27
    coverage['format_understood_but_unverified_note']='A1 A2 A7 independently verified in C2. FD limited to authenticated SFX tone2 reader scope.'
    coverage['expansion_batches']=[dict(order=1,proposal_only=True,ids=['unverified fixed-noise / periodic-noise / repeated-F3 / multi-slot SFX'],
        purpose='Manager-selected small group after original class preflight; no new IDs executed or implemented here'),
        dict(order=2,proposal_only=True,ids=['remaining music and language gaps'],purpose='separate authorisation and loop/horizon budgets')]
    save(PUB/'coverage.json',coverage)


if __name__=='__main__':run()
