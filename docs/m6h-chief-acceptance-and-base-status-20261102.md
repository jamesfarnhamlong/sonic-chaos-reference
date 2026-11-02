# M6-H — Chief F5 acceptance and base-game status
**2 November 2026 · Manager-san #9 · MGHZ-007 RESOLVED**

## Owner acceptance
Chief's report after the **single normal 348×196 MGHZ3 F5 acceptance**:

> "Yes, perfect! No notes, thats now working as intended."

**Decision: M6-H CHIEF ACCEPTED (functional/visual PASS).** Initial right camera gate between spike tips 3/4 hides the striped tree; subsequent camera pan reveals the tree, eight-spike arena and source boss naturally; completed arena, boss fight and progression were accepted **without notes**. No further MGHZ3 implementation or retest is needed without a newly demonstrated regression. This reverses the older M6-A no-code verdict on the specific spike-gated intro and closes the active MGHZ-007 issue.

## Exact accepted candidate — repository status
- **Private candidate exercised:** `E:\AI\Codex\Sonic Chaos\releases\SonicChaos_M6H_20261102_A_PRIVATE.zip`.
- **Source worktree/branch:** `poc/m6h-mghz3-spike-gated-reveal`, originating at the last published Chief-accepted **M6-G** commit `6e2ffcc1f333c5cdaa0048ac696b55c4f6308905`.
- **Important distinction:** At the F5 acceptance report, the M6-H production change was **still uncommitted and unpushed**. There is **no new accepted published source SHA yet**. Chief has accepted the *private candidate*, and a one-time source commit/push + exact hash/manifest check remains routine **closure housekeeping**, not another gameplay milestone. Do not relabel M6-G's commit as the accepted M6-H implementation or merge to `main` automatically.
- **2 Nov follow-up — benign text-format mismatch:** Designer's closeout verification found `objects/OBJ_chaos_object_19/Draw_0.gml` as **local CRLF (36 bytes)** versus accepted M6-H ZIP **LF (35 bytes)**. The Git HEAD blob matches the ZIP byte-for-byte; normalized text is identical. M6-H boss implementation matches the accepted candidate exactly. No commit/push was made. **Manager #9 authorizes restoring this unrelated file's exact 35-byte LF contents from the accepted ZIP/HEAD** (not rewriting gameplay or allowing an extra source change), then rechecking candidate payload/diff concordance and publishing only the already accepted M6-H change with public-safe evidence. If any other bytes differ, STOP instead of papering over it.
- Evidence in the private candidate: `docs/m6h-spike-gated-reveal.md`, private zip SHA-256 sidecar and source diff manifest. No private assets/screenshots/ROM data should be published to the public management repository.

## Source contract and internal evidence
- Original spike tips (world X): `3235,3243,3251,3259,3299,3307,3315,3323`. Two spike banks span `[3232,3264)` and `[3296,3328)`; striped tree opaque trunk `[3275,3285)`; boss anchor `(3269,288)`.
- At 348 wide, early right edge holds at world X3256 between spike 3/4, hiding the trunk. Final camera settles at X2980 and reveals the entire eight-spike trap through world X3328. The original 256×192 path and 4-px wide pan speed remain unchanged.
- One production source script changed, `scripts/SCR_chaos_mghz_boss/SCR_chaos_mghz_boss.gml`; 1,314 GameMaker resources and 38 IncludedFiles preserved. Candidate report says the other 6,647 runtime files match accepted M6-G byte for byte.
- Internal evidence reported: 12 PASS / **4 raw FAIL** retained. Two historical MGHZ3 camera verifiers encode superseded framing, an inherited M4 harness encounters `chaos_a3v_config` ReferenceError, and a G2-era resource list omits accepted M6-D art. All raw failures remain labelled; bounded policy-aware verification passes. Source-host tests and controlled ROM traces are not equivalent to Chief's actual Windows F5 acceptance.

## Next gate — base completion, not another speculative coding batch
1. **Publication housekeeping:** combined Research/Designer must commit/push only the exact Chief-accepted M6-H source and source-safe evidence from this private candidate; report full commit SHA, exact M6-G parent, clean worktree/remote parity, candidate receipt/source diff concordance and no private payload. No rebuild or new F5 necessary if identical. Do not modify gameplay after acceptance without renewed owner approval.
2. **Owner's complete normal base playthrough:** resume standard game progression, noting only fresh, concrete gameplay blockers or unfair widescreen presentation in one consolidated punch list. Previously accepted music, title cards, rings and enemies are not separate repeat acceptance gates.
3. **Base freeze decision:** if playthrough has no material issues, Chief can approve a private baseline freeze: one reproducible project `.yyp`, required private assets, signed manifest/hash, restoration/launch proof, source branch SHA, documented original/PC-wide deviations and technical HOLDs. No automatic main merge or public release.
4. **Optional post-base**: original attract demos, save/emerald progress, 60-FPS presentation experiment, pixel-preserving scaling, palette/effects, Vita assessment and workspace archiving only after explicit owner decisions.

## Known parked issues (not base blockers)
One-time startup/onset delay (unproven root cause), AQZ Tails underwater palette (provisionally accepted), historic SEZ/SS3/player contact quirks lacking a current reproduction, and original sound `$8E` with no known retail use. Separate technical holds include the F8 CPU-carry difference, historical SS5/THZ3/raw harness mismatches and partial natural SFX reachability. The 93-item AUDIT-0 archive is **not** an open bug queue.

**No currently confirmed mandatory production fix remains after M6-H's Chief PASS.** This is a scoped completion assessment, not a claim that every possible natural gameplay route or emulated CPU bit has been proven.
