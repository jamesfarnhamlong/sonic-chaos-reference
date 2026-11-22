# Sonic Chaos v1.0.0 — Final PRIVATE Release Accepted and Closed
**22 November 2026 · Manager-San #13 · Chief final private-release GO satisfied; GitHub release VERIFIED**

## Final status
**RELEASED — PRIVATE PERSONAL v1.0.0.** Chief gave express final release GO after passing the integrated v1.0.0-rc1 on **three physical Windows PCs**, including the former AVX-512 crash PC and different-processor laptop. Claude subsequently built, verified, tagged and published **Sonic Chaos v1.0.0** exclusively in the existing **PRIVATE** repository `jamesfarnhamlong/SonicChaos_POC`.

**Authoritative private GitHub Release:** https://github.com/jamesfarnhamlong/SonicChaos_POC/releases/tag/v1.0.0 (published 22 Nov 2026, non-draft, non-prerelease). Manager **independently queried GitHub's repo metadata**, release/tag and asset digest API, commit comparisons, delivery report, QA/restore and package receipt. GitHub reports **repo visibility PRIVATE**, five published assets and per-asset SHA256 digests matching the agent's claimed Windows/demo/source files. Manager did NOT separately read Chief's E:/H: local files nor independently redownload the release; Claude states it did both and checked content byte-for-byte.

**No PUBLIC release and no production `main` merge.** GitHub API confirms current main still `03a6e7dfcaed519993a9422cc35b60753d5d3dbd`. GitHub release API's generic `target_commitish: "main"` field MUST NOT be misread as the true tag target: independent `refs/tags/v1.0.0` is annotated tag **object `64c8f240e4b91c8688aadf0a939d8ca10bc810cc`** and peeling the Git tag proves its target is **`467c94477422ecff51bc54265adf67b5346445f5`** (receipts commit). The repo is private with only the owner as collaborator per Claude's inspection; privacy is still determined by repository access controls, not public distribution.

## Immutable final identities
| Item | SHA or identity |
|---|---|
| Branch | `release/v1.0.0-private-20261122` |
| **Compiled v1.0.0 GAME** | **`eb35c2401003a98b490e961ad01b593e671e45a5`** |
| Game tree | `54ba99843b9a6dd91d5324de0d48db2adfcefd52` |
| **Source ZIP & bundle PACKAGE commit** | **`d1ffa8e052d243c9590ac3640db2eed8742a528d`** |
| Package tree | `6cfec90a893e265b25f9bd8927e137d3186d3cfb` |
| Final tagged receipts commit | **`467c94477422ecff51bc54265adf67b5346445f5`** |
| `v1.0.0` annotated tag object | `64c8f240e4b91c8688aadf0a939d8ca10bc810cc` |
| Game Version | `v1.0.0`, Windows file `1.0.0.10` |
| Real save namespace | `%LOCALAPPDATA%\SonicChaos` (unchanged) |
| Separate SuperDemo save namespace | `%LOCALAPPDATA%\SonicChaosV1Demo` |

Manager independently compared the final GAME to accepted v1.0.0-rc1 GAME `7ae0bbe3852aa36c6d85b60ecdf6284e7df30412`: **exactly three metadata/identity paths** changed (`README.md`, `options/windows/options_windows.yy`, `scripts/SCR_chaos_frontend/SCR_chaos_frontend.gml`), no gameplay/audio/art. Compared final GAME vs TAG receipts commit: **only `verification/v1-final/`** changed (2 commits). The private tag message explicitly records the true GAME and PACKAGE SHAs. Original RC1, RC2-C1, experimental Super R3d and their recovery copies remain intact.

## Final artifacts and GitHub upload receipts
| Artifact | SHA256 | Distribution |
|---|---|---|
| **Windows v1.0.0 ZIP** | **`03322f3bef2b7d988813ae35fac881cae76d4a4ba4cd576d1db92c7301646ae3`** | PRIVATE GitHub Release, E:, H: |
| **Optional isolated SuperDemo ZIP** | **`020f5b484d47ff9df4dbe998d9af9a38045279c32116a10a7196da1c20e79d1a`** | PRIVATE GitHub Release, E:, H: |
| **Complete source ZIP (+22 private deps, 10,778 source files)** | **`2bba06a0a0c6d551cb24260c1dc039d9cc3c9eaba186807e46b518feaba018c5`** | PRIVATE GitHub Release, E:, H: |
| **Private Git bundle** | **`9d35f0093c296c74f940d493a90cb31a6547e8d474ea33a114094cac22a351d2`** | E:/H: only, intentionally not on GitHub Release |

The GitHub Release contains **five assets**: the three ZIPs plus `V1_FINAL_SHA256.txt` and `README.txt`. GitHub's asset digest API matched the published ZIP hashes shown above. Claude separately redownloaded all five assets and reported byte-identical content. The **final E: local delivery** is `management-audits/v1final-20261122/delivery/v1.0.0`; independent **H:** recovery `H:\codex_backup\SonicChaos_20261102_essential\v100-final-20261122`. Claude reports 16 E: and H: files byte-identical with complete SHA manifest; no earlier package overwritten.

## Quality, recovery and source parity
- Final `data.win`: identical to Chief-approved RC1 gameplay except two version strings, their relocated references, Windows version field 1→10 and GEN8 header. Textures/audio content chunk identical. `SonicChaos.exe` differs only in version-resource identity. Other runtime files identical; two custom native DLLs preserved with exact portable `a3v_psg.dll` SHA256 `511eb693c756c5842ae92f15164c0da8fee77657a1f9e2331e7d9831c50c537b` and `g1d_z80.dll` SHA256 `2e50d3f84345278907c02878a8b8b469d65af384cc121c7c2113e3e4dcaff3bc`.
- Focused final production checks all PASS, isolated SCTest, **zero observed Chief AppData writes**: actual shipping boot; Classic and Enhanced boot/music; 25 Super probe scenes **33,365/33,365** gameplay rows identical to accepted RC1, same 71 `$A5` twist requests; 2,185/2,185 act-clear rows; 6 save cases with required fixtures; optional SuperDemo boot; **H:-recompiled/restored executable BOOT PASS**.
- **IMPORTANT save-harness correction:** earlier v1.0.0-rc1 description of save suite as 6/6 worker PASS was overstated: 4 probe-internal failures occurred because runner omitted required fixtures. Without them final v1.0.0 reproduced the same 2/6 internal pass. Agent subsequently staged the missing hashes/fixtures into the unchanged save test build, reran under fresh IDs and **all six internal check groups passed** (fresh, restart, legacy, import, import-restart, final-restart). This is a corrected evidence/test setup issue, **not** a save-code/gameplay fix. Preserve historical admission, don't rewrite RC1 results.
- A fresh-profile SCTest job was **refused** in a mode not allowed by worker policy, caused HOLD and operator reset; not retried. No Chief save writes. Fresh-slot probe and real Chief RC1 three-PC acceptance cover relevant functionality.
- H: restore verified **10,778 source files, 22 private dependencies, and bundle tip/tree** with zero tracked source edits; restored Igor LTS 2026.0.0.23 build matches **7/8 runtime files exactly** with `data.win` differing only **42 GEN8 build-header bytes**, all game chunks identical; **restored exe boot PASS**.
- Source suite inherited **75/178** (103 historical failures), not fully green. Previous V1 RC1 native work 116 PASS/117 receipts (one corrected harness HOLD), previous Chief 3-PC acceptance retained by identity-only proof; no artificial full-game retest demanded.

## Feature scope and documented non-blockers
Final release includes true Classic 256x192 behavior, Enhanced save/option system, Boss Rush, ROM-authentic per gate-contact twist `$A5` sound, six-emerald Enhanced Sonic NG+ Super Sonic with transformation, faster physics, ring drain, legacy art and 42 new AQZ gold loop sprites, plus corrected portable x86-64 PSG driver. Don't claim 100% universal CPU support: two custom x64 DLLs audited, stock GameMaker binary proprietary, successful physical RC1 tests on 3 PCs including AVX-512 crash-PC.
- **GPZ3 natural limit:** only 19 collectible ring/rewards at most and 50 required to transform; blue Super tube spin/high-speed launcher in GPZ3 were *synthetic-fixture* sightings, not normal-play V1 release defects. Do not re-open on that basis.
- Legacy spring `$A6` potential mailbox mismatch, GPZ pipe seam/loop/attract numerical watch items, inherited source 75/178 and player residuals remain historical watch, not silently claimed perfect ROM parity.
- **No new gameplay defect** identified in final identity-only build or Chief RC1 real-world tests. No new user campaign required just for final strings.

## Manager milestone disposition
**FINAL V1 PRIVATE PERSONAL RELEASE — VERIFIED AND ACCEPTED AS DELIVERED** (Chief final release GO prior to publication and final integrity receipts now independently reviewed). Mark PRIVATE production integration #14, Super R3d integration #3 and final release #15 **closed / completed**, with detailed issue history and test-harness correction retained.

**No main merge, no public distribution, no deletion of archives/real saves, no new features or edits required.** Any future update should be a newly versioned branch/release without mutating v1.0.0 or its tag. The current release is sufficient as the finished personal milestone.

**User link:** https://github.com/jamesfarnhamlong/SonicChaos_POC/releases/tag/v1.0.0
