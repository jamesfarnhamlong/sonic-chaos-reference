"""Bounded PRIVATE P1 render/composition/chunk proof. Never bulk production.

Requires numpy from the established M4 dependency directory; pinned MAME binary,
authenticated M4 preparation directory and an authenticated local ROM.
All payloads, dry events and streams remain below ignored build/m5-proof/.
"""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import wave
import zipfile
import numpy as np
import audio1_psg_trace as T
import audio1b_render as R
import audio1b_checks as C
import audio1b_analyze as A
from m5p0_model import Model
from m5p0_proof import compare_case

ROOT=Path(__file__).resolve().parents[1]
PRIVATE=ROOT/'build/m5-proof'
OUT=PRIVATE/'package'
PUBLIC=ROOT/'data/m5-proof'
PIN='36821f4cfb6a1b6e386f1b468504245c21c6e24a2cbb0cba4b268703c96334a0'
RENDERS=[];START=time.perf_counter()
LIMIT_BYTES=2*1024**3;LIMIT_SECONDS=1800
SELECTED=(0x88,0xA0,0xA3,0xAC,0xB6,0xBA,0xBC,0xC0)

def sha(data):return hashlib.sha256(data).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def directory_bytes(p):return sum(x.stat().st_size for x in p.rglob('*') if x.is_file())
def limits():
    if time.perf_counter()-START>LIMIT_SECONDS:raise RuntimeError('30-minute proof budget reached')
    if directory_bytes(PRIVATE)>LIMIT_BYTES:raise RuntimeError('2GiB scratch cap reached')
    if shutil.disk_usage(PRIVATE).free<4*1024**3:raise RuntimeError('less than4GiB free; stop')
def wav(path,pcm):
    path.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(path),'wb') as f:f.setparams((1,2,44100,0,'NONE','not compressed'));f.writeframes(np.asarray(pcm,dtype='<i2').tobytes())
def mono(path):return R.read_wav(path)[:,0]

class MEMORY(ctypes.Structure):
    _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[(n,ctypes.c_size_t) for n in
        ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
def peak_memory(handle=None):
    if os.name!='nt':return None
    obj=MEMORY();obj.cb=ctypes.sizeof(obj)
    fn=ctypes.windll.psapi.GetProcessMemoryInfo
    fn.argtypes=[wintypes.HANDLE,ctypes.POINTER(MEMORY),wintypes.DWORD]
    if handle is None:
        ctypes.windll.kernel32.GetCurrentProcess.restype=wintypes.HANDLE
        handle=ctypes.windll.kernel32.GetCurrentProcess()
    if not fn(handle,ctypes.byref(obj),obj.cb):return None
    return int(obj.PeakWorkingSetSize)

def render(rows,label,fresh=False):
    limits();vgm=R.build_vgm(rows);assert not R.vgm_matches(rows,vgm)
    exe=Path(os.environ['AUDIO1B_VGM2WAV']);assert sha(exe.read_bytes())==PIN
    cache=PRIVATE/'render-cache';cache.mkdir(exist_ok=True)
    key=sha(vgm+exe.read_bytes());dest=cache/(key+'.wav');receipt=cache/(key+'.json')
    if not fresh and dest.exists() and receipt.exists() and sha(dest.read_bytes())==json.loads(receipt.read_text())['sha256']:
        return R.read_wav(dest)[:len(rows)*735]
    t=time.perf_counter();peak=0
    with tempfile.TemporaryDirectory(dir=PRIVATE) as temp:
        src=Path(temp)/'input.vgm';dst=Path(temp)/'output.wav';src.write_bytes(vgm)
        proc=subprocess.Popen([str(exe),'--samplerate','44100','--bps','16','--fade','0','--loops','1',str(src),str(dst)],
            stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,env=dict(os.environ,VGM_SN_CORE='MAME'))
        while proc.poll() is None:
            peak=max(peak,peak_memory(int(proc._handle)) or 0);time.sleep(.005)
        error=proc.stderr.read().decode(errors='replace')
        if proc.returncode or not dst.exists():raise RuntimeError(error)
        pcm=R.read_wav(dst)
        assert len(pcm)>=len(rows)*735 and np.array_equal(pcm[:,0],pcm[:,1])
        pcm=pcm[:len(rows)*735].copy()
        R.write_wav(dest,pcm)
    elapsed=time.perf_counter()-t
    save(receipt,dict(sha256=sha(dest.read_bytes()),key=key))
    RENDERS.append(dict(label=label,ticks=len(rows),seconds=elapsed,renderer_peak_working_set_bytes=peak,
        audio_seconds_per_wall_second=len(rows)/60/elapsed,fresh_process=True))
    return pcm

def capture(rom,music,events,ticks):
    d=T.Driver(rom);d.request(music);rows=[];states=[];flags=[]
    for t in range(1,ticks+1):
        for kind,value in events.get(t,[]):
            if kind=='request':d.request(value)
            elif kind=='fade':d.mem[0xDE09:0xDE0C]=bytes(value)
            else:raise ValueError(kind)
        n=len(d.writes);d.tick();rows.append([v for _,v in d.writes[n:]])
        states.append(d.psg.state());flags.append([d.mem[a] for a in T.CHANNELS])
    return rows,states,flags

def spectral(pcm):
    x=np.asarray(pcm,dtype=np.float64);x=x[np.abs(x)>0]
    if len(x)<16:return dict(samples=len(x),rms_lsb=0,zero_crossing_rate=0,spectral_flatness=None)
    seg=x[:min(len(x),16384)];p=np.abs(np.fft.rfft((seg-seg.mean())*np.hanning(len(seg))))**2+1e-12
    return dict(samples=len(x),rms_lsb=float(np.sqrt(np.mean(x*x))),zero_crossing_rate=float(np.mean(x[1:]*x[:-1]<0)),
        spectral_flatness=float(np.exp(np.mean(np.log(p)))/np.mean(p)))

def preserve_m4(m4,poc):
    expected='c57d37af7a8d4c7e83acbf1a1b2c9ef13ef4066e482cf575438006c30040d722'
    assert sha((m4/'manifest.json').read_bytes())==expected
    manifest=json.loads((m4/'manifest.json').read_text());before={}
    for rid in ('81','82','90','99','BF','A6'):
        for name in ('mix.wav','ch0.wav','ch1.wav','ch2.wav','ch3.wav','other3.wav'):
            rel=f'{rid}/{name}';p=m4/rel
            assert sha(p.read_bytes())==manifest['files'][rel]['sha256']
            before[str(p)]=sha(p.read_bytes())
    assert subprocess.check_output(['git','-C',str(poc),'rev-parse','HEAD'],text=True).strip()=='11bff34356d5f5d979218896dc95fdc4bb265eae'
    runtime=json.loads((poc/'datafiles/m4/runtime-manifest.json').read_text())
    for entry in runtime['files']:
        p=poc/'datafiles'/entry['file'];assert sha(p.read_bytes())==entry['sha256'];before[str(p)]=entry['sha256']
    return before

def library(rom,m4):
    cat={r['request_id']:r for r in json.loads((ROOT/'data/m5/catalogue.json').read_text())['entries']}
    templates={};metrics={}
    # B8 is a diagnostic-only fixed-rate control required by the coupled-noise brief.
    for rid in SELECTED+(0xB8,):
        n=cat[rid]['execution']['finite_inactive_tick']+20
        rows,states,flags=capture(rom,rid,{},n);folder=OUT/('diagnostic-B8' if rid==0xB8 else f'library/{rid:02X}')
        folder.mkdir(parents=True,exist_ok=True);(folder/'reference.vgm').write_bytes(R.build_vgm(rows))
        save(folder/'private-registers.json',dict(states=states,flags=flags))
        mix=render(rows,f'{rid:02X}-mix');st=[render(R.attenuation_stem(rows,c),f'{rid:02X}-voice{c}') for c in range(4)]
        repeat=render(rows,f'{rid:02X}-determinism',True);assert np.array_equal(mix,repeat)
        raw=[s[:,0].copy() for s in st];error=mix[:,0].astype(np.int32)-sum(s.astype(np.int32) for s in raw)
        corrected=[v.copy() for v in raw];c0=raw[0].astype(np.int32)+error
        assert np.abs(c0).max()<=32767;corrected[0]=c0.astype(np.int16)
        recon=sum(v.astype(np.int32) for v in corrected);assert np.array_equal(recon,mix[:,0].astype(np.int32))
        wav(folder/'mix.wav',mix[:,0])
        for c in range(4):wav(folder/f'raw{c}.wav',raw[c]);wav(folder/f'experimental{c}.wav',corrected[c])
        metric=dict(id=rid,diagnostic_only=rid==0xB8,ticks=n,rate=44100,bits=16,channels=1,samples=n*735,
            header=cat[rid]['driver_header'],release_ticks=cat[rid]['execution']['release_ticks'],sanity=C.sanity(mix),
            pitch=C.pitch_report(rows,st,min_ticks=1 if rid>=0xA0 else 3),envelope=C.duration_report(rows,st),noise=spectral(raw[3]),
            raw_reconstruction_max_lsb=int(np.abs(error).max()),residual_rms_lsb=float(np.sqrt(np.mean(error.astype(float)**2))),
            tone0_residual_when_original_tone0_silent=bool(np.count_nonzero(c0) and not np.count_nonzero(raw[0])),
            experimental_four_voice_reconstruction_max_lsb=int(np.abs(recon-mix[:,0]).max()),deterministic=True,
            mix_sha256=sha((folder/'mix.wav').read_bytes()),vgm_sha256=sha(R.build_vgm(rows)))
        save(folder/'metrics.json',metric);metrics[f'{rid:02X}']=metric
        templates[rid]=dict(raw=raw,corrected=corrected,states=states)
        print(f'P1 {rid:02X} rendered; residual {metric["raw_reconstruction_max_lsb"]}LSB; pitch failures {metric["pitch"]["windows_off_by_more_than_25_cents"]}',flush=True)
    for rid in (0x81,0x82,0x99,0xBF,0xA6):
        raw=[mono(m4/f'{rid:02X}/ch{c}.wav') for c in range(4)]
        corrected=[v.copy() for v in raw]
        corrected[0]=(mono(m4/f'{rid:02X}/other3.wav').astype(np.int32)-raw[1].astype(np.int32)-raw[3].astype(np.int32)).astype(np.int16)
        # Capturing registers is not regenerating any accepted M4 audio.
        rows,states,_=capture(rom,rid,{},len(raw[0])//735)
        templates[rid]=dict(raw=raw,corrected=corrected,states=states)
    return templates,metrics

def select_voice(m,voice):
    # Deliberately retained FAILED experiment: treating write-inhibit as mute
    # loses held PSG output (demonstrated by B8+BC). Never ship this selector.
    for i in ([4] if voice==1 else [5] if voice==2 else [6] if voice==3 else [])+[voice]:
        c=m.channels[i]
        if c.flags&128 and not c.flags&4 and not c.waiting:return c
    return None

def compose(bank,templates,music,events,ticks):
    m=Model(bank);m.direct(music);voices=[np.zeros(ticks*735,dtype=np.int32) for _ in range(4)];states=[]
    for tick in range(1,ticks+1):
        for kind,v in events.get(tick,[]):
            if kind=='request':m.direct(v)
            elif kind=='fade':m.fade=list(v)
        m.tick();period=[0,0,0];att=[15]*4;noise=0
        for voice in range(4):
            c=select_voice(m,voice)
            if c:
                data=templates[c.rid];age=c.age-1;a=age*735;b=a+735
                if b<=len(data['corrected'][voice]):voices[voice][(tick-1)*735:tick*735]=data['corrected'][voice][a:b]
                if age<len(data['states']):
                    snap=data['states'][age];att[voice]=snap[2][voice]
                    if voice<3:period[voice]=snap[0][voice]
                    else:
                        noise=snap[1]
                        if noise&3==3:period[2]=snap[0][2]
        # Retained generic fade approximation; offsets are metadata, no new synth.
        if m.fade[0]:
            gain=10**(-2*(12-m.fade[0])/20)
            for v in voices:v[(tick-1)*735:tick*735]=np.rint(v[(tick-1)*735:tick*735]*gain).astype(np.int32)
        states.append((tuple(period),noise,tuple(att)))
    return sum(voices),voices,states

def comparison_metrics(reference,composed,ref_voices,voices):
    x=reference.astype(np.float64);y=composed.astype(np.float64);error=y-x
    a=A.tick_rms(x);b=A.tick_rms(y);peak=max(float(np.max(np.abs(x))),1)
    return dict(sample_equal=bool(np.array_equal(reference,composed)),sample_max_error_lsb=int(np.max(np.abs(error))),
        sample_error_rms_lsb=float(np.sqrt(np.mean(error*error))),waveform_correlation=A.corr(x,y),
        envelope_correlation=A.corr(a,b),max_tick_rms_error_percent_peak=float(np.max(np.abs(a-b))/peak*100),
        per_voice=[dict(channel=c,sample_equal=bool(np.array_equal(ref_voices[c],voices[c])),
            waveform_correlation=A.corr(ref_voices[c],voices[c]),envelope_correlation=A.corr(A.tick_rms(ref_voices[c]),A.tick_rms(voices[c])),
            noise_metrics_reference=spectral(ref_voices[c]) if c==3 else None,
            noise_metrics_composed=spectral(voices[c]) if c==3 else None) for c in range(4)])

def scenarios(rom,bank,templates):
    cases={
        'BF-A3':(0x81,{30:[('request',0xBF)],35:[('request',0xA3)]},180),
        'A3-BF':(0x81,{30:[('request',0xA3)],35:[('request',0xBF)]},180),
        'AC-A0':(0x81,{30:[('request',0xAC)],35:[('request',0xA0)]},180),
        'B6-A0':(0x81,{30:[('request',0xB6)],35:[('request',0xA0)]},180),
        'BA-partial':(0x81,{30:[('request',0xBA)],36:[('request',0xAC)]},180),
        'fixed-B8-BC':(0x81,{30:[('request',0xB8)],35:[('request',0xBC)]},210),
        'near-loop':(0x81,{3989:[('request',0xA6)]},4200),
        'fade-multiple':(0x81,{30:[('request',0xAC)],35:[('request',0xA0)],40:[('fade',(12,1,2))]},120),
        'late-finite':(0x99,{1180:[('request',0xA6)]},1300)}
    result={}
    for name,(music,ev,n) in cases.items():
        limits();state=compare_case(rom,bank,music,ev,n);assert not state['failures'],(name,state['failures'][:1])
        rows,registers,flags=capture(rom,music,ev,n);mix=render(rows,name+'-continuous')[:,0]
        ref_voices=[render(R.attenuation_stem(rows,c),name+f'-ref-voice{c}')[:,0] for c in range(4)]
        composed,voices,approx_registers=compose(bank,templates,music,ev,n)
        folder=OUT/'scenarios'/name;folder.mkdir(parents=True,exist_ok=True)
        (folder/'continuous.vgm').write_bytes(R.build_vgm(rows));wav(folder/'continuous.wav',mix)
        assert np.abs(composed).max()<=32767
        wav(folder/'composed-experiment.wav',composed)
        for c in range(4):wav(folder/f'continuous-voice{c}.wav',ref_voices[c]);wav(folder/f'composed-voice{c}.wav',voices[c])
        # Gate/register projection from dry templates is deliberately tested,
        # not asserted equivalent to an executing driver envelope/modulator.
        mismatches=dict(audible_tone_periods=[0]*3,audible_attenuation=[0]*4,audible_noise_controls=0)
        for original,projected in zip(registers,approx_registers):
            for c in range(4):
                if original[2][c]<15 and original[2][c]!=projected[2][c]:mismatches['audible_attenuation'][c]+=1
            for c in range(3):
                if original[2][c]<15 and original[0][c]!=projected[0][c]:mismatches['audible_tone_periods'][c]+=1
            if original[2][3]<15 and original[1]!=projected[1]:mismatches['audible_noise_controls']+=1
        metric=comparison_metrics(mix,composed,ref_voices,voices)
        metric.update(ticks=n,state_model='PASS',register_projection_mismatches=mismatches,
            diagnostic_register_projection='not a note/envelope driver port; failures retained',
            voice_pitch_reference=C.pitch_report(rows,[np.repeat(v[:,None],2,axis=1) for v in ref_voices]),
            voice_pitch_composed=C.pitch_report(rows,[np.repeat(v[:,None],2,axis=1) for v in voices]),
            native_listening='NOT PERFORMED',generic_fade_approximation=name=='fade-multiple')
        save(folder/'private-timeline.json',dict(events=ev,registers=registers,flags=flags))
        save(folder/'metrics.json',metric);result[name]=metric
        print(f'{name}: state PASS, envelope {metric["envelope_correlation"]:.6f}, max RMS delta {metric["max_tick_rms_error_percent_peak"]:.3f}% peak',flush=True)
    return result

def split_chunks(voices,folder):
    folder.mkdir(parents=True,exist_ok=True);manifest=dict(rate=44100,bits=16,channels=1,samples_per_tick=735,chunk_ticks=4096,voices=[])
    for c,voice in enumerate(voices):
        raw=np.asarray(voice,dtype='<i2').tobytes();parts=[]
        for start in range(0,len(raw),4096*735*2):
            data=raw[start:start+4096*735*2];rel=f'voice{c}_{len(parts):03d}.pcm';(folder/rel).write_bytes(data)
            parts.append(dict(file=rel,first_sample=start//2,samples=len(data)//2,bytes=len(data),sha256=sha(data)))
        manifest['voices'].append(dict(samples=len(raw)//2,sha256=sha(raw),chunks=parts))
    save(folder/'manifest.json',manifest);return manifest

class ChunkReader:
    def __init__(self,folder,expected_manifest_sha256):
        self.folder=folder;raw=(folder/'manifest.json').read_bytes()
        if sha(raw)!=expected_manifest_sha256:raise ValueError('untrusted/corrupt manifest')
        self.manifest=json.loads(raw);self.cache={};names=set()
        if (self.manifest['rate'],self.manifest['bits'],self.manifest['channels'],self.manifest['chunk_ticks'])!=(44100,16,1,4096):raise ValueError('format mismatch')
        for voice in self.manifest['voices']:
            position=0
            for entry in voice['chunks']:
                if Path(entry['file']).name!=entry['file'] or entry['file'] in names:raise ValueError('unsafe/duplicate chunk path')
                names.add(entry['file'])
                if entry['first_sample']!=position or not 0<entry['samples']<=4096*735 or entry['bytes']!=entry['samples']*2:raise ValueError('invalid chunk addressing')
                position+=entry['samples']
            if position!=voice['samples']:raise ValueError('incomplete voice')
    def load(self,voice,index):
        entry=self.manifest['voices'][voice]['chunks'][index];path=self.folder/entry['file']
        if not path.is_file():raise ValueError('missing chunk')
        data=path.read_bytes()
        if len(data)!=entry['bytes'] or sha(data)!=entry['sha256']:raise ValueError('corrupt chunk')
        return data
    def sample(self,voice,absolute,cut=None,period=None):
        if cut is not None and absolute>=cut:absolute=cut+(absolute-cut)%period
        v=self.manifest['voices'][voice]
        if not 0<=absolute<v['samples']:raise IndexError('sample outside asset')
        index=absolute//(4096*735);entry=v['chunks'][index]
        key=(voice,index)
        if key not in self.cache:
            # Two synchronized chunk groups maximum; prototype, not native I/O.
            self.cache={k:v for k,v in self.cache.items() if k[1] in (index,index+1)}
            self.cache[key]=self.load(voice,index)
        local=(absolute-entry['first_sample'])*2
        return int.from_bytes(self.cache[key][local:local+2],'little',signed=True)

def chunk_proof(templates):
    voices=templates[0x82]['corrected'];folder=OUT/'chunks-82';manifest=split_chunks(voices,folder);trusted=sha((folder/'manifest.json').read_bytes());reader=ChunkReader(folder,trusted)
    exact=[]
    for c,v in enumerate(voices):
        raw=b''.join(reader.load(c,i) for i in range(len(manifest['voices'][c]['chunks'])))
        exact.append(raw==np.asarray(v,dtype='<i2').tobytes())
    rng=np.random.default_rng(5);positions=list(map(int,rng.integers(0,len(voices[0]),1000)))
    positions += [0,4096*735-1,4096*735,4096*735+1,8192*735-1,8192*735,len(voices[0])-1]
    assertions=0
    for c,v in enumerate(voices):
        for pos in positions:assert reader.sample(c,pos)==int(v[pos]);assertions+=1
        cut=1879*735;period=6912*735
        for pos in [cut-1,cut,4096*735-1,4096*735,8192*735,cut+period-1,cut+period,cut+period+1,cut+3*period+4096*735]:
            mapped=cut+(pos-cut)%period if pos>=cut else pos
            assert reader.sample(c,pos,cut,period)==int(v[mapped]);assertions+=1
    # Negative fixtures are separate copies, retaining every accepted source.
    entry=manifest['voices'][0]['chunks'][0];path=folder/entry['file'];original=path.read_bytes()
    path.write_bytes(original[:-2]+bytes((original[-2]^1,original[-1])))
    rejected=False
    try:ChunkReader(folder,trusted).load(0,0)
    except ValueError:rejected=True
    finally:path.write_bytes(original)
    assert rejected
    alternate=folder/'negative-missing';alternate.mkdir(exist_ok=True);save(alternate/'manifest.json',manifest)
    missing=False
    try:ChunkReader(alternate,trusted).load(0,0)
    except ValueError:missing=True
    assert missing
    # Leave no intentionally broken fixture in the deliverable inventory.
    (alternate/'manifest.json').unlink();alternate.rmdir()
    return dict(source='authenticated M4 82 existing continuous PCM; experimental tone0 residual grouping',
        no_new_music_render=True,chunk_ticks=4096,mono_chunk_max_bytes=4096*735*2,voices=4,
        reconstructed_exact=exact,sample_address_assertions=assertions,corrupt_rejected=rejected,missing_rejected=missing,
        synchronized_boundaries=True,loop_cut_sample=1879*735,loop_period_samples=6912*735,
        native_cache_performance='NOT TESTED',bytes=directory_bytes(folder))

def package(rom_path,m4,poc):
    OUT.mkdir(parents=True,exist_ok=True);free=shutil.disk_usage(PRIVATE).free
    before=preserve_m4(m4,poc);rom=T.load_rom(rom_path)
    p0=json.loads((PUBLIC/'p0-result.json').read_text());assert p0['status']=='PASS'
    bank=json.loads((PRIVATE/'dry-event-bank.json').read_text())
    save(PUBLIC/'budget-preflight.json',dict(free_bytes_before=free,scratch_cap_bytes=LIMIT_BYTES,archive_cap_bytes=512*1024**2,
        render_wall_cap_seconds=LIMIT_SECONDS,estimated_scratch_bytes=700*1024**2,estimated_archive_bytes=160*1024**2,
        approved_selected_ids=list(SELECTED),diagnostic_only_extra_id=0xB8,decision='within limits'))
    templates,metrics=library(rom,m4)
    coupled=scenarios(rom,bank,templates)
    chunks=chunk_proof(templates)
    for path,digest in before.items():assert sha(Path(path).read_bytes())==digest
    save(OUT/'M4-preservation.json',dict(before_and_after_equal=True,files_checked=len(before),sha256=before))
    shutil.copy2(PRIVATE/'dry-event-bank.json',OUT/'private-dry-event-bank.json')
    save(PUBLIC/'p1-library.json',metrics);save(PUBLIC/'coupled-noise.json',coupled);save(PUBLIC/'chunk-proof.json',chunks)
    save(OUT/'proof-results.json',dict(p0=p0,library=metrics,coupled=coupled,chunks=chunks))
    (OUT/'README_PRIVATE.txt').write_text('M5 P0/P1 PROOF ONLY. Original derived audio: PRIVATE, DO NOT PUBLISH.\nNo ROM or renderer binary included. Not a GameMaker release.\nExperimental compositions are NOT bit-identical and have NOT been listened to.\nUse public handover for GO/HOLD; do not treat asset presence as acceptance.\n',encoding='utf-8')
    manifest=dict(rom_sha256=T.ROM_SHA256,renderer_sha256=PIN,rate=44100,bits=16,ticks_per_second=60,clock=3546893,files={})
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and p!=OUT/'manifest.json':manifest['files'][p.relative_to(OUT).as_posix()]=dict(bytes=p.stat().st_size,sha256=sha(p.read_bytes()))
    save(OUT/'manifest.json',manifest)
    archive=PRIVATE/'SonicChaos_M5_P0P1_20261024_PROOF_PRIVATE.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for rel in manifest['files']:z.write(OUT/rel,rel)
        z.write(OUT/'manifest.json','manifest.json')
    assert archive.stat().st_size<512*1024**2
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for rel,v in manifest['files'].items():assert sha(z.read(rel))==v['sha256']
    limits()
    receipt=dict(archive_name=archive.name,sha256=sha(archive.read_bytes()),bytes=archive.stat().st_size,members=len(manifest['files'])+1,
        crc_and_hashes='PASS',manifest_sha256=sha((OUT/'manifest.json').read_bytes()))
    save(PUBLIC/'private-package-receipt.json',receipt)
    render_seconds=sum(x['seconds'] for x in RENDERS);audio_seconds=sum(x['ticks']/60 for x in RENDERS)
    save(PUBLIC/'measured-budget.json',dict(elapsed_seconds=time.perf_counter()-START,render_calls=RENDERS,
        renderer_wall_seconds=render_seconds,total_rendered_voice_timeline_seconds=audio_seconds,
        aggregate_timeline_per_wall_second=audio_seconds/max(render_seconds,1e-9),
        python_process_peak_working_set_bytes=peak_memory(),scratch_bytes=directory_bytes(PRIVATE),package_payload_bytes=directory_bytes(OUT),
        archive_bytes=archive.stat().st_size,free_bytes_after=shutil.disk_usage(PRIVATE).free,
        m4_preserved_files=len(before),m4_all_preserved=True))
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('rom');p.add_argument('--m4',required=True);p.add_argument('--poc',required=True);a=p.parse_args()
    package(a.rom,Path(a.m4),Path(a.poc))
