"""Produce/validate PRIVATE six-ID M4 assets with the existing AUDIO-1B toolchain.

Set PYTHONPATH=build/deps, AUDIO1B_VGM2WAV and workspace TEMP/TMP first.
python tools/m4_produce_audio.py ROM library|tails|package [--jobs 4]
Everything copyrighted/derived is confined to ignored build/m4/production/.
Public summaries contain aggregate measurements only, never note/read maps.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import shutil
import wave
import zipfile
import numpy as np
import m4_audio as M
import audio1_psg_trace as T
import audio1b_render as R
import audio1b_checks as C
import audio1b_analyze as A

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/m4/production'
LENGTHS={0x90:800,0x99:1300,0x82:13954,0x81:6469,0xBF:41,0xA6:61}
REC={0x81:(1093,2688),0x82:(130,6912)}

def sha(data):return hashlib.sha256(data).hexdigest()
def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf8')
def mono_wav(path,pcm):
    path.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(path),'wb') as f:
        f.setparams((1,2,44100,0,'NONE','not compressed'))
        f.writeframes(np.asarray(pcm,dtype='<i2').tobytes())
def stereo(path):return R.read_wav(path)
def mono(path):
    with wave.open(str(path),'rb') as f:
        assert (f.getnchannels(),f.getsampwidth(),f.getframerate())==(1,2,44100)
        return np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').copy()
def renderer():return R.LibvgmRenderer('MAME')
def strict_render(rows):
    vgm=R.build_vgm(rows)
    assert not R.vgm_matches(rows,vgm)
    pcm,_=R.render_libvgm(vgm,len(rows)*735,'MAME')
    assert len(pcm)>=len(rows)*735,'renderer returned short PCM'
    pcm=pcm[:len(rows)*735]
    assert np.array_equal(pcm[:,0],pcm[:,1]),'PSG stereo lanes differ'
    return pcm

def loop_cut(rid,rows,stems,mix):
    a,p=REC[rid];ks=np.arange(a,a+p,dtype=np.int64)
    signals=[v[:,0].astype(np.int32) for v in stems]+[mix[:,0].astype(np.int32)]
    scale=[max(float(np.sqrt(np.mean(v.astype(np.float64)**2))),1) for v in signals]
    jumps=np.array([np.abs(v[ks*735]-v[(ks+p)*735-1]) for v in signals])
    score=(jumps/np.array(scale)[:,None]).max(axis=0)
    idx=int(np.argmin(score));k=int(ks[idx]);measure=[]
    for name,v,den in zip(('tone0','tone1','tone2','noise','mix'),signals,scale):
        body=v[k*735:(k+p)*735]
        measure.append(dict(channel=name,wrap_jump_lsb=int(abs(int(body[0])-int(body[-1]))),
            ordinary_step_p999_lsb=float(np.percentile(np.abs(np.diff(body)),99.9)),
            ordinary_step_max_lsb=int(np.abs(np.diff(body)).max()),rms_lsb=round(den,3)))
    assert rows[a:a+p]==rows[a+p:a+2*p]
    return dict(recurrence_after_tick=a,period_ticks=p,selected_common_cut_after_tick=k,
        loop_start_sample=k*735,loop_end_sample_exclusive=(k+p)*735,
        prefix_samples=k*735,body_samples=p*735,candidates=p,
        normalized_worst_jump=float(score[idx]),per_channel=measure,
        command_period_repeats=True,inaudibility='not evaluated; listening required',
        policy='minimize max wrap jump/RMS across four stems and mix; earliest tie; no crossfade')

def library(rom):
    OUT.mkdir(parents=True,exist_ok=True)
    metrics={}
    for rid,n in LENGTHS.items():
        name=f'{rid:02X}';folder=OUT/name;folder.mkdir(exist_ok=True)
        _,rows,reads,inactive,_=M.capture(rom,rid,n)
        vgm=R.build_vgm(rows);(folder/'reference.vgm').write_bytes(vgm)
        save(folder/'stream-reads.json',dict(ticks=n,music_channels=list(T.MUSIC_CH),
            read_ticks=reads,source='CPU4341 hook; tone2 map is the pilot recovery authority'))
        key=sha(vgm+Path(os.environ['AUDIO1B_VGM2WAV']).read_bytes())
        cache=folder/'render-cache.json'
        valid=cache.exists() and json.loads(cache.read_text()).get('key')==key
        if valid:
            for file,digest in json.loads(cache.read_text())['hashes'].items():
                valid=valid and (folder/file).exists() and sha((folder/file).read_bytes())==digest
        if valid:
            mix=stereo(folder/'reference-stereo.wav')
            st=[np.repeat(mono(folder/f'ch{c}.wav')[:,None],2,axis=1) for c in range(4)]
        else:
            mix=strict_render(rows);R.write_wav(folder/'reference-stereo.wav',mix)
            st=[]
            for c in range(4):
                s=strict_render(R.attenuation_stem(rows,c));st.append(s)
                mono_wav(folder/f'ch{c}.wav',s[:,0])
            save(cache,dict(key=key,hashes={p.name:sha(p.read_bytes()) for p in folder.glob('*.wav')}))
        # A second renderer process starts from reset; no reused PCM is the oracle.
        repeat=strict_render(rows)
        assert np.array_equal(mix,repeat),f'{name}: deterministic render mismatch'
        summed=sum(s.astype(np.int32) for s in st)
        error=int(np.abs(summed-mix.astype(np.int32)).max())
        # Five LSB was AUDIO-1B's observed maximum for its five short samples,
        # not a proven bound for every stream. Retain that raw comparison below.
        # Core >>1, resampler integer division and final PCM >>8 independently
        # quantize the isolated renders; enforce a declared 8-LSB production cap.
        assert error<=8,f'{name}: stem sum max {error} exceeds declared 8-LSB cap'
        raw_other=st[0].astype(np.int32)+st[1].astype(np.int32)+st[3].astype(np.int32)
        # Keep original isolated stems. Put only their bounded rounding residual
        # into the grouped runtime stem, making tone2+other3 exactly the mix.
        combined=mix.astype(np.int32)-st[2].astype(np.int32)
        assert np.abs(combined).max()<32767
        mono_wav(folder/'other3-raw.wav',raw_other[:,0])
        mono_wav(folder/'other3.wav',combined[:,0])
        mono_wav(folder/'mix.wav',mix[:,0])
        sanity=C.sanity(mix);pitch=C.pitch_report(rows,st,min_ticks=1 if rid>=0xA0 else 3)
        duration=C.duration_report(rows,st)
        m=dict(request_id=name,ticks=n,samples=n*735,seconds=n/60,
            sanity=sanity,pitch=pitch,duration=duration,stem_sum_max_lsb=error,
            inherited_5lsb_observed_max_comparison='PASS' if error<=5 else 'FAIL',
            production_8lsb_quantization_cap='PASS',
            runtime_two_stem_sum_max_lsb=int(np.abs(combined+st[2].astype(np.int32)-mix.astype(np.int32)).max()),
            other3_rounding_residual_max_lsb=int(np.abs(combined-raw_other).max()),
            deterministic_fresh_renderer_process=True,first_music_inactive_tick=inactive,
            vgm_sha256=sha(vgm),mix_pcm_sha256=sha(mix.tobytes()),
            stream_read_counts=list(map(len,reads)),header=T.header_facts(rom,rid))
        if rid in REC:
            loop=loop_cut(rid,rows,st,mix);m['loop']=loop
            save(folder/'loop.json',loop)
            # Private recovery maps span every tick of both rendered bodies.
            a,p=REC[rid]
            for k in range(4):
                if reads[k]:assert all(t>0 for t in reads[k])
        if rid>=0xA0:m['sfx']=C.sfx_length_report(rom,rid,mix)
        if rid==0x99:
            m['terminal_silence_max_lsb']=int(np.abs(mix[1189*735:].astype(np.int32)).max())
            assert inactive==1189 and m['terminal_silence_max_lsb']==0
        save(folder/'metrics.json',m);metrics[name]=m
        print(f'library {name}: peak={sanity["peak"]} pitch_off={pitch["windows_off_by_more_than_25_cents"]} sum_error={error}',flush=True)
    # Existing independent negative-control noise experiment, not song metadata.
    noise=C.noise_variant_test({'libvgm_mame':renderer()})
    save(OUT/'noise-validation.json',noise)
    save(OUT/'library-metrics.json',metrics)
    conformance(rom)
    return metrics

def conformance(rom):
    expected={0x90:'6c5236eeb8cea069b3afba618484fa9299bb5789d8dec890ec68417be96bd7ac',
        0x82:'1508bf44d9e70260bd6a3268c8725c8af110fee2fd08af2983ca25ee01f0a16b',
        0x81:'bd62a05f02f555b8c60899b3fd0490512dbe654fbda35722971f93702785ea75',
        0xBF:'620e59241585a81c6c9d046fbd1a6bf27d8751982fe2ffc905430e34e739ddd8',
        0xA6:'30e98a0be3f6953835a432908ae8e0f2d958a8289958c2f916d0e457f415f34e'}
    result=[]
    for rid,want in expected.items():
        ticks=21 if rid==0xBF else 37 if rid==0xA6 else 900
        if rid==0x90:
            _,pt,_,_,_=M.capture(rom,rid,ticks);pcm=strict_render(pt)
        else:pcm=stereo(OUT/f'{rid:02X}/reference-stereo.wav')[:ticks*735]
        path=OUT/f'conformance/{rid:02X}_AUDIO1B.wav';R.write_wav(path,pcm)
        got=sha(path.read_bytes());assert got==want,(rid,got,want)
        result.append(dict(request=f'{rid:02X}',ticks=ticks,wav_sha256=got,byte_identical_AUDIO1B=True))
    save(OUT/'conformance-validation.json',result)
    _,pt,_,_,_=M.capture(rom,0x99,1300)
    ref=A.reference_render(pt,R.PAL);mix=stereo(OUT/'99/reference-stereo.wav');x=A.mono(mix)[0]
    save(OUT/'title-independent-reference.json',dict(
        reference='AUDIO-1B separately implemented counter/LFSR synth; independent of MAME, not independent ROM execution',
        waveform_correlation=A.corr(ref,x),tick_rms_correlation=A.corr(A.tick_rms(ref),A.tick_rms(x)),
        reference_peak=float(abs(ref).max()),mame_peak=float(abs(x).max())))

def phase_tail(rom,F,dry):
    folder=OUT/'opening-tails';path=folder/f'fade_{F:04d}.wav';receipt=folder/f'fade_{F:04d}.json'
    if path.exists() and receipt.exists():
        rec=json.loads(receipt.read_text())
        if sha(path.read_bytes())==rec['wav_sha256'] and rec['renderer_sha256']==sha(Path(os.environ['AUDIO1B_VGM2WAV']).read_bytes()):
            rec.setdefault('reset_tick_nonzero_samples',0)
            return rec
    d,rows,_,inactive,_=M.capture(rom,0x90,F+22,{F:[('fade',(12,1,2))]})
    assert inactive==F+22 and not d.active()
    pcm=strict_render(rows);start=(F-1)*735
    error=int(np.abs(pcm[:start].astype(np.int32)-dry[:start].astype(np.int32)).max()) if start else 0
    assert error==0,f'fade {F}: dry prefix mismatch {error}'
    tail=pcm[start:];assert len(tail)==23*735
    # The first sample can retain the preceding attenuation through libvgm's
    # fractional resampling bucket. Preserve it, rather than fabricating zeros.
    reset=tail[-735:,0].astype(np.int32)
    assert np.abs(reset[1:]).max()==0
    mono_wav(path,tail[:,0])
    rec=dict(fade_before_tick=F,reset_tick=F+22,samples=len(tail),
        prefix_max_error_lsb=error,reset_tick_max_lsb=int(np.abs(reset).max()),
        reset_tick_nonzero_samples=int(np.count_nonzero(reset)),wav_sha256=sha(path.read_bytes()),
        renderer_sha256=sha(Path(os.environ['AUDIO1B_VGM2WAV']).read_bytes()))
    save(receipt,rec);return rec

def tails(rom,jobs):
    dry=stereo(OUT/'90/reference-stereo.wav');results=[]
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        futures=[pool.submit(phase_tail,rom,F,dry) for F in range(9,746)]
        for fut in as_completed(futures):
            results.append(fut.result())
            if len(results)%50==0:print(f'opening phases {len(results)}/737 verified',flush=True)
    results.sort(key=lambda r:r['fade_before_tick'])
    save(OUT/'opening-tails/index.json',dict(phases=results,range_inclusive=[9,745],
        format=dict(rate=44100,bits=16,channels=1),source='90; DE09/0A/0B=12/1/2',
        mapping='F=post-entry E+7=title-handoff H-33; tail begins (F-1)*735; reset F+22'))
    # Fresh independent render of complete early/middle/late/natural paths.
    cases=[]
    for E in (2,70,300,600,738):
        F,H=E+7,E+40
        _,rows,_,inactive,_=M.capture(rom,0x90,H,{F:[('fade',(12,1,2))]})
        full=strict_render(rows)[:,0]
        assembled=np.concatenate((dry[:(F-1)*735,0],mono(OUT/f'opening-tails/fade_{F:04d}.wav'),
            np.zeros((H-F-22)*735,dtype=np.int16)))
        assert len(full)==len(assembled)
        err=int(np.abs(full.astype(np.int32)-assembled.astype(np.int32)).max())
        assert err==0
        mono_wav(OUT/f'opening-tails/listen_E{E:04d}.wav',assembled)
        cases.append(dict(post_entry_tick=E,fade_tick=F,handoff_tick=H,reset_tick=inactive,
            reconstruction_max_error_lsb=err))
    result=dict(phases=737,prefix_exact=all(r['prefix_max_error_lsb']==0 for r in results),
        reset_silent_after_first_sample=True,
        reset_tick_max_residual_lsb=max(r['reset_tick_max_lsb'] for r in results),
        reset_tick_max_nonzero_samples=max(r['reset_tick_nonzero_samples'] for r in results),cases=cases)
    save(OUT/'opening-validation.json',result);print(json.dumps(result),flush=True)

def recovery(rom):
    # Tone2 suppression-bit recovery oracle; OFF writes are not recovery.
    results=[]
    for rid in (0x90,0x99,0x82,0x81):
        for sfx,k in ((0xBF,20),(0xA6,40)):
            good=0
            for at in range(150,700,23):
                _,_,reads,_,_=M.capture(rom,rid,at+k+180)
                expected=next((t for t in reads[2] if t>at+k),None)
                d=T.Driver(rom);d.request(rid);actual=None
                for t in range(1,at+k+180):
                    if t==at:d.request(sfx)
                    before=d.mem[0xDEA0];d.tick()
                    if t>at+k and before&16 and not d.mem[0xDEA0]&16:actual=actual or t
                assert expected==actual and actual is not None,(rid,sfx,at,expected,actual)
                good+=1
            results.append(dict(music=f'{rid:02X}',sfx=f'{sfx:02X}',phases=24,matches=good))
    # Late finite title: a terminated music channel must not be resurrected.
    d=T.Driver(rom);d.request(0x99)
    for t in range(1,1350):
        if t==1175:d.request(0xA6)
        d.tick()
    assert not d.active() and d.psg.att==[15]*4
    result=dict(phase_tests=results,total_matches=sum(x['matches'] for x in results),
        finite_title_late_sfx_no_resurrection=True)
    # Repeat inherited audible envelope/pitch experiment using this Windows binary.
    result['waveform_envelope_tests']=[C.steal_audio_test(rom,renderer(),0x81,s,at)
        for s in (0xBF,0xA6) for at in (200,331,702)]
    wrap=[]
    for rid in REC:
        loop=json.loads((OUT/f'{rid:02X}/loop.json').read_text())
        at=loop['selected_common_cut_after_tick']+loop['period_ticks']-5
        for sfx,k in ((0xBF,20),(0xA6,40)):
            _,_,reads,_,_=M.capture(rom,rid,at+k+180)
            expected=next(t for t in reads[2] if t>at+k)
            d=T.Driver(rom);d.request(rid);actual=None
            for t in range(1,at+k+180):
                if t==at:d.request(sfx)
                before=d.mem[0xDEA0];d.tick()
                if t>at+k and before&16 and not d.mem[0xDEA0]&16:actual=actual or t
            assert expected==actual
            wrap.append(dict(music=f'{rid:02X}',sfx=f'{sfx:02X}',request_tick=at,
                release_tick=at+k,recovery_tick=actual,match=True))
    result['loop_wrap_controls']=wrap
    save(OUT/'recovery-validation.json',result)
    return result

def package():
    metrics=json.loads((OUT/'library-metrics.json').read_text())
    opening=json.loads((OUT/'opening-validation.json').read_text())
    recover=json.loads((OUT/'recovery-validation.json').read_text())
    for v in metrics.values():
        assert v['sanity']['clipped_frames']==0
        assert v['pitch']['windows_off_by_more_than_25_cents']==0
        assert all(r.get('mismatched_ticks',0)==0 for r in v['duration'].values())
        assert v['runtime_two_stem_sum_max_lsb']==0
    readme='''M4 SIX-ID PRIVATE AUDIO LIBRARY — 24 October 2026

Do not publish these ROM-derived WAV/VGM/read maps or this ZIP.
No ROM, third-party renderer binaries, or GameMaker project files are included.
Authoritative inventory: manifest.json. Verify the ZIP SHA-256 supplied separately
in private-package-receipt.json / the public production-validation receipt.

Restore from the Research topic's tools/m4_restore_audio.py:
  python tools/m4_restore_audio.py PRIVATE.zip NEW_PRIVATE_FOLDER --sha256 EXPECTED
  python tools/m4_restore_audio.py PRIVATE.zip NEW_PRIVATE_FOLDER --sha256 EXPECTED --check
The second restore should write 0 files. Never infer authenticity from a filename.

All delivery WAVs: 44100 Hz signed16 little-endian mono; 735 samples/tick.
reference-stereo.wav retains the identical two-lane original renderer output.
Per ID: ch0..ch3.wav are raw synchronized original-driver isolated stems.
Runtime: ch2.wav + other3.wav reproduces reference mix exactly. other3.wav is
reference_mix - ch2, assigning only the <=6-LSB isolated-stem rounding residual
to that grouped stem. other3-raw.wav retains the uncorrected ch0+ch1+ch3 sum.
No normalization/EQ/resampling/crossfade was applied. Raw four-stem sums reach
6 LSB for 99/82/81; preserve the recorded FAIL against AUDIO-1B's observed 5-LSB
short-sample maximum. The explicit production cap is 8 LSB; Manager reviews it.

81 and 82: apply one common loop.json sample interval to every stem, not the
whole WAV. Intervals are [start,end) with intro [0,start). Zero endpoint jump
was measured; inaudibility and native gapless playback are NOT established.
99: finite; all music channels inactive at tick1189, no loop flag. Temporary
silence at tick1086 is not completion. 90: dry opening800 ticks, not EEZ3 loop.
BF and A6: channel2 one-shots, channel ownership20/40 ticks despite audible
20/36 ticks. Use stream-reads.json tone2 map to recover after release; do not
resume at WAV end or infer recovery from any attenuation-off write.

opening-tails/fade_FFFF.wav: 23 ticks, begins before one-based driver tick F.
F=post-entry E+7=title handoff H-33, F range9..745 inclusive. Append dry prefix
[0,(F-1)*735), then the exact tail, then silence until H. Original reset on
F+22 can leave one resampler residual sample (<=887 LSB); the rest of that tick
is exactly zero. Preserve that sample. Five listen_E*.wav paths reconstruct
fresh full original-driver renderings exactly; they are not listening PASS.

Source contract cbf3e9c00abf094b140cdf846eb05826bbdeac2e; use the separately
accepted M3 baseline for future integration. No M3/POC changes are included.
Renderer/ROM/tool provenance and every file hash are in manifest.json.
Reproduction: m4_build_renderer.py, then m4_produce_audio.py ROM library,
tails --jobs 4, package. Work only inside ignored build storage.
'''
    (OUT/'RESTORE_AND_INTEGRATE.txt').write_text(readme,encoding='utf8')
    manifest=dict(schema_version=1,rom_sha256=T.ROM_SHA256,contract_commit='cbf3e9c00abf094b140cdf846eb05826bbdeac2e',
        renderer=json.loads((ROOT/'build/m4/renderer/build-manifest.json').read_text()),
        psg_clock_hz=3546893,driver_ticks_per_second=60,samples_per_tick=735,
        delivery_format=dict(rate=44100,bits=16,channels=1,encoding='signed little-endian PCM WAV'),
        references='stereo identical-lane WAV; VGM and private read maps retained',
        six_ids=list(metrics),assets=metrics,opening=opening,recovery=recover,
        source_files_sha256={str(p.relative_to(ROOT)).replace('\\','/'):sha(p.read_bytes())
            for p in [ROOT/'tools'/f for f in ('m4_produce_audio.py','m4_build_renderer.py',
                'm4_restore_audio.py','m4_audio.py','audio1_psg_trace.py','audio1b_render.py',
                'audio1b_analyze.py','audio1b_checks.py')]},
        listening='NOT PERFORMED; seam/timbre/native playback remain acceptance gates',files={})
    # Include all private payloads/evidence, excluding resumable render caches.
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and p.name not in ('manifest.json','render-cache.json'):
            manifest['files'][p.relative_to(OUT).as_posix()]=dict(bytes=p.stat().st_size,sha256=sha(p.read_bytes()))
    save(OUT/'manifest.json',manifest)
    archive=ROOT/'build/m4/SonicChaos_M4_AUDIO_20261024_PRIVATE.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for rel in manifest['files']:z.write(OUT/rel,rel)
        z.write(OUT/'manifest.json','manifest.json')
    # Verify CRC, traversal-safe names and every member hash without modifying sources.
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for rel,v in manifest['files'].items():
            assert not Path(rel).is_absolute() and '..' not in Path(rel).parts
            assert sha(z.read(rel))==v['sha256']
    receipt=dict(archive=archive.name,sha256=sha(archive.read_bytes()),bytes=archive.stat().st_size,
        members=len(manifest['files'])+1,crc_and_member_hashes='PASS',
        manifest_sha256=sha((OUT/'manifest.json').read_bytes()))
    save(ROOT/'build/m4/private-package-receipt.json',receipt)
    safe=dict(renderer={k:v for k,v in manifest['renderer'].items() if k!='executable'},
        metrics=metrics,opening=opening,recovery=recover,package=receipt,
        noise=json.loads((OUT/'noise-validation.json').read_text()),
        AUDIO1B_conformance=json.loads((OUT/'conformance-validation.json').read_text()),
        title_independent_reference=json.loads((OUT/'title-independent-reference.json').read_text()),
        no_listening_or_native_game_test=True)
    # Strip metadata stream addresses not needed in the public validation report.
    for v in safe['metrics'].values():v.pop('header',None)
    save(ROOT/'data/m4/production-validation.json',safe)
    print(json.dumps(receipt,indent=2))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom')
    p.add_argument('mode',choices=['library','tails','package']);p.add_argument('--jobs',type=int,default=4)
    a=p.parse_args();rom=T.load_rom(a.rom)
    if a.mode=='library':library(rom);recovery(rom)
    elif a.mode=='tails':tails(rom,a.jobs)
    else:package()

if __name__=='__main__':main()
