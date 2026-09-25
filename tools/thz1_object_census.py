#!/usr/bin/env python3
"""Generate the metadata-only THZ1 placed-object census.

The placement population comes from the committed object-record cache and is
checked byte-for-byte against the matching ROM.  Animation and mapping facts
are obtained through the existing verified decoders; curated research-status
text only summarizes evidence already committed elsewhere in this repository.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import thz1_animation_reach as animation
import thz1_object_assets as assets

EXPECTED_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
PLACED_TYPES = (0x09, 0x10, 0x18, 0x1B, 0x21, 0x26, 0x27, 0x28)
RECORDS_PATH = ROOT / "data" / "rom-cache" / "thz1" / "object-records.json"
GRAPHICS_PATH = ROOT / "data" / "rom-cache" / "thz1" / "graphics-map.json"
LAYOUT_PATH = ROOT / "data" / "rom-cache" / "thz1" / "layout-interactions.json"
REGIONS_PATH = ROOT / "asm" / "recovered" / "regions.json"
OBJECT_21_PATH = ROOT / "data" / "rom-cache" / "thz1" / "object-21.json"
OBJECT_27_PATH = ROOT / "data" / "rom-cache" / "thz1" / "object-27.json"
OBJECT_10_PATH = ROOT / "data" / "rom-cache" / "thz1" / "object-10.json"
DEFAULT_OUTPUT = ROOT / "data" / "rom-cache" / "thz1" / "object-census.json"


PROFILES = {
    0x09: {
        "role": "ring / sparkle graphics family",
        "semantic_status": "LIKELY / SUPPORTED BUT NOT CANONICAL",
        "semantic_basis": "Reachable reconstructed frames show ring and sparkle graphics; the ROM evidence cited here does not establish a canonical name for every state.",
        "graphics_completeness": "VERIFIED for statically reachable frames 0x00-0x06",
        "animation_completeness": "VERIFIED for all four statically decoded states",
        "behavior_completeness": "UNRESOLVED",
        "lifetime_contact_completeness": "UNRESOLVED",
        "poc_readiness": "PLACEMENT DATA READY; ORIGINAL OBJECT EXPANSION/BEHAVIOR NOT READY",
        "graphics_class": "static THZ1 VRAM",
        "graphics_load_ids": ["thz1_common_base_10"],
        "graphics_note": "The shared mapping uses absolute tile offsets 0x10-0x22 with placement art bases 0x00/0x00.",
        "renderer_note": "All THZ1 placement flags are 0x00; no placement-requested X mirror is present.",
        "collision": None,
        "handlers": [],
        "artifacts": ["tools/thz1_object_assets.py", "tools/thz1_animation_reach.py", "data/rom-cache/thz1/object-graphics-map.json", "docs/thz1-object-graphics.md"],
        "gaps": [
            "Trace what parameter 0x00 versus 0x01 means for the 24 raw records.",
            "Establish how the object stream relates to generated game entities; do not equate 24 records with the separately decoded 142 layout-ring positions.",
            "Trace collection, sparkle-state selection, persistence, and respawn behavior."
        ],
    },
    0x10: {
        "role": "monitor / item-box presentation",
        "semantic_status": "LIKELY / SUPPORTED BUT NOT CANONICAL",
        "semantic_basis": "Reachable reconstructed frames support monitor/item-box presentation; recovered handlers establish a breakable numeric-reward container, but no ROM string establishes a canonical name.",
        "graphics_completeness": "VERIFIED for statically reachable frames 0x00, 0x0B, 0x0C",
        "animation_completeness": "VERIFIED for all four statically decoded states",
        "behavior_completeness": "VERIFIED for THZ1-reachable behavior",
        "lifetime_contact_completeness": "VERIFIED",
        "poc_readiness": "RESEARCH READY FOR NUMERIC-TYPE IMPLEMENTATION",
        "graphics_class": "static THZ1 VRAM",
        "graphics_load_ids": ["thz1_common_base_10"],
        "graphics_note": "Active frames 0x0B/0x0C use absolute tile offsets 0x4C-0x5C with placement art bases 0x00/0x00; the placement parameter also drives the low dynamic selector path at $D3B3.",
        "renderer_note": "All THZ1 placement flags are 0x00; no placement-requested X mirror is present.",
        "collision": {"status": "VERIFIED", "horizontal_extent": 10, "vertical_extent": 24, "facts": ["Interaction requires player movement flag $D503 bit 1.", "Top/side success requires nonzero downward Y velocity; bottom contact instead launches the object and player apart."]},
        "handlers": ["object_10_scripts.asm", "object_10_handlers.asm", "object_10_reward_masks.asm", "object_10_tail_handlers.asm", "object_0f_scripts.asm", "object_0f_handlers.asm", "object_reward_dispatch.asm", "numeric_reward_counter.asm"],
        "artifacts": ["docs/object-10.md", "tools/thz1_object_10.py", "tests/test_thz1_object_10.py", "data/rom-cache/thz1/object-10.json"],
        "gaps": [
            "Canonical semantic name remains unverified; monitor/item-box presentation is supported but not canonical.",
            "User-facing names for numeric parameters 0x02/0x04/0x06 and affected RAM fields remain deliberately unassigned.",
            "The complete presentation/lifetime semantics of the parameter-0x06 child type 0x05 remain outside this focused study.",
            "No full-emulator gameplay observation exists; verification uses source tracing and controlled original-routine fixtures."
        ],
    },
    0x18: {
        "role": "end-of-act goal-sign/signpost presentation",
        "semantic_status": "LIKELY / SUPPORTED BUT NOT CANONICAL",
        "semantic_basis": "The verified dynamic VRAM loads reconstruct a coherent rotating goal sign; completion logic has not received a dedicated behavior study.",
        "graphics_completeness": "VERIFIED dynamic load path and reachable frames 0x00-0x05",
        "animation_completeness": "VERIFIED for all seven statically decoded states",
        "behavior_completeness": "PARTIALLY ESTABLISHED",
        "lifetime_contact_completeness": "UNRESOLVED",
        "poc_readiness": "GRAPHICS READY; COMPLETION BEHAVIOR NOT READY",
        "graphics_class": "dynamically loaded",
        "graphics_load_ids": ["dynamic_selector_0x12"],
        "graphics_note": "Selector RAM 0xD3B3 receives 0x12; loads replace tiles 0x6A-0xA9 from ROM 0x356BC and 0x24640.",
        "renderer_note": "The sole THZ1 placement has flags 0x00 and art bases 0x00/0x00; mapping tile values are supplied by the dynamic load.",
        "collision": None,
        "handlers": [],
        "artifacts": ["tools/thz1_type18_dynamic_graphics.py", "tools/thz1_animation_reach.py", "data/rom-cache/thz1/object-graphics-map.json", "docs/thz1-object-graphics.md"],
        "gaps": [
            "Formally trace trigger/contact and end-of-act completion logic.",
            "Trace lifetime, state timing, and any stage-results transition.",
            "Assign semantic meanings to animation states/frames only where behavior proves them."
        ],
    },
    0x1B: {
        "role": "retracting/moving spikes",
        "semantic_status": "VERIFIED",
        "semantic_basis": "Recovered handlers and scripts establish the rise, active damage, retract, and hidden phases.",
        "graphics_completeness": "VERIFIED reachable frame 0x0E",
        "animation_completeness": "VERIFIED for all five states",
        "behavior_completeness": "SUBSTANTIALLY VERIFIED",
        "lifetime_contact_completeness": "PARTIAL: active damage phases verified; camera activation/despawn not formally studied",
        "poc_readiness": "CORE STATE MACHINE READY; LIFETIME/INTEGRATION CHECKS REMAIN",
        "graphics_class": "static THZ1 VRAM",
        "graphics_load_ids": ["thz1_common_base_10"],
        "graphics_note": "Shared mapping frame 0x0E uses absolute tile offsets 0x62/0x64 with art bases 0x00/0x00.",
        "renderer_note": "All THZ1 placement flags are 0x00; no placement-requested X mirror is present.",
        "collision": {"status": "PARTIAL", "facts": ["Damage/contact helper runs in rising state 1 and raised state 2, not retracting/hidden states 3/4."]},
        "handlers": ["spike_object_handlers.asm", "spike_object_scripts.asm"],
        "artifacts": ["docs/act1-objects.md", "reports/windows-poc-15-objects.json", "asm/recovered/spike_object_handlers.asm", "asm/recovered/spike_object_scripts.asm"],
        "gaps": ["Formally trace camera activation, removal, occupancy release, and respawn.", "Verify complete damage aftermath and gameplay scheduling beyond selected handler comparisons."],
    },
    0x21: {
        "role": "ground patrol with spring-like top contact",
        "semantic_status": "LIKELY / SUPPORTED BUT NOT CANONICAL",
        "semantic_basis": "Behavior, sprite structure, and contact response are verified, but the possible canonical identity remains explicitly non-verified.",
        "graphics_completeness": "VERIFIED reachable frames 0x00-0x02 and both art bases",
        "animation_completeness": "VERIFIED for all seven states",
        "behavior_completeness": "VERIFIED for THZ1-reachable behavior",
        "lifetime_contact_completeness": "VERIFIED",
        "poc_readiness": "RESEARCH READY FOR IMPLEMENTATION",
        "graphics_class": "static THZ1 VRAM plus remapped supplemental graphics",
        "graphics_load_ids": ["thz1_base_86", "thz1_base_98_remap"],
        "graphics_note": "Renderer selects aux0 0x86 normally and remapped aux1 0x98 while X-mirrored.",
        "renderer_note": "Patrol scripts set bit 4 for negative-X orientation and clear it for positive-X orientation; bit 4 selects aux1 and mirrors piece coordinates.",
        "collision": {"status": "VERIFIED", "horizontal_extent": 11, "vertical_extent": 26, "facts": ["Top-contact comparison uses object_y - 4 against player integer Y."]},
        "handlers": ["object_21_handlers.asm", "object_21_scripts.asm"],
        "artifacts": ["docs/object-21.md", "tools/thz1_object_21.py", "tests/test_thz1_object_21.py", "data/rom-cache/thz1/object-21.json"],
        "gaps": ["Canonical semantic identity remains unverified.", "Full-emulator/gameplay observation is absent; the formal study uses source tracing and controlled original-routine fixtures."],
    },
    0x26: {
        "role": "concealed/contact spring",
        "semantic_status": "VERIFIED",
        "semantic_basis": "Recovered fixed and span handlers establish the spring contacts, impulses, extension, hold, and retraction paths.",
        "graphics_completeness": "VERIFIED reachable frames 0x00-0x03",
        "animation_completeness": "VERIFIED for all ten states",
        "behavior_completeness": "SUBSTANTIALLY VERIFIED",
        "lifetime_contact_completeness": "PARTIAL: contact/state machine verified; camera lifetime not formally studied",
        "poc_readiness": "CORE STATE MACHINE READY; INTEGRATION CHECKS REMAIN",
        "graphics_class": "static THZ1 VRAM supplemental graphics",
        "graphics_load_ids": ["thz1_base_72"],
        "graphics_note": "All four records use aux0/aux1 0x72 from the THZ1 supplemental stream.",
        "renderer_note": "All THZ1 placement flags are 0x00; no placement-requested X mirror is present.",
        "collision": {"status": "PARTIAL", "facts": ["Fixed contact rejects upward motion, missing floor/object contact, and player state 0x21.", "Vertical contact is measured against object_y - 28."]},
        "handlers": ["object_26_handlers.asm", "object_26_scripts.asm", "object_26_span_handlers.asm", "object_26_span_scripts.asm"],
        "artifacts": ["docs/act1-objects.md", "reports/windows-poc-15-objects.json", "asm/recovered/object_26_handlers.asm", "asm/recovered/object_26_span_handlers.asm"],
        "gaps": ["Formally trace camera activation, removal, occupancy release, and respawn.", "Verify complete scheduler/animation timing and gameplay contacts for all four placements."],
    },
    0x27: {
        "role": None,
        "semantic_status": "UNRESOLVED",
        "semantic_basis": "No semantic identity is established by the recovered ROM/source evidence.",
        "graphics_completeness": "VERIFIED reachable frames 0x00-0x02",
        "animation_completeness": "VERIFIED for all four states",
        "behavior_completeness": "VERIFIED for THZ1-reachable behavior",
        "lifetime_contact_completeness": "VERIFIED, except broader downstream interpretation of ordinary overlap bookkeeping",
        "poc_readiness": "RESEARCH READY FOR NUMERIC-TYPE IMPLEMENTATION",
        "graphics_class": "remapped supplemental graphics",
        "graphics_load_ids": ["thz1_base_AA_remap"],
        "graphics_note": "All placements use aux0/aux1 0xAA from the remapped supplemental stream.",
        "renderer_note": "Placement bit 4 is set for all records; it selects mirrored X coordinates and aux1 (also 0xAA), and causes FF 02 to negate X velocity.",
        "collision": {"status": "VERIFIED", "horizontal_extent": 9, "vertical_extent": 14, "facts": ["Ordinary overlap records generic contact but the tested callback does not request damage."]},
        "handlers": ["object_27_handlers.asm", "object_27_scripts.asm"],
        "artifacts": ["docs/object-27.md", "tools/thz1_object_27.py", "tests/test_thz1_object_27.py", "data/rom-cache/thz1/object-27.json"],
        "gaps": ["Semantic identity remains unresolved.", "Broader downstream meaning of generic contact bookkeeping on ordinary overlap is unresolved.", "No full-emulator gameplay observation exists for the formal trace."],
    },
    0x28: {
        "role": "moving platforms",
        "semantic_status": "VERIFIED",
        "semantic_basis": "Decoded placements and recovered platform code establish two lift records and four parameter-0x84 sag/bob platform records.",
        "graphics_completeness": "VERIFIED reachable decoded frames 0x00-0x01",
        "animation_completeness": "VERIFIED static reachability for all 15 states; command 0x09 is object[offset] = immediate and states 4/12/14 resolve to frame 0x01",
        "behavior_completeness": "PARTIALLY ESTABLISHED",
        "lifetime_contact_completeness": "PARTIAL: rider paths recovered; activation/despawn and edge cases remain",
        "poc_readiness": "PARTIAL ADAPTER EVIDENCE; FORMAL PLATFORM STUDY STILL NEEDED",
        "graphics_class": "static THZ1 VRAM supplemental graphics",
        "graphics_load_ids": ["thz1_base_6A"],
        "graphics_note": "All placements use aux0 0x6A; aux1 varies by record and is consumed by platform initialization as object-specific data, so it must not be treated uniformly as a second art base.",
        "renderer_note": "All placement flags are 0x00. Do not infer later orientation changes solely from the state table.",
        "collision": {"status": "PARTIAL", "facts": ["Recovered code includes rider/contact paths, but the census does not claim complete platform edge extents."]},
        "handlers": ["platform_code.asm", "platform_reverse.asm"],
        "artifacts": ["docs/audit-2026-09-21.md", "data/legacy/thz1_platforms.json", "asm/recovered/platform_code.asm", "asm/recovered/platform_reverse.asm"],
        "gaps": ["Formally trace subtype parameters 0x0A and 0x84, including activation, rider edges, removal, occupancy, and respawn.", "Separate verified original behavior from earlier adapter/video observations."],
    },
}

EVIDENCE_LEVELS = {
    0x09: ["decoded data", "decoded graphics/mapping metadata"],
    0x10: ["decoded data", "decoded graphics/mapping metadata", "byte-verified assembly", "source-traced behavior", "controlled original-Z80 trace"],
    0x18: ["decoded data", "decoded graphics/mapping metadata", "source-traced dynamic graphics path"],
    0x1B: ["decoded data", "byte-verified assembly", "source-traced behavior", "controlled original-Z80 trace (selected handlers)"],
    0x21: ["decoded data", "byte-verified assembly", "source-traced behavior", "controlled original-Z80 trace"],
    0x26: ["decoded data", "byte-verified assembly", "source-traced behavior", "controlled original-Z80 trace (selected handlers)"],
    0x27: ["decoded data", "byte-verified assembly", "source-traced behavior", "controlled original-Z80 trace"],
    0x28: ["decoded data", "byte-verified assembly", "source-traced behavior", "gameplay observation (earlier first-lift video; limited scope)"],
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def hx(value: int, width: int) -> str:
    return f"0x{value:0{width}X}"


def validate_records(rom: bytes, cache: dict) -> list[dict]:
    records = cache["records"]
    if len(records) != 53:
        raise AssertionError(f"object-record cache contains {len(records)}, expected 53")
    expected_offset = int(cache["record_start"], 16)
    seen_offsets = set()
    for expected_index, row in enumerate(records, 1):
        offset = int(row["rom_offset"], 16)
        if row["index"] != expected_index or offset != expected_offset:
            raise AssertionError(f"record order/offset mismatch at index {expected_index}")
        if offset in seen_offsets:
            raise AssertionError(f"duplicate record offset {row['rom_offset']}")
        seen_offsets.add(offset)
        raw = bytes.fromhex(row["raw_bytes"])
        if len(raw) != 9 or rom[offset:offset + 9] != raw:
            raise AssertionError(f"record bytes disagree with ROM at {row['rom_offset']}")
        if int(row["type_id"], 16) != raw[0]:
            raise AssertionError(f"record type disagrees with raw bytes at {row['rom_offset']}")
        if row["stored_x"] != int.from_bytes(raw[1:3], "little") or row["stored_y"] != int.from_bytes(raw[3:5], "little"):
            raise AssertionError(f"stored coordinates disagree at {row['rom_offset']}")
        bias = cache["coordinate_bias"]
        if row["world_x"] != row["stored_x"] - bias or row["world_y"] != row["stored_y"] - bias:
            raise AssertionError(f"world coordinates disagree at {row['rom_offset']}")
        expected_offset += 9
    terminator = int(cache["terminator"], 16)
    if expected_offset != terminator or rom[terminator] != 0xFF:
        raise AssertionError("object terminator mismatch")
    actual_types = tuple(sorted({int(row["type_id"], 16) for row in records}))
    if actual_types != PLACED_TYPES:
        raise AssertionError(f"unexpected placed types: {actual_types!r}")
    return records


def placement_projection(row: dict) -> dict:
    return {
        "record_index": row["index"],
        "rom_offset": row["rom_offset"],
        "world_x": row["world_x"],
        "world_y": row["world_y"],
        "flags": row["flags"],
        "parameter": row["parameter"],
        "aux0": row["aux0"],
        "aux1": row["aux1"],
    }


def validate_dedicated_placements(records: list[dict], type_id: int, path: Path) -> None:
    expected = [placement_projection(row) for row in records if int(row["type_id"], 16) == type_id]
    actual = load_json(path)["placements"]
    if actual != expected:
        raise AssertionError(f"dedicated type {type_id:02X} placements disagree with object-records.json")


def variants(rows: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str, str, str], list[int]] = defaultdict(list)
    for row in rows:
        grouped[(row["flags"], row["parameter"], row["aux0"], row["aux1"])].append(row["index"])
    return [
        {"flags": key[0], "parameter": key[1], "aux0": key[2], "aux1": key[3], "count": len(indices), "record_indices": indices}
        for key, indices in grouped.items()
    ]


def frame_metadata(rom: bytes, type_id: int, frame_index: int) -> dict:
    frame_cpu = animation.mapping_frame_cpu(rom, type_id, frame_index)
    frame = assets.parse_frame_record(rom, frame_cpu)
    return {
        "frame_index": hx(frame_index, 2),
        "frame_cpu": hx(frame_cpu, 4),
        "frame_rom": hx(assets.cpu15_to_rom(frame_cpu), 5),
        "shared_empty_frame": frame_cpu == assets.KNOWN_SHARED_FRAME,
        "piece_count": frame["piece_count"],
        # The shared mapping decoder deliberately leaves this word unnamed.
        # Dedicated studies establish collision extents only for types where
        # source behavior proves that interpretation.
        "raw_word_1": hx(frame["raw_word_1"], 4),
        "coordinate_table_cpu": hx(frame["coords_cpu"], 4) if frame["piece_count"] else None,
        "coordinate_table_rom": hx(frame["coords_rom"], 5) if frame["coords_rom"] is not None else None,
        "tile_list_cpu": hx(frame["tile_list_cpu"], 4) if frame["piece_count"] else None,
        "tile_list_rom": hx(frame["tile_list_rom"], 5) if frame["tile_list_rom"] is not None else None,
        "tile_offsets": [hx(value, 2) for value in frame["tile_offsets"]],
    }


def recovered_regions(profile: dict, regions: list[dict]) -> list[dict]:
    wanted = set(profile["handlers"])
    return [
        {
            "name": row["name"],
            "file": f"asm/recovered/{row['file']}",
            "rom_start": hx(row["start"], 5),
            "rom_end_exclusive": hx(row["end"], 5),
            "kind": row["kind"],
        }
        for row in regions
        if row["file"] in wanted
    ]


def build_census(rom: bytes) -> dict:
    digest = hashlib.sha256(rom).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"ROM SHA-256 mismatch: {digest}; expected {EXPECTED_SHA256}")

    record_cache = load_json(RECORDS_PATH)
    graphics_map = load_json(GRAPHICS_PATH)
    layout = load_json(LAYOUT_PATH)
    regions = load_json(REGIONS_PATH)
    if record_cache["rom_sha256"] != digest or graphics_map["rom_sha256"] != digest or layout["rom_sha256"] != digest:
        raise AssertionError("one or more committed cache files target a different ROM")

    records = validate_records(rom, record_cache)
    validate_dedicated_placements(records, 0x21, OBJECT_21_PATH)
    validate_dedicated_placements(records, 0x27, OBJECT_27_PATH)
    validate_dedicated_placements(records, 0x10, OBJECT_10_PATH)
    assets.validate_known_anchors(rom, graphics_map)
    animation.validate_animation_anchors(rom)

    stream_by_id = {entry["id"]: entry for entry in graphics_map["supplemental_list"]["entries"]}
    counts = Counter(int(row["type_id"], 16) for row in records)
    objects = []
    all_unresolved = 0

    for type_id in PLACED_TYPES:
        rows = [row for row in records if int(row["type_id"], 16) == type_id]
        trace = animation.trace_type(rom, type_id)
        mapping = assets.object_mapping(rom, type_id)
        unresolved_commands = [state["unresolved"] for state in trace["states"] if state["unresolved"] is not None]
        all_unresolved += len(unresolved_commands)
        profile = PROFILES[type_id]
        load_paths = []
        for load_id in profile["graphics_load_ids"]:
            if load_id in stream_by_id:
                entry = stream_by_id[load_id]
                load_paths.append({
                    "id": load_id,
                    "bank_byte": entry["bank_byte"],
                    "source_cpu": entry["stream_cpu_address"],
                    "source_rom": entry["stream_rom_offset"],
                    "vram_destination": entry["vram_destination"],
                    "base_tile": entry["base_tile"],
                    "transform_remap": entry["transform_remap"],
                })
            else:
                load_paths.append({
                    "id": "dynamic_selector_0x12",
                    "selector_ram": "0xD3B3",
                    "selector": "0x12",
                    "list_pointer_table_rom": "0x07BA6",
                    "list_cpu": "0x7BCB",
                    "loads": [
                        {"bank": "0x0D", "source_cpu": "0x96BC", "source_rom": "0x356BC", "vram_destination": "0x0D40", "tile_range": "0x6A-0x79", "tile_count": 16},
                        {"bank": "0x09", "source_cpu": "0x8640", "source_rom": "0x24640", "vram_destination": "0x0F40", "tile_range": "0x7A-0xA9", "tile_count": 48},
                    ],
                })

        objects.append({
            "type_id": hx(type_id, 2),
            "record_count": len(rows),
            "record_indices": [row["index"] for row in rows],
            "records": [placement_projection(row) for row in rows],
            "field_variants": variants(rows),
            "animation": {
                "type_table_entry_rom": hx(trace["type_table_entry_rom"], 5),
                "bank": hx(trace["bank"], 2),
                "state_table_cpu": hx(trace["state_table_cpu"], 4),
                "state_table_rom": hx(trace["state_table_rom"], 5),
                "state_count": trace["state_count"],
                "state_script_cpus": [hx(value, 4) for value in trace["state_script_cpus"]],
                "reachable_mapping_frames": [hx(value, 2) for value in trace["reachable_frame_indices"]],
                "unresolved_states": trace["unresolved_states"],
                "unresolved_commands": unresolved_commands,
            },
            "mapping": {
                "pointer_table_rom": hx(mapping["pointer_table_rom"], 5),
                "mapping_cpu": hx(mapping["mapping_cpu"], 4),
                "mapping_rom": hx(mapping["mapping_rom"], 5),
                "reachable_frame_records": [frame_metadata(rom, type_id, value) for value in trace["reachable_frame_indices"]],
            },
            "graphics": {
                "placement_aux_pairs": [{"aux0": a, "aux1": b} for a, b in sorted({(row["aux0"], row["aux1"]) for row in rows})],
                "classification": profile["graphics_class"],
                "load_paths": load_paths,
                "note": profile["graphics_note"],
            },
            "renderer_orientation": profile["renderer_note"],
            "collision": profile["collision"],
            "research": {
                "placement_completeness": "VERIFIED",
                "semantic_identity": {"status": profile["semantic_status"], "role": profile["role"], "basis": profile["semantic_basis"]},
                "graphics_completeness": profile["graphics_completeness"],
                "animation_script_completeness": profile["animation_completeness"],
                "behavior_completeness": profile["behavior_completeness"],
                "lifetime_contact_completeness": profile["lifetime_contact_completeness"],
                "evidence_levels": EVIDENCE_LEVELS[type_id],
                "poc_research_readiness": profile["poc_readiness"],
                "recovered_regions": recovered_regions(profile, regions),
                "artifacts": profile["artifacts"],
                "major_remaining_questions": profile["gaps"],
            },
        })

    return {
        "format": 1,
        "scope": "Every raw nine-byte object record directly placed in Turquoise Hill Zone Act 1",
        "rom_sha256": digest,
        "source_object_records": "data/rom-cache/thz1/object-records.json",
        "record_start": record_cache["record_start"],
        "terminator": record_cache["terminator"],
        "coordinate_bias": record_cache["coordinate_bias"],
        "raw_record_count": len(records),
        "placed_type_count": len(counts),
        "placed_type_ids": [hx(value, 2) for value in PLACED_TYPES],
        "type_counts": {hx(value, 2): counts[value] for value in PLACED_TYPES},
        "record_order": [hx(int(row["type_id"], 16), 2) for row in records],
        "separate_layout_ring_position_count": len(layout["rings"]),
        "ring_count_note": "The 24 raw type-0x09 records and the 142 ring positions decoded from THZ1 layout blocks are different populations; this census does not claim that either count is an expansion of the other.",
        "validation": {
            "object_records_match_rom": True,
            "mapping_anchor_types": ["0x21", "0x26", "0x27", "0x28"],
            "animation_anchor_types": ["0x1B", "0x26"],
            "dedicated_placement_caches": ["0x10", "0x21", "0x27"],
            "total_unresolved_animation_states": all_unresolved,
        },
        "objects": objects,
        "prioritized_research_backlog": {
            "object_behavior_needing_formal_trace": ["0x18 completion/lifetime study", "0x09 parameter/entity-generation/collection study", "0x28 formal platform subtype/lifetime study"],
            "graphics_palette_mapping_gaps": [],
            "placement_entity_expansion_gaps": ["Explain type-0x09 runtime entity generation and its relationship, if any, to the separate 142 layout-derived ring positions"],
            "generic_engine_dependencies": ["Camera activation/removal, occupancy release, and respawn studies for 0x1B, 0x26, and 0x28", "Full scheduler/gameplay validation beyond controlled subroutine fixtures"],
            "poc_integration_ready": ["0x10", "0x21", "0x27", "0x26 core state machine", "0x1B core state machine"],
            "recommended_next_independent_task": {"type_id": "0x18", "reason": "Type 0x10 now has a complete formal THZ1 behavior study. Type 0x18 retains a bounded completion/lifetime gap with its dynamic graphics path already verified."},
        },
    }


def write_census(path: Path, census: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(census, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    census = build_census(args.rom.read_bytes())
    write_census(args.output, census)
    print(json.dumps({"output": str(args.output), "raw_records": census["raw_record_count"], "types": census["type_counts"], "unresolved_animation_states": census["validation"]["total_unresolved_animation_states"]}, indent=2))


if __name__ == "__main__":
    main()
