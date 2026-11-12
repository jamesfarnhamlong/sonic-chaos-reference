# Sonic Chaos — C1-R6 Original Ordinary-Stage Initialization and Camera: Manager Closeout

**12 November 2026 · Manager-san #11 · EVIDENCE-LED NO-CHANGE RESEARCH PASS · PRODUCTION CLASSIC REPLACEMENT HOLD**

## Reviewed evidence and custody

Manager read Chief-uploaded complete Markdown `C1_R6_ORDINARY_LOADER_CAMERA_PHASE_20261112.md` (94 content lines), not the adjacent private ZIP/raw CPU traces, test binaries, source tree, recovery receipt, or original ROM. Numerical comparisons here are **Designer-reported**, not independently executed by Manager.

- C1 isolated project: `management-audits/c1-20261112/project/SonicChaos.yyp`.
- C1-R6 local branch `classic/c1-r6-ordinary-entry-camera-20261112`, **source HEAD remains exactly C1-R3 `b667cc5cebcd3c3e047d9f527cc78b76e1e027f0`**, tree `ffdfc37e23d1b18e866b8beae051234c443b9665`. R4/R5/R6 **no-change research** and do not have distinct committed production source. Never invent a R6 source commit, a shipping C1-R6 Windows/source ZIP or a production branch merge.
- Private full report `E:\AI\Codex\Sonic Chaos\management-audits\c1-20261112\r6\delivery\C1_R6_ORDINARY_LOADER_CAMERA_PHASE_20261112.md`; receipt `SonicChaos_20261112_C1_R6_ORDINARY_RESEARCH_RECEIPT.json`, evidence ZIP separately recorded in receipt. Original Europe v1.2 ROM hash `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`, verified locally per Designer.
- E:/H: original source and Git recovery, all **22 ignored dependencies (four runtime + eighteen original PNGs)** and private R6 evidence reported byte-verified, R1–R5 references and production S6 packages/source, historical Classic tag protected. No merge/push/tag/release/Chief C1 user test.

## Gate A successfully resolved: stable observation in the approximate harness

R5 exposed density-sensitive PC breakpoints in research `SMS._run_cycles` / `_step_over`. R6 created **research-process-only** timing census, preserving each 32-cycle scheduler chunk and IRQ polling boundary while stepping a breakpoint instruction using existing countdown. No ROM/GameMaker/shared tool change. Three identical power-on no-input original runs across **zero hooks, one player-engine hook and thirteen detailed hooks** produce **identical 12,000 frame digests, identical 10,894 selected memory-write records and 3,087 identical matched player snapshots** for available hook profiles. This establishes **hook-profile stability for these runs**, **not hardware cycle-exact timing**. 262×228 approximate VDP, saturated instruction budgets, unverified physical PAL50/NTSC60 D12D branch remain limitations.

**Important supersession of R5 counts:** With corrected profiling, the observed three demo bodies still have **1,080 original driver calls** each, but player/skip distribution differs:
| Demo | Driver calls | Body player | Non-player driver | Cleanup | Total player |
|---|---:|---:|---:|---:|---:|
| THZ/Sonic | 1080 | 1042 | 38 | 1 | **1043** |
| GPZ/Tails | 1080 | 1007 | 73 | 1 | **1008** |
| SEZ/Sonic | 1080 | 1035 | 45 | 1 | **1036** |

R5 1,042/1,016/1,036 was correct *for its old lightweight instrumentation* but **must not be reused as hook-invariant/hardware truth**. New results derive player ownership bounded by driver entry/return rather than treating late D15E sampled at PC16EE as pre-player skip decision at PC16C7. First input/cursor differences versus R5 old streams at player ordinals **804/522/156**. No skip table or replay constant should be hardcoded into GameMaker.

## Gate B original ordinary loader/camera evidence

- **12 original title/character/loader scenarios**, all six zones' first acts × Sonic/Tails, first **180 original player entries each**, genuine THZ new-game route and documented START_INDEX fixture for later zones (not natural full campaigns). All enter original current/next player **0/0**, with X/Y leads 104/120 and target Y120; first object phase writes next1 for THZ/SEZ/AQZ or next14 for GPZ/MGHZ/EEZ and target Y96, while current0 persists until later phase. Original state0 bank0C:807D begins `FF01/038F`; `038F→3657` initializes state-owned fields, frame/facing, max speed D373 and character-specific collision probe extents. **A numeric state0→1 rename in GM would NOT replicate this initializer/callback pipeline.**
- Original ordinary driver `16B8` calls `4C90` camera *before* `361D` player/state engine and `5DD1` objects; committed camera updated later at interrupt `0570/057C`. Original previous committed view consumed by player/objects.
- On **2,160/2,160 original pre-player snapshots**, GameMaker's *camera primitive evaluated as a controlled model* exactly matched original pending camera coordinates and working leads. This **supports camera calculation and original pre-player ownership**, **NOT the native regular runtime call-site**. A late hypothetical camera using player/object-next instead differed in **609 controlled samples**, despite 1,539 adjacent values coinciding; first lead divergence update1 (original120, late119), even when rounded camera pixels initially equal. This is a counterfactual model and cannot be labelled an actual native code fix.
- Current native regular stage `SCR_cc_new` seeds state1/1, zone Create publishes anchor, `SCR_chaos_adapter_step` prepares **only Special Stage** camera, and ordinary follow still executes in zone End Step after objects. Ordinary boss/sign/goal/act-reset owners share that timing, so wholesale relocating End Step is unsafe. **The actual GameMaker normal retail title→character→loader→first engine→camera/objects handoff has NOT been traced in equivalent execution**, and the source differences alone do not prove every Classic output incorrect.

## Controlled native demo-input diagnostic (NOT a shipped demo)

A disposable compiled GameMaker diagnostic started via debug loader and consumed the corrected original held/pressed pairs. Its context is still **not equivalent** to original title/loader, interrupt and driver skip scheduling:
| Demo | Native present / original engine entries | First state/next delta | First committed camera delta | First missing row | First observed positional delta |
|---|---:|---:|---:|---:|---:|
| THZ/Sonic | **851/1043** | 1 | 14 | 615 | 726 |
| GPZ/Tails | **1008/1008** | 1 | 12 | none | none sampled |
| SEZ/Sonic | **1036/1036** | 1 | 29 | none | 214 |

Input pairs were byte-exact for present rows; mismatched state0/1, ordinary camera phase, IRQ/driver, or loader remain possible causes. THZ 192 missing calls and SEZ later observed positions are **not proven core physics defects**. The report retained the initial native probe error reading an uninitialized camera during Create (trace-only guard fixed) and sandbox Windows launch error623 (same binary ran outside sandbox), not reclassified as shipping game bugs. No source files/resources left changed.

## Fidelity preservation and explicit holds
Designer reports on **unchanged exact C1-R3 source**:
- Enhanced versus immutable S6: **10,542 native state samples +102 native/output image comparisons exact**.
- Classic: **138 native 256×192/nearest1×–3× outputs** (23 rooms ×2 characters ×3 scales) plus30 frontend outputs exact.
- All R2 first SS anchors (10 controls), R3 original five-SS camera500 and settled SS5 clock145 exact; explicit-mode SS4 **22,742 assertions PASS**.
- Historical raw SS4/SS5 source-host FAILs remain correctly exposed under old mode/timeline assumptions, not overwritten.
- 382 ROM-wide coverage records/16 findings updated, but **native regular retail entry is explicitly `UNVERIFIED`**, along with natural death/restart/Continue, boss takeover, ordinary full campaigns, original first16 shared object pool, true three-demo playback, R4 palette-aware VDP mask/phase and original hardware timing.

**MANAGER VERDICT: C1-R6 measured-original research PASS / production no-change hold ACCEPTED.** This does not close the confirmed ordinary-stage camera phase divergence or grant Classic production integration. **Strict ROM original semantics only, no Classic QoL.** Enhanced Wide S6 exact `47c501ecb994a4fcb1eeac1c29793f3f1142a304` remains protected; Pause redesign parked and Chief personally creating six144×128 Save TV PNGs. S5–S7 owner acceptance 33 PASS/4 unobserved/0 functional FAIL, unrelated to C1 certification.

## Manager next decision
**C1-R7 will NOT repeat the broad R5/R6 timing census.** Use R6's now-stable original 12-route traces and prove actual **native retail** `Classic selector→character selection→regular zone Create→core/player first update→object/camera commit` with matched original route; isolate state0 initializer mapping and guard/phase interaction for **ordinary stages only**, including boss/sign/goal/death/reset ownership. Only then authorize a precise ROM-correct Classic-only code change; if unprovable, deliver a **bounded evidence-only hold**, report the single missing integration boundary and pause camera implementation rather than blindly repeating the same tests. [Binding C1-R7 narrower work](C1_R7_NATIVE_RETAIL_ENTRY_HANDOFF_SPRINT_20261112.md). No demo playback, first16 pool rewrite, VDP mask, Enhanced UI work, production Classic merge, push/tag/release or forced Chief test.

**C1-R6 RESEARCH HOLD SUCCESS; R7 NATIVE RETAIL HANDOFF INVESTIGATION GO; CLASSIC REPLACEMENT HOLD.**
