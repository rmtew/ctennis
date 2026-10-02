; Select pre-rendered native bitplane banks for the six scoreboard fields.
; Patch the inactive Copper list after a changed scoreboard selection.
patch_score_pointers:
        movem.l d0-d2/d7/a0-a4,-(sp)
        ; Each inactive list retains its selected banks. Rewriting all SCORE_PATCH_COUNT
        ; descriptors on every PAL publication stalls a source update even
        ; when no field changed. Cache values independently for the two lists.
        lea     score_pointer_cache(pc),a3
        tst.l   copper_write_delta
        beq.s   score_cache_selected
        addq.l  #6,a3
score_cache_selected:
        move.l  a3,a2
        lea     prepared_field_values(pc),a4
        moveq   #5,d7
score_cache_compare:
        move.b  (a4)+,d0
        cmp.b   (a3)+,d0
        bne.s   score_cache_changed
        dbra    d7,score_cache_compare
        bra.s   score_patch_done
score_cache_changed:
        lea     prepared_field_values(pc),a4
        moveq   #5,d7
score_cache_copy:
        move.b  (a4)+,(a2)+
        dbra    d7,score_cache_copy
        lea     score_patch_descriptors(pc),a0
        lea     prepared_field_values(pc),a4
        move.w  #SCORE_PATCH_COUNT-1,d7
patch_next_score_pointer:
        move.l  (a0)+,a1
        move.l  (a0)+,a2
        adda.l  copper_write_delta,a1
        adda.l  copper_write_delta,a2
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
score_patch_done:
        movem.l (sp)+,d0-d2/d7/a0-a4
        rts
score_pointer_cache: dcb.b 12,$ff
        even
