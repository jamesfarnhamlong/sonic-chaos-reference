# Sonic Chaos E0 — Chief's First Build Review: UI Corrections
**5 November 2026 · Manager-san #10 · Historical first E0 review; E0-R1 subsequently Chief accepted**

## Chief acceptance — closure

E0-R1 was subsequently approved by Chief ("yes thats fine") after the corrected five-point review. This is an **historical correction request**, not a currently open hold. [E0-R1 acceptance](E0_R1_CHIEF_ACCEPTANCE_20261105.md).

## E0-R1 candidate delivered (superseding pending correction assignment)

**E0-R1 CANDIDATE DELIVERED — TECHNICAL PASS; CHIEF ACCEPTANCE PENDING (5 Nov):** Designer private branch `enhancement/e0-r1-ui-20261105` at `deccefc0acd822f74b6b26895ec278cdf67a7cee`, exactly one commit after E0 `69450848b1e06fcef7de63f19ae238ff346e479a`, 0 behind (remote independently checked). Only new frontend `SCR_chaos_frontend.gml` and `OBJ_chaos_frontend/Draw_0.gml` differ at runtime from E0; frozen Classic original files and tag unchanged. Corrected SEGA splash waits 2 seconds *after first Draw*, two-mode picker, Enhanced directly opens empty Options and `START GAME` alone at bottom, ESC/pad B Back. Designer 1,767 source-host tests, 1,440 matched core updates and standard Windows compile/smoke PASS; native interactive **foreground focus problem blocked measured real logo timing and keyboard walkthrough**, so Chief must check visible duration, actual controller/keyboard and original intro/audio once. [E0-R1 Manager review](docs/E0_R1_MANAGER_TECHNICAL_REVIEW_20261105.md). **Do not call E0 accepted until Chief reports; GPZ3 visual bug and Enhanced ring scatter remain separate deferred queues.**


## Status
**FUNCTIONAL ACCEPTANCE IN PRINCIPLE — E0 NOT YET CHIEF-ACCEPTED. Two UI corrections explicitly requested.**

Original E0 private successor branch `enhancement/e0-unified-frontend-20261105` at `69450848b1e06fcef7de63f19ae238ff346e479a`; frozen `classic-core-20261105` annotated tag peels to unchanged `3a58912659b48573ac7f2c5c96a02a2211d5e4da`. Designer's automated E0 technical PASS remains valid within its scope; Chief's live UX assessment requires revision before completion.

## Chief's verbatim design intent
- "SEGA appears for less than 1 second!" — splash needs a more substantial visible hold.
- "Better to choose Enhanced, then see the options screen with Start game at the bottom. Nested menus that can be missed are horrible UI choices!"
- "We just need the list with ON OFF clearly marked and then a start game at the bottom."

## Binding correction 1 — splash timing
- Maintain the existing approved static inherited OpenSonicSMS blue-and-white SEGA final-frame, black background, silence, skip-safe, provenance clearly **PC-only**. Do not restore the inherited legacy animated splash room.
- Increase unskipped, *focused elapsed visible time* to **approximately 2 seconds** (a proposed implementation target satisfying Chief's complaint; allow fresh confirm to skip). Record real measured visibility and ensure no initial screen/centering delay steals most of the hold. Preserve focus-loss handling and input-release guards. No audio warm-up/delay hack.
- Accepted E0 `SCR_chaos_frontend` currently gates splash with `cp_s.elapsed>=1`, explaining the roughly one-second impression. Change only the new E0 shell; preserve all frozen preexisting GML.

## Binding correction 2 — replace nested Options navigation
- Mode picker contains **exactly two selectable entries: `CLASSIC` and `ENHANCED`**. Remove separate indented `OPTIONS` row, its Right-only/Up/Down shortcut and confusing third-row nav.
- Confirm **Classic** → existing safe input-release launch → original unmodified cinematic → original title/choice/game.
- Confirm **Enhanced** → directly open one clear **ENHANCED OPTIONS** screen. This screen is the primary configuration and start location for Enhanced, *not a hidden secondary menu*.
- In E0 there are **zero implemented features**: the Options page must accurately say `No additional features installed` or equivalent. **`START GAME` is clearly displayed and selected by default as the bottommost selectable row**. It launches Enhanced after the accepted release/neutral-input guards. Use visible `ESC / PAD B: BACK` help text to return to the two-mode picker, reselecting Enhanced. **Do not put another selectable Back row below `START GAME`: the Chief wants Start Game at the bottom.** Cancel never launches or commits a game.
- For future features, the same page will show the available options as one directly visible vertically navigable list with prominent values `ON` / `OFF`; changes are applied only when a feature really exists and is enabled by the central effective-feature resolver. `START GAME` remains **last/bottom** after all visible features. Off/On rows do not automatically launch. Features not yet implemented are not fabricated at E0.
- A separate Save Game, Boss Rush or similar *mode* may later use a distinct action/page; Chief's demand for ON/OFF is for configurable features, not an instruction to force all game modes into booleans.
- Commit `global.chaosFrontend.mode="enhanced"` only on actual `START GAME`, *not* on entry into Enhanced Options. Default Classic each fresh boot; session mode fixed after launch and retained through original return paths. No in-session switch in E0.
- Keyboard and physical gamepad Up/Down/Confirm/Cancel need discoverable prompts, sane default highlight, and cannot carry a held confirm into original cinematic skip. Nothing in existing original character-selection, sound, pause, Continue or clock/audio needs changing.

## Target visible navigation
```text
        [SHORT SILENT SEGA SPLASH ~2s]
                      ↓
                  CHOOSE MODE
                  > CLASSIC
                    ENHANCED
                    (two selectable modes only)
                      ↓ Enhanced confirm
                ENHANCED OPTIONS
             No additional features installed
                 > START GAME
              ESC / PAD B: BACK
                      ↓ Start Game
                ORIGINAL CINEMATIC
                  ORIGINAL TITLE
                  ORIGINAL GAME
```

Later, when actual features are installed:
```text
                ENHANCED OPTIONS
                CRT FILTER        OFF
                ENHANCED PALETTE   ON
                RICHER RING LOSS   OFF
                    ...
                > START GAME
             ESC / PAD B: BACK
```
These are **future illustrative labels only**; no switches/real enhancement implementations are commissioned here.

## Scope and verification for Designer corrective E0-R1
- Build from exact current E0 commit `69450848b1e06fcef7de63f19ae238ff346e479a` on the existing enhancement branch or a narrowly named successor; keep its source/Windows packages and receipts intact. Do not change frozen tag, accepted D branch or game main. Avoid new parallel game copies.
- Keep E0 change inventory narrow: only E0 `scripts/SCR_chaos_frontend.gml` and other **new E0-specific files if needed**, plus updated verification/report; preexisting frozen gameplay/frontends/ROM sprite bytes and project registration remain byte-identical. Do not rework current audio, game speed or existing `SCR_buttons`.
- Update controlled UI state-machine tests (two-row picker, Enhanced→Options, Options→Start Game, ESC/pad B cancel, held actions, fresh boot Classic, relaunch and mode retention), timer/focus-loss tests and screen-safe layout at 348×196 / actual Retro 290×218, with controlled 256×192 reference.
- Compile **one revised private Windows candidate** with a distinct filename/hash/receipt and validated H: recovery. Use short, focused gameplay/clock/audio regression, not another full cross-product campaign or 60 FPS investigation. Chief tests splash duration, legibility, physical-pad navigation and both start paths. No independent feature toggles exist yet.

**Manager disposition:** request narrowly scoped corrective E0-R1; do not close E0 or start E1 60 FPS until Chief accepts the revised frontend.
