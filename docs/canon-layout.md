# Turquoise Hill Act 1 canon-layout policy

The ROM is the source of truth for placement. The Windows POC may display an
interaction only when its coordinates can be regenerated from one of these
sources:

1. the bounded THZ1 layout stream at file `$48000`;
2. the 53-record THZ1 object stream at `$705AE..$7078A`;
3. a decoded runtime handler which adjusts a stored anchor or span.

The metadata-only cache under `data/rom-cache/` records those sources without
including commercial graphics or a ROM image. Unknown object types stay absent
from the POC until their type and presentation are decoded.

## Current placement audit

| POC element | ROM source | Result |
|---|---|---|
| Terrain springs | layout blocks `$30/$31/$33/$36/$38` | all nine positions exact |
| Static spike art | layout block `$3D` | all four cells retained |
| Moving spikes | object `$1B` | all four positions exact |
| Concealed springs | object `$26` | all four positions exact |
| Platforms | object `$28` | all six positions exact |
| Rings | layout blocks `$40..$43` | positions regenerated from block-local pixels |
| Ring monitors | layout block `$47` | all four positions exact |
| Sample-engine badniks | no ROM source | removed in POC 15.1 |
| Drawn finish sign | object `$18` is not yet decoded | fabricated marker removed |

The lower-route weak spring at `(1912,864)` and moving spikes at `(1936,864)`
are adjacent in the original object stream. Their records are not fabricated.
The spring handler moves its dormant/retraction anchor down 12 pixels during
initialization; POC 15 omitted that adjustment, making the activated spring look
incorrectly high beside the spike. POC 15.1 restores the original anchor shift
and six-pixel vertical contact window.
