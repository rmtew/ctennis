        section code,code
start:
        lea     expected(pc),a4
        moveq   #0,d0           ; first Z80 operand H
next_h:
        moveq   #0,d2           ; second Z80 operand L
next_l:
        moveq   #0,d5
        move.b  d0,d5
        moveq   #0,d6
        move.b  d2,d6
        bsr     unsigned_multiply_byte
        cmp.b   (a4)+,d5
        bne.s   failed
        cmp.b   (a4)+,d6
        bne.s   failed
        addq.w  #1,d2
        cmpi.w  #256,d2
        bne.s   next_l
        addq.w  #1,d0
        cmpi.w  #256,d0
        bne.s   next_h
        moveq   #0,d0
        rts
failed:
        moveq   #1,d0
        rts

MAKE_HL_NO_AR: MACRO
        moveq   #0,d7
        move.b  d5,d7
        lsl.w   #8,d7
        move.b  d6,d7
        move.w  d7,d6
        ENDM
MAKE_DE_NO_AR: MACRO
        moveq   #0,d7
        move.b  d3,d7
        lsl.w   #8,d7
        move.b  d4,d7
        move.w  d7,d4
        ENDM
MAKE_H: MACRO
        move.w  d6,d7
        lsr.w   #8,d7
        move.b  d7,d5
        andi.w  #$00ff,d6
        ENDM
PUSH_SR: MACRO
        move.w  sr,-(sp)
        ENDM
POP_SR: MACRO
        move.w  (sp)+,ccr
        ENDM

        include "build/translation/multiply-routine.s"
expected:
        incbin  "build/translation/multiply-expected.bin"
