# M5 developer Sound Test contract

Research design only, 24 October 2026. POC private visibility and authenticated
access were verified through GitHub; accepted source was inspected at
`11bff34356d5f5d979218896dc95fdc4bb265eae`, including
`SCR_chaos_debug_select`, `SCR_chaos_audio`, `SCR_buttons`, and
`OBJ_chaos_debug_select` Create/Step/Draw events. No GameMaker source changed.

The current menu contains 68 music/SFX rows, five preview WAV mappings and no
control category. Draw checks preview availability; the preview request helper
returns true even for a missing preview, so PLAYING can be misleading. The
historical82 label still says title and99 has no name. These are observed
source facts, not a new native UI test or criticism of accepted M4 scope.

## Catalogue and display

Use all 70 rows from [catalogue.json](../data/m5/catalogue.json), numeric-ID
ascending within Music(31), SFX(37), Controls(2). Preserve an ID row even if it
shares PCM. Each row displays hex ID, verified requesting-event label or
`Unknown $XX`, category, availability and alias status. Context labels describe
source events, not invented acoustic names. A header/PCM target is not proof
of original gameplay use. Details show “source request site found” separately
from “observed in original gameplay”; unknown observation is never USED.

Title99 and Character selection82 are distinct.90 details include opening and
EEZ3; audition uses the full new90 composition, not the short opening preview.
M4 finite opening preview/tail fixtures can remain a separately marked
diagnostic context, never an alias substituted for the full entry.

9B–9F are visible, disabled **EMPTY STREAM / NO VALID MUSIC** rows. All music
channels immediately terminate; the leftover tone2 period-zero register state
is not a reason to offer an audible song. Their actual analogue/DC output is
unresolved.00 is **CONTROL / EMPTY MAILBOX, DOES NOT STOP**; F8 is **CONTROL /
RESET ALL**. No PCM file for either. Unknown8E and the three no-site SFX
A8/B2/C1 remain playable once authenticated production confirms their output;
absence of a gameplay site does not make a nonempty stream unavailable.

A8/C2, BB/C4 and BC/C0 may share verified solo PCM but retain separate
priorities and semantics. Display `same solo output as $XX; priority differs`
where applicable. Never say “same ID,” and do not count them as missing.
Before production, show NOT PRODUCED; bad manifest/hash/format shows INVALID
ASSET. Do not treat a missing asset as successful playback or substitute an
inherited approximate SFX. Historical AUDIO-0 previews remain optional,
explicit PREVIEW tools with their old hashes, outside authoritative audition.

## Controls and ownership

Keep existing navigation conventions: keyboard arrows / pad D-pad navigate;
Left/Right cycles three categories, Up/Down wraps rows, fresh Space / Xbox A
(`gp_face1`, global `btSpacePress`) sends Play. Enter / pad Start or S sends
Stop. Esc / keyboard A / Xbox B (`gp_face2`, `btAPress`) returns to the
developer menu. This reflects inspected `SCR_buttons`; keyboard A is Back,
not the same as the physical Xbox A button. Render correct help text.
All actions use fresh edges, so a held button entering the page cannot play
or dismiss immediately. No new controller binding layer is needed.

Selection alone never plays. Play submits the selected numeric ID through the
existing persistent audio owner; repeated Play submits another request even
if the ID is unchanged. Music replaces music/effects and restarts from header.
SFX uses current original shared priority/slots, so it can be dropped. Status
comes from the dispatch result: QUEUED, PLAYING/RESTARTED, PRIORITY DROPPED,
FINISHED, CONTROL APPLIED or unavailable reason. Retain request order/slot
trace for developer inspection. No separate `audio_play_sound` preview owner.

Keep music running while navigating to SFX, enabling real channel arbitration.
For guaranteed isolated audition, Stop then Play; do not secretly clear
priority before every SFX.00 clears only the pending audition mailbox and
reports NO AUDIO ACTION. Selecting F8 submits its original priority57 request:
report PRIORITY DROPPED when blocked. The dedicated **Stop** invokes the
existing administrative reset/queue flush and always resets all audition slots,
gates and pending audio, including during a high-priority effect or after
finite completion. This PC developer action is deliberately distinct from F8
numeric admission; do not imply that the original driver exempts F8.

Entering the Sound Test follows existing debug-open stop behavior; no normal
game owner is destroyed or duplicated. Exiting stops audition, clears pending
test requests and returns to the existing developer menu. Returning to title
or launching a level then issues that scene's normal entry request afresh.
Do not restore an arbitrary saved song position or leave test music in gameplay.
Keep accepted pause, room deactivation and retiring-buffer shutdown fixes.

## Acceptance specification

Automate exact70 unique IDs/category counts, labels99/82/90, disabled empty
rows, controls not WAVs, alias rows with their own priorities, missing/corrupt
assets refusing success, edge-triggered navigation and repeat Play. Exercise
all playable IDs via manifest/owner tests; do not require Chief to audition70
rows manually. Check dropped requests, cross-slot coexistence, partial
replacement, F8 and return to title/level. Seek loop boundaries diagnostically
rather than waiting22 minutes for a boss loop.

One later short native session should sample every ownership class, a
two-stream effect, an alias pair with different priority, finite99, full90,
disabled/control rows, pad/keyboard navigation, Stop/restart, pause/back and
normal scene return. This is a proposed integration acceptance gate; none of
these new M5 UI behaviors has been implemented or human-accepted here.
