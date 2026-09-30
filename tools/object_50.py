#!/usr/bin/env python3
"""Full study of THZ3 object type $50 (research only, deterministic).

Everything is recomputed from the checked ROM. The output is
data/rom-cache/thz3/object-50.json (machine-facing: numeric labels only).

Evidence classes (same vocabulary as the earlier studies):
  DECODED DATA, BYTE-VERIFIED ASSEMBLY, SOURCE-TRACED BEHAVIOR,
  CONTROLLED ROUTINE RESULT (original Z80 routines run on kosarev/z80 with
  explicit RAM), EMULATED ORIGINAL FRAME (the whole original game booted in
  tools/sms_frame_harness.py, forced into THZ3), UNRESOLVED.

Usage:
  python tools/object_50.py ROM.sms                 # write the cache
  python tools/object_50.py ROM.sms --check         # compare with the cache
  python tools/object_50.py ROM.sms --static-only   # no Z80 execution
  python tools/object_50.py ROM.sms --png build/object-50   # also export PNGs
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
OUTPUT = ROOT / "data" / "rom-cache" / "thz3" / "object-50.json"
TYPE_ID = 0x50
BANK = 0x1E            # object code/state bank for types >= $26
SLOT = 0xD700          # first placement slot (allocator $5EE1)


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


assets = _load("thz1_object_assets")
anim = _load("thz1_animation_reach")
dyn = _load("thz1_type18_dynamic_graphics")
lp = _load("level_package")


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #
def h(v: int, digits: int = 4) -> str:
    return f"0x{v:0{digits}X}"


def u16(rom: bytes, pos: int) -> int:
    return rom[pos] | (rom[pos + 1] << 8)


def s16(v: int) -> int:
    return v - 65536 if v >= 32768 else v


def rom_of(bank: int, cpu: int) -> int:
    """File offset of a CPU address (slot 0/1 fixed banks 0/1, slot 2 paged)."""
    if cpu < 0x8000:
        return cpu
    return bank * 0x4000 + cpu - 0x8000


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def check_rom(rom: bytes) -> None:
    if len(rom) != 524288 or sha(rom) != ROM_SHA256:
        raise ValueError("expected the documented Sonic Chaos SMS research ROM")


EVIDENCE = {
    "DECODED DATA": "ROM tables/records decoded by a parser",
    "BYTE-VERIFIED ASSEMBLY": "routine bytes compared literally and disassembled by hand",
    "SOURCE-TRACED BEHAVIOR": "behavior read from the disassembly, not executed",
    "CONTROLLED ROUTINE RESULT": "original routine executed on a Z80 core with explicit RAM",
    "EMULATED ORIGINAL FRAME": "whole original game run in the approximate SMS harness",
    "UNRESOLVED": "not established",
}


# --------------------------------------------------------------------------- #
# 1. static facts
# --------------------------------------------------------------------------- #
# (name, bank, first CPU, end CPU exclusive, kind, purpose)
ROUTINES = [
    ("placement_creator_loop", 0x1C, 0x8000, 0x80EB, "code", "walk object list, window/spawn-map test, dispatch"),
    ("placement_create", 0x1C, 0x80EB, 0x813C, "code", "allocate slot, copy record fields, occupancy token"),
    ("spawn_window_map", 0x1C, 0x8146, 0x8546, "data", "32x32 spawn-map (0/1 inner, 2 edge ring, 3 outside)"),
    ("object_scheduler", 0x00, 0x5DF1, 0x5E70, "code", "per-slot update; types >= $26 use bank $1E"),
    ("callback_dispatch", 0x00, 0x5E91, 0x5E9B, "code", "JP (IX+$0C/$0D)"),
    ("animation_engine", 0x01, 0x64FA, 0x65AF, "code", "state script interpreter, frame record select"),
    ("anim_cmd_dispatch", 0x01, 0x6680, 0x66B6, "code", "FF xx command dispatcher and pointer table"),
    ("anim_cmd_spawn", 0x01, 0x671F, 0x67A1, "code", "FF 04 spawn child via allocator $5EE1"),
    ("anim_cmd_call_callback", 0x01, 0x67A1, 0x67C1, "code", "FF 05 call routine, set callback, select frame"),
    ("anim_cmd_sound", 0x01, 0x67D5, 0x67EC, "code", "FF 06 write sound request to $DE04"),
    ("move_by_velocity", 0x01, 0x60FB, 0x613C, "code", "vector $0338: position += 8.8 velocity"),
    ("player_type_fix", 0x01, 0x613C, 0x614E, "code", "vector $037D"),
    ("proximity_tests", 0x01, 0x61A5, 0x61D6, "code", "vectors $0383/$0386: |object - player| < BC"),
    ("visibility_lifetime", 0x01, 0x61E1, 0x6276, "code", "offscreen flag, $FE/$FF removal"),
    ("overlap_helper", 0x01, 0x6328, 0x640B, "code", "vector $033B: contact bits in +$21"),
    ("solid_dispatch", 0x01, 0x5FA0, 0x6065, "code", "vector $034D: overlap + solid push by contact bit"),
    ("slot_cleanup", 0x01, 0x5EF8, 0x5F17, "code", "vector $0344: clear occupancy byte and slot"),
    ("player_bounce_setter", 0x01, 0x5F17, 0x5F27, "code", "vector $035F -> $480C spring setter"),
    ("enemy_destroy_conversion", 0x01, 0x5F54, 0x5F84, "code", "vector $033E: score gate then slot becomes type $0F"),
    ("spring_setter_480C", 0x01, 0x480C, 0x482D, "code", "player state $0B, vy from HL, sound $A6"),
    ("level_complete_setter", 0x01, 0x4892, 0x48A7, "code", "vector $03F5: player state $20 and clear jingle"),
    ("camera_left_lock", 0x01, 0x59E3, 0x59F3, "code", "vector $0353: D280 = max(D280, camX)"),
    ("camera_right_lock", 0x01, 0x59F3, 0x5A03, "code", "vector $0356: D282 = min(D282, camX)"),
    ("camera_scroll_request", 0x01, 0x59C5, 0x59D8, "code", "vector $0359: pan target BC (x), DE (y)"),
    ("camera_scroll_release", 0x01, 0x59D8, 0x59E3, "code", "vector $035C"),
    ("camera_scroll_step", 0x01, 0x5956, 0x59B3, "code", "per-frame 1 px pan toward D2DA/D2DC"),
    ("dynamic_graphics_loader", 0x01, 0x7AC2, 0x7BA6, "code", "streams selector $D3B3 lists, 4 tiles per call"),
    ("dynamic_graphics_pointers", 0x01, 0x7BA6, 0x7BCB, "data", "selector $10.. list pointers"),
    ("queue_command_add", 0x00, 0x1CD3, 0x1CEB, "code", "vector $0374: add background/palette command C"),
    ("palette_flash_command_7", 0x1D, 0x83C6, 0x8442, "code", "queue command 7: CRAM colours 29/30 from table $9979"),
    ("boss_init_state0", BANK, 0x974C, 0x9771, "code", "state 0 callback"),
    ("boss_wait_player_state1", BANK, 0x9771, 0x97A1, "code", "state 1 callback"),
    ("boss_trigger_table", BANK, 0x97A1, 0x97C1, "data", "8 zones x (dx word, dy word) proximity limits"),
    ("boss_wait_child_state2", BANK, 0x97C1, 0x9808, "code", "state 2 callback"),
    ("boss_camera_target_table", BANK, 0x9808, 0x9828, "data", "8 zones x (dx word, dy word) camera target"),
    ("boss_setup_state3", BANK, 0x9828, 0x985B, "code", "state 3 callback"),
    ("boss_patrol_states_6_12", BANK, 0x985B, 0x9903, "code", "states 6/12 callback (both directions)"),
    ("boss_turn_state9", BANK, 0x9903, 0x9931, "code", "state 9 callback"),
    ("boss_turn_state15", BANK, 0x9931, 0x9961, "code", "state 15 callback"),
    ("boss_reaction_select", BANK, 0x9961, 0x9989, "code", "contact result -> reaction state"),
    ("boss_reaction_top", BANK, 0x9989, 0x9997, "code", "states 7/10/13/16 callback"),
    ("boss_reaction_hit", BANK, 0x9997, 0x99AE, "code", "states 8/11/14/17 callback"),
    ("boss_contact_damage", BANK, 0x99AE, 0x9A09, "code", "solid contact, bounce, damage, health"),
    ("boss_entry_state18", BANK, 0x9A09, 0x9A1E, "code", "state 18 callback"),
    ("boss_flicker_helpers", BANK, 0x9A1E, 0x9A3A, "code", "state 4 frame save/restore"),
    ("boss_state_table_and_scripts", BANK, 0x958B, 0x974C, "data", "19-entry state table + scripts"),
    ("boss_player_bounce_8105", BANK, 0x8105, 0x814D, "code", "attack-contact knockback of the player"),
    ("boss_contact_814D", BANK, 0x814D, 0x8168, "code", "state 18 contact helper"),
    ("boss_camera_save_8199", BANK, 0x8199, 0x81A6, "code", "left lock + save right limit in +$25/+$27"),
    ("boss_child_handle_81A6", BANK, 0x81A6, 0x81BD, "code", "allocate type $12, keep pointer in +$34/+$35"),
    ("boss_defeat_complete_state5", BANK, 0x81BD, 0x8212, "code", "state 5 callback"),
]

# State scripts, per-state facts. Hand-written descriptions are backed by the
# fixtures/emulated sections; numeric labels only.
STATE_FACTS = {
    0: dict(entry="object creation (placement creator writes state 0/requested 0)",
            callback="0x974C",
            action=[
                "sound request $8C when the script starts (FF 06 8C)",
                "set +$04 bit 1 (keep alive while offscreen)",
                "$D44E = $D297 + 1; $D4A5 = 0",
                "allocate child type $12 (pool $D540..) with parameter = high byte of the callback address ($97); keep slot pointer in +$34/+$35",
                "camera left limit $D280 = max($D280, cameraX); save right limit $D282 into +$25 (high) / +$27 (low)",
                "if player requested state ($D502) == $12 then $D502 = $0E"],
            movement="none", contact="none", frame=0),
    1: dict(entry="from state 0", callback="0x9771",
            action=[
                "every update: same camera left lock/save as state 0",
                "trigger: |objectX - playerX| < W and |objectY - playerY| < H, (W,H) from table $97A1[$D297+$D4A5] (zone 0: 160, 256)",
                "on trigger: camera right limit $D282 = min($D282, cameraX) and request state 2"],
            movement="none", contact="none", frame=0),
    2: dict(entry="from state 1", callback="0x97C1",
            action=[
                "wait while the type-$12 child's type byte is non-zero",
                "then $D27E = objectY + dy and camera pan target (objectX + dx, objectY + dy) with (dx,dy) from table $9808[$D297+$D4A5] (zone 0: -256, -160)",
                "request state 3"],
            movement="none", contact="none", frame=0),
    3: dict(entry="from state 2", callback="0x9828",
            action=[
                "$D3B3 = $13 (dynamic graphics selector: boss art)",
                "$D494 bit 5 set and $D495 = $0C (sprite palette $0C request)",
                "+$09 = $48 (mirrored art tile base); +$26 = 8 (health); +$3F = 1; +$1E = 0; +$32 = 0",
                "X velocity = -$0080 (8.8) = -0.5 px/update; set +$03 bit 7",
                "request state 18"],
            movement="vx = -0.5 px/update set here; applied from state 18", contact="none", frame=0),
    4: dict(entry="health reached 0 in contact routine $99AE", callback="0x032F (idle RET)",
            action=[
                "script spawns 5 type-$34 children (param $04) at offsets (-8,0) (8,0) (0,-16) (-8,-24) (-8,-24)",
                "saves the current frame in +$38 (FF 05 $9A1E) and alternates saved frame / blank frame 0 for 24 loops (4+2 updates each)",
                "no movement, no contact, no callback logic",
                "after the loop requests state 5"],
            movement="none", contact="none", frame="saved frame / 0 flicker"),
    5: dict(entry="from state 4", callback="0x81BD",
            action=[
                "wait for player background contact bit 1 ($D522 bit 1, floor)",
                "camera: $D280 = cameraX; scroll release ($035C); $D282 restored from +$25/+$27",
                "player: requested state $20 and sound $89 ($97 when $D298 == 2) via $03F5/$4892",
                "allocate child type $0A parameter 0 (pool $D540..)",
                "+$3F = $80, +$3E = 0, then $033E: no score for type >= $50, slot becomes type $0F with all state fields cleared"],
            movement="none", contact="none", frame=0),
    6: dict(entry="from state 18 (screen X in $80..$DF), from state 15, from reactions", callback="0x985B",
            action=["leftward patrol; +$04 = 0 (unmirrored); phases in +$32 (see transitions)"],
            movement="cruise -128/256 px/update on the first sweep, -130/256 after a turn (phase 1 stops once vx < -$0080)", contact="solid + damage (routine $99AE)", frame="1/2 alternate, 16 updates each"),
    7: dict(entry="player top contact while in state 6", callback="0x9989",
            action=["20-update timer +$1F; keeps moving by current velocity; returns to +$0B"],
            movement="continues", contact="none", frame="3,1 (2 updates each), 3,1 (3 each), then loops 4,2,4,2,3,1,3,1 (4 each)"),
    8: dict(entry="attack hit while in state 6", callback="0x9997",
            action=["20-update timer; NO movement; at 0: return to +$0B, velocity 0, +$32 = 1"],
            movement="frozen", contact="none", frame="1,2 alternate, 4 updates each"),
    9: dict(entry="deceleration of state 6 finished (velocity >= -8/256)", callback="0x9903",
            action=["turn left->right: X velocity += 2/256 per update while negative",
                    "when velocity >= $0020: +$32 = 1, request state 12"],
            movement="accelerates from ~0", contact="solid + damage", frame="5 (8-update record)"),
    10: dict(entry="player top contact while in state 9", callback="0x9989",
             action=["as state 7"], movement="continues", contact="none", frame="5,6 (2,2,3,3 updates) then loops 5,6 at 4 updates"),
    11: dict(entry="attack hit while in state 9", callback="0x9997",
             action=["as state 8"], movement="frozen", contact="none", frame="5 (8-update record)"),
    12: dict(entry="from state 9", callback="0x985B",
             action=["rightward patrol; +$04 = $10 (mirrored art via +$09); phases in +$32"],
             movement="cruise +128/256 px/update (phase 1 stops once vx >= $0080)", contact="solid + damage", frame="1/2 alternate, 16 updates each"),
    13: dict(entry="player top contact while in state 12", callback="0x9989",
             action=["as state 7"], movement="continues", contact="none", frame="mirrored: 1,3 (2 each), 1,3 (3 each), then loops 2,4,2,4,1,3,1,3 (4 each)"),
    14: dict(entry="attack hit while in state 12", callback="0x9997",
             action=["as state 8"], movement="frozen", contact="none", frame="mirrored 1,2 alternate, 4 updates each"),
    15: dict(entry="deceleration of state 12 finished (velocity < 0 after subtract)", callback="0x9931",
             action=["turn right->left: X velocity -= 2/256 per update while positive",
                     "when velocity < -$0020: +$32 = 1, request state 6"],
             movement="accelerates from ~0", contact="solid + damage", frame="5 (8-update record), unmirrored"),
    16: dict(entry="player top contact while in state 15", callback="0x9989",
             action=["as state 7"], movement="continues", contact="none", frame="6,5 (2,2,3,3 updates) then loops 6,5 at 4 updates"),
    17: dict(entry="attack hit while in state 15", callback="0x9997",
             action=["as state 8"], movement="frozen", contact="none", frame="5 (16-update record)"),
    18: dict(entry="from state 3", callback="0x9A09",
             action=["move by velocity; solid contact helper $814D (damage to non-attacking player, knockback for attacking player, no boss damage)",
                     "when screen X (+$1A low byte) is in $80..$DF: request state 6"],
             movement="vx = -0.5 px/update", contact="solid, no damage to boss", frame="1/2 alternate, 16 updates each"),
}


def routine_table(rom: bytes) -> list[dict]:
    out = []
    for name, bank, start, end, kind, purpose in ROUTINES:
        off = rom_of(bank, start)
        raw = rom[off:off + (end - start)]
        out.append({
            "name": name, "kind": kind, "purpose": purpose,
            "bank": h(bank, 2), "cpu": h(start), "cpu_end_exclusive": h(end),
            "rom_offset": h(off, 5), "length": end - start,
            "first_16_bytes": raw[:16].hex(), "sha256": sha(raw),
            "evidence": "BYTE-VERIFIED ASSEMBLY" if kind == "code" else "DECODED DATA",
        })
    return out


def placement(rom: bytes) -> dict:
    objs = json.loads((ROOT / "data/rom-cache/levels/thz3/objects.json").read_text(encoding="utf-8"))
    rec = objs["records"][0]
    off = int(rec["rom_offset"], 16)
    raw = rom[off:off + 9]
    return {
        "evidence": "DECODED DATA + BYTE-VERIFIED ASSEMBLY (creator $700EB)",
        "act": "thz3", "record_index_1_based": 1, "count_in_all_acts": 1,
        "rom_offset": h(off, 5), "bank": "0x1C", "cpu": h(0x8000 + off - 0x70000),
        "raw_bytes": raw.hex(" ").upper(),
        "type_id": h(raw[0], 2),
        "stored_x": u16(raw, 1), "stored_y": u16(raw, 3),
        "world_x": u16(raw, 1) - 256, "world_y": u16(raw, 3) - 256,
        "flags": h(raw[5], 2), "parameter": h(raw[6], 2), "aux0": h(raw[7], 2), "aux1": h(raw[8], 2),
        "object_list_start": objs["list"]["start_rom"],
        "record_matches_level_package": rec["raw_bytes"] == raw.hex(" ").upper(),
        "occupancy": {
            "byte_address": "0xD400", "token_plus_3E": 1,
            "rule": "occupancy byte $D400 + index holds the type ($50) after creation; the creator only "
                    "creates while that byte is 0; token = index + 1 is stored in +$3E",
            "cleanup": "$5EF8 clears the occupancy byte only when +$3E is non-zero; the defeat path clears +$3E first, "
                       "so the byte stays $50 and the boss is never re-created in this level session",
        },
        "act_context": {
            "zone_index": 0, "act_index": 2,
            "camera_limits_from_act_header": {"D280_left": 0, "D27C_top": 8, "D282_right": 2304, "D27E_bottom": 272},
        },
    }


def dispatch(rom: bytes) -> dict:
    entry = 0x65BA + (TYPE_ID - 1) * 2
    table = anim.animation_state_table(rom, TYPE_ID)
    mapping_ptr = 0x3C000 + TYPE_ID * 2
    aliases = [t for t in range(0x26, 0x60)
               if u16(rom, 0x65BA + (t - 1) * 2) == u16(rom, entry)]
    return {
        "evidence": "BYTE-VERIFIED ASSEMBLY + DECODED DATA",
        "chain": [
            "placement creator $80EB (bank $1C) writes type $50 into slot +$00, state 0",
            "scheduler $5DF1: slot type >= $26 and < $F0 -> map bank $1E, CALL $64FA (animation engine), CALL $5E91 (callback), then $61E1 (visibility)",
            "animation engine $64FA: state table = word at $65BA + (type-1)*2",
            "state script pointer = word at state_table + 2*state; records set +$0C/+$0D callback; $5E91 jumps to it every update",
        ],
        "type_table_entry_rom": h(entry, 5), "type_table_entry_value": h(u16(rom, entry)),
        "state_table_bank": h(BANK, 2), "state_table_cpu": h(table["state_table_cpu"]),
        "state_table_rom": h(table["state_table_rom"], 5), "state_count": table["state_count"],
        "state_script_cpus": [h(x) for x in table["state_script_cpus"]],
        "shares_state_table_with_types": [h(t, 2) for t in aliases],
        "scheduler": {"cpu": "0x5DF1", "type_ge_26_branch": "0x5E31", "engine": "0x64FA",
                      "callback_dispatch": "0x5E91", "slot_stride": 64, "slots_from": "0xD540", "slot_count": 19},
        "jump_table_path": "no per-type jump table: dispatch is data-driven (type -> $65BA word -> state word -> script record -> callback word)",
        "mapping_table": {"pointer_entry_rom": h(mapping_ptr, 5), "pointer_value": h(u16(rom, mapping_ptr)),
                          "bank": "0x0F", "cpu": h(u16(rom, mapping_ptr)),
                          "rom": h(0x3C000 + u16(rom, mapping_ptr) - 0x8000, 5)},
    }


def full_script(rom: bytes, start: int, limit: int = 200) -> list[dict]:
    """Complete decoder for every FF command the state machine can meet."""
    pc = start
    seen = set()
    out = []
    while len(out) < limit:
        if pc in seen:
            out.append({"cpu": h(pc), "op": "loops_back", "target": h(pc)})
            break
        seen.add(pc)
        o = rom_of(BANK, pc)
        b = rom[o]
        if b != 0xFF:
            out.append({"cpu": h(pc), "op": "record", "duration": b, "frame": rom[o + 1],
                        "callback": h(u16(rom, o + 2))})
            pc += 4
            continue
        c = rom[o + 1]
        a = rom[o + 2:o + 10]
        w = lambda i: a[i] | (a[i + 1] << 8)
        e = {"cpu": h(pc), "cmd": h(c, 2)}
        if c == 0:
            e.update(op="restart_state"); out.append(e); break
        if c == 3:
            e.update(op="request_state", state=a[0]); out.append(e); break
        if c == 1:
            e.update(op="call", target=h(w(0))); pc += 4
        elif c == 2:
            e.update(op="velocity_8_8", x=s16(w(0)), y=s16(w(2))); pc += 6
        elif c == 4:
            e.update(op="spawn", type=h(a[0], 2), dx=s16(w(1)), dy=s16(w(3)), parameter=h(a[5], 2)); pc += 8
        elif c == 5:
            e.update(op="call_and_set_callback", target=h(w(0)), callback=h(w(2))); pc += 6
        elif c == 6:
            e.update(op="sound", sound=h(a[0], 2)); pc += 3
        elif c == 7:
            e.update(op="jump", target=h(w(0))); pc = w(0)
        elif c == 9:
            e.update(op="set_field", offset=h(a[0], 2), value=h(a[1], 2)); pc += 4
        elif c == 0x0E:
            e.update(op="set_loop_counter", count=a[0]); pc += 3
        elif c == 0x0F:
            e.update(op="loop_jump", target=h(w(0))); pc += 4
        else:
            raise ValueError(f"unsupported command FF {c:02X} at ${pc:04X}")
        out.append(e)
    return out


def state_tables(rom: bytes) -> list[dict]:
    table = anim.animation_state_table(rom, TYPE_ID)
    states = []
    for n, cpu in enumerate(table["state_script_cpus"]):
        cmds = full_script(rom, cpu)
        frames = sorted({x["frame"] for x in cmds if x["op"] == "record"})
        cbs = sorted({x["callback"] for x in cmds if x["op"] == "record"} |
                     {x["callback"] for x in cmds if x["op"] == "call_and_set_callback"})
        s = dict(STATE_FACTS[n])
        s.update({
            "state": n, "script_cpu": h(cpu), "script_rom": h(rom_of(BANK, cpu), 5),
            "script_bytes": rom[rom_of(BANK, cpu):rom_of(BANK, cpu) + 2].hex(),
            "script": cmds, "frames_reached": frames, "callbacks_in_script": cbs,
            "evidence": "DECODED DATA (script) + SOURCE-TRACED BEHAVIOR (callback)",
        })
        states.append(s)
    return states


def transitions() -> list[dict]:
    """State edges. `via` is the code that writes the request byte +$02."""
    T = lambda a, b, cond, via, ev: {"from": a, "to": b, "condition": cond, "via": via, "evidence": ev}
    S, C = "SOURCE-TRACED BEHAVIOR", "CONTROLLED ROUTINE RESULT"
    return [
        T(0, 1, "first update after init", "$974C LD (IX+2),1", C),
        T(1, 2, "player within (W,H) of the object", "$9771..$979C", C),
        T(2, 3, "type-$12 child slot type byte becomes 0", "$97C1..$9803", C),
        T(3, 18, "unconditional next update", "$9839", C),
        T(18, 6, "screen X low byte in $80..$DF", "$9A18", C),
        T(6, 9, "+$32 = $FF and velocity + 8/256 carries (velocity >= -8/256)", "$98B8", C),
        T(9, 12, "velocity >= $0020 (sets +$32 = 1)", "$9928/$992C", C),
        T(12, 15, "+$32 = $FF and velocity + 8/256 carries (velocity < 0)", "$98BD", C),
        T(15, 6, "velocity < -$0020 (sets +$32 = 1)", "$9958/$995C", C),
        T(6, 7, "contact result 1 (player above)", "$9961..$996E", C),
        T(6, 8, "contact result $FF (attack hit)", "$9976..$9981", C),
        T(9, 10, "contact result 1", "$9961", C), T(9, 11, "contact result $FF", "$9976", C),
        T(12, 13, "contact result 1", "$9961", C), T(12, 14, "contact result $FF", "$9976", C),
        T(15, 16, "contact result 1", "$9961", C), T(15, 17, "contact result $FF", "$9976", C),
        T(7, 6, "20 updates elapsed, return to saved state (+$0B)", "$9990", C),
        T(10, 9, "as above", "$9990", S), T(13, 12, "as above", "$9990", S), T(16, 15, "as above", "$9990", S),
        T(8, 6, "20 updates elapsed, velocity cleared, +$32 = 1", "$999B..$99AD", C),
        T(11, 9, "as above", "$999B", S), T(14, 12, "as above", "$999B", S), T(17, 15, "as above", "$999B", S),
        T("6/9/12/15/18", 4, "health (+$26) decrements to 0 in an attack hit (states 6,9,12,15 only)", "$99F6", C),
        T(4, 5, "24-iteration flicker loop finished", "script FF 03 05 at $9619", C),
        T(5, "type $0F", "player on floor: slot converted by $033E", "$81E9..$81F1", C),
    ]


# --------------------------------------------------------------------------- #
# graphics
# --------------------------------------------------------------------------- #
def frame_table(rom: bytes) -> dict:
    m = assets.object_mapping(rom, TYPE_ID)
    ptrs = assets.mapping_frame_pointers(rom, m["mapping_cpu"])
    frames = []
    for i, p in enumerate(ptrs):
        r = assets.parse_frame_record(rom, p)
        pieces = r["pieces"]
        f = {
            "frame": i, "record_cpu": h(p), "record_rom": h(r["frame_rom"], 5),
            "raw_record": rom[r["frame_rom"]:r["frame_rom"] + 11].hex(" ").upper(),
            "piece_count": r["piece_count"],
            "contact_extent_x_plus_2C": rom[r["frame_rom"] + 1],
            "contact_extent_y_plus_2D": rom[r["frame_rom"] + 2],
            "y_origin": r["y_origin"], "x_origin": r["x_origin"],
            "coordinate_table_cpu": h(r["coords_cpu"]) if pieces else None,
            "tile_list_cpu": h(r["tile_list_cpu"]) if pieces else None,
            "pieces": [{"y": p2["relative_y"], "x": p2["relative_x"], "tile_offset": p2["tile_offset"]}
                       for p2 in pieces],
            "reachable": False,
        }
        if pieces:
            f["bounds_unmirrored"] = {
                "min_x": min(p2["relative_x"] for p2 in pieces),
                "max_x_exclusive": max(p2["relative_x"] for p2 in pieces) + 8,
                "min_y": min(p2["relative_y"] for p2 in pieces),
                "max_y_exclusive": max(p2["relative_y"] for p2 in pieces) + 16,
            }
            b = f["bounds_unmirrored"]
            f["bounds_mirrored"] = {"min_x": -b["max_x_exclusive"], "max_x_exclusive": -b["min_x"],
                                    "min_y": b["min_y"], "max_y_exclusive": b["max_y_exclusive"]}
        else:
            f["bounds_unmirrored"] = f["bounds_mirrored"] = None
        frames.append(f)
    return {"mapping": {"bank": "0x0F", "cpu": h(m["mapping_cpu"]), "rom": h(m["mapping_rom"], 5),
                        "pointer_entry_rom": h(m["pointer_table_rom"], 5), "frame_count": len(ptrs)},
            "frames": frames}


def dynamic_vram(rom: bytes) -> tuple[bytes, dict]:
    """THZ3 act VRAM + selector $13 loads, applied exactly as loader $7AC2 does."""
    desc = lp.build_descriptor(rom, "thz3")
    vram, _ = lp.build_vram(rom, desc["art"])
    vram = bytearray(vram)
    list_cpu, entries = dyn.dynamic_list_for_selector(rom, 0x13)
    loads = []
    for e in entries:
        raw = rom[e["source_rom"]:e["source_rom"] + e["tile_count"] * 32]
        if e["remap"]:
            raw = bytes(rom[0x100 + b] for b in raw)  # loader: LD D,1; LD E,(HL); LD A,(DE)
        vram[e["vram_destination"]:e["vram_destination"] + len(raw)] = raw
        loads.append({
            "list_entry_rom": h(e["list_rom"], 5), "bank": h(e["bank"], 2),
            "source_cpu": h(e["source_cpu"]), "source_rom": h(e["source_rom"], 5),
            "tile_count": e["tile_count"], "vram_destination": h(e["vram_destination"]),
            "first_tile": h(e["tile_base"], 2), "last_tile": h(e["tile_base"] + e["tile_count"] - 1, 2),
            "bit_reversed_copy": bool(e["remap"]), "source_sha256": sha(raw),
        })
    return bytes(vram), {"selector": "0x13", "pointer_table": "0x7BA6", "list_cpu": h(list_cpu), "loads": loads,
                         "list_terminator": "0xFF"}


def sprite_palette(rom: bytes, index: int) -> list:
    base = assets.PALETTE_DATA_ROM + index * 16
    return list(rom[base:base + 16])


def compose_frame(vram: bytes, frame: dict, mirrored: bool, palette: list, flash: tuple | None = None):
    """Compose one mapping frame the way renderer $226A/$22B6 does. Returns (w,h,x0,y0,indices)."""
    if not frame["pieces"]:
        return None
    base = 0x48 if mirrored else 0x00     # +$09 / +$08
    pieces = []
    for p in frame["pieces"]:
        x = -p["x"] - 8 if mirrored else p["x"]          # mirror table: -x-8 (origin negated too)
        pieces.append((p["y"], x, (p["tile_offset"] + base) & 0xFF))
    x0 = min(p[1] for p in pieces)
    y0 = min(p[0] for p in pieces)
    w = max(p[1] for p in pieces) + 8 - x0
    hgt = max(p[0] for p in pieces) + 16 - y0
    canvas = [[0] * w for _ in range(hgt)]
    for y, x, tile in pieces:
        top = assets.tile_pixels(vram, tile)
        bot = assets.tile_pixels(vram, tile + 1)
        for r, row in enumerate(top + bot):
            for c, v in enumerate(row):
                if v and 0 <= (x - x0 + c) < w and canvas[y - y0 + r][x - x0 + c] == 0:
                    canvas[y - y0 + r][x - x0 + c] = v     # first piece wins (SAT order)
    return w, hgt, x0, y0, canvas, pieces


def rgba_of(idx: int, pal: list) -> tuple:
    if idx == 0:
        return (0, 0, 0, 0)
    return assets.sms_color(pal[idx])


def orientation_reach(rom: bytes) -> dict:
    """+$04 bit 4 (mirror) is written by FF 09 04 xx at the start of states 6..18."""
    table = anim.animation_state_table(rom, TYPE_ID)
    normal, mirrored, per_state = set(), set(), {}
    for n, cpu in enumerate(table["state_script_cpus"]):
        cmds = full_script(rom, cpu)
        mode = "inherited"
        for e in cmds:
            if e["op"] == "set_field" and e["offset"] == "0x04":
                mode = "mirrored" if int(e["value"], 16) & 0x10 else "normal"
        fr = {e["frame"] for e in cmds if e["op"] == "record"}
        per_state[n] = {"orientation": mode, "frames": sorted(fr)}
        if mode == "mirrored":
            mirrored |= fr
        else:
            normal |= fr
    return {"normal_frames": sorted(normal), "mirrored_frames": sorted(mirrored), "per_state": per_state,
            "note": "states 0-5 do not write +$04 (state 4/5 keep the orientation of the state that ended); "
                    "frames 5/6 are only used unmirrored and do not fit the 44-tile mirrored copy"}


def graphics(rom: bytes, png_dir: Path | None) -> dict:
    ft = frame_table(rom)
    vram, dynload = dynamic_vram(rom)
    pal_level = sprite_palette(rom, 0x06)
    pal_boss = sprite_palette(rom, 0x0C)
    reach = set()
    for s in anim.animation_state_table(rom, TYPE_ID)["state_script_cpus"]:
        for e in full_script(rom, s):
            if e["op"] == "record":
                reach.add(e["frame"])
    for f in ft["frames"]:
        f["reachable"] = f["frame"] in reach
    # every reachable non-empty frame must sit inside the loaded blocks for both orientations
    used = {}
    for f in ft["frames"]:
        if f["pieces"]:
            offs = [p["tile_offset"] for p in f["pieces"]]
            used[f["frame"]] = {"first_tile_id_unmirrored": min(offs), "last_tile_id_unmirrored": max(offs) + 1,
                                "first_tile_id_mirrored": min(offs) + 0x48, "last_tile_id_mirrored": max(offs) + 0x48 + 1,
                                "fits_mirrored_copy_46_to_89": max(offs) + 1 <= 89}
    orient = orientation_reach(rom)
    hashes = {}
    sheet_items = []
    for f in ft["frames"]:
        for mirrored in (False, True):
            if mirrored and f["frame"] not in orient["mirrored_frames"]:
                continue
            r = compose_frame(vram, f, mirrored, pal_boss)
            key = f"frame_{f['frame']}_{'mirrored' if mirrored else 'normal'}"
            if r is None:
                hashes[key] = None
                continue
            w, hg, x0, y0, canvas, _ = r
            flat = bytes(v for row in canvas for v in row)
            hashes[key] = {"width": w, "height": hg, "origin_x": x0, "origin_y": y0,
                           "index_sha256": sha(flat),
                           "opaque_pixels": sum(1 for v in flat if v)}
            sheet_items.append((key, w, hg, canvas))
    out = {
        "evidence": "DECODED DATA + CONTROLLED ROUTINE RESULT (dynamic load reproduced) + EMULATED ORIGINAL FRAME (VRAM identical)",
        "art_source": {
            "resolved": True,
            "mechanism": "state 3 writes selector $13 to $D3B3; loader $7AC2 resolves it through the pointer table at $7BA6 "
                         "(word index selector-$10) to a 6-byte-per-entry list; 4 tiles are copied per call",
            "dynamic_load": dynload,
            "tile_base_unmirrored_plus_08": "0x00 (placement aux0)",
            "tile_base_mirrored_plus_09": "0x48 (state 3 writes +$09)",
            "mirrored_art": "second load applies the byte table at ROM $0100 (bit reversal) to the first 44 tiles; "
                            "mirrored frames therefore use tile ids offset + $48",
            "third_load_note": "12 tiles at tile $A2 (bank $09 $ABA0) are used by the type-$34 explosion children (art base $A2 in zone 0), "
                               "not by any type-$50 frame",
            "vram_tiles_first_last": ["0x2E", "0xAD"],
            "vram_image_sha256_tiles_2E_AD": sha(vram[0x2E * 32:0xAE * 32]),
        },
        "palette": {
            "level_sprite_palette_index": "0x06", "level_sprite_palette_rom": h(assets.PALETTE_DATA_ROM + 6 * 16, 5),
            "boss_sprite_palette_index": "0x0C", "boss_sprite_palette_rom": h(assets.PALETTE_DATA_ROM + 0x0C * 16, 5),
            "boss_sprite_palette_sha256": sha(bytes(pal_boss)),
            "level_sprite_palette_sha256": sha(bytes(pal_level)),
            "differs_at_colors": {str(i): {"level_palette_06": h(pal_level[i], 2), "boss_palette_0C": h(pal_boss[i], 2)}
                                  for i in range(16) if pal_boss[i] != pal_level[i]},
            "request": "state 3: $D494 bit 5 set, $D495 = $0C (consumer sets CRAM 16..31 = palette $0C; observed in the emulated run)",
            "hit_flash": "attack hit queues background/palette command 7; it writes CRAM colours 13 and 14 of the sprite palette "
                         "(shadow bytes $D48F/$D490) from table $1D:$9979 + zone*4 + step*2, 4 updates per step, 2 steps",
        },
        "mapping": ft["mapping"],
        "frames": ft["frames"],
        "reachable_frames": sorted(reach),
        "frames_by_orientation": orient,
        "tile_usage": used,
        "composed_frame_hashes": hashes,
        "registration": {
            "canonical_anchor": "(world_x, world_y) = (+$11, +$14); no per-type offset exists",
            "rule": "screen = anchor - camera; SAT_Y = screen_y + y_origin + piece_y; SAT_X = screen_x + x_origin' + piece_x'; "
                    "terrain_row = anchor_y + y_origin + piece_y + 18; terrain_col = anchor_x + x_origin' + piece_x + 1 "
                    "(shared registration pipeline, docs/mapped-object-screen-registration.md)",
            "mirroring": "+$04 bit 4: x_origin negated, piece x = -x-8, tile base +$09 instead of +$08",
            "rom_visible_bounds_rel_anchor": "see frames[].bounds_*; canonical anchor and bounds are stored separately",
            "visible_rows_rel_anchor_for_frames_1_2": [-48 + 18, 0 + 18 - 1],
        },
        "animation_timing": "see states[].script: durations are update counts (1 update per game frame)",
    }
    if png_dir is not None:
        write_pngs(png_dir, vram, ft, pal_boss, sheet_items, hashes)   # ROM-derived: stays under build/, never committed
    return out


def write_pngs(png_dir: Path, vram: bytes, ft: dict, pal: list, items: list, hashes: dict) -> None:
    png_dir.mkdir(parents=True, exist_ok=True)
    scale, pad = 4, 4
    cols = 7
    cell_w = max(w for _, w, _, _ in items) + pad * 2
    cell_h = max(hg for _, _, hg, _ in items) + pad * 2
    rows = 2
    W, H = cols * cell_w * scale, rows * cell_h * scale
    buf = bytearray(W * H * 4)
    for key, w, hg, canvas in items:
        _, fr, orient = key.split("_")
        cx, cy = int(fr) * cell_w, (1 if orient == "mirrored" else 0) * cell_h
        for y, row in enumerate(canvas):
            for x, v in enumerate(row):
                if not v:
                    continue
                rgba = bytes(rgba_of(v, pal))
                for sy in range(scale):
                    for sx in range(scale):
                        px, py = (cx + pad + x) * scale + sx, (cy + pad + y) * scale + sy
                        buf[(py * W + px) * 4:(py * W + px) * 4 + 4] = rgba
    assets.write_rgba_png(png_dir / "object-50-frames.png", W, H, bytes(buf))


# --------------------------------------------------------------------------- #
# 2. controlled routine fixtures (original Z80 code, explicit RAM)
# --------------------------------------------------------------------------- #
class Fixture:
    """Thin wrapper over tools/oracle.py with the object scheduler pair."""

    def __init__(self, rom: bytes):
        from oracle import Oracle
        self.rom = rom
        self.o = Oracle(rom)
        self.m = self.o.mem
        self.slot = SLOT
        self.m[0xD52C], self.m[0xD52D] = 9, 18       # player extents used by $6328 in the THZ1 fixtures
        self.o.mem[0xD500] = 1
        self.o.word(0xD174, 1600)
        self.o.word(0xD176, 80)
        for a, v in ((0xD280, 0), (0xD282, 2304), (0xD27C, 8), (0xD27E, 272)):
            self.o.word(a, v)
        self.o.mem[0xD297] = 0
        self.o.mem[0xD298] = 2

    def create(self, occupancy: int = 0xD400):
        self.o.bank(2, 0x1C)
        self.m[0xD12B] = 0x1C
        self.m[self.slot:self.slot + 0x40] = bytes(0x40)
        self.o.cpu.ix = self.slot
        self.o.cpu.hl = 0x88FE
        self.o.call(0x80EB, bc=occupancy)

    def w(self, off, v, n=1):
        for i in range(n):
            self.m[self.slot + off + i] = (v >> (8 * i)) & 255

    def r(self, off, n=1):
        return sum(self.m[self.slot + off + i] << (8 * i) for i in range(n))

    def force_state(self, st):
        self.w(0x01, st); self.w(0x02, st); self.w(0x0E, 0, 2)

    def step(self):
        for callee in (0x64FA, 0x5E91):
            self.m[0xD12B] = BANK
            self.o.bank(2, BANK)
            self.o.cpu.ix = self.slot
            self.o.call(callee)

    def call_bank(self, bank, addr):
        self.m[0xD12B] = bank
        self.o.bank(2, bank)
        self.o.cpu.ix = self.slot
        self.o.call(addr)

    def snap(self):
        return {"state": self.r(1), "requested": self.r(2), "frame": self.r(6), "timer": self.r(7),
                "callback": h(self.r(0x0C, 2)), "x": self.r(0x11, 2), "y": self.r(0x14, 2),
                "vx": s16(self.r(0x16, 2)), "vy": s16(self.r(0x18, 2)), "health": self.r(0x26),
                "cooldown_1E": self.r(0x1E), "timer_1F": self.r(0x1F), "phase_32": self.r(0x32),
                "saved_state_0B": self.r(0x0B), "flags_04": h(self.r(4), 2), "flags_03": h(self.r(3), 2)}


def fixtures(rom: bytes) -> dict:
    out = {"evidence": "CONTROLLED ROUTINE RESULT"}

    # -- creation ----------------------------------------------------------- #
    f = Fixture(rom)
    f.create()
    out["creation"] = {
        "fields": {"type": h(f.r(0), 2), "state": f.r(1), "requested": f.r(2), "flags_04": h(f.r(4), 2),
                   "x": f.r(0x11, 2), "y": f.r(0x14, 2), "saved_x_3A": f.r(0x3A, 2), "saved_y_3C": f.r(0x3C, 2),
                   "parameter_3F": f.r(0x3F), "aux0_08": f.r(8), "aux1_09": f.r(9), "token_3E": f.r(0x3E)},
        "occupancy_byte_D400": h(f.m[0xD400], 2),
    }

    # -- placement window (real loop $8000) -------------------------------- #
    def window(camx, camy, initial):
        g = Fixture(rom)
        g.o.bank(2, 0x1C); g.m[0xD12B] = 0x1C
        g.m[0xD400:0xD440] = bytes(0x40)
        g.m[0xD700:0xD9C0] = bytes(0x2C0)
        g.o.word(0xD174, camx); g.o.word(0xD176, camy); g.m[0xD440] = initial
        g.o.call(0x8000)
        return g.m[0xD700] == TYPE_ID
    out["placement_window"] = {
        "rule": "created when (x - camX + 128)/2 and (y - camY + 128)/2 both fit a byte, then spawn-map cell "
                "= map[(((y-camY+128)/2) & $F8)*4 + (((x-camX+128)/2)>>3 & $1F)]: cell 2 always creates; cells 0/1 create only while $D440 == 0 "
                "(initial fill); cell 3 never",
        "samples": [{"camera": [cx, cy], "initial_fill": ini, "created": window(cx, cy, ini)}
                    for cx, cy, ini in ((1600, 0, 0), (1600, 0, 1), (1552, 0, 0), (1553, 0, 0), (1500, 0, 0),
                                        (1836, 100, 0), (2064, 0, 0), (2065, 0, 0), (2200, 0, 0))],
    }

    # -- state 0 ------------------------------------------------------------ #
    f = Fixture(rom); f.create(); f.m[0xD502] = 0x12
    f.o.word(0xD174, 1600)
    f.step()
    out["state_0_init"] = {
        "after": f.snap(), "sound_request_DE04": h(f.m[0xDE04], 2),
        "D44E": f.m[0xD44E], "D4A5": f.m[0xD4A5], "left_limit_D280": f.o.word(0xD280),
        "saved_right_limit_25_27": f.r(0x25) << 8 | f.r(0x27),
        "child_slot_D540": {"type": h(f.m[0xD540], 2), "parameter_3F": h(f.m[0xD540 + 0x3F], 2)},
        "child_pointer_34_35": h(f.r(0x34, 2)), "player_requested_state_D502": h(f.m[0xD502], 2),
    }

    # -- state 1 thresholds -------------------------------------------------- #
    rows = []
    for dx, dy in ((159, 255), (160, 255), (159, 256), (-159, -255), (-160, 0), (0, -256)):
        g = Fixture(rom); g.create(); g.step()          # state 0 -> requested 1
        g.step()                                        # state 1 running
        g.o.position(g.r(0x11, 2) + dx, g.r(0x14, 2) + dy)
        g.o.word(0xD174, 1600)
        g.step()
        rows.append({"dx": dx, "dy": dy, "requested_after": g.r(2), "right_limit_D282": g.o.word(0xD282)})
    out["state_1_trigger"] = {"table_cpu": "0x97A1", "zone0_words": [160, 256], "cases": rows}

    # -- state 2 and camera target ----------------------------------------- #
    g = Fixture(rom); g.create(); g.step(); g.step()
    g.force_state(2)
    g.m[0xD540] = 0x12                                  # child present
    g.w(0x34, 0xD540, 2)
    g.step()
    waiting = g.snap()
    g.m[0xD540] = 0
    g.step()
    out["state_2_wait_and_camera_target"] = {
        "while_child_present": waiting, "after_child_gone": g.snap(),
        "bottom_limit_D27E": g.o.word(0xD27E), "pan_target_x_D2DA": g.o.word(0xD2DA), "pan_target_y_D2DC": g.o.word(0xD2DC),
        "D15E": h(g.m[0xD15E], 2), "D15F": h(g.m[0xD15F], 2),
    }

    # -- state 3 ------------------------------------------------------------- #
    g = Fixture(rom); g.create(); g.step(); g.force_state(3); g.step()
    out["state_3_setup"] = {
        "after": g.snap(), "D3B3": h(g.m[0xD3B3], 2), "D494": h(g.m[0xD494], 2), "D495": h(g.m[0xD495], 2),
        "aux1_09": h(g.r(9), 2), "param_3F": g.r(0x3F), "flags_03": h(g.r(3), 2),
    }

    # -- state 18 -> 6 ------------------------------------------------------- #
    rows = []
    for sx in (0x7F, 0x80, 0xDF, 0xE0, 0xE1):
        g = Fixture(rom); g.create(); g.step(); g.force_state(3); g.step()
        g.force_state(18); g.step()
        cam = g.r(0x11, 2) - sx
        g.o.word(0xD174, cam)
        g.o.position(g.r(0x11, 2) + 400, g.r(0x14, 2) - 300)   # player far away: no contact
        g.w(0x1A, sx, 2)                                        # screen X as $3FC8 leaves it
        g.m[0xD540] = 0
        g.call_bank(0x00, 0x3FC8)
        g.step()
        rows.append({"screen_x_low": sx, "requested_after": g.r(2)})
    out["state_18_exit"] = {"note": "screen X is recomputed from anchor - camera by $3FC8 before the callback", "cases": rows}

    # -- patrol cycle with no player ---------------------------------------- #
    g = Fixture(rom); g.create(); g.step(); g.force_state(3); g.step()
    g.o.position(0, 0)
    trace, prev = [], None
    cam_x = 1680
    g.o.word(0xD174, cam_x)
    for u in range(1400):
        g.o.position(cam_x - 4000, 0)
        g.call_bank(0x00, 0x3FC8)
        g.step()
        key = (g.r(1), g.r(2), g.r(0x32))
        if key != prev:
            sn = g.snap()
            trace.append({"update": u, "state": sn["state"], "requested": sn["requested"], "phase_32": sn["phase_32"],
                          "x": sn["x"], "vx": sn["vx"], "screen_x_low": g.r(0x1A), "flags_04": sn["flags_04"]})
            prev = key
    out["patrol_cycle"] = {"note": "camera fixed at X=1680, player parked far away; updates counted from state 3 entry",
                           "events": trace}

    # -- contact matrix ------------------------------------------------------- #
    def contact(state, dx, dy, attacking, health=8, cooldown=0, phase=0, player_vy=0, player_vx=0, frame_extents=None):
        g = Fixture(rom); g.create(); g.step(); g.force_state(3); g.step()
        g.force_state(state)
        g.w(0x26, health); g.w(0x1E, cooldown); g.w(0x32, phase)
        g.w(0x16, {6: -128, 9: -6, 12: 128, 15: 6, 18: -128}.get(state, 0) & 0xFFFF, 2)   # cruise / turn-start velocity
        bx, by = g.r(0x11, 2), g.r(0x14, 2)
        g.o.word(0xD174, bx - 250)
        g.o.position(bx + dx, by + dy)
        g.m[0xD503] = 2 if attacking else 0
        g.o.word(0xD516, player_vx); g.o.word(0xD518, player_vy)
        g.m[0xD3B0] = 0; g.m[0xD502] = 0; g.m[0xDE04] = 0; g.m[0xD452] = 0
        g.call_bank(0x00, 0x3FC8)
        g.step()
        sn = g.snap()
        sn.update({"contact_bits_21": h(g.r(0x21), 2), "damage_request_D3B0": h(g.m[0xD3B0], 2),
                   "player_requested_state_D502": h(g.m[0xD502], 2), "sound_DE04": h(g.m[0xDE04], 2),
                   "palette_command_slot_D452": g.m[0xD452], "player_vx": s16(g.o.word(0xD516)),
                   "player_vy": s16(g.o.word(0xD518)), "D448": g.m[0xD448],
                   "player_y_after": g.o.word(0xD514), "player_x_after": g.o.word(0xD511)})
        return sn

    matrix = []
    cases = (("attack_from_left_side", -26, 0, True), ("attack_from_right_side", 26, 0, True),
             ("attack_from_below", 0, 10, True), ("plain_side_contact", -26, 0, False),
             ("top_contact_attacking", 0, -40, True), ("top_contact_plain", 0, -40, False),
             ("no_contact", -200, 0, True))
    for st in (6, 9, 12, 15):
        for name, dx, dy, att in cases:
            r = contact(st, dx, dy, att, player_vy=0x0100)
            matrix.append({"start_state": st, "case": name, "result": r})
    out["contact_matrix"] = {
        "geometry": "boss frame 1/2 contact extents X 20, Y 48; player extents X 9, Y 18 (fixture values); "
                    "penetration axis rule of $6328", "cases": matrix}
    out["contact_state_18"] = [{"case": name, "result": contact(18, dx, dy, att)} for name, dx, dy, att in cases[:4]]
    out["cooldown"] = {
        "plain_contact_sets_cooldown_1E_2": contact(6, -26, 0, False),
        "contact_ignored_while_cooldown_active": contact(6, -26, 0, False, cooldown=2),
        "attack_ignored_while_cooldown_active": contact(6, -26, 0, True, cooldown=1),
    }
    out["health"] = {
        "initial_value_state_3": 8,
        "countdown": [contact(6, -26, 0, True, health=hp)["health"] for hp in (8, 7, 6, 5, 4, 3, 2)],
        "last_hit_from_1": contact(6, -26, 0, True, health=1),
        "hit_in_state_18_does_not_change_health": contact(18, -26, 0, True)["health"],
    }

    # -- reaction states ------------------------------------------------------ #
    def reaction(state, saved, velocity=-128):
        g = Fixture(rom); g.create(); g.step(); g.force_state(3); g.step()
        g.force_state(state)
        g.w(0x0B, saved); g.w(0x1F, 20); g.w(0x16, velocity & 0xFFFF, 2); g.w(0x32, 0)
        g.o.position(g.r(0x11, 2) + 400, g.r(0x14, 2) - 300)
        x0, seq = g.r(0x11, 2), []
        for u in range(22):
            g.o.position(g.r(0x11, 2) + 400, g.r(0x14, 2) - 300)
            g.step()
            seq.append((g.r(1), g.r(2), g.r(0x1F), g.r(0x16, 2)))
        end = g.snap()
        return {"state": state, "saved_state": saved, "x_moved_from": x0, "x_end": end["x"],
                "updates_until_return": next((i + 1 for i, q in enumerate(seq) if q[1] == saved), None),
                "end": end}
    out["reaction_states"] = [reaction(7, 6), reaction(8, 6), reaction(10, 9), reaction(11, 9),
                              reaction(13, 12, 128), reaction(14, 12, 128), reaction(16, 15, 128), reaction(17, 15, 128)]

    # -- state 4 defeat sequence --------------------------------------------- #
    g = Fixture(rom); g.create(); g.step(); g.force_state(3); g.step(); g.force_state(6)
    g.o.position(0, 0)
    g.w(0x06, 2)
    g.force_state(4)
    g.step()
    events, spawned = [], set()
    upd = 0
    for upd in range(1, 400):
        g.o.position(0, 0)
        g.step()
        for i in range(1, 11):
            b = SLOT + 0x40 * i
            if g.m[b] and b not in spawned:
                spawned.add(b)
                events.append({"update": upd, "slot": h(b), "type": h(g.m[b], 2),
                               "dx": s16(g.o.word(b + 0x11) - g.r(0x11, 2) & 0xFFFF),
                               "dy": s16(g.o.word(b + 0x14) - g.r(0x14, 2) & 0xFFFF),
                               "parameter_3F": h(g.m[b + 0x3F], 2), "flags_04": h(g.m[b + 4], 2)})
        if g.r(1) == 5:
            break
    out["state_4_defeat"] = {
        "spawn_events": events, "update_state_5_reached": upd, "saved_frame_38": g.r(0x38),
        "note": "boss update counter starts at the update that loads state 4 (frame 2 was saved); spawned children run their own scripts and are not stepped here",
    }

    # -- state 5 completion ---------------------------------------------------- #
    def completion(on_floor):
        g = Fixture(rom); g.create(); g.step(); g.force_state(3); g.step(); g.force_state(5)
        g.w(0x25, 2304 >> 8); g.w(0x27, 2304 & 255)
        g.o.word(0xD282, 1680); g.o.word(0xD280, 1600); g.o.word(0xD174, 1679)
        g.m[0xD522] = 2 if on_floor else 0
        g.m[0xDE04] = 0
        g.m[0xD502] = 0x05
        g.o.position(1700, 230)
        g.step()
        return {"player_on_floor": on_floor, "slot_type": h(g.r(0), 2), "slot_state": g.r(1), "slot_token_3E": g.r(0x3E),
                "slot_param_3F": g.r(0x3F), "score_gate": "type >= $50: no score",
                "child_type_0A_slots": [[h(a), g.m[a + 0x3F]] for a in range(0xD540, 0xD940, 0x40) if g.m[a] == 0x0A],
                "player_requested_state_D502": h(g.m[0xD502], 2), "sound_DE04": h(g.m[0xDE04], 2),
                "left_limit_D280": g.o.word(0xD280), "right_limit_D282": g.o.word(0xD282),
                "D15E": h(g.m[0xD15E], 2), "D15F": h(g.m[0xD15F], 2), "occupancy_byte_D400": h(g.m[0xD400], 2)}
    out["state_5_completion"] = [completion(False), completion(True)]
    g = Fixture(rom); g.create(); g.step(); g.force_state(5); g.m[0xD522] = 2; g.m[0xD298] = 1; g.step()
    out["state_5_completion"].append({"case": "act index D298=1", "sound_DE04": h(g.m[0xDE04], 2)})

    # -- score gate of the conversion routine ------------------------------------ #
    def score_gate(type_id):
        g = Fixture(rom); g.create(); g.w(0, type_id)
        before = bytes(g.m[0xD000:0xDF00])
        g.call_bank(0x01, 0x5F54)
        after = bytes(g.m[0xD000:0xDF00])
        changed = [0xD000 + i for i in range(len(before)) if before[i] != after[i]
                   and not SLOT <= 0xD000 + i < SLOT + 0x40]
        return {"type": h(type_id, 2), "slot_type_after": h(g.r(0), 2), "ram_changed_outside_slot": [h(a) for a in changed]}
    out["score_gate_5F54"] = [score_gate(TYPE_ID), score_gate(0x21)]

    # -- offscreen removal ------------------------------------------------------ #
    def offscreen(state, keep_alive):
        g = Fixture(rom); g.create(); g.step(); g.force_state(state)
        g.w(4, 0x42 if keep_alive else 0x00)
        g.o.word(0xD174, 0)
        g.o.word(0xD176, 0)
        g.call_bank(0x01, 0x61E1)
        return {"state": state, "flags_04_keep_alive_bit1": bool(keep_alive), "type_after": h(g.r(0), 2),
                "state_after": g.r(1)}
    out["offscreen_removal"] = [offscreen(6, False), offscreen(6, True)]

    # -- palette flash command 7 ---------------------------------------------- #
    g = Fixture(rom)
    g.o.bank(2, 0x1D); g.m[0xD12B] = 0x1D
    iy = 0xD452
    g.m[iy] = 7; g.m[iy + 1] = 0; g.m[iy + 2] = 0; g.m[iy + 3] = 0
    seq = []
    for i in range(10):
        g.o.cpu.iy = iy
        g.o.call(0x83C6)
        seq.append((g.m[0xD48F], g.m[0xD490], g.m[iy + 2], g.m[iy + 3]))
    out["palette_flash_command_7"] = {"zone": 0, "table_cpu": "0x9979", "bank": "0x1D",
                                      "per_call_D48F_D490_step_counter": [list(x) for x in seq]}
    return out


# --------------------------------------------------------------------------- #
# 3. emulated original frames (whole game, forced into THZ3)
# --------------------------------------------------------------------------- #
def _boot(rom: bytes, hook):
    from sms_frame_harness import SMS, BTN_1, BTN_2
    s = SMS(rom)
    st = {"done": False}

    def setact(m):
        m._write(0xD297, 0)
        m._write(0xD298, 2)         # THZ act 3 (zone 0, act index 2)

    s.add_pc_hook(0x07D5, setact)   # new-game init: after $D297/$D298 are cleared

    def start(m):
        if m.frame > 300 and not st["done"]:
            st["done"] = True
            hook(m)

    s.add_pc_hook(0x4E97, start)    # start-position loader return
    f = 0
    while True:
        if f < 250:
            s.pad = 0
        elif f < 700:
            s.pad = BTN_1 if f % 40 < 3 else 0
        elif not st["done"]:
            s.pad = (BTN_1 | BTN_2) if f % 60 < 10 else 0
        else:
            s.pad = 0
        s.run_frame()
        f += 1
        if st["done"] and s.mem[0xD500] == 1:
            return s
        if f > 4000:
            raise RuntimeError("did not reach gameplay")


def _boss_base(s):
    for i in range(19):
        b = 0xD540 + i * 0x40
        if s.mem[b] == TYPE_ID:
            return b
    return None


def _sound_logger(s):
    log = []
    orig = s._write

    def w(a, v):
        if a == 0xDE04 and v:
            log.append((s.frame, v))
        orig(a, v)
    s._write = w
    s.cpu.set_write_callback(w)
    return log


def emulated(rom: bytes, png_dir: Path | None) -> dict:
    def hook(m):
        m.w16(0xD2D6, 1600); m.w16(0xD2D8, 80); m.w16(0xD511, 1700); m.w16(0xD514, 230)

    def rec(s, b):
        m, u = s.mem, s.u16
        return {"state": m[b + 1], "requested": m[b + 2], "frame": m[b + 6], "timer": m[b + 7], "callback": h(u(b + 0x0C)),
                "x": u(b + 0x11), "y": u(b + 0x14), "vx": s16(u(b + 0x16)), "phase_32": m[b + 0x32],
                "health": m[b + 0x26], "screen_x": u(b + 0x1A), "flags_04": h(m[b + 4], 2)}

    result = {"evidence": "EMULATED ORIGINAL FRAME",
              "method": "original ROM booted in tools/sms_frame_harness.py; the new-game init ($07D5) is patched to zone 0 / act index 2 "
                        "(THZ3); at the start-position loader return the camera is set to (1600,80) and the player to (1700,230). "
                        "Frame numbers count harness frames after gameplay begins."}

    # ---- A: unattended intro and first patrol cycle --------------------------
    s = _boot(rom, hook)
    base_frame = s.frame
    intro, prev, seen = [], None, False
    sound = _sound_logger(s)
    art_done = None
    d3b3_set = None
    for f in range(1500):
        s.pad = 0
        if f < 150:
            s.w16(0xD511, 1700 if f < 10 else 1800); s.w16(0xD514, 230)
        else:
            s.w16(0xD511, 1700); s.w16(0xD514, 60)
        s.run_frame()
        b = _boss_base(s)
        if b is None:
            continue
        seen = True
        if s.mem[0xD3B3] and d3b3_set is None:
            d3b3_set = f
        if d3b3_set is not None and art_done is None and s.mem[0xD3B3] == 0:
            art_done = f
        key = (s.mem[b + 1], s.mem[b + 2], s.mem[b + 0x32])
        if key != prev:
            e = rec(s, b)
            e.update(frame_index=f, camera=[s.u16(0xD174), s.u16(0xD176)],
                     limits_left_right_bottom=[s.u16(0xD280), s.u16(0xD282), s.u16(0xD27E)],
                     scroll_flags=[h(s.mem[0xD15E], 2), h(s.mem[0xD15F], 2)], D44E=s.mem[0xD44E], D3B3=h(s.mem[0xD3B3], 2),
                     child_types=[h(s.mem[0xD540 + i * 0x40], 2) for i in range(19)
                                  if s.mem[0xD540 + i * 0x40] and 0xD540 + i * 0x40 != b])
            intro.append(e)
            prev = key
        if f == 200 and png_dir is not None:
            png_dir.mkdir(parents=True, exist_ok=True)
            s.save_png(str(png_dir / "emulated-state6.png"))
        if f == 200:
            cmp_ = _sat_comparison(rom, s, b)
    result["unattended_intro_and_patrol"] = {
        "events": intro, "sound_requests": _dedupe_sound(sound, base_frame),
        "dynamic_art_requested_at_frame": d3b3_set, "dynamic_art_finished_at_frame": art_done,
        "sprite_cram_after_state_3_equals_palette_0C": bytes(s.cram[16:]) == bytes(sprite_palette(rom, 0x0C)),
    }
    result["sat_comparison_state_6"] = cmp_

    # ---- B: eight attack hits, defeat, completion ------------------------------
    s = _boot(rom, hook)
    base_frame = s.frame
    sound = _sound_logger(s)
    events, hp_prev, st_prev = [], None, None
    boss_seen = False
    tail = {}
    cram_flash = []
    spawn_log = {}
    conv = None
    act_flag = None
    pstate_first20 = None
    last_cram = None
    next_level = None
    flag = {}

    def on_flag(mach):                 # $83ED: SET 4/5,(HL) on $D293 in the player state-$20 handler (bank $0C)
        if mach.slot[2] == 0x0C and "frame" not in flag:
            flag.update(frame=mach.frame - base_frame, D298=mach.mem[0xD298])
    s.add_pc_hook(0x83ED, on_flag)
    f = 0
    for f in range(4000):
        b = _boss_base(s)
        m, u = s.mem, s.u16
        if b:
            boss_seen = True
        if b and m[b + 1] in (6, 9, 12, 15, 18) and f > 200 and m[b + 0x1E] == 0:
            s.w16(0xD511, u(b + 0x11) - 20); s.w16(0xD514, u(b + 0x14)); m[0xD503] |= 2; s.w16(0xD516, 0)
        elif f >= 10 and conv is None and not (b and m[b + 1] == 5):
            s.w16(0xD511, 1800); s.w16(0xD514, 230)
        if b and m[b + 1] == 5:
            s.w16(0xD511, 1800); s.w16(0xD514, 236)   # stand on the floor so state 5 can finish
        s.pad = 0
        s.run_frame()
        b = _boss_base(s)
        m, u = s.mem, s.u16
        cram = (s.cram[29], s.cram[30])
        if last_cram is not None and cram != last_cram and b:
            cram_flash.append([f, cram[0], cram[1]])
        last_cram = cram
        if b:
            st = (m[b + 1], m[b + 2])
            if st != st_prev or m[b + 0x26] != hp_prev:
                e = rec(s, b)
                e["frame_index"] = f
                if m[b + 1] in (4, 5):
                    e["children"] = [[h(0xD540 + i * 0x40), h(m[0xD540 + i * 0x40], 2), u(0xD540 + i * 0x40 + 0x11),
                                      u(0xD540 + i * 0x40 + 0x14)] for i in range(19)
                                     if m[0xD540 + i * 0x40] and 0xD540 + i * 0x40 != b]
                events.append(e)
                st_prev, hp_prev = st, m[b + 0x26]
            if m[b + 1] == 8 and "player_at_first_hit" not in tail:
                tail["player_at_first_hit"] = {"frame_index": f, "D501_state": m[0xD501], "D503_flags": h(m[0xD503], 2),
                                               "extent_x_D52C": m[0xD52C], "extent_y_D52D": m[0xD52D],
                                               "note": "the attacker is teleported and only flagged as attacking; extents are those of the player's current frame"}
            if m[b + 1] == 4:
                for i in range(19):
                    a = 0xD540 + i * 0x40
                    if m[a] == 0x34 and a not in spawn_log:
                        spawn_log[a] = [f, u(a + 0x11), u(a + 0x14)]
        elif boss_seen and conv is None:
            conv = f
            tail.update({"frame_index": f, "slot_D700_type": h(m[0xD700], 2),
                    "objects": [[h(0xD540 + i * 0x40), h(m[0xD540 + i * 0x40], 2)] for i in range(19) if m[0xD540 + i * 0x40]],
                    "player_requested_state": m[0xD502], "camera": [u(0xD174), u(0xD176)],
                    "limits_left_right_bottom": [u(0xD280), u(0xD282), u(0xD27E)],
                    "D15E_D15F": [h(m[0xD15E], 2), h(m[0xD15F], 2)], "occupancy_D400": h(m[0xD400], 2)})
        if conv is not None:
            if pstate_first20 is None and m[0xD501] == 0x20:
                pstate_first20 = f
            if flag and act_flag is None:
                act_flag = flag["frame"]
                tail["act_complete_flag_set_at_frame"] = flag["frame"]
                tail["act_complete_flag_bit"] = 4 if flag["D298"] >= 2 else 5
                tail["player_x_at_flag"] = u(0xD511)
                tail["camera_x_at_flag"] = u(0xD174)
            if next_level is None and m[0xD297] != 0:
                next_level = f
                tail["next_zone_act_after_completion"] = [m[0xD297], m[0xD298]]
                tail["next_zone_first_seen_frame"] = f
                break
            if f - conv > 2500:
                break
    tail["player_state_20_first_frame"] = pstate_first20
    tail["frames_defeat_to_flag"] = None if act_flag is None else act_flag - conv
    tail["frames_defeat_to_next_zone"] = None if next_level is None else next_level - conv
    result["eight_hit_defeat"] = {
        "attacker": "scripted: while the boss is in a patrol/entry state (6, 9, 12, 15, 18) after frame 200 and its cooldown +$1E is 0 "
                    "the player is placed 20 px left of the boss anchor at the same Y with $D503 bit 1 (attack) set and X velocity 0",
        "events": events,
        "state_4_frame": next((e["frame_index"] for e in events if e["state"] == 4), None),
        "state_5_frame": next((e["frame_index"] for e in events if e["state"] == 5), None),
        "children_type_34_first_seen": [[h(a), v[0], v[1], v[2]] for a, v in sorted(spawn_log.items())],
        "sound_requests": _dedupe_sound(sound, base_frame),
        "sprite_palette_colors_13_14_changes": cram_flash[:40],
        "after_defeat": tail,
    }
    return result


def _dedupe_sound(log, base):
    out, prev = [], None
    for fr, v in log:
        if (v, ) != prev:
            out.append([fr - base, h(v, 2)])
        prev = (v,)
    return out


def _sat_comparison(rom, s, b) -> dict:
    """Expected SAT pieces from the decoded frame vs the game's own SAT."""
    ft = frame_table(rom)
    m, u = s.mem, s.u16
    frame = ft["frames"][m[b + 6]]
    mirrored = bool(m[b + 4] & 0x10)
    sx, sy = u(b + 0x1A), u(b + 0x1C)
    base = 0x48 if mirrored else 0
    want = set()
    for p in frame["pieces"]:
        x = (-p["x"] - 8) if mirrored else p["x"]
        want.add(((sy + p["y"]) & 0xFF, (sx + x) & 0xFF, (p["tile_offset"] + base) & 0xFF))
    have = {(y, x, n) for _, y, x, n in s.sat()}
    return {"frame_index": m[b + 6], "mirrored": mirrored, "screen_x": sx, "screen_y": sy,
            "expected_entries": len(want), "found_in_game_sat": len(want & have), "all_found": want <= have}


# --------------------------------------------------------------------------- #
def identity() -> dict:
    return {
        "verdict": "THZ boss object (proved from ROM behavior, see evidence list)",
        "machine_facing_label": "object_50 (numeric only; the word boss is used in prose after the evidence below)",
        "evidence": [
            "state machine with 8 hit points (+$26 = 8), 4 reaction pairs, contact routine that decrements health only on attack contact",
            "state 0 requests sound $8C (music class in data/sound-index-sms.csv) and sets flag $D44E",
            "state 1/2 lock the camera right/left limits and pan the camera to a fixed arena target",
            "state 3 loads act-specific art (selector $13) and a dedicated sprite palette $0C",
            "state 4 spawns explosion children and flickers; state 5 releases the camera, restores the saved right limit, "
            "requests player state $20 with the clear jingle, spawns type $0A and converts the slot to type $0F",
            "the score gate at $5F77 excludes types >= $50, so no points are awarded",
            "the act-complete flag $D293 bit 4 is set by the player's state $20 handler 181 frames after the slot conversion and the next zone loads "
            "about 1041 frames after it (emulated run)",
            "music request changes from the level music $81 (level start) to $8C when the object starts (emulated run), and $97 is requested on defeat",
        ],
        "classification": "boss (arena controller and fighter are the same object; there is no separate controller)",
    }


def known_unresolved() -> list:
    return [
        "Type $12 child (spawned by state 0, pool $D540): only its observable role is recorded (removes itself; state 2 waits for that). "
        "Its 12-byte SAT Y-buffer manipulation ($DB34..$DB3F) and purpose are not fully resolved (follow-up).",
        "Type $34 explosion child and type $0A (spawned by state 5) and type $0F (slot conversion) are not studied beyond what is recorded here (follow-ups).",
        "Palette command consumer for $D494/$D495 was identified by observed CRAM only, not fully traced.",
        "Player state $20 handler ($83A6) is only traced as far as its act-complete flag; the act-clear screen and next-level load are out of scope.",
        "Meaning of sound $8C beyond its 'music' class in the sound index; sound $C4 (explosions) and $B6 (hit) are named only by class.",
        "Screen X thresholds are compared on the low byte of +$1A; behavior for objects outside -128..383 screen X is not used by this boss.",
        "Zones other than 0 (table rows 1..7) are decoded as data only; types $33/$40-$4F share the same state table but are never placed in THZ.",
        "No Windows/GameMaker run was made; POC adapter values are not part of this study.",
    ]


def follow_ups() -> list:
    return [
        {"task": "object type $12", "why": "state 2 waits for it; SAT Y-buffer manipulation and lifetime"},
        {"task": "object type $34", "why": "explosion child, art base $A2, lifetime from parameter and +$1E"},
        {"task": "object type $0A", "why": "spawned after defeat; multiple instances appear (released animals?)"},
        {"task": "object type $0F", "why": "slot conversion target for defeated enemies and this boss"},
        {"task": "player state $20 and act-clear transition", "why": "sets $D293 bit 4 in act 3"},
    ]


def build(rom: bytes, static_only: bool = False, png_dir: Path | None = None) -> dict:
    check_rom(rom)
    report = {
        "format": 1,
        "rom_sha256": ROM_SHA256,
        "subject": "THZ3 object type $50",
        "research_only": True,
        "poc_untouched": True,
        "evidence_classes": EVIDENCE,
        "identity": identity(),
        "placement": placement(rom),
        "dispatch": dispatch(rom),
        "object_fields": {
            "+$00": "type ($50)", "+$01": "current state", "+$02": "requested state (writing it changes state)",
            "+$03": "flags (bit 7: overlap ignores player bit-6 gate; set by state 3)",
            "+$04": "render/lifetime flags (bit 1 keep alive; bit 4 mirror; bit 6 offscreen; placement flags | $40)",
            "+$05": "piece count (from frame record)", "+$06": "mapping frame", "+$07": "update timer for the current script record",
            "+$08": "tile base, unmirrored (placement aux0)", "+$09": "tile base, mirrored (placement aux1 until state 3 writes $48)",
            "+$0B": "saved state while in a reaction state", "+$0C/+$0D": "callback",
            "+$0E/+$0F": "script cursor", "+$10/+$13": "sub-pixel X/Y", "+$11/+$12": "world X", "+$14/+$15": "world Y",
            "+$16/+$17": "X velocity (8.8)", "+$18/+$19": "Y velocity (8.8; never set, stays 0)",
            "+$1A/+$1B": "screen X", "+$1C/+$1D": "screen Y", "+$1E": "contact cooldown (2 after harmful contact)",
            "+$1F": "reaction timer (20)", "+$21": "contact bits (0 above, 1 below, 2 right, 3 left; low nibble)",
            "+$25/+$27": "saved camera right limit", "+$26": "health", "+$28/+$29": "coordinate table pointer",
            "+$2A/+$2B": "frame record cursor", "+$2C": "contact extent X", "+$2D": "contact extent Y",
            "+$32": "patrol phase (0 cruise, $FF decelerate, 1 accelerate)", "+$34/+$35": "type-$12 child pointer",
            "+$38": "saved frame for the defeat flicker", "+$3A..+$3D": "saved X/Y (placement)", "+$3E": "placement token",
            "+$3F": "parameter (0 from placement; state 3 writes 1)",
            "evidence": "SOURCE-TRACED BEHAVIOR",
        },
        "routines": routine_table(rom),
        "states": state_tables(rom),
        "transitions": transitions(),
        "camera_and_level_control": {
            "evidence": "SOURCE-TRACED BEHAVIOR + CONTROLLED ROUTINE RESULT + EMULATED ORIGINAL FRAME",
            "camera_bounds": "state 0/1 raise the left limit ($D280) to the camera X every update; the trigger lowers the right limit ($D282) to camera X; "
                             "state 2 sets bottom limit $D27E and the pan target (objectX-256, objectY-160) for zone 0; "
                             "the pan then raises the right limit to 1680 and the camera settles at X 1679/1680, Y 78",
            "player_lockout": "none: the player is never frozen; only the type-$12 wait and the camera lock gate the fight",
            "music": "sound request $8C at state 0; no other music request from this object; defeat requests the act-3 clear jingle $97 (or $89)",
            "level_timer": "not touched by any $50 routine (no writes to timer variables found)",
            "act_complete": "indirect: state 5 requests player state $20, whose handler sets $D293 bit 4 (bit 5 for acts < 3)",
            "goal_end_object": "state 5 spawns type $0A (parameter 0); it is not the goal sign (type $18)",
            "terrain_mutation": "none found",
            "boss_flag": "$D44E = $D297 + 1 from state 0 onward; bank $1D background animations skip while non-zero; never cleared by this object",
            "player_state_writes": ["$D502 = $0E if it was $12 (states 0 and via $037D)", "$D3B0 = $FF damage request on non-attacking contact",
                                    "player state $0B via spring setter on top contact", "player state $1B via $8105 on attack contact",
                                    "player state $20 on defeat"],
        },
        "collision_and_damage": {
            "evidence": "SOURCE-TRACED BEHAVIOR + CONTROLLED ROUTINE RESULT",
            "contact_box": "contact extents X/Y come from the current frame record (+$2C/+$2D): 20/48 for frames 1-2, see frames[]",
            "overlap_rule": "$6328: |dx| <= playerExtX + extX and dy in [-extY, playerExtY]; least-penetration axis keeps bit pair (0/1) or (2/3); "
                            "no contact when object +$03 bit 6 is set, or when player $D503 bit 6 is set and object +$03 bit 7 is clear",
            "solid": "$034D pushes the player out along the contact axis; used in states 6, 9, 12, 15 and 18 only",
            "top_contact": "player above: player bounce (state $0B, Y velocity $FC00, $D448 = 0); boss unaffected; boss enters state S+1",
            "attack_contact": "side/below with $D503 bit 1 set: $8105 knockback (+-6.0 px/update on the contact axis), palette command 7, sound $B6, "
                              "health -1; health > 0 -> boss enters state S+2; health = 0 -> state 4 (no reaction state)",
            "plain_contact": "side/below without $D503 bit 1: $D3B0 = $FF (shared player damage) and +$1E = 2 (two-update cooldown)",
            "invulnerability": "after a hit the boss is in a reaction state for 20 updates in which no overlap routine runs",
            "power_up_note": "$D532 == 6 is NOT tested by this object (only $D503 bit 1)",
            "health": {"initial": 8, "decrement": 1, "storage": "+$26", "zero_action": "request state 4",
                       "hits_required": 8, "damage_by_top_contact": 0},
            "palette_flash": "sprite colours 13/14 flash white for 4 updates then return (command 7, zone 0 table)",
            "state_18_contact": "solid; damages a non-attacking player; knocks back an attacking player; never damages the boss",
        },
        "attack_and_spawns": {
            "evidence": "SOURCE-TRACED BEHAVIOR + CONTROLLED ROUTINE RESULT",
            "attacks": "no projectiles; the only offense is body contact while patrolling (about +-0.5 px/update sweeps)",
            "children": [
                {"type": "0x12", "by": "state 0 callback ($81A6)", "position": "slot pool $D540.. (not positioned)", "parameter": "0x97 (high byte of callback address)",
                 "lifetime": "until it removes itself (about 94 updates in the emulated run)", "purpose": "gates state 2; SAT Y-buffer effect (UNRESOLVED)"},
                {"type": "0x34", "by": "state 4 script FF 04 x5 (allocator $5EE1)",
                 "offsets": [[-8, 0], [8, 0], [0, -16], [-8, -24], [-8, -24]], "parameter": "0x04", "purpose": "explosion puffs (art base $A2)"},
                {"type": "0x0A", "by": "state 5 callback", "parameter": "0x00", "position": "slot pool $D540.. (own script positions it)",
                 "purpose": "UNRESOLVED (follow-up)"},
                {"type": "0x0F", "by": "$033E conversion of the boss slot itself", "purpose": "defeated-object effect (follow-up)"},
            ],
        },
        "graphics": None,
        "unresolved": known_unresolved(),
        "follow_up_tasks": follow_ups(),
    }
    report["graphics"] = graphics(rom, png_dir)
    if not static_only:
        report["controlled_execution"] = fixtures(rom)
        report["emulated_original_frames"] = emulated(rom, png_dir)
    return json.loads(json.dumps(report))     # JSON-native (string keys) so it compares equal to the stored cache


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("rom", type=Path)
    p.add_argument("--output", type=Path, default=OUTPUT)
    p.add_argument("--check", action="store_true")
    p.add_argument("--static-only", action="store_true")
    p.add_argument("--png", type=Path, default=None)
    a = p.parse_args()
    rom = a.rom.read_bytes()
    report = build(rom, a.static_only, a.png)
    text = json.dumps(report, indent=2) + "\n"
    if a.check:
        old = a.output.read_text(encoding="utf-8")
        if a.static_only:
            old_j = json.loads(old)
            new_j = json.loads(text)
            for k in new_j:
                if old_j.get(k) != new_j[k]:
                    print("MISMATCH", k)
                    sys.exit(1)
        elif old.replace("\r\n", "\n") != text:
            print("MISMATCH")
            sys.exit(1)
        print("object-50 cache matches ROM")
        return
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps({"output": str(a.output), "states": len(report["states"])}))


if __name__ == "__main__":
    main()
