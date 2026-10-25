"""Original-only diagnostic observer. This module never drives candidate playback."""
from pathlib import Path
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a0')]
import audio1_psg_trace as T
from backend import PSG


class OriginalNoise(T.Driver):
    def __init__(self,rom):
        path=ROOT.parent/'sonic-chaos-reference-m5-a0/build/m5-a0/psg-a0.dll'
        expected=json.loads((ROOT/'data/m5-a2/pcm.json').read_text())['A0_diagnostic_sha256']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==expected
        self.native=PSG(path)
        self.F3_states=[]
        super().__init__(rom)

    def _out(self,port,value):
        if port&255 in (0x7E,0x7F):
            before=self.native.state();self.native.write([value]);after=self.native.state()
            if self.cpu.pc==0x477F:
                self.F3_states.append(dict(tick=self.update,byte=value,mode=value&7,
                    RNG_before=before[21],RNG_after=after[21],noise_counter_before=before[16],noise_counter_after=after[16],
                    tone2_period=after[11],noise_period=after[12],
                    qualification='instant before/after actual original F3 OUT; no sample elapsed across the write'))
        super()._out(port,value)

    def tick(self):
        super().tick();self.native.render() # reference diagnostic time only; samples discarded

    def close(self):self.native.close()
