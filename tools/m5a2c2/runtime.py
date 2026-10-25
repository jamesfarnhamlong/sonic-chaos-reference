"""ROM-free SCSP v1 runtime using the source-gated FD extension and unchanged A1L."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/m5a2')]
from m5a2.bank import unpack
from m5a2.runtime import render as base_render,wav
from m5a2c2.decoder import Decoder


def render(bank,schedule,dll,split=False):
    return base_render(bank,schedule,dll,split=split,decoder_class=Decoder)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for f in ('bank','schedule','dll','out'):p.add_argument(f)
    a=p.parse_args();pcm,states=render(unpack(Path(a.bank).read_bytes()),json.loads(Path(a.schedule).read_text()),a.dll)
    wav(a.out,pcm)
