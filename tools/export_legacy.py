"""Export verified placement fields and loop lookup samples from the supplied SMS ROM."""
import argparse, csv, hashlib, json
from pathlib import Path

EXPECTED_SHA256 = 'eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607'

def export(rom_path, output):
    rom = Path(rom_path).read_bytes()
    digest = hashlib.sha256(rom).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError('ROM hash differs from the researched image; offsets are version-specific.')
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    pos = 0x705AE
    while rom[pos] != 0xFF:
        b = rom[pos:pos+9]
        x, y = int.from_bytes(b[1:3], 'little'), int.from_bytes(b[3:5], 'little')
        rows.append(dict(index=len(rows)+1, rom_offset=f'{pos:05X}', type_id=f'{b[0]:02X}',
                         stored_x=x, stored_y=y, world_x=(x-256)&65535, world_y=(y-256)&65535,
                         flags=f'{b[5]:02X}', parameter=f'{b[6]:02X}', aux0=f'{b[7]:02X}', aux1=f'{b[8]:02X}'))
        pos += 9
    assert len(rows) == 53 and pos == 0x7078B
    with (out/'thz1_objects.csv').open('w', newline='') as f:
        writer=csv.DictWriter(f, fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
    platforms=[]
    for row in rows:
        if row['type_id']!='28': continue
        subtype=int(row['parameter'],16)
        p=dict(row)
        if subtype==0x0A:
            travel=16*int(row['aux1'],16)
            p.update(behavior='vertical oscillator', pixels_per_active_update=1,
                     initial_direction='up', updates_per_leg=travel,
                     min_y=row['world_y']-travel, max_y=row['world_y'])
        elif subtype==0x84:
            p.update(behavior='stationary platform with rider sag', max_sag_pixels=8)
        platforms.append(p)
    (out/'thz1_platforms.json').write_text(json.dumps(platforms,indent=2)+'\n')
    for name, ybase, xbase, limit in [('loop_right',0x34000,0x34398,0x180),
                                     ('loop_left',0x346AE,0x34A46,0x180),
                                     ('loop_alternate_exit',0x34DDC,0x35140,0x1A0)]:
        # Include index zero through the exit threshold. Original velocity may skip
        # samples and overshoot this threshold before exiting; these are not
        # claimed to be the complete backing arrays.
        with (out/(name+'.csv')).open('w', newline='') as f:
            w=csv.writer(f);w.writerow(['path_index','dx_pixels','dy_pixels'])
            for i in range(limit+1):
                x=int.from_bytes(rom[xbase+i*2:xbase+i*2+2],'little',signed=True)
                y=int.from_bytes(rom[ybase+i*2:ybase+i*2+2],'little',signed=True)
                w.writerow([i,x,y])
    return dict(rom_sha256=digest, object_count=len(rows), platform_count=len(platforms),
                object_terminator=f'{pos:05X}')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom');p.add_argument('--output',default='decoded')
    args=p.parse_args();print(json.dumps(export(args.rom,args.output),indent=2))
