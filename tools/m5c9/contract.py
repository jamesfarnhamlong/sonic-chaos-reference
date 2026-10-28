"""Per-programme exact pitch-DATA permission; legacy SCSP and decoder unchanged."""
import hashlib
import json
from pathlib import Path
import struct
import zlib
from m5a2 import bank as legacy
from m5a2c2.decoder import Decoder as Accepted
from m5a2.decoder import DecodeError
canonical=legacy.canonical
pack=legacy.pack
def sha(b):return hashlib.sha256(b).hexdigest()
POLICY=Path(__file__).resolve().parents[2]/'data/m5-c9/reader-policy.json'
def policies():return json.loads(POLICY.read_text())
def identify(bank):
    candidates=[(int(k,16),v) for k,v in policies().items() if str(int(k,16)) in bank['programs']]
    if len(candidates)!=1:raise DecodeError('C9 bank requires exactly one assigned programme')
    rid,policy=candidates[0]
    if sha(canonical(bank['programs'][str(rid)]))!=policy['programme_sha256']:
        raise DecodeError('C9 programme metadata not authenticated')
    return rid,policy

def unpack(blob):
    try:
        if len(blob)<45 or len(blob)>legacy.MAX_BYTES or blob[:8]!=legacy.MAGIC:raise DecodeError('invalid SCSP header/length')
        size,=struct.unpack_from('<I',blob,8)
        if not 0<size<=legacy.MAX_BYTES:raise DecodeError('unpacked size exceeds bound')
        z=zlib.decompressobj();raw=z.decompress(blob[12:-32],size+1)
        if len(raw)!=size or not z.eof or z.unused_data or z.unconsumed_tail or sha(raw)!=blob[-32:].hex():raise DecodeError('invalid SCSP compressed length/checksum')
        meta=json.loads(raw);rid,policy=identify(meta);special={};ordinary=[];previous_end=0
        for s in meta['segments']:
            p,n=s['address'],s['length']
            if type(p)is not int or type(n)is not int or n<=0 or p<previous_end:raise DecodeError('overlap/truncated record')
            previous_end=p+n
            if 0x4630<=p<0x4636:
                data=bytes.fromhex(s['hex'])
                if p%2 or n%2 or p+n>0x4636 or len(data)!=n or sha(data)!=s['sha256']:raise DecodeError('invalid pitch DATA segment')
                for j in range(0,n,2):
                    if sha(data[j:j+2])!=policy['pair_hashes'].get(str(p+j)):raise DecodeError('pitch DATA pair not authenticated for programme')
                special.update({str(p+j):v for j,v in enumerate(data)})
            else:ordinary.append(s)
        if not special:return legacy.unpack(blob)
        meta['segments']=ordinary;raw=canonical(meta)
        checked=legacy.unpack(legacy.MAGIC+struct.pack('<I',len(raw))+zlib.compress(raw,9)+hashlib.sha256(raw).digest())
        checked['data'].update(special);return checked
    except (KeyError,TypeError,ValueError,OverflowError,zlib.error) as e:
        raise DecodeError('malformed C9 SCSP: '+str(e)) from e

class Decoder(Accepted):
    def __init__(self,bank,horizon=None):
        self.rid,self.policy=identify(bank);self._reader=None;self._command=False;self._pair=False
        for p in range(0x4630,0x4636,2):
            if any(str(q) in bank['data'] for q in (p,p+1)):
                try:pair=bytes(bank['data'][str(q)] for q in (p,p+1))
                except KeyError:raise DecodeError('truncated C9 pitch pair') from None
                if sha(pair)!=self.policy['pair_hashes'].get(str(p)):raise DecodeError('C9 pitch pair source hash mismatch')
        super().__init__(bank,horizon)
    def read(self,i):
        prior=self._reader;self._reader=i
        try:return super().read(i)
        finally:self._reader=prior
    def command(self,i,op,p):
        prior=self._command;self._command=True
        try:return super().command(i,op,p)
        finally:self._command=prior
    def word(self,p):
        if not 0x4630<=p<0x4636:return super().word(p)
        i=self._reader
        if i is None or self._command or self.owners[i]!=self.rid or self.ch[i][0]&8 or [i,self.ch[i][5],p,(p-0x4436)//2] not in self.policy['reader_scopes']:
            raise DecodeError('C9 pitch pair outside exact owner/note-reader scope')
        self._pair=True
        try:return super().word(p)
        finally:self._pair=False
    def byte(self,p):
        if 0x4630<=p<0x4636 and not self._pair:raise DecodeError('C9 pitch pair not stream-accessible')
        return super().byte(p)
