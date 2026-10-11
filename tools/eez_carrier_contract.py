"""Original-ROM correction oracle for mapped $17 / player $16/$17 only.

No POC model or substituted ROM instruction. Breakpoints observe real entries;
fixtures supply RAM at routine/update boundaries. Counts are explicit checked
predicates, not unittest method counts. Original overlap checks remain separate.
"""
import itertools
import json
from pathlib import Path

from oracle import Oracle
import eez_foundation as F
import level_package as L
import rom as R

S = 0xD700
P = 0xD500
WATCH = (0x4C56, 0x753E, 0x48BC, 0x401A, 0x45ED, 0x494F,
         0x4984, 0x4141, 0x402A, 0x4097, 0x690B)


def trace_call(o, address, watch=WATCH):
    """Observe original routine entries without replacing their instructions."""
    c = o.cpu
    c.pc = address
    c.sp = 0xDFE0
    o.word(c.sp, o.RETURN)
    for pc in watch:
        c.set_breakpoint(pc)
    events = []
    try:
        for _ in range(2000):
            c.ticks_to_stop = 100000
            c.run()
            if c.pc == o.RETURN:
                return events
            if c.pc in watch:
                pc = c.pc
                events.append(dict(pc=pc, ix=c.ix, iy=c.iy,
                                   player=list(o.mem[P:P+64]), owner=o.word(0xD3A6)))
                c.clear_breakpoint(pc)
                c.ticks_to_stop = 1
                c.run()
                c.set_breakpoint(pc)
        raise AssertionError(f'original callback did not return: {c.pc:04X}')
    finally:
        for pc in watch:
            c.clear_breakpoint(pc)


def fixture(raw):
    o = Oracle(raw)
    m = o.mem
    m[P:P+64] = bytes(64)
    m[S:S+64] = bytes(64)
    m[P] = 1
    m[P+1] = m[P+2] = 23
    m[P+44], m[P+45] = 8, 24
    m[S], m[S+1], m[S+2], m[S+63] = 23, 2, 2, 2
    m[S+44], m[S+45] = 12, 16
    m[S+4] = 128
    m[0xD297] = 5
    m[0xD298] = 0
    m[0xD443] = 0
    # Empty terrain isolates the callback branches; real ring cells are tested
    # separately. Header table and routines are always original ROM.
    m[0xC001:0xD000] = bytes([255]) * 4095
    o.word(S+17, 1000)
    o.word(S+20, 100)
    o.word(S+22, 321)
    o.word(S+24, 123)
    o.word(0xD3A6, S)
    o.word(0xD51C, 100)
    o.word(0xD373, 1024)
    m[0xD36B] = 255
    m[0xD12B] = 12
    m[0xD135] = 1  # satisfy original062D IRQ semaphore; no ROM patch
    o.cpu.ix, o.cpu.iy = P, S
    return o


def build(raw):
    checks = {}
    samples = {}

    def eq(group, actual, expected):
        assert actual == expected, (group, actual, expected)
        checks[group] = checks.get(group, 0) + 1

    # All 256 fractional values in each axis, with deliberately different
    # owner fractions; full cross product at boundary fractions as well.
    fractions = sorted(set([(f, 255-f) for f in range(256)] +
                           list(itertools.product((0, 1, 127, 128, 254, 255), repeat=2))))
    o = fixture(raw)
    m = o.mem
    for parameter, (fx, fy), (vx, vy) in itertools.product(
            (0, 2, 3, 255), fractions,
            ((0, 0), (0x8000, 0x7FFF), (0xFFFF, 1), (321, 0xFC00))):
        m[P+16], m[P+19] = fx, fy
        m[S+16], m[S+19] = 255-fx, 255-fy
        m[P+3], m[P+4] = 0xA5, 0xEF
        m[P+1], m[P+2] = 23, 30
        m[S+1], m[S+2], m[S+3], m[S+4], m[S+34] = 4, 5, 0x40, 0x80, 2
        m[S+63] = parameter
        o.word(S+22, vx)
        o.word(S+24, vy)
        o.call(0x4C56)
        eq('copy', [o.word(a) for a in (P+17, P+20, P+22, P+24)], [1000, 100, vx, vy])
        eq('copy', [m[P+16], m[P+19]], [fx, fy])
        eq('copy', [m[P+1], m[P+2], m[P+3], m[P+4], m[P+34]],
           [23, 30, 0xA7, 0xEF if parameter == 2 else 0xFF, 0])

    # Actual $4C12, including its ring/hurt/death calls and ordinary jump
    # setter. Exhaust all six held-input bits; direction bits do not steer.
    callback_examples = []
    for pad, water, tile, requested in itertools.product(range(64), (0, 1), (255, 0x90), (23, 30, 31)):
        o = fixture(raw)
        m = o.mem
        m[0xD137], m[0xD443], m[0xD36B] = pad, water, tile
        m[P+2] = requested
        m[P+16], m[P+19] = 77, 99
        events = trace_call(o, 0x4C12)
        pcs = [e['pc'] for e in events]
        eq('attached_callback', pcs[:4], [0x4C56, 0x753E, 0x48BC, 0x401A])
        eq('attached_callback', [pc for pc in pcs if pc in (0x4141, 0x402A, 0x4097, 0x690B)], [])
        detached = requested in (30, 31) or bool(pad & 48)
        eq('attached_callback', o.word(0xD3A6), 0 if detached else S)
        eq('attached_callback', [m[S+4], m[S+3], m[S+31], m[S+2]],
           [0, 64, 16, 2] if detached else [128, 0, 0, 2])
        # Deliberately request-only fixtures: unlike a real hurt/death setter,
        # these have no airborne bit.45ED can therefore overwrite1E/1F.
        jump = detached and tile != 0x90
        eq('attached_callback', [m[P+2], o.word(P+17), o.word(P+20), o.word(P+22), o.word(P+24)],
           [10 if jump else requested, 1000, 99 if jump else 100, 321,
            (0xFCC0 if water else 0xFBC0) if jump else 123])
        eq('attached_callback', [m[P+16], m[P+19], m[P+3]],
           [77, 99, 3 if jump else 2])
        eq('attached_callback', 0x45ED in pcs, detached)
        if pad in (0, 4, 8, 16, 32, 48) and not water and tile == 255:
            callback_examples.append(dict(pad=pad, requested=requested, entries=pcs,
                                          final_requested=m[P+2], owner=o.word(0xD3A6)))
    samples['attached_callback'] = callback_examples

    for screen_y in (0, 207, 208, 32767, 32768, 65535):
        o = fixture(raw)
        m = o.mem
        o.word(0xD51C, screen_y)
        events = trace_call(o, 0x4C12)
        dead = 208 <= screen_y < 32768
        eq('attached_screen_death', [m[P+2], o.word(0xD3A6), o.word(P+24)],
           [31, 0, 0xFB00] if dead else [23, S, 123])
        eq('attached_screen_death', 0x4984 in [e['pc'] for e in events], dead)

    # State16 callback unhides Sonic, hides owner, but does not copy the
    # owner's state/flags/fractions. Its script requests17 on next engine call.
    o = fixture(raw)
    m = o.mem
    m[P+4] = 0x80
    m[P+16], m[P+19] = 11, 22
    m[S+16], m[S+19] = 33, 44
    m[P+1] = m[P+2] = 22
    trace_call(o, 0x4C02)
    eq('player16', [m[P+4], m[S+4], m[P+3], m[P+16], m[P+19]], [0, 128, 2, 11, 22])
    o.bank(2, 12)
    o.call(0x835E)
    eq('player16', [m[P+1], m[P+2]], [22, 23])

    # Exact signed 16-bit screen-Y boundary, all possible values. No call
    # hooks needed: requested death state is the original routine's result.
    o = fixture(raw)
    m = o.mem
    for y in range(65536):
        m[0xD135] = 1
        o.word(0xD51C, y)
        m[P+2], m[P+3], m[P+4], m[P+34] = 23, 2, 16, 2
        o.word(P+24, 123)
        o.call(0x401A)
        dead = 208 <= y < 32768
        eq('screen_death', [m[P+2], m[P+3], m[P+4], m[P+34], o.word(P+24)],
           [31, 3, 0, 0, 0xFB00] if dead else [23, 2, 16, 2, 123])

    # Bounce enters494F, not48F7 or4942. Rings, immunity counter/flags and
    # zero-ring survival are observed rather than inferred from a name.
    bounce_examples = []
    for owner, rings, flags, floor, side in itertools.product(
            (0, S, S+64), (0, 1, 0x10, 0x99), (0, 2, 64, 128, 192), range(4), (0, 8)):
        o = fixture(raw)
        m = o.mem
        o.bank(2, 12)
        o.cpu.ix, o.cpu.iy = S, P
        m[P+3], m[P+4], m[P+34], m[P+35] = flags, 255, floor, side
        m[0xD29A], m[0xD3B1] = rings, 37
        m[S+34] = 3
        o.word(0xD3A6, owner)
        events = trace_call(o, 0xA6D7, (0x0419, 0x494F, 0x48F7, 0x4942, 0x4984))
        owns = owner == S
        eq('bounce', [e['pc'] for e in events], [0x0419, 0x494F] if owns else [])
        eq('bounce', [m[S+2], o.word(S+22), o.word(S+24), m[S+34], m[P+4]], [5, 0, 0xFC00, 1, 127])
        eq('bounce', [o.word(0xD3A6), m[P+2], m[P+3], m[0xD29A], m[0xD3B1]],
           [0 if owns else owner, 30 if owns else 23, flags | 1 if owns else flags, rings, 37])
        if owns:
            eq('bounce', [o.word(P+22), o.word(P+24), m[P+34]],
               [256 if side & 8 else 0xFF00, 256 if floor & 1 else 0xFC00, floor & ~2])
        if owns and flags == 2 and not floor and not side:
            bounce_examples.append(dict(rings_bcd=rings, requested=m[P+2], flags=m[P+3], immunity_ticks=m[0xD3B1]))
    samples['bounce'] = bounce_examples

    # Full hurt gate inside4C12, including zero rings versus ring loss and
    # existing immunity/invincibility. Different from the direct bounce.
    for rings, flags, selector in itertools.product((0, 1, 0x99), (0, 64, 128, 192), (0, 6)):
        o = fixture(raw)
        m = o.mem
        m[0xD29A], m[P+3], m[0xD532], m[0xD3B0], m[0xD3B1] = rings, flags, selector, 1, 37
        events = trace_call(o, 0x4C12)
        hurt = not flags & 192 and selector != 6
        eq('hurt_gate', o.word(0xD3A6), 0 if hurt else S)
        eq('hurt_gate', m[P+2], (30 if rings else 31) if hurt else 23)
        eq('hurt_gate', m[0xD29A], 0 if hurt and rings else rings)
        eq('hurt_gate', 0x45ED in [e['pc'] for e in events], hurt)

    # A cleared/deleted/reused owner slot is NOT validated by4C56/4C12.
    # Use RAM slots, including a zero slot; do not generalise arbitrary ROM
    # addresses to safe or recoverable behavior.
    invalid = []
    for owner_type in (0, 0xFE, 0xFF, 0x28):
        o = fixture(raw)
        m = o.mem
        m[S] = owner_type
        trace_call(o, 0x4C12)
        eq('invalid_owner', [o.word(0xD3A6), m[P+2], o.word(P+17), o.word(P+20)], [S, 23, 1000, 100])
        invalid.append(dict(slot_type=owner_type, retained_owner=True, copied_integer_position=[1000, 100]))
    samples['invalid_owner'] = invalid

    # Capture clears the token field, not its occupancy byte. Generic removal
    # later distinguishes token-backed FE from tokenless FF, without touching
    # D3A6. Original5EF8 clears the slot on its later scheduler visit.
    lifecycle = []
    for token in (0, 17):
        o = fixture(raw)
        m = o.mem
        o.cpu.ix = S
        m[S+62] = token
        m[0xD410] = 255
        o.word(0xD174, 2000)
        o.word(0xD176, 2000)
        o.call(0x61E1)
        eq('lifecycle', [m[S], bool(m[S+4] & 64), o.word(0xD3A6), m[0xD410]],
           [0xFE if token else 0xFF, True, S, 255])
        if token:
            o.call(0x626D)
            eq('lifecycle', [m[S], m[0xD410]], [255, 255])
        o.call(0x5EF8)
        eq('lifecycle', [list(m[S:S+64]), m[0xD410], o.word(0xD3A6)],
           [list(bytes(64)), 0 if token else 255, S])
        o.cpu.ix, o.cpu.iy = P, S
        m[P+16], m[P+19] = 11, 22
        trace_call(o, 0x4C12)
        eq('lifecycle', [o.word(P+17), o.word(P+20), m[P+16], m[P+19],
                         o.word(P+22), o.word(P+24), o.word(0xD3A6)], [0, 0, 11, 22, 0, 0, S])
        lifecycle.append(dict(token=token, removal_type=0xFE if token else 0xFF,
                              occupancy_after_cleanup=0 if token else 255,
                              stale_owner_retained=True, cleared_owner_copy=[0, 0, 0, 0]))
    samples['lifecycle'] = lifecycle

    for state, hurt, cooldown in itertools.product((14, 22, 23), (0, 64), (0, 1, 16)):
        o = fixture(raw)
        m = o.mem
        o.bank(2, 12)
        o.cpu.ix, o.cpu.iy = S, P
        o.position(1000, 84)
        m[P+1] = m[P+2] = state
        m[P+3] = 3
        m[S+3], m[S+31], m[S+62] = hurt, cooldown, 17
        m[0xD410] = 255
        o.word(0xD3A6, 0)
        o.call(0xA741)
        remaining = (cooldown-1)&255 if hurt and state != 23 else cooldown
        blocked = state == 23 or bool(hurt and remaining)
        eq('capture_cooldown', [m[S+31], m[S+3], o.word(0xD3A6), m[P+2], m[P+3]],
           [remaining, hurt if state == 23 else (64 if hurt and remaining else 0), 0 if blocked else S,
            state if blocked else 22, 3 if blocked else 0])
    o = fixture(raw)
    m = o.mem
    o.bank(2, 12)
    o.cpu.ix, o.cpu.iy = S, P
    o.position(1000, 84)
    m[P+1] = m[P+2] = 14
    m[S+4], m[S+62] = 0, 17
    m[0xD410] = 255
    o.call(0xA5D8)
    eq('capture_token', [m[P+2], o.word(0xD3A6), m[S+2], o.word(S+24), m[S+62], m[0xD410]],
       [22, S, 2, 1024, 0, 255])

    # Callback path sweeps use original terrain lookup, not a mocked block
    # lookup. Floor/marker flags are boundary fixtures, explicitly distinct
    # from a naturally arriving player/actor.
    obstacles = list(raw[0x32786:0x3278C])
    continuation = list(raw[0x32777:0x32786])
    for state, block, grounded in itertools.product((2, 3), range(256), (False, True)):
        o = fixture(raw)
        m = o.mem
        m[0xC001:0xD000] = bytes([block])*4095
        m[S+34] = 2 if grounded else 0
        o.word(S+22, 512 if state == 2 else -512)
        o.bank(2, 12)
        o.cpu.ix, o.cpu.iy = S, P
        events = trace_call(o, 0xA5F7 if state == 2 else 0xA63A,
                            (0xA741, 0xA734, 0xA6D7))
        obstacle = block in obstacles
        eq('motion_paths', [e['pc'] for e in events],
           ([0xA6D7] if obstacle and grounded else []) if obstacle else
           ([0xA741, 0xA734] if grounded else [0xA741]))
        eq('motion_paths', m[S+2], 5 if obstacle and grounded else (2 if grounded else 4))
        if not grounded:
            eq('motion_paths', [o.word(S+22), o.word(S+24)], [528 if state == 2 else 65008, 256])
    for marker, vy in itertools.product(range(256), (0xFF00, 0, 0x05DF, 0x05E0, 0x05FF, 0x0600)):
        o = fixture(raw)
        m = o.mem
        m[S+34] = 2
        m[S+62] = 17
        m[0xD410] = 255
        m[0xD36E] = marker
        o.word(S+24, vy)
        o.bank(2, 12)
        o.cpu.ix, o.cpu.iy = S, P
        trace_call(o, 0xA691)
        keep = marker in continuation
        eq('continuation', [m[S+2], o.word(S+24), m[S+62], m[0xD410]],
           [2, 1024, 0, 255] if keep else [5, 0xFC00, 17, 255])
        eq('continuation', o.word(0xD3A6), S if keep else 0)
    o = fixture(raw)
    m = o.mem
    o.bank(2, 12)
    o.cpu.ix = S
    m[S+4] = 64
    before = bytes(m[S:S+64])
    o.call(0xA5D8)
    eq('sleep', bytes(m[S:S+64]), before)
    for state, cb, gravity in ((4, 0xA691, 32), (5, 0xA716, 64)):
        for vy in (0xFF00, 0, 0x05BF, 0x05C0, 0x05DF, 0x05E0, 0x05FF, 0x0600):
            o = fixture(raw)
            m = o.mem
            m[S+34] = 0
            m[S+4] = 64  # these callbacks deliberately have no asleep gate
            o.word(S+24, vy)
            o.bank(2, 12)
            o.cpu.ix, o.cpu.iy = S, P
            trace_call(o, cb)
            new_v = R.s16(vy)+gravity
            expected_v = new_v if new_v < 1536 else R.s16(vy)
            eq('gravity_sleep', [o.word(S+24), o.word(S+20), m[S+19]],
               [expected_v & 65535, (100*256+expected_v)//256, (100*256+expected_v)&255])
    o = fixture(raw)
    m = o.mem
    o.bank(2, 12)
    o.cpu.ix = S
    m[S+34] = 2
    o.call(0xA716)
    eq('cleanup', m[S+2], 6)
    m[S+62], m[S+63] = 17, 2
    for _ in range(16):
        o.call(0xA72B)
        eq('cleanup', [m[S], m[S+62], m[S+63]], [23, 0, 0])
    o.call(0x0362)
    eq('cleanup', m[S], 255)

    # Original ring probe while attached at a natural EEZ1 ring quadrant.
    manifest = json.loads((F.OUT/'implementation-manifest.json').read_text())
    a = manifest['acts']['eez1']
    ring = a['rings']['terrain'][0]
    ring_samples = []
    for parity in (0, 1):
        o = fixture(raw)
        m = o.mem
        m[0xC001:0xD000] = bytes(a['layout']['rows'][i//128][i%128] for i in range(4095))
        m[0xD162] = a['descriptor']['header']['layout_bank']
        m[P+7] = parity
        x, y = ring['world_x'], ring['world_y'] + (8 if parity == 0 else -2)
        o.word(S+17, x)
        o.word(S+20, y)
        events = trace_call(o, 0x4C12)
        eq('terrain_ring', [e['pc'] for e in events[:4]], [0x4C56, 0x753E, 0x48BC, 0x401A])
        eq('terrain_ring', m[0xD29A], 1)
        eq('terrain_ring', o.word(0xD3A6), S)
        ring_samples.append(dict(parity=parity, owner_integer=[x, y], collected_rings=m[0xD29A]))
    samples['terrain_ring'] = ring_samples

    census = json.loads((F.OUT / 'object-census.json').read_text())
    placements = [dict(act=act, index=r['index'], world=[r['world_x'], r['world_y']],
                       parameter=r['parameter'], rom=r['rom_offset'], record=r)
                  for act, data in census['acts'].items() for r in data['records'] if r['type_id'] == '0x17']
    eq('placements', [sum(p['act'] == 'eez'+str(a) for p in placements) for a in (1, 2, 3)], [2, 2, 1])
    samples['placements'] = [{k: v for k, v in p.items() if k != 'record'} for p in placements]
    return dict(assertions=sum(checks.values()), groups=checks, samples=samples,
                method='original ROM routines; RAM boundary fixtures; breakpoint entry observations; no patched ROM code',
                limits='Controlled routine results. Natural-placement scheduler replay is a separate cache. Arbitrary non-RAM owner pointers and input-only whole-act traversal are not claimed.')
