# GPZ3 `$51` boss/support assets — approved art audit

ROM/version/base/provenance are the same as `gpz-enemy-audit.md`.
The package closes the sprite/support extraction scope and statically traces the
21-state script graph. It does **not** certify the boss's complete gameplay,
arena/contact/damage/clear behavior for implementation. A bounded runtime/oracle
pass is still required before a boss rollout. Regular enemy implementation may
be scheduled independently after PNG approval and canonical review.

## Placement, controller and linked composition

**Decoded data:** one mapped `$51/$00` record at `(1728,270)`, bank
`$1C:$8DF6`, file `$70DF6`; raw record retained in the manifest.
Type-table file `$665A` selects bank `$1E:$9A3A` (file `$79A3A`), 21 states.
Mapping bank `$0F` contains 12 frame entries: blank 0 plus visible 1..11.

**Source-traced behavior:** parameter 0 initialization `$9A99` caps camera X at
`$680`, moves the runtime parent X to `$740` (1856), requests boss music `$8C`,
and selects mode/timing fields from the player's Y low byte. This is an explicit
runtime move; canonical placement remains 1728. Nonzero child parameters bypass
that controller setup and `$9AE0` requests `parameter+1`.

**Correction:** the rejected board reversed the vertical link, assigned the head
to parameter1 instead of parameter0, and forced the conditional fourth ball.
Its assembly was wrong. The replacement follows the original `$5DD1` scheduler,
allocator, scripts and callbacks; see `gpz3-boss-composition-correction.md` and
`data/rom-cache/gpz/boss-51-composition.json` for complete evidence.

Normal modes0/1 form four linked objects, top to bottom: `$51/$00` head (state7,
frame2), `$51/$01`, `$51/$02`, `$51/$03` balls (state6, frames3..9). Mode2 adds
`$51/$04` at the bottom. `$9B91` bypasses the fourth spawn in modes0/1.
`$A141` writes the new lower child into the upper object's `+$34` pointer;
the lower child's `+$36` points upward. `$9E4B` makes each upper object follow
its lower support using signed offsets at `$1E:$A154` and
`(mainPhase + parameter) & 31`. The lower ball supports the whole stack.

## Art, palette, frames and mirror exclusion

**Source-traced + decoded data:** callback `$9B37` sets dynamic selector `$14`
and sprite-palette command index `$0D` via `$D494/$D495`.

| Load | File / bank:CPU | Destination | Count | Use |
|---|---|---|---:|---|
| Boss art | `$29280` / `$0A:$9280` | VRAM `$05C0`, tile `$2E` | 104 tiles | `$51` frames1..11 |
| Puff art | `$26BA0` / `$09:$ABA0` | VRAM `$12C0`, tile `$96` | 12 tiles | `$34` frames1..4 |
| Sprite palette | `$3B71D` | palette `$0D` | 16 colors | boss + active effects |

Selector `$14`'s list is CPU/file `$7BEB`; neither load requests transformed art.
Do not reuse THZ selector `$13`, palette `$0C`, THZ puff base `$A2`, or its mirrored
boss stream. Normal boss art bases are 0/0 inherited from the mapped record and
dynamic allocator; mapping tile offsets address the loaded patterns directly.

Frames1/2 are the head; frames3..9 are segment rotation/presentation; frames10/11
are landing dust, now **scheduler-observed** on `$51/$11` children in state18.
Floor callback `$9F14` installs inline tail `$9C0F`, spawning parameter `$11`;
the initializer requests parameter+1 (state18). These frames are canonical
runtime candidates, approved with the corrected `$51` package on 2026-10-03. Frame1 has the
source-traced head-hit path; frame2 and3..11 are observed in scheduler replay.
States11/15 and19/20 use frames3..9 at two-update
record timing; state6 uses four-update timing. The cache retains every state,
duration, callback, velocity command and child/effect spawn.

Runtime `$51` uses bit4=0. Forced bit4=1 changes coordinate registration but has
no matching reversed graphics copy, visibly splitting the head/segments.
Those PNGs are **unused diagnostics, excluded from import candidates**. They are
not a second facing animation to approve. The same exclusion applies to forced
mirrors of puff/poof/sparkle support. Shared registration remains (+1,+18) in
terrain space, separate from gameplay anchors and collision extents.

## Required support and behavior gates

| Type / component | Source of use | Art needed | Status |
|---|---|---|---|
| `$51` parameters1..3 (+4 in mode2) | states1..4, `$9B91` gate, `$A141` linkage | balls3..9; head belongs to parameter0 | Required; scheduler-captured composition |
| `$12` | state0 calls `$81A6` | existing HUD SAT sprites, no new standalone bitmap | HUD slide controller; prior shared audit applies |
| `$34` parameters8/4 | states14/17 explicit spawns | frames1..4, GPZ zone-table art base `$96` | Required explosion puffs |
| `$0A` parameter0 | `$9D4E..$9D55` creates type10 then initializer vector `$03F5` | sparkle frames5/6, base0 | Post-boss bonus/sparkle chain, source-traced |
| `$0F` parameter0 | regular enemy shared conversion `$5F54` | smoke frames7/8/9, base0 | Required for ordinary enemy defeat; not asserted as a `$51` child |
| `$51/$11` state18 | floor tail `$9C0F`, init `$9AE0` | dust10/11 | Required landing child, runtime observed; deletes through `$9DB9` |

The `$34` initializer uses zone table bank `$1E:$8C98` (GPZ entry1=$96), clears
flags, picks the state1/2 sequence by update parity, and retains the parameter as
its delay/counter. Both sequence timings are in the cache. `$12` manipulates the
existing 12 HUD SAT Y bytes and uses blank frame0; inventing a new HUD sprite
for it would be incorrect. Its shared timed slide behavior is already covered
by `thz3-boss-support-audit.md`.

Ordinary GPZ `$0F` uses the level sprite palette7. Boss effects use active
palette13. Frames7..9 use indices 0/7/10/11; their decoded RGBA colors are
identical under palettes7 and13, checked in the cache, so the smoke sheet
also represents regular GPZ defeat. Final renderer code must consume current
CRAM, not a fixed THZ palette.
Audio requests are numeric facts only; no audio samples are extracted here.
Results-screen assets remain outside this batch and no substitutes are created.

The source trace reveals contact paths that differ by state/segment: state7
can request13 and apply player Y=-4 on attacking contact; `$A0F5` multiplexes
segment collision and applies ±4 X with sound `$AB`; `$A0E6` writes `$D3B0=$FF`
for damaging overlap in detached motion. These are **source traces, not a complete
contact specification**. Do not copy THZ boss contact, vulnerability, eight-hit
health, knockback, cooldown, world clamps or completion timing into `$51`.
Full contact/health/arena/clear boundary sweeps and the `$9D26` floor-gated clear
handoff remain rollout work. Linked-slot composition, low-byte mode selection,
bottom-up detachment and regrowth now have focused original-scheduler coverage.

## Verification and limits

The raw tile decoder preserves SMS palette indices and 8x16 even-tile selection.
Every frame/orientation is executed through the original frame selector,
screen-coordinate preparation and SAT X/Y renderer and compared with the
independent registration model. PNG composition respects first-piece priority.
Code-region instruction traces come from reachable instruction control flow,
not linear disassembly of animation data; offsets and hashes are cached.

These checks establish source/mapping consistency. They cannot prove that a
palette, complete pose or visual direction looks correct to James. Human PNG
approval was granted for corrected `$51` on 2026-10-03. `$25`, `$2C` and
support-effect approvals remain unchanged. Research commit/push is authorized;
POC remains untouched and main integration is a separate step.
