#!/usr/bin/env python3
"""U5-A: POC implementation handoff (machine-readable), built only from the committed U5-A JSON - no ROM, no POC checkout needed.

    python tools/u5a_handoff.py            # rewrite data/u5a/poc-handoff.json
    python tools/u5a_handoff.py --check    # compare with the committed file

The handoff names the smallest presentation-only changes for the POC (commit b4737e83...).  Nothing here changes gameplay, physics or any accepted resource.
ROM-derived PNGs referenced below are regenerated into the ignored build/u5a by tools/u5a_player_presentation.py and tools/u5a_opening.py.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import u5a_opening as O  # noqa: E402
import u5a_player_presentation as P  # noqa: E402

OUTPUT = ROOT / "data" / "u5a" / "poc-handoff.json"


def player_asset(fr, fid, part, role, name):
    f = fr["0x%02X" % fid]
    return {"part": part, "role": role, "proposed_resource": name, "source_png": "build/u5a/frames/frame-%02X.png" % fid, "rom_frame": "0x%02X" % fid,
            "width": f["canvas_width"], "height": f["canvas_height"], "origin_x": f["gamemaker_origin_x"], "origin_y": f["gamemaker_origin_y"],
            "index_sha256": f["index_sha256"], "rgba_sha256_thz1_palette": f["rgba_sha256_thz1_palette"], "variant": "single (Sonic's eleven colours are identical in every act, AQZ variant not needed)"}


def build():
    ps = P.load_json(P.STATIC_JSON)
    os_ = O.load_json(O.STATIC_JSON)
    fr = ps["frames"]["frames"]
    assets = []
    for fid in (0x3C, 0x3D, 0x3E, 0x3F):
        assets.append(player_asset(fr, fid, "A", "strip walk/run frame (marker set, previous surface $19)", "SPR_chaos_player_frame_%02X" % fid))
    assets.append(player_asset(fr, 0x0B, "B", "Spring Shoes pose (state $12); also the ROM idle frame of states $00/$01", "SPR_chaos_player_frame_0B"))
    for fid in (7, 8, 9, 0x0A):
        assets.append(player_asset(fr, fid, "D", "opening: Sonic run frame", "SPR_chaos_player_frame_%02X" % fid))
    for k, f in sorted(os_["mapping"]["tails_type_2_frames_used"]["frames"].items(), key=lambda kv: int(kv[0])):
        assets.append({"part": "D", "role": "opening: Tails walk frame (object type 2, selector $8EE1)", "proposed_resource": "SPR_chaos_opening_tails_%02X" % int(k),
                       "source_png": "build/u5a/opening/frames/tails-%02X.png" % int(k), "rom_frame": "type2:%s" % k, "width": f["canvas"][0], "height": f["canvas"][1],
                       "origin_x": f["gamemaker_origin"][0], "origin_y": f["gamemaker_origin"][1], "index_sha256": f["index_sha256"],
                       "rgba_sha256_opening_sprite_palette": f["rgba_sha256_opening_sprite_palette"], "variant": "single, sprite palette record 41"})
    for k, f in sorted(os_["mapping"]["machine_type_1F"]["frames"].items(), key=lambda kv: int(kv[0])):
        if not f["piece_count"]:
            continue
        b = f["bounds"]
        assets.append({"part": "D", "role": "opening: type $1F machine frame (17 pieces, tile base $6A)", "proposed_resource": "SPR_chaos_opening_machine_%02X" % int(k),
                       "source_png": "build/u5a/opening/frames/machine-%02X.png" % int(k), "rom_frame": "type1F:%s" % k, "width": b["width"], "height": b["height"],
                       "origin_x": -b["min_x"], "origin_y": -b["min_y"], "rgba_sha256_opening_sprite_palette": f["rgba_sha256"], "variant": "single, sprite palette record 41"})
    lv = os_["level"]
    assets.append({"part": "D", "role": "opening: background (zone 7 act 0, 256x8 blocks of 32 px) as one indexed 4096x256 strip, or re-import through the G1-B level importer",
                   "proposed_resource": "SPR_chaos_opening_level_strip", "source_png": "build/u5a/opening/level-strip.png", "width": 4096, "height": 256, "origin_x": 0, "origin_y": 0,
                   "palette": {"background_record": lv["palette"]["background_record"], "colours": lv["palette"]["background_colours"], "palette1_is_sprite_record": lv["palette"]["sprite_record"],
                               "colours_palette1": lv["palette"]["sprite_colours"]}, "layout_sha256": lv["layout"]["sha256"],
                   "note": "4096 px covers camera 0..3578 plus a 348-wide widescreen view; the full world is 8192 px but the cinematic never leaves x < 3840"})
    return {
        "research_base": P.BASE_COMMIT, "poc_commit": P.POC_COMMIT, "scope": "presentation only; no gameplay, physics or accepted-resource change",
        "assets": assets,
        "changes": [
            {"id": "A-1", "part": "A", "file": "scripts/SCR_chaos_player_animation_data/SCR_chaos_player_animation_data.gml", "poc_lines": "15-36, 36+",
             "change": "add cases 60..63 to chaos_player_frame_sprite (SPR_chaos_player_frame_3C..3F, no AQZ variant) and the four sprites to chaos_player_rom_resource (resource identity owns registration)"},
            {"id": "A-2", "part": "A", "file": "scripts/SCR_chaos_player_animation/SCR_chaos_player_animation.gml", "poc_lines": "12-35 (walk/run branch), 63-75 (present)",
             "change": "for requested state 5 or 6: strip = (cp_c.special & 1) != 0 && (cp_c.previous & 31) == 25 evaluated ONLY when the record reloads (as the ROM selector does); walk: side contact (cp_c.contacts & 12) keeps "
                       "the legacy sprite (frame $5E not imported) and takes precedence; when strip: wrap the shared index at 4, frame = $3C + index, counter 4 (run) or the walk duration table, mark the shadow active "
                       "so present() draws SPR_chaos_player_frame_3x until the record ends"},
            {"id": "A-3", "part": "A", "file": "same", "poc_lines": "63-75",
             "change": "the legacy branch that mirrors facing from sign(vx) is skipped while presenting: keep cp_c.player_flags bit 4 current with chaos_player_facing_input(cp_c) in walk (ROM $3791 calls $48A7) and leave it untouched in run ($384D never calls $48A7)"},
            {"id": "B-1", "part": "B", "file": "scripts/SCR_chaos_player_animation_data/SCR_chaos_player_animation_data.gml", "poc_lines": "2-13, 15-36",
             "change": "add `case 18: return [[0,4,11,33606],[1,0,0,33610]];` (script $8346), frame case 11 -> SPR_chaos_player_frame_0B, and the sprite to chaos_player_rom_resource"},
            {"id": "B-2", "part": "B", "file": "scripts/SCR_chaos_player_animation/SCR_chaos_player_animation.gml", "poc_lines": "5-10",
             "change": "add cp_state == 18 to chaos_player_animation_supported; present() already mirrors from cp_c.player_flags bit 4, which the footwear code keeps from Left/Right"},
            {"id": "B-3", "part": "B", "file": "scripts/SCR_chaos_adapter/SCR_chaos_adapter.gml", "poc_lines": "59, 65, 98",
             "change": "no edit needed once present() returns true (the SPR_player_jump / image_index 0 state-12 branch is then unreachable); the footwear object code is untouched"},
            {"id": "C-1", "part": "C", "file": "none", "poc_lines": "-", "change": "no change: programs 11, 14, 20 and the 18 imported frame resources already reproduce the ROM exactly; request a POC trace if the symptom persists"},
            {"id": "D-1", "part": "D", "file": "new presentation room/object (not a level)", "poc_lines": "-",
             "change": "play opening-replay.json (738 rows) with the imported frames; background from the level strip or the zone-7 level through the existing importer; fade-in passes every 5 updates "
                       "(4 passes, the first is black), fade-out 3 passes after the last update, then 30 waits, then the title; button 1/2 skips to a fade-out and the title (not New Game); "
                       "music request $90 is recorded numerically (no asset)"},
            {"id": "D-2", "part": "D", "file": "objects/OBJ_menu_opening, rooms/ROM_menu_opening", "poc_lines": "Draw_0/Create_0",
             "change": "decision for Manager: the inherited Sega logo (SPR_opening_sega) has no ROM counterpart; the ROM goes from black straight to the cinematic"},
        ],
        "data_files": ["data/u5a/player-static.json", "data/u5a/player-observed.json", "data/u5a/player-poc-source.json", "data/u5a/opening-static.json", "data/u5a/opening-replay.json",
                       "data/u5a/opening-observed.json", "data/u5a/startup-census.json", "data/u5a/evidence-matrix.json"],
        "acceptance_checks": [
            "A: on a GPZ2/MGHZ1 strip at full speed the presented frames follow $3F,$3C,$3D,$3E (4 updates each, order from the shared index) and leave the strip set on the first record reload after the previous surface is not $19",
            "A: the strip-fall tumble ($14, 4 updates per frame) is unchanged (already exact)",
            "B: while a Spring Shoes bounce runs Sonic shows frame $0B on every update, mirrored only by Left/Right; the shoe object keeps its own frame 3 x12 / 4 cadence",
            "C: weak mapped spring and boss bounce show $1C..$21 at 4 updates per frame (82-update cycle), strong springs show $61",
            "D: the replay reproduces the 738 rows; machine states 40/43/66/113/486/536; Tails from update 661; camera frozen from update 601; fades every 5 updates",
        ],
        "not_in_scope": ["any change to movement, contact, springs, platforms or the ring counter", "ordinary walk/run/idle/stand ROM art ($01-$0A) outside the strip and Spring Shoes cases",
                         "audio assets", "title/attract demo implementation", "Windows acceptance (James)"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    text = P.dumps(build())
    if a.check:
        if OUTPUT.read_text(encoding="utf-8") != text:
            raise SystemExit("MISMATCH: " + str(OUTPUT))
        print("poc-handoff.json matches the committed U5-A data")
        return
    OUTPUT.write_text(text, encoding="utf-8")
    print("wrote", OUTPUT.relative_to(ROOT), len(text))


if __name__ == "__main__":
    main()
