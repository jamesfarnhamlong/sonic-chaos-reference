; dispatch_target_0614E: ROM $0614E..$06167 (end exclusive $06168).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Routine entered only through player-callback dispatch (a supported JP stub or a script operand the engine executes); boundaries proven by confined descent.
SC_0614E:
    LD DE,0
SC_06151:
    LD BC,0
SC_06154:
    CALL $7725
SC_06157:
    LD A,($D364)
SC_0615A:
    BIT 6,A
SC_0615C:
    JR nz,SC_06165
SC_0615E:
    BIT 7,A
SC_06160:
    JR nz,SC_06165
SC_06162:
    LD A,$FF
SC_06164:
    RET
SC_06165:
    LD A,0
SC_06167:
    RET
