; dispatch_target_062F7: ROM $062F7..$0630A (end exclusive $0630B).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Routine entered only through player-callback dispatch (a supported JP stub or a script operand the engine executes); boundaries proven by confined descent.
SC_062F7:
    LD H,(IX+$17)
SC_062FA:
    LD L,(IX+$16)
SC_062FD:
    DEC HL
SC_062FE:
    LD A,H
SC_062FF:
    CPL
SC_06300:
    LD H,A
SC_06301:
    LD A,L
SC_06302:
    CPL
SC_06303:
    LD L,A
SC_06304:
    LD (IX+$17),H
SC_06307:
    LD (IX+$16),L
SC_0630A:
    RET
