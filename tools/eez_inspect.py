"""Local linear disassembly reconnaissance; output is not annotated canonical code."""
import argparse
from z80dis import z80
import rom

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom');p.add_argument('regions',nargs='+',help='bank:start:end (hex)')
    a=p.parse_args();r=rom.load(a.rom)
    for region in a.regions:
        bank,start,end=(int(x,16) for x in region.split(':'))
        print('REGION',region)
        while start<end:
            off=start if bank==0 else bank*0x4000+start-0x8000
            d=z80.decode(r[off:off+4],start)
            print(f'{start:04X}',z80.disasm(d));start+=d.len

if __name__=='__main__':main()
