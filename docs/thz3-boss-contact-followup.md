# THZ3 boss contact and hit-feedback follow-up

Research only; POC untouched; checkpoint on `research/thz3-contact-feedback`,
pending review before integration into main. Based on clean
Research main `ce2ef9b` (contains footwear checkpoint `150977e`). Target local
ROM SHA-256: `eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.

This extends [the boss/support audit](thz3-boss-support-audit.md), not the boss
state machine. Reproducer: `tools/thz3_boss_contact_followup.py`; cache:
`data/rom-cache/thz3/boss-contact-followup.json`; regression tests:
`tests/test_thz3_boss_contact_followup.py`. Original Z80 routines run in the
existing `BossLab`/`Oracle`; whole-game fixtures use the existing `Thz3`/`Aligned`
harness with all external writes at `$1336`. No ROM or graphic dump is emitted.

Evidence: **source-traced behavior**, **controlled routine result**, and
**emulated original frame**. Code-region hashes and bank/CPU/file addresses are
in `evidence`. The approximate SMS harness does not synthesize PSG audio;
sound conclusions concern exact request bytes, not listening judgments.

## 1. Successful damaging contacts

In boss fighting states **6, 9, 12, 15**, `$1E` must be zero; `$99AE`
(`1E:$99AE`, file `0x799AE`) calls `$034D/$5FA0` for overlap and solid projection.
Top classification is handled first. Any other contact requires **player
`$D503` bit 1** to damage the boss; power-up `$D532 == 6` is not an alternative.

For ordinary Sonic define `dx = playerX - bossX`, `dy = playerY - bossY` at the
contact call. Overlap is inclusive `abs(dx) <= 28`, `-48 <= dy <= 24`.
Minimum penetration chooses the contact axis; ties choose the vertical axis.
Thus a negative dy alone does **not** mean top contact.

The exact `$8105` response (`1E:$8105`, file `0x78105`), velocities in pixels/update:

| Classification | Contact bit | X speed afterward | Y speed afterward |
|---|---:|---|---|
| Sonic left of boss | 3 (`$08`) | **-6.0** | **negative of incoming Y speed** |
| Sonic right of boss | 2 (`$04`) | **+6.0** | **negative of incoming Y speed** |
| Sonic below boss | 1 (`$02`) | incoming X speed | **+6.0** |

Y negation is exact signed 16-bit 8.8 two's-complement negation, not a fixed
upward launch. Side contact while descending at +7.0 yields **-7.0**;
while rising at -8.0 it yields **+8.0**; at zero it stays zero. A high rebound
from a descending side hit is canonical. Below hits drive Sonic **downward**.
Facing, incoming X speed, boss direction and patrol phase do not select another
response. The controlled sweeps cover both X directions, rising/zero/falling
Y speed, flags/floor variations, all four vulnerable states and both power cases.

`$D502 := $1B`; current `$D501` is unchanged until the next player animation
update. `$8105` does **not** call the general `$47FB` ramp setter: it writes only
the two velocities and requested state. It preserves `$D503`, including attack,
airborne, hurt and invulnerability bits, and `$D522` floor flags. Do not add
automatic airborne/floor clearing merely because the requested state is `$1B`.
Solid projection precedes these writes and uses canonical anchors; it changes
position, not speed. Existing `$D523` collision/edge guards can suppress a
projection independently of the attack outcome.

The hit queues palette command 7 and sound **`$B6`**, decrements health once,
then requests S+2 with reaction timer 20, or state 4 when health reaches zero.
The aligned whole-game contact hooks capture actual incoming/outgoing speeds
before later fixture parking writes can overwrite them.

## 2. Exact top contact

For normal Sonic, top iff:

```
-48 <= dy <= -1
abs(dx) <= 28
48 + dy <= 28 - abs(dx)       # ties are top
```

Equivalently `dy <= -20 - abs(dx)`. At `dy=-34`, `abs(dx)=14` is top;
15 is side. At `dx=0`, `dy=-20` is top; -19 is side. At `dy=-48`, even
`abs(dx)=28` is top. The one-pixel exterior rim and every internal tie/boundary
are swept across all vulnerable states (17,700 cases).

Top handling precedes the attack check: **attacking and non-attacking Sonic both
bounce**. It clears `$D448`, then calls `$035F/$5F17 -> $480C` with `$FC00`.
If incoming signed Y speed is nonnegative:

- Y speed becomes **-4.0**, X speed unchanged; `$D502 := $0B`;
- `$D503` bit 0 set (airborne), bit 1 cleared (attack); other bits preserved;
- `$D522` bit 1 cleared (floor); sound **`$A6`**;
- player object-contact byte `$D521` cleared by `$5F17`;
- boss health unchanged; no command-7 flash; boss requests S+1, timer 20.

If already rising, `$480C` returns without velocity/state/attack/floor/sound
changes. `$D448` and `$D521` are still cleared, solid projection has already
occurred, and the boss still enters S+1 for 20 updates. The rising top-contact
case therefore consumes a boss reaction without refreshing Sonic's ascent.

No `$1E` cooldown is written for top contact. The reaction state suppresses
all contact for 20 updates; first available contact is update **21** afterward.
The boss moves during the top reaction. Non-attacking Sonic can bounce again
after coming down: attack posture being cleared does not prevent repetition.

Whole-game Y/state/flags/gravity run freely in two fixtures. An initially aligned
stationary Sonic gets one bounce as the boss moves away. With **only X** kept
aligned synthetically, bounces occur at relative updates **1, 69, 137, 205**;
the attack bit stays clear. Highest anchor is world Y **106**, signed screen Y
**28** in this fixture. Repetition can keep Sonic high above the boss, but this
does not prove an unassisted indefinite tactic or offscreen accumulation.
There is no increasing rebound impulse: each refreshed top bounce is -4.0.
An already higher incoming trajectory is not reset while rising.

## 3. Hurt, blinking invulnerability and invincibility power

Boss `+$03` bit 7 (set during state 3) bypasses the shared `$6328` player's
hurt-bit-6 rejection. Neither `$99AE` nor `$8105` gates on player bit 6, bit 7
or power `$D532`. These cases must be separated from the later player damage
consumer `$48BC`.

| Player condition | Fighting side/below contact with attack clear | Attack bit set |
|---|---|---|
| Ordinary vulnerable Sonic | Solid projection; queue `$D3B0=$FF`; boss `$1E=2`; next `$48BC` hurts/deaths according to rings/state | Boss damaged; directional rebound; request `$1B` |
| Hurt bit 6 only | Same projection/request/cooldown; `$48BC` clears `$D520` and returns; no fresh movement/state response | Boss damaged and rebounds despite hurt bit |
| Blinking bit 7, with/without bit 6 | Same projection/request/cooldown; `$48BC` processes i-frame timer/blink, suppressing new damage | Boss damaged and rebounds despite i-frames |
| `$D532==6`, attack clear | Same projection/request/cooldown; power branch clears `$D3B0/$D520`; no hurt/rebound from damage consumer | Boss damaged **because bit 1 is set**, not because power is 6 |

Top contact in **all** these conditions takes section 2, including the -4.0
spring response and attack clearing. This provides a canonical explanation for
the Windows impression of "springing during i-frames". An attack bit retained
from hurt can also produce a genuine side-hit rebound and boss damage.
Non-attacking side contact alone is a projection, not an upward velocity setter.

Damage suppression does not cancel the boss's `$1E=2` write. After two suppressed
helper calls another non-attacking overlap writes 2 again. The raw bit-6-only
consumer does not clear `$D3B0`; bit-7 timer processing leaves it pending while
the timer runs, then clears it when invulnerability ends (`$4A25`). This is
distinct from power-6's immediate clear. Do not model all cases as one early
"ignore boss overlap" return.

## 4. Contact cooldown and entry exception

In fighting states, `+$1E` is written **only** for a non-top contact with attack
bit clear, even if the later player handler suppresses damage. Starting at 2:

| Update relative to contact | Helper action |
|---:|---|
| 0 | project; queue damage; write 2 |
| 1 | decrement 2 to 1; return before overlap/projection |
| 2 | decrement 1 to 0; return before overlap/projection |
| 3 | overlap active; may project, bounce, damage boss or request damage again |

Suppression covers the **whole** helper. It does not clear/recompute the old
contact nibble during the early return; stale bits are not a new contact.
Decrement happens only when `$99AE` runs (states 6/9/12/15); reaction states do
not run it and retain any existing remainder. Hits/top contacts write no 2.

For a hit/top at update 0, reaction callbacks run on updates 1..20, request the
saved fighting state on 20, then promote and run contact on **21**. The older
audit's **22** interval is the schedule of its whole-game attack driver, which
waited to observe the fighting *current* state before injecting another hit;
it is **not a mandatory extra canonical delay**. The new continuous-overlap
fixtures verify the first recontact on 21 for all four states and both reactions.

**State 18 is an exception:** it moves first and uses `$814D`, not `$99AE`.
That helper has **no `$1E` read, decrement or write**. It projects every eligible
overlap; a non-attacker queues damage (even from above); an attacker uses `$8105`
(including -4.0 for top, preserving attack/floor flags), requests `$1B`, but never
damages the boss or queues hit flash/sound. The inherited `boss_model(18,...)`
cooldown assumption must not be treated as evidence. New scope fixtures verify
contact in state 18 even with synthetic `$1E=2`.

## 5. Exact hit presentation and hit progression

Every successful hit, including hit 8, executes the same sound **`$B6`** and
queue command **7**. It does not spawn an effect or toggle visibility at the
ordinary hit call. The short flash changes only sprite-palette entries **13/14**,
absolute CRAM indices **29/30**, from **`$35/$20`** to **`$3F/$3F`** (white).
It is a global sprite-palette change, not whole-sprite white tint or alpha flicker.
Mapping pixels that use other palette indices retain their normal colors.

Trace:

1. `$99E0 -> $0374/$1CD3`: command 7 queued in the first free one of four
   8-byte records at `$D452/$D45A/$D462/$D46A`. Full queue drops the request.
2. `1D:$8000` dispatches queued commands once/update when `$D492==0`; command 7
   dispatches to `1D:$83C6` (file `0x743C6`). Fade activity can pause dispatch.
3. It increments record `+3` before testing 4. First three calls leave palette
   unchanged; call 4 copies two bytes from `1D:$9979` (file `0x75979`) to
   `$D48F/$D490`, sets `$D496=$FF`, and advances record step `+2`.
4. Calls 4..7 have `$3F/$3F`; call 8 restores `$35/$20` from the next table pair
   and clears command/counter/step via `$03FE -> $1D06`.
5. `$1CBD` sees `$D496` and uploads all 32 shadow palette bytes `$D472..$D491`
   to CRAM, then clears the pending byte. In the aligned fixture white CRAM is
   observed on boundaries **hit+5..hit+8**, restored at **hit+9**. Distinguish
   palette-command update timing from the later IRQ transfer/display boundary.

The previously unresolved initial palette consumer is now source traced:
`0E:$B45A` checks two descriptors at `$D492/$D494`; bit 5 reaches `$B49E`, copies
16 bytes selected by `$B63E` (`$B64D + index*16`) into the palette shadow, clears
the descriptor and marks `$D496`. Index `$0C` selects file **`0x3B70D`**;
sprite shadow is `$D482..$D491`, making `$D48F/$D490` entries 13/14.

| Hit | Health | Boss response | Mapping/visual response |
|---|---|---|---|
| 1..7 | 8->7 through 2->1 | S+2, no movement for 20 updates; return saved phase state, X speed 0, patrol phase 1 | S6->8 / S12->14: frames 1/2 every 4 updates, mirrored only for 14; S9->11: frame 5, record 8; S15->17: frame 5, record 16; same command-7 flash and `$B6` |
| 8 | 1->0 | request state 4 directly; no ordinary hit reaction; no further contact | same immediate flash/sound/rebound, then existing defeat script: five `$34` children; first four updates saved-frame/blank alternate one update each; thereafter 24 loops of 4 visible +2 blank updates; existing completion chain |

Thus hits 1..7 share hit effects but **reaction animation varies by phase**.
Hit 8 adds defeat flicker/explosions, not a different immediate bounce/flash.
96 controlled progression fixtures cover 8 health values x 4 phases x 3 damaging
quadrants. No escalating launch strength or hit-count-specific flash was found.

## 6. Canonical entry presentation oracle

These are start-of-update boundary samples relative to creation from the
specified fixture: camera `(1500,80)`, player `(1604,238)`, Right for 75 harness
frames, then parked away from entry contact. Absolute durations depend on the
player trigger, camera and child timing; preserve the relationships, not a new
universal 171-update entry constant. Full update/timer/frame/palette records are
in cache `aligned.rows`.

| Update | Current/requested state | Timer | Mapping | Presentation/event |
|---:|---|---:|---:|---|
| 0 | 0/0 | 0 | 0 | Newly allocated blank slot; initial flags `$40`; no boss sprites |
| 1 | 0/1 | 224 | 0 | Initializer ran; `$12` child allocated; music `$8C`; blank |
| 2 | 1/1 | 224 | 0 | Await trigger; HUD child slides away |
| 18 | 2/2 | 224 | 0 | Trigger promoted; blank; waiting for `$12` |
| 100 | 2/2 | 142 | 0 | Child type `$FF` (cleanup not yet finished) |
| 101 | 2/3 | 141 | 0 | Child now zero; pan requested; still blank |
| 102 | 3/18 | 224 | 0 | Camera begins 1px pan on both axes; art selector `$13`, palette `$0C`, health 8, boss vx -0.5 |
| 103 | 18/18 | 16 | 1 | Entry first mapping selected; screen anchor X272; art transfer still pending |
| 104 | 18/18 | 15 | 1 | First matching onscreen SAT pieces from preceding update (2 pieces); ordinary palette still in CRAM |
| 106 | 18/18 | 13 | 1 | CRAM sprite palette `$0C` now installed |
| 119 | 18/18 | 16 | 2 | Next animation record; camera X has reached1679 |
| 134 | 18/18 | 1 | 2 | Art request cleared after original multi-update upload |
| 135 | 18/18 | 16 | 1 | Normal 16-update mapping alternation continues |
| 149 | 18/18 | 2 | 1 | Camera Y first reaches78 |
| 151 | 18/18 | 16 | 2 | Mapping alternate |
| 167 | 18/18 | 16 | 1 | Mapping alternate; screen X224 |
| 170 | 18/6 | 13 | 1 | Entry exit requested after screen-X test |
| 171 | 6/6 | 16 | 1 | First fighting script record reloads timer/frame; screen X222; all 13 preceding-update SAT pieces found |

Frame 0 is empty, not a drive pose. State 18 alternates frames1/2 at16 updates;
switching to state6 **restarts** its own script at frame1/timer16. Camera lock
does not itself request a special boss frame, flash or visibility toggle.
Art upload, palette installation, mapping selection and SAT transfer are
different events: SAT at a boundary contains the preceding update's rendered
pose/coordinates, not necessarily the slot's current mapping/coordinates.
"First SAT pieces" does not assert that every newly transferred art tile was
already correct at that instant; the original art request is still pending.

## 7. POC recommendations, validation and unresolved items

POC-san should compare its trace against the equations/timelines above:

- Preserve side Y inversion, below +6.0, delayed current-state promotion, and
  successful-hit flag preservation; **do not weaken the rebound empirically**.
- Classify top by minimum penetration (vertical wins ties), before attack and
  immunity checks; preserve the rising guard and attack clearing of `$480C`.
- Keep hurt/i-frames and power6 distinct. Suppress *player damage* in the player
  handler; do not suppress boss projection, top bounce or attack-based damage.
- Implement palette entries13/14 white for4 command updates, with the recovered
  command delay, `$B6` request and phase-specific reaction animation. No ordinary
  hit alpha flicker, blanket tint, substitute explosion or invented asset.
- Separate harmful-contact `$1E=2` from reaction20; first active reaction update
  is21. State18's helper has no `$1E` gate and cannot damage the boss.
- Preserve blank states0..3, first entry frame1, sixteen-update entry records,
  frame1/timer16 restart at state6 and separate asset/palette/SAT readiness.
- **Arena clamp remains the accepted WORLD-space rectangle. No width change.**

Validation is focused, not the full suite: 8,000 response cases and 17,700
geometry cases with zero model mismatches; 320 separated immunity/contact
fixtures with subsequent real `$48BC` calls;24 cooldown sequences;13 decrement
scope fixtures;96 hit/phase progression traces;8 repeated-contact timelines;
72 facing/direction/phase independence cases;10 palette calls;3 update-aligned
whole-game runs (entry/hit, free top bounce, X-tracked top bounce). Focused
16-test module includes byte-identical replay of the whole new cache. All16
pass, with no skips; the3 existing `TestContact` checks also pass (19 total).
`git diff --check` passes. Verified local runtime is Python3.12.14. Checkpoint
branch is `research/thz3-contact-feedback`.

Unresolved/limits: no GameMaker or Windows diagnosis; no PSG playback/acoustic
identification of `$A6/$B6`; no human-play proof of indefinite or offscreen top
bounce tactics; approximate VDP timing is not cycle-exact hardware evidence.
First-visible SAT detection is original-code/harness evidence, not a guarantee
that the original partial art upload has finished. No arena-width re-audit.

AGENTS.md candidate updates (root file intentionally unchanged):

- `$50` side hits set vx±6 and **negate incoming vy**; below sets vy+6;
  requested `$1B` preserves player flags/floor.
- Top is minimum-depth/tie-winning contact; non-rising player bounces at-4,
  requests `$0B`, clears attack/floor; non-attacking and hurt/i-frame players
  can bounce. Bit1 still permits boss damage during hurt/i-frames; power6 alone
  does not attack.
- `$1E=2` follows only fighting non-top/non-attacking contacts and skips two
  whole helper calls. Reaction20 permits recontact on update21; state18 uses a
  separate helper with no `$1E` gate and no boss damage.
- Hit command7 flashes global sprite palette entries13/14 white for4 updates
  after a4-call command delay; `$B6` on every hit; final hit adds defeat flicker.
- Link this follow-up as the precise contact/presentation supplement; keep
  WORLD arena clamp unchanged and entry mapping/asset/palette clocks separate.

Reproduction:

```powershell
.venv\Scripts\python.exe tools\thz3_boss_contact_followup.py '..\source\Sonic Chaos (Europe).sms' --check
.venv\Scripts\python.exe -m unittest discover -s tests -p test_thz3_boss_contact_followup.py -v
```
