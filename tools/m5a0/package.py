"""Package only bounded private proof files; never publishes them or renders audio."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'build/m5-a0';PUB=ROOT/'data/m5-a0'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
report=json.loads((PUB/'results.json').read_text())
files=list((OUT/'cases').rglob('*.wav'))+list((OUT/'cases').rglob('*.json'))+[OUT/'private-dry-emission-bank.json',OUT/'psg-a0.dll',OUT/'build.json']
files+=list(PUB.glob('*.json'));files=[p for p in files if p.name not in ['private-package.json','verification.json']]
size=sum(p.stat().st_size for p in files);assert size<512*1024**2
archive=ROOT/'build/SonicChaos_M5_A0_20261024_STATEFUL_PRIVATE.zip'
manifest={}
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in files:
  name=p.relative_to(OUT).as_posix() if p.is_relative_to(OUT) else 'safe-metadata/'+p.name
  assert name not in manifest
  manifest[name]=dict(bytes=p.stat().st_size,sha256=sha(p));z.write(p,name)
 z.writestr('manifest.json',json.dumps(dict(files=manifest,original_ROM_included=False,redistribution_clearance=False),indent=2)+'\n')
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for n,m in manifest.items():assert hashlib.sha256(z.read(n)).hexdigest()==m['sha256']
receipt=dict(name=archive.name,sha256=sha(archive),bytes=archive.stat().st_size,members=len(manifest)+1,payload_bytes=size,crc_and_member_hashes='PASS',contains_original_ROM=False,contains_original_Z80_binary=False,contains_private_audio=True,redistribution_clearance=False,reason='local Manager review proof only; helper licensing unresolved',source_parent=report['parent'])
(PUB/'private-package.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
