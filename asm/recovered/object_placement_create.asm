; object_placement_create: ROM $700EB..$7013D (end exclusive $7013E).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Create a placement-backed object, preserving origin, parameter, art bases, and occupancy token.
SC_700EB:
    PUSH BC
SC_700EC:
    CALL $0329
SC_700EF:
    POP BC
SC_700F0:
    JR c,SC_7013B
SC_700F2:
    LD A,(HL)
SC_700F3:
    LD (IY+0),A
SC_700F6:
    LD (BC),A
SC_700F7:
    INC HL
SC_700F8:
    LD A,(HL)
SC_700F9:
    LD (IY+$3A),A
SC_700FC:
    LD (IY+$11),A
SC_700FF:
    INC HL
SC_70100:
    LD A,(HL)
SC_70101:
    DEC A
SC_70102:
    LD (IY+$3B),A
SC_70105:
    LD (IY+$12),A
SC_70108:
    INC HL
SC_70109:
    LD A,(HL)
SC_7010A:
    LD (IY+$3C),A
SC_7010D:
    LD (IY+$14),A
SC_70110:
    INC HL
SC_70111:
    LD A,(HL)
SC_70112:
    DEC A
SC_70113:
    LD (IY+$3D),A
SC_70116:
    LD (IY+$15),A
SC_70119:
    INC HL
SC_7011A:
    LD A,(HL)
SC_7011B:
    OR $40
SC_7011D:
    LD (IY+4),A
SC_70120:
    INC HL
SC_70121:
    LD A,(HL)
SC_70122:
    LD (IY+$3F),A
SC_70125:
    INC HL
SC_70126:
    LD A,(HL)
SC_70127:
    LD (IY+8),A
SC_7012A:
    INC HL
SC_7012B:
    LD A,(HL)
SC_7012C:
    LD (IY+9),A
SC_7012F:
    LD L,C
SC_70130:
    LD H,B
SC_70131:
    LD DE,$D400
SC_70134:
    XOR A
SC_70135:
    SBC HL,DE
SC_70137:
    INC L
SC_70138:
    LD (IY+$3E),L
SC_7013B:
    RET
SC_7013C:
    EXX
SC_7013D:
    RET
