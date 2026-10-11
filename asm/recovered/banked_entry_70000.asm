; banked_entry_70000: ROM $70000..$700CA (end exclusive $700CB).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Bank $1C entry (CPU $8000), called from the gameplay frame update: selects a record list through word tables at $8546 indexed by $D297 then $D298, converts the camera position ($D174/$D176) into a window and walks 9-byte records; for a record whose occupancy byte at $D400+n is zero and whose position falls in the window it dispatches on the byte at +5 through the 16-word table at $80CB (file $700CB, data, not part of this region). Ends with the table dispatch JP (HL).
SC_70000:
    LD A,($D297)
SC_70003:
    ADD A,A
SC_70004:
    LD E,A
SC_70005:
    LD D,0
SC_70007:
    LD HL,$8546
SC_7000A:
    ADD HL,DE
SC_7000B:
    LD A,(HL)
SC_7000C:
    INC HL
SC_7000D:
    LD H,(HL)
SC_7000E:
    LD L,A
SC_7000F:
    LD A,($D298)
SC_70012:
    ADD A,A
SC_70013:
    LD E,A
SC_70014:
    ADD HL,DE
SC_70015:
    LD A,(HL)
SC_70016:
    INC HL
SC_70017:
    LD H,(HL)
SC_70018:
    LD L,A
SC_70019:
    LD BC,$D400
SC_7001C:
    EXX
SC_7001D:
    LD HL,($D174)
SC_70020:
    INC H
SC_70021:
    LD DE,$FF80
SC_70024:
    ADD HL,DE
SC_70025:
    EX DE,HL
SC_70026:
    LD HL,($D176)
SC_70029:
    INC H
SC_7002A:
    LD BC,$FF80
SC_7002D:
    ADD HL,BC
SC_7002E:
    LD C,L
SC_7002F:
    LD B,H
SC_70030:
    EXX
SC_70031:
    LD A,(HL)
SC_70032:
    INC A
SC_70033:
    JR z,SC_70043
SC_70035:
    LD A,(BC)
SC_70036:
    OR A
SC_70037:
    PUSH HL
SC_70038:
    CALL z,$8049
SC_7003B:
    POP HL
SC_7003C:
    INC BC
SC_7003D:
    LD DE,9
SC_70040:
    ADD HL,DE
SC_70041:
    JR SC_70031
SC_70043:
    LD A,1
SC_70045:
    LD ($D440),A
SC_70048:
    RET
SC_70049:
    INC HL
SC_7004A:
    LD A,(HL)
SC_7004B:
    EXX
SC_7004C:
    LD L,A
SC_7004D:
    EXX
SC_7004E:
    INC HL
SC_7004F:
    LD A,(HL)
SC_70050:
    EXX
SC_70051:
    LD H,A
SC_70052:
    XOR A
SC_70053:
    SBC HL,DE
SC_70055:
    JP c,$813C
SC_70058:
    SRL H
SC_7005A:
    RR L
SC_7005C:
    LD A,H
SC_7005D:
    OR A
SC_7005E:
    JP nz,$813C
SC_70061:
    LD A,L
SC_70062:
    LD ($D100),A
SC_70065:
    EXX
SC_70066:
    INC HL
SC_70067:
    LD A,(HL)
SC_70068:
    EXX
SC_70069:
    LD L,A
SC_7006A:
    EXX
SC_7006B:
    INC HL
SC_7006C:
    LD A,(HL)
SC_7006D:
    EXX
SC_7006E:
    LD H,A
SC_7006F:
    XOR A
SC_70070:
    SBC HL,BC
SC_70072:
    JP c,$813C
SC_70075:
    SRL H
SC_70077:
    RR L
SC_70079:
    LD A,H
SC_7007A:
    OR A
SC_7007B:
    JP nz,$813C
SC_7007E:
    PUSH DE
SC_7007F:
    LD A,($D100)
SC_70082:
    RRCA
SC_70083:
    RRCA
SC_70084:
    RRCA
SC_70085:
    AND $1F
SC_70087:
    LD E,A
SC_70088:
    LD A,L
SC_70089:
    AND $F8
SC_7008B:
    LD L,A
SC_7008C:
    LD H,0
SC_7008E:
    LD D,0
SC_70090:
    ADD HL,HL
SC_70091:
    ADD HL,HL
SC_70092:
    ADD HL,DE
SC_70093:
    LD DE,$8146
SC_70096:
    ADD HL,DE
SC_70097:
    POP DE
SC_70098:
    LD A,(HL)
SC_70099:
    CP 2
SC_7009B:
    JR z,SC_700A9
SC_7009D:
    CP 3
SC_7009F:
    JP nc,$813C
SC_700A2:
    LD A,($D440)
SC_700A5:
    OR A
SC_700A6:
    JP nz,$813C
SC_700A9:
    EXX
SC_700AA:
    LD DE,$FFFC
SC_700AD:
    ADD HL,DE
SC_700AE:
    LD A,(HL)
SC_700AF:
    INC A
SC_700B0:
    INC A
SC_700B1:
    JR nz,SC_700EB
SC_700B3:
    LD A,$FF
SC_700B5:
    LD (BC),A
SC_700B6:
    LD DE,5
SC_700B9:
    ADD HL,DE
SC_700BA:
    EX DE,HL
SC_700BB:
    LD A,(DE)
SC_700BC:
    ADD A,A
SC_700BD:
    LD HL,$80CB
SC_700C0:
    ADD A,L
SC_700C1:
    LD L,A
SC_700C2:
    LD A,0
SC_700C4:
    ADC A,H
SC_700C5:
    LD H,A
SC_700C6:
    LD A,(HL)
SC_700C7:
    INC HL
SC_700C8:
    LD H,(HL)
SC_700C9:
    LD L,A
SC_700CA:
    JP (HL)
