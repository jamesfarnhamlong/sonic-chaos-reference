#!/usr/bin/env python3
"""Build the bounded player-state $11 and THZ1 discrepancy fixture report."""
from __future__ import annotations

import argparse, hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from oracle import Oracle

SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
PLACEMENTS = [(656,846,0x06),(1712,494,0x06),(336,270,0x04),(1472,110,0x04),(2688,686,0x02)]
SURFACES = [864,512,288,128,864]

def s16(v): return v - 0x10000 if v & 0x8000 else v

def state11_call(rom, input_bits=0, vx=0, vy=0, timer=300, x=1000, y=700):
    o=Oracle(rom); o.position(x,y); o.mem[0xD501]=o.mem[0xD502]=0x11
    o.mem[0xD503]=0; o.mem[0xD504]=0; o.mem[0xD137]=input_bits
    o.word(0xD51C,100)
    o.word(0xD516,vx); o.word(0xD518,vy); o.word(0xD44C,timer)
    o.word(0xD373,0x700); o.mem[0xD52C]=9; o.mem[0xD52D]=18
    o.call(0x3A7C)
    return {"input":f"0x{input_bits:02X}","x":o.word(0xD511),"y":o.word(0xD514),
            "vx":s16(o.word(0xD516)),"vy":s16(o.word(0xD518)),
            "requested_state":f"0x{o.mem[0xD502]:02X}","flags":f"0x{o.mem[0xD503]:02X}",
            "sound":f"0x{o.mem[0xDE04]:02X}","timer":o.word(0xD44C)}

def acceleration_call(rom, input_bits, vy):
    o=Oracle(rom); o.mem[0xD137]=input_bits; o.word(0xD518,vy); o.call(0x3AC1)
    return {"input":f"0x{input_bits:02X}","before":s16(vy),"after":s16(o.word(0xD518))}

def state11_entry(rom):
    o=Oracle(rom); o.mem[0xD501]=1; o.mem[0xD502]=1
    o.word(0xD516,0x234); o.word(0xD518,0xFEDC); o.mem[0xD503]=0x42
    # Level $08 bypasses the interrupt-wait call, which the subroutine oracle
    # intentionally does not emulate. All state-entry writes are shared; only
    # the documented timer/sound fork differs from ordinary THZ1.
    o.mem[0xD297]=8; o.word(0xD44C,300); o.call(0x4775)
    return {"vx":s16(o.word(0xD516)),"vy":s16(o.word(0xD518)),"maximum":o.word(0xD373),
            "timer_copy":o.word(0xD3A1),"requested_state":f"0x{o.mem[0xD502]:02X}",
            "flags":f"0x{o.mem[0xD503]:02X}","sound":f"0x{o.mem[0xDE04]:02X}",
            "fixture_level":"0x08 (interrupt-free shared entry path)"}

def overlap(rom, dx, dy, attack=0, power=0):
    o=Oracle(rom); o.cpu.ix=0xD700; o.mem[0xD700]=0x21
    o.word(0xD711,500); o.word(0xD714,500); o.mem[0xD72C]=11; o.mem[0xD72D]=26
    o.word(0xD511,500+dx); o.word(0xD514,500+dy); o.mem[0xD52C]=9; o.mem[0xD52D]=18
    o.mem[0xD503]=attack; o.mem[0xD532]=power; o.call(0x6328)
    bits=o.mem[0xD721]&15
    return {"dx":dx,"dy":dy,"bits":f"0x{bits:02X}","overlap":bool(bits)}

def spike_samples(rom):
    o=Oracle(rom); rows=[]
    for x in (1504,1536,2208,2240):
        for lx in (0,1,15,16,30,31):
            for ly in (14,15,16,17,30,31):
                s=o.collision_sample(x+lx,832+ly-18)
                rows.append({"cell_x":x,"local_x":lx,"local_y":ly,"tile":f"0x{s['tile']:02X}",
                    "flags":f"0x{s['flags']:02X}","vertical":s["vertical"],"horizontal":s["horizontal"]})
    return rows

def build(rom):
    if hashlib.sha256(rom).hexdigest()!=SHA256: raise ValueError("ROM SHA-256 mismatch")
    anchors=[]
    for (x,y,p),surface in zip(PLACEMENTS,SURFACES):
        anchors.append({"x":x,"y":y,"parameter":f"0x{p:02X}","surface_y":surface,
            "sprite_top":y-24,"sprite_bottom":y+7,"empty_rows_to_surface":surface-(y+7)-1})
    boundary=[overlap(rom,dx,dy) for dx,dy in [(-21,0),(-20,0),(-19,0),(19,0),(20,0),(21,0),
        (0,-27),(0,-26),(0,-25),(0,17),(0,18),(0,19),(20,-4),(20,-3),(0,-4),(0,-3)]]
    return {"format":1,"rom_sha256":SHA256,
      "type_10_vertical":{"renderer_cpu":"0x226A","placements":anchors,
        "contract":"SAT_Y=(object_y-camera_y)+signed_piece_y; displayed scanline is SAT_Y+1"},
      "player_state_11":{"script_cpu":"0x8334","script_rom":"0x30334","callback_cpu":"0x3A7C",
        "script":[{"duration":8,"frame":"0x38"},{"duration":4,"frame":"0x39"},
                  {"duration":8,"frame":"0x3A"},{"duration":4,"frame":"0x39"}],
        "fixtures":{"entry":state11_entry(rom),"neutral":state11_call(rom,vx=0x100),
          "left":state11_call(rom,1),"right":state11_call(rom,2),
          "expiry":state11_call(rom,timer=0),"acceleration":[acceleration_call(rom,0,0x100),
            acceleration_call(rom,0,0xFF00),acceleration_call(rom,1,0),
            acceleration_call(rom,2,0),acceleration_call(rom,1,0xFD00),
            acceleration_call(rom,2,0x0300)]}},
      "static_spikes":{"block":"0x3D","header_flags":"0x85","floor_profile":[16]*32,
        "side_profile":[64]*16+[96]*16,"samples":spike_samples(rom)},
      "type_21_contact":{"player_extents":{"x":9,"y":18},"object_extents":{"x":11,"y":26},
        "helper_cpu":"0x6328","boundaries":boundary,
        "contract":"overlap abs(dx)<=20 and -26<=dy<=18; helper retains the minimum-penetration axis in object+$21; local type-$21 code treats any nonzero result as contact"}}

def main():
    p=argparse.ArgumentParser();p.add_argument("rom",type=Path);p.add_argument("--metadata",type=Path)
    a=p.parse_args(); report=build(a.rom.read_bytes())
    if a.metadata:
        a.metadata.parent.mkdir(parents=True,exist_ok=True);a.metadata.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"fixtures":len(report["type_21_contact"]["boundaries"])+len(report["static_spikes"]["samples"])+11}))
if __name__=="__main__": main()
