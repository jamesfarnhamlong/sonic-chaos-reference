; dispatch_target_0606B: ROM $0606B..$06079 (end exclusive $0607A).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Routine entered only through player-callback dispatch (a supported JP stub or a script operand the engine executes); boundaries proven by confined descent.
SC_0606B:
    LD DE,$D500
SC_0606E:
    XOR A
SC_0606F:
    SBC HL,DE
SC_06071:
    LD A,H
SC_06072:
    SLA L
SC_06074:
    RLA
SC_06075:
    SLA L
SC_06077:
    RLA
SC_06078:
    INC A
SC_06079:
    RET
