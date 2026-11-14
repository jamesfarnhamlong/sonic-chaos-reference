# Sonic Chaos — RC1 Post-Test Housekeeping / Low-Mess Closeout
**14 November 2026 · Manager-San #13 · PARKED UNTIL AFTER CHIEF'S RC1 WEEK AND ANY FIXES**

## Why this is parked
Chief wants the 0.99 private test to be clean and later remove the disposable Windows `SCTest` user/profile and sprawling temporary audit artifacts. Previous R22 testing polluted Chief's live `%LOCALAPPDATA%\SonicChaos` with thousands of PNG/JSON diagnostics. Chief made an independent full backup and chose an intentionally new canonical RC1 live profile; engineering runtime checks were executed as a separate standard Windows user `SCTest` with zero observed writes to Chief AppData. **Do not remove SCTest during the week or while follow-up repros/repair checks may still need it.**

## Protected/retain by default
- **Final certified RC1 frozen code** `ad499c9b483776714cf18683ed9a23aa0ed1e668`, final private report-only HEAD `b6fecd2522f7805e4089a74957027fb03588cb0e`, R22 historical source, protected production main and Classic freeze tags/branches.
- Two **final** private `delivery-final` RC1 ZIPs, SHA256.txt, final Git report/receipt, source/dependency manifests and clean build proof: Windows SHA256 `21708c14b262d8b9634abbfdda811190b6e594d9473333061e07e7dc02885150` and source SHA256 `9010573c7f378c03e238bcd9bf947a1a1d1761b073a2338fdee3ed9c591b6adb`.
- **H: independent source+runtime recovery** `H:\codex_backup\SonicChaos_20261102_essential\v099-rc1-20261114\final`; private rights/custody metadata and required historical preservation evidence.
- Chief's separately backed up original 5-emerald Sonic campaign and prior AppData/config snapshots, and **new RC1 campaign saves** created during the owner's week. Never delete these in a general junk cleanup.
- Compact named evidence supporting actual failures discovered during the week, hashes, logs and screenshots needed for regressions.

## Cleanup after owner gives explicit post-test GO
1. Finalize RC1 acceptance/findings and note any open fixes; determine whether a follow-up candidate needs SCTest for repro. Ensure all required private Git/H: backup, final delivery and Chief new saves are protected and restored/tested as appropriate.
2. Confirm SCTest has signed out and no subprocess/test runner uses that account. Windows **Settings > Accounts > Other users > SCTest > Remove > Remove account and data**. Removing account+data removes its local Windows profile, including isolated game saves and diagnostics, but not shared `C:\Users\Public` staging directories.
3. Identify the **exact** shared SCTest-only staging/test folder actually created (e.g. `C:\Users\Public\Documents\SonicChaos-RC1-Test` only if it exists and belongs solely to the harness), then remove *only that path* after archiving selected evidence. Never blanket-delete `C:\Users\Public`.
4. Identify scratch build outputs, superseded R22/R21/R20 trial ZIP copies, intermediate unshippable RC1 ZIPs, and enormous captures under the explicitly approved `management-audits` scratch dirs. Record estimated counts/bytes and the protected-list first; Chief may authorize deleting these **exact expendable paths**. Keep final `delivery-final` and authoritative receipts intact; no automatic sweeping of `E:\AI\Codex` or `H:\`.
5. Verify Windows RC still launches from its independent clean install folder, and check Chief's current live `%LOCALAPPDATA%\SonicChaos` normal save remains available. Final summary: account removed, paths deleted, bytes freed, evidence/backups preserved.
6. Avoid creating another large diagnostic dump merely to verify deletion. Small `Get-ChildItem`/hash/status checks are sufficient.

## Current status
**No cleanout of SCTest or E:/H: reports has been executed or authorized yet.** RC1 engineering PASS; Chief's week-long playtest has not been reported finished. This is a *future, reversible-where-practical, scoped* cleanout task, not an instruction to delete immediately.

See [live RC1 charter and owner testing](V099_RC1_PRIVATE_BUILD_CHARTER_AND_OWNER_WEEK_TEST_20261114.md), [ROADMAP](../ROADMAP.md), [MEMORY](../MEMORY.md).
