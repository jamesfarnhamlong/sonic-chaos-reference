# MGHZ3 `$56/$57/$58` Research package — 2026-10-05

Branch `research/mghz3-boss-56`, based exactly on Research main
`7ba4d8a7bfb7f8164462fbf50db05c4b63cec0fe`. Research runtime dependency chain
closed for review/merge before POC consumption. Research main, POC and root
AGENTS are untouched. No merge is performed by this package.

Deliverables:

- `tools/mghz56_runtime.py`: verified-ROM scripts/metadata, controlled original
  Z80 tests and manifest generator.
- `tools/mghz56_fullgame.py`: original MGHZ3 loader through eleven actual boss
  hit entries, defeat, results/tally and AQZ1 load.
- `tools/mghz56_review.py`: compact PNG recap of already approved canonical
  art plus original 256 px harness screenshots; Pillow only for this renderer.
- `tests/test_mghz56_runtime.py`: 29 cache/original-ROM regression tests.
- `data/rom-cache/mghz/boss-56-runtime.json`, `boss-56-fullgame.json`,
  `boss-56-implementation-manifest.json`: regenerated/checkable canonical
  numeric metadata and trajectories, no ROM/pixel/audio dump.
- `docs/mghz3-boss-56-audit.md`: complete source addresses, state tables,
  ownership/update order, collision/damage, effects, clear path and adapter
  candidates. Foundation/census docs point to this newer closure.

Verification:

- **151 MGHZ tests passed**, including29 new boss tests. After final fixture
  corrections (canonical placement token12 and controller keep-alive flag),
  the29 boss tests passed again against regenerated final caches; other MGHZ
  runtime files/tools were unchanged.
- **226,601 counted runtime oracle/model assertions + 4 whole-game completion
  assertions = 226,605**, in addition to art/static hashes and unittest checks.
- Verified exact local ROM: 524,288 bytes, SHA-256
  `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
- Deterministic runtime/manifest/fullgame regeneration passed. Fullgame trace
  has543 update-boundary rows,11 damaging-hit entries and actual results/AQZ1 marks.
- All11 reachable nonblank body/child compositions match the already approved
  2026-10-04 foundation hashes. No new visual approval is required.
- Local review board: `build/mghz56-review/boss-56-review-board.png`, SHA-256
  `3ca39bbe4edec0483ce965c03f6bd8eb31cc3630b7b264439df918a5a0f990e6`.
- `git diff --check` clean. Build PNGs/debug traces stay ignored; no ROM,
  package ZIP, build debris or POC changes enter the commit.

Material findings for the POC reviewer:

- Canonical body anchor3269/288, camera target3061/256 (settled3060/256),
  strict PLAYER_DIST160/304 trigger. Preserve WORLD rise/fall288/430.
- HP byte10 requires **eleven top-classified attack hits** to underflowFF.
  Attack contact still bounces/sounds during the8-call HP lockout; hits do not
  select a dedicated reaction state. Nonvulnerable fall/recovery still has contact.
- Grounded contact from below invokes player death before attack handling.
  Boss contact bypasses the usual hurt-bit overlap skip through its own bit7.
- `$57/$58` projectiles have independent lifetimes and no controller owner link;
  warning phase24 calls is inert, then straight or three-way leftward motion.
  Preserve allocator pools, ascending-slot scheduling and allocation-failure skip.
- MGHZ defeat uses **WORLD(playerX)>=3356 AND floor bit1** before player20,
  bonus controller and smoke conversion; timer keeps running. Results advance AQZ1.
- Body uses full `$5FA0` projection/terrain/camera guards. That is a direct
  dependency to implement correctly for boss contact, not authorization to mix
  the separate POC shared monitor fix into this package.
- Art uses selector16, palette15, unmirrored shared mapping9861; flash restores
  palette entries13/14 to2A/15, not THZ35/20.

Unresolved/downstream:

- Width256 Windows/original-game comparison and optional widescreen arena/
  transient-projectile adapter choices. Baseline constants and candidate
  relationships are explicit; no widening is silently made canonical.
- State0A exists in the table, but no request to it is reached/proven from the
  audited init/combat chain. Preserve the definition without inventing a trigger.
- Full-fight evidence uses update-aligned synthetic attacks in the approximate
  SMS VDP/IRQ harness, not a controller-only replay.
- Existing deferred shared POC results graphics/audio remain downstream.
  No new unresolved gameplay dependency blocks the bounded boss implementation.

## AGENTS candidate updates

- Add this reviewed Research checkpoint and `docs/mghz3-boss-56-audit.md` /
  `data/rom-cache/mghz/boss-56-implementation-manifest.json` to canonical references
  after review/merge; replace “boss next Research package” with “POC implementation
  and width256/widescreen Windows acceptance next.”
- Record HP10/11 top-attack hits, 8-call HP-only lockout, grounded-below death,
  independent `$57/$58`, timer continuation, WORLD3356+floor clear gate and AQZ1.
- Preserve shared monitor/contact fix and parked slope/spring/facing defects as
  separate packages. Boss consumes complete canonical solid projection without
  changing that scope boundary.
