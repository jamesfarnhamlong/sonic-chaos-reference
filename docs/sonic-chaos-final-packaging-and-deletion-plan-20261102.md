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
