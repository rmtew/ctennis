        section code,code
animation_records equ $14fa

start:
        lea     virtual_memory,a6
        lea     virtual_memory+$c000,a5
        lea     cases,a4
        clr.w   case_index
next_case:
        move.b  (a4)+,$43(a5)
        move.b  (a4)+,$44(a5)
        move.b  (a4)+,$6d(a5)
        move.b  (a4)+,$6e(a5)
        move.b  (a4)+,$4b(a5)
        move.b  (a4)+,$47(a5)
        bsr     animate_lower_player
        bsr     animate_upper_player
        move.b  (a4)+,d7
        cmp.b   $43(a5),d7
        bne.s   failed
        move.b  (a4)+,d7
        cmp.b   $44(a5),d7
        bne.s   failed
        move.b  (a4)+,d7
        cmp.b   $6d(a5),d7
        bne.s   failed
        move.b  (a4)+,d7
        cmp.b   $6e(a5),d7
        bne.s   failed
        move.b  (a4)+,d7
        cmp.b   $4b(a5),d7
        bne.s   failed
        move.b  (a4)+,d7
        cmp.b   $47(a5),d7
        bne.s   failed
        addq.w  #1,case_index
        cmpi.w  #2048,case_index
        bne.s   next_case
        moveq   #0,d0
        rts
failed:
        move.w  case_index,d0
        addq.w  #1,d0
        rts

GET_ADDRESS: MACRO
        lea     virtual_memory+\1,\2
        ENDM
LOAD_HL: MACRO
        move.w  #\1,d6
        move.b  #(\1)>>8,d5
        ENDM
MAKE_BC_NO_AR: MACRO
        moveq   #0,d7
        move.b  d1,d7
        lsl.w   #8,d7
        move.b  d2,d7
        move.w  d7,d2
        ENDM
MAKE_HL_NO_AR: MACRO
        moveq   #0,d7
        move.b  d5,d7
        lsl.w   #8,d7
        move.b  d6,d7
        move.w  d7,d6
        ENDM
MAKE_H: MACRO
        move.w  d6,d7
        lsr.w   #8,d7
        move.b  d7,d5
        andi.w  #$00ff,d6
        ENDM
MAKE_HL: MACRO
        MAKE_HL_NO_AR
        lea     virtual_memory,\1
        moveq   #0,d7
        move.w  d6,d7
        adda.l  d7,\1
        ENDM
PUSH_SR: MACRO
        move.w  sr,-(sp)
        ENDM
POP_SR: MACRO
        move.w  (sp)+,ccr
        ENDM

        include "build/translation/player-animation-routine.s"
        include "build/translation/threshold-routine.s"
        even
case_index:
        dc.w    0
virtual_memory:
        incbin  "build/translation/player-animation-memory.bin"
cases:
        incbin  "build/translation/player-animation-cases.bin"
