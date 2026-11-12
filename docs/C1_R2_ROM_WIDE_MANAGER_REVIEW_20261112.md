# Sonic Chaos — C1-R2 ROM-wide Classic Fidelity: Manager Review
**12 November 2026 · Manager-san #11 · ISOLATED RESEARCH TRIAL TECHNICAL PASS · PRODUCTION CLASSIC INTEGRATION HOLD**

## Actual reviewed evidence
Chief uploaded the full private **`C1_R2_ROM_WIDE_FIDELITY_20261112.md`** report to Manager; its text was inspected. The linked machine-readable relative attachments `c1-r2/coverage-matrix.json`, `c1-r2/reconciled-findings.json`, raw traces, candidate ZIP and local receipt were **not uploaded**, so Manager has not audited their bytes or independently reproduced Windows/ROM checks. Do not overstate this manager review as a binary inspection.

- **Private source/branch:** `classic/c1-r2-rom-wide-gap-closure-20261112`, exact source `316125f6f280f24a7a8af507155d9dfe86954cea`, parent isolated C1-R1 `bc32e706691666b420c4daeff87338ec865190e5`.
- **Report:** `E:\AI\Codex\Sonic Chaos\releases\C1_R2_ROM_WIDE_FIDELITY_20261112.md`
- **Windows:** `E:\AI\Codex\Sonic Chaos\releases\SonicChaos_Windows_20261112_C1_R2_CLASSIC_FIDELITY_TRIAL_PRIVATE.zip`
- **Complete source:** `E:\AI\Codex\Sonic Chaos\releases\SonicChaos_Production_20261112_C1_R2_CLASSIC_FIDELITY_SOURCE_PRIVATE.zip`
- **Source/ZIP hashes and recovery receipt:** `E:\AI\Codex\Sonic Chaos\releases\SonicChaos_20261112_C1_R2_CLASSIC_FIDELITY_RECEIPT.json`
- Independent H: recovery and packaged Windows startup **reported verified by Designer**, not rerun by Manager; all 22 ignored runtime/sprite source dependencies preserved. C1-R1 and immutable S4–S6 packages and frozen old Classic tag unchanged; S7 no-change untouched. No merge/push/tag, release, production Classic replacement or Chief in-motion test.

## Original-ROM correction accepted in bounded scope
**C1-04 / C1-15 first Special Stage instance registration:** single code file `objects/OBJ_chaos_zone/Create_0.gml` changed, **Classic-only**. Native constructor seeded correct raw ROM Y, but did not publish corresponding registration; subsequent `SCR_chaos_adapter_step` imported `instanceY - chaosAnchorOffset` (offset5px) unconditionally. Original ROM traced on actual natural hundred-ring SS entry; first coordinate divergence at update1 `registration_import`, BEFORE collision/movement, **−1280 units 16.8 = −5 pixels**. After registering already seeded core once, GameMaker matches original raw Y at first import in SS2=1838, SS3=622, SS4=366, SS5=878. SS1=118 unchanged negative control. Eight compiled stage/character corrections and two SS1 negative controls; Tails Special Stage entries are developer stress, NOT naturally reachable retail gameplay. **No positional fudge, map modification, floor snap, physics/collision change, or Enhanced change.**

**NOT fully closed:** original initial player state0 vs current GameMaker state1 abstraction, camera pending work phase, SS1 Y15 vs ROM14, SS3 R2 settled camera Y519 vs ROM518 (R1 Y516), SS4 look-down, SS5 update11 camera X30 vs ROM31 and inherited failing SS5 verifier. No automatic ±1 pixel patch authorized.

## Research-grade ROM findings, no speculative implementation
**Object pool C1-05:** ROM shared first16 slots, `$FE/$FF` pending entries not instantly reusable; filling 0..15 prevents lost-ring scatter even when 16..18 available. Current GM independent lost-ring list lacks occupancy of other owners: confirmed model gap. But controlled original GPZ `$51` boss scheduler over 1600 updates peaked at six active first16 slots, and four sampled hits at updates233/387/500/1000 all allocated seven rings. No genuinely reachable owner-contention failure yet demonstrated. **Do not blanket-cap dropped rings or broadly refactor pool** without a naturally reachable ROM/native owner map and actual shortage timeline.

**Attract C1-06:** Original idle execution observed three genuine replay sequences THZ Sonic, GPZ Tails, SEZ Sonic; 1042/1016/1036 original player-engine entries, not the documented 1080-loop budget. Need align loader/interrupt/lag/player dispatch before implementing replay in GameMaker; do not synthesize generic scripted demo.

**VDP C1-11:** Original R0=`$26`, bit5 masks left8 pixels on 256×192 raster, 8×192=1536 pixels. The backdrop varies (THZ blue, SEZ dark blue, title/loading black); current Classic lacks equivalent scene-aware final presentation mask. **Do not paint an unconditional black stripe**. Find authentic palette ownership, final draw pass and sprite limits; evidence is approximate NTSC renderer, not true physical Europe/PAL50 or VDP cycle-exact proof.

## Explicit verification scope
- C1 register reconciled **382 coverage entries, 16 findings**, with 01/02 closed in R1, 03/07 canonical quirks, 04/15 PARTIAL, 05 model gap, 06 original demos observed/port missing, 11 renderer policy divergence/coverage, other coverage/test-limit statuses retained. Manager read the table in the uploaded report, **not** the complete linked machine-readable JSON.
- Enhanced S6 native exact: **4,554 stage-room+5,988 boss/ring = 10,542 bounded state samples; 46+12+44 = 102 native/full-output protected-S6 image comparisons**. These do not imply all Enhanced routes prove exact.
- Ordinary Classic 3,564 sampled states match R1 unchanged. All **23 rooms × two characters × original 1/2/3× = 138** captured native256×192/int-scaled outputs PASS.
- Native programme/SFX testing 68 original contexts /32,640 ordered PSG changes exact; NOT all compiled SFX request timing or VBlank/PCM.
- Source-host C1 contract 1,095 PASS and new SS-entry60 PASS; SS1–SS4 gameplay-host PASS. **SS5 inherited clock-camera FAIL remains FAIL**. No full natural campaigns/physical-controller test or completed VDP/PAL timing proof.

## Verdict and next work
**C1-R2 technical source correction PASS; ROM-wide complete Classic certification HOLD; integration into current production Classic HOLD.** Chief's strict mode contract remains: if the ROM does it, Classic reproduces it; NO QoL, workaround without ROM proof, or hidden widescreen fairness. Existing **Enhanced Wide348×196 S6 (`47c501ecb994a4fcb1eeac1c29793f3f1142a304`) stays exact**, including accepted PC fairness, with *new optional gameplay QoL OFF*. User's separate S5–S7 combined Windows acceptance uses immutable S6, unrelated to C1 trial. Original Classic historic freeze tag must not move.

**Recommended next C1-R3 scoped phase:** first resolve the **Special Stage loader/first-update camera ownership/phase** using authentic ROM update-order evidence across SS1–SS5. Reproduce and disposition SS1 Y14/15, SS3 original Y518/R2 Y519, SS4 look-down and SS5 original update11 X31/R2 X30; fix only proven Classic source/phase errors, no single-pixel shims, retain failing tests until source correction. Shared ring/other-object slot contention, authentic demos, palette-aware left-eight VDP mask/cycle timing and 18-act edge cases remain separate documented gates; research may continue, but **do not use a broad allocator rewrite or port attract demos in this tightly scoped R3**. [R3 binding Designer scope](C1_R3_SPECIAL_STAGE_CAMERA_PHASE_SPRINT_20261112.md).

Before future integration, require C1 technical source/audit completion, preserved S6 Enhanced raster/state parities, safe source conflict assessment, and an actual Chief review of one integrated candidate. No automatic C1 merge or release.
