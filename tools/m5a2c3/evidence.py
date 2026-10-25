"""Authentic F3 reset/counter, ownership, terminal and negative-control facts."""
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
from m5a2.bank import unpack
from m5a2c2.decoder import Decoder
from m5a2c3.proof import OUT,PUB,C2OLD,BATCH,ENDS,CASES,save,sha
from m5a2c3.noise_diagnostic import observe,wav
import numpy as np


def load(name):return json.loads((OUT/(name+'.json')).read_text())


def run():
    bank=unpack((OUT/'programs.scsp').read_bytes());pre=json.loads((PUB/'preflight.json').read_text())['rows']
    terminal={};resets={};negative={}
    for rid,end in zip(BATCH,ENDS):
        name=f'solo-{rid:02X}';r=load(name);rows=r['original']
        assert next(i+1 for i,x in enumerate(rows) if not any(f&128 for f in x['channels']))==end
        assert len(rows)-end==32 and all(not x['ports'] and not any(f&128 for f in x['channels']) for x in rows[end:])
        assert all(x['registers']==rows[end-1]['registers'] for x in rows[end:]) and rows[-1]['registers'][2]==[15]*4
        original=next(x for x in pre if x['request_id']==rid)
        assert original['post_completion_observed_ticks']==128 and original['post_inactive_physically_enabled_ticks']==0
        pcm,state=observe(bank,CASES[name]);save(OUT/(name+'-native.json'),state)
        expected=original['original_F3_native_diagnostics'];actual=state['controls']
        assert len(expected)==len(actual)
        for a,b in zip(actual,expected):assert all(a[k]==b[k] for k in a)
        terminal[f'{rid:02X}']=dict(inactive_tick=end,candidate_post_ticks=32,original_preflight_post_ticks=128,
            final_attenuation=rows[-1]['registers'][2],post_writes=0,PCM_samples=len(rows)*735)
        resets[f'{rid:02X}']=dict(F3_ticks=[x['tick'] for x in actual],modes=[x['mode'] for x in actual],
            original_and_decoded_instant_core_states_equal=True)
        if rid in (0xB0,0xB7):
            second=actual[1];assert second['RNG_before']!=second['RNG_after'] and second['RNG_after']==32768
            assert second['noise_counter_before']==second['noise_counter_after']==21
            resets[f'{rid:02X}']['second_write']=second
            wrong,badstate=observe(bank,CASES[name],deduplicate_noise_controls=True)
            differences=sum(a['RNG']!=b['RNG'] for a,b in zip(state['frames'],badstate['frames']))
            error=int(np.abs(pcm.astype(np.int32)-wrong.astype(np.int32)).max())
            assert differences>0 and error>0
            wav(OUT/(name+'-negative-dedup.wav'),wrong)
            negative[f'{rid:02X}']=dict(dropped_duplicate_noise_control=True,LFSR_mismatching_ticks=differences,max_signed16_error=error,
                verdict='FAIL as intended; register control value alone would miss the reset')
    multi=load('solo-BA')['original'];assert sum(bool(f&128) for f in multi[0]['channels'][4:])==2
    assert not multi[4]['channels'][6]&128 and multi[4]['channels'][4]&128
    assert not multi[24]['channels'][4]&128
    admissions={name:load(name)['SFX_admissions'] for name in ['B0-retrigger','B7-retrigger','BA-retrigger','B7-block-ring','BA-priority-noise-replace']}
    gate=json.loads((PUB/'emission.json').read_text());counts={name:gate['cases'][name]['opcodes'].get('F3',0) for name in admissions}
    assert admissions['B7-block-ring']==[[1,0xB7],[8,0xBF]]
    assert admissions['BA-priority-noise-replace']==[[30,0xBA],[33,0xB7]]
    concurrent=load('BA-concurrent-hurt')['original'][31];assert all(f&128 for f in concurrent['channels'][4:])
    native_context={};pcm_gate=json.loads((PUB/'pcm.json').read_text())
    for name in ['B0-tone2-interrupt','BA-concurrent-hurt','BA-retrigger']:
        _,native=observe(bank,CASES[name]);save(OUT/(name+'-native.json'),native)
        assert not pcm_gate['cases'][name]['register_counter_LFSR_failures']
        f=native['frames'];muted=sum(a['RNG']!=b['RNG'] for a,b in zip(f,f[1:]) if a['noise_attenuation']==15 and b['noise_attenuation']==15)
        native_context[name]=dict(core_state_reference_exact=True,noise_modes=sorted({r['noise_control']&7 for r in f}),
            noise_counter_range=[min(r['noise_counter'] for r in f),max(r['noise_counter'] for r in f)],
            tone2_period_values=len({r['tone2_register'] for r in f}),RNG_changes_across_muted_frame_pairs=muted)
    restores={name:load(name)['saved_noise_restores'] for name in ['solo-B0','solo-B7','solo-BA','THZ-B0','THZ-B7','THZ-BA']}
    clock_pcm,clock=observe(bank,CASES['B7-to-music98']);save(OUT/'B7-to-music98-native.json',clock)
    frames=[r for r in clock['frames'] if r['tick']>=15 and r['noise_control']==3]
    periods=sorted({r['tone2_register'] for r in frames});assert len(periods)>1 and all(r['noise_attenuation']==15 for r in frames)
    assert any(r['music_tone2_flags']&128 and not r['music_tone2_flags']&4 and r['tone2_register'] for r in frames)
    recover={}
    for name in ['THZ-B0','THZ-B7','THZ-BA']:
        rows=load(name)['original']
        for i in (1,2,3):
            suppressed=[t+1 for t,r in enumerate(rows) if r['channels'][i]&4]
            if not suppressed:continue
            resumed=next(t+1 for t,r in enumerate(rows) if t+1>max(suppressed) and r['channels'][i]&128 and not r['channels'][i]&20)
            recover[f'{name}-music{i}']=dict(suppression=[min(suppressed),max(suppressed)],next_read=resumed)
    class MissingTerminal(Decoder):
        def release(self,i):self.ch[i][0]=0
    m=MissingTerminal(bank);m.direct(0xBA);expected=load('solo-BA')['candidate'];failure=None
    for t in range(1,58):
        m.tick()
        if m.writes!=expected[t-1]['ports']:failure=t;break
    assert failure is not None
    times=[];active_times=[];idle_times=[]
    for _ in range(50):
        for rid in BATCH:
            m=Decoder(bank);m.direct(rid)
            for _ in range(CASES[f'solo-{rid:02X}'][2]):
                active=any(c[0]&128 for c in m.ch) or any(m.mail)
                start=time.perf_counter_ns();m.tick();elapsed=time.perf_counter_ns()-start;times.append(elapsed)
                (active_times if active else idle_times).append(elapsed)
    memory={}
    for name,blob in [('previous',(C2OLD/'programs.scsp').read_bytes()),('expanded',(OUT/'programs.scsp').read_bytes())]:
        gc.collect();tracemalloc.start();b=unpack(blob);m=Decoder(b);m.direct(0x81)
        for _ in range(4200):m.tick()
        current,peak=tracemalloc.get_traced_memory();tracemalloc.stop();memory[name]=dict(current_bytes=current,peak_bytes=peak)
    save(PUB/'facts.json',dict(termination=terminal,F3_reset_evidence=resets,duplicate_control_negative=negative,
        BA_simultaneous_solo_slots=2,BA_noise_slot_release_tick=5,BA_tone1_release_tick=25,BA_with_hurt_simultaneous_slots=3,
        admissions=admissions,F3_counts=counts,music_recovery=recover,BA_missing_terminal_detected_tick=failure,
        native_interference=native_context,DE11_restore_contexts=restores,
        music_clock=dict(noise_mode=3,music_tone2_periods=periods,noise_muted=True,frames=len(frames),
            qualification='actual post-B7 retained periodic control clocked by later music while muted; not audible noise under a simultaneous music owner'),
        performance=dict(ticks=len(times),median_ns=statistics.median(times),p99_ns=sorted(times)[int(.99*len(times))],max_ns=max(times),
            active_ticks=len(active_times),active_median_ns=statistics.median(active_times),idle_ticks=len(idle_times),idle_median_ns=statistics.median(idle_times),memory=memory,
            scope='Python sparse bank/decoder and bounded diagnostics, excludes interpreter base/PCM; NOT GameMaker performance')))
    coverage=json.loads((ROOT/'data/m5-a2c2/coverage.json').read_text())
    for r in coverage['entries']:
        if r['request_id'] in BATCH:
            r['decoder_status']='fully-decoded-in-tested-scope';r['tested_scope']='complete solo +32 post, original-only +128 physical check, selected noise/retrigger/priority/multi-slot contexts and ROM-free replay'
    coverage['counts']={s:sum(r['decoder_status']==s for r in coverage['entries']) for s in
       ('fully-decoded-in-tested-scope','partially-decoded','format-understood-but-unverified','unsupported-or-unknown','empty-or-control')}
    coverage['extracted_unique_headers']=30
    coverage['format_understood_but_unverified_note']='C3 B0 B7 BA now verified in scope; unsupported original-language/reader boundaries remain unchanged.'
    coverage['expansion_batches']=[dict(order=1,proposal_only=True,ids=['unverified single-F3 coupled-white effects and remaining tone2 effects'],
        purpose='Manager-selected small batch after original-only opcode, lifetime and ownership preflight; no additional IDs executed here'),
        dict(order=2,proposal_only=True,ids=['remaining music / language gaps'],purpose='separate loop, horizon and command authorisation')]
    save(PUB/'coverage.json',coverage)


if __name__=='__main__':run()
