# Sonic Chaos M5-B0 — Manager-san #7 source audit (initial; 27 October 2026)

**Status:** SOURCE-BACKED INITIAL INVENTORY; B0 designer crosswalk/preflight remains subject to review. **M5 OPEN**. This manager-owned **documentation branch** is independent of Research C6/C7, GameMaker M4/A4B and canonical management `main`. Publishing this document is not programme approval, a source merge, or a Windows runtime acceptance.

## Exact source checkpoints

- Canonical `AGENTS.md`, `MEMORY.md`, `ROADMAP.md`: `sonic-chaos-reference:main@759cbd8a8077b75a8d5609de63281fc9aa2ced63`.
- C6 request catalogue: `research/m5-a2c6-preflight-tone2-proof@45b15a578285add733fa1def9a7e7174c0215c2d`, specifically `data/m5-a2c6/coverage.json` and `planning.json`.
- C7-1 source-backed research: `research/m5-c7-1-original-music@7496725dd1a1cc1dda339e1334931b7a5a495198`, especially `docs/m5-c7-1-original-music.md`, `data/m5-c7-1/verdict.json`. C7 is **not merged into main**.
- Chief-accepted stable private GameMaker M4: `SonicChaos_POC:poc/m4-authentic-six-id-audio@11bff34356d5f5d979218896dc95fdc4bb265eae`.
- Chief-human-functionally-accepted native THZ experiment A4B: `SonicChaos_POC:poc/m5-a4b-title-card-bridge@afdd6a1e62e5e61234159266a05bcddab825faf9`. Neither experiment nor research is promoted by this document.

## Exact ID reconciliation

C6 lists **70** original request IDs: 39 bounded verified (15 music / 24 SFX), 24 unsupported/unverified (11 music / 13 SFX), seven empty/control. M4 F2 already lists exactly **68** UI IDs, $81 through $C4 inclusive, partitioned into 31 music ($81..$9F) and 37 SFX ($A0..$C4). The remaining two C6 IDs are internal `$00` empty pending request and `$F8` reset/silence; neither is a song. Five of the 68 F2 rows (`$9B..$9F`) are empty: **no invented playback**.

The machine-readable **70-row ledger** at [`../data/m5-b0/manager7-ledger.json`](../data/m5-b0/manager7-ledger.json) was assembled from pinned C6 coverage and the actual M4 debug menu JSON; it retains C6 status, original lifecycle, historical F2 label and preview availability separately. All `gameplay_writer_inventory_complete` flags are false until Designer's data-driven writer census is independently reviewed.

M4 game PCM/stem catalogue: `$90,$99,$82,$81,$BF,$A6` (six IDs). The M4 F2 explicit preview assets are only `$90,$82,$81,$BF,$A6` (five). A4B has exactly `$81,$96,$88,$BF,$A6` as genuine original-driver native IDs, gated to THZ1 and *not automatically wired into F2*. Do not equate historical PCM previews with verified original native programme playback.

### Confirmed existing F2 contract defect (M4 source)

`chaos_debug_audio_request(id,true)` invokes `chaos_audio_preview(chaos_debug_audio_preview_asset(id))` and **returns true unconditionally**, even if the mapping is `noone`. The F2 Step labels that success PLAYING; the Draw availability check uses a different fallback-capable asset function (`$A4` can appear available when no dedicated F2 preview exists). Do not relabel unavailable requests as native playable. The historic sample-backed playback path also suspends/clears the current audio owner. Any F2 native experiment must explicitly define ownership, stop, same-ID retrigger, finite end, authentic loop and return-to-game controls.

Actual M4 source: [menu](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/11bff34356d5f5d979218896dc95fdc4bb265eae/scripts/SCR_chaos_debug_select/SCR_chaos_debug_select.gml), [Step](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/11bff34356d5f5d979218896dc95fdc4bb265eae/objects/OBJ_chaos_debug_select/Step_0.gml), [Draw](https://github.com/jamesfarnhamlong/SonicChaos_POC/blob/11bff34356d5f5d979218896dc95fdc4bb265eae/objects/OBJ_chaos_debug_select/Draw_0.gml).

### Game event evidence already mapped — not exhaustive

M4 `chaos_audio_level_music(zone,act)` maps THZ `$81`, GPZ `$83`, SEZ `$91`, MGHZ `$92`, AQZ `$93`, EEZ1/2 `$95`, EEZ3 `$90`; `OBJ_chaos_zone/Create_0.gml` requests `$8F` for Special Stages. Title/choice/opening include `$99/$82/$90`. Results/death include `$88/$96/$B4/$87/$94`. Boss entry `$8C` and boss events can request `$B6/$C4/$97`; rings `$BF`, spring `$A6`. **Dynamic ending, title, SS and boss event tables, and all objects, need full Designer enumeration.** Empty ledger writer fields never mean proof of unreachability.

M4 deliberately withholds `$90` playback in EEZ3 because pilot PCM is opening-only; the same numeric ID in two scenes does not prove a common authentic native repeating life cycle.

## C7-1 current Research status — diagnostic accepted, full programmes HOLD

At `7496725dd1a1cc1dda339e1334931b7a5a495198`, original solo driver recurrence is independently established:
- `$83` GPZ: original full driver recurrence **3072** ticks; first original recurring state tick 522, repeat 3594. **Candidate fails at tick 2784** on pitch table data read `$4634–$4635` outside validated SCSP regions. The original uses executable-range bytes as note data; this does not authorise broad executable-data import or guessed pitch.
- `$92` MGHZ: original full driver recurrence **3648** ticks; first state 511, repeat 4159. **Candidate fails at tick 3266** on real F7 index 4 using channel byte 43. This byte lies in nominal call-stack storage; no demonstrated live stack collision, but a narrowly proved alias/lifecycle contract is essential.

Research reported 144 public tests PASS, 10/10 negative controls caught, 12,148 matched candidate/original prefix ticks, 59,770 ordered PSG bytes and 8,928,780 exact A1L PCM samples. Both complete solos rejected; C6 verified count remains **39**. The original driver loops are not a substitute for an executable decoder/SCSP/renewal certificate or native A1L playback certification.

**Recommended next Research gate:** C7-1R proof/repair for only these two failures, preferably one independently acceptable path at a time. Do not start a new two-song rollout while these sources are explicitly blocked. No globally relaxed 4200 guard, F7 index, memory provenance checks or arbitrary data/code records; continue full original-Z80 state + ordered PSG + continuous accepted A1L exactness and genuine per-song renewal proofs.

## Designer B0-D handoff and approval boundary

Designer reports a 21-check PASS source-only preflight and a conditional proposal: authentic **finite `$99` title music** via an A4B-derived experimental GameMaker worktree plus **bounded native F2 audition**, while non-THZ zone music and C7 $83/$92 remain HOLD. The Designer worktree `poc/m5-b0d-audio-preflight` reportedly remains at A4B head with **uncommitted/unpushed** docs. This report is a second-hand status, not yet independently verified by Manager.

**Immediate action to Designer:** commit/push *only* B0-D documentation and source checks to a private, isolated branch, send exact remote SHA and report path; keep M4 and A4B read-only. Reconcile your complete 70-row writer ledger with this initial manager ledger; record meaningful disagreements with cited exact sources. Manager will read the actual private report before final implementation GO.

If B0-D passes review, the first bounded code candidate may add only `$99` (C6-finite) to a new A4B-derived experiment and wire `$99` plus already-native authenticated allowed IDs to F2 **only where native eligibility is actually proven**. No unproven zone routing, no faked F2 playable statuses, no copied PCM substitution. Gate new scenes/priority/fade/reset, original finite endpoint, exact independent Z80+PSG+735-sample continuous A1L, single persistent PSG/audio owner, pause/return/teardown and short Chief Windows F5 listening. All new code commits require their own isolated branch and explicit narrow authorisation.

## Preserved technical invariants and roadmap

Original 60 sound ticks/s; 735 samples/tick at 44100 Hz; original Z80 ordered PSG write sequence, driver/channel/global/IY/DE11/priority/ownership state; accepted unchanged A1L PCM and single persistent PSG owner; authenticated per-song loop and bounded guard; exact private bank/SCSP hashes; fail hard unknown operations. No restart of parked A4L/Q/S latency probes or queue policy changes, no stable M4 changes or automatic A4B promotion. Private ROM/audio/SCSP/DLL/image assets never enter public Research. M5 soundtrack and F2 remain first; SFX after; M6/M7/M8 parked as previously documented.

**Authority level:** This is an initial B0 source audit and communication aid for Designer/Research, NOT an amendment to `AGENTS.md`, `MEMORY.md` or `ROADMAP.md` and NOT a statement that 70 writers are exhaustively mapped. Final B0 awaits pushed Designer documentation and managerial review.
