"""Reload each new finite SCSP record in a fresh process forbidding oracle access."""
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2')]
from m5a2c5.proof import OUT,PUB,save,sha
from m5a2c5.proof import CASES


def run():
    guard=r'''
import importlib.abc,runpy,sys
class NoOracle(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.split('.')[0] in {'z80','audio1_psg_trace','m5p0r_probe','audio1b_render'}:
   raise RuntimeError('oracle import forbidden')
sys.meta_path.insert(0,NoOracle())
def audit(event,args):
 if event=='open' and any(s in str(args[0]).lower() for s in ('.sms','.vgm','dry-event-bank','dry-emission-bank','terminal-diagnostic')):
  raise RuntimeError('original input forbidden')
sys.addaudithook(audit)
sys.argv=sys.argv[1:];runpy.run_path(sys.argv[0],run_name='__main__')
assert 'z80' not in sys.modules
'''
    dll=ROOT.parent/'sonic-chaos-reference-m5-a1l/build/m5-a1l/psg-a1l.dll'
    result={};folder=OUT/'isolated';folder.mkdir(parents=True,exist_ok=True)
    for name in CASES:
        output=folder/(name+'.wav')
        args=[sys.executable,'-c',guard,str(ROOT/'tools/m5a2c2/runtime.py'),str(OUT/'programs.scsp'),
              str(OUT/'pcm'/name/'schedule.json'),str(dll),str(output)]
        r=subprocess.run(args,capture_output=True,text=True)
        if r.returncode:raise RuntimeError(r.stderr)
        assert output.read_bytes()==(OUT/'pcm'/name/'candidate.wav').read_bytes()
        result[name]=dict(fresh_process=True,ROM_and_oracle_access_forbidden=True,
            PCM_identical=True,WAV_sha256=sha(output.read_bytes()))
    save(PUB/'isolation.json',dict(cases=result,SCSP_version=1,previous_records_compatible=True))
    print(f'{len(result)} fresh-process ROM-free SFX solo/interaction replays PASS')


if __name__=='__main__':run()
