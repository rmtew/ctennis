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
        bsr     ui_text
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
        bsr     ui_text
        rts
.title:
        tst.b   ui_paused
        bne     .done
        moveq   #0,d0
        move.b  ui_overlay_kind,d0
        beq     .title_menu
        lea     ui_overlay_plane,a2
        moveq   #0,d4
        cmpi.b  #1,d0
        bne.s   .win_overlay
        lea     ui_demo_text,a0
        bsr     ui_text
        lea     ui_overlay_plane+256,a2
        lea     ui_demo_hint,a0
        bsr     ui_text
        bra     .done
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
        bsr     ui_text
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
        bsr     ui_text
        bra     .done
.old_win_overlay:
        cmpi.b  #8,d0
        bcs.s   .human_win
        lea     ui_demo_blue_win,a0
        cmpi.b  #8,d0
        beq.s   .win_text
        lea     ui_demo_red_win,a0
        bra.s   .win_text
.human_win:
        cmpi.b  #4,d0
        beq.s   .serve_overlay
        lea     ui_blue_win,a0
        cmpi.b  #2,d0
        beq.s   .win_text
        lea     ui_red_win,a0
.win_text:
        bsr     ui_text
        move.b  game_games_a,d0
        addi.b  #'0',d0
        move.b  d0,ui_tally_blue_digit
        move.b  d0,ui_demo_tally_blue_digit
        move.b  game_games_b,d0
        addi.b  #'0',d0
        move.b  d0,ui_tally_red_digit
        move.b  d0,ui_demo_tally_red_digit
        lea     ui_overlay_plane+256,a2
        lea     ui_tally_text,a0
        tst.b   ui_demo
        beq.s   .tally_text
        lea     ui_demo_tally_text,a0
.tally_text:
        bsr     ui_text
        bra     .done
.serve_overlay:
        lea     ui_serve_text,a0
        bsr     ui_text
        bra     .done
.title_menu:
        cmpi.w  #GAME_TITLE,game_lifecycle
        bne     .done
        tst.b   ui_dirty
        beq     .done
        clr.b   ui_dirty
        ; Static authored pages are baked once at build time. Copy one
        ; identical white plane to all four destinations, sampling between
        ; planes. Dynamic menu choice remains the same native font drawing.
        moveq   #0,d0
        move.b  ui_page,d0
        mulu.w  #80*32,d0
        lea     ui_cached_pages,a3
        adda.l  d0,a3
        lea     title_plane0+112*32,a2
        moveq   #3,d6
.copy_plane:
        move.l  a3,a0
        move.l  a2,a1
        move.w  #80*32/32-1,d7
.copy_word:
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
        dbra    d6,.copy_plane
        tst.b   ui_page
        bne.s   .publish
        move.w  #6144,d4
        tst.b   ui_player_count
        beq.s   .marker
        lea     title_plane0+152*32,a2
        lea     ui_players_two,a0
        bsr     ui_text
.marker:
        moveq   #0,d0
        move.b  ui_selection,d0
        lsl.w   #8,d0
        lea     title_plane0+144*32-2,a2
        adda.w  d0,a2
        lea     ui_marker,a0
        bsr     ui_text
.publish:
        move.b  #1,display_ready
.done:  rts

; A0 zero-terminated ASCII (<=28 columns); A2 line origin; D4 plane stride/0.
ui_text:
        movem.l d0-d3/d5/d7/a0-a2/a4,-(sp)
        addq.l  #4,a2
.char:
        moveq   #0,d0
        move.b  (a0)+,d0
        beq.s   .done
        lsl.w   #3,d0
        lea     ui_font,a1
        adda.w  d0,a1
        moveq   #7,d7
        move.l  a2,a4
.row:
        move.b  (a1)+,d1
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
