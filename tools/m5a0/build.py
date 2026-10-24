"""Build only an integration adapter and the pinned PSG/resampler/logging files."""
import argparse,hashlib,json,subprocess,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--cc',type=Path,required=True);a=p.parse_args()
s=a.source.resolve();out=ROOT/'build/m5-a0';out.mkdir(parents=True,exist_ok=True)
pin=subprocess.check_output(['git','rev-parse','HEAD'],cwd=s,text=True).strip()
assert pin=='a6eed945ecf4e5a25cf82004779c6f7e4fd5c319'
paths=[ROOT/'tools/m5a0/psg_adapter.c',s/'emu/cores/sn76496.c',s/'emu/Resampler.c',s/'emu/logging.c']
cmd=[str(a.cc.resolve()),'cc','-shared','-O2','-I',str(s),str(paths[0]),str(paths[2]),str(paths[3]),'-o',str(out/'psg-a0.dll')]
env=dict(os.environ,ZIG_GLOBAL_CACHE_DIR=str(out/'zig-cache'),ZIG_LOCAL_CACHE_DIR=str(out/'zig-local'),TEMP=str(out),TMP=str(out))
subprocess.run(cmd,check=True,env=env)
h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
(out/'build.json').write_text(json.dumps(dict(core_commit=pin,command=cmd,inputs={str(f):h(f) for f in paths},binary_sha256=h(out/'psg-a0.dll')),indent=2)+'\n')
print('built',out/'psg-a0.dll')
