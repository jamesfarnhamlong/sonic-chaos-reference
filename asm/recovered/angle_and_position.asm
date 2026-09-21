; angle_and_position: ROM $06089..$0613B (end exclusive $0613C).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; angle byte IX+$0A and magnitude byte IX+$0B -> signed 8.8 velocity.
SC_06089:
    XOR A
SC_0608A:
    LD (IX+$16),A
SC_0608D:
    LD (IX+$17),A
SC_06090:
    LD (IX+$18),A
SC_06093:
    LD (IX+$19),A
SC_06096:
    LD A,(IX+11)
SC_06099:
    OR A
SC_0609A:
    RET z
SC_0609B:
    LD D,0
SC_0609D:
    LD E,(IX+10)
; Signed table at $0200; multiply sample by magnitude, arithmetic shift right four.
SC_060A0:
    LD HL,$200
SC_060A3:
    ADD HL,DE
SC_060A4:
    LD A,(HL)
SC_060A5:
    LD E,A
SC_060A6:
    AND $80
SC_060A8:
    RLCA
SC_060A9:
    NEG
SC_060AB:
    LD D,A
SC_060AC:
    LD HL,0
SC_060AF:
    LD B,(IX+11)
SC_060B2:
    ADD HL,DE
SC_060B3:
    DJNZ SC_060B2
SC_060B5:
    LD A,L
SC_060B6:
    SRA H
SC_060B8:
    RRA
SC_060B9:
    SRA H
SC_060BB:
    RRA
SC_060BC:
    SRA H
SC_060BE:
    RRA
SC_060BF:
    SRA H
SC_060C1:
    RRA
SC_060C2:
    LD (IX+$16),A
SC_060C5:
    LD (IX+$17),H
; Y uses the same table with angle+$C0, wrapping to 8 bits.
SC_060C8:
    LD A,(IX+10)
SC_060CB:
    ADD A,$C0
SC_060CD:
    LD E,A
SC_060CE:
    LD D,0
SC_060D0:
    LD HL,$200
SC_060D3:
    ADD HL,DE
SC_060D4:
    LD A,(HL)
SC_060D5:
    LD E,A
SC_060D6:
    AND $80
SC_060D8:
    RLCA
SC_060D9:
    NEG
SC_060DB:
    LD D,A
SC_060DC:
    LD HL,0
SC_060DF:
    LD B,(IX+11)
SC_060E2:
    ADD HL,DE
SC_060E3:
    DJNZ SC_060E2
SC_060E5:
    LD A,L
SC_060E6:
    SRA H
SC_060E8:
    RRA
SC_060E9:
    SRA H
SC_060EB:
    RRA
SC_060EC:
    SRA H
SC_060EE:
    RRA
SC_060EF:
    SRA H
SC_060F1:
    RRA
SC_060F2:
    LD (IX+$18),A
SC_060F5:
    LD (IX+$19),H
SC_060F8:
    RET
SC_060F9:
    RET
SC_060FA:
    RET
; Integrate velocities into object 16.8 positions; preserve subpixels.
SC_060FB:
    LD L,(IX+$10)
SC_060FE:
    LD H,(IX+$11)
SC_06101:
    LD E,(IX+$16)
SC_06104:
    LD D,(IX+$17)
SC_06107:
    LD B,(IX+$12)
SC_0610A:
    LD A,D
SC_0610B:
    AND $80
SC_0610D:
    RLCA
SC_0610E:
    DEC A
SC_0610F:
    CPL
SC_06110:
    ADD HL,DE
SC_06111:
    ADC A,B
SC_06112:
    LD (IX+$12),A
SC_06115:
    LD (IX+$10),L
SC_06118:
    LD (IX+$11),H
SC_0611B:
    LD L,(IX+$13)
SC_0611E:
    LD H,(IX+$14)
SC_06121:
    LD E,(IX+$18)
SC_06124:
    LD D,(IX+$19)
SC_06127:
    LD B,(IX+$15)
SC_0612A:
    LD A,D
SC_0612B:
    AND $80
SC_0612D:
    RLCA
SC_0612E:
    DEC A
SC_0612F:
    CPL
SC_06130:
    ADD HL,DE
SC_06131:
    ADC A,B
SC_06132:
    LD (IX+$15),A
SC_06135:
    LD (IX+$13),L
SC_06138:
    LD (IX+$14),H
SC_0613B:
    RET
