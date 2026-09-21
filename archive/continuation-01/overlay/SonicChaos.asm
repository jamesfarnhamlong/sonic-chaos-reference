; Sonic Chaos SMS Version Disassembly By Ravenfreak AKA Amber Davis
.def Copy_CRAM       $D472      ; copy of C-RAM data
.def RingArt         $2A9A      ; Ring art pointers
.def Frame_Count     $D2C2      ; frame counter used to update the timer

.MEMORYMAP
SLOTSIZE $4000
SLOT 0 $0000
SLOT 1 $4000
SLOT 2 $8000
DEFAULTSLOT 2
.ENDME

.ROMBANKMAP
BANKSTOTAL 32
BANKSIZE $4000
BANKS 32
.ENDRO


; Banking:
;   Bank 0 in slot 0
;   Bank 1 in slot 1
;   Bank 2 in slot 1
;   Bank 3 in slot 2
;   Bank 4's slot unknown
;   Bank 5 in slot 2
;   Bank 6's slot unknown
;   Bank 7's slot unknown
;   Bank 8's slot unknown
;   Bank 9's slot unknown
;   Bank 10's slot unknown
;   Bank 11's slot unknown
;   Bank 12 in slot 2
;   Bank 13's slot unknown
;   Bank 14 in slot 2
;   Bank 15 in slot 2
;   Bank 16 in slot 2
;   Bank 17's slot unknown
;   Bank 18's slot unknown
;   Bank 19 in slot 2
;   Bank 20's slot unknown
;   Bank 21's slot unknown
;   Bank 22's slot unknown
;   Bank 23's slot unknown
;   Bank 24's slot unknown
;   Bank 25's slot unknown
;   Bank 26's slot unknown
;   Bank 27 in slot 2
;   Bank 28 in slot 2
;   Bank 29 in slot 2
;   Bank 30 in slot 2
;   Bank 31 in slot 2

; RAM access
.def RAM_D12E $D12E ; byte
.def RAM_D295 $D295 ; byte
.def RAM_D51D $D51D ; byte
.def RAM_D501 $D501 ; byte
.def RAM_D440 $D440 ; byte
.def RAM_D100 $D100 ; byte
.def RAM_D2E2 $D2E2 ; byte
.def RAM_D3B6 $D3B6 ;      word
.def RAM_D3B8 $D3B8 ;      word
.def RAM_D3B5 $D3B5 ; byte
.def RAM_D3BA $D3BA ;      word
.def RAM_D3B4 $D3B4 ; byte
.def RAM_D3B3 $D3B3 ; byte
.def RAM_D521 $D521 ; byte
.def RAM_D2CD $D2CD ; byte
.def Screenmode $D294 ; byte
.def RAM_D2CC $D2CC ; byte
.def RAM_DBB3 $DBB3 ; byte
.def RAM_DBB1 $DBB1 ; byte
.def RAM_DBAB $DBAB ; byte
.def RAM_DBA9 $DBA9 ; byte
.def Lives_Count $D299 ; byte
.def RAM_D3A1 $D3A1 ;      word
.def HorizontalVelocity $D516 ;      word
.def PowerUpTimer $D44C ;      word
.def RAM_D373 $D373 ;      word
.def PowerUp $D532 ; byte
.def RAM_D375 $D375 ;      word
.def VerticalVelocity $D518 ;      word
.def RAM_D16C $D16C ;      word
.def RAM_D2DC $D2DC ;      word
.def RAM_D2DA $D2DA ;      word
.def RAM_D15F $D15F ; byte
.def RAM_D495 $D495 ; byte
.def RAM_D493 $D493 ; byte
.def RAM_D2BD $D2BD ; byte
.def RAM_D450 $D450 ;      word
.def RAM_D46A $D46A ; byte
.def RAM_D462 $D462 ; byte
.def RAM_D45A $D45A ; byte
.def RAM_D452 $D452 ; byte
.def RAM_D2E0 $D2E0 ;      word
.def Ring_Count $D29A ; byte
.def RAM_D164 $D164 ;      word
.def RAM_D16E $D16E ;      word
.def RAM_D278 $D278 ;      word
.def RAM_D168 $D168 ;      word
.def RAM_D170 $D170 ;      word
.def RAM_D162 $D162 ; byte
.def RAM_D514 $D514 ;      word
.def RAM_D511 $D511 ;      word
.def RAM_D2D8 $D2D8 ;      word
.def RAM_D2D6 $D2D6 ;      word
.def BottomBound $D28E ; byte
.def TopBound $D28F ; byte
.def RAM_D28D $D28D ; byte
.def RightBound $D28B ; byte
.def LeftBound $D28C ; byte
.def RAM_D28A $D28A ; byte
.def Y_CamOffset $D289 ; byte
.def X_CamOffset $D288 ; byte
.def RAM_D27E $D27E ;      word
.def RAM_D282 $D282 ;      word
.def RAM_D27C $D27C ;      word
.def RAM_D280 $D280 ;      word
.def RAM_DB39 $DB39 ; byte
.def RAM_DB38 $DB38 ; byte
.def BitField $D340 ; Bitfield counter,byte
.def RAM_D344 $D344 ;      word
.def RAM_D346 $D346 ;      word
.def RAM_D343 $D343 ; byte
.def RAM_D342 $D342 ; byte word
.def RAM_D34C $D34C ; byte
.def RAM_D4A3 $D4A3 ; byte
.def StopWatchPwrUp $D3C4 ; byte
.def RAM_DBBF $DBBF ; byte
.def RAM_DBBD $DBBD ; byte
.def TimerMin $D2BF ; byte
.def RAM_DBB9 $DBB9 ; byte
.def TimerSec $D2C0 ; byte
.def RAM_D44B $D44B ; byte
.def RAM_D2BE $D2BE ; byte
.def RAM_DE11 $DE11 ; byte
.def RAM_DE15 $DE15 ; byte
.def RAM_DE01 $DE01 ; byte
.def RAM_DE0D $DE0D ; byte
.def RAM_DE0B $DE0B ; byte
.def RAM_DE0A $DE0A ; byte
.def RAM_DE09 $DE09 ; byte
.def RAM_DE02 $DE02 ; byte
.def PlaySound $DE04 ; byte
.def RAM_D4A4 $D4A4 ; byte
.def RAM_D506 $D506 ; byte
.def RAM_D350 $D350 ; byte
.def RAM_D504 $D504 ; byte
.def SATUpdate $D134 ; byte
.def RAM_D110 $D110 ;      word
.def RAM_D371 $D371 ;      word
.def RAM_D36F $D36F ;      word
.def RAM_D500 $D500 ; byte
.def RAM_D34F $D34F ; byte
.def RAM_D34E $D34E ; byte
.def ControlByte $D2DE ; used only for demos,word
.def RAM_D157 $D157 ; byte
.def RAM_D147 $D147 ; byte
.def RAM_D138 $D138 ; byte
.def Joypad_Press $D137 ; byte
.def RAM_DBB7 $DBB7 ; byte
.def RAM_DBB5 $DBB5 ; byte
.def RAM_D39B $D39B ;      word
.def RAM_D399 $D399 ;      word
.def RAM_D351 $D351 ; byte
.def RAM_D12F $D12F ; byte
.def RAM_D286 $D286 ; byte word
.def RAM_D284 $D284 ; byte word
.def VertOffset $D176 ; byte word
.def HorizOffset $D174 ; byte word
.def RAM_D15E $D15E ; byte
.def BGYScroll $D173 ; Background on Y plane scroll byte
.def BGXScroll $D172 ; Background on X plane scroll byte
.def RAM_D290 $D290 ; byte
.def RAM_D136 $D136 ; byte
.def RAM_D44F $D44F ; byte
.def BGPalleteControlByte $D492 ; byte
.def RAM_D131 $D131 ; byte
.def PaletteUpdate $D496 ; byte
.def RAM_D11E $D11E ; byte
.def Underwater $D443 ; byte
.def RAM_D132 $D132 ; byte
.def Gamestate $D293 ; byte
.def CurrentAct $D298 ; byte
.def RAM_D2E5 $D2E5 ;      word
.def RAM_D2E4 $D2E4 ; byte
.def RAM_D2C8 $D2C8 ; byte
.def CurrentLevel $D297 ; current level :V, byte
.def DemoBank $D2E3 ; byte
.def RAM_D292 $D292 ; byte
.def RAM_D2D4 $D2D4 ; byte
.def RAM_D2D1 $D2D1 ;      word
.def RAM_D2CF $D2CF ;      word
.def RAM_D2CE $D2CE ; byte
.def RAM_DE03 $DE03 ; byte
.def RAM_DE91 $DE91 ; byte
.def RAM_D12D $D12D ; byte
.def RAM_D12B $D12B ; byte
.def RAM_D12A $D12A ; byte


.BANK 0 SLOT 0
.ORG $0000

_START:
	di
	im   1
	ld   sp, $DFF0     ; set stack pointer to offset $DFF0
	ld   a, $00
	ld   ($FFFC), a    ; set up banks
	ld   a, $00
	ld   ($FFFD), a
	inc  a
	ld   ($FFFE), a
	inc  a
	ld   ($FFFF), a
_RST_18H:
	in   a, ($7E)
	cp   $B0
	jr   nz, _RST_18H
	ld   hl, $C001    ; clear work-ram
	ld   de, $C002
	ld   bc, $1FEE
	ld   (hl), $00
	ldir
	ld   a, $01
	ld   (RAM_D12A), a
	ld   a, $02
	ld   (RAM_D12B), a
	jp   _LABEL_476_3

_IRQ_HANDLER:
	di
	push af
	in   a, ($BF)
	rlca
	jp   c, _LABEL_4E2_36
	jp   _LABEL_650_37


; Data from 43 to 65 (35 bytes)
.db $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00
.db $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00
.db $00, $02, $00

_NMI_HANDLER:
	jp   Pause_Handler


; Data from 69 to 328 (704 bytes)
.db $00, $00, $00, $00, $00, $00, $00, $32, $00, $00, $CD, $DA, $21, $3E, $01, $32
.db $D3, $D2, $21, $4C, $3A, $11, $89, $00, $01, $05, $00, $CD, $E3, $1D, $18, $05
.db $45, $52, $52, $4F, $52, $06, $B4, $FB, $CD, $2D, $06, $10, $FA, $C3, $00, $00
.db $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00
.db $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00
.db $00, $00, $00, $00, $00, $00, $00, $4D, $53, $20, $53, $4F, $4E, $49, $43, $A5
.db $43, $48, $41, $4F, $53, $20, $20, $20, $20, $3C, $20, $56, $65, $72, $31, $2E
.db $32, $30, $20, $3E, $20, $20, $20, $31, $39, $39, $33, $2F, $30, $38, $2F, $30
.db $33, $20, $40, $53, $45, $47, $41, $2F, $41, $73, $70, $65, $63, $74, $20, $43
.db $6F, $2E, $2C, $4C, $74, $64, $20, $00, $80, $40, $C0, $20, $A0, $60, $E0, $10
.db $90, $50, $D0, $30, $B0, $70, $F0, $08, $88, $48, $C8, $28, $A8, $68, $E8, $18
.db $98, $58, $D8, $38, $B8, $78, $F8, $04, $84, $44, $C4, $24, $A4, $64, $E4, $14
.db $94, $54, $D4, $34, $B4, $74, $F4, $0C, $8C, $4C, $CC, $2C, $AC, $6C, $EC, $1C
.db $9C, $5C, $DC, $3C, $BC, $7C, $FC, $02, $82, $42, $C2, $22, $A2, $62, $E2, $12
.db $92, $52, $D2, $32, $B2, $72, $F2, $0A, $8A, $4A, $CA, $2A, $AA, $6A, $EA, $1A
.db $9A, $5A, $DA, $3A, $BA, $7A, $FA, $06, $86, $46, $C6, $26, $A6, $66, $E6, $16
.db $96, $56, $D6, $36, $B6, $76, $F6, $0E, $8E, $4E, $CE, $2E, $AE, $6E, $EE, $1E
.db $9E, $5E, $DE, $3E, $BE, $7E, $FE, $01, $81, $41, $C1, $21, $A1, $61, $E1, $11
.db $91, $51, $D1, $31, $B1, $71, $F1, $09, $89, $49, $C9, $29, $A9, $69, $E9, $19
.db $99, $59, $D9, $39, $B9, $79, $F9, $05, $85, $45, $C5, $25, $A5, $65, $E5, $15
.db $95, $55, $D5, $35, $B5, $75, $F5, $0D, $8D, $4D, $CD, $2D, $AD, $6D, $ED, $1D
.db $9D, $5D, $DD, $3D, $BD, $7D, $FD, $03, $83, $43, $C3, $23, $A3, $63, $E3, $13
.db $93, $53, $D3, $33, $B3, $73, $F3, $0B, $8B, $4B, $CB, $2B, $AB, $6B, $EB, $1B
.db $9B, $5B, $DB, $3B, $BB, $7B, $FB, $07, $87, $47, $C7, $27, $A7, $67, $E7, $17
.db $97, $57, $D7, $37, $B7, $77, $F7, $0F, $8F, $4F, $CF, $2F, $AF, $6F, $EF, $1F
.db $9F, $5F, $DF, $3F, $BF, $7F, $FF, $00, $03, $06, $09, $0C, $0F, $12, $15, $19
.db $1C, $1F, $22, $25, $28, $2B, $2E, $31, $34, $36, $39, $3C, $3F, $42, $44, $47
.db $49, $4C, $4F, $51, $53, $56, $58, $5A, $5C, $5F, $61, $63, $65, $67, $68, $6A
.db $6C, $6E, $6F, $71, $72, $73, $75, $76, $77, $78, $79, $7A, $7B, $7C, $7D, $7D
.db $7E, $7E, $7F, $7F, $7F, $7F, $7F, $7F, $7F, $7F, $7F, $7F, $7E, $7E, $7D, $7D
.db $7C, $7B, $7B, $7A, $79, $78, $77, $75, $74, $73, $71, $70, $6E, $6D, $6B, $69
.db $68, $66, $64, $62, $60, $5E, $5B, $59, $57, $55, $52, $50, $4D, $4B, $48, $46
.db $43, $40, $3D, $3B, $38, $35, $32, $2F, $2C, $29, $26, $23, $20, $1D, $1A, $17
.db $14, $11, $0E, $0B, $07, $04, $01, $00, $FF, $FC, $F9, $F5, $F2, $EF, $EC, $E9
.db $E6, $E3, $E0, $DD, $DA, $D7, $D4, $D1, $CE, $CB, $C8, $C5, $C3, $C0, $BD, $BA
.db $B8, $B5, $B3, $B0, $AE, $AB, $A9, $A7, $A5, $A2, $A0, $9E, $9C, $9A, $98, $97
.db $95, $93, $92, $90, $8F, $8D, $8C, $8B, $89, $88, $87, $86, $85, $85, $84, $83
.db $83, $82, $82, $81, $81, $81, $81, $81, $81, $81, $81, $81, $81, $82, $82, $83
.db $83, $84, $85, $86, $87, $88, $89, $8A, $8B, $8D, $8E, $8F, $91, $92, $94, $96
.db $98, $99, $9B, $9D, $9F, $A1, $A4, $A6, $A8, $AA, $AD, $AF, $B1, $B4, $B7, $B9
.db $BC, $BE, $C1, $C4, $C7, $CA, $CC, $CF, $D2, $D5, $D8, $DB, $DE, $E1, $E4, $E7
.db $EB, $EE, $F1, $F4, $F7, $FA, $FD, $00, $00, $00, $00, $00, $00, $00, $00, $00
.db $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00
.db $00, $00, $00, $00, $00, $00, $00, $C3, $CB, $77, $C3, $3D, $5F, $C3, $FD, $6B

_LABEL_329_392:
	jp   FindEmptyObjSlotBadnik


; Data from 32C to 44F (292 bytes)
.db $C3, $9C, $5E, $C3, $65, $60, $C3, $6B, $60, $C3, $7A, $60, $C3, $FB, $60, $C3
.db $28, $63, $C3, $54, $5F, $C3, $25, $77, $C3, $F8, $5E, $C3, $38, $31, $C3, $F0
.db $64, $C3, $A0, $5F, $C3, $84, $5F, $C3, $E3, $59, $C3, $F3, $59, $C3, $C5, $59
.db $C3, $D8, $59, $C3, $17, $5F, $C3, $F5, $64, $C3, $27, $5F, $C3, $05, $26, $C3
.db $85, $28, $C3, $89, $60, $C3, $B7, $5E, $C3, $D3, $1C, $C3, $E1, $18, $C3, $4E
.db $61, $C3, $3C, $61, $C3, $7E, $61, $C3, $A5, $61, $C3, $B1, $61, $C3, $BB, $61
.db $C3, $0B, $69, $C3, $57, $36, $C3, $C6, $3B, $C3, $C6, $36, $C3, $A7, $48, $C3
.db $3C, $46, $C3, $3B, $39, $C3, $ED, $45, $C3, $23, $3A, $C3, $F0, $3B, $C3, $71
.db $3A, $C3, $37, $3A, $C3, $4E, $3B, $C3, $01, $39, $C3, $55, $39, $C3, $59, $37
.db $C3, $13, $37, $C3, $FB, $47, $C3, $7C, $3A, $C3, $C5, $38, $C3, $D1, $38, $C3
.db $1B, $3C, $C3, $FC, $3C, $C3, $AE, $3D, $C3, $4D, $38, $C3, $4F, $04, $C3, $59
.db $3A, $C3, $E6, $39, $C3, $F0, $36, $C3, $6F, $38, $C3, $9A, $38, $C3, $83, $37
.db $C3, $FD, $3E, $C3, $D6, $61, $C3, $04, $31, $C3, $92, $48, $C3, $48, $3A, $C3
.db $68, $61, $C3, $06, $1D, $C3, $9C, $1D, $C3, $EF, $3F, $C3, $B9, $59, $C3, $9B
.db $1C, $C3, $A8, $1C, $C3, $1A, $69, $C3, $3E, $75, $C3, $BC, $48, $C3, $4F, $49
.db $C3, $5E, $71, $C3, $76, $62, $C3, $1A, $40, $C3, $84, $49, $C3, $1F, $6C, $C3
.db $B3, $59, $C3, $D5, $62, $C3, $1A, $63, $C3, $0B, $63, $C3, $F7, $62, $C3, $9B
.db $18, $C3, $6D, $39, $C3, $B6, $39, $C3, $FB, $3B, $C3, $2D, $06, $C3, $02, $4C
.db $C3, $12, $4C, $C9

_LABEL_450_67:
	di
	ld   sp, $DFF0
	call _LABEL_1DB9_17
	ld   hl, $C001
	ld   de, $C002
	ld   bc, $1FEE
	ld   (hl), $00
	ldir
	ld   a, $00
	ld   ($FFFC), a
	ld   a, $00
	ld   ($FFFD), a
	inc  a
	ld   ($FFFE), a
	inc  a
	ld   ($FFFF), a
_LABEL_476_3:
	call _LABEL_1C76_4
	ld   a, $02
	ld   a, $02
	ld   (RAM_D12A), a
	ld   ($FFFE), a
	call _LABEL_83FB_8
	ld   a, $01
	ld   (RAM_D12A), a
	ld   ($FFFE), a
	call _LABEL_1D14_10
	call _LABEL_7AB4_12
	call _LABEL_7A7A_16
	call _LABEL_1DC7_20
	call _LABEL_1DAB_19
	call _LABEL_CF1_21
	ld   hl, $D492
	ld   (hl), $00
	set  7, (hl)
	inc  hl
	ld   (hl), $01
	ld   hl, $D494
	ld   (hl), $00
	set  7, (hl)
	inc  hl
	ld   (hl), $01
	ld   hl, $D292       ; load screen mode into hl
	set  6, (hl)         ; set intro flag
	ld   a, $04
	ld  (RAM_D2D4), a
	call Screen
	call _LABEL_3065_417

; Data from 4C4 to 4E1 (30 bytes)
.db $3E, $04, $32, $D4, $D2, $F3, $CD, $DA, $21, $CD, $7E, $29, $AF, $32, $92, $D2
.db $CD, $00, $2A, $CD, $2D, $06, $21, $93, $D2, $36, $42, $C3, $33, $13

_LABEL_4E2_36:
	ex   af, af'
	push af
	push bc
	push de
	push hl
	exx
	push bc
	push de
	push hl
	push ix
	push iy
	ld   a, (RAM_D131)
	or   a
	jr   z, _LABEL_513_41
	ld   a, (BGPalleteControlByte)
	and  $CF
	jr   nz, _LABEL_513_41
	ld   a, (RAM_D132)
	out  ($BF), a
	ld   a, $8A
	out  ($BF), a
	ld   a, (RAM_D11E)
	or   $10
	ld   (RAM_D11E), a
	out  ($BF), a
	ld   a, $80
	out  ($BF), a
_LABEL_513_41:
	ld   a, (RAM_D44F)
	or   a
	jp   nz, _LABEL_627_42
	ld   a, (RAM_D136)
	or   a
	jp   nz, _LABEL_5C9_43
	call _LABEL_1DB9_17
	ld   bc, $0000
	ld   a, (RAM_D290)
	or   a
	jp   z, _LABEL_53E_44
	dec  a
	ld   (RAM_D290), a
	and  $06
	ld   e, a
	ld   d, $00
	ld   hl, $0648
	add  hl, de
	ld   c, (hl)
	inc  hl
	ld   b, (hl)
_LABEL_53E_44:
	ld   a, (BGXScroll)
	add  a, b
	out  ($BF), a
	ld   a, $88        ; horizontal scroll
	out  ($BF), a
	ld   a, (BGYScroll)
	add  a, c
	out  ($BF), a
	ld   a, $89        ; vertical scroll
	out  ($BF), a
	ld   a, (RAM_D15E)
	bit  6, a
	jr   z, _LABEL_57C_45
	res  6, a
	ld   (RAM_D15E), a
	ld   ix, $D15E
	bit  4, (ix+0)
	call nz, _LABEL_5405_46
	bit  5, (ix+0)
	call nz, _LABEL_5359_52
	ld   hl, (RAM_D284)
	ld   (HorizOffset), hl
	ld   hl, (RAM_D286)
	ld   (VertOffset), hl
_LABEL_57C_45:
	call _LABEL_1E36_56
	ld   a, $1D
	ld   ($FFFF), a
	call _LABEL_7450A_58
	call _LABEL_1DAB_19
	call _LABEL_1CBD_60
	call Read_Input
	call LoadPlayerTiles
	ld   a, (Gamestate)
	bit  0, a
	jr   nz, _LABEL_5C9_43
	ld   a, $0E
	ld   ($FFFF), a
	call _LABEL_3B45A_75
	ld   a, (Gamestate)
	bit  6, a             ; set to intro
	jr   z, _LABEL_5C9_43
	ld   a, (Gamestate)
	bit  1, a             ; set to title card
	jr   nz, _LABEL_5C9_43
	ld   a, (RAM_D131)
	or   a
	jr   nz, _LABEL_5C1_101
	ld   a, $0F
	ld   ($FFFF), a
	call Update_SpriteAtrb
	call _LABEL_1027_122
_LABEL_5C1_101:
	ld   a, $1D
	ld   ($FFFF), a
	call _LABEL_74000_124
_LABEL_5C9_43:
	ld   a, (RAM_D4A4)
	or   a
	jr   z, _LABEL_5D6_127
	ld   (PlaySound), a
	xor  a
	ld   (RAM_D4A4), a
_LABEL_5D6_127:
	ld   a, $02
	ld   ($FFFE), a
	ld   a, $03
	ld   ($FFFF), a
	call _LABEL_8000_128
	ld   a, (RAM_D12D)
	or   a
	jp   nz, _LABEL_5F9_226
	ld   hl, $D4A2
	inc  (hl)
	ld   a, (hl)
	cp   $05
	jp   c, _LABEL_5F9_226
	ld   (hl), $00
	call _LABEL_8000_128
_LABEL_5F9_226:
	ld   a, (RAM_D292)
	or   a
	call nz, Intro_ChkButton
	call Increment_Timer
	ld   hl, $D12F
	inc  (hl)
	ld   a, (RAM_D12A)
	ld   ($FFFE), a
	ld   a, (RAM_D12B)
	ld   ($FFFF), a
	ld   hl, $D135         ; pause timer
	inc  (hl)              ; pause until start button is pressed again
	pop  iy
	pop  ix
	pop  hl
	pop  de
	pop  bc
	exx
	pop  hl
	pop  de
	pop  bc
	pop  af
	ex   af, af'
	pop  af
	ei
	ret

_LABEL_627_42:
	call _LABEL_1CBD_60
	jp   _LABEL_5C9_43

WaitForInterrupt:
	ei
	xor  a
	ld   (RAM_D44F), a
	ld   hl, $D135
_LABEL_635_235:
	ld   a, (hl)
	or   a
	jr   z, _LABEL_635_235
	ld   (hl), $00
	ret

Intro_ChkButton:
	ld   a, (RAM_D157) ; read Joypad_Press
	and  $30           ; has the 1/2 button been pressed?
	ret  z             ; if not return

	ld   hl, $D292      ; screen mode address
	set  7, (hl)        ; set the screen to title screen
	ret                 ; return


; Default Scroll Values
.db $FE, $00, $FE, $FE, $02, $02, $00, $02

_LABEL_650_37:
	push bc
	push hl
	ld   a, (RAM_D132)
	inc  a
	jr   nz, CRam_Setup
	ld   a, (Underwater)
	or   a
	jp   z, _LABEL_683_39
CRam_Setup:
	ld   a, $00      ; set V-Ram up to write to C-Ram
	out  ($BF), a
	ld   a, $C0
	out  ($BF), a
	ld   hl, $0688   ; write colors to V-Ram (deal that's how I spell it xP)
	ld   b, $20
_LABEL_66C_40:
	ld   a, (hl)
	out  ($BE), a
	inc  hl
	djnz _LABEL_66C_40
	ld   a, (RAM_D11E)
	and  $EF
	ld   (RAM_D11E), a
	out  ($BF), a
	ld   a, $80
	out  ($BF), a
	ld   (PaletteUpdate), a
_LABEL_683_39:
	pop  hl
	pop  bc
	pop  af
	ei
	ret


; Colors to write to V-Ram
.db $14, $3F, $00, $3A, $2A, $15, $37, $32, $21, $2C, $28, $20, $30, $34, $38, $3D
.db $10, $24, $39, $2B, $16, $3E, $00, $3F, $27, $11, $25, $3A, $2E, $1A, $25, $1D

Pause_Handler:
	push af
	ld   a, (BGPalleteControlByte)
	and  $DF
	jr   nz, _LABEL_6C4_421
	ld   a, (RAM_D292)    ; check to see if the start button is pressed
	or   a
	jr   nz, _LABEL_6C4_421
	ld   a, (Gamestate)
	and  $FE
	cp   $40
	jr   nz, _LABEL_6C4_421
	ld   a, $01
	ld   (RAM_D12E), a
_LABEL_6C4_421:            
	pop  af
	retn

_LABEL_6C7_411:
	di
	call _LABEL_21C8_412

; Data from 6CB to 718 (78 bytes)
.db $3E, $07, $32, $97, $D2, $AF, $32, $98, $D2, $CD, $7E, $29, $CD, $E1, $78, $DD
.db $21, $5E, $D1, $CD, $CE, $4F, $CD, $DC, $4F, $CD, $AD, $4D, $CD, $4F, $2A, $3E
.db $01, $32, $00, $D5, $CD, $9B, $18, $CD, $4F, $79, $CD, $B3, $59, $3E, $40, $32
.db $93, $D2, $01, $1E, $00, $CD, $B8, $07, $01, $C4, $02, $CD, $9F, $07, $AF, $32
.db $93, $D2, $CD, $AF, $1C, $06, $1E, $FB, $CD, $2D, $06, $10, $FA, $C9

_LABEL_719_407:
	di
	call ClearWorkingVRAM
	call _LABEL_21DA_33
	call _LABEL_2F49_408

; Data from 723 to 7CD (171 bytes)
.db $3E, $40, $32, $93, $D2, $21, $92, $D4, $36, $00, $CB, $FE, $23, $36, $1B, $21
.db $94, $D4, $36, $00, $CB, $FE, $23, $36, $1C, $06, $18, $FB, $CD, $2D, $06, $10
.db $FA, $3E, $BE, $32, $04, $DE, $CD, $77, $2F, $06, $0C, $FB, $CD, $2D, $06, $10
.db $FA, $3E, $99, $32, $04, $DE, $AF, $32, $2F, $D1, $01, $1E, $00, $CD, $B8, $07
.db $01, $74, $04, $CD, $9F, $07, $CD, $99, $0C, $CD, $D1, $0C, $AF, $32, $93, $D2
.db $C9, $CD, $81, $0C, $CD, $B9, $0C, $3E, $1B, $CD, $6F, $1C, $3A, $2F, $D1, $11
.db $D0, $BC, $E6, $20, $28, $03, $11, $F4, $BC, $21, $4E, $3D, $01, $12, $01, $CD
.db $49, $23, $C9, $21, $92, $D2, $CB, $7E, $C8, $F1, $F1, $C9, $C5, $CD, $2D, $06
.db $CD, $96, $07, $CD, $B8, $16, $3A, $92, $D2, $CB, $67, $C4, $74, $07, $C1, $0B
.db $78, $B1, $20, $E8, $C9, $C5, $CD, $2D, $06, $CD, $B8, $16, $3A, $92, $D2, $CB
.db $67, $C4, $74, $07, $C1, $0B, $78, $B1, $20, $EB, $C9

_LABEL_7CE_415:
	xor  a
	ld   (CurrentLevel), a
	ld   (CurrentAct), a
	ld   hl, $D2CE
	bit  0, (hl)
	ret  z

	di
	call _LABEL_7979_414

; Data from 7DF to ACF (753 bytes)
.db $CD, $CE, $4F, $CD, $7E, $29, $CD, $DA, $21, $11, $D8, $08, $21, $08, $38, $01
.db $18, $15, $3E, $01, $32, $D3, $D2, $CD, $83, $23, $21, $92, $D4, $36, $00, $CB
.db $FE, $23, $36, $02, $21, $94, $D4, $36, $00, $CB, $FE, $23, $36, $02, $FB, $AF
.db $32, $C9, $D2, $CD, $5A, $08, $3A, $C9, $D2, $87, $5F, $16, $00, $21, $2A, $08
.db $19, $7E, $32, $97, $D2, $23, $7E, $32, $98, $D2, $C9, $00, $00, $00, $01, $00
.db $02, $01, $00, $01, $01, $01, $02, $02, $00, $02, $01, $02, $02, $03, $00, $03
.db $01, $03, $02, $04, $00, $04, $01, $04, $02, $05, $00, $05, $01, $05, $02, $08
.db $00, $09, $00, $0A, $00, $0B, $00, $0C, $01, $00, $00, $CD, $2D, $06, $CD, $70
.db $08, $CD, $B7, $08, $3A, $47, $D1, $CB, $6F, $28, $F0, $3E, $FF, $32, $95, $D2
.db $C9, $3A, $47, $D1, $CB, $47, $20, $2B, $CB, $4F, $20, $31, $3A, $37, $D1, $E6
.db $03, $28, $1B, $3A, $46, $D4, $3C, $32, $46, $D4, $FE, $28, $D8, $3E, $26, $32
.db $46, $D4, $3A, $37, $D1, $CB, $47, $20, $0A, $CB, $4F, $20, $10, $C9, $AF, $32
.db $46, $D4, $C9, $3A, $C9, $D2, $B7, $C8, $3D, $32, $C9, $D2, $C9, $3A, $C9, $D2
.db $FE, $11, $D0, $3C, $32, $C9, $D2, $C9, $3A, $C9, $D2, $6F, $26, $00, $29, $29
.db $29, $29, $29, $29, $11, $B8, $38, $19, $11, $D1, $08, $01, $01, $03, $CD, $49
.db $23, $C9, $20, $01, $3C, $01, $20, $01, $C9, $20, $20, $20, $20, $2D, $20, $5A
.db $4F, $4E, $45, $20, $53, $45, $4C, $45, $43, $54, $20, $2D, $20, $20, $20, $20
.db $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20
.db $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20
.db $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20
.db $20, $54, $55, $52, $51, $55, $4F, $49, $53, $45, $20, $48, $49, $4C, $4C, $20
.db $20, $20, $20, $20, $41, $43, $54, $2D, $31, $20, $20, $20, $20, $20, $20, $20
.db $20, $20, $20, $20, $20, $20, $5A, $4F, $4E, $45, $20, $20, $41, $43, $54, $2D
.db $32, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20
.db $20, $20, $20, $20, $41, $43, $54, $2D, $33, $47, $49, $47, $41, $4C, $4F, $50
.db $4F, $4C, $49, $53, $20, $20, $20, $20, $20, $20, $20, $20, $41, $43, $54, $2D
.db $31, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $5A, $4F  ; Zone Select Text
.db $4E, $45, $20, $20, $41, $43, $54, $2D, $32, $20, $20, $20, $20, $20, $20, $20  ; starts here
.db $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $41, $43, $54, $2D
.db $33, $53, $4C, $45, $45, $50, $49, $4E, $47, $20, $45, $47, $47, $20, $20, $20
.db $20, $20, $20, $20, $41, $43, $54, $2D, $31, $20, $20, $20, $20, $20, $20, $20
.db $20, $20, $20, $20, $20, $20, $5A, $4F, $4E, $45, $20, $20, $41, $43, $54, $2D
.db $32, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20
.db $20, $20, $20, $20, $41, $43, $54, $2D, $33, $4D, $45, $43, $48, $41, $20, $47
.db $52, $45, $45, $4E, $20, $48, $49, $4C, $4C, $20, $20, $20, $41, $43, $54, $2D
.db $31, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $5A, $4F
.db $4E, $45, $20, $20, $41, $43, $54, $2D, $32, $20, $20, $20, $20, $20, $20, $20
.db $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $41, $43, $54, $2D
.db $33, $41, $51, $55, $41, $20, $50, $4C, $41, $4E, $45, $54, $20, $20, $20, $20
.db $20, $20, $20, $20, $41, $43, $54, $2D, $31, $20, $20, $20, $20, $20, $20, $20
.db $20, $20, $20, $20, $20, $20, $5A, $4F, $4E, $45, $20, $20, $41, $43, $54, $2D
.db $32, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20
.db $20, $20, $20, $20, $41, $43, $54, $2D, $33, $45, $4C, $45, $43, $54, $52, $49
.db $43, $20, $45, $47, $47, $20, $20, $20, $20, $20, $20, $20, $41, $43, $54, $2D
.db $31, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $5A, $4F
.db $4E, $45, $20, $20, $41, $43, $54, $2D, $32, $20, $20, $20, $20, $20, $20, $20
.db $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $20, $41, $43, $54, $2D
.db $33

_LABEL_AD0_413:
	ld   hl, $D2CE
	bit  1, (hl)
	ret  z

	di
	call _LABEL_7979_414

; Data from ADA to CF0 (535 bytes)
.db $CD, $CE, $4F, $CD, $7E, $29, $CD, $DA, $21, $3E, $01, $32, $D3, $D2, $21, $14
.db $39, $11, $F6, $0A, $01, $0E, $00, $CD, $E3, $1D, $18, $0E, $2D, $20, $53, $4F
.db $55, $4E, $44, $20, $54, $45, $53, $54, $20, $2D, $3E, $01, $32, $D3, $D2, $21
.db $10, $3A, $11, $17, $0B, $01, $0A, $00, $CD, $E3, $1D, $18, $0A, $53, $4F, $55
.db $4E, $44, $20, $43, $4F, $44, $45, $21, $92, $D4, $36, $00, $CB, $FE, $23, $36
.db $02, $21, $94, $D4, $36, $00, $CB, $FE, $23, $36, $29, $FB, $3E, $80, $32, $BF
.db $D2, $F3, $3E, $08, $CD, $6F, $1C, $21, $00, $02, $CD, $50, $1D, $21, $40, $B3
.db $AF, $CD, $C2, $24, $FB, $3E, $01, $32, $00, $D5, $3E, $36, $32, $01, $D5, $32
.db $02, $D5, $21, $40, $00, $22, $11, $D5, $21, $90, $00, $22, $14, $D5, $21, $93
.db $D2, $CB, $F6, $CD, $2D, $06, $CD, $1D, $36, $CD, $D1, $5D, $CD, $70, $08, $3A
.db $C9, $D2, $3C, $32, $C9, $D2, $3A, $47, $D1, $E6, $03, $C2, $97, $0B, $3A, $C9
.db $D2, $E6, $07, $C2, $D3, $0B, $3A, $37, $D1, $E6, $07, $28, $3C, $06, $01, $E6
.db $01, $28, $02, $06, $FF, $3A, $37, $D1, $E6, $10, $28, $0E, $3A, $47, $D1, $E6
.db $03, $CA, $B4, $0B, $78, $87, $87, $87, $87, $47, $3A, $BF, $D2, $80, $F6, $80
.db $FE, $FF, $CA, $CC, $0B, $FE, $C5, $DA, $CC, $0B, $FE, $C5, $3E, $FF, $28, $02
.db $3E, $C4, $32, $BF, $D2, $AF, $32, $C9, $D2, $3E, $01, $32, $D3, $D2, $21, $2C
.db $3A, $11, $E6, $0B, $01, $01, $00, $CD, $E3, $1D, $18, $01, $30, $3E, $01, $32
.db $D3, $D2, $21, $32, $3A, $11, $FA, $0B, $01, $01, $00, $CD, $E3, $1D, $18, $01
.db $48, $3A, $BF, $D2, $3C, $CA, $12, $0C, $3D, $47, $3E, $01, $32, $D3, $D2, $21
.db $2E, $3A, $CD, $50, $0C, $C3, $29, $0C, $3E, $01, $32, $D3, $D2, $21, $2C, $3A
.db $11, $25, $0C, $01, $04, $00, $CD, $E3, $1D, $18, $04, $45, $58, $49, $54, $3A
.db $47, $D1, $E6, $20, $28, $06, $3A, $BF, $D2, $32, $04, $DE, $3C, $C2, $6D, $0B
.db $21, $93, $D2, $CB, $B6, $3E, $FF, $32, $00, $D5, $CD, $AF, $1C, $06, $2A, $FB
.db $CD, $2D, $06, $10, $FA, $C9, $F3, $CD, $50, $1D, $78, $0F, $0F, $0F, $0F, $E6
.db $0F, $F6, $F0, $27, $C6, $A0, $CE, $40, $D3, $BE, $3A, $D3, $D2, $00, $00, $00
.db $D3, $BE, $78, $E6, $0F, $F6, $F0, $27, $C6, $A0, $CE, $40, $D3, $BE, $3A, $D3
.db $D2, $00, $00, $00, $D3, $BE, $C9, $3A, $47, $D1, $E6, $0F, $C8, $2A, $CF, $D2
.db $BE, $20, $05, $23, $22, $CF, $D2, $C9, $21, $14, $0D, $22, $CF, $D2, $C9, $2A
.db $CF, $D2, $7E, $FE, $FF, $C0, $21, $00, $00, $22, $CF, $D2, $21, $CE, $D2, $CB
.db $C6, $3E, $A9, $32, $04, $DE, $06, $1E, $FB, $CD, $2D, $06, $10, $FA, $C9, $3A
.db $47, $D1, $E6, $0F, $C8, $2A, $D1, $D2, $BE, $20, $05, $23, $22, $D1, $D2, $C9
.db $21, $14, $0D, $22, $D1, $D2, $C9, $2A, $D1, $D2, $7E, $FE, $FF, $C0, $21, $00
.db $00, $22, $D1, $D2, $21, $CE, $D2, $CB, $CE, $3E, $A9, $32, $04, $DE, $06, $1E
.db $FB, $CD, $2D, $06, $10, $FA, $C9

_LABEL_CF1_21:
	xor  a
	ld   (RAM_D2CE), a
_LABEL_CF5_410:
	ld   hl, $0D02
	ld   (RAM_D2CF), hl
	ld   hl, $0D0B
	ld   (RAM_D2D1), hl
	ret


; Data from D02 to D14 (19 bytes)
.db $01, $01, $02, $02, $08, $04, $08, $04, $FF, $02, $02, $01, $01, $04, $08, $04
.db $08, $FF, $00

LoadPlayerTiles:
	ld   a, (RAM_D34E)
	and  $A0
	cp   $A0
	ret  nz

	ld   a, (RAM_D34F)
	or   a
	jp   z, ClearPlayerTiles
	ld   l, a
	ld   h, $00
	add  hl, hl
	add  hl, hl
	ld   de, $104B
	ld   a, (RAM_D500)
	dec  a
	jr   z, _LABEL_D35_70
	ld   de, $11CF
_LABEL_D35_70:
	add  hl, de
	ld   a, $1F
	ld   ($FFFF), a
	ld   a, (hl)
	inc  hl
	ld   e, (hl)
	inc  hl
	ld   d, (hl)
	inc  hl
	ld   b, (hl)
	ld   ($FFFF), a
	ld   a, (RAM_D34E)
	bit  6, a
	jp   nz, _LABEL_EA1_71
	ld   a, $00
	out  ($BF), a
	ld   a, $00
	or   $40
	out  ($BF), a
_LABEL_D57_72:
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	ld   a, (de)
	out  ($BE), a
	inc  de
	nop
	dec  b
	jp   nz, _LABEL_D57_72
	ld   hl, $D34E
	res  7, (hl)
	ret

_LABEL_EA1_71:
	ld   a, $00
	out  ($BF), a
	ld   a, $00
	or   $40
	out  ($BF), a
	ex   de, hl
	ld   d, $01
_LABEL_EAE_73:
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	dec  b
	jp   nz, _LABEL_EAE_73
	xor  a
	ld   (RAM_D34E), a
	ret

ClearPlayerTiles:
	ld   a, $00
	out  ($BF), a
	ld   a, $00
	or   $40
	out  ($BF), a
	xor  a
	ld   b, $20
_LABEL_1004_74:
	out  ($BE), a
	out  ($BE), a
	out  ($BE), a
	out  ($BE), a
	out  ($BE), a
	out  ($BE), a
	out  ($BE), a
	out  ($BE), a
	out  ($BE), a
	out  ($BE), a
	out  ($BE), a
	out  ($BE), a
	out  ($BE), a
	out  ($BE), a
	out  ($BE), a
	out  ($BE), a
	djnz _LABEL_1004_74
	ret

_LABEL_1027_122:
	ld   hl, $D34E
	ld   a, (RAM_D504)
	rlca
	rlca
	and  $40
	or   $20
	ld   (hl), a
	ld   a, (RAM_D350)
	cp   (hl)
	jr   z, _LABEL_1040_123
	ld   a, (hl)
	ld   (RAM_D350), a
	set  7, (hl)
_LABEL_1040_123:
	ld   a, (RAM_D34F)
	ld   b, a
	ld   a, (RAM_D506)
	cp   b
	ret  z

	ld   (RAM_D34F), a
	set  7, (hl)
	ret


; Data from 104F to 16B7 (1641 bytes)
.incbin "SonicChaos.sms.dat.4"

Engine_UpdateLevelState:
	ld   a, (RAM_D131)
	or   a
	jp   nz, _LABEL_16EF_297
	ld   ix, $D15E
	bit  6, (ix+0)
	jp   nz, _LABEL_16EA_298
	call _LABEL_4C90_299
	call _LABEL_361D_332
	call _LABEL_5DD1_363
	call _LABEL_7AC2_371
	ld   a, (RAM_D2E2)
	cp   $04
	jp   c, _LABEL_16EA_298
	xor  a
	ld   (RAM_D2E2), a
	ld   a, $1C
	call SwapFrame2
	call _LABEL_70000_386
_LABEL_16EA_298:
	ld   hl, $D2E2
	inc  (hl)
	ret

_LABEL_16EF_297:
	ld   ix, $D15E
	bit  6, (ix+0)
	jp   nz, _LABEL_173A_398
	call _LABEL_4C90_299
	ld   a, $FF
	ld   (RAM_D44F), a
	call _LABEL_361D_332
	xor  a
	ld   (RAM_D44F), a
	call _LABEL_5DD1_363
	ld   a, $FF
	ld   (RAM_D44F), a
	ld   a, $0F
	ld   (RAM_D12B), a
	ld   ($FFFF), a
	call Update_SpriteAtrb

; Data from 171C to 1739 (30 bytes)
.db $CD, $27, $10, $AF, $32, $4F, $D4, $CD, $C2, $7A, $3A, $E2, $D2, $FE, $04, $DA
.db $3A, $17, $AF, $32, $E2, $D2, $3E, $1C, $CD, $6F, $1C, $CD, $00, $80

_LABEL_173A_398:
	ld   hl, $D2E2
	inc  (hl)
	ret


; Data from 173F to 1752 (20 bytes)
.db $3A, $2E, $D1, $B7, $C8, $AF, $32, $2E, $D1, $3E, $80, $32, $08, $DE, $21, $93
.db $D2, $CB, $C6, $C9

_LABEL_1753_362:
	xor  a
	ld   (RAM_D2BE), a
	ret


; Data from 1758 to 178E (55 bytes)
.db $3E, $FF, $32, $BE, $D2, $AF, $32, $C2, $D2, $C9, $07, $DA, $3F, $18, $07, $DA
.db $15, $18, $07, $07, $DA, $B0, $17, $3A, $93, $D2, $07, $07, $07, $DA, $AE, $14
.db $07, $DA, $43, $15, $07, $07, $DA, $F2, $15, $07, $07, $DA, $96, $16, $CD, $B8
.db $16, $CD, $3F, $17, $C3, $33, $13

LoadSpecialStage:
	ld   a, (RAM_D2C8); check to see if the player is tails
	dec  a
	ret  nz           ; if so, skip over this

	ld   a, (CurrentLevel)
	cp   $06
	ret  nc

	ld   a, (RAM_D2CC)
	and  $1F
	cp   $1F
	ret  z

	call _LABEL_1753_362
	ld   a, $88          ; set Special Stage flag
	ld   (Screenmode), a
	ld   a, $01          ; set Special Stage results card
	ld   (RAM_D2CD), a
	ret


; Data from 17B0 to 189A (235 bytes)
.db $3E, $8A, $32, $04, $DE, $06, $1E, $FB, $CD, $2D, $06, $10, $FA, $AF, $32, $31
.db $D1, $CD, $EB, $1C, $21, $92, $D4, $36, $00, $CB, $F6, $CB, $E6, $21, $94, $D4
.db $36, $00, $CB, $F6, $CB, $E6, $06, $96, $FB, $CD, $2D, $06, $10, $FA, $F3, $CD
.db $7B, $18, $CD, $CE, $4F, $CD, $34, $29, $CD, $16, $31, $CD, $4A, $31, $21, $59
.db $00, $22, $BF, $D2, $CD, $5C, $28, $CD, $9B, $18, $CD, $4F, $79, $21, $92, $D4
.db $CB, $E6, $21, $94, $D4, $CB, $E6, $CD, $B3, $59, $CD, $58, $17, $21, $94, $D2
.db $CB, $9E, $C3, $33, $13, $CD, $53, $17, $DD, $21, $00, $D5, $CD, $84, $49, $CD
.db $E1, $18, $21, $92, $D4, $36, $00, $CB, $F6, $CB, $E6, $21, $94, $D4, $36, $00
.db $CB, $F6, $CB, $E6, $06, $1E, $FB, $CD, $2D, $06, $10, $FA, $C3, $69, $18, $CD
.db $53, $17, $3E, $8A, $32, $04, $DE, $06, $1E, $FB, $CD, $2D, $06, $10, $FA, $21
.db $92, $D4, $36, $00, $CB, $F6, $CB, $E6, $21, $94, $D4, $36, $00, $CB, $F6, $CB
.db $E6, $06, $78, $FB, $CD, $2D, $06, $10, $FA, $AF, $32, $94, $D2, $3A, $96, $D2
.db $32, $97, $D2, $21, $93, $D2, $CB, $EE, $C3, $33, $13, $3A, $97, $D2, $32, $96
.db $D2, $06, $08, $3A, $CC, $D2, $0F, $30, $0D, $04, $0F, $30, $09, $04, $0F, $30
.db $05, $04, $0F, $30, $01, $04, $78, $32, $97, $D2, $C9

UpdateMusic:
	ld   a, (RAM_D4A3)
	or   a
	ret  nz

	ld   a, (CurrentLevel)
	ld   b, a
	add  a, a
	add  a, b
	ld   b, a
	ld   a, (CurrentAct)
	add  a, b
	ld   l, a
	ld   h, $00
	ld   de, $18BA
	add  hl, de
	ld   a, (hl)
	ld   (PlaySound), a
	ld   (RAM_D4A4), a
	ret


; Music ID's
.db $81, $81, $81   ; THZ
.db $83, $83, $83   ; GZ
.db $91, $91, $91   ; SEZ
.db $92, $92, $92   ; MGHZ
.db $93, $93, $93   ; APZ
.db $95, $95  $90   ; EEZ
.db $8F, $8F, $8F   ; $8F Special Stage 2
.db $90, $90, $90   ; Intro
.db $8F, $8F, $8F
.db $8F, $8F, $8F
.db $8F, $8F, $8F
.db $8F  $8F, $8F
.db $8F, $8F, $8F

_LABEL_18E1_402:
	ld   hl, $DE09
	ld   (hl), $0C
	inc  hl
	ld   (hl), $01
	inc  hl
	ld   (hl), $02
	ret


; Data from 18ED to 1C6E (898 bytes)
.db $3A, $C8, $D2, $3D, $C2, $CD, $1A, $3A, $CC, $D2, $E6, $3F, $FE, $3F, $C2, $41
.db $1A, $F3, $11, $60, $10, $CD, $DD, $21, $CD, $E0, $30, $F3, $3E, $09, $CD, $6F
.db $1C, $21, $00, $02, $CD, $50, $1D, $21, $90, $BD, $AF, $CD, $C2, $24, $FB, $CD
.db $5E, $1B, $3E, $01, $32, $00, $D5, $3E, $31, $32, $01, $D5, $32, $02, $D5, $3E
.db $10, $32, $04, $D5, $21, $80, $00, $22, $11, $D5, $21, $76, $00, $22, $14, $D5
.db $3E, $22, $32, $00, $D7, $3E, $8D, $32, $04, $DE, $21, $92, $D4, $36, $00, $CB
.db $FE, $23, $36, $2A, $01, $DC, $05, $CD, $26, $1A, $21, $92, $D4, $CB, $EE, $23
.db $36, $2B, $01, $DC, $05, $CD, $26, $1A, $21, $92, $D4, $CB, $EE, $23, $36, $2C
.db $01, $DC, $05, $CD, $26, $1A, $21, $92, $D4, $CB, $EE, $23, $36, $2D, $01, $DC
.db $05, $CD, $26, $1A, $21, $92, $D4, $CB, $EE, $23, $36, $2E, $01, $DC, $05, $CD
.db $26, $1A, $21, $92, $D4, $CB, $EE, $23, $36, $2F, $01, $B8, $0B, $CD, $26, $1A
.db $3A, $C1, $D3, $3C, $C2, $47, $19, $CD, $AF, $1C, $CD, $E1, $18, $06, $3C, $FB
.db $CD, $2D, $06, $10, $FA, $11, $60, $10, $CD, $DD, $21, $3E, $FF, $32, $00, $D5
.db $32, $00, $D7, $11, $C0, $00, $CD, $DD, $21, $F3, $3E, $0E, $CD, $6F, $1C, $21
.db $00, $02, $CD, $50, $1D, $21, $3A, $B2, $AF, $CD, $C2, $24, $FB, $3E, $15, $32
.db $40, $D7, $3E, $00, $32, $7F, $D7, $3E, $15, $32, $80, $D7, $3E, $01, $32, $BF
.db $D7, $3E, $15, $32, $C0, $D7, $3E, $02, $32, $FF, $D7, $3E, $15, $32, $00, $D8
.db $3E, $03, $32, $3F, $D8, $21, $92, $D4, $36, $00, $CB, $FE, $23, $36, $2A, $21
.db $94, $D4, $36, $00, $CB, $FE, $23, $36, $29, $CD, $2D, $06, $CD, $D1, $5D, $3A
.db $66, $D7, $3C, $28, $03, $C3, $16, $1A, $C9, $C5, $CD, $2D, $06, $CD, $1D, $36
.db $CD, $D1, $5D, $CD, $88, $1B, $C1, $3A, $C1, $D3, $3C, $28, $06, $0B, $78, $B1
.db $C2, $26, $1A, $C9, $F3, $11, $C0, $00, $CD, $DD, $21, $3E, $09, $CD, $6F, $1C
.db $21, $00, $02, $CD, $50, $1D, $21, $00, $B6, $AF, $CD, $C2, $24, $FB, $3E, $01
.db $32, $00, $D5, $3E, $33, $32, $01, $D5, $32, $02, $D5, $21, $40, $00, $22, $11
.db $D5, $21, $90, $00, $22, $14, $D5, $3E, $1F, $32, $00, $D7, $21, $90, $00, $22
.db $11, $D7, $21, $58, $00, $22, $14, $D7, $3E, $01, $32, $3F, $D7, $21, $92, $D4
.db $36, $00, $CB, $FE, $23, $36, $2A, $21, $94, $D4, $36, $00, $CB, $FE, $23, $36
.db $29, $3E, $9A, $32, $04, $DE, $CD, $2D, $06, $CD, $1D, $36, $CD, $D1, $5D, $3A
.db $00, $D5, $3D, $CA, $A3, $1A, $06, $3C, $FB, $CD, $2D, $06, $10, $FA, $CD, $AF
.db $1C, $CD, $E1, $18, $06, $78, $FB, $CD, $2D, $06, $10, $FA, $CD, $D3, $34, $C9
.db $F3, $11, $60, $10, $CD, $DD, $21, $CD, $65, $7A, $3E, $0E, $CD, $6F, $1C, $21
.db $00, $02, $CD, $50, $1D, $21, $DA, $AB, $AF, $CD, $C2, $24, $FB, $CD, $5E, $1B
.db $3E, $02, $32, $00, $D5, $3E, $31, $32, $01, $D5, $32, $02, $D5, $3E, $10, $32
.db $04, $D5, $21, $80, $00, $22, $11, $D5, $21, $76, $00, $22, $14, $D5, $3E, $16
.db $32, $00, $D7, $21, $80, $00, $22, $11, $D7, $21, $00, $00, $22, $14, $D7, $3E
.db $10, $32, $08, $D7, $21, $92, $D4, $36, $00, $CB, $FE, $23, $36, $2A, $21, $94
.db $D4, $36, $00, $CB, $FE, $23, $36, $29, $3E, $8D, $32, $04, $DE, $CD, $2D, $06
.db $CD, $1D, $36, $CD, $D1, $5D, $CD, $88, $1B, $3A, $00, $D5, $3D, $3D, $CA, $3A
.db $1B, $06, $78, $FB, $CD, $2D, $06, $3A, $37, $D1, $E6, $B0, $20, $02, $10, $F3
.db $C9, $FD, $21, $00, $D8, $FD, $36, $35, $B0, $FD, $36, $34, $F0, $AF, $FD, $77
.db $00, $FD, $77, $24, $FD, $77, $38, $FD, $77, $39, $FD, $36, $1A, $0B, $FD, $36
.db $1E, $1F, $FD, $36, $1F, $04, $FD, $36, $2C, $00, $C9, $3E, $1A, $CD, $6F, $1C
.db $FD, $21, $00, $D8, $FD, $7E, $39, $B7, $C0, $FD, $7E, $38, $B7, $28, $04, $FD
.db $35, $38, $C9, $FD, $66, $35, $FD, $6E, $34, $7E, $32, $10, $D1, $B7, $20, $15
.db $06, $20, $3A, $2D, $D1, $B7, $28, $02, $06, $4C, $FD, $70, $38, $FD, $36, $24
.db $00, $CD, $28, $1C, $C9, $FE, $02, $20, $08, $FD, $36, $2C, $FF, $CD, $28, $1C
.db $C9, $FE, $01, $20, $08, $FD, $36, $24, $01, $CD, $28, $1C, $C9, $FE, $FF, $20
.db $0A, $FD, $36, $39, $FF, $3E, $FF, $32, $C1, $D3, $C9, $21, $00, $3D, $FD, $7E
.db $24, $B7, $28, $03, $21, $00, $3C, $16, $00, $FD, $7E, $1E, $87, $5F, $19, $FD
.db $7E, $2C, $B7, $28, $02, $2B, $2B, $3A, $10, $D1, $CD, $36, $1C, $FD, $35, $1E
.db $FD, $7E, $1E, $FD, $BE, $1F, $C0, $FD, $36, $1E, $1F, $FD, $34, $1F, $FD, $34
.db $1F, $CD, $28, $1C, $FD, $35, $1A, $C0, $C3, $77, $1B, $FD, $66, $35, $FD, $6E
.db $34, $23, $FD, $74, $35, $FD, $75, $34, $C9, $22, $1C, $D1, $D6, $20, $21, $70
.db $B0, $87, $16, $00, $5F, $19, $5E, $23, $56, $FD, $7E, $24, $B7, $28, $05, $21
.db $04, $02, $19, $EB, $01, $02, $03, $2A, $1C, $D1, $F3, $CD, $49, $23, $FB, $2A
.db $1C, $D1, $11, $04, $00, $19, $01, $02, $03, $11, $E5, $B4, $F3, $CD, $49, $23
.db $FB, $C9

SwapFrame2:
	ld   (RAM_D12B), a
	ld   ($FFFF), a
	ret

_LABEL_1C76_4:
	ld   bc, $0A96
	in   a, ($BF)
_LABEL_1C7B_5:
	in   a, ($BF)
	and  a
	jp   p, _LABEL_1C7B_5
_LABEL_1C81_6:
	dec  bc
	ld   a, c
	or   b
	jp   nz, _LABEL_1C81_6
	in   a, ($BF)
	and  a
	ld   a, $01
	jp   m, _LABEL_1C90_7
	dec  a
_LABEL_1C90_7:
	ld   (RAM_D12D), a
	or   a
	ret  nz

	ld   a, $80
	ld   (RAM_DE91), a
	ret


; Data from 1C9B to 1CAE (20 bytes)
.db $3A, $92, $D4, $E6, $CF, $C0, $06, $36, $0E, $00, $C3, $38, $1D, $06, $26, $0E
.db $00, $C3, $38, $1D

_LABEL_1CAF_404:
	ld   hl, $D492
	ld   (hl), $00
	set  6, (hl)    ; set background fade to black flag
	inc  hl
	inc  hl
	ld   (hl), $00
	set  6, (hl)   ; set foreground fade to black flag
	ret

_LABEL_1CBD_60:
	ld   a, (PaletteUpdate)
	or   a
	ret  z

	ld   hl, Copy_CRAM    ; C-Ram copy
	ld   de, $C000
	ld   bc, $0020
	call _LABEL_1D9C_61
	xor  a
	ld   (PaletteUpdate), a
	ret


; Data from 1CD3 to 1CEA (24 bytes)
.db $FD, $21, $52, $D4, $06, $04, $11, $08, $00, $FD, $7E, $00, $B7, $28, $05, $FD
.db $19, $10, $F6, $C9, $FD, $71, $00, $C9

_LABEL_1CEB_401:
	xor  a
	ld   (RAM_D452), a
	ld   (RAM_D45A), a
	ld   (RAM_D462), a
	ld   (RAM_D46A), a
	ld   hl, $0000
	ld   (RAM_D39B), hl
	xor  a
	ld   (RAM_D131), a
	ld   (RAM_D132), a
	ret


; Data from 1D06 to 1D13 (14 bytes)
.db $AF, $FD, $77, $00, $FD, $77, $01, $FD, $77, $02, $FD, $77, $03, $C9

_LABEL_1D14_10:
	in   a, ($BF)
	ld   b, $0B
	ld   c, $80
	ld   de, $D11E
	ld   hl, $1D2D
_LABEL_1D20_11:
	ld   a, (hl)
	out  ($BF), a
	ld   (de), a
	ld   a, c
	out  ($BF), a
	inc  c
	inc  de
	inc  hl
	djnz _LABEL_1D20_11
	ret


; Data from 1D2D to 1D4F (35 bytes)
.db $26, $82, $FF, $FF, $FF, $FF, $FB, $00, $00, $00, $FF, $C5, $E5, $78, $D3, $BF
.db $79, $F6, $80, $D3, $BF, $78, $06, $00, $21, $1E, $D1, $09, $77, $E1, $C1, $C9
.db $DB, $BF, $C9

_LABEL_1D50_14:
	push af
	ld   a, l
	out  ($BF), a
	ld   a, h
	or   $40
	out  ($BF), a
	pop  af
	ret


; Data from 1D5B to 1D89 (47 bytes)
.db $7D, $D3, $BF, $7C, $E6, $3F, $D3, $BF, $F5, $F1, $C9, $F5, $CD, $50, $1D, $F1
.db $D3, $BE, $C9, $CD, $5B, $1D, $DB, $BE, $C9, $D5, $F5, $CD, $50, $1D, $F1, $57
.db $7A, $D3, $BE, $F5, $F1, $DB, $BE, $0B, $78, $B1, $C2, $7B, $1D, $D1, $C9

_LABEL_1D8A_13:
	call _LABEL_1D50_14
_LABEL_1D8D_15:
	ld   a, e
	out  ($BE), a
	push af
	pop  af
	ld   a, d
	out  ($BE), a
	dec  bc
	ld   a, b
	or   c
	jp   nz, _LABEL_1D8D_15
	ret

_LABEL_1D9C_61:
	ex   de, hl
	call _LABEL_1D50_14
_LABEL_1DA0_62:
	ld   a, (de)
	out  ($BE), a
	inc  de
	dec  bc
	ld   a, b
	or   c
	jp   nz, _LABEL_1DA0_62
	ret

_LABEL_1DAB_19:
	ld   hl, $D11F
	ld   a, (hl)
	or   $40
	ld   (hl), a
	out  ($BF), a
	ld   a, $81
	out  ($BF), a
	ret

_LABEL_1DB9_17:
	ld   hl, $D11F
	ld   a, (hl)
	and  $BF
	ld   (hl), a
	out  ($BF), a
	ld   a, $81
	out  ($BF), a
	ret

_LABEL_1DC7_20:
	ld   hl, $D11F
	ld   a, (hl)
	or   $20
	ld   (hl), a
	out  ($BF), a
	ld   a, $81
	out  ($BF), a
	ret


; Data from 1DD5 to 1E35 (97 bytes)
.db $21, $1F, $D1, $7E, $E6, $DF, $77, $D3, $BF, $3E, $81, $D3, $BF, $C9, $F3, $CD
.db $50, $1D, $D5, $C5, $1A, $D3, $BE, $3A, $D3, $D2, $00, $00, $00, $D3, $BE, $13
.db $0B, $79, $B0, $20, $EF, $C1, $D1, $C9, $D5, $C5, $3A, $92, $D2, $CB, $7F, $20
.db $2D, $F3, $CD, $50, $1D, $1A, $D3, $BE, $3A, $D3, $D2, $00, $00, $00, $D3, $BE
.db $FB, $C5, $D5, $E5, $06, $06, $FB, $CD, $2D, $06, $3A, $37, $D1, $E6, $B0, $20
.db $02, $10, $F3, $E1, $D1, $C1, $23, $23, $13, $0B, $79, $B0, $20, $CC, $C1, $D1
.db $C9

_LABEL_1E36_56:
	ld   hl, $D134
	xor  a
	or   (hl)
	ret  z

	ld   (hl), $00
	ld   a, (RAM_D12F)
	rrca
	jp   c, _LABEL_1FE4_57
	ld   a, $00
	out  ($BF), a
	ld   a, $3F
	or   $40
	out  ($BF), a
	ld   hl, $DB00
	ld   c, $BE
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	ld   a, $80
	out  ($BF), a
	ld   a, $3F
	or   $40
	out  ($BF), a
	ld   hl, $DB40
	ld   c, $BE
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	ret

_LABEL_1FE4_57:
	ld   a, $00
	out  ($BF), a
	ld   a, $3F
	or   $40
	out  ($BF), a
	ld   hl, $DB00
	ld   c, $BE
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	ld   hl, $DB3F
	ld   c, $BE
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	outd
	ld   a, $80
	out  ($BF), a
	ld   a, $3F
	or   $40
	out  ($BF), a
	ld   hl, $DB40
	ld   c, $BE
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	outi
	ld   hl, $DBBE
	ld   de, $FFFC
	ld   c, $BE
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	outi
	outi
	add  hl, de
	ret

_LABEL_21C8_412:
	ld   de, $0000
	call WaitForInterrupt
	di
	ld   hl, $3800
	ld   bc, $0380
	call _LABEL_1D8A_13
	jr   _LABEL_21F6_265

_LABEL_21DA_33:
	ld   de, $00C0
	call WaitForInterrupt
	di
	ld   hl, $3800
	ld   bc, $0380
	call _LABEL_1D8A_13
	ld   hl, $1800
	ld   bc, $0020
	ld   de, $0000
	call _LABEL_1D8A_13
_LABEL_21F6_265:
	ld   hl, $DB00
	ld   de, $DB40
	xor  a
	ld   b, $40
_LABEL_21FF_236:
	ld   (hl), $F0
	inc  hl
	ld   (de), a
	inc  de
	ld   (de), a
	inc  de
	djnz _LABEL_21FF_236
	ld   a, $FF
	ld   (SATUpdate), a
	ret

Update_SpriteAtrb:
	ld   ix, $D500
	ld   hl, $DB00
	ld   (RAM_D36F), hl
	ld   hl, $DB40
	ld   (RAM_D371), hl
	ld   b, $14
_LABEL_2220_120:
	xor  a
	or   (ix+5)
	jp   z, _LABEL_224A_103
	ld   a, (ix+0)
	dec  a
	cp   $EF
	jr   nc, _LABEL_224A_103
	push bc
	ld   c, (ix+4)
	bit  5, c                 ; flash sprite
	call nz, _LABEL_2335_104
	bit  7, c
	jr   nz, _LABEL_2249_106
	bit  6, c
	jr   nz, _LABEL_2249_106
	call _LABEL_3FC8_107
	call _LABEL_226A_108
	call _LABEL_22B6_113
_LABEL_2249_106:
	pop  bc
_LABEL_224A_103:
	ld   de, $0040
	add  ix, de
	djnz _LABEL_2220_120
	ld   hl, (RAM_D36F)
	ld   a, $32
	sub  l
	jr   c, _LABEL_2264_121
	inc  a
	ld   c, a
	ld   b, $00
	ld   e, l
	ld   d, h
	inc  de
	ld   (hl), $E0
	ldir
_LABEL_2264_121:
	ld   a, $FF
	ld   (SATUpdate), a
	ret

_LABEL_226A_108:
	ld   iy, (RAM_D36F)
	ld   h, (ix+43)
	ld   l, (ix+42)
	ld   e, (hl)
	inc  hl
	ld   d, (hl)
	ld   l, (ix+28)
	ld   h, (ix+29)
	add  hl, de
	push hl
	exx
	ld   d, (ix+41)
	ld   e, (ix+40)
	pop  bc
	exx
	ld   b, (ix+5)
_LABEL_228B_112:
	exx
	ld   a, (de)
	ld   l, a
	inc  de
	ld   a, (de)
	ld   h, a
	inc  de
	add  hl, bc
	ld   (iy+0), l
	ld   a, $40
	add  a, l
	ld   l, a
	jr   nc, _LABEL_229D_109
	inc  h
_LABEL_229D_109:
	ld   a, h
	or   a
	jr   nz, _LABEL_22A6_110
	ld   a, l
	cp   $30
	jr   nc, _LABEL_22AA_111
_LABEL_22A6_110:
	ld   (iy+0), $E0
_LABEL_22AA_111:
	inc  de
	inc  de
	inc  iy
	exx
	djnz _LABEL_228B_112
	ld (RAM_D36F), iy
	ret

_LABEL_22B6_113:
	ld   iy, (RAM_D371)
	ld   h, (ix+43)
	ld   l, (ix+42)
	inc  hl
	inc  hl
	ld   e, (hl)
	inc  hl
	ld   d, (hl)
	bit  4, (ix+4)
	jr   z, _LABEL_22D2_114
	dec  de
	ld   a, e
	cpl
	ld   e, a
	ld   a, d
	cpl
	ld   d, a
_LABEL_22D2_114:
	inc  hl
	ld   c, (hl)
	inc  hl
	ld   b, (hl)
	ld   (RAM_D110), bc
	ld   l, (ix+26)
	ld   h, (ix+27)
	add  hl, de
	push hl
	exx
	ld   d, (ix+41)
	ld   e, (ix+40)
	inc  de
	inc  de
	bit  4, (ix+4)
	jr   z, _LABEL_22F6_115
	ld   hl, $0D08
	add  hl, de
	ex   de, hl
_LABEL_22F6_115:
	pop  bc
	exx
	ld   b, (ix+5)
_LABEL_22FB_119:
	exx
	ld   a, (de)
	ld   l, a
	inc  de
	ld   a, (de)
	ld   h, a
	inc  de
	add  hl, bc
	ld   (iy+0), l
	ld   a, h
	or   a
	jr   z, _LABEL_230E_116
	ld   (iy+0), $00
_LABEL_230E_116:
	inc  de
	inc  de
	inc  iy
	ld   hl, (RAM_D110)
	ld   a, (hl)
	bit  4, (ix+4)
	jr   z, _LABEL_2321_117
	add  a, (ix+9)
	jr   _LABEL_2324_118

_LABEL_2321_117:
	add  a, (ix+8)
_LABEL_2324_118:
	ld   (iy+0), a
	inc  hl
	ld   (RAM_D110), hl
	inc  iy
	exx
	djnz _LABEL_22FB_119
	ld (RAM_D371), iy
	ret

_LABEL_2335_104:
	inc  (ix+46)
	ld   a, (ix+46)
	rrca
	rrca
	jr   c, _LABEL_2344_105
	res  7, (ix+4)
	ret

_LABEL_2344_105:
	set  7, (ix+4)
	ret


; Data from 2349 to 2450 (264 bytes)
.db $CD, $C7, $23, $C5, $E5, $41, $CD, $50, $1D, $1A, $D3, $BE, $13, $23, $1A, $00
.db $00, $D3, $BE, $13, $23, $7D, $E6, $3F, $C2, $6F, $23, $D5, $11, $40, $00, $B7
.db $ED, $52, $CD, $50, $1D, $D1, $10, $E1, $E1, $01, $40, $00, $09, $7C, $FE, $3F
.db $C2, $7E, $23, $26, $38, $C1, $10, $CB, $FB, $C9, $CD, $C7, $23, $C5, $E5, $41
.db $CD, $50, $1D, $1A, $D3, $BE, $3A, $D3, $D2, $F5, $F1, $D3, $BE, $13, $23, $CD
.db $A9, $23, $10, $EF, $E1, $01, $40, $00, $09, $CD, $B9, $23, $C1, $10, $DE, $C9
.db $7D, $E6, $3F, $C0, $D5, $11, $40, $00, $B7, $ED, $52, $CD, $50, $1D, $D1, $C9
.db $7C, $FE, $3F, $C0, $26, $38, $C9, $7C, $FE, $38, $D0, $26, $3E, $C9, $C5, $7D
.db $E6, $C0, $47, $3A, $74, $D1, $0F, $0F, $85, $E6, $3E, $B0, $6F, $E5, $3A, $76
.db $D1, $0F, $0F, $0F, $E6, $1F, $07, $4F, $06, $00, $21, $7A, $54, $09, $4E, $23
.db $46, $E1, $09, $7C, $FE, $3F, $38, $06, $B7, $01, $00, $07, $ED, $42, $C1, $C9
.db $F3, $CD, $03, $24, $01, $04, $04, $C3, $4C, $23, $2A, $5A, $D3, $7D, $E6, $E0
.db $6F, $CB, $3C, $CB, $1D, $CB, $3C, $CB, $1D, $01, $7A, $54, $09, $4E, $23, $46
.db $3A, $58, $D3, $0F, $0F, $E6, $38, $6F, $26, $38, $09, $C9, $F3, $CD, $2F, $24
.db $01, $04, $04, $C3, $4C, $23, $2A, $62, $D3, $7D, $E6, $E0, $6F, $CB, $3C, $CB
.db $1D, $CB, $3C, $CB, $1D, $01, $7A, $54, $09, $4E, $23, $46, $3A, $60, $D3, $0F
.db $0F, $E6, $38, $6F, $26, $38, $09, $C9

Read_Input:
	ld   hl, $D145
	ld   de, $D146
	ld   bc, $000F
	lddr
	ld   hl, $D155
	ld   de, $D156
	ld   bc, $000F
	lddr
	call Port1_Input
	cpl
	ld   (Joypad_Press), a   ; store Joypad_Press bitfield
	ld   a, (RAM_D138)
	xor  $FF
	ld   b, a
	ld   a, (Joypad_Press)
	and  $BF             ; Joypad_Press 1 bitfields
	ld   c, a
	xor  $FF
	xor  b
	and  c
	ld   (RAM_D147), a
	ld   (RAM_D157), a
	ld   a, (RAM_D292)       ; should the CPU ControlByte sonic?
	bit  3, a
	call nz, CPU_ControlByte_Demo ; if so, call routine to set ControlBytes for the demo
	in   a, ($DD)            ; was the reset button pressed?
	cpl
	and  $10
	ret  z

	jp   _LABEL_450_67


; Data from 2495 to 2495 (1 bytes)
.db $C9

Port1_Input:
	in   a, ($DC)         ; read Joypad_Press
	or   $C0              ; enable pin input
	and  $7F              ; held state $7F= null $7A= Up $77= Right $7E= Left $80,$81= 1 and 2
	ld   b, a
	ld   c, $80           ; dump button press
	and  $30              ; check to see if 1/2 buttons have been pressed
	jr   nz, _LABEL_24A5_65 ; if so, branch
	ld   c, $00
_LABEL_24A5_65:
	ld   a, c
	or   b
	ret

CPU_ControlByte_Demo:
	ld   a, (RAM_D2E4)  ; get bank with ControlByte sequences
	ld   ($FFFF), a
	ld   hl, (ControlByte)  ; get ControlByte offset
	ld   a, h
	or   l
	ret  z

	ld   a, (hl)        ; load ControlByte byte
	ld   (Joypad_Press), a  ; save it for later
	inc  hl
	ld   a, (hl)
	ld   (RAM_D147), a
	inc  hl
	ld   (ControlByte), hl  ; get next offset
	ret

Tile_Loading_Routines:
	ld   (RAM_D34C), a
	push hl
	inc  hl
	inc  hl
	ld   a, (hl)
	ld   (RAM_D342), a
	inc  hl
	ld   a, (hl)
	ld   (RAM_D343), a
	inc  hl
	ld   e, (hl)
	inc  hl
	ld   d, (hl)
	inc  hl
	ld   (RAM_D346), hl
	pop  hl
	add  hl, de
	ld   (RAM_D344), hl
	ld   hl, $D320
	ld   de, $D321
	ld   bc, $001F
	ld   (hl), $00
	ldir
	xor  a
	ld   (BitField), a
_LABEL_24EF_252:
	call _LABEL_259C_242
	cp   $00
	jr   nz, _LABEL_24FB_246
	call _LABEL_25C8_247
	jr   _LABEL_251C_251

_LABEL_24FB_246:
	cp   $02
	jr   nz, _LABEL_2507_253
	call _LABEL_253A_254
	call _LABEL_25D3_258
	jr   _LABEL_251C_251

_LABEL_2507_253:
	cp   $03
	jr   nz, _LABEL_2516_259
	call _LABEL_253A_254
	call _LABEL_256B_260
	call _LABEL_25D3_258
	jr   _LABEL_251C_251

_LABEL_2516_259:
	call _LABEL_2528_262
	call _LABEL_25D3_258
_LABEL_251C_251:
	ld   hl, (RAM_D342)
	dec  hl
	ld   (RAM_D342), hl
	ld   a, l
	or   h
	jr   nz, _LABEL_24EF_252
	ret

_LABEL_2528_262:
	ld   bc, $0020
	ld   hl, (RAM_D346)
	ld   de, $D300
	ld   bc, $0020
	ldir
	ld   (RAM_D346), hl
	ret

_LABEL_253A_254:
	ld   ix, $D300
	ld   hl, (RAM_D346)
	ld   e, (hl)
	inc  hl
	ld   d, (hl)
	inc  hl
	ld   c, (hl)
	inc  hl
	ld   b, (hl)
	inc  hl
	ld   a, $20
_LABEL_254B_257:
	push af
	rr   b
	rr   c
	rr   d
	rr   e
	jr   c, _LABEL_255C_255
	ld   (ix+0), $00
	jr   _LABEL_2561_256

_LABEL_255C_255:
	ld   a, (hl)
	ld   (ix+0), a
	inc  hl
_LABEL_2561_256:
	inc  ix
	pop  af
	dec  a
	jr   nz, _LABEL_254B_257
	ld   (RAM_D346), hl
	ret

_LABEL_256B_260:
	ld   ix, $D300
	ld   b, $07
_LABEL_2571_261:
	ld   a, (ix+0)
	xor  (ix+2)
	ld   (ix+2), a
	ld   a, (ix+1)
	xor  (ix+3)
	ld   (ix+3), a
	ld   a, (ix+16)
	xor  (ix+18)
	ld   (ix+18), a
	ld   a, (ix+17)
	xor  (ix+19)
	ld   (ix+19), a
	inc  ix
	inc  ix
	djnz _LABEL_2571_261
	ret

_LABEL_259C_242:
	ld   a, (BitField)
	cp   $04
	jr   nz, _LABEL_25AE_243
	ld   hl, (RAM_D344)
	inc  hl
	ld   (RAM_D344), hl
	xor  a
	ld   (BitField), a
_LABEL_25AE_243:
	ld   b, a
	ld   hl, (RAM_D344)
	ld   a, (hl)
_LABEL_25B3_245:
	dec  b
	jp   m, _LABEL_25BC_244
	rrca
	rrca
	jp   _LABEL_25B3_245

_LABEL_25BC_244:
	and  $03
	push af
	ld   a, (BitField)
	inc  a
	ld   (BitField), a
	pop  af
	ret

_LABEL_25C8_247:
	ld   hl, $D320
	ld   de, $D300
	ld   bc, $0020
	ldir
_LABEL_25D3_258:
	ld   a, (RAM_D34C)
	or   a
	jp   nz, _LABEL_25E8_248
	ld   hl, $D300
	ld   b, $20
_LABEL_25DF_249:
	ld   a, (hl)
	out  ($BE), a
	push hl
	pop  hl
	inc  hl
	djnz _LABEL_25DF_249
	ret

_LABEL_25E8_248:
	ld   hl, $D300
	ld   b, $20
_LABEL_25ED_250:
	ld   e, (hl)
	ld   d, $01
	ld   a, (de)
	out  ($BE), a
	push hl
	pop  hl
	inc  hl
	djnz _LABEL_25ED_250
	ret


; Data from 25F9 to 27ED (501 bytes)
.db $16, $00, $6A, $06, $08, $29, $30, $01, $19, $10, $FA, $C9, $06, $10, $AF, $29
.db $17, $BB, $38, $03, $93, $CB, $C5, $10, $F6, $C9, $3E, $10, $CB, $23, $CB, $12
.db $ED, $6A, $38, $09, $ED, $42, $30, $08, $09, $3D, $20, $F0, $C9, $B7, $ED, $42
.db $1C, $3D, $20, $E8, $C9, $C9, $3A, $92, $D2, $B7, $C0, $ED, $5B, $9D, $D2, $ED
.db $53, $A0, $D2, $3A, $9F, $D2, $32, $A2, $D2, $AF, $11, $9D, $D2, $1A, $8E, $27
.db $12, $13, $23, $1A, $8E, $27, $12, $13, $23, $1A, $8E, $27, $12, $30, $0F, $21
.db $A3, $D2, $36, $90, $23, $36, $99, $23, $36, $99, $3E, $02, $18, $02, $3E, $01
.db $32, $BB, $D2, $C3, $6F, $26, $3A, $9E, $D2, $E6, $F0, $47, $3A, $A1, $D2, $E6
.db $F0, $B8, $C8, $3A, $C8, $D2, $3D, $C2, $91, $26, $3A, $9E, $D2, $E6, $F0, $CA
.db $BD, $26, $FE, $50, $CA, $BD, $26, $C9, $3A, $9E, $D2, $0F, $0F, $0F, $0F, $E6
.db $0F, $CD, $CD, $26, $5F, $3A, $9F, $D2, $E6, $0F, $CD, $CD, $26, $57, $3A, $9F
.db $D2, $0F, $0F, $0F, $0F, $E6, $0F, $CD, $CD, $26, $83, $82, $CD, $CD, $26, $B7
.db $CA, $BD, $26, $C9, $3A, $C3, $D2, $47, $3C, $E6, $7F, $4F, $78, $E6, $80, $B1
.db $32, $C3, $D2, $C9, $B7, $C8, $06, $03, $90, $30, $FD, $80, $C9, $F3, $3E, $01
.db $32, $BA, $D2, $21, $9A, $D2, $11, $24, $3A, $CD, $26, $27, $FB, $C9, $F3, $3E
.db $02, $32, $BA, $D2, $21, $A6, $D2, $11, $E0, $3A, $CD, $26, $27, $FB, $C9, $F3
.db $3E, $03, $32, $BA, $D2, $21, $9D, $D2, $7E, $23, $B6, $23, $B6, $28, $0F, $21
.db $9D, $D2, $11, $9A, $3B, $CD, $26, $27, $21, $A4, $3B, $11, $16, $A5, $11, $16
.db $A5, $21, $A6, $3B, $01, $01, $02, $F3, $CD, $83, $23, $FB, $C9, $D5, $E5, $11
.db $AE, $D2, $01, $07, $00, $ED, $B0, $E1, $CD, $AD, $27, $E1, $3A, $BA, $D2, $FE
.db $02, $38, $12, $28, $08, $11, $B9, $D2, $01, $05, $06, $18, $10, $11, $B7, $D2
.db $01, $03, $04, $18, $08, $11, $B5, $D2, $01, $01, $02, $18, $00, $22, $1C, $D1
.db $79, $B7, $28, $0A, $0D, $1A, $FE, $00, $20, $04, $3E, $0A, $18, $03, $0E, $00
.db $1A, $C5, $87, $D5, $F3, $2A, $1C, $D1, $CD, $50, $1D, $21, $16, $A5, $5F, $16
.db $00, $19, $7E, $D3, $BE, $F5, $F1, $3A, $D3, $D2, $D3, $BE, $F5, $F1, $23, $E5
.db $2A, $1C, $D1, $23, $23, $22, $1C, $D1, $11, $3E, $00, $19, $CD, $50, $1D, $E1
.db $7E, $D3, $BE, $F5, $F1, $3A, $D3, $D2, $D3, $BE, $F5, $F1, $23, $FB, $D1, $1B
.db $C1, $10, $AD, $C9, $AF, $21, $AE, $D2, $11, $B4, $D2, $3A, $BA, $D2, $4F, $47
.db $FE, $04, $3F, $D8, $7E, $E6, $0F, $FE, $0A, $3F, $D8, $7E, $E6, $F0, $FE, $A0
.db $3F, $D8, $23, $10, $EF, $21, $AE, $D2, $AF, $41, $ED, $67, $12, $13, $ED, $67
.db $12, $13, $23, $10, $F5, $C9, $00, $00, $00, $01, $00, $00, $10, $00, $00, $50
.db $00, $00, $10, $00, $00

Increment_Timer:
	ld   a, (RAM_D2BE)  ; check to see if the timer needs to be updated
	or   a
	ret  z              ; if not, skip over this

	ld   hl, Frame_Count; get frame counter
	inc  (hl)           ; increment it
	ld   a, $3C         ; update timer every 60th frame
	sub  (hl)           ; if it's been 60 frames, keep looping
	ret  nz

	ld   (hl), a
	ld   hl, $D294     ; get screenmode offset
	bit  7, (hl)       ; is Sonic in a special stage?
	jr   nz, SSTimer   ; if so, jump
	ld   a, $01        ; set a to 1
	ld   hl, $D2BF     ; load seconds
	add  a, (hl)       ; add 1 second each frame
	daa
	ld   (hl), a
	sub  $60           ; keep increasing the seconds until 59 seconds
	jp   nz, SetTimerSprites ; set the sprites
	ld   (hl), a             ; roll over to minutes
	ld   a, $01              ; continue adding seconds
	inc  hl
	add  a, (hl)             ; add 1 to minutes after 59 seconds
	daa
	ld   (hl), a             ; check to see if the timer is at 9:59
	sub  $10
	jp   nz, SetTimerSprites ; set sprites
	ld   a, $C0              ; set time to 9:59, and kill the player
	ld   (RAM_D44B), a       ; kill player flag
	xor  a
	ld   (RAM_D2BE), a       ; reset timer update flag
	ret

SSTimer:
	ld   a, (StopWatchPwrUp)        ; check to see if the time has been frozen
	or   a
	jp   nz, StopWatch_Timer  ; if so, jump to limit the time for the power-up
	ld   hl, $D2BF            ; load ss timer
	ld   a, (hl)
	dec  a                    ; decrease seconds
	cp   $FF                  ; check to see if the timer has expired
	jp   z, SSResults         ; if so, jump
	ld   b, a
	and  $0F
	cp   $0F
	jr   nz, Update_SSTimer
	ld   a, b
	sub  $06
	ld   b, a
Update_SSTimer:
	ld   (hl), b
	jp   SetTimerSprites

SSResults:
	ld   hl, $D294            ; get screenmode offset
	set  5, (hl)              ; set it to results card
	ret

StopWatch_Timer:
	ld   a, (StopWatchPwrUp)        ; get timer power-up
	dec  a                    ; decrement it
	ld   (StopWatchPwrUp), a
	jp   z, UpdateMusic
	ld   a, $B5               ; play time frozen sound
	ld   (PlaySound), a
	ret

SetTimerSprites:
	ld   a, (RAM_D292)
	or   a
	ret  nz

	ld   a, (TimerSec)
	rlca
	and  $1E
	add  a, $2E
	ld   (RAM_DBB9), a
	ld   a, (TimerMin)
	rrca
	rrca
	rrca
	and  $1E
	add  a, $2E
	ld   (RAM_DBBD), a
	ld   a, (TimerMin)
	rlca
	and  $1E
	add  a, $2E
	ld   (RAM_DBBF), a
	ret


; Data from 2885 to 2933 (175 bytes)
.db $DD, $7E, $0B, $B7, $C8, $16, $00, $DD, $5E, $0A, $21, $00, $02, $19, $7E, $A7
.db $F2, $A5, $28, $32, $00, $D1, $3E, $FF, $32, $01, $D1, $32, $06, $D1, $18, $0A
.db $32, $00, $D1, $AF, $32, $01, $D1, $32, $06, $D1, $21, $00, $00, $22, $04, $D1
.db $DD, $46, $0B, $2A, $04, $D1, $ED, $5B, $00, $D1, $19, $22, $04, $D1, $10, $F3
.db $DD, $E5, $E1, $11, $10, $00, $19, $11, $04, $D1, $AF, $1A, $8E, $77, $13, $23
.db $1A, $8E, $77, $13, $23, $1A, $8E, $77, $DD, $7E, $0A, $C6, $C0, $5F, $16, $00
.db $21, $00, $02, $19, $7E, $A7, $F2, $FB, $28, $32, $00, $D1, $3E, $FF, $32, $01
.db $D1, $32, $06, $D1, $18, $0A, $32, $00, $D1, $AF, $32, $01, $D1, $32, $06, $D1
.db $21, $00, $00, $22, $04, $D1, $DD, $46, $0B, $2A, $04, $D1, $ED, $5B, $00, $D1
.db $19, $22, $04, $D1, $10, $F3, $DD, $E5, $E1, $11, $13, $00, $19, $11, $04, $D1
.db $AF, $1A, $8E, $77, $13, $23, $1A, $8E, $77, $13, $23, $1A, $8E, $77, $C9

Level_Setup:
	di
	call ClearWorkingVRAM
	call LoadLevelTiles
	call LoadHUD
	ld   ix, $D15E
	call ClearLevelAttrib
	call LoadLevelHeaders
	call LoadLevel_Layout
	call LoadRingArtPointers
	call SetUpWater
	ld   a, (RAM_D2C8)
	ld   (RAM_D500), a ; set up either Sonic or Tails sprite
	dec  a
	call nz, _LABEL_79DF_289
	call _LABEL_79F2_290
	ld   a, (RAM_D2BD)
	or   a
	jr   nz, _LABEL_297A_291
	xor  a
	ld   (TimerMin), a
	ld   (TimerSec), a
	ld   a, (RAM_D292)
	or   a
	jr   nz, _LABEL_2976_292
	ld   a, $FF
	ld   (RAM_D2BE), a
_LABEL_2976_292:
	call WaitForInterrupt
	ret

_LABEL_297A_291:
	call WaitForInterrupt
	ret

ClearWorkingVRAM:
	ld   hl, $D300
	ld   de, $D301
	ld   bc, $08BF
	ld   (hl), $00
	ldir
	xor  a
	ld   (RAM_D131), a
	ld   (RAM_D132), a
	ret

LoadHUD:
	ld   a, (RAM_D292)
	or   a
	ret  nz

	di
	call _LABEL_21F6_265
	ld   hl, $29C4
	ld   ix, $DB34             ; VPOS for last 12 sprites in the SST (Sprite Status Table)
	ld   iy, $DBA8             ; HPOS/Char for last 12 sprites
	ld   b, $0C
	call _LABEL_29E8_266
	ld   a, (CurrentLevel)     ; is the current level Electric Egg?
	cp   $06
	jr   nz, _LABEL_29C2_267   ; if so, skip over this
	ld   a, (CurrentAct)
	cp   $02                  ; Is it act 3?
	jr   nz, _LABEL_29C2_267
	ld   a, $E0               ; if it is, load a to $E0
	ld   (RAM_DB38), a
	ld   (RAM_DB39), a
_LABEL_29C2_267:
	ei
	ret


; Icon positions
;  hpos vpos char
.db $10, $28, $2E   ; Life Icon
.db $10, $20, $34
.db $10, $10, $48
.db $10, $18, $4A
.db $20, $20, $2E   ; Ring
.db $20  $28, $2E
.db $20, $10, $10
.db $20, $18, $12
.db $00, $10, $2E   ; Timer
.db $00, $18, $42
.db $00, $20  $2E
.db $00, $28, $2E

_LABEL_29E8_266:
	ld   a, (hl)
	ld   (ix+0), a
	inc  hl
	ld   a, (hl)
	ld   (iy+0), a
	inc  hl
	ld   a, (hl)
	ld   (iy+1), a
	inc  hl
	inc  ix
	inc  iy
	inc  iy
	djnz _LABEL_29E8_266
	ret


; Sets all counters to default values
.db $AF, "2", $9A, $D2  ; set ring counter
.db "2", $9D, $D2       ; score
.db "2", $9E, $D2,      ; score
.db "2", $9F, $D2       ; score
.db "2", $A8, $D2, ""   ; calculate score
.db "2", $A9, $D2
.db "2", $AA, $D2,
.db "2", $AB, $D2, 
.db "2", $AC, $D2,
.db "2", $AD, $D2,
.db "2", $CC  $D2
.db ":", $95, $D2,
.db $B7, $C0, "2",
.db $97, $D2, "2",
.db $98, $D2, $C9

SetUpWater:
	ld   a, (CurrentLevel)
	cp   $04
	ret  nz

	ld   a, (CurrentAct)
	cp   $02
	ret  z

	ld   c, $0D
	ld   h, $00
	call FindEmptyObjSlot
	ld   c, $0D
	ld   h, $01
	call FindEmptyObjSlot
	ld   hl, $0300
	ld   (RAM_D450), hl
	ret

LoadRingArtPointers:
	xor  a
	ld   (Ring_Count), a
	ld   a, (CurrentLevel)
	add  a, a
	ld   l, a
	ld   h, $00
	ld   de, RingArt
	add  hl, de
	ld   e, (hl)
	inc  hl
	ld   d, (hl)
	ld   a, (CurrentAct)
	add  a, a
	ld   l, a
	ld   h, $00
	add  hl, de
	ld   e, (hl)
	inc  hl
	ld   d, (hl)
	ex   de, hl
	ld   e, (hl)
	inc  hl
	ld   d, (hl)
	inc  hl
	ld   (RAM_D2E0), de
	ld   e, (hl)
	inc  hl
	ld   d, (hl)
	inc  hl
	ld   (RAM_D399), de
	ld   e, (hl)
	inc  hl
	ld   d, (hl)
	inc  hl
	ld   (RAM_D39B), de
	ld   a, (hl)
	ld   (RAM_D452), a
	inc  hl
	ld   a, (hl)
	ld   (RAM_D45A), a
	inc  hl
	ld   a, (hl)
	ld   (RAM_D462), a
	inc  hl
	ld   a, (hl)
	ld   (RAM_D46A), a
	inc  hl
	ret


; Ring Pointers
.db $BA, $2A, $C0, $2A, $C6, $2A, $CC, $2A, $D2, $2A, $D8, $2A, $BA, $2A, $DE, $2A
.db $E4, $2A, $E4, $2A, $EA, $2A, $E4, $2A, $EA, $2A, $BA, $2A, $F0, $2A, $F0, $2A
.db $F6, $2A, $F6, $2A, $F6, $2A, $00, $2B, $00, $2B, $00, $2B, $0A, $2B, $0A, $2B
.db $0A, $2B, $14, $2B, $14, $2B, $14, $2B, $1E, $2B, $1E, $2B, $1E, $2B, $28, $2B
.db $28, $2B, $28, $2B, $32, $2B, $32, $2B, $32, $2B, $3C, $2B, $3C, $2B, $3C, $2B
.db $46, $2B, $46, $2B, $46, $2B, $F6, $2A, $F6, $2A, $F6, $2A, $00, $80, $5D, $85
.db $60, $22, $01, $00, $00, $00, $00, $80, $5D, $85, $80, $29, $04, $00, $00, $00
.db $00, $80, $5D, $85, $A0, $29, $05, $00, $00, $00, $00, $80, $5D, $85, $60, $21
.db $02, $03, $0E, $00, $00, $80, $5D, $85, $C0, $28, $05, $00, $00, $0B, $00, $80
.db $5D, $85, $E0, $2A, $05, $06, $08, $0D, $00, $80, $5D, $85, $00, $00, $00, $00
.db $00, $00, $00, $80, $5D, $85, $A0, $2B, $0C, $00, $00, $00, $00, $80, $5D, $85
.db $00, $2B, $00, $00, $00, $00

Screen:
	ld   a, (RAM_D292)
	rlca
	jp   c, _LABEL_2C17_23
	rlca
	jr   c, Intro_TitleScreen_Start
	rlca
	jp   c, _LABEL_2B77_25
	rlca
	jp   c, _LABEL_2B9F_26
	rlca
	jp   c, Play_Demo            ; start demo
	rlca
	jp   c, _LABEL_2C0D_28
	jp   Screen

Intro_TitleScreen_Start:
	ld   hl, $D292
	res  6, (hl)      ; reset intro flag
	set  5, (hl)      ; set title screen flag
	jp   Screen   ; determine which gamemode to go to next

_LABEL_2B77_25:
	call _LABEL_CF5_410
	call _LABEL_6C7_411

; Data from 2B7D to 2B9E (34 bytes)
.db $CD, $AF, $1C, $CD, $E1, $18, $06, $1E, $FB, $CD, $2D, $06, $10, $FA, $CD, $DA
.db $21, $21, $92, $D2, $CB, $BE, $21, $92, $D2, $CB, $AE, $CB, $BE, $CB, $E6, $C3
.db $50, $2B

_LABEL_2B9F_26:
	call ClearLevelAttrib
	call ClearWorkingVRAM
	call _LABEL_719_407

; Data from 2BA8 to 2BC2 (27 bytes)
.db $CD, $AF, $1C, $CD, $E1, $18, $06, $1E, $FB, $CD, $2D, $06, $10, $FA, $CD, $DA
.db $21, $21, $92, $D2, $CB, $A6, $CB, $DE, $C3, $50, $2B

Play_Demo:
	di
	call Change_DemoLevel   ; change demo level
	ld   a, $40           ; set demo flag
	ld   (Gamestate), a   ; set gamestate to demo
	call _LABEL_2CA4_32   ; load demo level
	ld   hl, (RAM_D2E5)   ; get next ControlByte
	ld   (ControlByte), hl    ; set ControlByte byte, to ControlByte player
	ld   bc, $0438        ; set demo time
	call _LABEL_2C8A_295
	call _LABEL_2CC4_399
	ld   hl, $0000
	ld   (ControlByte), hl
	xor  a
	ld   (Gamestate), a
	ld   (CurrentLevel), a
	ld   (CurrentAct), a
	ld   hl, $D292
	bit  7, (hl)
	jr   z, _LABEL_2C01_406
	ld   hl, $D292
	res  7, (hl)
	res  3, (hl)
	set  4, (hl)        ; set demo flag
	jp   Screen

_LABEL_2C01_406:
	ld   hl, $D292
	res  7, (hl)
	res  3, (hl)
	set  5, (hl)
	jp   Screen

_LABEL_2C0D_28:
	ld   hl, $D292
	res  2, (hl)
	set  5, (hl)
	jp   Screen

_LABEL_2C17_23:
	xor  a
	ld   (RAM_D295), a
	call _LABEL_AD0_413
	call _LABEL_7CE_415
	call _LABEL_1CAF_404
	ld   b, $2A
_LABEL_2C26_416:
	ei
	call WaitForInterrupt
	djnz _LABEL_2C26_416
	xor  a
	ld   (RAM_D292), a
	ld   (Gamestate), a
	ret

Change_DemoLevel:
	ld   a, (DemoBank)      ; load demo number
	inc  a                  ; increment demo number
	cp   $03                ; has all the demos been played yet?
	jr   c, _LABEL_2C3D_30  ; if not, jump
	xor  a
_LABEL_2C3D_30:
	ld   (DemoBank), a      ; clear bank
	add  a, a               ; calculate which demo to play
	add  a, a
	ld   l, a
	ld   h, $00
	ld   de, $2C7E
	ld   a, (RAM_D12D)
	or   a
	jr   nz, _LABEL_2C51_31
	ld   de, $2C72
_LABEL_2C51_31:
	add  hl, de
	ld   a, (hl)
	and  $0F
	ld   (CurrentLevel), a
	ld   a, (hl)
	and  $80                ; get ControlByteler sequence
	rlca
	inc  a
	ld   (RAM_D2C8), a
	inc  hl
	ld   a, (hl)
	ld   (RAM_D2E4), a
	inc  hl
	ld   e, (hl)
	inc  hl
	ld   d, (hl)
	ld   (RAM_D2E5), de
	xor  a
	ld   (CurrentAct), a
	ret


; Demo Headers, determines which levels to play in demos
;   Level Bank      ControlByte sequence Pointer
.db $02,  $1F,      $00, $94
.db $00,  $1F,      $00, $80
.db $81,  $1F,      $00, $8A
.db $02,  $1F,      $00, $B2
.db $00,  $1F,      $00, $9E
.db $81,  $1F,      $00, $A8

_LABEL_2C8A_295:
	push bc
	call WaitForInterrupt
	call Engine_UpdateLevelState
	pop  bc
	ld   a, (RAM_D292)
	bit  7, a
	ret  nz

	ld   a, (Gamestate)
	cp   $40                  ; set demo flag again
	ret  nz

	dec  bc                   ; decrement demo time
	ld   a, b
	or   c
	jr   nz, _LABEL_2C8A_295
	ret

_LABEL_2CA4_32:
	di
	ld   hl, $D293
	set  1, (hl)         ; set title card sequence
	call _LABEL_21DA_33
	call Level_Setup
	call UpdateMusic
	call _LABEL_794F_293
	call _LABEL_59B3_294
	ld   a, $20
	ld   (Ring_Count), a
	ld   hl, $D293
	res  1, (hl)           ; reset title card flag
	ret

_LABEL_2CC4_399:
	call WaitForInterrupt
	call _LABEL_361D_332
	ld   a, (RAM_D501)
	cp   $1F
	jr   nz, _LABEL_2CD8_400
	ld   a, (RAM_D51D)
	cp   $02
	jr   nz, _LABEL_2CC4_399
_LABEL_2CD8_400:
	call _LABEL_1CEB_401
	call _LABEL_18E1_402
	ld   b, $1E
_LABEL_2CE0_403:
	ei
	call WaitForInterrupt
	djnz _LABEL_2CE0_403
	call _LABEL_1CAF_404
	ld   b, $2A
_LABEL_2CEB_405:
	ei
	call WaitForInterrupt
	djnz _LABEL_2CEB_405
	ret


; Data from 2CF2 to 2F48 (599 bytes)
.db $CD, $2D, $06, $E5, $E1, $3A, $92, $D2, $CB, $7F, $C0, $2B, $7C, $B5, $C8, $18
.db $EF, $C9, $C9, $C9, $C9, $C9, $AF, $32, $10, $D1, $3A, $9A, $D2, $FE, $00, $28
.db $15, $3D, $27, $32, $9A, $D2, $CD, $00, $2F, $F3, $CD, $D6, $26, $CD, $F8, $26
.db $FB, $CD, $E6, $2E, $18, $E4, $2A, $A6, $D2, $7D, $FE, $00, $28, $06, $D6, $01
.db $27, $6F, $18, $0B, $2E, $99, $7C, $FE, $00, $28, $17, $D6, $01, $27, $67, $22
.db $A6, $D2, $CD, $FB, $2E, $F3, $CD, $E7, $26, $CD, $F8, $26, $FB, $CD, $E6, $2E
.db $18, $D4, $C9, $3A, $98, $D2, $FE, $02, $C0, $3A, $97, $D2, $87, $21, $84, $2D
.db $16, $00, $5F, $19, $4E, $23, $46, $C5, $CD, $05, $2F, $F3, $CD, $F8, $26, $FB
.db $CD, $E6, $2E, $C1, $0B, $78, $B1, $20, $EE, $06, $0C, $FB, $CD, $2D, $06, $10
.db $FA, $C9, $32, $00, $64, $00, $96, $00, $C8, $00, $FA, $00, $58, $02, $DD, $7E
.db $00, $B7, $C8, $DD, $7E, $0A, $FE, $03, $CA, $7C, $2E, $FE, $02, $CA, $79, $2E
.db $FE, $01, $CA, $E7, $2D, $FE, $00, $CA, $AD, $2D, $C9, $DD, $34, $1F, $DD, $35
.db $1E, $DD, $7E, $1E, $B7, $20, $04, $DD, $36, $00, $00, $DD, $6E, $1E, $DD, $7E
.db $2C, $B7, $28, $02, $CB, $3D, $26, $00, $29, $DD, $56, $35, $DD, $5E, $34, $19
.db $DD, $74, $31, $DD, $75, $30, $DD, $66, $37, $DD, $6E, $36, $DD, $74, $24, $DD
.db $75, $23, $C3, $1E, $2E, $DD, $34, $1F, $DD, $35, $1E, $DD, $7E, $1E, $B7, $20
.db $04, $DD, $36, $00, $00, $DD, $66, $35, $DD, $6E, $34, $DD, $74, $31, $DD, $75
.db $30, $DD, $66, $37, $DD, $74, $24, $DD, $6E, $36, $DD, $75, $23, $11, $02, $00
.db $AF, $ED, $52, $DD, $74, $37, $DD, $75, $36, $C3, $1E, $2E, $DD, $46, $1C, $C5
.db $06, $01, $DD, $4E, $1F, $79, $DD, $BE, $1A, $38, $03, $DD, $4E, $1A, $DD, $66
.db $24, $DD, $6E, $23, $DD, $56, $31, $DD, $5E, $30, $F3, $DD, $7E, $2C, $B7, $20
.db $05, $CD, $49, $23, $18, $03, $CD, $83, $23, $FB, $DD, $66, $24, $DD, $6E, $23
.db $11, $40, $00, $19, $DD, $74, $24, $DD, $75, $23, $26, $00, $DD, $6E, $1A, $DD
.db $7E, $2C, $B7, $20, $01, $29, $DD, $56, $31, $DD, $5E, $30, $19, $DD, $74, $31
.db $DD, $75, $30, $C1, $10, $A9, $C9, $C3, $7F, $2E, $C3, $7F, $2E, $C9, $DD, $7E
.db $00, $B7, $C8, $DD, $35, $1E, $DD, $7E, $1E, $B7, $20, $04, $DD, $36, $00, $00
.db $DD, $46, $1C, $DD, $4E, $1A, $DD, $66, $37, $DD, $6E, $36, $DD, $56, $35, $DD
.db $5E, $34, $F3, $CD, $49, $23, $FB, $DD, $66, $37, $DD, $6E, $36, $DD, $7E, $0A
.db $FE, $03, $28, $0D, $FE, $02, $28, $11, $FE, $01, $28, $13, $FE, $00, $28, $17
.db $C9, $11, $40, $00, $AF, $ED, $52, $18, $14, $11, $40, $00, $19, $18, $0E, $11
.db $02, $00, $AF, $ED, $52, $18, $06, $11, $02, $00, $19, $18, $00, $DD, $74, $37
.db $DD, $75, $36, $C9, $3A, $10, $D1, $3C, $32, $10, $D1, $3A, $37, $D1, $B7, $C0
.db $C5, $06, $FF, $F5, $F1, $10, $FC, $C1, $C9, $21, $E2, $27, $18, $08, $21, $E5
.db $27, $18, $03, $21, $EB, $27, $3A, $C3, $D2, $F5, $CD, $2F, $26, $3A, $C3, $D2
.db $47, $F1, $B8, $28, $26, $E6, $7F, $FE, $08, $38, $02, $3E, $08, $87, $87, $6F
.db $26, $00, $11, $5C, $3C, $19, $11, $2C, $A5, $3A, $C8, $D2, $FE, $01, $28, $03
.db $11, $30, $A5, $01, $02, $02, $F3, $CD, $83, $23, $FB, $3A, $10, $D1, $E6, $0F
.db $C0, $3E, $B4, $32, $04, $DE, $C9

_LABEL_2F49_408:
	call ClearWorkingVRAM
	call ClearLevelAttrib
	ld   hl, $3800
	ld   bc, $0380
	ld   de, $0080
	call _LABEL_1D8A_13
	call _LABEL_798D_409

; Data from 2F5E to 3064 (263 bytes)
.db $21, $8E, $38, $01, $12, $0E, $11, $14, $BA, $CD, $49, $23, $21, $E8, $3D, $01
.db $0A, $01, $11, $0C, $BC, $CD, $49, $23, $C9, $CD, $08, $30, $CD, $2D, $06, $DD
.db $21, $00, $D7, $CD, $90, $2D, $DD, $7E, $00, $F5, $DD, $21, $40, $D7, $CD, $90
.db $2D, $F1, $DD, $46, $00, $A8, $20, $E4, $DD, $21, $00, $D7, $DD, $36, $00, $10
.db $DD, $36, $1A, $0B, $DD, $36, $1C, $04, $DD, $36, $1E, $05, $DD, $36, $1F, $00
.db $DD, $21, $40, $D7, $DD, $36, $00, $11, $DD, $36, $1A, $0B, $DD, $36, $1C, $04
.db $DD, $36, $1E, $04, $DD, $36, $1F, $00, $CD, $2D, $06, $DD, $21, $00, $D7, $CD
.db $80, $2E, $DD, $7E, $00, $F5, $DD, $21, $40, $D7, $CD, $80, $2E, $F1, $DD, $46
.db $00, $A8, $20, $E4, $AF, $DD, $21, $00, $D7, $DD, $77, $00, $DD, $21, $40, $D7
.db $DD, $77, $00, $3E, $14, $32, $00, $D7, $CD, $2D, $06, $CD, $D1, $5D, $3A, $26
.db $D7, $B7, $28, $F4, $3E, $BF, $32, $04, $DE, $C9, $DD, $21, $00, $D7, $DD, $36
.db $00, $10, $DD, $36, $0A, $00, $21, $20, $BC, $DD, $74, $35, $DD, $75, $34, $21
.db $00, $3C, $DD, $74, $37, $DD, $75, $36, $DD, $36, $1A, $0B, $DD, $36, $1C, $04
.db $DD, $36, $1E, $0B, $DD, $36, $1F, $00, $DD, $21, $40, $D7, $DD, $36, $00, $11
.db $DD, $36, $0A, $01, $21, $78, $BC, $DD, $74, $35, $DD, $75, $34, $21, $3E, $3C
.db $DD, $74, $37, $DD, $75, $36, $DD, $36, $1A, $0B, $DD, $36, $1C, $04, $DD, $36
.db $1E, $0B, $DD, $36, $1F, $00, $C9

_LABEL_3065_417:
	call ClearWorkingVRAM
	call ClearLevelAttrib
	call _LABEL_21DA_33
	call _LABEL_79B7_418

; Data from 3071 to 3103 (147 bytes)
.db $AF, $32, $C8, $D2, $21, $00, $38, $01, $20, $18, $11, $9C, $8E, $CD, $49, $23
.db $21, $92, $D4, $36, $00, $CB, $FE, $23, $36, $1E, $21, $94, $D4, $36, $00, $CB
.db $FE, $23, $36, $07, $3A, $C8, $D2, $3C, $32, $00, $D5, $3E, $30, $32, $01, $D5
.db $32, $02, $D5, $21, $80, $00, $22, $11, $D5, $21, $88, $00, $22, $14, $D5, $3E
.db $40, $32, $93, $D2, $0E, $10, $CD, $D3, $1C, $3E, $82, $32, $04, $DE, $CD, $22
.db $35, $21, $C8, $D2, $34, $06, $1E, $FB, $CD, $2D, $06, $10, $FA, $CD, $EB, $1C
.db $CD, $AF, $1C, $CD, $E1, $18, $06, $5A, $FB, $CD, $2D, $06, $10, $FA, $C9, $CD
.db $65, $7A, $21, $16, $39, $01, $0A, $0B, $11, $F5, $B6, $CD, $49, $23, $21, $92
.db $D4, $36, $00, $CB, $FE, $23, $36, $2A, $21, $94, $D4, $36, $00, $CB, $FE, $23
.db $36, $07, $C9

LivesCounterUpdate:
	ld   a, $A9             ; get extra life sound effect
	ld   (PlaySound), a     ; play it
	ld   a, (Lives_Count)   ; load lives counter
	cp   $99                ; does the player have 99 lives?
	jr   z, Cap_Counter     ; if so jump to cap the counter 
	add  a, $01             ; add one to life counter
	daa
	ld   (Lives_Count), a   ; update lives counter
Cap_Counter:
	ld   a, (RAM_D292)
	or   a
	ret  nz

	ld   a, (Lives_Count)
	and  $0F
	rlca
	and  $1E
	add  a, $2E
	ld   (RAM_DBA9), a     ; first nibble of counter
	ld   a, (Lives_Count)
	and  $F0
	rrca
	rrca
	rrca
	and  $1E
	add  a, $2E
	ld   (RAM_DBAB), a    ; last nibble
	ret


Increment_Ring:
       ld a, (Ring_Count)
       add a, $01
       daa
       ld (Ring_Count), a
       or  a
       jr nz, _LABEL_314A_359
       call LivesCounterUpdate
       call LoadSpecialStage


_LABEL_314A_359:
	ld   a, (RAM_D292)
	or   a
	ret  nz

	ld   a, (CurrentLevel)       ; check to see if it's Electric Egg Act 3
	cp   $06
	jr   nz, _LABEL_315C_360
	ld   a, (CurrentAct)
	cp   $02
	ret  z

_LABEL_315C_360:                  ; sets up the ring counter
	ld   a, (Ring_Count)
	rrca
	rrca
	rrca
	and  $1E
	add  a, $2E
	ld   (RAM_DBB1), a        ; last nibble of ringcounter
	ld   a, (Ring_Count)
	rlca
	and  $1E
	add  a, $2E
	ld   (RAM_DBB3), a       ; first nibble of ringcounter
	
	ret


; Data from 3175 to 361C (1192 bytes) Title Card Mappings?
.incbin "SonicChaos.sms.dat.C"

_LABEL_361D_332:
	ld   ix, $D500    ; set up player object
	ld   a, (RAM_D500)
	or   a
	ret  z

	res  7, (ix+4)
	ld   a, (RAM_D44B)
	and  $40
	call nz, X.X          ; call death routine
	ld   a, $FF
	ld   (RAM_D44F), a
	ld   a, $0C
	call SwapFrame2
	call _LABEL_64FA_335
	xor  a
	ld   (RAM_D44F), a
	ld   a, $FF
	ld   (RAM_D44F), a
	ld   a, $0C
	call SwapFrame2
	call _LABEL_5E91_343
	xor  a
	ld   (RAM_D44F), a
	jp   MonitorChk


; Data from 3657 to 3FC7 (2417 bytes) Player Setstates
.incbin "SonicChaos.sms.dat.D" READ $5C4
.include "research/loop_states.asm"
.incbin "SonicChaos.sms.dat.D" SKIP $8A6

_LABEL_3FC8_107:
	ld   l, (ix+17)
	ld   h, (ix+18)
	ld   de, (HorizOffset)
	xor  a
	sbc  hl, de
	ld   (ix+26), l
	ld   (ix+27), h
	ld   l, (ix+20)
	ld   h, (ix+21)
	ld   de, (VertOffset)
	xor  a
	sbc  hl, de
	ld   (ix+28), l
	ld   (ix+29), h
	ret


; Data from 3FEF to 3FFF (17 bytes)
.db $CD, $46, $4B, $CD, $1A, $40, $CD, $41, $41, $DD, $7E, $01, $FE, $05, $30, $06
.db $21


.BANK 1 SLOT 1
.ORG $0000


; Data from 4000 to 4774 (1909 bytes)
.incbin "include/PlayerLogic.bin"

RocketPwrUp:
	ld   hl, $0000
	ld   (HorizontalVelocity), hl      ; reset velocity
	ld   (VerticalVelocity), hl
	ld   hl, $0700                ; set max horizontal velocity 
	ld   (RAM_D373), hl
	ld   hl, $1770
	ld   a, (CurrentLevel)
	cp   $08               
	jr   z, _LABEL_4799_356
	ld   a, $85
	ld   (PlaySound), a  ; play Rocket Shoes jingle
	call WaitForInterrupt  ; call interrupt routine to pause the timer for Stopwatch Monitor
	ld   hl, $012C         ; load power-up time
_LABEL_4799_356:
	ld   (RAM_D3A1), hl
	res  1, (ix+3)
	res  6, (ix+3)
	ld   (ix+2), $11
	ret


; Preserved bytes around recovered spring state routines.
.db $DD, $CB, $03, $86, $DD, $CB, $03, $8E, $DD, $36, $02, $06, $C9, $DD, $CB, $03
.db $46, $C0, $3E, $A1, $32, $04, $DE, $DD, $CB, $03, $8E, $DD, $36, $02, $07, $C9
.db $DD, $CB, $03, $46, $C0, $3E, $A1, $32, $04, $DE, $DD, $CB, $03, $8E, $DD, $36
.db $02, $08, $C9, $DD, $7E, $17, $B7, $CA, $BB, $46, $DD, $36, $02, $09, $21, $00
.db $06, $22, $73, $D3, $DD, $CB, $03, $86, $DD, $CB, $03, $CE, $3E, $A5, $32, $04
.db $DE, $C9, $DD, $36, $02, $1B, $DD, $CB, $03, $C6, $DD, $CB, $03, $CE, $DD, $CB
.db $22, $8E, $C9
.include "research/spring_states.asm"
.db $3E, $20, $32, $02, $D5, $0E, $89, $3A, $98, $D2, $FE, $02, $20, $02, $0E, $97
.db $79, $32, $04, $DE, $C9, $3A, $37, $D1, $07, $07, $E6, $30, $C8, $E6, $10, $47
.db $DD, $7E, $04, $E6, $EF, $B0, $DD, $77, $04, $C9, $DD, $CB, $03, $7E, $C2, $F7
.db $49, $DD, $CB, $03, $76, $C2, $2E, $4A, $3A, $32, $D5, $FE, $06, $20, $08, $AF
.db $32, $B0, $D3, $32, $20, $D5, $C9, $3A, $B0, $D3, $B7, $CA, $EB, $48, $AF, $32
.db $B0, $D3, $DD, $CB, $23, $86, $C3, $F7, $48, $3A, $20, $D5, $B7, $C8, $DD, $CB
.db $03, $4E, $C2, $C3, $49, $3A, $01, $D5, $FE, $11, $20, $17, $AF, $32, $32, $D5
.db $21, $A3, $D3, $CB, $9E, $CD, $9B, $18, $CD, $2D, $06, $3E, $C3, $32, $04, $DE
.db $C3, $42, $49, $3A, $9A, $D2, $B7, $CA, $84, $49, $0F, $0F, $0F, $0F, $E6, $0F
.db $3C, $FE, $08, $38, $02, $3E, $07, $47, $0E, $06, $26, $00, $C5, $CD, $9C, $5E
.db $C1, $24, $10, $F8, $AF, $32, $9A, $D2, $CD, $4A, $31, $3E, $A4, $32, $04, $DE
.db $DD, $CB, $03, $FE, $DD, $CB, $03, $F6, $3E, $78, $32, $B1, $D3, $DD, $36, $20
.db $00, $DD, $36, $02, $1E, $DD, $CB, $03, $C6, $DD, $CB, $22, $8E, $21, $00, $FC
.db $DD, $CB, $22, $46, $28, $03, $21, $00, $01, $22, $18, $D5, $21, $00, $01, $DD
.db $CB, $23, $5E, $20, $03, $21, $00, $FF, $22, $16, $D5, $21, $00, $00, $22, $75
.db $D3, $C9

X.X:                        ; Death routine
	ld   (ix+2), $1F
	set  0, (ix+3)
	ld   (ix+4), $00
	ld   hl, $FB00          ; make the sprite bounce up
	ld   (VerticalVelocity), hl ; store Vertical velocity
	ld   hl, $0000
	ld   (RAM_D375), hl
	res  1, (ix+34)
	ld   a, (CurrentLevel)
	cp   $08
	jr   nc, _LABEL_49BD_334
	ld   hl, $D293
	set  2, (hl)
	ld   a, (RAM_D44B)
	and  $80
	ld   (RAM_D44B), a
	ld   a, $96
	ld   (PlaySound), a  ; play life loss jingle
	call WaitForInterrupt
	ret

_LABEL_49BD_334:
	ld   hl, $D294
	set  5, (hl)
	ret


; Data from 49C3 to 4A73 (177 bytes)
.db $DD, $CB, $21, $66, $20, $0B, $DD, $CB, $21, $6E, $20, $18, $AF, $32, $20, $D5
.db $C9, $3A, $01, $D5, $FE, $09, $28, $F4, $DD, $CB, $03, $C6, $21, $80, $00, $22
.db $18, $D5, $18, $E8, $DD, $CB, $03, $C6, $DD, $CB, $22, $8E, $21, $00, $FD, $22
.db $18, $D5, $18, $D8, $3A, $B1, $D3, $B7, $28, $1C, $3D, $32, $B1, $D3, $DD, $7E
.db $01, $FE, $1E, $28, $07, $3A, $B1, $D3, $0F, $0F, $38, $05, $DD, $CB, $04, $BE
.db $C9, $DD, $CB, $04, $FE, $C9, $DD, $CB, $04, $BE, $DD, $CB, $03, $BE, $DD, $CB
.db $03, $B6, $AF, $32, $B0, $D3, $DD, $77, $20, $18, $E1, $DD, $36, $20, $00, $C9
.db $01, $FC, $FF, $11, $12, $00, $CD, $66, $76, $3A, $68, $D3, $47, $C5, $01, $04
.db $00, $11, $12, $00, $CD, $66, $76, $3A, $68, $D3, $C1, $4F, $90, $30, $02, $ED
.db $44, $FE, $10, $D8, $79, $B8, $28, $14, $38, $09, $DD, $36, $02, $19, $DD, $CB
.db $04, $E6, $C9, $DD, $36, $02, $19, $DD, $CB, $04, $A6, $C9, $DD, $36, $02, $01
.db $C9

MonitorChk:
	ld   a, (PowerUp)     ; power up check
	or   a
	jr   z, Monitors
	cp   $03
	jr   nz, +
	ld   hl, $0600
	ld   (RAM_D373), hl
+:
	ld   hl, (PowerUpTimer)
	dec  hl
	ld   (PowerUpTimer), hl
	ld   a, h
	or   l
	jr   nz, Monitors
	ld   a, (PowerUp)   ; get powerup
	cp   $04
	jr   z, LoadPwrUp
	cp   $06            ; is the power-up invincibility?
	jr   z, LoadPwrUp
	jr   Monitors

LoadPwrUp:
	call UpdateMusic
	xor  a            ; clear power-up flag
	ld   (PowerUp), a
Monitors:
	ld   hl, $D3A3           ; Monitors offset
	ld   a, (hl)
	bit  0, a
	jr   nz, Ring
	bit  1, a
	jr   nz, OneUp
	bit  2, a
	jr   nz, Sneakers
	bit  3, a
	jr   nz, RocketSneakers
	bit  4, a
	jr   nz, Stop_Watch
	bit  5, a
	jr   nz, Invincible
	ret

Ring:
	res  0, (hl)          ; reset bit to zero (ring monitor)
	ld   a, (Ring_Count)  ; get ring counter
	add  a, $10           ; add 10 rings
	daa
	ld   (Ring_Count), a
	call _LABEL_314A_359
	ld   a, (Ring_Count)
	cp   $10
	ret  nc

	call LivesCounterUpdate   ; call update routine
	jp   LoadSpecialStage
	


OneUp:
	res  1, (hl)           ; reset monitor array so the player can't collect the power up again
	jp   LivesCounterUpdate  ; jump to update routine

RocketSneakers:
	res  3, (hl)
	ld   a, (RAM_D500)      ; set up sprite
	dec  a
	ret  nz

	ld   a, $04
	ld   (PowerUp), a
	ld   hl, $012C          ; set power up time
	ld   a, (CurrentLevel)  ; get current level
	cp   $08                ; is Sonic in SS1?
	jr   nz, PwrUpTimerSS   ; if so, jump so the power-up doesn't run
	ld   hl, $1770          ; out before collecting a emerald or before the ss time runs out
PwrUpTimerSS:
	ld   (PowerUpTimer), hl ; get timer
	ld   ix, $D500          ; set up sprite
	jp   RocketPwrUp        ; jump to routine

Stop_Watch:
	res  4, (hl)
	ld   a, $0B
	ld   (StopWatchPwrUp), a
	ld   a, $F8
	ld   (PlaySound), a
	ret

Sneakers:
	res  2, (hl)
	ld   a, $03
	ld   (PowerUp), a   ; check for powerup
	ld   hl, $0384
	ld   (PowerUpTimer), hl
	ret

Invincible:
	res  5, (hl)
	ld   hl, $D503  ; get invincible power-up
	set  1, (hl)    ; set player as invulnerable
	set  7, (hl)
	ld   a, $84     ; load Invincibility theme
	ld   (PlaySound), a
	call WaitForInterrupt ; call interrupt so the game can find an empty obj slot
	ld   hl, $0258        ; power-up time
	ld   (PowerUpTimer), hl
	ld   a, (PowerUp)
	cp   $06              ; check for power-up
	ret  z

	ld   a, $06           ; set power-up
	ld   (PowerUp), a
	ld   c, $05
	ld   h, $00
	jp   FindEmptyObjSlot ; find an empty object slot so the stars can load



; Underwater Updates
.db $3A, $97, $D2, $FE, $04, $C0, $3A, $98, $D2, $FE, $02, $D0, $CD, $C0, $4B, $3A
.db $43, $D4, $B7, $20, $05, $AF, $32, $45, $D4, $C9, $21, $44, $D4, $34, $7E, $FE
.db $78, $D8, $36, $00, $CD, $88, $4B, $21, $45, $D4, $34, $7E, $FE, $0B, $28, $05
.db $FE, $11, $28, $08, $C9, $0E, $32, $26, $00, $C3, $9C, $5E, $3E, $1F, $32, $02
.db $D5, $C9, $ED, $5F, $E6, $04, $C0, $0E, $0C, $26, $03, $C3, $9C, $5E, $3A, $43
.db $D4, $B7, $C8, $2A, $73, $D3, $CB, $3C, $CB, $1D, $22, $73, $D3, $C9, $C9, $3A
.db $43, $D4, $B7, $C8, $DD, $34, $30, $DD, $7E, $30, $E6, $03, $C8, $11, $00, $00
.db $ED, $53, $75, $D3, $ED, $53, $77, $D3, $D1, $C9, $2A, $14, $D5, $ED, $4B, $50
.db $D4, $AF, $ED, $42, $DA, $FD, $4B, $3A, $43, $D4, $B7, $20, $07, $0E, $0E, $26
.db $00, $CD, $9C, $5E, $3E, $FF, $32, $43, $D4, $3A, $19, $D5, $CB, $7F, $C0, $DD
.db $CB, $03, $4E, $C8, $3A, $17, $D5, $CB, $7F, $28, $02, $ED, $44, $FE, $04, $D8
.db $21, $00, $FD, $22, $18, $D5, $C9, $AF, $32, $43, $D4, $C9, $DD, $CB, $04, $BE
.db $FD, $2A, $A6, $D3, $CD, $56, $4C, $FD, $CB, $04, $FE, $C9, $FD, $2A, $A6, $D3
.db $CD, $56, $4C, $CD, $3E, $75, $CD, $BC, $48, $CD, $1A, $40, $DD, $7E, $02, $FE
.db $1E, $28, $0E, $FE, $1F, $28, $0A, $DD, $CB, $03, $86, $3A, $37, $D1, $E6, $30
.db $C8, $FD, $2A, $A6, $D3, $FD, $CB, $04, $BE, $FD, $36, $1F, $10, $FD, $CB, $03
.db $F6, $FD, $7E, $3F, $FD, $77, $02, $21, $00, $00, $22, $A6, $D3, $C3, $ED, $45
.db $FD, $6E, $11, $FD, $66, $12, $22, $11, $D5, $FD, $6E, $14, $FD, $66, $15, $22
.db $14, $D5, $FD, $6E, $16, $FD, $66, $17, $22, $16, $D5, $FD, $6E, $18, $FD, $66
.db $19, $22, $18, $D5, $21, $03, $D5, $CB, $CE, $FD, $7E, $3F, $FE, $02, $28, $05
.db $DD, $CB, $04, $E6, $C9, $DD, $CB, $04, $A6, $C9

_LABEL_4C90_299:
	ld   ix, $D15E
	bit  7, (ix+0)
	ret  z

	call UpdateCurrentPos
	ld   a, (RAM_D162)
	call SwapFrame2
	call UpdateCamXPos
	call UpdateCamYPos
	call CalculateBGScroll
	set  6, (ix+0)
	ret

UpdateCamXPos:
	bit  2, (ix+0)
	jr   z, _LABEL_4CD3_320
	ld   hl, (RAM_D284)
	ld   a, h
	cp   $FF
	jr   z, _LABEL_4CF0_321
	ld   de, (RAM_D280)
	xor  a
	sbc  hl, de
	jr   c, _LABEL_4CF0_321
	ld   a, (HorizOffset)
	ld   b, a
	ld   a, (RAM_D284)
	xor  b
	jp   nz, _LABEL_52FA_322
	ret

_LABEL_4CD3_320:
	bit  3, (ix+0)
	ret  z

	ld   hl, (RAM_D284)
	ld   de, (RAM_D282)
	xor  a
	sbc  hl, de
	jr   nc, _LABEL_4CF0_321
	ld   a, (HorizOffset)
	ld   b, a
	ld   a, (RAM_D284)
	xor  b
	jp   nz, _LABEL_52FA_322
	ret

_LABEL_4CF0_321:
	ld   hl, (HorizOffset)
	ld   (RAM_D284), hl
	ret

UpdateCamYPos:
	bit  0, (ix+0)
	jr   z, _LABEL_4D1A_328
	ld   hl, (RAM_D286)
	ld   a, h
	cp   $FF
	jr   z, Update_CamYPosLimit
	ld   de, (RAM_D27C)
	xor  a
	sbc  hl, de
	jr   c, Update_CamYPosLimit
	ld   a, (VertOffset)
	ld   b, a
	ld   a, (RAM_D286)
	xor  b
	jp   nz, _LABEL_53BF_277
	ret

_LABEL_4D1A_328:
	bit  1, (ix+0)
	ret  z

	ld   hl, (RAM_D286)
	ld   de, (RAM_D27E)
	xor  a
	sbc  hl, de
	jr   nc, Update_CamYPosLimit
	ld   a, (VertOffset)
	ld   b, a
	ld   a, (RAM_D286)
	xor  b
	jp   nz, _LABEL_53BF_277
	ret

Update_CamYPosLimit:
	ld   hl, (VertOffset)
	ld   (RAM_D286), hl
	ret

CalculateBGScroll:
	ld   a, (HorizOffset)    ; get horizontal scroll
	add  a, $01           ; 2's comp the low byte
	neg
	ld   (BGXScroll), a   ; set bg x scroll
	ld   hl, (VertOffset)   ; get vertical scroll
	ld   de, $0011        ; set de to $0011
	add  hl, de           ; add v scroll and de together
	ld   de, $00E0        ; set screen height (224)
_LABEL_4D52_331:
	xor  a
	sbc  hl, de
	jr   nc, _LABEL_4D52_331
	add  hl, de
	ld   a, l
	ld   (BGYScroll), a
	ret

_LABEL_4D5D_278:
	ld   hl, (HorizOffset)
	bit  2, (ix+0)
	jr   z, _LABEL_4D6A_279
	ld   bc, $0008
	add  hl, bc
_LABEL_4D6A_279:
	srl  h
	rr   l
	srl  h
	rr   l
	srl  h
	rr   l
	srl  h
	rr   l
	srl  h
	rr   l
	ld   (RAM_D170), hl
	ld   hl, (VertOffset)
	add  hl, de
	sla  l
	rl   h
	sla  l
	rl   h
	sla  l
	rl   h
	ld   (ix+3), h
	ld   a, h
	add  a, a
	ld   l, a
	ld   h, $00
	ld   de, (RAM_D168)
	add  hl, de
	ld   e, (hl)
	inc  hl
	ld   d, (hl)
	ld   hl, (RAM_D170)
	add  hl, de
	ld   de, $C001
	add  hl, de
	ld   (RAM_D278), hl
	ret

LoadLevel_Layout:
	di                    ; disable interrrupts to start decompressing each layout
	ld   ix, $D15E        ; get layout data from headers
	ld   a, (ix+5)
	call SwapFrame2
	ld   l, (ix+8)
	ld   h, (ix+9)
	ld   de, $C001
	push hl
	pop  iy
_LABEL_4DC4_275:
	ld   a, d
	and  $F0
	cp   $C0
	jr   nz, _LABEL_4DFB_272
	ld   a, (iy+0)
	cp   $FF
	jp   nz, _LABEL_4DF1_273
	ld   a, (iy+2)
	or   a
	jp   z, _LABEL_4DFB_272
	ld   b, a
_LABEL_4DDB_274:
	ld   a, d
	and  $F0
	cp   $C0
	jr   nz, _LABEL_4DFB_272
	ld   a, (iy+1)
	ld   (de), a
	inc  de
	djnz _LABEL_4DDB_274
	ld   bc, $0003
	add  iy, bc
	jp   _LABEL_4DC4_275

_LABEL_4DF1_273:
	ld   a, (iy+0)
	ld   (de), a
	inc  de
	inc  iy
	jp   _LABEL_4DC4_275

_LABEL_4DFB_272:
	ei
	call _LABEL_4E57_276
	ld   hl, (RAM_D2D6)
	ld   (HorizOffset), hl
	ld   (RAM_D284), hl
	ld   hl, (RAM_D2D8)
	ld   (VertOffset), hl
	ld   (RAM_D286), hl
	ld   b, $1D
_LABEL_4E13_282:
	di
	push bc
	ld   hl, (VertOffset)
	ld   de, $0008
	add  hl, de
	ld   (RAM_D286), hl
	ld   a, (RAM_D162)
	call SwapFrame2
	call _LABEL_53BF_277
	set  6, (ix+0)
	call WaitForInterrupt
	pop  bc
	djnz _LABEL_4E13_282
	ld   hl, (RAM_D2D6)
	ld   (RAM_D284), hl
	ld   (HorizOffset), hl
	ld   hl, (RAM_D2D8)
	ld   (RAM_D286), hl
	ld   (VertOffset), hl
	ld   de, $0010
	add  hl, de
	ld   de, $00E0
_LABEL_4E4B_283:
	xor  a
	sbc  hl, de
	jr   nc, _LABEL_4E4B_283
	add  hl, de
	ld   a, l
	ld   (BGYScroll), a
	ei
	ret

_LABEL_4E57_276:
	ld   a, (CurrentLevel)
	ld   l, a
	ld   h, $00
	add  hl, hl
	ld   de, $4E98
	add  hl, de
	ld   e, (hl)
	inc  hl
	ld   d, (hl)
	ld   a, (CurrentAct)
	ld   l, a
	ld   h, $00
	add  hl, hl
	add  hl, de
	ld   e, (hl)
	inc  hl
	ld   d, (hl)
	push de
	pop  iy
	ld   l, (iy+0)
	ld   h, (iy+1)
	ld   (RAM_D2D6), hl
	ld   l, (iy+2)
	ld   h, (iy+3)
	ld   (RAM_D2D8), hl
	ld   l, (iy+4)
	ld   h, (iy+5)
	ld   (RAM_D511), hl
	ld   l, (iy+6)
	ld   h, (iy+7)
	ld   (RAM_D514), hl
	ret


; Level Layout Positions
.db $B8, $4E, $BE, $4E, $C4, $4E, $CA, $4E, $D0, $4E, $D6, $4E, $B8, $4E, $DC, $4E
.db $E2, $4E, $E8, $4E, $EE, $4E, $F4, $4E, $FA, $4E, $B8, $4E, $00, $4F, $00, $4F
.db $06, $4F, $0E, $4F, $16, $4F, $1E, $4F, $26, $4F, $2E, $4F, $36, $4F, $3E, $4F
.db $46, $4F, $4E, $4F, $56, $4F, $5E, $4F, $66, $4F, $6E, $4F, $76, $4F, $7E, $4F
.db $86, $4F, $8E, $4F, $96, $4F, $96, $4F, $96, $4F, $9E, $4F, $9E, $4F, $9E, $4F
.db $A6, $4F, $A6, $4F, $A6, $4F, $AE, $4F, $AE, $4F, $AE, $4F, $B6, $4F, $B6, $4F
.db $B6, $4F, $BE, $4F, $BE, $4F, $BE, $4F, $C6, $4F, $C6, $4F, $C6, $4F, $26, $00
.db $12, $02, $8E, $00, $8E, $02, $06, $00, $12, $01, $6E, $00, $8E, $01, $00, $00
.db $70, $00, $6E, $00, $E0, $00, $00, $00, $10, $01, $6E, $00, $80, $01, $00, $00
.db $50, $01, $6E, $00, $C0, $01, $4B, $00, $F0, $00, $BB, $00, $60, $01, $00, $00
.db $60, $02, $6E, $00, $CE, $02, $00, $00, $E6, $02, $6E, $00, $4E, $03, $00, $00
.db $BE, $02, $6E, $00, $35, $03, $00, $00, $50, $00, $4E, $00, $C0, $00, $00, $00
.db $BF, $01, $70, $00, $2E, $02, $00, $00, $30, $00, $6E, $00, $A0, $00, $00, $00
.db $63, $00, $6E, $00, $CE, $00, $00, $00, $BF, $01, $6E, $00, $2E, $02, $00, $00
.db $84, $00, $6E, $00, $EE, $00, $7E, $00, $F0, $02, $EE, $00, $60, $03, $3A, $00
.db $3E, $01, $AA, $00, $AE, $01, $00, $00, $B0, $00, $6E, $00, $20, $01, $08, $00
.db $08, $00, $60, $00, $8E, $00, $00, $00, $0F, $00, $6F, $00, $76, $00, $00, $00
.db $BF, $06, $6F, $00, $2E, $07, $1F, $00, $0E, $02, $8F, $00, $6E, $02, $1E, $00
.db $FE, $00, $8E, $00, $6E, $01, $1F, $00, $00, $03, $8F, $00, $6E, $03, $00, $00
.db $00, $01, $B0, $00, $70, $01

ClearLevelAttrib:
	ld   hl, $D15E
	ld   de, $D15F
	ld   bc, $0132
	ld   (hl), $00
	ldir
	ret

LoadLevelHeaders:
	ld   a, (CurrentLevel)
	ld   l, a
	ld   h, $00
	add  hl, hl
	ld   de, $5082   ; load level headers
	add  hl, de
	ld   e, (hl)
	inc  hl
	ld   d, (hl)
	ld   a, (CurrentAct)
	ld   l, a
	ld   h, $00
	add  hl, hl
	add  hl, de
	ld   e, (hl)
	inc  hl
	ld   d, (hl)
	push de
	pop  iy
	ld   ix, $D15E      ; offset where level headers start
	
        ld   a, (iy+0)
	ld   (ix+4), a      ; $D162 ($64D1 in ROM) Bank Number for 32x32 mappings
	
        ld   a, (iy+1)      ; Pointer to 32x32 mappings ($D164-$D166)
	ld   (ix+6), a
	ld   a, (iy+2)
	ld   (ix+7), a
	
        ld   a, (iy+3)      ; Bank Number for Level Layout ($D163)
	ld   (ix+5), a

	ld   a, (iy+4)      ; Pointer to Level Layout ($D166-$D167)
	ld   (ix+8), a
	ld   a, (iy+5)
	ld   (ix+9), a

	ld   a, (iy+6)
	ld   (ix+14), a
	ld   a, (iy+7)
	ld   (ix+15), a
	ld   a, (iy+8)
	ld   (ix+12), a
	ld   a, (iy+9)
	ld   (ix+13), a
	ld   a, (iy+10)
	ld   (ix+16), a
	ld   a, (iy+11)
	ld   (ix+17), a
	ld   l, (iy+12)
	ld   h, (iy+13)
	ld   (RAM_D280), hl
	ld   l, (iy+14)
	ld   h, (iy+15)
	ld   (RAM_D27C), hl
	ld   l, (iy+16)
	ld   h, (iy+17)
	ld   (RAM_D282), hl
	ld   l, (iy+18)
	ld   h, (iy+19)
	ld   (RAM_D27E), hl
	ld   a, (iy+20)
	ld   (ix+10), a
	ld   a, (iy+21)
	ld   (ix+11), a
	ld   a, $68
	ld   (X_CamOffset), a
	ld   a, $78
	ld   (Y_CamOffset), a
	call Calculate_CameraBounds
	ret


; Level Headers
.db $A2, $50, $A8, $50, $AE, $50, $B4, $50, $BA, $50, $C0, $50, $A2, $50, $C6, $50
.db $CC, $50, $D2, $50, $D8, $50, $DE, $50, $E4, $50, $A2, $50, $EA, $50, $EA, $50
.db $EA, $50, $00, $51, $16, $51, $2C, $51, $42, $51, $58, $51, $6E, $51, $84, $51
.db $9A, $51, $B0, $51, $C6, $51, $DC, $51, $F2, $51, $08, $52, $1E, $52, $34, $52
.db $4A, $52, $60, $52, $76, $52, $76, $52, $76, $52, $8C, $52, $8C, $52, $8C, $52
.db $A2, $52, $A2, $52, $A2, $52, $B8, $52, $B8, $52, $B8, $52, $CE, $52, $CE, $52
.db $CE, $52, $E4, $52, $E4, $52, $E4, $52, $11, $00, $80, $12, $00, $80, $80, $00
.db $80, $FF, $80, $03, $00, $00, $08, $00, $00, $0F, $10, $03, $97, $5A, $11, $00
.db $80, $12, $A9, $8B, $80, $00, $80, $FF, $80, $03, $00, $00, $08, $00, $00, $0F
.db $10, $03, $97, $5A, $11, $00, $80, $12, $15, $98, $50, $00, $B0, $FF, $30, $02
.db $00, $00, $08, $00, $00, $09, $10, $01, $67, $5B, $11, $40, $96, $12, $25, $9C
.db $A0, $00, $60, $FF, $60, $04, $00, $00, $08, $00, $00, $13, $10, $02, $63, $5A
.db $11, $40, $96, $12, $00, $AA, $80, $00, $80, $FF, $80, $03, $00, $00, $08, $00
.db $00, $0F, $10, $03, $97, $5A, $11, $40, $96, $12, $97, $B8, $50, $00, $B0, $FF
.db $30, $02, $00, $00, $08, $00, $00, $09, $10, $01, $67, $5B, $11, $40, $AA, $15
.db $00, $80, $80, $00, $80, $FF, $80, $03, $00, $00, $08, $00, $00, $0F, $10, $03
.db $97, $5A, $11, $40, $AA, $15, $C8, $8C, $80, $00, $80, $FF, $80, $03, $00, $00
.db $08, $00, $00, $0F, $10, $03, $97, $5A, $11, $40, $AA, $14, $60, $B4, $80, $00
.db $80, $FF, $80, $03, $00, $00, $08, $00, $00, $0F, $10, $03, $97, $5A, $14, $00
.db $80, $15, $D4, $99, $80, $00, $80, $FF, $80, $03, $00, $00, $08, $00, $00, $0F
.db $10, $03, $97, $5A, $14, $00, $80, $15, $B8, $A6, $80, $00, $80, $FF, $80, $03
.db $00, $00, $08, $00, $00, $0F, $10, $03, $97, $5A, $14, $00, $80, $15, $FB, $B2
.db $78, $00, $88, $FF, $48, $03, $00, $00, $08, $00, $00, $0E, $10, $02, $D7, $5A
.db $14, $20, $93, $17, $00, $80, $A8, $00, $58, $FF, $98, $04, $00, $00, $08, $00
.db $00, $14, $10, $02, $33, $5A, $14, $20, $93, $17, $C1, $87, $80, $00, $80, $FF
.db $80, $03, $00, $00, $08, $00, $00, $0F, $10, $03, $97, $5A, $14, $20, $93, $15
.db $F3, $BA, $50, $00, $B0, $FF, $30, $02, $00, $00, $08, $00, $00, $09, $10, $01
.db $67, $5B, $14, $E0, $A4, $17, $3A, $8F, $80, $00, $80, $FF, $80, $03, $00, $00
.db $08, $00, $00, $0F, $10, $03, $97, $5A, $14, $E0, $A4, $17, $73, $9B, $80, $00
.db $80, $FF, $80, $03, $00, $00, $08, $00, $00, $0F, $10, $03, $97, $5A, $14, $E0
.db $A4, $17, $53, $A8, $70, $00, $90, $FF, $10, $03, $00, $00, $08, $00, $00, $0D
.db $10, $03, $1D, $5B, $11, $00, $80, $17, $07, $B4, $00, $01, $00, $FF, $00, $07
.db $00, $00, $08, $00, $00, $1F, $10, $00, $13, $5A, $1B, $00, $80, $1A, $00, $80
.db $00, $02, $00, $FE, $00, $0E, $00, $00, $08, $00, $00, $3F, $10, $00, $03, $5A
.db $1B, $00, $80, $1A, $A8, $85, $18, $00, $E8, $FF, $A8, $00, $00, $00, $08, $00
.db $00, $02, $10, $07, $7B, $5C, $1B, $60, $8F, $1A, $48, $88, $80, $00, $80, $FF
.db $80, $03, $00, $00, $08, $00, $00, $0F, $10, $02, $97, $5A, $1B, $00, $80, $1A
.db $1E, $8C, $00, $01, $00, $FF, $00, $07, $00, $00, $08, $00, $00, $1F, $10, $01
.db $13, $5A, $1B, $60, $8F, $1A, $58, $92, $30, $00, $D0, $FF, $50, $01, $00, $00
.db $08, $00, $00, $05, $10, $03, $CF, $5B

_LABEL_52FA_322:
	ld   de, $0008
	call _LABEL_4D5D_278
	ld   de, $0008
	bit  3, (ix+0)
	jr   nz, _LABEL_530C_323
	ld   de, $0000
_LABEL_530C_323:
	add  hl, de
	exx
	ld   de, $D178
	exx
	ld   b, $08
_LABEL_5314_326:
	push bc
	push hl
	ld   e, (hl)
	ld   d, $00
	ex   de, hl
	add  hl, hl
	ld   bc, (RAM_D164)
	add  hl, bc
	ld   e, (hl)
	inc  hl
	ld   d, (hl)
	ld   a, (HorizOffset)
	bit  2, (ix+0)
	jr   z, _LABEL_532E_324
	add  a, $08
_LABEL_532E_324:
	rrca
	rrca
	and  $06
	ld   l, a
	ld   h, $00
	add  hl, de
	ld   b, $04
	push hl
	exx
	pop  hl
	exx
_LABEL_533C_325:
	exx
	ld   a, (hl)
	ld   (de), a
	inc  hl
	inc  de
	ld   a, (hl)
	ld   (de), a
	inc  de
	ld   a, $07
	add  a, l
	ld   l, a
	exx
	djnz _LABEL_533C_325
	pop  hl
	ld   de, (RAM_D16C)
	add  hl, de
	pop  bc
	djnz _LABEL_5314_326
	set  5, (ix+0)
	ret

_LABEL_5359_52:
	ld   hl, (VertOffset)
	ld   bc, $0008
	add  hl, bc
	srl  h
	rr   l
	srl  h
	rr   l
	srl  h
	rr   l
	add  hl, hl
	ld   bc, $547A
	add  hl, bc
	ld   c, (hl)
	inc  hl
	ld   b, (hl)
	ld   a, (HorizOffset)
	bit  2, (ix+0)
	jr   z, _LABEL_537F_53
	add  a, $08
_LABEL_537F_53:
	rrca
	rrca
	and  $3E
	ld   l, a
	ld   h, $78
	add  hl, bc
	ld   bc, $0040
	ld   d, $7F
	ld   e, $07
	exx
	ld   a, (VertOffset)
	add  a, $08
	rrca
	rrca
	and  $06
	ld   l, a
	ld   h, $00
	ld   de, $D178
	add  hl, de
	ld   b, $36
	ld   c, $BE
_LABEL_53A3_55:
	exx
	ld   a, l
	out  ($BF), a
	ld   a, h
	out  ($BF), a
	add  hl, bc
	ld   a, h
	cp   d
	jp   c, _LABEL_53B2_54
	sub  e
	ld   h, a
_LABEL_53B2_54:
	exx
	outi
	outi
	jp   nz, _LABEL_53A3_55
	res  5, (ix+0)
	ret

_LABEL_53BF_277:
	ld   de, $0000
	call _LABEL_4D5D_278
	ld   de, (RAM_D16E)
	bit  1, (ix+0)
	jr   nz, _LABEL_53D2_280
	ld   de, $0000
_LABEL_53D2_280:
	add  hl, de
	exx
	ld   de, $D1F8
	exx
	ld   b, $09
_LABEL_53DA_281:
	push bc
	push hl
	ld   e, (hl)
	ld   d, $00
	ex   de, hl
	add  hl, hl
	ld   bc, (RAM_D164)
	add  hl, bc
	ld   e, (hl)
	inc  hl
	ld   d, (hl)
	ld   a, (VertOffset)
	and  $18
	ld   l, a
	ld   h, $00
	add  hl, de
	push hl
	exx
	pop  hl
	ld   bc, $0008
	ldir
	exx
	pop  hl
	inc  hl
	pop  bc
	djnz _LABEL_53DA_281
	set  4, (ix+0)
	ret

_LABEL_5405_46:
	ld   a, (HorizOffset)
	bit  2, (ix+0)
	jr   z, _LABEL_5410_47
	add  a, $08
_LABEL_5410_47:
	rrca
	rrca
	and  $06
	ld   l, a
	ld   h, $00
	ld   de, $D1F8
	add  hl, de
	ex   de, hl
	ld   hl, (VertOffset)
	srl  h
	rr   l
	srl  h
	rr   l
	srl  h
	rr   l
	add  hl, hl
	ld   bc, $547A
	add  hl, bc
	ld   c, (hl)
	inc  hl
	ld   b, (hl)
	ld   a, (HorizOffset)
	bit  2, (ix+0)
	jr   z, _LABEL_543E_48
	add  a, $08
_LABEL_543E_48:
	rrca
	rrca
	and  $3E
	ld   l, a
	ld   h, $78
	add  hl, bc
	ld   b, $21
	bit  2, (ix+0)
	jr   z, _LABEL_544F_49
	dec  b
_LABEL_544F_49:
	ld   a, l
	out  ($BF), a
	ld   a, h
	out  ($BF), a
_LABEL_5455_51:
	ld   a, (de)
	out  ($BE), a
	inc  de
	inc  hl
	ld   a, (de)
	out  ($BE), a
	inc  de
	inc  hl
	ld   a, l
	and  $3F
	jp   nz, _LABEL_5473_50
	push de
	ld   de, $0040
	or   a
	sbc  hl, de
	ld   a, l
	out  ($BF), a
	ld   a, h
	out  ($BF), a
	pop  de
_LABEL_5473_50:
	djnz _LABEL_5455_51
	res  4, (ix+0)
	ret


; Data from 547A to 5831 (952 bytes)
.db $00, $00, $40, $00, $80, $00, $C0, $00, $00, $01, $40, $01, $80, $01, $C0, $01
.db $00, $02, $40, $02, $80, $02, $C0, $02, $00, $03, $40, $03, $80, $03, $C0, $03
.db $00, $04, $40, $04, $80, $04, $C0, $04, $00, $05, $40, $05, $80, $05, $C0, $05
.db $00, $06, $40, $06, $80, $06, $C0, $06, $00, $00, $40, $00, $80, $00, $C0, $00
.db $00, $01, $40, $01, $80, $01, $C0, $01, $00, $02, $40, $02, $80, $02, $C0, $02
.db $00, $03, $40, $03, $80, $03, $C0, $03, $00, $04, $40, $04, $80, $04, $C0, $04
.db $00, $05, $40, $05, $80, $05, $C0, $05, $00, $06, $40, $06, $80, $06, $C0, $06
.db $00, $00, $40, $00, $80, $00, $C0, $00, $00, $01, $40, $01, $80, $01, $C0, $01
.db $00, $02, $40, $02, $80, $02, $C0, $02, $00, $03, $40, $03, $80, $03, $C0, $03
.db $00, $04, $40, $04, $80, $04, $C0, $04, $00, $05, $40, $05, $80, $05, $C0, $05
.db $00, $06, $40, $06, $80, $06, $C0, $06, $00, $00, $40, $00, $80, $00, $C0, $00
.db $00, $01, $40, $01, $80, $01, $C0, $01, $00, $02, $40, $02, $80, $02, $C0, $02
.db $00, $03, $40, $03, $80, $03, $C0, $03, $00, $04, $40, $04, $80, $04, $C0, $04
.db $00, $05, $40, $05, $80, $05, $C0, $05, $00, $06, $40, $06, $80, $06, $C0, $06
.db $00, $00, $40, $00, $80, $00, $C0, $00, $00, $01, $40, $01, $80, $01, $C0, $01
.db $00, $02, $40, $02, $80, $02, $C0, $02, $00, $03, $40, $03, $80, $03, $C0, $03
.db $00, $04, $40, $04, $80, $04, $C0, $04, $00, $05, $40, $05, $80, $05, $C0, $05
.db $00, $06, $40, $06, $80, $06, $C0, $06, $00, $00, $40, $00, $80, $00, $C0, $00
.db $00, $01, $40, $01, $80, $01, $C0, $01, $00, $02, $40, $02, $80, $02, $C0, $02
.db $00, $03, $40, $03, $80, $03, $C0, $03, $00, $04, $40, $04, $80, $04, $C0, $04
.db $00, $05, $40, $05, $80, $05, $C0, $05, $00, $06, $40, $06, $80, $06, $C0, $06
.db $00, $00, $40, $00, $80, $00, $C0, $00, $00, $01, $40, $01, $80, $01, $C0, $01
.db $00, $02, $40, $02, $80, $02, $C0, $02, $00, $03, $40, $03, $80, $03, $C0, $03
.db $00, $04, $40, $04, $80, $04, $C0, $04, $00, $05, $40, $05, $80, $05, $C0, $05
.db $00, $06, $40, $06, $80, $06, $C0, $06, $00, $00, $40, $00, $80, $00, $C0, $00
.db $00, $01, $40, $01, $80, $01, $C0, $01, $00, $02, $40, $02, $80, $02, $C0, $02
.db $00, $03, $40, $03, $80, $03, $C0, $03, $00, $04, $40, $04, $80, $04, $C0, $04
.db $00, $05, $40, $05, $80, $05, $C0, $05, $00, $06, $40, $06, $80, $06, $C0, $06
.db $00, $00, $40, $00, $80, $00, $C0, $00, $00, $01, $40, $01, $80, $01, $C0, $01
.db $00, $02, $40, $02, $80, $02, $C0, $02, $00, $03, $40, $03, $80, $03, $C0, $03
.db $00, $04, $40, $04, $80, $04, $C0, $04, $00, $05, $40, $05, $80, $05, $C0, $05
.db $00, $06, $40, $06, $80, $06, $C0, $06, $00, $00, $40, $00, $80, $00, $C0, $00
.db $00, $01, $40, $01, $80, $01, $C0, $01, $00, $02, $40, $02, $80, $02, $C0, $02
.db $00, $03, $40, $03, $80, $03, $C0, $03, $00, $04, $40, $04, $80, $04, $C0, $04
.db $00, $05, $40, $05, $80, $05, $C0, $05, $00, $06, $40, $06, $80, $06, $C0, $06
.db $00, $00, $40, $00, $80, $00, $C0, $00, $00, $01, $40, $01, $80, $01, $C0, $01
.db $00, $02, $40, $02, $80, $02, $C0, $02, $00, $03, $40, $03, $80, $03, $C0, $03
.db $00, $04, $40, $04, $80, $04, $C0, $04, $00, $05, $40, $05, $80, $05, $C0, $05
.db $00, $06, $40, $06, $80, $06, $C0, $06, $00, $00, $40, $00, $80, $00, $C0, $00
.db $00, $01, $40, $01, $80, $01, $C0, $01, $00, $02, $40, $02, $80, $02, $C0, $02
.db $00, $03, $40, $03, $80, $03, $C0, $03, $00, $04, $40, $04, $80, $04, $C0, $04
.db $00, $05, $40, $05, $80, $05, $C0, $05, $00, $06, $40, $06, $80, $06, $C0, $06
.db $00, $00, $40, $00, $80, $00, $C0, $00, $00, $01, $40, $01, $80, $01, $C0, $01
.db $00, $02, $40, $02, $80, $02, $C0, $02, $00, $03, $40, $03, $80, $03, $C0, $03
.db $00, $04, $40, $04, $80, $04, $C0, $04, $00, $05, $40, $05, $80, $05, $C0, $05
.db $00, $06, $40, $06, $80, $06, $C0, $06, $00, $00, $40, $00, $80, $00, $C0, $00
.db $00, $01, $40, $01, $80, $01, $C0, $01, $00, $02, $40, $02, $80, $02, $C0, $02
.db $00, $03, $40, $03, $80, $03, $C0, $03, $00, $04, $40, $04, $80, $04, $C0, $04
.db $00, $05, $40, $05, $80, $05, $C0, $05, $00, $06, $40, $06, $80, $06, $C0, $06
.db $00, $00, $40, $00, $80, $00, $C0, $00, $00, $01, $40, $01, $80, $01, $C0, $01
.db $00, $02, $40, $02, $80, $02, $C0, $02, $00, $03, $40, $03, $80, $03, $C0, $03
.db $00, $04, $40, $04, $80, $04, $C0, $04, $00, $05, $40, $05, $80, $05, $C0, $05
.db $00, $06, $40, $06, $80, $06, $C0, $06, $00, $00, $40, $00, $80, $00, $C0, $00
.db $00, $01, $40, $01, $80, $01, $C0, $01, $00, $02, $40, $02, $80, $02, $C0, $02
.db $00, $03, $40, $03, $80, $03, $C0, $03, $00, $04, $40, $04, $80, $04, $C0, $04
.db $00, $05, $40, $05, $80, $05, $C0, $05, $00, $06, $40, $06, $80, $06, $C0, $06
.db $00, $00, $40, $00, $80, $00, $C0, $00, $00, $01, $40, $01, $80, $01, $C0, $01
.db $00, $02, $40, $02, $80, $02, $C0, $02, $00, $03, $40, $03, $80, $03, $C0, $03
.db $00, $04, $40, $04, $80, $04, $C0, $04, $00, $05, $40, $05, $80, $05, $C0, $05
.db $00, $06, $40, $06, $80, $06, $C0, $06

UpdateCurrentPos:
	ld   a, (RAM_D15E)
	and  $F0
	ld   (RAM_D15E), a
	bit  0, (ix+1)
	jp   nz, _LABEL_5956_301
	call _LABEL_58E1_302
	ld   a, (RAM_D28A)
	ld   b, a
	ld   hl, (RAM_D511)
	ld   de, (RAM_D284)
	xor  a
	sbc  hl, de
	jr   z, _LABEL_5894_309
	ld   a, l
	cp   b
	jr   c, _LABEL_5876_310
	ld   a, (RightBound)
	ld   b, a
	ld   a, l
	cp   b
	jr   c, _LABEL_5894_309
	sub  b
	cp   $08
	jr   c, _LABEL_5867_311
	ld   a, $07
_LABEL_5867_311:
	ld   l, a
	ld   de, (HorizOffset)
	add  hl, de
	ld   (RAM_D284), hl
	set  3, (ix+0)
	jr   _LABEL_5894_309

_LABEL_5876_310:
	ld   a, (LeftBound)
	ld   b, a
	ld   a, l
	cp   b
	jr   nc, _LABEL_5894_309
	sub  b
	cp   $F8
	jr   nc, _LABEL_5885_312
	ld   a, $F9
_LABEL_5885_312:
	ld   l, a
	ld   h, $FF
	ld   de, (HorizOffset)
	add  hl, de
	ld   (RAM_D284), hl
	set  2, (ix+0)
_LABEL_5894_309:
	ld   a, (RAM_D28D)
	ld   b, a
	ld   hl, (RAM_D514)
	ld   de, (RAM_D286)
	xor  a
	sbc  hl, de
	ret  z

	ld   a, l
	cp   b
	jr   c, _LABEL_58C3_313
	ld   a, (BottomBound)
	ld   b, a
	ld   a, l
	cp   b
	ret  c

	sub  b
	cp   $08
	jr   c, _LABEL_58B5_314
	ld   a, $07
_LABEL_58B5_314:
	ld   l, a
	ld   de, (VertOffset)
	add  hl, de
	ld   (RAM_D286), hl
	set  1, (ix+0)
	ret

_LABEL_58C3_313:
	ld   a, (TopBound)
	ld   b, a
	ld   a, l
	cp   b
	ret  nc

	sub  b
	cp   $F8
	jr   nc, _LABEL_58D1_315
	ld   a, $F9
_LABEL_58D1_315:
	ld   l, a
	ld   h, $FF
	ld   de, (VertOffset)
	add  hl, de
	ld   (RAM_D286), hl
	set  0, (ix+0)
	ret

_LABEL_58E1_302:
	ld   b, $78
	ld   a, (RAM_D15F)
	and  $03
	jr   nz, _LABEL_58F5_303
	ld   b, $68
	ld   a, (RAM_D504)
	bit  4, a
	jr   z, _LABEL_58F5_303
	ld   b, $88
_LABEL_58F5_303:
	ld   a, b
	ld   (X_CamOffset), a
	ld   a, (RAM_D28A)
	ld   b, a
	ld   a, (X_CamOffset)
	cp   b
	jr   z, _LABEL_5917_304
	jr   c, _LABEL_5908_305
	inc  b
	jr   SetLeftRightBounds

_LABEL_5908_305:
	dec  b
SetLeftRightBounds:
	ld   a, b
	ld   (RAM_D28A), a
	sub  $08
	ld   (LeftBound), a
	add  a, $10
	ld   (RightBound), a
_LABEL_5917_304:
	ld   a, (RAM_D28D)
	ld   b, a
	ld   a, (Y_CamOffset)
	cp   b
	ret  z

	jr   c, _LABEL_5925_307
	inc  b
	jr   SetTopBottomBounds

_LABEL_5925_307:
	dec  b
SetTopBottomBounds:
	ld   a, b
	ld   (RAM_D28D), a  ; set camera bounds
	sub  $10
	ld   (TopBound), a
	add  a, $20
	ld   (BottomBound), a
	ret

Calculate_CameraBounds:
	ld   a, (X_CamOffset)
	ld   (RAM_D28A), a
	sub  $08
	ld   (LeftBound), a
	add  a, $10
	ld   (RightBound), a
	ld   a, (Y_CamOffset)
	ld   (RAM_D28D), a
	sub  $10
	ld   (TopBound), a
	add  a, $20
	ld   (BottomBound), a
	ret

_LABEL_5956_301:
	ld   hl, (RAM_D2DA)
	ld   de, (HorizOffset)
	xor  a
	sbc  hl, de
	jr   z, _LABEL_5992_316
	jr   c, _LABEL_597C_317
	inc  de
	ld   (RAM_D284), de
	set  3, (ix+0)
	ld   a, (CurrentLevel)
	cp   $06
	jr   z, _LABEL_5992_316
	ld   hl, (RAM_D2DA)
	ld   (RAM_D282), hl
	jr   _LABEL_5992_316

_LABEL_597C_317:
	dec  de
	ld   (RAM_D284), de
	set  2, (ix+0)
	ld   a, (CurrentLevel)
	cp   $06
	jr   z, _LABEL_5992_316
	ld   hl, (RAM_D2DA)
	ld   (RAM_D280), hl
_LABEL_5992_316:
	ld   hl, (RAM_D2DC)
	ld   de, (VertOffset)
	xor  a
	sbc  hl, de
	ret  z

	jr   c, _LABEL_59A9_318
	inc  de
	ld   (RAM_D286), de
	set  1, (ix+0)
	ret

_LABEL_59A9_318:
	dec  de
	ld   (RAM_D286), de
	set  0, (ix+0)
	ret

_LABEL_59B3_294:
	ld   hl, $D15E
	set  7, (hl)
	ret


; Data from 59B9 to 5DD0 (1048 bytes)
.incbin "SonicChaos.sms.dat.16"

_LABEL_5DD1_363:
	xor  a
	ld   (RAM_D521), a
	ld   ix, $D540
	ld   b, $13
_LABEL_5DDB_370:
	push bc
	ld   a, $FF
	ld   (RAM_D44F), a
	call _LABEL_5DF1_364
	xor  a
	ld   (RAM_D44F), a
	ld   de, $0040
	add  ix, de
	pop  bc
	djnz _LABEL_5DDB_370
	ret

_LABEL_5DF1_364:
	ld   a, (ix+0)
	or   a
	ret  z

	cp   $F0
	jr   nc, _LABEL_5E61_365
	ld   a, (ix+0)
	cp   $26
	jr   nc, _LABEL_5E31_366
	ld   a, $FF
	ld   (RAM_D44F), a
	ld   a, $0C
	ld   (RAM_D12B), a
	ld   ($FFFF), a
	call _LABEL_64FA_335
	xor  a
	ld   (RAM_D44F), a
	ld   a, $FF
	ld   (RAM_D44F), a
	ld   a, $0C
	ld   (RAM_D12B), a
	ld   ($FFFF), a
	call _LABEL_5E91_343
	xor  a
	ld   (RAM_D44F), a
	ld   a, (ix+1)
	or   a
	ret  z

	jp   _LABEL_61E1_367

_LABEL_5E31_366:
	ld   a, $FF
	ld   (RAM_D44F), a
	ld   a, $1E
	ld   (RAM_D12B), a
	ld   ($FFFF), a
	call _LABEL_64FA_335
	xor  a
	ld   (RAM_D44F), a
	ld   a, $FF
	ld   (RAM_D44F), a
	ld   a, $1E
	ld   (RAM_D12B), a
	ld   ($FFFF), a
	call _LABEL_5E91_343
	xor  a
	ld   (RAM_D44F), a
	ld   a, (ix+1)
	or   a
	ret  z

	jp   _LABEL_61E1_367

_LABEL_5E61_365:
	and  $0F
	add  a, a
	ld   l, a
	ld   h, $00
	ld   de, $5E70
	add  hl, de
	ld   e, (hl)
	inc  hl
	ld   d, (hl)
	ex   de, hl
	jp   (hl)


; Data from 5E70 to 5E90 (33 bytes)
.db $90, "^", $90, "^", $90, "^", $90, "^", $90, "^", $90, "^", $90, "^", $90, "^", $90, ""
.db "^", $90, "^", $90, "^", $90, "^", $90, "^", $90, "^mb", $F8, "^", $C9

_LABEL_5E91_343:        ; called on collision
	ld   l, (ix+12)
	ld   h, (ix+13)
	ld   a, h
	or   l
	ret  z

	jp   (hl)
        ret

FindEmptyObjSlot:            ; Find an empty object slot
	ld   iy, $D540
	ld   b, $10
	ld   de, $0040
_LABEL_5EA5_288:
	ld   a, (iy+0)
	or   a
	jr   z, _LABEL_5EB0_287
	add  iy, de
	djnz _LABEL_5EA5_288
	ret

_LABEL_5EB0_287:
	ld   (iy+0), c
	ld   (iy+63), h
	ret


;Data from 5EB7 to 5EE0 (42 bytes)
.db $D9, $FD, $21, $40, $D5, $06, $10, $11, $40, $00, $FD, $7E, $00, $B7, $28, $06
.db $FD, $19, $10, $F6, $D9, $C9, $D9, $FD, $70, $00, $FD, $71, $3F, $FD, $72, $12
.db $FD, $73, $11, $FD, $74, $15, $FD, $75, $14, $C9

FindEmptyObjSlotBadnik:
	ld   iy, $D700
	ld   de, $0040
	ld   b, $0B
_LABEL_5EEA_395:
	ld   a, (iy+0)
	or   a
	jr   z, _LABEL_5EF6_394
	add  iy, de
	djnz _LABEL_5EEA_395
	scf
	ret

_LABEL_5EF6_394:
	xor  a
	ret


; Data from 5EF8 to 61E0 (745 bytes)
.db $DD, $7E, $3E, $B7, $CA, $09, $5F, $3D, $5F, $16, $00, $21, $00, $D4, $19, $36
.db $00, $DD, $E5, $E1, $36, $00, $5D, $54, $13, $01, $3F, $00, $ED, $B0, $C9, $DD
.db $E5, $DD, $21, $00, $D5, $DD, $36, $21, $00, $CD, $0C, $48, $DD, $E1, $C9, $ED
.db $4B, $11, $D5, $ED, $5B, $14, $D5, $19, $DD, $71, $11, $DD, $70, $12, $DD, $75
.db $14, $DD, $74, $15, $C9, $DD, $7E, $21, $E6, $0F, $C8, $3A, $32, $D5, $FE, $06
.db $28, $06, $3A, $03, $D5, $CB, $4F, $C8, $DD, $36, $3F, $80, $CD, $77, $5F, $DD
.db $36, $00, $0F, $AF, $DD, $77, $01, $DD, $77, $02, $DD, $77, $04, $DD, $77, $07
.db $DD, $77, $0E, $DD, $77, $0F, $DD, $36, $3E, $00, $DD, $36, $3F, $00, $C9, $DD
.db $7E, $00, $FE, $50, $D0, $C8, $21, $EB, $27, $C3, $2F, $26, $DD, $6E, $18, $DD
.db $66, $19, $19, $5D, $54, $CB, $7C, $20, $08, $AF, $ED, $42, $38, $03, $C9, $59
.db $50, $DD, $73, $18, $DD, $72, $19, $C9, $CD, $28, $63, $C3, $A6, $5F, $DD, $7E
.db $21, $E6, $0F, $C8, $87, $5F, $16, $00, $21, $B9, $5F, $19, $7E, $23, $66, $6F
.db $E9, $D9, $5F, $F1, $5F, $DA, $5F, $D9, $5F, $38, $60, $D9, $5F, $D9, $5F, $D9
.db $5F, $09, $60, $D9, $5F, $D9, $5F, $D9, $5F, $D9, $5F, $D9, $5F, $D9, $5F, $D9
.db $5F, $C9, $3A, $23, $D5, $CB, $4F, $C0, $3A, $2D, $D5, $5F, $16, $00, $DD, $6E
.db $14, $DD, $66, $15, $19, $22, $14, $D5, $C9, $3A, $23, $D5, $CB, $47, $C0, $DD
.db $5E, $2D, $16, $00, $DD, $6E, $14, $DD, $66, $15, $AF, $ED, $52, $22, $14, $D5
.db $C9, $3A, $23, $D5, $CB, $5F, $C0, $2A, $74, $D1, $11, $20, $00, $19, $ED, $5B
.db $11, $D5, $AF, $ED, $52, $D0, $DD, $5E, $2C, $16, $00, $3A, $2C, $D5, $6F, $26
.db $00, $19, $EB, $DD, $6E, $11, $DD, $66, $12, $AF, $ED, $52, $22, $11, $D5, $C9
.db $3A, $23, $D5, $CB, $57, $C0, $2A, $74, $D1, $11, $E0, $00, $19, $ED, $5B, $11
.db $D5, $AF, $ED, $52, $D8, $DD, $5E, $2C, $16, $00, $3A, $2C, $D5, $6F, $26, $00
.db $19, $EB, $DD, $6E, $11, $DD, $66, $12, $19, $22, $11, $D5, $C9, $C9, $AF, $DD
.db $77, $1F, $C9, $11, $00, $D5, $AF, $ED, $52, $7C, $CB, $25, $17, $CB, $25, $17
.db $3C, $C9, $3D, $67, $AF, $CB, $3C, $1F, $CB, $3C, $1F, $6F, $11, $00, $D5, $19
.db $C9, $AF, $DD, $77, $16, $DD, $77, $17, $DD, $77, $18, $DD, $77, $19, $DD, $7E
.db $0B, $B7, $C8, $16, $00, $DD, $5E, $0A, $21, $00, $02, $19, $7E, $5F, $E6, $80
.db $07, $ED, $44, $57, $21, $00, $00, $DD, $46, $0B, $19, $10, $FD, $7D, $CB, $2C
.db $1F, $CB, $2C, $1F, $CB, $2C, $1F, $CB, $2C, $1F, $DD, $77, $16, $DD, $74, $17
.db $DD, $7E, $0A, $C6, $C0, $5F, $16, $00, $21, $00, $02, $19, $7E, $5F, $E6, $80
.db $07, $ED, $44, $57, $21, $00, $00, $DD, $46, $0B, $19, $10, $FD, $7D, $CB, $2C
.db $1F, $CB, $2C, $1F, $CB, $2C, $1F, $CB, $2C, $1F, $DD, $77, $18, $DD, $74, $19
.db $C9, $C9, $C9, $DD, $6E, $10, $DD, $66, $11, $DD, $5E, $16, $DD, $56, $17, $DD
.db $46, $12, $7A, $E6, $80, $07, $3D, $2F, $19, $88, $DD, $77, $12, $DD, $75, $10
.db $DD, $74, $11, $DD, $6E, $13, $DD, $66, $14, $DD, $5E, $18, $DD, $56, $19, $DD
.db $46, $15, $7A, $E6, $80, $07, $3D, $2F, $19, $88, $DD, $77, $15, $DD, $75, $13
.db $DD, $74, $14, $C9, $3A, $00, $D5, $FE, $01, $C8, $3A, $02, $D5, $FE, $18, $C0
.db $3E, $0E, $32, $02, $D5, $C9, $11, $00, $00, $01, $00, $00, $CD, $25, $77, $3A
.db $64, $D3, $CB, $77, $20, $07, $CB, $7F, $20, $03, $3E, $FF, $C9, $3E, $00, $C9
.db $11, $F0, $FF, $01, $00, $00, $CD, $25, $77, $3A, $64, $D3, $CB, $7F, $20, $03
.db $3E, $FF, $C9, $3E, $00, $C9, $DD, $66, $12, $DD, $6E, $11, $ED, $5B, $11, $D5
.db $01, $0C, $00, $CD, $BB, $61, $B7, $C8, $DD, $66, $15, $DD, $6E, $14, $ED, $5B
.db $14, $D5, $01, $0C, $00, $CD, $BB, $61, $B7, $C8, $3E, $FF, $C9, $DD, $66, $12
.db $DD, $6E, $11, $ED, $5B, $11, $D5, $18, $0A, $DD, $66, $15, $DD, $6E, $14, $ED
.db $5B, $14, $D5, $AF, $ED, $52, $16, $00, $CB, $7C, $28, $09, $2B, $7C, $2F, $67
.db $7D, $2F, $6F, $16, $FF, $AF, $ED, $42, $3E, $00, $D0, $3E, $FF, $C9, $3A, $04
.db $DE, $B7, $C0, $3E, $C4, $32, $04, $DE, $C9

_LABEL_61E1_367:
	res  6, (ix+4)
	ld   l, (ix+17)
	ld   h, (ix+18)
	ld   bc, $0080
	add  hl, bc
	ld   bc, (HorizOffset)
	xor  a
	sbc  hl, bc
	jp   c, _LABEL_624C_368
	srl  h
	rr   l
	ld   a, h
	or   a
	jp   nz, _LABEL_624C_368
	ld   e, l
	ld   l, (ix+20)
	ld   h, (ix+21)
	ld   bc, $0080
	add  hl, bc
	ld   bc, (VertOffset)
	xor  a
	sbc  hl, bc
	jp   c, _LABEL_624C_368
	srl  h
	rr   l
	ld   a, h
	or   a
	jp   nz, _LABEL_624C_368
	ld   a, e
	rrca
	rrca
	rrca
	and  $1F
	ld   e, a
	ld   a, l
	and  $F8
	ld   l, a
	ld   h, $00
	ld   d, $00
	add  hl, hl
	add  hl, hl
	add  hl, de
	ld   de, $8146
	add  hl, de
	ld   a, $1C
	ld   (RAM_D12B), a
	ld   ($FFFF), a
	ld   a, (hl)
	cp   $03
	jp   z, _LABEL_624C_368
	and  $02
	ret  z

	set  6, (ix+4)
	ret

_LABEL_624C_368:
	set  6, (ix+4)
	bit  1, (ix+4)
	ret  nz

	ld   a, (ix+62)
	or   a
	jr   z, _LABEL_6264_369
	ld   (ix+0), $FE
	ld   (ix+1), $00
	ret

_LABEL_6264_369:
	ld   (ix+0), $FF
	ld   (ix+1), $00
	ret


; Data from 626D to 64F9 (653 bytes)
.db $DD, $36, $00, $FF, $DD, $36, $01, $00, $C9, $AF, $F5, $21, $AD, $62, $87, $87
.db $16, $00, $5F, $19, $5E, $23, $56, $23, $22, $1C, $D1, $2A, $BF, $D2, $AF, $ED
.db $52, $38, $04, $F1, $3C, $18, $E3, $F1, $ED, $5B, $1C, $D1, $1A, $6F, $13, $1A
.db $67, $3A, $9A, $D2, $D6, $11, $27, $85, $27, $6F, $30, $03, $7C, $3C, $27, $C9
.db $29, $00, $00, $09, $59, $00, $00, $08, $29, $01, $00, $07, $59, $01, $00, $06
.db $29, $02, $00, $05, $59, $02, $00, $04, $29, $03, $00, $03, $59, $03, $00, $02
.db $59, $04, $00, $01, $FF, $FF, $00, $00, $DD, $66, $12, $DD, $6E, $11, $DD, $CB
.db $17, $7E, $20, $09, $DD, $56, $3B, $DD, $5E, $3A, $EB, $18, $06, $DD, $56, $38
.db $DD, $5E, $37, $AF, $ED, $52, $D0, $3E, $FF, $C9, $DD, $66, $17, $DD, $6E, $16
.db $2B, $7C, $2F, $67, $7D, $2F, $6F, $DD, $74, $17, $DD, $75, $16, $C9, $CD, $28
.db $63, $DD, $7E, $21, $E6, $0F, $C8, $3E, $FF, $32, $B0, $D3, $C9, $DD, $66, $19
.db $DD, $6E, $18, $19, $DD, $74, $19, $DD, $75, $18, $C9, $AF, $DD, $77, $20, $DD
.db $7E, $21, $E6, $F0, $DD, $77, $21, $DD, $CB, $03, $76, $C0, $DD, $CB, $03, $7E
.db $20, $06, $3A, $03, $D5, $CB, $77, $C0, $2A, $11, $D5, $DD, $5E, $11, $DD, $56
.db $12, $AF, $ED, $52, $38, $17, $7C, $B7, $C2, $02, $64, $3A, $2C, $D5, $DD, $86
.db $2C, $95, $DA, $02, $64, $4F, $DD, $CB, $21, $D6, $C3, $85, $63, $7C, $3C, $C2
.db $02, $64, $7D, $ED, $44, $CA, $02, $64, $6F, $3A, $2C, $D5, $DD, $86, $2C, $95
.db $DA, $02, $64, $4F, $DD, $CB, $21, $DE, $2A, $14, $D5, $DD, $5E, $14, $DD, $56
.db $15, $AF, $ED, $52, $38, $12, $7C, $B7, $20, $6B, $3A, $2D, $D5, $95, $38, $65
.db $6F, $DD, $CB, $21, $CE, $C3, $BA, $63, $7C, $3C, $20, $59, $7D, $ED, $44, $28
.db $54, $6F, $DD, $7E, $2D, $95, $38, $4D, $6F, $DD, $CB, $21, $C6, $79, $BD, $06
.db $0C, $38, $02, $06, $03, $DD, $7E, $21, $A0, $DD, $77, $21, $3A, $03, $D5, $CB
.db $7F, $20, $04, $DD, $36, $20, $01, $DD, $CB, $03, $7E, $20, $09, $DD, $E5, $E1
.db $CD, $6B, $60, $32, $20, $D5, $DD, $7E, $21, $E6, $0F, $47, $E6, $03, $0E, $0C
.db $28, $02, $0E, $03, $78, $A9, $07, $07, $07, $07, $47, $3A, $21, $D5, $E6, $0F
.db $B0, $32, $21, $D5, $C9, $DD, $7E, $21, $E6, $F0, $DD, $77, $21, $C9, $AF, $DD
.db $77, $20, $DD, $7E, $21, $E6, $F0, $DD, $77, $21, $DD, $CB, $03, $76, $C0, $DD
.db $CB, $03, $7E, $20, $06, $3A, $03, $D5, $CB, $77, $C0, $2A, $11, $D5, $DD, $5E
.db $11, $DD, $56, $12, $AF, $ED, $52, $38, $16, $7C, $B7, $C2, $C2, $64, $3A, $2C
.db $D5, $DD, $86, $2C, $95, $DA, $C2, $64, $DD, $CB, $21, $D6, $C3, $66, $64, $7C
.db $3C, $C2, $C2, $64, $7D, $ED, $44, $CA, $C2, $64, $6F, $3A, $2C, $D5, $DD, $86
.db $2C, $95, $DA, $C2, $64, $DD, $CB, $21, $DE, $2A, $14, $D5, $DD, $5E, $14, $DD
.db $56, $15, $AF, $ED, $52, $38, $11, $7C, $B7, $20, $4A, $3A, $2D, $D5, $95, $38
.db $44, $DD, $CB, $21, $CE, $C3, $99, $64, $7C, $3C, $20, $39, $7D, $ED, $44, $28
.db $34, $6F, $DD, $7E, $2D, $95, $38, $2D, $DD, $CB, $21, $C6, $DD, $36, $21, $0F
.db $3A, $03, $D5, $CB, $7F, $20, $04, $DD, $36, $20, $01, $DD, $CB, $03, $7E, $20
.db $09, $DD, $E5, $E1, $CD, $6B, $60, $32, $20, $D5, $3A, $21, $D5, $E6, $0F, $F6
.db $F0, $32, $21, $D5, $C9, $DD, $7E, $21, $E6, $F0, $DD, $77, $21, $C9, $DD, $46
.db $22, $3A, $C0, $D3, $B7, $20, $0D, $DD, $CB, $03, $4E, $20, $12, $3A, $03, $D5
.db $CB, $7F, $20, $0B, $DD, $7E, $21, $0F, $0F, $0F, $0F, $E6, $0F, $B0, $47, $DD
.db $70, $23, $C9, $DD, $36, $00, $FE, $C9, $DD, $36, $00, $FF, $C9

_LABEL_64FA_335:
	ld   a, (ix+14)
	or   (ix+15)
	jr   z, _LABEL_651D_336
	bit  3, (ix+3)
	jr   nz, _LABEL_6510_337
	ld   a, (ix+2)
	cp   (ix+1)
	jr   nz, _LABEL_6517_338
_LABEL_6510_337:
	dec  (ix+7)
	jp   z, _LABEL_653D_339
	ret

_LABEL_6517_338:
	ld   a, (ix+2)
	ld   (ix+1), a
_LABEL_651D_336:
	ld   a, (ix+0)
	dec  a
	add  a, a
	ld   l, a
	ld   h, $00
	ld   de, $65BA
	add  hl, de
	ld   e, (hl)
	inc  hl
	ld   d, (hl)
	ld   a, (ix+1)
	add  a, a
	ld   l, a
	ld   h, $00
	add  hl, de
	ld   e, (hl)
	inc  hl
	ld   d, (hl)
	ld   (ix+14), e
	ld   (ix+15), d
_LABEL_653D_339:
	ld   l, (ix+14)
	ld   h, (ix+15)
	ld   a, (hl)
	cp   $FF
	jp   z, _LABEL_6680_340
	ld   (ix+7), a
	inc  hl
	ld   a, (hl)
	ld   (ix+6), a
	inc  hl
	ld   a, (hl)
	ld   (ix+12), a
	inc  hl
	ld   a, (hl)
	ld   (ix+13), a
	inc  hl
	ld   (ix+14), l
	ld   (ix+15), h
	ld   a, $0F
	call SwapFrame2
	ld   l, (ix+0)
	ld   h, $00
	add  hl, hl
	ld   de, $8000
	add  hl, de
	ld   e, (hl)
	inc  hl
	ld   d, (hl)
	ld   l, (ix+6)
	ld   h, $00
	add  hl, hl
	add  hl, de
	ld   e, (hl)
	inc  hl
	ld   d, (hl)
	ex   de, hl
	ld   a, (hl)
	bit  3, (ix+4)
	jr   z, _LABEL_6590_341
	or   a
	jr   z, _LABEL_6590_341
	inc  a
	jr   z, _LABEL_658D_342
	dec  a
_LABEL_658D_342:
	or   $80
	xor  a
_LABEL_6590_341:
	ld   (ix+5), a
	inc  hl
	ld   a, (hl)
	ld   (ix+44), a
	inc  hl
	ld   a, (hl)
	ld   (ix+45), a
	inc  hl
	ld   a, (hl)
	ld   (ix+40), a
	inc  hl
	ld   a, (hl)
	ld   (ix+41), a
	inc  hl
	ld   (ix+42), l
	ld   (ix+43), h
	ret


; Data from 65AF to 667F (209 bytes)
.db $E5, $23, $7E, $23, $7E, $23, $7E, $23, $7E, $E1, $C9, $00, $80, $BB, $89, $2A
.db $98, $6E, $98, $3D, $99, $FB, $99, $FE, $9A, $C8, $9B, $C8, $9B, $58, $9C, $AC
.db $9C, $AC, $9C, $9B, $9D, $8B, $9F, $C9, $9F, $01, $A1, $2D, $A2, $55, $A2, $8A
.db $A2, $AF, $A3, $12, $A4, $1E, $A5, $82, $A5, $BC, $A7, $4F, $AA, $9F, $AB, $4A
.db $AC, $59, $AD, $E4, $AD, $2A, $AE, $B3, $AE, $D0, $B0, $B6, $B1, $F9, $B2, $D9
.db $B3, $45, $B4, $0D, $B5, $12, $82, $47, $89, $39, $84, $47, $89, $47, $89, $47
.db $89, $47, $89, $45, $8A, $45, $8A, $1A, $8B, $12, $82, $68, $94, $C6, $94, $8B
.db $95, $E1, $8B, $0C, $8D, $A3, $8D, $96, $8E, $61, $8F, $E7, $90, $90, $91, $F1
.db $91, $F1, $91, $91, $92, $79, $93, $39, $84, $8B, $95, $8B, $95, $8B, $95, $8B
.db $95, $8B, $95, $8B, $95, $8B, $95, $8B, $95, $8B, $95, $8B, $95, $8B, $95, $8B
.db $95, $8B, $95, $8B, $95, $8B, $95, $8B, $95, $8B, $95, $3A, $9A, $3A, $9A, $3A
.db $9A, $DC, $A1, $55, $A4, $C4, $A4, $D7, $A6, $8A, $A7, $BA, $A7, $08, $AC, $2B
.db $AD, $60, $AD, $D5, $AE, $4C, $AF, $5D, $B3, $59, $B5, $49, $B9, $76, $BB, $23
.db $BC

_LABEL_6680_340:
	inc  hl
	ld   a, (hl)
	inc  hl
	ld   (ix+14), l
	ld   (ix+15), h
	add  a, a
	ld   l, a
	ld   h, $00
	ld   de, $6696
	add  hl, de
	ld   a, (hl)
	inc  hl
	ld   h, (hl)
	ld   l, a
	jp   (hl)


; Data from 6696 to 78E0 (4683 bytes)
.incbin "SonicChaos.sms.dat.19" SKIP $0 READ $3DF
.include "research/spring_contacts.asm"
.incbin "SonicChaos.sms.dat.19" SKIP $438 READ $1EC
.include "research/loop_contacts.asm"
.incbin "SonicChaos.sms.dat.19" SKIP $64F READ $171
.include "research/twist_entry.asm"
.incbin "SonicChaos.sms.dat.19" SKIP $8CB READ $251
.include "research/spring_left_contact.asm"
.incbin "SonicChaos.sms.dat.19" SKIP $B7A READ $84
.include "research/spring_right_contact.asm"
.incbin "SonicChaos.sms.dat.19" SKIP $C20

LoadLevelTiles:
	di
	call _LABEL_7A7A_16
	ld   a, (CurrentLevel)
	ld   b, a
	add  a, a
	add  a, b
	ld   b, a
	ld   a, (CurrentAct)
	add  a, b
	ld   l, a
	ld   h, $00
	ld   c, a
	ld   b, $00
	add  hl, hl
	add  hl, hl
	add  hl, hl
	xor  a
	sbc  hl, bc
	ld   de, $7CED
	add  hl, de
	push hl
	pop  iy
	ld   a, (iy+0)
	call SwapFrame2
	ld   l, (iy+1)
	ld   h, (iy+2)
	call _LABEL_1D50_14
	ld   l, (iy+3)
	ld   h, (iy+4)
	xor  a
	call Tile_Loading_Routines
	ld   l, (iy+5)
	ld   h, (iy+6)
	push hl
	pop  iy
_LABEL_7925_263:
	ld   a, (iy+0)
	cp   $FF
	ret  z

	and  $1F
	call SwapFrame2
	ld   l, (iy+1)
	ld   h, (iy+2)
	di
	call _LABEL_1D50_14
	ld   l, (iy+3)
	ld   h, (iy+4)
	ld   a, (iy+0)
	and  $80
	call Tile_Loading_Routines
	ld   bc, $0005
	add  iy, bc
	jr   _LABEL_7925_263

_LABEL_794F_293:
	ld   a, (CurrentLevel)
	ld   b, a
	add  a, a
	add  a, b
	ld   b, a
	ld   a, (CurrentAct)
	add  a, b
	ld   l, a
	ld   h, $00
	add  hl, hl
	ld   de, $7F3C
	add  hl, de
	ld   a, (hl)
	ld   (RAM_D493), a
	inc  hl
	ld   a, (hl)
	ld   (RAM_D495), a
	ld   hl, $D492
	ld   (hl), $00
	set  7, (hl)
	inc  hl
	inc  hl
	ld   (hl), $00
	set  7, (hl)
	ret

_LABEL_7979_414:
	di
	ld   a, $10
	call SwapFrame2
	ld   hl, $2400
	call _LABEL_1D50_14
	ld   hl, $8670
	xor  a
	call Tile_Loading_Routines

; Data from 798C to 798C (1 bytes)
.db $C9

_LABEL_798D_409:
	di
	ld   a, $1B
	call SwapFrame2
	ld   hl, $1000
	call _LABEL_1D50_14
	ld   hl, $9E00
	xor  a
	call Tile_Loading_Routines

; Data from 79A0 to 79B6 (23 bytes)
.db $3E, $09, $CD, $6F, $1C, $21, $C0, $BE, $11, $00, $02, $01, $80, $00, $CD, $9C
.db $1D, $3E, $1B, $CD, $6F, $1C, $C9

_LABEL_79B7_418:
	di
	ld   a, $13
	call SwapFrame2
	ld   hl, $1800
	call _LABEL_1D50_14
	ld   hl, $8000
	xor  a
	call Tile_Loading_Routines

; Data from 79CA to 79DE (21 bytes)
.db $C9, $F3, $3E, $13, $CD, $6F, $1C, $21, $00, $20, $CD, $50, $1D, $21, $9C, $94
.db $AF, $CD, $C2, $24, $C9

_LABEL_79DF_289:
	di
	ld   a, $0E
	call SwapFrame2
	ld   hl, $A2A0
	ld   de, $0900
	ld   bc, $0080
	call _LABEL_1D9C_61
	ret

_LABEL_79F2_290:
	di
	ld   a, $0E
	call SwapFrame2
	ld   hl, $0CC0
	call _LABEL_1D50_14
	ld   a, (CurrentLevel)
	add  a, a
	ld   l, a
	ld   h, $00
	ld   de, $A3A0
	add  hl, de
	ld   e, (hl)
	inc  hl
	ld   d, (hl)
	ex   de, hl
	xor  a
	call Tile_Loading_Routines
	ret


; Data from 7A12 to 7A79 (104 bytes)
.db $F3, $3E, $13, $CD, $6F, $1C, $21, $00, $20, $CD, $50, $1D, $21, $E5, $A7, $AF
.db $CD, $C2, $24, $C9, $C9, $C9, $F3, $3E, $10, $CD, $6F, $1C, $21, $00, $18, $CD
.db $50, $1D, $21, $70, $8A, $AF, $CD, $C2, $24, $C9, $F3, $3E, $16, $CD, $6F, $1C
.db $21, $00, $18, $CD, $50, $1D, $21, $E4, $B1, $AF, $CD, $C2, $24, $C9, $F3, $3E
.db $13, $CD, $6F, $1C, $21, $00, $18, $CD, $50, $1D, $21, $AF, $B5, $AF, $CD, $C2
.db $24, $C9, $C9, $F3, $3E, $1A, $CD, $6F, $1C, $21, $00, $0C, $CD, $50, $1D, $21
.db $DC, $95, $AF, $CD, $C2, $24, $C9, $C9

_LABEL_7A7A_16:
	di
	call _LABEL_1DB9_17
	ld   hl, $0000
	ld   de, $0000
	ld   bc, $0400
	call _LABEL_1D50_14
_LABEL_7A8A_18:
	ld   a, e
	out  ($BE), a
	out  ($BE), a
	out  ($BE), a
	out  ($BE), a
	out  ($BE), a
	out  ($BE), a
	out  ($BE), a
	out  ($BE), a
	out  ($BE), a
	out  ($BE), a
	out  ($BE), a
	out  ($BE), a
	out  ($BE), a
	out  ($BE), a
	out  ($BE), a
	out  ($BE), a
	dec  bc
	ld   a, b
	or   c
	jr   nz, _LABEL_7A8A_18
	call _LABEL_1DAB_19
	ret

_LABEL_7AB4_12:
	di
	ld   hl, $C000
	ld   de, $0000
	ld   bc, $0020
	call _LABEL_1D8A_13
	ret

_LABEL_7AC2_371:
	ld   a, (RAM_D3B3)
	or   a
	ret  z

	ld   a, (RAM_D3B4)
	or   a
	call z, _LABEL_7B51_372
	ld   a, (RAM_D3B3)
	or   a
	ret  z

	ld   a, (RAM_D3B5)
	or   a
	call z, _LABEL_7B6D_374
	di
	ld   a, (RAM_D3B4)
	bit  7, a
	jr   nz, _LABEL_7B24_378
	call SwapFrame2
	ld   hl, (RAM_D3B8)
	call _LABEL_1D50_14
	ld   hl, (RAM_D3B6)
	ld   a, (RAM_D3B5)
	or   a
	jp   z, _LABEL_7B92_375
	cp   $04
	jr   c, _LABEL_7AFB_379
	ld   a, $04
_LABEL_7AFB_379:
	ld   b, a
_LABEL_7AFC_381:
	ld   c, $20
_LABEL_7AFE_380:
	ld   a, (hl)
	out  ($BE), a
	inc  hl
	dec  c
	jp   nz, _LABEL_7AFE_380
	djnz _LABEL_7AFC_381
_LABEL_7B08_385:
	ei
	ld   (RAM_D3B6), hl
	ld   hl, (RAM_D3B8)
	ld   bc, $0080
	add  hl, bc
	ld   (RAM_D3B8), hl
	ld   a, (RAM_D3B5)
	sub  $04
	ld   (RAM_D3B5), a
	ret  nc

	xor  a
	ld   (RAM_D3B5), a
	ret

_LABEL_7B24_378:
	and  $1F
	call SwapFrame2
	ld   hl, (RAM_D3B8)
	call _LABEL_1D50_14
	ld   hl, (RAM_D3B6)
	ld   a, (RAM_D3B5)
	or   a
	jr   z, _LABEL_7B92_375
	cp   $04
	jr   c, _LABEL_7B3E_382
	ld   a, $04
_LABEL_7B3E_382:
	ld   b, a
	ld   d, $01
_LABEL_7B41_384:
	ld   c, $20
_LABEL_7B43_383:
	ld   e, (hl)
	ld   a, (de)
	out  ($BE), a
	inc  hl
	dec  c
	jp   nz, _LABEL_7B43_383
	djnz _LABEL_7B41_384
	jp   _LABEL_7B08_385

_LABEL_7B51_372:
	ld   a, (RAM_D3B3)
	cp   $10
	jp   c, _LABEL_7C71_373
	sub  $10
	add  a, a
	ld   l, a
	ld   h, $00
	ld   de, $7BA6
	add  hl, de
	ld   e, (hl)
	inc  hl
	ld   d, (hl)
	ld   (RAM_D3BA), de
	jp   _LABEL_7B6D_374

_LABEL_7B6D_374:
	ld   hl, (RAM_D3BA)
	ld   a, (hl)
	cp   $FF
	jr   z, _LABEL_7B92_375
	ld   (RAM_D3B4), a
	inc  hl
	ld   a, (hl)
	ld   (RAM_D3B5), a
	inc  hl
	ld   e, (hl)
	inc  hl
	ld   d, (hl)
	ld   (RAM_D3B8), de
	inc  hl
	ld   e, (hl)
	inc  hl
	ld   d, (hl)
	ld   (RAM_D3B6), de
	inc  hl
	ld   (RAM_D3BA), hl
	ret

_LABEL_7B92_375:
	xor  a
	ld   (RAM_D3B3), a
	ld   (RAM_D3B4), a
	ld   (RAM_D3B5), a
	ld   hl, $0000
	ld   (RAM_D3B8), hl
	ld   (RAM_D3B6), hl
	ret


; Data from 7BA6 to 7C70 (203 bytes)
.db $CA, $7B, $CA, $7B, $CB, $7B, $D8, $7B, $EB, $7B, $F8, $7B, $05, $7C, $12, $7C
.db $1F, $7C, $2C, $7C, $33, $7C, $47, $7C, $4E, $7C, $55, $7C, $5C, $7C, $63, $7C
.db $6A, $7C, $40, $7C, $FF, $0D, $10, $40, $0D, $BC, $96, $09, $30, $40, $0F, $40
.db $86, $FF, $0A, $48, $C0, $05, $40, $89, $8A, $2C, $C0, $0E, $40, $89, $09, $0C
.db $40, $14, $A0, $AB, $FF, $0A, $68, $C0, $05, $80, $92, $09, $0C, $C0, $12, $A0
.db $AB, $FF, $0A, $46, $C0, $05, $80, $9F, $09, $0C, $80, $0E, $A0, $AB, $FF, $05
.db $40, $C0, $05, $80, $B6, $09, $0C, $C0, $0D, $A0, $AB, $FF, $0A, $84, $C0, $05
.db $40, $A8, $09, $0C, $40, $16, $A0, $AB, $FF, $0B, $84, $C0, $05, $00, $80, $09
.db $0C, $40, $16, $A0, $AB, $FF, $0B, $8C, $C0, $05, $80, $A1, $FF, $0B, $5A, $C0
.db $05, $00, $B3, $09, $0C, $00, $11, $A0, $AB, $FF, $0B, $88, $C0, $05, $80, $90
.db $FF, $0D, $10, $40, $0D, $BC, $94, $FF, $0D, $10, $40, $0D, $BC, $96, $FF, $0D
.db $10, $40, $0D, $BC, $98, $FF, $0D, $10, $40, $0D, $BC, $9A, $FF, $0D, $10, $40
.db $0D, $BC, $9C, $FF, $0D, $10, $40, $0D, $BC, $9E, $FF

_LABEL_7C71_373:
	di
	ld   a, $0E
	call SwapFrame2
	ld   a, (RAM_D3B3)
	add  a, a
	ld   l, a
	ld   h, $00
	ld   de, $7CBB
	ld   a, (RAM_D500)
	dec  a
	jr   z, _LABEL_7C8A_376
	ld   de, $7CC7
_LABEL_7C8A_376:
	add  hl, de
	ld   e, (hl)
	inc  hl
	ld   d, (hl)
	ex   de, hl
	ld   de, $0980
	ld   bc, $00C0
	call _LABEL_1D9C_61
	ld   a, (RAM_D3B3)
	add  a, a
	ld   l, a
	ld   h, $00
	ld   de, $7CD3
	ld   a, (RAM_D500)
	dec  a
	jr   z, _LABEL_7CAB_377
	ld   de, $7CDF
_LABEL_7CAB_377:
	add  hl, de
	ld   e, (hl)
	inc  hl
	ld   d, (hl)
	ex   de, hl
	ld   de, $0BC0
	ld   bc, $0080
	call _LABEL_1D9C_61
	ei
	jp   _LABEL_7B92_375


; Data from 7CBD to 7FFF (835 bytes)
.db $A0, $99, $60, $9A, $20, $9B, $60, $9D, $A0, $9C, $E0, $9B, $A0, $99, $E0, $A1
.db $20, $9B, $60, $9D, $A0, $9C, $E0, $9B, $E0, $9E, $60, $9F, $E0, $9F, $60, $A1
.db $E0, $A0, $60, $A0, $E0, $9E, $20, $A3, $E0, $9F, $60, $A0, $E0, $A0, $60, $A0
.db $10, $00, $18, $9E, $8F, $13, $7E, $10, $00, $18, $9E, $8F, $13, $7E, $10, $00
.db $18, $9E, $8F, $13, $7E, $10, $00, $18, $78, $A4, $32, $7E, $10, $00, $18, $78
.db $A4, $32, $7E, $10, $00, $18, $78, $A4, $32, $7E, $18, $00, $18, $00, $80, $56
.db $7E, $18, $00, $18, $00, $80, $56, $7E, $18, $00, $18, $00, $80, $56, $7E, $18
.db $00, $18, $F0, $99, $75, $7E, $18, $00, $18, $F0, $99, $75, $7E, $18, $00, $18
.db $F0, $99, $75, $7E, $16, $00, $18, $00, $80, $99, $7E, $16, $00, $18, $00, $80
.db $99, $7E, $16, $00, $18, $00, $80, $99, $7E, $16, $00, $18, $00, $98, $C2, $7E
.db $16, $00, $18, $00, $98, $C2, $7E, $16, $00, $18, $00, $98, $C2, $7E, $10, $00
.db $18, $9E, $8F, $13, $7E, $10, $00, $18, $9E, $8F, $13, $7E, $10, $00, $18, $9E
.db $8F, $13, $7E, $10, $00, $18, $9E, $8F, $EB, $7E, $10, $00, $18, $9E, $8F, $EB
.db $7E, $10, $00, $18, $9E, $8F, $EB, $7E, $19, $00, $18, $00, $80, $FB, $7E, $19
.db $00, $18, $00, $80, $FB, $7E, $19, $00, $18, $00, $80, $FB, $7E, $19, $00, $18
.db $00, $80, $06, $7F, $19, $00, $18, $00, $80, $06, $7F, $19, $00, $18, $00, $80
.db $06, $7F, $19, $00, $18, $90, $95, $16, $7F, $19, $00, $18, $90, $95, $16, $7F
.db $19, $00, $18, $90, $95, $16, $7F, $19, $00, $18, $00, $80, $21, $7F, $19, $00
.db $18, $00, $80, $21, $7F, $19, $00, $18, $00, $80, $21, $7F, $19, $00, $18, $90
.db $95, $31, $7F, $19, $00, $18, $90, $95, $31, $7F, $19, $00, $18, $90, $95, $31
.db $7F, $10, $00, $18, $9E, $8F, $13, $7E, $10, $00, $18, $9E, $8F, $13, $7E, $10
.db $00, $18, $9E, $8F, $13, $7E, $08, $00, $02, $40, $B3, $09, $40, $0D, $C0, $A1
.db $09, $40, $0E, $30, $A0, $09, $C0, $10, $B0, $9A, $89, $00, $13, $B0, $9A, $89
.db $40, $15, $A0, $95, $FF, $08, $00, $02, $40, $B3, $09, $40, $0D, $C0, $A2, $09
.db $40, $0E, $30, $A0, $09, $C0, $10, $20, $A7, $09, $80, $11, $90, $96, $09, $C0
.db $12, $80, $97, $89, $00, $15, $80, $97, $FF, $08, $00, $02, $40, $B3, $09, $40
.db $0D, $70, $A3, $09, $40, $0E, $30, $A0, $09, $C0, $10, $50, $99, $09, $80, $12
.db $40, $A8, $89, $80, $14, $C0, $93, $FF, $08, $00, $02, $40, $B3, $09, $40, $0D
.db $70, $A4, $09, $40, $0E, $80, $A7, $09, $80, $0F, $D0, $9C, $89, $C0, $11, $D0
.db $9C, $09, $00, $14, $E0, $9E, $09, $80, $15, $40, $A8, $FF, $08, $00, $02, $40
.db $B3, $09, $40, $0D, $90, $B0, $09, $00, $0E, $50, $B1, $09, $00, $10, $70, $A5
.db $09, $C0, $10, $E0, $B3, $09, $C0, $11, $C0, $B2, $09, $00, $14, $60, $AB, $09
.db $80, $14, $A0, $B4, $FF, $08, $00, $02, $40, $B3, $09, $40, $0D, $30, $A6, $09
.db $40, $0E, $50, $AA, $09, $80, $0F, $20, $AD, $09, $40, $12, $D0, $AF, $09, $80
.db $12, $90, $96, $09, $C0, $13, $30, $A0, $09, $40, $16, $F0, $AF, $FF, $08, $00
.db $02, $40, $B3, $09, $40, $0D, $00, $B6, $09, $C0, $14, $60, $BB, $FF, $08, $00
.db $02, $40, $B3, $0E, $40, $0D, $1A, $A5, $FF, $08, $00, $02, $40, $B3, $0E, $40
.db $0D, $3A, $A6, $09, $C0, $0E, $40, $A8, $FF, $08, $00, $02, $40, $B3, $0E, $40
.db $0D, $9A, $A7, $FF, $08, $00, $02, $40, $B3, $0E, $40, $0D, $0A, $A9, $09, $C0
.db $0E, $30, $A0, $FF, $08, $00, $02, $40, $B3, $0E, $40, $0D, $6A, $AA, $FF, $15
.db $06, $15, $06, $15, $06, $16, $07, $16, $07, $16, $07, $17, $08, $17, $08, $17
.db $08, $18, $09, $18, $09, $18, $09, $19, $0A, $19, $0A, $19, $0A, $1A, $0B, $1A
.db $0B, $1A, $0B, $15, $06, $15, $06, $15, $06, $28, $29, $28, $29, $28, $29, $26
.db $12, $26, $12, $26, $12, $26, $12, $26, $12, $26, $12, $27, $13, $27, $13, $27
.db $13, $26, $12, $26, $12, $26, $12, $27, $14, $27, $14, $27, $14, $15, $06, $15
.db $06, $15, $06, $15, $06, $15, $06, $15, $06, $15, $06, $15, $06, $15, $06, $FF
.db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
.db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
.db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
.db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
.db $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF, $FF
.db $FF, $FF, $FF, $54, $4D, $52, $20, $53, $45, $47, $41, $FF, $FF, $66, $FD, $21
.db $90, $00, $40


.BANK 2 SLOT 1
.ORG $0000

_LABEL_8000_128:
	ld   hl, $DE08
	ld   a, (hl)
	or   a
	jr   z, _LABEL_800C_129
	ret  p

	dec  (hl)
	jp   _LABEL_83FB_8

_LABEL_800C_129:
	call _LABEL_807F_130
	call _LABEL_8066_133
	call _LABEL_80B0_135
	call _LABEL_8119_146
	ld   ix, $DE40
	bit  7, (ix+0)
	call nz, _LABEL_84C2_159
	ld   ix, $DE70
	bit  7, (ix+0)
	call nz, _LABEL_84C2_159
	ld   ix, $DEA0
	bit  7, (ix+0)
	call nz, _LABEL_84C2_159
	ld   ix, $DED0
	bit  7, (ix+0)
	call nz, _LABEL_864A_215
	ld   ix, $DF00
	bit  7, (ix+0)
	call nz, _LABEL_84C2_159
	ld   ix, $DF30
	bit  7, (ix+0)
	call nz, _LABEL_84C2_159
	ld   ix, $DF60
	bit  7, (ix+0)
	call nz, _LABEL_84C2_159
	ret

_LABEL_8066_133:
	ld   hl, $DE01
	ld   a, (hl)
	or   a
	ret  z

	dec  (hl)
	ret  nz

	ld   a, (RAM_DE02)
	ld   (hl), a
	ld   hl, $DE4A
	ld   de, $0030
	ld   b, $04
_LABEL_807A_134:
	inc  (hl)
	add  hl, de
	djnz _LABEL_807A_134
	ret

_LABEL_807F_130:
	ld   de, $DE04
	ld   ix, $DE0F
	ld   iy, $DE03
	call _LABEL_8090_131
	call _LABEL_8090_131
_LABEL_8090_131:
	ld   a, (de)
	and  $7F
	jr   z, _LABEL_80AC_132
	dec  a
	ld   hl, $506F
	ld   c, a
	ld   b, $00
	add  hl, bc
	ld   a, (hl)
	cp   (ix+0)
	jr   c, _LABEL_80AC_132
	and  $7F
	ld   (ix+0), a
	ld   a, (de)
	ld   (iy+0), a
_LABEL_80AC_132:
	xor  a
	ld   (de), a
	inc  de
	ret

_LABEL_80B0_135:
	ld   a, (RAM_DE09)
	or   a
	ret  z

	ld   hl, $DF00
	ld   b, $03
	ld   de, $0030
_LABEL_80BD_139:
	bit  7, (hl)
	jp   z, _LABEL_80E4_136
	push hl
	inc  hl
	ld   a, (hl)
	cp   $A0
	jp   nz, _LABEL_80D2_137
	ld   hl, $DE70
	res  2, (hl)
	jp   _LABEL_80E1_138

_LABEL_80D2_137:
	cp   $E0
	jp   nz, _LABEL_80DC_145
	ld   hl, $DED0
	res  2, (hl)
_LABEL_80DC_145:
	ld   hl, $DEA0
	res  2, (hl)
_LABEL_80E1_138:
	pop  hl
	xor  a
	ld   (hl), a
_LABEL_80E4_136:
	add  hl, de
	djnz _LABEL_80BD_139
	ld   a, (RAM_DE0A)
	dec  a
	jr   z, _LABEL_80F1_140
	ld   (RAM_DE0A), a
	ret

_LABEL_80F1_140:
	ld   a, (RAM_DE0B)
	ld   (RAM_DE0A), a
	ld   a, (RAM_DE09)
	dec  a
	ld   (RAM_DE09), a
	jp   z, _LABEL_83E5_141
	ld   hl, $DE46
	ld   de, $0030
	ld   b, $03
_LABEL_8109_143:
	call _LABEL_8112_142
	add  hl, de
	djnz _LABEL_8109_143
	ld   hl, $DE16
_LABEL_8112_142:
	ld   a, (hl)
	inc  a
	cp   $0C
	ret  nc

	ld   (hl), a
	ret

_LABEL_8119_146:
	ld   a, (RAM_DE03)
	bit  7, a
	jp   z, _LABEL_83E5_141
	cp   $A0
	jr   c, _LABEL_8168_147
	cp   $C5
	jp   c, _LABEL_81A7_148
	cp   $D4
	jp   nc, _LABEL_83E5_141
	sub  $D0
	ld   hl, $4138
	call _LABEL_841D_149
	jp   (hl)


; Data from 8138 to 8167 (48 bytes)
.db $40, $41, $E5, $43, $50, $41, $00, $70, $3E, $0C, $32, $09, $DE, $3E, $12, $32
.db $0A, $DE, $32, $0B, $DE, $C3, $A1, $41, $FD, $21, $00, $DF, $11, $30, $00, $06
.db $03, $21, $67, $41, $FD, $75, $03, $FD, $74, $04, $FD, $19, $10, $F6, $C9, $F2

_LABEL_8168_147:
	sub  $81
	ret  m

	ex   af, af'
	call _LABEL_83E5_141
	ex   af, af'
	ld   hl, $50C2
	ld   c, a
	ex   af, af'
	call _LABEL_8427_156
	ld   (RAM_DE01), a
	ld   (RAM_DE02), a
	ex   af, af'
	ld   hl, $50E1
	call _LABEL_841D_149
	inc  hl
	inc  hl
	ld   b, (hl)
	inc  hl
	inc  hl
	ld   a, (hl)
	ex   af, af'
	inc  hl
	ld   a, (hl)
	ld   (RAM_DE01), a
	ld   (RAM_DE02), a
	ld   iy, $4263
	inc  hl
	ld   de, $DE40
_LABEL_819C_158:
	call _LABEL_822B_157
	djnz _LABEL_819C_158
_LABEL_81A1_9:
	ld   a, $80
	ld   (RAM_DE03), a
	ret

_LABEL_81A7_148:
	ld   (RAM_DE0D), a
	sub  $A0
	ld   hl, $511F
	call _LABEL_841D_149
	inc  hl
	inc  hl
	ld   a, (hl)
	inc  hl
	ex   af, af'
	ld   b, (hl)
	inc  hl
_LABEL_81B9_154:
	inc  hl
	ld   a, (hl)
	dec  hl
	cp   $A0
	jr   z, _LABEL_81E8_150
	cp   $C0
	jr   z, _LABEL_81CD_151
	ld   de, $DF60
	ld   iy, $DED0
	jr   _LABEL_81EF_152

_LABEL_81CD_151:
	ld   iy, $DF60
	bit  6, (iy+0)
	jr   nz, _LABEL_81DF_155
	set  2, (iy+0)
	ld   a, $FF
	out  ($7F), a
_LABEL_81DF_155:
	ld   de, $DF30
	ld   iy, $DEA0
	jr   _LABEL_81EF_152

_LABEL_81E8_150:
	ld   de, $DF00
	ld   iy, $DE70
_LABEL_81EF_152:
	call _LABEL_81F6_153
	djnz _LABEL_81B9_154
	jr   _LABEL_81A1_9

_LABEL_81F6_153:
	set  2, (iy+0)
	ld   c, $36
	push de
	pop  ix
	ldi
	ldi
	ex   af, af'
	ld   (de), a
	inc  de
	ex   af, af'
	xor  a
	ldi
	ldi
	ldi
	ldi
	ld   (de), a
	inc  de
	ld   (de), a
	inc  de
	ld   a, c
	ld   (de), a
	inc  de
	xor  a
	ld   (ix+39), a
	ld   (ix+40), a
	ld   (ix+41), a
	inc  a
	ld   (de), a
	push hl
	ld   hl, $0026
	add  hl, de
	ex   de, hl
	pop  hl
	ret

_LABEL_822B_157:
	ld   c, $34
	push de
	pop  ix
	ld   a, $80
	ld   (de), a
	inc  de
	ld   a, (iy+0)
	ld   (de), a
	inc  de
	inc  iy
	ex   af, af'
	ld   (de), a
	inc  de
	ex   af, af'
	xor  a
	ldi
	ldi
	ldi
	ldi
	ld   (de), a
	inc  de
	ld   (de), a
	inc  de
	ld   a, c
	ld   (de), a
	inc  de
	xor  a
	ld   (ix+39), a
	ld   (ix+40), a
	ld   (ix+41), a
	inc  a
	ld   (de), a
	push hl
	ld   hl, $0026
	add  hl, de
	ex   de, hl
	pop  hl
	ret


; Data from 8263 to 8266 (4 bytes)
.db $80, $A0, $C0, $E0

_LABEL_8267_178:
	bit  7, (ix+7)
	ret  z

	bit  1, (ix+0)
	ret  nz

	ld   e, (ix+16)
	ld   d, (ix+17)
	push ix
	pop  hl
	ld   b, $00
	ld   c, $14
	add  hl, bc
	ex   de, hl
	ldi
	ldi
	ldi
	ld   a, (hl)
	srl  a
	ld   (de), a
	xor  a
	ld   (ix+18), a
	ld   (ix+19), a
	ret

_LABEL_8292_179:
	bit  7, (ix+8)
	ret  z

	bit  1, (ix+0)
	ret  nz

	bit  7, (ix+29)
	ret  nz

	ld   a, $FF
	ld   (ix+31), a
	and  $10
	or   (ix+30)
	ld   (ix+29), a
	ret

_LABEL_82AF_182:
	ld   l, (ix+11)
	ld   h, (ix+12)
	ld   a, (ix+7)
	or   a
	ret  z

	jp   p, _LABEL_8305_183
	dec  (ix+20)
	ret  nz

	inc  (ix+20)
	push hl
	ld   l, (ix+18)
	ld   h, (ix+19)
	dec  (ix+21)
	jr   nz, _LABEL_82F0_184
	ld   e, (ix+16)
	ld   d, (ix+17)
	push de
	pop  iy
	ld   a, (iy+1)
	ld   (ix+21), a
	ld   a, (ix+22)
	ld   c, a
	and  $80
	rlca
	neg
	ld   b, a
	add  hl, bc
	ld   (ix+18), l
	ld   (ix+19), h
_LABEL_82F0_184:
	pop  bc
	add  hl, bc
	dec  (ix+23)
	ret  nz

	ld   a, (iy+3)
	ld   (ix+23), a
	ld   a, (ix+22)
	neg
	ld   (ix+22), a
	ret

_LABEL_8305_183:
	dec  a
	ex   de, hl
	ld   hl, $48AC
	call _LABEL_841D_149
	jr   _LABEL_8312_185

_LABEL_830F_190:
	ld   (ix+21), a
_LABEL_8312_185:
	push hl
	ld   c, (ix+21)
	call _LABEL_8427_156
	pop  hl
	bit  7, a
	jr   z, _LABEL_8339_186
	cp   $83
	jr   z, _LABEL_832E_187
	jr   nc, _LABEL_8335_188
	cp   $80
	jr   z, _LABEL_8332_189
	set  5, (ix+0)
	pop  hl
	ret

_LABEL_832E_187:
	inc  de
	ld   a, (de)
	jr   _LABEL_830F_190

_LABEL_8332_189:
	xor  a
	jr   _LABEL_830F_190

_LABEL_8335_188:
	ld   h, $FF
	jr   _LABEL_833B_191

_LABEL_8339_186:
	ld   h, $00
_LABEL_833B_191:
	ld   l, a
	add  hl, de
	inc  (ix+21)
	ret

_LABEL_8341_161:
	res  1, (ix+0)
	res  4, (ix+0)
	ld   e, (ix+3)
	ld   d, (ix+4)
_LABEL_834F_165:
	ld   a, (de)
	inc  de
	cp   $E0
	jp   nc, _LABEL_86D5_162
	bit  3, (ix+0)
	jp   nz, _LABEL_83C7_163
	cp   $D8
	jr   c, _LABEL_8369_164
	and  $07
	ld   (ix+6), a
	jp   _LABEL_834F_165

_LABEL_8369_164:
	cp   $80
	jr   c, _LABEL_8391_166
	jr   z, _LABEL_83C2_167
	ex   af, af'
	ld   a, (ix+29)
	and  $7F
	ld   (ix+29), a
	ex   af, af'
	call _LABEL_8415_168
	ld   (ix+11), l
	ld   (ix+12), h
_LABEL_8382_173:
	ld   a, (de)
	inc  de
	or   a
	jp   p, _LABEL_8391_166
	ld   a, (ix+13)
	ld   (ix+10), a
	dec  de
	jr   _LABEL_839A_169

_LABEL_8391_166:
	call _LABEL_842C_174
	ld   (ix+10), a
	ld   (ix+13), a
_LABEL_839A_169:
	ld   (ix+3), e
	ld   (ix+4), d
	bit  1, (ix+0)
	ret  nz

	bit  6, (ix+0)
	jr   nz, _LABEL_83AF_170
	res  5, (ix+0)
_LABEL_83AF_170:
	ld   a, (ix+15)
	ld   (ix+14), a
	xor  a
	ld   (ix+21), a
	bit  7, (ix+8)
	ret  nz

	ld   (ix+31), a
	ret

_LABEL_83C2_167:
	call _LABEL_85E6_171
	jr   _LABEL_8382_173

_LABEL_83C7_163:
	ld   h, a
	ld   a, (de)
	inc  de
	ld   l, a
	or   h
	jr   z, _LABEL_83DA_176
	ld   b, $00
	ld   a, (ix+5)
	or   a
	ld   c, a
	jp   p, _LABEL_83D9_177
	dec  b
_LABEL_83D9_177:
	add  hl, bc
_LABEL_83DA_176:
	ld   (ix+11), l
	ld   (ix+12), h
	ld   a, (de)
	inc  de
	jp   _LABEL_8391_166

_LABEL_83E5_141:
	push hl
	push bc
	push de
	ld   hl, $DE03
	ld   de, $DE04
	ld   bc, $018C
	ld   (hl), $00
_LABEL_83F3_144:
	ldi
	jp   pe, _LABEL_83F3_144
	pop  de
	pop  bc
	pop  hl
_LABEL_83FB_8:
	push hl
	push bc
	ld   hl, $440B
	ld   b, $0A
	ld   c, $7F
	otir
	pop  bc
	pop  hl
	jp   _LABEL_81A1_9


; Data from 840B to 8414 (10 bytes)
.db $80, $00, $A0, $00, $C0, $00, $9F, $BF, $DF, $FF

_LABEL_8415_168:
	and  $7F
	add  a, (ix+5)
	ld   hl, $4436
_LABEL_841D_149:
	ld   c, a
	ld   b, $00
	add  hl, bc
	add  hl, bc
	ld   c, (hl)
	inc  hl
	ld   h, (hl)
	ld   l, c
	ret

_LABEL_8427_156:
	ld   b, $00
	add  hl, bc
	ld   a, (hl)
	ret

_LABEL_842C_174:
	ld   b, (ix+2)
	dec  b
	ret  z

	ld   c, a
_LABEL_8432_175:
	add  a, c
	djnz _LABEL_8432_175
	ret


; Data from 8436 to 84C1 (140 bytes)
.db $56, $03, $26, $03, $F9, $02, $CE, $02, $A5, $02, $80, $02, $5C, $02, $3A, $02
.db $1A, $02, $FB, $01, $DF, $01, $C4, $01, $AB, $01, $93, $01, $7D, $01, $67, $01
.db $53, $01, $40, $01, $2E, $01, $1D, $01, $0D, $01, $FE, $00, $EF, $00, $E2, $00
.db $D6, $00, $C9, $00, $BE, $00, $B4, $00, $A9, $00, $A0, $00, $97, $00, $8F, $00
.db $87, $00, $7F, $00, $78, $00, $71, $00, $6B, $00, $65, $00, $5F, $00, $5A, $00
.db $55, $00, $50, $00, $4B, $00, $47, $00, $43, $00, $40, $00, $3C, $00, $39, $00
.db $36, $00, $33, $00, $30, $00, $2D, $00, $2B, $00, $28, $00, $26, $00, $24, $00
.db $22, $00, $20, $00, $1F, $00, $1D, $00, $1B, $00, $1A, $00, $18, $00, $17, $00
.db $16, $00, $15, $00, $13, $00, $12, $00, $11, $00, $00, $00

_LABEL_84C2_159:
	dec  (ix+10)
	jr   nz, _LABEL_84DC_160
	call _LABEL_8341_161
	bit  4, (ix+0)
	ret  nz

	bit  2, (ix+0)
	ret  nz

	call _LABEL_8267_178
	call _LABEL_8292_179
	jr   _LABEL_84F9_180

_LABEL_84DC_160:
	bit  2, (ix+0)
	ret  nz

	ld   a, (ix+14)
	or   a
	jr   z, _LABEL_84ED_214
	dec  (ix+14)
	call z, _LABEL_85E6_171
_LABEL_84ED_214:
	ld   a, (ix+7)
	or   a
	jr   z, _LABEL_8528_181
	bit  5, (ix+0)
	jr   nz, _LABEL_8528_181
_LABEL_84F9_180:
	bit  6, (ix+0)
	jr   nz, _LABEL_8528_181
	call _LABEL_82AF_182
	ld   d, $00
	ld   a, (ix+37)
	or   a
	jp   p, _LABEL_850C_192
	dec  d
_LABEL_850C_192:
	ld   e, a
	add  hl, de
	ld   a, (ix+1)
	cp   $E0
	jr   nz, _LABEL_8517_193
	ld   a, $C0
_LABEL_8517_193:
	ld   c, a
	ld   a, l
	and  $0F
	or   c
	out  ($7F), a
	ld   a, l
	and  $F0
	or   h
	rrca
	rrca
	rrca
	rrca
	out  ($7F), a
_LABEL_8528_181:
	call _LABEL_8546_194
	bit  2, (ix+0)
	ret  nz

	bit  4, (ix+0)
	ret  nz

	add  a, (ix+6)
	bit  4, a
	jr   z, _LABEL_853E_213
	ld   a, $0F
_LABEL_853E_213:
	or   (ix+1)
	add  a, $10
	out  ($7F), a
	ret

_LABEL_8546_194:
	ld   a, (ix+8)
	or   a
	ret  z

	jp   p, _LABEL_85FD_195
	bit  4, (ix+29)
	jr   z, _LABEL_856E_196
	ld   d, (ix+32)
	ld   a, (ix+31)
	sub  d
	jr   nc, _LABEL_855E_197
	xor  a
_LABEL_855E_197:
	or   a
	ld   (ix+31), a
	jr   nz, _LABEL_85DC_198
	ld   a, (ix+29)
	xor  $30
	ld   (ix+29), a
	jr   _LABEL_85DC_198

_LABEL_856E_196:
	bit  5, (ix+29)
	jr   z, _LABEL_859E_199
	ld   a, (ix+31)
	ld   d, (ix+33)
	ld   e, (ix+34)
	add  a, d
	jr   c, _LABEL_8583_200
	cp   e
	jr   c, _LABEL_8584_201
_LABEL_8583_200:
	ld   a, e
_LABEL_8584_201:
	cp   e
	ld   (ix+31), a
	jr   nz, _LABEL_85DC_198
	ld   a, (ix+29)
	bit  3, (ix+29)
	jr   z, _LABEL_8597_202
	xor  $30
	jr   _LABEL_8599_203

_LABEL_8597_202:
	xor  $60
_LABEL_8599_203:
	ld   (ix+29), a
	jr   _LABEL_85DC_198

_LABEL_859E_199:
	bit  6, (ix+29)
	jr   z, _LABEL_85C0_204
	ld   a, (ix+31)
	ld   d, (ix+35)
	add  a, d
	jr   nc, _LABEL_85AF_205
	ld   a, $FF
_LABEL_85AF_205:
	cp   $FF
	ld   (ix+31), a
	jr   nz, _LABEL_85DC_198
	ld   a, (ix+29)
	and  $8F
	ld   (ix+29), a
	jr   _LABEL_85DC_198

_LABEL_85C0_204:
	ld   a, (ix+31)
	ld   d, (ix+36)
	add  a, d
	jr   nc, _LABEL_85D9_206
	ld   a, (ix+29)
	and  $0F
	ld   (ix+29), a
	ld   a, $FF
	ld   (ix+31), a
	jp   _LABEL_8639_172

_LABEL_85D9_206:
	ld   (ix+31), a
_LABEL_85DC_198:
	ld   a, (ix+31)
	rrca
	rrca
	rrca
	rrca
	and  $0F
	ret

_LABEL_85E6_171:
	bit  1, (ix+0)
	ret  nz

	bit  7, (ix+8)
	jp   z, _LABEL_8639_172
	ld   a, (ix+29)
	and  $0F
	or   $80
	ld   (ix+29), a
	ret

_LABEL_85FD_195:
	dec  a
	ld   hl, $49FD
	call _LABEL_841D_149
	jr   _LABEL_8609_207

_LABEL_8606_212:
	ld   (ix+31), a
_LABEL_8609_207:
	push hl
	ld   c, (ix+31)
	call _LABEL_8427_156
	pop  hl
	bit  7, a
	jr   z, _LABEL_8635_208
	cp   $82
	jr   z, _LABEL_8625_209
	cp   $81
	jr   z, _LABEL_862F_210
	cp   $80
	jr   z, _LABEL_862C_211
	inc  de
	ld   a, (de)
	jr   _LABEL_8606_212

_LABEL_8625_209:
	set  4, (ix+0)
	pop  hl
	jr   _LABEL_8639_172

_LABEL_862C_211:
	xor  a
	jr   _LABEL_8606_212

_LABEL_862F_210:
	set  4, (ix+0)
	pop  hl
	ret

_LABEL_8635_208:
	inc  (ix+31)
	ret

_LABEL_8639_172:
	set  4, (ix+0)
	bit  2, (ix+0)
	ret  nz

	ld   a, $1F
	add  a, (ix+1)
	out  ($7F), a
	ret

_LABEL_864A_215:
	dec  (ix+10)
	jp   nz, _LABEL_8528_181
	res  4, (ix+0)
	ld   e, (ix+3)
	ld   d, (ix+4)
	ld   a, (de)
	inc  de
	cp   $E0
	jr   nc, _LABEL_866B_216
	cp   $80
	jp   c, _LABEL_8391_166
	call _LABEL_8674_217
	jp   _LABEL_8382_173

_LABEL_866B_216:
	ld   hl, $4671
	jp   _LABEL_86D8_225


; Data from 8671 to 8673 (3 bytes)
.db $13, $18, $E6

_LABEL_8674_217:
	bit  5, a
	jr   nz, _LABEL_868F_218
	bit  4, a
	jr   nz, _LABEL_8697_219
	bit  3, a
	jr   nz, _LABEL_869F_220
	bit  2, a
	jr   nz, _LABEL_86A7_221
	bit  1, a
	jr   nz, _LABEL_86AF_222
	bit  0, a
	jr   nz, _LABEL_86B7_223
	jp   _LABEL_8639_172

_LABEL_868F_218:
	ld   a, $1E
	ld   b, $02
	ld   c, $E4
	jr   _LABEL_86BF_224

_LABEL_8697_219:
	ld   a, $1D
	ld   b, $03
	ld   c, $E6
	jr   _LABEL_86BF_224

_LABEL_869F_220:
	ld   a, $27
	ld   b, $02
	ld   c, $E4
	jr   _LABEL_86BF_224

_LABEL_86A7_221:
	ld   a, $28
	ld   b, $04
	ld   c, $E4
	jr   _LABEL_86BF_224

_LABEL_86AF_222:
	ld   a, $24
	ld   b, $02
	ld   c, $E4
	jr   _LABEL_86BF_224

_LABEL_86B7_223:
	ld   a, $25
	ld   b, $02
	ld   c, $E5
	jr   _LABEL_86BF_224

_LABEL_86BF_224:
	ld   (ix+8), a
	ld   a, b
	ld   (ix+6), a
	bit  2, (ix+0)
	ret  nz

	ld   a, (RAM_DE15)
	add  a, c
	ld   (RAM_DE11), a
	out  ($7F), a
	ret

_LABEL_86D5_162:
	ld   hl, $46E9
_LABEL_86D8_225:
	push hl
	sub  $E0
	ld   hl, $46ED
	add  a, a
	ld   c, a
	ld   b, $00
	add  hl, bc
	ld   c, (hl)
	inc  hl
	ld   h, (hl)
	ld   l, c
	ld   a, (de)
	jp   (hl)


; Data from 86E9 to BFFF (14615 bytes)
.incbin "SonicChaos.sms.dat.21"




.BANK 14 SLOT 2
.ORG $0000


; Data from 38000 to 3B459 (13402 bytes)
.incbin "SonicChaos.sms.dat.E0"

_LABEL_3B45A_75:
	ld   hl, $D2D5
	inc  (hl)
	ld   a, (RAM_D2D4)
	cp   (hl)
	ret  nc

	ld   (hl), $00
	ld   ix, $D492
	ld   iy, Copy_CRAM
	ld   b, $02
_LABEL_3B46F_100:
	push bc
	push iy
	ld   a, (ix+0)
	or   a
	jr   z, _LABEL_3B480_76
	call _LABEL_3B490_77
	ld   a, $FF
	ld   (PaletteUpdate), a
_LABEL_3B480_76:
	ld   de, $0002
	add  ix, de
	pop  iy
	ld   de, $0010
	add  iy, de
	pop  bc
	djnz _LABEL_3B46F_100
	ret

_LABEL_3B490_77:
	bit  7, a
	jr   nz, _LABEL_3B4AE_78
	bit  6, a
	jp   nz, _LABEL_3B517_79
	bit  5, a
	jr   nz, _LABEL_3B49E_80
	ret

_LABEL_3B49E_80:
	call _LABEL_3B63E_81
	push iy
	pop  de
	ld   bc, $0010
	ldir
	ld   (ix+0), $00
	ret

_LABEL_3B4AE_78:
	bit  4, a
	jp   nz, _LABEL_3B574_91
	call _LABEL_3B63E_81
	ld   b, $10
_LABEL_3B4B8_95:
	push bc
	ld   a, (ix+0)
	and  $03
	ld   c, a
	ld   a, (hl)
	and  $03
	xor  $03
	ld   b, a
	ld   a, c
	sub  b
	jr   nc, _LABEL_3B4CA_92
	xor  a
_LABEL_3B4CA_92:
	and  $03
	ld   (iy+0), a
	ld   a, (hl)
	and  $0C
	xor  $0C
	rrca
	rrca
	ld   b, a
	ld   a, c
	sub  b
	jr   nc, _LABEL_3B4DC_93
	xor  a
_LABEL_3B4DC_93:
	rlca
	rlca
	and  $0C           ; check left/right buttons?
	or   (iy+0)
	ld   (iy+0), a
	ld   a, (hl)
	and  $30
	xor  $30
	rrca
	rrca
	rrca
	rrca
	ld   b, a
	ld   a, c
	sub  b
	jr   nc, _LABEL_3B4F5_94
	xor  a
_LABEL_3B4F5_94:
	rlca
	rlca
	rlca
	rlca
	and  $30
	or   (iy+0)
	ld   (iy+0), a
	inc  iy
	inc  hl
	pop  bc
	djnz _LABEL_3B4B8_95
	inc  (ix+0)
	ld   a, (ix+0)
	and  $07
	cp   $04
	ret  nz

	ld   (ix+0), $00
	ret

_LABEL_3B517_79:
	bit  4, a
	jp   nz, _LABEL_3B5E1_82
	call _LABEL_3B63E_81
	ld   b, $10
_LABEL_3B521_86:
	ld   a, (iy+0)
	and  $3C
	ld   c, a
	ld   a, (iy+0)
	and  $03
	jr   z, _LABEL_3B536_83
	sub  $01
	and  $03
	or   c
	ld   (iy+0), a
_LABEL_3B536_83:
	ld   a, (iy+0)
	and  $33
	ld   c, a
	ld   a, (iy+0)
	and  $0C
	jr   z, _LABEL_3B54B_84
	sub  $04
	and  $0C
	or   c
	ld   (iy+0), a
_LABEL_3B54B_84:
	ld   a, (iy+0)
	and  $0F                 ; palette fade in/out
	ld   c, a
	ld   a, (iy+0)
	and  $30
	jr   z, _LABEL_3B560_85
	sub  $10
	and  $30
	or   c
	ld   (iy+0), a
_LABEL_3B560_85:
	inc  iy
	djnz _LABEL_3B521_86
	inc  (ix+0)
	ld   a, (ix+0)
	and  $03
	cp   $03
	ret  nz

	ld   (ix+0), $00
	ret

_LABEL_3B574_91:
	call _LABEL_3B63E_81
	ld   b, $10
_LABEL_3B579_99:
	ld   a, (ix+0)
	and  $03
	ld   c, a
	push bc
	ld   a, (hl)
	and  $03
	ld   c, a
	ld   a, (iy+0)
	ld   b, a
	and  $3C
	ld   d, a
	ld   a, b
	and  $03
	cp   c
	jr   z, _LABEL_3B599_96
	sub  $01
	and  $03
	or   d
	ld   (iy+0), a
_LABEL_3B599_96:
	ld   a, (hl)
	and  $0C
	ld   c, a
	ld   a, (iy+0)
	ld   b, a
	and  $33
	ld   d, a
	ld   a, b
	and  $0C
	cp   c
	jr   z, _LABEL_3B5B2_97
	sub  $04
	and  $0C
	or   d
	ld   (iy+0), a
_LABEL_3B5B2_97:
	ld   a, (hl)
	and  $30
	ld   c, a
	ld   a, (iy+0)
	ld   b, a
	and  $0F
	ld   d, a
	ld   a, b
	and  $30
	cp   c
	jr   z, _LABEL_3B5CB_98
	sub  $10
	and  $30
	or   d
	ld   (iy+0), a
_LABEL_3B5CB_98:
	inc  iy
	inc  hl
	pop  bc
	djnz _LABEL_3B579_99
	inc  (ix+0)
	ld   a, (ix+0)
	and  $07
	cp   $04
	ret  nz

	ld   (ix+0), $00
	ret

_LABEL_3B5E1_82:
	call _LABEL_3B63E_81
	ld   b, $10
_LABEL_3B5E6_90:
	push bc
	ld   a, (iy+0)
	ld   b, a
	and  $3C
	ld   c, a
	ld   a, b
	and  $03
	cp   $03
	jr   z, _LABEL_3B5FD_87
	add  a, $01
	and  $03
	or   c
	ld   (iy+0), a
_LABEL_3B5FD_87:
	ld   a, (iy+0)
	ld   b, a
	and  $33
	ld   c, a
	ld   a, b
	and  $0C
	cp   $0C
	jr   z, _LABEL_3B613_88
	add  a, $04
	and  $0C
	or   c
	ld   (iy+0), a
_LABEL_3B613_88:
	ld   a, (iy+0)
	ld   b, a
	and  $0F
	ld   c, a
	ld   a, b
	and  $30
	cp   $30
	jr   z, _LABEL_3B629_89
	add  a, $10
	and  $30
	or   c
	ld   (iy+0), a
_LABEL_3B629_89:
	inc  iy
	pop  bc
	djnz _LABEL_3B5E6_90
	inc  (ix+0)
	ld   a, (ix+0)
	and  $03
	cp   $03
	ret  nz

	ld   (ix+0), $00
	ret

_LABEL_3B63E_81:
	ld   a, (ix+1)
	ld   l, a
	ld   h, $00
	add  hl, hl
	add  hl, hl
	add  hl, hl
	add  hl, hl
	ld   de, $B64D
	add  hl, de
	ret


; Data from 3B64D to 3BFFF (2483 bytes)  Palettes
.incbin "SonicChaos.sms.dat.ED"





.BANK 28 SLOT 2
.ORG $0000

_LABEL_70000_386:
	ld   a, (CurrentLevel)
	add  a, a
	ld   e, a
	ld   d, $00
	ld   hl, $8546
	add  hl, de
	ld   a, (hl)
	inc  hl
	ld   h, (hl)
	ld   l, a
	ld   a, (CurrentAct)
	add  a, a
	ld   e, a
	add  hl, de
	ld   a, (hl)
	inc  hl
	ld   h, (hl)
	ld   l, a
	ld   bc, $D400
	exx
	ld   hl, (HorizOffset)
	inc  h
	ld   de, $FF80
	add  hl, de
	ex   de, hl
	ld   hl, (VertOffset)
	inc  h
	ld   bc, $FF80
	add  hl, bc
	ld   c, l
	ld   b, h
	exx
_LABEL_70031_397:
	ld   a, (hl)
	inc  a
	jr   z, _LABEL_70043_387
	ld   a, (bc)
	or   a
	push hl
	call z, _LABEL_70049_388
	pop  hl
	inc  bc
	ld   de, $0009
	add  hl, de
	jr   _LABEL_70031_397

_LABEL_70043_387:
	ld   a, $01
	ld   (RAM_D440), a
	ret

_LABEL_70049_388:
	inc  hl
	ld   a, (hl)
	exx
	ld   l, a
	exx
	inc  hl
	ld   a, (hl)
	exx
	ld   h, a
	xor  a
	sbc  hl, de
	jp   c, _LABEL_7013C_389
	srl  h
	rr   l
	ld   a, h
	or   a
	jp   nz, _LABEL_7013C_389
	ld   a, l
	ld   (RAM_D100), a
	exx
	inc  hl
	ld   a, (hl)
	exx
	ld   l, a
	exx
	inc  hl
	ld   a, (hl)
	exx
	ld   h, a
	xor  a
	sbc  hl, bc
	jp   c, _LABEL_7013C_389
	srl  h
	rr   l
	ld   a, h
	or   a
	jp   nz, _LABEL_7013C_389
	push de
	ld   a, (RAM_D100)
	rrca
	rrca
	rrca
	and  $1F
	ld   e, a
	ld   a, l
	and  $F8
	ld   l, a
	ld   h, $00
	ld   d, $00
	add  hl, hl
	add  hl, hl
	add  hl, de
	ld   de, $8146
	add  hl, de
	pop  de
	ld   a, (hl)
	cp   $02
	jr   z, _LABEL_700A9_390
	cp   $03
	jp   nc, _LABEL_7013C_389
	ld   a, (RAM_D440)
	or   a
	jp   nz, _LABEL_7013C_389
_LABEL_700A9_390:
	exx
	ld   de, $FFFC
	add  hl, de
	ld   a, (hl)
	inc  a
	inc  a
	jr   nz, _LABEL_700EB_391
	ld   a, $FF
	ld   (bc), a
	ld   de, $0005
	add  hl, de
	ex   de, hl
	ld   a, (de)
	add  a, a
	ld   hl, $80CB
	add  a, l
	ld   l, a
	ld   a, $00
	adc  a, h
	ld   h, a
	ld   a, (hl)
	inc  hl
	ld   h, (hl)
	ld   l, a
	jp   (hl)


; Data from 700CB to 700EA (32 bytes)
.db "?", $81, ">", $81, ">", $81, ">", $81, ">", $81, ">", $81, ">", $81, ">", $81, ""
.db ">", $81, ">", $81, ">", $81, ">", $81, ">", $81, ">", $81, ">", $81, ">", $81

_LABEL_700EB_391:
; Object record bytes 1..4 are biased world coordinates: subtract $0100 from X and Y.
	push bc
	call _LABEL_329_392
	pop  bc
	jr   c, _LABEL_7013B_396
	ld   a, (hl)
	ld   (iy+0), a
	ld   (bc), a
	inc  hl
	ld   a, (hl)
	ld   (iy+58), a
	ld   (iy+17), a
	inc  hl
	ld   a, (hl)
	dec  a
	ld   (iy+59), a
	ld   (iy+18), a
	inc  hl
	ld   a, (hl)
	ld   (iy+60), a
	ld   (iy+20), a
	inc  hl
	ld   a, (hl)
	dec  a
	ld   (iy+61), a
	ld   (iy+21), a
	inc  hl
	ld   a, (hl)
	or   $40
	ld   (iy+4), a
	inc  hl
	ld   a, (hl)
	ld   (iy+63), a
	inc  hl
	ld   a, (hl)
	ld   (iy+8), a
	inc  hl
	ld   a, (hl)
	ld   (iy+9), a
	ld   l, c
	ld   h, b
	ld   de, $D400
	xor  a
	sbc  hl, de
	inc  l
	ld   (iy+62), l
_LABEL_7013B_396:
	ret

_LABEL_7013C_389:
	exx
	ret


; Data from 7013E to 73FFF (16066 bytes)
.incbin "SonicChaos.sms.dat.1C0"


.BANK 29 SLOT 2
.ORG $0000

_LABEL_74000_124:
	ld   a, (BGPalleteControlByte)
	or   a
	ret  nz

	ld   iy, $D452
	ld   b, $04
_LABEL_7400B_126:
	push bc
	call _LABEL_74018_125
	ld   bc, $0008
	add  iy, bc
	pop  bc
	djnz _LABEL_7400B_126
	ret

_LABEL_74018_125:
	ld   a, (iy+0)
	add  a, a
	ld   l, a
	ld   h, $00
	ld   de, $8028
	add  hl, de
	ld   e, (hl)
	inc  hl
	ld   d, (hl)
	ex   de, hl
	jp   (hl)


; Data from 74028 to 74509 (1250 bytes)
.incbin "SonicChaos.sms.dat.1D0"

_LABEL_7450A_58:
	ld   a, (RAM_D12F)
	and  $07
	ret  nz

	ld   a, (RAM_D351)
	inc  a
	cp   $04
	jr   c, _LABEL_74519_59
	xor  a
_LABEL_74519_59:
	ld   (RAM_D351), a
	add  a, a
	add  a, a
	add  a, a
	add  a, a
	add  a, a
	ld   l, a
	ld   h, $00
	add  hl, hl
	add  hl, hl
	ld   de, (RAM_D399)
	add  hl, de
	ld   de, (RAM_D39B)
	ld   a, d
	or   e
	ret  z

	ld   a, e
	out  ($BF), a
	ld   a, d
	or   $40
	out  ($BF), a
	ld   b, $80
	ld   c, $BE
	otir
	ld   a, (RAM_D351)
	add  a, a
	ld   l, a
	ld   h, $00
	ld   bc, $8555
	add  hl, bc
	ld   a, (hl)
	ld   (RAM_DBB5), a
	inc  hl
	ld   a, (hl)
	ld   (RAM_DBB7), a
	ret


; Data from 74555 to 77FFF (15019 bytes)
.incbin "SonicChaos.sms.dat.1D1"
.include "banks.asm"

