"""ROM/oracle-free C9 checkpoint capabilities over the unchanged4200 engine.

Only an exact bank, initial solo request and authenticated complete state may
advance to another window. Recurrence returns proof position, never PSG state.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2'),str(ROOT/'tools/m5a0')]
from m5c9.contract import Decoder as Bounded,unpack,sha,canonical,DecodeError

def state(m):
    r=m.snapshot();r.update(channel_bytes=[list(c) for c in m.ch],shared_IY=m.iy,globals=[*m.tempo,m.selected,*m.mail,*m.fade,m.last_sfx,m.noise_offset,m.fade_noise_volume]);return r
def fingerprint(m):return sha(canonical({k:v for k,v in state(m).items() if k!='ports'}))

class Decoder(Bounded):
    def __init__(self,bank,horizon=None):
        if horizon not in (None,4200):raise DecodeError('C9 requires unchanged4200 engine window')
        self.cert=None;self.requests=0;self.eligible=False;self.position=0;self.absolute=0;self.renewals=0;self.extensions=0;self.completed=False
        super().__init__(bank,horizon)
        self.cert=json.loads((ROOT/'data/m5-c9/capabilities.json').read_text()).get(f'{self.rid:02X}')
        if self.cert is None or sha(canonical(bank))!=self.cert['bank_canonical_sha256']:raise DecodeError('C9 continuation bank not authenticated')
    def direct(self,rid,slot=0):
        self.requests+=1;self.eligible=self.requests==1 and rid==self.rid and slot==0
        return super().direct(rid,slot)
    def tick(self):
        if self.absolute and (any(self.mail) or any(self.fade)):self.eligible=False
        # Revoked capabilities never gain time from a previously renewed window.
        if not self.eligible and self.absolute>=4200:raise DecodeError('C9 continuation revoked; ordinary4200 exhausted')
        rec=self.cert['recurrence'];release=self.cert['finite_release_tick']
        if self.eligible and rec and self.position==rec['repeat_tick']:
            if fingerprint(self)!=self.cert['repeat_fingerprint']:raise DecodeError('C9 recurrence state mismatch')
            self.position=rec['first_tick'];self.renewals+=1
        if self.eligible and self.position and self.position%4200==0:
            expected=self.cert['checkpoints'].get(str(self.position))
            if expected is None or fingerprint(self)!=expected:raise DecodeError('C9 coverage checkpoint state mismatch')
            self.extensions+=1
        if release and self.eligible and self.position>=self.cert['finite_proof_end']:
            raise DecodeError('C9 finite programme complete; idle proof window exhausted')
        self.tick_number=self.position%4200;n=len(self.loops)
        super().tick();self.position+=1;self.absolute+=1;self.tick_number=self.absolute
        for j in range(n,len(self.loops)):
            _,i,p,q=self.loops[j];self.loops[j]=(self.absolute,i,p,q)
        if len(self.loops)>64:del self.loops[:-64]
        if release and self.eligible and self.position==release:
            if fingerprint(self)!=self.cert['completion_fingerprint'] or any(c[0]&128 for c in self.ch) or self.psg.attenuation!=[15]*4:
                raise DecodeError('C9 finite completion state mismatch')
            self.completed=True

def render_receipt(bank,schedule,dll):
    from backend import PSG
    m=Decoder(bank);m.direct(schedule['initial']);pcm=hashlib.sha256();native=hashlib.sha256();emission=hashlib.sha256()
    with PSG(dll) as chip:
        for t in range(1,schedule['ticks']+1):
            for kind,v in schedule.get('events',{}).get(str(t),[]):
                if kind=='request':m.direct(v)
                elif kind=='fade':m.fade=list(v)
                else:raise ValueError('unsupported action')
            m.tick();chip.write(m.writes);before=chip.state();pcm.update(chip.render().tobytes());native.update(canonical([before,chip.state()]));emission.update(canonical(state(m)))
    return dict(ticks=schedule['ticks'],samples=schedule['ticks']*735,PCM_sha256=pcm.hexdigest(),native_sha256=native.hexdigest(),state_PSG_sha256=emission.hexdigest(),renewals=m.renewals,extensions=m.extensions,completed=m.completed)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ('bank','schedule','dll','out'):p.add_argument(k)
    a=p.parse_args();r=render_receipt(unpack(Path(a.bank).read_bytes()),json.loads(Path(a.schedule).read_text()),a.dll);Path(a.out).write_text(json.dumps(r)+'\n')
