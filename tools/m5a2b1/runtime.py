"""ROM-free A2B1 playback. SCSP v1 and accepted A1L synthesis are unchanged."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2')]
from m5a2.bank import unpack
from m5a2.runtime import render as accepted_render,wav
from m5a2b1.decoder import Decoder


def render(bank,schedule,dll,split=False):
    return accepted_render(bank,schedule,dll,split=split,decoder_class=Decoder)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for field in ('bank','schedule','dll','out'):p.add_argument(field)
    a=p.parse_args()
    pcm,states=render(unpack(Path(a.bank).read_bytes()),json.loads(Path(a.schedule).read_text()),a.dll)
    wav(a.out,pcm)
