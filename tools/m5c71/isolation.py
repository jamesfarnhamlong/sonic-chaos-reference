"""Fresh-process private-bank playback with original input/import rejection."""
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from m5c71.research import OUT,PUB,CASES,load,save,sha,schedule

GUARD=r'''
import importlib.abc,runpy,sys
class NoOracle(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.split('.')[0] in {'z80','audio1_psg_trace','m5p0r_probe','audio1b_render','m5c71'}:
   raise RuntimeError('oracle import forbidden')
sys.meta_path.insert(0,NoOracle())
def audit(event,args):
 if event=='open' and any(s in str(args[0]).lower() for s in ('.sms','.vgm','-original.json','-original-a1l.wav','-candidate.json','boundaries.json')):
  raise RuntimeError('oracle input forbidden')
sys.addaudithook(audit)
for attempt in (lambda:__import__('z80'),lambda:open('forbidden.sms'),lambda:open('forbidden-original.json')):
 try:attempt()
 except RuntimeError:pass
 else:raise AssertionError('access guard failed')
sys.argv=sys.argv[1:];runpy.run_path(sys.argv[0],run_name='__main__')
assert 'z80' not in sys.modules
'''

def run():
    folder=OUT/'isolated';folder.mkdir(parents=True,exist_ok=True);result={}
    dll=ROOT.parent/'sonic-chaos-reference-m5-a1l/build/m5-a1l/psg-a1l.dll'
    for name,c in load(PUB/'emission.json')['cases'].items():
        assert c['failure_count']==0
        sch=schedule(CASES[name]);sch['ticks']=c['ticks'];sp=folder/(name+'-schedule.json');save(sp,sch)
        output=folder/(name+'.wav')
        r=subprocess.run([sys.executable,'-c',GUARD,str(ROOT/'tools/m5a2c2/runtime.py'),str(OUT/'programs.scsp'),str(sp),str(dll),str(output)],capture_output=True,text=True)
        if r.returncode:raise RuntimeError(r.stderr)
        assert output.read_bytes()==(OUT/(name+'-candidate.wav')).read_bytes()
        result[name]=dict(ticks=c['ticks'],fresh_process=True,three_access_guard_probes_pass=True,PCM_identical=True,WAV_sha256=sha(output.read_bytes()))
    save(PUB/'isolation.json',dict(cases=result,complete_song_eligibility=False,partial_windows_only=True))
    print(len(result),'fresh-process replays PASS')

if __name__=='__main__':run()
