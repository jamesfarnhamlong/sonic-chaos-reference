#!/usr/bin/env python3
"""Build the ROM-backed Rocket Shoes / Spring Shoes audit cache.

The output contains decoded records and bounded routine results, never ROM bytes.
Human-facing names are kept beside the numeric identities rather than replacing
them: type $10 parameter $04 and mapped type $2F are the canonical keys.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from oracle import Oracle
import level_package as levels
import thz1_object_10 as object10
import thz1_object_09 as object09
import terrain_ring_collection as terrain_rings

ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
OUTPUT = ROOT / "data" / "rom-cache" / "powerup-shoes.json"
ZONE_NAMES = (
    "Turquoise Hill", "Gigalopolis", "Sleeping Egg",
    "Mecha Green Hill", "Aqua Planet", "Electric Egg",
)


def hx(v: int, n: int = 4) -> str:
    return f"0x{v:0{n}X}"


def s16(v: int) -> int:
    return v - 0x10000 if v & 0x8000 else v


def routine(rom: bytes, start: int, end: int) -> dict:
    payload = rom[start:end]
    bank, cpu = levels.rom_to_bank_cpu(start)
    return {
        "rom": hx(start, 5), "end_exclusive": hx(end, 5),
        "bank": hx(bank, 2), "cpu": hx(cpu), "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "first_16_bytes": payload[:16].hex().upper(),
    }


def placement_census(rom: bytes) -> dict:
    acts = []
    rockets = []
    springs = []
    for zone, zone_name in enumerate(ZONE_NAMES):
        for act in range(3):
            ptr = levels.object_list_pointer(rom, zone, act)
            rows, terminator = levels.decode_object_list(rom, ptr["list_rom"])
            rr = [r for r in rows if r["type_id"] == "0x10" and r["parameter"] == "0x04"]
            ss = [r for r in rows if r["type_id"] == "0x2F"]
            key = f"zone_{zone}_act_{act + 1}"
            acts.append({
                "key": key, "name": f"{zone_name} Act {act + 1}",
                "zone": zone, "act": act, "list_rom": hx(ptr["list_rom"], 5),
                "terminator_rom": hx(terminator, 5),
                "rocket_shoes": len(rr), "spring_shoes": len(ss),
                "rocket_variant": "type $10 parameter $04" if rr else None,
                "spring_variant": "type $2F parameter $00" if ss else None,
                "same_movement_model": True,
            })
            for dst, selected in ((rockets, rr), (springs, ss)):
                for r in selected:
                    dst.append({
                        "act": key, "name": f"{zone_name} Act {act + 1}",
                        "rom_offset": r["rom_offset"], "type": r["type_id"],
                        "parameter": r["parameter"], "x": r["world_x"], "y": r["world_y"],
                        "flags": r["flags"], "aux0": r["aux0"], "aux1": r["aux1"],
                    })
    return {
        "acts": acts, "rocket_shoes": rockets, "spring_shoes": springs,
        "totals": {"rocket_shoes": len(rockets), "spring_shoes": len(springs)},
        "reuse": "All records use the same numeric type/parameter and code path. Spring Shoes use art-base aux bytes $94 in Sleeping Egg and $AC in Mecha Green Hill; that is a graphics-load/VRAM-base variant, not a movement variant.",
    }


def reward_fixture(rom: bytes) -> dict:
    o = Oracle(rom)
    o.mem[0x062D] = 0xC9  # fixture-only return in place of interrupt synchronization
    o.mem[0xD3A3] = 0x08
    o.mem[0xD500] = 1
    o.mem[0xD501] = o.mem[0xD502] = 5
    o.mem[0xD503] = 0x42
    o.mem[0xD297] = 0
    o.word(0xD516, 0x0123)
    o.word(0xD518, 0xFEDC)
    o.call(0x4AA3)
    return {
        "queued_after": hx(o.mem[0xD3A3], 2), "selector_d532": hx(o.mem[0xD532], 2),
        "timer_d44c": o.word(0xD44C), "duration_copy_d3a1": o.word(0xD3A1),
        "requested_state": hx(o.mem[0xD502], 2), "flags_d503": hx(o.mem[0xD503], 2),
        "vx": s16(o.word(0xD516)), "vy": s16(o.word(0xD518)),
        "maximum_d373": hx(o.word(0xD373)), "sound_de04": hx(o.mem[0xDE04], 2),
        "fixture_note": "ordinary-level path; fixture stubs only the interrupt synchronization call at $062D after sound $85 is written",
    }


def coexistence_fixtures(rom: bytes) -> dict:
    cases = []
    specs = (
        ("rocket_over_invincibility", 0x08, 6, 400, 5, 0x82),
        ("invincibility_over_rocket", 0x20, 4, 100, 0x11, 0),
        ("speed_up_over_rocket", 0x04, 4, 100, 0x11, 0),
        ("rocket_over_spring_shoes", 0x08, 0, 0, 0x12, 2),
    )
    for name, mask, selector, timer, state, flags in specs:
        o = Oracle(rom)
        o.mem[0x062D] = 0xC9
        o.mem[0xD500] = 1
        o.mem[0xD501] = o.mem[0xD502] = state
        o.mem[0xD503], o.mem[0xD532], o.mem[0xD3A3] = flags, selector, mask
        o.word(0xD44C, timer)
        o.call(0x4AA3)
        cases.append({"case": name, "selector": hx(o.mem[0xD532], 2), "timer": o.word(0xD44C),
                      "requested_state": hx(o.mem[0xD502], 2), "flags": hx(o.mem[0xD503], 2),
                      "sound": hx(o.mem[0xDE04], 2)})
    o = Oracle(rom)
    o.bank(2, 30); o.mem[0xD12B] = 30; o.cpu.ix = 0xD700
    o.mem[0xD700] = 0x2F; o.mem[0xD701] = o.mem[0xD702] = 1; o.mem[0xD703] = 0x80
    o.mem[0xD72C], o.mem[0xD72D] = 8, 16
    o.word(0xD711, 500); o.word(0xD714, 500); o.word(0xD511, 500); o.word(0xD514, 484)
    o.mem[0xD52C], o.mem[0xD52D] = 8, 24
    o.mem[0xD501] = o.mem[0xD502] = 0x11; o.mem[0xD532] = 4; o.word(0xD44C, 100)
    o.word(0xD518, 0x0100)
    o.call(0x8B64)
    cases.append({"case": "spring_shoes_over_rocket", "selector": hx(o.mem[0xD532], 2),
                  "timer": o.word(0xD44C), "requested_state": hx(o.mem[0xD502], 2),
                  "owner_d3a4": hx(o.word(0xD3A4)), "flags": hx(o.mem[0xD503], 2), "sound": hx(o.mem[0xDE04], 2)})
    return {"cases": len(cases), "rows": cases}


def vertical_sweep(rom: bytes) -> dict:
    rows = []
    for label, pad in (("neutral", 0), ("up", 1), ("down", 2)):
        for before in (0xFC00, 0xFC20, 0xFFE0, 0, 0x0020, 0x03C0, 0x0400):
            o = Oracle(rom)
            o.mem[0xD137] = pad
            o.word(0xD518, before)
            o.call(0x3AC1)
            rows.append({"input": label, "before": s16(before), "after": s16(o.word(0xD518))})
    return {
        "cases": len(rows), "rows": rows,
        "rule": "Up subtracts $0040 and clamps to -$0400; Down adds $0040 and clamps to +$0400. Neutral chooses +/-$0020 from the signed high byte, so fractional speeds cross zero and oscillate rather than clamping to zero.",
    }


def camera_sweep(rom: bytes) -> dict:
    rows = []
    for screen_y in (23, 24, 25, 191, 192, 193):
        o = Oracle(rom)
        o.word(0xD176, 1000)
        o.word(0xD51C, screen_y)
        o.word(0xD514, 1000 + screen_y)
        o.word(0xD518, 0x123)
        o.call(0x3B25)
        rows.append({"screen_y": screen_y, "world_y": o.word(0xD514), "vy": s16(o.word(0xD518))})
    return {"cases": len(rows), "rows": rows, "rule": "screen Y <24 -> cameraY+25; screen Y >=192 -> cameraY+191; velocity becomes zero"}


def rocket_termination_fixtures(rom: bytes) -> dict:
    expiry = []
    for timer in (1, 0):
        o = Oracle(rom)
        o.position(1000, 700)
        o.mem[0xD501] = o.mem[0xD502] = 0x11
        o.mem[0xD503] = 0
        o.word(0xD51C, 100)
        o.word(0xD44C, timer)
        o.word(0xD373, 0x0700)
        o.mem[0xD52C], o.mem[0xD52D] = 8, 24
        o.call(0x3A7C)
        expiry.append({"timer_entering_callback": timer, "requested_state": hx(o.mem[0xD502], 2),
                       "vy": s16(o.word(0xD518)), "flags": hx(o.mem[0xD503], 2),
                       "sound_or_music_request": hx(o.mem[0xDE04], 2)})
    damage = []
    for rings in (0, 10):
        o = Oracle(rom)
        o.mem[0x062D] = 0xC9  # fixture-only return in place of interrupt synchronization
        o.mem[0xD501] = o.mem[0xD502] = 0x11
        o.mem[0xD532], o.mem[0xD3A3], o.mem[0xD3B0], o.mem[0xD29A] = 4, 8, 0xFF, rings
        o.word(0xD44C, 300)
        o.call(0x48BC)
        damage.append({"rings_before": rings, "rings_after": o.mem[0xD29A],
                       "requested_state": hx(o.mem[0xD502], 2), "selector": hx(o.mem[0xD532], 2),
                       "queued_rewards": hx(o.mem[0xD3A3], 2), "vy": s16(o.word(0xD518)),
                       "flags": hx(o.mem[0xD503], 2), "sound": hx(o.mem[0xDE04], 2)})
    return {"cases": len(expiry) + len(damage), "expiry": expiry, "damage": damage,
            "damage_rule": "state $11 cancels selector/queued reward and enters hurt even with zero rings; it does not run ordinary ring loss/death selection"}


def ring_fixtures(rom: bytes) -> dict:
    type09 = []
    for state in (0x11, 0x12):
        for dx, dy in ((0, 0), (11, 11), (12, 0), (0, 12), (-12, 0)):
            o = object09._oracle(rom)
            o.mem[0xD501] = o.mem[0xD502] = state
            o.mem[0xD73F], o.mem[0xD73E] = 0, 7
            o.word(0xD711, 1000); o.word(0xD714, 500)
            o.word(0xD511, 1000 - dx); o.word(0xD514, 500 - dy)
            o.call(0x9C22)
            type09.append({"state": hx(state, 2), "dx": dx, "dy": dy, "collected": o.mem[0xD73E] == 0})
    lab = terrain_rings.Lab(rom)
    rows = [[0] * 128 for _ in range(32)]
    block, q = next((b, q) for b, values in lab.pres.items() for q, present in enumerate(values) if present)
    cx, cy = 10, 10
    rows[cy][cx] = block
    lab.set_layout(rows)
    px = cx * 32 + (q & 1) * 16 + 8
    py = cy * 32 + (q >> 1) * 16 + 8
    terrain = []
    addr = lab.cell_addr(cx, cy)
    for state in (0x11, 0x12):
        for bit0 in (0, 1):
            lab.m[addr] = block
            anchor_y = py + (8 if bit0 == 0 else -2)
            got = lab.trial(px, anchor_y, bit0, req=state)
            terrain.append({"state": hx(state, 2), "counter_bit0": bit0,
                            "anchor": [px, anchor_y], "probe": list(got["probe"]),
                            "collected": got["counter"] == 1})
    reach = terrain_rings.state_reach(rom)
    selected = [r for r in reach["rows"] if r["state"] in ("0x11", "0x12")]
    return {"cases": len(type09) + len(terrain), "type_09": type09, "terrain_753e": terrain,
            "state_reach": selected, "model_mismatches": sum(r["collected"] != (abs(r["dx"]) < 12 and abs(r["dy"]) < 12) for r in type09) + sum(not r["collected"] for r in terrain)}


def spring_shoes_attachment_sweep(rom: bytes) -> dict:
    rows = []
    for dy in (-17, -16, -15, -14, -13):
        for attack in (0, 2):
            o = Oracle(rom)
            o.bank(2, 30)
            o.mem[0xD12B] = 30
            o.cpu.ix = 0xD700
            o.mem[0xD700] = 0x2F
            o.mem[0xD701] = o.mem[0xD702] = 1
            o.mem[0xD703] = 0x80
            o.mem[0xD72C] = 8
            o.mem[0xD72D] = 16
            o.word(0xD711, 500)
            o.word(0xD714, 500)
            o.word(0xD511, 500)
            o.word(0xD514, 500 + dy)
            o.mem[0xD52C] = 8
            o.mem[0xD52D] = 24
            o.mem[0xD501] = o.mem[0xD502] = 1
            o.mem[0xD503] = attack
            o.word(0xD518, 0x0100)
            o.call(0x8B64)
            rows.append({
                "dy": dy, "attack_before": bool(attack),
                "requested_player_state": hx(o.mem[0xD502], 2),
                "requested_object_state": o.mem[0xD702],
                "owner_d3a4": hx(o.word(0xD3A4)),
                "attack_after": bool(o.mem[0xD503] & 2),
                "contact": hx(o.mem[0xD721] & 15, 2),
            })
    return {"cases": len(rows), "rows": rows, "attack_inheritance": "unchanged by attachment"}


def spring_shoes_bounce_sweep(rom: bytes) -> dict:
    rows = []
    for attack in (0, 2):
        for contacts in (0, 2, 4, 8):
            o = Oracle(rom)
            o.cpu.ix = 0xD500
            o.mem[0xD501] = o.mem[0xD502] = 0x12
            o.mem[0xD503] = attack
            o.mem[0xD523] = contacts
            o.mem[0xD522] = contacts
            o.word(0xD3A4, 0xD700)
            o.mem[0xD700] = 0x2F
            o.mem[0xD701] = o.mem[0xD702] = 3
            o.mem[0xD706] = 3
            o.word(0xD511, 600)
            o.word(0xD514, 500)
            o.word(0xD518, 0x0100)
            o.call(0x3B66)
            rows.append({
                "attack_before": bool(attack), "contact_bits": hx(contacts, 2),
                "requested_state": hx(o.mem[0xD502], 2), "flags": hx(o.mem[0xD503], 2),
                "vy": s16(o.word(0xD518)), "owner_state": o.mem[0xD702],
                "sound": hx(o.mem[0xDE04], 2),
            })
    return {"cases": len(rows), "rows": rows, "floor_rule": "contact bit 1 -> airborne, vy=-$0780 (-7.5), owner state 3, sound $C2; attack bit is preserved"}


def monitor_order_sweep(rom: bytes) -> dict:
    rows = []
    for req in (0x09, 0x0F, 0x10):
        for dy, label in ((-25, "top-1"), (-24, "top"), (-23, "top+1"), (0, "side"), (23, "bottom-1"), (24, "bottom"), (25, "bottom+1")):
            for vy in (0x0000, 0x0100, 0xF000):
                r = object10.run_contact_fixture(
                    rom, parameter=2, delta_x=0 if dy else 18, delta_y=dy,
                    player_flags=2, player_state=0x09, requested_state=req,
                    player_y_velocity=vy,
                )
                rows.append({"requested_state": hx(req, 2), "edge": label, "dy": dy,
                             "vy": s16(vy), **r})
    return {
        "cases": len(rows), "rows": rows,
        "order": "$5FA0 solid projection runs before the attack branch. Top contacts reject requested states $0F/$10/$15/$1A; side contacts do not. Every break path also needs nonzero, nonnegative Y speed. Object contact flags can therefore be staged before conversion.",
        "classification": "D: canonical arrangement/contact-class edge case. A geometrically top-classified contact during requested $0F/$10 is rejected; an unambiguous side contact with attack bit set and downward nonzero Y speed breaks. A surviving unambiguous side contact in the POC would instead be B/C and needs the exact Windows replay.",
    }


def build(rom: bytes) -> dict:
    if len(rom) != 524288 or hashlib.sha256(rom).hexdigest() != ROM_SHA256:
        raise ValueError("Expected Sonic Chaos (Europe) v1.2")
    placements = placement_census(rom)
    vertical = vertical_sweep(rom)
    camera = camera_sweep(rom)
    attach = spring_shoes_attachment_sweep(rom)
    bounce = spring_shoes_bounce_sweep(rom)
    monitor = monitor_order_sweep(rom)
    termination = rocket_termination_fixtures(rom)
    rings = ring_fixtures(rom)
    coexistence = coexistence_fixtures(rom)
    routines = {
        "rocket_reward_dispatch": routine(rom, 0x4AA3, 0x4B46),
        "rocket_entry": routine(rom, 0x4775, 0x47A9),
        "rocket_state_11": routine(rom, 0x3A7C, 0x3B4E),
        "spring_shoes_state_12": routine(rom, 0x3B4E, 0x3BC1),
        "spring_shoes_object": routine(rom, 0x78B5B, 0x78BE1),
        "monitor_contact": routine(rom, 0x3216C, 0x321D3),
    }
    controlled = vertical["cases"] + camera["cases"] + attach["cases"] + bounce["cases"] + monitor["cases"] + termination["cases"] + rings["cases"] + coexistence["cases"] + 1
    assert placements["totals"] == {"rocket_shoes": 11, "spring_shoes": 16}
    assert reward_fixture(rom)["requested_state"] == "0x11"
    assert all(r["attack_before"] == r["attack_after"] for r in attach["rows"])
    assert all(r["vy"] == -0x780 for r in bounce["rows"] if r["contact_bits"] == "0x02")
    assert rings["model_mismatches"] == 0
    return {
        "format": 1, "rom_sha256": ROM_SHA256, "research_only": True, "poc_untouched": True,
        "machine_facing_label": "powerup_shoes", "evidence": ["DECODED DATA", "BYTE-VERIFIED ASSEMBLY", "SOURCE-TRACED", "CONTROLLED ROUTINE RESULT"],
        "routines": routines,
        "identities": {
            "rocket_shoes": {"object": "0x10", "parameter": "0x04", "reward_mask": "0x08", "selector_d532": "0x04", "player_state": "0x11", "timer": "D44C", "duration_copy": "D3A1"},
            "spring_shoes": {"object": "0x2F", "parameter": "0x00", "monitor_reward": None, "selector_d532": None, "player_state": "0x12", "owner_pointer": "D3A4", "timer": None},
        },
        "placements": placements,
        "rocket_shoes": {
            "pickup": {"fixture": reward_fixture(rom), "order": "object phase N queues D3A3 bit 3; player update N+1 runs the old state then dispatches the reward and requests $11; the animation engine applies current state $11 on N+2"},
            "animation": {"script_cpu": "0x8334", "script_rom": "0x30334", "records": [[8, "0x38"], [4, "0x39"], [8, "0x3A"], [4, "0x39"]]},
            "movement": {"vertical_sweep": vertical, "horizontal": "entry vx=0, maximum=$0700; $48A7 changes facing from Left/Right, then state $11 ORs held Left/Right into D137 from facing every update. Shared state-$11 acceleration is +/-$0010 dry, +/-$0002 water. This is facing-steered auto-cruise, not ordinary optional horizontal input.", "gravity": "state $11 bypasses ordinary gravity; only the vertical controller changes vy", "ground": "shared terrain collision remains active; floor contact clears object contact bit 1, moves y up 2, and zeros vy"},
            "camera": {"vertical_clamp": camera, "other": "ordinary horizontal edge clamp/follow; no footwear-specific lead or follow-speed change found"},
            "rings": {"fixtures": rings, "type_09": "ordinary strict abs(dx)<12 && abs(dy)<12 path is state-independent", "terrain": "state $11 is explicitly in the 26-state $753E probe family; shared movement/projection runs first; probe uses anchor X and animation-counter parity Y-8 even / Y+2 odd", "poc_failure_explanation": "The accepted source already lists states 17/18 in the terrain-ring probe and runs type-$09 proximity independently. The reported no-ring Windows behavior is not explained by a canonical skip and is not reproduced by static inspection; it likely predates the accepted ring migrations or needs an exact build/runtime replay."},
            "attack_and_objects": "Entry clears D503 bit 1. Normal Rocket Shoes are non-attacking: monitors survive; type $21 top-stomps first but side/low contact damages; type $27 and hazards damage. Invincibility can later set bit 1 while state $11 persists, so state alone must not decide attack.",
            "terrain": "ordinary floor/wall/ceiling/slopes/one-way and shared platform/object contact remain active. Terrain upright/diagonal/horizontal springs explicitly reject current state $11; ceiling spring does not. Type $26 has no state-$11 exclusion and can override the player state/velocity when its normal gates pass.",
            "duration": {"fixtures": termination, "rule": "D44C starts at 300 ($012C) ordinarily. End-of-update decrement yields 300 full state-$11 updates at timer 300..1; the following callback at zero still moves/collides, restores music, and requests fall $0E with vy=+1.0. Landing/terrain do not cancel. State-$11 damage immediately clears D532 and queued bit 3, restores music, requests hurt and does not execute ordinary ring loss."},
        },
        "spring_shoes": {
            "pickup": {"attachment_sweep": attach, "rule": "descending/non-rising player projected onto the top requests player $12, records owner object in D3A4, and requests object state 3; no selector, timer, pickup music or palette effect"},
            "animation": {"script_cpu": "0x8346", "script_rom": "0x30346", "record": {"duration": 4, "frame": "0x0B", "callback_vector": "0x03B0 -> 0x3B4E"}},
            "movement": {"bounce_sweep": bounce, "horizontal": "same state-table acceleration row as $11 (+/-$0010 dry, +/-$0002 water), but no forced direction; neutral friction is +/-$0020", "gravity": "ordinary airborne gravity (+$0030 dry / +$0018 water, terminal +7/+4)", "manual_jump": "button $10/$20 detaches owner, clears airborne and invokes normal jump $45ED (-4.25 dry/-3.25 water, state $0A)", "foot_probe": "state $12 adds +8 to the shared foot-probe offset"},
            "canonical_springs": "No multiplication/addition. Type $26 or terrain upright spring overrides with its canonical state/velocity and clears attack; diagonal/horizontal terrain springs override with their canonical state/velocity and set attack. Leaving current state $12 makes object $2F detach on its next update.",
            "rings": "Type $09 strict proximity remains active. State $12 is explicitly in the same 26-state $753E family and uses the same animation-counter parity probe.",
            "attack_and_hazards": "Type $2F and state $12 do not write attack bit 1: pickup and automatic rebounds inherit it. Enemy outcomes therefore follow D503 bit 1 at the exact contact. Type $21 top stomp, springs, side hurt, ordinary damage or another state detach the wearable; spikes remain hazards.",
            "duration": "No timer and no D532 ownership. It lasts while player current state is $12 and owner object remains attached. Manual jump, side-wall state-$12 hurt path, damage, canonical spring transitions, death/clear/state replacement detach it; expiry-on-landing does not exist.",
            "graphics": {"mapping_table_rom": "0x3C05E", "mapping_cpu": "0x9287", "mapping_rom": "0x3D287", "sleeping_egg": {"stream_rom": "0x26840", "vram_destination": "0x1280", "tile_ids": "0x94..0xA3"}, "mecha_green_hill": {"stream_rom": "0x26840", "vram_destination": "0x1580", "tile_ids": "0xAC..0xBB"}, "note": "same 512-byte source stream, different VRAM base/art byte"},
            "camera": "ordinary camera and player edge clamp; no state-$12-specific camera routine found",
        },
        "coexistence": {
            "fixtures": coexistence,
            "shared_selector": "Rocket $04, speed-up $03 and invincibility $06 share D532/D44C; Spring Shoes do not.",
            "replacement": "A later monitor reward overwrites D532/D44C. Rocket pickup requests $11 and thereby detaches type $2F. A type-$2F pickup requests $12 and ends Rocket movement, but the prior D532/D44C keeps decrementing until overwritten/expired.",
            "invincibility": "While $11 persists, $06 overwrites the timer with 600 and sets attack bit 1; aura/attack overlay is active. Rocket entry after invincibility overwrites selector/timer and clears attack.",
            "speed_up": "Speed-up overwrites selector/timer and changes the ordinary maximum, while current $11 can continue. At timer zero $4A74 deliberately does not clear selector 3; the next decrement wraps D44C from 0 to $FFFF, so the speed-up remains until another reset/reward. This combination must use the selector/state split, not a single footwear enum.",
        },
        "monitor_spin_dash": monitor,
        "poc_migration": [
            {"area": "Rocket pickup/state", "canonical": "$10/$04 -> D532=4, D44C=300, state $11", "accepted_poc": "identity/entry broadly present", "action": "retain numeric identity and two-update activation order"},
            {"area": "Rocket horizontal control", "canonical": "facing-selected forced Left/Right every state-$11 callback", "accepted_poc": "passes only user input to shared movement", "action": "inject the facing direction before movement"},
            {"area": "Rocket neutral vertical", "canonical": "+/-$20 chosen by signed high byte; fractional oscillation", "accepted_poc": "clamps toward exactly zero", "action": "reproduce signed-high-byte step"},
            {"area": "Rocket attack", "canonical": "entry clears attack, but later invincibility can set it while $11 continues", "accepted_poc": "blanket !state11 suppression", "action": "store/test canonical D503 bit 1 independently"},
            {"area": "Rocket damage cleanup", "canonical": "state-$11 special branch keeps rings (even zero), cancels selector/queue, requests hurt $1E and sound $C3", "accepted_poc": "generic hurt path can scatter rings or choose death before cancel_state11", "action": "add the state-$11 special branch ahead of ordinary ring-loss/death selection"},
            {"area": "Rocket rings", "canonical": "both type $09 and terrain $753E active", "accepted_poc": "current source already includes both", "action": "keep; reproduce the exact failing Windows build before changing probes"},
            {"area": "Rocket terrain springs", "canonical": "terrain upright/diagonal/horizontal reject $11; type $26 can override", "accepted_poc": "needs explicit audit during migration", "action": "preserve this split"},
            {"area": "Spring Shoes", "canonical": "mapped $2F attachment, player $12, no timer/selector", "accepted_poc": "not implemented", "action": "add object/attachment ownership, state $12 physics and detach paths"},
            {"area": "Spring Shoes attack", "canonical": "inherited bit across attach/rebounce", "accepted_poc": "not implemented", "action": "do not infer attack from state/airborne"},
            {"area": "Monitor/spin-dash", "canonical": "$5FA0 first; top rejects req $0F/$10; true side can break", "accepted_poc": "similar staged ordering", "action": "classify exact Windows contact geometry before altering collision"},
        ],
        "counts": {"controlled_routine_cases": controlled, "decoded_placements": placements["totals"]["rocket_shoes"] + placements["totals"]["spring_shoes"], "acts_censused": len(placements["acts"]), "model_mismatches": 0},
        "unresolved": [
            "Exact persistence/reset across death and act-transition RAM clearing was not followed through every global initializer; normal state replacement/damage behavior is closed.",
            "The Windows report that Rocket Shoes collect no rings is contradicted by canonical code and the accepted POC source; the exact historical executable/save state was not available for replay.",
            "The observed monitor stop lacks an exact player/object pose. Canonical top-classification rejection is proved; a surviving unambiguous side contact would be a separate POC mismatch.",
        ],
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("rom", type=Path)
    p.add_argument("--metadata", type=Path, default=OUTPUT)
    p.add_argument("--check", action="store_true")
    a = p.parse_args()
    fresh = build(a.rom.read_bytes())
    encoded = json.dumps(fresh, indent=1) + "\n"
    if a.check:
        if not a.metadata.is_file() or a.metadata.read_text(encoding="utf-8") != encoded:
            raise SystemExit(f"cache differs: {a.metadata}")
    else:
        a.metadata.parent.mkdir(parents=True, exist_ok=True)
        a.metadata.write_text(encoded, encoding="utf-8")
    print(json.dumps(fresh["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
