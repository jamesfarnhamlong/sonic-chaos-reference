; object_26_handlers: ROM $7825A..$783B2 (end exclusive $783B3).
; Original Sonic Chaos instructions/data. See docs/provenance.md.
; Generated deterministically by tools/recover.py. Semantic coverage varies.

; Initialize object $26; parameter bit 7 selects a low-seven-bit times 16 trigger span.
SC_7825A:
    LD A,7
SC_7825C:
    LD (IX+2),A
SC_7825F:
    LD (IX+10),A
SC_78262:
    LD H,(IX+$15)
SC_78265:
    LD L,(IX+$14)
SC_78268:
    LD DE,12
SC_7826B:
    ADD HL,DE
SC_7826C:
    LD (IX+$15),H
SC_7826F:
    LD (IX+$14),L
SC_78272:
    LD (IX+$3D),H
SC_78275:
    LD (IX+$3C),L
SC_78278:
    LD A,(IX+$3F)
SC_7827B:
    BIT 7,A
SC_7827D:
    RET z
SC_7827E:
    RES 7,A
SC_78280:
    LD H,0
SC_78282:
    LD L,A
SC_78283:
    SLA L
SC_78285:
    RL H
SC_78287:
    SLA L
SC_78289:
    RL H
SC_7828B:
    SLA L
SC_7828D:
    RL H
SC_7828F:
    SLA L
SC_78291:
    RL H
SC_78293:
    LD (IX+$35),H
SC_78296:
    LD (IX+$34),L
SC_78299:
    LD A,8
SC_7829B:
    LD (IX+2),A
SC_7829E:
    LD (IX+10),A
SC_782A1:
    LD (IX+$3F),1
SC_782A5:
    LD A,(IX+9)
SC_782A8:
    OR A
SC_782A9:
    RET nz
SC_782AA:
    LD (IX+$3F),0
SC_782AE:
    RET
; Fixed concealed spring contact: top contact selects -7.375 or -5.0 and states 1/3.
SC_782AF:
    BIT 6,(IX+4)
SC_782B3:
    RET nz
SC_782B4:
    LD A,($D519)
SC_782B7:
    BIT 7,A
SC_782B9:
    RET nz
SC_782BA:
    LD A,($D522)
SC_782BD:
    BIT 1,A
SC_782BF:
    RET z
SC_782C0:
    LD A,($D502)
SC_782C3:
    CP $21
SC_782C5:
    RET z
SC_782C6:
    LD BC,12
SC_782C9:
    CALL $0383
SC_782CC:
    OR A
SC_782CD:
    RET z
SC_782CE:
    LD H,(IX+$15)
SC_782D1:
    LD L,(IX+$14)
SC_782D4:
    LD DE,$FFE4
SC_782D7:
    ADD HL,DE
SC_782D8:
    LD DE,($D514)
SC_782DC:
    XOR A
SC_782DD:
    SBC HL,DE
SC_782DF:
    RET c
SC_782E0:
    LD DE,6
SC_782E3:
    XOR A
SC_782E4:
    SBC HL,DE
SC_782E6:
    RET nc
SC_782E7:
    LD B,$FF
SC_782E9:
    LD HL,$F8A0
SC_782EC:
    LD A,(IX+$3F)
SC_782EF:
    OR A
SC_782F0:
    JR z,SC_782F7
SC_782F2:
    LD B,0
SC_782F4:
    LD HL,$FB00
SC_782F7:
    LD A,B
SC_782F8:
    LD ($D448),A
SC_782FB:
    CALL $035F
SC_782FE:
    LD A,(IX+$3F)
SC_78301:
    CP 1
SC_78303:
    LD A,1
SC_78305:
    JR nz,SC_78309
SC_78307:
    LD A,3
SC_78309:
    LD (IX+2),A
SC_7830C:
    LD A,$1C
SC_7830E:
    LD (IX+$1E),A
SC_78311:
    RET
; Strong spring extension: counter -7 and Y -7; hold state 2 starts at 32.
SC_78312:
    LD A,(IX+$1E)
SC_78315:
    SUB 7
SC_78317:
    LD (IX+$1E),A
SC_7831A:
    JR nc,SC_78327
SC_7831C:
    LD A,2
SC_7831E:
    LD (IX+2),A
SC_78321:
    LD A,$20
SC_78323:
    LD (IX+$1E),A
SC_78326:
    RET
SC_78327:
    LD H,(IX+$15)
SC_7832A:
    LD L,(IX+$14)
SC_7832D:
    LD DE,7
SC_78330:
    XOR A
SC_78331:
    SBC HL,DE
SC_78333:
    LD (IX+$15),H
SC_78336:
    LD (IX+$14),L
SC_78339:
    RET
; Strong extended-state counter requests retract state 5.
SC_7833A:
    LD A,(IX+$1E)
SC_7833D:
    SUB 1
SC_7833F:
    LD (IX+$1E),A
SC_78342:
    RET nc
SC_78343:
    LD A,5
SC_78345:
    LD (IX+2),A
SC_78348:
    RET
; Shared spring retraction: Y +7 to saved base, then restore saved rest state.
SC_78349:
    LD H,(IX+$15)
SC_7834C:
    LD L,(IX+$14)
SC_7834F:
    LD DE,7
SC_78352:
    XOR A
SC_78353:
    ADD HL,DE
SC_78354:
    LD (IX+$15),H
SC_78357:
    LD (IX+$14),L
SC_7835A:
    LD D,(IX+$3D)
SC_7835D:
    LD E,(IX+$3C)
SC_78360:
    EX DE,HL
SC_78361:
    XOR A
SC_78362:
    SBC HL,DE
SC_78364:
    JR z,SC_78369
SC_78366:
    JR c,SC_78369
SC_78368:
    RET
SC_78369:
    LD A,(IX+10)
SC_7836C:
    LD (IX+2),A
SC_7836F:
    LD H,(IX+$3D)
SC_78372:
    LD L,(IX+$3C)
SC_78375:
    LD (IX+$15),H
SC_78378:
    LD (IX+$14),L
SC_7837B:
    RET
; Weak spring extension; hold state 4 starts at 10.
SC_7837C:
    LD A,(IX+$1E)
SC_7837F:
    SUB 7
SC_78381:
    LD (IX+$1E),A
SC_78384:
    JR nc,SC_78391
SC_78386:
    LD A,4
SC_78388:
    LD (IX+2),A
SC_7838B:
    LD A,10
SC_7838D:
    LD (IX+$1E),A
SC_78390:
    RET
SC_78391:
    LD H,(IX+$15)
SC_78394:
    LD L,(IX+$14)
SC_78397:
    LD DE,7
SC_7839A:
    XOR A
SC_7839B:
    SBC HL,DE
SC_7839D:
    LD (IX+$15),H
SC_783A0:
    LD (IX+$14),L
SC_783A3:
    RET
; Weak extended-state counter requests retract state 6.
SC_783A4:
    LD A,(IX+$1E)
SC_783A7:
    SUB 1
SC_783A9:
    LD (IX+$1E),A
SC_783AC:
    RET nc
SC_783AD:
    LD A,6
SC_783AF:
    LD (IX+2),A
SC_783B2:
    RET
