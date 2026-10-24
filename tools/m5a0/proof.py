"""M5-A0 bounded integration proof. Candidate never consumes combined oracle events."""
import argparse,copy,ctypes as C,hashlib,json,os,shutil,statistics,sys,time,zipfile,zlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from backend import PSG,candidate
from m5p1c import CASES as BASE,preservation
from m5p0r_probe import Trace
import audio1_psg_trace as T
from m5p1_proof import mono,wav,comparison_metrics
from m5p1c_pcm import pitch_report
from m5p0r_pcm import phase_energy
OUT=ROOT/'build/m5-a0';PUB=ROOT/'data/m5-a0';PRIOR=ROOT.parent/'sonic-chaos-reference-m5-p1c/build/m5-p1c';P0P1=ROOT.parent/'sonic-chaos-reference-m5-proof/build/m5-proof'
DLL=OUT/'psg-a0.dll'
def load(p):return json.loads(p.read_text())
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
CASES=copy.deepcopy(BASE)
CASES.update({'BF-A3':dict(initial=0x81,events={30:[('request',0xBF)],35:[('request',0xA3)]},ticks=180),
 'A3-BF':dict(initial=0x81,events={30:[('request',0xA3)],35:[('request',0xBF)]},ticks=180),
 'near-loop':dict(initial=0x81,events={3989:[('request',0xA6)]},ticks=4200)})
def original(rom,case):
 d=Trace(rom);d.request(case['initial']);rows=[]
 for tick in range(1,case['ticks']+1):
  for kind,value in case['events'].get(tick,[]):
   if kind=='request':d.request(value)
   elif kind=='fade':d.mem[0xDE09:0xDE0C]=bytes(value)
  start=len(d.writes);d.tick()
  rows.append(dict(ports=[b for _,b in d.writes[start:]],registers=d.psg.state(),latch=d.psg.latch//16,saved_noise=d.mem[0xDE11],channels=[d.mem[a]&0xD4 for a in T.CHANNELS],priority=d.mem[0xDE0F]))
 return rows

def refs(name):
 mapping={'fixed-hold':'fixed-B8-BC','music-context-B6':'B6-A0','music-context-BA':'BA-partial','BF-A3':'BF-A3','A3-BF':'A3-BF','near-loop':'near-loop'}
 if name in mapping:
  d=P0P1/'package/scenarios'/mapping[name];return d/'continuous.wav',[d/f'continuous-voice{v}.wav' for v in range(4)]
 if name=='isolated-context-B6':
  d=P0P1/'package/library/B6';return d/'mix.wav',[d/f'raw{v}.wav' for v in range(4)]
 d=PRIOR/'references'/name;return d/'continuous.wav',[d/f'voice{v}.wav' for v in range(4)]

def masked(bank,case,voice):
 # A diagnostic sink suppresses amplitudes only, preserving every event and clock.
 # Production candidate is always the full four-voice persistent instance.
 from audio1b_render import attenuation_stem
 from m5p0r_emission import EmissionModel
 m=EmissionModel(bank);m.direct(case['initial']);rows=[]
 for tick in range(1,case['ticks']+1):
  for kind,v in case['events'].get(tick,[]):
   if kind=='request':m.direct(v)
   else:m.fade=list(v)
  m.tick();rows.append(list(m.writes))
 rows=attenuation_stem(rows,voice);blocks=[]
 with PSG(DLL) as p:
  for row in rows:p.write(row);blocks.append(p.render())
 return np.concatenate(blocks)

def memory():
 class PMC(C.Structure):
  _fields_=[('cb',C.c_ulong),('faults',C.c_ulong)]+[(n,C.c_size_t) for n in ['peak_rss','rss','peak_paged','paged','peak_nonpaged','nonpaged','pagefile','peak_pagefile']]
 p=PMC();p.cb=C.sizeof(p)
 C.windll.psapi.GetProcessMemoryInfo(C.c_void_p(-1),C.byref(p),p.cb)
 return dict(process_peak_working_set_bytes=p.peak_rss,process_working_set_bytes=p.rss,scope='whole Python/NumPy process, not isolated native core or GameMaker')

def bench():
 with PSG(DLL) as p:
  p.write([0xC8,0x10,0xD0,0xE7,0xF2]);p.render()
  runs=[]
  for _ in range(5):
   t=time.perf_counter();p.lib.a0_bench(p.ptr,1200);runs.append(time.perf_counter()-t)
  block=[]
  for _ in range(600):
   t=time.perf_counter();p.render();block.append(time.perf_counter()-t)
  return dict(native_ticks_per_run=1200,native_runs_seconds=runs,median_native_seconds_per_tick=statistics.median(runs)/1200,
   median_realtime_factor=20/statistics.median(runs),ctypes_block_median_seconds=statistics.median(block),ctypes_block_p99_seconds=float(np.quantile(block,.99)),
   fixed_state_bytes=p.lib.a0_state_bytes(),resampler_buffer_bytes=p.lib.a0_buffer_bytes(p.ptr),native_rate=3546893//16,
   estimated_native_updates_per_tick=(3546893//16)/60,output_queue_bytes=8*735*2,memory=memory(),native_GameMaker='NOT MEASURED')

def run(rom):
 OUT.mkdir(exist_ok=True,parents=True);free=shutil.disk_usage(OUT).free;assert free>1024**3
 before=preservation();p1c_zip=ROOT.parent/'sonic-chaos-reference-m5-p1c/build/SonicChaos_M5_P1C_20261024_PROOF_PRIVATE.zip'
 assert sha(p1c_zip)=='fbd5264b6c07ed9bb04d63350a7c9e8a0b854a19208012f92adc4d96f9a9984c'
 sourcebank=PRIOR/'dry-emission-bank.json';bankpath=OUT/'private-dry-emission-bank.json'
 if not bankpath.exists():
  from m5p0r_proof import export
  export(rom,ids=[0x81],initial_bank=load(sourcebank),output_path=bankpath,max_ticks=4200)
 bank=load(bankpath);results={};input_hashes={};total=0;ordered=0;allrows={};start=time.perf_counter()
 for name,case in CASES.items():
  # Finish independently scheduled candidate before creating the oracle.
  t=time.perf_counter();pcm,rows=candidate(bank,case,DLL);candidate_seconds=time.perf_counter()-t
  oracle=original(rom,case);fail=[];chipfail=[];counterfail=[];written=set();latch=3;unwritten_defaults=0
  with PSG(DLL) as refstate:
   for tick,(o,m) in enumerate(zip(oracle,rows),1):
    for k in ['ports','registers','latch','saved_noise','channels','priority']:
     if json.dumps(o[k])!=json.dumps(m[k]):fail.append(dict(tick=tick,field=k))
    # Reference-only diagnostic core. Never feeds candidate or its PCM.
    refstate.write(o['ports']);refstate.render();s=refstate.state()
    if s!=m['psg_after']:counterfail.append(tick)
    # Check all actual chip register low fields against scheduled physical state.
    for value in m['ports']:
     if value&128:latch=(value>>4)&7
     written.add(latch)
    regs=m['psg_before'][:8];tones,noise,atten=m['registers']
    projected=[tones[0],atten[0],tones[1],atten[1],tones[2],atten[2],noise,atten[3]]
    for i in range(8):
     actual=regs[i]&(7 if i==6 else 15 if i&1 else 1023)
     if actual!=projected[i]:
      if i in written:chipfail.append(tick)
      else:unwritten_defaults+=1
  assert not fail and not chipfail and not counterfail,(name,fail[:2],chipfail[:2],counterfail[:2])
  mixpath,vpaths=refs(name);ref=mono(mixpath);n=len(pcm);assert len(ref)>=n;ref=ref[:n]
  refvoices=[mono(p)[:n] for p in vpaths]
  voices=[masked(bank,case,v) for v in range(4)]
  metrics=comparison_metrics(ref,pcm,refvoices,voices);metrics['pitch']=pitch_report([r['ports'] for r in rows],voices)
  metrics['reference_pitch']=pitch_report([r['ports'] for r in oracle],refvoices)
  metrics['phase_energy']=phase_energy(ref,pcm,refvoices,voices)
  metrics['nonzero_error_samples']=int(np.count_nonzero(pcm.astype(int)-ref))
  errors=(pcm.astype(np.int32)-ref.astype(np.int32)).reshape(-1,735)
  metrics['first_sample_max_error_lsb']=int(abs(errors[:,0]).max());metrics['interior_max_error_lsb']=int(abs(errors[:,1:]).max())
  aligned,_=candidate(bank,case,DLL,reference_chunks=True)
  metrics['reference_callback_alignment']=dict(callback_frames=2048,max_error_lsb=int(abs(aligned.astype(int)-ref).max()),
    nonzero_error_samples=int(np.count_nonzero(aligned!=ref)),events_from='independent model, unchanged')
  folder=OUT/'cases'/name;folder.mkdir(parents=True,exist_ok=True);wav(folder/'candidate.wav',pcm);wav(folder/'reference.wav',ref);wav(folder/'callback-aligned-candidate.wav',aligned)
  for v in range(4):wav(folder/f'candidate-voice{v}.wav',voices[v]);wav(folder/f'reference-voice{v}.wav',refvoices[v])
  save(folder/'private-state.json',dict(case=case,candidate_rows=rows,original_rows=oracle))
  total+=len(rows);ordered+=sum(len(r['ports']) for r in rows);allrows[name]=rows
  results[name]=dict(ticks=len(rows),ordered_bytes=sum(len(r['ports']) for r in rows),emission='PASS',emission_failures=fail,
   physical_chip_register_failures=chipfail,unwritten_core_vs_logical_initial_defaults=unwritten_defaults,counter_lfsr_reference_diagnostic_failures=counterfail,
   pcm=metrics,candidate_total_seconds=candidate_seconds,classification='same-core integration; residual measured, not bit-identical' if metrics['nonzero_error_samples'] else 'same-core integration; sample-exact bounded capture')
  for p in [mixpath]+vpaths:input_hashes[str(p.relative_to(ROOT.parent))]=sha(p)
  print(name,'emission PASS','PCM max',metrics['sample_max_error_lsb'],'interior',metrics['interior_max_error_lsb'],flush=True)
 # Counterexample-specific state evidence, no full note/clock programme is published.
 rows=allrows['coupled-steal-recover']
 _,solo=candidate(bank,dict(initial=0xA3,events={},ticks=48),DLL)
 history=dict(muted_ticks=28,muted_interval=[6,33],counter_lfsr_differences_from_uninterrupted_solo=sum(r['psg_after'][13:22]!=s['psg_after'][13:22] for r,s in zip(rows[5:33],solo[5:33])),
  changed_LFSR_boundaries=sum(rows[i]['psg_after'][21]!=rows[i-1]['psg_after'][21] for i in range(6,33)),resumed_source_reset=False,
  state33_noise_lfsr=rows[32]['psg_after'][21],solo33_noise_lfsr=solo[32]['psg_after'][21])
 # Diagnostic segmentation of exact resumed waveform.
 a=mono(OUT/'cases/coupled-steal-recover/reference-voice3.wav')[33*735:48*735]
 b=mono(OUT/'cases/coupled-steal-recover/candidate-voice3.wav')[33*735:48*735]
 history.update(resumed_noise_correlation=float(np.corrcoef(a,b)[0,1]),resumed_noise_max_error_lsb=int(abs(a.astype(int)-b).max()))
 fade=allrows['finite-fade'];fa=mono(OUT/'cases/finite-fade/reference-voice3.wav')[39*735:47*735];fb=mono(OUT/'cases/finite-fade/candidate-voice3.wav')[39*735:47*735]
 held=dict(first_tick=40,last_tick=47,reference_nonzero_samples=int(np.count_nonzero(fa)),candidate_nonzero_samples=int(np.count_nonzero(fb)),max_error_lsb=int(abs(fa.astype(int)-fb).max()),source_padding=False)
 # Pause means no driver/chip advance or speculative queue production.
 with PSG(DLL) as p:
  p.write([0xC8,0x10,0xD0,0xE7,0xF2]);p.render();state=p.state();time.sleep(.001);pause=p.state()==state
 # Segment-size sensitivity retained, not hidden by a widened tolerance.
 basepcm,_=candidate(bank,CASES['coupled-steal-recover'],DLL);splitpcm,_=candidate(bank,CASES['coupled-steal-recover'],DLL,True)
 segmentation=dict(block735_vs100plus635_max_error_lsb=int(abs(basepcm.astype(int)-splitpcm).max()),nonzero_error_samples=int(np.count_nonzero(basepcm!=splitpcm)))
 bankbytes=bankpath.read_bytes();eventbytes=sum(2+len(row['ports']) for row in allrows['near-loop'])
 report=dict(parent='ce0eb2df1a943386082c48e3b35ae00e0e622f76',management='01af5a87a8c06cd198db94cdf300867013b4c2d1',rom_sha256=T.ROM_SHA256,
  cases=results,total_ticks=total,total_ordered_bytes=ordered,candidate_inputs='intrinsic dry bank + external request/fade schedule only; oracle constructed afterwards',
  intrinsic_bank_sha256=sha(bankpath),intrinsic_source_bank_sha256=sha(sourcebank),new_solo_export=dict(id=0x81,ticks=4200,reason='existing accepted loop-boundary control exceeds old1400 coverage; no combined oracle data or PCM'),intrinsic_program_count=len(bank['programs']),intrinsic_bank_bytes=len(bankbytes),intrinsic_bank_deflate_bytes=len(zlib.compress(bankbytes,9)),
  representative_near_loop_scheduled_wire_bytes=eventbytes,representative_near_loop_mono_PCM_bytes=len(allrows['near-loop'])*735*2,
  reference_asset_hashes=input_hashes,build=load(OUT/'build.json'),history=history,held_fade=held,pause_no_advance=pause,segmentation=segmentation,
  performance=bench(),total_proof_seconds=time.perf_counter()-start,initial_free_bytes=free,preservation_before=before,preservation_after=preservation(),
  prior_P1C_archive_sha256=sha(p1c_zip),new_original_reference_renders=0,
  retained_diagnostics=[dict(issue='first gain trial was half reference amplitude',resolution='single-PSG VGMPlayer normalization 0x80 -> 0x200; fixed documented gain, no fitted waveform scaling'),
    dict(issue='initial unwritten MAME volume registers0 versus logical model off15',resolution='original-vs-model full-register assertion unchanged; core post-write check separate; reset starts volume amplitudes zero; defaults counted explicitly'),
    dict(issue='near-loop intrinsic1400-tick guard stopped prototype',resolution='extend solo81 intents only to4200; no combined oracle playback and no PCM padding')],
  verdict='CONDITIONAL GO: stateful integration demonstrated; licensing and native timing gates remain',native_listening='NOT PERFORMED')
 save(PUB/'results.json',report)
 print(json.dumps(dict(history=history,held=held,segmentation=segmentation,performance=report['performance']),indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--rom',required=True);a=p.parse_args();run(T.load_rom(a.rom))
