# Sonic Chaos — RC2 Manager Engineering Delivery Review
**17 November 2026 · Manager-San #13 · PRIVATE RC2 package ENGINEERING PASS; final Chief release signoff HOLD**

## Decision
**Accept Claude's private RC2 engineering delivery as a recoverable, Chief-testable candidate**. Do **not** declare RC2 released/Chief-approved, merge to main, publish, tag v1.0.0 or integrate Super Sonic. Gameplay code is effectively Chief-accepted F3 (metadata-only identity change). Two remaining release gates:
1. PRIVATE [camera research #10](https://github.com/jamesfarnhamlong/SonicChaos_POC/issues/10): Codex's focused **compiled-native Classic GPZ3 Tails Up+Jump upper-flight-boundary run**; worker now confirmed READY and an exclusive staged-EXE slot released by Claude, per #10 comment 6952819293. Earlier source-host Y97 vs Y98 movement divergence is REAL conditional evidence, not yet confirmed as a compiled-game defect. **Final camera-risk signoff HOLD** pending native result and Manager/Chief decision. No camera patch approved.
2. PRIVATE [R-FS1 fullscreen #12](https://github.com/jamesfarnhamlong/SonicChaos_POC/issues/12): Chief normal-account Enhanced **Alt+Enter** (and Enhanced Pause borderless if needed) must be checked. On SCTest it overflowed; F11 is intentionally Classic-only. Pre-existing display code, not an RC2 regression. If it reproduces on Chief's main monitor, separate release-scope decision; do not secretly patch frozen RC2.

These gates do **not** invalidate Chief 17/17 F1/F2 or 6/6 F3 physical PASS; nor do they permit ignoring a newly proven gameplay mismatch.

## Source, provenance and checked evidence
Reviewed Chief-uploaded `RC2_DELIVERY_REPORT.md`, `RC2_TEST_MATRIX.md`, `RC2_RESEARCH_RISK_DISPOSITION.md`, `RC2_CHANGE_INVENTORY.md`, `RC2_CHIEF_ACCEPTANCE_GUIDE.md`, plus PRIVATE GitHub commit comparison and issue/worker receipts.

- Release branch: `release/v0.99.4-rc2-20261117`.
- Chief-accepted F3 gameplay source: `407377d5d9eeb0748b6b1698f6e377108eb3bf5a`.
- **RC2 frozen GAME source: `342050ee1b237d37e7e17a6f6ea83b16655d0e6b`**, tree `e9cbd45b1e78c039ef257e6c49f46d060f63f8a1`. Exact source comparison changes ONLY 3 identity paths (`README.md`, `options/windows/options_windows.yy`, `SCR_chaos_frontend.gml`) plus verification-only tooling. F3 game elements (physics, bosses, cameras, save schema, audio, art, room order) unchanged, Super `21176dd` NOT merged.
- **RC2 package/verification-only tip: `d064549cda914895c31ffbe62ff211c2d7eeb2b1`**; private GitHub compare from game commit confirms later modifications confined to `verification/rc2/`.
- Identity: `Sonic Chaos v0.99.4-rc2`, Windows `0.99.4.2`. Boot room `ROM_system_start`; canonical save namespace **`SonicChaos`** unchanged.

### Private archive identities / provenance (agent checks, not Manager-local byte verification)
- Windows 8-file ZIP: `SonicChaos_v0.99.4-rc2_Windows_PRIVATE.zip` **SHA256 `98d2290e9a70da42b8fc19a92b427b0e499918dc09615d75292f0259ad57645a`**.
- Complete source ZIP (22/22 authenticated private deps): **SHA256 `903177682a5e102ccc9feb35564a775ec08ad12320ebfec3941d820208862a77`**.
- Bundle `RC2_PRIVATE_d064549.bundle` and manifest/receipt, new H: recovery folder `H:\codex_backup\SonicChaos_20261102_essential\v0994-rc2-20261117`.
- Claude reports all H: package hashes and per-file checks PASS, independent bundle clone/fsck/tip, extracted source ZIP from H: copy, all 22 deps and rebuild. 7/8 runtime files byte-identical. `data.win` differences confined to `GEN8` build header (ID/timestamp): the **initial independent build** listed **42** differing header bytes in `verification/rc2/evidence/RC2_REPRODUCIBILITY_DATAWIN.json` (GitHub independently opened); the **later H: restore compile** report states **41** differing bytes. These are distinct comparison runs, **not necessarily contradictory**; ask Claude to explicitly label both receipts and identify their compared build identities in final notes. Do not assert a deterministic byte-for-byte `data.win` rebuild when GEN8 differs.
- Manager has verified **GitHub content and reported SHA values, not local E:/H: physical ZIP bytes**. Actual byte checks remain Claude's cited receipts.

## Native verification vs accepted F3
- 10/10 exact R22 checks (7 preservation +3 feature) against F3 baseline; 31/31 native F1/F2/F3 cases identical in **gameplay rows**; 6/6 save compatibility cases, 46 checks.
- Across RC2 native tests **76 SCTest runs with receipts: 74 PASS, 2 REFUSED/HOLD by worker-protocol errors**, **zero observed writes** to Chief's `%LOCALAPPDATA%\SonicChaos`. The two HOLDs: wrong manual/fresh-profile mode and manual timeout without operator, **not a proven game fault**. Claude reports successful corrected manual fresh profile and reload, now worker READY and idle, held exclusively for Codex's research slot; research did not cause worker failures.
- Audio delivery lists jitter between runs of the *same* build; F3/RC2 24 same-session A/B reruns show game rows stable. Sound ID differences are not characterised as a new RC2 code change; retain as test measurement limitation.
- Source suite remains **75/178 PASS**, suite-for-suite same as accepted F3; never say 178/178.
- Independently restored 8-file build's boot wasn't rerun, but EXE matched, non-GEN8 content matched. Chief acceptance smoke needed; no fresh full campaign prescribed when source gameplay unchanged.

## Residual research: separate verdicts
**EEZ3 stages 1–2:** Chief played and reported visual PASS in F3. Independent Codex `ad49b16` and Claude original-ROM controlled trace show partial camera-rule parity, **not complete compiled-native chase equivalence**. Codex conditional input-driven stage1 758/758 exact; controlled fixture stage1 502/506 and stage2 502/504 (six counterexamples documented). Claude reports EEZ3 Y-pan exclusive-limit differences in fixtures and a fixed vertical lead 120 vs ROM working96. The latter might affect **high Tails flight**, even if Sonic's ordinary jump cannot reach the divergent vertical interval. No shipping-native material issue confirmed. **Manager proposes bounded, explicit EEZ numerical-risk acceptance** for this private RC2 candidate, not unqualified ROM-parity certification. Chief owns final scope disposition; optional post-RC2 focused Tails flight research may be appropriate, no unrequested gameplay edit.

**GPZ3 Tails flight:** Original ROM logical camera settles Y97 while F3/RC2 logic Y98; both present top115. Actual Tails flight boundary `SCR_cc_tails_flight_edges` reads cameraY. Original ROM and source-host test at worldY121+Up → Y120 with camera97; accepted source-host with camera98 → Y122 (flight ceiling oscillation 120/121 vs121/122). **Compiled-native gameplay effect NOT YET CONFIRMED**; do not classify nonfunctional or definitively P1. One Codex prepared F3 probe under the exclusive worker slot: `--f1case=f3gpzflight --classic --rc1-run=<fresh-id>`, no FreshProfile, diagnostic mode, unique staged folder, validate actual flight state and input alignment. If confirmed, obtain Chief/Manager targeted correction/risk decision; protect visually accepted GPZ3 top115 (latched ROM R9 vs logical Y difference) and Enhanced separation. If not, report fixture/timing analysis.

**SFX research #7**, attract tapers, loop exit, $A5 twist sound and ordinary-level Classic D2-A remain parked, not hidden changes.

## Suggested Chief private RC2 acceptance smoke (once or in parallel with Codex)
1. Extract Windows ZIP to NEW folder; verify full SHA against `SHA256.txt`; boot to normal Classic/Enhanced chooser, inspect v0.99.4-rc2 identity, preserve existing save data.
2. Classic: F11 resize; authentic Level Select cheat; MGHZ3, GPZ3, EEZ3 camera glance; Classic Pause no white hint, Resume/Quit to Title still works.
3. Enhanced: load original Sonic/Tails slot; Features OFF by default in fresh profile, Options and Boss Rush start/quit, pause/display options.
4. **R-FS1 critical:** on Chief's normal Windows account with own monitor DPI scaling, press **Enhanced Alt+Enter** (F11 Classic-only), confirm window fits monitor or overflows; also test Enhanced Pause borderless if relevant. Record monitor resolution, Windows scaling percentage, multiple-monitor placement if failed; screenshots/screensize, cancel and return to window. Do NOT change Windows scaling as a workaround without documenting cause.
5. Quit to desktop/restart and resume same existing slot, no save data reset. Do not require another full campaign.

## Final decision gate
**Engineering package: ACCEPTED FOR PRIVATE CHIEF TRIAL.** Claimed release/recovery integrity PASS with the two minor header comparison receipts to distinguish. **Final RC2/normal-game signoff: HOLD pending Codex GPZ native result and Chief R-FS1 display check**, plus explicit EEZ numerical-risk acceptance if continuing with known incomplete parity. Avoid speculative fixes and unreviewed branch changes. If a material GPZ Tails difference or reproducing fullscreen overflow requires a correction, create a scoped private corrective branch and repackage from a newly identified game SHA only after an explicit Chief/Manager decision. Never modify the already hashed RC2 ZIP in place.

No public release, `main` merge, v1.0 tag or Super R3d cherry-pick without separate Chief signoff.
