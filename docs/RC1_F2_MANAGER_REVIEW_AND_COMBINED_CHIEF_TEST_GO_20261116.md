# Sonic Chaos — F2 Manager Engineering Review and Combined Chief Test GO
**16 November 2026 · Manager-San #13 · private v0.99.2-f2 candidate, NOT RC2**

## Decision
**GO for Chief's combined F1+F2 physical test band** based on native engineering evidence. F1 and F2 **Chief acceptance remain PENDING**. No automatic RC2 nomination, main merge, public release, tag, v1.0.0 approval or Super Sonic integration. The owner may split testing across short rounds without repeating full campaigns at the outset.

## Inputs examined
Chief uploaded `F2_RESULT_MATRIX.md`, `F2_CHANGE_INVENTORY.md`, `F2_COMBINED_CHIEF_ACCEPTANCE_GUIDE.md`, `F2_DELIVERY_REPORT.md` and local transcript (16 Nov). Manager independently used private GitHub compare to verify exact F2 game source descendancy and post-build branch changes. Local E:/H: ZIP bytes not accessible to Manager, so reported package and H: SHA checks are **delivery claims**, to be verified by Chief if required.

## Identities and integrity
- Private repo `jamesfarnhamlong/SonicChaos_POC`.
- Branch `fix/f2-rc1-presentation-20261116`.
- Frozen F1 compiled-game ancestor `e82af5554a755f2708b9120809ca3bb17ddc1eb7`.
- **F2 game code in Windows ZIP**: `5d045ae0bba8dcbfa3f220c8e96d78baaa4fc22e`, tree `d5d35c546c26f201f35257353ba4ea2dcd28974e`.
- Delivery claims later verification/source package commit `29f6f00d19e566b51a8e8a81cb501fb0fa64637e`; GitHub compare from frozen game commit to both package commit and current F2 branch showed **6 later commits with changes only to 14 files under `verification/`**, not gameplay resource paths.
- Windows ZIP `SonicChaos_v0.99.2-f2_Windows_PRIVATE.zip`, SHA256 **`45a3debd66d120c5ca67c61cd36879f0ac23c5d06b8d8eb45faceeca8893ba38`**. Source ZIP `SonicChaos_v0.99.2-f2_Source_PRIVATE.zip`, SHA256 **`56d592b09613bca1dced9505b198e44e54c766fc4b519e16fe182bf754c481ed`**. 8 runtime files, 10,008 source files and all 22 private dependencies, per delivery report. Independent restore/H: evidence **reported PASS** at `H:\codex_backup\SonicChaos_20261102_essential\v0992-f2-20261116`. Manager has not personally read E:/H: artifacts.
- The F2 package uses the original `SonicChaos` canonical save namespace, no migration/reset. **Chief's two completed RC1 campaigns/saves must remain intact**. Extract private ZIP to a NEW Windows folder rather than overwriting RC1 or F1.

## Verification and limitations
- **F2 7 issue dispositions:** SC-RC1-14 original ROM Zone Select (ROM cheat/graphics/flow ported; native pixel-exact tested and confirm into MGHZ2); 15 Classic white hint removed (ROM pixel-exact); 11 Save TV completed THZ / incomplete frontier (**source checks plus native smoke; focused real menu Chief test outstanding**); 12 six authentic Pause previews; 13 Enhanced ending white flash fills wide margins (Classic unchanged); 04 GPZ fade transparent-backdrop fix, timing unchanged; 02 AQZ booster **no source change** after original ROM live-VRAM pixel comparison confirmed red/pink colors authentic (0 of 1024 pixels different).
- F1 carryforward: all TEN F1 tickets, **17/17 compiled-native cases same as accepted F1 engineering outcome**. Seven preservation runs exact against original RC1. Boss/Boss Rush differ only where F1 already intentionally changed pogo clear and AQZ HUD. Source-suite **75/178 pass**, identical to F1 with no formerly RC1-passing test newly failing; inherited limitations must not be erased/claimed 178/178.
- Native F2's first-cut Zone Select room mistakenly became startup room; separate fix `cd0f361` moved it last in room order, native corrected build starts normally; F2 reported total **77 SCTest runs, zero FileSystemWatcher Chief AppData write events**. SCTest disposable files remain isolated; do not remove SCTest until follow-up repairs and Chief testing close.
- The ROM's *second* cheat opens a Sound Test but **is not ported**, explicitly outside F2's SC-RC1-14 Zone Select scope (potential future choice; no retroactive scope creep). Natural loop approach, SEZ3 big-drop fight, Classic full boss cameras and Save TV focus still require owner actions. A reported native input stand-in is probe-only, not in shipping runtime.

## Chief recommended staged physical testing (no new full run yet)
**Band A — high-risk startup/Classic, ~targeted scenes:** verify Windows ZIP SHA, extract new folder, launch to normal frontend (NOT Zone Select room). Classic title has no white hint. Enter authentic cheat **Up Up Down Down Right Left Right Left, then Start**, see original `- ZONE SELECT -` and 6 zones/acts, confirm at least MGHZ2 and ensure chosen character/game start, return to title normally. Try Classic GPZ3 complete boss with visible floor; test TV landing/still/jump/break, SS1 TV start. Check no data loss/saved Sonic/Tails slots still load.

**Band B — Enhanced presentation/save/results:** open incomplete vs completed Save TVs (incomplete frontier, completed THZ1), use a spare slot for erase/restart, Pause all six zone previews, complete GPZ1/GPZ2 fade with no black/white hold, Sonic EEZ3 ending white flash widescreen including actual ending, optional Tails; confirm AQZ booster remains original red/pink (no-change intentionally).

**Band C — gameplay F1 carryover:** naturally reach AQZ1/2 Sonic loops; THZ1/THZ2/EEZ2 crumbling ledges; GPZ1 Features ON invincibility→Sneakers zone music, GPZ3 boss invincible entry, SEZ3 pogo falling boss damage and Tails victory landing, boss→results music, AQZ3 last boss HP pip + Boss Rush music, all Classic boss cameras. Some checks can be reached using the authentic original Classic cheat; Enhanced tests via existing completed RC1 saves and regular routes.

Record PASS/FAIL/UNTESTED per ticket, character, act, mode, Features state, approximate world spot and reproduction; no assumption that untested = pass. Report early P1 regressions as soon as found; Agent may prepare an isolated corrective branch. Only after Chief approves combined behavior may we nominate **RC2** and separately decide Super Sonic NG+ integration. No need to force a week-long replay immediately.

## Operations
- Keep working RC1 and F1 ZIP/backup and F2 SHA manifests and private H: recovery. Keep chief canonical AppData saves from fresh completed RC1 runs.
- SCTest standard Windows account/worker window may be closed when inactive, but do **not** remove SCTest account/profile or H: evidence during any ongoing corrective tests.
- Preserve the parked post-test housekeeping doc and sound `$A5` research / closed MGHZ2 false positive. No automatic merge of Super Sonic R3d `21176dd03138b155412bef9256306437275414ca`.

**State: F2 engineering GO for Chief targeted combined trial. RC2 and v1.0 HOLD.**
