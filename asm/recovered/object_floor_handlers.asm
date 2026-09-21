; object_floor_handlers: ROM $0782B..$07856 (end exclusive $07857).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

SC_0782B:
    RET
SC_0782C:
    BIT 0,(IX+3)
SC_07830:
    RET nz
SC_07831:
    SET 4,(IX+3)
SC_07835:
    RET
SC_07836:
    BIT 1,(IX+$22)
SC_0783A:
    RET z
SC_0783B:
    LD HL,$FF00
SC_0783E:
    LD A,($D353)
SC_07841:
    CP $F0
SC_07843:
    JR z,SC_07848
SC_07845:
    LD HL,$100
SC_07848:
    LD E,(IX+$11)
SC_0784B:
    LD D,(IX+$12)
SC_0784E:
    ADD HL,DE
SC_0784F:
    LD (IX+$11),L
SC_07852:
    LD (IX+$12),H
SC_07855:
    RET
SC_07856:
    RET
