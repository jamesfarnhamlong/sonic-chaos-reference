; bounded_layout_decoder: ROM $04DC4..$04DFB (end exclusive $04DFC).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; RLE loop. DE starts at C001; stop when it leaves C000..CFFF, even inside a run.
SC_04DC4:
    LD A,D
SC_04DC5:
    AND $F0
SC_04DC7:
    CP $C0
SC_04DC9:
    JR nz,SC_04DFB
SC_04DCB:
    LD A,(IY+0)
SC_04DCE:
    CP $FF
SC_04DD0:
    JP nz,$4DF1
SC_04DD3:
    LD A,(IY+2)
SC_04DD6:
    OR A
SC_04DD7:
    JP z,$4DFB
SC_04DDA:
    LD B,A
SC_04DDB:
    LD A,D
SC_04DDC:
    AND $F0
SC_04DDE:
    CP $C0
SC_04DE0:
    JR nz,SC_04DFB
SC_04DE2:
    LD A,(IY+1)
SC_04DE5:
    LD (DE),A
SC_04DE6:
    INC DE
SC_04DE7:
    DJNZ SC_04DDB
SC_04DE9:
    LD BC,3
SC_04DEC:
    ADD IY,BC
SC_04DEE:
    JP $4DC4
SC_04DF1:
    LD A,(IY+0)
SC_04DF4:
    LD (DE),A
SC_04DF5:
    INC DE
SC_04DF6:
    INC IY
SC_04DF8:
    JP $4DC4
; Decoder exit; next instructions initialize level rendering. Not a standalone RET.
SC_04DFB:
    EI
