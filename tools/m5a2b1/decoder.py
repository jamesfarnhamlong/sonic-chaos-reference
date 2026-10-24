"""A2B1 narrowly extends the accepted interpreter with authenticated E1."""
from m5a2.decoder import Decoder as AcceptedDecoder


class Decoder(AcceptedDecoder):
    def command(self,i,op,p):
        if op==0xE1:
            # Original CPU $487E..$4881: LD (IX+$25),A; RET.
            # Signed addition is already performed at $4504..$450D.
            self.ch[i][37]=self.byte(p)
            self.ops+=1
            self.opcodes[op]=self.opcodes.get(op,0)+1
            return p+1
        return super().command(i,op,p)
