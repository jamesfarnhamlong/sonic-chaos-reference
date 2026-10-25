"""C4 measured single-control, ownership, native continuity and frozen regression evidence."""
import argparse
import gc
import json
from pathlib import Path
import statistics
import sys
import time
import tracemalloc

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2')]
import numpy as np
import audio1_psg_trace as T
from m5a2.bank import unpack
from m5a2c2.decoder import Decoder
from m5a2c3.original_noise import OriginalNoise
from m5a2c3.noise_diagnostic import observe,wav
from m5a2c4.proof import OUT,PUB,C3OLD,BATCH,ENDS,CASES,save


class AllControls(OriginalNoise):
    def __init__(self,rom):
        self.all_controls=[]
        super().__init__(rom)

    def _out(self,port,value):
        control=port&255 in (0x7E,0x7F) and value&128 and value>>4&7==6
        if control:before=self.native.state()
        super()._out(port,value)
        if control:
            after=self.native.state()
            self.all_controls.append(dict(tick=self.update,byte=value,mode=value&7,RNG_before=before[21],RNG_after=after[21],
                noise_counter_before=before[16],noise_counter_after=after[16],tone2_period=after[11],noise_period=after[12]))


def load(name):return json.loads((OUT/(name+'.json')).read_text())


def run(rom):
    bank=unpack((OUT/'programs.scsp').read_bytes());pre=json.loads((PUB/'preflight.json').read_text())['rows']
    gate=json.loads((PUB/'emission.json').read_text());pcm_gate=json.loads((PUB/'pcm.json').read_text())
    terminal={};native_context={};controls={};negatives={}
    # Complete decoded-data synthesis before creating the independent Z80 in every case.
    for name,case in CASES.items():
        pcm,native=observe(bank,case)
        initial,events,ticks=case;d=AllControls(rom);d.request(initial);reference=[]
        for tick in range(1,ticks+1):
            for kind,value in events.get(tick,[]):
                if kind=='request':d.request(value)
                elif kind=='fade':d.mem[0xDE09:0xDE0C]=bytes(value)
            d.tick();s=d.native.state()
            reference.append(dict(tick=tick,noise_control=s[6],noise_attenuation=s[7],tone2_register=s[4],tone2_period=s[11],
              noise_period=s[12],noise_counter=s[16],RNG=s[21],music_tone2_flags=d.mem[T.MUSIC_CH[2]],SFX_flags=[d.mem[a] for a in T.SFX_CH]))
        assert reference==native['frames'],name
        assert d.all_controls==native['controls'],name
        assert len(d.F3_states)==gate['cases'][name]['opcodes'].get('F3',0),name
        assert not pcm_gate['cases'][name]['register_counter_LFSR_failures']
        save(OUT/(name+'-native.json'),dict(candidate=native,original=dict(frames=reference,controls=d.F3_states)))
        d.close();f=native['frames'];c=[{k:v for k,v in r.items() if k!='qualification'} for r in d.F3_states];controls[name]=c
        muted=sum(a['RNG']!=b['RNG'] for a,b in zip(f,f[1:]) if a['noise_attenuation']==15 and b['noise_attenuation']==15)
        native_context[name]=dict(core_state_reference_exact=True,F3_count=len(c),F3_ticks=[x['tick'] for x in c],F3_modes=[x['mode'] for x in c],
            instant_F3_states_exact=True,all_F3_preserve_noise_countdown=all(x['noise_counter_before']==x['noise_counter_after'] for x in c),
            tone2_period_values=len({x['tone2_register'] for x in f}),noise_counter_range=[min(x['noise_counter'] for x in f),max(x['noise_counter'] for x in f)],
            RNG_changes_across_muted_frame_pairs=muted,maximum_simultaneous_SFX_slots=max(sum(bool(v&128) for v in x['SFX_flags']) for x in f))
    for rid,end in zip(BATCH,ENDS):
        name=f'solo-{rid:02X}';r=load(name);rows=r['original'];original=next(x for x in pre if x['request_id']==rid)
        assert next(i+1 for i,x in enumerate(rows) if not any(f&128 for f in x['channels']))==end
        assert len(rows)-end==32 and all(not x['ports'] and not any(f&128 for f in x['channels']) for x in rows[end:])
        assert all(x['registers']==rows[end-1]['registers'] for x in rows[end:]) and rows[-1]['registers'][2]==[15]*4
        assert original['post_completion_observed_ticks']==128 and original['post_inactive_physically_enabled_ticks']==0
        assert native_context[name]['F3_ticks']==[1] and native_context[name]['F3_modes']==[7]
        terminal[f'{rid:02X}']=dict(inactive_tick=end,candidate_post_ticks=32,original_preflight_post_ticks=128,final_attenuation=rows[-1]['registers'][2],post_writes=0,PCM_samples=len(rows)*735)
    # Repeat the accepted C3 dedup negative on the expanded bank; never used in playback.
    for rid in (0xB0,0xB7):
        case=(rid,{},39);good,gs=observe(bank,case);wrong,bs=observe(bank,case,deduplicate_noise_controls=True)
        badticks=sum(a['RNG']!=b['RNG'] for a,b in zip(gs['frames'],bs['frames']))
        error=int(np.abs(good.astype(np.int32)-wrong.astype(np.int32)).max())
        assert badticks==36 and error==16384
        second=gs['controls'][1];assert second['RNG_after']==32768 and second['RNG_before']!=32768
        assert second['noise_counter_before']==second['noise_counter_after']==21
        wav(OUT/f'C3-{rid:02X}-negative-dedup.wav',wrong)
        negatives[f'{rid:02X}']=dict(LFSR_mismatching_ticks=badticks,max_signed16_error=error,second_F3=second)
    class MissingTerminal(Decoder):
        def release(self,i):self.ch[i][0]=0
    class MissingF3(Decoder):
        def command(self,i,op,p):
            if op==0xF3:return p+1
            return super().command(i,op,p)
    bad={}
    for rid in BATCH:
        expected=load(f'solo-{rid:02X}')['candidate'];bad[f'{rid:02X}']={}
        for label,cls in [('missing_F3',MissingF3),('missing_terminal',MissingTerminal)]:
            m=cls(bank);m.direct(rid);fail=None
            for tick in range(1,len(expected)+1):
                m.tick()
                if m.writes!=expected[tick-1]['ports']:fail=tick;break
            assert fail is not None
            bad[f'{rid:02X}'][label+'_detected_tick']=fail
    admissions={name:load(name)['SFX_admissions'] for name in CASES}
    assert admissions['B1-block-ring']==[[1,0xB1],[30,0xBF]]
    assert admissions['AF-to-A7']==[[30,0xAF]] and admissions['B1-to-B0']==[[30,0xB1]]
    assert admissions['B9-to-B7']==[[30,0xB9],[45,0xB7]]
    assert admissions['BA-to-B9']==[[30,0xBA],[32,0xB9]]
    assert native_context['BA-to-B9']['maximum_simultaneous_SFX_slots']==2
    for name in ['AF-retrigger','B1-retrigger','B9-retrigger']:
        assert len(admissions[name])==4 and len(controls[name])==4
        assert all(x['RNG_after']==32768 for x in controls[name])
        assert any(x['RNG_before']!=32768 for x in controls[name][1:])
    recovery={}
    for name in ['THZ-AF','THZ-B1','THZ-B9','THZ-late-B9']:
        rows=load(name)['original']
        for i in (2,3):
            sup=[t+1 for t,r in enumerate(rows) if r['channels'][i]&4]
            nxt=next(t+1 for t,r in enumerate(rows) if t+1>max(sup) and r['channels'][i]&128 and not r['channels'][i]&20)
            recovery[f'{name}-music{i}']=dict(suppression=[min(sup),max(sup)],next_read=nxt)
    # Historical class counts do not execute or promote any further ID.
    coverage=json.loads((ROOT/'data/m5-a2c3/coverage.json').read_text())
    for row in coverage['entries']:
        if row['request_id'] in BATCH:
            row['decoder_status']='fully-decoded-in-tested-scope';row['tested_scope']='complete solo +32 post, original-only +128 physical check, selected single-F3 noise/phase/priority/recovery contexts and ROM-free replay'
    coverage['counts']={s:sum(r['decoder_status']==s for r in coverage['entries']) for s in ('fully-decoded-in-tested-scope','partially-decoded','format-understood-but-unverified','unsupported-or-unknown','empty-or-control')}
    coverage['extracted_unique_headers']=33
    coverage['format_understood_but_unverified_note']='C4 AF/B1/B9 verified only in authenticated scope; prior command and reader boundaries unchanged.'
    p1c=json.loads((ROOT/'data/m5-p1c/coverage.json').read_text());unverified={r['request_id'] for r in coverage['entries'] if r['decoder_status']=='unsupported-or-unknown'}
    classes={k:[f'{i:02X}' for i in ids if i in unverified] for k,ids in p1c['classes'].items()}
    remaining=dict(source='accepted historical P1C original-only classes intersected with C4 unverified catalogue; no fresh execution of other IDs',classes=classes,counts={k:len(v) for k,v in classes.items()},remaining_music=sum(r['request_id'] in unverified and r['category']=='music' for r in coverage['entries']),qualification='Class metadata does not verify stream grammar, envelope paths or candidate execution of remaining IDs.')
    coverage['remaining_original_classes']=remaining
    coverage['expansion_batches']=[dict(order=1,proposal_only=True,ids=['Manager-selected small tone2-only group'],purpose='largest remaining class; fresh original-only opcode/envelope/raw-mode preflight before implementation'),dict(order=2,proposal_only=True,ids=classes['coupled-white-noise-single-F3'],purpose='remaining historical single-F3 class, separately authorised only; not begun')]
    save(PUB/'coverage.json',coverage)
    times=[];active_times=[];idle_times=[]
    for _ in range(50):
        for rid in BATCH:
            m=Decoder(bank);m.direct(rid)
            for _ in range(CASES[f'solo-{rid:02X}'][2]):
                active=any(c[0]&128 for c in m.ch) or any(m.mail)
                start=time.perf_counter_ns();m.tick();elapsed=time.perf_counter_ns()-start;times.append(elapsed)
                (active_times if active else idle_times).append(elapsed)
    memory={}
    for name,blob in [('previous',(C3OLD/'programs.scsp').read_bytes()),('expanded',(OUT/'programs.scsp').read_bytes())]:
        gc.collect();tracemalloc.start();b=unpack(blob);m=Decoder(b);m.direct(0x81)
        for _ in range(4200):m.tick()
        current,peak=tracemalloc.get_traced_memory();tracemalloc.stop();memory[name]=dict(current_bytes=current,peak_bytes=peak)
    save(PUB/'facts.json',dict(termination=terminal,native_diagnostics=native_context,F3_controls=controls,C3_duplicate_control_negative=negatives,negative_controls=bad,admissions=admissions,music_recovery=recovery,DE11_restore_contexts={n:load(n)['saved_noise_restores'] for n in CASES},remaining_original_classes=remaining,
      performance=dict(ticks=len(times),median_ns=statistics.median(times),p99_ns=sorted(times)[int(.99*len(times))],max_ns=max(times),active_ticks=len(active_times),active_median_ns=statistics.median(active_times),idle_ticks=len(idle_times),idle_median_ns=statistics.median(idle_times),memory=memory,scope='Python sparse bank/decoder and bounded diagnostics; excludes interpreter base/PCM; NOT GameMaker performance')))
    print('native states, phase controls, terminal negatives, C3 dedup regression and catalogue PASS')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('rom');a=p.parse_args();run(T.load_rom(a.rom))
