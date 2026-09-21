"""Apply the source overlay to a new copy of the original disassembly and verify its build."""
import argparse, hashlib, json, shutil, subprocess
from pathlib import Path

from export_data import EXPECTED_SHA256

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',help='Original extracted Sonic Chaos disassembly directory')
p.add_argument('--output',default='research-build',help='New directory; must not exist')
p.add_argument('--wla-z80',default='wla-z80')
p.add_argument('--wlalink',default='wlalink')
a=p.parse_args()
source=Path(a.source).resolve();output=Path(a.output).resolve()
original=(source/'SonicChaos.sms').read_bytes()
assert hashlib.sha256(original).hexdigest()==EXPECTED_SHA256,'Unexpected source ROM revision'
if output.exists(): raise SystemExit('Output already exists; select a new directory.')
if source==output or source in output.parents:
    raise SystemExit('Choose an output directory outside the source tree.')
# Keep the original inputs intact; copy into a separate build tree.
shutil.copytree(source,output)
shutil.copytree(Path(__file__).resolve().parent/'overlay',output,dirs_exist_ok=True)
subprocess.run([a.wla_z80,'-o','SonicC.o','SonicChaos.asm'],cwd=output,check=True)
subprocess.run([a.wlalink,'-r','-s','Link.txt','SCresearch.sms'],cwd=output,check=True)
built=(output/'SCresearch.sms').read_bytes()
if built!=original:
    mismatch=next((i for i,(x,y) in enumerate(zip(original,built)) if x!=y),min(len(original),len(built)))
    raise SystemExit(f'Build differs at file offset ${mismatch:05X}, lengths {len(original)}/{len(built)}')
result=dict(byte_identical=True,bytes_compared=len(original),sha256=hashlib.sha256(built).hexdigest())
(output/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
