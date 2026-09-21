; terrain_update: ROM $0690B..$06972 (end exclusive $06973).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Shared collision order: floor, sides, ceiling, top special probe, merge.
SC_0690B:
    CALL $691A
SC_0690E:
    CALL $715E
SC_06911:
    CALL $73C9
SC_06914:
    CALL $753E
SC_06917:
    JP $64CB
; Save previous modifier, clear current modifier; foot probe at dx=0,dy=0 normally.
SC_0691A:
    LD A,($D369)
SC_0691D:
    LD ($D36A),A
SC_06920:
    XOR A
SC_06921:
    LD ($D369),A
SC_06924:
    LD A,($D36B)
SC_06927:
    LD ($D497),A
SC_0692A:
    LD BC,0
SC_0692D:
    LD DE,0
SC_06930:
    BIT 1,(IX+0)
SC_06934:
    JR z,SC_0693C
SC_06936:
    LD BC,0
SC_06939:
    LD DE,0
SC_0693C:
    LD A,(IX+1)
SC_0693F:
    CP $21
SC_06941:
    JR nz,SC_06948
SC_06943:
    LD DE,$FFF2
SC_06946:
    JR SC_0694F
SC_06948:
    CP $12
SC_0694A:
    JR nz,SC_0694F
SC_0694C:
    LD DE,8
; Lookup uses current centre X and Y+18, with state-specific Y offsets above.
SC_0694F:
    CALL $7666
SC_06952:
    LD A,($D353)
SC_06955:
    LD ($D36B),A
SC_06958:
    LD ($D36D),A
; Floor projection runs BEFORE D36C is replaced by the newly sampled surface type.
SC_0695B:
    CALL $6F61
SC_0695E:
    LD A,($D364)
SC_06961:
    LD ($D36C),A
; Dispatch using current surface type AND $1F.
SC_06964:
    AND $1F
SC_06966:
    ADD A,A
SC_06967:
    LD L,A
SC_06968:
    LD H,0
SC_0696A:
    LD DE,$6973
SC_0696D:
    ADD HL,DE
SC_0696E:
    LD E,(HL)
SC_0696F:
    INC HL
SC_06970:
    LD D,(HL)
SC_06971:
    EX DE,HL
SC_06972:
    JP (HL)
