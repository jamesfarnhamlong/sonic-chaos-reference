; dispatch_target_05EB7: ROM $05EB7..$05EE0 (end exclusive $05EE1).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Routine entered only through player-callback dispatch (a supported JP stub or a script operand the engine executes); boundaries proven by confined descent.
SC_05EB7:
    EXX
SC_05EB8:
    LD IY,$D540
SC_05EBC:
    LD B,$10
SC_05EBE:
    LD DE,$40
SC_05EC1:
    LD A,(IY+0)
SC_05EC4:
    OR A
SC_05EC5:
    JR z,SC_05ECD
SC_05EC7:
    ADD IY,DE
SC_05EC9:
    DJNZ SC_05EC1
SC_05ECB:
    EXX
SC_05ECC:
    RET
SC_05ECD:
    EXX
SC_05ECE:
    LD (IY+0),B
SC_05ED1:
    LD (IY+$3F),C
SC_05ED4:
    LD (IY+$12),D
SC_05ED7:
    LD (IY+$11),E
SC_05EDA:
    LD (IY+$15),H
SC_05EDD:
    LD (IY+$14),L
SC_05EE0:
    RET
