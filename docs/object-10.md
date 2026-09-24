# Turquoise Hill object type `$10`

## 1. ROM and revision scope

This study applies only to the 524,288-byte Master System ROM with SHA-256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
CPU addresses in `$8000..$BFFF` name the stated slot-2 bank; `ROM` means a file
offset. Type `$10` scripts and callbacks are in bank `$0C`, CPU `$A101..$A22C`,
ROM `$32101..$3222C`.

Evidence labels used below are:

- **STATIC DATA**: bytes decoded from the checked ROM or committed cache;
- **BYTE-VERIFIED ASSEMBLY**: generated recovered source that reconstructs the
  same bytes;
- **SOURCE-TRACED**: behavior followed through decoded instructions;
- **CONTROLLED TRACE**: original routines executed through `tools/oracle.py`
  with explicit RAM fixtures;
- **GAMEPLAY OBSERVATION**: not claimed in this study;
- **UNRESOLVED**: the checked evidence does not justify a stronger statement.

## 2. Result summary

Type `$10` is a stationary, placement-backed numeric-reward container.
Reconstructed reachable graphics support a monitor/item-box presentation, but
no checked ROM string establishes a canonical name. Its semantic status is
therefore **SUPPORTED BUT NOT CANONICAL**.

The active object alternates frames `$0B/$0C`. Player overlap alone is not
enough: player movement flag `$D503` bit 1 must be set. A qualifying hit from
above or a side additionally requires nonzero downward player Y velocity. It
queues a parameter-selected bit in `$D3A3`, applies the generic score addition
`10 00 00`, converts the same slot to type `$0F`, and clears its placement
token. A qualifying bottom hit does not consume it: player Y velocity becomes
`+$0200`, object Y velocity becomes `-$0200`, and state 3 moves the object until
it lands and requests active state 2 again.

The three THZ1 parameters have exact numeric effects:

| Parameter | Queued bit | Direct dispatch result |
|---:|---:|---|
| `$02` | `$D3A3` bit 1 (`$02`) | clear bit; increment BCD byte `$D299` up to `$99`; sound request `$A9` |
| `$04` | `$D3A3` bit 3 (`$08`) | for player type `$01`, set `$D532=$04`, timer `$D44C=$012C` (or `$1770` at level `$08`), then run player setup `$4775` |
| `$06` | `$D3A3` bit 5 (`$20`) | set `$D503` bits 1/7, sound `$84`, timer `$D44C=$0258`, `$D532=$06`, and allocate type `$05` parameter zero unless `$D532` was already `$06` |

These are numeric ROM effects, not inferred item names.

## 3. All five placements

**STATIC DATA.** The bank-$1C placement stream contains exactly five records:

| Record ROM | Raw bytes | World X | World Y | Flags | Parameter | `aux0` | `aux1` |
|---:|---|---:|---:|---:|---:|---:|---:|
| `$705F6` | `10 90 03 4E 04 00 06 00 00` | 656 | 846 | `$00` | `$06` | `$00` | `$00` |
| `$705FF` | `10 B0 07 EE 02 00 06 00 00` | 1712 | 494 | `$00` | `$06` | `$00` | `$00` |
| `$70608` | `10 50 02 0E 02 00 04 00 00` | 336 | 270 | `$00` | `$04` | `$00` | `$00` |
| `$70611` | `10 C0 06 6E 01 00 04 00 00` | 1472 | 110 | `$00` | `$04` | `$00` | `$00` |
| `$7061A` | `10 80 0B AE 03 00 02 00 00` | 2688 | 686 | `$00` | `$02` | `$00` | `$00` |

Distribution: `$02` ×1, `$04` ×2, `$06` ×2.

## 4. Creation path

**SOURCE-TRACED / CONTROLLED TRACE.** All five records use the shared creator
bank `$1C:$80EB`, ROM `$700EB`. This is the same generic path documented by the
type-`$21` and type-`$27` studies. It calls the 11-slot allocator through vector
`$0329` to fixed `$5EE1`, beginning at `$D700` in `$40`-byte steps.

The creator writes the selected occupancy byte at `$D400 + record_index` and
copies:

| Object field | Value/source |
|---:|---|
| `+$00` | placement type `$10` |
| `+$11/+$12` and `+$3A/+$3B` | current and saved world X |
| `+$14/+$15` and `+$3C/+$3D` | current and saved world Y |
| `+$04` | placement flags OR `$40`; all five begin as `$40` |
| `+$3F` | parameter `$02/$04/$06` |
| `+$08/+$09` | `aux0/aux1`, both zero |
| `+$3E` | one-based occupancy token |

Controlled creation of all five records reproduced every field. Their
occupancy addresses are `$D409..$D40D`, tokens 10..14, and each occupancy byte
becomes `$10`.

## 5. Complete state table and scripts

**STATIC DATA / SOURCE-TRACED.** The type-pointer entry is ROM `$065D8`. The
four-entry state table is bank `$0C:$A101`, ROM `$32101`.

| State | Script CPU / ROM | Ordinary records | Callback | Behavioral relationship |
|---:|---:|---|---:|---|
| 0 | `$A109` / `$32109` | duration 1, frame 0 | `$A149` | initialization; requests 1 |
| 1 | `$A10F` / `$3210F` | duration 1, frame 0 | `$A161` | visibility/graphics latch entry; requests 2 |
| 2 | `$A115` / `$32115` | durations 5,5,4,4,3,3; frames `$0B/$0C` alternating | `$A16C` | active contact/reward state |
| 3 | `$A12F` / `$3212F` | same durations and `$0B/$0C` alternation | `$A20D` | airborne after bottom hit; landing requests 2 |

Each script ends in `FF 00`, restarting its own state script: `$A10D`, `$A113`,
`$A12D`, and `$A147`. There are no unsupported commands or unresolved states.
The fixed animation engine `$64FA..$65AE` copies duration to `+$07`, frame to
`+$06`, callback to `+$0C/+$0D`, and mapping-derived extents to `+$2C/+$2D`.

## 6. Initialization

**SOURCE-TRACED.** Callback `$A149` (ROM `$32149`):

1. sets object `+$03` bit 7;
2. writes requested state `+$02 = 1`;
3. reads player type `$D500`;
4. if `$D500 != 1` and parameter `+$3F == $04`, replaces the parameter with
   `$01`; otherwise it preserves the parameter.

For player type `$01`, controlled fixtures for `$02/$04/$06` all preserved the
parameter and requested state 1. No velocity, position, saved origin, art base,
occupancy token, internal reward identifier, or collision extent is initialized
here. Current state `+$01` remains 0 until the generic animation engine applies
the request on the next update.

State-1 callback `$A161` loads the parameter into `B`, calls `$A1F9`, and
requests state 2. `$A1F9` stores current flags `+$04` into visibility history
`+$26`. On a prior-off-screen/current-visible transition it writes `B` directly
to graphics selector `$D3B3`. Controlled transitions produced selectors
`$02/$04/$06` unchanged.

The low-selector loader at fixed `$7C71` maps bank `$0E` and loads 6 tiles to
VRAM `$0980` plus 4 tiles to `$0BC0`. The exact pointer values differ by
parameter and player type and are recorded in `object-10.json`; no graphical
appearance is used to name the parameters.

## 7. Contact and break logic

### Runtime extents and overlap

**STATIC DATA / SOURCE-TRACED.** Both active mapping records—frame `$0B` at
bank `$0F:$8D0F` (ROM `$3CD0F`) and frame `$0C` at `$8D1A` (ROM `$3CD1A`)—begin
with `06 0A 18`. The animation engine proves that `$0A` and `$18` are copied to
runtime horizontal extent `+$2C = 10` and vertical extent `+$2D = 24`.

Active callback `$A16C` first calls graphics latch `$A1F9`, returns while
visibility bit `+$04.6` is set, then calls overlap/resolution helper `$5FA0`.
That helper calls `$6328` and preserves one low contact bit:

- bit 0 (`$01`): player above / top;
- bit 1 (`$02`): player below / bottom;
- bit 2/3 (`$04/$08`): right/left side.

With player extents 9×18 and object extents 10×24, controlled strict boundaries
are:

| Axis/direction | Inside | Exact edge | Outside |
|---|---:|---:|---:|
| horizontal right delta | 18 | 19 contacts | 20 |
| player above delta | -23 | -24 contacts | -25 |
| player below delta | 17 | 18 contacts | 19 |

### Required player state and direction

After resolution, `$A16C` requires `$D503` bit 1. Ordinary overlap therefore
does nothing to type `$10`, its parameter, score, reward bits, or occupancy.
`$D532 == $06` alone does not substitute for this attack/rolling flag.

For bottom contact `$02`, direction and player requested state are not tested:
player Y velocity becomes `+$0200`, object Y velocity becomes `-$0200`, and
object state 3 is requested.

Top contact `$01` rejects requested player states `$0F/$10/$15/$1A`. Every
remaining top contact and every side contact requires player Y velocity to be
nonzero and downward (high-byte bit 7 clear). Zero or upward velocity returns
without consumption. On success the callback queues the parameter effect,
writes `+$3F=$40`, optionally changes player Y velocity to `-$0400` when current
player state is not 9, and jumps through vector `$033E` to conversion `$5F54`.

No branch writes damage request `$D3B0`. The study therefore finds no direct
type-`$10` damage path.

## 8. Parameter `$02/$04/$06` semantics

**SOURCE-TRACED / CONTROLLED TRACE.** `$A1D3` (ROM `$321D3`) accepts parameters
below `$0A`, indexes the byte table `$A1F0`, ORs the selected mask into `$D3A3`,
then clears `+$3F` and sets its bit 6. The relevant table entries are:

| Parameter | Table byte / queued mask |
|---:|---:|
| `$02` | `$02` |
| `$04` | `$08` |
| `$06` | `$20` |

The fixed dispatcher `$4AA3..$4B45` processes the lowest queued bit.

### Parameter `$02`

Bit-1 branch `$4ADA` clears `$D3A3.1` and jumps to `$3104`. That routine writes
sound request `$A9`; if BCD byte `$D299` is below `$99`, it adds one using
`DAA`. A controlled initial `$09` became `$10`. The semantic name of `$D299`
is **UNRESOLVED**.

### Parameter `$04`

Bit-3 branch `$4ADF` clears `$D3A3.3`. For player type `$01`, it writes
`$D532=$04`, sets `$D44C=$012C` (300; `$1770` only when `$D297 == 8`), changes
`IX` to the player, and jumps to `$4775`. That routine zeroes X/Y velocity,
sets maximum X field `$D373=$0700`, requests sound `$85`, calls the frame-wait
helper, stores `$D3A1=$012C`, clears player flags `+$03` bits 1/6, and requests
player state `$11`.

For a non-`$01` player type, type-`$10` initialization changes parameter `$04`
to `$01`. `$A1D3` then queues bit 0; dispatcher `$4AC0` adds BCD `$10` to
`$D29A` before shared display/update calls. This alternate-player path is
source-traced, but its user-facing meaning is **UNRESOLVED**.

### Parameter `$06`

Bit-5 branch `$4B1D` clears `$D3A3.5`, sets `$D503` bits 1 and 7, requests sound
`$84`, waits for the next available frame flag through `$062D`, and writes
`$D44C=$0258` (600). If `$D532` is not already `$06`, it sets `$D532=$06` and
calls allocator `$5E9C` with `C=$05`, `H=0`. The first free slot receives type
`$05` and parameter `+$3F=0`. The allocator does not copy type-`$10` X/Y; any
positioning belongs to type `$05` initialization and is **UNRESOLVED** here.

## 9. Reward, replacement, and effect path

**SOURCE-TRACED / CONTROLLED TRACE.** Successful top/side interaction uses the
shared conversion `$5F54`:

1. `$5F77` selects the type-`$10` score-table entry and `$262F` adds it;
2. controlled score bytes change by `10 00 00`;
3. the same slot becomes type `$0F`;
4. current/requested states, flags, animation duration/cursor, placement token,
   and parameter are cleared.

Type `$0F` state table bank `$0C:$9FC9`, ROM `$31FC9`, is recovered because it
is the directly invoked replacement. With cleared parameter, initialization
`$A060` requests state 1, clears art bases, sets object flag `+$04.0`, and
preserves the inherited nonzero type-`$10` X/Y. State 1 displays mapping frames
`$07/$08/$09`, later reaches `$A0C6`, and selects type `$FF` removal because
the cleared parameter has no high-bit lifetime mode. The replacement is
detached from placement occupancy.

Parameter `$06` additionally allocates type `$05` as described above. Its full
state machine is outside the bounded type-`$10` proof; only the allocation
contract is claimed.

## 10. Mapping and presentation states

**SOURCE-TRACED.** Frame 0 is the shared empty mapping record and is used only
by states 0 and 1. Frames `$0B/$0C` alternate in both active state 2 and
bottom-hit airborne state 3. They are therefore not parameter-dependent
contents and not the destruction presentation. The callback difference—not
the mapping frame—distinguishes stationary interaction from airborne motion.

Destruction/replacement presentation belongs to type `$0F` frames `$07/$08/$09`.
No source evidence gives a narrower semantic label to the visual difference
between `$0B` and `$0C`; they are documented as alternating active frames.

## 11. Sound, score, and global effects

Directly established effects are:

| Cause | Effect |
|---|---|
| every successful top/side interaction | score bytes `10 00 00`; same-slot type `$0F`; placement token cleared |
| parameter `$02` dispatch | BCD `$D299` +1 capped at `$99`; sound `$A9` |
| parameter `$04` dispatch for player type `$01` | `$D532=$04`; `$D44C=$012C`; sound `$85`; velocity zero; `$D373=$0700`; `$D3A1=$012C`; request state `$11` |
| parameter `$06` dispatch | `$D503` bits 1/7; `$D44C=$0258`; `$D532=$06`; sound `$84`; allocate type `$05`, parameter zero when newly selected |
| parameter `$04` rewritten to `$01` for other player type | queue bit 0; BCD `$D29A += $10` before shared display/update calls |

Sound IDs and numeric RAM effects are deliberately not assigned user-facing
names without stronger evidence.

## 12. Lifetime, despawn, occupancy, and respawn

**SOURCE-TRACED / CONTROLLED TRACE.** Creation sets visibility bit `+$04.6`.
The generic post-update routine `$61E1` clears and recomputes it against the
camera/map window. Type `$10` never sets persistence bit `+$04.1`.

- Untouched/off-range type `$10`: `$61E1` sets type `$FE` while preserving the
  placement token. Lifecycle `$626D` advances it to `$FF`; cleanup `$5EF8`
  clears the named occupancy byte and the slot. It can respawn when eligible.
- Bottom-hit-only type `$10`: state 3 retains the same placement token and does
  not set persistence bit 1. If it leaves range before landing, the same tracked
  cleanup releases occupancy. It can respawn. On the first THZ1 placement, a
  controlled state-3 trajectory starting at Y 846, velocity `-$0200`, landed
  after 17 callback updates and requested state 2.
- Successfully consumed type `$10`: `$5F54` clears `+$3E` but does not clear
  the nonzero `$D400` occupancy byte. Later type-`$0F/$FF` removal sees token
  zero, so cleanup cannot release that placement. It does not respawn merely by
  leaving and re-entering the camera range during the same loaded act.

The placement scan activation window and map-cell eligibility are shared with
the already verified type-`$21/$27` creation path. Semantic names for every
map-cell eligibility value remain outside this study.

## 13. Verification

Committed artifacts:

- `tools/thz1_object_10.py`
- `tests/test_thz1_object_10.py`
- `data/rom-cache/thz1/object-10.json`
- generated recovered regions for type `$10`, direct type `$0F` replacement,
  and the numeric reward dispatcher

The dedicated tool validates the ROM hash, reads committed placement metadata,
decodes the complete animation table, and executes original placement,
initialization, contact-boundary, parameter, reward, airborne, replacement, and
lifetime routines. `tests/verify_cache.py` regenerates the report and compares
it structurally with the committed JSON.

Reproduce with:

```text
python tools/thz1_object_10.py path/to/SonicChaos.sms
python -m unittest tests.test_thz1_object_10 -v
python tests/verify_rom.py path/to/SonicChaos.sms --output reports
python tests/verify_cache.py path/to/SonicChaos.sms
python tools/build_verify.py path/to/SonicChaos.sms --output build/verify
```

## 14. Remaining unresolved questions

- The canonical semantic name is **UNRESOLVED**. “Type `$10`, monitor/item-box
  presentation supported” is the strongest justified identity.
- User-facing names for parameters `$02/$04/$06` are **UNRESOLVED**; their
  numeric effects are verified above.
- Semantic names for sound IDs `$84/$85/$A9`, BCD byte `$D299`, and display/
  score byte `$D29A` are **UNRESOLVED**.
- The complete presentation and lifetime of the parameter-`$06` child type
  `$05` are **UNRESOLVED** beyond its verified allocation contract.
- Hardware-frame timing and a full-emulator gameplay observation are
  **UNRESOLVED**. Controlled subroutine execution is not a full SMS replay.
