; object_21_handlers: ROM $33210..$332F8 (end exclusive $332F9).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Object $21 initialization: request state 3, set velocity (-$0080,+$0200), and compute X-param*16 left bound.
SC_33210:
    LD (IX+2),3
SC_33214:
    LD (IX+$17),$FF
SC_33218:
    LD (IX+$16),$80
SC_3321C:
    LD (IX+$19),2
SC_33220:
    LD (IX+$18),0
SC_33224:
    SET 7,(IX+3)
SC_33228:
    LD A,(IX+$3F)
SC_3322B:
    LD (IX+$3F),0
SC_3322F:
    LD H,(IX+$12)
SC_33232:
    LD L,(IX+$11)
SC_33235:
    LD D,0
SC_33237:
    LD E,A
SC_33238:
    SLA E
SC_3323A:
    RL D
SC_3323C:
    SLA E
SC_3323E:
    RL D
SC_33240:
    SLA E
SC_33242:
    RL D
SC_33244:
    SLA E
SC_33246:
    RL D
SC_33248:
    XOR A
SC_33249:
    SBC HL,DE
SC_3324B:
    LD (IX+$38),H
SC_3324E:
    LD (IX+$37),L
SC_33251:
    LD A,(IX+4)
SC_33254:
    BIT 4,A
SC_33256:
    RET z
SC_33257:
    LD (IX+$3F),1
SC_3325B:
    LD (IX+4),0
SC_3325F:
    LD (IX+2),5
SC_33263:
    RET
; Left-facing patrol callback clears orientation bit 4, then joins the shared patrol handler.
SC_33264:
    RES 4,(IX+4)
; Object $21 patrol: move, project to floor, reverse at saved bounds, then process player contact.
SC_33268:
    BIT 6,(IX+4)
SC_3326C:
    RET nz
SC_3326D:
    CALL $0338
SC_33270:
    CALL $0320
SC_33273:
    LD A,(IX+$22)
SC_33276:
    BIT 1,A
SC_33278:
    JR nz,SC_3327F
SC_3327A:
    LD (IX+2),1
SC_3327E:
    RET
SC_3327F:
    LD A,($D12F)
SC_33282:
    RRCA
SC_33283:
    JR c,SC_332AF
SC_33285:
    CALL $042E
SC_33288:
    OR A
SC_33289:
    JR z,SC_332AF
SC_3328B:
    CALL $0437
SC_3328E:
    LD A,(IX+2)
SC_33291:
    BIT 0,(IX+$3F)
SC_33295:
    JR nz,SC_332A3
SC_33297:
    CP 4
SC_33299:
    LD A,3
SC_3329B:
    JR z,SC_3329F
SC_3329D:
    LD A,4
SC_3329F:
    LD (IX+2),A
SC_332A2:
    RET
SC_332A3:
    CP 6
SC_332A5:
    LD A,5
SC_332A7:
    JR z,SC_332AB
SC_332A9:
    LD A,6
SC_332AB:
    LD (IX+2),A
SC_332AE:
    RET
; Object $21 contact: top contact springs the player; attack/invincibility destroys; other contact requests damage.
SC_332AF:
    CALL $033B
SC_332B2:
    LD A,(IX+$21)
SC_332B5:
    OR A
SC_332B6:
    RET z
SC_332B7:
    LD H,(IX+$15)
SC_332BA:
    LD L,(IX+$14)
SC_332BD:
    LD DE,$FFFC
SC_332C0:
    ADD HL,DE
SC_332C1:
    LD DE,($D514)
SC_332C5:
    XOR A
SC_332C6:
    SBC HL,DE
SC_332C8:
    JR c,SC_332D5
SC_332CA:
    LD A,$FF
SC_332CC:
    LD ($D448),A
SC_332CF:
    LD HL,$F940
SC_332D2:
    JP $035F
SC_332D5:
    LD A,($D503)
SC_332D8:
    BIT 1,A
SC_332DA:
    JP nz,$033E
SC_332DD:
    LD A,($D532)
SC_332E0:
    CP 6
SC_332E2:
    JP z,$033E
SC_332E5:
    LD A,$FF
SC_332E7:
    LD ($D3B0),A
SC_332EA:
    RET
SC_332EB:
    LD (IX+7),$E0
SC_332EF:
    RET
; Falling callback: integrate position and add $0040 to Y velocity.
SC_332F0:
    CALL $0338
SC_332F3:
    LD DE,$40
SC_332F6:
    JP $0431
