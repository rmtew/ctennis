GET_ADDRESS: MACRO
        lea     virtual_memory+\1,\2
        ENDM
LOAD_HL: MACRO
        move.w  #\1,d6
        move.b  #(\1)>>8,d5
        ENDM
LOAD_DE: MACRO
        move.w  #\1,d4
        move.b  #(\1)>>8,d3
        ENDM
LOAD_BC: MACRO
        move.w  #\1,d2
        move.b  #(\1)>>8,d1
        ENDM
MOVE_W_TO_REG: MACRO
        moveq   #0,d7
        move.b  1(\1),d7
        lsl.w   #8,d7
        move.b  (\1),d7
        move.w  d7,\2
        ENDM
MOVE_W_FROM_REG: MACRO
        move.b  \1,(\2)
        move.w  \1,d7
        lsr.w   #8,d7
        move.b  d7,1(\2)
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
MAKE_BC_NO_AR: MACRO
        moveq   #0,d7
        move.b  d1,d7
        lsl.w   #8,d7
        move.b  d2,d7
        move.w  d7,d2
        ENDM
MAKE_B: MACRO
        move.w  d2,d7
        lsr.w   #8,d7
        move.b  d7,d1
        andi.w  #$00ff,d2
        ENDM
MAKE_DE_NO_AR: MACRO
        moveq   #0,d7
        move.b  d3,d7
        lsl.w   #8,d7
        move.b  d4,d7
        move.w  d7,d4
        ENDM
MAKE_D: MACRO
        move.w  d4,d7
        lsr.w   #8,d7
        move.b  d7,d3
        andi.w  #$00ff,d4
        ENDM
MAKE_AR_FROM_HL: MACRO
        MAKE_HL_NO_AR
        lea     virtual_memory,\1
        moveq   #0,d7
        move.w  d6,d7
        adda.l  d7,\1
        ENDM
MAKE_AR_FROM_DE: MACRO
        MAKE_DE_NO_AR
        lea     virtual_memory,\1
        moveq   #0,d7
        move.w  d4,d7
        adda.l  d7,\1
        ENDM
MAKE_HL: MACRO
        MAKE_HL_NO_AR
        lea     virtual_memory,\1
        moveq   #0,d7
        move.w  d6,d7
        adda.l  d7,\1
        ENDM
MAKE_DE: MACRO
        MAKE_DE_NO_AR
        lea     virtual_memory,\1
        moveq   #0,d7
        move.w  d4,d7
        adda.l  d7,\1
        ENDM
PUSH_SR: MACRO
        move.w  sr,-(sp)
        ENDM
POP_SR: MACRO
        move.w  (sp)+,ccr
        ENDM
READ_Z80_REFRESH: MACRO
        ifd LIVE_REFRESH_ADAPTER
        jsr     read_refresh_adapter
        else
        clr.b   d0
        endif
        ENDM
CLR_XC_FLAGS: MACRO
        andi.b  #$ee,ccr
        ENDM
SET_XC_FLAGS: MACRO
        ori.b   #$11,ccr
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

