# M2-R3 — AQZ palette and spear fidelity

23 October 2026. Research only, parent `d6f2fafcda7903c0fc7082b2a9cbf4fed6e0bf98`.
Read canonical AGENTS/MEMORY/ROADMAP at `main@5c95e9e` and M2-R2 at
`cd417c1`; neither branch merged. Accepted POC remains `7476affc`.

**One confirmed presentation defect; no confirmed collision defect.** Private
M2 Package B uses an alpha-index decoder for RGB-indexed Tails textures. Its
encoded dark red pixels consequently reach the screen unchanged. The thin
AQZ spears are moving object **type `$3C`**, distinct from terrain block `$3C`.
Their bounded original-code and Package B contacts agree. Chief's reported
placement-specific Windows failure remains OPEN pending the exact runtime route.

The local B ZIP SHA-256 was independently read as
`3ee8ed903df63ceedd6de2298df936bd41ef357f1598311c5a48bd64cd5f68a3`.
Inspected source/art files were compared to that ZIP, not assumed to exist in
public Q3. No POC, Package B, coordination root or private asset was modified.

## Palette: source and rendering policy

`data/m2r3/evidence.json` holds original-code listings/hashes, per-frame indices,
per-condition colours and CRAM controls. All 88 valid nonblank Tails mappings
were regenerated privately: **176 normal/indexed B textures match exactly**.
The regular RGBA import uses palette7; every opaque index actually used by
these frames has identical colour in stage sprite records6..11, including
AQZ record10. Complete palettes differ in other entries. This is not a wrong
normal import, missing Tails palette, or evidence for manual recolouring.

| Condition | Original source / required presentation |
|---|---|
| AQZ above water, including AQZ3 | AQZ background record25 and sprite record10, bank14 palette table file `$3B64D`; sprite index `i` reads CRAM `16+i`. |
| Split-waterline view | `$0C:$9DED`: `0 < waterline-cameraY <=192`; line IRQ `$0652` copies **fixed 32-byte `$0688` source**, then saved above palette is restored through `$1CBD`. Select per rendered row, not whole sprite or player water flag. |
| Fully submerged camera | Leaving split mode with `waterline<=cameraY` queues background48/sprite49 (`$30/$31`). These colours are different from fixed IRQ data. |
| Waterline below view | Leaving split mode with delta>192 queues background25/sprite10. Requests are stateful, not rewritten every call. |
| Transparency | Original sprite nibble0 is transparent, even when corresponding CRAM RGB is nonblack. Keep alpha0. Opaque black index6 remains opaque. |

Water lines are world568/788 in AQZ1/2. Equality of **player** anchor with the
line sets underwater gameplay; it does not select the rendering palette.
AQZ3 has no water controller. Preserve B's documented adapter: original
192-line enable domain and first lower row `R10+1` at 348×196. Software CRAM
checks prove source/copy/restore, not cycle-exact hardware or Windows GPU timing.

Example Tails index3: above RGB `(255,170,85)`, split `(255,170,170)`, fully
submerged `(170,170,255)`. These are exact SMS 2-bit component expansions.

**Actual B failure:** `m2_assets.py` writes indexed opaque pixels
`(17+i,1,1,255)`. `chaos_aqz_player_draw` selects `player_source=1` for Tails
indexed companions. That shader branch reads `alpha*255-1`, yielding **254**
rather than `16+i`. It rejects the encoded index and emits the dark RGB payload
`(18..32,1,1)` unchanged in every palette mode. Decoder equation controls cover
all15 opaque index values ×3 modes; pixel checks cover actual frame indices.
This source mechanism matches the silhouette observation; no live GPU capture
was made. Original IRQ writer and restore were separately executed for both
characters, including IRQ skip controls (8 cases); raster boundaries also rerun.

**Designer recommendation:** give Tails RGB-indexed resources their correct
decoder mode. Minimal scoped option: in the draw routing, use existing
`player_source=0` for authenticated `chaos_tails_indexed(cp_base)` resources;
retain the alpha proxy for Sonic's existing proxy resources. If using an explicit
format enum instead, preserve those two formats separately. Use ROM CRAM lookup
for above/split/full rows. Preserve tint/alpha application after decoding,
nearest sampling, origins, valid frame selection and the frame5E exception.
No sprite recolour, palette approximation or physics change is justified.

## Spear identity and placements

Chief narrowed the observation to the beginning of AQZ1 and supplied a marked
map. The opening lower-corridor thin spear pair is mapped type `$3C` records
12/13 at **(1104,686)/(1232,686)**. Reconstructed original art distinguishes
these from white spike beds and blue cross masonry. Original frame1 points up;
frame2 points down. Art is private; bounds/hashes are in the evidence.

| Act | All mapped `$3C` spear anchors | Parameter/orientation |
|---|---|---|
| AQZ1 | (1104,686), (1232,686), (2480,654), (2608,654), (2752,654), (4368,654), (4448,558), (4528,654) | All0/up except (4448,558):1/down |
| AQZ2 | (1088,814), (1216,814), (496,462) | First two0/up; (496,462):1/down |

These are objects, so **no terrain tile ID, collision plane or terrain profile
owns their contact**. Records retain art bases `$6A/$6A`, flags, parameter,
placement address/token; all are enumerated. Ground beneath/near an object is
ordinary separately decoded terrain, not its hazard shape.

Original `$1E:$9251` selects state1/frame1 for0; nonzero selects5/frame2 and
adds12 to Y. Up cycles: Y−4 for4 callbacks, dwell32, Y+4 for4, dwell32 (72
callbacks). Down cycles reverse legs from the shifted anchor. Motion continues
asleep; contact does not. Package B agrees for all11 placements ×180 updates,
including a40-update sleep interval. Its placement lists, runtime layouts and
spear art/registration also agree with the original checks.

`$9284→$0434→$630B→$6328` tests overlap **after movement**, only when awake and
`D12F bit0=0`. Extents are spear3×13, ordinary player8×24. Inclusive ordinary
contact is `abs(playerX-spearX)<=11`, relative Y in `[-13,+24]`; state `$0F`
uses player width9, extending X by1 (inherited original geometry contract).
The visible shaft is not a solid collision profile. Frame1 opaque bounds are
`[-3,-14]..[2,17]`; frame2 `[-3,-32]..[2,-1]` before shared presentation
registration `(1,18)`. Original art and hazard extents are deliberately distinct.

Any qualifying overlap requests `$D3B0=FF`; the following player pass consumes
it through `$48BC→$48F7`. **No physical wall/floor/ceiling projection or stomp
defeat is performed by this spear.** Top, side and underside overlaps use the
same box; attack alone does not protect either character. Player hurt bit6
suppresses overlap, blink bit7/selector6 suppress damage. Water, terrain plane
and character identity do not change the callback. Passage outside the box,
through shaft-only artwork, during skipped contact phases or while protected
can be legitimate. A persistent unprotected overlap across awake even phases
should hurt; its failure would need investigation.

Original-game software-harness routes seed player/character/camera once near
the first pair, then use input only with original objects/layout/scheduler.
Both grounded routes hurt (Sonic update113, Tails112); both upper routes pass
at Y558 without hurt. These are **arrival-assisted**, not natural entrance
playthroughs or native Windows acceptance. Exact Chief contact phase/path has
not been reproduced in Windows.

## Terrain controls, ownership and unresolved risk

The separate terrain inventory contains **13 block `$3C` beds in AQZ1** and
**9 block `$3D` beds in AQZ2**, both terrain type5. All placements include both
plane headers, 32-entry vertical/horizontal profiles, 16 mapping attributes,
individual tile IDs/flips/palette/priority and neighbors. Blue cross masonry
blocks04/29 are inventoried as negative visual controls (type2/type0).
No placed ceiling `$3E/$3F` or side `$F4/$F5` spike tiles occur in these acts.

Original terrain controls and B agree across1,152 paired approaches. Landing
contacts can project and hurt after the previous-surface floor projection;
rising contacts skip that branch. Low side contact can project without damage;
the tested high sides/ceiling do not turn these floor beds into omnidirectional
hazards. These are sample approach controls at every bed, not exhaustive
continuous collision or every reachable player state. Do not add rectangular
hazards or change accepted THZ spike processing.

Owner assessment: **confirmed Tails-only presentation routing** into AQZ's
shared palette renderer. No confirmed AQZ layout or shared collision defect.
Original `D12F` is VBlank-owned; B approximates it once per effect step. Object
creation, previous sleep flag, camera history and cycle phase can therefore
affect a placement's instantaneous contact. This is an adapter/lifecycle
follow-up, not a demonstrated cause of Chief's persistent symptom. Candidate
contact tests inject clock/sleep inputs; they do not prove the full native
camera/lifecycle history at348. Keep the Windows observation OPEN.

For a scoped palette correction, retest Tails AQZ1/2 above/full/split crossing,
including a sprite straddling the line, transparent edges, AQZ3, and non-AQZ
Tails. Protect Sonic AQZ1/2 normal/underwater/Rocket presentation and shared
object/terrain/HUD palettes; retain all six B passes. Revisit both first spears
with Sonic/Tails on foot, jumping and after backtracking at348 with F6 trace.
If a later proven shared hazard change is proposed, add accepted THZ static
floor/rising/side spike and moving `$1B` controls, AQZ beds and both character
damage protections. No such shared change is recommended now.

## Reproduction and limits

```text
python tools/m2r3_aqz.py PRIVATE_ROM --package PRIVATE_B_DIRECTORY --check
python tools/m2r3_game.py PRIVATE_ROM --check
node tools/m2r3_package.js PRIVATE_B_DIRECTORY
python -m unittest discover -s tests -p test_m2r3_aqz.py -v
```

22,528 original routine/B contact pairs,1,980 motion updates,1,152 terrain
pairs,176 privately regenerated Tails textures,8 original IRQ/restore controls,
4 original scheduler routes/800 updates and10 focused tests. The shader result
is an equation/source diagnosis, not compiled GPU execution. No full historical
suite or new Windows test; inherited SS5 camera-X, obsolete THZ3 cap and U5-A
whole-core comparison failures retain their status. See machine register and
validation receipt. **Stop for Manager review; no Package C implementation or
Research main promotion performed.**
