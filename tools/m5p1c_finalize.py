"""Read-only final diagnostics and private packaging; never renders."""
import hashlib,json,wave,zipfile,shutil
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'build/m5-p1c'; PUBLIC=ROOT/'data/m5-p1c'
def load(p):return json.loads(p.read_text())
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pcm(p):
 with wave.open(str(p)) as w:
  assert (w.getnchannels(),w.getsampwidth(),w.getframerate())==(1,2,44100)
  return np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)
def segment(a,b,start,end):
 a=a[(start-1)*735:end*735];b=b[(start-1)*735:end*735]
 return dict(first_tick=start,last_tick=end,samples=len(a),correlation=float(np.corrcoef(a,b)[0,1]),rms_reference=float(np.sqrt(np.mean(a*a))),rms_candidate=float(np.sqrt(np.mean(b*b))),max_error_lsb=float(np.max(abs(a-b))),sign_disagreement_fraction=float(np.mean(np.sign(a)!=np.sign(b))))
def main():
 report=load(PUBLIC/'pcm-feasibility.json');a=pcm(OUT/'references/coupled-steal-recover/voice3.wav');b=pcm(OUT/'candidate/coupled-steal-recover/voice3.wav')
 segments={name:segment(a,b,s,e) for name,s,e in [('matched_entry',1,5),('resumed_noise',34,48)]}
 gate=load(OUT/'finite-fade-gate.json')['rows']; selection=load(OUT/'candidate/finite-fade/private-selection.json')
 budget=dict(renderer_processes=report['new_process_count'],renderer_process_seconds=sum(x['seconds'] for x in report['process_calls']),rendered_tick_sum=sum(x['ticks'] for x in report['process_calls']),max_new_target_ticks=report['all_targets_at_most_ticks'],scratch_bytes=sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()),free_bytes=shutil.disk_usage(OUT).free,peak_working_memory='NOT MEASURED: short-lived renderer processes were not sampled; no runtime memory acceptance')
 detail=dict(coupled_segments=segments,hidden_clock_ticks=report['cases']['coupled-steal-recover']['compatibility']['hidden_noise_clock_differences'],finite_fade=dict(first_unsupported_tick=selection['unsupported_sources'][0]['tick'],unsupported_voice_ticks=len(selection['unsupported_sources']),audible_clock_mismatches=len(selection['audible_clock_differences']),original_tick40_physical_registers=gate[39]['original']['registers'],reason='fade cancels source stream while physical noise continues; baked music tone period also differs'),budget=budget,rendering_stopped=True,thresholds_relaxed=False)
 save(PUBLIC/'diagnostics.json',detail)
 # Standalone review package: new fixture data + bounded reused corrections, excluding caches/ROM/tools.
 package=OUT/'review-package';package.mkdir(exist_ok=True)
 for folder in ['references','candidate']:
  shutil.copytree(OUT/folder,package/folder,dirs_exist_ok=True)
 for p in OUT.glob('*-gate.json'):shutil.copy2(p,package/p.name)
 shutil.copy2(OUT/'dry-emission-bank.json',package/'private-dry-emission-bank.json')
 for call in report['process_calls']:
  if call['label'] in ['A3-finite-carrier','B7-finite-carrier']:
   target=package/'carriers'/(call['label']+'.wav');target.parent.mkdir(exist_ok=True)
   shutil.copy2(OUT/'render-cache'/(call['key']+'.wav'),target)
 for p in OUT.glob('*carrier*.wav'):shutil.copy2(p,package/p.name)
 # Carrier files are kept at the paths specified by the renderer implementation.
 for p in OUT.rglob('*.wav'):
  if 'carrier' in p.name.lower() and 'render-cache' not in p.parts and 'review-package' not in p.parts:
   target=package/'carriers'/p.name;target.parent.mkdir(exist_ok=True);shutil.copy2(p,target)
 old=ROOT.parent/'sonic-chaos-reference-m5-p0r/build/m5-p0r'
 for name in ['B8-carrier-diagnostic.wav','B8-BC-carrier-composed.wav','B6-A0-context-composed.wav','BA-partial-context-composed.wav']:
  target=package/'reused'/name;target.parent.mkdir(exist_ok=True);shutil.copy2(old/'pcm'/name,target)
 prior=ROOT.parent/'sonic-chaos-reference-m5-proof/build/m5-proof/package/scenarios'
 for case in ['fixed-B8-BC','B6-A0','BA-partial']:
  for p in (prior/case).glob('continuous*.wav'):
   target=package/'reused'/case/p.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
 for name in ['verification.json','private-package-receipt.json']:
  stale=package/name
  if stale.exists():stale.unlink()  # External receipts are finalized after packaging.
 for p in PUBLIC.glob('*.json'):
  if p.name not in ['private-package-receipt.json','verification.json']:shutil.copy2(p,package/p.name)
 files=[p for p in package.rglob('*') if p.is_file() and p.name!='manifest.json']
 manifest={p.relative_to(package).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p)) for p in files};save(package/'manifest.json',dict(files=manifest,rom_sha256=report['rom_sha256'],renderer_sha256=report['renderer_sha256']))
 archive=ROOT/'build/SonicChaos_M5_P1C_20261024_PROOF_PRIVATE.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
  for p in package.rglob('*'):
   if p.is_file():z.write(p,p.relative_to(package).as_posix())
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None
  for name,entry in manifest.items():assert hashlib.sha256(z.read(name)).hexdigest()==entry['sha256']
 assert archive.stat().st_size<128*1024**2
 save(PUBLIC/'private-package-receipt.json',dict(name=archive.name,sha256=sha(archive),bytes=archive.stat().st_size,members=len(manifest)+1,crc_and_member_hashes='PASS',payload_bytes=sum(x['bytes'] for x in manifest.values()),manifest_sha256=sha(package/'manifest.json'),prior_archives_immutable=report['preservation_after']))
 print(json.dumps(detail,indent=2));print('PRIVATE PACKAGE',archive,sha(archive))
if __name__=='__main__':main()
