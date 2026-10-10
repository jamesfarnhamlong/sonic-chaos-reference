"""SS-A4: large goal ring (type $31): contact box, collection effects, simultaneous-flag ordering and failure paths."""
import argparse
import itertools
import json
from pathlib import Path
import level_package as L
import rom as R
import mghz_object_census as C
from oracle import Oracle
from ss_rig import SSRig
import ss_foundation as F

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/rom-cache/special-stages/goal-ring.json'
SLOT = 0xD740


def fixture(r, o, ring_x=2000, ring_y=300, param=1, d503=0, ix4=0, ix3=0x80, ix2c=8, ix2d=16, p2d=24, p2c=8):
    o.bank(2, 0x1E)
    m = o.mem
    m[SLOT:SLOT + 64] = bytes(64)
    m[SLOT] = 0x31; m[SLOT + 1] = 1; m[SLOT + 2] = 1; m[SLOT + 3] = ix3; m[SLOT + 4] = ix4
    o.word(SLOT + 0x11, ring_x); o.word(SLOT + 0x14, ring_y)
    m[SLOT + 0x2C] = ix2c; m[SLOT + 0x2D] = ix2d; m[SLOT + 0x3F] = param; m[SLOT + 0x3E] = 2
    m[0xD503] = d503; m[0xD52C] = p2c; m[0xD52D] = p2d
    m[0xD294] = 0x80; m[0xD2CC] = 0; m[0xD2CD] = 1; m[0xD2C3] = 0; m[0xD2BF] = 0x37
    o.cpu.ix = SLOT


def contact_sweep(r):
    """Original callback $1E:$9489 for every player offset around the ring: collected iff D294 bit6 set."""
    res = {}
    for label, kw in (('normal_8x24', {}), ('state0F_9x24', dict(p2c=9)), ('hurt_blink_d503_40', dict(d503=0x40)), ('invincible_d503_80', dict(d503=0x80))):
        hit = set()
        for dx, dy in itertools.product(range(-24, 25), range(-34, 40)):
            o = Oracle(r); fixture(r, o, **kw)
            o.word(0xD511, 2000 + dx); o.word(0xD514, 300 + dy)
            o.call(0x9489)
            if o.mem[0xD294] & 0x40:
                hit.add((dx, dy))
        xs = sorted({p[0] for p in hit}); ys = sorted({p[1] for p in hit})
        res[label] = dict(dx=[xs[0], xs[-1]], dy=[ys[0], ys[-1]], cells=len(hit), full_rectangle=len(hit) == len(xs) * len(ys))
    o = Oracle(r); fixture(r, o, ix4=0x40); o.word(0xD511, 2000); o.word(0xD514, 300); o.call(0x9489)
    res['asleep_or_hidden_ix4_bit6_blocks_collection'] = not (o.mem[0xD294] & 0x40)
    o = Oracle(r); fixture(r, o, ix3=0xC0); o.word(0xD511, 2000); o.word(0xD514, 300); o.call(0x9489)
    res['ix3_bit6_blocks_collection'] = not (o.mem[0xD294] & 0x40)
    return res


def collection_effects(r):
    out = {}
    for param, emer0, cont0, timer, d294 in ((1, 0, 0, 0x58, 0x80), (2, 0x01, 5, 0x20, 0x80), (4, 0x03, 0x7F, 0x00, 0x80), (8, 0x07, 0x80, 0x59, 0x80), (16, 0x0F, 0x7E, 0x01, 0xA0)):
        o = Oracle(r); fixture(r, o, param=param); m = o.mem
        m[0xD2CC] = emer0; m[0xD2C3] = cont0; m[0xD2BF] = timer; m[0xD294] = d294
        o.word(0xD511, 2000); o.word(0xD514, 300); o.call(0x9489)
        out[f'param{param}'] = dict(pre=dict(emeralds=emer0, continues=cont0, timer=timer, mode=d294),
                                    post=dict(emeralds=m[0xD2CC], continues=m[0xD2C3], card=m[0xD2CD], d2a6=o.word(0xD2A6), mode=m[0xD294], slot_type=m[SLOT], token=m[SLOT + 0x3E]))
    return out


def whole_game(r):
    out = {}
    g = SSRig(r, 1); m, s = g.m, g.s
    # simultaneous failure + success flags: success path wins in the dispatcher ($1762 tests bit6 before bit5)
    g.begin(15248, 118, cur=0x0E, f3=1, floor=False, rings=0)
    forced = [False]

    def both(gg):
        pass
    for f in range(400):
        s.pad = 0; s.run_frame()
        if m[0xD294] & 0x40 and not forced[0]:
            m[0xD294] |= 0x20; forced[0] = True
        if forced[0] and m[0xD297] == 0:
            break
    out['success_and_failure_flags_together'] = dict(emeralds=m[0xD2CC], card=m[0xD2CD], continues=m[0xD2C3], zone=m[0xD297], act=m[0xD298])
    # pit death: falling below the screen without rocket shoes (stage 1 has no floor under the start monitor corridor)
    g = SSRig(r, 1); m, s = g.m, g.s
    g.begin(300, 130, cur=0x0E, f3=1, floor=False, rings=0)
    ev = []
    for f in range(200):
        s.pad = 0; s.run_frame()
        if m[0xD501] == 0x1F and not ev:
            ev.append(dict(frame=f, screen_y=s.u16(0xD514) - s.u16(0xD176), world_y=s.u16(0xD514)))
        if m[0xD294] & 0x20:
            ev.append(dict(frame=f, mode=hex(m[0xD294]), lives=m[0xD299])); break
    out['pit_death_ss1'] = ev
    return out


def build(r):
    d = dict(format=1, rom_sha256=L.ROM_SHA256, research_base=F.BASE, stage='SS-A4 goal ring',
             evidence='original callback $1E:$9489 executed over a boundary sweep; whole-game traces in the approximate SMS harness')
    d['object'] = dict(type=0x31, type_table_entry_rom=0x661A, bank=0x1E, state_table_cpu=0x9468, scripts=C.public_script(C.state_scripts(r, 0x31)),
                       state0='$9480: state := 1, SET bit7 of +3 (contact ignores player blink/hurt bit)',
                       state1='frames 1,2,3 for 6 updates each; callback $9489',
                       fields={'+3': 0x80, '+0x2C': 8, '+0x2D': 16, '+0x3F': 'placement parameter = completion bit'},
                       art_bases=[0x6A, 0x6A])
    d['callback_9489'] = [
        'if (+4 bit6) return                                     ; asleep/hidden: no contact',
        'contact test = shared $6328 (closed intervals): |dx| <= playerHalfW($D52C)+8 ; dy in [-(ringHalfH 16), +playerHalfH($D52D)]',
        'any overlap class bit (+0x21 & $F) != 0 -> collect',
        'D2A6 := (D2BF << 8) ; D2CC |= +0x3F ; D2CD := $FF ; +0x3E := 0 ; type := $FF (delete) ; D294 |= $40 ; D2C3 := (D2C3+1) & $7F',
        'no player state change, no velocity change, no sound here']
    d['contact_sweep'] = contact_sweep(r)
    d['collection_effects'] = collection_effects(r)
    d['whole_game'] = whole_game(r)
    return d


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('rom', type=Path); p.add_argument('--check', action='store_true'); a = p.parse_args()
    d = json.dumps(build(R.load(a.rom)), indent=2) + '\n'
    if a.check:
        assert OUT.read_text(encoding='utf-8') == d
    else:
        OUT.write_text(d, encoding='utf-8')
    print('ok')
