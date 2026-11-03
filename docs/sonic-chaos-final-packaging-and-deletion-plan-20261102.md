# Sonic Chaos — final packaging, source hygiene and permanent workspace deletion
**Manager-san #9 · 2 November 2026 · CHIEF DIRECTION**

## Chief's specific direction

The final game must not be presented as `SonicChaos_A4B_EXPERIMENTAL`; its standalone ZIP and source root contain visible old/research artifacts. Chief explicitly wants **permanent deletion of unneeded content**, **not an ever-growing archive**. The fully counted Windows workspace properties show **133 GB / 2,929,194 files / 1,268,255 folders** at `E:\AI\Codex\Sonic Chaos`. Earlier 1.41 GB count was incomplete.

Scope is **packaging and housekeeping**, not new gameplay features. Preserve M6-H Chief F5 PASS, native audio, original fidelity, 256 and 348 modes, rings, persistence, results, all Special Stages and original Sound Test. This is not a public release authorization.

## Evidence from accepted M6-G source / owner M6-H screenshots

- Project `SonicChaos_A4B_EXPERIMENTAL.yyp` contains project `name` / `%Name` = `SonicChaos_A4B_EXPERIMENTAL`.
- `options/windows/options_windows.yy`: `option_windows_display_name` is already `Sonic Chaos`; `option_windows_executable_name` is `SonicChaos_A4B_EXPERIMENTAL.exe`, while `option_windows_description_info` is `A GameMaker Game`, `option_windows_company_info` is `YoYo Games Ltd`, `option_windows_product_info` is `openSonicSMS`. Preserve original upstream acknowledgements, but do not misrepresent placeholders as current product metadata.
- Existing M6-H `datafiles`, `verification`, `experiments`, `docs`, `roms`, `objects`, `scripts`, etc. are in source extraction. Do **not** delete any folder merely because its name suggests tests or ROMs; the `roms` folder may contain private owned ROM material.
- Executable extracted contents include `data.win` (~16 MB), `options.ini`, native `g1d_z80.dll` and `g1d_driver.bin`, `a3v_psg.dll`, `a3v_programs.scsp`, `a3v_policy.json`, `a3v_c10_*.scsp`, `a3v_g1b_*.scsp`, `g1d_cases.json`, `g1e_cases.json`, `m4/`, and `SFX_*.ogg/SND_*.ogg`. All are bundled by the accepted package; mere visibility beside EXE is NOT proof a file is unnecessary.
- Accepted GameMaker script references: `a3v_policy.json`, `a3v_programs.scsp`, `a3v_psg.dll`, `g1d_z80.dll`, `g1d_driver.bin` are explicitly opened or required; `g1d_cases.json` and `g1e_cases.json` appear in proof paths and are candidate test-only files **only after** confirming normal startup/menu/Sound Test/campaign never references them. The historical `m4` PCM backend, old G1B files and streamed OGGs require dependency checks before exclusion.

## Cleanup Batch 1 — manager-reviewed; Chief deletion approval pending (2 Nov)

Designer reports a read-only verified first deletion batch of **seven exact E: paths**, totaling **2,179,106,838 logical bytes (2.18 GB decimal)**: 426,370,449 bytes of generated/extracted E: folders and 1,752,736,389 bytes across four clean historical registered worktrees. Manager review: **GO in principle**, subject to Chief's explicit approval of exact paths, a last-minute status check, verified backup and restore proof. No deletion was performed.

| Exact E: path | Reported size | Disposition |
| --- | ---: | --- |
| `E:\AI\Codex\Sonic Chaos\releases\SonicChaos_Windows_20261102_CANDIDATE_B` | ~28.48 MB | DELETE extracted duplicate of retained B ZIP |
| `E:\AI\Codex\Sonic Chaos\management-audits\production-cleanup-20261102\build` | ~369.42 MB | DELETE generated outputs (includes `build\export-b` 97.68 MB; do not double-count) |
| `E:\AI\Codex\Sonic Chaos\releases\SonicChaos_Windows_20261102_CANDIDATE` | 28,477,236 bytes | DELETE failed A extracted exact duplicate |
| `E:\AI\Codex\Sonic Chaos\SonicChaos_POC_audit1` | 468,264,673 bytes | DELETE via `git worktree remove` after status check |
| `E:\AI\Codex\Sonic Chaos\SonicChaos_POC_m5b0d` | 456,389,033 bytes | DELETE via `git worktree remove` after status check |
| `E:\AI\Codex\Sonic Chaos\SonicChaos_POC_release_m4` | 451,873,620 bytes | DELETE via `git worktree remove` after status check |
| `E:\AI\Codex\Sonic Chaos\SonicChaos_POC_release_m3a` | 376,209,063 bytes | DELETE via `git worktree remove` after status check |

**Exclude from this E: batch:** `H:\codex_backup\SonicChaos_20261102_essential\source-restore-check-b` (~104.40 MB) is an additional proposed restored-copy deletion and must be separately authorised. **KEEP** active `E:\AI\Codex\Sonic Chaos\SonicChaos_Production` (496.32 MB registered worktree containing uncommitted source renaming/metadata/startup guard), and both `packaging-b` report directories at `E:\AI\Codex\Sonic Chaos\management-audits\production-cleanup-20261102\packaging-b` and `H:\codex_backup\SonicChaos_20261102_essential\cleanup-review\packaging-b`. Their records include one unique compiled-check report.

**Candidate B smoke:** PASS as reported; new names `SonicChaos.yyp` and `SonicChaos.exe` exist locally but remain uncommitted on the packaging worktree. Native sound, C10 Sound Test banks and required DLLs retained. Tested omission of old `m4/`, eleven legacy G1B resources, `g1d_cases.json`, `g1e_cases.json` and `igor.output.manifest` for accepted normal standalone scope. OGG-by-file requirement and `options.ini` remain unresolved; keep them.

**Seven-path deletion guards:** Obtain Chief approval of exact paths; stop if any path differs, is a junction/reparse point, or contains newly discovered private/untracked/ignored data. Revalidate clean git status, registered worktree topology, independent Git bundle/source ZIP backups and restoration before each removal. Use Git's ordinary worktree remove for four registered folders, exact-path deletion for the three non-worktrees, never force, glob or delete the parent audit/release directories. Log recovered sizes and remaining worktrees. Do not let generated packages or separate source-restore folder become incidental removals.

**Unapproved 14.425 GB proposal:** Local `proposed-deletion-manifest.json` was not available for Manager verification in this chat. Its larger contents and unusually high-count directories remain UNKNOWN/NOT APPROVED until exact evidence is reviewed.

**Separate gameplay issue:** `PROD-AUDIO-A7-REPEAT` is open. Chief reports repeated spike SFX `$A7` when player crosses spike X even at very large Y separation. Possible relationship to enemy persistence is unverified. Do not treat Candidate B packaging PASS as resolving it or change gameplay as part of cleanup.

## Source package B — missing GameMaker Notes resources (3 Nov)

**Chief packaging failure:** first private source package did not open in GameMaker until omitted `notes/` files were restored. Verified accepted M6-H `.yyp` `resources[]` explicitly registers two `GMNotes` resources:
- `notes/notes/notes.yy` and associated `notes.txt`;
- `notes/compatibility_report_190926_1658555855/compatibility_report_190926_1658555855.yy` and associated report `.txt`.

These are **not standalone runtime requirements or gameplay sound assets**. However they **are GameMaker project-resource dependencies so long as the `.yyp` references them**. An incomplete source ZIP is a packaging **FAIL** regardless of a separately successful Windows EXE smoke. Do not describe historical notes as inherently load-bearing *game code*; they are **registered IDE resources**. If Chief chooses to remove old notes, remove their resource entries via GameMaker and re-save the project, preserving original history/attribution as appropriate. Otherwise include them in the source package.

**Required packager fix, not another temporary package job:** Derive a complete required-resource closure from `.yyp` resource `id.path`, folder references, `IncludedFiles`, event scripts and dependent resource files; verify every declared path exists in the source ZIP **before delivery**. Validate extraction and successful IDE-open from an isolated folder, not an existing worktree with missing resources supplied elsewhere. This check must include notes and any future seldom-used GameMaker resource types. Do not blindly delete registered source resources in the name of housekeeping.

**Version distinction:** Chief's 3 Nov distant-spike reproduction used `SonicChaos_Production_20261102_SOURCE_PRIVATE_B`, which predates the later local-only environmental-audio correction. Maintain separate labels: B source package openability, B compiled executable smoke PASS, and **environmental audio correction awaiting Chief F5 from `SonicChaos_Production\SonicChaos.yyp`**. No extra builds/worktrees needed for this check.

## Revised Chief direction — one substantial deletion pass

Chief rejects microbatches of roughly 2 GB against a 133 GB workspace; the seven-path Batch 1 is a verified **subset**, not a separate end-goal. Chief has H: backup space available. Reuse the existing full scan and 14.425 GB proposed-deletion manifest **as a starting point**, not a ceiling. No new builds, GameMaker worktrees, packaging candidates or repeated entire-disk scans.

**Priorities:** (1) inspect `E:\AI\Codex\Sonic Chaos\releases` (Chief estimates ~13 GB) by file types, ZIP/content hashes and duplicate extracted packages; **retain** exact accepted M6-H source, Candidate B source/Windows ZIP, private-only assets and unique receipts; **do not delete the releases directory wholesale**. (2) Classify the largest historic clones/worktrees `SonicChaos_POC_thz1_cleanup`, `SonicChaos_POC_m2`, `SonicChaos_POC_g2b`, `SonicChaos_POC_eez_p1` and others by Git status, ignored/untracked/unique data, recoverable sizes and directory counts. (3) Find reproducible generated/cache/output duplication across projects. Focus on reclaiming **tens of GB if substantiated**, not maximizing number of paperwork rounds.

**Backups:** Use verified H: essential backup space for the current `SonicChaos_Production` dirty source + B ZIP, accepted M6-H private original/sidecar, required ignored/native game assets, unique research and verified Git bundles/restore. Verify physical independence, source checksums and a scratch restore. There is **no requirement to clone 133 GB of known recreatable junk**.

**One consolidated deliverable:** ranked exact-path `DELETE / KEEP / INVESTIGATE` manifest for a large deletion wave with bytes/counts, content identity, Git worktree ownership, dirty/ignored/private data checks, backup/restore evidence, deletion method and stop conditions. Present before/after totals and the top remaining unknown data. Group clean worktrees and duplicate extracts, so Chief can approve one **substantial** path-enumerated batch rather than 70 smaller requests. The existing seven paths are carried into this bulk proposal; no double-count of nested `build\export-b`.

**Execution:** Chief's request to be ruthless establishes the *goal*, not blanket authorization to erase unknown/dirty folders. Once Chief approves the substantial precise manifest, use normal `git worktree remove` for clean registered worktrees, exact-path removal for duplicate/generated items, and verify after batches. No unsafe glob/root deletion, force-removal or entire releases wipe. Do not delay even the read-only inventory for the ongoing Sonic/Tails playthrough.

## Work order — independently verifiable gates

### Gate 0 — preserve accepted M6-H source before cleanup

1. Work from exact Chief-accepted private `SonicChaos_M6H_20261102_A_PRIVATE.zip`; verify its SHA-256 and source diff, retain an independent copy of this irreplaceable private candidate and the missing ignored assets.
2. The previous closure stopped due to one unrelated `OBJ_chaos_object_19/Draw_0.gml` 36-byte local CRLF versus 35-byte accepted ZIP/HEAD LF. Restore that file to the exact accepted LF bytes only, verify again that the M6-H boss code is identical to the Chief-tested candidate, then commit/push **only accepted M6-H source and source-safe receipts**. No new F5 or main merge. Report exact SHA/branch/clean remote parity. If any other difference, STOP.
3. Record a verified Git bundle of each distinct POC/reference repository and independently preserve ignored/untracked private dependencies before large deletion.

### Gate 1 — presentable, minimal windows candidate

1. Create an **isolated new GameMaker working copy** directly from the newly committed accepted source; no direct mutations of the freeze baseline. Choose canonical new project name `SonicChaos.yyp` and display label `Sonic Chaos`; use IDE **File > Save Project As** where safe, then compare registered resource counts and run F5 to ensure no GameMaker reference break. Do not rename thousands of resource references manually without dependency proof.
2. In Windows Game Options set executable filename `SonicChaos.exe`, product/title/description appropriately; remove misleading default metadata while retaining clear upstream project attribution in source credits. Do not change viewport, physics, frame rate, VM target, audio mode, timings or original content.
3. Produce separate Windows **VM x64 Package as ZIP** candidate in a *staging* folder, with `SonicChaos.exe`, `data.win` and all required external resources. Do not promise a single-file EXE; optional installer or single-file repackage is out of scope.
4. Build a complete generated-file inventory and dependency graph for included files and streamed OGGs. Label each external file **required gameplay**, **required Sound Test**, **optional compatibility/backend**, **verification-only**, **unused** or **unresolved**. Test candidate removals by rebuilding a *new* ZIP with the relevant Included Files/export switches or controlled staging omission, then perform **isolated clean-folder launch** (no original project or parent datafiles available), first music/cinematic, title/character selection, menu F2/Sound Test, selected level starts and normal end-of-stage, and both campaigns as Chief prefers. Preserve a raw before/after manifest; never delete a file directly from the only accepted standalone candidate.
5. Source root: audit and relocate evidence to correct source-safe `docs/` or remove verified duplicate presentation previews/receipts in a separate cosmetic commit. `*.yyp`, `*.resource_order`, `options/`, `objects/`, `scripts/`, `sprites/`, `sounds/`, `rooms/` (if present), `datafiles/` are not assumed removable. `verification/` and `experiments/` may be development-only for runtime but can hold irreplaceable evidence or ignored assets: compare to Git history and private manifest.
6. Chief gate: one **new packaging/naming-focused smoke**, not a full replay of previously accepted feature tests. Do not label this new presentation candidate as Chief-accepted before observed F5/EXE and source identity.

### Gate 2 — permanent workspace deletion, NOT archiving

1. Perform **read-only storage and Git topology inventory**. Identify counts and byte size per first-level directory, top small-file/folder explosion hotspots, actual registered worktrees, standalone clones, branches and dirty/untracked/ignored/private files, latest source/release checksums, generated outputs, symlinks/junctions/reparse points. Avoid a blind recursive million-file copy.
2. Every proposed deletion must be an exact path or a clearly enumerated set, with proven redundancy/reproducibility, ownership/repository/worktree relationship, unique-data check, estimated bytes and files freed, and stop/rollback evidence. Classify **DELETE**, **KEEP** or **UNKNOWN / NOT AUTHORISED**. Do **not** simply replace deletion with a historical archive.
3. Chief approves the specific deletion manifest, including required exact worktree paths and any exceptional files. After an independent verified backup of **only irreplaceable canonical source/private assets, history/receipts and other explicitly kept unique data**, permanently delete approved redundant candidates. Use `git worktree remove` only as appropriate for verified clean registered worktrees, and avoid Explorer moving registered worktrees or blanket `git clean -fdx`. Never follow reparse-point targets or force-remove unknown dirty trees.
4. Execute **small batches with logs**, validating Git worktree list, canonical project launch, required resources and remaining on-disk inventory between batches. Stop on unexpected contents/errors. Avoid deleting other projects in shared parent directories.
5. Final deliverables: one easily opened named canonical source project, one clean private Windows ZIP, independent **small** verified preserved backup (not 133 GB of junk), exact source SHA, full *deleted-path manifest*, final remaining folder/file/byte totals, and documented optional known technical limitations.

**Safety:** Chief explicitly requests permanent removal of unneeded material but has NOT individually authorised path deletion yet. Until a reviewed precise manifest exists, no automated broad cleanup or worktree removal. Do not add game features or respec ROM behaviour.
