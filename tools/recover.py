"""Recover selected code and explicitly identified tables from the checked ROM."""
import argparse, json, re
from pathlib import Path
from z80dis import z80
from rom import load

# End offsets are exclusive. Code/data are classified explicitly: exploratory
# linear-disassembly output is deliberately not treated as annotated source.
REGIONS = [
 ('side_sensors',0x3686,0x36c6,'code'),
 ('rolling_and_ramp_states',0x38c5,0x3901,'code'),
 ('spring_state_updates',0x393b,0x396d,'code'),
 ('movement_core',0x401a,0x429d,'code'),
 ('movement_tables',0x429d,0x45b3,'data'),
 ('standing_walk_setters',0x45b3,0x45ed,'code'),
 ('player_state_setters',0x45ed,0x4775,'code'),
 ('ramp_state_setters',0x47dc,0x480c,'code'),
 ('bounded_layout_decoder',0x4dc4,0x4dfc,'code'),
 ('angle_and_position',0x6089,0x613c,'code'),
 ('merge_collision_flags',0x64cb,0x64f0,'code'),
 ('terrain_update',0x690b,0x6973,'code'),
 ('floor_dispatch_table',0x6973,0x69b1,'data'),
 ('ramp_contact',0x69b1,0x6a5b,'code'),
 ('floor_projection',0x6f61,0x715e,'code'),
 ('side_collision',0x715e,0x73c9,'code'),
 ('ceiling_collision',0x73c9,0x753e,'code'),
 ('collision_lookup',0x7666,0x77cb,'code'),
 ('object_floor_update',0x77cb,0x77ed,'code'),
 ('object_floor_dispatch',0x77ed,0x782b,'data'),
 ('object_floor_handlers',0x782b,0x7857,'code'),
 ('breakable_handlers',0x7857,0x78e1,'code'),
 ('twist_dispatch',0x314c1,0x314f5,'code'),
 ('twist_tables',0x314f5,0x315dd,'data'),
 ('twist_handlers',0x315dd,0x3182a,'code'),
 ('spike_object_scripts',0x32c4a,0x32c7d,'data'),
 ('spike_object_handlers',0x32c7d,0x32d59,'code'),
 # Previously recovered regions retained where they do not overlap the above.
 ('loop_states',0x3c1b,0x3efd,'code'),
 ('spring_setters',0x480c,0x4892,'code'),
 ('spring_contacts',0x6a75,0x6ace,'code'),
 ('loop_contacts',0x6cba,0x6ce5,'code'),
 ('twist_entry',0x6e56,0x6f61,'code'),
 ('platform_reverse',0x780f1,0x78105,'code'),
 ('object_26_scripts',0x78212,0x7825a,'data'),
 ('object_26_handlers',0x7825a,0x783b3,'code'),
 ('object_26_span_scripts',0x783b3,0x783bf,'data'),
 ('object_26_span_handlers',0x783bf,0x78439,'code'),
 ('platform_code',0x78577,0x78947,'code'),
]

COMMENTS = {
0x3686:'Default side probes: (-9,-12) and (+9,-12); lookup adds +18 to Y.',
0x38d1:'Ramp-launch state $1B update wrapper; state scripts use vector $03C8.',
0x393b:'Vertical spring update: shared movement, then landing/apex state decisions.',
0x3955:'Diagonal spring update: shared movement; on apex requests falling.',
0x402a:'Integrate signed 8.8 horizontal velocity, input delta and surface delta into 16.8 X.',
0x403b:'Combined contact bit 2 blocks movement to the right.',
0x4052:'Combined contact bit 3 blocks movement to the left.',
0x408d:'Blocked movement clears velocity and input delta.',
0x4097:'Vertical integration. Airborne flag is IX+$03 bit 0.',
0x40ca:'Dry airborne gravity: state $0B +$18; $1B +$24; other states +$30.',
0x40ea:'Water path halves those increments; downward terminal velocity is +4.',
0x410b:'Grounded/background floor bit forces +7 Y motion, or +9 for modifiers $0A/$0C.',
0x4141:'Input/state-dependent speed deltas and modifier-table lookup.',
0x41b8:'D369 is a BYTE OFFSET into signed 16-bit table at $459D.',
0x4223:'No-direction friction uses table $439D. $451D is not selected by this branch.',
0x429d:'Six 32-state arrays of two 16-bit values, followed by 11 signed surface modifiers.',
0x45b3:'Request standing state $01; clear airborne/rolling, zero X velocity, set max X=4.',
0x45ed:'Normal jump requests state $0A and Y=-4.25 (dry) or -3.25 (water).',
0x463c:'Falling setter requests state $0E and sets Y velocity to +1.0; normal-jump state is exempt.',
0x47fb:'Request ramp-launch state $1B; set airborne and rolling; clear ground contact.',
0x4dc4:'RLE loop. DE starts at C001; stop when it leaves C000..CFFF, even inside a run.',
0x4dfb:'Decoder exit; next instructions initialize level rendering. Not a standalone RET.',
0x6089:'angle byte IX+$0A and magnitude byte IX+$0B -> signed 8.8 velocity.',
0x60a0:'Signed table at $0200; multiply sample by magnitude, arithmetic shift right four.',
0x60c8:'Y uses the same table with angle+$C0, wrapping to 8 bits.',
0x60fb:'Integrate velocities into object 16.8 positions; preserve subpixels.',
0x64cb:'Merge background flags (+$22) with selected object-contact flags (+$21) into +$23.',
0x690b:'Shared collision order: floor, sides, ceiling, top special probe, merge.',
0x691a:'Save previous modifier, clear current modifier; foot probe at dx=0,dy=0 normally.',
0x694f:'Lookup uses current centre X and Y+18, with state-specific Y offsets above.',
0x695b:'Floor projection runs BEFORE D36C is replaced by the newly sampled surface type.',
0x6964:'Dispatch using current surface type AND $1F.',
0x6973:'31 handler pointers for low-five-bit surface types $00..$1E.',
0x69b2:'Surface type $12 ramp behavior; upward motion returns without applying it.',
0x69b7:'Previous modifier D36A controls launch versus initial-roll path.',
0x69ea:'Initial-roll path: tile $1F or tile >=$22 adds -4 X; other tile IDs add +4.',
0x6a18:'Rightward ramp launch sets Y velocity to -(X + floor(X/2)); request $1B.',
0x6a3b:'Leftward path takes magnitude first, then applies the same upward launch formula.',
0x6f61:'Use PREVIOUS surface type D36C to select solid / one-way projection.',
0x6f72:'The profile magnitude uses AND $3F: values 33..63 are not invalid heights.',
0x6f99:'Solid Y correction = (profile & 63) + (adjustedY & 31) - 32, when nonnegative.',
0x6fbb:'One-way branch; IX+$24 bits 0/1 select special subpaths (not in Python subset).',
0x6fdf:'One-way correction must be strictly less than unsigned high-byte(vy)+9.',
0x7056:'Look up the tile one map row above. May project Y or extend the profile.',
0x7079:'Dual header: bit 5 plus nonzero object+$25 selects the header seven bytes later.',
0x70c3:'Above-tile bit 6 branch: extend low-six-bit value by 32, except subtype 9.',
0x70e7:'Generic object floor projection; different one-way tolerance (+7).',
0x715e:'Clear side contacts, test right (+9,+6 effective), then left (-9,+6 effective).',
0x71b2:'Right-side ordinary projection: require surface bit 7; use HORIZONTAL profile D367.',
0x71cf:'Horizontal profile bit 6 chooses boundary measured from the right edge.',
0x7210:'Left-side probe uses D498/D49A offsets initialized at $3686.',
0x7257:'Left-side ordinary projection; low six bits are extent, bit 6 selects orientation.',
0x72b6:'Breakable side handler checks rolling and X-speed before changing map data.',
0x73a7:'Tile $A1 can clear collision plane object+$25; early unwind of right-side check.',
0x73b8:'Tile $A2 can set collision plane object+$25; early unwind of left-side check.',
0x73c9:'Ceiling centre probe uses dy=-24, effective Y-6 after lookup anchor adjustment.',
0x7464:'Ceiling breakable handler; routes to map modification at $7898.',
0x7666:'Full collision lookup; temporarily maps bank 14 into $8000..$BFFF.',
0x7690:'Add 18 to the player anchor Y; clamp a negative signed result to zero.',
0x76af:'Use row-stride pointer D168, then base C001; reject outside C000..CFFF.',
0x76d2:'Collision header pointer table comes from D2E0 (THZ: CPU $8000 in bank 14).',
0x76df:'Surface bit 5 plus object plane +$25 chooses alternate seven-byte header.',
0x76fb:'Index first profile by adjusted X & 31 -> D368 (vertical projection).',
0x770e:'Index second profile by adjusted Y & 31 -> D367 (horizontal projection).',
0x7725:'Lightweight lookup reads only base surface type; does not select the alternate header.',
0x77b0:'Outside map: tile $FF, surface/profile values zero; D100 modifier is not cleared here.',
0x77cb:'Generic object floor update; useful for enemy grounding, not the player routine.',
0x7857:'Changes the collided map block to $46, refreshes mapping and spawns debris.',
0x7898:'Changes the collided map block to $9D, refreshes mapping and spawns four fragments.',
0x314c1:'Twist state $22: damage check, floor update, validate type, table dispatch.',
0x314f5:'Four table pointers, then four tables of 28 handler pointers for tiles $58..$73.',
0x315dd:'After tile handler: angle-to-velocity conversion then position integration.',
0x315f1:'Original LD ($0000),A falls through. ROM write has no effect on an SMS.',
0x3174d:'RET at this address makes the following two INC instructions unreachable via this entry.',
0x31755:'Decrease magnitude by one; if below $10 select variant 2.',
0x31763:'Increase magnitude by two below $A0; preserve wrapping arithmetic.',
0x31772:'RET at this entry: do not translate the following subtraction as active behavior.',
0x3179f:'Y alignment using (Y-16)&~31, then +46.',
0x317b8:'Sonic Y alignment: ((Y-32)&~31)+46; alternate character branch differs.',
0x31812:'X low-byte alignment to tile boundary +22; high byte is preserved.',
0x32c4a:'Object type $1B has five state-script pointers; THZ1 places four parameter-zero instances.',
0x32c7d:'Initialize retracting spikes: request state 1 and clear the hit cooldown.',
0x32c8b:'Rising state: damage/contact helper, then move Y up six pixels to an 18-pixel limit.',
0x32ccc:'Retracting state: move Y down six pixels to the saved base, then request hidden state 4.',
0x32cfd:'Spike contact helper; hit cooldown is object+$1F.',
0x78212:'Object type $26 state-script table and scripts for fixed and span variants.',
0x7825a:'Initialize object $26; parameter bit 7 selects a low-seven-bit times 16 trigger span.',
0x782af:'Fixed concealed spring contact: top contact selects -7.375 or -5.0 and states 1/3.',
0x78312:'Strong spring extension: counter -7 and Y -7; hold state 2 starts at 32.',
0x7833a:'Strong extended-state counter requests retract state 5.',
0x78349:'Shared spring retraction: Y +7 to saved base, then restore saved rest state.',
0x7837c:'Weak spring extension; hold state 4 starts at 10.',
0x783a4:'Weak extended-state counter requests retract state 6.',
0x783bf:'Span state 8: check a saved X interval before requesting activation state 9.',
0x78401:'Span activation aligns object X to the player on a 16-pixel boundary and launches.',
}

def generate(rom_path, output):
    rom=load(rom_path);output.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for name,start,end,kind in sorted(REGIONS,key=lambda x:x[1]):
        assert start//0x4000 == (end-1)//0x4000, name
        bank=start//0x4000
        base=0 if bank==0 else 0x4000 if bank in (1,2) else 0x8000
        lines=[f'; {name}: ROM ${start:05X}..${end-1:05X} (end exclusive ${end:05X}).',
               '; Original Sonic Chaos instructions/data. See docs/provenance.md.',
               '; Generated deterministically by tools/recover.py. Semantic coverage varies.','']
        instructions=[];p=start
        if kind=='code':
            while p<end:
                pc=base+p%0x4000;d=z80.decode(rom[p:p+4],pc)
                if not d.len or p+d.len>end:raise ValueError((name,hex(p),'bad boundary'))
                instructions.append((p,pc,z80.disasm(d)));p+=d.len
            labels={pc:f'SC_{addr:05X}' for addr,pc,_ in instructions}
            for addr,pc,assembly in instructions:
                if addr in COMMENTS:lines.append('; '+COMMENTS[addr])
                lines.append(f'SC_{addr:05X}:')
                if assembly.startswith(('JR ','DJNZ ')):
                    match=re.search(r'0x([0-9a-f]+)$',assembly)
                    target=int(match.group(1),16)
                    # All recovered JR/DJNZ destinations must be decoded labels.
                    if target not in labels:raise ValueError((name,hex(addr),assembly))
                    assembly=assembly[:match.start()]+labels[target]
                assembly=re.sub(r'0x([0-9a-f]+)',lambda m:'$'+m.group(1).upper(),assembly)
                assembly=assembly.replace('(IX)','(IX+0)').replace('(IY)','(IY+0)')
                lines.append('    '+assembly)
        else:
            if start in COMMENTS:lines.append('; '+COMMENTS[start])
            for p in range(start,end,16):
                lines.append(f'SC_{p:05X}:')
                lines.append('    .db '+', '.join(f'${b:02X}' for b in rom[p:min(p+16,end)]))
        (output/(name+'.asm')).write_text('\n'.join(lines)+'\n')
        manifest.append(dict(name=name,start=start,end=end,bank=bank,kind=kind,
                             bytes=end-start,instructions=len(instructions),file=name+'.asm'))
    (output/'regions.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom')
    p.add_argument('--output',type=Path,default=Path('asm/recovered'))
    a=p.parse_args();m=generate(a.rom,a.output)
    print(json.dumps(dict(regions=len(m),bytes=sum(x['bytes'] for x in m),
                          instructions=sum(x['instructions'] for x in m))))
