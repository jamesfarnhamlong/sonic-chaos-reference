; Recovered original Z80 code, file $071B2..$0720F.
; Numeric object fields are offsets from IX. No behavior changes intended.
; Branch labels preserve original addresses; build_check.py verifies every ROM byte.

CR_071B2:
    LD A,($D364)
CR_071B5:
    BIT 7,A
CR_071B7:
    RET z
CR_071B8:
    LD A,($D367)
CR_071BB:
    BIT 6,A
CR_071BD:
    JR nz,CR_071CF
CR_071BF:
    AND $3F
CR_071C1:
    RET z
CR_071C2:
    LD B,A
CR_071C3:
    LD A,($D358)
CR_071C6:
    AND $1F
CR_071C8:
    CP B
CR_071C9:
    RET nc
CR_071CA:
    LD C,A
CR_071CB:
    LD B,0
CR_071CD:
    JR CR_071EC
CR_071CF:
    AND $3F
CR_071D1:
    RET z
CR_071D2:
    LD C,A
CR_071D3:
    LD HL,($D358)
CR_071D6:
    LD DE,$20
CR_071D9:
    ADD HL,DE
CR_071DA:
    LD A,L
CR_071DB:
    AND $E0
CR_071DD:
    LD L,A
CR_071DE:
    LD B,0
CR_071E0:
    XOR A
CR_071E1:
    SBC HL,BC
CR_071E3:
    EX DE,HL
CR_071E4:
    LD HL,($D358)
CR_071E7:
    SBC HL,DE
CR_071E9:
    RET c
CR_071EA:
    LD C,L
CR_071EB:
    LD B,H
CR_071EC:
    LD HL,($D511)
CR_071EF:
    XOR A
CR_071F0:
    SBC HL,BC
CR_071F2:
    LD ($D511),HL
CR_071F5:
    SET 2,(IX+$22)
CR_071F9:
    CALL $64CB
CR_071FC:
    LD A,($D364)
CR_071FF:
    AND $1F
CR_07201:
    CP 10
CR_07203:
    RET nz
CR_07204:
    LD A,($D501)
CR_07207:
    CP $11
CR_07209:
    RET z
CR_0720A:
    LD HL,$FA00
CR_0720D:
    JP $4868
