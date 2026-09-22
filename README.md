# Sonic Chaos SMS — engine reference

A research reference for the original Sonic Chaos Master System engine, developed while building a Windows proof of concept in GameMaker. It continues work begun with RF / Ravenfreak / Amber Davis's partial disassembly and the supplied SMS ROM.

This first reference release documents collision, the first Turquoise Hill curve, movement parameters, spring states, loops, the twisting strip, placements, and sound pointers. **It is a reference package, not a new GameMaker build or a complete decompilation.**

The complete earlier `SonicChaos_Disassembly_Continuation_01` package is preserved byte for byte under [`archive/continuation-01/`](archive/continuation-01/). You only need this reference package for a new repository; its current build and tests use `asm/recovered/`, `tools/` and `tests/`, not the archived overlay.

## Start here

- [Full research and POC audit — 21 September 2026](docs/audit-2026-09-21.md): measured coverage, fresh verification results, remaining unknowns and concrete v14 integration gaps.
- [Windows Act 1 POC roadmap after 14.5](docs/windows-poc-roadmap.md): the next spring/object, twisting-strip and completion passes with acceptance checks.
- [Act 1 emulator observations, 21 September 2026](reports/emulator-observations-2026-09-21.md): retracting spikes, the concealed contact spring and the validated opening red-spring height.
- [Act 1 concealed springs and retracting spikes](docs/act1-objects.md): decoded type `$26` and `$1B` state machines used by Windows POC 15.
- [Act 1 canon-layout policy](docs/canon-layout.md): ROM-only placement sources, the metadata cache, and the POC 15.1 placement audit.
- [POC 15.1 layout result](reports/windows-poc-15.1-layout.json): the machine-readable canon-placement totals and removals.
- [Findings and corrections](docs/findings.md): what the investigation established and why the prototype got stuck.
- [Terrain collision](docs/collision.md): sensors, profiles, previous-frame state, projection and planes.
- [Player movement and springs](docs/movement.md): original units, gravity, input/friction tables and spring flight.
- [Twisting strip](docs/twist.md): all four dispatch tables and the recovered movement handlers.
- [RAM reference](docs/ram.md): addresses checked in Chaos, rather than copied from Sonic 2.
- [Data formats](docs/data-formats.md): headers, layout, placements and sound index.
- [Porting plan and open questions](docs/porting.md): bounded next steps for the Windows prototype.
- [Provenance and verification](docs/provenance.md): credit, revision, tool versions and evidence limits.

## Verified in this release

| Check | Result |
|---|---|
| Recovered assembly | 38 regions, 8,811 bytes, 3,353 decoded instructions; explicit tables counted separately |
| Assembly reconstruction | All 524,288 ROM bytes match; unrecovered gaps are preserved from the supplied ROM |
| Differential checks | 37,233 comparisons against original Z80 subroutines pass |
| THZ collision data | 256 base headers plus 16 alternate-plane headers |
| First curve | Reproducible movement-core fixture requests ramp-launch state `$1B` |
| Upright spring | Empty-map fixture rises 296.25 pixels; requests falling on update 80 |
| Twist | Four tables × 28 tile entries; angle conversion checked for all 256 angles |
| Sound pointers | All 68 supplied SMS offsets match the ROM pointer table |

These are source and subroutine checks. They are not a full SMS gameplay replay or a Windows playtest. Tests describe the supplied RAM state and scope explicitly.

## Reproduce

Use Python 3.10 or newer. Supply your own matching ROM; this repository contains no ROM or extracted binary banks.

```sh
python -m pip install -r requirements.txt
python tools/export_reference.py path/to/SonicChaos.sms --output data
python tools/cache_game_data.py path/to/SonicChaos.sms
python tools/recover.py path/to/SonicChaos.sms --output asm/recovered
python tests/verify_rom.py path/to/SonicChaos.sms --output reports
python tests/verify_cache.py path/to/SonicChaos.sms
```

For assembly verification, install WLA-DX with `wla-z80` and `wlalink` on PATH:

```sh
python tools/build_verify.py path/to/SonicChaos.sms --output build
```

The build directory must be new. Alternatively pass `--wla-z80 PATH --wlalink PATH`. It contains a local copy of the input ROM and reconstructed ROM and is ignored by Git.

The exporter uses the standard library. `recover.py` needs `z80dis`; differential tests use the `z80` CPU emulator. No tools contact an external service or upload the supplied ROM.

## Repository layout

| Path | Contents |
|---|---|
| `asm/recovered/` | Current generated source, address labels, annotations and region manifest |
| `asm/previous/` | Earlier annotated recovery retained for provenance; not assembled a second time |
| `archive/continuation-01/` | All 22 files from the earlier continuation ZIP, including its historical overlay/build script |
| `tools/` | Version-checked exporters, decoder, reconstruction script, CPU harness and readable reference functions |
| `tests/` | Original-instruction differential checks and explicit movement fixtures |
| `data/` | Decoded profiles, pointers, parameters and prior placement/path exports |
| `reports/` | Verification results and CSV traces |
| `docs/` | Explanations, evidence, corrections and remaining work |

Assembly labels use ROM file offsets, e.g. `SC_07666`. Banked CPU addresses are identified separately in the documents and CSVs. Contributions should preserve this distinction and state whether a claim is inferred, source-traced or tested. See [CONTRIBUTING.md](CONTRIBUTING.md).
