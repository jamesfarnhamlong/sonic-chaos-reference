; animation_command_dispatch: ROM $06680..$06695 (end exclusive $06696).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Animation command dispatcher after the FF prefix.
SC_06680:
    INC HL
SC_06681:
    LD A,(HL)
SC_06682:
    INC HL
SC_06683:
    LD (IX+14),L
SC_06686:
    LD (IX+15),H
SC_06689:
    ADD A,A
SC_0668A:
    LD L,A
SC_0668B:
    LD H,0
SC_0668D:
    LD DE,$6696
SC_06690:
    ADD HL,DE
SC_06691:
    LD A,(HL)
SC_06692:
    INC HL
SC_06693:
    LD H,(HL)
SC_06694:
    LD L,A
SC_06695:
    JP (HL)
