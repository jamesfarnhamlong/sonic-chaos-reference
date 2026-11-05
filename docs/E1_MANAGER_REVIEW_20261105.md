# Sonic Chaos E1 — Manager Research Review
**5 November 2026 · Manager-san #10 · E1 research accepted; baseline measurement authorized; runtime pilot ON HOLD**

## Decision
Designer delivered the read-only `REPORT.md` from `management-audits/e1-framerate-research-20261105/`, reviewed as attached report. **Research PASS.** Ordinary Sonic/Tails gameplay in the accepted E0-R1 source targets **60 logical updates per second**, without a global alternate-frame simulation gate. Frame-duration-controlled artwork (e.g., Sonic running nominally one pose per four ticks) can appear substantially less than 60 unique images/s despite 60 updates and expected Draw events. **Actual Windows presented cadence, dropped/duplicate presentation and physical scanout remain unmeasured**; 60 target is not the same as measured delivery.

**Reject for now:** 30→60 conversion, blanket interpolation and true 60 Hz simulation rewrite. The ordinary simulation already targets 60 and has no demonstrated missing 30 Hz intermediate-state stream. Camera End Step and state-sensitive animation/audio forbid casually increasing or resampling ticks.

**Manager authorization:** do only E1-P0, **external baseline presentation measurement of the existing accepted E0-R1 Windows ZIP**, no source changes, engine setting changes, instrumentation build or new E0 game candidate. Measure first; **E1-P1 optional `tm_countvsyncs_winalt` GML/Windows compatibility pilot remains HOLD** pending reproducible baseline unevenness and a separate Chief/Manager go. If baseline is even, close E1 performance-pacing proposal as no demonstrated benefit and proceed to approved scaling/CRT research later.

## Authoritative source and API evidence
- Accepted Enhanced E0-R1 private commit `deccefc0acd822f74b6b26895ec278cdf67a7cee`, verified remote; game `OBJ_chaos_zone/Create_0.gml` sets `global.chaosTickRate=60` and `game_set_speed(global.chaosTickRate,gamespeed_fps)`.
- Native Windows options `option_windows_vsync=true`, `option_windows_sleep_margin=10` (independently checked via private GitHub), no ordinary custom timing method identified by Designer.
- GameMaker LTS `game_set_speed()` specifies **game-frame target**, not independently scheduled render frames: `https://manual.gamemaker.io/lts/en/GameMaker_Language/GML_Reference/General_Game_Control/game_set_speed.htm`.
- LTS Event Order describes Begin Step → Step → End Step → Draw; the relative order of instances within the same event type is not generally guaranteed: `https://manual.gamemaker.io/lts/en/The_Asset_Editors/Object_Properties/Event_Order.htm`.
- GameMaker LTS says default VSync timing is generally smoothest and `tm_countvsyncs_winalt` is a Windows-specific alternative only to try when performance issues exist; `tm_systemtiming` removes game speed control and is unsuitable: `https://manual.gamemaker.io/lts/en/GameMaker_Language/GML_Reference/Cameras_And_Display/display_set_timing_method.htm`. The default Windows sleep margin is 10 ms and still influences VSync: `https://manual.gamemaker.io/lts/en/GameMaker_Language/GML_Reference/Cameras_And_Display/display_set_sleep_margin.htm`.
- Source report rates are configured/intended. E0 frontend screen inherits project 30 target; opening/title/choice and ordinary zones target 60; native audio independently services 60 wall-clock driver ticks/s with pause/debt handling. 30-looking animation could simply be original per-state pose hold, not an engine scheduler failure.

## E1-P0 external measurement — GO
- Use the accepted unmodified `SonicChaos_Windows_20261105_E0_R1_PRIVATE.zip`, SHA-256 from its private E0-R1 receipt, no recompilation or instrumentation. Record Windows build, installed GameMaker VM runner, GPU/driver, display refresh and VRR, window/fullscreen mode, VSync, effective resolution/scaling, available monitor setups.
- Use existing nonintrusive PresentMon/ETW capture (if available and approved locally) to measure per-process presentation timestamps, displayed intervals and long holds. Correlate with high-speed camera/recording only if it materially disambiguates actual screen refresh; telemetry alone may not prove physical scanout. Collect several short ordinary THZ1 traversals with movement and camera scroll; capture at 348×196 Wide first, include Sonic/Tails and a convenient second refresh mode where available, rather than demanding all monitor configurations.
- Quantify median/p95/p99 displayed-frame interval, 16.67 ms expected target, repeats/drops, interval histogram, hitches, stable vs unstable segments. Identify whether repeat pictures are intentional animation holds or missing presentations. Save timestamp/sample metadata; note capture overhead/limitations and preserve original E0 source/ZIP/hash. **Do not use `fps_real` as independent proof of display cadence.**
- **GO for possible P1 only if:** uneven presentation recurs across representative normal runs, measurement quality suffices to exclude capture-only artifacts, and credible Windows timing issue is identifiable. If presentation is already steady, no 60 FPS pacing enhancement is needed.
- No runtime flags, hidden Fx modes, GameMaker `display_set_timing_method` calls, sleep margin change, graphics shader, audio clock changes, build, merge, tag or new runtime feature. Stop and report if external tooling is not already available, needs elevated install/permissions, or fails to produce reliable timestamps.

## Contingent P1 (NOT authorized)
Designer suggested Enhanced-only Windows frame-pacing compatibility option `e1_windows_pacing` (default off) toggling `tm_countvsyncs_winalt`, with actual timing-method capture/restore on all lifecycle exits, normal Classic settings and original 60 logic/audio unchanged. This is **not yet a go** and should not be advertised as a 60 FPS boost or enabled by default until shown useful and Chief accepted.

## Next decision
Return one E1-P0 baseline presentation assessment with numeric interval distributions and measurement limits, plus a recommendation: **NO PACING WORK REQUIRED**, **UNMEASURABLE — SPECIFIC LIMITATION**, or **CONSIDER P1 — DATA SUPPORTS A PACING PROBLEM**. No Chief full playthrough.

**References:** E1 source report uploaded 5 November; [E1 research brief](E1_FRAMERATE_PRESENTATION_RESEARCH_BRIEF_20261105.md); [accepted E0 baseline](E0_R1_CHIEF_ACCEPTANCE_20261105.md); [enhancement roadmap](ENHANCEMENTS_ROADMAP_20261105.md).
**Deferred unrelated scopes:** GPZ3 source map seam bug, QoL richer ring loss, sprite art/CRT/scaling; original immutable Classic `classic-core-20261105` unchanged.
