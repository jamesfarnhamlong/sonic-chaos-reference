; breakable_handlers: ROM $07857..$078E0 (end exclusive $078E1).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Changes the collided map block to $46, refreshes mapping and spawns debris.
SC_07857:
    LD A,1
SC_07859:
    LD ($D3B3),A
SC_0785C:
    LD A,($D162)
SC_0785F:
    CALL $1C6F
SC_07862:
    LD A,$46
SC_07864:
    LD HL,($D354)
SC_07867:
    LD (HL),A
SC_07868:
    LD L,A
SC_07869:
    LD H,0
SC_0786B:
    ADD HL,HL
SC_0786C:
    LD A,($D164)
SC_0786F:
    LD C,A
SC_07870:
    LD A,($D165)
SC_07873:
    LD B,A
SC_07874:
    ADD HL,BC
SC_07875:
    LD E,(HL)
SC_07876:
    INC HL
SC_07877:
    LD D,(HL)
SC_07878:
    CALL $23F9
SC_0787B:
    LD HL,($D358)
SC_0787E:
    LD A,L
SC_0787F:
    AND $E0
SC_07881:
    ADD A,$10
SC_07883:
    LD L,A
SC_07884:
    EX DE,HL
SC_07885:
    LD HL,($D35A)
SC_07888:
    LD A,L
SC_07889:
    AND $E0
SC_0788B:
    ADD A,8
SC_0788D:
    LD L,A
SC_0788E:
    LD B,15
SC_07890:
    LD C,$40
SC_07892:
    CALL $5EB7
SC_07895:
    JP $4AC2
; Changes the collided map block to $9D, refreshes mapping and spawns four fragments.
SC_07898:
    LD A,($D162)
SC_0789B:
    CALL $1C6F
SC_0789E:
    LD A,$9D
SC_078A0:
    LD HL,($D354)
SC_078A3:
    LD (HL),A
SC_078A4:
    LD L,A
SC_078A5:
    LD H,0
SC_078A7:
    ADD HL,HL
SC_078A8:
    LD A,($D164)
SC_078AB:
    LD C,A
SC_078AC:
    LD A,($D165)
SC_078AF:
    LD B,A
SC_078B0:
    ADD HL,BC
SC_078B1:
    LD E,(HL)
SC_078B2:
    INC HL
SC_078B3:
    LD D,(HL)
SC_078B4:
    CALL $23F9
SC_078B7:
    LD HL,($D358)
SC_078BA:
    LD A,L
SC_078BB:
    AND $E0
SC_078BD:
    LD L,A
SC_078BE:
    LD ($D35C),HL
SC_078C1:
    LD HL,($D35A)
SC_078C4:
    LD A,L
SC_078C5:
    AND $E0
SC_078C7:
    LD L,A
SC_078C8:
    LD ($D35E),HL
SC_078CB:
    LD C,7
SC_078CD:
    LD H,0
SC_078CF:
    CALL $5E9C
SC_078D2:
    LD H,1
SC_078D4:
    CALL $5E9C
SC_078D7:
    LD H,2
SC_078D9:
    CALL $5E9C
SC_078DC:
    LD H,3
SC_078DE:
    JP $5E9C
