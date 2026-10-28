"""Verify final gated runtime (not diagnostic traversal), continuous A1L and isolation."""
import hashlib
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2'),str(ROOT/'tools/m5a0')]
import numpy as np
from backend import PSG
from m5c9.proof import OUT,PUB,IDS,rows,save,load,sha,canonical
from m5c9.runtime import Decoder,unpack,state
from m5c71r83.pcm import DLL
GUARD=r'''
import importlib.abc,runpy,sys
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,name,path=None,target=None):
  if name.split('.')[0] in {'z80','audio1_psg_trace','audio1b_render','m5p0r_probe','m5c71'} or name.endswith(('.proof','.original','.verify')):
   raise RuntimeError('original import forbidden')
sys.meta_path.insert(0,Block())
def audit(event,args):
 if event=='open' and any(s in str(args[0]).lower() for s in ('.sms','.vgm','-original.','-notes.','-records.','-contract.')):
  raise RuntimeError('original capture forbidden')
sys.addaudithook(audit)
for fn in (lambda:__import__('z80'),lambda:open('forbidden.sms'),lambda:open('forbidden-original.jsonl.gz')):
 try:fn()
 except RuntimeError:pass
 else:raise AssertionError('guard failed')
sys.argv=sys.argv[1:];runpy.run_path(sys.argv[0],run_name='__main__')
assert 'z80' not in sys.modules
'''

def verify(name,rid,bankname,events=None):
    original=load(PUB/(name+'.json'));bankpath=OUT/bankname;bank=unpack(bankpath.read_bytes());m=Decoder(bank);m.direct(rid)
    pcm=hashlib.sha256();refpcm=hashlib.sha256();native=hashlib.sha256();emission=hashlib.sha256();captured=hashlib.sha256();samplebad=statebad=partitionbad=0;bad=[];count=0;edges=0;complete_at=None;events=events or {}
    with PSG(DLL) as chip,PSG(DLL) as ref,PSG(DLL) as split:
        for t,o in enumerate(rows(name),1):
            for kind,v in events.get(t,[]):
                if kind=='request':m.direct(v)
                elif kind=='fade':m.fade=list(v)
                else:raise ValueError('unsupported action')
            m.tick();r=state(m)
            for k,v in o['row'].items():
                if canonical(r[k])!=canonical(v):bad.append(dict(tick=t,field=k))
            actual=[[t,i,q] for tick,i,p,q in m.loops if tick==t]
            if actual!=o['transfers']:bad.append(dict(tick=t,field='transfers'))
            edges+=len(actual);captured.update(canonical(o)+b'\n');emission.update(canonical(r))
            chip.write(r['ports']);ref.write(o['row']['ports']);split.write(r['ports'])
            before=chip.state();refbefore=ref.state();splitbefore=split.state()
            a=chip.render();b=ref.render();c=np.concatenate([split.render(100),split.render(635)])
            samplebad+=int(np.count_nonzero(a!=b));statebad+=before!=refbefore or chip.state()!=ref.state()
            partitionbad+=not np.array_equal(a,c) or before!=splitbefore or chip.state()!=split.state()
            pcm.update(a.tobytes());refpcm.update(b.tobytes());native.update(canonical([before,chip.state()]));count=t
            if m.completed and complete_at is None:complete_at=t
    assert captured.hexdigest()==original['original_capture_sha256']
    assert not bad and not samplebad and not statebad and not partitionbad,(name,bad[:4],samplebad,statebad,partitionbad)
    schedule=dict(initial=rid,ticks=count,events={str(k):v for k,v in events.items()});save(OUT/(name+'-schedule.json'),schedule)
    output=OUT/(name+'-isolated-receipt.json')
    cmd=[sys.executable,'-c',GUARD,str(ROOT/'tools/m5c9/runtime.py'),str(bankpath),str(OUT/(name+'-schedule.json')),str(DLL),str(output)]
    proc=subprocess.run(cmd,capture_output=True,text=True)
    if proc.returncode:raise RuntimeError(proc.stderr)
    isolated=load(output)
    expected=dict(ticks=count,samples=count*735,PCM_sha256=pcm.hexdigest(),native_sha256=native.hexdigest(),state_PSG_sha256=emission.hexdigest(),renewals=m.renewals,extensions=m.extensions,completed=m.completed)
    assert isolated==expected
    result=dict(expected,status='PASS',sample_mismatches=samplebad,native_before_after_mismatching_ticks=statebad,partition_mismatching_ticks=partitionbad,state_PSG_transfer_mismatches=len(bad),original_PCM_sha256=refpcm.hexdigest(),original_capture_sha256=captured.hexdigest(),isolated_process_exact=True,access_guards_tested=3,transfer_edges=edges,finite_completed_at=complete_at,SCSP_sha256=sha(bankpath.read_bytes()),A1L_sha256=sha(DLL.read_bytes()),native_fields=26,chip_resets_at_windows_or_loops=0)
    save(PUB/(name+'-verified.json'),result);print(name,'gated state/PSG/PCM/isolation PASS',count,flush=True)

def main():
    assert sha(DLL.read_bytes())=='47e15c47e255900b819847e0ddefd7e3f0751dcc8f75dff3a1690f7e76adcf65'
    for rid in IDS:verify(f'{rid:02X}-solo',rid,f'{rid:02X}.scsp')

if __name__=='__main__':main()
