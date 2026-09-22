# Sonic Chaos ROM-derived cache

This cache contains deterministic metadata extracted from the version-checked
Sonic Chaos Master System ROM. It deliberately contains no ROM image, graphics,
tile pixels, palettes, or audio.

Every generated file records the required ROM SHA-256. Rebuild the THZ1 cache:

```bash
python tools/cache_game_data.py /path/to/SonicChaos.sms
```

`thz1/object-records.json` preserves all 53 raw nine-byte records as hexadecimal
metadata. Only types `$1B`, `$26`, and `$28` receive gameplay names because their
handlers have been decoded. Unknown types remain unnamed rather than being
assigned a guessed enemy or item.

`thz1/layout-interactions.json` records interaction-bearing layout cells and the
ring positions visible within the decoded ring blocks. Coordinates are direct
world coordinates after applying the established object-table `$0100` bias where
applicable.
