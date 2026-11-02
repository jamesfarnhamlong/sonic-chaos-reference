# Sonic Chaos — Local worktree and release archive strategy
**Draft plan · 2 November 2026 · NOT an authorization to delete files**

## Why this exists

**Correction, 2 November:** Explorer's previous screenshot showing 1.41 GB / 50,963 files / 20,642 directories was captured **while Properties was still counting** and is invalid as a total. The later screenshot of `E:\AI\Codex\Sonic Chaos` shows **133 GB (143,395,317,692 bytes; 135 GB allocated), 2,929,194 files and 1,268,255 folders**. This is the latest observed count, **not yet independently confirmed as a final, stable count**. Former estimates of ~170 refer only to top-level development/worktree groups, not their recursively counted folders. The workspace is large in both bytes and file counts; inventory-first planning is required. Earlier cleanup did not prevent continued worktree/candidate proliferation. Janitor-san is no longer assigned; Chief, Manager-san and the **combined Research/Designer Codex agent** will handle this carefully at base freeze. Nothing is to be deleted, moved or unregistered before that approval.

This document is a **controlled archival design**, not an instruction to run automatic cleanup now. The full playable private GameMaker source and ignored/private assets may not all be represented by the public Git repositories.

## Emergency preservation and pre-cleanup backup gate

1. Preserve the **exact Chief-accepted M6-H private ZIP** and its SHA-256/manifest. Designer's 2 Nov closeout was temporarily blocked by the **local CRLF (36-byte) versus accepted ZIP LF (35-byte)** difference in an *unrelated* goal-draw script. The already accepted boss script matches byte-for-byte. Restore only the unrelated file to the exact accepted ZIP/HEAD LF bytes, verify source identity, then commit/push M6-H with a new full SHA and clean receipt **before** declaring Git history backed up.
2. **Immediately protect the small irreplaceable artifacts first**, especially the accepted M6-H private ZIP, SHA-256 sidecar, local uncommitted M6-H source/diff, research receipts and required ignored/private resources, on an **independent physical disk or separately snapshotted backup target**; verify package hashes. Preserve the original untouched. **Do not run a blind whole-tree Robocopy yet**: the latest Explorer observation is already 133 GB / 2.93 million files / 1.27 million folders, and the count may not be final. First perform a **read-only top-level and filesystem/size inventory** to identify Git worktrees, large directories, junctions/reparse points, duplicated generated trees and private-only assets. Then select and verify a practical **complete workspace backup** (e.g. volume/snapshot-based backup or controlled file copy) before any deletion. Backing up on E: alone is not independent. A Git commit or bundle cannot replace ignored/untracked material.
3. Independently make `git bundle create <name>.bundle --all` backups for each **distinct repository root** (at least POC and reference). Check registered `git worktree list --porcelain`, dirty/untracked statuses and local-only refs before bundling. Verify using `git bundle verify` and a **scratch clone**/branch-list check. A Git bundle does not contain ignored/untracked private files, Git LFS payloads not in objects, or a worktree's dirty edits; they require the full workspace and private source ZIP copies.
4. Keep a frozen standalone Windows **Package as Zip (VM, x64)** from Chief's accepted H project as an optional smoke artifact, not a replacement for the reproducible .yyp + private included files. Compare first-launch opening/audio onset versus IDE F5; do not change GameMaker target/physics or driver while evaluating the delay.
5. A **lightweight, read-only inventory is appropriate now** to size the backup and expose recursive folder hotspots; the full deletion/archive classification and all destructive action still wait for Chief's planned Sonic/Tails playthrough and explicit approval. No files are to be removed or moved in this phase. No deletion until Chief signs off the exact dry-run action list, backup location and restore result.

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

**For now:** M6-H is Chief F5 accepted; first protect the accepted private ZIP and local uncommitted source, do a read-only high-level inventory, finalize the exact source commit, and plan a verified independent full backup. Chief's two campaign playthroughs and explicit disposal approval still precede destructive cleanup. Nothing in this document grants deletion permission. Read [AGENTS.md](../AGENTS.md) and [ROADMAP.md](../ROADMAP.md) for current authority.
