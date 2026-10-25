"""Decoded-data PSG state observer; never supplies events to production playback."""
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2'),str(ROOT/'tools/m5a0')]
from backend import PSG
from m5a2c2.decoder import Decoder
from m5a2c2.runtime import wav
from m5a2.pcm import DLL
import numpy as np


def observe(bank,case,deduplicate_noise_controls=False):
    initial,events,ticks=case;m=Decoder(bank);m.direct(initial);controls=[];frames=[];blocks=[];last=None
    with PSG(DLL) as chip:
        for t in range(1,ticks+1):
            for kind,value in events.get(t,[]):
                if kind=='request':m.direct(value)
                elif kind=='fade':m.fade=list(value)
                elif kind=='mailbox':m.direct(*value)
            m.tick()
            for value in m.writes:
                control=bool(value&128 and value>>4&7==6)
                before=chip.state()
                if not (deduplicate_noise_controls and control and value==last):chip.write([value])
                after=chip.state()
                if control:
                    controls.append(dict(tick=t,byte=value,mode=value&7,RNG_before=before[21],RNG_after=after[21],
                      noise_counter_before=before[16],noise_counter_after=after[16],tone2_period=after[11],noise_period=after[12]))
                    last=value
            blocks.append(chip.render());s=chip.state()
            frames.append(dict(tick=t,noise_control=s[6],noise_attenuation=s[7],tone2_register=s[4],tone2_period=s[11],
                  noise_period=s[12],noise_counter=s[16],RNG=s[21],music_tone2_flags=m.ch[2][0],SFX_flags=[c[0] for c in m.ch[4:]]))
    return np.concatenate(blocks),dict(controls=controls,frames=frames)
