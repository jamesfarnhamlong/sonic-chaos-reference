; object_10_tail_handlers: ROM $321F9..$3222C (end exclusive $3222D).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; On off-screen to visible transition, copy the parameter to dynamic graphics selector $D3B3.
SC_321F9:
    LD C,(IX+$26)
SC_321FC:
    LD A,(IX+4)
SC_321FF:
    LD (IX+$26),A
SC_32202:
    BIT 6,A
SC_32204:
    RET nz
SC_32205:
    BIT 6,C
SC_32207:
    RET z
SC_32208:
    LD A,B
SC_32209:
    LD ($D3B3),A
SC_3220C:
    RET
; Type $10 bottom-hit airborne callback: integrate, add gravity, test floor, and return to state 2 on landing.
SC_3220D:
    CALL $0338
SC_32210:
    LD H,(IX+$19)
SC_32213:
    LD L,(IX+$18)
SC_32216:
    LD DE,$40
SC_32219:
    ADD HL,DE
SC_3221A:
    LD (IX+$19),H
SC_3221D:
    LD (IX+$18),L
SC_32220:
    CALL $037A
SC_32223:
    OR A
SC_32224:
    RET nz
SC_32225:
    CALL $0320
SC_32228:
    LD (IX+2),2
SC_3222C:
    RET
