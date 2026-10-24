"""Create one bounded local A1L review package; no rendering or external transfer."""
import hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from m5p1c import preservation
OUT=ROOT/'build/m5-a1l';PUB=ROOT/'data/m5-a1l'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
prior=preservation()
for path,expected in [('sonic-chaos-reference-m5-p1c/build/SonicChaos_M5_P1C_20261024_PROOF_PRIVATE.zip','fbd5264b6c07ed9bb04d63350a7c9e8a0b854a19208012f92adc4d96f9a9984c'),('sonic-chaos-reference-m5-a0/build/SonicChaos_M5_A0_20261024_STATEFUL_PRIVATE.zip','580725052986dcf5b79718fd2dd1ebfe93f09ed5ba0b9db879cea53c8343f004')]:
 p=ROOT.parent/path;assert sha(p)==expected;prior['private_archives'].append(dict(name=p.name,sha256=expected,unchanged=True))
comparisons=json.loads((PUB/'comparisons.json').read_text());assert sha(OUT/'psg-a1l.dll')==comparisons['build']['binary_sha256']
files=list((OUT/'cases').rglob('*.wav'))+list((OUT/'cases').rglob('*.json'))
files += [OUT/n for n in ['psg-a1l.dll','psg-a1l.pdb','retained_psg.c','adapter.obj','support.obj','adapter.d','support.d','build.json','link-trace.txt']]
files += [p for p in PUB.glob('*.json') if p.name not in ['verification.json','private-package.json']]
files += [ROOT/'docs/m5-a1l-THIRD-PARTY-NOTICES.md',ROOT/'tools/m5a1l/LICENSE-MIT.txt']
size=sum(p.stat().st_size for p in files);assert size<256*1024**2
archive=ROOT/'build/SonicChaos_M5_A1L_20261024_HELPER_EXPERIMENT_PRIVATE.zip';manifest={}
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in files:
  name=p.relative_to(OUT).as_posix() if p.is_relative_to(OUT) else 'metadata/'+p.name
  assert name not in manifest;manifest[name]=dict(bytes=p.stat().st_size,sha256=sha(p));z.write(p,name)
 z.writestr('manifest.json',json.dumps(dict(files=manifest,prior_preservation=prior),indent=2)+'\n')
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for n,e in manifest.items():assert hashlib.sha256(z.read(n)).hexdigest()==e['sha256']
receipt=dict(name=archive.name,sha256=sha(archive),bytes=archive.stat().st_size,members=len(manifest)+1,payload_bytes=size,crc_and_member_hashes='PASS',prior_preservation=prior,contains_ROM=False,contains_original_Z80_binary=False,private_review_only=True,production_fidelity='HOLD')
(PUB/'private-package.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items() if k!='prior_preservation'},indent=2))
