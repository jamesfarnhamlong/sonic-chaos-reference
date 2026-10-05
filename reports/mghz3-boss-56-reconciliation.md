# Focused MGHZ3 boss reconciliation — 2026-10-05

Branch `research/mghz3-boss-reconciliation`, based on Research main
`badba9d085906054e4f15fa1d1a960ca2ae0abdd`. No main merge, POC edit or root
AGENTS edit. Commit identity is reported in the delivery message.

Both reported discrepancies are confirmed. The reviewed package incorrectly
described A77F as RET and treated the A69F A-register return as the selector's
branch condition. Neither error was caught by the original fixtures, which
tested active-flight contact and the helper's A return but omitted warning
callbacks and the caller's flag-dependent selection. These gaps now have
original-Z80 regression coverage, beyond prose corrections.

- Bank1E CPU A77F / file7A77F: `CD 34 04` CALL0434, then C9 RET atA782.
  Warning state01 executes contact on every one of24 calls, stationary frames
  14/13 in4-call runs, repeated3 times. Extents4×16 give normal Sonic closed
  dx±12, dy−16..24. Attack cannot defeat/protect against it; hurt bit6 skips
  overlap; invulnerability and selector6 are handled by the next player hurt
  consumer. The scheduler/callback/consumer fixtures cover both parameters,
  all flag combinations, all24 calls and both warning-frame boundary boxes.
- A613 selects06 if unsigned playerY<bodyY OR (signed bodyVy>=0 AND bodyY==430);
  otherwise07. SBC/CARRY controls the first branch; helper BIT/SBC/Z controls
  the second. LD A and RET preserve Z. Exhaustive sweep:65536 playerY values
  ×3 body Y values429/430/431 ×3 velocity classes−1/0/+1 =589824 executions.
  State06 count134082; state07 count455742. Existing A-return floor/turn tests
  remain valid for callers that explicitly test A; do not change those to equality.
- State05 CALL035C enables shared5832 follow and disables pan, restores exclusive
  right3584, retains existing intro left limit, then tests WORLD3356+grounded.
  Camera precedes player and objects, so follow starts next update even while
  the clear gate is false. Working lead slews1 toward104/136 by facing; ±8
  deadzone; usual ±7 cap, exact−8 preserved; no player-speed cap. Both directions
  are possible. Limit overshoots are rejected, not clamped. Delayed full-game
  replay proves ±7 before clear. Intro-dependent left is2954 in main replay,
  2947 in delayed fixture; neither is a new fixed WORLD constant.

Counter/Y reconstruction:

- Full-game format2 records D12F at boundary and relevant callback phases,
  pre-driver state and post-physics state. `frame+96` is not a ROM rule.
  Actual main boundary offsets are188/237/252/253. IRQ0606 increments the
  counter; setup075A resets it. Reported14/256 offsets that complete a fight
  are fitted synthetic fixtures, not proof of matching the recorded update
  sequence. Use recorded phase counters instead.
- Boundary Y430 is driver input. Main post-player samples for that input include
  398/430/437; the usual resting platform value is398. Delayed-clear X3260
  settles414. A384..412 parking choice is legitimate only as a documented
  synthetic safe-position choice, not exact reconstruction or a ROM invariant.
- Additional PC breakpoints can alter approximate harness IRQ alignment: main
  replay now has546 rows rather than543. It still executes11 original hits,
  results/tally and AQZ1 progression. A separate delayed-gate replay records
  both camera directions. No controller-only replay or new visual claim is made.

Canonical changes:

- `tools/mghz56_reconciliation.py`: byte/disassembly, exhaustive selector,
  all24 scheduler warning contacts/consumer, geometry and camera/limit oracles.
- `tools/mghz56_runtime.py`: deterministic reconciliation cache/manifest
  integration; counter added to controlled scheduler samples.
- `tools/mghz56_fullgame.py`: phase-aware counter/player/camera/flag capture,
  delayed-gate camera replay, explicit fixture reconstruction metadata.
- `tests/test_mghz56_runtime.py`:8 additional regression tests (37 total).
- Regenerated `boss-56-runtime.json`, `boss-56-fullgame.json` and
  `boss-56-implementation-manifest.json` under `data/rom-cache/mghz/`.
- Updated canonical audit and marked initial package report superseded.

Verification: **37 boss tests; 159 MGHZ tests**. Counted generator assertions:
894975 runtime (including668374 reconciliation), plus8 full-game = **894983**.
Tests regenerate and compare runtime, manifest and full-game caches from the ROM.
Exact local ROM524288 bytes, SHA256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
Git whitespace check is part of final verification. No ROM, visual asset or
ignored build/debug file is added. Existing approved art is unchanged.

POC M4 implications: its reported warning contact and Z-driven selector already
match these corrected facts; no change to those reported behaviors is indicated.
The reported smooth right-only4px/player-speed camera remains an explicit adapter.
For256px canonical fidelity, use recovered shared bidirectional follow, rates,
limits and timing. Replay tests should consume phase-recorded counter/physics
values instead of fitted offsets or a parked-Y range. This assessment is based
on POC's report, not inspection or modification of its uncommitted implementation.

Unresolved: Manager review; Windows/original-game visual acceptance; explicit
widescreen camera adapter choice; exact controller-only replay timing under an
SMS-accurate IRQ/VDP harness. Existing state0A trigger and deferred shared results
presentation remain as documented. Separate monitor/contact and parked player
presentation defects remain outside this follow-up.

AGENTS candidate update: record the reviewed reconciliation checkpoint with
warning contact active all24 calls, flag-driven06/07 condition, and post-defeat
shared bidirectional camera follow. Treat full-game boundary player positions
as driver inputs; use recorded D12F/post-player phases for replay. Preserve
explicit widescreen adapters and the existing separate-defect scope boundary.
