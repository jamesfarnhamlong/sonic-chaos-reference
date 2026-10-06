# SEZ3 focused right-side safe-zone discrepancy

Base: canonical Research `eff4cec` on `main`. No POC edits. Evidence: verified
Europe v1.2 ROM, source-traced branches, controlled original Z80 callbacks,
and original whole-game code running in the existing approximate SMS harness.
This checks the normal bounce -> 11 -> 12 path only.

## Finding

The settled canonical right edge **can naturally request state 11**. The
cached-coordinate caveat is real, but does not prevent this branch in the
right-edge traces. There is no support here for disabling the escape/drop at
the right clamp or treating it as a universally safe hiding position.

The video observation remains unreconciled: no specific video/sequence was
provided to compare entry history, input, player posture or boss phase. These
results do not turn a visual discrepancy into a POC acceptance pass. The harness
is approximate, not an independent hardware-accurate emulator; repeat the cited
scenario in an independent emulator/video if it still conflicts visibly.

## Exact selector

Bank `$1E`, callback `$A339`, file `$7A339`; selector `$A385..$A395`, file
`$7A385..$7A395`. It runs only after state 10 moves and finds boss world Y >=622.
Contact/projection precedes movement and selection. The bounce speed and X
direction are selected first, and request 7 is written before this test:

```
b = unsigned byte boss+$1A
p = unsigned byte $D51A
if b >= 208 and p >= b: request 11
```

There is no fresh world-X comparison, cache-age guard, player-facing/input test,
right-clamp exclusion, or requirement that the boss actually touch Sonic.
The independent world-distance comparison (`bossX-playerX <96`, including
negative differences) chooses horizontal velocity only. It does not gate 11.

The exact branch region is **cached boss byte 208..255, cached player byte
bossByte..255**. With fresh, in-window caches at fixed camera2975 and a stationary
player in the canonical clamp domain2991..3222, this becomes cached boss world
X3183..3222 and player XbossX..3222. That conversion applies only to caches from
that camera/position: it is not permission to replace the original cached bytes
with current coordinates. At the observed stopped boss X3187, the selector
region is player cached world X3187..3222, inclusive. Player contact can already
have displaced Sonic by the time the selector executes.

## Cache refresh and original ordering

Renderer loop `$220E`, file `$0220E`, visits the player D500 followed by object
slots. At `$2220` it rejects zero render record +5 and invalid types. It also
skips coordinate preparation when flags4 bit7 or bit6 is set. Otherwise `$2240`
calls `$3FC8`, file `$03FC8`, which stores the **16-bit** world-minus-camera
coordinates at +1A/+1B and +1C/+1D. The selector reads only the low X byte.
Sprite composition follows the cache write; clipping/SAT capacity by itself is
not a new cache-skip condition at this gate.

The game uses camera update -> player/terrain -> ascending object scheduler ->
render preparation; a callback therefore normally sees the previous render's
caches. The trace hooks observe actual execution at `$2220`, `$3FC8`, `$3FEE`,
`$A385`, `$A391` and `$A395`; they do not manufacture cache refreshes. Original
lifecycle/sleep handling also remains active. Blank intro/drop records, escape
sleep and player hurt/blink can produce skipped renders/stale coordinates.
Controlled renderer calls verify all three skip conditions retain a synthetic
old byte199 while the eligible render refreshes it to212.

This focused rig restores the complete writable Z80 `get_state_view()` alongside
the existing VDP/mapper snapshot. The older shared register-only restore omits
core fields including `frame_tick`, WZ, interrupt mode, index prefix and interrupt
shadow. Reusing it produced later, post-hurt frame/IRQ event differences between
scenario orders (the first escape's positions/bytes/outcome agreed). The local
complete-state restore removes that history dependence without executing a NOP
or changing gameplay. Shared infrastructure/older caches are left untouched.

Across the 23 long scenarios, cached versus freshly calculated *branch outcomes*
agree at all196 observed selector calls. This does not prove eager refreshing is
generally interchangeable: player caches are observed as old as three updates;
the controlled selector sweep deliberately proves the branch uses cached bytes
even when world positions would give a different answer.

## Natural pad-only right/left traces

The game boots SEZ3 via the existing zone selector. A single synthetic approach
placement `(3060,620)` occurs at a player-update boundary. Thereafter these five
cases use real pad input only: no player repositioning, flags/state/health writes,
boss forcing, camera writes or cache writes. The original mapped creator, HUD
wait, pan, player edge clamp, movement/contact, boss scripts and renderer run.
This is whole-game execution of the arena sequence, not a recorded traversal
of the complete level from its start.

| Input | First request11 | Selector player world X | Cached player/boss X | First hurt |
|---|---:|---:|---|---:|
| Hold Right | 493 | 3222 | 247 / 212 | 598 |
| Right until near edge, then neutral | 493 | 3220 | 245 / 212 | 598 |
| Right through update400, then neutral | 493 | 3222 | 247 / 212 | 598 |
| Hold Left | none in1800 updates | — | — | 473 |
| Left until edge, then neutral | none in1800 updates | — | — | 473 |

At the right-clamp decision on update493, camera is `(2975,462)`, boss is
`(3187,623)`, Sonic is `(3222,622)`, and boss flags4=2 (awake, keepalive).
Both caches were written by `$3FC8` during update492: boss `(3187,619)` ->
screen `(212,157)`, player `(3222,622)` -> `(247,160)`. Both cache ages are one.
The selector writes7 then11; subsequent natural rows execute states11 and12.
The neutral-clamp case loses its47 decimal rings on update598 and subsequently
dies on update836. Rendering skips after hurt do not explain away the first
escape, which happened105 updates earlier with correctly refreshed X caches.

The left clamp is not a whole-fight safe spot in these traces: child `$55`
eventually causes ring loss even though the parent never selects11. Its full
mechanics are unchanged; this observation is only a limit on the word "safe".

## Exact stationary sweep geography for this entry

In addition to the five pad-only cases, 18 long cases and an exhaustive232-case
sweep perform **one** controlled X/zero-X-speed/fraction placement on the first
settled camera update, then use neutral input. They retain the real player
terrain, contact reactions and renderer thereafter; they do not pin Sonic
through damage or repeatedly repair caches. Sweep stops on first hurt.

For every integer starting X in **2991..3222**, Sonic is hurt by update598
(first-hurt range332..598). Thus the safe set is **empty for grounded neutral
waiting in this defined entry fixture**; its unsafe starting-X range is the
entire2991..3222 interval. This is not a theorem about every possible fight
history or player action.

The narrower **escape before first hurt** region in that sweep is precisely
**3216..3222**, inclusive. At2991..3215, some other contact hurts Sonic before
the first escape; that absence of11 does not establish safety. In longer traces,
starting3200 or3210 can reach11 after an earlier hurt/contact displacement.
Do not confuse this history-dependent observed interval with the selector's
exact cached-byte region above.

## Reproduction and review

```
.venv/Scripts/python.exe tools/sez54_safe_zone.py "../source/Sonic Chaos (Europe).sms" --check
.venv/Scripts/python.exe tools/sez54_safe_zone.py "../source/Sonic Chaos (Europe).sms" --sweep --check
.venv/Scripts/python.exe -m unittest tests.test_sez54_safe_zone -q
```

Committed caches: `boss-54-safe-zone.json` (selector/cache provenance, pad-only
and controlled cases, source hashes, 1536 original-callback selector cases plus
four renderer-gate cases), `boss-54-stationary-sweep.json` (all232 starting-X
results and full-trace hashes). Complete per-update rows/render hook events are
reproducibly written under ignored `build/sez54-safe-*.json`; no ROM is committed.

Validation: corrected complete-state sweep regenerated all232 positions; eight
focused tests pass, including right/left/right history-independent full-trace
replay and exact stationary boundary replays2991/3215/3216/3222. All14 existing
S5 tests also pass, including regeneration of the prior runtime/full-game caches.
Both caches carry the verified ROM SHA256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.

No changes to S5 art, HP/defeat/clear, Spring Shoes, `$55` contract or POC are
required by this check. The original full-game fixture's repeatedly parked
cycle/contact/fight writes remain disclosed and are not a right-edge acceptance
oracle; the new pad-only scenarios close that coverage gap.

AGENTS candidate: SEZ3 right-clamp state11 reachability confirmed with original
renderer caches212/247 at camera2975; no universal right hiding zone established.
Preserve cached-byte ordering; defer widescreen safe-zone policy until any
specific conflicting original-game sequence is reconciled.
