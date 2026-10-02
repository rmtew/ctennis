; D0 raw joystick mask, D3 player. Track each physical source before keyboard OR.
; Entry-held bits retire on their own physical release, including during pause.
ui_filter_joystick:
        lea     ui_joystick_bits,a1
        move.b  d0,0(a1,d3.w)
        lea     ui_joystick_entry,a2
        move.b  0(a2,d3.w),d1
        and.b   d0,d1
        move.b  d1,0(a2,d3.w)
        not.b   d1
        and.b   d1,d0
        rts

ui_sample:
        movem.l d0-d7/a0-a4,-(sp)
        clr.b   ui_edges
        clr.b   ui_fresh_input
        clr.b   ui_takeover_edge
        lea     ui_joystick_bits,a0
        lea     ui_joystick_previous,a1
        lea     ui_joystick_pressed,a2
        moveq   #1,d7
ui_joystick_edges:
        move.b  (a0)+,d0
        move.b  (a1),d1
        move.b  d0,(a1)+
        eor.b   d0,d1
        and.b   d0,d1
        move.b  d1,(a2)+
        dbra    d7,ui_joystick_edges
        lea     game_keyboard_matrix,a0
        lea     ui_previous_keys,a1
        moveq   #0,d1
ui_input_keys:
        move.b  (a0)+,d0
        move.b  (a1),d2
        move.b  d0,(a1)+
        tst.b   d2
        bne     ui_input_next
        tst.b   d0
        beq     ui_input_next
        ; Only supported gameplay/menu positions count as fresh demo input.
        cmpi.w  #$24,d1
        bne.s   ui_not_g
        st      ui_takeover_edge
ui_not_g:
        lea     game_keyboard_mapping,a2
ui_find_key:
        move.b  (a2)+,d3
        bmi.s   ui_check_menu_key
        cmp.b   d1,d3
        beq.s   ui_mark_fresh
        addq.l  #2,a2
        bra.s   ui_find_key
ui_check_menu_key:
        cmpi.w  #$01,d1
        beq.s   ui_mark_fresh
        cmpi.w  #$02,d1
        beq.s   ui_mark_fresh
        cmpi.w  #$46,d1
        beq.s   ui_mark_fresh
        cmpi.w  #$42,d1
        beq.s   ui_mark_fresh
        cmpi.w  #$44,d1
        beq.s   ui_mark_fresh
        cmpi.w  #$45,d1
        beq.s   ui_mark_fresh
        cmpi.w  #$19,d1
        bne.s   ui_key_recognized
ui_mark_fresh:
        st      ui_fresh_input
ui_key_recognized:
        cmpi.w  #$4c,d1
        beq     ui_input_up
        cmpi.w  #$11,d1
        beq     ui_input_up
        cmpi.w  #$4d,d1
        beq     ui_input_down
        cmpi.w  #$21,d1
        beq     ui_input_down
        cmpi.w  #$4f,d1
        beq     ui_input_left
        cmpi.w  #$20,d1
        beq     ui_input_left
        cmpi.w  #$4e,d1
        beq     ui_input_right
        cmpi.w  #$22,d1
        beq     ui_input_right
        cmpi.w  #$44,d1
        beq     ui_input_action
        cmpi.w  #$45,d1
        beq     ui_input_escape
        cmpi.w  #$19,d1
        beq     ui_input_pause
        bra     ui_input_next
ui_input_up:    ori.b   #UI_UP,ui_edges
        bra     ui_input_next
ui_input_down:  ori.b   #UI_DOWN,ui_edges
        bra     ui_input_next
ui_input_left:  ori.b   #UI_LEFT,ui_edges
        bra     ui_input_next
ui_input_right: ori.b   #UI_RIGHT,ui_edges
        bra     ui_input_next
ui_input_action: ori.b  #UI_ACTION,ui_edges
        bra     ui_input_next
ui_input_escape: ori.b  #UI_ESCAPE,ui_edges
        bra     ui_input_next
ui_input_pause: ori.b   #UI_PAUSE,ui_edges
ui_input_next:  addq.w  #1,d1
        cmpi.w  #128,d1
        bcs     ui_input_keys
        move.b  game_input_pressed,d0
        or.b    game_input_pressed+1,d0
        or.b    ui_joystick_pressed,d0
        or.b    ui_joystick_pressed+1,d0
        btst    #1,d0
        beq.s   ui_input_pad_down
        ori.b   #UI_UP,ui_edges
ui_input_pad_down:
        btst    #3,d0
        beq.s   ui_input_pad_left
        ori.b   #UI_DOWN,ui_edges
ui_input_pad_left:
        btst    #2,d0
        beq.s   ui_input_pad_right
        ori.b   #UI_LEFT,ui_edges
ui_input_pad_right:
        btst    #0,d0
        beq.s   ui_input_pad_action
        ori.b   #UI_RIGHT,ui_edges
ui_input_pad_action:
        andi.b  #$30,d0
        beq.s   ui_input_dispatch
        ori.b   #UI_ACTION,ui_edges
ui_input_dispatch:
        cmpi.w  #GAME_RESULT_SOUND,game_lifecycle
        beq     ui_demo_input_done
        tst.b   ui_demo
        beq.s   ui_demo_input_done
        btst    #5,ui_joystick_pressed
        beq.s   ui_demo_g
        st      ui_takeover_edge
ui_demo_g:
        tst.b   ui_takeover_edge
        beq.s   ui_demo_other
        ; P1 only: G / connector2 button2. Consume until physical release.
        clr.b   ui_demo
        bsr     game_latch_old_actions
        clr.b   ui_edges
        bra     ui_input_draw
ui_demo_other:
        move.b  game_input_pressed,d0
        or.b    game_input_pressed+1,d0
        or.b    ui_joystick_pressed,d0
        or.b    ui_joystick_pressed+1,d0
        or.b    ui_fresh_input,d0
        beq.s   ui_demo_input_done
        bsr     ui_return_title
        bra     ui_input_draw
ui_demo_input_done:
        tst.b   ui_paused
        bne     ui_input_paused
        cmpi.w  #GAME_TITLE,game_lifecycle
        beq     ui_input_draw
        cmpi.w  #GAME_SELECTION_HELD,game_lifecycle
        beq     ui_input_draw
        cmpi.w  #GAME_TITLE_TRANSITION,game_lifecycle
        bcc     ui_input_draw
        move.b  ui_edges,d0
        andi.b  #UI_PAUSE+UI_ESCAPE,d0
        beq     ui_input_draw
        st      ui_paused
        clr.b   ui_selection
        clr.b   ui_confirmation
        ; Paula volume registers are write-only: preserve sequencer-owned levels.
        moveq   #0,d0
        move.b  game_audio_voices+AV_LEVEL,d0
        move.w  d0,ui_saved_volumes
        move.b  game_audio_voices+AV_SIZE+AV_LEVEL,d0
        move.w  d0,ui_saved_volumes+2
        move.b  game_audio_voices+2*AV_SIZE+AV_LEVEL,d0
        move.w  d0,ui_saved_volumes+4
        clr.w   $dff0a8
        clr.w   $dff0b8
        clr.w   $dff0d8
        bra     ui_input_draw
ui_input_paused:
        move.b  ui_edges,d0
        andi.b  #UI_PAUSE+UI_ESCAPE,d0
        beq.s   ui_input_pause_choice
        tst.b   ui_confirmation
        beq     ui_resume
        clr.b   ui_confirmation
        bra     ui_input_draw
ui_input_pause_choice:
        move.b  ui_edges,d0
        andi.b  #UI_UP+UI_DOWN+UI_LEFT+UI_RIGHT,d0
        beq.s   ui_input_pause_action
        eori.b  #1,ui_selection
ui_input_pause_action:
        btst    #4,ui_edges
        beq     ui_input_draw
        tst.b   ui_confirmation
        beq.s   ui_input_pause_accept
        tst.b   ui_selection ; default NO, select YES explicitly
        beq     ui_resume
        bsr     ui_return_title
        bra     ui_input_draw
ui_input_pause_accept:
        tst.b   ui_selection
        beq     ui_resume
        st      ui_confirmation
        clr.b   ui_selection
ui_input_draw:  bsr     ui_feedback
        bsr     ui_render
        movem.l (sp)+,d0-d7/a0-a4
        rts
