        section code,code
start:
        lea     cases(pc),a4
        moveq   #0,d3
next_case:
        moveq   #0,d0
        move.b  (a4)+,d0
        move.b  (a4)+,mode_status_flags
        moveq   #0,d6
        move.b  (a4)+,d6
        bsr     normalize_input_for_player_side
        cmp.b   (a4)+,d2
        bne.s   failed
        addq.w  #1,d3
        cmpi.w  #1024,d3
        bne.s   next_case
        moveq   #0,d0
        rts
failed:
        move.w  d3,d0
        addq.w  #1,d0
        rts

GET_ADDRESS: MACRO
        lea     \1,a0
        ENDM
PUSH_SR: MACRO
        move.w  sr,-(sp)
        ENDM
POP_SR: MACRO
        move.w  (sp)+,ccr
        ENDM

        include "build/translation/input-side-routine.s"
        even
mode_status_flags:
        dc.b    0
cases:
        incbin  "build/translation/input-side-cases.bin"
