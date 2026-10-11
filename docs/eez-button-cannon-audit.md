# EEZ3 floor button / ceiling cannon bolt — focused audit

Existing contract (not a new model): `eez-environment-audit.md` and `eez-objects-audit.md` already close
surface `$0B` (`$6BAA`, cell `$B1->$B2`, type `$37` parameter 1, no restoration). This audit re-proves it
through the whole-game scheduler for EEZ3 (`tools/eez_button_cannon.py`, `data/rom-cache/eez/button-cannon.json`,
`tests/test_eez_button_cannon.py`). The POC's permanent disable matches the ROM.

Chain: floor pass -> `$6BAA` (needs floor bit1) -> `$6BAF` C=`$B2`, `$6BD4` writes layout cell `*$D354` and redraws it
-> `$5E9C` type `$37` parameter 1 -> `$1E:$8ED0` state 3 -> `$8F43` falls +4.25, hurts while at/before cellY-24
-> state 2 dissipate -> delete. EEZ3 act index 2 uses the -120 spawn offset (EEZ2 uses -88).

1. No re-arm. Cell stays `$B2` until the level loader (`$4DAE..$4DFB`) re-decodes the layout (death/restart).
2. No callback count or event exists; only a level (re)load restores `$B1`.
3. No visible reset: `$B2` is written and redrawn once.
4. Local per layout cell: seven `$B1` cells at EEZ3 row 26, x=36,38..48, each fires once. Shared: object pool, scratch `$D354/$D35C/$D35E`.
5. Standing: handler fires once (update 18), later frames probe `$B2`; 700 updates, one allocation.
6. No effect on the cell. Bolt leaving the camera is removed by generic lifecycle (cell stays `$B2`); the cell survives 1000 offscreen updates.

Evidence: whole-game fixtures S1-S4; immediate-operand scan finds `$6BAF` as the only `LD C,$B2 ; CALL $6BD4`.
Fixture writes: placement, invincibility `$D532=6`, camera `$D174/$D176/$D284/$D286`; the layout cell is never written.
Limitation: S4 death by walking into the pit; the harness is approximate SMS, not natural-input acceptance.
