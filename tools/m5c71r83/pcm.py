"""Exact continuous same-A1L original comparison and independent-process replay."""
import sys
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2'),str(ROOT/'tools/m5a0')]
import numpy as np
from backend import PSG
from m5c71r83.proof import CASES,OUT,PUB,load,save,sha
from m5c71r83.contract import unpack
from m5c71r83.runtime import render,wav
GUARD=r'''
import importlib.abc,runpy,sys
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,name,path=None,target=None):
  if name.split('.')[0] in {'z80','audio1_psg_trace','audio1b_render','m5p0r_probe','m5c71'} or name.endswith('.proof'):
   raise RuntimeError('original import forbidden')
sys.meta_path.insert(0,Block())
def audit(event,args):
 if event=='open' and any(s in str(args[0]).lower() for s in ('.sms','.vgm','-original.json','-candidate.json','records.json','-reference.wav')):
  raise RuntimeError('original capture forbidden')
sys.addaudithook(audit)
for fn in (lambda:__import__('z80'),lambda:open('forbidden.sms'),lambda:open('forbidden-original.json')):
 try:fn()
 except RuntimeError:pass
 else:raise AssertionError('guard failed')
sys.argv=sys.argv[1:];runpy.run_path(sys.argv[0],run_name='__main__')
assert 'z80' not in sys.modules
'''
DLL=ROOT.parent/'sonic-chaos-reference-m5-a1l/build/m5-a1l/psg-a1l.dll'

def run():
    assert sha(DLL.read_bytes())=='47e15c47e255900b819847e0ddefd7e3f0751dcc8f75dff3a1690f7e76adcf65'
    bank=unpack((OUT/'programs.scsp').read_bytes());result={};folder=OUT/'pcm';folder.mkdir(parents=True,exist_ok=True)
    for name,(rid,events,ticks) in CASES.items():
        schedule=dict(initial=rid,events={str(k):v for k,v in events.items()},ticks=ticks,renew83=ticks>4200)
        audio,states=render(bank,schedule,DLL);split,splitstates=render(bank,schedule,DLL,split=True)
        original=load(OUT/(name+'-original.json'));blocks=[];refstates=[]
        with PSG(DLL) as chip:
            for row in original['rows']:
                chip.write(row['ports']);before=chip.state();blocks.append(chip.render());refstates.append([before,chip.state()])
        ref=np.concatenate(blocks);bad=int(np.count_nonzero(audio!=ref));statebad=sum(a!=b for a,b in zip(states,refstates))
        wav(folder/(name+'-candidate.wav'),audio);wav(folder/(name+'-reference.wav'),ref)
        save(folder/(name+'-native.json'),dict(candidate=states,original=refstates));save(folder/(name+'-schedule.json'),schedule)
        isolated=folder/(name+'-isolated.wav')
        process=subprocess.run([sys.executable,'-c',GUARD,str(ROOT/'tools/m5c71r83/runtime.py'),str(OUT/'programs.scsp'),str(folder/(name+'-schedule.json')),str(DLL),str(isolated)],capture_output=True,text=True)
        if process.returncode:raise RuntimeError(process.stderr)
        isolation=isolated.read_bytes()==(folder/(name+'-candidate.wav')).read_bytes()
        result[name]=dict(ticks=ticks,samples=len(audio),PCM_mismatches=bad,native_before_after_state_mismatching_ticks=statebad,partition_exact=np.array_equal(audio,split) and states==splitstates,
            PCM_sha256=sha(audio.tobytes()),original_PCM_sha256=sha(ref.tobytes()),isolated_process_exact=isolation,three_access_guards_tested=True,status='PASS' if not bad and not statebad and np.array_equal(audio,split) and states==splitstates and isolation else 'FAIL')
        print(name,result[name],flush=True)
        assert result[name]['status']=='PASS'
    save(PUB/'pcm.json',dict(cases=result,A1L_sha256=sha(DLL.read_bytes()),rate=44100,clock=3546893,tick_samples=735,
        same_A1L_exact=True,MAME_or_hardware_identity_claim=False,native_fields_per_before_and_after=26,chip_resets_at_loop=0))

if __name__=='__main__':run()
