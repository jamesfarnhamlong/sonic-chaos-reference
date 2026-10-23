# M2-R2 — Sonic versus Tails interaction matrix

23 October 2026. Research only, SMS Europe v1.2, SHA-256
`eabc8db59746714262d2f91a921d054823484349099a9fcd04fd6e84a1fee607`.
Parent `d6f2fafcda7903c0fc7082b2a9cbf4fed6e0bf98`; branch
`research/m2r2-tails-interaction-audit`. Accepted POC `7476affc` remains read-only;
no GameMaker, root coordination, public pixels/audio or baseline promotion.

## Finding and evidence boundary

**A Rocket monitor placement becomes a Ring monitor for Tails, before artwork
selection or destruction. Tails receives +10 rings, not an empty pickup.** The
separate reward gate that refuses a forced Rocket reward for Tails is a second
defence, not the normal monitor lifecycle. Life monitors retain their reward but
select the current character's portrait. Spring Shoes work for both characters.

`data/m2r2/character-interaction-matrix.json` is the Designer-facing contract.
`data/m2r2/evidence.json` contains decoded placements, hashed source listings,
original-routine controls and original-game scheduler observations. Numeric
character IDs are **1 Sonic / 2 Tails**, matching gameplay `D500` and `D2C8`;
the character-choice cursor uses a different, zero-based representation.

Each matrix row is classified **ROM gameplay proven**, **controlled-only**,
**static source**, or **unresolved**. Gameplay here means unmodified original
game code in the repository's approximate SMS harness, not physical hardware or
cycle-exact VDP validation. Arrival-assisted cases place only player/camera at
the start-loader return; objects, state requests, code, banks and VDP remain
under original ownership. These establish actual mapped pickup reachability
from the named arrival, not an input-only journey from the stage entrance.
The failed 500-frame entrance attempts are retained separately: neither reached
the monitor; they are not negative evidence against pickup eligibility.

Reproduce:

```text
python tools/m2r2_interactions.py PRIVATE_ROM --gameplay
python tools/m2r2_interactions.py PRIVATE_ROM --check
python -m unittest discover -s tests -p test_m2r2_interactions.py -v
```

The second command re-executes source/controlled checks and compares the stored
gameplay records without replaying them; `--gameplay --check` replays everything.
Only metadata is committed. Routine fixtures stub the interrupt wait `$062D`
where needed, as in earlier footwear work; no such stub exists in gameplay runs.

## 1. All placed monitor variants

Ordinary 18-act census: **69 monitors**: parameter1 ×16, 2 ×12, 3 ×9,
4 ×11, 6 ×21. Five Special Stage lists add **18**: parameter4 ×6, 5 ×5,
6 ×7. No placed parameter0, 7, 8 or 9 appears in these 23 lists. Parameter5 is
a Special Stage clock, not Spring Shoes. Unplaced reward-table bits do not
establish another reachable monitor variant.

| Placement `$10` parameter | Sonic selection / displayed icon | Tails selection / displayed icon | Activation → reward → continuing effects | Classification |
|---|---|---|---|---|
| `$01` Ring | `$01`, Ring | `$01`, identical Ring art | Successful break queues bit0; `$4AC0` adds BCD `$10` rings; wrap pays a life then calls character-gated Special Stage entry | controlled-only; wrap gate separately controlled |
| `$02` life | `$02`, Sonic portrait | `$02`, Tails portrait | bit1 → `$3104`: one life, cap BCD99, sound `$A9`; no equipment state/timer | controlled-only |
| `$03` speed-up | `$03`, speed shoe | `$03`, same art | bit2 → selector3, timer900; `$4A74` forces maximum `$0600`; current player state unchanged | controlled-only |
| `$04` Rocket | stays `$04`, Rocket shoe | **converted to `$01`, Ring** | Sonic bit3 → selector4, timer300, `$4775` requests `$11`, clears attack and initializes motion. Tails bit0 → **+10 rings**, no Rocket state/timer | **ROM gameplay proven**, THZ1 arrival-assisted both characters |
| `$05` clock | `$05`, clock | Forced Tails uses same selector/art; no normal Tails SS entry | bit4 → `D3C4=11`, sound `$F8`; SS clock pause owner is separate from `D44C` | controlled-only reward; static source for forced Tails artwork/reachability exclusion |
| `$06` invincibility | `$06`, stars | `$06`, identical stars | bit5 → attack/blink flags1/7, sound `$84`, selector6, timer600, allocate type5 aura unless already selected | controlled-only |

### Complete monitor chain and lifetime

1. **Placement:** bank28 list record holds original type `$10`, parameter at
   record+6, biased X/Y, flags and art-base bytes. Creator `$80EB` copies parameter
   into slot+$3F. All eleven ordinary Rocket records remain `$04` in ROM; there
   is no separate Tails object list.
2. **Conversion:** bank12 `$A149..$A160` enables contact, requests state1,
   reads `D500`; for any type other than1, only parameter4 is rewritten to1.
   Parameters1/2/3/5/6 are unchanged. This happens once per newly created slot,
   before state1's graphics latch; it is not a reward-time cosmetic replacement.
3. **Artwork:** `$A161/$A16C→$A1F9` latches effective parameter into `D3B3`
   on offscreen-to-visible change. `$7C71` uses character-dependent pointer tables
   `$7CBB/$7CC7` and `$7CD3/$7CDF`, bank14, transferring 192 and128 bytes to
   VRAM `$0980/$0BC0`. Life parameter2 selects different layers for Tails;
   parameters1/3/5/6 have byte-identical layer hashes across characters. Tails's
   raw parameter4 table entry is **not** the normally displayed Rocket-placement
   art: initialization has already selected1. Hashes/pointers are in controls.
   Container active mappings remain `$0B/$0C`, extents10×24; no character clamp,
   geometry or animation-speed change is in the monitor handler.
4. **Activation:** `$A16C` performs solid projection `$5FA0` first. Attack
   flag `D503.1` is required; bottom contact makes the box hop (player VY+2,
   object VY−2, object state3) without consuming it. Top rejects requested
   `$0F/$10/$15/$1A`; remaining top/side breaks need nonzero downward VY.
   Requested state and stored attack flag matter, not visual character pose.
   Tails flight clears attack; a rotor graphic is not an attack hitbox or a
   monitor-disable rule. Nonattacking, rising, zero-VY, blocked-top and bottom
   controls preserve the box for both characters.
5. **Destruction:** `$A1D3` queues the mask from the **converted** parameter;
   `$033E→$5F54` converts the same slot to `$0F`, awards the shared +10 raw score,
   clears its placement token and leaves the placement occupied. Rebound is
   VY−4 except current state9. Destruction effect frames7/8/9 and eventual
   deletion are shared. Consumed monitors do not respawn in the same loaded act;
   an untouched or bottom-hit monitor can be deleted off-range and recreated.
   Recreated Tails Rocket placements must run initialization and convert again.
6. **Reward/effects:** `$4AA3` consumes the lowest queued bit once per call.
   Ring and life counters are shared; score-derived continues still use the
   character-specific score threshold. A direct, synthetic bit3 for Tails is
   cleared with no Rocket activation; this must not replace step2's Ring reward.

The THZ1 `(336,270)` scheduler case starts player `(336,220)` and camera
`(208,152)`, lets the real placement create/initialize, then uses Button1 taps.
Both break at harness frame1062; reward dispatch at1063 sees queue8 for Sonic
and queue1 for Tails. The graphics loader saw4 versus1. Tails's observed ring
write is BCD `$02→$12`; Sonic subsequently executes `$4775` with selector4.
No monitor object or attack flag was injected. Bounded nearby ring collections
make final Sonic/Tails counters unsuitable as a paired isolated reward delta;
the watched reward write and controlled fixtures provide that delta.

## 2. Equipment, animation, ownership and cancellation

| Interaction | Sonic | Tails | Shared or distinct lifecycle / qualification | Classification |
|---|---|---|---|---|
| Spring Shoes mapped `$2F` | Requests `$12`, player frame `$0B` | Requests `$12`, player frame `$0A` | Same owner `D3A4`, no power selector/timer. Shoe frames3 for12 updates after bounce then4; −7.5 VY rebound, shared8×24 player extent | **ROM gameplay proven** SEZ1 arrival-assisted both |
| Spring Shoes release | Manual jump, side-wall hurt, damage/stomp, terrain spring or state replacement | Same source owners; manual jump observed | Current player state decides owner detach; stale pointer is not cleared. Detached shoe state5 falls/deletes via lifetime and can be recreated | gameplay proven **manual jump only**; other Tails routes static source |
| Mapped `$26` versus Spring Shoes | Effective launch is blocked by state12 phase/floor semantics | Same handler/state12 ownership | Earlier isolated-handler launch result was corrected by `spring-shoes-presentation-audit.md`; no fresh Tails mapped-spring gameplay claim | static source for Tails; inherited Sonic gameplay evidence |
| Rocket equipment | State11, input forced from facing, vertical control, stored attack semantics; damage cancels Rocket without ring loss | Normal placement grants rings; forced state11 aliases stand-init/frame `$0A`, not Rocket motion | State and `D532/D44C` are separate. Tails cannot be assigned Sonic's state11 callback merely because its numeric ID matches | gameplay proven normal selection; controlled-only forced animation |
| Invincibility | Shared flags/aura/selector6 | Shared flags/aura/selector6 | Hazard response gated by selector/flags; monitor still tests attack flag. Expiry clears selector6 through `$189B`, not a character-specific duration | controlled-only reward/timer; inherited source for aura/contact |
| Speed-up | selector3, maximum6 | selector3, maximum6 | Timer1→0 leaves selector3; next0→65535. It is not a proven 900-update termination. Replacement overwrites shared selector/timer | controlled-only edges, both |
| Replacement/overlap | Rocket may coexist with later invincibility/speed selector; Spring pickup replaces movement state | No normal Rocket state; Spring state can coexist with selector3/6 | Do not use one footwear enum for player state, queued reward, aura, attached owner and power timer. New Tails-specific coexistence schedules not executed here | static source; unresolved broad schedules |
| Flight/contact | Sonic has Peel-Out, no flight pickup | Up+fresh action flight; water blocks/ends it, timer300, clears attack | `$613C` cancels requested Tails flight `$18→$0E` when invoked by its callers; controlled negative Sonic and nonflight states preserved | controlled-only helper; M1 static route authority |
| EEZ carrier `$17` | selector frames `$5F/$60` | selector frames `$56/$57` | `$9138` chooses character table; shared ownership `D3A6`, integer position/velocity copy and attack/facing writers. No pickup substitute or character exclusion shown | controlled-only animation; static source capture/effects |

SEZ1 authentic Spring Shoes `(224,398)` test uses START_INDEX SEZ1 and arrival
player `(224,348)`, camera `(96,280)`. Attachment occurs at step16, first state12
at17; shoe frame3 at17..28, frame4 at29..97, bounce at98, then179 (81-update
period). Sonic holds frame11; Tails holds10. Button1 at180 requests ordinary
jump and shoe5 at181; player jump at182. Both use extent8×24. These validate
the same original callback and a real owner across repeated bounces, not just
the no-character-gate reading of `$8B64`.

Footwear termination details remain `powerup-shoes-audit.md` as amended by
`spring-shoes-presentation-audit.md`: sign `$18` and boss `$50` convert pending
state12 to fall at wake; no general shoe timer. The already-awake-sign vertical
stall remains **conditionally reproduced for Sonic, naturally unresolved**;
it is not newly established for a natural Tails route. Spring side-wall hurt
can retain rings and omit invulnerability. Do not replace it with generic damage.

## 3. Rewards and relevant gated outcomes outside monitors

| Interaction / placement | Selection and art | Activation → outcome | Classification |
|---|---|---|---|
| Goal sign `$18`, normal acts1/2 | Same zone-parity prize tables `$A919/$A962`; class1 own portrait (Sonic `$1B`, Tails `$1D`); class3 other portrait (Sonic `$1D`, Tails `$1B`) | life+1 / continue+1 respectively. Class2 same Ring `$1E`/+10 rings; retry0 same blank `$20`; no-prize same bird `$1F`. Same landing/retry/child chain | **ROM gameplay proven, inherited U3**; new focused original landing controls across six zones/both |
| Terrain rings / type09 / Ring monitor | Same pickups and ring counter; no Tails no-reward rule | Ring wrap pays life to both; `$178F` enters Special Stage only if `D2C8==1`, normal zone<6 and Emerald mask incomplete. Tails keeps life and ordinary stage | controlled-only new monitor wrap; inherited G0/SS source/gameplay for entry |
| Special Stage Rocket / clock / invincibility / Emerald / tube | Shared placed objects for Sonic; no ordinary Tails SS entry | SS1 Rocket timer6000 at zone8; other Rocket timers300. Clock pauses SS clock. Tails debug-forced outcomes are controls, not campaign features | static source reachability; inherited SS original execution; new forced monitor controls |
| Score pickups/destruction/sign bonus | Same score writer, character-specific continue threshold | Sonic5,000 raw; Tails3,000 raw digit-sum rule, including wrap exception; these are **continues**, not lives | controlled-only inherited G2-E; no new million-score sweep |
| Final EEZ encounter/ending | `$1E:$BB1A` tests player1 and Emerald mask `$1F`; terminal `$18ED` tests character | Tails takes ordinary final route/own ending regardless Sonic Emerald completion; Sonic all-Emerald route differs. Not a new item reward or an impossible Tails Emerald requirement | static source here; inherited EEZ/G0 execution retains original scope |
| Carrier/loop/twist/springs/water/oil and hazards | Character animation tables may differ; recovered common object/surface owners remain shared | No additional item substitution established. Flight changes posture/reachability, not a general immunity or tail attack. Side-wall pushing checks character-specific frame `$55` for Tails versus Sonic comparison input | static source for inspected owners; untested combinations unresolved |

Sign classification is inherited **with provenance**, not a new complete natural
Tails campaign. U3 executed Tails life/rings/continue/retry sign cases with arrival
fixtures; it did not establish each Tails act-normal handoff. New84 landing
controls cover seven counts × six zones × two characters; table parity remains
zone-dependent, not character-dependent. Sign +10 rings writes directly in its
own handler and must not be assumed to invoke the monitor's life/SS wrap chain.

The absolute-character-read census records33 `LD A,(D500/D2C8)` candidates.
Relevant sites include monitor init, graphics table selection, Rocket reward,
ring SS gate, sign face choices, carrier selector, flight cancellation and final
EEZ gate. Other candidates belong to title/choice/start/continue/ending, animation
transfer and score, already covered by M1/G0/G2-E. `$AE88` family uses `D2C8`
in a scene-specific context; it is not evidence of a new gameplay pickup.
This opcode scan is a cross-check, **not** proof that every indirect character
test or every game interaction was exhaustively recovered. MGHZ `$24/$2E`
remain hazard/emitter systems; no evidence makes them footwear or Tails-only
equipment. No unrelated enemy/boss/terrain re-audit was performed.

## 4. Explicit corrections and unresolved register

* **M1 §A power-ups:** correct Rocket eligibility but incomplete lifecycle.
  Add `$A149` parameter4→1, Ring artwork, ordinary break/+10 reward and ring-wrap
  effects. State11 alias does not imply a dead/unchanged Rocket monitor.
* **THZ1 object10 earlier cache:** already contained the non-Sonic rewrite and
  +10 path, but its historical identity/counter/sound uncertainty predates later
  score/footwear work. This is recovered existing evidence plus new end-to-end
  tests, not a claim the rewrite was absent from all prior Research.
* **`powerup-shoes-audit.md`:** Rocket table/placement inventory is correct for
  Sonic; qualify global reuse by character initialization. Spring descriptions
  saying “Sonic” are not an exclusion of Tails. Preserve the later presentation
  audit's mapped-spring correction; do not revive the isolated `$26` launch.
* **`spring-shoes-presentation-audit.md`:** extend observed attachment,
  frame/owner cadence and manual-jump detach to Tails in SEZ1 only. Do not
  upgrade the unresolved natural sign-stall or every detach route to proven.
* **M2-R1:** unchanged. Shared state20 can select malformed Tails frame `$5E`
  under injected side contact. Its natural reachability remains unresolved;
  new monitor/Spring tests do not close that question or justify replacement art.
* **Speed-up:** timer900 is a load value, not proof of expiry; zero retains
  selector3, as the earlier footwear correction states. Both-character edge
  controls now explicitly establish it.

Additive register `data/m2r2/fidelity-register.json` names confirmed contracts and
open reachability/combination questions. No prior accepted finding is silently
reclassified; unresolved Tails sign stall, every damage/transition overlap,
natural M2-R1 frame5E and untested full-act routes remain visible.

## 5. Review / Designer acceptance implications

Before M2 Package B acceptance, test Tails at an original Rocket placement:
Ring art **before** impact, ordinary solidity/bottom-hop/attack break, +10 rings,
no Rocket state, and correct wrap-life without SS entry. Test ordinary life
monitor portrait/reward, speed/invincibility persistence and Spring Shoes with
Tails's own frame10, original owner/cadence and jump detach. Preserve Sonic's
Rocket entry/control/damage/expiry and life portrait. Use the machine matrix
and evidence controls as inputs; these Research results are not Windows proof
and do not authorize GameMaker edits or acceptance.

Validation: **12 M2-R2 + 9 M1 + 9 M2-R1 tests PASS**, with the private ROM
supplied for original-routine re-execution. The148 focused routine cases and
all six scheduler sessions (four successful arrival-assisted pickup sessions,
two unsuccessful entrance attempts) reproduce with `--gameplay --check`.
`data/m2r2/validation.json` records counts and scope. No full historical sweep
or Windows execution was performed. Stop for Manager review after branch push.
