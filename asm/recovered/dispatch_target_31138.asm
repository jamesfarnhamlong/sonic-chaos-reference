; dispatch_target_31138: ROM $31138..$31162 (end exclusive $31163).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Routine entered only through player-callback dispatch (a supported JP stub or a script operand the engine executes); boundaries proven by confined descent.
SC_31138:
    LD DE,$9163
SC_3113B:
    LD A,($D500)
SC_3113E:
    DEC A
SC_3113F:
    JR z,SC_31144
SC_31141:
    LD DE,$9167
SC_31144:
    LD A,(IX+$1E)
SC_31147:
    BIT 7,(IX+$17)
SC_3114B:
    JR nz,SC_31150
SC_3114D:
    INC A
SC_3114E:
    JR SC_31151
SC_31150:
    DEC A
SC_31151:
    AND 3
SC_31153:
    LD (IX+$1E),A
SC_31156:
    LD L,A
SC_31157:
    LD H,0
SC_31159:
    ADD HL,DE
SC_3115A:
    LD A,(HL)
SC_3115B:
    LD (IX+6),A
SC_3115E:
    LD (IX+7),3
SC_31162:
    RET
