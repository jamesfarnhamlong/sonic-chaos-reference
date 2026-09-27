; layout_ring_handler: ROM $0753E..$075DB (end exclusive $075DC).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Terrain-ring top probe: surface type 7 plus block IDs $40-$43 selects a quadrant, replaces the block, increments the ring counter and creates a type-$03 effect.
SC_0753E:
    LD BC,0
SC_07541:
    LD DE,$FFE6
SC_07544:
    BIT 0,(IX+7)
SC_07548:
    JR z,SC_0754D
SC_0754A:
    LD DE,$FFF0
SC_0754D:
    LD A,($D441)
SC_07550:
    LD ($D442),A
SC_07553:
    CALL $7725
SC_07556:
    LD ($D441),A
SC_07559:
    AND $1F
SC_0755B:
    CP 7
SC_0755D:
    JR z,SC_0756F
SC_0755F:
    CP $1D
SC_07561:
    JP z,$760C
SC_07564:
    CP $1A
SC_07566:
    JP z,$7646
SC_07569:
    CP $14
SC_0756B:
    JP $749D
SC_0756E:
    RET
SC_0756F:
    LD A,($D162)
SC_07572:
    CALL $1C6F
SC_07575:
    LD A,($D353)
SC_07578:
    SUB $40
SC_0757A:
    LD ($D352),A
SC_0757D:
    LD L,A
SC_0757E:
    LD H,0
SC_07580:
    ADD HL,HL
SC_07581:
    ADD HL,HL
SC_07582:
    LD DE,$75DC
SC_07585:
    ADD HL,DE
SC_07586:
    LD A,($D358)
SC_07589:
    RRCA
SC_0758A:
    RRCA
SC_0758B:
    RRCA
SC_0758C:
    RRCA
SC_0758D:
    AND 1
SC_0758F:
    LD C,A
SC_07590:
    LD B,0
SC_07592:
    ADD HL,BC
SC_07593:
    LD A,($D35A)
SC_07596:
    RRCA
SC_07597:
    RRCA
SC_07598:
    RRCA
SC_07599:
    AND 2
SC_0759B:
    LD E,A
SC_0759C:
    LD D,0
SC_0759E:
    ADD HL,DE
SC_0759F:
    LD A,(HL)
SC_075A0:
    OR A
SC_075A1:
    RET z
SC_075A2:
    EX DE,HL
SC_075A3:
    ADD HL,BC
SC_075A4:
    EX DE,HL
SC_075A5:
    LD BC,$18
SC_075A8:
    ADD HL,BC
SC_075A9:
    LD A,(HL)
SC_075AA:
    LD HL,($D354)
SC_075AD:
    LD (HL),A
SC_075AE:
    LD L,A
SC_075AF:
    LD H,0
SC_075B1:
    ADD HL,HL
SC_075B2:
    LD A,($D164)
SC_075B5:
    LD C,A
SC_075B6:
    LD A,($D165)
SC_075B9:
    LD B,A
SC_075BA:
    ADD HL,BC
SC_075BB:
    LD E,(HL)
SC_075BC:
    INC HL
SC_075BD:
    LD D,(HL)
SC_075BE:
    CALL $23F9
SC_075C1:
    LD HL,($D358)
SC_075C4:
    LD ($D35C),HL
SC_075C7:
    LD HL,($D35A)
SC_075CA:
    LD ($D35E),HL
SC_075CD:
    LD C,3
SC_075CF:
    LD H,0
SC_075D1:
    CALL $5E9C
SC_075D4:
    LD A,$BF
SC_075D6:
    LD ($DE04),A
SC_075D9:
    JP $3138
