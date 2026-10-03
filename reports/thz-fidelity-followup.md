# THZ fidelity follow-up — findings for review

Research only, based on Research main `bbcef38`, on branch
`research/thz-fidelity-followup`. POC was inspected read-only. Canonical
documentation, caches, type-$27 gameplay findings and root AGENTS.md are unchanged.
The POC comparison is against accepted HEAD
`42aaa5032cef385284a00d0c1b7a0e7714747b4b`; the same relevant code/assets are
present in the active checkout, which also contains unrelated GPZ work.

Verified local ROM: Sonic Chaos (Europe) v1.2, SHA-256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
Machine-readable evidence: `reports/thz-fidelity-followup.json`.
Reproducer: `tools/thz_fidelity_followup.py`. Tests:
`tests/test_thz_fidelity_followup.py`. Generated graphics stay in ignored `build/`.

## A. Type $27 graphics: diagnosis 3, POC draw assembly

**Research's extracted mapping and tile data are correct. Its normal-coordinate
preview is composed correctly for that coordinate stream, but is not a faithful
placed-bee preview. The POC imports that preview intact, then flips the whole
bitmap. That is not the original renderer's operation for this object.**

The three THZ1 placements set bit 4 and both art bases to `$AA`. The animation
scripts in bank `$1E`, `$8947` (file `$78947`) use blank mapping 0 at initialization
and mappings 1/2 at two-update record durations in states 1/2/3. The report
includes every existing decoded animation record/control command; no animation,
movement, trigger or lifetime finding has changed.

Visual data path:

| Field | Original data / behavior |
|---|---|
| Type pointer | bank `$0F`, `$804E`, file `$3C04E`, points to `$91F5` |
| Mapping table | bank `$0F:$91F5`, file `$3D1F5`; 0 shared blank `$A0E4`, 1 `$91FB`, 2 `$9206` |
| Frame records | 1 file `$3D1FB`, 2 file `$3D206`; **three 8×16 pieces** each |
| Count / extent word | count 3; `$0E09` is collision extents 9/14, not flip/palette/priority bits |
| Origins | signed X=0, Y=0 on both visible frames |
| Coordinate table | `$0F:$A26B`, file `$3E26B`; normal X `[-12,-4,+4]`, Y `[-16,-16,-16]` |
| Mirrored X stream | selected with coordinate pointer +`$0D08` by `$22B6`; X `[+4,-4,-12]`; Y unchanged |
| Tile-offset lists | frame 1 `$9211` / file `$3D211`: `[0,2,4]`; frame 2 `$9214` / file `$3D214`: `[6,8,4]` |
| Art selection | bit 4 selects `+$09`; otherwise `+$08`; **both are `$AA`**, so orientation does not select different tile pixels here |
| SAT tile bytes | frame 1 `[$AA,$AC,$AE]`; frame 2 `[$B0,$B2,$AE]` in both orientations |
| Tile patterns | 8×16 pairs AA/AB, AC/AD, AE/AF; B0/B1, B2/B3, AE/AF; all starts even |
| Graphics load | bank-byte `$89`, bank `$09:$95A0`, file `$255A0`, 10 tiles to VRAM `$1540` |
| Load transform | all tile bytes bit-reversed through ROM `$0100..$01FF`; all 256 lookup entries checked |
| Palette | THZ sprite selector 6, bank `$0E:$B6AD`, file `$3B6AD`; CRAM sprite half, index 0 transparent |
| Attributes | SMS sprite SAT has no per-piece X/Y flip, palette selector or priority attribute; these are not background tile words |
| Priority | SAT order controls sprite overlaps; background priority is the separate VDP/background mechanism; no invented mapping priority field |

The SMS renderer reverses the **piece X positions**, not the pixel rows within
each piece. The art load has already reversed those pixels. Whole-bitmap flipping
reverses piece placement *and* reverses each piece's pixels a second time. With
the pre-mirrored art, that gives the wrong head, centre, nozzle and flame assembly.
Removing `image_xscale=-1` alone would leave the piece order wrong as well.

Evidence:

- Original `$226A/$22B6` executed for both frames and both orientation flags.
  Its emitted SAT exactly matches independently decoded signed coordinates,
  tile offsets and base selection in all four cases.
- All 320 bee-art VRAM bytes from the original game boot match Research's
  decompression/remap output byte for byte. Runtime VDP R1=`$E2`, R6=`$FB`:
  8×16 sprites, pattern base 0. The low bit of an 8×16 SAT tile number is ignored;
  all actual bee tile numbers are even, so it cannot explain this discrepancy.
- Both imported POC frames match Research's normal preview with **zero visible
  pixel differences**. Their registered `image_xscale=-1` draws differ from the
  original mirrored SAT composition at **198 / 202 pixels** respectively.
- POC `Create_0.gml` sets `image_xscale=-1`; `Draw_0.gml` passes it unchanged to
  `draw_sprite_ext`. Resource origin `(16,20)` and the accepted +18 Y registration
  are preserved in the comparison. This is a composition error, not a reason to
  move canonical anchors or tune the existing vertical registration.

The original registration remains `screen=world-camera` (`$3FC8`), signed mapping
origin/piece offsets (`$226A/$22B6`), then SAT Y+1. Relative to scrolling terrain,
the previously recovered shared relationship is +1 X / +18 Y. The fixture uses
the accepted POC X registration for a like-for-like composition comparison; it
does not re-audit its one-pixel horizontal presentation policy.

Local sheet: `build/thz-fidelity-followup/bee-contact-sheet.png`. Rows are mappings
1/2; columns are Research normal preview, current POC draw, original mirrored SAT.
Grey background reveals the opaque black centre. The sheet is normalized to the
common anchor/terrain Y registration and excludes scanline clipping/background
occlusion. It is not a captured hardware screenshot.

Recommended POC handoff, after review: export the canonical mirrored SAT
composition using the existing `$AA` VRAM pixels, register it at the recovered
origin, and draw it without a second pixel flip. Keep this as a graphics/import
change; no `$27` gameplay changes are supported.

## B. Grounded roll: rebound rule upheld; POC changes flags incorrectly

**Grounded rolling Sonic can and does reach `$8105` carrying +7.0 Y velocity.
Terrain projection does not normalize it to zero. The original does negate it
to -7.0, but preserves grounded flags, so the next player update does not turn
that value into an aerial launch.**

Update-aligned setup uses the existing original-game THZ3 harness, with its act
selection boot patch. All approach setup writes occur at `$1336`. Once fighting
state 6 is reached, one approach state/position/velocity is supplied; subsequent
player updates, terrain, boss contact and rebound run freely, with no player
parking or per-update velocity writes. The boss enters and runs its own real
state machine. Setup values and all retained update rows are in the report.
These are controlled original-update trajectories, not a claim to reconstruct
the exact unseen hardware video's inputs.

Hooks record `$3FEF` player update, `$4097` vertical movement, `$690B` terrain
entry, `$64CB` contact merge, `$99AE` boss helper, **actual PC `$8105`**, and
`$99E0` immediately after the helper. Top goes through `$480C` instead.
Code-region hashes and bank/file addresses are recorded separately.

### Actual call boundaries

Velocities below are exact signed 8.8 integers; divide by 256 for pixels/update.
Coordinates are gameplay anchors, after the shared solid projection.

| Approach | Update | Current/requested | D503 / D522 | Player; boss | Contact | Incoming vx,vy | Result vx,vy; requested |
|---|---:|---|---|---|---|---|---|
| Grounded roll from left | 9 | 9 / 9 | `$02` / `$02` | `(1869,238)`; `(1897,238)` | `$08`, left side | `979,1792` | `-1536,-1792`; `$1B` |
| Descending airborne from left | 1 | `$0A` / `$0A` | `$03` / `$00` | `(1873,214)`; `(1901,238)` | `$08`, left side | `1008,864` | `-1536,-864`; `$1B` |
| Rising airborne from left | 1 | `$0A` / `$0A` | `$03` / `$00` | `(1873,202)`; `(1901,238)` | `$08`, left side | `1008,-672` | `-1536,672`; `$1B` |
| Exact top rim | 0 | `$0A` / `$0A` | `$03` / `$00` | `(1901,190)`; `(1901,238)` | `$01`, top | `0,48` | `0,-1024`; `$0B`, flags `$01`, floor `$00` |

Side hits preserve current state, D503 and D522; only requested state changes.
Top never reaches `$8105` in fighting state: `$480C` performs its separate
non-rising -4.0 bounce and clears attack/floor. The exact top fixture initially
starts at dy=-48 with vy=0; ordinary gravity adds `$30`, and the integer anchor
is still at dy=-48 after shared solid projection, before the top setter. The next boundary captures
requested `$0B`, vy=-1024 and flags/floor 1/0.

### Grounded rolling trace around the hit

On hit update 9:

1. Vertical movement starts at Y238, floor bit set; `$410B` forces vy=`$0700`.
2. `$4124` stores that velocity and integration moves Y to245.
3. Floor projection `$6F61` restores Y238, sets floor, and does **not** clear vy.
4. `$99AE -> $5FA0` chooses side contact at dx=-28,dy=0. It does not change speed.
5. At actual `$8105`: current/requested9/9, flags2, floor2, vx979, vy1792.
6. After `$8105`: vx=-1536, vy=-1792, request27; **flags2, floor2 preserved**.

On update10, requested27 has promoted. `$4097` sees grounded movement; its
grounded negative-speed path takes the magnitude. `$410B` again forces +7.0
because floor remains set. Integration reaches Y245 and terrain projects to238.
The subsequent freely executed rows stay at Y238; there is no sustained ascent.
The negative velocity existed at the hit boundary, but not as an airborne impulse.

This is not a missing pre-contact velocity reset. Resetting incoming vy to zero
would contradict the original update trace.

### Read-only POC cause

Accepted POC `scripts/SCR_chaos_boss/SCR_chaos_boss.gml`, in the damaging branch:

```gml
cp_c.next=27; cp_c.move|=3; cp_c.bg &= ~2; cp_c.contacts &= ~2;
```

That extra mutation sets airborne and removes floor/support contact despite the
previously recovered `$8105` preservation rule. `git show HEAD:...` confirms it
is present in accepted `42aaa503`, not just the unrelated GPZ working changes.
It converts the negated grounded +7.0 into a lasting -7.0 aerial velocity.

A flag-only control executes original `$4097` from state27, Y238, vy=-1792:

| Flags/floor | Next vy | Integrated Y before terrain |
|---|---:|---:|
| Original preserved `$02/$02` | +1792 (+7.0) |245 |
| POC-mutated `$03/$00` | -1756 (-6.859375) |231 |

Only flags differ. Thus the high-launch mechanism is explained without changing
the recovered rebound strength, contact timing or side/top geometry. Airborne
descending contact legitimately retains an upward rebound; rising side contact
legitimately reverses downward. Do not globally suppress either.

An original `$4097` boundary sweep covers 6,144 cases: every signed velocity high
byte with low bytes00/FF, states9/27, flags2/3, floor bit set, modifiers0/0A/0C.
Zero mismatches: floor forces +7 normally, +9 for modifiers0A/0C. This isolated
sweep does not replace the whole-update terrain/contact evidence above.

Recommended POC handoff, after review: preserve the player flags/floor in the
damaging side/below response exactly as `$8105` does; verify the following
grounded state27 update keeps the floor override/projection. Keep the separate
top bounce semantics. No empirical velocity cap or pre-contact zeroing is supported.

## Validation and limits

Reproduction (local graphics remain under ignored `build/`):

```powershell
.venv/Scripts/python.exe tools/thz_fidelity_followup.py '../source/Sonic Chaos (Europe).sms' --check
.venv/Scripts/python.exe -m unittest discover -s tests -p test_thz_fidelity_followup.py -v
```

Six focused tests cover original-VRAM equality, exact SAT pieces, imported-preview
equality versus incorrect POC draw, actual grounded hit/next-update behavior,
airborne/top distinctions, velocity boundary sweep/flag control, and complete
byte-identical report replay from the verified local ROM.

Validation: all **25 tests pass**, no skips (6 new diagnostic tests, 3 existing
type-$27 tests, 16 existing boss-contact follow-up tests including its ROM replay).
The new 6,144-case sweep has zero mismatches. `git diff --check` passes. No ROM,
PNG, binary graphics dump or POC file is included in the checkpoint.

The approximate SMS harness is not cycle-exact hardware, and no hardware video
was attached for frame synchronization. The GameMaker diagnosis is source/asset
inspection plus original-code controls; no POC edit, build or Windows acceptance
was performed. Bee behavior/lifecycle/collision/trigger and boss response rules
remain unchanged. No canonical documentation was rewritten before review.

**AGENTS candidate updates: none.** Existing accepted ROM facts did not change;
the newly traced grounded continuation reinforces the already documented
preservation rule. Manager may reference this diagnostic report without
replacing that rule or adding a speculative velocity normalization rule.
