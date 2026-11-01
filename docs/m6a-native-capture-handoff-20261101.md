# M6-A — Gate A native capture handoff after bounded runner failure (1 November 2026)

## Manager #8 decision

**Windows runtime preflight exhausted; stop troubleshooting in the current agent session.** Designer/Astra reports a reproducible Windows loader error before GameMaker gameplay starts. **No GameMaker code change, no M6-A fix, no native 348×196 capture, no reclassification of MGHZ-007 yet.** Accepted G2 remains `SonicChaos_POC@91fd74b56296bb9182768c3a9db78a186fa78f9e`; M6-A `poc/m6a-mghz3-staged-reveal` is reportedly clean at that parent, no local commit/push.

Evidence (Designer report, not independently rerun by Manager):
- Host: `Windows-Gaming`, Windows `10.0.26300.0`.
- IDE: GameMaker LTS `2026.0.0.16`; matching Windows x64 runtime `2026.0.0.23`.
- Attempt: runtime `Runner.exe -game "<...>/SonicChaos_A4B_EXPERIMENTAL.win"` from the corresponding output directory.
- Failure: Windows error **623 — Illegal System DLL Relocation**, independently of Igor. `CreateProcess`/loader failed before gameplay; no process exit code. Error contains unresolved `%hs` placeholders; **no offending DLL identified, underlying cause unknown**. Previously used native harness launched a packaged EXE from its build directory; the user-confirmed successful IDE F5 route cannot be driven here because desktop controls are unavailable and event-log access denied. No basis to accuse corrupt GML, modify runtime security settings, or diagnose a particular DLL.
- Original evidence: verified pit static terrain, spike banks X3232/X3296, central terrain X3264; boss $56 at WORLD(3269,288). Seeded original ROM trace: trigger update46, pan starts106, combat107, settled camera(3060,256) at169 (seeded update counts, NOT 30Hz capture times). Original boss pan 1px/tick. G2 `chaos_56_pan` at width348 uses +/-4px/tick on both axes and target X2968; this is a **possible presentation divergence only**. Source ROM confirms preexisting terrain and descent during camera movement. Chief original footage was YouTube-stretched 16:9 from a 4:3 source; normalize for comparison only, don't treat as original 348 rendering.

## One short Chief-side capture: enough for visual comparison

1. Use the **already-accepted G2 private source package** `SonicChaos_M5_G2_20261101_A_PRIVATE.zip` with normal working GameMaker IDE **F5**. Do not switch backend or edit scripts; do not use the unmodified M6-A isolated branch unless it has the required same private dependencies.
2. Use normal Level Select to enter **MGHZ Act 3** before the boss, rather than spawning directly in combat. Start recording approximately **3–5 seconds before** Sonic reaches the final grassy platform/spike-pit approach. Continue through first boss appearance, completed camera pan and **5–10 seconds of combat**. One uninterrupted clip ~15–30s is sufficient.
3. Capture the **current G2 348×196 widescreen** game window at its native proportions (or an integer-scale display such as 696×392); **do not force it into 4:3**. YouTube's source-video stretching is unrelated to G2's intentional 348×196 presentation. Use 60fps if easy; 30fps is adequate for visibility/order, not game tick certification. Leave HUD and camera natural; avoid custom debug overlay, pausing, hand-scripting or manually forcing boss states. MP4 preferred.
4. Share privately in this management chat. No ROMs or captured assets need publishing; only public-safe written observations and timing/shape deltas will be placed on GitHub.
5. Manager will compare pit/tree/spike first exposure, first boss pixel relative to pole and platform edge, pan/settle pace, overlay/priority, visibility during vertical descent against original reference, **with aspect-ratio and 30fps-video limits**. If actual mismatch exists, dispatch **smallest source-supported production fix + complete boss/clear/AQZ1 proof**; if not, close/qualify MGHZ-007 rather than manufacturing cinematic effects. If timestamps alone are ambiguous, narrow developer-only telemetry can be captured later, but no automatic new human test.

No need for another agent environment repair, speculative 4px->1px code change, extra video frame extraction by Chief, or additional unrelated M5 regression. Startup first-audible delay remains separate parked polish.
