# GPZ enemy / boss approved Research checkpoint

Date: 2026-10-03. Branch: `research/gpz-enemies-art-approval`, base `08fb38c`.
Status: **$25, $2C, corrected $51, $34, $0A, $0F approved by the user on 2026-10-03.
Research commit/push authorized; main integration and POC handoff remain separate**.

Outputs:

- `docs/gpz-enemy-audit.md`: regular behavior/contact/lifecycle/placements/reuse.
- `docs/gpz3-boss-art-support-audit.md`: mode-dependent linked boss composition and support assets,
  source-traced state scripts; complete boss gameplay certification explicitly deferred.
- `docs/gpz-art-approval-checklist.md`: frame counts, mirroring, anchors, child/effect
  dependencies, completed approval record and AGENTS candidate update.
- `data/rom-cache/gpz/enemy-art-approval.json`: version-checked data and original-routine
  results, source-region hashes, full 18-act placement census and asset usage.
- `tools/gpz_enemy_approval.py`, `tools/gpz_enemy_previews.py`: reproducible extraction
  and deterministic labelled PNG rendering; decoded art stays under ignored build/.
- `tests/test_gpz_enemy_approval.py`: five tests, including original-ROM execution.
- `build/gpz-enemy-approval/png-manifest.json`: retained original 67-PNG manifest;
  approved sibling assets are unchanged. Its old boss exclusions/status are superseded
  by `build/gpz51-correction/png-manifest.json` and the per-subject approval cache.
- `docs/gpz3-boss-composition-correction.md`, `data/rom-cache/gpz/boss-51-composition.json`:
  corrected head/ball links, mode gate, bottom-first throws, regrowth and live dust.
- `tools/gpz51_composition.py`, `tools/gpz51_previews.py`, `tests/test_gpz51_composition.py`:
  three-mode/both-direction original-scheduler replay and boss-only corrected PNGs.

Verification:

- Canonical ROM size/hash verified on every extractor/test invocation.
- 5 new tests passed with `SONIC_CHAOS_ROM` set (none skipped).
- Existing `$27` arithmetic/reuse tests: 3 passed.
- Existing mapped-object registration regression tests: 17 passed.
- 5,555 overlap-grid points: zero mismatches, plus 96 posture/invincibility/direction
  reaction cases; state `$0F` extent uses the prior shared geometry audit.
- 256 original `$25` initializers passed; signed `$2C` 64/384 boundaries passed.
- All 48 nonblank frame/orientation SAT reconstructions agree with the independent
  original-renderer model; forced unused mirrors remain excluded from imports.
- Full cache regenerated and `--check` passed. PNGs reopened/verified locally.
- `git diff --check` passed; new files separately checked for whitespace.

Visual QA corrected the `$25` context to the original GPZ terrain-projected anchor
`(848,302)` from raw placement `(848,334)` without modifying placement data.
The original boss composition was wrong and is retained only as rejected history.
Replacement uses original scheduler-captured positions, parameter0 head above
three balls in modes0/1, four balls only in mode2, and parameter17 landing dust.
The supplied 11.5-second video confirms the normal shrink/regrow sequence.

Unresolved: below-map GPZ1 `$25` reachability; informal names;
complete GPZ3 health/contact/arena/clear boundary oracles;
later EEZ art, results/audio. No substitute art, ROM dumps or assets in tracked output.
POC was not modified; its unrelated existing untracked diagnostics were left alone.

## $51 correction verification

- 11 GPZ approval/composition tests passed with the verified ROM, no skips.
- 20 existing object27/registration checks passed (31 focused checks total).
- Original scheduler replay covers three modes and left/right motion; 256
  initializer low-byte cases verify both mode selection and conditional spawn.
- Both caches regenerate identically; 28 corrected boss-only PNGs reopen and
  match their manifest hashes/dimensions. Five sheets plus eleven transparent
  frames and eleven context snapshots, plus the six-panel sequence summary.
- All 41 original non-boss PNG files match their retained hashes; `$25`, `$2C`
  and support-effect approvals remain unchanged. The original 26 boss PNG files
  remain available as rejected history; none was overwritten by this correction.
- Replacement art was visually checked against source composition and the
  supplied recording. James explicitly approved the corrected `$51` package.
- Normal stack is head + balls1/2/3, throws3 ->2 ->1, regrowth1 ->2 ->3;
  frames10/11 are runtime-used `$51/$11` landing dust. Mode2 adds ball4.
- `data/rom-cache/gpz/approved-art-manifest.json` freezes 69 current PNG records,
  26 approved transparent runtime frame files and the superseded boss board hashes.
  ROMs, extracted graphics and gameplay video remain local-only, under ignored build/;
  only metadata, reproducible tools, tests and documentation enter Git.
- Commit SHA and push status are reported with the completed checkpoint. The
  research branch starts at main `08fb38c`; main needs integration after push.
  POC and root AGENTS were untouched.
