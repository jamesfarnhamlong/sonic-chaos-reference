"""Regenerate the ROM metadata cache and compare it byte-for-byte."""
import sys
from pathlib import Path

import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from cache_game_data import EXPECTED_SHA256, decode_layout, decode_objects, layout_interactions
import thz1_object_10 as object10
import thz1_object_21 as object21
import thz1_object_09 as object09
import thz1_final_runtime_closure as final_closure
import player_state_11_graphics as player_graphics
import thz1_background_registration as background
import mapped_object_registration as registration
import object_50
import object_18
import collision_geometry
import viewport_semantics
import terrain_ring_collection
import player_animation_counter
import spring_interaction
import platform_spike_collision
import player_attack_badnik
import thz3_boss_support
import powerup_shoes
import player_hurt_ring_scatter
import mghz_foundation
import mghz_object_census
import sez_foundation
import sez_object_census
import sez_art_approval
import sez_surfaces
import sez_platform_28
import sez_enemies_20_23
import mghz_surface_ceiling
import mghz_m1_followup
import mghz_object_24_2e
import spring_shoes_presentation
import player_fall_control


def main(rom_path):
    rom = Path(rom_path).read_bytes()
    assert hashlib.sha256(rom).hexdigest() == EXPECTED_SHA256
    layout, layout_end = decode_layout(rom)
    records = decode_objects(rom)
    interactions = layout_interactions(layout)
    stored_objects = json.loads((ROOT / "data/rom-cache/thz1/object-records.json").read_text())
    stored_layout = json.loads((ROOT / "data/rom-cache/thz1/layout-interactions.json").read_text())
    assert stored_objects["records"] == records
    assert stored_layout["compressed_read_end"] == f"0x{layout_end:05X}"
    assert stored_layout["terrain"] == interactions["terrain"]
    assert stored_layout["rings"] == interactions["rings"]
    stored_object10 = json.loads(
        (ROOT / "data/rom-cache/thz1/object-10.json").read_text(encoding="utf-8")
    )
    assert stored_object10 == object10.build_report(rom)
    stored_object21 = json.loads(
        (ROOT / "data/rom-cache/thz1/object-21.json").read_text(encoding="utf-8")
    )
    assert stored_object21 == object21.build_report(rom)
    stored_object09 = json.loads(
        (ROOT / "data/rom-cache/thz1/object-09.json").read_text(encoding="utf-8")
    )
    assert stored_object09 == object09.build_report(rom)
    stored_final = json.loads(
        (ROOT / "data/rom-cache/thz1/final-runtime-closure.json").read_text(encoding="utf-8")
    )
    assert stored_final == final_closure.build(rom)
    stored_coverage = json.loads(
        (ROOT / "data/rom-cache/thz1/poc-coverage.json").read_text(encoding="utf-8")
    )
    assert stored_coverage == final_closure.coverage()
    stored_player = json.loads(
        (ROOT / "data/rom-cache/thz1/player-state-11-graphics.json").read_text(encoding="utf-8")
    )
    assert stored_player == player_graphics.build(rom)
    stored_background = json.loads(
        (ROOT / "data/rom-cache/thz1/background-registration.json").read_text(encoding="utf-8")
    )
    for patch in stored_background["patches"]:
        patch.pop("poc_18_5", None)
    assert stored_background == background.build(rom)
    stored_registration = json.loads(
        (ROOT / "data/rom-cache/mapped-object-registration.json").read_text(encoding="utf-8")
    )
    # Static (byte checks, mapping tables, controlled routine fixtures, rule) part is regenerated here;
    # the emulated-frame part is checked by `tools/mapped_object_registration.py ROM --check ...` (~60 s).
    static = registration.build(rom, static_only=True)
    assert stored_registration["source_facts"]["routine_byte_checks"] == static["source_facts"]["routine_byte_checks"]
    assert stored_registration["source_facts"]["mapping_tables"] == static["source_facts"]["mapping_tables"]
    assert stored_registration["source_facts"]["controlled_routine_fixtures"] == static["source_facts"]["controlled_routine_fixtures"]
    assert stored_registration["interpretation"]["registration_rule"] == static["interpretation"]["registration_rule"]
    # THZ3 type $50 study: static, controlled-routine and emulated sections are all regenerated (~10 s).
    stored_object50 = json.loads(
        (ROOT / "data/rom-cache/thz3/object-50.json").read_text(encoding="utf-8")
    )
    assert stored_object50 == object_50.build(rom)
    # THZ1/THZ2 type $18 and act-clear study: static, controlled-routine and emulated sections are regenerated (~20 s).
    stored_object18 = json.loads(
        (ROOT / "data/rom-cache/object-18-act-clear.json").read_text(encoding="utf-8")
    )
    assert stored_object18 == json.loads(json.dumps(object_18.build(rom)))
    # Collision-geometry audit: extents, helper models, grids and sweeps are regenerated (~30 s).
    stored_geometry = json.loads(
        (ROOT / "data/rom-cache/collision-geometry.json").read_text(encoding="utf-8")
    )
    assert stored_geometry == json.loads(json.dumps(collision_geometry.build(rom)))
    # Viewport-semantics audit: static tables, sweeps and emulated runs are regenerated (~25 s).
    stored_viewport = json.loads(
        (ROOT / "data/rom-cache/viewport-semantics.json").read_text(encoding="utf-8")
    )
    assert stored_viewport == json.loads(json.dumps(viewport_semantics.build(rom)))
    # Terrain-ring collection study: probe, sweeps, state reach and emulated runs are regenerated (~35 s).
    stored_rings = json.loads(
        (ROOT / "data/rom-cache/terrain-ring-collection.json").read_text(encoding="utf-8")
    )
    assert stored_rings == json.loads(json.dumps(terrain_ring_collection.build(rom)))
    # Player animation counter study: engine fixtures, differential sweeps and emulated play are regenerated (~20 s).
    stored_counter = json.loads(
        (ROOT / "data/rom-cache/player-animation-counter.json").read_text(encoding="utf-8")
    )
    assert stored_counter == json.loads(json.dumps(player_animation_counter.build(rom)))
    # Spring interaction audit: controlled sweeps and emulated launches are regenerated (~2 min).
    stored_springs = json.loads(
        (ROOT / "data/rom-cache/spring-interaction.json").read_text(encoding="utf-8")
    )
    assert stored_springs == json.loads(json.dumps(spring_interaction.build(rom)))
    # Platform / spike collision audit: controlled sweeps and emulated scenarios are regenerated (~2.5 min).
    stored_platform_spike = json.loads(
        (ROOT / "data/rom-cache/platform-spike-collision.json").read_text(encoding="utf-8")
    )
    assert stored_platform_spike == json.loads(json.dumps(platform_spike_collision.build(rom)))
    # Player attack posture / badnik interaction audit: controlled sweeps and emulated runs are regenerated (~2 min).
    stored_attack = json.loads(
        (ROOT / "data/rom-cache/player-attack-badnik.json").read_text(encoding="utf-8")
    )
    assert stored_attack == json.loads(json.dumps(player_attack_badnik.build(rom)))
    # THZ3 boss/support audit + $1B/$28 closure: controlled sweeps and update-aligned emulated runs are regenerated (~2.5 min).
    stored_thz3_support = json.loads(
        (ROOT / "data/rom-cache/thz3-boss-support.json").read_text(encoding="utf-8")
    )
    fresh_thz3_support = json.loads(json.dumps(thz3_boss_support.build(rom)))
    assert stored_thz3_support == fresh_thz3_support
    assert json.loads((ROOT / "data/rom-cache/thz3/implementation-manifest.json").read_text(encoding="utf-8")) == json.loads(
        json.dumps(thz3_boss_support.manifest(rom, fresh_thz3_support)))
    # Rocket/Spring Shoes package: placements and focused original-routine sweeps (~1 s).
    stored_shoes = json.loads(
        (ROOT / "data/rom-cache/powerup-shoes.json").read_text(encoding="utf-8")
    )
    assert stored_shoes == json.loads(json.dumps(powerup_shoes.build(rom)))
    # Player hurt / lost-ring scatter audit: controlled sweeps, model-vs-ROM sweep and the GPZ3 whole-game example are regenerated (~10 s).
    stored_scatter = json.loads(
        (ROOT / "data/rom-cache/player-hurt-ring-scatter.json").read_text(encoding="utf-8")
    )
    assert stored_scatter == json.loads(json.dumps(player_hurt_ring_scatter.build(rom)))
    # MGHZ foundation and object census: regenerated from the ROM.
    assert (ROOT / "data/rom-cache/mghz/implementation-manifest.json").read_text(encoding="utf-8") == mghz_foundation.dumps(mghz_foundation.build(rom))
    assert (ROOT / "data/rom-cache/mghz/object-census.json").read_text(encoding="utf-8") == mghz_object_census.dumps(mghz_object_census.build(rom))
    # MGHZ surface $1B (oil) and ceiling-spike audit: controlled sweeps and emulated scenarios are regenerated (~20 s).
    assert (ROOT / "data/rom-cache/mghz/surface-1b-ceiling-spikes.json").read_text(encoding="utf-8") == mghz_surface_ceiling.dumps(mghz_surface_ceiling.build(rom))
    # MGHZ M1 Windows follow-up (rising platform into terrain, strip $1A8/$1A9, breakable $0D): controlled and emulated fixtures are regenerated (~30 s).
    assert (ROOT / "data/rom-cache/mghz/m1-windows-followup.json").read_text(encoding="utf-8") == mghz_m1_followup.dumps(mghz_m1_followup.build(rom))
    # MGHZ object $24 / $2E audit (trigger, shake/fall/landing, contact sweeps, strip emitter, lifecycle and runtime-art fixtures): controlled and whole-game fixtures are regenerated (~25 s).
    assert (ROOT / "data/rom-cache/mghz/object-24-2e.json").read_text(encoding="utf-8") == mghz_object_24_2e.dumps(mghz_object_24_2e.build(rom))
    # Shared player fall / control audit (special fall $14, monitor + wall, fall-state support): controlled sweeps and whole-game fixtures are regenerated (~85 s).
    assert (ROOT / "data/rom-cache/player-fall-control.json").read_text(encoding="utf-8") == player_fall_control.dumps(player_fall_control.build(rom))
    # Spring Shoes presentation / act-clear / detach audit: controlled and whole-game fixtures are regenerated (~35 s).
    assert (ROOT / "data/rom-cache/spring-shoes-presentation.json").read_text(encoding="utf-8") == spring_shoes_presentation.dumps(spring_shoes_presentation.build(rom))
    # SEZ foundation (corrected bank-relative mapping, surfaces, effect 5, controlled handlers), object census and art-approval manifest: regenerated from the ROM (~10 s).
    assert (ROOT / "data/rom-cache/sez/implementation-manifest.json").read_text(encoding="utf-8") == sez_foundation.dumps(sez_foundation.build(rom))
    assert (ROOT / "data/rom-cache/sez/object-census.json").read_text(encoding="utf-8") == sez_object_census.dumps(sez_object_census.build(rom))
    assert (ROOT / "data/rom-cache/sez/art-approval.json").read_text(encoding="utf-8") == json.dumps(sez_art_approval.manifest_for(sez_art_approval.build(rom)), indent=2) + "\n"
    # SEZ terrain mechanics (surface $0C/$13 crumble ledge, surface $1A booster pad): controlled sweeps, whole-game fixtures and runtime contracts are regenerated (~60 s).
    sez_data, sez_contracts = sez_surfaces.build_all(rom)
    assert (ROOT / "data/rom-cache/sez/surfaces-0c-1a.json").read_text(encoding="utf-8") == sez_surfaces.dumps(sez_data)
    assert (ROOT / "data/rom-cache/sez/surface-runtime-contracts.json").read_text(encoding="utf-8") == sez_surfaces.dumps(sez_contracts)
    assert (ROOT / "data/rom-cache/sez/platform-28-runtime.json").read_text(encoding="utf-8") == sez_platform_28.dumps(sez_platform_28.build(rom))
    assert json.loads((ROOT / 'data/rom-cache/sez/enemies-20-23-runtime.json').read_text(encoding='utf-8')) == json.loads(json.dumps(sez_enemies_20_23.build(rom)))
    import sez54_runtime, sez54_fullgame
    assert json.loads((ROOT / 'data/rom-cache/sez/boss-54-runtime.json').read_text(encoding='utf-8')) == json.loads(json.dumps(sez54_runtime.build(rom)))
    assert json.loads((ROOT / 'data/rom-cache/sez/boss-54-fullgame.json').read_text(encoding='utf-8')) == json.loads(json.dumps(sez54_fullgame.build(rom)))
    # AQZ A1: fresh bank-relative extraction, full placement census, original SAT
    # compositions and complete-state replay. James approved all A1 boards.
    import aqz_foundation, aqz_art_approval, aqz_original_checks
    aqz_manifest, aqz_census, _ = aqz_foundation.build(rom)
    for name, value in [('implementation-manifest.json', aqz_manifest), ('object-census.json', aqz_census),
                        ('art-approval.json', aqz_art_approval.build(rom)[0]), ('original-checks.json', aqz_original_checks.build(rom))]:
        assert (ROOT / 'data/rom-cache/aqz' / name).read_text(encoding='utf-8') == aqz_foundation.dumps(value), name
    import aqz_water, aqz_water_game
    for path, value in [(aqz_water.OUTPUT, aqz_water.build(rom)), (aqz_water_game.OUTPUT, aqz_water_game.build(rom))]:
        assert path.read_text(encoding='utf-8') == aqz_foundation.dumps(value), path
    import aqz_platform_3f, aqz_platform_game
    for path,value in [(aqz_platform_3f.OUTPUT,aqz_platform_3f.build(rom)),(aqz_platform_game.OUTPUT,aqz_platform_game.build(rom))]:
        assert path.read_text(encoding='utf-8') == aqz_foundation.dumps(value),path
    import aqz_enemies, aqz_enemies_game
    for path,value in [(aqz_enemies.OUTPUT,aqz_enemies.build(rom)),(aqz_enemies_game.OUTPUT,aqz_enemies_game.build(rom))]:
        assert path.read_text(encoding='utf-8') == aqz_foundation.dumps(value),path
    import aqz59_runtime, aqz59_game
    for path,value in [(aqz59_runtime.OUTPUT,aqz59_runtime.build(rom)),(aqz59_game.OUTPUT,aqz59_game.build(rom))]:
        assert path.read_text(encoding='utf-8') == aqz_foundation.dumps(value),path
    manifest = json.loads(
        (ROOT / "data/rom-cache/thz1/manifest.json").read_text(encoding="utf-8")
    )
    for name, expected in manifest["files"].items():
        payload = (ROOT / "data/rom-cache/thz1" / name).read_bytes()
        assert len(payload) == expected["bytes"]
        assert hashlib.sha256(payload).hexdigest() == expected["sha256"]
    assert len(records) == 53
    assert sum(r["decoded_kind"] is not None for r in records) == 14
    print(
        "ROM cache: 53 records, 14 decoded placements, 17 terrain interactions, "
        "142 rings; type-$09/$10/$21, final closure, coverage, player-$11 graphics, background metadata, THZ3 type-$50, type-$18 act-clear, collision-geometry and viewport-semantics studies deterministic"
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("usage: python tests/verify_cache.py /path/to/SonicChaos.sms")
    main(sys.argv[1])
