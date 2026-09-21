"""Version-specific ROM primitives. No ROM is distributed with this project."""
from pathlib import Path
import hashlib

SHA256 = 'eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607'

def load(path):
    data = Path(path).read_bytes()
    if len(data) != 524288 or hashlib.sha256(data).hexdigest() != SHA256:
        raise ValueError('Expected the documented Sonic Chaos SMS research ROM; see docs/provenance.md.')
    return data

def u16(data, offset):
    return int.from_bytes(data[offset:offset+2], 'little')

def s16(n):
    return (n + 32768) % 65536 - 32768

def header(rom, tile, plane=0, table=0x38000):
    address = 0x30000 + u16(rom, table + tile*2)
    if rom[address] & 0x20 and plane:
        address += 7
    vp = 0x30000 + u16(rom, address+2)
    hp = 0x30000 + u16(rom, address+4)
    return dict(tile=tile, plane=int(bool(plane)), address=address,
                flags=rom[address], modifier=rom[address+1],
                vertical_pointer=vp, horizontal_pointer=hp,
                vertical=list(rom[vp:vp+32]), horizontal=list(rom[hp:hp+32]),
                trailing_byte=rom[address+6])

def layout(rom):
    """THZ1 runtime map: loader $4DC4 stops at D000 after 4095 output bytes.

    The complete compressed stream encodes 4096 cells; the engine's RAM bound
    prevents the final one being written. Preserve that distinction.
    """
    result = []
    pos = 0x48000
    while len(result) < 4095:
        value = rom[pos]; pos += 1
        if value == 255:
            value, count = rom[pos:pos+2]; pos += 2
            if not count:
                break
            result.extend([value] * min(count,4095-len(result)))
        else:
            result.append(value)
    if len(result) != 4095:
        raise ValueError(f'Unexpected THZ1 decoded length: {len(result)}')
    return result
