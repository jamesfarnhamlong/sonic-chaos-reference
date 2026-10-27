"""SCSP v1 exact two-byte $83 pitch-data exception, no language changes.

Legacy validator/decoder remain untouched. The loader recognises one exact,
source-pinned DATA record; it never makes that region a stream or code reader.
"""
import hashlib
import json
import struct
import zlib
from m5a2 import bank as legacy
from m5a2c2.decoder import Decoder as AcceptedDecoder
from m5a2.decoder import DecodeError

PAIR_ADDRESS=0x4634
PAIR_SHA256='adcafa4fcf2eff3e3fe49e504aa73303b8b0ea5c89162703717a90cfaf0f1b2e'
HEADER_SHA256='307b8461133deabd7649dceeb62547d785440e2f748bb9e5558731dd502b5272'
PROGRAM_SHA256='882ed37dc8bce866f990a14017d1385d2304805c39deaed287a7b2200bd28ddb'
canonical=legacy.canonical
def sha(b):return hashlib.sha256(b).hexdigest()
pack=legacy.pack

def validate_program(bank):
    if sha(canonical(bank['programs'].get('131')))!=PROGRAM_SHA256:
        raise DecodeError('two-byte pitch record requires exact authenticated83 header')

def unpack(blob):
    # Bounded outer validation before examining any private segment. All ordinary
    # SCSP schema, pointer, source, length, ordering and region checks remain owned
    # by the unchanged validator below.
    try:
        if len(blob)<45 or len(blob)>legacy.MAX_BYTES or blob[:8]!=legacy.MAGIC:
            raise DecodeError('invalid SCSP header/length')
        size,=struct.unpack_from('<I',blob,8)
        if not 0<size<=legacy.MAX_BYTES:raise DecodeError('unpacked size exceeds bound')
        z=zlib.decompressobj();raw=z.decompress(blob[12:-32],size+1)
        if len(raw)!=size or not z.eof or z.unused_data or z.unconsumed_tail or sha(raw)!=blob[-32:].hex():
            raise DecodeError('invalid SCSP compressed length/checksum')
        meta=json.loads(raw);special=[];ordinary=[];previous_end=0
        for s in meta['segments']:
            p,n=s['address'],s['length']
            if type(p)is not int or type(n)is not int or n<=0 or p<previous_end:
                raise DecodeError('overlap/truncated record')
            previous_end=p+n
            if p==PAIR_ADDRESS:
                b=bytes.fromhex(s['hex'])
                if n!=2 or len(b)!=2 or s['sha256']!=PAIR_SHA256 or sha(b)!=PAIR_SHA256:
                    raise DecodeError('pitch DATA pair source authentication failed')
                special.append(b)
            else:ordinary.append(s)
        if not special:return legacy.unpack(blob)
        if len(special)!=1:raise DecodeError('duplicate pitch pair')
        validate_program(meta)
        meta['segments']=ordinary;raw=canonical(meta)
        checked=legacy.unpack(legacy.MAGIC+struct.pack('<I',len(raw))+zlib.compress(raw,9)+hashlib.sha256(raw).digest())
        checked['data'].update({str(PAIR_ADDRESS+i):v for i,v in enumerate(special[0])})
        return checked
    except (KeyError,TypeError,ValueError,OverflowError,zlib.error) as e:
        if isinstance(e,DecodeError):raise
        raise DecodeError('malformed SCSP83 contract') from e

class Decoder(AcceptedDecoder):
    def __init__(self,bank,horizon=None):
        self._reader=None;self._in_command=False;self._pair_access=False
        if any(str(p) in bank['data'] for p in (PAIR_ADDRESS,PAIR_ADDRESS+1)):
            validate_program(bank)
            try:b=bytes(bank['data'][str(p)] for p in (PAIR_ADDRESS,PAIR_ADDRESS+1))
            except KeyError:raise DecodeError('truncated pitch DATA pair') from None
            if sha(b)!=PAIR_SHA256:raise DecodeError('pitch DATA pair source authentication failed')
        super().__init__(bank,horizon)

    def read(self,i):
        prior=self._reader;self._reader=i
        try:return super().read(i)
        finally:self._reader=prior

    def command(self,i,op,p):
        prior=self._in_command;self._in_command=True
        try:return super().command(i,op,p)
        finally:self._in_command=prior

    def word(self,p):
        if p!=PAIR_ADDRESS:return super().word(p)
        # Only inherited ordinary note-table lookup in $83 music tone1. Calls,
        # branches, raw reads, envelope/pitch-modulation and other owners have no
        # permission. Arithmetic remains entirely in the accepted reader.
        if self._reader!=1 or self._in_command or self.owners[1]!=0x83 or self.ch[1][5]!=247 or self.ch[1][0]&8:
            raise DecodeError('pitch DATA pair outside authenticated83 note-reader scope')
        self._pair_access=True
        try:return super().word(p)
        finally:self._pair_access=False

    def byte(self,p):
        if PAIR_ADDRESS<=p<=PAIR_ADDRESS+1 and not self._pair_access:
            raise DecodeError('pitch DATA pair is not stream-accessible')
        return super().byte(p)
