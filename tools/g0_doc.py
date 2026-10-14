"""Render the generated tables of docs/g0-campaign-contract.md from the committed JSON (no ROM needed)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "g0-campaign-contract.md"
BEGIN, END = "<!-- g0-generated:begin -->", "<!-- g0-generated:end -->"
ZONES = ["THZ", "GPZ", "SEZ", "MGHZ", "AQZ", "EEZ"]


def cell(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def render_tables(contract, ledger):
    out = []
    out.append("### Run state and flow bytes\n")
    out.append("| Name | Address | Scope | Role |\n|---|---|---|---|")
    for r in contract["ram"]:
        out.append("| `%s` | `$%s` | %s | %s |" % (r["name"], r["address"], r["scope"], cell(r["role"])))
    out.append("\n### Transitions\n")
    for tr in contract["transitions"]:
        flag = " **(FORCED-ONLY)**" if tr.get("forced_only") else ""
        out.append("#### %s - %s%s\n" % (tr["id"], tr["name"], flag))
        out.append("Trigger: %s. Evidence: %s. Oracle: %s.\n" % (cell(tr["trigger"]), "; ".join(tr["evidence"]), ", ".join("`%s`" % o for o in tr["oracle"]) or "none (source-traced)"))
        for f in contract["fields"]:
            out.append("- **%s**: %s" % (f.replace("_", " "), cell(tr["effects"][f])))
        out.append("\n_%s_\n" % cell(tr["notes"]))
    out.append("### Expected outcomes\n")
    out.append("| Event | Where | Result | Transition |\n|---|---|---|---|")
    for o in contract["outcomes"]:
        out.append("| %s | %s | %s | %s |" % (cell(o["event"]), cell(o["where"]), cell(o["result"]), o["transition"]))
    out.append("\n### ROM start positions (camera and player, from the table at `$4E65`)\n")
    out.append("| Zone | Act 1 (index 0) | Act 2 (index 1) | Act 3 (index 2) |\n|---|---|---|---|")
    sp = {(r["zone"], r["act"]): r for r in contract["start_positions"]}
    for z in range(6):
        out.append("| %d %s | %s |" % (z, ZONES[z], " | ".join("player (%d,%d), camera (%d,%d)" % (sp[(z, a)]["player_x"], sp[(z, a)]["player_y"], sp[(z, a)]["camera_x"], sp[(z, a)]["camera_y"]) for a in range(3))))
    out.append("\n### Palette steps after the tally (harness frames relative to the `$14AE` entry)\n")
    out.append("| Run | tally returned | first CRAM change | full white | black | act incremented |\n|---|---|---|---|---|---|")
    for sid, r in contract["palette_fade_answer"]["emulated"].items():
        out.append("| `%s` | %d | %d | %d | %d | %d |" % (sid, r["tally_returned"], r["tally_returned"] + r["first_change_after_tally"], r["to_white_frame"], r["to_black_frame"], r["act_incremented"]))
    out.append("\n### Ordered G1/G2 dependency ledger\n")
    out.append("| # | Package | Milestone | Depends on | Status | Contract | Gaps needing new proof |\n|---|---|---|---|---|---|---|")
    for p in ledger["ordered_dependency_ledger"]:
        out.append("| %d | %s %s | %s | %s | %s | %s | %s |" % (p["order"], p["id"], cell(p["title"]), p["milestone"], ", ".join(p["depends_on"]) or "-", cell(p["status"]),
                                                                  ", ".join(p["contract"]), cell("; ".join(p["gaps"]) or "-")))
    out.append("\n### Unresolved items\n")
    out.append("| Id | Item | State | Blocks |\n|---|---|---|---|")
    for u in contract["unresolved"]:
        out.append("| %s | %s | %s | %s |" % (u["id"], cell(u["item"]), cell(u["state"]), cell(u["blocks"])))
    out.append("\n### FULLGAME-0 reconciliation\n")
    out.append("| Feature | FULLGAME-0 (POC SS1) | G0 | Basis | Note |\n|---|---|---|---|---|")
    for r in ledger["fullgame0_reconciliation"]:
        out.append("| %s | %s | %s | %s | %s |" % (r["id"], r["fg0"], r["g0"], cell(r["basis"]), cell(r["note"])))
    out.append("\n| Question | FULLGAME-0 | G0 | Answer |\n|---|---|---|---|")
    for q in ledger["fullgame0_questions"]:
        out.append("| %s | %s | %s | %s |" % (q["id"], cell(q["fg0"]), q["g0"], cell(q["answer"])))
    out.append("\n### Static POC observations (read-only, accepted SS5 `%s`)\n" % ledger["poc_ss5"][:7])
    out.append("| Id | File | Lines | Finding |\n|---|---|---|---|")
    for s in ledger["static_poc_observations"]:
        out.append("| %s | `%s` | %s | %s |" % (s["id"], s["file"], s["line"], cell(s["finding"])))
    return "\n".join(out) + "\n"


def splice(text, tables):
    a, b = text.index(BEGIN) + len(BEGIN), text.index(END)
    return text[:a] + "\n\n" + tables + "\n" + text[b:]


def update(contract, ledger):
    DOC.write_text(splice(DOC.read_text(encoding="utf-8"), render_tables(contract, ledger)), encoding="utf-8", newline="\n")
