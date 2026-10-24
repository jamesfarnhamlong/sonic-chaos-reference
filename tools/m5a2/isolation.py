"""Fresh process candidate playback with oracle/ROM access explicitly forbidden."""
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from m5a2.proof import OUT,PUB,save,sha


def run():
    output=OUT/'isolated-candidate.wav'
    dll=ROOT.parent/'sonic-chaos-reference-m5-a1l/build/m5-a1l/psg-a1l.dll'
    script=r'''
import importlib.abc,runpy,sys
class NoOracle(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.split('.')[0] in {'z80','audio1_psg_trace','m5p0r_probe','audio1b_render'}:
   raise RuntimeError('oracle import forbidden: '+fullname)
sys.meta_path.insert(0,NoOracle())
def audit(event,args):
 if event=='open':
  p=str(args[0]).lower()
  if any(x in p for x in ('.sms','.vgm','dry-emission-bank','dry-event-bank','private-state','first-failure')):
   raise RuntimeError('reference input forbidden: '+p)
sys.addaudithook(audit)
sys.argv=sys.argv[1:]
runpy.run_path(sys.argv[0],run_name='__main__')
assert 'z80' not in sys.modules
'''
    args=[sys.executable,'-c',script,str(ROOT/'tools/m5a2/runtime.py'),str(OUT/'programs.scsp'),
          str(OUT/'pcm/THZ-loop/schedule.json'),str(dll),str(output)]
    result=subprocess.run(args,capture_output=True,text=True)
    if result.returncode:raise RuntimeError(result.stderr)
    expected=OUT/'pcm/THZ-loop/candidate.wav'
    assert output.read_bytes()==expected.read_bytes()
    save(PUB/'isolation.json',dict(fresh_process=True,case='THZ-loop',ticks=4200,
         forbidden_original_imports_and_inputs=True,PCM_file_identical=True,
         candidate_wav_sha256=sha(output.read_bytes()),ROM_reopened=False,
         runtime_inputs=['SCSP private data','host request schedule','unchanged accepted A1L backend']))
    print('ROM-free isolated 4200-tick decoder and synthesis PASS')


if __name__=='__main__':run()
