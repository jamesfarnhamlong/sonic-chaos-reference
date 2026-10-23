# Sonic Chaos — FIDELITY_REGISTER

**Planning edition 0.2 | 22 October 2026 | M0/M1 Research reconciliation | review ledger, not exhaustive ROM verification**

## Status convention

**CLOSED-348:** tested and accepted by Chief at 348×196 for stated scope. **OPEN-OBS:** Chief observed but exact reproducible/canonical mismatch not established. **OPEN-SOURCE:** a source-model issue/question has evidence but no safe accepted runtime correction. **KNOWN-ADAPTER:** intentional or constrained wide adaptation; retain for later improvement only if prioritised. **TEST-EXCEPTION:** raw automated assertion remains non-green; **not automatically a Windows bug**. **FEATURE-GAP:** original functionality incomplete. **PARKED:** not needed for original feature-complete milestone.

When source and user experience disagree, record **both**, not a synthetic universal PASS. Closed items can reopen only with a new exact reproduction/contract.

## 1. Gameplay, collision and control

| ID | Status / urgency | Evidence and next decisive step |
|---|---|---|
| `Q2R1-AQZ-FACING` | **CLOSED-348** | Proven stale gameplay-facing bit in Q2-R1 seeded wet dash case; Q2-P1 corrected canonical writers and Chief passed AQZ1/AQZ2 wrong-direction testing. A specific new counterexample is needed before reopening. [Q2 closure](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/7476affc6ed7626dabf69b446cdab0c9c3d7492e/docs/q2p1-closure.md). |
| `Q2R1-SS3-MONITOR` | **OPEN-OBS / medium** | Chief became embedded near upper-left of an invincibility monitor; seeded Q2-R1 approaches did **not** reproduce a persistent trap. Identify which of seven mapped monitors, exact incoming movement/state, keys and escape attempts; preserve the existing collision model pending causal trace. [Q2 Research](https://github.com/jamesfarnhamlong/sonic-chaos-reference/blob/8eacc666b0298d3bca955cec782c64f547ef1b77/docs/q2-r1-campaign-defect-triage.md). |
| `Q2R1-REBOUND` | **OPEN-OBS / medium** | Chief noted bounce/instant-kill/pass-through variation on Badniks/monitors. Canonical top/side/attack and velocity/state exclusions already explain some differences; reproduce *identical* impact/posture cases across zones before changing extents or callbacks. |
| `C2-HIST-OSCILLATION` | **OPEN-OBS / medium** | Historical visibly rapid lateral oscillation following spring/Badnik contact. C2-R2 proved only canonical-supported 1/16px no-input X cycle—not the reported visible effect. No generic velocity clamp. |
| `HIST-SLOPE-STICKING` | **OPEN-OBS / medium** | Older slope sticking report; current end-to-end success is not a direct negation. Seek exact act/tile/input and paired ROM/POC terrain contact. |
| `HIST-DIAGONAL-STATIC-SPIKE` | **OPEN-OBS / medium** | Older unusual diagonal spike contact. Require exact placement, touch direction and canonical mask comparison. |
| `C2R3-SPIKE-WIDTH-PHASE` | **OPEN-SOURCE / low–medium** | A moving spike was raised in 256 source host but hidden at 348 due to object activation phase; canonical lifecycle implications unproven. Do not unify width rules without evidence. |
| `THZ1-NATURAL-MAPPED-SPRING` | **UNVERIFIED / low** | Research Q2 C2-R3 reached a natural mapped patrol stomp but never completed a naturally reached mapped `$26` spring launch in its eight routes. This is a coverage gap, not a proven defect. |
| `SS3-SS5-JUNCTION-TIMING` | **OPEN-OBS / low** | Chief found timing difficult, later reported SS routes felt fine; potential wireless controller/GameMaker latency is a hypothesis only. Original routing uses **held** direction + position/first-decision latch; retain the canonical window unless a new paired mismatch is proven. |
| `HIST-HURT-LANDING-VY` | **OPEN-SOURCE / low, M6** | Historical Research `c4c389c` / `docs/player-hurt-ring-scatter-audit.md` and local deferred reference identify extra hurt-landing vy=0. Current Q3 `SCR_cc_hurt_tick` still contains that write. This is not the cause of canonical stationary ring recollection. Require narrow paired landing trace and focused Windows hurt/recovery before correction. |
| `HIST-SEZ-SHOES-CONTACT` | **OPEN-OBS / medium, M6** | Local deferred reference: Spring Shoes fall/contact lock and variable monitor breaks. No exact current-route reproduction or independent closure found; zero steering in state14 is canonical. Group with rebound/contact evidence, not a SEZ-only physics patch. |
| `HIST-SLOPE-FALL-PRESENTATION` | **OPEN-OBS / low–medium, M6** | Historical downhill/ball/fall visual instability and possible alternate isometric-platform fall. U5-A source matches scoped weak-spring tumble; VISUAL-P1 accepted art and unchanged gameplay do not reproduce every old route. Need exact state/pose/input capture, then focused F5 if changed. |
| `HIST-TERRAIN-RING-FEEL` | **OPEN-OBS / low, parked** | Deferred reference says narrow/floaty downhill pickup felt similar in emulator. Preserve canonical probe; no proven defect or change authorised. |

## 2. Bosses, camera and presentation

| ID | Status / urgency | Evidence and next decisive step |
|---|---|---|
| `THZ-BOSS-PATROL-WIDE` | **CLOSED-348** | Q3-A right-only repair failed Chief's left-coverage acceptance; Q3-B reconciled patrol and camera, source-model screen X ≈48–300; Chief passed full cycles and defeat/handoff. Preserve the rejected-A finding as history, not an active bug. [Q3 closure](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/7476affc6ed7626dabf69b446cdab0c9c3d7492e/docs/q3p1-closure.md). |
| `SS4-CLOCK-TV-SEAM` | **CLOSED-348** | SS foreground filtering guard added in Q3-B; original art untouched; Chief reported Windows PASS. |
| `PRES-ENTRY-MGHZ3` | **OPEN-OBS / medium** | Original locks at spike-pit, camera reveals tree and double spikes; POC exposes arena early/Robotnik appears abruptly. Needs faithful staged reveal evidence and narrow camera owner; do not introduce hide gate or fake scenery. |
| `Q2R1-GOAL-CENTER` | **KNOWN-ADAPTER / low–medium** | Q3 source preflight shows some signs are ~38–46px off centre at 348 due to valid world-right cap, forward-only pan and state20 freeze. Exact Chief example not paired; avoid pushing camera into non-world space or changing goal completion to centre graphics. |
| `Q2R1-SLZ1-PRIORITY` | **OPEN-OBS / low–medium** | User-labelled “SLZ1” vertical texture alternates in front of Sonic/Badnik. Stage label/structure unconfirmed; record act, screenshot landmark, front tile/object, and original priority. **Do not silently map SLZ1 to SEZ1.** |
| `Q2R1-BOSS1-RIGHT` | **OPEN-OBS / identity unresolved** | Historical “Boss 1 off right” report may relate to THZ3, now fixed, but the source does not prove they are identical. Only close after identifying encounter. |
| `STATE20-TIMING-LAG` | **OPEN-SOURCE / low** | Approx. seven-update original-versus-POC player X lag in state `$20` traces; current clear/results accepted. Source-model timing comparison needed before any global state20 change. |
| `THZ-LOOP-ANCHOR` | **OPEN-SOURCE / low** | Historical entry ±1px and occasional one-tick sprite publication lag, despite accepted 42-frame original loop artwork. Park unless visibly impactful. |
| `CARD-WIDE-FRAMING` | **CLOSED-348** | Q2 native-size title/results background extension Chief-approved; preserve original text/palette/timing. |
| `PRE-TITLE-CINEMATIC` | **CLOSED-348, SILENT** | Authentic opening sequence accepted; missing accompanying music is audio FEATURE-GAP, not a cinematic regression. |
| `HIST-AQZ-MONITOR-PUFF` | **OPEN-OBS / low, M6** | Local `docs/DEFERRED_ISSUES_REFERENCE.md` and ROADMAP VIS-01 record black break puff against canonical blue backdrop. This reconciliation did not establish a current reproduction or exact superseding effect-palette acceptance. Trace current effect owner/palette before changes; never revert the backdrop to conceal it. |
| `HIST-ENEMY-LIFECYCLE` | **OPEN-OBS / low, M6** | Same deferred reference reports abrupt spawn/despawn on scrolling/return. Preserve canonical sleep bands and type27 triggered keepalive; require exact enemy/placement/camera route, no global activation widening. |
| `XZ-022A-THZ-FOREGROUND` | **CLOSED-348 / historical scope** | Root archived CROSSZONE-FG1/INTEGRATION-1: accepted THZ priority pass and ring-box redraw, combined6/6 Windows including SS5 fixture return. Do not recommission or equate unidentified SLZ1 with this closed issue. XZ-022B withdrawn, not a GPZ defect. |

## 3. Objects, effects, rewards and audio

| ID | Status / urgency | Evidence and next decisive step |
|---|---|---|
| `BREAKABLE-SEZ-AQZ-SS4` | **CLOSED-348** | Authentic ROM-derived fragment resources and common S2 pool behaviour added Q3; Chief passed SEZ/AQZ/SS4, no new placement invention. |
| `BREAKABLE-GPZ-MGHZ-EEZ` | **OPEN-SOURCE / medium** | Corresponding original art can be decoded but correct first-16-slot allocation, scheduler interleaving and freeing for additional owners are unproven. Do not simply remove THZ/SEZ gating or reuse fragments. |
| `Q2R1-CONTINUES` | **OPEN-OBS / low** | Many continues accumulated in Chief's campaign; G2-E score and Special Stage reward paths already established. Need exact score/award ledger and ROM expected limits before claiming excess awards. |
| `IN-GAME-AUDIO` | **FEATURE-GAP / high for completion** | 70 classified sound request IDs and five AUDIO-A0 preview WAVs exist, but they are **Sound Test previews**, not authentic gameplay music loops/arbitration/fades. Plan audio evidence/dispatcher/pilot/expanded library separately; no imaginary audio parity. [Audio closure](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/7476affc6ed7626dabf69b446cdab0c9c3d7492e/docs/audio-a0-closure.md). |
| `TAILS-AUTHENTIC-PLAYER` | **FEATURE-GAP / high for completion** | Inherited GameMaker sprites remain in `SCR_player_sprites_tails`; canonical SMS frames/state transitions and playable campaign not integrated/accepted. Research authentic assets and mechanics before implementation. |
| `TITLE-CHAR-SELECT-ATTRACT` | **FEATURE-GAP / high for completion** | Inherited `SPR_title` draw and a New Game path forcing Sonic; original title and character-select presentation, Tails entry and attract demos need ROM-backed integration. Existing pre-title cinematic/Level Select are complete in their own scopes. |
| `M1-TAILS-FLIGHT` | **SOURCE-ONLY / M2 gate** | New static `$3713/$473C/$3EFD` decode: look-up plus fresh action, water blocks entry, state18 timer300, direct held-direction motion; no swim feature justified. Complete callback/equipment controls before runtime edits. [Contract](../docs/m1-tails-frontend-contract.md). Chief flight/water/contact/timeout gate remains unexecuted. |
| `M1-TAILS-ASSETS` | **PARTIAL / M2 gate** | Census decodes89 mappings/54 scripts and18 palette bindings;11 authenticated imported opening/Continue resources,29 inherited Tails-named resources. No new PNGs. Private exporter, branch/selector closure, palette binding and resource restoration required; no playable claim. [Census](../data/m1/tails-asset-census.json). |
| `M2-TAILS-ACTCLEAR-SIDE-MAPPING` | **OPEN / UNRESOLVED natural reachability; M2 act-clear gate** | M2-R1 original engine confirms state20 selector8EE1 side predicate (+23&0C)→frame5E/duration2. Type2 table85BF entry867B really reads0785 in resident bank0, decoding230 pieces; forced original harness produces malformed RAM tile transfer/display corruption. No legitimate image exists to import. Three arrival-seeded sign/backtracking controls exclude side in those routes only; original THZ3 floor gate permits synthetic retained side flags. Natural full-act/boss reachability not proven either way. [Exact contract, controls and proposed isolation](../docs/m2r1-tails-act-clear-frame5e.md). No silent substitution or parity claim; temporary no-draw exception requires Manager approval. Other M2 work only if independent; full act-clear acceptance remains blocked. |
| `M1-FRONTEND-CHOICE` | **SOURCE-ONLY / M3 gate** | Separate SMS screen verified at3065/3522: Sonic default, fresh Left/Right clamped0/1, Button2 confirm. Public integration requires accepted Tails and full title/choice picture/timing proof. No dead option. |
| `M1-TITLE-AUDIO-ID` | **SOURCE-ONLY / M4 prerequisite** | Title0756 requests99; choice30BC requests82. Historic82 preview name unchanged; add authenticated99 to pilot, retain unknown friendly-name status. No live audio correction made. |
| `M1-ATTRACT-RECORDINGS` | **PARTIAL / M3 or M6** | Tables2C72/2C7E point to bank31 recordings; cached order THZ1 Sonic→GPZ1 Tails→SEZ1 Sonic. Input decoder/abort/reset isolation still requires proof before public integration. |
| `HIST-DYNAMIC-POOL-OCCUPANCY` | **PARTIAL / M6 evidence prerequisite** | Historical SEZ20/23 occupancy can reduce crumble allocations; VISUAL-P2/Q3 implement shared occupancy for instantiated occupants, not universal ROM scheduler parity. Need current owner/slot comparison before claiming all-pool closure or changing counts. |

## 4. Inherited automated failure ledger — NEVER call these green

M2-R4 Research amendment (23 October 2026; actual private Package C, no runtime acceptance):

| ID | Status / owner | Evidence and next gate |
|---|---|---|
| `M2R4-AQZ-PALETTE-SWITCH` | **UNRESOLVED-WINDOWS / palette and GPU boundary** | C's ordinary row selection, RGB Tails/alpha Sonic routing and three palettes match scoped source controls.88 Tails frames have substantial lower-split colour differences; unchanged guaranteed crossings cannot be dismissed as identical colours. A conditional full-camera→split upper-base mismatch is isolated, but normal steady AQZ bounds exclude full camera. Exact conditional recommendation and shortest F6/F7+screenshot capture: [M2-R4](../docs/m2r4-aqz-water-reversal.md). AQZ3 has no controller; separate normal presentation only. |
| `M2R4-AQZ-REVERSE-JUMP-LAUNCH` | **UNRESOLVED-WINDOWS / movement and contact ownership** | Original controlled arrivals reproduce retained momentum plus fresh jump and repeated skim, paired with actual C.54,120 movement-phase snapshots agree;156/192 continuous100-update source runs match selected fields.50 raw post-terrain differences and36 divergent continuous runs remain explicit, principally unsupported type30 sides and damage/lifecycle; no demonstrated cause of Chief's exact launch. No clamp/gravity/jump/skim/bounce correction. Need short native input/state/velocity-writer trace; [machine register](../data/m2r4/fidelity-register.json). |

Chief's Package C AQZ1 appearance, Sonic palette, opening spear pair and B
essential retests PASS remain scoped human reports. M2-R4 independently reads
the exact C ZIP/source; it does not close full Tails campaign, natural frame5E
log, every contact route or native GPU evidence. R3's B decoder finding is
historical and corrected in C source; its original Windows lifecycle caveats
are not erased by the opening-pair pass. No POC edits or main promotion.

M2-R3 Research amendment (23 October 2026; no runtime acceptance):

| ID | Status / owner | Evidence and next gate |
|---|---|---|
| `M2R3-AQZ-TAILS-INDEX-DECODER` | **CONFIRMED-SOURCE / Tails presentation** | Private B's correct RGB-indexed textures use alpha decoder, yielding invalid254 and exposing dark payload.176 textures regenerated; exact three-mode CRAM policy retained. Route Tails to RGB decoder, preserve Sonic proxies; Manager/Designer/Chief review required. [Report](../docs/m2r3-aqz-palette-hazards.md). |
| `M2R3-AQZ-SPEAR-CONTACT` | **OPEN-WINDOWS-OBS / mapped object lifecycle** | Thin spears are type3C objects; first AQZ1 pair1104,686/1232,686.22,528 original/B contacts and1,980 motion updates match; original grounded Sonic/Tails routes hurt. Exact Chief Windows phase/approach unresolved. No generic hitbox/shared physics/THZ change justified. [Machine register](../data/m2r3/fidelity-register.json). |
| `M2R3-AQZ-TERRAIN-NEGATIVE-CONTROL` | **BOUNDED-CANONICAL-MATCH** | Distinct terrain type5 blocks3C/3D:22 beds;1,152 paired approaches match. Cross masonry04/29 not inferred dangerous from artwork. Full placement/profile inventory in evidence. Not exhaustive state/natural route parity. |

M2-R2 `cd417c1` was read independently, not merged. Existing M1 asset status
above describes its historical checkpoint; M2-R3 additionally checks the actual
private B imports and routing. No full Tails campaign, frame5E natural log gate,
historical failure or acceptance status is closed by these findings.

| ID | Classification | Known current state |
|---|---|---|
| `verify_ss5_play.js` | **TEST-EXCEPTION / raw FAIL** | SS5 clock scenario camera X at 256 differs from cached value by up to **2px**; 348 paired camera series unchanged at Q2; no 256 Windows acceptance required. Retain exact raw failure, investigate only if it affects future feature changes. |
| `verify_thz3_boss_clear.js:113` | **TEST-EXCEPTION / raw FAIL** | Historical 6px camera step exceeds **obsolete 4px test cap**, accepted release cap **7px**. Oracle/Windows release passes; fix test contract only in separately authorised verifier-maintenance step, keeping original raw evidence. |
| `verify_gpz_boss_e1.js:62` | **HISTORICAL TEST-EXCEPTION** | Sprite ID 1115 !=1352; not rerun Q3. |
| `verify_mghz_boss_wide.js` | **HISTORICAL TEST-EXCEPTION** | 60-second timeout; not rerun Q3. |
| `AQZ parent source equality / THZ2 shards` | **HISTORICAL TEST-EXCEPTION** | Earlier frozen source-equality mismatch and shards timeout. Preserve original context rather than combining with live Q3 paired gate. |

## 5. Acceptance discipline and grouping

### M2-R5 scoped update — 23 October 2026

`M2-TAILS-ACTCLEAR-SIDE-MAPPING`: **OPEN-EXCEPTION / ORIGINAL ARRIVAL-REACHABLE**.
Four native POC sign bursts are Manager-log-confirmed. Actual original Z80
sign chains in GPZ1/2, MGHZ1 and EEZ1 select94 with organically generated
bg/contact6 in12/20 approach-phase controls, without state/contact injection.
Four base controls and eight phase negatives select normal frames instead.
Full entrance-owned original routes and exact Windows phase remain unresolved.
The no-draw continuation remains a deliberate difference from invalid original
mapping/transfer reads; no closure or runtime modification authorised.
See [M2-R5](../docs/m2r5-natural-frame5e.md) and `data/m2r5/summary.json`.

- One group per causal family: **Tails movement + authentic animation**, **title+character selection**, **sound dispatch + lifecycle**, **remaining original presentation**, **contact/physics with a reproduced trace**, **other object scheduler + fragments**. Do not use this register as authorisation for single-bug ZIPs.
- Record both human test and source comparator with exact width, route, date and SHA. 256×192 is the **ROM/source-model** target, **not** a mandatory Windows F5 mode. Windows test baseline is 348×196.
- Remove/close an OPEN record only after concrete evidence. For original quirks and constrained widescreen rules, prefer `KNOWN-ADAPTER` or documented canon over speculative “fix”.
- M0 read the mounted root AGENTS and Q3 FINAL inventory; older archive coverage remains incomplete. The changed root hash is recorded without installing a candidate. See [M0 reconciliation](../docs/m0-reconciliation-report.md) for G0–G10, superseded opening/Continue gaps and exact acceptance authorities. This register is not exhaustive. Each open row retains its next evidence prerequisite; M2 handles character work, M3 frontend, M4/M5 audio, and M6 only separately selected fidelity fixes.
