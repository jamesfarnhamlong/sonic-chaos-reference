"""Reassemble every recovered region and compare the reconstructed ROM byte for byte.

Unrecovered gaps are preserved with INCBIN. This validates recovered assembly
bytes, not semantic annotations. The caller supplies the original ROM locally.
"""
import argparse, hashlib, json, shutil, subprocess
from pathlib import Path
from rom import load, SHA256

def verify(rom_path, output, wla, linker):
    rom=load(rom_path)
    if output.exists():raise ValueError('Build directory must be new')
    output.mkdir(parents=True)
    source=Path(__file__).resolve().parents[1]/'asm'/'recovered'
    regions=json.loads((source/'regions.json').read_text())
    shutil.copytree(source,output/'recovered')
    (output/'input.sms').write_bytes(rom)
    lines=['.MEMORYMAP','SLOTSIZE $4000','SLOT 0 $0000','SLOT 1 $4000',
           'SLOT 2 $8000','DEFAULTSLOT 2','.ENDME','.ROMBANKMAP',
           'BANKSTOTAL 32','BANKSIZE $4000','BANKS 32','.ENDRO']
    for bank in range(32):
        slot=0 if bank==0 else 1 if bank in (1,2) else 2
        lines.extend([f'.BANK {bank} SLOT {slot}', '.ORG 0'])
        cursor=bank*0x4000
        for region in (r for r in regions if r['bank']==bank):
            if region['start']<cursor:raise ValueError('Overlapping recovered ranges')
            if region['start']>cursor:
                lines.append(f'.incbin "input.sms" SKIP ${cursor:X} READ ${region["start"]-cursor:X}')
            lines.append(f'.include "recovered/{region["file"]}"')
            cursor=region['end']
        if cursor<(bank+1)*0x4000:
            lines.append(f'.incbin "input.sms" SKIP ${cursor:X} READ ${(bank+1)*0x4000-cursor:X}')
    (output/'research.asm').write_text('\n'.join(lines)+'\n')
    (output/'link.txt').write_text('[objects]\nresearch.o\n')
    subprocess.run([wla,'-o','research.o','research.asm'],cwd=output,check=True)
    subprocess.run([linker,'-r','-s','link.txt','research.sms'],cwd=output,check=True)
    built=(output/'research.sms').read_bytes()
    if built!=rom:
        offset=next((i for i,(a,b) in enumerate(zip(built,rom)) if a!=b),min(len(built),len(rom)))
        raise ValueError(f'Rebuild differs at ${offset:05X}')
    result=dict(byte_identical=True,rom_bytes=len(rom),sha256=hashlib.sha256(built).hexdigest(),
                recovered_regions=len(regions),recovered_bytes=sum(r['bytes'] for r in regions),
                decoded_instructions=sum(r['instructions'] for r in regions),
                meaning='Exact assembly-byte verification; unrecovered gaps use supplied ROM bytes.')
    (output/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom')
    p.add_argument('--output',type=Path,default=Path('build'))
    p.add_argument('--wla-z80',default='wla-z80');p.add_argument('--wlalink',default='wlalink')
    a=p.parse_args();print(json.dumps(verify(a.rom,a.output,a.wla_z80,a.wlalink),indent=2))
