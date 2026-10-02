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
        move.w  #511,d7
.clear_overlay:
        clr.b   (a2)+
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
        cmpi.b  #8,d0
        bcs.s   .human_win
        lea     ui_demo_blue_win,a0
        cmpi.b  #8,d0
        beq.s   .win_text
        lea     ui_demo_pink_win,a0
        bra.s   .win_text
.human_win:
        cmpi.b  #4,d0
        beq.s   .serve_overlay
        lea     ui_blue_win,a0
        cmpi.b  #2,d0
        beq.s   .win_text
        lea     ui_pink_win,a0
.win_text:
        bsr     ui_text
        move.b  game_games_a,d0
        addi.b  #'0',d0
        move.b  d0,ui_tally_blue_digit
        move.b  d0,ui_demo_tally_blue_digit
        move.b  game_games_b,d0
        addi.b  #'0',d0
        move.b  d0,ui_tally_pink_digit
        move.b  d0,ui_demo_tally_pink_digit
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
        lea     title_plane0+112*32,a2
        moveq   #3,d6
.clear_plane:
        move.w  #80*32-1,d7
        move.l  a2,a1
.clear_row:
        clr.b   (a1)+
        dbra    d7,.clear_row
        adda.w  #6144,a2
        dbra    d6,.clear_plane
        move.w  #6144,d4
        moveq   #0,d0
        move.b  ui_page,d0
        bne.s   .page
        lea     ui_menu_lines,a3
        lea     title_plane0+144*32,a2
        moveq   #3,d6
.menu_line:
        move.l  (a3)+,a0
        cmpi.b  #2,d6
        bne.s   .menu_draw
        lea     ui_players_one,a0
        tst.b   ui_player_count
        beq.s   .menu_draw
        lea     ui_players_two,a0
.menu_draw:
        bsr     ui_text
        adda.w  #256,a2
        dbra    d6,.menu_line
        moveq   #0,d0
        move.b  ui_selection,d0
        lsl.w   #8,d0
        lea     title_plane0+144*32-2,a2
        adda.w  d0,a2
        lea     ui_marker,a0
        bsr     ui_text
        lea     title_plane0+184*32,a2
        lea     ui_menu_hint,a0
        bsr     ui_text
        bra.s   .publish
.page:
        subq.w  #1,d0
        lsl.w   #2,d0
        lea     ui_pages,a0
        move.l  0(a0,d0.w),a3
        lea     title_plane0+112*32,a2
        moveq   #9,d6
.page_line:
        move.l  (a3)+,a0
        bsr     ui_text
        adda.w  #256,a2
        dbra    d6,.page_line
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
        move.l  a4,d2
        moveq   #3,d5
.plane:
        ; Keep glyph pointer A1, use A4 temporarily for destination.
        move.l  a4,-(sp)
        move.l  d2,a4
        move.b  d1,(a4)
        move.l  (sp)+,a4
        add.l   d4,d2
        dbra    d5,.plane
        adda.w  #32,a4
        dbra    d7,.row
        addq.l  #1,a2
        bra.s   .char
.done:  movem.l (sp)+,d0-d3/d5/d7/a0-a2/a4
        rts

