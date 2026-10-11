#!/usr/bin/env python3
"""Whole-ROM address ledger for Sonic Chaos (Europe) v1.2 (task DECOMP-0).

    python tools/rom_ledger.py /path/to/SonicChaos.sms [--output data/rom-ledger] [--check]

Every one of the 524,288 ROM bytes receives exactly one primary classification
(CODE / DATA / GRAPHICS / MUSIC / COMPRESSED / PADDING / UNKNOWN). Semantic
information (subtype, subsystem, logical content), recovery status, evidence
quality and source references are stored beside it, never inside it.

Rules (full statement in docs/rom-address-ledger.md):

* File offsets are authoritative; intervals are half-open ``[start, end)``.
* A *claim* is one source's statement about an exact range. Claims are imported
  only where both boundaries and the class are supported by a recovered-assembly
  manifest, an existing decoder/loader, a verified table, or an audit manifest
  whose SHA-256 range hash matches the ROM *and* which states ``kind``.
* Overlapping claims of the same primary class are compatible (nested/identical
  descriptions are merged, partial overlaps are listed). Overlapping claims of
  different classes are *contradictory*: the bytes become UNKNOWN, are flagged
  ``contested`` and the pair is reported. Nothing is chosen silently.
* Recovery status (``recovered`` / ``not_recovered``) is tracked independently of
  the class so recovering code later raises source coverage without implying new
  structural knowledge.

The output is metadata only: no ROM bytes, graphics or audio payloads.
"""
import argparse
import csv
import glob
import hashlib
import json
import os
import re
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import level_package as L  # noqa: E402
import player_scripts as PS  # noqa: E402
import rom as R  # noqa: E402
import rom_flow as F  # noqa: E402
import tile_decompress as T  # noqa: E402

FORMAT = 1
ROM_SIZE = 524288
BANK_SIZE = 0x4000
BANKS = ROM_SIZE // BANK_SIZE
ROM_SHA256 = R.SHA256
CATEGORIES = ("CODE", "DATA", "GRAPHICS", "MUSIC", "COMPRESSED", "PADDING", "UNKNOWN")
ZONES = 6            # six ROM zones x three acts (zone index 6 aliases zone 0's tables)
ACTS_PER_ZONE = 3
DEFAULT_OUTPUT = ROOT / "data" / "rom-ledger"
REVIEWED = "data/rom-ledger/reviewed-ranges.json"
DEFAULT_ROM = ROOT.parent / "source" / "Sonic Chaos (Europe).sms"
REGEN = "python tools/rom_ledger.py <SonicChaos.sms>"

# Evidence quality, strongest first.
QUALITY = ("byte_verified_assembly", "decoder_verified", "reviewed_flow_verified", "structure_verified",
           "manifest_hash_verified", "manifest_copy")
QUALITY_RANK = {q: i for i, q in enumerate(QUALITY)}
ENGINE_BANKS = (0, 1)   # file offset == CPU address (resident engine region)
CRLF, LF = b"\r\n", b"\n"   # committed files are LF; Windows checkouts may convert


def hx(value, digits=5):
    return "0x%0*X" % (digits, value)


def rel(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def sha256(data):
    return hashlib.sha256(data).hexdigest()


# --- claims -----------------------------------------------------------------
def make_claim(start, end, primary, importer, source, evidence, *, subtype=None,
               subsystem=None, logical_content=None, recovered=False, name=None,
               basis="independent"):
    if not (0 <= start < end <= ROM_SIZE):
        raise ValueError("claim %s..%s outside the ROM (%s)" % (hx(start), hx(end), name))
    if primary not in CATEGORIES or primary == "UNKNOWN":
        raise ValueError("claims need a known primary class, got %r" % primary)
    if evidence not in QUALITY_RANK:
        raise ValueError("unknown evidence quality %r" % evidence)
    return {
        "start": start, "end": end, "primary": primary, "subtype": subtype,
        "subsystem": subsystem, "logical_content": logical_content,
        "recovered": bool(recovered), "evidence": evidence,
        "basis": basis, "importer": importer,
        "sources": [source] if source else [], "names": [name] if name else [],
    }


def dedupe_claims(claims):
    """Merge exact duplicates (same range and attributes) from different sources."""
    merged = OrderedDict()
    for c in claims:
        key = (c["start"], c["end"], c["primary"], c["subtype"], c["subsystem"],
               c["logical_content"], c["recovered"], c["basis"])
        if key not in merged:
            merged[key] = dict(c, sources=list(c["sources"]), names=list(c["names"]),
                               importers=[c["importer"]])
            del merged[key]["importer"]
            continue
        m = merged[key]
        for s in c["sources"]:
            if s not in m["sources"]:
                m["sources"].append(s)
        for n in c["names"]:
            if n not in m["names"]:
                m["names"].append(n)
        if c["importer"] not in m["importers"]:
            m["importers"].append(c["importer"])
        if QUALITY_RANK[c["evidence"]] < QUALITY_RANK[m["evidence"]]:
            m["evidence"] = c["evidence"]
    out = sorted(merged.values(), key=lambda c: (c["start"], c["end"], c["primary"],
                                                 c["subtype"] or "", c["subsystem"] or "",
                                                 c["logical_content"] or "", c["recovered"]))
    for c in out:
        c["sources"].sort()
        c["names"].sort()
        c["importers"].sort()
    for i, c in enumerate(out):
        c["id"] = i
    return out


# --- Stage A: recovered assembly --------------------------------------------
def import_recovered(root=ROOT, drop_regions=()):
    """All registered regions of asm/recovered/regions.json (never hard-coded).

    ``drop_regions`` (names) lets an evidence tool ask what the ledger said before those regions existed.
    """
    manifest = root / "asm" / "recovered" / "regions.json"
    regions = [r for r in json.loads(manifest.read_text(encoding="utf-8")) if r["name"] not in drop_regions]
    claims = []
    for r in regions:
        if r["end"] - r["start"] != r["bytes"]:
            raise ValueError("region %s: bytes != end-start" % r["name"])
        if r["start"] // BANK_SIZE != r["bank"] or (r["end"] - 1) // BANK_SIZE != r["bank"]:
            raise ValueError("region %s crosses or misstates its bank" % r["name"])
        if r["kind"] not in ("code", "data"):
            raise ValueError("region %s: unknown kind %r" % (r["name"], r["kind"]))
        if not (root / "asm" / "recovered" / r["file"]).is_file():
            raise ValueError("region %s: missing source file %s" % (r["name"], r["file"]))
        m = re.match(r"^object_([0-9a-f]{2})_", r["name"])
        claims.append(make_claim(
            r["start"], r["end"], r["kind"].upper(), "recovered_assembly",
            "asm/recovered/" + r["file"], "byte_verified_assembly",
            subsystem=("object-type-$%s" % m.group(1).upper()) if m else None,
            recovered=True, name=r["name"], basis="recovery_manifest"))
    return claims, regions


# --- Stage B importers --------------------------------------------------------
def bank_check(start, end, what):
    if start // BANK_SIZE != (end - 1) // BANK_SIZE:
        raise ValueError("%s %s..%s crosses a bank boundary" % (what, hx(start), hx(end)))


def import_level_structures(rom):
    """Per-act structures found through the existing level_package decoders."""
    src = "tools/level_package.py"
    claims = []
    seen_art = set()

    def add(start, end, primary, subtype, evidence, source, **kw):
        claims.append(make_claim(start, end, primary, "level_structures", source,
                                 evidence, subtype=subtype, **kw))

    block_bases = {}
    for z in range(ZONES):
        sub = "level-zone-%d" % z
        add(L.ACT_HEADER_TABLE + 2 * z, L.ACT_HEADER_TABLE + 2 * z + 2, "DATA",
            "act-header-zone-pointer", "structure_verified", src + " (loader $4FDC)", subsystem=sub)
        add(L.OBJECT_ZONE_TABLE_ROM + 2 * z, L.OBJECT_ZONE_TABLE_ROM + 2 * z + 2, "DATA",
            "object-list-zone-pointer", "structure_verified", src + " (placement creator)", subsystem=sub)
        add(L.START_TABLE + 2 * z, L.START_TABLE + 2 * z + 2, "DATA",
            "player-start-zone-pointer", "structure_verified", src + " (loader $4E57)", subsystem=sub)
        for a in range(ACTS_PER_ZONE):
            act = "level-zone-%d-act-%d" % (z, a)
            h = L.act_header(rom, z, a)
            add(h["act_pointer_rom"], h["act_pointer_rom"] + 2, "DATA", "act-header-act-pointer",
                "structure_verified", src + " (loader $4FDC)", subsystem=sub, name=act)
            add(h["header_rom"], h["header_rom"] + L.ACT_HEADER_SIZE, "DATA", "level-act-header",
                "structure_verified", src + " (loader $4FDC)", subsystem=sub, name=act)
            cells, end, terminated = L.decode_layout_stream(rom, h["layout_rom"])
            if not terminated:
                raise ValueError(act + ": layout stream did not terminate")
            add(h["layout_rom"], end, "COMPRESSED", "level-layout-rle", "decoder_verified",
                src + " decode_layout_stream (loader $4DC4)", subsystem=sub,
                logical_content="level layout cells (%d encoded)" % len(cells), name=act)
            block_bases.setdefault(h["block_mapping_rom"], set()).update(cells)
            ol = L.object_list_pointer(rom, z, a)
            add(ol["act_pointer_rom"], ol["act_pointer_rom"] + 2, "DATA", "object-list-act-pointer",
                "structure_verified", src + " (placement creator)", subsystem=sub, name=act)
            records, tail = L.decode_object_list(rom, ol["list_rom"])
            add(ol["list_rom"], tail + 1, "DATA", "object-placement-list", "decoder_verified",
                src + " decode_object_list (creator $70031)", subsystem=sub,
                logical_content="%d nine-byte records + $FF terminator" % len(records), name=act)
            ps = L.player_start(rom, z, a)
            sp = L.START_TABLE
            zone_ptr = L.u16(rom, sp + 2 * z)
            add(zone_ptr + 2 * a, zone_ptr + 2 * a + 2, "DATA", "player-start-act-pointer",
                "structure_verified", src + " (loader $4E57)", subsystem=sub, name=act)
            add(ps["record_rom"], ps["record_rom"] + 8, "DATA", "player-start-record",
                "structure_verified", src + " player_start (loader $4E57)", subsystem=sub, name=act)
            art = L.art_entry(rom, z, a)
            add(art["entry_rom"], art["entry_rom"] + L.ART_ENTRY_SIZE, "DATA", "level-art-load-entry",
                "structure_verified", src + " art_entry (loader $78E1)", subsystem=sub, name=act)
            add(art["supplemental_list_rom"], art["supplemental_terminator_rom"] + 1, "DATA",
                "level-art-supplemental-list", "structure_verified", src + " art_entry (loader $78E1)",
                subsystem=sub, name=act, logical_content="%d five-byte entries + $FF" % len(art["supplemental"]))
            for stream in [art["primary"]] + art["supplemental"]:
                off = stream["stream_rom"]
                if off in seen_art:
                    continue
                seen_art.add(off)
                s, e, tiles = tile_stream_extent(rom, off)
                add(s, e, "COMPRESSED", "tile-stream", "decoder_verified",
                    "tools/tile_decompress.py (loader tile routine)", subsystem=sub,
                    logical_content="tile graphics (%d tiles)" % tiles)
            pal = L.palette_selection(rom, z, a)
            add(pal["selector_rom"], pal["selector_rom"] + 2, "DATA", "palette-selector",
                "structure_verified", src + " palette_selection (loader $794F)", subsystem=sub, name=act)
            for key in ("background_rom", "sprite_rom"):
                add(pal[key], pal[key] + 16, "GRAPHICS", "cram-palette", "structure_verified",
                    src + " palette_selection (resolver $3B63E)", subsystem=sub, name=act)
    # block-mapping tables: 256 word pointers (cell values are bytes) + used 32-byte blocks
    for base in sorted(block_bases):
        bank = base // BANK_SIZE
        for i in range(256):
            cpu = L.u16(rom, base + 2 * i)
            if not 0x8000 <= cpu <= 0xBFFF:
                raise ValueError("block-mapping pointer %d at %s is not a bank-slot address" % (i, hx(base)))
        claims.append(make_claim(base, base + 512, "DATA", "level_structures",
                                 src + " block_mapping (render loops $5316/$53DA)",
                                 "structure_verified", subtype="block-mapping-pointer-table",
                                 subsystem="level-renderer", logical_content="256 word pointers",
                                 name="block mapping table %s" % hx(base)))
        for block in sorted(block_bases[base]):
            off = L.bank_cpu_to_rom(bank, L.u16(rom, base + 2 * block))
            claims.append(make_claim(off, off + 32, "DATA", "level_structures",
                                     src + " block_mapping (render loops $5316/$53DA)",
                                     "structure_verified", subtype="block-mapping-entry",
                                     subsystem="level-renderer",
                                     logical_content="16 tile-entry words (4x4 tiles)",
                                     name="block $%02X of table %s" % (block, hx(base))))
    return claims


def tile_stream_extent(rom, offset):
    """Bytes the tile decoder consumes: header, payload and command stream.

    Verified contiguous (payload end == command stream start) for every stream
    imported; anything else is rejected rather than guessed.
    """
    count = T.read_u16le(rom, offset + 2)
    cmd = offset + T.read_u16le(rom, offset + 4)
    pos = offset + 6
    for i in range(count):
        c = T.extract_command(rom, cmd, i)
        if c == 1:
            pos += 32
        elif c in (2, 3):
            _, pos = T._expand_sparse_tile(rom, pos)
    if pos != cmd:
        raise ValueError("tile stream %s is not contiguous with its command stream" % hx(offset))
    return offset, cmd + (count + 3) // 4, count


def import_collision(rom):
    """Collision pointer table, 7-byte surface headers and 32-byte profile arrays."""
    src = "tools/rom.py header(); docs/data-formats.md"
    table = 0x38000
    ptrs = [0x30000 + R.u16(rom, table + 2 * t) for t in range(256)]
    headers = {}
    for t in range(256):
        h = R.header(rom, t, 0)
        headers[h["address"]] = h
        if rom[h["address"]] & 0x20:
            alt = R.header(rom, t, 1)
            headers[alt["address"]] = alt
    addresses = sorted(headers)
    if any(b - a != 7 for a, b in zip(addresses, addresses[1:])):
        raise ValueError("collision headers are not a contiguous 7-byte-stride block")
    claims = [make_claim(table, table + 512, "DATA", "collision", src, "structure_verified",
                         subtype="collision-header-pointer-table", subsystem="collision",
                         logical_content="256 CPU pointers (+$30000)", name="collision header pointers")]
    claims.append(make_claim(addresses[0], addresses[-1] + 7, "DATA", "collision", src,
                             "structure_verified", subtype="collision-surface-header",
                             subsystem="collision",
                             logical_content="%d seven-byte headers (256 base + %d alternates)"
                             % (len(addresses), len(addresses) - 256), name="collision surface headers"))
    profiles = sorted({h["vertical_pointer"] for h in headers.values()} |
                      {h["horizontal_pointer"] for h in headers.values()})
    for p in profiles:
        claims.append(make_claim(p, p + 32, "DATA", "collision", src, "structure_verified",
                                 subtype="collision-profile-array", subsystem="collision",
                                 logical_content="32 height/width bytes", name="collision profile"))
    return claims


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def import_pointer_tables(rom, root=ROOT):
    """Tables with a committed export that the ROM bytes must reproduce."""
    claims = []
    data = root / "data"
    rows = read_csv(data / "sound-index-sms.csv")
    for r in rows:
        p = int(r["pointer_file"], 16)
        if R.u16(rom, p) != int(r["stored_address"], 16):
            raise ValueError("sound pointer %s does not match the ROM" % r["id_hex"])
        claims.append(make_claim(p, p + 2, "DATA", "pointer_tables", "data/sound-index-sms.csv",
                                 "structure_verified", subtype="sound-track-pointer",
                                 subsystem="sound", name="sound id $" + r["id_hex"]))
    rows = read_csv(data / "sonic-state-scripts.csv")
    for i, r in enumerate(rows):
        p = 0x30000 + 2 * i
        if R.u16(rom, p) != int(r["script_cpu"], 16):
            raise ValueError("state-script pointer %d does not match the ROM" % i)
        claims.append(make_claim(p, p + 2, "DATA", "pointer_tables", "data/sonic-state-scripts.csv; tools/export_reference.py",
                                 "structure_verified", subtype="player-state-script-pointer",
                                 subsystem="player-states", name="state $" + r["state_hex"]))
    rows = read_csv(data / "twist-dispatch.csv")
    for r in rows:
        p = int(r["pointer_file"], 16)
        if R.u16(rom, p) != int(r["handler_cpu"], 16):
            raise ValueError("twist dispatch pointer at %s does not match the ROM" % r["pointer_file"])
        claims.append(make_claim(p, p + 2, "DATA", "pointer_tables", "data/twist-dispatch.csv",
                                 "structure_verified", subtype="twist-dispatch-pointer",
                                 subsystem="terrain-twist", name="tile $" + r["tile_hex"]))
    for r in read_csv(data / "movement-tables.csv"):
        p = int(r["file_offset"], 16)
        claims.append(make_claim(p, p + 4, "DATA", "pointer_tables", "data/movement-tables.csv",
                                 "structure_verified", subtype="movement-table-entry",
                                 subsystem="player-movement", logical_content="two signed 8.8 values",
                                 name="%s state $%s" % (r["table"], r["state_hex"])))
    for r in read_csv(data / "surface-modifiers.csv"):
        p = int(r["file_offset"], 16)
        claims.append(make_claim(p, p + 2, "DATA", "pointer_tables", "data/surface-modifiers.csv",
                                 "structure_verified", subtype="surface-modifier",
                                 subsystem="player-movement", logical_content="signed 8.8 increment",
                                 name="surface modifier +%s" % r["byte_offset"]))
    return claims


def walk_json(node, path=()):
    if isinstance(node, dict):
        yield path, node
        for k, v in node.items():
            for item in walk_json(v, path + (k,)):
                yield item
    elif isinstance(node, list):
        for v in node:
            for item in walk_json(v, path):
                yield item


def hexnum(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and re.fullmatch(r"(0x|\$)[0-9A-Fa-f]+", value):
        return int(value.replace("$", "0x"), 16)
    return None


def cache_files(root=ROOT):
    pattern = str(root / "data" / "rom-cache" / "**" / "*.json")
    return sorted(Path(p) for p in glob.glob(pattern, recursive=True))


SUBSYSTEM_BY_CACHE = {
    "object-18-act-clear.json": "object-type-$18",
    "thz3/object-50.json": "object-type-$50",
}


def import_layout_manifests(rom, root=ROOT):
    """Layout descriptors in implementation manifests, re-decoded from the ROM."""
    claims, rejected = [], []
    for path in cache_files(root):
        if not path.name.endswith("manifest.json") or path.parent.name == "levels":
            continue
        if path.name != "implementation-manifest.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        rp = rel(path)
        subsystem = "special-stage" if "special-stages" in rp else "level"
        for where, node in walk_json(data):
            if not {"rom", "end_rom", "encoded_cells"} <= set(node):
                continue
            start, end = node["rom"], node["end_rom"]
            cells, real_end, terminated = L.decode_layout_stream(rom, start)
            label = "/".join(where)
            if not (terminated and real_end == end and len(cells) == node["encoded_cells"]):
                rejected.append({"source": rp, "where": label, "start": start, "end": end,
                                 "reason": "manifest layout extent does not match a fresh decode"})
                continue
            claims.append(make_claim(start, end, "COMPRESSED", "layout_manifests", rp,
                                     "decoder_verified", subtype="level-layout-rle", subsystem=subsystem,
                                     logical_content="level layout cells (%d encoded)" % len(cells),
                                     name=label))
    return claims, rejected


def import_manifest_ranges(rom, root=ROOT, recovered_regions=()):
    """Audit-manifest ranges: hash-verified, imported only when ``kind`` is stated.

    Returns (claims, unclassified, rejected, ignored_count). Ranges whose SHA-256
    matches the ROM but which state no code/data kind are reported, not guessed.
    """
    claims, unclassified, rejected = [], {}, []
    ignored = 0
    recovered_ranges = {(r["start"], r["end"], r["kind"]) for r in recovered_regions}
    for path in cache_files(root):
        rp = rel(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        stem = path.parent.name + "/" + path.name
        subsystem = SUBSYSTEM_BY_CACHE.get(path.name) or SUBSYSTEM_BY_CACHE.get(stem)
        for where, node in walk_json(data):
            # form 1: start + length (+ optional end) + sha256 [+ kind]
            skey = next((k for k in ("rom_offset", "rom", "file_offset") if hexnum(node.get(k)) is not None), None)
            lkey = next((k for k in ("length", "bytes", "size")
                         if isinstance(node.get(k), int) and not isinstance(node.get(k), bool)), None)
            if skey and lkey:
                start, length = hexnum(node[skey]), node[lkey]
                name = node.get("name") or node.get("purpose") or node.get("id") or ""
                label = {"source": rp, "name": str(name)[:80], "start": start, "end": start + length}
                if length <= 0 or start < 0 or start + length > ROM_SIZE:
                    rejected.append(dict(label, reason="range outside the ROM"))
                    continue
                # some caches state the exclusive end as a file offset, others as a CPU address
                ends = {start + length, 0x8000 + start % BANK_SIZE + length}
                for ekey in ("end_exclusive", "rom_end_exclusive", "end_rom", "end_cpu_exclusive", "cpu_end_exclusive"):
                    if ekey in node and hexnum(node[ekey]) is not None and hexnum(node[ekey]) not in ends:
                        rejected.append(dict(label, reason="%s matches neither the file nor the CPU end" % ekey))
                        break
                else:
                    digest = node.get("sha256")
                    if not digest:
                        ignored += 1
                        continue
                    if sha256(rom[start:start + length]) != digest:
                        rejected.append(dict(label, reason="sha256 does not match the ROM range"))
                        continue
                    kind = node.get("kind")
                    if kind in ("code", "data"):
                        claims.append(make_claim(start, start + length, kind.upper(), "audit_manifests", rp,
                                                 "manifest_hash_verified", subsystem=subsystem,
                                                 name=str(name)[:80] or None))
                    else:
                        unclassified.setdefault((start, start + length), dict(label, kind=kind))
                continue
            # form 2: rom_start/rom_end_exclusive/kind copies of recovered regions
            if "rom_start" in node and "rom_end_exclusive" in node and "kind" in node:
                start, end = hexnum(node["rom_start"]), hexnum(node["rom_end_exclusive"])
                if start is None or end is None or not node["kind"] in ("code", "data"):
                    continue
                # derivative copies of regions.json: must match a registered region exactly
                if (start, end, node["kind"]) not in recovered_ranges:
                    rejected.append({"source": rp, "name": str(node.get("name"))[:80], "start": start,
                                     "end": end, "reason": "manifest copy matches no recovered region "
                                     "(exact range and kind required)"})
                    continue
                claims.append(make_claim(start, end, node["kind"].upper(), "manifest_copies", rp,
                                         "manifest_copy", name=node.get("name"),
                                         basis="recovery_manifest"))
    return claims, unclassified, rejected, ignored


# --- DECOMP-1A: reviewed classifications ------------------------------------------
def dispatch_table_word(rom, region, index):
    p = region["start"] + 2 * index
    if p + 2 > region["end"]:
        raise ValueError("dispatch table %s has no entry %d" % (region["name"], index))
    return R.u16(rom, p)


def import_reviewed(rom, root=ROOT, regions=None):
    """Re-verify every reviewed code-flow claim; any stale or inconsistent entry raises.

    Each review names its entry points and the control-flow support for each:
    ``{"site": off}`` (a CALL/JP/JR at ``off`` inside proven code resolves to the
    entry) or ``{"table": name, "index": i, "load_site": off}`` (word ``i`` of a
    recovered dispatch table, whose address is loaded by proven code at
    ``load_site``). Proven code is the recovered CODE regions plus the claimed
    runs of reviews already verified; reviews are verified to a fixed point, so
    file order does not matter. Control flow is then re-run confined to the
    review's bounds and must fetch every claimed byte as an instruction without
    touching a recovered DATA region.
    """
    path = Path(root) / REVIEWED
    if not path.is_file():
        return [], {"reviews": 0, "claims": 0, "unresolved": []}
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("rom_sha256") != ROM_SHA256 or doc.get("format") != 1:
        raise ValueError("reviewed-ranges.json is for a different ROM or format")
    if regions is None:
        regions = json.loads((Path(root) / "asm" / "recovered" / "regions.json").read_text(encoding="utf-8"))
    by_name = {r["name"]: r for r in regions}
    proven = {}
    for r in F.code_regions(regions):
        for p, n, _ in F.region_instructions(rom, r):
            proven[p] = n
    data_bytes = set()
    for r in regions:
        if r["kind"] == "data":
            data_bytes.update(range(r["start"], r["end"]))
    loads = {}
    for r in F.code_regions(regions):
        for p, n, d in F.region_instructions(rom, r):
            if d.op == F.OP.LD:
                for kind, value in d.operands:
                    if kind.name == "IMM":
                        loads.setdefault(value, set()).add(p)

    def jumps_after(site):
        for r in F.code_regions(regions):
            if r["start"] <= site < r["end"]:
                return any(F.is_indirect_jump(d) for p, _, d in F.region_instructions(rom, r) if p > site)
        return False

    def seed_ok(seed):
        via = seed["via"]
        off = seed["offset"]
        if "site" in via:
            site = via["site"]
            if site not in proven:
                return False
            d = F.decode(rom, site)
            if d.op not in F.TRANSFER_OPS:
                return False
            target = F._addr_operand(d)
            return target is not None and F.resolve_target(site, target) == off
        if "player_script" in via:
            return PS.seed_supported(rom, off, via["player_script"])
        region = by_name.get(via.get("table"))
        if region is None or region["kind"] != "data" or region["start"] >= F.RESIDENT_END:
            raise ValueError("review seed %s names a non-resident or unknown dispatch table" % hx(off))
        if via["load_site"] not in loads.get(region["start"], ()):
            raise ValueError("no recovered code loads the address of table %s at %s"
                             % (region["name"], hx(via["load_site"])))
        if not jumps_after(via["load_site"]):
            raise ValueError("the routine loading table %s never jumps indirectly afterwards" % region["name"])
        return dispatch_table_word(rom, region, via["index"]) == off

    pending = list(doc["code_flow_reviews"])
    verified, claims = [], []
    while pending:
        progress = False
        for review in list(pending):
            lo, hi = review["bounds"]
            resident = hi <= F.RESIDENT_END          # banks 0 and 1 form one contiguous engine region
            if not (0 <= lo < hi <= ROM_SIZE) or (not resident and lo // BANK_SIZE != (hi - 1) // BANK_SIZE):
                raise ValueError("review %s: bounds outside one bank" % review["id"])
            if not all(seed_ok(s) for s in review["seeds"]):
                continue                         # every recorded seed must be supported (deferred until it is)
            good = [s["offset"] for s in review["seeds"]]
            reached, notes = F.descend(rom, good, lo, hi)
            covered = set()
            for a, n in reached.items():
                covered.update(range(a, a + n))
            claimed = [c for c in review["claims"]]
            wanted = set()
            for c in claimed:
                if c["primary"] != "CODE" or not lo <= c["start"] < c["end"] <= hi:
                    raise ValueError("review %s: claim %s-%s is not CODE inside its bounds"
                                     % (review["id"], hx(c["start"]), hx(c["end"])))
                wanted.update(range(c["start"], c["end"]))
            if not wanted <= covered:
                continue                         # entry points not all proven yet
            # run boundaries must fall on fetched instruction boundaries
            for c in claimed:
                if c["start"] not in reached or (c["end"] not in reached and c["end"] not in covered_end(reached)):
                    raise ValueError("review %s: claim %s-%s splits an instruction"
                                     % (review["id"], hx(c["start"]), hx(c["end"])))
            if covered & data_bytes:
                raise ValueError("review %s: flow reaches recovered DATA at %s"
                                 % (review["id"], hx(min(covered & data_bytes))))
            for c in claimed:
                for a, n in reached.items():
                    if c["start"] <= a < c["end"]:
                        proven[a] = n
                claims.append(make_claim(
                    c["start"], c["end"], "CODE", "reviewed_ranges", REVIEWED, "reviewed_flow_verified",
                    subtype=c.get("subtype", "routine"), subsystem=c.get("subsystem"),
                    logical_content=c.get("logical_content"),
                    name=" / ".join(a["name"] for a in review["audit_ranges"] if a.get("name")) or None))
                claims[-1]["sources"] += sorted({a["source"] for a in review["audit_ranges"]})
            pending.remove(review)
            verified.append(review)
            progress = True
        if not progress:
            raise ValueError("reviewed-ranges.json has unverifiable reviews: %s"
                             % ", ".join(str(r["id"]) for r in pending))
    summary = {"reviews": len(verified), "claims": len(claims),
               "unresolved": doc.get("unresolved", [])}
    return claims, summary


def covered_end(reached):
    return {a + n for a, n in reached.items()}


# --- resolution -----------------------------------------------------------------
def resolve(claims):
    """Reduce claims to one primary class per byte.

    Returns (segments, conflicts, overlap_stats). Segments never cross a bank and
    cover [0, ROM_SIZE) contiguously.
    """
    points = {0, ROM_SIZE}
    points.update(b * BANK_SIZE for b in range(BANKS + 1))
    for c in claims:
        points.add(c["start"])
        points.add(c["end"])
    cuts = sorted(points)
    by_start = sorted(claims, key=lambda c: (c["start"], c["end"], c["id"]))
    active, nxt = [], 0
    raw = []
    for lo, hi in zip(cuts, cuts[1:]):
        while nxt < len(by_start) and by_start[nxt]["start"] <= lo:
            active.append(by_start[nxt])
            nxt += 1
        active = [c for c in active if c["end"] > lo]
        raw.append((lo, hi, tuple(c["id"] for c in sorted(active, key=lambda c: c["id"]))))
    by_id = {c["id"]: c for c in claims}
    segments = []
    for lo, hi, ids in raw:
        seg = describe(lo, hi, [by_id[i] for i in ids])
        if segments and segments[-1]["_ids"] == ids and segments[-1]["end"] == lo \
                and segments[-1]["start"] // BANK_SIZE == lo // BANK_SIZE:
            segments[-1]["end"] = hi
            segments[-1]["length"] = hi - segments[-1]["start"]
        else:
            seg["_ids"] = ids
            segments.append(seg)
    for seg in segments:
        seg["claims"] = list(seg.pop("_ids"))
    conflicts = find_overlaps(claims)
    return segments, conflicts


def describe(lo, hi, covering):
    primaries = sorted({c["primary"] for c in covering})
    contested = len(primaries) > 1
    if not covering:
        primary = "UNKNOWN"
    elif contested:
        primary = "UNKNOWN"
    else:
        primary = primaries[0]
    pool = [] if contested else covering
    # narrowest claim wins for descriptive fields; ties -> strongest evidence
    ranked = sorted(pool, key=lambda c: (c["end"] - c["start"], QUALITY_RANK[c["evidence"]], c["id"]))

    def pick(field):
        for c in ranked:
            if c[field]:
                return c[field]
        return None

    independent = any(c["basis"] == "independent" for c in pool)
    best = min((QUALITY_RANK[c["evidence"]] for c in covering), default=None)
    return {
        "start": lo, "end": hi, "length": hi - lo, "bank": lo // BANK_SIZE,
        "cpu_paged": 0x8000 + lo % BANK_SIZE,
        "cpu_resident": lo if lo // BANK_SIZE in ENGINE_BANKS else None,
        "primary": primary, "subtype": pick("subtype"), "subsystem": pick("subsystem"),
        "logical_content": pick("logical_content"),
        "recovery": "recovered" if any(c["recovered"] for c in covering) else "not_recovered",
        "classification_basis": ("contested" if contested else "independent" if independent
                                 else "recovery_manifest_only" if pool else "none"),
        "evidence": QUALITY[best] if best is not None else None,
        "regions": sorted({n for c in covering if c["recovered"] for n in c["names"]}),
        "contested": contested,
    }


def find_overlaps(claims):
    """Pairwise overlap audit: nested-compatible, partial-compatible, contradictory."""
    ordered = sorted(claims, key=lambda c: (c["start"], c["end"], c["id"]))
    stats = {"compatible_nested_pairs": 0, "compatible_partial_overlap_pairs": 0,
             "contradictory_pairs": 0}
    partial, hard = [], []
    active = []
    for c in ordered:
        active = [a for a in active if a["end"] > c["start"]]
        for a in active:
            lo, hi = max(a["start"], c["start"]), min(a["end"], c["end"])
            if lo >= hi:
                continue
            if a["primary"] != c["primary"]:
                stats["contradictory_pairs"] += 1
                hard.append({"claims": [a["id"], c["id"]], "overlap": [lo, hi],
                             "classes": [a["primary"], c["primary"]],
                             "names": [(a["names"] or [None])[0], (c["names"] or [None])[0]],
                             "sources": [a["sources"][:1], c["sources"][:1]]})
            elif (a["start"] <= c["start"] and a["end"] >= c["end"]) or \
                    (c["start"] <= a["start"] and c["end"] >= a["end"]):
                stats["compatible_nested_pairs"] += 1
            else:
                stats["compatible_partial_overlap_pairs"] += 1
                partial.append({"claims": [a["id"], c["id"]], "overlap": [lo, hi],
                                "class": a["primary"]})
        active.append(c)
    return {"stats": stats, "contradictory": hard, "partial": partial}


# --- reporting -----------------------------------------------------------------
def totals(segments):
    by_cat = OrderedDict((c, 0) for c in CATEGORIES)
    out = {"by_category": by_cat, "recovered_bytes": 0, "recovered_code_bytes": 0,
           "recovered_data_bytes": 0, "contested_bytes": 0, "classified_bytes": 0,
           "independent_structural_bytes": 0, "classified_by_recovery_only_bytes": 0,
           "recovered_and_independently_classified_bytes": 0}
    for s in segments:
        n = s["length"]
        by_cat[s["primary"]] += n
        if s["primary"] != "UNKNOWN":
            out["classified_bytes"] += n
        if s["contested"]:
            out["contested_bytes"] += n
        if s["recovery"] == "recovered":
            out["recovered_bytes"] += n
            if s["primary"] == "CODE":
                out["recovered_code_bytes"] += n
            elif s["primary"] == "DATA":
                out["recovered_data_bytes"] += n
        if s["classification_basis"] == "independent":
            out["independent_structural_bytes"] += n
            if s["recovery"] == "recovered":
                out["recovered_and_independently_classified_bytes"] += n
        if s["classification_basis"] == "recovery_manifest_only":
            out["classified_by_recovery_only_bytes"] += n
    out["unknown_bytes"] = by_cat["UNKNOWN"]
    out["total_bytes"] = sum(by_cat.values())
    return out


def bank_totals(segments):
    banks = []
    for b in range(BANKS):
        part = [s for s in segments if s["bank"] == b]
        t = totals(part)
        banks.append(OrderedDict([
            ("bank", b), ("start", b * BANK_SIZE), ("end", (b + 1) * BANK_SIZE),
            ("by_category", t["by_category"]), ("classified_bytes", t["classified_bytes"]),
            ("recovered_bytes", t["recovered_bytes"]), ("unknown_bytes", t["unknown_bytes"]),
            ("contested_bytes", t["contested_bytes"]),
        ]))
    return banks


def build_ledger(rom, root=ROOT, reviewed=True, drop_regions=()):
    if len(rom) != ROM_SIZE or sha256(rom) != ROM_SHA256:
        raise ValueError("Expected Sonic Chaos (Europe) v1.2, %d bytes, SHA-256 %s" % (ROM_SIZE, ROM_SHA256))
    recovered, regions = import_recovered(root, drop_regions)
    raw = list(recovered)
    raw += import_level_structures(rom)
    raw += import_collision(rom)
    raw += import_pointer_tables(rom, root)
    layout_claims, rejected = import_layout_manifests(rom, root)
    raw += layout_claims
    manifest_claims, unclassified, rejected_ranges, ignored = import_manifest_ranges(rom, root, regions)
    raw += manifest_claims
    review_summary = {"reviews": 0, "claims": 0, "unresolved": []}
    if reviewed:
        review_claims, review_summary = import_reviewed(rom, root, regions)
        raw += review_claims
    rejected = rejected + rejected_ranges
    claims = dedupe_claims(raw)
    segments, overlaps = resolve(claims)
    t = totals(segments)
    if t["total_bytes"] != ROM_SIZE:
        raise AssertionError("ledger does not account for the whole ROM")
    unclassified_rows = [OrderedDict([("start", start), ("end", end), ("name", row["name"]),
                                      ("source", row["source"])])
                         for (start, end), row in sorted(unclassified.items())]
    for row in unclassified_rows:
        by_class = OrderedDict()
        for seg in segments:
            if seg["start"] < row["end"] and seg["end"] > row["start"]:
                n = min(seg["end"], row["end"]) - max(seg["start"], row["start"])
                by_class[seg["primary"]] = by_class.get(seg["primary"], 0) + n
        row["bytes_by_class"] = OrderedDict(sorted(by_class.items()))
        unknown_n = by_class.get("UNKNOWN", 0)
        row["status"] = ("classified" if not unknown_n else
                         "unresolved" if unknown_n == row["end"] - row["start"] else "partial")
    union = merge_ranges([(r["start"], r["end"]) for r in unclassified_rows])
    unk_in_union = sum(min(s["end"], hi) - max(s["start"], lo)
                       for lo, hi in union for s in segments
                       if s["primary"] == "UNKNOWN" and s["start"] < hi and s["end"] > lo)
    ledger = OrderedDict()
    ledger["format"] = FORMAT
    ledger["generator"] = "tools/rom_ledger.py"
    ledger["regenerate"] = REGEN
    ledger["rom"] = OrderedDict([("name", "Sonic Chaos (Europe) v1.2"), ("size", ROM_SIZE),
                                 ("sha256", ROM_SHA256), ("banks", BANKS), ("bank_size", BANK_SIZE)])
    ledger["conventions"] = OrderedDict([
        ("offsets", "zero-based file offsets, half-open [start, end); authoritative"),
        ("cpu_paged", "0x8000 + offset % 0x4000: address when the bank is paged into slot 2"),
        ("cpu_resident", "file offset == CPU address; banks 0 and 1 only (resident engine region)"),
        ("categories", list(CATEGORIES)),
        ("contested", "overlapping claims with different primary classes: bytes are UNKNOWN until resolved"),
    ])
    ledger["totals"] = t
    ledger["coverage"] = OrderedDict([
        ("recovered_assembly_bytes", t["recovered_bytes"]),
        ("recovered_assembly_pct", pct(t["recovered_bytes"])),
        ("structurally_classified_bytes", t["classified_bytes"]),
        ("structurally_classified_pct", pct(t["classified_bytes"])),
        ("unknown_bytes", t["unknown_bytes"]),
        ("unknown_pct", pct(t["unknown_bytes"])),
    ])
    ledger["recovered_manifest"] = OrderedDict([
        ("regions", len(regions)), ("bytes", sum(r["bytes"] for r in regions)),
        ("code_bytes", sum(r["bytes"] for r in regions if r["kind"] == "code")),
        ("data_bytes", sum(r["bytes"] for r in regions if r["kind"] == "data")),
        ("source", "asm/recovered/regions.json")])
    ledger["banks"] = bank_totals(segments)
    ledger["overlaps"] = overlaps
    ledger["unclassified_range_claims"] = OrderedDict([
        ("note", "ranges whose SHA-256 matches the ROM but whose cache states no code/data kind; "
                 "not imported, listed as the cheapest next classifications"),
        ("count", len(unclassified_rows)), ("union_bytes", sum(hi - lo for lo, hi in union)),
        ("union_bytes_still_unknown", unk_in_union), ("ranges", unclassified_rows)])
    ledger["reviewed"] = OrderedDict([
        ("source", REVIEWED), ("reviews", review_summary["reviews"]), ("claims", review_summary["claims"]),
        ("code_bytes", sum(c["end"] - c["start"] for c in claims if "reviewed_ranges" in c["importers"])),
        ("unresolved_clusters", len(review_summary["unresolved"])),
        ("unresolved_unknown_bytes", sum(u["unknown_bytes"] for u in review_summary["unresolved"]))])
    ledger["rejected_claims"] = rejected
    ledger["ignored_hashless_ranges"] = ignored
    ledger["claims"] = claims
    ledger["segments"] = segments
    return ledger


def merge_ranges(ranges):
    out = []
    for lo, hi in sorted(ranges):
        if out and lo <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], hi))
        else:
            out.append((lo, hi))
    return out


def pct(n):
    return round(100.0 * n / ROM_SIZE, 3)


def dumps(value):
    text = json.dumps(value, indent=1, sort_keys=False)
    return text + "\n"


def summary_markdown(ledger):
    t = ledger["totals"]
    lines = ["# ROM address ledger summary", "",
             "Generated by `%s`. Do not edit by hand." % REGEN, "",
             "ROM: %s, %d bytes, SHA-256 `%s`" % (ledger["rom"]["name"], ROM_SIZE, ROM_SHA256), "",
             "## Primary classification", "", "| Category | Bytes | % |", "|---|---:|---:|"]
    for c in CATEGORIES:
        lines.append("| %s | %d | %.3f |" % (c, t["by_category"][c], pct(t["by_category"][c])))
    lines.append("| **Total** | **%d** | 100 |" % t["total_bytes"])
    cov = ledger["coverage"]
    rm = ledger["recovered_manifest"]
    lines += ["", "## Coverage", "",
              "| Metric | Bytes | % |", "|---|---:|---:|",
              "| Recovered into reproducible assembly | %d | %.3f |" % (cov["recovered_assembly_bytes"], cov["recovered_assembly_pct"]),
              "| Structurally classified (primary class known) | %d | %.3f |" % (cov["structurally_classified_bytes"], cov["structurally_classified_pct"]),
              "| of which classified only by the recovery manifest | %d | %.3f |" % (t["classified_by_recovery_only_bytes"], pct(t["classified_by_recovery_only_bytes"])),
              "| of which independently evidenced | %d | %.3f |" % (t["independent_structural_bytes"], pct(t["independent_structural_bytes"])),
              "| Recovered and independently evidenced | %d | %.3f |" % (t["recovered_and_independently_classified_bytes"], pct(t["recovered_and_independently_classified_bytes"])),
              "| UNKNOWN | %d | %.3f |" % (cov["unknown_bytes"], cov["unknown_pct"]),
              "| Contested (counted in UNKNOWN) | %d | %.3f |" % (t["contested_bytes"], pct(t["contested_bytes"])),
              "", "Recovered manifest: %d regions, %d bytes (%d code, %d data)." %
              (rm["regions"], rm["bytes"], rm["code_bytes"], rm["data_bytes"]),
              "", "## Per bank", "",
              "| Bank | File range | " + " | ".join(c.title() for c in CATEGORIES[:5]) + " | Padding | Unknown | Recovered | Classified % |",
              "|---:|---|" + "---:|" * 9]
    for b in ledger["banks"]:
        bc = b["by_category"]
        lines.append("| %d | `%05X-%05X` | %s | %d | %d | %d | %.1f |" % (
            b["bank"], b["start"], b["end"] - 1,
            " | ".join(str(bc[c]) for c in CATEGORIES[:5]), bc["PADDING"], bc["UNKNOWN"],
            b["recovered_bytes"], 100.0 * b["classified_bytes"] / BANK_SIZE))
    o = ledger["overlaps"]
    lines += ["", "## Overlaps", "",
              "- compatible nested pairs: %d" % o["stats"]["compatible_nested_pairs"],
              "- compatible partial overlaps: %d" % o["stats"]["compatible_partial_overlap_pairs"],
              "- contradictory pairs: %d" % o["stats"]["contradictory_pairs"]]
    for h in o["contradictory"]:
        lines.append("  - `%05X-%05X` %s vs %s (%s)" % (h["overlap"][0], h["overlap"][1], h["classes"][0],
                                                       h["classes"][1], " / ".join(str(n) for n in h["names"])))
    u = ledger["unclassified_range_claims"]
    status = {}
    for r in u["ranges"]:
        status[r["status"]] = status.get(r["status"], 0) + 1
    rv = ledger["reviewed"]
    lines += ["", "## Hash-verified ranges with no stated kind", "",
              "%d ranges (%d bytes in union, %d still UNKNOWN): %d fully classified, %d partially, %d unresolved." %
              (u["count"], u["union_bytes"], u["union_bytes_still_unknown"], status.get("classified", 0),
               status.get("partial", 0), status.get("unresolved", 0)),
              "", "Reviewed code-flow classifications (`%s`): %d reviews, %d CODE bytes; %d clusters (%d UNKNOWN bytes) unresolved." %
              (rv["source"], rv["reviews"], rv["code_bytes"], rv["unresolved_clusters"], rv["unresolved_unknown_bytes"]),
              "", "Rejected claims: %d. Hashless ranges ignored: %d." %
              (len(ledger["rejected_claims"]), ledger["ignored_hashless_ranges"]),
              "", "## Largest UNKNOWN runs", "", "| File range | Bytes | Bank |", "|---|---:|---:|"]
    runs = []
    for s in ledger["segments"]:
        if s["primary"] != "UNKNOWN":
            continue
        if runs and runs[-1][1] == s["start"] and runs[-1][0] // BANK_SIZE == s["bank"]:
            runs[-1] = (runs[-1][0], s["end"])
        else:
            runs.append((s["start"], s["end"]))
    for lo, hi in sorted(runs, key=lambda r: (-(r[1] - r[0]), r[0]))[:25]:
        lines.append("| `%05X-%05X` | %d | %d |" % (lo, hi - 1, hi - lo, lo // BANK_SIZE))
    return "\n".join(lines) + "\n"


def load_rom(path):
    data = Path(path).read_bytes()
    if len(data) != ROM_SIZE or sha256(data) != ROM_SHA256:
        raise ValueError("Expected Sonic Chaos (Europe) v1.2, %d bytes, SHA-256 %s" % (ROM_SIZE, ROM_SHA256))
    return data


def generate(rom_path, output=DEFAULT_OUTPUT, check=False):
    ledger = build_ledger(load_rom(rom_path))
    files = {"ledger.json": dumps(ledger), "summary.md": summary_markdown(ledger)}
    output = Path(output)
    if check:
        stale = [n for n, text in files.items()
                 if not (output / n).is_file()
                 or (output / n).read_bytes().replace(CRLF, LF) != text.encode("utf-8")]  # CRLF checkouts
        return ledger, stale
    output.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (output / name).write_bytes(text.encode("utf-8"))   # LF newlines on every platform
    return ledger, []


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("rom", nargs="?", default=os.environ.get("SONIC_CHAOS_ROM", str(DEFAULT_ROM)))
    ap.add_argument("--output", default=str(DEFAULT_OUTPUT))
    ap.add_argument("--check", action="store_true", help="fail if the committed ledger is stale")
    args = ap.parse_args(argv)
    ledger, stale = generate(args.rom, args.output, args.check)
    t = ledger["totals"]
    print("ledger: %d bytes accounted, %d classified, %d recovered, %d unknown, %d contested"
          % (t["total_bytes"], t["classified_bytes"], t["recovered_bytes"], t["unknown_bytes"], t["contested_bytes"]))
    for c in CATEGORIES:
        print("  %-10s %7d" % (c, t["by_category"][c]))
    if stale:
        print("STALE: " + ", ".join(stale))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
