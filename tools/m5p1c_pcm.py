"""Small private class proof, after coverage and exact emission gate.

Thirty renderer processes maximum, each <=240 ticks. Earlier packages read-only.
No note synthesis or live PSG engine; unsupported shared-clock contexts STOP.
"""
import argparse
import json
import os
from pathlib import Path
import tempfile
import time
import numpy as np
import audio1_psg_trace as T
import audio1b_render as R
import audio1b_analyze as A
import audio1b_checks as C
from m5p1c import ROOT,OUT,PUBLIC,P0P1,OLD,M4,PIN,CASES,load,save,sha,preservation
from m5p0r_pcm import gain_carrier,phase_energy
from m5p1_proof import mono,wav,comparison_metrics,spectral

def raw_rows(name):return [r['ports'] for r in load(OUT/f'{name}-gate.json')['rows']]

class Renderer:
    def __init__(self,reuse_only=False):
        self.reuse_only=reuse_only
        self.calls=[];self.cache=OUT/'render-cache';self.cache.mkdir(parents=True,exist_ok=True)
        temp=OUT/'renderer-temp';temp.mkdir(exist_ok=True);tempfile.tempdir=str(temp.resolve())
        self.exe=Path(os.environ['AUDIO1B_VGM2WAV']);assert sha(self.exe.read_bytes())==PIN
    def render(self,rows,label,fresh=False):
        assert len(rows)<=240
        vgm=R.build_vgm(rows);assert not R.vgm_matches(rows,vgm)
        key=sha(vgm+self.exe.read_bytes());path=self.cache/(key+'.wav');receipt=self.cache/(key+'.json')
        if (not fresh or self.reuse_only) and path.exists() and receipt.exists():
            m=load(receipt)
            if sha(path.read_bytes())==m['wav_sha256']:return mono(path)
        if self.reuse_only:raise RuntimeError('STOP: analysis may only reuse verified existing renders')
        if len(self.calls)>=30:raise RuntimeError('bounded render limit reached')
        if sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())>1024**3:raise RuntimeError('scratch cap')
        t=time.perf_counter();pcm,_=R.render_libvgm(vgm,len(rows)*735,'MAME');pcm=pcm[:len(rows)*735]
        assert len(pcm)==len(rows)*735 and np.array_equal(pcm[:,0],pcm[:,1])
        wav(path,pcm[:,0]);(self.cache/(key+'.vgm')).write_bytes(vgm)
        self.calls.append(dict(label=label,ticks=len(rows),seconds=time.perf_counter()-t,key=key,peak_lsb=int(np.abs(pcm.astype(np.int32)).max())))
        save(receipt,dict(key=key,wav_sha256=sha(path.read_bytes()),renderer_sha256=PIN))
        return pcm[:,0]

def solo(rom,rid,ticks):
    d=T.Driver(rom);d.request(rid);rows=[];states=[]
    for _ in range(ticks):
        n=len(d.writes);d.tick();rows.append([b for _,b in d.writes[n:]]);states.append(d.psg.state())
    return rows,states

def carrier_rows(rows,voice,last_tick):
    rows=R.attenuation_stem(rows,voice);out=[];latch=0
    for tick,row in enumerate(rows,1):
        fixed=[]
        for byte in row:
            if byte&128:latch=(byte>>4)&7
            if tick<=last_tick and latch==voice*2+1:byte=(byte&0xF0) if byte&128 else 0
            fixed.append(byte)
        if tick==1:fixed=[0x90+voice*32]+fixed
        out.append(fixed)
    return out

def templates(rom,renderer):
    data={}
    # Existing baked sources and their actual solo register profiles.
    for rid in (0x81,0x88,0xBF,0xBC,0xB8,0xA3,0xB7,0xA0,0xAC):
        if rid in (0x81,0xBF):
            folder=M4/f'{rid:02X}';voices=[mono(folder/f'ch{c}.wav') for c in range(4)]
            voices[0]=(mono(folder/'other3.wav').astype(np.int32)-voices[1]-voices[3]).astype(np.int16)
            _,states=solo(rom,rid,220 if rid==0x81 else len(voices[0])//735)
        elif rid in (0x88,0xBC,0xA3,0xB8,0xA0,0xAC):
            folder=P0P1/'package'/('diagnostic-B8' if rid==0xB8 else f'library/{rid:02X}')
            voices=[mono(folder/f'raw{c}.wav') for c in range(4)] if rid!=0x88 else [mono(folder/f'experimental{c}.wav') for c in range(4)]
            states=load(folder/'private-registers.json')['states']
        else:
            rows,states=solo(rom,rid,27);voices=[np.zeros(27*735,dtype=np.int16) for _ in range(4)]
        data[rid]=dict(voices=voices,states=states,carrier=False)
    # Proven P0R fixed carrier reused unchanged.
    data[0xB8]['voices'][3]=mono(OLD/'pcm/B8-carrier-diagnostic.wav');data[0xB8]['carrier']=True
    carrier_meta={}
    for rid,n,end in ((0xA3,69,48),(0xB7,27,6)):
        rows,states=solo(rom,rid,n);forced=carrier_rows(rows,3,end)
        noise=renderer.render(forced,f'{rid:02X}-finite-carrier')
        fresh=renderer.render(forced,f'{rid:02X}-carrier-fresh-process',fresh=True)
        assert np.array_equal(noise,fresh)
        data[rid]['voices'][3]=noise;data[rid]['carrier']=True
        wav(OUT/f'assets/{rid:02X}-carrier.wav',noise)
        save(OUT/f'assets/{rid:02X}-source-clock.json',dict(states=states,last_authenticated_active_tick=end,full_capture_ticks=n))
        carrier_meta[f'{rid:02X}']=dict(active_source_ticks=end,total_ticks=n,pcm_sha256=sha(noise.tobytes()),determinism='fresh-process byte equal',
            mode='white tone2-derived' if rid==0xA3 else 'periodic tone2-derived',phase_cursor='continuous own age; no restart on inhibition')
    return data,carrier_meta

def references(renderer):
    result={}
    old_names={'fixed-hold':'fixed-B8-BC','music-context-B6':'B6-A0','music-context-BA':'BA-partial'}
    for name,c in CASES.items():
        if name in old_names:
            folder=P0P1/'package/scenarios'/old_names[name]
            mix=mono(folder/'continuous.wav');voices=[mono(folder/f'continuous-voice{v}.wav') for v in range(4)]
            result[name]=dict(mix=mix,voices=voices,reused=True)
        elif name=='isolated-context-B6':
            folder=P0P1/'package/library/B6';result[name]=dict(mix=mono(folder/'mix.wav'),voices=[mono(folder/f'raw{v}.wav') for v in range(4)],reused=True)
        else:
            rows=raw_rows(name);mix=renderer.render(rows,name+'-reference');voices=[renderer.render(R.attenuation_stem(rows,v),name+f'-voice{v}') for v in range(4)]
            folder=OUT/'references'/name;folder.mkdir(parents=True,exist_ok=True);wav(folder/'continuous.wav',mix)
            for v in range(4):wav(folder/f'voice{v}.wav',voices[v])
            result[name]=dict(mix=mix,voices=voices,reused=False)
    # Only one representative full reference is repeated; old core determinism reused.
    fresh=renderer.render(raw_rows('coupled-steal-recover'),'coupled-reference-fresh-process',fresh=True)
    assert np.array_equal(fresh,result['coupled-steal-recover']['mix'])
    return result

def compose(name,data):
    case=load(OUT/f'{name}-gate.json');rows=case['rows'];n=len(rows)
    voices=[np.zeros(n*735,dtype=np.int32) for _ in range(4)]
    # Clock owner follows real noise-control emissions, not last request or activity.
    noise_owner=None;issues=[];hidden=[];audible_clock=[];past_lifetime=[];source_silent=[];choices=[]
    for r in rows:
        tick=r['tick'];reg=r['original']['registers'];channels=r['channel_sources']
        for e in r['audit']:
            if e['reason']=='music-noise-control':noise_owner=3
            elif e['reason']=='F3-noise-control':noise_owner=e['channel']
            elif e['reason']=='F2-saved-noise-restore' and e['value']&128 and (e['value']>>4)&7==6:noise_owner=3
            elif e['reason']=='reset-off':noise_owner=None
        selected=[]
        for v in range(4):
            level=reg[2][v]
            if v==3:index=noise_owner
            elif v in (1,2) and channels[v+3]['flags']&128:index=v+3
            else:index=v
            if index is None:selected.append(None);continue
            ch=channels[index];rid=ch['id'];age=ch['age']
            # A canceled source has no authenticated continuing clock schedule.
            if not ch['flags']&128 and level<15:
                issues.append(dict(tick=tick,voice=v,reason='physical output survives source stream cancellation/completion',id=rid));selected.append(None);continue
            if rid not in data:
                if level<15:issues.append(dict(tick=tick,voice=v,reason='no validated source in this small batch',id=rid))
                selected.append(None);continue
            d=data[rid];source_tick=age-1
            if not 0<=source_tick<len(d['states']):
                if level<15:past_lifetime.append(dict(tick=tick,voice=v,id=rid,age=age))
                selected.append(None);continue
            source=d['states'][source_tick];clock_ok=True
            if v==3:
                clock_ok=source[1]==reg[1] and ((reg[1]&3)!=3 or source[0][2]==reg[0][2])
                if not clock_ok:
                    (hidden if level==15 else audible_clock).append(dict(tick=tick,id=rid,source_age=age,source_mode=source[1],actual_mode=reg[1]))
            elif source[0][v]!=reg[0][v] and level<15:
                audible_clock.append(dict(tick=tick,id=rid,voice=v,reason='audible tone period differs from source'))
                clock_ok=False
            selected.append(dict(id=rid,age=age,clock_compatible=clock_ok))
            if level==15:continue
            sample=d['voices'][v][source_tick*735:(source_tick+1)*735].astype(float)
            if len(sample)!=735:past_lifetime.append(dict(tick=tick,voice=v,id=rid,age=age));continue
            if v==3 and d['carrier']:
                target=gain_carrier(sample,[level])
            else:
                src_level=source[2][v]
                if src_level==15:
                    source_silent.append(dict(tick=tick,voice=v,id=rid,target_level=level));continue
                # Existing source keeps its entry phase. Gain uses original attenuation,
                # not a blanket assumption that an inhibited write muted the PSG.
                table=[int(8192*2**(-i/3)+.5) for i in range(15)]+[0]
                target=np.rint(sample*table[level]/table[src_level]).astype(np.int32)
            voices[v][(tick-1)*735:tick*735]=target
        choices.append(selected)
    mixed=sum(voices);assert np.abs(mixed).max()<32768
    return mixed,voices,dict(unsupported_sources=issues,hidden_noise_clock_differences=hidden,audible_clock_differences=audible_clock,
        source_lifetime_overruns=past_lifetime,baked_silent_source_needed=source_silent,choices=choices)

def timing(reference,candidate,rows,voice):
    a=A.tick_rms(reference);b=A.tick_rms(candidate);enabled=np.array([r['original']['registers'][2][voice]<15 for r in rows])
    return dict(missing_non_DC_ticks=[int(t+1) for t in np.flatnonzero((a>1)&(b<=1))],
        extra_non_DC_ticks=[int(t+1) for t in np.flatnonzero((a<=1)&(b>1))],
        original_logical_enabled_ticks=int(enabled.sum()),candidate_nonzero_after_logical_off_samples=int(sum(np.count_nonzero(candidate[t*735:(t+1)*735]) for t in np.flatnonzero(~enabled))),
        qualification='1LSB AC-RMS measurement proxy, not a PASS tolerance; original DC startup and one-sample resampler buckets kept separately')

def pitch_report(rows,voices):
    with np.errstate(invalid='ignore',divide='ignore'):
        windows=C.pitch_windows(rows,[np.repeat(v[:,None],2,axis=1) for v in voices])
    valid=[w for w in windows if np.isfinite(w[5]) and w[3]>0 and w[4]>0]
    invalid=[w for w in windows if not (np.isfinite(w[5]) and w[3]>0 and w[4]>0)]
    bad=[w for w in valid if abs(w[5])>25]
    return dict(windows=len(windows),valid_windows=len(valid),invalid_measurement_windows=len(invalid),
        windows_off_by_more_than_25_cents=len(bad),max_abs_cents=float(max((abs(w[5]) for w in valid),default=0)),
        per_voice=[dict(voice=c,valid=sum(w[0]==c for w in valid),invalid=sum(w[0]==c for w in invalid),off=sum(w[0]==c for w in bad)) for c in range(3)],
        status='UNRESOLVED measurement windows' if invalid else 'measured; no acceptance threshold relaxed')

def run(rom,reuse_only=False):
    assert load(PUBLIC/'emission-gate.json')['status']=='PASS','emission gate first'
    previous=load(PUBLIC/'pcm-feasibility.json') if reuse_only else None
    before=preservation();renderer=Renderer(reuse_only)
    # Capture this finite planned reference set before evaluating unsupported classes.
    ref=references(renderer);data,carriers=templates(rom,renderer)
    results={};stop=[]
    reused={'fixed-hold':OLD/'pcm/B8-BC-carrier-composed.wav','music-context-B6':OLD/'pcm/B6-A0-context-composed.wav','music-context-BA':OLD/'pcm/BA-partial-context-composed.wav'}
    for name,c in CASES.items():
        reference=ref[name];rows=load(OUT/f'{name}-gate.json')['rows']
        if name in reused:
            prior_correction=load(ROOT/'data/m5-p0r/composition-feasibility.json')
            key='carrier_experiment' if name=='fixed-hold' else 'B6_context' if name=='music-context-B6' else 'BA_context'
            results[name]=dict(reused_reference=True,reused_composition=True,emission='PASS',metrics=prior_correction[key]['after'],
                scope='previous explicitly bounded correction retained; not reclassified as new generalized carrier success')
            continue
        if name=='isolated-context-B6':
            results[name]=dict(reused_reference=True,emission='PASS',context='saved DE11 zero and actual data latch, original solo behavior retained',
                solo_mix_sha256=sha(reference['mix'].tobytes()),gate_only_asset_context=True)
            continue
        mixed,voices,compat=compose(name,data)
        metrics=comparison_metrics(reference['mix'],mixed,reference['voices'],voices)
        metrics['phase_energy']=phase_energy(reference['mix'],mixed,reference['voices'],voices)
        residual=sum(v.astype(np.int32) for v in reference['voices'])-reference['mix'].astype(np.int32)
        metrics['reference_stem_reconstruction']=dict(max_error_lsb=int(np.abs(residual).max()),
            nonzero_samples=int(np.count_nonzero(residual)),rms_lsb=float(np.sqrt(np.mean(residual.astype(float)**2))),
            qualification='independently rendered attenuation stems; rounding/resampling residual retained')
        metrics['pitch']=pitch_report([r['ports'] for r in rows],voices)
        metrics['reference_pitch']=pitch_report([r['ports'] for r in rows],reference['voices'])
        metrics['timing']=[timing(reference['voices'][v],voices[v],rows,v) for v in range(4)]
        metrics['reference_noise']=spectral(reference['voices'][3]);metrics['candidate_noise']=spectral(voices[3])
        # Diagnose physical/clock incompatibility without declaring silent truncation a fix.
        status='BOUNDED APPROXIMATION; NOT NATIVE ACCEPTED'
        if compat['unsupported_sources'] or compat['audible_clock_differences'] or compat['source_lifetime_overruns'] or compat['baked_silent_source_needed']:
            status='HOLD unsupported physical clock/source context';stop.append(name)
        elif compat['hidden_noise_clock_differences']:
            status='HOLD exact oscillator-history continuity not represented';stop.append(name)
        folder=OUT/'candidate'/name;folder.mkdir(parents=True,exist_ok=True);wav(folder/'composed-diagnostic.wav',mixed)
        for v in range(4):wav(folder/f'voice{v}.wav',voices[v])
        save(folder/'private-selection.json',compat)
        # Public diagnostics omit full clock/note timelines.
        safe={k:dict(count=len(v),first_tick=v[0]['tick'] if v else None) for k,v in compat.items() if k!='choices'}
        results[name]=dict(emission='PASS',status=status,compatibility=safe,metrics=metrics,
            entry='matched source reset for A3; changes during interruption isolated from arbitrary initial music entry' if name=='coupled-steal-recover' else 'seeded original-driver controlled case')
    calls=previous['process_calls'] if reuse_only else renderer.calls
    report=dict(rom_sha256=T.ROM_SHA256,renderer_sha256=PIN,cases=results,carrier_assets=carriers,
        process_calls=calls,new_process_count=len(calls),analysis_followup_new_processes=len(renderer.calls) if reuse_only else None,
        all_targets_at_most_ticks=max(x['ticks'] for x in calls),
        blocking_cases=stop,overall='HOLD for architecture decision' if stop else 'CONDITIONAL GO bounded classes only',
        preservation_before=before,preservation_after=preservation(),new_synthesis=False,full_library_rendered=False,native_listening='NOT PERFORMED')
    save(PUBLIC/'pcm-feasibility.json',report)
    print(json.dumps(dict(overall=report['overall'],processes=len(renderer.calls),cases={k:(v.get('status','reused'),v.get('compatibility',{})) for k,v in results.items()}),indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('rom');p.add_argument('--analyze-existing',action='store_true');a=p.parse_args();run(T.load_rom(a.rom),a.analyze_existing)
