; Select pre-rendered native bitplane banks for the six scoreboard fields.
; Call only in vertical blank after field_values changes.
patch_score_pointers:
        movem.l d0-d2/d7/a0-a4,-(sp)
        lea     score_patch_descriptors(pc),a0
        lea     field_values(pc),a4
        move.w  #SCORE_PATCH_COUNT-1,d7
patch_next_score_pointer:
        move.l  (a0)+,a1
        move.l  (a0)+,a2
        move.l  (a0)+,a3
        move.w  (a0)+,d1
        cmpi.w  #$ffff,d1
        beq.s   use_fixed_pointer
        moveq   #0,d2
        move.b  0(a4,d1.w),d2
        lsl.w   #2,d2
        move.l  0(a3,d2.w),d0
        bra.s   write_score_pointer
use_fixed_pointer:
        move.l  (a3),d0
write_score_pointer:
        move.l  d0,d1
        swap    d1
        move.w  d1,(a1)
        move.w  d0,(a2)
        dbra    d7,patch_next_score_pointer
        movem.l (sp)+,d0-d2/d7/a0-a4
        rts
