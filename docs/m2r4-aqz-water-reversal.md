# M2-R4 — AQZ water palette and reversal/jump audit

23 October 2026. **RESEARCH ONLY — stop for Manager review.**

Read canonical `AGENTS.md`, `MEMORY.md`, `ROADMAP.md` at Research
`main@5e579728d302a422e515d605e06b1996f553962e`; branch parent is accepted
M2-R3 `33c4c13ebeadb54834c8cddd5bafedaae5e13015`. Read A2 water contract,
M2-R3 and independent M2-R2 `cd417c1` character matrix. Neither main nor R2
was merged. Accepted POC remains `7476affc6ed7626dabf69b446cdab0c9c3d7492e`.

## Disposition

**Neither reported Windows symptom is resolved by these controls. No Designer
gameplay correction or Windows-targeted palette correction is justified yet.**
C's palette data, decoder and ordinary above-to-split row selection agree.
One conditional full-camera-to-split upper-palette history mismatch is isolated
below; normal steady camera bounds do not reach its prerequisite.
An authentic retained-momentum backward jump and repeated skim are reproduced
in original game code and C, but Chief's exact violent launch/surface route
has not been identified. Do not call the entire observation canonical.

The actual private C ZIP was independently hashed:
`321bcd86b2daa5539485f17107f037c843a7902267db514b16d22864ef556964`.
All **548 GML/vertex/fragment source files**, all 88 indexed Tails textures and
the inspected Sonic proxy textures matched that ZIP's extracted directory.
The archive contains 7,870 entries. No POC/package/root-management file changed;
no ROM, pixel, audio or executable payload is included in this Research change.

Evidence labels used below: **original-code controlled** means actual original
Z80 instructions in the approximate SMS software harness; **C source-host**
means shipped GML executed in its existing JS host; **shader equation** means
source-locked CPU arithmetic, not compiled shader execution. These do not
establish physical SMS raster timing, native Windows GPU output or natural
entrance-to-encounter reachability.

## A. Complete palette chain

AQZ1/2 world lines are **568/788**. Original `$4BC0` compares the player's
unsigned **anchor** against the line, equality submerged. That water flag
selects physics; it does not choose a sprite's rendering palette. Original
type `$0D` callbacks `$0C:$9DDD` prepare the raster from camera `$D176` and
line `$D450`, then both publish their identical world line. Act creation first
sets line768; normal controller initialization/publication takes two passes.
AQZ3 has no controller/updater and must keep ordinary presentation.

| Camera condition, delta = line − cameraY | Original and C selection |
|---|---|
| delta193 or more, after leaving split | Above: background record25 + sprite record10, palette table file `$3B64D`, bank14 `$B64D` |
| 1..192 inclusive | Split enabled; `$D132=delta`, line IRQ copies **fixed 32 bytes at `$0688`**; first lower-colour adapter row is delta+1 |
| delta0 or negative, after leaving split | Queue records48/49; fully submerged palette, different from fixed IRQ |
| AQZ3 | Above palette; no switching |

Original `$9DED..$9E55` changes the base palette **when exiting an enabled
split**, not on every call outside the split domain. A freshly disabled
controller called directly at delta0 does not independently queue49. Both
prior-enabled and prior-disabled cases are retained, rather than forcing a
stateless approximation. In split mode the upper rows retain the saved base
palette; the ordinary above→split→full→split→above route follows the table.
Artificial full→split histories expose the conditional difference described
below; no native restoration-timing claim is made from isolated calls.

Original `$0652` IRQ writer and `$1CBD` saved-CRAM restoration were re-executed
for both characters, water0/255 and raster96/255: eight controls, including
the no-copy negative. Restore copies `$D472[32]` and clears its request.
Two additional `$1CBD` controls restore the fully submerged saved CRAM for
Sonic/Tails. The three C palette arrays were independently compared with original ROM
records/fixed IRQ bytes. CRAM expands red bits0..1, green2..3, blue4..5 by85.

Original header camera bounds and C's camera table agree: AQZ1 bottom528
exclusive; AQZ2 bottom784 exclusive. Thus an ordinary steady bounded camera
cannot reach cameraY568/788: its minimum integer deltas are41/5. A player
deep underwater normally uses **lower split IRQ colours**, not palette49.
Moving between two deep underwater positions can legitimately leave colours
unchanged. The fully submerged-camera branch was tested by controlled camera
placement, not claimed to be a normal standing location. Arrival fixtures can
temporarily put camera state outside steady limits; their camera histories
are recorded and must not be used as natural-reachability evidence.

### Exact row/decoder/output path in C

`SCR_chaos_aqz_environment.gml:266` uploads 32 RGB triples per palette, disables
filtering and supplies cameraY, raster+1 and mode. `:319..324` draws through
`chaos_aqz_player_source`; Tails indexed resources select `player_source=0`,
Sonic proxy resources select1. The incoming Tails sprite can **already** be
indexed; the routing handles that without sending it through the alpha path.
`SCR_chaos_tails_frames` enumerates the authenticated indexed resources.

The vertex shader exports `in_Position.y`. The fragment shader decodes the
immutable texture before tint: Tails `(17+i,1,1,255)` → CRAM index16+i;
Sonic proxy alpha17..32 → index16..31. Above water the Sonic proxy preserves
its legacy RGB (some pixels differ from the nearest palette entry); split/full
use direct indexed RGB. Tails uses direct lookup in all modes. The fragment
compares interpolated `worldY-screen_top >= irq_cut`, then applies vertex
tint/alpha. Source registration is anchor+(1,18), with each sprite's own origin.
The previous GPU filtering state is restored afterward.

At Tails index3 (CRAM19), opaque input `(20,1,1,255)` yields:

| Mode | Output RGBA before tint |
|---|---|
| Above | 255,170,85,255 |
| Lower split | 255,170,170,255 |
| Full camera | 170,170,255,255 |

Index0 transparency remains alpha0 even if its decoded RGB is nonblack;
Sonic alpha0 does not decode as an opaque proxy. Opaque black index6/CRAM22
stays alpha255. The report contains actual texture index inventories and
source-locked sample input/index/lookup/output/tint vectors; no texture pixels
are published.

Forty original raster controls cover AQZ1/2 × Sonic/Tails × prior split off/on
× delta0,1,191,192,193. Eighty actual C draw-route captures exercise both
decoders for those controls. All 15 opaque sprite indexes are checked at nine
sample rows per capture. Actual Tails frame3 and Sonic jump texture/origins
are also sampled privately while crossing the cut, with 192/196-height clipping.
At delta191 lower rows start192: none are visible at192 height, four at196.
At delta192 lower rows start193: none at192 height, three at196. Delta193
disables split even in196 height, retaining the documented original192-line
enable domain. Delta1 begins lower colour at row2; delta0 after split selects
full49. A sprite can have different colours on different rows.

**Finding:** all 88 indexed Tails frames have a split-colour change on more
than half their opaque pixels (range55.74%..96.61%). Frame3 changes241/305
opaque pixels when wholly in the lower split region; at anchor=line its
registration straddles the cut (77 above/228 lower,177 changed pixels).
No palette-source/decoder/ordinary above-to-split selector defect was found in C. But unchanged colours
across a *guaranteed visible crossing* cannot be dismissed as identical original
colours. Chief's actual camera/row/GPU condition is unknown: **UNRESOLVED-WINDOWS**.
AQZ3 normal source presentation is correct in these controls; no native AQZ3
visual complaint is explained or rejected by absence of a controller.

**Conditional history difference, not a demonstrated Chief-route defect:**
`palette-original.json.histories` executes `$9DED` through deltas
193→191→1→0→1→193 for both characters. At delta0 it queues48/49; after
those requests complete, saved base CRAM is full. Returning to delta1 merely
enables split and queues no above palette. Actual `$1CBD` controls confirm
that a saved full palette restores as full. The original therefore has full
colours above the cut and fixed IRQ colours below. C retains `cp_e.palette=1`
but mode2's shader upper branch unconditionally chooses `above` (or Sonic
proxy RGB). This is a **source-confirmed selection difference conditional on
full base restoration**; the inter-call queue-completion history is a
source-backed model, not a natural or cycle-exact gameplay reproduction.

If Manager elects to support/test that controlled history, the minimal exact
Designer correction is: upload a separate `upper_submerged` uniform from
`cp_e.palette`; in the fragment selection use `submerged[i]` for mode1 **or**
mode2 with `!lower && upper_submerged>0.5`, fixed `split[i]` for lower mode2,
otherwise preserve the current RGB/above choice. Preserve the latch on entry
to split and let the existing [25,10] exit request clear it. This needs both
Sonic and Tails full→split→above regression controls; no texture change or
physics change is involved. **Do not package this as the fix for Chief's
unexplained absent switching:** steady AQZ camera limits exclude full mode,
and no native trace has shown that prerequisite. No implementation is made.

Host correction made only in this Research runner: its inherited `array_push`
mock accepted one value, whereas palette upload calls GML's variadic form with
three components. The runner supplies the correct variadic mock. This was a
test-host limitation, not a C runtime change or a diagnosed Windows defect.

## B. Reversal, fresh jump and repeated skim

`original-game.json` records96 cases/9,600 original player updates. Each case
seeds arrival/state once at X816, then uses input only with original code,
layout, objects and scheduler. Cases cover AQZ1/2, both characters, both
directions, grounded/airborne attack/nonattack, near-surface attack, tap/held
jump; forward/no-jump, reversal/no-jump and low-speed controls. Most start at
6px/update; charge controls start at zero and use the original Down+fresh
Jump/release sequence to obtain7px/update before reversing/jumping. These are
**controlled arrivals**, not run-up routes from the act entrance. The first
ground projection can correct the seeded anchor; preserve it in the trace.
A normal running approach to Chief's exact location is still missing.

Each update has start/end fixed-point position, signed VX/VY, current/requested
state, attack/air bits, facing, polled held/fresh input, jump counter, water,
anchor/line, camera/bounds, contact/support and acceleration. Separate compact
phase rows record water before/after, input before, X before, Y before and
terrain before. `$64FA` rows are **after the previous callback/object pass**;
their input bytes may already be polled for the upcoming update. Explicit
`starts` records drive C, avoiding a one-update input shift. Wall-clock/VDP
frames are retained separately from player updates.

Actual C GML executes9,020 original shared-call snapshots. **54,120 phase
snapshots ×19 fields match exactly**, through the entry to terrain. All paired
shared-call VX/VY results also match, including the cases with other differences.
One hundred updates are replayed continuously through C's adapter in each case
at256×192 and348×196: **156/192 runs match all nine compared trajectory/state
fields throughout** (X/Y, VX/VY, executing/requested state, flags, water, jump
counter). All96 AQZ2 width/character runs match those selected fields.
Camera input is deliberately replayed from the original controlled history;
the first C frame uses the original first completed camera to avoid an
arrival-induced offscreen-death artefact. This is not an independent natural
C camera/lifecycle or Windows timing reproduction.

### What is authentically reproduced

* Abrupt direction input changes facing/brake selection before horizontal
  momentum reverses. Underwater walk same-direction acceleration2, brake4,
  jump opposite braking8 and same-direction4 are preserved; there is no instant
  VX sign flip on fresh Jump. Example `a1-c1-d1-ground-hold`, update13:
  held Left+Jump, VX **+1502/256**, VY **−832/256**, request10; subsequent
  held-jump updates give VY−808 after gravity24. Both characters/directions are
  represented. Backward relative to input/facing is not automatically a bug.
* `$3901` increments the byte jump counter while held and rewrites VY−832
  while count<14; release sets32. `$45ED` performs the initial launch and
  subtracts1px from Y. Neither launch setter reverses VX. Dry values are−1088.
* `$4BC0` repeatedly writes−768 when anchor>=line, VY>=0, attack bit1 set,
  abs(**signed high byte** VX)>=4. No Jump edge, facing or near-surface test
  exists in that gate. Negative−1023 qualifies; positive+1023 does not.
  **192 original/C boundary controls** include both characters/acts, above/equal/
  below, attacking/nonattacking, ascending/nonnegative VY and both thresholds.
* The original scheduler traces contain116 qualifying writes, across20 cases
  with repeated qualification. **64 are subsequently overwritten** within the
  shared update (for example grounded support's +7 integration/projection),
  so a gate write alone does not prove a visible bounce. Example
  `a1-c1-d1-air_attack-tap` updates1/33 both write−768; after underwater gravity
  the shared result is−744. The anchor rises toward/through the line; following
  updates can clear water and use dry gravity. The impulse is not a newly
  invented water-surface contact.
* AQZ2 rightward charge control reaches an original terrain diagonal-spring
  launch (state28, VY−1408 at update13), also matched by C. It occurs **before**
  the later reverse+jump action; it is not evidence that reversal creates that
  impulse. Sprite, terrain and action timing must be separated.

### Differences retained, not labelled PASS

There are **50 raw shared-return differences**:42 side/contact cases in AQZ1
and8 no-ring damage-field cases. The corresponding pre-terrain phase values
match, and none differs in returned VX/VY.

* Original side terrain type`$1E` routes through `$716B..$71B2`/`$7210..$7257`:
  ordinary projection still occurs and the character's push frame can request
  state`$34`. C `SCR_cc_sides` (`SCR_chaos_core.gml:454..487`) explicitly marks
  type30 unsupported and skips projection. Example leftward ground tap update15:
  original X187114 versus C186346 fixed-point units (3px), left contact8 versus0.
  Some later requested-state differences are the missing push path. This is a
  **bounded inherited source gap**, shared by both characters; it does not
  establish the Windows reverse-launch cause or authorize a wall/physics fix.
* At eight source snapshots with a staged spear hurt request and no rings,
  original death setup also clears grounded/input fields; C's zero-ring early
  return in `SCR_cc_hurt_rom` (`:601..609`) requests31/VY−1280 while retaining
  those fields. This is a **bounded source mismatch at damage**, not skim.
* Continuous runs diverge first on the type30 wall path or later moving-object
  hurt/lifecycle;36/192 are not full matches. The C host's newly initialized
  placement scheduler is not synchronized to the original boot-aged object
  cycle. Eight later runs vary between widths after such contact divergence;
  they do not prove a width-dependent jump law. First differences and every
  comparison are retained in `package-comparison.json` and `summary.json`.

Original order is callback held-jump write → `$3FEF` water/skim → screen-death
check → acceleration → X → Y/gravity/support → terrain → damage `$48BC` → fresh
jump → callback tail → camera/object scheduling. C ordinary `SCR_cc_tick` /
`SCR_cc_shared` preserves the movement sequence; damage/object staging and
viewport bounds belong to its adapter. The comparator explicitly supplies the
damage owner before the fresh-action tail when pairing `$3FEF` returns; C's
shared helper alone does not include that owner. The continuous runner uses
the actual adapter, with room/player bounds and its actual object phase.
The original request/attack ownership and the accepted Q2 facing correction
must not be replaced by velocity-derived presentation facing.

**Finding:** retained-momentum jumps, repeated skims and a distinct terrain
launch have paired evidence. Chief's particular high-speed reversal/jump
sky-launch and repeated surface rebound remain **UNRESOLVED-WINDOWS**. No
gravity change, clamp, jump reduction, skim disable or new bounce is proposed.

## Smallest next Designer / Chief evidence

No Package D gameplay correction is recommended. Use C unchanged for a short
local capture first; Manager may commission diagnostics if the existing logs
are insufficient. This is a recommendation, not implementation authorisation.

1. **Palette:** one AQZ1 or AQZ2 Tails capture at348×196, with F6
   `aqz-runtime-trace.jsonl` and F7 `player-runtime-trace.jsonl`, plus two matching
   lossless screenshots of the *same pose* above and wholly below the rendered
   cut (or one visible straddle). Include `palette_draw` cameraY/line/delta,
   mode/enabled/raster/cut and F7 draw resource/origin/position. A same-scene
   Sonic control is useful; AQZ3 gets a separate ordinary-colour screenshot.
   Normal deep-camera49 need not be reachable. If mode2, decoded resource0 and
   opaque rows below the cut are logged but expected pink/blue lookup does not
   appear, then a native shader/uniform/vertex/texture-page capture is the next
   boundary. Existing logs do not read back fragment RGB.
2. **Movement:** one reproducing act/character/location, roughly30 player
   updates before reversal through90 after the first launch, plus a short
   synchronized video. Existing F7 water gate/result and draw events narrow
   the event, but **omit held/fresh, jump counter and facing**. The smallest
   additional diagnostic record is one monotonic update ID and start/end
   X/Y/VX/VY, held/fresh, jump count, executing/requested state, move/facing,
   water/line, camera, contacts/support/queued hurt; mark which owner wrote VY
   (hold, jump, skim, gravity, support, terrain, damage/object rebound). Do not
   alter any value to collect it. Replay those exact inputs in the original
   arrival and actual C before selecting any correction.

The short Windows capture is needed to distinguish unknown native output/
timing from already paired source behaviour. Neither Chief's previous passes
nor this audit closes the natural Tails frame5E log gate or campaign acceptance.

## Reproduce and validate

```text
python tools/m2r4_aqz.py PRIVATE_ROM --gameplay
python tools/m2r4_private.py PRIVATE_C_DIRECTORY PRIVATE_C_ZIP
node tools/m2r4_package.js PRIVATE_C_DIRECTORY
python tools/m2r4_summarize.py
python -m unittest discover -s tests -p test_m2r4_aqz.py -v
```

Eleven focused evidence tests PASS; ten inherited R3 cached-evidence tests also
PASS (not new Package B execution). Source/archive hashes are in
`data/m2r4/private-checks.json`; original palette/routine controls, hashes and
source locations are in `palette-original.json`; per-update original/C tables
are separate from the additive Fidelity Register. No full historical suite,
Windows test, executable build, POC change, public asset export or Research
main promotion was performed. Preserve inherited SS5/THZ3/U5-A raw failures;
they were not rerun or relabelled by this audit.
