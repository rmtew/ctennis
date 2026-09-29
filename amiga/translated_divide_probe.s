        section code,code
start:
        lea     cases(pc),a4
        moveq   #0,d2
next_case:
        moveq   #0,d5
        move.b  (a4)+,d5       ; source H
        moveq   #0,d6
        move.b  (a4)+,d6       ; source L
        moveq   #0,d4
        move.b  (a4)+,d4       ; source E
        bsr     restoring_divide_byte
        cmp.b   (a4)+,d5      ; quotient
        bne.s   failed
        cmp.b   (a4)+,d6      ; remainder
        bne.s   failed
        addq.w  #1,d2
        cmpi.w  #8448,d2
        bne.s   next_case
        moveq   #0,d0
        rts
failed:
        move.w  d2,d0
        addq.w  #1,d0
        rts

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
PUSH_SR: MACRO
        move.w  sr,-(sp)
        ENDM
POP_SR: MACRO
        move.w  (sp)+,ccr
        ENDM
CLR_XC_FLAGS: MACRO
        andi.b  #$ee,ccr
        ENDM
INVERT_XC_FLAGS: MACRO
        eori.b  #$01,ccr
        SET_X_FROM_C
        ENDM
SET_X_FROM_C: MACRO
        move.w  sr,-(sp)
        move.w  (sp),d7
        bset    #4,d7
        btst    #0,d7
        bne.s   carry_set\@
        bclr    #4,d7
carry_set\@:
        move.w  d7,(sp)
        move.w  (sp)+,ccr
        ENDM

        include "build/translation/divide-routine.s"
cases:
        incbin  "build/translation/divide-cases.bin"
