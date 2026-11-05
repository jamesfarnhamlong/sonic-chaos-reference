# Sonic Chaos — S1 Protected Rendering Hooks: Manager Approval
**5 November 2026 · Manager-san #10 · FOUR GUARDED HOOKS APPROVED · S1 RESUME**

## Decision and reason
Chief had explicitly instructed Manager and Designer to run a **substantial development sprint** with one integrated deliverable, rather than repeatedly stopping after 1–10-minute micro-tasks. The initial S1 safety rule made any edit to a pre-existing frozen GML file a hard stop. Designer correctly obeyed it and returned `S1_DISPLAY_FOUNDATION_BOUNDARY_20261105.md` at local private checkpoint `5786dacc1ebc73006a79a255d071000e93d6c479`, branch `enhancement/s1-display-foundation-20261105`, without making the protected edits.

**Manager's decision:** approve the four proposed **minimal, reversible, Enhanced-only renderer lifecycle hooks**. The original frozen source *commit/tag/archive* must never change; changing a guarded file on a **new isolated successor branch** is permissible when the original Classic execution path is demonstrated identical.

This resolves the reported boundary without requesting another Chief approval. Designer should resume S1 and make substantial integrated progress. Routine debugging, controlled experiments, small extra display-only guards in the same ownership/lifecycle problem, and focused internal tests are **delegated**. A fresh stop is only justified by a real Classic gameplay/audio/collision/room-state change, an unsafe architecture without fail-closed fallback, or a significant product-design choice outside S1.

## Inputs independently checked
- Designer's attached 48-line boundary report identifies exact affected call sites; source-host verification 1,738 assertions reported PASS, 9,336 tracked files/archive comparison and independent E:/H: hashes reported PASS. These are **Designer local assertions**; Manager reviewed actual frozen-source content through the private game GitHub connector, not the local H: archive.
- The four files at accepted E0-R1 `deccefc0acd822f74b6b26895ec278cdf67a7cee` are in fact frozen-original files.
- `scripts/SCR_screen/SCR_screen.gml` calculates Auto/Wide348×196/Retro290×218 then sets window, application surface and view port at logical size multiplied by `global.windowSize`. A guarded alternate Enhanced-only config can be inserted before the existing assignments with fail-closed return behavior.
- `objects/OBJ_pause/Alarm_0.gml` calls `instance_deactivate_all(true)`, then `chaos_audio_pause(true)` and sets `pause=true`. Keep those existing statements intact/in order.
- `scripts/SCR_chaos_results/SCR_chaos_results.gml`, in `chaos_results_capture_draw`, copies the current app surface, deactivates other instances, and keeps audio alive. Never alter the original captured frame or audio call order.
- `scripts/SCR_chaos_death/SCR_chaos_death.gml`, in `chaos_death_draw`, performs matching capture/deactivation and audio keepalive before original results rendering.
- Official GameMaker LTS docs: `instance_deactivate_all(true)` keeps caller active, deactivation takes effect at end of event, and the draw sequence includes Post Draw after Draw. Disabling automatic application-surface presentation requires explicit alpha/blend handling; unsupported absence of a live presenter can leave a blank screen. This is a **viable guarded architecture proposal, not proof of an implemented fix**.

## Four explicitly approved amendments (S1 successor branch ONLY)
1. **Screen configuration — `SCR_screen.gml`**: following the existing logical Wide/Retro/Auto dimension calculations, immediately before current window/surface/view assignments, call a *new, registered* display-policy helper only if committed Enhanced mode, an actual working Integer Fit feature, helper readiness, and scene ownership all satisfy a precise guard. Return early **only after successful and complete display configuration**. On all other paths including Classic, Sharp-only, unsupported/failed Enhanced modes and stale preferences, execute all existing original statements unchanged. Restore any partially changed application-surface state before fallback.
2. **Pause — `OBJ_pause/Alarm_0.gml`**: after `instance_deactivate_all(true)` insert a guarded display keepalive call that reactivates **only the registered Enhanced presenter instance**, not game world objects. The existing `chaos_audio_pause(true)` and `pause=true` sequence must remain unaltered.
3. **Results — `SCR_chaos_results.gml` / `chaos_results_capture_draw`**: immediately after original `chaos_audio_keepalive()` following deactivation, add the same guarded display keepalive. Preserve original capture timing, colour/alpha result and phase/audio sequence.
4. **Death — `SCR_chaos_death.gml` / `chaos_death_draw`**: after original `chaos_audio_keepalive()` following deactivation, add the guarded display keepalive. Preserve original death/results capture, Continue timing and audio ordering.

**Guard contract:** Feature eligibility must be centrally derived from the committed E0 Enhanced state; Classic and all Enabled-features-OFF should never change renderer ownership or window/app-surface dimensions; any uncreated/missing/suspended presenter, failed surface or unconfigured view triggers the original automatic path without black output. Do not activate other actors; do not synthesize gameplay or native audio ticks. The protected Classic tag/source files and all accepted packages remain unchanged.

## Mandatory lifecycle proof, inside S1 (NOT a new Chief-facing milestone)
- First implement the smallest guarded hooks **without disabling automatic app-surface presentation**. Run a focused compiled GameMaker lifecycle probe to confirm the presenter remains active in its own Post Draw event across Pause, results capture, death, Continue, resume, room transitions, selected view sizes, minimize/restore and surface loss. Verify ordering for Draw-time deactivation and subsequent reactivation rather than relying on an End Step watchdog or assuming `persistent=true` prevents deactivation.
- Prove OFF/Classic paths use original screen assignments, active instance set, pause/results/death frame capture, timing and audio request/order; source-host checks alone are insufficient for the new Post Draw owner.
- Only after proving safe ownership may Enhanced manual presentation be enabled. On any error, unsupported renderer, failed shader, missing surface or destroyed presenter, **immediately restore automatic app-surface presentation** before leaving the scene. Manage alpha with nonblended opaque copy matching GameMaker's original automatic surface drawing; restore GPU filter, blend, shader and any changed draw state, and no sample-from-active-target.
- No added native audio owner or edits to original physics/contacts, collision, object ticks, camera input, ROM art or engine target frame rate.

## Scope flexibility — no further paperwork for routine work
Designer-san may make small **same-purpose**, guarded presentation lifecycle adjustments on the S1 successor branch if needed to finish the one approved Enhanced display system (for example, a room-transition cleanup or a fallback guard), while logging any original-file edits individually with before/after diff and corresponding Classic/off proof. This is permission for **presentation-only** integration fixes, not general Classic gameplay rewriting. If the implementation crosses into world simulation, audio, original camera semantics, unbounded surface ownership changes or can't fail safely, stop with one meaningful architectural report.

## Finish the sprint
- W1: keep E2-P1 **SHARP PIXELS** toggle, default OFF, without separate Chief check.
- W2: implement validated **native-grid integer-fit** (not simply nearest filtering the old multiplied target), preserving logical Wide/Retro/Auto, exact visible world and original camera. Treat unimplemented full-screen/resize modes honestly.
- W3: after W2 safety gate only, attempt one restrained attributed **CRT FILTER** ON/OFF, default OFF. Do not port multi-pass Lola or attempt temporal feedback.
- Preserve one Enhanced Options list, clear ON/OFF and **START GAME bottommost**, initial feature defaults OFF. One integrated private Windows/source candidate, controlled visual comparisons, combined Classic/all-OFF parity and native lifecycle matrix, SHA/H: receipts, brief Chief F5 at the **end of S1**. Internal compiles are allowed to prove risky GameMaker API behavior; avoid per-feature Chief builds. No public release, main merge or retag.
- If Integer Fit cannot be safely implemented with these guarded edits, retain accepted Sharp-only as a recoverable checkpoint and report the architectural blocker; do not silently claim S1 complete or ship a broken CRT.

## Canonical refs
[Original S1 sprint charter](ENHANCED_SPRINT_S1_DISPLAY_FOUNDATION_20261105.md) · [E2-P1 visual review](E2_P1_MANAGER_VISUAL_REVIEW_20261105.md) · [Classic source tag/accepted E0](E0_R1_CHIEF_ACCEPTANCE_20261105.md).

**MANAGER GATE: FOUR GUARDED SOURCE HOOKS — GO; S1 CONTINUED. No Chief F5 or new milestone between source-hook proof and combined sprint delivery.**
