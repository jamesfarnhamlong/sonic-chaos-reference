# Final playable zone canonical audit

Branch: `research/final-zone-canonical`, based on canonical `89641f8093e62401cd81f94e6ac889422f600472`. A1–A5 research contracts are prepared for review. Research main and the POC were not modified. Visual approval remains pending James.

## Deliverables

The implementation entry point is `data/rom-cache/eez/implementation-manifest.json`; numeric placements and parameters are in the same directory. Contracts are documented in `docs/eez-foundation-audit.md`, `eez-environment-audit.md`, `eez-objects-audit.md`, `eez-carrier-audit.md`, and `eez-boss-endgame-audit.md`. Reproducible extractors, controlled Z80 routine checks and original scheduler checks live in `tools/eez*.py`, with focused `tests/test_eez*.py` coverage.

The three acts are 4096×1024, 4096×1024 and 3584×1024. Starts/cameras are (238,864)/(126,752), (170,430)/(58,318), and (110,288)/(0,176). Camera right limits are 3840,3840,3328; bottom is784. The corrected bank-relative mappings were checked against both original consumers for all256 entries in all three acts. Loader ceilings, written-cell counts, rings, effects and palettes are recorded in the manifest.

## Recovered mapped census

There are59 natural mapped records and422 terrain rings (146/276/0). Numeric identity is retained wherever semantic naming is not independently proved.

| Type | Act1 | Act2 | Act3 | Total |
|---|---:|---:|---:|---:|
|09|0|6|0|6|
|10|4|3|0|7|
|17|2|2|1|5|
|18|1|1|0|2|
|26|0|2|0|2|
|28|4|3|2|9|
|2C|1|8|0|9|
|36|4|6|0|10|
|38|3|4|0|7|
|5E|0|0|1|1|
|60|0|0|1|1|

New dependency chains include terrain-created3A/37, carrier17 and player16/17, ordinary36/37 and38/39, intermediate5E/5F, final60/63 and escape61/62. Shared09/10/18/26/28/2C contracts were verified rather than inferred from art. WORLD, EDGE and player-distance rules, allocation failures and update order are distinguished in the stage documents.

## Validation

Every ROM-loading tool verifies Europe v1.2 SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`. No ROM or raw ROM dump is committed.

The final full opt-in EEZ batch, including the animation extension, passed21 tests with no skips in129.478s. The focused closure suite also passed all3 tests (latest rerun2.060s). Recorded controlled assertions total601,927: environment5200, transport44800, ordinary objects10718, carrier32470, terrain/effects202, boss/endgame507036, allocations574, reuse44, natural transport79, scheduler systems9, ending command768 and render checks27. Separately, foundation verification covers1536 mapping-consumer comparisons and11774 original whole-game layout cells; complete CPU/platform restore was replayed48 updates twice per act. These are recorded oracle checks, not a count of unittest assertion calls.

Five complete controlled boss/terminal sweeps reached title: partial/full Sonic, alternate character ending selection, and delayed even/odd final-hit routes. They use explicit player/camera fixtures and original boss/scheduler code; they are not input-only playthroughs. Full CPU restore and regenerated machine caches matched. The SMS harness is approximate and does not establish cycle-exact VDP behavior. `git diff --check` passed.

## Graphics pending approval

`build/eez-approval/REVIEW.md` indexes21 locally generated boards: one new-terrain board,13 object/support composition boards, four effect boards and three original ending scene boards. `data/rom-cache/eez/approval-board-index.json` records filenames and hashes. Shared earlier compositions are deduplicated. Mapping origins, piece positions and original frame coverage are preserved; no redraw or added animation is used. The dotted terrain was checked against original VRAM and original raster samples. Boards are reproducible local artifacts, not committed copyrighted pixel dumps.

## Final clear and remaining limits

5E has16 HP and loses HP only on its recovered top-hit path. Type60 has a hit latch rather than an ordinary HP fight; non-attacking overlap directly requests death and bypasses ring loss. Its even/odd escape branches were both exercised. The61/62 chain sets final-clear flags; final zone progression bypasses ordinary results, advances to zone6/act0, selects the recovered ending and returns to title. Sonic full/partial and alternate character ending paths are source traced and exercised. No unproved credits names or substitute ending behavior is supplied.

There is no unresolved foundational decode blocker. James's21 visual approvals remain outstanding. Contributor names have not been transcribed. Widescreen arena, lifecycle and edge adapters require explicit POC design and Windows acceptance; this research does not claim that acceptance.

## Checkpoint chain

`c0ba628` foundation → `e48b69d` environment/routes → `5fd777b` ordinary objects → `9454723` carrier capture → `3824f1e` terrain/effects → `73896ef` reuse/allocation → `65b088b` carrier cleanup → `5574d29` natural transport → `84fb7b3` bosses/endings → `fd037e0` animation selector closure. The final graphics/report checkpoint follows this chain.

## Proposed POC rollout

1. Foundation, effects, terrain01/0B/0E/13, player21 and3A, retaining accepted shared families.
2. Carrier17 and player16/17 ownership/copy/detach behavior.
3. Ordinary36/37, then38/39, including producer pool failure and score presentation.
4. Intermediate5E/5F, then60/63, then61/62 and final-clear handoff.
5. Recovered ending/credits/title presentation and explicit widescreen adapters.

Review and merge useful Research checkpoints before treating them as accepted canonical POC inputs. Each POC milestone still requires Windows acceptance.

## AGENTS candidate updates

- Record zone5's three-act package after review, with manifest/census and new17/36–39/3A/5E–63 contracts.
- Record5E's16 top-hit HP,60's direct-death contact and final-clear ending/title branch rather than ordinary zone progression.
- Clarify shared score: BCD accumulator +10 becomes displayed100 points because the renderer appends a fixed trailing zero; this does not reopen accepted earlier-zone gameplay.
- Record21 pending visual boards separately from canonical behavior verification and Windows acceptance.

