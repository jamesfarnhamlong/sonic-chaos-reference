#!/usr/bin/env python3
"""G2-E research: the score owner, the score display and every score award of Sonic Chaos (Europe v1.2).

    python tools/g2e_score.py ROM                    # regenerate data/g2e/*.json (about 4 minutes; the whole-game census dominates)
    python tools/g2e_score.py ROM --check            # recompute everything and compare with the committed JSON
    python tools/g2e_score.py ROM --only static      # decoded layer only (seconds)
    python tools/g2e_score.py ROM --only controlled  # static + original-routine fixtures (no whole-game emulation)
    python tools/g2e_score.py ROM --poc DIR          # additionally (re)read the POC source facts from a SonicChaos_POC checkout (read only)
    python tools/g2e_score.py --validate             # no ROM: internal consistency of the committed JSON

Layers (every field belongs to exactly one; the matrix keeps them apart):

* ``static``     - DECODED DATA / BYTE-VERIFIED ASSEMBLY.  The one score adder ``$262F``, its award table ``$27E2``, the conversion gate ``$5F77``, every call
                   site of the shared defeat conversions (vectors ``$0323`` -> ``$5F3D`` and ``$033E`` -> ``$5F54``), the complete reader/writer census of the three score
                   bytes ``$D29D..$D29F``, the draw census of the score field and the digit/glyph tables.
* ``controlled`` - CONTROLLED ROUTINE RESULT.  The original Z80 routines run on ``tools/oracle.py`` (kosarev z80, not an SMS): ``$262F`` swept across a full
                   1,000,000-raw cycle for both characters against an independent BCD model, the 256-entry type gate, and the original callbacks of every
                   score-awarding object type executed on the real placement records and decoded layouts.
* ``observed``   - EMULATED ORIGINAL FRAME (tools/sms_frame_harness through tools/g0_rig): a natural run through all 18 acts with the attack posture forced
                   (every ``$5F77``/``$262F`` event with type, token, position and award), a revisit test of defeated enemies, and the results card with preset scores.
* ``poc``        - POC SOURCE (read only, commit b4737e8): each existing score writer with file, line and the number it adds.

No ROM byte, tile pixel or palette is committed.  Disassembly text is mnemonic only (the repository already carries such listings in asm/recovered).
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import level_package as L  # noqa: E402
import thz1_animation_reach as A  # noqa: E402
import mghz_object_census as C  # noqa: E402
from oracle import Oracle  # noqa: E402

ROM_SHA256 = "eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607"
BASE_COMMIT = "30655e088421ac10eab456e8fa8a3cb2aae8040b"
POC_COMMIT = "b4737e834982b2985c6fdcb8d4d76cb78c9092c8"
DATA = ROOT / "data" / "g2e"
STATIC_JSON = DATA / "score-static.json"
CONTROLLED_JSON = DATA / "score-controlled.json"
OBSERVED_JSON = DATA / "score-observed.json"
POC_JSON = DATA / "score-poc-source.json"
MATRIX_JSON = DATA / "award-matrix.json"
CONTRACT_JSON = DATA / "g2e-contract.json"
SLOT = 0xD700
ZONE_KEYS = ("thz", "gpz", "sez", "mghz", "aqz", "eez")

# object types whose callbacks contain a call to a shared defeat conversion (found by the static scan; asserted in build_static)
SCORE_TYPES = (0x10, 0x20, 0x21, 0x23, 0x24, 0x25, 0x27, 0x2C, 0x38, 0x3D)


def hx(v, n=4):
    return "0x%0*X" % (n, v)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def dumps(obj):
    return json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=True) + "\n"


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_rom(path):
    data = Path(path).read_bytes()
    if len(data) != 524288 or sha(data) != ROM_SHA256:
        raise SystemExit("Expected the canonical Sonic Chaos (Europe) v1.2 ROM")
    return data


def u16(rom, o):
    return rom[o] | rom[o + 1] << 8


def disasm(rom, bank, start, end):
    """Mnemonic listing [(cpu, text)] of a slot-1/2 region (bank selects the slot-2 bank for CPU >= $8000)."""
    from z80dis import z80
    out, pos = [], start
    while pos < end:
        o = pos if pos < 0x8000 else bank * 0x4000 + pos - 0x8000
        d = z80.decode(rom[o:o + 4], pos)
        out.append([hx(pos), z80.disasm(d)])
        pos += d.len
    return out


# ------------------------------------------------------------------------------------------------------------------------------------------
# STATIC LAYER
def find_ops(rom, operand, ops, lo=0, hi=None):
    """File offsets of `op lo hi` where op is in `ops` and the 16-bit operand equals `operand` (fixed code and every bank: candidates, not proofs)."""
    pat = bytes([operand & 255, operand >> 8])
    out = []
    pos = lo
    hi = hi or len(rom)
    while True:
        i = rom.find(pat, pos, hi)
        if i < 0:
            return out
        if i > 0 and rom[i - 1] in ops:
            out.append(i - 1)
        pos = i + 1


CALL_JP = (0xCD, 0xC3, 0xC2, 0xCA, 0xD2, 0xDA, 0xC4, 0xCC, 0xD4, 0xDC)


def cpu_of(off):
    return off if off < 0x8000 else 0x8000 + off % 0x4000


def bank_of(off):
    return off // 0x4000


def add_routine(rom):
    """Byte-verified facts of $262F (score add + continue threshold) from the ROM bytes themselves."""
    b = rom[0x262F:0x26D6]
    facts = {}
    # explicit, human-checkable byte strings
    checks = {
        "gate_d292_nonzero_returns": (0x262F, "3a92d2b7c0"),
        "save_previous_score": (0x2634, "ed5b9dd2ed53a0d23a9fd232a2d2"),
        "bcd_add_three_bytes_adc_daa": (0x2642, "af119dd21a8e27121323" "1a8e27121323" "1a8e2712"),
        "carry_out_branch": (0x2656, "300f"),
        "carry_out_writes_dead_cap": (0x2658, "21a3d2" "3690" "23" "3699" "23" "3699" "3e02" "1802"),
        "no_carry_flag_one": (0x2667, "3e01"),
        "store_flag_d2bb": (0x2669, "32bbd2"),
        "thousands_changed_test": (0x266F, "3a9ed2e6f047" "3aa1d2e6f0b8c8"),
        "character_test_sonic": (0x267C, "3ac8d23dc29126"),
        "sonic_award_digit_0_or_5": (0x2683, "3a9ed2e6f0cabd26" "fe50cabd26c9"),
        "continue_increment_bit7_kept": (0x26BD, "3ac3d2473ce67f4f78e6" "80b132c3d2c9"),
        "mod3_helper": (0x26CD, "b7c80603" "90" "30fd" "80c9"),
    }
    for name, (addr, hexs) in checks.items():
        exp_b = bytes.fromhex(hexs)
        assert rom[addr:addr + len(exp_b)] == exp_b, (name, hx(addr))
        facts[name] = {"cpu": hx(addr), "bytes_sha256_prefix": sha(exp_b)[:12], "length": len(exp_b)}
    listing = disasm(rom, 1, 0x262F, 0x26D6)
    return {
        "range_cpu": [hx(0x262F), hx(0x26D6)], "sha256": sha(b), "byte_checks": facts, "listing": listing,
        "semantics": {
            "input": "HL = pointer to a three-byte packed-BCD amount (little endian); the routine adds it to D29D..D29F",
            "gate": "D292 != 0 (title, menu, attract flow bits) returns before anything is changed",
            "wrap": "ADC/DAA on three bytes: the sum is taken modulo 1,000,000 raw. Carry out of the top byte does NOT saturate; it only writes D2A3..D2A5 := 90 99 99 and D2BB := 2 (both never read anywhere in the ROM, see readers)",
            "threshold": "after the add, if the thousands digit (high nibble of D29E) differs from the saved previous score: Sonic (D2C8 == 1) awards a continue when the new digit is 0 or 5; any other character awards when "
                         "(thousands + ten-thousands + hundred-thousands digit) mod 3 == 0; the award is a binary +1 of D2C3 with bit 7 kept",
        },
    }


def award_table(rom):
    base = 0x27E2
    entries = []
    for i in range(4):
        raw = rom[base + 3 * i:base + 3 * i + 3]
        digits = "%02X%02X%02X" % (raw[2], raw[1], raw[0])
        entries.append({"cpu": hx(base + 3 * i), "bcd_bytes_le": raw.hex(), "raw_units": int(digits), "displayed_points": int(digits) * 10})
    assert [e["raw_units"] for e in entries] == [1, 10, 50, 10]
    users = {}
    for e in entries:
        a = int(e["cpu"], 16)
        users[e["cpu"]] = [hx(o) for o in find_ops(rom, a, (0x21,), 0, 0x8000)]
    return {"base": hx(base), "entries": entries, "referenced_by_ld_hl_in_fixed_code": users,
            "roles": {"0x27E2": "results word loop step (+1 raw = 10 displayed)", "0x27E5": "results ring loop step (+10 raw = 100 displayed)",
                      "0x27E8": "NEVER REFERENCED (+50 raw = 500 displayed is dead data)", "0x27EB": "act-3 boss bonus loop step AND the enemy/monitor conversion award (+10 raw = 100 displayed)"}}


def writer_census(rom):
    """Every operand reference to D29D/D29E/D29F and to the score adder entry points in the 512 KiB ROM."""
    def refs(addr, ops):
        pat = bytes([addr & 255, addr >> 8])
        out = []
        pos = 0
        while True:
            i = rom.find(pat, pos)
            if i < 0:
                return out
            if i > 0 and rom[i - 1] in ops:
                out.append(hx(i - 1, 5))
            pos = i + 1
    mem_ops = (0x32, 0x3A, 0x21, 0x11, 0x01, 0x22, 0x2A)
    census = {n: refs(a, mem_ops) for n, a in (("D29D", 0xD29D), ("D29E", 0xD29E), ("D29F", 0xD29F))}
    # the ED-prefixed 16-bit forms LD DE,(nn) / LD (nn),DE carry the operand after ED 5B / ED 53
    for n, a in (("D29D", 0xD29D),):
        pat = bytes([a & 255, a >> 8])
        for i in range(len(rom) - 2):
            if rom[i:i + 2] == pat and i >= 2 and rom[i - 2] == 0xED and rom[i - 1] in (0x5B, 0x53, 0x4B, 0x43, 0x7B, 0x73):
                census[n].append(hx(i - 2, 5))
    expected = {
        "D29D": {"0x013D8": "new game: clear", "0x02643": "$262F: BCD add destination pointer", "0x026FE": "$26F8: draw source pointer", "0x02708": "$26F8: draw source pointer",
                 "0x02A04": "continue accepted: clear", "0x02634": "$262F: save previous (LD DE,(D29D))"},
        "D29E": {"0x013DB": "new game: clear", "0x0266F": "$262F: threshold digit test (new)", "0x02683": "$262F: Sonic test", "0x02691": "$262F: other-character digit sum", "0x02A07": "continue accepted: clear"},
        "D29F": {"0x013DE": "new game: clear", "0x0263C": "$262F: save previous", "0x0269E": "$262F: other-character digit sum", "0x026A7": "$262F: other-character digit sum", "0x02A0A": "continue accepted: clear"},
    }
    got = {k: sorted(set(v)) for k, v in census.items()}
    want = {k: sorted(v) for k, v in expected.items()}
    assert got == want, (got, want)
    callers = {
        "262F": [hx(o, 5) for o in find_ops(rom, 0x262F, CALL_JP)],
        "2EFB_word_step": [hx(o, 5) for o in find_ops(rom, 0x2EFB, CALL_JP)],
        "2F00_ring_step": [hx(o, 5) for o in find_ops(rom, 0x2F00, CALL_JP) if o < 0x8000],
        "2F05_boss_step": [hx(o, 5) for o in find_ops(rom, 0x2F05, CALL_JP)],
        "26F8_draw_score": [hx(o, 5) for o in find_ops(rom, 0x26F8, CALL_JP)],
        "26D6_draw_rings": [hx(o, 5) for o in find_ops(rom, 0x26D6, CALL_JP)],
        "26E7_draw_word": [hx(o, 5) for o in find_ops(rom, 0x26E7, CALL_JP)],
    }
    assert callers["262F"] == ["0x02F0C", "0x05F81"], callers["262F"]
    assert callers["26F8_draw_score"] == ["0x02D1F", "0x02D4B", "0x02D6E", "0x033A8"], callers["26F8_draw_score"]
    return {"references": expected, "references_found_offsets": got, "callers": callers, "dead_state": {
        "D2A3..D2A5": "written once per overflow ($2658) and never read by any instruction operand; the 7-byte copy at $2728 only reads them as padding",
        "D2BB": "written at $2667/$2669 (1 normal, 2 overflow) and never read"},
        "dead_state_reader_scan": {n: [hx(o, 5) for o in find_ops(rom, a, (0x32, 0x3A, 0x21, 0x11, 0x01, 0x22, 0x2A))] for n, a in
                                    (("D2A3", 0xD2A3), ("D2A4", 0xD2A4), ("D2A5", 0xD2A5), ("D2BB", 0xD2BB))}}


def gate_routine(rom):
    b = rom[0x5F3D:0x5F84]
    assert rom[0x5F77:0x5F77 + 13].hex() == "dd7e00" "fe50" "d0" "c8" "21eb27" "c32f26"
    assert rom[0x5F3D:0x5F57].hex() == ("dd7e21e60fc8" "3a32d5fe062806" "3a03d5cb4fc8" "dd363f80" "cd775f"), rom[0x5F3D:0x5F57].hex()
    vec = {}
    for v, t in ((0x0323, 0x5F3D), (0x033E, 0x5F54), (0x034D, 0x5FA0)):
        assert rom[v] == 0xC3 and u16(rom, v + 1) == t, hx(v)
        vec[hx(v)] = hx(t)
    return {"range_cpu": [hx(0x5F3D), hx(0x5F84)], "sha256": sha(b), "listing": disasm(rom, 1, 0x5F3D, 0x5F84), "vectors": vec,
            "semantics": {
                "$5F3D (vector $0323)": "needs (IX+$21 & $0F) != 0 (contact bits from $6328) AND (D532 == 6 OR D503 bit 1); then falls into the conversion. Anything else returns with no score and no state change",
                "$5F54 (vector $033E)": "the conversion itself: calls the gate $5F77, then turns the slot into type $0F, zeroes state/request/script fields/flags and clears the placement token (+$3E) and parameter (+$3F). No condition",
                "$5F77 gate": "CP $50 / RET NC: any type >= $50 returns with no score (the following RET Z is dead code). Every type 0..$4F adds the single flat amount at $27EB (+10 raw = 100 displayed) through $262F by JP. There is no per-type score table",
                "$5FA0 (vector $034D)": "NOT a score path: overlap helper $6328 followed by the surface/solid-contact dispatch at $5FB9 (nine entries: RET, push-back handlers)"}}


def scan_sites(rom):
    """Every call site of the three shared vectors, with the nearest callback entry (a heuristic, validated by the controlled fixtures)."""
    stub = {}
    for o in range(0x320, 0x450, 3):
        if rom[o] == 0xC3:
            stub[o] = u16(rom, o + 1)
    entries = {12: [], 30: []}
    state_count = {}
    for t in range(2, 0x64):
        try:
            st = A.animation_state_table(rom, t)
        except Exception:
            continue
        state_count[t] = st["state_count"]
        b = st["bank"]
        for si, sc in enumerate(st["state_script_cpus"]):
            try:
                p = A.parse_state_script(rom, b, sc, si)
            except Exception:
                continue
            for r in p["records"]:
                cb = int(r["callback_cpu"], 16)
                if cb < 0x4000:
                    cb = stub.get(cb, cb)
                if 0x8000 <= cb < 0xC000:
                    entries[b].append((cb, t, si))
    for b in entries:
        entries[b] = sorted(set(entries[b]))
    rows = []
    for vec, label in ((0x0323, "5F3D_attack_gated"), (0x033E, "5F54_conversion"), (0x034D, "5FA0_solid_contact_not_score")):
        for off in find_ops(rom, vec, CALL_JP):
            if off < 0x8000:
                continue
            b, cpu = bank_of(off), cpu_of(off)
            es = entries.get(b)
            if es is None:
                continue
            keys = [e[0] for e in es]
            import bisect
            i = bisect.bisect_right(keys, cpu) - 1
            if i < 0:
                rows.append({"site_file": hx(off, 5), "bank": hx(b, 2), "site_cpu": hx(cpu), "vector": hx(vec), "kind": label, "entry": None, "types": []})
                continue
            ent = es[i][0]
            same = sorted({(t, s) for (c, t, s) in es if c == ent})
            types = collections.OrderedDict()
            for t, s in same:
                types.setdefault(hx(t, 2), []).append(s)
            rows.append({"site_file": hx(off, 5), "bank": hx(b, 2), "site_cpu": hx(cpu), "vector": hx(vec), "kind": label, "nearest_entry_cpu": hx(ent), "types_states": types,
                         "awards_after_gate": any(t < 0x50 and t != 0 for t, _ in same)})
    return rows


def placement_census(rom):
    cen = collections.defaultdict(lambda: collections.defaultdict(int))
    keys = {}
    for z in list(range(0, 7)) + list(range(8, 13)):
        for a in range(3):
            recs, _ = L.decode_object_list(rom, L.object_list_pointer(rom, z, a)["list_rom"])
            for r in recs:
                t = int(r["type_id"], 16)
                cen[t]["%d.%d" % (z, a)] += 1
                if t in SCORE_TYPES:
                    keys.setdefault((t, r["flags"], r["parameter"], r["aux0"], r["aux1"]), []).append((z, a, r["raw_bytes"]))
    sel = {hx(t, 2): dict(sorted(v.items())) for t, v in sorted(cen.items()) if t in SCORE_TYPES or t >= 0x50}
    variants = [{"type": hx(k[0], 2), "flags": k[1], "parameter": k[2], "aux0": k[3], "aux1": k[4], "placements": len(v), "first": "%d.%d" % (v[0][0], v[0][1])} for k, v in sorted(keys.items())]
    return {"zones_note": "zones 0..5 = THZ GPZ SEZ MGHZ AQZ EEZ; zone 6 repeats the THZ lists; zones 8..12 are the Special Stages (monitors only)", "counts": sel, "variants": variants}, keys


def spawn_graph(rom):
    spawned = collections.defaultdict(set)
    for t in range(2, 0x64):
        try:
            sc = C.state_scripts(rom, t)
        except Exception:
            continue
        for s in sc["spawns"]:
            spawned[s["type"]].add(t)
    return {hx(k, 2): sorted(hx(x, 2) for x in v) for k, v in sorted(spawned.items())}


def hud_facts(rom):
    import u4_results as U
    st = U.__dict__
    base = 0xA516
    tab = U._bank_bytes(rom, U.BANK_RESULTS, base, 24)
    digits = [[tab[2 * d], tab[2 * d + 1]] for d in range(10)]
    # the fixed block at $3BA6: LD DE,$A516; LD BC,$0201 (columns 1, rows 2) -> bytes A516,A517 == the glyph of digit 0
    assert rom[0x2717:0x2717 + 3].hex() == "1116a5" and rom[0x271A:0x271A + 6].hex() == "21a63b010102", rom[0x2717:0x2720].hex()
    assert rom[0x2721:0x2724].hex() == "cd8323"
    d0 = digits[0]
    block_tiles = [tab[0], tab[1]]
    assert block_tiles == d0
    plan = load_json(ROOT / "data" / "u4" / "ordinary-results-static.json")["draw_plan"]
    sc = next(f for f in plan["number_fields"] if f["id"] == "score")
    return {
        "digit_glyph_table": {"source": "bank $13 slot 2, CPU $A516", "pairs_top_bottom_tile_ids": digits, "blank_pair": [tab[20], tab[21]]},
        "fixed_block": {"name_table_address": "0x3BA6", "column": 19, "row": 14, "size_cols_rows": [1, 2], "source_cpu": "0xA516", "tile_ids": block_tiles, "equals_digit_0_glyph": True,
                        "meaning": "a literal '0' glyph: the displayed score is the raw BCD score x 10 (u4 doc section 7: 'ring = 100, bonus step = 10')"},
        "digit_field": {"name_table_address": hx(int(sc["name_table_address"], 16)), "col": sc["col"], "row": sc["row"], "digits": sc["digits"], "leading_zero_blank": sc["leading_zero_blank"],
                        "rule": "the six raw digits are drawn most significant first as 8x16 glyphs (two stacked tiles); the first five zero digits are replaced by the blank glyph, the last raw digit is always drawn; "
                                "if D29D|D29E|D29F == 0 the digit loop is skipped entirely and the previous contents of the field stay on screen"},
        "max_displayed": 9999990, "draw_sites": ["$2D1F (ring step)", "$2D4B (word step)", "$2D6E (boss step)", "$33A8 (card draw)"],
        "gameplay_hud": "none: D29D..D29F are read only by $262F and $26F8; $26F8 is called only from the results card and its three tally loops",
        "invalid_bcd": "$27AD returns carry on any nibble > 9 and the field is not drawn (cannot happen through $262F)",
    }


def build_static(rom):
    sites = scan_sites(rom)
    awarding_types = sorted({t for s in sites if s["kind"] != "5FA0_solid_contact_not_score" for t in s.get("types_states", {}) if int(t, 16) < 0x50})
    placements, keys = placement_census(rom)
    spawners = spawn_graph(rom)
    placed = {int(t, 16) for t in placements["counts"]}
    spawned = {int(t, 16) for t in spawners}
    reachable = sorted(hx(int(t, 16), 2) for t in awarding_types if int(t, 16) in placed or int(t, 16) in spawned)
    unreachable = sorted(set(awarding_types) - set(reachable))
    return {
        "format": 1, "rom_sha256": ROM_SHA256, "research_base": BASE_COMMIT,
        "evidence": "DECODED DATA / BYTE-VERIFIED ASSEMBLY (byte checks asserted at generation time)",
        "add_routine": add_routine(rom), "award_table": award_table(rom), "writer_census": writer_census(rom), "conversion_gate": gate_routine(rom),
        "conversion_sites": sites, "types_reaching_a_conversion_below_0x50": awarding_types,
        "of_which_placed_or_script_spawned": reachable, "state_table_aliases_never_placed_or_script_spawned": unreachable,
        "placements": placements, "script_spawners_of_score_types": {k: v for k, v in spawners.items() if int(k, 16) in SCORE_TYPES},
        "hud": hud_facts(rom),
    }, keys


# ------------------------------------------------------------------------------------------------------------------------------------------
# CONTROLLED LAYER (tools/oracle.py: original Z80 routines, no SMS hardware)
def bcd_bytes(raw):
    d = "%06d" % raw
    return [int(d[4:6], 16), int(d[2:4], 16), int(d[0:2], 16)]


def from_bcd(b):
    return int("%02X%02X%02X" % (b[2], b[1], b[0]))


def model_add(raw_before, add_raw, character, continues):
    """Independent model of $262F (not derived from the emulation): modulo-1,000,000 add and the thousands-digit continue rule."""
    after = (raw_before + add_raw) % 1000000
    th_before, th_after = raw_before // 1000 % 10, after // 1000 % 10
    awarded = False
    if th_before != th_after:
        if character == 1:
            awarded = th_after in (0, 5)
        else:
            awarded = (after // 1000) % 3 == 0
    c = continues
    if awarded:
        c = (c & 0x80) | ((c + 1) & 0x7F)
    return after, c


def oracle_add(o, raw, table, character, continues=0, d292=0):
    m = o.mem
    b = bcd_bytes(raw)
    m[0xD292] = d292
    m[0xD2C8] = character
    m[0xD29D], m[0xD29E], m[0xD29F] = b
    m[0xD2A0:0xD2A6] = bytes([0xEE] * 6)
    m[0xD2BB] = 0xEE
    m[0xD2C3] = continues
    o.cpu.hl = table
    o.call(0x262F)
    return from_bcd([m[0xD29D], m[0xD29E], m[0xD29F]]), m[0xD2C3], bytes(m[0xD2A3:0xD2A6]).hex(), m[0xD2BB]


def controlled_add(rom):
    o = Oracle(rom)
    mism = []
    awards = {1: [], 2: []}
    for ch in (1, 2):
        for k in range(1000):                       # one complete cycle: +10 raw taken from x,990 into the next thousand
            raw = k * 1000 + 990
            got, cont, cap, flag = oracle_add(o, raw, 0x27E5, ch, 0)
            exp, econt = model_add(raw, 10, ch, 0)
            if (got, cont) != (exp, econt):
                mism.append((ch, raw, got, cont, exp, econt))
            if cont:
                awards[ch].append((k + 1) % 1000)
            if k == 999:
                wrap_row = {"character": ch, "before": raw, "after": got, "continues_after": cont, "dead_cap_d2a3": cap, "dead_flag_d2bb": flag}
                if ch == 1:
                    wrap_sonic = wrap_row
                else:
                    wrap_tails = wrap_row
    # corners and the gate
    corners = []
    for raw, table, ch, d292 in ((999990, 0x27E5, 1, 0), (999995, 0x27E5, 1, 0), (999999, 0x27E2, 1, 0), (999960, 0x27E8, 1, 0), (999980, 0x27E5, 1, 0), (0, 0x27E5, 1, 0), (5, 0x27E5, 1, 0),
                                 (4990, 0x27E5, 1, 0), (4990, 0x27E5, 2, 0), (2990, 0x27E5, 1, 0), (2990, 0x27E5, 2, 0), (999990, 0x27E5, 2, 0), (998990, 0x27E5, 2, 0), (999990, 0x27E5, 1, 0x10), (999990, 0x27E5, 1, 0x20)):
        got, cont, cap, flag = oracle_add(o, raw, table, ch, 0, d292)
        corners.append({"before": raw, "table": hx(table), "character": ch, "d292": d292, "after": got, "continues_after": cont, "d2a3_d2a5": cap, "d2bb": flag})
    # bit 7 of the continue byte is preserved, the count is a 7-bit binary wrap
    bit7 = []
    for c in (0x00, 0x7F, 0x80, 0xFF, 0x05):
        got, cont, _, _ = oracle_add(o, 4990, 0x27E5, 1, c)
        bit7.append({"continues_before": c, "after": cont})
    assert not mism, mism[:3]
    assert awards[1] == list(range(5, 1000, 5)) + [0] and awards[2] == list(range(3, 1000, 3)) + [0], (awards[1][:3], awards[2][:3])
    return {
        "evidence": "CONTROLLED ROUTINE RESULT (original $262F on tools/oracle.py) + independent Python model with zero mismatches",
        "cycle_sweep": {"fixture": "score = k*1000+990 raw, HL=$27E5 (+10 raw), k = 0..999, D2C3 = 0, D292 = 0", "model_mismatches": len(mism),
                        "sonic_awards": len(awards[1]), "tails_awards": len(awards[2]),
                        "sonic_new_thousand_values": awards[1][:6], "tails_new_thousand_values": awards[2][:6],
                        "tails_last_three_new_thousand_values": awards[2][-3:], "sonic_period_raw": 5000, "tails_period_raw": 3000,
                        "tails_wrap_award_is_1000_raw_after_the_999000_award": awards[2][-2:] == [999, 0]},
        "wrap": {"sonic": wrap_sonic, "tails": wrap_tails}, "corners": corners, "continue_byte_bit7": bit7,
    }


def controlled_gate(rom):
    o = Oracle(rom)
    m = o.mem
    awarded = []
    for t in range(256):
        m[0xD292] = 0
        m[0xD2C8] = 1
        m[0xD29D:0xD2A0] = bytes(3)
        m[0xD2C3] = 0
        m[SLOT:SLOT + 0x40] = bytes(0x40)
        m[SLOT] = t
        o.cpu.ix = SLOT
        o.call(0x5F77)
        if m[0xD29D:0xD2A0] != bytes(3):
            awarded.append((t, bytes(m[0xD29D:0xD2A0]).hex()))
    assert [t for t, _ in awarded] == list(range(0, 0x50)), [t for t, _ in awarded][:5]
    assert {v for _, v in awarded} == {"100000"}
    return {"evidence": "CONTROLLED ROUTINE RESULT ($5F77 called for every type byte 0..255 with D292=0)", "awarding_types": "0x00..0x4F (80 type bytes; the RET Z after CP $50 is dead because every A >= $50 already returned on NC)", "amount_bcd_le": "100000", "amount_raw": 10,
            "non_awarding_types": "0x50..0xFF"}


# ---- object fixtures ------------------------------------------------------------------------------------------------------------------------
class ObjLab:
    """Original placement creator $80EB on the act's own decoded layout, then the animation engine $64FA + callback per update (as thz1/mghz labs do)."""

    def __init__(self, rom, zone, act, raw):
        self.rom = rom
        h = L.act_header(rom, zone, act)
        cells, _, _ = L.decode_layout_stream(rom, h["layout_rom"])
        o = Oracle(rom)
        m = o.mem
        m[0xC001:0xD000] = bytes((cells + [0] * 4095)[:4095])
        o.word(0xD168, h["row_offset_table_cpu"])
        o.word(0xD16A, -h["width_cells"])
        o.bank(2, 0x1C)
        m[0xDA00:0xDA09] = bytes.fromhex(raw.replace(" ", ""))
        m[SLOT:SLOT + 0x40] = bytes(0x40)
        o.cpu.ix = SLOT
        o.cpu.iy = SLOT
        o.cpu.hl = 0xDA00
        o.call(0x80EB, bc=0xD418)
        self.o, self.m = o, m
        self.ox, self.oy = o.word(SLOT + 0x11), o.word(SLOT + 0x14)
        o.word(0xD174, max(self.ox - 100, 0))
        o.word(0xD176, max(self.oy - 100, 0))
        m[0xD500] = 1
        m[0xD52C], m[0xD52D] = 8, 24
        self.type = m[SLOT]
        self.bank = A.animation_bank(self.type)
        m[0xD292] = 0
        m[0xD2C8] = 1
        m[0xD29D:0xD2A0] = bytes(3)
        m[0xD2C3] = 0

    def step(self):
        o, m = self.o, self.m
        m[SLOT + 4] &= 0xBF          # the lifetime scheduler (not run here) is what clears the created-asleep bit
        o.bank(2, self.bank)
        m[0xD12B] = self.bank
        o.cpu.ix = SLOT
        o.call(0x64FA)
        cb = m[SLOT + 0xC] | m[SLOT + 0xD] << 8
        if cb:
            o.bank(2, self.bank)
            m[0xD12B] = self.bank
            o.cpu.ix = SLOT
            o.call(cb)
        m[0xD12F] = (m[0xD12F] + 1) & 255

    def settle(self, limit=120):
        n = 0
        while self.m[SLOT + 1] == 0 and n < limit:
            self.step()
            n += 1
        for _ in range(2):
            self.step()
        return n

    def player(self, dx, dy, flags, d532, vy, state=5):
        o, m = self.o, self.m
        o.position(o.word(SLOT + 0x11) + dx, o.word(SLOT + 0x14) + dy)
        m[0xD503] = flags
        m[0xD532] = d532
        m[0xD501] = state
        m[0xD502] = state
        o.word(0xD518, vy & 0xFFFF)
        m[0xD3B0] = 0

    def score(self):
        return bytes(self.m[0xD29D:0xD2A0]).hex()


POSTURES = (("attack", 2, 0), ("invincible", 0, 6), ("airborne_only", 1, 0), ("none", 0, 0))


def contact_matrix(rom, keys):
    """The $5F3D family and $21: centre contact in each posture on every distinct placement record, plus a second update after a defeat (no second award)."""
    rows = []
    for k, v in sorted(keys.items()):
        t = k[0]
        if t in (0x10, 0x24, 0x38):
            continue
        z, a, raw = v[0]
        row = {"type": hx(t, 2), "flags": k[1], "parameter": k[2], "aux0": k[3], "aux1": k[4], "act": "%d.%d" % (z, a), "postures": {}}
        for name, fl, d5 in POSTURES:
            lab = ObjLab(rom, z, a, raw)
            row["settle_updates"] = lab.settle()
            res = []
            for _ in range(3):
                lab.player(0, 0, fl, d5, 0)
                lab.step()
                res.append((lab.m[SLOT], lab.score(), lab.m[0xD3B0]))
            row["postures"][name] = {"award_bcd_le": res[0][1], "type_after_first": hx(res[0][0], 2), "damage_request_d3b0": hx(res[0][2], 2), "score_after_third_update": res[-1][1]}
        rows.append(row)
    return rows


def state_matrix(rom, keys):
    """For each type: forced requested state, one update in contact with the attack posture, which states convert and score."""
    out = {}
    seen = set()
    for k, v in sorted(keys.items()):
        t = k[0]
        if t in (0x10, 0x24, 0x38) or t in seen:
            continue
        seen.add(t)
        z, a, raw = v[0]
        n = A.animation_state_table(rom, t)["state_count"]
        res = {}
        for s in range(1, n):
            lab = ObjLab(rom, z, a, raw)
            lab.settle()
            lab.m[SLOT + 2] = s
            lab.player(0, 0, 2, 0, 0)
            try:
                lab.step()
            except RuntimeError:
                res[str(s)] = "not_exercised"
                continue
            res[str(s)] = "award_and_convert" if lab.score() == "100000" and lab.m[SLOT] == 0x0F else ("no_award" if lab.score() == "000000" else "award:" + lab.score())
        out[hx(t, 2)] = res
    return out


def monitor_grid(rom, keys):
    out = {}
    params = sorted({k[2] for k in keys if k[0] == 0x10 and any(x[0] < 6 for x in keys[k])})
    for p in params:
        k = next(k for k in keys if k[0] == 0x10 and k[2] == p and keys[k][0][0] < 6)
        z, a, raw = keys[k][0]
        cells = collections.defaultdict(list)
        for name, fl, d5 in (("attack", 2, 0), ("invincible", 0, 6), ("none", 0, 0)):
            for dx in (-16, 0, 16):
                for dy in (-28, -20, -8, 0, 8, 20, 28):
                    for vy in (0x300, 0x100, 0, -0x100):
                        lab = ObjLab(rom, z, a, raw)
                        lab.settle()
                        lab.m[0xD3A3] = 0
                        got = []
                        for _ in range(2):
                            lab.player(dx, dy, fl, d5, vy)
                            lab.step()
                            got.append(lab.score())
                        if got[0] != "000000" or got[1] != "000000":
                            cells[name].append([dx, dy, vy, got[0], got[1], hx(lab.m[SLOT], 2)])
        out[p] = {"act": "%d.%d" % (z, a), "cells_tested_per_posture": 84,
                  "awarding_cells": {n: len(c) for n, c in cells.items()}, "attack_cells": sorted(cells.get("attack", [])),
                  "second_update_never_adds": all(c[4] == c[3] for c in cells.get("attack", []))}
    return out


def type21_grid(rom, keys):
    k = next(k for k in sorted(keys) if k[0] == 0x21 and k[1] == "0x00" and k[2] == "0x02")
    z, a, raw = keys[k][0]
    cells = []
    for name, fl, d5 in (("attack", 2, 0), ("invincible", 0, 6), ("none", 0, 0)):
        for dx in (-16, 0, 16):
            for dy in (-30, -20, -8, 0, 8, 20, 30):
                lab = ObjLab(rom, z, a, raw)
                lab.settle()
                lab.player(dx, dy, fl, d5, 0x100)
                lab.step()
                cells.append([name, dx, dy, lab.score(), hx(lab.m[SLOT], 2), hx(lab.m[0xD3B0], 2), hex(lab.o.word(0xD518))])
    top = [c for c in cells if c[0] == "attack" and c[2] <= -20]
    low = [c for c in cells if c[0] == "attack" and -8 <= c[2] <= 8 and c[1] == 0]
    return {"act": "%d.%d" % (z, a), "cells": cells,
            "summary": {"attack_cells_with_award": sum(1 for c in cells if c[0] == "attack" and c[3] == "100000"), "attack_cells": sum(1 for c in cells if c[0] == "attack"),
                        "no_posture_cells_with_award": sum(1 for c in cells if c[0] == "none" and c[3] == "100000"),
                        "top_contact_cells_attack": [c[1:5] for c in top], "side_contact_attack_centre": [c[1:5] for c in low]}}


def autonomous_types(rom, keys):
    """$24 (falls and lands) and $38 (proximity self-destruct) convert without any player attack: player parked at a fixed offset, no attack."""
    out = []
    for t, trials in ((0x24, ((40, 0), (-40, 0))), (0x38, ((20, 10), (0, 0)))):
        for k in sorted(kk for kk in keys if kk[0] == t):
            z, a, raw = keys[k][0]
            for dx, dy in trials:
                for name, fl, d5 in (("no_attack", 0, 0), ("attack", 2, 0)):
                    lab = ObjLab(rom, z, a, raw)
                    first = None
                    px = py = None
                    for i in range(500):
                        if i == 0:
                            lab.player(dx, dy, fl, d5, 0, state=1)
                            px, py = lab.o.word(0xD511), lab.o.word(0xD514)
                        else:
                            lab.o.position(px, py)
                            lab.m[0xD503], lab.m[0xD532], lab.m[0xD501], lab.m[0xD502] = fl, d5, 1, 1
                            lab.m[0xD3B0] = 0
                        lab.step()
                        if first is None and lab.score() != "000000":
                            first = {"update": i, "score": lab.score(), "type_after": hx(lab.m[SLOT], 2), "damage_request_same_update": hx(lab.m[0xD3B0], 2)}
                    out.append({"type": hx(t, 2), "parameter": k[2], "act": "%d.%d" % (z, a), "player_offset": [dx, dy], "posture": name, "first_award": first, "final_score": lab.score()})
    # far player: nothing
    far = []
    for t in (0x24, 0x38):
        k = next(kk for kk in sorted(keys) if kk[0] == t)
        z, a, raw = keys[k][0]
        lab = ObjLab(rom, z, a, raw)
        lab.o.position(lab.ox + 3000 if lab.ox < 3000 else lab.ox - 3000, 0)
        for _ in range(900):
            lab.step()
        far.append({"type": hx(t, 2), "updates": 900, "score": lab.score(), "type_after": hx(lab.m[SLOT], 2)})
    return {"trials": out, "player_far_away": far}


def build_controlled(rom, keys):
    return {
        "format": 1, "rom_sha256": ROM_SHA256, "research_base": BASE_COMMIT,
        "evidence": "CONTROLLED ROUTINE RESULT (tools/oracle.py: original $262F/$5F77 and original object callbacks with the real placement records and decoded layouts)",
        "score_adder": controlled_add(rom), "type_gate": controlled_gate(rom), "contact_matrix": contact_matrix(rom, keys), "state_matrix": state_matrix(rom, keys),
        "monitor_grid": monitor_grid(rom, keys), "type_21_grid": type21_grid(rom, keys), "autonomous_conversions": autonomous_types(rom, keys),
        "fixture_notes": ["the lifetime scheduler is not run: the created-asleep bit (+4 bit 6) is cleared before each update", "the player is a synthetic overlap (position, D503, D532, Y velocity are written before each update)",
                          "monitors in the Special Stages run the same global object code; they were not separately executed"],
    }


# ------------------------------------------------------------------------------------------------------------------------------------------
# OBSERVED LAYER (whole game on the approximate SMS harness)
def whole_game_census(rom):
    import g0_rig
    out = []
    for zone in range(6):
        for act in range(3):
            S = g0_rig.Session(rom)
            m = S.m
            ev = []

            def gate(mm, ev=ev):
                ix = mm.cpu.ix
                ev.append(["gate", mm.frame, mm.mem[ix], mm.mem[ix + 0x3E], mm.mem[ix + 0x11] | mm.mem[ix + 0x12] << 8, mm.mem[ix + 0x14] | mm.mem[ix + 0x15] << 8,
                           mm.mem[mm.cpu.sp] | mm.mem[mm.cpu.sp + 1] << 8, mm.mem[0xD299]])
            S.hook(0x5F77, gate)
            S.hook(0x262F, lambda mm, ev=ev: ev.append(["add", mm.frame, mm.cpu.hl, mm.mem[0xD29D:0xD2A0].hex()]))
            S.hook(0x26F8, lambda mm, ev=ev: ev.append(["draw", mm.frame, mm.mem[0xD293]]))
            if (zone, act) != (0, 0):
                S.set_start_index(zone, act)
            S.boot_new_game(character=0)
            S.hook(0x64FA, lambda mm: mm.mem.__setitem__(0xD503, mm.mem[0xD503] | 2) if mm.cpu.ix == 0xD500 else None)
            S.run_until(lambda s: s.playing(), limit=3000)
            start = S.s.frame
            for _ in range(3500):
                S.run(1, pad=g0_rig.BTN_RIGHT)
                if m[0xD293] & 0x30:
                    break
            gates = [e for e in ev if e[0] == "gate"]
            adds = [e for e in ev if e[0] == "add" and e[2] not in (0x27E5, 0x27E2)]
            draws = [e for e in ev if e[0] == "draw" and e[1] >= start]
            out.append({"act": "%d.%d" % (zone, act), "frames_from_play": S.s.frame - start,
                        "score_field_draws_while_playing": sum(1 for e in draws if not e[2] & 0x30), "score_field_draws_total": len(draws),
                        "gate_events": [{"frame": e[1] - start, "type": hx(e[2], 2), "token": e[3], "x": e[4], "y": e[5], "lives": e[7]} for e in gates],
                        "lives_at_end": m[0xD299],
                        "award_events": [{"frame": e[1] - start, "table": hx(e[2]), "score_before_bcd_le": e[3]} for e in adds],
                        "final_score_bcd_le": bytes(m[0xD29D:0xD2A0]).hex()})
    return out


def revisit_test(rom):
    import g0_rig
    res = []
    for zone, act in ((0, 0), (1, 0)):
        S = g0_rig.Session(rom)
        m = S.m
        ev = []
        S.hook(0x5F77, lambda mm, ev=ev: ev.append((mm.frame, mm.mem[mm.cpu.ix], mm.mem[mm.cpu.ix + 0x3E], mm.mem[mm.cpu.ix + 0x11] | mm.mem[mm.cpu.ix + 0x12] << 8)))
        if (zone, act) != (0, 0):
            S.set_start_index(zone, act)
        S.boot_new_game(character=0)
        S.hook(0x64FA, lambda mm: mm.mem.__setitem__(0xD503, mm.mem[0xD503] | 2) if mm.cpu.ix == 0xD500 else None)
        S.run_until(lambda s: s.playing(), limit=3000)
        S.run_until(lambda s: len(ev) > 0, pad=g0_rig.BTN_RIGHT, limit=3000)
        first = ev[0]
        passes = []
        for p in range(3):
            S.run(5, pad=0)
            S.s.w16(0xD511, max(first[3] - 600, 64))
            S.s.w16(0xD2D6, max(first[3] - 700, 0))
            n0 = len(ev)
            for _ in range(450):
                S.run(1, pad=g0_rig.BTN_RIGHT)
                if (m[0xD511] | m[0xD512] << 8) > first[3] + 200:
                    break
            passes.append({"pass": p + 1, "gate_events_for_same_token": sum(1 for e in ev[n0:] if e[2] == first[2]), "player_x_end": m[0xD511] | m[0xD512] << 8})
        res.append({"act": "%d.%d" % (zone, act), "first_defeat": {"type": hx(first[1], 2), "token": first[2], "x": first[3]}, "score_after_first": "100000", "score_end": bytes(m[0xD29D:0xD2A0]).hex(), "revisit_passes": passes})
    return res


GLYPH_TOP_BOTTOM = {}


def decode_cells(rows, digit_pairs):
    pair = {(t, b): str(d) for d, (t, b) in enumerate(digit_pairs)}
    pair[(digit_pairs[8][0], digit_pairs[9][1])] = "9"
    s = ""
    for c in range(len(rows[0])):
        top, bot = rows[0][c] - 256, rows[1][c] - 256
        s += " " if (top, bot) == (33, 33) else pair.get((top, bot), "?")
    return s


def card_cases(rom, digit_pairs, only=None):
    import u4_results as U
    import g0_rig

    class Sess2(g0_rig.Session):
        def __init__(self, rom, sms=None):
            super().__init__(rom, sms)
            self.hook(0x2D08, lambda mm: (mm._write(0xD2A6, 0), mm._write(0xD2A7, 0)))     # zero the time word where a case needs an exact total

    class RigProxy:
        Session = Sess2
        RAM = g0_rig.RAM
        BTN_RIGHT = g0_rig.BTN_RIGHT

        def __getattr__(self, k):
            return getattr(g0_rig, k)

    def cells(snap):
        nt = U.nt_words(snap["vram"])
        return [[nt[r][c] for c in range(13, 20)] for r in (14, 15)]
    cases = [("zero", (0, 0, 0), 0, False), ("ten_raw", (0x10, 0, 0), 0, False), ("raw_12340", (0x40, 0x23, 0x01), 0, False), ("raw_999990", (0x90, 0x99, 0x99), 0, False),
             ("raw_999999", (0x99, 0x99, 0x99), 0, False), ("wrap_to_zero_one_ring", (0x90, 0x99, 0x99), 1, True), ("wrap_past_zero_25_rings", (0x90, 0x99, 0x99), 0x25, True)]
    out = []
    saved = U._import_rig
    for name, sc, rings, zero_word in cases:
        if only is not None and name not in only:
            continue
        U._import_rig = (lambda: (RigProxy(), None)) if zero_word else saved
        try:
            f, raw = U.run_clear(rom, rings=rings, pre=dict(score0=sc[0], score1=sc[1], score2=sc[2], bonus=0), tail_frames=5)
        finally:
            U._import_rig = saved
        sn = raw["snaps"]
        a, b = sn["at_numbers_done"], sn["at_tally_return"]
        ram = lambda s, ad: s["ram"][ad - 0xD000]
        out.append({"case": name, "rings_bcd": "%02X" % rings, "time_word_zeroed": zero_word, "score_in_bcd_le": "%02x%02x%02x" % sc,
                    "card_start": {"score_ram": "%02x%02x%02x" % (ram(a, 0xD29D), ram(a, 0xD29E), ram(a, 0xD29F)), "continues": ram(a, 0xD2C3), "field_text": decode_cells(cells(a), digit_pairs)},
                    "tally_return": {"score_ram": "%02x%02x%02x" % (ram(b, 0xD29D), ram(b, 0xD29E), ram(b, 0xD29F)), "continues": ram(b, 0xD2C3), "field_text": decode_cells(cells(b), digit_pairs)}})
    return out


def build_observed(rom, static):
    pairs = static["hud"]["digit_glyph_table"]["pairs_top_bottom_tile_ids"]
    return {
        "format": 1, "rom_sha256": ROM_SHA256, "research_base": BASE_COMMIT,
        "evidence": "EMULATED ORIGINAL FRAME (tools/sms_frame_harness through tools/g0_rig; NTSC, approximate VDP; unmodified ROM; fixtures are RAM writes noted per block)",
        "natural_census": {"fixture": "new game, character Sonic, hold RIGHT, D503 bit 1 forced at every player update (attack posture), up to 3,500 frames or the act-clear flag; no other input, no teleport",
                           "acts": whole_game_census(rom)},
        "revisit": {"fixture": "after the first defeat the player is teleported 600 px left of the defeated enemy and walks through it three times with the attack posture", "acts": revisit_test(rom)},
        "results_card": {"fixture": "run_clear on THZ1 with the score preset; the time word is zeroed at $2D08 where noted. field_text = the 7 cells at name-table columns 13..19, rows 14..15 decoded through the glyph table", "cases": card_cases(rom, pairs)},
    }


# ------------------------------------------------------------------------------------------------------------------------------------------
# POC LAYER (read only)
POC_PROBES = [
    # id, file, regex that must match exactly one line, role
    ("type_bytes_only", "scripts/SCR_chaos_adapter/SCR_chaos_adapter.gml", r"^function SCR_chaos_enemy_score_100_bytes\(\)", "records the ROM bytes 10 00 00 in three globals; does not touch `score`"),
    ("score_writer", "scripts/SCR_chaos_adapter/SCR_chaos_adapter.gml", r"^function chaos_continue_score_add\(cp_units\)", "the single POC score writer (units = displayed points = raw x 10) with the G2-B continue test"),
    ("units_comment", "scripts/SCR_chaos_adapter/SCR_chaos_adapter.gml", r"The POC score is raw x 10", "documents the unit"),
    ("monitor_10", "objects/OBJ_chaos_object_10/Step_0.gml", r"^SCR_chaos_enemy_score_100_bytes\(\);", "monitor break: bytes only"),
    ("enemy_21", "objects/OBJ_chaos_object_21/Step_0.gml", r"^\s*SCR_chaos_enemy_score_100_bytes\(\);", "type $21 defeat: bytes only"),
    ("enemy_25", "objects/OBJ_chaos_object_25/Step_0.gml", r"^\s*SCR_chaos_enemy_score_100_bytes\(\);", "type $25 defeat: bytes only"),
    ("enemy_27_2c", "objects/OBJ_chaos_object_27/Step_0.gml", r"^\s*SCR_chaos_enemy_score_100_bytes\(\);", "type $27 and (inherited) $2C defeat: bytes only"),
    ("enemy_20_23", "scripts/SCR_chaos_sez_enemy/SCR_chaos_sez_enemy.gml", r"^\s*chaos_continue_score_add\(10\);", "SEZ $20/$23 defeat: adds 10 units"),
    ("enemy_3d", "scripts/SCR_chaos_aqz_enemy/SCR_chaos_aqz_enemy.gml", r"SCR_chaos_enemy_score_100_bytes\(\);chaos_continue_score_add\(10\);", "AQZ $3D defeat: adds 10 units"),
    ("enemy_38", "scripts/SCR_chaos_eez/SCR_chaos_eez.gml", r"SCR_chaos_enemy_score_100_bytes\(\);chaos_continue_score_add\(10\);", "EEZ $38 conversion: adds 10 units"),
    ("enemy_24_add", "scripts/SCR_chaos_mghz_m3/SCR_chaos_mghz_m3.gml", r"if \(!cp_b\.score_disabled\) cp_b\.score\+=10;", "MGHZ $24 landing: M3 counter +10"),
    ("enemy_24_post", "scripts/SCR_chaos_mghz_m3/SCR_chaos_mghz_m3.gml", r"chaos_continue_score_add\(cp_b\.score-cp_score\)", "M3 counter difference forwarded to the writer (10 units)"),
    ("tally_boss", "scripts/SCR_chaos_results/SCR_chaos_results.gml", r"cp_s\.fixed_steps--;chaos_results_score\(cp_s,10,false\);", "boss bonus step: 10 raw"),
    ("tally_ring", "scripts/SCR_chaos_results/SCR_chaos_results.gml", r"cp_raw=10;if\(variable_struct_exists", "ring step: 10 raw"),
    ("tally_word", "scripts/SCR_chaos_results/SCR_chaos_results.gml", r"cp_s\.time_units--;cp_raw=1;", "word step: 1 raw"),
    ("tally_writer", "scripts/SCR_chaos_ss1/SCR_chaos_ss1.gml", r"chaos_continue_score_add\(cp_raw\*10\);", "raw x 10: the correct scaling"),
    ("card_digits", "scripts/SCR_chaos_results/SCR_chaos_results.gml", r"floor\(score/10\)", "results card draws floor(score/10) as the raw digits and then the constant zero glyph"),
    ("card_skip_zero", "scripts/SCR_chaos_results/SCR_chaos_results.gml", r"if\(cp_f\.id!=\"score\" \|\| cp_v>0\)", "digits skipped while the score is zero (as the ROM)"),
    ("card_trailing_zero", "scripts/SCR_chaos_results/SCR_chaos_results.gml", r"cp_z=cp_plan\.score_trailing_zero", "fixed glyph drawn"),
    ("reset_continue", "scripts/SCR_chaos_adapter/SCR_chaos_adapter.gml", r"^\s*score = 0;", "continue accepted: score 0"),
    ("reset_new_game", "scripts/SCR_chaos_level/SCR_chaos_level.gml", r"^\s*score = cp_initial\.score;", "run-state initialiser"),
    ("m3_boss_none", "scripts/SCR_chaos_boss/SCR_chaos_boss.gml", r"No score here", "bosses add nothing at defeat (correct)"),
]


def poc_source(poc_dir):
    poc = Path(poc_dir)
    out = []
    for pid, rel, rx, role in POC_PROBES:
        lines = (poc / rel).read_text(encoding="utf-8", errors="replace").splitlines()
        hits = [i + 1 for i, ln in enumerate(lines) if re.search(rx, ln)]
        if not hits:
            raise SystemExit("POC probe %s not found in %s (the POC changed since %s)" % (pid, rel, POC_COMMIT[:7]))
        out.append({"id": pid, "file": rel, "line": hits[0], "matches": len(hits), "role": role})
    return {"format": 1, "poc_commit": POC_COMMIT, "evidence": "POC SOURCE (read only; static reading, not run)", "probes": out}


# ------------------------------------------------------------------------------------------------------------------------------------------
# MATRIX AND CONTRACT (hand-authored from the evidence above; validate() cross-checks them against the data)
def award_matrix():
    R = []

    def row(i, event, rom_source, zones, eligibility, raw, passes, poc_writer, status, note):
        R.append({"id": i, "event": event, "rom_source": rom_source, "where_placed": zones, "eligibility": eligibility, "rom_raw_units": raw, "rom_displayed_points": raw * 10,
                  "through_262F": passes, "poc_writer": poc_writer, "poc_status": status, "poc_units_should_add": raw * 10, "note": note})
    ELIG_5F3D = "contact AND (D503 bit 1 attack OR D532 == 6 invincible); needs no direction; non-attacking contact scores nothing"
    row("E01", "Type $27 badnik defeated by contact", "$0323 -> $5F3D, callbacks states 1..3 ($89AC/$89F3/$8A29)", "THZ1, THZ2 (and the zone-6 THZ copy)", ELIG_5F3D, 10, True,
        "OBJ_chaos_object_27/Step_0.gml: SCR_chaos_enemy_score_100_bytes()", "MISSING", "bytes only, `score` never changes")
    row("E02", "Type $2C badnik defeated by contact", "same callbacks as $27 (alias state table)", "GPZ1, GPZ2, EEZ1, EEZ2", ELIG_5F3D, 10, True,
        "OBJ_chaos_object_2C inherits OBJ_chaos_object_27 (event_inherited)", "MISSING", "bytes only")
    row("E03", "Type $25 badnik defeated by contact", "$0323 -> $5F3D, states 1,2 ($B573/$B5A0 region; reversal returns before overlap)", "GPZ1, GPZ2", ELIG_5F3D, 10, True,
        "OBJ_chaos_object_25/Step_0.gml: SCR_chaos_enemy_score_100_bytes()", "MISSING", "bytes only")
    row("E04", "Type $21 badnik defeated by side/low contact", "$033E from the state 3/6 callback $B268 after the attack test; TOP contact bounces instead (no score)", "THZ1, THZ2, MGHZ1, MGHZ2",
        "contact AND NOT top contact (player Y <= object Y - 4 bounces first) AND (D503 bit 1 OR D532 == 6); other contact hurts", 10, True,
        "OBJ_chaos_object_21/Step_0.gml: SCR_chaos_enemy_score_100_bytes()", "MISSING", "bytes only")
    row("E05", "Types $20 and $23 badniks defeated by contact", "$0323 -> $5F3D ($20 state 4 callback $B14C, $23 states 1,2)", "SEZ1, SEZ2", ELIG_5F3D, 10, True,
        "SCR_chaos_sez_enemy.gml chaos_sez_enemy_defeat: chaos_continue_score_add(10)", "MIS-SCALED", "adds 10 displayed points, must add 100")
    row("E06", "Type $3D badnik defeated by contact", "$0323 -> $5F3D (states 1,2; $3C is a pure hazard with no score)", "AQZ1, AQZ2", ELIG_5F3D, 10, True,
        "SCR_chaos_aqz_enemy.gml chaos_aqz_enemy_contact: chaos_continue_score_add(10)", "MIS-SCALED", "adds 10, must add 100")
    row("E07", "Type $24 hazard lands and converts (no player action needed)", "$033E at the end of state 3 ($B4F0): converts when the cell under it is solid", "MGHZ1, MGHZ2",
        "autonomous: Sonic within 48 px horizontally starts the fall; the landing converts and scores whatever the player does afterwards", 10, True,
        "SCR_chaos_mghz_m3.gml: cp_b.score+=10 then chaos_continue_score_add(difference)", "MIS-SCALED", "adds 10, must add 100")
    row("E08", "Type $38 mine self-destructs", "$033E from state 3 ($904F): proximity < 32 px on both axes starts the countdown; the conversion follows", "EEZ1, EEZ2 (and $38 children of the parameter-1 producer)",
        "autonomous: the player only has to come close; attack is irrelevant and the same update may also hurt", 10, True,
        "SCR_chaos_eez.gml chaos_ordinary_convert: chaos_continue_score_add(10)", "MIS-SCALED", "adds 10, must add 100")
    row("E09", "Monitor (type $10) broken, every parameter", "$033E from the state-2 callback ($A16C): after $034D contact, requires D503 bit 1 and a downward Y velocity", "all ordinary zones and the Special Stages",
        "contact AND D503 bit 1 (D532 == 6 alone is NOT enough) AND player Y velocity > 0; the reward parameter does not change the score", 10, True,
        "OBJ_chaos_object_10/Step_0.gml: SCR_chaos_enemy_score_100_bytes()", "MISSING", "bytes only; the reward bits are applied but the score is not")
    row("E10", "Boss hit or boss defeat (types >= $50)", "$033E/$5F54 reached, but the gate $5F77 returns for type >= $50", "THZ3 .. EEZ3", "never", 0, False,
        "boss scripts add nothing at defeat", "CORRECT", "natural run: AQZ3 reached the gate 6 times (type $5A) and $262F ran 0 times")
    row("E11", "Act clear: ring tally", "$2D18 CALL $2F00 (+10 raw per ring)", "every ordinary act clear", "once per ring counted down", 10, True,
        "chaos_results_tally: cp_raw=10 -> chaos_results_score -> chaos_ss_score_add(raw) -> add(raw*10)", "CORRECT", "")
    row("E12", "Act clear: time/bonus word tally", "$2D44 CALL $2EFB (+1 raw per word step)", "every ordinary act clear", "once per word step", 1, True,
        "chaos_results_tally: cp_raw=1", "CORRECT", "")
    row("E13", "Act 3 fixed boss bonus", "$2D6A CALL $2F05 (+10 raw per step, N = 50/100/150/200/250 by zone)", "THZ3..AQZ3 results", "once per step before the ring loop", 10, True,
        "chaos_results_boss_bonus: chaos_results_score(cp_s,10,false)", "CORRECT", "")
    row("E14", "Off-screen deletion, lifetime window, scrolling away and back", "none: the cleanup writes types $FE/$FF and never reaches $5F54", "all", "never awards", 0, False,
        "no writer on deletion", "CORRECT", "defeated placements stay occupied and do not respawn in the same act load")
    row("E15", "Repeated contact with a converted enemy or monitor", "the same update sets (IX) := $0F, so no later callback of the type runs", "all", "at most one award per slot instance", 0, False,
        "instance_destroy() / consumed flags", "CORRECT", "a new life reloads the placements: the enemy can be defeated and scored again")
    row("E16", "Any award while D292 != 0 (title, menu, attract demo)", "$262F returns at its first instruction", "attract demos", "never", 0, False, "no POC equivalent", "NOT_APPLICABLE", "relevant only if the POC ever plays the demos")
    row("E17", "Score carry past 999,990 raw", "$262F ADC/DAA wraps modulo 1,000,000 raw; awards a continue when the thousands digit changes", "any", "the add still happens", 0, True,
        "none: `score` grows without a modulus", "MISSING", "display wraps naturally in chaos_results_digits (mod 10 per place); the stored value does not")
    return R


def contract():
    return {
        "format": 1, "title": "G2-E proposed implementation contract (presentation-neutral, for POC review)", "research_base": BASE_COMMIT, "poc_commit": POC_COMMIT,
        "rules": [
            {"id": "S1", "rule": "One owner: the existing GameMaker `score`, in DISPLAYED points (ROM raw x 10, always a multiple of 10). One writer: a single `chaos_score_award_raw(raw)` = `chaos_continue_score_add(raw * 10)`. No other statement may modify `score` except the two resets (S6)."},
            {"id": "S2", "rule": "Enemy/monitor award is the single flat value raw 10 = 100 points for every converted object whose ROM type is below $50. Types >= $50 (all bosses) award nothing; type 0 cannot occur in a live slot. There is no per-type table."},
            {"id": "S3", "rule": "Award exactly once, in the same update the slot becomes type $0F (the call site of the existing SCR_chaos_enemy_score_100_bytes). Defeated placements stay occupied for the act load; deletion, lifetime sleep and scrolling never award."},
            {"id": "S4", "rule": "Eligibility is the existing per-type conversion logic, unchanged (E01..E09). Do not add an attack requirement to $24 and $38, and do not accept D532 == 6 alone for monitors."},
            {"id": "S5", "rule": "Raw ring step 10, word step 1 and act-3 fixed step 10 stay as they are (already correct)."},
            {"id": "S6", "rule": "Resets: New Game (run-state initialiser) and an accepted Continue set `score` to 0; nothing else does. Death, Game Over and act changes keep it."},
            {"id": "S7", "rule": "Wrap: keep `score` modulo 10,000,000 displayed points (raw modulo 1,000,000) inside the single writer, AFTER evaluating the continue threshold on the unwrapped before/after pair. The wrap itself is a threshold crossing (thousands digit 9 -> 0) and awards one continue to BOTH characters; it is implemented in G2-E as part of the shared score owner."},
            {"id": "S8", "rule": "Threshold, both characters, G2-E scope: Sonic is unchanged (one continue each time the thousands digit becomes 0 or 5, i.e. every 5,000 raw, including the wrap). Tails earns one continue each time floor(raw/1000) becomes a multiple of 3 (every 3,000 raw), so TWO separate award events occur near the end of a cycle: one when the score crosses 999,000 raw and one when it wraps to 0 at 1,000,000 raw, 1,000 raw later; each pays exactly one continue and neither event pays two. The stateless floor(raw/3000) formula of the G2-B writer misses the second event and must be extended (for example by also paying when the score wraps). Broader Tails gameplay (movement, signs, bosses, art) remains G6 and is outside this contract."},
            {"id": "H1", "rule": "There is NO live score HUD in the original: the score is drawn only on the results card (and its three tally loops). Do not add an in-level score display. The results-card drawing already matches (six raw digits, five leading blanks, constant '0' glyph, field skipped while score == 0)."},
            {"id": "H2", "rule": "Optional exact parity: at the instant the score wraps to exactly zero during a tally the ROM does not redraw the field (the old digits remain). Reproduce only if a pixel-exact tally is required; it is unreachable in normal play."},
        ],
        "smallest_poc_changes": [
            {"id": "P1", "files": ["scripts/SCR_chaos_adapter/SCR_chaos_adapter.gml"], "change": "add `function chaos_score_award_raw(cp_raw){ SCR_chaos_enemy_score_100_bytes(); return chaos_continue_score_add(cp_raw*10); }` and the S7 wrap inside chaos_continue_score_add"},
            {"id": "P2", "files": ["objects/OBJ_chaos_object_10/Step_0.gml", "objects/OBJ_chaos_object_21/Step_0.gml", "objects/OBJ_chaos_object_25/Step_0.gml", "objects/OBJ_chaos_object_27/Step_0.gml"], "change": "replace the bytes-only call by chaos_score_award_raw(10) (also covers $2C through inheritance)"},
            {"id": "P3", "files": ["scripts/SCR_chaos_sez_enemy", "scripts/SCR_chaos_aqz_enemy", "scripts/SCR_chaos_eez"], "change": "replace chaos_continue_score_add(10) by chaos_score_award_raw(10)"},
            {"id": "P4", "files": ["scripts/SCR_chaos_mghz_m3/SCR_chaos_mghz_m3.gml"], "change": "forward `(cp_b.score - cp_score) * 10` (or call chaos_score_award_raw(10) per conversion) instead of the raw difference"},
        ],
        "acceptance_checks": [
            "THZ1 natural run with the attack posture forced awards 100 points to each of: first $21, first monitor, second $21 (observed census: ROM score bytes 10, 20, 30 raw)",
            "defeating the same placement twice (revisit) never adds a second 100",
            "a boss hit adds nothing; the AQZ3 boss run keeps the score at 0 until the tally",
            "an MGHZ $24 landing adds exactly 100 even if the player never touches it; an EEZ $38 self-destruct adds exactly 100",
            "a monitor with only invincibility (D532 == 6) and no attack bit adds nothing",
            "score 999,900 displayed + 100 wraps to 0 and grants one continue for both characters",
            "Tails, continues 0: 9,989,900 -> 9,990,000 displayed (998,990 -> 999,000 raw) grants one continue; then 9,999,900 -> 0 displayed (999,990 -> 0 raw) grants exactly one more (total 2, two events)",
        ],
    }


# ------------------------------------------------------------------------------------------------------------------------------------------
def validate(static, controlled, observed, poc, matrix, contr):
    n = 0

    def ok(c, m=""):
        nonlocal n
        assert c, m
        n += 1
    # static
    ok(static["rom_sha256"] == ROM_SHA256)
    ok(static["writer_census"]["callers"]["262F"] == ["0x02F0C", "0x05F81"])
    ok([e["raw_units"] for e in static["award_table"]["entries"]] == [1, 10, 50, 10])
    ok(static["award_table"]["referenced_by_ld_hl_in_fixed_code"]["0x27E8"] == [], "the +50 entry is referenced")
    ok(static["hud"]["fixed_block"]["equals_digit_0_glyph"])
    ok(static["hud"]["fixed_block"]["name_table_address"] == "0x3BA6")
    ok(static["hud"]["max_displayed"] == 9999990)
    ok(set(static["types_reaching_a_conversion_below_0x50"]) >= {hx(t, 2) for t in SCORE_TYPES}, static["types_reaching_a_conversion_below_0x50"])
    sites = [s for s in static["conversion_sites"] if s["kind"] != "5FA0_solid_contact_not_score"]
    ok(len(sites) == 20, len(sites))
    ok(sum(1 for s in static["conversion_sites"] if s["kind"] == "5FA0_solid_contact_not_score") == 9)
    # controlled
    add = controlled["score_adder"]
    ok(add["cycle_sweep"]["model_mismatches"] == 0)
    ok(add["cycle_sweep"]["sonic_awards"] == 200 and add["cycle_sweep"]["tails_awards"] == 334, (add["cycle_sweep"]["sonic_awards"], add["cycle_sweep"]["tails_awards"]))
    ok(add["wrap"]["sonic"]["after"] == 0 and add["wrap"]["sonic"]["continues_after"] == 1)
    ok(add["wrap"]["tails"]["after"] == 0 and add["wrap"]["tails"]["continues_after"] == 1)
    ok(add["wrap"]["sonic"]["dead_cap_d2a3"] == "909999" and add["wrap"]["sonic"]["dead_flag_d2bb"] == 2)
    ok(all(c["after"] == c["before"] and c["continues_after"] == 0 for c in add["corners"] if c["d292"] != 0) and sum(1 for c in add["corners"] if c["d292"] != 0) == 2, "gate")
    ok(controlled["type_gate"]["amount_raw"] == 10)
    for r in controlled["contact_matrix"]:
        p = r["postures"]
        ok(p["attack"]["award_bcd_le"] == "100000" and p["attack"]["type_after_first"] == "0x0F", (r["type"], r["parameter"]))
        ok(p["attack"]["score_after_third_update"] == "100000", "second update must not add")
        ok(p["invincible"]["award_bcd_le"] == "100000")
        ok(p["airborne_only"]["award_bcd_le"] == "000000" and p["none"]["award_bcd_le"] == "000000", (r["type"], r["parameter"]))
    for pname, g in controlled["monitor_grid"].items():
        ok(g["awarding_cells"].get("attack", 0) > 0 and g["awarding_cells"].get("invincible", 0) == 0 and g["awarding_cells"].get("none", 0) == 0, pname)
        ok(g["second_update_never_adds"])
    s21 = controlled["type_21_grid"]["summary"]
    ok(s21["no_posture_cells_with_award"] == 0)
    for t in controlled["autonomous_conversions"]["trials"]:
        if t["type"] == "0x38" and t["parameter"] == "0x01":
            ok(t["first_award"] is None, "the parameter-1 producer never self-destructs (its children do)")
        else:
            ok(t["first_award"] is not None and t["first_award"]["score"] == "100000" and t["first_award"]["type_after"] == "0x0F", t)
    ok(all(f["score"] == "000000" for f in controlled["autonomous_conversions"]["player_far_away"]))
    # observed
    nat = observed["natural_census"]["acts"]
    ok(len(nat) == 18)
    ok(all(a["score_field_draws_while_playing"] == 0 for a in nat), "the score field is drawn during play")
    for a in nat:
        ok(all(e["table"] == "0x27EB" for e in a["award_events"]), a["act"])
        ok(len(a["award_events"]) == len([g for g in a["gate_events"] if int(g["type"], 16) < 0x50 and int(g["type"], 16) != 0]), a["act"])
        tokens = [(g["type"], g["token"], g["lives"]) for g in a["gate_events"] if int(g["type"], 16) < 0x50]
        ok(len(tokens) == len(set(tokens)), "two awards for one placement within one life in " + a["act"])
    boss = next(a for a in nat if a["act"] == "4.2")
    ok(len(boss["gate_events"]) >= 1 and boss["award_events"] == [] and all(int(g["type"], 16) >= 0x50 for g in boss["gate_events"]))
    for r in observed["revisit"]["acts"]:
        ok(all(p["gate_events_for_same_token"] == 0 for p in r["revisit_passes"]) and r["score_end"] == "100000", r["act"])
    cases = {c["case"]: c for c in observed["results_card"]["cases"]}
    ok(cases["zero"]["card_start"]["field_text"] == "      0")
    ok(cases["ten_raw"]["card_start"]["field_text"] == "    100")
    ok(cases["raw_12340"]["card_start"]["field_text"] == " 123400")
    ok(cases["raw_999990"]["card_start"]["field_text"] == "9999900")
    ok(cases["wrap_to_zero_one_ring"]["tally_return"]["score_ram"] == "000000" and cases["wrap_to_zero_one_ring"]["tally_return"]["continues"] == 1)
    ok(cases["wrap_to_zero_one_ring"]["tally_return"]["field_text"] == cases["wrap_to_zero_one_ring"]["card_start"]["field_text"] == "9999900", "stale field")
    # poc and matrix
    if poc:
        ids = {p["id"] for p in poc["probes"]}
        ok({"score_writer", "enemy_20_23", "enemy_3d", "enemy_38", "monitor_10", "tally_writer"} <= ids)
    ok(len(matrix) == 17)
    ok({r["poc_status"] for r in matrix} == {"MISSING", "MIS-SCALED", "CORRECT", "NOT_APPLICABLE"})
    ok(all(r["rom_displayed_points"] == r["rom_raw_units"] * 10 for r in matrix))
    ok(contr["rules"][1]["id"] == "S2")
    return n


def build_all(rom, only, poc_dir):
    static, keys = build_static(rom)
    out = {STATIC_JSON: static}
    controlled = observed = None
    if only in ("controlled", "all"):
        controlled = build_controlled(rom, keys)
        out[CONTROLLED_JSON] = controlled
    if only == "all":
        observed = build_observed(rom, static)
        out[OBSERVED_JSON] = observed
    poc = poc_source(poc_dir) if poc_dir else (load_json(POC_JSON) if POC_JSON.exists() else None)
    if poc_dir:
        out[POC_JSON] = poc
    mat, con = award_matrix(), contract()
    out[MATRIX_JSON] = {"format": 1, "title": "G2-E event-to-award matrix", "research_base": BASE_COMMIT, "poc_commit": POC_COMMIT,
                        "legend": {"MISSING": "the POC has the defeat but no `score` write", "MIS-SCALED": "the POC writes 10 displayed points where the ROM awards 100",
                                   "CORRECT": "matches the ROM", "NOT_APPLICABLE": "no POC counterpart needed"}, "rows": mat}
    out[CONTRACT_JSON] = con
    return out, static, controlled, observed, poc, mat, con


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rom", nargs="?", type=Path)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--only", choices=("static", "controlled", "all"), default="all")
    ap.add_argument("--poc", type=Path)
    ap.add_argument("--validate", action="store_true")
    a = ap.parse_args()
    if a.validate:
        n = validate(load_json(STATIC_JSON), load_json(CONTROLLED_JSON), load_json(OBSERVED_JSON), load_json(POC_JSON), load_json(MATRIX_JSON)["rows"], load_json(CONTRACT_JSON))
        print("validate: %d assertions" % n)
        return
    if a.rom is None:
        ap.error("ROM path required")
    rom = load_rom(a.rom)
    out, static, controlled, observed, poc, mat, con = build_all(rom, a.only, a.poc)
    if a.only == "all":
        print("validate: %d assertions" % validate(static, controlled, observed, poc, mat, con))
    DATA.mkdir(parents=True, exist_ok=True)
    bad = []
    for path, obj in out.items():
        text = dumps(obj)
        if a.check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                bad.append(str(path.relative_to(ROOT)))
        else:
            path.write_text(text, encoding="utf-8")
            print("wrote", path.relative_to(ROOT), len(text))
    if a.check:
        if bad:
            raise SystemExit("MISMATCH: " + ", ".join(bad))
        print("g2e score: committed data match the ROM-derived regeneration (%s)" % a.only)


if __name__ == "__main__":
    main()
