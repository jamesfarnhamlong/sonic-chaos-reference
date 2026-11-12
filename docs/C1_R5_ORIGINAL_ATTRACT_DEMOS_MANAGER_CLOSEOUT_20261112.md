# Sonic Chaos — C1-R5 Original Attract-Demo Research: Manager Closeout
**12 November 2026 · Manager-san #11 · EVIDENCE-LED NO-CHANGE HOLD ACCEPTED · CLASSIC PRODUCTION REPLACEMENT HOLD**

## Review provenance and source custody
Manager read the **actual uploaded full Markdown R5 report** `C1_R5_ORIGINAL_ATTRACT_DEMOS_20261112.md` (86 visible text lines), not the private ZIP, machine-readable traces/matrices, original ROM bytes, temporary compiled diagnostic outputs, E:/H: archives, or receipt bytes. R5 report's numerical tests are Designer-reported and have not been independently re-executed by Manager.

- Private local source project: `management-audits/c1-20261112/project/SonicChaos.yyp`.
- R5 local branch: `classic/c1-r5-original-attract-demos-20261112`; **unchanged source HEAD `b667cc5cebcd3c3e047d9f527cc78b76e1e027f0`**, tree `ffdfc37e23d1b18e866b8beae051234c443b9665` (same as C1-R3). No new source commit, standard Windows candidate, production demo feature, C1-to-S6 integration, push, merge, tag, release or immediate Chief playtest.
- Original Master System Europe v1.2 local ROM SHA256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`, verified locally per report. Private source/data stay E:/H:.
- Full report `E:\AI\Codex\Sonic Chaos\management-audits\c1-20261112\r5\delivery\C1_R5_ORIGINAL_ATTRACT_DEMOS_20261112.md`; evidence ZIP `SonicChaos_20261112_C1_R5_ATTRACT_RESEARCH_EVIDENCE_PRIVATE.zip`; receipt `SonicChaos_20261112_C1_R5_ATTRACT_RESEARCH_RECEIPT.json` in same R5 delivery folder. H: byte-exact research evidence recovery and R3 full Git/source/22 ignored dependencies reported verified by Designer. Earlier C1-R1/R2/R3/R4, frozen historical Classic tag and S4–S6 candidates protected.

## Major original-ROM result: loop budget fully reconciled
Original retail three demos rotate **THZ/Sonic → GPZ/Tails → SEZ/Sonic**, power-on rotation index1→2→0, with two ROM header sets selected through D12D timing branch; the controlled approximate harness observes D12D=0 (bank `$1F`, streams THZ `$8000`, GPZ `$8A00`, SEZ `$9400`). Alternate bank pointers `$9E00/$A800/$B200` were decoded but **NOT** verified as a naturally selected PAL/NTSC run. Do not infer physical mode from this branch without hardware evidence.

The source driver `$2C8A` performs **1,080 driver calls**, decrementing BC on each even when `$16B8` skips player/object on D15E bit6. It then makes one original cleanup player call after the body. Exact lightweight original `$64FA` hook accounting:

| Demo | Driver calls | Non-player driver calls | Body player calls | Cleanup player calls | Total engine calls |
| --- | ---: | ---: | ---: | ---: | ---: |
| THZ/Sonic | 1080 | 39 | 1041 | 1 | **1042** |
| GPZ/Tails | 1080 | 65 | 1015 | 1 | **1016** |
| SEZ/Sonic | 1080 | 45 | 1035 | 1 | **1036** |

`1042=1080−39+1`; `1016=1080−65+1`; `1036=1080−45+1`. **Counts are player engine entries, not 1080 recorded input pairs, current PC frames or literal PAL/NTSC refresh-rate proof.** The source title has 24/12 wait loops, 30 unpolled waits and 1140 polled waits; these are not the 1080 demo budget. Loading and 72 exit waits are outside the body.

**Critical instrumentation caveat:** Additional PC/loader/input breakpoints perturb this approximate reference harness `SMS._run_cycles` bookkeeping (cycles counted before `_step_over` executes another instruction). Detailed-hook body/skip patterns therefore differ (1035/45;1011/69;1042/38), though they repeat under their own configuration. No one schedule may be hardcoded as ROM physics or actual hardware cadence. R5 kept both evidence profiles distinct.

## Input, exit and original-demo ownership
- `$24A8` streams **uncompressed held/pressed byte pairs**, not RLE or movie data; advances live cursor **D2DE** by2; prior R2 'input_pointer' D2E5 is only *fixed source start*, not live cursor. Original pressed edges are read separately at D157 before demo override, so don't recompute all pressed states from sampled held values.
- Original loader `$2BC3/$2CA4` establishes original demo flow D293=$40, original zone/character/music/palettes/20 rings and input stream pointer, then enters `$2C8A`.
- Six real button1/button2 cancel samples follow D292 bit7 directly to title; direction-only control runs full BC budget back through opening→title, preserving D2E3 rotation. No Original Pause NMI path or desktop keyboard Start mapping has been proven; no synthetic PC cancellation.
- Source recorded actual demo progress in original volatile RAM is not permission to mutate PC campaign save files. Since GameMaker attract mode has not been built, no real native replay save-isolation PASS can be claimed.

## Diagnostic readiness, not implementation certification
Original recorded held/pressed pairs were fed directly into a **temporary compiled Windows GameMaker diagnostic**, with temporary resources restored afterward, not a shipping attract implementation. Original entry uses `state/next=0/0` versus native wrapper `1/1`; ROM ordinary camera prepares before player while current native ordinary zone End Step follows player/objects (R3 fixed **Special Stages only**).

| Original demo | Native player calls observed vs original | First camera difference | First position difference | First absent native call |
| --- | --- | --- | --- | --- |
| THZ/Sonic | **850/1042** | ordinal14 | ordinal726 (where both present) | ordinal615 |
| GPZ/Tails | **1016/1016** | ordinal12 | no sampled delta | none |
| SEZ/Sonic | **1036/1036** | ordinal29 | ordinal214 | none |

GPZ sampled positions matching is **not** full camera/loader/exit/cadence identity. THZ lifecycle gap (192 absent calls) invalidates later naive ordinal comparisons. SEZ first observed positional delta `60/256 pixel` at ordinal214. The approximate harness itself is timing-sensitive. No evidence yet isolates these later symptoms to player physics or object-pool correctness. **No original demo playback shipped**. These are informative diagnostics with unproven retail entry and cadence equivalence.

## Preservation
Fresh R5-local identical S6 Enhanced regression: **10,542 bounded native states and102 protected images exact** (not universal gameplay proof). Classic original 256×192: **138 source/output captures** across 23 rooms, both characters,1×/2×/3×, plus30 Classic frontend integer outputs; R2 ten start controls, R3 500 Special Stage camera phase matches and145 equivalent-state SS5 clock matched unchanged; original SS4 explicit mode22,742 assertions PASS. Historical raw SS4/SS5 FAILs remain marked FAIL under their legacy mode/phase assumptions; not retrospectively converted to PASS. Protected saves/INI and E:/H: complete source hashes passed per agent. 382 coverage records and16 findings kept with R5 annotations; C1-06 attract playback remains **OPEN/NOT IMPLEMENTED**.

## Manager verdict and next gate
**C1-R5 successful research and no-change HOLD accepted. Classic production replacement/integration remains HOLD.** Keep VDP mask confirmed but missing from R4, shared first16 object slot ownership model gap, original state0/1 initialization wrapper, original visible-frame/fade/PAL timing and original unvisited campaign/SS paths explicitly OPEN. Never call evidence-only demo traces a playable original attract feature. Classic remains strictly original ROM including quirks; Enhanced Wide S6 exact with new QoL options OFF; no pause redesign, and Chief owns six 144×128 Save TV zone thumbnails.

**NEXT C1-R6 BINDING:** [ordinary-stage original loader/driver/camera phase fidelity, with non-perturbing original timing census](C1_R6_ORDINARY_LOADER_CAMERA_PHASE_SPRINT_20261112.md). The R5 earliest common observable mismatch is original ordinary state0/0 vs GameMaker1/1 and early camera lead phase; address that **root dependency before demos**. No R6 attract playback, fake 1080-per-PC-Step schedule, pool rewrite or VDP black stripe; ROM-first evidence and optional bounded Classic-only correction. Defer replay integration until original driver/input cadence and source entry compare across THZ/GPZ/SEZ with corrected ordinary scene semantics.

**C1-R5 NO-CODE CLOSEOUT; R6 RESEARCH/PROVEN-CORRECTION GO; CLASSIC REPLACEMENT HOLD.**
