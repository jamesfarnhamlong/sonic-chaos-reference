# M6-A — Original MGHZ3 boss-approach video observation (1 November 2026)

## Provenance and limitations

Chief supplied `Video Project 1.mp4` on 1 Nov 2026 as **visual reference for the original Master System MGHZ3 boss approach** after Designer-san correctly STOPPED Gate A (missing authentic staged-reveal contract). This is a **private user-uploaded clip**, not a ROM trace, byte-verified VDP capture, or proof of any internal camera state. **Do not publish/rehost the source video, frames or derived images in the public Git repository.** Chief specifically warned that YouTube presented it as **16:9 instead of the original 4:3**. Supplied file metadata: H264 MP4, 852×480, 30 FPS, 177 decoded frames, ~5.9 seconds with audio. User-facing analysis created a 640×480 *aspect-corrected viewing copy* and a 16-keyframe storyboard in the conversation's private working files; these are **viewing aids only** and cannot recover original 256×192 source pixels or exact 60Hz game tick boundaries.

**Do not derive WORLD coordinates, original aspect-exact sprite extents, 60Hz input/event timings or VDP layer priorities from the stretched/corrected pixels alone.** The original source contract must come from actual ROM/level map and camera/object routines. The footage is valuable for *visible ordering* and for choosing the relevant original-ROM natural approach test route.

## Captured visual sequence (approximate real-time clip timestamps)

| MP4 t (s) | Visible event / reliable description | Source-code implication (NOT established by video) |
| --- | --- | --- |
| 0.00–1.00 | Sonic runs right across the grass-topped block platform. Thin striped vertical trunks/poles and hanging yellow/green details scroll past; original timer/rings HUD present. | Retrieve MGHZ3 terrain/metatile coordinates and camera follow state rather than hand-place new decorative objects. |
| 1.00–1.67 | Sonic approaches/stops near the right edge of the raised platform. A **spiked lower pit** becomes visible on the right; platform edge remains at a fairly fixed visible point for part of this interval. | Distinguish ordinary camera follow/right-limit change from a scripted reveal trigger. |
| 1.67–2.33 | Sonic waits near the platform lip; a stripe-patterned vertical pole/trunk is visible across the gap; no evidence of a new sky/background object popping into existence. | Determine when mapped boss $56 is created and when its camera gate activates; visual absence is not proof of object absence. |
| ~2.33–2.60 | First part of the round metallic boss body becomes visible **at upper-right**, partially clipped by the viewport. | Could be original blank-to-combat graphics state and/or camera exposure; cannot determine from screenshots alone. |
| ~2.60–3.33 | Camera composition shifts to expose more of the spike trench and right-side pole/trunk. Boss becomes more visible and **descends along the right-hand vertical feature** while Sonic remains on the left platform. | **Separate horizontal camera movement from vertical movement of the boss.** Do not fabricate a vertical camera cinematic. |
| ~3.33–3.75 | Boss is low near the spikes/right-side feature, then begins to rise; two hazard banks divided by vertical scenery are visible as the scene completes. | Match authentic boss movement/state table and map priority. |
| 4.00–5.87 | Sonic jumps/attacks; boss continues up/down along the vertical pole. A projectile/effect appears on or above the left platform. Gameplay is already in the combat phase. | Preserve verified $56 combat, $57/$58 projectiles and post-hit state transitions. |

At this capture resolution, frame timestamps are **30Hz video frames**, not exact 60Hz emulated game updates. Original footage ends mid-fight, not after boss defeat. Chief's prior belief in an abrupt G2 entrance remains a historical observation; this original clip **does not alone establish a before-vs-after G2 divergence**.

## Cross-reference with previously verified original-ROM code

The existing [MGHZ3 $56 ROM audit](mghz3-boss-56-audit.md) establishes all of the following independently of the video:
- MGHZ3 mapped $56 boss at WORLD (3269,288) (record12); boss creation in right outer band, screenX288..351, not necessarily visibly on-screen.
- State0 requests boss music $8C; state1 requires strict `abs(playerX-bodyX)<160` and `abs(playerY-bodyY)<304` to enter state2.
- State2 waits for HUD slot removal, then starts original 1px/update X/Y camera pan toward (3061,256), settles at (3060,256) because right limit exclusive, and requests state3 **without waiting for pan completion**.
- State3 initializes artwork/palette, HP10, cooldown and enters moving/combat state0B; $56 movement has original Y bounds288/430, gravity/fall, rise and projectiles $57/$58.
- These records do **NOT** prove which *terrain tile/priority/object state* is the vertical stripe or two spike-bank features seen in the natural approach, nor their precise visible reveal/occlusion in the G2 rendering.
- The referenced full-game driver/trace is **synthetic**, so its emulated images are not sufficient to establish natural input-driven entrance framing.

The video is broadly **consistent** with a brief interval when the camera pans while the boss appears at the right side and begins moving vertically. However it does not independently identify the tick when state2 vs state3 occurs. It also suggests the scene may be primarily **continuous camera/terrain exposure rather than a new scripted scenery animation**. Do not treat interpretation as established source fidelity.

## Corrected M6-A Gate A continuation (research-first)

**M6-A production editing remains HOLD until the missing contract is demonstrated.** Continue the existing assignment with a **targeted natural-route reproduction** rather than another vague analysis of "staged reveal."

1. Use the original ROM in its authorized local research environment to obtain a naturally input-driven MGHZ3 approach, replayable route or equivalent original-trace series. Align major scene transitions from Chief's video with original-ROM `camera D174/D280/D282`, $56 state/type/position, player WORLD X/Y/state, active HUD, source object scanner and tile/priority rendering, at minimum pre-trigger, first boss pixel, first pan, pan settle and combat start. If a natural approach cannot be automated, extract camera + render evidence from the original emulator with a precise limitation.
2. Map **which terrain/metatile/stripe and spike tiles** occupy the relevant WORLD positions using the canonical MGHZ3 map/VDP priority bits. Confirm whether the vertical feature is map/background artwork or a separate runtime object. Determine if any object/palette/draw-priority change or *staged animation* actually occurs. Don't add fake scenery, reveal timers or mask bands if the original effect is camera pan plus existing map.
3. Capture the **current accepted G2 normal GameMaker** approach at 348×196 with the same route concept and alongside 256 native-source modeling where available. Establish *exactly which visible transition differs*: platform edge/camera, early boss sprite onset, pit width, spike positioning, vertical scenery, priority or intro timing. Merely demonstrating original video is not proof the GameMaker is wrong in that detail.
4. Produce a compact original-vs-G2 **frame/time/update concordance** with distinct columns for ROM-source certainty, video observation and GameMaker observation; if possible, identify the smallest genuine correction within accepted $56 combat/camera ownership. Preserve M5 audio. 
5. Only after source mapping and an observed POC contrast establish a concrete gap, resume original M6-A implementation Gate B. If still inconclusive, STOP with **one narrow source mapping/VDP question** that Research-kun can solve. No release archive/Chief F5 until a cohesive integrated patch exists.

**Source safety:** Private ROM, audio banks, graphics captures and source video remain local/private; commit only evidence metadata, public-safe summary and non-restricted test code. Do not change current accepted G2 production code while Gate A is unresolved.

## Decision

**Designer Gate A STOP was correct.** New Chief-supplied video materially strengthens visible approach chronology but is **not yet a completed original map/layer/source contract**. Resume targeted Gate A evidence acquisition; do not substitute this clip for a code-backed source contract and do not mislabel existing audio/gameplay acceptance as pending.
