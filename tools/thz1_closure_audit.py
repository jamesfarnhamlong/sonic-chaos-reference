#!/usr/bin/env python3
"""Build the deterministic final THZ1 closure classification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CENSUS = ROOT / "data/rom-cache/thz1/object-census.json"
GRAPHICS10 = ROOT / "data/rom-cache/thz1/object-10-graphics.json"
DEFAULT_OUTPUT = ROOT / "data/rom-cache/thz1/closure-audit.json"

REFERENCE_SHA = "69edb63b18ae3777310635c1ae1df26c8e483c1f"
POC_SHA = "231aeaf6d898ec572ee803609ac9a4f9bf97f392"
ROM_SHA = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"


def build_audit() -> dict:
    census = json.loads(CENSUS.read_text(encoding="utf-8"))
    graphics = json.loads(GRAPHICS10.read_text(encoding="utf-8"))
    expected = {"0x09": 24, "0x10": 5, "0x18": 1, "0x1B": 4,
                "0x21": 6, "0x26": 4, "0x27": 3, "0x28": 6}
    if census["raw_record_count"] != 53 or census["type_counts"] != expected:
        raise AssertionError("canonical object census changed")
    if census["separate_layout_ring_position_count"] != 142:
        raise AssertionError("layout-derived ring population changed")
    if graphics["rom_sha256"] != ROM_SHA:
        raise AssertionError("type-0x10 graphics cache ROM mismatch")

    objects = [
        {"type": "0x09", "records": 24, "placement": "CLOSED", "graphics": "CLOSED", "animation": "CLOSED", "behavior": "UNRESOLVED", "contact_collision": "UNRESOLVED", "lifetime_respawn": "UNRESOLVED", "poc": "No distinct raw-record implementation; 142 layout rings remain a separate implemented population", "discrepancy": "No proved visible/mechanical expansion from the 24 raw records; relationship remains unknown", "classification": "FUTURE FIDELITY"},
        {"type": "0x10", "records": 5, "placement": "CLOSED", "graphics": "CLOSED in research", "animation": "CLOSED", "behavior": "CLOSED for THZ1 reachability", "contact_collision": "CLOSED", "lifetime_respawn": "CLOSED", "poc": "Five canonical records and body/replacement frames; selector content absent", "discrepancy": "ROM-backed dynamic tiles 0x4C-0x51 are not rendered", "classification": "BLOCKER"},
        {"type": "0x18", "records": 1, "placement": "CLOSED", "graphics": "CLOSED", "animation": "CLOSED", "behavior": "PARTIAL", "contact_collision": "ADAPTER", "lifetime_respawn": "PARTIAL", "poc": "Canonical placement and five frames with explicit completion helper", "discrepancy": "Original contact/results transition is not claimed", "classification": "ACCEPTED ADAPTER"},
        {"type": "0x1B", "records": 4, "placement": "CLOSED", "graphics": "CLOSED", "animation": "CLOSED", "behavior": "SUBSTANTIAL", "contact_collision": "SUBSTANTIAL", "lifetime_respawn": "PARTIAL", "poc": "Four moving-spike placements with bounded implementation", "discrepancy": "No concrete contradiction; generic lifetime proof is less formal", "classification": "FUTURE FIDELITY"},
        {"type": "0x21", "records": 6, "placement": "CLOSED", "graphics": "CLOSED", "animation": "CLOSED", "behavior": "CLOSED for THZ1 reachability", "contact_collision": "CLOSED", "lifetime_respawn": "CLOSED", "poc": "Six canonical placements and verified behavior", "discrepancy": "None material", "classification": "CLOSED"},
        {"type": "0x26", "records": 4, "placement": "CLOSED", "graphics": "CLOSED", "animation": "CLOSED", "behavior": "SUBSTANTIAL", "contact_collision": "SUBSTANTIAL", "lifetime_respawn": "PARTIAL", "poc": "Four canonical object-spring placements with bounded implementation", "discrepancy": "No concrete contradiction; scheduler/lifetime proof remains less formal", "classification": "FUTURE FIDELITY"},
        {"type": "0x27", "records": 3, "placement": "CLOSED", "graphics": "CLOSED", "animation": "CLOSED", "behavior": "CLOSED for THZ1 reachability", "contact_collision": "CLOSED", "lifetime_respawn": "CLOSED", "poc": "Three canonical placements and verified behavior", "discrepancy": "None material", "classification": "CLOSED"},
        {"type": "0x28", "records": 6, "placement": "CLOSED", "graphics": "CLOSED", "animation": "CLOSED static reachability", "behavior": "PARTIAL", "contact_collision": "ADAPTER", "lifetime_respawn": "PARTIAL", "poc": "Six canonical platforms through bounded subtype adapter", "discrepancy": "Command 0x09 is closed; full rider/subtype/lifetime behavior remains bounded", "classification": "ACCEPTED ADAPTER"},
    ]
    terrain = [
        {"system": "terrain/layout reconstruction", "poc": "canonical THZ1 flattened layout", "classification": "CLOSED"},
        {"system": "collision profiles", "poc": "ROM-derived collision profiles used by movement core", "classification": "CLOSED"},
        {"system": "first ramp", "poc": "controlled fixtures and ramp launch integrated", "classification": "CLOSED"},
        {"system": "loops", "poc": "traversable bounded state adapter; presentation timing can differ", "classification": "ACCEPTED ADAPTER"},
        {"system": "twist/Mobius traversal", "poc": "all 112 dispatch entries and 1,078 boundary fixtures; bounded presentation adapter", "classification": "ACCEPTED ADAPTER"},
        {"system": "terrain springs", "poc": "nine placements; contextual terrain composition", "classification": "ACCEPTED ADAPTER"},
        {"system": "static spike cells", "poc": "four canonical cells, no duplicated object art", "classification": "CLOSED"},
        {"system": "moving spike presentation", "poc": "four canonical type-0x1B placements", "classification": "FUTURE FIDELITY"},
        {"system": "ring-bearing layout cells", "poc": "72 cells stripped to background-only terrain", "classification": "CLOSED"},
        {"system": "142 layout-derived rings", "poc": "142 separate collectible instances; not merged with type 0x09", "classification": "CLOSED"},
        {"system": "six platform placements", "poc": "two 0x0A and four 0x84 records represented", "classification": "ACCEPTED ADAPTER"},
        {"system": "end-of-act boundary", "poc": "type 0x18 presentation plus explicit non-original completion helper", "classification": "ACCEPTED ADAPTER"},
        {"system": "camera/lifetime traversal", "poc": "bounded room-instance cleanup/recreation adapters", "classification": "ACCEPTED ADAPTER"},
    ]
    return {
        "format": 1,
        "scope": "final bounded THZ1 closure audit against POC 18.3",
        "rom_sha256": ROM_SHA,
        "starting_reference_sha": REFERENCE_SHA,
        "starting_poc_sha": POC_SHA,
        "canonical_counts": {"raw_object_records": 53, "placed_types": 8, "layout_ring_positions": 142, "type_counts": expected},
        "poc_verification": {"type_10": 5, "type_18": 1, "type_21": 6, "type_27": 3, "moving_spikes": 4, "static_spikes": 4, "platforms": 6, "terrain_springs": 9, "layout_rings": 142, "legacy_layout_monitors": 0, "fabricated_finish_marker_treated_as_canonical": False, "commit_self_check": "verification/verify_v18_objects.py passes after its contradictory absence assertion for the committed OBJ_ring/Draw_0.gml is isolated; the committed custom draw path is a POC adapter"},
        "command_09": {"handler_cpu": "0x6827", "bytes_consumed_after_command": 2, "total_command_bytes": 4, "semantics": "object[offset] = immediate", "field_effects_in_type_28": [{"states": [4, 12, 14], "offset": "0x1E", "value": "0x50"}, {"states": [12, 14], "offset": "0x27", "value": "0x80"}], "remaining_type_28_animation_gaps": 0},
        "type_05_bounded": graphics["type_05_bounded"],
        "objects": objects,
        "terrain_mechanics": terrain,
        "blockers": ["POC 18.3 does not render selector-dependent type-0x10 tiles 0x4C-0x51 in frame 0x0B.", "POC 18.3 omits the ROM-backed 32-frame type-0x05 visible effect allocated by selector 0x06."],
        "accepted_adapters": ["type 0x18 completion/contact/results boundary", "type 0x28 platform subtype/rider/lifetime implementation", "loop/twist/spring presentation scheduling", "camera/off-range room-instance lifetime behavior", "custom POC ring Draw event; POC 18.3 verifier incorrectly asserts that the committed file is absent"],
        "future_fidelity": ["type 0x09 behavior and any relationship to the separate 142 layout rings", "formal generic lifetime/scheduler completion for types 0x1B and 0x26", "full type 0x28 subtype/rider/lifetime proof beyond the accepted adapter", "full type 0x18 end-of-act/results state machine", "exact type 0x05 special-render anchor path and broader all-game variants"],
        "overall_conclusion": "THZ1 POC BLOCKED",
        "conclusion_answer": "Yes. The current POC still omits the now-ROM-backed selector graphics for type 0x10 and the visible type 0x05 effect for selector 0x06. No other established THZ1 discrepancy is classified as a blocker.",
        "recommended_next_task": "Integrate object-10-graphics.json into the POC for selectors 0x02/0x04/0x06 and add the bounded type-0x05 selector-0x06 presentation, then rerun this closure gate before beginning the next zone.",
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = ap.parse_args()
    audit = build_audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "conclusion": audit["overall_conclusion"]}, indent=2))


if __name__ == "__main__":
    main()
