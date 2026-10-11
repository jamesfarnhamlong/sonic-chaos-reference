; main_loop_bit1_handler: ROM $01673..$01695 (end exclusive $01696).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Handler for $D293 bit 1: calls $4FCE, $3175, the level load sequence $2934, $3116, $314A, $285C, $189B, $794F and the camera vector routine $59B3, clears the bit and returns to the main loop.
SC_01673:
    CALL $4FCE
SC_01676:
    CALL $3175
SC_01679:
    CALL $2934
SC_0167C:
    CALL $3116
SC_0167F:
    CALL $314A
SC_01682:
    CALL $285C
SC_01685:
    CALL $189B
SC_01688:
    CALL $794F
SC_0168B:
    CALL $59B3
SC_0168E:
    LD HL,$D293
SC_01691:
    RES 1,(HL)
SC_01693:
    JP $1333
