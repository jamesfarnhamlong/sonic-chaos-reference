; dispatch_target_0384D: ROM $0384D..$0386E (end exclusive $0386F).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Routine entered only through player-callback dispatch (a supported JP stub or a script operand the engine executes); boundaries proven by confined descent.
SC_0384D:
    CALL $3FEF
SC_03850:
    LD A,($D502)
SC_03853:
    CP 6
SC_03855:
    RET nz
SC_03856:
    LD HL,$D137
SC_03859:
    BIT 1,(HL)
SC_0385B:
    JP nz,$47DC
SC_0385E:
    LD A,($D517)
SC_03861:
    BIT 7,A
SC_03863:
    JR z,SC_03867
SC_03865:
    NEG
SC_03867:
    CP 4
SC_03869:
    JP c,$45CE
SC_0386C:
    JP $3831
