; object_visibility_lifetime: ROM $061E1..$06275 (end exclusive $06276).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Post-update visibility/lifetime check. Off-range placed objects become $FE for tracked cleanup and later respawn.
SC_061E1:
    RES 6,(IX+4)
SC_061E5:
    LD L,(IX+$11)
SC_061E8:
    LD H,(IX+$12)
SC_061EB:
    LD BC,$80
SC_061EE:
    ADD HL,BC
SC_061EF:
    LD BC,($D174)
SC_061F3:
    XOR A
SC_061F4:
    SBC HL,BC
SC_061F6:
    JP c,$624C
SC_061F9:
    SRL H
SC_061FB:
    RR L
SC_061FD:
    LD A,H
SC_061FE:
    OR A
SC_061FF:
    JP nz,$624C
SC_06202:
    LD E,L
SC_06203:
    LD L,(IX+$14)
SC_06206:
    LD H,(IX+$15)
SC_06209:
    LD BC,$80
SC_0620C:
    ADD HL,BC
SC_0620D:
    LD BC,($D176)
SC_06211:
    XOR A
SC_06212:
    SBC HL,BC
SC_06214:
    JP c,$624C
SC_06217:
    SRL H
SC_06219:
    RR L
SC_0621B:
    LD A,H
SC_0621C:
    OR A
SC_0621D:
    JP nz,$624C
SC_06220:
    LD A,E
SC_06221:
    RRCA
SC_06222:
    RRCA
SC_06223:
    RRCA
SC_06224:
    AND $1F
SC_06226:
    LD E,A
SC_06227:
    LD A,L
SC_06228:
    AND $F8
SC_0622A:
    LD L,A
SC_0622B:
    LD H,0
SC_0622D:
    LD D,0
SC_0622F:
    ADD HL,HL
SC_06230:
    ADD HL,HL
SC_06231:
    ADD HL,DE
SC_06232:
    LD DE,$8146
SC_06235:
    ADD HL,DE
SC_06236:
    LD A,$1C
SC_06238:
    LD ($D12B),A
SC_0623B:
    LD ($FFFF),A
SC_0623E:
    LD A,(HL)
SC_0623F:
    CP 3
SC_06241:
    JP z,$624C
SC_06244:
    AND 2
SC_06246:
    RET z
SC_06247:
    SET 6,(IX+4)
SC_0624B:
    RET
SC_0624C:
    SET 6,(IX+4)
SC_06250:
    BIT 1,(IX+4)
SC_06254:
    RET nz
SC_06255:
    LD A,(IX+$3E)
SC_06258:
    OR A
SC_06259:
    JR z,SC_06264
SC_0625B:
    LD (IX+0),$FE
SC_0625F:
    LD (IX+1),0
SC_06263:
    RET
SC_06264:
    LD (IX+0),$FF
SC_06268:
    LD (IX+1),0
SC_0626C:
    RET
SC_0626D:
    LD (IX+0),$FF
SC_06271:
    LD (IX+1),0
SC_06275:
    RET
