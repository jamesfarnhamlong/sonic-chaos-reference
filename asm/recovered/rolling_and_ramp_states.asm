; rolling_and_ramp_states: ROM $038C5..$03900 (end exclusive $03901).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

SC_038C5:
    CALL $3FEF
SC_038C8:
    LD A,($D502)
SC_038CB:
    CP 9
SC_038CD:
    RET nz
SC_038CE:
    JP $37F4
; Ramp-launch state $1B update wrapper; state scripts use vector $03C8.
SC_038D1:
    CALL $3FEF
SC_038D4:
    LD A,($D502)
SC_038D7:
    CP $1B
SC_038D9:
    RET nz
SC_038DA:
    BIT 1,(IX+$23)
SC_038DE:
    RET z
SC_038DF:
    RES 0,(IX+3)
SC_038E3:
    LD A,($D147)
SC_038E6:
    AND $30
SC_038E8:
    JP nz,$45ED
SC_038EB:
    LD HL,($D516)
SC_038EE:
    BIT 7,H
SC_038F0:
    JR z,SC_038F9
SC_038F2:
    DEC HL
SC_038F3:
    LD A,H
SC_038F4:
    CPL
SC_038F5:
    LD H,A
SC_038F6:
    LD A,L
SC_038F7:
    CPL
SC_038F8:
    LD L,A
SC_038F9:
    LD A,L
SC_038FA:
    AND $C0
SC_038FC:
    OR H
SC_038FD:
    JP z,$45B3
SC_03900:
    RET
