"""SS-A4: replay input-only natural completions and failure/return routes for every stage from the original ROM (approximate SMS harness).

`natural-inputs.json` holds controller input only (run-length `[pad, frames]`, from `ss_search.py` or a hand controller).  Replay starts from the
natural stage-entry snapshot (the 100th ring injected through the original `$3138`), applies input only, and requires the original game itself to set
`$D294` bit 6; the run is then continued to the return to the ordinary act.
"""
import argparse
import hashlib
import json
from pathlib import Path
import rom as R
from ss_rig import SSRig, STAGE_BIT
from ss_search import restore

ROOT = Path(__file__).resolve().parents[1]
IN = ROOT / 'data/rom-cache/special-stages/natural-inputs.json'
OUT = ROOT / 'data/rom-cache/special-stages/natural-completions.json'


def replay(g, rle):
    s, m = g.s, g.m
    restore(g, g.e.base)
    f = 0
    for pad, n in rle:
        for _ in range(n):
            s.pad = pad; s.run_frame(); f += 1
            if m[0xD294] & 0x40:
                return f
    return None


def finish(g, origin_zone):
    s, m = g.s, g.m
    for f in range(4500):
        s.pad = 0; s.run_frame()
        if m[0xD297] == origin_zone and m[0xD298] == 1 and m[0xD500] == 1 and m[0xD293] == 0x40 and m[0xD294] == 0:
            return f
    return None


def failures(r, stage):
    """Timeout (no input, original timer) and out-of-bounds death for each stage."""
    out = {}
    g = SSRig(r, stage); s, m = g.s, g.m
    restore(g, g.e.base)
    for f in range(4000):
        s.pad = 0; s.run_frame()
        if m[0xD294] & 0x60:
            break
    out['idle_from_start'] = dict(frame=f, mode=hex(m[0xD294]), timer=hex(m[0xD2BF]), player_state=m[0xD501], lives=m[0xD299], emeralds=m[0xD2CC],
                                  ended_by='timer underflow' if m[0xD2BF] == 0 and m[0xD2BE] == 0 else 'death')
    # out-of-bounds: controlled placement below the camera's bottom limit (screen Y >= $D8 death rule), everything else original
    g = SSRig(r, stage); s, m = g.s, g.m
    bottom = s.u16(0xD27E)
    g.begin(s.u16(0xD511), bottom + 232, cur=0x0E, f3=1, floor=False, rings=0)
    ev = None
    for f in range(240):
        s.pad = 0; s.run_frame()
        if m[0xD294] & 0x20:
            ev = dict(frame=f, mode=hex(m[0xD294]), player_state=m[0xD501], lives=m[0xD299], emeralds=m[0xD2CC]); break
    out['pit_death_controlled_placement'] = ev
    return out


def build(r):
    inputs = json.loads(IN.read_text(encoding='utf-8'))
    d = dict(format=1, rom_sha256=R.SHA256, evidence='EMULATED ORIGINAL FRAME; input-only replay from the stage-entry snapshot', stages={})
    for stage in range(1, 6):
        rle = inputs.get(f'ss{stage}')
        g = SSRig(r, stage)
        if rle is None:
            row = dict(completed=False, reason='no input-only completion found within the search budget (see SS-A4 audit)')
            row['failure_routes'] = failures(r, stage)
            d['stages'][f'ss{stage}'] = row
            continue
        frames = replay(g, rle)
        row = dict(input_sha256=hashlib.sha256(json.dumps(rle).encode()).hexdigest(), input_runs=len(rle), input_frames=sum(n for _, n in rle))
        if frames is None or not (g.m[0xD2CC] & STAGE_BIT[stage]):
            row['completed'] = False
        else:
            row.update(completed=True, completion_frame=frames, timer_remaining=hex(g.m[0xD2BF]), emerald_bits=g.m[0xD2CC], bit_expected=STAGE_BIT[stage],
                       continues=g.m[0xD2C3], result_card=g.m[0xD2CD])
            row['return_frame_after_contact'] = finish(g, 0)
            row['returned_zone_act'] = [g.m[0xD297], g.m[0xD298]]
        row['failure_routes'] = failures(r, stage)
        d['stages'][f'ss{stage}'] = row
    return d


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('rom', type=Path); p.add_argument('--check', action='store_true'); a = p.parse_args()
    d = json.dumps(build(R.load(a.rom)), indent=2) + '\n'
    if a.check:
        assert OUT.read_text(encoding='utf-8') == d
    else:
        OUT.write_text(d, encoding='utf-8')
    print('ok')
