"""Readable translations of a bounded, tested subset of Chaos collision code.

Addresses are ROM CPU addresses with bank 1 mapped. Integer masking is intentional.
This is a research reference, not a complete game/player implementation.
"""
from rom import header, s16

def lookup(rom, tiles, x, y, dx=0, dy=0, plane=0):
    # $7666: 16-bit arithmetic; the lookup adds 18 to the object's Y anchor.
    ax = (x+dx) & 65535
    ay = (y+dy+18) & 65535
    if ay & 32768:
        ay = 0
    # Three left shifts retain only the low eight tile-column bits.
    column = (ax >> 5) & 255
    row = (ay >> 5) & 127  # table index doubles in the 8-bit A register
    pointer = (0xc001 + row*128 + column) & 65535
    if pointer & 0xf000 != 0xc000:
        return dict(tile=255, map_address=0xcfff, x=ax, y=ay,
                    flags=0, modifier=None, vertical=0, horizontal=0)
    tile = tiles[pointer-0xc001]
    h = header(rom, tile, plane)
    return dict(tile=tile, map_address=pointer, x=ax, y=ay, flags=h['flags'],
                modifier=h['modifier'], vertical=h['vertical'][ax & 31],
                horizontal=h['horizontal'][ay & 31])

def above_projection(rom, tiles, sample, player_y, plane=0):
    """$7056, for probes whose above-map address remains inside C001..CFFF."""
    address = sample['map_address']-128
    if not 0xc001 <= address < 0xd000:
        raise ValueError('Above-map probe outside this translation fixture')
    h = header(rom, tiles[address-0xc001], plane)
    v = h['vertical'][sample['x'] & 31] & 63
    modifier = sample['modifier']
    raw = sample['vertical']
    if h['flags'] & 64:
        if h['flags'] & 31 != 9 and v:
            raw = (v+32) & 255
    elif h['flags'] & 128:
        modifier = h['modifier']
        if v:
            player_y = (player_y-v) & 65535
    return player_y, raw, modifier

def project_floor(rom, tiles, sample, player_y, vy, previous_flags,
                  collision_flags=0, plane=0):
    """$6F61 ordinary path, IX+$24 bits 0/1 clear; includes $7056.

    Returns Y, background flags, surface modifier, and possibly extended profile.
    $691A supplies previous_flags from D36C, not the just-fetched D364.
    """
    raw = sample['vertical']; modifier = sample['modifier']
    applied_modifier = 0
    if not previous_flags & 0xc0 or vy & 0x8000:
        return player_y, collision_flags, applied_modifier, raw
    solid = bool(previous_flags & 128)
    if (solid and raw & 63 == 32) or (not solid and raw & 63 == 0):
        player_y, raw, modifier = above_projection(rom, tiles, sample, player_y, plane)
    if not solid:
        collision_flags &= ~2
    value = raw
    if solid:
        if raw & 64 and previous_flags & 31 == 28:
            value = 32
        value &= 63
    total = (value + (sample['y'] & 31)) & 255
    if total >= 32:
        correction = total-32
        limit = ((vy >> 8)+9) & 255
        if solid or correction < limit:
            player_y = (player_y-correction) & 65535
            collision_flags |= 2
            applied_modifier = modifier
    return player_y, collision_flags, applied_modifier, raw

def project_side(x, adjusted_x, surface_flags, raw, side):
    """Normal side-projection cores $71B2/$7257; specials excluded.

    side='right' tests x+9 and moves left; side='left' tests x-9 and moves right.
    """
    if not surface_flags & 128 or not raw & 63:
        return x, 0
    value = raw & 63
    local = adjusted_x & 31
    if side == 'right':
        if raw & 64:
            boundary = (((adjusted_x+32) & 65535) & 0xffe0)-value
            delta = adjusted_x-boundary
            if delta < 0:
                return x, 0
        else:
            if local >= value:
                return x, 0
            delta = local
        return (x-delta) & 65535, 4
    if side != 'left':
        raise ValueError(side)
    if raw & 64:
        delta = ((((adjusted_x+32) & 65535) & 0xffe0)-1)-adjusted_x
        if delta < 0 or delta >= value:
            return x, 0
    else:
        if local >= value:
            return x, 0
        delta = value-local-1
    return (x+delta) & 65535, 8

def angle_velocity(rom, angle, magnitude):
    """$6089: signed sine-table sample times magnitude, arithmetic shift by 4."""
    def component(index):
        sample = rom[0x200+(index & 255)]
        if sample & 128:
            sample -= 256
        return s16(sample*magnitude) >> 4
    return component(angle), component(angle+0xc0)
