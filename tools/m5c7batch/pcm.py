"""Exact same-A1L PCM, all26 before/after fields, partitioning and isolated replay."""
import sys
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2'),str(ROOT/'tools/m5a0')]
import numpy as np
from backend import PSG
from m5c7batch.proof import OUT,PUB,load,save,sha
from m5c7batch.runtime import render,wav,unpack
from m5c71r83.pcm import GUARD,DLL

def run():
    assert sha(DLL.read_bytes())=='47e15c47e255900b819847e0ddefd7e3f0751dcc8f75dff3a1690f7e76adcf65'
    folder=OUT/'pcm';folder.mkdir(parents=True,exist_ok=True)
    for receipt in sorted(PUB.glob('emission-*.json')):
        if len(sys.argv)>1 and receipt.name not in sys.argv[1:]:continue
        emission=load(receipt);bankpath=OUT/emission['bank'];bank=unpack(bankpath.read_bytes());results={}
        for name,c in emission['cases'].items():
            assert not c['failure_count']
            schedule=load(OUT/(name+'-candidate.json'))['schedule'];schedule['ticks']=c['ticks']
            audio,states=render(bank,schedule,DLL);split,splitstates=render(bank,schedule,DLL,True)
            original=load(OUT/(name+'-original.json'));blocks=[];refstates=[]
            with PSG(DLL) as chip:
                for row in original['rows'][:c['ticks']]:
                    chip.write(row['ports']);before=chip.state();blocks.append(chip.render());refstates.append([before,chip.state()])
            ref=np.concatenate(blocks);bad=int(np.count_nonzero(audio!=ref));statebad=sum(a!=b for a,b in zip(states,refstates))
            wav(folder/(name+'-candidate.wav'),audio);wav(folder/(name+'-reference.wav'),ref)
            save(folder/(name+'-schedule.json'),schedule)
            isolated=folder/(name+'-isolated.wav')
            proc=subprocess.run([sys.executable,'-c',GUARD,str(ROOT/'tools/m5c7batch/runtime.py'),str(bankpath),str(folder/(name+'-schedule.json')),str(DLL),str(isolated)],capture_output=True,text=True)
            if proc.returncode:raise RuntimeError(proc.stderr)
            isolation=isolated.read_bytes()==(folder/(name+'-candidate.wav')).read_bytes()
            r=dict(ticks=c['ticks'],samples=len(audio),PCM_mismatches=bad,native_before_after_state_mismatching_ticks=statebad,partition_exact=np.array_equal(audio,split) and states==splitstates,isolated_process_exact=isolation,three_access_guards_tested=True,PCM_sha256=sha(audio.tobytes()),original_PCM_sha256=sha(ref.tobytes()))
            assert not bad and not statebad and r['partition_exact'] and isolation
            r['status']='PASS';results[name]=r
            print(name,'PCM PASS',len(audio),flush=True)
        save(PUB/receipt.name.replace('emission-','pcm-'),dict(cases=results,SCSP_sha256=sha(bankpath.read_bytes()),A1L_sha256=sha(DLL.read_bytes()),clock=3546893,rate=44100,tick_samples=735,native_fields_per_before_and_after=26,chip_resets_at_loop=0,scope='matched prefixes only for HOLD cases; exact same A1L, no hardware/MAME claim'))

if __name__=='__main__':run()
