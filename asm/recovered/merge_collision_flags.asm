; merge_collision_flags: ROM $064CB..$064EF (end exclusive $064F0).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Merge background flags (+$22) with selected object-contact flags (+$21) into +$23.
SC_064CB:
    LD B,(IX+$22)
SC_064CE:
    LD A,($D3C0)
SC_064D1:
    OR A
SC_064D2:
    JR nz,SC_064E1
SC_064D4:
    BIT 1,(IX+3)
SC_064D8:
    JR nz,SC_064EC
SC_064DA:
    LD A,($D503)
SC_064DD:
    BIT 7,A
SC_064DF:
    JR nz,SC_064EC
SC_064E1:
    LD A,(IX+$21)
SC_064E4:
    RRCA
SC_064E5:
    RRCA
SC_064E6:
    RRCA
SC_064E7:
    RRCA
SC_064E8:
    AND 15
SC_064EA:
    OR B
SC_064EB:
    LD B,A
SC_064EC:
    LD (IX+$23),B
SC_064EF:
    RET
