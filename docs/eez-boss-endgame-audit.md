# Zone5 final-act chain and completion

Canonical source/controlled results are in `data/rom-cache/eez/`:
`boss-endgame-recon.json`, five `boss-game-*` traces, `allocation-checks.json`
and `ending-scripts.json`. Europe v1.2 SHA is verified on every build. The
routine package executes 507,036 independent boundary comparisons. Original
game traces supply player/camera boundary fixtures; they never write boss HP,
state, movement or children. These are not input-only fights or Windows approval.

The two mapped records are `$5E` at WORLD(2080,494) and `$60` at WORLD(2464,494).
They are consecutive encounters, followed by `$61/$62`; ordinary sign/player20
completion must not be substituted for their handoffs. All state scripts,
record durations, commands, child parameters and source region hashes are cached.

Shared trigger rows5/6 use strict PLAYER_DIST X<96,Y<304. `$60` additionally
waits on `$D4A7`, signalled by the first encounter. Nominal locked camera targets
are (1952,334)/(2336,334), from placement offsets(-128,-160); shared exclusive
pan reaches (1951,333)/(2335,333). `$8199->$59E3` raises camera-left limit to
max(oldLeft,cameraX), saving the prior right limit in actor25/27. Trigger
`$59F3` lowers the right limit to min(oldRight,cameraX); pan sets bottom334.
Handoffs release pan and restore saved right limits. Generic player edge clamps
remain viewport-relative. Do not invent a THZ-style fixed world arena here.

`$5E` has14 states and HP16. Setup selects dynamic art24/palette17, shifts its
own anchor +128, sets VX−0.75 and starts the224-count entry. Its patrol callbacks
use cached screen-X48/192; WORLD motion, floor494 and player-distance decisions
are separate rules. Decision `$B257` skips frames3/4, pauses8 calls, and chooses
patrol/child attack or grounded-near jump; 33,264 decision combinations are checked.
Jump gravity is +32/256 while rising and +56/256 otherwise, with16-call floor
delay. Scripts8/11 share the jump path; source graphs retain aliases.

Contact `$B2EC` uses actual frame geometry: frames1..4 extents16×64, frame5
16×48. Shared projection is retained. Attacking+grounded Sonic skips contact
unless frame5. A nonzero cooldown decrements and skips the helper's damage
branch. Bottom contact requests hurt; non-bottom attack soundsB6 and rebounds,
but **only top contact reduces HP**. Top damage installs cooldown16 and flashes
palette13/14 white; zero HP requests defeat4. Side feedback is not an HP hit.
48,492 complete geometry cases include both Sonic horizontal extents8/9.

Defeat4 uses shared explosions, then5 rises−1 through20 frame20/0 loops,
runs right+2, waits asleep and32-count borrow, releases the camera, signals
D4A7FF and converts toFE with parameter80. There is no player20/act-clear yet.
`$5F` children have seven states: parameter1 bounces with three floor contacts;
0 selects projectile/tether by update parity; FF and FE have separate velocity/
parent-link paths. Every parameter/parity initializer is checked. WORLD Y>494,
sleep deletion, cached screen7/249 reflection and parent-relative wobble remain
distinct source rules; no widened player-distance substitute is introduced.

`$60` has13 states. Its command4 creates `$63` and stores its slot pointer.
After D4A7 and the shared trigger, it waits until that slot is no longer type63,
loads selector25, places Y414, and starts a32-count flight delay. Route selection
uses cached player screen-X<85, >=165, or alternating middle routes. All256
screen-X values,256 angles and both middle counters are checked (131,072).
Odd/even flights start at EDGE(LEFT,0)/EDGE(RIGHT,0), VX±3.5. Routes0/2 start
WORLD Y414,1/3 Y480. Route2 turns at cameraX+32/+224 and cameraY, then uses
VY+6,VX±1.625. Movement precedes acceleration. Full per-route arithmetic is
retained in the machine contract; screen constants must be explicit adapters.

Attacking **top** contact sets its hit latch/palette feedback. Odd angle requests
escape10 immediately; even angle disables contact and waits for asleep, then
delay80 before escape. **Every other overlap invokes direct death `$4984`,
state1F/sound96**, bypassing ordinary ring loss. There is no ordinary HP countdown.
Both successful angle branches execute through the original whole chain.
Escape10/11 emits shared explosions, passes offscreen, and state12 spawns61,
releases the camera and convertsFE. Failed allocation has no invented fallback.

`$63` uses selector33, keepalive, Y414 and the original32/8-call animation.
It oscillates by±2/256, testing the new velocity's sign and **low byte**; the
natural endpoints are+32/256 and−34/256. All131,072 phase/velocity combinations
are checked. It then moves left−2.5 until asleep and deletes, releasing60 entry.

`$61` stops the timer, loads selector26/palette17 and initializes WORLD(2752,494).
Strict player X-distance<112 begins its chase. Forward-only X follows
cameraX+176..239 in a128-call triangle, capped WORLD3504; player WORLD X>=3456
requests its next sequence. All256 counter bytes and boundary combinations
are swept. It raises/sets D3E7; `$62`, at WORLD(3536,430), bobs, rises−1 when
signalled, then clears D3E7 and deletes when asleep.61 waits for this release,
emits `$0A` parameter1, settles and offers contact. Sonic with flags exactly1F
must collect the final bit5; other cases can clear early in state5. Final7
sets flags|20hex, D293=50hex and deletes. All character-byte/flag combinations
in the relevant early-clear gate and terminal selector are checked.

`D293=50hex` takes the final zone-clear path. Zone>=5 skips ordinary `$32F9`
results; `$15CE` sets act0, zone6 and flagbit7. `$1333->$1365->$18ED` selects
the ending; it returns through `$04B4` to title. Zone6 is not another playable act.
Sonic with all six flag bits takes18FE; partial flags take1A41; other character
takes1ACD (initializes Tails type2/state31). All three controlled terminal
branches reach title without further fixture writes after final clear.

The full Sonic scene loads bank9:BD90, palettes2A..2F, sound8D, Sonic31/type22,
then bank14:B23A and type15 parameters0..3. Original raster samples visibly
show credits labels and final `END.`; the type15/D766 wait is source-traced.
Partial Sonic uses bank9:B600, Sonic33/type1F, sound9A, then34D3's timed
`TRY AGAIN` scene (visible in the original raster samples).
Tails uses bank14:ABDA, state31/type16, then its own tail. CreditsD3C1FF moves
Tails31->32; player field26=1 releases16; its absolute script write D526FF
releases Tails32->33, then gravity and Y-high-byte2 delete it. `ending-scripts.json`
includes complete Sonic/Tails ending scripts: the former long script exceeds
the reconnaissance decoder's80-op cap and is decoded with512. Command0A's
absolute-byte write is byte-verified at6841 and checked with768 routine cases.
No invented
contributor names, credits text, replacement assets or added animation.

New composition and original scene boards are pending James review. The SMS
harness is approximate; raster samples support registration and control-flow
findings, not a claim of cycle-exact VDP behavior. A widescreen POC must design
separate EDGE/camera adapters and preserve WORLD anchors and branch rules.
