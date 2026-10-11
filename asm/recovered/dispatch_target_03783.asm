; dispatch_target_03783: ROM $03783..$037CB (end exclusive $037CC).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Routine entered only through player-callback dispatch (a supported JP stub or a script operand the engine executes); boundaries proven by confined descent.
SC_03783:
    LD A,$60
SC_03785:
    LD ($D289),A
SC_03788:
    CALL $3FEF
SC_0378B:
    LD A,(IX+2)
SC_0378E:
    CP 5
SC_03790:
    RET nz
SC_03791:
    CALL $48A7
SC_03794:
    LD A,(IX+$17)
SC_03797:
    INC A
SC_03798:
    CP 2
SC_0379A:
    JR c,SC_037A4
SC_0379C:
    LD HL,$D137
SC_0379F:
    BIT 1,(HL)
SC_037A1:
    JP nz,$47DC
SC_037A4:
    LD A,($D443)
SC_037A7:
    OR A
SC_037A8:
    JR nz,SC_037C6
SC_037AA:
    LD HL,($D516)
SC_037AD:
    BIT 7,H
SC_037AF:
    JR z,SC_037B8
SC_037B1:
    DEC HL
SC_037B2:
    LD A,H
SC_037B3:
    CPL
SC_037B4:
    LD H,A
SC_037B5:
    LD A,L
SC_037B6:
    CPL
SC_037B7:
    LD L,A
SC_037B8:
    LD A,($D374)
SC_037BB:
    CP H
SC_037BC:
    JP z,$47A9
SC_037BF:
    BIT 0,(IX+$24)
SC_037C3:
    JP nz,$4663
SC_037C6:
    CALL $37CC
SC_037C9:
    JP $3831
