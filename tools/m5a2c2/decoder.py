"""Minimal FD extension, bounded to the authenticated SFX tone2 reader class."""
from m5a2b1.decoder import Decoder as AcceptedDecoder
from m5a2.decoder import DecodeError


class Decoder(AcceptedDecoder):
    def command(self,i,op,p):
        if op==0xFD:
            # CPU $47BA..$47C7 changes only bit3: operand1 sets; all others clear.
            # $46E7 loads the operand; $46E9 consumes it after handler return.
            if i!=5 or self.ch[i][1]!=0xC0:
                raise DecodeError('FD reader transition outside verified SFX tone2 scope')
            a=self.byte(p)
            self.ch[i][0]=self.ch[i][0]|8 if a==1 else self.ch[i][0]&~8
            self.ops+=1;self.opcodes[op]=self.opcodes.get(op,0)+1
            return p+1
        return super().command(i,op,p)
