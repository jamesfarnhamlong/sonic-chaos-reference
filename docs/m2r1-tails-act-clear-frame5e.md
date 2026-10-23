# M2-R1 — Tails act-clear frame $5E

23 October 2026. Research branch `research/m2r1-tails-frame5e`, parent `5b7f5a10232f4f6511c3a7b9d9b4deaea5842182`. Accepted POC `7476affc6ed7626dabf69b446cdab0c9c3d7492e` read-only. Canonical SMS Europe v1.2 ROM hash `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607` verified before execution.

## Decision

**UNRESOLVED: natural reachability of the bad Tails run-off branch.** The pointer interpretation and forced original behaviour are established: frame `$5E` really reads resident code at `$0785` as a mapping, and original-code execution with forced side contact corrupts the display. It is **not** a legitimate missing image, a blank mapping, or an automatic previous-frame-retention rule. Do not extract a new Tails `$5E` sprite or substitute Sonic/push artwork.

Three arrival-seeded original sign-chain runs reached state `$20` and completed with clear side bits; none reached `$5E`. These are not input-only full-stage playthroughs. The original sign and THZ3 boss completion gates require floor contact but do not themselves exclude side contact. Controlled boss-gate execution permits a state-$20 request with the side bits retained. That does not demonstrate a naturally reached boss defeat or prove an original-game bug during ordinary play. **Do not label this PROVEN UNREACHABLE.**

M2's blocker `M2-TAILS-ACTCLEAR-SIDE-MAPPING` therefore remains OPEN. Other M2 preflight work may be reviewed separately; full act-clear animation parity is not established. A deliberate guard/exception needs Manager approval before runtime edits.

## Inputs and boundaries

Read M1 census and decoder, `docs/object-18-act-clear.md`, `docs/object-50.md`, existing act-clear fixtures and recovered animation/render/contact source. Also read the accessible, uncommitted Designer `SonicChaos_POC_m2/docs/m2-preflight.md` and its metadata-only `verification/m2/preflight.json`. Designer's four expanded side-contact counterexamples were reproduced independently here. The other M2 preflight/ending/asset claims remain Designer-reported; this task does not re-accept them or amend that worktree.

The new evidence is original Z80 routine execution and original whole-game code driving the repository's **approximate** SMS VDP harness. It is not GameMaker, hardware, or an independently cycle-exact emulator. RAM fixtures are explicit below; no original ROM bytes were modified. Captured PNGs remain ignored under `build/m2r1/`; public evidence contains only decoded addresses/instructions, numeric observations and hashes, no ROM, sprite, screenshot or WAV payload.

## 1. Exact pointer interpretation

| Step | Original address / calculation | Observed result |
|---|---|---|
| State script | type2 bank `$0C`, table `$89BB`, state `$20` → `$8C39` | `FF05` selector `$8EE1`, callback `$83A6`; then restart. This differs in script location from Sonic `$839E` but uses the same two routines. |
| Selector predicate | `$8EE1..$8EE6`: read player+$23, AND `$0C`, branch nonzero to `$8F3C` | Either bit2 or bit3 suffices. Floor, strip marker, type and held keys are not tested before this branch. |
| Selected record | `$8F3C..$8F44` | Writes frame `$5E` and duration2; returns without advancing shared selector index `$D52F`. |
| Mapping bank | `$6562..$6573` | Maps bank `$0F`; type2 indexes word at `$8000+2*2=$8004`, yielding table base `$85BF`. |
| Frame arithmetic | `$6574..$657D` | Zero-extended byte frame, doubled as a word: `$85BF+2*$5E=$867B`. No table-length test, clamp or character fallback. |
| Pointer read | bank15 CPU `$867B/$867C`, ROM offsets `$3C67B/$3C67C` | Word `$0785`. The CPU consumes it; it is not merely a decoder prediction. |
| Effective target | `$657E/$657F` exchanges pointer into HL and reads `(HL)` | Slots observed `[0,1,15]`: `$0785` is in resident bank0, ROM offset `$00785`, **not** bank15 `$8785`. No bank-relative rebasing is performed. |

M1's 89 identified mapping entries `$00..$58` remain correct as the authored contiguous pointer census. Its stopping heuristic rejects later words as mapping pointers; the original engine has no corresponding bounds check. The would-be `$5E` entry lies inside following data. The correct resolution is not to expand the authored census through that data.

More precisely, M1 identifies Tails frame1's record at bank15 `$8671` and frame2's at `$867C`. The word at `$867B` straddles the end of frame1's record and frame2's first byte (piece count7). This explains how `$0785` arises without an authored frame94 pointer. It is an out-of-table read of real adjacent data, followed by an actual low-address dereference.

At resident `$0785` the title blink routine contains `AND $20`, followed by a conditional jump and an `LD DE` instruction. Interpreting those instruction operands as a mapping header produces, by original `$657F..$65AB` execution:

- piece count `$E6` = **230**;
- collision extent bytes `$20,$28` = **32,40**;
- piece-data pointer `$1103`;
- origin-data pointer `$078A`.

These values overwrite the object's mapping fields. They are neither a valid type2 pose nor zero pieces. A host decoder which rejects pointers outside `$8000..$BFFF` is correctly rejecting an authored-resource import, but must not describe that rejection as original CPU bounds enforcement.

Separate visibility controls still apply: original `$6580..$6590` suppresses the piece count when object+$04 bit3 is set. Two additional original-engine controls give count230 at flags0 and count0 at flags8, both still selecting94 and reading the malformed pointers. Offscreen/hide policies can also prevent drawing. Thus “not a blank mapping” describes the data/ordinary visible case, not a claim that every flag combination must show corruption; visibility suppression does not supply an authored blank `$5E` pose.

There is a second out-of-range read. IRQ tile transfer `$0D15..$0D42` uses the frame shadow, chooses Tails' fixed table `$11CF`, and reads `$11CF+4*$5E=$1347`. Original execution observes mapper byte19, source CPU `$DA07`, block count `$AE`=174 (11,136 bytes). `$DA07` is RAM, so bank19 does not turn it into a normal ROM tile source; a long sequential CPU read also crosses the address wrap. This is not an authenticated sprite tile transfer. Normal Sonic `$5E` instead uses bank7 source `$B640`, six64-byte blocks (384 bytes).

## 2. Update order, predicate and reachability

Player `$361D` selects bank12 and runs animation engine `$64FA` first. On a new state or expired record it executes `FF05` through `$67A1..$67C0`, installs callback `$83A6`, runs the selector and immediately decodes the selected mapping in bank15. Only afterward does `$3643..$364D` restore bank12 and dispatch the callback. During an unexpired record, the counter decrements and mapping selection is held; side contact is not re-evaluated until a record reload. The ordinary “hold last mapping until reload” behaviour is distinct from inventing retention for invalid `$5E`.

The relevant contact byte is **prior to the current callback**. Ordinary terrain processing merges background/object contact into +$23 through `$64CB`. State `$20`'s callback has no terrain/contact refresh and does not clear +$23. Its helper `$0407→$59B9` changes camera ownership/left bound, not contacts. Therefore one cannot assume current movement will clear a stale side bit before animation selection.

| Reachability layer | Evidence / result | What remains unproven |
|---|---|---|
| Engine predicate |16 original engine controls: Sonic/Tails × +$23 values0,1,2,4,8,12,16,255. Every side case selects94/duration2; non-side controls select ordinary frame2. | These explicitly force a valid engine state and contacts. Not natural play. |
| Shared completion setter |12 controls: act indices0/1/2 × contacts2/6/10/14; original `$4892` requests32 and `$89/$97`, preserving +$23. | No gameplay reachability of the synthetic contact tuple is implied. |
| Sign child | bank12 `$AB8C..$AB9E`: skip if already20; helper `$037D`; require **background** `$D522` bit1; call `$03F5→$4892`. No side exclusion. | The floor test is on a different byte and is not a proof that +$23 &12 is zero. |
| THZ3 boss completion | bank30 `$81BD..$8212`, type `$50`; eight controlled calls with background0/2 × contacts2/6/10/14. No floor: no state20. Floor: state20 requested, boss converts to type0F, side bits preserved. | A forced terminal callback is not a natural fight/defeat. Other boss encounter routes were not newly run. EEZ terminal ending is not an ordinary state20 exit. |
| THZ1 normal sign control | Actual Tails title selection; ARRIVAL player/camera near mapped sign; Right until state20. Original sign/prize/child/handoff runs without state/contact injection.30 state20 updates, all contact2; next act reached. | Arrival is seeded. Not input-only THZ1 traversal or every approach. |
| THZ1 and THZ2 backtracking | Same original chain; after mapped sign is touched, held Left before state20.94 state20 updates each, all contact2; next acts reached. | Only these two deterministic backtracking routes. Not proof for every obstacle, object slot, approach/state or zone. |
| Input-only full act / natural boss defeat | **NOT RUN in M2-R1.** | Natural bad-branch reachability remains unresolved; no universal exclusion theorem was derived from scene data. |

The sign sessions seed only original act entry/arrival position and camera, then use input; state20 and contacts are never forced in them. They establish real sign-chain behaviour after that fixture. The boss routine controls are a separate, stronger fixture. Neither category may be called a natural campaign observation.

## 3. What the forced original branch renders

Three matched whole-game controls boot through the original title/character choice, settle90 frames, then force current=requested state20 with a zero script cursor at one player-engine entry. Tails clear-side, Tails side4 and Sonic side4 use the same THZ1 position/camera. Current=requested is required for this zero-cursor engine fixture; a preliminary incorrect FF-current sentinel trial was discarded. The finished controls assert the expected selector/callback and mapping read, so a fixture reset cannot masquerade as a blank-frame result.

| Control | Original engine/render result over64 harness frames |
|---|---|
| Tails, side0 |63 player/callback passes; genuine frames1..6, valid mapping counts. Normal scene/Tails raster. |
| Sonic, side4 |63 passes, frame94, valid six-piece mapping at bank15 `$858B`. Normal scene and Sonic pushing pose. This is comparison evidence only, not Tails art authority. |
| Tails, side4 |First mapping read is `$0785`, frame94/count230. One player/callback pass observed in the bounded window, malformed large tile transfer at frame1049; subsequent captures show corrupted scene/vertical pixel stripes and no normal continued run-off. |

Sampled raw RGB, PNG, VRAM, tile-region and SAT-shadow hashes plus sampled CPU/bank state are in `data/m2r1/frame5e-evidence.json`. Private images `build/m2r1/tails-side-07.png` and `...-63.png` were visually inspected against the clear/Sonic controls. Original code generated the corrupt images; none is a frame to import. The renderer writes mapping-derived data into the normal SAT staging buffers and the tile loader overwrites a much larger VRAM region than a player frame. Do not infer a portable authored image from a screenshot of this RAM-dependent corruption.

The bounded harness slowdown/loss of callback progression is recorded, **not** promoted to a hardware crash diagnosis or an invariant outcome for all RAM/IRQ phases. Accurate overflow/mid-line effects and real-console behaviour are outside this harness. Nevertheless the actual pointer/header/transfer reads disprove a valid authored `$5E` pose, blank mapping or implicit previous-frame preservation.

## 4. Minimal Designer contract and isolation decision

**Unambiguous original selection/progression rule:** retain the shared `$8EE1` selector for type2 state20, with callback `$83A6`; do not replace it with Tails' ordinary walk selector `$8CB4`. Evaluate side first at record reload. Side → numeric94, counter2, unchanged `$D52F`. Clear side → existing shared ordinary/strip phase and speed-based duration. Do not substitute frame55, Sonic94, clamp88, or treat failed lookup as authored blank. The callback clears player+$04 bits7/4, zeros Y velocity, ignores input, accelerates nonnegative VX by16 toward its high-byte6 threshold and uses `$0338` position integration. Camera-relative completion thresholds and bit5/bit4 flags stay exactly as existing `$83A6`; no exit timing/threshold workaround is justified here.

**Current implementation gate:** there is no safe fully faithful sprite import for the side branch. M2 must not silently claim this branch covered. No change has been approved or implemented by this Research checkpoint.

Smallest safe isolation while Manager decides:

1. Keep public New Game on accepted Sonic. Other authenticated Tails states/assets may be prepared in the isolated M2 developer worktree; do not mark the whole milestone accepted.
2. At the **type2 + state20 + selected94** resource boundary, use an explicit unsupported-contract tripwire that records state/current/request, contacts, counter, phase, callback and route before candidate acceptance. Fail that route/test visibly; do not let a generic fallback choose artwork or expand the raw-pointer decoder. Keep all other character/state/frame lookups unchanged.
3. If Manager explicitly permits a temporary fidelity exception, the smallest proposed adapter is a **no-draw result for this exact unsupported selection**, retaining numeric94/counter2/phase and continuing the independently validated callback, while preventing invalid mapping/extent/VRAM reads. It creates no blank sprite and no fake art. This intentionally differs from the original forced corruption and may retain normal adapter extents instead of malformed32×40; it is **not authorised here**, and cannot be labelled original act-clear parity. Record every occurrence and require targeted Windows return/clear checks under the approved exception.

Without such approval, M2 may continue only work independent of this branch; candidate/full-act-clear acceptance remains blocked. Preserving the previous image is a different intentional exception and is not recommended as an undocumented default. Reproducing arbitrary resident-code/RAM corruption in GameMaker would be broad emulation work and is not a narrow image fix.

**Next decisive evidence if full parity is required:** record an input-only Tails goal or ordinary-boss route with +$23/selector reloads, or prove from all relevant reachable contact producers and handoff timing that side bits are excluded. If a naturally reached case is found, repeat in an independent SMS emulator/hardware with mapping/SAT/VRAM capture before choosing a deliberate adapter. Chief need not resupply the local ROM for this mounted session; a cloud successor needs it privately. No missing asset upload can turn `$0785` into an authored pose.

## 5. Reproduction and checks

```powershell
python tools/m2r1_frame5e.py PRIVATE_ROM
python tools/m2r1_frame5e.py PRIVATE_ROM --check
python -m unittest discover -s tests -p test_m2r1_frame5e.py -v
git diff --check
```

Nine focused evidence checks PASS: pointer/bank/predicate, corrupted-pointer and frame-substitution negative controls, malformed header/duration/visibility, setter/boss floor gates, observed mapping/IRQ reads, normal/corrupt rendering controls, fixture-labelled sign handoffs, unresolved-status preservation and payload boundaries. The executable producer runs16 engine/callback controls,2 hide-flag controls,12 setter controls,8 boss-gate controls and6 whole-game sessions. Deterministic original-code replay comparison PASS. `--check` repeats original-code execution and compares the full metadata; PNG encoder hashes are local-environment-specific, raw RGB/VRAM hashes are the content evidence. No expensive broad historical regression was run.

POC Q3, M2 runtime and root AGENTS were not edited. M2's pre-existing three fragment-metadata status flags were observed, not repaired or relabelled clean. No pixels/ROM/audio were committed, no executable or GameMaker compilation, no merge/main promotion, no automatic runtime exception. Stop for Manager review.
