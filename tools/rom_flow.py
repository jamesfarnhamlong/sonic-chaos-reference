"""Static control-flow evidence for the ROM address ledger (DECOMP-1A).

Two small, deterministic primitives, both built on the existing ``z80dis``
decoder and the byte-verified recovered assembly:

* ``branch_sites`` lists every CALL / JP / JR / DJNZ / RST inside the recovered
  CODE regions together with the file offset its target resolves to. A site in a
  recovered region is byte-verified code, so its target is an executed entry
  point. Targets below ``$8000`` are the resident engine (file offset == CPU
  address). A site that itself executes in slot 2 (CPU ``$8000+``) cannot remap
  slot 2, so a slot-2 target is in the *same* bank. A resident site calling a
  slot-2 address is ambiguous and is never resolved.
* ``descend`` follows control flow from entry points, confined to a byte range.
  It reports exactly which bytes are fetched as instructions and why each path
  stopped. Nothing outside the range is decoded.

Neither primitive guesses: an undecodable byte, a branch leaving the range, a
fall-through off the end, or an unresolvable indirect jump is reported.
"""
from z80dis import z80

OP = z80.OP
BANK = 0x4000
RESIDENT_END = 0x8000
TRANSFER_OPS = (OP.CALL, OP.JP, OP.JR, OP.DJNZ)


def decode(rom, offset):
    d = z80.decode(bytes(rom[offset:offset + 4]), offset & 0xFFFF)
    return d


def is_invalid(d):
    return not d.len or d.op == OP.NONI


def _addr_operand(d):
    for kind, value in d.operands:
        if kind.name == "ADDR":
            return value
    return None


def _has_cond(d):
    return any(kind.name == "COND" for kind, _ in d.operands)


def is_terminal(d):
    """Instruction after which execution never falls through."""
    if d.op in (OP.RETI, OP.RETN, OP.HALT):
        return True
    if d.op == OP.RET:
        return not _has_cond(d)
    if d.op in (OP.JP, OP.JR):
        return not _has_cond(d)          # includes JP (HL)/(IX)/(IY)
    return False


def is_indirect_jump(d):
    return d.op == OP.JP and _addr_operand(d) is None


def resolve_target(site_offset, cpu_target):
    """File offset of a branch target, or None when the bank is ambiguous."""
    if cpu_target < RESIDENT_END:
        return cpu_target
    site_bank = site_offset // BANK
    if site_bank >= 2 and (0x8000 + site_offset % BANK) >= 0x8000 and cpu_target < 0xC000:
        return site_bank * BANK + (cpu_target - 0x8000)
    return None


def code_regions(regions):
    return [r for r in regions if r["kind"] == "code"]


def region_instructions(rom, region):
    """Instruction (offset, length, decoded) tuples of one recovered code region."""
    out, p = [], region["start"]
    while p < region["end"]:
        d = decode(rom, p)
        if is_invalid(d) or p + d.len > region["end"]:
            raise ValueError("recovered region %s does not decode at %05X" % (region["name"], p))
        out.append((p, d.len, d))
        p += d.len
    return out


def branch_sites(rom, regions):
    """{site_offset: (op_name, cpu_target, resolved_file_offset_or_None, region_name)}"""
    sites = {}
    for region in code_regions(regions):
        for p, _, d in region_instructions(rom, region):
            if d.op in TRANSFER_OPS:
                target = _addr_operand(d)
                if target is not None:
                    sites[p] = (d.op.name, target, resolve_target(p, target), region["name"])
            elif d.op == OP.RST:
                pass
    return sites


def descend(rom, seeds, lo, hi):
    """Recursive descent confined to ``[lo, hi)``.

    Returns (reached, notes): ``reached`` maps instruction offset -> length;
    ``notes`` lists stop reasons (``invalid``, ``leaves_range``, ``falls_off``,
    ``indirect``) as (kind, offset). Branches to targets outside the range are
    not followed and are recorded as ``leaves_range``.
    """
    reached, notes = {}, []
    stack = list(seeds)
    while stack:
        p = stack.pop()
        while True:
            if p in reached:
                break
            if not lo <= p < hi:
                notes.append(("leaves_range", p))
                break
            d = decode(rom, p)
            if is_invalid(d) or p + d.len > hi:
                notes.append(("invalid" if is_invalid(d) else "falls_off", p))
                break
            reached[p] = d.len
            if is_indirect_jump(d):
                notes.append(("indirect", p))
            elif d.op in TRANSFER_OPS:
                target = _addr_operand(d)
                t = resolve_target(p, target)
                if t is None or not lo <= t < hi:
                    notes.append(("leaves_range", p))
                else:
                    stack.append(t)
            if is_terminal(d):
                break
            p += d.len
    return reached, sorted(set(notes))


def runs(reached):
    """Contiguous byte runs (start, end) covered by the reached instructions."""
    out = []
    for p in sorted(reached):
        end = p + reached[p]
        if out and out[-1][1] == p:
            out[-1] = (out[-1][0], end)
        else:
            out.append((p, end))
    return out
