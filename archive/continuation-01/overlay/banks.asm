.BANK 3 SLOT 2
.ORG $0000
Bank3:

; Data from C000 to FFFF (16384 bytes)
.incbin "include/banks/Bank3.bin"


.BANK 4
.ORG $0000
Bank4:

; Data from 10000 to 13FFF (16384 bytes)
.incbin "include/banks/Bank4.bin"      ; Unc.Sonic art



.BANK 5 SLOT 2
.ORG $0000
Bank5:

; Data from 14000 to 17FFF (16384 bytes)
.incbin "include/banks/Bank5.bin"
;$14000    Art - more Sonic
;$16940    Art - Tails
;$17680    Art - MGHZ pole climber boss
;$17EA0    Blank

.BANK 6
.ORG $0000
Bank6:

; Data from 18000 to 1BFFF (16384 bytes)
.incbin "include/banks/Bank6.bin"


.BANK 7
.ORG $0000
Bank7:

; Data from 1C000 to 1FFFF (16384 bytes)
.incbin "include/banks/Bank7.bin"


.BANK 8
.ORG $0000

Bank8:
; Data from 20000 to 23FFF (16384 bytes)
.incbin "include/banks/Bank8.bin"


.BANK 9
.ORG $0000

Bank9:
; Data from 24000 to 27FFF (16384 bytes)
.incbin "include/banks/Bank9.bin"


.BANK 10
.ORG $0000
Bank10:

; Data from 28000 to 2BFFF (16384 bytes)
.incbin "include/banks/Bank10.bin"


.BANK 11
.ORG $0000
Bank11:

; Data from 2C000 to 2FFFF (16384 bytes)
.incbin "include/banks/Bank11.bin"


.BANK 12 SLOT 2
.ORG $0000

Bank12:
; Data from 30000 to 33FFF (16384 bytes)
.incbin "include/banks/Bank12.bin" READ $14C1
.include "research/twist_dispatch.asm"
.incbin "include/banks/Bank12.bin" SKIP $14F5


.BANK 13
.ORG $0000
Bank13:

; Data from 34000 to 37FFF (16384 bytes)
.incbin "include/banks/Bank13.bin"

.BANK 15 SLOT 2
.ORG $0000
Bank15:

; Data from 3C000 to 3FFFF (16384 bytes)
.incbin "include/banks/Bank15.bin"    ; mappings


.BANK 16 SLOT 2
.ORG $0000
Bank16:

; Data from 40000 to 43FFF (16384 bytes)
.incbin "include/banks/Bank16.bin"
; $40000  Compressed Art- SEGA logo,
; 4039E    Mappings
;40670    CompArt - text (level select, credits?)-same in GG
;40A70    CompArt - "TIME OVER"
; 40F16    Mappings
;40F9E    CompArt - THZ/intro tiles
;42478    CompArt - GPZ tiles
;43E24    Blank

.BANK 17
.ORG $0000
Bank17:

; Data from 44000 to 47FFF (16384 bytes)
.incbin "include/banks/Bank17.bin"
;44000    32x32 - THZ/intro
;$447B0-$447BF First Spring mappings, other mappings are located here
;45640    32x32 - GPZ
;46A40    32x32 - SEZ
;477C0    Blank

.BANK 18
.ORG $0000
Bank18:

; Data from 48000 to 4BFFF (16384 bytes)
.incbin "include/banks/Bank18.bin"

Bank19:
.BANK 19 SLOT 2
.ORG $0000


; Data from 4C000 to 4FFFF (16384 bytes)
.incbin "include/banks/Bank19.bin"


.BANK 20
.ORG $0000
Bank20:

; Data from 50000 to 53FFF (16384 bytes)
.incbin "include/banks/Bank20.bin"


.BANK 21
.ORG $0000
Bank21:

; Data from 54000 to 57FFF (16384 bytes)
.incbin "include/banks/Bank21.bin"


.BANK 22
.ORG $0000
Bank22:

; Data from 58000 to 5BFFF (16384 bytes)
.incbin "include/banks/Bank22.bin"


.BANK 23
.ORG $0000
Bank23:

; Data from 5C000 to 5FFFF (16384 bytes)
.incbin "include/banks/Bank23.bin"


.BANK 24
.ORG $0000
Bank24:

; Data from 60000 to 63FFF (16384 bytes)
.incbin "include/banks/Bank24.bin"


.BANK 25
.ORG $0000
Bank25:

; Data from 64000 to 67FFF (16384 bytes)
.incbin "include/banks/Bank25.bin"


.BANK 26
.ORG $0000
Bank26:

; Data from 68000 to 6BFFF (16384 bytes)
.incbin "include/banks/Bank26.bin"


.BANK 27 SLOT 2
.ORG $0000
Bank27:

; Data from 6C000 to 6FFFF (16384 bytes)
.incbin "include/banks/Bank27.bin"

.BANK 30 SLOT 2
.ORG $0000
Bank30:

; Data from 78000 to 7BFFF (16384 bytes)
; Keep unrelated bank 30 data unchanged; recover platform routines in-place.
.incbin "include/banks/Bank30.bin" READ $F1
.include "research/platform_reverse.asm"
.incbin "include/banks/Bank30.bin" SKIP $105 READ $472
.include "research/platform_code.asm"
.incbin "include/banks/Bank30.bin" SKIP $947


.BANK 31 SLOT 2
.ORG $0000
Bank31:

; Data from 7C000 to 7FFFF (16384 bytes)
.incbin "include/banks/Bank31.bin"