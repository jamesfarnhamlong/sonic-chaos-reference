; dispatch_target_300D9: ROM $300D9..$3010D (end exclusive $3010E).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Routine entered only through player-callback dispatch (a supported JP stub or a script operand the engine executes); boundaries proven by confined descent.
SC_300D9:
    LD A,($D297)
SC_300DC:
    CP 4
SC_300DE:
    JR nz,SC_3010C
SC_300E0:
    LD A,($D298)
SC_300E3:
    OR A
SC_300E4:
    JP nz,$810C
SC_300E7:
    LD A,($D514)
SC_300EA:
    CP $2E
SC_300EC:
    JP nz,$810C
SC_300EF:
    LD A,($D515)
SC_300F2:
    DEC A
SC_300F3:
    JP nz,$810C
SC_300F6:
    LD A,($D511)
SC_300F9:
    ADD A,8
SC_300FB:
    AND $F8
SC_300FD:
    CP $F0
SC_300FF:
    JP nz,$810C
SC_30102:
    LD A,($D512)
SC_30105:
    CP 6
SC_30107:
    JP nz,$810C
SC_3010A:
    XOR A
SC_3010B:
    RET
SC_3010C:
    SCF
SC_3010D:
    RET
