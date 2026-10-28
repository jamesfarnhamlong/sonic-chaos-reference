"""ROM/oracle-free batch runtime. Uses the unchanged C6 decoder and persistent A1L."""
import argparse
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2'),str(ROOT/'tools/m5a0')]
import numpy as np
from backend import PSG
from m5a2.bank import unpack
from m5a2c2.decoder import Decoder
from m5a2.runtime import wav

def render(bank,schedule,dll,split=False):
    from m5c7batch.alias92 import Decoder as Alias
    from m5c7batch.renewal import Decoder as Renewing
    cls=Renewing if schedule.get('renew') else Alias if schedule['initial']==0x92 else Decoder
    m=cls(bank);m.direct(schedule['initial']);blocks=[];states=[]
    with PSG(dll) as chip:
        for t in range(1,schedule['ticks']+1):
            for kind,value in schedule.get('events',{}).get(str(t),[]):
                if kind=='request':m.direct(value)
                elif kind=='fade':m.fade=list(value)
                else:raise ValueError('unsupported action')
            m.tick();chip.write(m.writes);before=chip.state()
            blocks.append(np.concatenate([chip.render(100),chip.render(635)]) if split else chip.render())
            states.append([before,chip.state()])
    return np.concatenate(blocks),states

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ('bank','schedule','dll','out'):p.add_argument(k)
    a=p.parse_args();audio,states=render(unpack(Path(a.bank).read_bytes()),json.loads(Path(a.schedule).read_text()),a.dll)
    wav(a.out,audio)
