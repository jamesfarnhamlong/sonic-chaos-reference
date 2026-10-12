# EEZ ending credits audit

Evidence: decoded Europe v1.2 data, source-traced behavior, every-call controlled
routine results, and controlled original-frame observations. No external credits
list, other release, substituted glyph or POC implementation was used.

## Reproduction and outputs

ROM SHA-256: `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
Use Python 3.10+ (the repository decoder dependency requires it; local tested
Python 3.13). From the Research root:

```powershell
.venv/Scripts/python.exe tools/eez_credits.py "../source/Sonic Chaos (Europe).sms" --trace
.venv/Scripts/python.exe tools/eez_credits.py "../source/Sonic Chaos (Europe).sms" --trace --check
.venv/Scripts/python.exe -m unittest discover -s tests -p test_eez_credits.py
```

`ending-credits.json` is the deterministic decoded contract: every padded row and
control, its source, glyph descriptors, compressed asset sources/hashes, palettes,
NTSC/PAL call timings, and END actor scripts/mappings. The two
`ending-credits-trace-{full,partial}.json` files contain original-path PC events,
audio writes, raster hashes, CRAM, scroll, SAT and actor anchors. `--trace` uses the
accepted boundary-controlled boss runner; it does not rewrite ending RAM, actors,
text or timing. It is not an input-only playthrough or cycle-exact SMS emulator.

Ignored `build/eez-credits/{full,partial}/board.png` and individual PNGs show every
completed text row (including blank erasures), scene samples, END animation at
16-frame intervals and the partial TRY AGAIN card. These are local review pixels,
not distributable assets or Windows acceptance. The original ending samples also
remain under ignored `build/eez-approval/` through the reused runner.

## Complete displayed text, in order

Whitespace is preserved in the JSON; the following table strips outer padding only.
There are **6 headings + 28 entries = 34 nonblank rows**, plus **7 blank erase rows**:
**41 text rows total**. These are sequential two-line display states, not 41 static
pages. Each heading persists while the lower row is replaced. There is one later
END card, composed of four animated sprite glyphs.

| Heading | Entries in display order |
|---|---|
| CAST | SONIC; MILES POWER; ROBOTNIK |
| GAME DESIGN | M.SHIMA; RAY; 500ZO |
| ART | 7LY.BIGKING; GEN♥; NOBURIN; EAST |
| SOUND | MIX; NAGAO N.GEE |
| PROGRAM | KOKO; HIRO 777; TOSHIYAN; TOMOYAN |
| THANKS TO | HITMEN; THE HASE; KENSAN; GADAI; MIKARIN; LLG; J.S; K.DASH; HASUWO; YOKOYAMASAN; TOMOZO; AND YOU. |

Final card: **END.** Preserve `MILES POWER` as displayed; do not correct it from
outside knowledge. `GEN$` is the literal stored ASCII spelling, but `$` selects a
heart glyph: displayed `GEN♥`. `7LY.BIGKING`, zeroes in `500ZO`, punctuation and
capitalisation above are ROM-backed and visually checked on the original boards.

## ROM provenance and representation

All intervals here are half-open. JSON sources also carry exact per-range SHA-256.
Physical bank numbering is zero-based; banked addresses below use slot 2.

| Data | Bank:CPU | File range | Meaning |
|---|---|---|---|
| Credits stream | 1A:B0F0..B2ED | 6B0F0..6B2ED | Literal ASCII rows, control bytes 00/01/02/FF |
| Glyph pointers | 1A:B070..B0F0 | 6B070..6B0F0 | 64 little-endian pointers, indexed by (ASCII-20)*2 |
| Glyph descriptors | 1A:B2ED..B6F5 | 6B2ED..6B6F5 | Name and heading 2x3 name-table entries; not character bytes |
| Font compressed stream | 1A:95DC..B06F | 695DC..6B06F | 339 Mode-4 tiles, loaded at VRAM 0C00 by 7A65 |
| Initial full scene map | 1A:B6F5..B7D1 | 6B6F5..6B7D1 | 11x10 two-byte name-table entries, 30E0 writes at 3916 |
| Full scene art | 09:BD90..BEBE | 27D90..27EBE | 18 compressed tiles, VRAM 0200 |
| Partial scene art | 09:B600..BB53 | 27600..27B53 | 60 compressed tiles, VRAM 0200 |
| END art | 0E:B23A..B452 | 3B23A..3B452 | 26 compressed tiles, VRAM 0200 |
| END actor table/scripts/init | 0C:A412..A51E | 32412..3251E | Type 15 states, parameters 0..3, movement and completion |
| END sprite mappings | 0F:8DCB..8DF4 | 3CDCB..3CDF4 | Frames 1..4, exact piece descriptors in cache |
| TRY AGAIN graphics | 16:B1E4..B6B0 | 5B1E4..5B6B0 | 46 compressed tiles, VRAM 1800 |
| TRY AGAIN map | 16:B6B0..B6F0 | 5B6B0..5B6F0 | 16x4 one-byte tile IDs; attribute byte generated as zero |
| Palette records | 0E:B64D + selector*10 | 3B64D + selector*10 | 16 SMS colour values per record; exact used records in JSON |

The compressed format is the existing original `$24C2` decoder: header tile count
at +2, relative packed 2-bit command pointer at +4, data at +6. Commands mean zero,
raw tile, sparse tile, or sparse tile with XOR reconstruction. Endpoints include
both payload and command streams. No lookup remap is enabled for these loads.
Decoder output is planar SMS Mode-4 graphics, not a raster font redrawn by Python.

The renderer is fixed `$1B5E..$1C6E`; setup/ending control is `$18ED..$1B5D`.
`$1C36` subtracts ASCII 20, looks up the pointer and adds 0204 for heading glyphs.
It copies 3 rows x 2 columns through `$2349`; tile words carry pattern, H/V flip,
palette and priority. It also writes a 2x3 blank glyph two columns to the right.
The cache decodes these fields for all 29 characters used by the credits. The heart
has its own ROM glyph; it must never be replaced with a platform Unicode font.

END is **not a literal string** in this stream. It is sprite frames 1..4 of type
15. Cached SAT pieces and original compressed source reproduce E, N, D and dot,
including their slanted artwork. Parameters 0..3 initialize anchors X=112,128,144,
156; Y=0, art base=16. Use the cached scripts and mapping pieces, not text rendering.

## Credits update algorithm and timing

`$1B5E` initializes stream pointer B0F0, 11 characters, right column 31, stop
column 4, no delay/heading/shift. `$1B88` is called once per ending loop update.

- 00: clear heading mode, advance stream, set delay to 32 if D12D=0, otherwise 76.
  Each following call decrements it and returns. Thus the next character begins
  after the control call plus 32/76 delay calls.
- 01: select heading row/variant and advance, consuming one call.
- 02: shift the current line left one tile and advance, consuming one call.
- FF: mark stopped and write D3C1=FF. No implicit audio request.
- Printable byte: draw its glyph at the current right column, blank the two columns
  to its right, then decrement right. When right equals stop, reset right=31,
  increment stop by 2 and advance the character. After 11 characters reset stop=4
  and clear shift. The 11 glyphs take 27,25,...,7 calls: **187 calls per row**.

This is a repeated horizontal tile-write animation on a stationary name table,
not vertical scrolling, instantaneous page replacement or a generic text ticker.
Stable first-cell X is **40**, or **32** with control 02; successive characters are
16 px apart. Heading Y=128, lower-row Y=160; glyphs are 16x24. Padding participates
in the animation and positioning. Scroll registers remain 0,0 throughout observed
credits and END. Exact first/last call and position of all 41 rows are in JSON.
For example CAST is calls 3..189 and SONIC 223..409 (NTSC).

Both region branches were checked against original `$1B88` on **every call**, including all emitted VRAM bytes and addresses:
NTSC **8,909**, PAL **10,537**, including **7,667 glyph-write calls** each. The
full raster trace independently reaches the FF control at call 8,909. PAL here
means the original D12D delay branch, not a PAL VDP raster claim. Do not convert
these to a fixed duration in seconds without choosing the POC update-rate adapter.

Full background palette selectors 2A,2B,2C,2D,2E are scheduled for 1,500 calls each;
2F for 3,000. Each call exits early when D3C1=FF. At NTSC the final 2F interval lasts
1,409 calls. If still running, the six-selector schedule repeats: PAL reaches
10,500 then finishes 37 calls into the next 2A interval. Sprite palette is 07 during
credits, 29 for END. Background is black outside the original emerald/actor scene.
Selectors, ROM colour records and observed CRAM are retained, rather than naming
colours from a screenshot. Fades use original palette-controller flags (7=set,
5=change, 6=fade); no added white flash or scrolling background is implied.

## Ending, END and title sequence

Route selection remains the accepted `$18ED` logic; no P4 gameplay re-audit or
POC edit is included. Sonic full enters `$18FE`; Sonic partial enters `$1A41`.
Only full Sonic invokes the contributor renderer and type-15 END card. The two
Sonic routes share cleanup/fade/title code, **not contributor text or END art**.
Existing Tails ending research is retained; it is outside this Sonic dependency.

Full: clear display, load font/map via 30E0, load 09:BD90, initialize accepted
Sonic31/type22 scene, request 8D, run credits and palette schedule. D3C1=FF ends
that loop. At 19A4 fade palettes, at 19A7 request the driver fade parameters via
18E1, wait 60 frame waits. Clear presentation/player actors; load 0E:B23A,
initialize four END actors, palettes 2A/29. Run 062D + object scheduler until
D766=FF. Common return then fades palettes/audio, waits 60, and jumps to title04B4.

END lasts **638 object-loop calls** in the controlled original trace: 32 invisible,
28 initial falling/gravity, three 38-call bounce intervals, 16-call hold, two
224-call holds, then parameter0 signals completion. Parameter0 adjusts Y -8;
parameters2/3 adjust Y +8 at their script callbacks; their positions and SAT
artwork are preserved. Gravity callback A4E9 adds 0040 (8.8) per update; bounce
velocity is -0480. It is four moving sprites, not a static END overlay.

Relative to full `$18FE` entry in the NTSC harness: first credits-loop start f35;
FF f8944; END load f9007; END loop start f9009; completion f9647; title f9707.
The source wait counts and routine-call counts are canonical evidence; these frame
numbers also include approximate-harness load/IRQ timing and are not cycle-exact.

Partial: load 09:B600, accepted Sonic33/type1F scene with request9A and palettes
2A/29. Wait for Sonic deletion, wait60, fade palettes/audio, wait120, enter34D3.
TRY AGAIN clears/reloads its own graphics/map, uses background palette25 and
request98, holds240+120 frame waits, fades, waits90, then common title return.
Controlled partial offsets: request9A f6; fade f1179; TRY AGAIN entry f1299;
request98 f1306; common return wait start f1755; title f1815. No invented
contributor page is inserted on this route.

## Audio evidence

Keep accepted 8D full and 9A partial identities. Additional directly evidenced
requests: **98** at34FA for TRY AGAIN; END parameter0 script requests **A6** four
times (initial landing and three bounces) and **BA** once after the 16-call hold.
Full trace offsets: A6 f9069/9107/9145/9183, BA f9199. Command06 at67E3 and67E6
writes DE04 twice consecutively; the trace deliberately retains both writes per
script request, not two invented sound retriggers.

`$18E1..$18EC` writes driver fields DE09=12, DE0A=1, DE0B=2 for fade. It is called
before the full END transition, before partial TRY AGAIN, after TRY AGAIN and at
common title return. This is a source-traced driver fade event, not request00 or
a presumed F8 reset. No additional DE04 reset/stop request was observed within
these ending paths. PSG synthesis is not modeled by the harness; audible fade
shape remains the accepted audio-driver implementation's responsibility.

## Validation and limits

Static cache regeneration, full/partial original traces and raster/SAT hashes are
deterministic. Focused tests lock the exact stream, special heart encoding,
positions, all-call NTSC/PAL timing, glyph source bounds, END script/mapping and
route/audio observations. Original font VRAM is compared byte-for-byte with the
decoder at every completed full credits row. Existing ending-script test passes.
No ROM, compressed payload, decoded pixel dump, PNG or POC change is tracked.

No contributor, glyph mapping, ordering, row placement, credits timing or Sonic
route relationship remains unresolved. Exact cycle-level VDP load/fade timing and
PSG waveform synthesis are outside this approximate harness; source waits,
palette data and driver writes are preserved so POC need not invent replacements.
Windows presentation acceptance and Manager review remain required; this branch
must not be promoted to Research main before review.

AGENTS candidate update: complete EEZ credits extractor/cache now covers 34
nonblank rows, 41 animated rows including erasures, original font and END sprite
sources, NTSC/PAL call timings, and Sonic route/audio transitions. Cite the reviewed
commit here only after acceptance; replace the old untranscribed-credits limitation.
