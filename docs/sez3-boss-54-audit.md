# SEZ S5: boss `$54`, child `$55`, arena and clear

Focused right-clamp reachability/renderer follow-up:
[`sez3-boss-54-safe-zone-audit.md`](sez3-boss-54-safe-zone-audit.md).
The pad-only right-clamp trace naturally reaches11/12 with cached212/247;
its local complete CPU restore closes the shared snapshot timing gap for this
discrepancy check. A specific conflicting original-video sequence remains
unreconciled; this is not POC Windows acceptance.

Research base: `8b7fc8aeaec6f5a57f9aa9b6a58d9f579b62514c`. This package
closes the ROM contract; Manager review and merge precede POC consumption.
No POC, root AGENTS, replacement results assets or approval boards are changed.

Evidence is decoded data, byte-verified assembly (source-region hashes),
source-traced behavior, controlled original-Z80 routine results, and guarded
whole-game observations. The approximate SMS harness is not a hardware accuracy
claim. Synthetic player writes are disclosed in each fixture; gameplay callbacks
are original. JSON coordinates and IDs are decimal unless explicitly hex strings;
velocities are signed 8.8 units (256 = one pixel per update).

Canonical deliverables:

- `data/rom-cache/sez/boss-54-runtime.json`: scripts, placement, creator/init,
  state graph, movement/contact/lifecycle contracts, exhaustive boundary vectors,
  long scheduler traces, allocator exhaustion and approved art hashes.
- `data/rom-cache/sez/boss-54-fullgame.json`: approach, HUD wait, camera takeover,
  attack cycles, 64 contact cases, eight actual HP decrements, independent children,
  five puffs, clear, results and an active MGHZ1 player.
- `data/rom-cache/sez/implementation-manifest.json`: S5 CLOSED status and POC
  integration constraints. Windows acceptance remains pending.

## Placement and initialization

SEZ3 is 4096 x 1024. Its only boss is record **5** (zero-based4), world
**(3200,622)**, bank `$1C:$90AE`, file **`$710AE`**. Stored coordinates are
(3456,878), flags0, parameter0, aux0/aux1 both0, art bases0/0. There is no sign
`$18`; `$55` has no mapped placement. The approximate `$7108A` reconnaissance
offset is superseded by the decoded record.

The mapped creator `$1C:$80EB` initializes state/request0, zero velocity and
fractions, flags3=0, flags4=`$40` (sleep), placement token5, and occupancy byte
`$D404`. The controlled creator rig uses a synthetic occupancy pointer/token25;
its cache distinguishes this from the natural token5 confirmed in whole-game.
Do not import that fixture token25 as placement data.

Shared state0 plays music `$8C`, sets flags4 bit1 keepalive, `$D44E=3` (zone+1),
`$D4A5=0`, allocates HUD `$12`, saves its slot pointer in +34/+35, raises the left
camera limit to current camera and saves right limit in +25(high)/+27(low).
Requested Spring Shoes `$12` becomes fall `$0E`, as already recovered.

Combat init `$1E:$A291` sets dynamic selector `$15`, palette14 and palette-update
bit `$D494.5`, HP +26=8, requests6, clears +34/+35/+36/+0A/+1E/vx, shifts
anchor (-64,-192) to **(3136,430)** and sets vy=+192 (+0.75). It does not set
flags3 bit7 or facing bit4. Keep the saved right-limit bytes around HP intact.

## State graph and timing

All 13 boss states are reachable through the original source graph. Whole-game
rows cover 0..4 and6..12; state5 is proved by its `$81BD` callback/bonus-spawn hook
because grounded conversion removes its type before the next row. Child state1
has no natural entry: the only spawn starts0, which requests3; state3 requests2.

| State | Script / callback | Exact behavior |
|---|---|---|
| 0 | 95B1 / 974C | Music8C; blank224 loop; shared init ->1. |
| 1 | 95BA / 9771 | Blank224 loop; strict trigger ->2. |
| 2 | 95C0 / 97C1 | Blank224 loop; wait HUD type0; set pan ->3 immediately. |
| 3 | A1F6 / A291 | Blank224 loop; combat init ->6. |
| 4 | 95CC / 032F,9A1E,9A29,9A2F | Shared five-puff/frame-restoration explosion script ->5. |
| 5 | 961E / 81BD | Blank224; floor-only clear/conversion. |
| 6 | A1FC / A2EA | Frame1/224; solid contact, move, worldY>=622 ->9. |
| 7 | A202 / A2FA | Move, right-stop, gravity+24, contact, nonnegative updatedvy increments request. |
| 8 | A23C / A312 | Frames5,7,6,8 each4; move, right-stop, contact, gravity+48, Y>=610 increments request. |
| 9 | A24E / A32A | Entry soundA6; frames15,16 each2; contact, move, Y>=610 increments request. |
| 10 | A25D / A339 | Frames15,16 each2; contact, move, Y>=622 bounce/selector. |
| 11 | A267 / A396 | Entry vx0/vy-2048; frames5,7,6,8 each4; gravity+32 before move; +36=FF; contact helper; prior sleepbit increments request. |
| 12 | A281 / A3AF | 32 blank no-op calls; then vx0/vy512; first following record copies playerX, clears36, requests8 without moving. |

Duration counts include the callback when a record is installed. Restart/jump
commands do not replay one-time velocity/sound commands unless the script jumps
back across them. Machine cache carries every operand and callback.

State7 animation is two repetitions of (2/frame3,2/frame4), then three repetitions
of spawn55 at (-16,-36), param0, followed by (3/frame3,3/frame4). Its remaining
loop is 2/frame1,8/frame3,2/frame2,8/frame4. The vertical transition may interrupt
this script; do not force all child spawns when leaving state7 early.

State10 increments +1E on a floor-threshold call. Counter>=3 resets0 and uses
vy=-1152 (-4.5), otherwise vy=-896 (-3.5). Set vx=+128 when bossX-playerX<96,
including all negative differences; otherwise -128. It requests7 unless cached
boss screenX byte>=208 AND cached player screenX byte>=boss screenX, which
requests11. Right-stop only zeros nonnegative vx when cached screenX>=212,
after movement. No mirrored left stop exists.

There are no terrain probes, floor projection, parent lookups or `$D12F`
selectors in the `$54/$55` fight callbacks. World thresholds610/622/626 govern
their vertical behavior. The player still uses real terrain. Boss/child motion
must not be changed to follow an arbitrary engine floor height.

## Contact, HP and final-hit arbitration

Boss frames1..8 have extents **20 x 80**; frames15/16 **20 x 64**. Closed normal
Sonic overlap is X[-28,+28], Y[-80,+24] or[-64,+24]; state `$0F` widens X to
[-29,+29]. `$6328` chooses minimum penetration, vertical wins ties. `$5FA0`
then projects Sonic with the existing `$D523` terrain and camera side-push guards.
Contact geometry stays on world anchors, independent of SAT presentation.

State6 calls shared `$814D`: any nonattacking contact queues damage; attacking
contact rebounds, with no HP decrement. States7..10 call `$A3D8`; state11 calls
it after +36=FF, so projection still happens but sound/rebound/HP/damage do not.
State12 blank/dropping setup runs no contact. Intro, explosions and clear do not
add a hidden contact path.

**SEZ HP is not attack-gated.** After projection, contact must exist, must not be
bottom-classified, cooldown must be zero and playerY<=bossY-16. Those conditions
decrement HP even with `$D503.1` clear. Every helper call first decrements nonzero
+34, so old1 permits a hit; a damaging call sets18. Repositioned continuous
eligible contact hits on helper calls0,18,36. Cooldown gates HP only; projection,
sound and attacker rebound still run. Initial8 reaches zero after **eight**
successful decrements. Starting0 wraps255 and does not defeat.

Attack bit `$D503.1` controls `$8105` rebound only: top vy=-4; bottom vy=+6;
right vx=+6; left vx=-6; side negates incoming vy. Request player `$1B`; preserve
movement/floor flags. `$D532==6` is not a replacement attack bit. Hurt bit6
suppresses overlap for this boss (it never sets object03.7); blink bit7 and
invincibility selector6 do not suppress HP contact. Combat bottom contact queues
`$D3B0=FF` only when floor bit1 is set, including attackers. Other nonattacking
combat contacts can damage the boss without damaging Sonic. Queued player damage
is consumed next player update by the canonical shared `$48BC` priority rules.

Sound `$B6` is requested for every contact when +36=0, including HP cooldown.
A damaging hit issues command7: the original palette effect turns entries29/30
white on command calls4..7 and restores SEZ palette14 on call8. No replacement
sound or palette system is needed.

Zero HP sets +35=FF and requests4 **immediately**, but the rest of the enclosing
callback continues. State7 with updatedvy>=0 increments4 to5; states8/9 at
Y>=610 increment4 to5; state10 atY>=622 overwrites4 with7 or11. The next contact
helper requests4 again from +35, but later instructions may overwrite again.
An eventual request5 can skip the explosion script. This is source-traced and
executed at callback boundaries; preserve the exact order instead of adding a
generic unconditional defeat transition. The ordinary full-game fixture takes
state4, waits148 updates, then converts through state5.

## Child `$55`, ownership and allocation

Table `$1E:$A455`, four scripts. State0: blank8/$A481 writes vx=-768 (-3),
vy=704 (+2.75), requests3, no movement/contact. State3: frames17,19,18,19 each3;
callback forces extents2 x4, calls damage-only `$630B`, then integrates. After
movement worldY>=626 requests2. State2: frame17/8, callback `$A49D` converts to
`$0F`, parameter0, without an attack test or score. State1 frame17/8 requests2
but is naturally unreachable. No gravity; fractional Y advances 2,3,3,3 pixels
from fraction0 rather than an invented integer2.75 update.

Closed child contact boxes: normal X[-10,+10], state0F X[-11,+11], Y[-4,+24].
Attack cannot defeat it. Hurt suppresses overlap; blinking/invulnerability and
invincibility suppress damage in the next shared player consumer rather than
preventing the queued contact. Contact is before movement, unlike many boss
states. Mapping metadata is retained in cache, but callback2x4 overrides it.

The child has token0 and no owner pointer or parent-state/HP test. Three coexist
in whole-game. Existing children keep moving after final hit/parent state change;
they expire by their own threshold/lifecycle, not by a parent cleanup sweep.

Script spawn allocator `$5EE1` scans eleven slots D700..D980. Later allocated
slots run in the same ascending scheduler pass; earlier free slots wait until
next update. Exhaustion skips all six spawn operand bytes and continues the
parent script: saturated/unsaturated parent traces match. HUD/bonus `$5E9C`
uses sixteen slots D540..D900. On HUD exhaustion `$81A6` still saves IY=D940:
state2 waits on that unrelated slot's type, passing if zero and stalling if
nonzero until it clears. This narrow canonical failure path is tested.

## Arena, lifecycle and viewport rules

Steady mapped creation occurs at screen X288..351 or-96..-33, with the generic
initial-fill exception. Trigger is strict abs(dx)<160 AND abs(dy)<304
(`PLAYER_DIST`), independent of facing/view width. Initialization sets active
flag3 before trigger. Shared callbacks raise left limit to the current camera;
trigger lowers right limit to current camera. State2 waits only for HUD slot
type0, then sets bottom limit462 and pan target **(2976,462)**. Both axes pan
1 pixel/update simultaneously. Exclusive right limit settles X at2975; Y462.
State3 starts immediately, without waiting for camera arrival.

Initial camera limits are [left0,right3840,top8,bottom784]. The generic player
edge clamp applies; there is no SEZ-specific world arena clamp in these callbacks.
Use the canonical engine edge-clamp model, including its documented SMS wrap
artifact, and an explicit full-width POC edge adapter.

Mapped boss keepalive prevents generic outer-window deletion. Visibility still
updates sleep; state11 uses the prior update's sleep bit to leave its upward
escape. Other boss callbacks do not pause on sleep. Child55 has no keepalive:
generic awake[-32,288), outer[-96,352) on both axes at the 256px baseline;
outside outer window marksFF and later scheduler cleanup clears its slot. Its
callback itself ignores sleep. It can therefore be deleted above the camera
before reaching worldY626. Boss conversion detaches token5, retaining occupancy;
no natural recreation of the defeated boss follows.

Classification for a future POC adapter:

- `WORLD`: placement3200,622, combat transform, Y610/622/626, saved camera bounds.
- `PLAYER_DIST`: strict160/304 trigger; never silently widen.
- `LOCKED_CAMERA`: target2976,462 and settled2975,462. Reframing is an explicit
  POC decision, not permission to move the canonical boss anchor.
- `EDGE`: lifecycle bands, cached screen208 = RIGHT-48, screen212 = RIGHT-44,
  player edge clamp and solid side guards32/224. The original selectors compare
  cached unsigned screen bytes; do not silently replace with fresh coordinates.
- `EDGE(RIGHT,+33)`: state20 completion threshold289; use the accepted clear adapter.

Dynamic55 does not automatically receive the mapped post-wake retention adapter.
No empirical 640px boss composition is prescribed. Lifecycle height256 is the
canonical table domain, not a claim that the visible SMS display has256 rows.
Screen caches +1A/+1C are written by renderer `$3FC8` (caller `$2240`), not by
the lifecycle helper. Callbacks read the latest rendered coordinates, which can
stay stale when rendering is skipped. Sleep is from the preceding lifecycle call.
The whole-game fixtures retain the original renderer/camera/player/object order.

## Defeat, support, clear and progression

Shared state4 `$95CC` attempts five `$34/4` puffs at(-8,0),(8,0),(0,-16),
(-8,-24),(-8,-24), with original frame save/restore calls and 24 loop repeats.
The guarded normal fixture measures148 updates in state4, then state5 runs.
Shared support contracts are in `docs/thz3-boss-support-audit.md` and
`docs/player-attack-badnik-audit.md`; SEZ uses the same scripts/parameters.

State5 `$81BD` needs **floor bit1 only**, with no SEZ world-X threshold. It sets
left limit=current camera, releases the pan, restores saved right3840, requests
player state20, allocates `$0A/0` bonus controller and converts boss to `$0F`.
Both boss/expired child use `$5F54` token detachment/parameter0 conversion; the
type>=50 score gate awards no ordinary badnik score. `$0A` uses the existing
bonus and parameterFF sparkle chain. HUD remains absent until the next level.

The timer stays running through fight/defeat and state20. There is no sign chain.
The original state20 right-edge handoff reaches results and the progression
target **zone3, act0 = MGHZ1**, confirmed by new-act loader, active walking player
and original start(78,192). Results replacement graphics/audio remain excluded.

All runtime-used boss/child frames0..8,15..19 match the existing approved SEZ
unmirrored package. No missing composition or new approval is needed.

## Verification and unresolveds

Both generators reject any ROM other than Europe v1.2,524288 bytes, SHA256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
Run generators with `--check`, focused `test_sez54*.py`, relevant SEZ/shared boss
regressions, `tests/verify_cache.py`, and `git diff --check`.

The runtime generator executes **448,818 assertions**, including exhaustive
frame geometry, attack/hurt/blink/power matrices, threshold/selector/final-hit
cases, lifecycle bands, allocator exhaustion and approved image hashes. Eight
600-update original scheduler scenarios provide event vectors and full-trace
hashes. Whole-game includes a repeated1100-update cycle with identical guarded
restore output,64 controlled contact cases, and the complete eight-hit clear.
The whole-game generator adds134 assertions: **448,952 S5 assertions total**.
The focused/regression batch passes **272 tests**, with no skips: SEZ126,
THZ shared boss/support59, MGHZ boss37, GPZ boss18, shared attack/badnik32.
The full `tests/verify_cache.py` rebuild and `git diff --check` both pass.

**Unresolved S5 runtime dependencies: none.** Human-facing boss names are not
claimed; POC implementation and Windows gameplay acceptance remain downstream.
Existing deferred results presentation does not block the original clear chain.

AGENTS candidates (Manager consolidation only): SEZ54 HP uses post-projection
height/cooldown rather than attack posture; eight hits reach zero; record the
final-hit arbitration quirk, independent damage-only child55 and camera2975,462;
SEZ boss clear is floor-only and progresses MGHZ1.
