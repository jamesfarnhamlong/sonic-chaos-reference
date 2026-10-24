"""Focused original Z80 output diagnostics; private traces only."""
import hashlib
import json
from pathlib import Path
import audio1_psg_trace as T
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/m5-p0r'
PRIOR=ROOT.parent/'sonic-chaos-reference-m5-proof/build/m5-proof'

class Trace(T.Driver):
    def __init__(self,rom):
        self.port_trace=[];self.markers=[]
        super().__init__(rom)
    def _out(self,port,value):
        if port&255 in (0x7E,0x7F):
            self.port_trace.append(dict(tick=self.update,pc=self.cpu.pc,ix=self.cpu.ix,value=value,
                flags=list(self.mem[a] for a in T.CHANNELS),attenuation=list(self.psg.att)))
        super()._out(port,value)

def capture(rom,events,ticks,music=0x81):
    d=Trace(rom);d.request(music);states=[]
    for tick in range(1,ticks+1):
        for kind,v in events.get(tick,[]):
            if kind=='request':d.request(v)
            elif kind=='fade':d.mem[0xDE09:0xDE0C]=bytes(v)
        d.tick();states.append(dict(psg=d.psg.state(),flags=[d.mem[a] for a in T.CHANNELS],priority=d.mem[0xDE0F]))
    return d,states

def diagnose(rom):
    OUT.mkdir(parents=True,exist_ok=True)
    prior=PRIOR/'SonicChaos_M5_P0P1_20261024_PROOF_PRIVATE.zip'
    assert hashlib.sha256(prior.read_bytes()).hexdigest()=='3adf174848e83fc40644a7e12142dbd44062c25c5dff674d09df031fe4b9881f'
    import numpy as np
    import m5p1_proof as P
    bank=json.loads((PRIOR/'dry-event-bank.json').read_text());templates={}
    for rid in (0x81,0xA0,0xB6,0xB8,0xBC,0xBA,0xAC,0xBF,0xA3):
        if rid in (0x81,0xBF):
            folder=ROOT.parent/f'sonic-chaos-reference-m4/build/m4/production/{rid:02X}'
            raw=[P.mono(folder/f'ch{c}.wav') for c in range(4)];corrected=list(raw)
            corrected[0]=(P.mono(folder/'other3.wav').astype(np.int32)-raw[1]-raw[3]).astype(np.int16)
            _,s=capture(rom,{},len(raw[0])//735,music=rid)
            states=[x['psg'] for x in s]
        else:
            folder=PRIOR/'package'/('diagnostic-B8' if rid==0xB8 else f'library/{rid:02X}')
            corrected=[P.mono(folder/f'experimental{c}.wav') for c in range(4)]
            states=json.loads((folder/'private-registers.json').read_text())['states']
        templates[rid]=dict(corrected=corrected,states=states)
    for name,ev,n in [('B6-A0',{30:[('request',0xB6)],35:[('request',0xA0)]},180),
                      ('B8-BC',{30:[('request',0xB8)],35:[('request',0xBC)]},210),
                      ('BA-partial',{30:[('request',0xBA)],36:[('request',0xAC)]},180)]:
        d,states=capture(rom,ev,n);_,_,old=P.compose(bank,templates,0x81,ev,n)
        mismatch=[]
        for tick,(s,p) in enumerate(zip(states,old),1):
            for ch in range(4):
                if s['psg'][2][ch]<15 and s['psg'][2][ch]!=p[2][ch]:mismatch.append(dict(tick=tick,channel=ch,original=s['psg'][2][ch],old=p[2][ch]))
        (OUT/f'{name}-original.json').write_text(json.dumps(dict(events=ev,states=states,ports=d.port_trace),indent=2)+'\n')
        print(name,'mismatches',mismatch[:5])
        if name=='B6-A0':
            for m in mismatch:
                t=m['tick'];print('B6 boundary',t,'before/after',states[t-2:t]);print('ports', [r for r in d.port_trace if t-1<=r['tick']<=t+1])
    return templates

if __name__=='__main__':
    import sys
    diagnose(T.load_rom(sys.argv[1]))
