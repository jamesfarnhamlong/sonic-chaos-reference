"""Sonic Chaos SMS tile-stream decompression helpers.

The decoder reproduces the raw 32-byte tile buffer produced by the original
Tile_Loading_Routines before the optional $0100 lookup remap used by some
graphics loads.

Python 3.10+.
"""

from typing import Tuple


def read_u16le(data: bytes, pos: int) -> int:
    if pos < 0 or pos + 2 > len(data):
        raise ValueError("truncated input while reading 16-bit value")
    return data[pos] | (data[pos + 1] << 8)


def extract_command(data: bytes, command_ptr: int, tile_index: int) -> int:
    """Return one packed 2-bit command, least-significant pair first."""
    if tile_index < 0:
        raise ValueError("negative tile index")
    pos = command_ptr + (tile_index // 4)
    if pos < 0 or pos >= len(data):
        raise ValueError("truncated command stream")
    shift = (tile_index % 4) * 2
    return (data[pos] >> shift) & 0x03


def _rr(value: int, carry_in: int) -> Tuple[int, int]:
    """Z80 RR: rotate right through carry; return (new value, carry out)."""
    carry_out = value & 0x01
    new_value = ((carry_in & 0x01) << 7) | (value >> 1)
    return new_value & 0xFF, carry_out


def _expand_sparse_tile(data: bytes, data_ptr: int) -> Tuple[bytearray, int]:
    """Reproduce the E,D,C,B bitmap expansion used by the ROM."""
    if data_ptr < 0 or data_ptr + 4 > len(data):
        raise ValueError("truncated sparse-tile bitmap")

    e = data[data_ptr]
    d = data[data_ptr + 1]
    c = data[data_ptr + 2]
    b = data[data_ptr + 3]
    data_ptr += 4

    tile = bytearray(32)
    for i in range(32):
        # The original path restores a clear carry before each RR chain.
        carry = 0
        b, carry = _rr(b, carry)
        c, carry = _rr(c, carry)
        d, carry = _rr(d, carry)
        e, carry = _rr(e, carry)

        if carry:
            if data_ptr >= len(data):
                raise ValueError("truncated sparse-tile payload")
            tile[i] = data[data_ptr]
            data_ptr += 1

    return tile, data_ptr


def _xor_reconstruct(tile: bytearray) -> None:
    """Apply the command-3 seven-step XOR reconstruction."""
    if len(tile) != 32:
        raise ValueError("XOR reconstruction requires exactly 32 bytes")

    for i in range(7):
        base = i * 2
        tile[base + 2] ^= tile[base]
        tile[base + 3] ^= tile[base + 1]
        tile[base + 18] ^= tile[base + 16]
        tile[base + 19] ^= tile[base + 17]


def decompress_tile_stream(data: bytes, offset: int = 0) -> bytes:
    """Decode one Sonic Chaos compressed tile stream.

    Header fields used by the original routine:
      +2/+3  little-endian tile count
      +4/+5  little-endian relative pointer to the packed command stream
      +6...  payload stream

    Command 0: output a zero/reference tile
    Command 1: copy one raw 32-byte tile
    Command 2: sparse bitmap expansion
    Command 3: sparse bitmap expansion plus XOR reconstruction
    """
    if offset < 0 or offset + 6 > len(data):
        raise ValueError("truncated tile-stream header")

    tile_count = read_u16le(data, offset + 2)
    command_offset = read_u16le(data, offset + 4)
    command_ptr = offset + command_offset
    data_ptr = offset + 6

    output = bytearray()

    for tile_index in range(tile_count):
        command = extract_command(data, command_ptr, tile_index)

        if command == 0:
            tile = bytearray(32)

        elif command == 1:
            if data_ptr + 32 > len(data):
                raise ValueError("truncated raw tile")
            tile = bytearray(data[data_ptr:data_ptr + 32])
            data_ptr += 32

        elif command in (2, 3):
            tile, data_ptr = _expand_sparse_tile(data, data_ptr)
            if command == 3:
                _xor_reconstruct(tile)

        else:
            raise AssertionError("unreachable 2-bit command")

        output.extend(tile)

    return bytes(output)


def apply_rom_remap(tile_bytes: bytes, rom: bytes) -> bytes:
    """Apply the optional $0100-$01FF byte lookup used when load bit 7 is set."""
    if len(rom) < 0x200:
        raise ValueError("ROM too small for $0100 lookup table")
    table = rom[0x100:0x200]
    return bytes(table[value] for value in tile_bytes)
