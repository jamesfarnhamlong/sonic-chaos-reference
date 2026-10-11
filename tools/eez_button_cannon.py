"""EEZ3 floor button (surface $0B, cell $B1->$B2) and the type-$37 parameter-1 cannon bolt.

Whole-game fixtures run original scheduler/player/terrain/object code from the zone5 act3
snapshot. Fixture writes are Sonic's placement, invincibility selector $D532=6 (so contact
cannot knock him off the button), camera/park position (to force offscreen sleep) and, in the
reload case, a pit position. The layout cell is only observed, never written.
"""
import argparse
import eez_foundation as F
import level_package as L
from sez_surfaces_rig import ZoneGame

ZONE, ACT, WIDTH = 5, 2, 112
BUTTONS = [(36, 26), (38, 26), (40, 26), (42, 26), (44, 26), (46, 26), (48, 26)]
OLD, NEW = 0xB1, 0xB2
HANDLER, ALLOC16, INIT, STATE3, STATE2, DELETE, LOADER = 0x6BAA, 0x5E9C, 0x8ED0, 0x8F43, 0x8F23, 0x8F3E, 0x4DAE


CONTRACT = dict(
    chain='terrain floor pass -> surface $0B handler $6BAA (needs floor bit1 $D522) -> $6BAF C=$B2, $6BD4: layout cell (*$D354)=$B2 and nametable redraw -> $5E9C (16-slot) type $37 parameter 1 -> init $1E:$8ED0 state3 at cell X+15, Y=cell+24-120 (act index 2) -> state3 $8F43 falls +4.25 and hurts while at/before cellY-24 -> state2 dissipate -> delete.',
    q1='No. Nothing re-arms. The cell stays $B2 until the act layout is re-decoded by the level loader ($4DAE..$4DFB) on death/restart/reload.',
    q2='Not applicable (no callback count or event restores $B1). Only level (re)load resets it.',
    q3='No visible reset: $B2 is written once and redrawn once; the button stays in its changed art.',
    q4='Local to each layout cell. EEZ3 has seven $B1 cells at row 26, x=36,38,...,48; each fires independently and once. Shared state is only the object pool and scratch $D35C/$D35E/$D354.',
    q5='One firing only: the handler runs with floor bit1 once, rewrites the cell, and later frames probe $B2, so the handler is not entered. Standing for 700 updates gives one allocation.',
    q6='No. Reset is not object-owned. The bolt is a normal object and is removed by generic offscreen lifecycle if the camera leaves (the cell stays $B2), and the cell persists through 1000 offscreen updates.')


class Case:
    """One fork of the snapshot with named events and a per-update script."""

    def __init__(self, r, script, n, pad=None, rings=0, inv=True, start=(0, 0), types=(0x37,)):
        self.g = g = ZoneGame(r, ZONE, ACT, hooks={0x16D0: 'after_player', 0x16D3: 'after_objects'})
        s, m = g.s, g.m
        cpu = bytes(s.cpu.get_state_view())

        def restore():
            g.e.restore()
            s.cpu.get_state_view()[:] = cpu
        g.restore_snapshot = restore
        self.ev, self.script, self.inv, self.s, self.m = [], script, inv, s, m
        names = {HANDLER: 'surface0B', ALLOC16: 'alloc16', INIT: 'bolt_init', STATE3: 'bolt_state3', STATE2: 'bolt_state2',
                 DELETE: 'bolt_delete', LOADER: 'level_loader'}
        for pc, name in names.items():
            g.hook(pc, self._note(name))
        old = g._engine_hook

        def engine(mm):
            old(mm)
            if g.recording and mm.cpu.ix == 0xD500:
                self.script(self, len(g.rows) + 1)
        g.hook(0x64FA, engine)
        x, y, kw = start
        g.begin(x, y, cur=14, floor=False, rings=rings, d532=6 if inv else None, types=types, **kw)
        self.rows = g.run(n, padf=pad)

    def _note(self, name):
        def fn(mm):
            g = self.g
            if not g.recording:
                return
            row = dict(u=len(g.rows) + 1, ev=name)
            if name == 'surface0B':
                row.update(floor_bit1=bool(self.m[0xD522] & 2), cell_ptr=self.s.u16(0xD354))
            self.ev.append(row)
        return fn

    def cell(self, i):
        cx, cy = BUTTONS[i]
        return self.m[0xC001 + cy * WIDTH + cx]

    def park(self, x, y):
        self.s.w16(0xD511, x); self.s.w16(0xD514, y); self.s.w16(0xD516, 0); self.s.w16(0xD518, 0)
        self.set_camera(max(0, x - 112), max(8, y - 100))
        self.m[0xD501] = self.m[0xD502] = 14

    def set_camera(self, x, y):
        # $0573 copies staging words $D284/$D286 into live camera $D174/$D176 at V-blank.
        for a, v in ((0xD174, x), (0xD176, y), (0xD284, x), (0xD286, y)):
            self.s.w16(a, v)

    def camera_to_sonic(self):
        self.set_camera(max(0, self.s.u16(0xD511) - 112), max(8, self.s.u16(0xD514) - 100))

    def count(self, name, lo=0, hi=1 << 30):
        return sum(e['ev'] == name and lo <= e['u'] <= hi for e in self.ev)


def top(i):
    return BUTTONS[i][0] * 32 + 16, BUTTONS[i][1] * 32 - 40


def build(r):
    out = {}
    # S1: land on button 0 and keep standing (invincible) for 700 updates.
    cells = []
    c1 = Case(r, lambda c, u: cells.append((u, c.cell(0), c.cell(1))), 700, start=(*top(0), dict(vy=256)))
    firing = [e for e in c1.ev if e['ev'] == 'surface0B' and e['floor_bit1']]
    fire_u = firing[0]['u']
    bolt = [e['u'] for e in c1.ev if e['ev'] == 'bolt_delete']
    assert c1.count('alloc16') >= 1 and fire_u > 0
    first_b2 = next(u for u, a, b in cells if a == NEW)
    assert all(a == NEW for u, a, b in cells if u >= first_b2) and all(b == OLD for u, a, b in cells)
    standing_rows = [rw for rw in c1.rows if rw['u'] > fire_u + 70]
    out['S1_stand'] = dict(
        fixture='Sonic lands on EEZ3 cell (36,26), invincibility selector 6, no input, 700 updates.',
        fire_update=fire_u, floor_hits_total=len(firing), handler_entries=c1.count('surface0B'),
        alloc16=c1.count('alloc16'), bolt_inits=c1.count('bolt_init'), bolt_delete_updates=bolt,
        first_b2_update=first_b2, cell0_after=hex(cells[-1][1]), cell1_after=hex(cells[-1][2]),
        sonic_still_on_button=all(rw['y'] >= 836 and rw['x'] == top(0)[0] for rw in standing_rows), updates=len(c1.rows))
    # S2: fire, stay, park far away (sleep window), return to button 0 (now $B2), then step on button 1.
    far = (200, 400)
    timeline = []

    def script2(c, u):
        c.m[0xD532] = 6
        if 120 <= u < 1020:
            c.park(*far)
        elif u == 1020:
            c.park(*top(0)); c.s.w16(0xD518, 256)
        elif u == 1420:
            c.park(*top(1)); c.s.w16(0xD518, 256)
        if 1020 <= u < 1040 or 1420 <= u < 1440:
            c.camera_to_sonic()
        timeline.append((u, c.cell(0), c.cell(1)))
    c2 = Case(r, script2, 1700, start=(*top(0), dict(vy=256)))
    s2_fire = [e['u'] for e in c2.ev if e['ev'] == 'surface0B' and e['floor_bit1']]
    s2_alloc = [e['u'] for e in c2.ev if e['ev'] == 'alloc16']
    out['S2_offscreen_return'] = dict(
        fixture='Fire button 0 (u~17), park Sonic at WORLD(200,400) u120..1019 (button 0 ~1000px offscreen), return u1020, step on fresh button 1 at u1420.',
        floor_hits=s2_fire, alloc16=s2_alloc, cell0_at=dict((u, hex(a)) for u, a, b in timeline if u in (60, 119, 1019, 1100, 1400, 1699)),
        cell1_at=dict((u, hex(b)) for u, a, b in timeline if u in (60, 1100, 1419, 1500, 1699)), updates=len(c2.rows))
    assert len(s2_fire) == 2 and s2_fire[0] < 40 and s2_fire[1] >= 1420
    assert all(a == NEW for u, a, b in timeline if u >= s2_fire[0] + 1) and all(b == OLD for u, a, b in timeline if u < s2_fire[1])
    # S3: camera/Sonic leave 3 updates after the bolt is allocated (bolt asleep in flight), then return.
    def script3(c, u):
        c.m[0xD532] = 6
        fired = next((e['u'] for e in c.ev if e['ev'] == 'alloc16'), None)
        if fired and fired + 3 <= u < fired + 500:
            c.park(*far)
        elif fired and u == fired + 500:
            c.park(*top(0)); c.s.w16(0xD518, 256)
        if fired and fired + 500 <= u < fired + 520:
            c.camera_to_sonic()
        s3_cells.append((u, c.cell(0)))
    s3_cells = []
    c3 = Case(r, script3, 800, start=(*top(0), dict(vy=256)))
    s3_hits = [e['u'] for e in c3.ev if e['ev'] == 'surface0B' and e['floor_bit1']]
    out['S3_bolt_asleep'] = dict(
        fixture='Fire button 0, move Sonic+camera away 3 updates after allocation for 500 updates, then return to the same cell.',
        floor_hits=s3_hits, alloc16=c3.count('alloc16'), bolt_alive_updates=[rw['u'] for rw in c3.rows if rw['o']],
        cell0_final=hex(s3_cells[-1][1]), updates=len(c3.rows))
    assert len(s3_hits) == 1 and c3.count('alloc16') == 1 and s3_cells[-1][1] == NEW
    assert out['S3_bolt_asleep']['bolt_alive_updates'] and max(out['S3_bolt_asleep']['bolt_alive_updates']) < 30
    # S4: fire, then walk right (no input trickery) into the pit that follows the button row; death reloads the act.
    def script4(c, u):
        c.m[0xD532] = 6 if u < 80 else 0
        s4_cells.append((u, c.cell(0), c.cell(3)))
    s4_cells = []
    c4 = Case(r, script4, 900, pad=lambda u, f: 8 if u >= 80 else 0, start=(*top(0), dict(vy=256)))
    loads = [e['u'] for e in c4.ev if e['ev'] == 'level_loader']
    assert loads
    fires = [e['u'] for e in c4.ev if e['ev'] == 'surface0B' and e['floor_bit1']]
    out['S4_reload'] = dict(fixture='Fire button 0, run right over buttons 1..6 and into the pit; invincibility off from u80.',
        level_loader_updates=loads, floor_hits=fires,
        cell0_before_loader=hex(next(b for u, b, d in reversed(s4_cells) if u < loads[0])),
        cell3_before_loader=hex(next(d for u, b, d in reversed(s4_cells) if u < loads[0])),
        cell0_after_loader=hex(next(b for u, b, d in s4_cells if u > loads[0] + 2)),
        cell3_after_loader=hex(next(d for u, b, d in s4_cells if u > loads[0] + 2)), updates=len(c4.rows))
    assert out['S4_reload']['cell0_before_loader'] == hex(NEW) and out['S4_reload']['cell0_after_loader'] == hex(OLD)
    scan = [i for i in range(len(r) - 1) if r[i] == 0x0E and r[i + 1] == NEW and r[i + 2:i + 5] == bytes([0xCD, 0xD4, 0x6B])]
    assert scan == [0x6BAF]
    out['static'] = dict(layout_cell_writers_of_B2=[hex(x) for x in scan],
        note='Immediate-operand scan: the only LD C,$B2 followed by CALL $6BD4 is surface $0B at $6BAF. $6BD4 stores C to the probed layout cell ($D354) and redraws it.')
    out['contract'] = CONTRACT
    out['rom_sha256'] = L.ROM_SHA256
    out['method'] = __doc__
    return out, (c1, c2)


def main():
    p = argparse.ArgumentParser(); p.add_argument('rom'); a = p.parse_args()
    r = L.load_rom(a.rom)
    out, _ = build(r)
    (F.OUT / 'button-cannon.json').write_text(F.dumps(out), encoding='utf-8')
    print('button-cannon.json written')


if __name__ == '__main__':
    main()
