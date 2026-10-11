; banked_dispatch_7013E: ROM $7013E..$70145 (end exclusive $70146).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Dispatch-table targets: $7013E is a bare RET (words 1-15 of the table at $700CB); $7013F (word 0) reads the handler word at (HL+1..HL+2) and jumps to it. The final JP (HL) is an indirect exit that is not followed.
SC_7013E:
    RET
SC_7013F:
    EX DE,HL
SC_70140:
    INC HL
SC_70141:
    LD E,(HL)
SC_70142:
    INC HL
SC_70143:
    LD D,(HL)
SC_70144:
    EX DE,HL
SC_70145:
    JP (HL)
