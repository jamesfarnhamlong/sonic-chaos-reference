# M6-G — Manager review and single Chief F5 gate
**Manager-san #8 · 2 November 2026**

## Decision: MANAGER GO for ONE Chief native GameMaker F5 session; NOT Chief accepted

Verified `jamesfarnhamlong/SonicChaos_POC:poc/m6g-all-enemy-persistence@6e2ffcc1f333c5cdaa0048ac696b55c4f6308905` against **fully Chief-accepted M6-F-R1 `636ed72be111bc3de4c297e5768c40c8f38a54e6`**. GitHub compare reports **one commit ahead, zero behind**, exact remote branch tip. There are **four production GML changes** and source-host verification/report/coverage artifacts. No POC main merge. Private user-local full source ZIP `SonicChaos_M6G_20261102_A_PRIVATE.zip` and external SHA256 receipt were reported, but Manager GitHub review cannot directly authenticate E: drive package bytes. Do not claim a Windows native GameMaker smoke has run; Chief's F5 is pending.

Reviewed the GitHub report `docs/m6g-enemy-persistence.md`, `verification/m6g/coverage.csv`, `verification/m6g/gate.json`, actual GML changes, logs and separately uploaded owner report/matrix. The **95 placements / seven regular-enemy numeric types** are correctly reflected in the matrix (THZ/MGHZ `$21` 26, GPZ `$25` 12, SEZ `$20` 7, SEZ `$23` 8, AQZ `$3D` 19, THZ `$27` 7, GPZ/EEZ `$2C` 16). Other original placed actors (MGHZ `$24/$2E`, AQZ `$3C`, EEZ `$36/$38` and related) have distinct hazard/emitter/pool contracts and were catalogued rather than blanket-modified. THZ1's additional nine room-authored enemies were considered separately. Census is about **ordinary regular enemies**, not every actor or every natural gameplay route.

**Implementation checks:**
- `SCR_chaos_placement.gml`: dedicated already-awake patrol lifecycle. In **348-wide** mode retain within **camera.left-512 <= X < camera.left+viewWidth+512**; outside vertical awake band **camera.top-128 <= Y < camera.top+384**, return **sleep/cell2** instead of destroy/cell3. Original native256 entry/retire remains for the covered regular family. This is an explicitly labelled **PC-widescreen QoL departure**, not falsely claimed original generic ROM deletion.
- `OBJ_chaos_object_25/Create_0.gml`, `Step_0.gml`: classify as `$25`, add explicit blank initial scheduler pass, restore original `$B573` callback updates even while asleep (including continuous movement/floor/reversals/contacts), and bound true below-world falls with a type-specific world-bottom guard. **This does change native256 callback timing/motion from inherited code**, with original Z80 controls as justification; don't write 'all 256 behaviour byte-identical'.
- `SCR_chaos_aqz_enemy.gml`: apply only to `$3D`; spear hazard `$3C` unchanged.
- THZ `$21`, SEZ `$20/$23` retain state while vertical asleep and respect their own original pause/continue callback rules; THZ/GPZ/EEZ `$27/$2C` R1 flying behaviour is unchanged.
- Source diff confirms **no change** to lost-ring script, shared player/camera, audio, original km/h, character-select/intro, game assets, or boss/projectile logic; 1,314 resource registrations/38 IncludedFiles preserved per agent inventory/packaging evidence.
- Evidence includes THZ1 token27 retirement update115, THZ2 token34 update114, GPZ2 token28 update56, SEZ1 `$20` token31 update61 and `$23` token35 update165; the candidate retains the encountered token and evolving state, rather than recreating an origin-initialised enemy. These are controlled local/source-host update numbers, **not native game footage**.

**Verification:** `verification/m6g/gate.json` reports **19 PASS / 2 raw FAIL**. Focused 11,774 placement/character assertions, 760 placement/axis/width scenarios, 20 physical terrain/player/camera routes; 9,196 original Z80 assertions at95 placements;10,306 original-vs-GML comparison assertions across72 nonflying placements;4,012 ownership checks. Accepted R1 197 bee tests, M6-F 15,748 scoped tests with2,038 ring trace rows, lost-ring verifier879,757, plus GPZ/AQZ/MGHZ/EEZ/SEZ and frontend/regression gates passed in documented order. No full native input-only 18-act comparison claimed.

**Retained raw FAILs must stay FAIL**, not simply 'two inherited':
1. `verify_viewport_adapter.js:249` — **inherited** all-width384 literal ignores accepted widescreen flying lifetime policy since M6-F.
2. `verify_sez_s4.js:329` — original raw test expects old wide vertical removal; **newly superseded by M6-G's intended QoL** sleep/retention. The separate SEZ policy-aware verifier passes. Historic raw output unchanged; this is not a hidden green.
The inherited M6-G source report also explicitly retains `$21` falling `$B2F0` while-asleep motion mismatch in previous GameMaker global gate (not fixed here; original awake callback comparison only), and GPZ1 `$25` token18 origin Y878 below authored768px layout (natural accessibility unproven). These are **known source scope limits**, not conditions to claim blanket ROM parity. Include in base-playthrough watchlist if a real gameplay symptom emerges; avoid speculative changes before user test.

## Exactly ONE Chief F5 gate

Use `E:\AI\Codex\Sonic Chaos\releases\SonicChaos_M6G_20261102_A_PRIVATE.zip`; extract to a fresh directory and open existing GameMaker `SonicChaos_A4B_EXPERIMENTAL.yyp` in normal **348×196** F5. No additional agent build before this gate.

1. **THZ regular ground patroller**: engage/observe a patrol and its direction change, descend vertically or move away, return. The **same living encounter** should retain its position, direction and patrol phase rather than reset. Original asleep patrols can *pause movement* while out of active range; pausing is not itself failure.
2. **GPZ `$25` patrol**: observe it moving/reversing, make a modest backtrack/vertical departure, return. Patrol should persist and continue moving offscreen consistent with original `$B573` callbacks. Very large horizontal separations and a genuine below-map fall may still retire it.
3. **SEZ `$20` hopping walker**: observe a hop, depart briefly, return. Same walker should resume from its preserved hop/walk state, not restart at its initial placement. Sleeping callbacks may pause, which is canonical.
Chief may report **THZ PASS/FAIL, GPZ PASS/FAIL, SEZ PASS/FAIL**, with concrete visible position/route only for failures. **No GPZ3 lost rings, THZ2 bee, 63 Sound Test tracks, original km/h, character select, other acts or full-campaign human retests.** Source-host passes do not replace this native approval.

If all three are Chief PASS: promote integrated `6e2ffcc1f333c5cdaa0048ac696b55c4f6308905` to the fully accepted private production baseline and proceed with Chief's planned full base-game playthrough *before* enhancements. If a scenario fails, retain accepted R1 as fallback and correct the precise family in a coherent small batch, without reopening ring/bee or repeating huge verification unnecessarily. No automatic POC main merge/public release.

**Reference:** [M6-G Chief directive](m6g-regular-enemy-persistence-chief-directive-20261102.md), [M6-F-R1 previous acceptance and review](m6fr1-manager-review-chief-gate-20261102.md). AGENTS/ROADMAP/MEMORY/current issue register should reflect Manager GO/Chief F5 pending and do not append old future task banners.
