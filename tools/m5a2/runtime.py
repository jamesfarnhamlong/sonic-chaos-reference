"""ROM-free executable proof: SCSP + host requests -> decoder -> A1L -> PCM.

This module does not import original-driver tooling or read captured event rows.
"""
import argparse
import json
from pathlib import Path
import sys
import wave

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'tools/m5a0'), str(Path(__file__).parent)]
from bank import unpack
from decoder import Decoder
from backend import PSG
import numpy as np


def render(bank, schedule, dll, split=False, decoder_class=Decoder):
    m = decoder_class(bank)
    m.direct(schedule['initial'])
    blocks, states = [], []
    with PSG(dll) as chip:
        for t in range(1, schedule['ticks']+1):
            for kind, value in schedule['events'].get(str(t), []):
                if kind == 'request': m.direct(value)
                elif kind == 'mailbox': m.direct(*value)
                elif kind == 'fade': m.fade = list(value)
                else: raise ValueError('unsupported host action')
            m.tick()
            chip.write(m.writes)
            blocks.append(np.concatenate([chip.render(100),chip.render(635)]) if split else chip.render())
            states.append(chip.state())
    return np.concatenate(blocks), states


def wav(path, pcm):
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(44100)
        w.writeframes(pcm.astype('<i2').tobytes())


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('bank')
    p.add_argument('schedule')
    p.add_argument('dll')
    p.add_argument('out')
    a = p.parse_args()
    pcm, states = render(unpack(Path(a.bank).read_bytes()), json.loads(Path(a.schedule).read_text()), a.dll)
    wav(a.out, pcm)
    Path(a.out).with_suffix('.states.json').write_text(json.dumps(states))
