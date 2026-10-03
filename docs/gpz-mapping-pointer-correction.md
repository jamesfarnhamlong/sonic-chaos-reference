# GPZ block mapping pointer correction — pre-commit report

Branch: `research/gpz-mapping-pointer-correction`, based on canonical Research
`ee477ea5884b4a3b5c108d31e3192c24ea22f609`. No commit or push has been made.
POC and root AGENTS.md are untouched. The local Europe v1.2 ROM was verified
against SHA-256 `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.

## 1. Original formula and independently verified consumer

**SOURCE-TRACED + CONTROLLED ORIGINAL ROUTINE RESULT.** Loader `$4FDC` selects
the act header via `$5082`. `$4FFC..$500B` stores header byte 0 (mapping bank)
in `$D162`; `$5002..$500B` stores header bytes 1/2 (mapping table CPU address)
in `$D164/$D165`. For every GPZ act these are `$11` and `$9640`.
`$4C9C` and `$4E1F` read `$D162` and call `$1C6F`; that routine writes the bank
to `$D12B` and mapper register `$FFFF`, selecting ROM slot `$8000..$BFFF`.

Horizontal render loop `$5316..$5322`:

```text
LD E,(HL)                 ; 8-bit layout block ID
LD D,0
EX DE,HL
ADD HL,HL                 ; block ID * 2
LD BC,($D164)             ; mapping table CPU address
ADD HL,BC                 ; pointer entry address
LD E,(HL)
INC HL
LD D,(HL)                 ; raw little-endian word is absolute CPU address
```

`$5335 ADD HL,DE` adds only the selected column offset (0/2/4/6), and
`$533D/$5341` read attributes directly through that address. There is no second
addition of the table base. Vertical render loop `$53DF..$53E8` performs the
same lookup; `$53F1` adds only the selected row offset (0/8/16/24), then `$53F8`
copies eight attribute bytes with LDIR. Mutation consumer `$761C..$7628` also
loads the raw word into DE and passes it directly to `$23F9`.

For block ID `b`, table CPU address `T`, and bank `B`:

```text
bankBase = B * $4000
tableFile = bankBase + T - $8000
entryFile = tableFile + 2*b
P = LE16(ROM[entryFile:entryFile+2])
mappingCPU = P
mappingFile = bankBase + P - $8000
```

GPZ bank base is exactly `$44000` (bank `$11`), not `$45640`.
Examples (all addresses hexadecimal):

| Block | Entry file | Raw word | Bank:CPU | Correct file | Old wrong file |
|---|---|---|---|---|---|
| `$00` | `$45640` | `$9840` | `$11:$9840` | `$45840` | `$46E80` |
| `$3C` spike | `$456B8` | `$9F20` | `$11:$9F20` | `$45F20` | `$47560` |
| `$8C` deck | `$45758` | `$A360` | `$11:$A360` | `$46360` | `$479A0` |
| `$97` deck | `$4576E` | `$A4C0` | `$11:$A4C0` | `$464C0` | `$47B00` |

The original loader was executed for all 18 normal acts. Both original pointer
consumers were then executed for all 256 block IDs in each act, and their
bank-mapped 32 attribute bytes compared with the decoder: **9,216 checks**.
Routine-region hashes and per-act pointer/attribute hashes are reproducible in
`data/rom-cache/gpz/block-mapping-audit.json` via `tools/block_mapping_audit.py`.
This is a bounded routine oracle, not a full SMS presentation emulator.

## 2. POC diagnosis

Confirmed: the previous decoder used `mapping_rom + P - $8000`, creating an
erroneous `$1640` addition for GPZ. THZ's table begins at `$44000`, so the
incorrect and correct formulas happen to agree there.

## 3. Affected records and files

The **289 records** are manifest records across GPZ1/2/3: **103/115/71**, with
127 distinct exported block IDs including replacement targets. They are not
289 entries in one table: the GPZ table has 256 entries, all using the same
bank-relative rule. Every exported record's address, mapping attributes/hash,
decoded pixel hash and pixel count has been regenerated from the corrected
decoder. All 289 mapping and pixel hashes changed.

Changed production tools: `tools/level_package.py`, `tools/isometric_platform.py`,
`tools/gpz_foundation.py`. Regenerated caches: GPZ implementation manifest and
isometric-platform cache; the manifest's isometric dependency hash and copied
surface1c contract now follow the regenerated cache. Added the independent
all-zone pointer audit tool/cache and its tests. Corrected both GPZ foundation
and isometric audit documents and their graphic fixtures/tests.

## 4. Corrected surface $1C visual/collision interpretation

All twelve `$8C..$97` blocks contain visible terrain deck/platform art. The old
wrong addresses read 16 `$FFFF` attributes for every deck block, referencing
unloaded tile `$1FF`; the resulting zero pixels were a decoder error. The prior
invisible/collision-only interpretation is withdrawn.

Nonzero pixels per 32x32 block, in `$8C..$97` order:
`512, 512, 200, 512, 1024, 1024, 478, 1024, 1024, 1024, 712, 1024`.
Static spike `$3C` has 384 nonzero pixels; `$00` remains correctly blank.
Pointer/attribute/pixel hashes for these representative fixtures are in the
audit cache. A local, ignored preview is
`build/gpz-mapping-correction-fixtures.png`; it was visually inspected.

The systems remain independent: `$1C` is terrain with its own profiles;
type `$28/$83` is an object with its shared mapping/anchor/support behavior.
Object platform graphics were unaffected. Dynamic palette/background/scroll
presentation remains a separate unresolved scope.

## 5. Collision findings

Only graphics/mappings and their interpretation change. Both collision planes,
raw vertical/horizontal profiles, header flags/modifiers and special `$1C`
bit-6 continuation remain identical to the prior manifest. The isometric cache's
entire `surface_1c_boundary_sweeps`, `type_28_parameter_83_sweep`,
`selected_emulator_traces`, and object `graphics` sections were regenerated and
compared with HEAD: **identical**. Layouts, rings, placements, VRAM hashes/loads
and palettes also remain unchanged. No collision geometry was tuned.

## 6. Other zones and tools audited

All three acts within each zone share the following table and conversion:

| Zone | Bank | Bank file base | Table CPU | Table file | Previous address error |
|---|---|---|---|---|---|
| THZ | `$11` | `$44000` | `$8000` | `$44000` | 0 |
| GPZ | `$11` | `$44000` | `$9640` | `$45640` | `+$1640` |
| SEZ | `$11` | `$44000` | `$AA40` | `$46A40` | `+$2A40` |
| MGHZ | `$14` | `$50000` | `$8000` | `$50000` | 0 |
| Aqua (tool key `apz`) | `$14` | `$50000` | `$9320` | `$51320` | `+$1320` |
| EEZ | `$14` | `$50000` | `$A4E0` | `$524E0` | `+$24E0` |

The shared decoder fixes future SEZ/Aqua/EEZ exports too. No committed rendered
block/level caches for those zones exist in this Research checkout, so no
additional existing Research cache needs regeneration for this pointer bug.
Local/generated exports made with the old decoder for those zones need rebuilding.
THZ committed level packages regenerate unchanged.

Audited callers: `block_pixel_maps`, `block_usage`, `level_maps`, `level_export`,
`gpz_foundation`, `isometric_platform`. THZ-specific background registration and
final-runtime closure have explicit `$44000` bank-base formulas; they are correct
for their stated THZ scope. Object mapping/frame readers (`thz1_object_assets`,
`thz1_animation_reach`, object10/18/50 and player/shoe graphics tools) use explicit
bank bases, independently of table location. `rom.header` collision/profile
conversion uses the fixed collision bank base, not its pointer-table offset.
No second generalized table-relative conversion was found in the tools search.

## 7. Regenerated hashes and cache impact

Canonical JSON SHA-256 uses sorted keys and compact separators, matching the
manifest dependency-hash convention, and is independent of checkout line endings:

| Cache | Corrected canonical JSON SHA-256 |
|---|---|
| `isometric-platform.json` | `34a3dbdda4b5261c483363e5a8718979c27dae78096571fdb02164a339533161` |
| `gpz/implementation-manifest.json` | `f37cf40d2e27068b785c9793889616a8c49ce93dbaba9deb69f05686e886073e` |
| `gpz/block-mapping-audit.json` | `a679e5cc82b6c7eac30e68ac6cdde40aa52067b84ae4ce30add00c0ff29145a9` |

All 256 GPZ mappings concatenated in block-ID order hash to
`aa6b5fc4883f606ea4cf05bb38f3fd36906387374d76a75b14e4d08b49e19a89`.
Corrected spike `$3C` decoded palette-index hash:
`aee96c13cb89abd37b74d8391f8664085015b521c642824bf83eecc7bc17e188`.
Corrected deck `$8C` decoded palette-index hash:
`39a8f04e764f53c8bff03ebfd881780ea39985b1871619bd76cc01c122a4bf26`.
No erroneous expected mapping hash was preserved to satisfy tests.

## 8. Focused tests and reproducibility

Run in the Research worktree with `SONIC_CHAOS_ROM` pointing to the verified
local ROM:

```text
.venv/Scripts/python.exe tools/block_mapping_audit.py "../source/Sonic Chaos (Europe).sms" --check
.venv/Scripts/python.exe tools/isometric_platform.py "../source/Sonic Chaos (Europe).sms" --check
.venv/Scripts/python.exe tools/gpz_foundation.py "../source/Sonic Chaos (Europe).sms" --check
.venv/Scripts/python.exe -m unittest tests.test_block_mapping_audit tests.test_gpz_foundation tests.test_isometric_platform tests.test_level_package -q
git diff --check
```

**72 focused tests passed, zero skips**, including original-ROM checks,
deterministic full isometric regeneration and unchanged THZ package regeneration.
The new five tests include a synthetic non-bank-aligned table with distinguishable
correct/wrong data, invalid CPU pointer rejection, both original consumers across
all acts, spike/deck pixel locks, and all 289 exported records. `git diff --check`
passes. No POC build or Windows gameplay acceptance is claimed.

## 9. AGENTS.md candidate correction

> GPZ block mapping table is bank $11:$9640 (file $45640). Its words are absolute
> CPU pointers within bank $11: file = $44000 + pointer - $8000. Never add the
> table's intra-bank offset when resolving mapping words. Apply this bank-relative
> rule to all zone tables. The old surface $1C zero-opaque-pixel/collision-only
> conclusion was a decoder error; blocks $8C..$97 contain visible canonical
> deck/platform art. Existing collision profiles, $1C special rules and object
> $28/$83 behavior are unchanged. Regenerate POC GPZ art/mapping data from the
> corrected Research package before the next Windows comparison.

Manager-san can consolidate this correction at an accepted checkpoint. The root
coordination file was not edited.
