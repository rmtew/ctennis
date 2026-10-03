; Update only the building bank. Prepared fields remain tied to its generation.
patch_score_pointers:
        movem.l d0-d7/a0-a5,-(sp)
        lea     score_pointer_cache(pc),a3
        move.w  build_bank_index,d0
        mulu.w  #6,d0
        adda.w  d0,a3
score_cache_selected:
        move.l  a3,a2
        lea     prepared_field_values(pc),a4
        moveq   #0,d3
        moveq   #0,d4
        cmpi.b  #$ff,(a2)
        bne.s   score_cache_mask
        moveq   #1,d4
score_cache_mask:
        moveq   #0,d2
        moveq   #5,d7
score_cache_compare:
        move.b  (a4)+,d0
        cmp.b   (a3)+,d0
        beq.s   score_cache_same
        bset    d2,d3
score_cache_same:
        addq.w  #1,d2
        dbra    d7,score_cache_compare
        tst.b   d3
        beq     score_patch_done
score_cache_changed:
        bsr     hud_prepare_pixels
        move.b  d3,d0
        andi.b  #$30,d0
        bne.s   score_patch_regions
        tst.b   d4
        beq     score_cache_commit
score_patch_regions:
        lea     score_patch_descriptors(pc),a0
        lea     prepared_field_values(pc),a4
        move.w  #SCORE_PATCH_COUNT-1,d7
patch_next_score_pointer:
        move.w  12(a0),d1
        cmpi.w  #$fffe,d1
        bcc.s   use_fixed_pointer
        btst    d1,d3
        beq.s   skip_score_pointer
        move.l  8(a0),a3
        moveq   #0,d2
        move.b  0(a4,d1.w),d2
        lsl.w   #2,d2
        move.l  0(a3,d2.w),d0
        bra.s   write_score_pointer
use_fixed_pointer:
        tst.b   d4
        beq.s   skip_score_pointer
        move.l  8(a0),a3
        move.l  (a3),d0
        cmpi.w  #$fffe,d1
        bne.s   write_score_pointer
        move.w  build_bank_index,d2
        mulu.w  #HUD_BANK_SIZE,d2
        add.l   d2,d0
write_score_pointer:
        move.l  (a0),a1
        move.l  4(a0),a5
        adda.l  copper_write_delta,a1
        adda.l  copper_write_delta,a5
        move.l  d0,d1
        swap    d1
        move.w  d1,(a1)
        move.w  d0,(a5)
skip_score_pointer:
        lea     14(a0),a0
        dbra    d7,patch_next_score_pointer
score_cache_commit:
        ; Publish cache only after all bitmap words and region pointers are ready.
        lea     prepared_field_values(pc),a4
        moveq   #5,d7
score_cache_copy:
        move.b  (a4)+,(a2)+
        dbra    d7,score_cache_copy
score_patch_done:
        movem.l (sp)+,d0-d7/a0-a5
        rts

; D3=changed-field mask. No live field reads or front/ready-bank writes.
hud_prepare_pixels:
        movem.l d0-d7/a0-a4,-(sp)
        lea     hud_bank0,a4
        move.w  build_bank_index,d0
        mulu.w  #HUD_BANK_SIZE,d0
        adda.l  d0,a4
        btst    #0,d3
        beq.s   .point_b
        moveq   #0,d0
        move.b  prepared_field_values,d0
        bsr     hud_point_mask
        lea     HUD_POINT2+2(a4),a0
        bsr     hud_stamp_point
.point_b:
        btst    #1,d3
        beq.s   .status
        moveq   #0,d0
        move.b  prepared_field_values+1,d0
        bsr     hud_point_mask
        move.l  a1,a2
        lea     HUD_POINT0+28(a4),a0
        bsr     hud_stamp_point
        move.l  a2,a1
        lea     HUD_POINT2+28(a4),a0
        bsr     hud_stamp_point
        move.l  a2,a1
        lea     HUD_POINT3+28(a4),a0
        bsr     hud_stamp_point
.status:
        btst    #4,d3
        beq.s   .games
        moveq   #0,d0
        move.b  prepared_field_values+4,d0
        lsl.w   #2,d0
        lea     hud_status_plane1,a1
        move.l  0(a1,d0.w),a1
        lea     HUD_GAMES+24*32(a4),a0
        moveq   #63,d7
.status_copy:
        move.l  (a1)+,(a0)+
        dbra    d7,.status_copy
.games:
        ; Copying status overwrites both WIN words in row3. Repair each side
        ; even if that side's count did not change (including all earned -> grey).
        moveq   #2,d5
        lea     HUD_GAMES+2(a4),a0
        bsr.s   hud_games_side
        moveq   #3,d5
        lea     HUD_GAMES+28(a4),a0
        bsr.s   hud_games_side
        movem.l (sp)+,d0-d7/a0-a4
        rts

hud_point_mask:
        cmpi.w  #5,d0
        bne.s   .not_deuce
        moveq   #3,d0
.not_deuce:
        cmpi.w  #6,d0
        bne.s   .index
        moveq   #5,d0
.index:
        lsl.w   #5,d0
        lea     hud_point_tiles,a1
        adda.w  d0,a1
        rts
hud_stamp_point:
        moveq   #15,d7
.row:
        move.w  (a1)+,(a0)
        adda.w  #32,a0
        dbra    d7,.row
        rts

hud_games_side:
        moveq   #0,d6
        moveq   #5,d7
        btst    d5,d3
        bne.s   .draw
        btst    #4,d3
        beq.s   .done
        moveq   #3,d6
        moveq   #0,d7
        adda.w  #24*32,a0
.draw:
        lea     prepared_field_values(pc),a1
        moveq   #0,d0
        move.b  0(a1,d5.w),d0
.label:
        lea     hud_win_tile,a1
        moveq   #7,d1
.row:
        move.w  (a1)+,d2
        cmp.w   d0,d6
        bcc.s   .grey
        clr.w   d2
.grey:
        move.w  d2,(a0)
        adda.w  #32,a0
        dbra    d1,.row
        addq.w  #1,d6
        dbra    d7,.label
.done:
        rts
        even
score_pointer_cache: dcb.b 18,$ff
        even
