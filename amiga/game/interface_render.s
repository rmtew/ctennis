; One authored/private offline font; text rendered into UI-owned chip memory.
; Title uses four existing planes. Overlay uses one white bit pattern in all four.
ui_render:
        moveq   #0,d0
        move.b  ui_overlay_kind,d0
        tst.b   ui_paused
        beq.s   .signature
        moveq   #6,d0
        tst.b   ui_confirmation
        beq.s   .signature
        moveq   #7,d0
.signature:
        moveq   #0,d1
        move.b  ui_selection,d1
        lsl.w   #8,d1
        move.b  d0,d1
        tst.b   ui_paused
        bne.s   .compare_signature
        tst.b   ui_demo
        beq.s   .compare_signature
        ori.w   #$4000,d1
        tst.b   ui_demo_choice
        beq.s   .compare_signature
        ori.w   #$8000,d1
.compare_signature:
        cmp.w   ui_overlay_signature,d1
        beq     .title_menu
        move.w  d1,ui_overlay_signature
        lea     ui_overlay_plane,a2
        moveq   #0,d4
        move.w  #512/4-1,d7
.clear_overlay:
        clr.l   (a2)+
        dbra    d7,.clear_overlay
        tst.b   ui_paused
        beq.s   .title
        lea     ui_paused_text,a0
        tst.b   ui_confirmation
        beq.s   .pause_text
        lea     ui_confirm_text,a0
.pause_text:
        lea     ui_overlay_plane,a2
        bsr     ui_footer_text
        lea     ui_resume_text,a0
        tst.b   ui_confirmation
        beq.s   .pause_selection
        lea     ui_no_text,a0
.pause_selection:
        tst.b   ui_selection
        beq.s   .pause_line
        lea     ui_return_text,a0
        tst.b   ui_confirmation
        beq.s   .pause_line
        lea     ui_yes_text,a0
.pause_line:
        lea     ui_overlay_plane+256,a2
        bsr     ui_footer_selected
        rts
.title:
        tst.b   ui_paused
        bne     .done
        moveq   #0,d0
        move.b  ui_overlay_kind,d0
        beq     .footer_finish
        lea     ui_overlay_plane,a2
        moveq   #0,d4
.win_overlay:
        cmpi.b  #10,d0
        bcs.s   .old_win_overlay
        cmpi.b  #12,d0
        bcc.s   .match_cached
        lea     ui_match_blue,a0
        btst    #0,d0
        beq.s   .match_digits
        lea     ui_match_red,a0
.match_digits:
        move.b  game_games_a,d1
        addi.b  #'0',d1
        move.b  d1,ui_match_blue_a
        move.b  d1,ui_match_red_a
        move.b  game_games_b,d1
        addi.b  #'0',d1
        move.b  d1,ui_match_blue_b
        move.b  d1,ui_match_red_b
        bsr     ui_footer_text
        ; Scores freeze for the celebration. Preserve the first line so prompt
        ; appearance and pause/resume need only one font line per callback.
        lea     ui_overlay_plane,a1
        lea     ui_match_banner,a2
        moveq   #63,d7
.match_save:
        move.l  (a1)+,(a2)+
        dbra    d7,.match_save
        bra     .done
.match_cached:
        lea     ui_match_banner,a1
        lea     ui_overlay_plane,a2
        moveq   #63,d7
.match_copy:
        move.l  (a1)+,(a2)+
        dbra    d7,.match_copy
        lea     ui_overlay_plane+256,a2
        lea     ui_match_continue,a0
        bsr     ui_footer_text
        bra     .done
.old_win_overlay:
        cmpi.b  #4,d0
        beq     .serve_overlay
        lea     ui_blue_win,a0
        cmpi.b  #2,d0
        beq.s   .win_text
        lea     ui_red_win,a0
        btst    #7,game_mode
        bne.s   .win_text
        lea     ui_ai_win,a0
.win_text:
        bsr     ui_footer_text
        move.b  game_games_a,d0
        addi.b  #'0',d0
        move.b  d0,ui_tally_blue_digit
        move.b  game_games_b,d0
        addi.b  #'0',d0
        move.b  d0,ui_tally_red_digit
        tst.b   ui_demo
        bne.s   .footer_finish
        lea     ui_overlay_plane+256,a2
        lea     ui_tally_text,a0
        bsr     ui_footer_text
        bra     .done
.serve_overlay:
        lea     ui_serve_text,a0
        bsr     ui_footer_text
.footer_finish:
        tst.b   ui_demo
        beq     .title_menu
        moveq   #0,d0
        move.b  ui_demo_choice,d0
        lsl.w   #8,d0
        lea     ui_demo_options,a1
        adda.w  d0,a1
        lea     ui_overlay_plane+256,a2
        moveq   #63,d7
.demo_controls_copy:
        move.l  (a1)+,(a2)+
        dbra    d7,.demo_controls_copy
        bra     .done
.title_menu:
        cmpi.w  #GAME_TITLE,game_lifecycle
        bne     .done
        tst.b   ui_dirty
        beq     .done
        clr.b   ui_dirty
        ; Pages use one white plane; title caches contain four explicit colour
        ; planes. Both copy once per destination and sample between planes.
        ; Selected menu rows retain the small normal/inverted row caches.
        moveq   #0,d0
        move.b  ui_page,d0
        tst.b   d0
        beq.s   .menu_cache
        subq.w  #1,d0
        mulu.w  #116*32,d0
        lea     ui_cached_pages,a3
        adda.l  d0,a3
        bra.s   .cache_ready
.menu_cache:
        lea     ui_title_pages,a3
        tst.b   ui_player_count
        beq.s   .cache_ready
        adda.w  #4*116*32,a3
.cache_ready:
        lea     title_plane0+76*32,a2
        moveq   #3,d6
.copy_plane:
        move.l  a3,a0
        move.l  a2,a1
        ; Unroll each128-byte block to keep the full-page return callback
        ; under the unchanged deadline without extra chip caches.
        move.w  #116*32/128-1,d7
.copy_word:
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        dbra    d7,.copy_word
        bsr     ui_construction_sample
        adda.w  #6144,a2
        tst.b   ui_page
        bne.s   .same_plane
        adda.w  #116*32,a3
.same_plane:
        dbra    d6,.copy_plane
        tst.b   ui_page
        bne.s   .page_selection
.selection:
        moveq   #0,d0
        move.b  ui_selection,d0
        move.w  d0,d1
        mulu.w  #11*32,d1
        lea     title_plane0+114*32,a2
        adda.w  d1,a2
        lsl.w   #8,d0
        lea     ui_menu_options,a0
        adda.w  d0,a0
        bsr     ui_title_row_copy
        bra.s   .publish
.page_selection:
        moveq   #0,d0
        move.b  ui_help_choice,d0
        lsl.w   #8,d0
        lea     ui_help_options,a0
        adda.w  d0,a0
        lea     title_plane0+182*32,a2
        bsr     ui_menu_row_copy
.publish:
        st      game_title_display
        move.b  #1,display_ready
.done:  rts

; A0 cached256-byte title row, A2 first title-plane row. Only x88..167
; belongs to the central menu; copying a full row would erase/recolour the
; flanking Classic figures. Both modes share the same three selected captions.
; Text is centred at x108 and spans40 pixels. Byte edges surround the two
; even-address longwords: never use a68000 word/longword at offset11.
ui_title_row_copy:
        movem.l d1/d7/a0-a3,-(sp)
        move.l  a0,a3
        moveq   #3,d1
.plane:
        move.l  a3,a0
        move.l  a2,a1
        moveq   #7,d7
.row:
        move.b  11(a0),11(a1)
        move.l  12(a0),12(a1)
        move.l  16(a0),16(a1)
        move.b  20(a0),20(a1)
        adda.w  #32,a0
        adda.w  #32,a1
        dbra    d7,.row
        adda.w  #6144,a2
        dbra    d1,.plane
        movem.l (sp)+,d1/d7/a0-a3
        rts

; A0 cached256-byte menu row, A2 matching first title-plane row. Copy the
; same independently authored normal/inverted pixels to all four planes.
ui_menu_row_copy:
        movem.l d1/d7/a0-a3,-(sp)
        move.l  a0,a3
        moveq   #3,d1
.plane:
        move.l  a3,a0
        move.l  a2,a1
        moveq   #63,d7
.row:
        move.l  (a0)+,(a1)+
        dbra    d7,.row
        adda.w  #6144,a2
        dbra    d1,.plane
        movem.l (sp)+,d1/d7/a0-a3
        rts

; A0 zero-terminated ASCII (<=28 columns); A2 line origin; D4 plane stride/0.
ui_selected_text:
        movem.l d0-d3/d5/d7/a0-a2/a4,-(sp)
        moveq   #-1,d3
        bra.s   ui_text_draw
ui_text:
        movem.l d0-d3/d5/d7/a0-a2/a4,-(sp)
        moveq   #0,d3
ui_text_draw:
        addq.l  #4,a2
.char:
        moveq   #0,d0
        move.b  (a0)+,d0
        beq.s   .done
        lsl.w   #3,d0
        lea     ui_font,a1
        cmpi.w  #GAME_TITLE,game_lifecycle
        bne.s   .font_ready
        lea     ui_menu_font,a1
.font_ready:
        adda.w  d0,a1
        moveq   #7,d7
        move.l  a2,a4
.row:
        move.b  (a1)+,d1
        eor.b   d3,d1
        move.b  d1,(a4)
        tst.w   d4
        beq.s   .next_row
        move.b  d1,6144(a4)
        move.b  d1,12288(a4)
        move.b  d1,18432(a4)
.next_row:
        adda.w  #32,a4
        dbra    d7,.row
        addq.l  #1,a2
        bra.s   .char
.done:  movem.l (sp)+,d0-d3/d5/d7/a0-a2/a4
        rts

; A0 ASCII, A2 footer-line origin. Court viewport is32 bytes/256 pixels;
; ui_text's four-byte title indent is compensated here, not globally changed.
; Constant footer strings must fit32 columns; overlong text is never drawn.
ui_footer_selected:
        movem.l d0-d2/a1-a2,-(sp)
        moveq   #-1,d2
        bra.s   ui_footer_draw
ui_footer_text:
        movem.l d0-d2/a1-a2,-(sp)
        moveq   #0,d2
ui_footer_draw:
        move.l  a0,a1
        moveq   #0,d0
.length:
        tst.b   (a1)+
        beq.s   .centre
        addq.w  #1,d0
        cmpi.w  #32,d0
        bhi.s   .done
        bra.s   .length
.centre:
        moveq   #32,d1
        sub.w   d0,d1
        lsr.w   #1,d1
        subq.w  #4,d1
        adda.w  d1,a2
        tst.b   d2
        bne.s   .selected
        bsr     ui_text
        bra.s   .done
.selected:
        bsr     ui_selected_text
.done:
        movem.l (sp)+,d0-d2/a1-a2
        rts
