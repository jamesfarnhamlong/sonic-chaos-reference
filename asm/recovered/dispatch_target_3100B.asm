; dispatch_target_3100B: ROM $3100B..$3103C (end exclusive $3103D).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Routine entered only through player-callback dispatch (a supported JP stub or a script operand the engine executes); boundaries proven by confined descent.
SC_3100B:
    LD HL,($D53C)
SC_3100E:
    LD DE,($D514)
SC_31012:
    XOR A
SC_31013:
    SBC HL,DE
SC_31015:
    SRL L
SC_31017:
    SRL L
SC_31019:
    SRL L
SC_3101B:
    SRL L
SC_3101D:
    LD H,0
SC_3101F:
    ADD HL,HL
SC_31020:
    LD DE,$906C
SC_31023:
    LD A,(IX+0)
SC_31026:
    DEC A
SC_31027:
    JR z,SC_3102C
SC_31029:
    LD DE,$90D2
SC_3102C:
    ADD HL,DE
SC_3102D:
    LD A,(HL)
SC_3102E:
    CP (IX+6)
SC_31031:
    JR nz,SC_31034
SC_31033:
    INC HL
SC_31034:
    LD A,(HL)
SC_31035:
    LD (IX+6),A
SC_31038:
    LD (IX+7),6
SC_3103C:
    RET
