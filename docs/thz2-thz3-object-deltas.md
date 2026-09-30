# THZ2 / THZ3 object parameter deltas ($26, $10, $28)

Research only. ROM: Sonic Chaos (Europe) v1.2, SHA-256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607` (verified; never committed).
`SonicChaos_POC` was not touched.

Machine-readable output: `data/rom-cache/levels/object-deltas.json`. Tool: `tools/thz2_thz3_object_deltas.py`.
Tests: `tests/test_thz2_thz3_object_deltas.py`. Regenerate with `python tools/thz2_thz3_object_deltas.py ROM`.

Evidence classes: DECODED DATA, BYTE-VERIFIED ASSEMBLY, SOURCE-TRACED BEHAVIOR, CONTROLLED ROUTINE RESULT
(original Z80 routine executed in `tools/oracle.py`; not an emulator), ORIGINAL-GAME OBSERVATION (none used), UNRESOLVED.
Object fields are numeric; no semantic names are assigned. Object-field naming used below: the placement creator
`$700EB` stores record byte 5 (flags) at `+$04` (OR `$40`), byte 6 (parameter) at `+$3F`, byte 7 (aux0) at `+$08`,
byte 8 (aux1) at `+$09`.

## 1. Implementation delta table (for POC-san)

| Object | Variant | Proven meaning | THZ1 logic reusable? | New POC logic required |
|---|---|---|---|---|
| `$26` | param `$88`, aux `$72/$72` | bit 7 = span mode, low 7 bits x 16 = trigger width in px -> **128 px** (THZ1 `$8A` = 160 px). Weak launch because aux1 != 0. | Yes, entirely | Feed width 128 into the existing span logic; decode `(p & $7F) * 16` instead of hard-coding 160 |
| `$26` | params `$00`/`$01` (THZ2, THZ3) | strong `-7.375` / weak `-5.0`, unchanged | Yes | None |
| `$10` | param `$01` (THZ3) | queues `$D3A3` bit 0; BCD `$D29A += $10`; carry past `$99` also runs the `$D299 +1` / sound `$A9` pair | Contact, bottom hit, conversion, score `10 00 00` | Reward branch only: add 10 to the ring counter with the existing 100-ring carry |
| `$10` | param `$03` (THZ2 x2) | queues bit 2; power code `$D532 = 3`, timer `$D44C = 900`; while code 3 is active the maximum-X-speed field `$D373` is forced to `$0600` every update | Contact, bottom hit, conversion, score | New reward branch: set code 3 + 900-update timer, cap X speed at `$0600`; no sound, no state request |
| `$28` | param `$0A`, aux1 `$19` / `$13` (THZ2) | reversal period = `16 * aux1` updates (400 / 304) | Yes | Feed canonical aux1 into the existing lift period |
| `$28` | param `$84`, aux1 `$00` (THZ2 x1) | identical to the four THZ1 records | Yes | None |
| all | flags | every `$26/$10/$28` record in THZ1/2/3 has flags `$00` | - | - |

## 2. Type $26

### 2.1 Every THZ2 / THZ3 placement (THZ1 shown as control)

All records: flags `$00`, aux0 `$72`, aux1 `$72`. Rows marked (new) are the only ones whose parameter is absent from the
THZ1 research.

| Act | # | ROM | Raw bytes | World (X,Y) | Parameter | Form |
|---|---:|---|---|---|---|---|
| THZ2 | 4 | `$707A7` | `26 60 04 80 04 00 00 72 72` | (864,896) | `$00` | fixed strong |
| THZ2 | 5 | `$707B0` | `26 C0 04 80 04 00 00 72 72` | (960,896) | `$00` | fixed strong |
| THZ2 | 6 | `$707B9` | `26 20 05 80 04 00 00 72 72` | (1056,896) | `$00` | fixed strong |
| THZ2 | 7 | `$707C2` | `26 10 09 20 03 00 00 72 72` | (2064,544) | `$00` | fixed strong |
| THZ2 | 8 | `$707CB` | `26 80 0D 80 04 00 00 72 72` | (3200,896) | `$00` | fixed strong |
| THZ2 | 9 | `$707D4` | `26 E0 0D 80 04 00 00 72 72` | (3296,896) | `$00` | fixed strong |
| THZ2 | 10 | `$707DD` | `26 40 0E 80 04 00 00 72 72` | (3392,896) | `$00` | fixed strong |
| THZ2 | 11 | `$707E6` | `26 F0 0E 80 04 00 00 72 72` | (3568,896) | `$00` | fixed strong |
| **THZ2** | **26** | **`$7086D`** | `26 E0 06 80 04 00 88 72 72` | **(1504,896)** | **`$88` (new)** | **span, 128 px, weak** |
| THZ2 | 27 | `$70876` | `26 90 0E 20 02 00 01 72 72` | (3472,288) | `$01` | fixed weak |
| THZ3 | 2-5 | `$70907/$70910/$70919/$70922` | `26 .. .. .. .. 00 00 72 72` | (656,384) (720,384) (784,384) (1456,384) | `$00` | fixed strong |
| THZ1 (control) | 7, 8, 22, 23 | see `thz1-object-census.md` | | (688,864) (3568,768) (1296,608) (1912,864) | `$00 $00 $8A $01` | |

Coordinates are the package's canonical `stored - 256` values, unmodified.

### 2.2 What `$88` means — BYTE-VERIFIED ASSEMBLY + CONTROLLED ROUTINE RESULT

Initializer `$7825A` (bank `$1E`; state 0 script `E0 00 5A 82`):

1. writes requested/rest state 7 (fixed idle) and adds 12 to the current and saved Y (`+$14/+$15`, `+$3C/+$3D`);
2. reads `+$3F`. If **bit 7 is clear** it returns — fixed springs. Only `$00` (strong) and `$01` (weak) are used; the
   low seven bits are not read by any fixed-spring code;
3. if **bit 7 is set**: `(+$3F & $7F) * 16` is stored at `+$34/+$35` (four `SLA L / RL H` steps), states 2 and 10 become 8
   (span idle), and `+$3F` is rewritten to 1 (weak) unless placement aux1 (`+$09`) is zero, in which case 0 (strong).

So `$88` is **not** an enum and not independent flags: it is *one flag bit plus a 7-bit multiplicand*.

| Bit(s) | Proven role |
|---|---|
| 7 | span (concealed trigger) mode |
| 6..0 | trigger width = value x 16 px. `$08` -> 128 px, `$0A` -> 160 px |

No other bit is tested by the initializer (`$7825A`), fixed contact (`$782AF`), span idle (`$783BF`) or span launch (`$78401`).
Strength is **not** encoded in the parameter for spans; it comes from aux1 (`$72` for every record -> weak).

Executed fixtures (real record bytes through creator `$700EB`, then the original routines):

| Fixture | After init `$7825A` | Result |
|---|---|---|
| THZ1 `$00` (control) | state 7, `+$3F=$00`, span 0 | fixed strong |
| THZ1 `$01` (control) | state 7, `+$3F=$01`, span 0 | fixed weak |
| THZ1 `$8A` (control) | state 8, `+$3F=$01`, span 160 | weak span |
| **THZ2 `$88`** | state 8, `+$3F=$01`, **span 128** | weak span |

Span idle state 8 (`$783BF`) requests state 9 only when: player Y velocity high byte bit 7 clear (`$D519`), player state
`$D502 != $21`, `$D522` bit 1 set, `object.X <= player.X < object.X + span` (unsigned, strict upper bound — X is the
placed X), and `|object.Y - player.Y| < $30` (object Y already includes the +12). Executed boundaries for `$88`:

| player.X - object.X | -1 | 0 | 1 | 127 | 128 | 159 | 160 |
|---|---|---|---|---|---|---|---|
| resulting state | 8 | 9 | 9 | 9 | **8** | 8 | 8 |

(The THZ1 `$8A` control yields 9 through +159 and 8 at +160.) Vertical window: activates for `player.Y - object.Y` in
`[-47, +47]`, not at `-48` or `+48`, for both.

Span launch (state 9, `$78401`): object X := `player.X & $FFF0` (measured: 1541 -> 1536); launch through `$035F -> $5F17 ->
$480C` with `HL = $FB00` (weak) and `$D448 = $00`; player requested state `$0B`, player Y velocity `$FB00` (-5.0), player flags
`$D503` bit 0 set; object counter `+$1E = $1C`; object requested state 3. **Identical to the THZ1 `$8A` control in every
recorded field.** Fixed controls: `$00` -> object state 1, `$F8A0` (-7.375), `$D448 = $FF`; `$01` -> state 3, `$FB00`.

The extension/hold/retraction handlers (`$78312..$783B2`) are shared and unchanged.

### 2.3 Derived numbers (arithmetic on proven constants, not observed gameplay)

Upright ascent gravity `$18/256` per update (docs/movement.md), gravity added before the move; the same model reproduces the
documented 296.25 px for -7.5. Weak `-5.0` rises **130.84 px** in 53 updates; strong `-7.375` rises **286.41 px** in 78
updates (ceilings and the apex wrapper ignored).

### 2.4 Does THZ2 traversal depend on `$88`?

**No evidence that it does.** DERIVED from the canonical layout: the `$88` spring sits in the floor of the row-28 corridor
(x 1120-1760; row 28 is an unbroken run of solid surface-type-1 blocks, no gap or wall). Its 128-px span `[1504,1632)` ends exactly where the
spike cell (block `$3D`, surface type 5) at (1632,864) begins (another at (1312,864)); the weak launch (~131 px) carries the
player over it. The nearest ceiling underside above the span is y = 608, 288 px up — more than the weak rise, so it is not
a route to an upper level either. The springs THZ2 progression more plausibly needs are the ordinary fixed ones
(params `$00`/`$01`, existing logic) — eight strong springs at (864/960/1056,896), (2064,544), (3200/3296/3392/3568,896)
and one weak at (3472,288). Reachability was **not simulated**; the statement is layout geometry only.

## 3. Type $10 parameters $01 and $03

### 3.1 Every THZ2 / THZ3 placement

| Act | # | ROM | Raw bytes | World (X,Y) | Param | aux0/aux1 | Queued mask |
|---|---:|---|---|---|---|---|---|
| THZ2 | 12 | `$707EF` | `10 40 05 CE 01 00 06 00 00` | (1088,206) | `$06` | 00/00 | `$20` |
| THZ2 | 13 | `$707F8` | `10 50 02 2E 02 00 03 00 00` | (336,302) | `$03` | 00/00 | `$04` |
| THZ2 | 14 | `$70801` | `10 E0 0B 0E 02 00 03 00 00` | (2784,270) | `$03` | 00/00 | `$04` |
| THZ2 | 15 | `$7080A` | `10 F0 0A EE 02 00 04 00 00` | (2544,494) | `$04` | 00/00 | `$08` |
| THZ2 | 16 | `$70813` | `10 40 01 CE 03 00 02 00 00` | (64,718) | `$02` | 00/00 | `$02` |
| THZ3 | 6 | `$7092B` | `10 B0 06 6E 02 00 01 00 00` | (1456,366) | `$01` | 00/00 | `$01` |

### 3.2 Mechanism (what is common) — SOURCE-TRACED / BYTE-VERIFIED

Lookup `$A1D3` (bank `$0C`) accepts parameters below `$0A` and indexes byte table ROM `$321F0`:
`00 01 02 04 08 10 20 40 00` for parameters 0-8, ORs the byte into `$D3A3`, then clears `+$3F` and sets bit 6. Dispatcher
`$4AA3` handles the lowest queued bit: bit 0 -> `$4AC0`, bit 1 -> `$4ADA`, bit 2 -> `$4B0F`, bit 3 -> `$4ADF`,
bit 4 -> `$4B02`, bit 5 -> `$4B1D`. Initializer `$A149` (state 1, graphics selector copy `$A161`) treats every
parameter identically except the existing `$04 -> $01` rewrite for a non-`$01` player type; fixtures for `$01` and `$03`
preserve the parameter and request state 1 for both player types, and `$A161` writes selector `$01` / `$03` to `$D3B3`.

### 3.3 Parameter `$01` (THZ3)

Mask `$01` -> branch `$4AC0`: `$D29A := BCD($D29A + $10)` (`ADD A,$10 ; DAA`), refresh the two-digit display (`$314A`), and if the
result is below `$10` (wrapped past `$99`) run `$3104` (sound request `$A9`, `$D299` +1 capped at `$99`) then `$178F`.
Executed: `$D29A $05 -> $15`; `$95 -> $05` with `$D299 $09 -> $10` and sound `$A9`.

`$D29A` is proven to be the ring counter used by the layout-ring handler (CONTROLLED ROUTINE RESULT + SOURCE-TRACED):
the terrain-ring handler tail `$3138` executes `$D29A := BCD($D29A + 1)` and, on wrap to `$00`, the same `$3104` + `$178F` pair
(executed `$05 -> $06`; `$99 -> $00`, `$D299 $09 -> $10`); damage scatter (`$4915..$4937`) spawns `C=6` objects (count derived from the
tens digit of `$D29A`, capped at 7) and zeroes it. Parameter `$01` therefore adds ten to the same counter with the same carry
behavior. No name is asserted for it. (Parameter `$02` remains the `$D299 +1` / `$A9` path from the THZ1 study, and the
non-`$01` player-type `$04 -> $01` rewrite lands here too.)

Presentation: selector `$01` loads 6 tiles from `$399A0` to VRAM `$0980` and 4 tiles from `$39EE0` to `$0BC0`; frame `$0B` differs
from selectors `$02/$04/$06`, fixed frame `$0C` is identical (hashes in the JSON). Contact, bottom-hit, conversion to `$0F`,
score `10 00 00` and persistence are the THZ1 behavior.

### 3.4 Parameter `$03` (THZ2 x2)

Mask `$04` -> branch `$4B0F`: `$D532 := 3`, `$D44C := $0384` (900), return. **No** sound request, **no** player state request, no
velocity change (executed: `$D502`, velocities, `$D373 = $0400`, `$DE04 = 0` unchanged by the dispatch itself).

The per-update routine `$4A74` (reached by `JP` from `$3654`) while `$D532 == 3`: writes `$D373 := $0600` and decrements `$D44C`.
`$D373` is the maximum-X-speed field read by the movement core (walking setters store `$0400`, state `$11` stores `$0700`,
ramp `$0600`). Executed: `$D373` reads `$0600` on every update. At timer zero the routine only clears power codes 4 and 6
(music restore `$189B`, `$D532 := 0`); code 3 is **not** cleared — in isolation `$D44C` wraps to `$FFFF` and code 3 persists
(the code-4 control clears at zero and leaves `$D373 = $0400`).

The only other code-3 consumer found is object init `$98EC` (bank `$0C`), used by type `$04` (state table `$986E`, eight position-history
followers reading `$D379..$D398`); it removes its object (`type := $FF`) unless `$D532 == 3`. No allocator for type `$04` was located
by static scan (`LD C,4` patterns), so whether the followers appear is UNRESOLVED.

### 3.5 Deltas vs the THZ1 type-$10 study

Only the queued bit / dispatch branch and the graphics selector differ. Nothing else in type `$10` depends on the parameter.

## 4. Type $28

### 4.1 Every THZ2 / THZ3 placement

THZ3 has none. THZ2:

| # | ROM | Raw bytes | World (X,Y) | Param | aux0 | aux1 | New vs THZ1 |
|---:|---|---|---|---|---|---|---|
| 1 | `$7078C` | `28 28 03 D0 03 00 0A 6A 19` | (552,720) | `$0A` | `$6A` | **`$19`** | aux1 |
| 2 | `$70795` | `28 58 0F 60 03 00 0A 6A 13` | (3672,608) | `$0A` | `$6A` | **`$13`** | aux1 |
| 3 | `$7079E` | `28 10 07 30 02 00 84 6A 00` | (1552,304) | `$84` | `$6A` | `$00` | none |

(THZ1 lifts: aux1 `$09` and `$0D`; four `$84` records with aux1 `$00`.)

### 4.2 What the fields do — BYTE-VERIFIED ASSEMBLY + CONTROLLED ROUTINE RESULT

Initializer `$78585`: parameter bit 7 -> `+$25 = $FF`, bit 6 -> `+$26 = $FF`, `(p & $3F) + 1` -> states (`+$02`, `+$36`);
aux1 (`+$09`) is copied to `+$34` and `+$37` (`$785C0`), `+$30 := $10`. State 11 (param `$0A`, callback `$786DA`) calls the reversal
counter `$78925` with `B = $10` each update; `$78925` counts `+$30` down from `$10`, and on each zero decrements `+$37`; when
that reaches zero it reloads `+$37` from `+$34` and returns `$FF` (the caller then reverses via `$0437`). Period is therefore exactly
**`16 * aux1` updates**. Executed until the return: aux1 `$09` -> 144, `$0D` -> 208 (the THZ1 values), `$13` -> **304**, `$19` -> **400**.

aux1 is read at exactly one site (the initializer); it does not affect graphics, collision, axis, speed or phase. The THZ2
`$84` record produces the same init fields as the THZ1 records (state 5, axis flag `+$25 = $FF`, counters 0).

UNRESOLVED / inherited: per-update speed (1 px/update) and initial direction come from the THZ1 lift study and were not re-executed;
whether the longer travel intersects terrain is a level-design question (`$19` = 400 px from (552,720) upward would reach y = 320).

## 5. Canonical coordinates of every new variant

| Variant | Act | (X,Y) |
|---|---|---|
| `$26` `$88` | THZ2 | (1504,896) |
| `$10` `$03` | THZ2 | (336,302), (2784,270) |
| `$10` `$01` | THZ3 | (1456,366) |
| `$28` `$0A`/aux1 `$19` | THZ2 | (552,720) |
| `$28` `$0A`/aux1 `$13` | THZ2 | (3672,608) |

## 6. Unresolved / follow-ups

* `$10` `$03`: whether anything besides the static-scan-visible writers clears `$D532 == 3`; type `$04` follower allocation; semantic names.
* `$10` `$01`: meaning of `$178F`.
* `$26`: camera activation/removal and occupancy (inherited).
* `$28`: speed and initial direction were not re-executed; rider surface unchanged.
* THZ2 progression reachability with the ordinary springs was not simulated.

## 7. Method notes

Every fixture builds the object from the real record bytes with the original creator `$700EB` where a record exists, then runs
the named ROM routine in the repository Oracle with explicit RAM. The two graphics tables and hashes reuse
`tools/thz1_object_10_graphics.py` with selectors `$01/$03/$02`. No pixels are committed.
