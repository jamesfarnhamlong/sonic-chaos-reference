# Canonical spring application census

Research branch `research/spring-application-census`, based on reviewed main
`81b82941e7f44865e0d551484bee82d28d600d43`. Pending Manager review; not merged.
POC was read only. No spring physics or placements were changed.

`data/rom-cache/spring-application-census.json` contains **800 natural occurrences**
in THZ/GPZ/SEZ/MGHZ/AQZ acts 1–3. Each occurrence retains WORLD cell coordinates
or the mapped placement index, ROM offset, bank/CPU address, type, flags,
parameter and aux bytes. Terrain rows retain block ID and collision-header offset.
An `applications` array gives the closed response contracts; one cell can have
multiple contact paths. Numeric byte IDs are decimal JSON integers.

| Application | Count |
|---|---:|
| Mapped `$26` | 52 |
| Mapped `$30` (AQZ shared `$26` runtime) | 2 |
| Terrain upright | 37 |
| Terrain diagonal floor dispatch | 99 |
| Terrain horizontal | 33 |
| Ceiling `$3A/$3B` | 22 |
| Type `$21` stomp | 26 |
| THZ3 type `$50` top bounce | 1 |
| Spring Shoes `$2F` | 16 |
| Ramp cells | 26 |
| Breakable bounce cells | 508 |

There are 822 application records: the 22 ceiling cells also retain their type
`$14` floor-dispatch contract. These are paths, not two simultaneously instantiated
springs. `$3A/$3B` floor dispatch uses the existing `$6A90` comparison (`block >=
$38` means left); ceiling/ring-probe dispatch uses `$749D` (right/down). The
unconditional terrain-ring-probe tail can fire while falling. Do not register
every type-`$14` cell as only a diagonal spring or only a ceiling spring.

Speeds are pixels/update. `preserved` means no write. D503 specifies bits 0/1;
other bits are preserved. Values describe a successful setter's exit, before
remaining wrapper/probe logic. In particular same-state horizontal contact can
subsequently request `$07/$08` under opposing input, and later ceiling-probe contact
can replace an earlier request. Animation families describe script entry;
requesting the executing state again does not restart its current script. A new
strong launch can therefore temporarily continue an already-running weak script.

All 54 mapped springs divide into **38 strong / 16 weak**. Span strength comes
from aux1, not the span-width parameter. Every weak placement is listed below;
all other mapped spring rows in the JSON are strong.

| Act | WORLD X,Y | Parameter / aux1 |
|---|---|---|
| THZ1 | 1296,608 | `$8A/$72` span |
| THZ1 | 1912,864 | `$01/$72` |
| THZ2 | 1504,896 | `$88/$72` span |
| THZ2 | 3472,288 | `$01/$72` |
| GPZ1 | 4112,192 | `$87/$72` span |
| GPZ1 | 2288,608 | `$86/$72` span |
| GPZ2 | 2672,704 | `$01/$72` |
| SEZ1 | 1152,864; 1312,800; 1472,864; 1632,896 | `$01/$72` |
| SEZ2 | 544,192; 752,384; 1072,256; 1168,256; 1264,256 | `$01/$72` |

SEZ1's spans at **(336,736)** `$8C/$00` and **(1088,544)** `$88/$00` are strong.
AQZ's type `$30` placements at **AQZ1 (5008,672)** and **AQZ3 (944,256)** have
parameter `$00`, aux0/aux1 `$86`, and are fixed strong.
THZ3 `$50` starts at **(1936,238)** and top-bounces at vy **−4.0**, request `$0B`,
D448 **0**, D503 low bits **1**, weak tumble family. Its moving contact anchor is
not its initial placement. Weak mapped springs use the same state/animation
contract with vy **−5.0**. Terrain upright is −7.5; mapped strong is −7.375;
type `$21` stomp is −6.75. None of these values is interchangeable.

AQZ2 has **no mapped springs**: 13 diagonal cells, 2 upright, 7 horizontal,
2 ramp cells and 27 breakable bounces. AQZ3 has 11 ordinary diagonal cells,
7 ceiling cells (also floor dispatch), 1 horizontal, 1 breakable and 1 mapped
strong `$30`. No naturally placed surface type `$15` occurs in these 15 acts.

Evidence is freshly decoded from the SHA-256-verified local Europe v1.2 ROM,
using `level_package`'s original act/object tables, 4095-cell runtime loader
bound and per-act map width. Runtime contracts reuse the accepted
[spring audit](spring-interaction-audit.md),
[airborne closure](player-spring-airborne-state-closure.md),
[footwear audit](powerup-shoes-audit.md) and [ramp behavior](movement.md).
Their accepted cache hashes are recorded. No new physics sweep is needed.
Special stages/Electric Egg and ordinary damage/attack rebounds are outside
this spring registration census. Ramp output remains dependent on prior surface
modifier/contact/direction; the JSON records the formula and alternate path,
not an invented constant. Spring Shoes rows describe later floor rebounds,
not an immediate pickup impulse.

POC cross-check (separate from canonical data):
`reports/spring-application-poc-crosscheck.json`. All **30** act terrain/placement
sources match: no missing/extra/wrong spring block or mapped placement bytes.
THZ1 terrain comes from `SCR_chaos_motion_data`; its 4 mapped springs and 6 stomp
objects match room-authored classes/anchors. Other acts use generated arrays.
THZ1's span class supplies the natural 160-pixel weak default. Runtime source
inspection of `SCR_chaos_level`, `SCR_chaos_spring`, `SCR_chaos_core` and
`SCR_chaos_boss` agrees on span strength, AQZ `$30`, zone-dependent diagonal vy,
upright/horizontal/ceiling requests and D448, and the `$50` weak bounce.
**Concrete POC registration mismatches: none found.** This is a static comparison,
not Windows acceptance or an exhaustive runtime replay. The POC checkout has
uncommitted Package E/F work on baseline `5d99a38`; the report hashes checked
table sources rather than attributing those changes to the baseline commit.

Reproduce with Python 3.8+ (tested Python 3.13):

```sh
python tools/spring_application_census.py path/to/SonicChaos.sms --check
python tools/spring_application_census.py path/to/SonicChaos.sms --check --poc path/to/POC
python -m unittest tests.test_spring_application_census
```

Omit `--check` to regenerate canonical JSON. The optional cross-check writes
only the separate Research report. No POC or ROM files are written.
