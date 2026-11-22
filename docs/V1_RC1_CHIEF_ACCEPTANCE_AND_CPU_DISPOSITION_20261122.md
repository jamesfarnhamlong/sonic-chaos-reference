# Sonic Chaos v1.0.0-rc1 — Chief Acceptance and Processor Compatibility Disposition
**22 November 2026 · Manager-San #13 · CHIEF ACCEPTED V1 PRIVATE RC1 · final personal v1.0.0 promotion separately gated**

## Chief's actual verdict
Chief reports that **all requested v1.0.0-rc1 personal checks PASS**, including the PC which previously crashed after picking Classic/Enhanced and **a third, different-processor laptop that also runs without crashing**. Normal save/Enhanced Super/new twist sound functional/acceptable in Chief's overall verdict. Do not invent measured FPS, precise CPU models, AVX support states on all three PCs, full-game campaign or a separate list of Chief numerical ROM parity checks. There are **three successful physical PCs**, and the decisive former-failure machine now passes.

**Manager decision:** **V1.0.0-rc1 PRIVATE CHIEF TRIAL ACCEPTED**. The versioned integrated game is suitable for the next private personal v1.0.0 release-engineering step. No new gameplay correction or broad regression is required. Exact frozen RC1 source and archives remain protected until separate explicit Chief GO for final `v1.0.0` identity, final production package/hash/H: recovery, tag or `main` merge. This acceptance is not a claim that the final v1.0.0 tagged release exists.

## Accepted candidate
Private repo `jamesfarnhamlong/SonicChaos_POC`, branch `integration/v1-super-r3d-a5-20261121`:
- Work A Classic/Enhanced ROM-authentic `$A5`: `4494210efd6e5a2d3f4aa8a330fcebf811b20b2f`.
- Work B Enhanced Super R3d: `856baa13bbd17353dac1765607921ab7d281ae4c`.
- Version candidate: `c178a939394ae09a63e2a62a7de2b4bedeadff85`.
- Portable PSG C/ **frozen GAME SHA `7ae0bbe3852aa36c6d85b60ecdf6284e7df30412`**.
- Verification/package-only HEAD `b57bb3d05b0f72b10f6d130003badf7d42615879`.
- Private Windows ZIP SHA256 `323807fec25c9b05f379848ca3413a37465e1b47f118c336f834390b3ec22757`.
- Optional isolated SuperDemo ZIP SHA256 `6e19c885e09244b7f0700d67113efa897b4649282b8f13cf6ce6367d561fa46b`.
- Complete source with 22 deps ZIP SHA256 `f5b0d0e41c797769a8f812b4386861e9d1c0bac9ffc02501a28a1e4ad1e4aa01`.
- Private bundle SHA256 `02ae7ed9b6c18ac3543757bb825b96f0c5772030ca3bd57d327d5736bae35d09`.
- E: delivery and H: `v100-rc1-20261122` manifest/recovery 17/17 reported by Claude; Manager GitHub/audit evidence reviewed but local E:/H: bytes not physically rehashed.
- Native 117 receipts: 116 PASS and one corrected probe-table failure not product defect; zero observed Chief canonical AppData writes, 17/17 R22 preservation/features exact, F1/F2/F3/C1 scenarios matching old normal-game build, save6/6, source75/178 unchanged. R3d core parity and targeted act-clear PASS.

## GPZ3: correction to the known-limitations presentation
Chief reminds Manager of an **already-agreed natural-play constraint**: GPZ3 contains a maximum **19 rings/rewards** and the boss act does not carry enough usable rings to reach the **50-ring Super transformation threshold** naturally. The scripted R3d and V1 `r3d-gpz3-route` / tube diagnostics used controlled fixture conditions to test Super-specific high-speed code; they are **not** proof of natural Enhanced NG+ 50-ring transformation in GPZ3. Thus the **85-update blue tube-spin sprite** and Super-speed tube-mouth overshoot in GPZ3 are **fixture-only observations under the existing stage economy, not ordinarily reachable Super gameplay defects**. Preserve them as engineering/edge-case notes, **downgrade release-priority**; do not commission cosmetic code changes solely on that basis. The non-Super high-speed GPZ3 launcher overshoot at 7.0 remains a pre-existing normal-play edge case, separate from Super.

If later data shows a natural 50-ring GPZ3 route or an intentional ring-supply redesign, reopen evaluation with real evidence; none is authorised here. No ring map adjustment as a workaround. The release notes for the final private build should distinguish the scripted fixture from normal play.

## CPU hardware: exactly what the audit establishes
V1 shipping Windows ZIP contains **8 runtime files**, enforced by `verification/v1-integrated/package_v1.py`:
`a3v_policy.json`, `a3v_psg.dll`, `data.win`, `g1d_driver.bin`, `g1d_z80.dll`, `options.ini`, `s3_9b_program.bin`, `SonicChaos.exe`.
**Only two are custom native Windows DLLs:**
- `a3v_psg.dll` SHA256 `511eb693c756c5842ae92f15164c0da8fee77657a1f9e2331e7d9831c50c537b`: recovered exact source and corrected Zig build from host-native (old AVX-512 hard requirement) to `-target x86_64-windows-gnu -mcpu=x86_64` (SSE2 baseline). 1,222 audited instructions, **0 extensions above baseline**. Same exports/imports; 50,802 frames ~37.3M audio samples bit-exact to old build.
- `g1d_z80.dll` SHA256 `2e50d3f84345278907c02878a8b8b469d65af384cc121c7c2113e3e4dcaff3bc`: `bridge.obj` 1,066 and `z80.obj` 7,819 audited project-owned instructions, **0 extensions above baseline**; combined DLL does contain AVX/AVX2/FMA/SSE4.2 instructions in its statically linked Microsoft CRT, which its runtime-dispatch startup is reported to guard. This is a **high-confidence source/build audit**, not formal proof of every CRT control-flow path.
- `SonicChaos.exe`: stock proprietary **GameMaker LTS 2026.0.0.23 Windows VM runner**, not custom compiled C/YYC code. Disassembler finds AVX/AVX2/FMA/BMI2 and one odd disassembly row `movaps xmm16` (possibly misdecoded/unreachable) within its large vendor runtime; it is NOT valid to infer from mere opcode occurrence that these are unconditional requirements, nor to certify every path is guarded without source/control-flow proof. The GameMaker runner reached picker on the previously failing PC even before the PSG fix and runs successfully on all three physical PCs with the portable DLL. Official GameMaker Windows VM documentation says it uses the vendor YoYo Runner, while YYC differs.
- `g1d_driver.bin` and `s3_9b_program.bin` are audio/driver data for a simulated Z80/PSG, not additional executable x64 DLLs; `data.win` contains VM game data, not a separately built host-CPU-native module; JSON/INI are metadata/configuration. **No further custom x64 executable dependencies appear in the packaged eight-runtime-file manifest.**

**Confidence:** no known remaining hard **AVX-512**/host-native compiled dependency among **project-owned Windows DLLs**; boot+Classic+Enhanced previously crashing PC and different-processor third laptop are strong empirical evidence. **Not 100% universal compatibility**: vendor GameMaker binary and MSVC CRT could contain guarded optimised paths or unsupported OS/GPU/device paths, and three systems cannot exhaustively prove every x64 CPU/platform. Do not say a machine without AVX-512 will fail or claim an official minimum instruction set for every version of GameMaker beyond the actual portable DLL audit. No new CPU-compatibility blocker or source rewrite indicated by current evidence. Optional final packaging check: run static PE/import inventory on **final versioned ZIP** and require exactly these eight expected runtime files and the same audited DLL SHA256 / correct portable target; this is a build validation, not a demand for another Chief hardware test.

## Remaining final release gate
Chief accepted **private RC1**. Before changing identity to final `v1.0.0`, creating a final tag or publishing even a private GitHub Release, request a separate Chief authorisation for those actions (and separately for `main` merge). The recommended final action is a **clean, privately archived `v1.0.0` shipping build**, build identity only (not changing game behavior), with new Windows/source ZIP hashes, private Git bundle, E:/H: checks, independent H: restored executable boot, precise release notes (especially GPZ3 fixture-only observation), without repeating the full feature/native campaign.

**Status: V1.0.0-RC1 — CHIEF ACCEPTED FOR PRIVATE PERSONAL RELEASE PREPARATION; final V1 promotion/tag/release still a separate decision.**
