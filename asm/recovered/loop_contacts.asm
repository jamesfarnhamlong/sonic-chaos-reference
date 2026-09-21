; loop_contacts: ROM $06CBA..$06CE4 (end exclusive $06CE5).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

SC_06CBA:
    LD A,(IX+$25)
SC_06CBD:
    OR A
SC_06CBE:
    RET z
SC_06CBF:
    BIT 1,(IX+$22)
SC_06CC3:
    RET z
SC_06CC4:
    LD A,($D497)
SC_06CC7:
    CP $52
SC_06CC9:
    JP z,$3EE1
SC_06CCC:
    RET
SC_06CCD:
    LD A,(IX+$25)
SC_06CD0:
    OR A
SC_06CD1:
    RET nz
SC_06CD2:
    BIT 1,(IX+$22)
SC_06CD6:
    RET z
SC_06CD7:
    LD A,($D497)
SC_06CDA:
    CP $51
SC_06CDC:
    JP z,$3EAB
SC_06CDF:
    CP $57
SC_06CE1:
    JP z,$3EF7
SC_06CE4:
    RET
