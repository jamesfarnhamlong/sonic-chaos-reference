; object_screen_coordinate_preparation: ROM $03FC8..$03FEE (end exclusive $03FEF).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Prepare generic object screen coordinates: integer object X/Y minus camera X/Y into object+$1A/$1C.
SC_03FC8:
    LD L,(IX+$11)
SC_03FCB:
    LD H,(IX+$12)
SC_03FCE:
    LD DE,($D174)
SC_03FD2:
    XOR A
SC_03FD3:
    SBC HL,DE
SC_03FD5:
    LD (IX+$1A),L
SC_03FD8:
    LD (IX+$1B),H
SC_03FDB:
    LD L,(IX+$14)
SC_03FDE:
    LD H,(IX+$15)
SC_03FE1:
    LD DE,($D176)
SC_03FE5:
    XOR A
SC_03FE6:
    SBC HL,DE
SC_03FE8:
    LD (IX+$1C),L
SC_03FEB:
    LD (IX+$1D),H
SC_03FEE:
    RET
