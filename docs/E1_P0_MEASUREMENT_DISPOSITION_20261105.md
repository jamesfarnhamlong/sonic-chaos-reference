# Sonic Chaos E1-P0 — Manager Disposition: Presentation Measurement Inconclusive
**5 November 2026 · Manager-san #10 · C — INCONCLUSIVE · E1-P1 HOLD**

## Decision
Designer completed the approved **external, read-only E1-P0 baseline measurement attempt**. **Accept the report as an honest measurement-blocked closeout.** No credible displayed-frame intervals were captured, so **neither stable 60 FPS delivery nor a frame-pacing defect has been demonstrated**. This is not a failed performance test of the game.

**Manager decision:** E1-P1 alternate timing method / interpolation / any code pilot remains **HOLD**. No debug FX switch, GameMaker timing changes, `game_set_speed` change, source editing, new Windows candidate, display-mode change or native audio change is justified. Park further telemetry until there is a validated, authorized capture route. Research-only planning for scaling/CRT may be considered separately without representing E1 as solved.

## Verified source baseline and local report
- Accepted private Enhanced shell branch `enhancement/e0-r1-ui-20261105` independently still points to `deccefc0acd822f74b6b26895ec278cdf67a7cee` on GitHub.
- Original frozen Classic annotated tag `classic-core-20261105` remains tag object `87f13ef24877519c820d4d2612b58279a43578e6`, peeling to accepted original `3a58912659b48573ac7f2c5c96a02a2211d5e4da`; frozen production and game `main` refs unchanged. These remote refs were rechecked 5 Nov.
- Designer report `management-audits/e1-p0-presentation-baseline-20261105/REPORT.md` verified locally the immutable accepted Windows ZIP `SonicChaos_Windows_20261105_E0_R1_PRIVATE.zip`: **SHA-256 `a087b6b1900a4160bfa3febc3abdf67fd54ce54d1f00f6c0ac13e0b124adaf6b`** (matched private receipt). Manager did not hash local Windows ZIP or touch H: directly.
- Windows 11 reported build 26300.9818 / 26H2, registry RTX 4070 driver `32.0.16.2101`; `EnumDisplaySettingsW` reported desktop **1920×1080 at nominal 100 Hz**. Those are host settings, not a measured game frame stream. No game launched during collector availability probes; no game view, VSync override, VRR, fullscreen mode or actual scanout independently confirmed.

## Capture/tool evidence
- Existing NVIDIA FrameViewSDK `PresentMon_x64.exe` v`1.9.12728.0`: `--help` succeeded; a bounded availability attempt targeting `SonicChaos.exe` returned code `1` with no CSV, stdout or stderr. Crucial qualification: **SonicChaos.exe was not running** during this probe, so the exit cannot alone establish why capture failed or a broken PresentMon install. It does establish zero usable timing records from this authorized attempt; do not invent diagnosis.
- Existing WPR 10.0.26100 `wpr -start GPU -filemode` (non-elevated) returned **`0xc5585011`** with 'Failed to enable the policy to profile system performance.' Follow-up WPR status showed no active recording. Do not claim a precise root cause beyond current capture context/policy failure; no elevated attempt was authorized.
- **Zero** THZ1 Sonic/Tails samples, CSV/ETL present timestamps, per-frame intervals, p95/p99 percentiles, dropped frames, actual scanout or input-to-photon measurements. The Designer correctly stopped and did not substitute `fps_real`, frame-count assumptions or animation pose rates.

## 100 Hz display relevance
The desktop being set to **100 Hz** is worth recording because a target of 60 logical/Draw cycles per second is **not an integer divisor** of 100 Hz: even a perfect 60 Hz output may require uneven distribution over fixed 100 Hz refresh intervals when VSync/compositor behavior demands alignment. **This is a theoretical compatibility consideration, not proof of actual stutter, performance drop, or measured monitor output.** Real Windows compositor, VRR and display behavior remain unknown. Do not automatically impose 60 Hz or 120 Hz monitor changes on Chief, and do not alter the executable.

## Allowed future return path (not commissioned)
If Chief later wants to revisit this, seek a reliable external collector first, with explicit user permission if capture needs elevated rights, or a simpler Chief-led, short comparison on a supported 60 Hz vs 100 Hz display mode if practical (record observed differences as *subjective*, not timestamp telemetry). Only after credible repeatable uneven delivery is observed should Manager consider a separate short timing-compatibility P1. The default experience may already be adequate.

## Workstream sequencing
- **E1:** research accepted; **P0 closed inconclusive**; P1 HOLD. Do not label 60 FPS presentation a new implemented Enhanced feature or claim there is no issue.
- **E2:** next proposed work is **read-only, source-and-runtime feasibility research into pixel-preserving scaling and CRT compatibility**; defer any implementation, filter integration, forced display settings or art changes until Chief approves a bounded design.
- Keep [Classic post-freeze GPZ3 map/import seams](tracking/POST_FREEZE_CLASSIC_DEFECTS.md) and [Enhanced richer lost-ring scatter](tracking/ENHANCED_QOL_IDEAS.md) outside this performance probe.

**Source references:** Designer E1-P0 report (5 Nov, owner attachment), [E1 research and management gate](E1_MANAGER_REVIEW_20261105.md), [accepted E0-R1 checkpoint](E0_R1_CHIEF_ACCEPTANCE_20261105.md).
