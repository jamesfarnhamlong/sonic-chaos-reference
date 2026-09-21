; twist_dispatch: ROM $314C1..$314F4 (end exclusive $314F5).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Twist state $22: damage check, floor update, validate type, table dispatch.
SC_314C1:
    CALL $0416
SC_314C4:
    CALL $0410
SC_314C7:
    LD A,($D364)
SC_314CA:
    AND $3F
SC_314CC:
    CP $17
SC_314CE:
    JP nz,$95E4
SC_314D1:
    LD A,(IX+$38)
SC_314D4:
    AND 3
SC_314D6:
    ADD A,A
SC_314D7:
    LD E,A
SC_314D8:
    LD D,0
SC_314DA:
    LD HL,$94F5
SC_314DD:
    ADD HL,DE
SC_314DE:
    LD A,(HL)
SC_314DF:
    INC HL
SC_314E0:
    LD H,(HL)
SC_314E1:
    LD L,A
SC_314E2:
    LD A,($D353)
SC_314E5:
    SUB $58
SC_314E7:
    ADD A,A
SC_314E8:
    LD E,A
SC_314E9:
    LD D,0
SC_314EB:
    ADD HL,DE
SC_314EC:
    LD A,(HL)
SC_314ED:
    INC HL
SC_314EE:
    LD H,(HL)
SC_314EF:
    LD L,A
SC_314F0:
    LD DE,$95DD
SC_314F3:
    PUSH DE
SC_314F4:
    JP (HL)
