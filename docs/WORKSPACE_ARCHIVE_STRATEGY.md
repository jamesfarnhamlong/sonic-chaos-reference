# Sonic Chaos — Local worktree and release archive strategy
**Draft plan · 2 November 2026 · NOT an authorization to delete files**

## Why this exists

Chief reports approximately **170 folders** in the local Sonic Chaos working area. Earlier cleanup did not prevent continued worktree/candidate proliferation. Janitor-san is no longer assigned; Chief, Manager-san and the **combined Research/Designer Codex agent** will handle this carefully at base freeze. Nothing is to be deleted, moved or unregistered before that approval.

This document is a **controlled archival design**, not an instruction to run automatic cleanup now. The full playable private GameMaker source and ignored/private assets may not all be represented by the public Git repositories.

## A. Read-only inventory (run later, locally)

Produce one machine-readable manifest (suggested CSV + JSON) for every direct and nested top-level candidate directory under the known Sonic Chaos workspace. Record:
- Full absolute path, folder size, last modified timestamp, and provisional label.
- Git repository identity and `git rev-parse HEAD`, current branch, remote and `git status --porcelain=v1 -uall` / tracked/untracked counts where applicable.
- All registered Git worktrees via `git worktree list --porcelain` **from each actual repository**. Note whether a folder is a registered worktree, standalone clone, detached copy, release ZIP, generated runner cache, ROM cache or unknown.
- Presence of `.yyp`, `.yy`, ignored sprite/audio files, `IncludedFiles`, unique local data, original ROM binaries, output executables and receipts.
- Existing source ZIP/receipt filename, size, SHA-256, ability to verify contents, acceptance status and original commit lineage. **No hashing of every huge file in every folder upfront**; hash candidate archives and unique/valuable payloads first, escalate only for duplicates/ambiguous contents.
- Flags for dirty tracked edits, untracked work, missing LFS/private art/restoration, and any file inaccessible to the agent.

**No deduction from names alone:** a folder called `old` or `test` may contain the only copy of uncommitted research or required resources.

## B. Proposed eventual archive classification

| Class | Typical contents | Initial action |
| --- | --- | --- |
| **CURRENT CANONICAL** | Last **Chief-accepted** GameMaker source, original resources, build dependencies, working reference research docs | Preserve accessible; prove opening/running from restored source and record exact source SHA |
| **IMPORTANT HISTORICAL** | Milestone source snapshots, unique original-ROM research, unusual bug traces, acceptance receipts, milestone notes | Keep in indexed read-only archive (or immutable source commit plus private asset manifest); verify ZIP/restore |
| **DIRTY OR UNKNOWN** | Uncommitted/untracked experiments, detached and unmatched folders | **Keep untouched; investigate individually** |
| **REPRODUCIBLE GENERATED** | Temporary compilation output, clean identical checkout, re-generated diagnostic cache with verified dependencies | Candidate for future removal **only after** reproduction proof and Chief explicit approval |
| **SUPERSEDED PRIVATE RELEASES** | Intermediate source-only ZIPs with a later verified equivalent and no unique private assets | Candidate for cold archival/deduplication, **not automatic deletion** |
| **UNRELATED/OTHER PROJECTS** | Shared tools, other game research, unknown install directories | Out of scope, never touch |

A Git commit records tracked source, **not untracked files and excluded private art**. Never assume a public POC checkout alone can reproduce the accepted private GameMaker source; maintain a manifest of all dependencies and an independently backed up full private checkpoint.

## C. Approval and staged execution

1. Combined Codex agent delivers the **inventory and dry-run proposal only**, with estimated space savings, exact folders, Git worktree relationship and hash evidence. Manager reviews for wrong classifications and updates a shortlist.
2. Chief chooses the archive location and approves **specific individual folder classes or paths**, not a blanket “clean all” instruction. Retain at least one independent verified backup outside the working directory; GitHub does not substitute for it.
3. Before any removal, perform a **scratch-location restore smoke** from the candidate canonical private archive: exactly one registered GameMaker `.yyp`, 1,314 current resources (or later accepted count), 38 current IncludedFiles (or later accepted), native driver, copied/ignored files present, GameMaker opens and F5 runs on Chief's working installation. Verify SHA-256 and resource manifest.
4. Where registered Git worktrees are actually retired, use Git's worktree management commands **only after ensuring clean/no-unique-data**. Don't move registered worktrees in Explorer; don't strip Git metadata or force-prune unknown worktrees.
5. After Chief approves, execute cleanup in small logged batches. Maintain before/after manifest, paths touched, bytes recovered and validation. Retain a non-destructive rollback window where possible. If a hash/restore/status check differs, **STOP**.
6. The ideal steady state is **one active POC worktree + one reference checkout + short-lived explicitly named feature worktree**, a separately backed-up archive and immutable Git history. New agent milestones should retire a worktree at the *next approved archiving window*, not spawn permanent clones without a receipt.

## D. Safety invariants

**Forbidden without explicit Chief authorization:** `Remove-Item -Recurse` over unknown directory trees, `git clean -fdx`, `git reset --hard` on dirty branches, forced `git worktree prune`, deleting last private assets or ROM source, changing GitHub repo visibility, publishing ROM/art/audio/private packs, deleting source ZIPs simply because a newer build exists.

**For now:** continue the accepted M6-F Chief F5 gate and full playthrough; this is a later archival milestone, not today's workload. Read [AGENTS.md](../AGENTS.md) and [ROADMAP.md](../ROADMAP.md) for current project authority.
