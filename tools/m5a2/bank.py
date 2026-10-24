"""SCSP v1 private data container: bounded zlib JSON records, no executable code."""
import hashlib
import json
import struct
import zlib
from decoder import DecodeError

MAGIC = b'SCSP\x01\r\n\x1a'
MAX_BYTES = 256 * 1024
ROM_HASH = 'eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607'


def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':')).encode()


def digest(x):
    return hashlib.sha256(x).hexdigest()


def records(bank):
    meta = {k: v for k, v in bank.items() if k != 'data'}
    segments = []
    for address in sorted(map(int, bank['data'])):
        value = bank['data'][str(address)]
        if segments and segments[-1][0] + len(segments[-1][1]) == address:
            segments[-1][1].append(value)
        else:
            segments.append([address, bytearray([value])])
    meta['segments'] = [dict(address=p, length=len(b), sha256=digest(b), hex=b.hex()) for p, b in segments]
    return meta


def pack(bank):
    raw = canonical(records(bank))
    if len(raw) > MAX_BYTES: raise DecodeError('bank too large')
    return MAGIC + struct.pack('<I', len(raw)) + zlib.compress(raw, 9) + hashlib.sha256(raw).digest()


def unpack(blob):
    if len(blob) < 45 or blob[:8] != MAGIC or len(blob) > MAX_BYTES:
        raise DecodeError('invalid SCSP header/length')
    size, = struct.unpack_from('<I', blob, 8)
    if not 0 < size <= MAX_BYTES: raise DecodeError('unpacked size exceeds bound')
    try:
        z = zlib.decompressobj()
        raw = z.decompress(blob[12:-32], size + 1)
        if len(raw) != size or not z.eof or z.unused_data or z.unconsumed_tail:
            raise DecodeError('invalid compressed length')
        if hashlib.sha256(raw).digest() != blob[-32:]: raise DecodeError('bank checksum mismatch')
        meta = json.loads(raw)
        if meta['version'] != 1 or meta['source_sha256'] != ROM_HASH:
            raise DecodeError('wrong source/version')
        if type(meta['horizon']) is not int or not 0 < meta['horizon'] <= 4200:
            raise DecodeError('unsupported bank horizon')
        data = {}
        previous_end = 0
        for segment in meta.pop('segments'):
            p, n = segment['address'], segment['length']
            b = bytes.fromhex(segment['hex'])
            if type(p) is not int or p < previous_end or n != len(b) or not n:
                raise DecodeError('overlap/truncated record')
            if not (0x4436 <= p and p+n <= 0x44C2 or 0x48AC <= p and p+n <= 0xC000):
                raise DecodeError('record crosses data region')
            if digest(b) != segment['sha256']: raise DecodeError('record hash mismatch')
            data.update((str(p+j), v) for j, v in enumerate(b))
            previous_end = p+n
        for key, pr in meta['priority'].items():
            if not 0 <= int(key) <= 255 or type(pr) is not int or not 0 <= pr <= 255:
                raise DecodeError('invalid priority')
        for key, program in meta['programs'].items():
            rid = int(key)
            if not 0x81 <= rid <= 0xC4: raise DecodeError('invalid program ID')
            streams = program['streams']
            if not 1 <= len(streams) <= (4 if rid < 0xA0 else 3):
                raise DecodeError('invalid channel count')
            expected = 6 + 4*len(streams) if rid < 0xA0 else 4 + 6*len(streams)
            if program['header_length'] != expected or len(program['header_sha256']) != 64:
                raise DecodeError('invalid source header receipt')
            for field in ('multiplier', 'tempo'):
                if type(program[field]) is not int or not 0 <= program[field] <= 255:
                    raise DecodeError('invalid initialization')
            if program['multiplier']==0:
                raise DecodeError('unverified zero duration multiplier')
            for i, s in enumerate(streams):
                if str(s['pointer']) not in data: raise DecodeError('stream start not extracted')
                valid_latch = s['latch'] == 0x80+32*i if rid < 0xA0 else s['latch'] in (0xA0,0xC0,0xE0)
                if not valid_latch:
                    raise DecodeError('invalid channel latch')
                if any(type(s[f]) is not int or not 0 <= s[f] <= 255 for f in ('volume','flags')):
                    raise DecodeError('invalid stream initialization')
                if type(s['transpose']) is not int or not -128<=s['transpose']<=255:
                    raise DecodeError('invalid transpose')
        meta['data'] = data
        return meta
    except (KeyError, TypeError, OverflowError, zlib.error, ValueError) as e:
        if isinstance(e, DecodeError): raise
        raise DecodeError('malformed bank') from e
