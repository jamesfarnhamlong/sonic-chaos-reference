# Sonic Chaos — Risk-Ranked Legacy GameMaker Adapter Audit (Parked)
**13 November 2026 · MANAGER #12 · DESIGN-ONLY FOLLOW-UP · NOT A CURRENT CODING JOB**

Chief reasonably asks whether R18's vestigial THZ-specific special-case indicates other early prototype fixes or retained GameMaker template code. The uploaded `THZ_OVERRIDE_AUDIT.md` supports a **narrow finding**, not a codebase-wide diagnosis: obsolete THZ ring-TV swept collision and two dispatch guards conflicted with later shared terrain-monitor handling; **no other THZ-only monitor bypass** was found in audited paths. No evidence currently establishes which historical developer/agent originally introduced it, whether it was a temporary workaround or precisely how/why the branch survived.

**No more sweeping 'fix all legacy code' sprint.** Chief's practical, playable game is the priority. After R18 actual physical F5 passes and P1 fullscreen/title Quit/live-setting issues are addressed, conduct at most **one short static/source ownership inventory** and zero speculative deletions, using the relevant Git history where available. Record each candidate by: original purpose/provenance if known; current caller; whether source is used by an actually compiled ordinary/Special Stage/Boss Rush path; whether it overlaps current shared ROM-derived path; any user-visible failure; and a recommended KEEP / INVESTIGATE ON REPRODUCTION / REMOVE AFTER TEST decision.

Specific attention, without presuming bugs:
- `OBJ_CHAOS_mask_07/Step_2.gml`: legacy one-way solid handler, normal player uses ROM terrain profiles, but other runtime consumers may still rely on it.
- `OBJ_monitors` legacy sample-engine bridge: narrow nonattacking/not-airborne contact path; prove caller and effects before considering retirement.
- `OBJ_chaos_terrain_3/Draw_0.gml`: current four-cell broken-map rendering; likely legitimate.
- `SCR_cc_spring` zone-zero diagonal spring impulse: original ROM difference, **preserve**.
- Other stage-level `if zone==...` gameplay overrides, only when conflicting with a newer common handler; zone-specific source-original content is not inherently vestigial.

**Escalate to coding only for an actual confirmed collision, duplicate owner, unreachable replaced code or reproducible gameplay issue.** Use focused compiled tests and relevant source comparisons; do not spend many sessions producing a hundred-page inventory or require 100% ROM decomp parity. This task is not authorised to edit R18/R17 or production now.

Only current gate: Chief actual Windows R18 near/far/chain spin-dash monitor acceptance. Followed by P1 Classic fullscreen + **both-mode title Quit** + Enhanced live pause setting labels. Later attraction-tail polish and limited Enhanced extras can proceed by owner priority.
