# Sonic Chaos — Enhanced Quality-of-Life Ideas

> **LATEST 13 NOV 2026: R20 IMPLEMENTATION GO.** R19 Chief all-four physical PASS; exact five Enhancement features and one default-OFF main Enhanced Options master flag actively commissioned in [R20 sprint](../R20_FIVE_ENHANCED_FEATURES_SINGLE_MASTER_FLAG_IMPLEMENTATION_20261113.md). Old individual ring-scatter flag below is superseded; Super Sonic post-finish.


> **CHIEF SCOPE DECISION 13 NOV 2026 — SUPERSEDES INDIVIDUAL-TOGGLE BACKLOG:** The final Enhanced upgrade phase is **exactly FIVE owner-selected features** behind **ONE `Enhanced Features: OFF/ON` master switch under main Enhanced Options**, default OFF, persisted and Classic ignored. Approved: Sonic1 Mega Drive loss/scatter, boss face+pips HUD, boss music priority after invincibility, Spring Shoes top-hit boss (Chief called SLZ; verify runtime stage/boss), Speed Shoes music speedup. Full binding scope: [Chief five-feature decision](../CHIEF_ENHANCED_FEATURES_FINAL_SCOPE_AND_SUPER_SONIC_PARKING_20261113.md). Prior proposal to give ring loss its OWN standalone toggle, and old “2–3 features” limit, are historical and superseded. No implementation during R19. **Super Sonic desired but separate optional post-finish asset/mechanics work.** Other ideas below are PARKED, NOT additional approved flags.

**Opened 5 November 2026 · Chief-originated optional enhancements · no source change authorized**

## Design rule
This is separate from [Post-Freeze Classic Defects](POST_FREEZE_CLASSIC_DEFECTS.md). Classic's approved ROM-faithful gameplay stays the reference; optional behavior changes must operate only through the single unified **Enhanced** mode/feature registry, with deliberate user On/Off controls when appropriate. Preserve original frozen tag `classic-core-20261105` at `3a58912659b48573ac7f2c5c96a02a2211d5e4da`. Do not mislabel original behavior as a bug. E0 has an *empty* feature registry until separate Chief approval of an actual feature.

## Active proposals

### ENH-QOL-001 — Richer, 16-bit-inspired ring loss / scattered ring recovery

| Field | Entry |
|---|---|
| **Chief's idea** | On taking damage, scatter **more recoverable rings**, with greater randomness/variation and fuller onscreen spread, evocative of 16-bit Sonic rather than original SMS scarcity. |
| **Status** | **BACKLOG — research/tuning only; no implementation commissioned** |
| **Mode** | Enhanced-only, proposed user-facing On/Off option (`Enhanced Ring Scatter` or similar). **Off/effectively absent in Classic.** |
| **Priority** | Gameplay feel/QoL; schedule after E0 accepted and initial 60 FPS/display research unless Chief reprioritizes. |
| **Owner acceptance** | Chief chooses an enjoyable visual/recapture balance and checks short damage/collect cases. |

### Important correction to the starting assumption
Chief observed typical low-count losses that show **one or two** rings, and suggested that SMS can only display 1–2. The existing frozen GameMaker implementation, however, explicitly reproduces original research: the **scattered count is `min(7, floor(rings/10)+1)` for 1–99 rings** (0 if no rings), **up to seven**, not a universal 1–2 limit. Examples: 9 rings → 1, 13 → 2, 32 → 4, 47 → 5, 64 → 7. Source: `SonicChaos_POC/docs/lost-ring-scatter.md` and `scripts/SCR_chaos_lost_ring/SCR_chaos_lost_ring.gml` at the frozen D commit. The existing separate pool limit is 16 active dropped rings, not a current 16-ring scatter burst. The 256 vs wide retention and recapture rules are already accepted Classic adaptations; don't erase them.

### Investigation / potential Enhanced contract
1. Consider a 16-bit-inspired scatter count tied to rings actually carried, with an owner-selected bounded maximum (research 16–32 as candidate limits, **not an approved number**). This will require explicit decisions about the current 16-token live-ring pool and active-object density. More particles must not imply 16-bit ROM parity.
2. Vary launch angles and velocities via **seeded, reproducible** pseudo-random spread (or authored balanced patterns plus seeded variations), avoiding repeated identical seven-token shapes. Distribute across both left/right and upward arcs without trapping recoverable rings inside impassable walls.
3. Preserve fair temporary pickup lockout, bounce/recollection opportunity and original-like Ring animation/sounds. Study vertical and horizontal off-screen retention to avoid visually disappearing recoverable rings or excessive long-lived objects.
4. Keep physics/collision and frame cadence of player/enemies unchanged. The opt-in Enhanced adapter should own only scatter quantity/trajectory/lifecycle and have deterministic comparison with Classic Off; avoid modifying accepted Classic source or importing unrelated Sonic 16-bit sprites.
5. Benchmark crowded zones/boss arenas and both 256 control and 348 widescreen to bound visual clutter, performance and sound request storms. Test ring counts 0,1,9,10,13,32,47,64,99 and repeated hits; confirm Classic hashes/behavior untouched.

**Deliverable when commissioned:** short design with prototype tuning table, screenshots/recordings, source-to-baseline delta, one meaningful Chief comparison. No global physics refactor or full campaign required.

## Other currently parked Enhanced QoL candidates (not approved fixes)
- MGHZ falling-coconut/Spring Shoes damage and activation rules; only alter by explicit toggle if Chief wants noncanonical protection/activation. Existing ROM behavior was correctly preserved.
- SEZ Spring Shoes/pogo boss freedom; first confirm exact stage/object (Chief previously mentioned `SLZ`, not automatically assumed to be a known zone), and design Enhanced-only alternative.
- AQZ boss-theme restoration on invincibility expiry (original ROM can revert to zone theme; preserving it in Classic was Chief's express decision).
- THZ3 spike sound masking by jump SFX priority: if desired, an Enhanced audio-priority preference, not a Classic fidelity fix.
- Options for modern display and control comfort, distinct from gameplay QoL, are managed by [Enhancements Roadmap](../ENHANCEMENTS_ROADMAP_20261105.md).

## New proposals
Append ENH-QOL-002 etc. with Chief's intended player benefit, original-ROM behavior, on/off/mode ownership, performance and sound implications, deterministic criteria and acceptance. Avoid uncontrolled proliferation of overlapping feature flags.
