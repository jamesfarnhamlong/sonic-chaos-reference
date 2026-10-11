; dispatch_target_03901: ROM $03901..$0393A (end exclusive $0393B).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Routine entered only through player-callback dispatch (a supported JP stub or a script operand the engine executes); boundaries proven by confined descent.
SC_03901:
    LD HL,$D3B2
SC_03904:
    LD A,($D137)
SC_03907:
    AND $30
SC_03909:
    JR nz,SC_0390F
SC_0390B:
    LD (HL),$20
SC_0390D:
    JR SC_03924
SC_0390F:
    INC (HL)
SC_03910:
    LD A,(HL)
SC_03911:
    CP 14
SC_03913:
    JR nc,SC_03924
SC_03915:
    LD HL,$FBC0
SC_03918:
    LD A,($D443)
SC_0391B:
    OR A
SC_0391C:
    JR z,SC_03921
SC_0391E:
    LD HL,$FCC0
SC_03921:
    LD ($D518),HL
SC_03924:
    CALL $3FEF
SC_03927:
    LD A,($D502)
SC_0392A:
    CP 10
SC_0392C:
    RET nz
SC_0392D:
    BIT 1,(IX+$23)
SC_03931:
    RET z
SC_03932:
    LD A,($D36C)
SC_03935:
    CP 13
SC_03937:
    JP nz,$45CE
SC_0393A:
    RET
