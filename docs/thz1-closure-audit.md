# THZ1 closure audit

## 1. Scope and ROM revision

This is the final bounded audit of Turquoise Hill Zone Act 1 against POC 18.3.
The authoritative ROM is 524,288 bytes with SHA-256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
The audit separates static data, byte-verified assembly, source traces,
controlled original-Z80 traces, gameplay observation, POC adapters and
unresolved behavior. Appearance is not used to assign semantic item names.

## 2. Starting revisions

- Reference `main`: `69edb63b18ae3777310635c1ae1df26c8e483c1f`.
- POC `main` (read-only): `231aeaf6d898ec572ee803609ac9a4f9bf97f392`,
  `Sonic Chaos Act 1 POC 18.3`.

## 3. Type `$10` dynamic graphics

**SOURCE-TRACED / deterministic ROM decoding.** `$7AC2` dispatches nonzero
`$D3B3`; selectors below `$10` enter `$7C71`. The loader maps bank `$0E`, indexes a player-specific
pointer table as `table + selector*2`, and directly copies uncompressed SMS
Mode-4 planar bytes. Both transfers run synchronously, then the selector and
loader state are cleared.

| Selector | player `$01` sources (CPU / ROM) | Transfers |
|---:|---|---|
| `$02` | `$9A60/$39A60`; `$9F60/$39F60` | 192 bytes to `$0980`; 128 to `$0BC0` |
| `$04` | `$9D60/$39D60`; `$A160/$3A160` | same |
| `$06` | `$9BE0/$39BE0`; `$A060/$3A060` | same |

The first transfer overwrites six preloaded common tiles, `$4C-$51`. Frame
`$0B` at `$8D0F` uses those six tiles as its top three 8×16 pieces; its bottom
pieces remain `$52-$57`. Frame `$0C` at `$8D1A` uses `$58-$5D` and `$52-$57`
and therefore has no selector-dependent pixels. Thus `$0B/$0C` are not two
dynamic icon layers: only `$0B` exposes the selected content, while `$0C` is a
fixed alternate frame.

The second transfer overwrites tiles `$5E-$61`. Shared mapping frame `$0D`
references them, but type `$10` reaches only `$00/$0B/$0C`; no placed THZ1
type reaches `$0D`. Type `$05` uses a separate mapping and tiles `$20/$22`.
Consequently the second transfer is loaded with the first but contributes to
neither the visible type-`$10` body nor the bounded type-`$05` presentation in
THZ1. Its broader all-game consumer is not assigned here.

Alternate-player pointers are preserved in the JSON: selector `$02` uses
`$A1E0/$A320`, `$04` uses `$9D60/$A060`, and `$06` uses `$9BE0/$A060`.
All source, decoded-pixel and composited-RGBA hashes are in
`object-10-graphics.json`.

## 4. Palette

**STATIC DATA / SOURCE-TRACED.** THZ1 selects background palette `$15` and
sprite palette `$06` through the level palette table at ROM `$07F3C`. Palette
`$06` begins at ROM `$3B6AD`; index zero is transparent. Dynamic content and
fixed shell pieces are rendered as sprites with this same palette. The raw
palette SHA-256 is
`c6715cef80884efccdc74a30c6c85023858169524ded2be963e16badb1f677e2`.

Deterministic non-committed previews are generated under
`build/thz1-type10-graphics/`: `selector-02.png`, `selector-04.png`,
`selector-06.png`, their per-frame PNGs, and `type-05-contact.png`.

## 5. Type `$05` bounded child

**STATIC DATA / SOURCE-TRACED.** Type `$05` has state table `$993D`
and mapping table `$8A57`. Parameter zero initializes state 1, sets object flag
bits 0/1, and begins with empty frame zero. State 1 calls `$99EA`, which cycles
frames `$01-$20`; all 32 frames contain one visible 8×16 piece using preloaded
tiles `$20` or `$22`. The frame origins move that piece around the rendering
anchor. Callback `$998A` retains it while `$D532==$06` and changes the object
to `$FF` when that selector ends.

The allocation and initializer do not copy the consumed type-`$10` world
coordinates. The exact special-render anchor path is intentionally left
unresolved. This clean boundary is enough for closure: POC 18.3 omits a
ROM-backed visible 32-frame effect associated with selector `$06`, while its
numeric reward mechanics are already implemented.

## 6. Object closure matrix

| Type | Count | Placement | Graphics / animation | Behavior / contact | Lifetime | POC discrepancy | Class |
|---:|---:|---|---|---|---|---|---|
| `$09` | 24 | closed | closed | unresolved | unresolved | no proved expansion; not merged with 142 layout rings | FUTURE FIDELITY |
| `$10` | 5 | closed | research-closed | THZ1-closed | closed | selected content absent from POC | BLOCKER |
| `$18` | 1 | closed | closed | partial / adapter | partial | original completion/results logic not claimed | ACCEPTED ADAPTER |
| `$1B` | 4 | closed | closed | substantial | partial | no concrete contradiction | FUTURE FIDELITY |
| `$21` | 6 | closed | closed | THZ1-closed | closed | none material | CLOSED |
| `$26` | 4 | closed | closed | substantial | partial | no concrete contradiction | FUTURE FIDELITY |
| `$27` | 3 | closed | closed | THZ1-closed | closed | none material | CLOSED |
| `$28` | 6 | closed | static reachability closed | adapter | partial | bounded subtype/rider/lifetime implementation | ACCEPTED ADAPTER |

## 7. Terrain and mechanics closure matrix

| System | Result | Class |
|---|---|---|
| terrain/layout and collision profiles | canonical layout and ROM-derived profiles | CLOSED |
| first ramp | controlled fixtures and launch behavior integrated | CLOSED |
| loops and twist/Mobius | traversable, with bounded scheduling/presentation | ACCEPTED ADAPTER |
| nine terrain springs | canonical placements; contextual composition | ACCEPTED ADAPTER |
| four static spike cells | canonical and not duplicated as objects | CLOSED |
| four moving spikes | canonical type-`$1B`; generic lifetime proof remains | FUTURE FIDELITY |
| ring-bearing cells and 142 rings | 72 cells are background-only; 142 separate objects retained | CLOSED |
| six platforms | two `$0A`, four `$84`; bounded rider/subtype behavior | ACCEPTED ADAPTER |
| end-of-act boundary | canonical `$18` art/placement, explicit POC helper | ACCEPTED ADAPTER |
| camera/lifetime | bounded room-instance cleanup/recreation | ACCEPTED ADAPTER |

POC source verification confirms five `$10`, one `$18`, six `$21`, three
`$27`, four moving spikes, four static spikes, six platforms, nine terrain
springs, 142 layout rings, and zero legacy layout-monitor instances. No
fabricated finish marker is treated as canonical; the completion helper is
explicitly POC-only.

One POC-commit self-check is internally inconsistent: `231aeaf` commits a
custom `OBJ_ring/Draw_0.gml`, while its `verify_v18_objects.py` asserts that the
file is absent. The remaining source assertions pass when that single
contradictory absence check is isolated in an extracted read-only copy. The
custom draw event is therefore recorded as a POC presentation adapter, not
original behavior and not a ROM-backed blocker.

## 8. Animation command `$09`

**BYTE-VERIFIED ASSEMBLY.** Handler `$6827` consumes two operand bytes after
the command and performs `object[offset] = immediate`; total form is four bytes
including `FF 09`. Type `$28` states 4/12/14 write `$50` to offset `$1E`, and
states 12/14 also write `$80` to offset `$27`. All three states then resolve to
frame `$01`; the census now has zero unresolved animation states. This closes
the animation parser gap without claiming complete platform behavior.

## 9. Remaining classifications

**BLOCKERS**

- POC 18.3 does not render selector-dependent type-`$10` tiles `$4C-$51`.
- POC 18.3 omits the visible 32-frame type-`$05` effect for selector `$06`.

**ACCEPTED ADAPTERS**

- Type `$18` completion/contact/results boundary.
- Type `$28` subtype/rider/lifetime behavior.
- Loop, twist and terrain-spring presentation scheduling.
- Camera/off-range room-instance lifetime behavior.
- The custom POC ring Draw event (and its contradictory POC verifier assertion).

**FUTURE FIDELITY**

- Type `$09` behavior and any relationship to the separate 142 layout rings.
- Formal generic lifetime/scheduler completion for `$1B/$26`.
- Full `$18` results state machine and full `$28` subtype study.
- Exact type `$05` special-render anchor path and broader all-game variants.

## 10. THZ1 milestone conclusion

**THZ1 POC BLOCKED**

Yes: two ROM-backed visible issues remain in the current POC and should prevent
declaring POC 18.3 complete as-is. Both are now bounded integration work, not
open-ended research: selector graphics for type `$10`, and the selector-`$06`
type-`$05` effect. No other established THZ1 issue is a blocker.

## 11. Recommended next project task

Integrate `object-10-graphics.json` into the POC for selectors `$02/$04/$06`,
add the bounded type-`$05` presentation, and rerun this closure gate. If both
visual discrepancies are removed without new contradictions, reassess as
`THZ1 POC READY WITH DOCUMENTED ADAPTERS` before beginning the next zone.
