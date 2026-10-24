"""A1L helper experiment versus accepted A0, with unchanged independent emitter.
Only prior intrinsic event data and external schedules drive candidate playback.
Recorded original-driver rows are used after candidate generation for comparison.
"""
import ctypes as C,hashlib,json,sys,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools/m5a0'),str(ROOT/'tools'),str(Path(__file__).parent)]
from backend import PSG,candidate
from proof import CASES
from m5p1_proof import mono,wav,comparison_metrics
from m5p1c_pcm import pitch_report
from audio1b_render import attenuation_stem
from pe import pe_imports
OUT=ROOT/'build/m5-a1l';PUB=ROOT/'data/m5-a1l';A0=ROOT.parent/'sonic-chaos-reference-m5-a0/build/m5-a0';DLL=OUT/'psg-a1l.dll'
def load(p):return json.loads(p.read_text())
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def diff(a,b):
 e=a.astype(float)-b.astype(float)
 return dict(max_error_lsb=int(abs(e).max()),rms_error_lsb=float(np.sqrt(np.mean(e*e))),unequal_samples=int(np.count_nonzero(e)),correlation=float(np.corrcoef(a,b)[0,1]) if a.std() and b.std() else None)
def render(rows,dll):
 blocks=[]
 with PSG(dll) as p:
  for row in rows:p.write(row);blocks.append(p.render())
 return np.concatenate(blocks)
def run():
 parent=ROOT.parent/'sonic-chaos-reference-m5-a0/build/SonicChaos_M5_A0_20261024_STATEFUL_PRIVATE.zip'
 assert sha(parent)=='580725052986dcf5b79718fd2dd1ebfe93f09ed5ba0b9db879cea53c8343f004'
 bankpath=A0/'private-dry-emission-bank.json';bank=load(bankpath);results={};inputhash={};t=time.perf_counter()
 for name,case in CASES.items():
  start=time.perf_counter();pcm,rows=candidate(bank,case,DLL);elapsed=time.perf_counter()-start
  old=A0/'cases'/name;oldrows=load(old/'private-state.json');original=oldrows['original_rows'];baseline=oldrows['candidate_rows']
  emission=[];state=[]
  for tick,(m,o,a) in enumerate(zip(rows,original,baseline),1):
   for key in ['ports','registers','latch','saved_noise','channels','priority']:
    if json.dumps(m[key])!=json.dumps(o[key]):emission.append(dict(tick=tick,field=key))
   if m['psg_before'][:22]!=a['psg_before'][:22] or m['psg_after'][:22]!=a['psg_after'][:22]:state.append(tick)
  ref=mono(old/'reference.wav');a0=mono(old/'candidate.wav');aligned,_=candidate(bank,case,DLL,reference_chunks=True);fresh,_=candidate(bank,case,DLL)
  assert len(ref)==len(pcm) and not emission and not state
  voices=[render(attenuation_stem([r['ports'] for r in rows],v),DLL) for v in range(4)]
  refvoices=[mono(old/f'reference-voice{v}.wav') for v in range(4)]
  metrics=comparison_metrics(ref,pcm,refvoices,voices);metrics['pitch']=pitch_report([r['ports'] for r in rows],voices)
  folder=OUT/'cases'/name;folder.mkdir(parents=True,exist_ok=True);wav(folder/'candidate.wav',pcm)
  for v in range(4):wav(folder/f'voice{v}.wav',voices[v])
  save(folder/'private-state.json',dict(candidate_rows=rows,emission_failures=emission,state_failures=state))
  results[name]=dict(ticks=len(rows),emission='PASS',emission_failures=emission,core_register_counter_LFSR_failures=state,
   versus_A0_735=diff(pcm,a0),versus_original_MAME_2048=diff(pcm,ref),callback_aligned_vs_original=diff(aligned,ref),
   new_callback_partition_invariance=bool(np.array_equal(pcm,aligned)),fresh_instance_determinism=bool(np.array_equal(pcm,fresh)),metrics=metrics,candidate_seconds=elapsed,
   fidelity='NEW residuals retained; A0 matched-callback byte identity NOT preserved')
  for p in [old/'reference.wav',old/'candidate.wav',old/'private-state.json']:inputhash[str(p.relative_to(ROOT.parent))]=sha(p)
  print(name,'emission/state PASS','vsA0',results[name]['versus_A0_735']['max_error_lsb'],'vsMAME',results[name]['versus_original_MAME_2048']['max_error_lsb'],flush=True)
 # Native contract checks independent of ROM data.
 with PSG(DLL) as p:
  p.write([0xC4,0x01,0xD0,0xE7,0xF2]);p.render();snapshot=p.state();pause=p.state()==snapshot
  p.write([0x9F,0xBF,0xDF,0xFF]);p.render();before=p.state();silent=p.render();off=dict(samples_nonzero=int(np.count_nonzero(silent)),state_continues=before[:22]!=p.state()[:22])
  p.lib.a1_volumes.argtypes=[C.c_void_p,C.c_void_p];table=(C.c_int*16)();p.lib.a1_volumes(p.ptr,table)
  expected=[int(8192*2**(-i/3)+.5) for i in range(15)]+[0];assert list(table)==expected
  sizes=dict(state_bytes=p.lib.a0_state_bytes(),scratch_bytes=p.lib.a0_buffer_bytes(p.ptr))
 a,b=candidate(bank,CASES['coupled-steal-recover'],DLL),candidate(bank,CASES['coupled-steal-recover'],DLL,split=True)
 segmentation=diff(a[0],b[0])
 newnoise=mono(OUT/'cases/coupled-steal-recover/voice3.wav')[33*735:48*735];oldnoise=mono(A0/'cases/coupled-steal-recover/reference-voice3.wav')[33*735:48*735]
 fadenew=mono(OUT/'cases/finite-fade/voice3.wav')[39*735:47*735];fadeold=mono(A0/'cases/finite-fade/reference-voice3.wav')[39*735:47*735]
 imports=pe_imports(DLL);assert imports=={'KERNEL32.dll':['GetProcessHeap','HeapAlloc','HeapFree']}
 save(PUB/'comparisons.json',dict(parent='549de7543b6704cf9d219d5c87f5a03bf854ec9e',cases=results,total_ticks=sum(c['ticks'] for c in results.values()),
  elapsed_seconds=time.perf_counter()-t,build=load(OUT/'build.json'),binary_imports=imports,volume_table_equal=True,
  memory=sizes,pause_no_advance=pause,off=off,segmentation=segmentation,history_resumption=diff(newnoise,oldnoise),
  finite_fade_held=dict(reference_nonzero_samples=int(np.count_nonzero(fadeold)),candidate_nonzero_samples=int(np.count_nonzero(fadenew)),error=diff(fadenew,fadeold)),
  reference_inputs=inputhash,intrinsic_bank_sha256=sha(bankpath),A0_archive_sha256=sha(parent),new_original_reference_renders=0,thresholds_relaxed=False,
  verdict='HOLD for Manager fidelity decision: dependency-reduced source strategy demonstrated; exact A0 resampler parity lost',native_GameMaker='NOT RUN'))
if __name__=='__main__':run()
