; object_sprite_coordinate_renderer: ROM $0226A..$02334 (end exclusive $02335).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Generic Y renderer: screen anchor object+$14 minus camera Y, then add each signed mapping-piece Y offset and write the raw VDP SAT Y byte.
SC_0226A:
    LD IY,($D36F)
SC_0226E:
    LD H,(IX+$2B)
SC_02271:
    LD L,(IX+$2A)
SC_02274:
    LD E,(HL)
SC_02275:
    INC HL
SC_02276:
    LD D,(HL)
SC_02277:
    LD L,(IX+$1C)
SC_0227A:
    LD H,(IX+$1D)
SC_0227D:
    ADD HL,DE
SC_0227E:
    PUSH HL
SC_0227F:
    EXX
SC_02280:
    LD D,(IX+$29)
SC_02283:
    LD E,(IX+$28)
SC_02286:
    POP BC
SC_02287:
    EXX
SC_02288:
    LD B,(IX+5)
SC_0228B:
    EXX
SC_0228C:
    LD A,(DE)
SC_0228D:
    LD L,A
SC_0228E:
    INC DE
SC_0228F:
    LD A,(DE)
SC_02290:
    LD H,A
SC_02291:
    INC DE
SC_02292:
    ADD HL,BC
SC_02293:
    LD (IY+0),L
SC_02296:
    LD A,$40
SC_02298:
    ADD A,L
SC_02299:
    LD L,A
SC_0229A:
    JR nc,SC_0229D
SC_0229C:
    INC H
SC_0229D:
    LD A,H
SC_0229E:
    OR A
SC_0229F:
    JR nz,SC_022A6
SC_022A1:
    LD A,L
SC_022A2:
    CP $30
SC_022A4:
    JR nc,SC_022AA
SC_022A6:
    LD (IY+0),$E0
SC_022AA:
    INC DE
SC_022AB:
    INC DE
SC_022AC:
    INC IY
SC_022AE:
    EXX
SC_022AF:
    DJNZ SC_0228B
SC_022B1:
    LD ($D36F),IY
SC_022B5:
    RET
; Sprite renderer; object+$04 bit 4 selects mirrored coordinates and art base object+$09 instead of +$08.
SC_022B6:
    LD IY,($D371)
SC_022BA:
    LD H,(IX+$2B)
SC_022BD:
    LD L,(IX+$2A)
SC_022C0:
    INC HL
SC_022C1:
    INC HL
SC_022C2:
    LD E,(HL)
SC_022C3:
    INC HL
SC_022C4:
    LD D,(HL)
SC_022C5:
    BIT 4,(IX+4)
SC_022C9:
    JR z,SC_022D2
SC_022CB:
    DEC DE
SC_022CC:
    LD A,E
SC_022CD:
    CPL
SC_022CE:
    LD E,A
SC_022CF:
    LD A,D
SC_022D0:
    CPL
SC_022D1:
    LD D,A
SC_022D2:
    INC HL
SC_022D3:
    LD C,(HL)
SC_022D4:
    INC HL
SC_022D5:
    LD B,(HL)
SC_022D6:
    LD ($D110),BC
SC_022DA:
    LD L,(IX+$1A)
SC_022DD:
    LD H,(IX+$1B)
SC_022E0:
    ADD HL,DE
SC_022E1:
    PUSH HL
SC_022E2:
    EXX
SC_022E3:
    LD D,(IX+$29)
SC_022E6:
    LD E,(IX+$28)
SC_022E9:
    INC DE
SC_022EA:
    INC DE
SC_022EB:
    BIT 4,(IX+4)
SC_022EF:
    JR z,SC_022F6
SC_022F1:
    LD HL,$D08
SC_022F4:
    ADD HL,DE
SC_022F5:
    EX DE,HL
SC_022F6:
    POP BC
SC_022F7:
    EXX
SC_022F8:
    LD B,(IX+5)
SC_022FB:
    EXX
SC_022FC:
    LD A,(DE)
SC_022FD:
    LD L,A
SC_022FE:
    INC DE
SC_022FF:
    LD A,(DE)
SC_02300:
    LD H,A
SC_02301:
    INC DE
SC_02302:
    ADD HL,BC
SC_02303:
    LD (IY+0),L
SC_02306:
    LD A,H
SC_02307:
    OR A
SC_02308:
    JR z,SC_0230E
SC_0230A:
    LD (IY+0),0
SC_0230E:
    INC DE
SC_0230F:
    INC DE
SC_02310:
    INC IY
SC_02312:
    LD HL,($D110)
SC_02315:
    LD A,(HL)
SC_02316:
    BIT 4,(IX+4)
SC_0231A:
    JR z,SC_02321
SC_0231C:
    ADD A,(IX+9)
SC_0231F:
    JR SC_02324
SC_02321:
    ADD A,(IX+8)
SC_02324:
    LD (IY+0),A
SC_02327:
    INC HL
SC_02328:
    LD ($D110),HL
SC_0232B:
    INC IY
SC_0232D:
    EXX
SC_0232E:
    DJNZ SC_022FB
SC_02330:
    LD ($D371),IY
SC_02334:
    RET
