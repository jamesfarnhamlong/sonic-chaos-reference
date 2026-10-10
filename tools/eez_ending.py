"""Complete long ending scripts without the shared reconnaissance 80-op cap."""
import argparse
import eez_foundation as F
import level_package as L
import mghz_object_census as C
from oracle import Oracle

def build(r):
    scripts={}
    for t in (1,2,21,22,31,34):
        sc=C.state_scripts(r,t)
        if t in (1,2):sc['states']=[s for s in sc['states'] if s['state'] in ((49,50,51) if t==2 else (49,51))]
        for st in sc['states']:
            # Local extension keeps earlier committed research caches unchanged.
            previous=C.CMD_LEN.get(10);C.CMD_LEN[10]=3
            try:ops,ok=C.decode_script(r,sc['bank'],st['script_cpu'],stop_cpu=st['bounded_by_cpu'],limit=512)
            finally:
                if previous is None:del C.CMD_LEN[10]
                else:C.CMD_LEN[10]=previous
            for op in ops:
                if op.get('command')==10:
                    off=L.bank_cpu_to_rom(sc['bank'],op['cpu'])
                    op.update(op='write_absolute_byte',address=L.u16(r,off+2),value=r[off+4])
            st['ops']=ops;st['cleanly_terminated']=ok
            assert ok,(t,st['state'])
        sc['frames']=sorted({x['frame'] for s in sc['states'] for x in s['ops'] if x['op']=='record'})
        sc['callbacks']=sorted({x['callback'] for s in sc['states'] for x in s['ops'] if 'callback' in x})
        sc['calls']=sorted({x['target'] for s in sc['states'] for x in s['ops'] if x['op'] in ('call','call_and_set_callback')})
        scripts[f'0x{t:02X}']=C.public_script(sc)
    o=Oracle(r);m=o.mem;checks=0;S=0xD700
    for address in (0xD3C1,0xD526,0xD766):
        for value in range(256):
            o.bank(2,12);m[0xD12B]=12;o.cpu.ix=S;m[S:S+64]=bytes(64);m[S]=22;o.word(S+14,0xDA00)
            m[0xDA00:0xDA07]=bytes((address&255,address>>8,value,224,0,47,3));m[address]=value^255
            o.call(0x6841)
            assert m[address]==value and o.word(S+14)==0xDA07;checks+=1
    return dict(rom_sha256=L.ROM_SHA256,scripts=scripts,assertions=checks,command10=dict(cpu=0x6841,operand_bytes=3,semantics='write absolute RAM byte then process next script record; creditsD3C1FF releases Tails49->50; type16 ending writesD526FF, releases Tails50->51'),
        source_regions=[F.A.source(r,12,0x84D4,0x880A),F.A.source(r,12,0x8D36,0x8E1F),F.A.source(r,12,0xA3B6,0xA582),F.A.source(r,12,0xAEC3,0xB0C0),F.A.source(r,12,0xB2F9,0xB3D9),F.A.source(r,0,0x18ED,0x1C28),F.A.source(r,0,0x6841,0x6857)],
        scope='Original ending actors15/1F/22 and Sonic states31/33. Full script durations/loops/velocities retained; no visual identities inferred. 31 has more than80 operations and needs limit512, not truncated reconnaissance. Terminal routine traces prove both Sonic branches returntitle; not input-only play.',
        visual_evidence='Original controlled scene samples preserve complete raster hashes, SAT and CRAM in boss-game-* caches. Sonic sixflags branch visibly shows CAST/GAME DESIGN/SOUND/THANKS TO and final END.; partial branch differs and uses34D3 timed TRY AGAIN scene. Other-character branch1ACD initializes Tails type2/state31, thenoriginal loop reaches title. Approval boards are approximate-harness observations, not Windows approval.',
        validation_limits='Individual visible contributor strings have not been transcribed; do not invent names or replace original ending art. Scene loading addresses are source-traced; original raster/SAT snapshots remain reproducible local-only pixels.')

def main():
    p=argparse.ArgumentParser();p.add_argument('rom');a=p.parse_args();v=build(L.load_rom(a.rom));(F.OUT/'ending-scripts.json').write_text(F.dumps(v),encoding='utf-8');print({k:sum(len(s['ops']) for s in v['states']) for k,v in v['scripts'].items()})

if __name__=='__main__':main()
