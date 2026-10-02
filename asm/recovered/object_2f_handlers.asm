; object_2f_handlers: ROM $78B5B..$78BE0 (end exclusive $78BE1).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Object type $2F initializes as a non-generic-damage solid; top projection attaches it and requests player state $12.
SC_78B5B:
    LD (IX+2),1
SC_78B5F:
    SET 7,(IX+3)
SC_78B63:
    RET
SC_78B64:
    BIT 6,(IX+4)
SC_78B68:
    RET nz
SC_78B69:
    LD A,($D519)
SC_78B6C:
    RLCA
SC_78B6D:
    RET c
SC_78B6E:
    LD A,($D501)
SC_78B71:
    CP $12
SC_78B73:
    RET z
SC_78B74:
    CALL $034D
SC_78B77:
    LD A,(IX+$21)
SC_78B7A:
    AND 15
SC_78B7C:
    RET z
SC_78B7D:
    BIT 0,(IX+$21)
SC_78B81:
    JR z,SC_78B95
SC_78B83:
    LD ($D3A4),IX
SC_78B87:
    LD A,$12
SC_78B89:
    LD ($D502),A
SC_78B8C:
    LD (IX+2),3
SC_78B90:
    LD (IX+$1F),$FF
SC_78B94:
    RET
SC_78B95:
    LD A,($D522)
SC_78B98:
    BIT 1,A
SC_78B9A:
    RET z
SC_78B9B:
    LD A,($D503)
SC_78B9E:
    BIT 1,A
SC_78BA0:
    RET z
SC_78BA1:
    LD A,1
SC_78BA3:
    LD ($D502),A
SC_78BA6:
    LD HL,0
SC_78BA9:
    LD ($D516),HL
SC_78BAC:
    LD H,(IX+$12)
SC_78BAF:
    LD L,(IX+$11)
SC_78BB2:
    LD DE,$10
SC_78BB5:
    BIT 2,(IX+$21)
SC_78BB9:
    JR nz,SC_78BBE
SC_78BBB:
    LD DE,$FFF0
SC_78BBE:
    ADD HL,DE
SC_78BBF:
    LD ($D511),HL
SC_78BC2:
    RET
SC_78BC3:
    LD A,($D501)
SC_78BC6:
    CP $12
SC_78BC8:
    RET z
SC_78BC9:
    LD (IX+2),5
SC_78BCD:
    RET
SC_78BCE:
    LD (IX+$19),1
SC_78BD2:
    LD (IX+$18),$80
SC_78BD6:
    RET
SC_78BD7:
    LD DE,$80
SC_78BDA:
    CALL $0431
SC_78BDD:
    CALL $0338
SC_78BE0:
    RET
