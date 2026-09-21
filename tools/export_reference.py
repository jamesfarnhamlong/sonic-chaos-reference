"""Export collision headers, movement parameters, dispatch tables and sound pointers."""
import argparse, csv, json
from pathlib import Path
from rom import load, header, layout, u16, s16, SHA256
from export_legacy import export as export_legacy

def csv_write(path, rows):
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)

def export(path, output):
    rom=load(path);output.mkdir(parents=True,exist_ok=True)
    headers=[]
    for tile in range(256):
        h=header(rom,tile);headers.append(h)
        if h['flags']&32:headers.append(header(rom,tile,1))
    (output/'thz-collision-headers.json').write_text(json.dumps(headers,indent=2)+'\n')
    tiles=layout(rom)
    (output/'thz1-layout.json').write_text(json.dumps(tiles)+'\n')
    csv_write(output/'zone-collision-pointers.csv',[
        dict(level=level,act=act,act_header_file=f'{u16(rom,u16(rom,0x2a9a+level*2)+act*2):05X}',
             collision_table_cpu=f'{u16(rom,u16(rom,u16(rom,0x2a9a+level*2)+act*2)):04X}')
        for level in range(6) for act in range(3)])
    csv_write(output/'thz-collision-index.csv',[
        dict(tile_hex=f'{h["tile"]:02X}',plane=h['plane'],header_file=f'{h["address"]:05X}',
             flags_hex=f'{h["flags"]:02X}',modifier_offset=h['modifier'],
             vertical_file=f'{h["vertical_pointer"]:05X}',horizontal_file=f'{h["horizontal_pointer"]:05X}',
             vertical_min=min(h['vertical']),vertical_max=max(h['vertical'])) for h in headers])
    tables=[('dry_nonnegative',0x429d),('dry_negative',0x431d),('no_direction',0x439d),
            ('water_nonnegative',0x441d),('water_negative',0x449d),('not_selected_by_4141',0x451d)]
    csv_write(output/'movement-tables.csv',[
        dict(table=name,state_hex=f'{state:02X}',file_offset=f'{base+state*4:05X}',
             first_8_8=s16(u16(rom,base+state*4)),second_8_8=s16(u16(rom,base+state*4+2)))
        for name,base in tables for state in range(32)])
    csv_write(output/'surface-modifiers.csv',[
        dict(byte_offset=i,file_offset=f'{0x459d+i:05X}',delta_8_8=s16(u16(rom,0x459d+i)),
             delta_pixels=s16(u16(rom,0x459d+i))/256) for i in range(0,22,2)])
    csv_write(output/'floor-dispatch.csv',[
        dict(type_hex=f'{i:02X}',handler_cpu=f'{u16(rom,0x6973+i*2):04X}') for i in range(31)])
    rows=[]
    for variant in range(4):
        table=u16(rom,0x314f5+variant*2)
        for tile in range(0x58,0x74):
            pos=0x28000+table+(tile-0x58)*2
            target=u16(rom,pos)
            rows.append(dict(variant=variant,tile_hex=f'{tile:02X}',table_cpu=f'{table:04X}',
                             pointer_file=f'{pos:05X}',handler_cpu=f'{target:04X}',handler_file=f'{target+0x28000:05X}'))
    csv_write(output/'twist-dispatch.csv',rows)
    csv_write(output/'sonic-state-scripts.csv',[
        dict(state_hex=f'{i:02X}',script_cpu=f'{u16(rom,0x30000+i*2):04X}',
             script_file=f'{u16(rom,0x30000+i*2)+0x28000:05X}') for i in range(61)])
    # User-supplied SMS 1.2 index, independently checked against the ROM table.
    supplied = (
        '9169 963F 9793 9CE8 9EB2 9F7A A005 A0A5 A152 A1E1 A23D A948 AF69 '
        'B634 B6C4 B8EB BEF6 C3DD C8B6 CFDD D206 D7DC D881 D91C D991 DBCA '
        'DE54 DE6E DE88 DEA2 DEBC DED6 DF05 DF1B DF42 DF6D DFAC DFC4 DFF5 '
        'E00B E04B E079 E08C E0A5 E0D4 E0EC E10F E132 E150 E16B E193 E1B9 '
        'E1E1 E1FC E22E E24C E267 E29B E2DD E30D E330 E358 E376 E391 E3B4 '
        'E3CC E40C E434'
    )
    expected = [int(value,16) for value in supplied.split()]
    rows=[]
    for i in range(68):
        pointer=u16(rom,0x90e1+i*2);offset=pointer+0x4000
        assert offset==expected[i],(hex(0x81+i),hex(offset),hex(expected[i]))
        rows.append(dict(id_hex=f'{0x81+i:02X}',pointer_file=f'{0x90e1+i*2:05X}',
                         stored_address=f'{pointer:04X}',file_offset=f'{offset:05X}',
                         header_word=f'{u16(rom,offset):04X}',
                         reported_class='music' if 0x81+i<0xa0 else 'sfx'))
    csv_write(output/'sound-index-sms.csv',rows)
    legacy=export_legacy(path,output/'legacy')
    summary=dict(rom_sha256=SHA256,collision_headers=len(headers),base_tiles=256,
                 layout_bytes=len(tiles),layout_base_ram='C001',sound_pointers_verified=68,
                 twist_dispatch_entries=112,state_script_pointers=61,legacy=legacy)
    (output/'manifest.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom')
    p.add_argument('--output',type=Path,default=Path('data'));a=p.parse_args()
    print(json.dumps(export(a.rom,a.output),indent=2))
