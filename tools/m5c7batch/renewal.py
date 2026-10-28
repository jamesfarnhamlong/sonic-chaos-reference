"""Pinned92/8F solo capabilities only; unchanged4200 bound for all other contexts."""
import json
from pathlib import Path
from m5c7batch.alias92 import Decoder as Bounded,sha,canonical
from m5a2.decoder import DecodeError

def fingerprint(m):
    r=m.snapshot();r.pop('ports')
    r.update(channel_bytes=[list(c) for c in m.ch],shared_IY=m.iy,
        globals=[*m.tempo,m.selected,*m.mail,*m.fade,m.last_sfx,m.noise_offset,m.fade_noise_volume])
    return sha(canonical(r))

class Decoder(Bounded):
    def __init__(self,bank,horizon=None):
        certs=json.loads((Path(__file__).resolve().parents[2]/'data/m5-c7-batch/continuation-certificates.json').read_text())
        self.cert=next((c for c in certs.values() if c['bank_canonical_sha256']==sha(canonical(bank))),None)
        if self.cert is None or horizon not in (None,4200):raise DecodeError('batch solo bank/window not authenticated')
        self.coverage_tick=0;self.renewal_count=0;self.requests=0;self.eligible=False;self.last_renewal_tick=None
        super().__init__(bank,horizon)
    def direct(self,rid,slot=0):
        self.requests+=1;self.eligible=self.requests==1 and rid==self.cert['request_id'] and slot==0
        return super().direct(rid,slot)
    def tick(self):
        absolute=self.tick_number
        if absolute and (any(self.mail) or any(self.fade)):self.eligible=False
        if self.coverage_tick==self.cert['repeat_tick'] and self.eligible:
            rid=self.cert['request_id']
            if any(v!=rid for v in self.owners[:len(self.bank['programs'][str(rid)]['streams'])]) or fingerprint(self)!=self.cert['state_sha256']:
                self.eligible=False
            else:
                self.coverage_tick=self.cert['first_tick'];self.renewal_count+=1;self.last_renewal_tick=absolute
        self.tick_number=self.coverage_tick;n=len(self.loops)
        try:
            super().tick();self.coverage_tick=self.tick_number
            for j in range(n,len(self.loops)):
                _,i,p,q=self.loops[j];self.loops[j]=(absolute+1,i,p,q)
        finally:self.tick_number=absolute+1
        if len(self.loops)>64:del self.loops[:-64]
