; dispatch_target_03A37: ROM $03A37..$03A58 (end exclusive $03A59).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Routine entered only through player-callback dispatch (a supported JP stub or a script operand the engine executes); boundaries proven by confined descent.
SC_03A37:
    CALL $3FEF
SC_03A3A:
    LD A,($D502)
SC_03A3D:
    CP 14
SC_03A3F:
    RET nz
SC_03A40:
    BIT 1,(IX+$23)
SC_03A44:
    JP nz,$45CE
SC_03A47:
    RET
SC_03A48:
    CALL $3FEF
SC_03A4B:
    LD A,($D502)
SC_03A4E:
    CP $14
SC_03A50:
    RET nz
SC_03A51:
    BIT 1,(IX+$23)
SC_03A55:
    JP nz,$45CE
SC_03A58:
    RET
