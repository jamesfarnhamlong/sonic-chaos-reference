"""Input-only route search for Special Stages (snapshot DFS/best-first over short held-input macros).

The search starts from the stage-start snapshot (nothing is injected: only controller input is chosen), forks via full harness snapshots and succeeds when the
original game itself sets `$D294` bit 6 (goal ring collected).  The resulting input list is a natural completion and is replayed from the start for
verification by `ss_natural.py`.
"""
from __future__ import annotations

import heapq
import itertools
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))

from ss_rig import SSRig, PAD  # noqa: E402

NEUTRAL = 0


def take(g):
    """Complete-state snapshot: harness snapshot plus the z80 core's full state view (hidden decode/WZ/interrupt state)."""
    return (g.e.snapshot(), bytes(g.s.cpu.get_state_view()))


def restore(g, snap):
    if snap is g.e.base:
        snap = (g.e.base, g.base_cpu)
    g.e.restore(snap[0])
    g.s.cpu.get_state_view()[:] = snap[1]


def run_macro(g, pad, frames):
    s, m = g.s, g.m
    for _ in range(frames):
        s.pad = pad
        s.run_frame()
        if m[0xD294] & 0x60:
            break
    return m[0xD294]


def observe(g):
    s, m = g.s, g.m
    return dict(x=s.u16(0xD511), y=s.u16(0xD514), state=m[0xD501], req=m[0xD502], vx=s.u16(0xD516), vy=s.u16(0xD518), mode=m[0xD294],
                timer=m[0xD2BF], floor=m[0xD522] & 2)


def search(g, actions, key, score, max_frames=3300, max_nodes=4000, macro_frames=12, verbose=False, goal_bit=0, start_snap=None, used0=0, prefix=(), time_weight=0.0, success=None):
    """Best-first search.  actions(obs) -> list of (pad, frames); key(obs) -> hashable; score(obs) -> lower is better (distance to goal)."""
    start = start_snap or (g.e.base, g.base_cpu)
    restore(g, start)
    root = (score(observe(g)), 0, used0, start, tuple(prefix))
    heap = [root]
    seen = {key(observe(g))}
    counter = itertools.count(1)
    best = None
    nodes = 0
    while heap and nodes < max_nodes:
        sc, _, used, snap, inputs = heapq.heappop(heap)
        nodes += 1
        restore(g, snap)
        obs0 = observe(g)
        for pad, frames in actions(obs0):
            if used + frames > max_frames:
                continue
            restore(g, snap)
            mode = run_macro(g, pad, frames)
            ob = observe(g)
            ni = inputs + ((pad, frames),)
            if (success(g) if success else (mode & 0x40 and (g.m[0xD2CC] & goal_bit) == goal_bit and mode != 0xFF)):
                return dict(inputs=ni, frames=used + frames, nodes=nodes, obs=ob)
            if mode & 0x20 or g.m[0xD501] == 0x1F:
                continue
            k = key(ob)
            if k in seen:
                continue
            seen.add(k)
            ns = score(ob) + time_weight * (used + frames)
            if best is None or ns < best[0]:
                best = (ns, ob, ni)
            heapq.heappush(heap, (ns, next(counter), used + frames, take(g), ni))
        if verbose and nodes % 50 == 0:
            print(nodes, len(heap), best[0] if best else None, best[1] if best else None, flush=True)
    return dict(inputs=None, nodes=nodes, best=best)
