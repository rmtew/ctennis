        section code,code
upper_player_y equ $c045
lower_player_y equ $c049
player_sprite_descriptors equ $115a

start:
        lea     cases,a4
        clr.w   case_index
next_case:
        lea     virtual_memory+$c000,a5
        move.b  (a4)+,$45(a5)
        move.b  (a4)+,$46(a5)
        move.b  (a4)+,$47(a5)
        move.b  (a4)+,$48(a5)
        move.b  (a4)+,$49(a5)
        move.b  (a4)+,$4a(a5)
        move.b  (a4)+,$4b(a5)
        move.b  (a4)+,$4c(a5)
        bsr     build_player_sprites
        lea     $14(a5),a1
        moveq   #11,d6
check_lower:
        move.b  (a4)+,d7
        cmp.b   (a1)+,d7
        bne.s   failed
        dbra    d6,check_lower
        lea     $24(a5),a1
        moveq   #11,d6
check_upper:
        move.b  (a4)+,d7
        cmp.b   (a1)+,d7
        bne.s   failed
        dbra    d6,check_upper
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

        include "build/translation/player-sprites-routine.s"
        even
case_index:
        dc.w    0
virtual_memory:
        incbin  "build/translation/player-sprites-memory.bin"
cases:
        incbin  "build/translation/player-sprites-cases.bin"
