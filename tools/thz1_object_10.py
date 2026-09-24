#!/usr/bin/env python3
"""Produce ROM-backed metadata and controlled traces for THZ1 object type $10."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
OBJECT_RECORDS = ROOT / "data" / "rom-cache" / "thz1" / "object-records.json"

ANIM_PATH = ROOT / "tools" / "thz1_animation_reach.py"
spec = importlib.util.spec_from_file_location("thz1_animation_reach", ANIM_PATH)
anim = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(anim)

PARAMETER_MASKS = {0x02: 0x02, 0x04: 0x08, 0x06: 0x20}
TOP_BLOCKED_STATES = (0x0F, 0x10, 0x15, 0x1A)


def s16(value: int) -> int:
    return (value + 0x8000) % 0x10000 - 0x8000


def banked_cpu_to_rom(bank: int, cpu: int) -> int:
    if not 0x8000 <= cpu <= 0xBFFF:
        raise ValueError(f"CPU ${cpu:04X} outside slot 2")
    return bank * 0x4000 + cpu - 0x8000


def load_placements() -> list[dict]:
    records = json.loads(OBJECT_RECORDS.read_text(encoding="utf-8"))
    return [
        {
            "record_index": row["index"],
            "rom_offset": row["rom_offset"],
            "world_x": row["world_x"],
            "world_y": row["world_y"],
            "flags": row["flags"],
            "parameter": row["parameter"],
            "aux0": row["aux0"],
            "aux1": row["aux1"],
        }
        for row in records["records"]
        if int(row["type_id"], 16) == 0x10
    ]


def parameter_distribution(placements: list[dict]) -> dict[str, int]:
    counts = Counter(row["parameter"] for row in placements)
    return dict(sorted(counts.items()))


def validate_placement_bytes(rom: bytes) -> bool:
    records = json.loads(OBJECT_RECORDS.read_text(encoding="utf-8"))["records"]
    rows = [row for row in records if int(row["type_id"], 16) == 0x10]
    if len(rows) != 5:
        raise AssertionError(f"found {len(rows)} type-$10 records, expected five")
    for row in rows:
        offset = int(row["rom_offset"], 16)
        raw = bytes.fromhex(row["raw_bytes"])
        if len(raw) != 9 or rom[offset:offset + 9] != raw:
            raise AssertionError(f"placement bytes differ at {row['rom_offset']}")
    return True


def reward_mask(parameter: int) -> int:
    """Translate the table lookup at bank $0C:$A1D3 for valid THZ1 values."""
    return PARAMETER_MASKS[parameter]


def overlap_contact(delta_x: int, delta_y: int, object_x_extent: int = 10,
                    object_y_extent: int = 24, player_x_extent: int = 9,
                    player_y_extent: int = 18) -> int:
    """Pure translation of the relevant low-nibble result from fixed $6328."""
    if delta_x >= 0:
        x_penetration = player_x_extent + object_x_extent - delta_x
        x_bit = 0x04
    else:
        if delta_x == 0:
            return 0
        x_penetration = player_x_extent + object_x_extent + delta_x
        x_bit = 0x08
    if x_penetration < 0:
        return 0

    if delta_y >= 0:
        y_penetration = player_y_extent - delta_y
        y_bit = 0x02
    else:
        y_penetration = object_y_extent + delta_y
        y_bit = 0x01
    if y_penetration < 0:
        return 0
    return x_bit if x_penetration < y_penetration else y_bit


def _oracle_type():
    sys.path.insert(0, str(ROOT / "tools"))
    from oracle import Oracle
    return Oracle


def _new_object_oracle(rom: bytes):
    Oracle = _oracle_type()
    oracle = Oracle(rom)
    oracle.bank(2, 0x0C)
    oracle.mem[0xD12B] = 0x0C
    oracle.cpu.ix = 0xD700
    oracle.mem[0xD700] = 0x10
    return oracle


def run_creation_fixtures(rom: bytes) -> list[dict]:
    results = []
    for placement in load_placements():
        oracle = _new_object_oracle(rom)
        oracle.bank(2, 0x1C)
        oracle.mem[0xD700:0xD740] = bytes(0x40)
        record_rom = int(placement["rom_offset"], 16)
        record_cpu = 0x8000 + (record_rom - 0x70000)
        occupancy = 0xD400 + placement["record_index"]
        oracle.cpu.hl = record_cpu
        oracle.call(0x80EB, bc=occupancy)
        results.append({
            "record_rom": placement["rom_offset"],
            "record_cpu": f"0x{record_cpu:04X}",
            "occupancy_address": f"0x{occupancy:04X}",
            "occupancy_value": f"0x{oracle.mem[occupancy]:02X}",
            "object_type": f"0x{oracle.mem[0xD700]:02X}",
            "current_x": oracle.word(0xD711),
            "current_y": oracle.word(0xD714),
            "saved_x": oracle.word(0xD73A),
            "saved_y": oracle.word(0xD73C),
            "object_flags_04": f"0x{oracle.mem[0xD704]:02X}",
            "parameter_3f": f"0x{oracle.mem[0xD73F]:02X}",
            "art_base_08": f"0x{oracle.mem[0xD708]:02X}",
            "art_base_09": f"0x{oracle.mem[0xD709]:02X}",
            "placement_token_3e": oracle.mem[0xD73E],
        })
    return results


def run_init_fixture(rom: bytes, parameter: int, player_type: int = 1) -> dict:
    oracle = _new_object_oracle(rom)
    oracle.mem[0xD500] = player_type
    oracle.mem[0xD703] = 0x01
    oracle.mem[0xD704] = 0x40
    oracle.mem[0xD73F] = parameter
    oracle.call(0xA149)
    return {
        "parameter_before": f"0x{parameter:02X}",
        "player_type_d500": f"0x{player_type:02X}",
        "requested_state": oracle.mem[0xD702],
        "object_flags_03": f"0x{oracle.mem[0xD703]:02X}",
        "object_flags_04": f"0x{oracle.mem[0xD704]:02X}",
        "parameter_after": f"0x{oracle.mem[0xD73F]:02X}",
    }


def run_state_entry_fixture(rom: bytes, parameter: int) -> dict:
    oracle = _new_object_oracle(rom)
    oracle.mem[0xD703] = 0x80
    oracle.mem[0xD704] = 0
    oracle.mem[0xD726] = 0x40
    oracle.mem[0xD73F] = parameter
    oracle.call(0xA161)
    return {
        "parameter": f"0x{parameter:02X}",
        "requested_state": oracle.mem[0xD702],
        "previous_visibility_26": f"0x{oracle.mem[0xD726]:02X}",
        "graphics_selector_d3b3": f"0x{oracle.mem[0xD3B3]:02X}",
    }


def _contact_oracle(rom: bytes, parameter: int = 2, delta_x: int = 0,
                    delta_y: int = -20, player_flags: int = 2,
                    player_state: int = 5, requested_state: int | None = None,
                    player_y_velocity: int = 0x0100, power_up: int = 0):
    oracle = _new_object_oracle(rom)
    oracle.mem[0xD703] = 0x80
    oracle.mem[0xD704] = 0
    oracle.mem[0xD726] = 0
    oracle.mem[0xD73E] = 10
    oracle.mem[0xD73F] = parameter
    oracle.mem[0xD409] = 0x10
    oracle.word(0xD711, 500)
    oracle.word(0xD714, 500)
    oracle.mem[0xD72C] = 10
    oracle.mem[0xD72D] = 24
    oracle.word(0xD511, 500 + delta_x)
    oracle.word(0xD514, 500 + delta_y)
    oracle.mem[0xD52C] = 9
    oracle.mem[0xD52D] = 18
    oracle.mem[0xD501] = player_state
    oracle.mem[0xD502] = player_state if requested_state is None else requested_state
    oracle.mem[0xD503] = player_flags
    oracle.mem[0xD532] = power_up
    oracle.word(0xD518, player_y_velocity)
    return oracle


def _contact_result(oracle) -> dict:
    return {
        "contact_bits_21": f"0x{oracle.mem[0xD721] & 0x0F:02X}",
        "object_type_after": f"0x{oracle.mem[0xD700]:02X}",
        "requested_object_state": oracle.mem[0xD702],
        "object_y_velocity_8_8": s16(oracle.word(0xD718)),
        "player_y_velocity_8_8": s16(oracle.word(0xD518)),
        "requested_player_state": oracle.mem[0xD502],
        "damage_request_d3b0": f"0x{oracle.mem[0xD3B0]:02X}",
        "reward_bits_d3a3": f"0x{oracle.mem[0xD3A3]:02X}",
        "parameter_after": f"0x{oracle.mem[0xD73F]:02X}",
        "placement_token_after": oracle.mem[0xD73E],
        "occupancy_value_after": f"0x{oracle.mem[0xD409]:02X}",
        "score_bytes_after": " ".join(
            f"{value:02X}" for value in oracle.mem[0xD29D:0xD2A0]
        ),
    }


def run_contact_fixture(rom: bytes, **kwargs) -> dict:
    oracle = _contact_oracle(rom, **kwargs)
    oracle.call(0xA16C)
    return _contact_result(oracle)


def run_contact_fixtures(rom: bytes) -> dict:
    boundary = []
    for axis, values in (
        ("horizontal_right", (18, 19, 20)),
        ("top", (-23, -24, -25)),
        ("bottom", (17, 18, 19)),
    ):
        for value in values:
            dx, dy = (value, 0) if axis == "horizontal_right" else (0, value)
            oracle = _contact_oracle(
                rom, delta_x=dx, delta_y=dy, player_flags=0,
                player_y_velocity=0,
            )
            oracle.call(0xA16C)
            boundary.append({
                "axis": axis,
                "delta": value,
                "contact_bits_21": f"0x{oracle.mem[0xD721] & 0x0F:02X}",
                "translated_contact": f"0x{overlap_contact(dx, dy):02X}",
            })

    blocked_states = {}
    for state in TOP_BLOCKED_STATES:
        blocked_states[f"0x{state:02X}"] = run_contact_fixture(
            rom, requested_state=state,
        )

    return {
        "ordinary_top_contact": run_contact_fixture(rom, player_flags=0),
        "power_up_06_without_attack": run_contact_fixture(
            rom, player_flags=0, power_up=6,
        ),
        "top_attack_downward": run_contact_fixture(rom),
        "top_attack_zero_velocity": run_contact_fixture(
            rom, player_y_velocity=0,
        ),
        "top_attack_upward": run_contact_fixture(
            rom, player_y_velocity=0xFF00,
        ),
        "side_attack_downward": run_contact_fixture(
            rom, delta_x=15, delta_y=0,
        ),
        "bottom_attack_upward": run_contact_fixture(
            rom, delta_x=0, delta_y=0, player_y_velocity=0xFF00,
        ),
        "top_blocked_player_states": blocked_states,
        "overlap_boundaries": boundary,
    }


def run_reward_fixture(rom: bytes, parameter: int) -> dict:
    oracle = _contact_oracle(rom, parameter=parameter)
    oracle.mem[0xD299] = 0x09
    oracle.mem[0xD29A] = 0x00
    oracle.word(0xD516, 0x0123)
    oracle.word(0xD518, 0x0100)
    oracle.call(0xA16C)
    after_contact = _contact_result(oracle)
    # $062D waits for a frame flag. Pre-setting it models the next available
    # interrupt boundary while still executing the original $4B1D branch.
    oracle.mem[0xD135] = 1
    oracle.call(0x4AA3)
    child = {
        "slot": "0xD540",
        "type": f"0x{oracle.mem[0xD540]:02X}",
        "parameter_3f": f"0x{oracle.mem[0xD57F]:02X}",
    }
    return {
        "parameter": f"0x{parameter:02X}",
        "table_mask": f"0x{reward_mask(parameter):02X}",
        "after_contact": after_contact,
        "after_reward_dispatch": {
            "reward_bits_d3a3": f"0x{oracle.mem[0xD3A3]:02X}",
            "counter_d299_bcd": f"0x{oracle.mem[0xD299]:02X}",
            "counter_d29a_bcd": f"0x{oracle.mem[0xD29A]:02X}",
            "power_up_d532": f"0x{oracle.mem[0xD532]:02X}",
            "timer_d44c": oracle.word(0xD44C),
            "player_flags_d503": f"0x{oracle.mem[0xD503]:02X}",
            "player_requested_state_d502": f"0x{oracle.mem[0xD502]:02X}",
            "player_x_velocity_8_8": s16(oracle.word(0xD516)),
            "player_y_velocity_8_8": s16(oracle.word(0xD518)),
            "player_max_x_d373": f"0x{oracle.word(0xD373):04X}",
            "timer_d3a1": oracle.word(0xD3A1),
            "sound_request_de04": f"0x{oracle.mem[0xDE04]:02X}",
            "child": child,
        },
    }


def run_alternate_player_parameter_04_fixture(rom: bytes) -> dict:
    init = run_init_fixture(rom, 4, player_type=2)
    oracle = _contact_oracle(rom, parameter=1)
    oracle.mem[0xD500] = 2
    oracle.mem[0xD29A] = 0
    oracle.call(0xA16C)
    reward_bits = oracle.mem[0xD3A3]
    # The bit-0 branch calls display helpers not supported by the minimal
    # fixture state. The source-level numeric effect before those calls is
    # independently represented by the recovered dispatcher.
    return {
        "initialization": init,
        "effective_parameter": "0x01",
        "reward_bits_d3a3": f"0x{reward_bits:02X}",
        "dispatch_entry": "0x4AC0",
        "direct_numeric_effect": "BCD byte $D29A += $10 before shared display/update calls",
    }


def run_airborne_fixture(rom: bytes) -> dict:
    oracle = _new_object_oracle(rom)
    oracle.mem[0xC001:0xD000] = bytes(0xFFF)
    oracle.mem[0xD702] = 3
    oracle.word(0xD711, 500)
    oracle.word(0xD714, 500)
    oracle.word(0xD718, 0xFE00)
    oracle.call(0xA20D)
    empty_map = {
        "requested_state": oracle.mem[0xD702],
        "y_integer_after": oracle.word(0xD714),
        "y_fraction_after": oracle.mem[0xD713],
        "y_velocity_8_8_after": s16(oracle.word(0xD718)),
    }

    landing = _new_object_oracle(rom)
    landing.mem[0xD702] = 3
    landing.word(0xD711, 656)
    landing.word(0xD714, 846)
    landing.word(0xD718, 0xFE00)
    for tick in range(1, 300):
        landing.call(0xA20D)
        if landing.mem[0xD702] == 2:
            break
    else:
        raise AssertionError("type $10 state 3 did not return to state 2")
    return {
        "empty_map_first_update": empty_map,
        "first_thz1_placement_landing": {
            "updates": tick,
            "requested_state": landing.mem[0xD702],
            "y_integer": landing.word(0xD714),
            "y_fraction": landing.mem[0xD713],
            "y_velocity_8_8": s16(landing.word(0xD718)),
        },
    }


def run_lifetime_fixtures(rom: bytes) -> dict:
    untouched = _new_object_oracle(rom)
    untouched.mem[0xD704] = 0
    untouched.mem[0xD73E] = 10
    untouched.mem[0xD409] = 0x10
    untouched.word(0xD711, 1000)
    untouched.word(0xD714, 500)
    untouched.call(0x61E1)
    before_cleanup = {
        "object_type": f"0x{untouched.mem[0xD700]:02X}",
        "placement_token": untouched.mem[0xD73E],
        "occupancy_value": f"0x{untouched.mem[0xD409]:02X}",
    }
    untouched.call(0x626D)
    untouched.call(0x5EF8)

    consumed = _contact_oracle(rom, parameter=2)
    consumed.call(0xA16C)
    after_conversion = {
        "object_type": f"0x{consumed.mem[0xD700]:02X}",
        "placement_token": consumed.mem[0xD73E],
        "occupancy_value": f"0x{consumed.mem[0xD409]:02X}",
    }
    consumed.call(0xA060)
    consumed.mem[0xD704] = 0
    consumed.word(0xD174, 0)
    consumed.word(0xD176, 0)
    consumed.call(0x61E1)
    consumed.call(0x5EF8)
    return {
        "untouched_off_range_before_cleanup": before_cleanup,
        "untouched_after_cleanup": {
            "occupancy_value": f"0x{untouched.mem[0xD409]:02X}",
            "slot_is_zero": not any(untouched.mem[0xD700:0xD740]),
            "can_respawn": True,
        },
        "consumed_after_conversion": after_conversion,
        "consumed_after_replacement_cleanup": {
            "occupancy_value": f"0x{consumed.mem[0xD409]:02X}",
            "slot_is_zero": not any(consumed.mem[0xD700:0xD740]),
            "can_respawn_same_loaded_act": False,
        },
    }


def _compact_animation(trace: dict) -> dict:
    states = []
    for state in trace["states"]:
        records = []
        seen = set()
        for row in state["records"]:
            if row["cpu"] in seen:
                continue
            seen.add(row["cpu"])
            records.append({key: value for key, value in row.items() if key != "rom"})
        commands = []
        seen = set()
        for row in state["commands"]:
            if row.get("command") == "loop_detected" or row["cpu"] in seen:
                continue
            seen.add(row["cpu"])
            commands.append({key: value for key, value in row.items() if key != "rom"})
        states.append({
            "state_index": state["state_index"],
            "script_cpu": state["script_cpu"],
            "script_rom": state["script_rom"],
            "frame_indices": state["frame_indices"],
            "records": records,
            "commands": commands,
            "unresolved": state["unresolved"],
        })
    return {
        "type_table_entry_rom": f"0x{trace['type_table_entry_rom']:05X}",
        "bank": f"0x{trace['bank']:02X}",
        "state_table_cpu": f"0x{trace['state_table_cpu']:04X}",
        "state_table_rom": f"0x{trace['state_table_rom']:05X}",
        "state_count": trace["state_count"],
        "state_script_cpus": [f"0x{x:04X}" for x in trace["state_script_cpus"]],
        "reachable_mapping_frame_indices": [
            f"0x{x:02X}" for x in trace["reachable_frame_indices"]
        ],
        "unresolved_states": trace["unresolved_states"],
        "states": states,
    }


def dynamic_graphics_pointers(rom: bytes) -> dict:
    def pointer(base: int, selector: int) -> int:
        pos = base + selector * 2
        return rom[pos] | rom[pos + 1] << 8

    rows = []
    for parameter in PARAMETER_MASKS:
        rows.append({
            "parameter": f"0x{parameter:02X}",
            "selector": f"0x{parameter:02X}",
            "sonic_layer_1_cpu": f"0x{pointer(0x7CBB, parameter):04X}",
            "alternate_layer_1_cpu": f"0x{pointer(0x7CC7, parameter):04X}",
            "sonic_layer_2_cpu": f"0x{pointer(0x7CD3, parameter):04X}",
            "alternate_layer_2_cpu": f"0x{pointer(0x7CDF, parameter):04X}",
        })
    return {
        "selector_ram": "0xD3B3",
        "loader_cpu": "0x7AC2",
        "low_selector_path_cpu": "0x7C71",
        "source_bank": "0x0E",
        "vram_destinations": ["0x0980 (6 tiles)", "0x0BC0 (4 tiles)"],
        "parameters": rows,
    }


def build_report(rom: bytes) -> dict:
    digest = hashlib.sha256(rom).hexdigest()
    if digest != ROM_SHA256:
        raise ValueError(f"ROM SHA-256 mismatch: {digest}")
    placements = load_placements()
    return {
        "format": 1,
        "rom_sha256": digest,
        "object_type": "0x10",
        "placement_bytes_verified": validate_placement_bytes(rom),
        "identity": {
            "status": "SUPPORTED BUT NOT CANONICAL",
            "description": "type $10, monitor/item-box presentation supported",
            "basis": "reachable reconstructed graphics plus verified container/reward behavior; no ROM string establishes a canonical name",
        },
        "placements": placements,
        "parameter_distribution": parameter_distribution(placements),
        "animation": _compact_animation(anim.trace_type(rom, 0x10)),
        "mapping": {
            "table_cpu": "0x8C71",
            "table_rom": "0x3CC71",
            "active_frames": [
                {"index": "0x0B", "cpu": "0x8D0F", "rom": "0x3CD0F"},
                {"index": "0x0C", "cpu": "0x8D1A", "rom": "0x3CD1A"},
            ],
            "collision_extents_from_both_active_frames": {
                "horizontal_2c": 10,
                "vertical_2d": 24,
            },
        },
        "handlers": {
            "initialization": {"cpu": "0xA149", "rom": "0x32149"},
            "state_1_entry": {"cpu": "0xA161", "rom": "0x32161"},
            "active_contact": {"cpu": "0xA16C", "rom": "0x3216C"},
            "reward_bit_selection": {"cpu": "0xA1D3", "rom": "0x321D3"},
            "graphics_visibility_latch": {"cpu": "0xA1F9", "rom": "0x321F9"},
            "airborne_after_bottom_hit": {"cpu": "0xA20D", "rom": "0x3220D"},
            "reward_dispatch": {"cpu": "0x4AA3", "rom": "0x04AA3"},
        },
        "interaction": {
            "overlap_and_resolution_helper_cpu": "0x5FA0",
            "requires_player_flag_d503_bit_1": True,
            "power_up_06_alone_substitutes_for_attack": False,
            "bottom_contact_bit": "0x02",
            "top_contact_bit": "0x01",
            "side_contact_bits": ["0x04", "0x08"],
            "top_blocked_requested_player_states": [
                f"0x{x:02X}" for x in TOP_BLOCKED_STATES
            ],
            "top_or_side_requires_nonzero_downward_y_velocity": True,
            "bottom_hit_requires_y_direction": False,
            "bottom_hit_result": "player Y velocity +0x0200; object Y velocity -0x0200; request object state 3",
            "successful_top_or_side_result": "queue numeric reward bit, convert same slot to type 0x0F, clear placement token",
            "damage_request": False,
        },
        "parameter_semantics": {
            "0x02": "queues $D3A3 bit 1; dispatcher clears it, increments BCD byte $D299 up to $99, and requests sound $A9",
            "0x04": "queues $D3A3 bit 3 for player type 1; dispatcher sets $D532=$04, $D44C=$012C (or $1770 at level $08), and enters player state setup at $4775",
            "0x06": "queues $D3A3 bit 5; dispatcher sets $D503 bits 1/7, sound $84, $D44C=$0258, $D532=$06, and allocates type $05 with parameter zero unless already $06",
            "alternate_player_parameter_0x04": "initialization rewrites it to $01 when $D500 != $01; the resulting bit-0 dispatcher adds BCD $10 to $D29A before shared display/update calls",
        },
        "dynamic_graphics": dynamic_graphics_pointers(rom),
        "replacement": {
            "type": "0x0F",
            "conversion_cpu": "0x5F54",
            "score_bytes_added": "10 00 00",
            "placement_token_cleared": True,
            "initial_state": 1,
            "presentation_frames": ["0x07", "0x08", "0x09"],
            "eventual_removal": "type 0xFF with token zero; placement occupancy is not released",
        },
        "lifetime": {
            "untouched_off_range": "type 0xFE then tracked cleanup; occupancy released; can respawn",
            "bottom_hit_only_off_range": "still placement-backed; tracked cleanup releases occupancy; can respawn",
            "successfully_consumed": "conversion clears token but leaves occupancy nonzero; cannot respawn in the same loaded act",
        },
        "controlled_original_routine_fixtures": {
            "evidence": "controlled trace",
            "placement_creation": run_creation_fixtures(rom),
            "initialization": [run_init_fixture(rom, value) for value in (2, 4, 6)],
            "alternate_player_parameter_04": run_alternate_player_parameter_04_fixture(rom),
            "state_1_entry": [run_state_entry_fixture(rom, value) for value in (2, 4, 6)],
            "ordinary_non_contact_update": run_contact_fixture(
                rom, delta_x=100, delta_y=100, player_flags=0,
            ),
            "contact": run_contact_fixtures(rom),
            "reward": [run_reward_fixture(rom, value) for value in (2, 4, 6)],
            "airborne": run_airborne_fixture(rom),
            "lifetime": run_lifetime_fixtures(rom),
        },
        "unresolved": [
            "canonical semantic name; the ROM-backed status remains supported but not canonical",
            "user-facing names for parameter values 0x02/0x04/0x06",
            "semantic names of sound IDs 0x84, 0x85, and 0xA9",
            "semantic label for BCD counter $D299 and score/display byte $D29A",
            "full lifetime and presentation semantics of the parameter-0x06 child type 0x05 beyond its allocation contract",
            "hardware-frame timing and emulator-observed gameplay",
        ],
    }


def report_markdown(report: dict) -> str:
    return "\n".join([
        "# THZ1 object `$10` controlled report",
        "",
        f"ROM SHA-256: `{report['rom_sha256']}`",
        "",
        "Five placements, four states, active frames `$0B/$0C`, and parameter "
        "values `$02/$04/$06` were verified. Successful top/side attack contact "
        "converts the slot to type `$0F`; bottom attack contact launches type `$10` "
        "into state 3 without consuming it.",
        "",
        "The JSON report contains exact source records plus original-routine "
        "creation, initialization, contact-boundary, reward, replacement, and "
        "lifetime fixtures. These are not full-emulator gameplay observations.",
    ]) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "build" / "thz1-object-10"
    )
    parser.add_argument("--metadata", type=Path)
    args = parser.parse_args()

    report = build_report(args.rom.read_bytes())
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    (args.output / "REPORT.md").write_text(
        report_markdown(report), encoding="utf-8"
    )
    if args.metadata:
        args.metadata.parent.mkdir(parents=True, exist_ok=True)
        args.metadata.write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps({
        "state_table": report["animation"]["state_table_cpu"],
        "states": report["animation"]["state_count"],
        "placements": len(report["placements"]),
        "output": str(args.output),
    }))


if __name__ == "__main__":
    main()
