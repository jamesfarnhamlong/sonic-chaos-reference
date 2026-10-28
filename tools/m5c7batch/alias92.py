"""Exact92 music-tone2 F7 index4 permission; original byte43 stays aliased RAM.

Only the authenticated source command at87C1, no active call frame. No extra
counter array, clearing on return/restart, or global loop-index change.
"""
from m5a2c2.decoder import Decoder as Accepted
from m5a2.decoder import DecodeError
from m5a2.bank import canonical
import hashlib
def sha(b):return hashlib.sha256(b).hexdigest()
HEADER='30a4d25c5450cb3126e22d170b27fd8e17ef315b06716eb052a6cf5b8896920f'
COMMAND='49cbae1e90de16843ae3bede06d2565c0e7d7c1849c630c27e4e0760fb3595e3'
PROGRAM='543cf37c84ee11c1f51c7f4cc0a2b7e341d6e69f3d5494dcbefd59d500f34f5a'

class Decoder(Accepted):
    def command(self,i,op,p):
        if op!=0xF7 or self.byte(p)<=2:return super().command(i,op,p)
        c=self.ch[i]
        if i!=2 or self.owners[i]!=0x92 or c[1]!=0xC0 or p!=0x87C2 or self.byte(p)!=4 or c[9]!=48:
            raise DecodeError('92 alias outside exact owner/command/inactive-stack scope')
        if self.bank['programs'].get('146',{}).get('header_sha256')!=HEADER or sha(canonical(self.bank['programs'].get('146')))!=PROGRAM:
            raise DecodeError('92 alias header not authenticated')
        if sha(bytes(self.byte(q) for q in range(p-1,p+4)))!=COMMAND:
            raise DecodeError('92 alias command not authenticated')
        self.ops+=1;self.opcodes[op]=self.opcodes.get(op,0)+1
        if not c[43]:c[43]=self.byte(p+1)
        c[43]=(c[43]-1)&255
        if c[43]:
            q=self.word(p+2);self.loops.append((self.tick_number,i,p-1,q));return q
        return p+4
