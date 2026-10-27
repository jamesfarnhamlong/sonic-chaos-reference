"""Opt-in $83 solo continuation; never a global coverage-horizon override.

Each renewal requires the pinned authenticated bank and exact complete driver
signature at the proved3072-tick recurrence. Any later host request/fade revokes
further renewals. No driver/channel/PSG state is reset or copied.
"""
from m5c71r83.contract import Decoder as BoundedDecoder,DecodeError,sha,canonical

BANK_SHA256='0f7b8a17250efdf301143eb20f1ed8ffba96ea7366213a912adb9a8b586d1bdc'
STATE_SHA256='b330f0e3c6dbea3cd0835ca6048791c2796691ec2560cd61792ddb97c1516871'
FIRST=522
REPEAT=3594
PERIOD=3072

def fingerprint(m):
    r=m.snapshot();r.pop('ports')
    r.update(channel_bytes=[list(c) for c in m.ch],shared_IY=m.iy,
        globals=[*m.tempo,m.selected,*m.mail,*m.fade,m.last_sfx,m.noise_offset,m.fade_noise_volume])
    return sha(canonical(r))

class Decoder(BoundedDecoder):
    def __init__(self,bank,horizon=None):
        if sha(canonical(bank))!=BANK_SHA256:raise DecodeError('83 renewal bank not authenticated')
        if horizon is not None and horizon!=4200:raise DecodeError('83 renewal requires unchanged4200 window')
        self.coverage_tick=0;self.renewal_count=0;self.last_renewal_tick=None;self._requests=0;self._eligible=False;self.transfer_log_dropped=0
        super().__init__(bank,horizon)

    def direct(self,rid,slot=0):
        self._requests+=1
        self._eligible=self._requests==1 and rid==0x83 and slot==0
        return super().direct(rid,slot)

    def tick(self):
        absolute=self.tick_number
        if absolute and (any(self.mail) or any(self.fade)):self._eligible=False
        if self.coverage_tick==REPEAT and self._eligible:
            if self.owners[:4]!=[0x83]*4 or fingerprint(self)!=STATE_SHA256:
                # Fail closed to the ordinary window: a signature mismatch never
                # grants another tick of coverage or mutates the original state.
                self._eligible=False
            else:
                self.coverage_tick=FIRST;self.renewal_count+=1;self.last_renewal_tick=absolute
        self.tick_number=self.coverage_tick
        n=len(self.loops)
        try:
            super().tick()
            self.coverage_tick=self.tick_number
            for j in range(n,len(self.loops)):
                _,i,p,q=self.loops[j];self.loops[j]=(absolute+1,i,p,q)
        finally:self.tick_number=absolute+1
        # This log is diagnostic only; memory remains bounded under long playback.
        if len(self.loops)>64:
            dropped=len(self.loops)-64;del self.loops[:dropped];self.transfer_log_dropped+=dropped
