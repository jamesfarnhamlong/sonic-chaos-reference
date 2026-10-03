# GPZ PNG approval checklist — complete, 2026-10-03

Generated package: `build/gpz-enemy-approval/` (ignored, local-only art).
User approved `type-25-approval.png`, `type-2c-approval.png` and
`support-approval.png`. Their PNGs and approvals are unchanged. The original
`type-51-approval.png` is rejected and superseded by `build/gpz51-correction/`.
See `gpz3-boss-composition-correction.md` for the replacement sequence/checklist.
Each main board includes raw decoded tiles, composed
frames, registration marks and a canonical terrain context. Individual sheets
also separate SAT pieces. Individual transparent PNGs retain a stable 128x112
canvas, origin (64,56) in pre-presentation SAT space. Context views add (+1,+18).
Do not shift collision anchors to match the canvas.

| Subject | Visible frames | GPZ use | Mirror mechanism | Anchor / dependencies |
|---|---:|---|---|---|
| `$25` | 2 (mapping0 blank) | 1/2, both states1/2 | alternate bit-reversed art `$96/$A8` + mapping coordinate mirror; no whole-image flip | canonical placement anchor; generic terrain/lifecycle/contact + `$0F` defeat |
| `$2C` | 2 (mapping0 blank) | 1/2, bit4=0 at all GPZ placements | shared art `$8C/$8C`; forced mirror is diagnostic only | canonical placement anchor; shared bee movement with distinct 12x16 extent; `$0F` defeat |
| `$51` | 11 (mapping0 blank) | 1 hit head,2 normal head,3..9 balls,10/11 live landing dust | bit4=0 in both directions; forced mirrors excluded | parameter0 head above three children1/2/3; mode2 adds4; parameter17 dust; `$12/$34/$0A` |
| `$34` puff | 4 | 1..4, both state1/2 timing sequences | normal only; forced mirror excluded | spawned anchor + mapping origins, GPZ art base `$96` |
| `$0A` sparkle | 2 selected from shared mapping | 5/6 | normal only | emitter/child anchors; base0; shared bonus chain |
| `$0F` smoke | 3 selected from shared mapping | 7/8/9, regular defeated enemies | normal only | preserves defeated object's anchor, resets art bases0; detached placement token |
| `$12` HUD slide | no own nonblank frame | blank0 controller | no mirror | moves existing HUD SAT; no new bitmap to import |

Approval questions for each runtime candidate:

- Are the body, limbs, head and exhaust assembled correctly, with all pieces present?
- Does `$25` reverse correctly between the two canonical orientations, without a second flip?
- Does `$2C`'s GPZ bit4=0 exhaust point correctly? Its forced opposite-side placement
  uses unchanged tile pixels; do not approve it as a runtime facing without a new trace.
- Does the corrected boss show head above three balls, bottom-up detachment,
  head-only and regrowth from below the floor? Mode2's fourth ball is separately labelled.
- Are the blue/yellow/orange/white colors correct under palettes7 and13?
- Do magenta registration marks align with the canonical terrain context?
- Are the puff, sparkle, smoke and `$51` particle frames recognizable and complete?

`$25`, `$2C`, corrected `$51`, `$34`, `$0A` and `$0F` are **approved by the user**.
The corrected boss replaces the earlier wrong composition. A generated image
or passing test alone is not approval. The tracked
`data/rom-cache/gpz/approved-art-manifest.json` freezes the approved PNG hashes,
sizes and exact transparent frame files. It excludes whole sheets/context
images and unused forced mirrors. Approval should identify subjects and any
rejected frame/orientation; never treat a blanket image-generation success as approval.

Ambiguities / separate rollout gates:

- Informal enemy/boss names are not ROM-proven.
- Forced `$2C`/boss/effect mirrors are not used by this GPZ batch and must not be imported.
- Contexts are controlled composites; corrected boss uses original scheduler
  captures and is compared visually with the supplied gameplay video.
- The below-map GPZ1 `$25` placement remains unchanged; reachability is unresolved.
- Boss contact, complete phase/timing/mode/arena and clear-chain oracle work is
  deliberately not certified by this art pass.
- `$51` frames10/11 are live parameter17 landing dust. Runtime use is now proven;
  their corrected runtime use is included in the approved `$51` package.
- Later EEZ art and audio/results assets are outside approval scope.

The user authorized committing/pushing the full Research package. Main may be
fast-forwarded after canonical integration is separately authorized. Send a scoped
POC job only when instructed; POC and root AGENTS remain untouched.

AGENTS candidate update (for Manager-san at an accepted checkpoint):
"GPZ $25/$2C, corrected $51 and $34/$0A/$0F art are explicitly approved.
The approved-art manifest freezes hashes/import candidates; $2C reuses $27
movement with distinct 12x16 object extents; GPZ3 selector
$14/palette$0D and head-above-three-ball $51 composition (four balls only in mode2)
must not inherit THZ boss art/runtime; $51/$11 is live landing dust.
Keep approval and remaining boss runtime gates explicit."
