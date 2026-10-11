; Preview-only causal dispatch. Original live/replay/seek core stays unchanged.
; Route is chosen once from the complete immutable edited incoming origin.
; No fallback can continue an already reduced context as full match state.
game_preview_predictor_code_begin:

; A5 complete origin. D0=1 projected/0 original, D1 rejection class0..7.
; Preserve D2-D7/A0-A6. No writes, no logical operation or hardware access.
game_preview_predictor_eligible:
        movem.l d2-d7/a0-a6,-(sp)
        moveq   #0,d0
        moveq   #1,d1
        tst.w   game_preview_projection_requested
        beq     .done
        cmpi.w  #3,game_preview_kind
        bcc     .done
        tst.b   game_preview_incoming_valid
        beq     .done
        moveq   #2,d1
        cmpi.w  #GAME_PLAYING,game_lifecycle-game_core_state(a5)
        bne     .done
        moveq   #3,d1
        tst.b   game_score_initialized-game_core_state(a5)
        beq     .done
        cmpi.b  #S_ACTIVE,game_score_state+S_STAGE-game_core_state(a5)
        bne     .done
        moveq   #4,d1
        tst.b   game_core_command-game_core_state(a5)
        bne     .done
        tst.b   game_restart_context-game_core_state(a5)
        bne     .done
        move.b  game_mode-game_core_state(a5),d2
        andi.b  #$e4,d2 ; title/input suppression, round/result, two-human
        bne     .done
        moveq   #5,d1
        moveq   #0,d7
        move.w  game_preview_end,d7
        cmpi.w  #1,d7
        bhi     .done
        moveq   #1,d2
        lsl.b   d7,d2 ; upper AI1 when human lower; lower AI2 when human upper
        cmp.b   game_score_state+S_AI-game_core_state(a5),d2
        bne     .done
        ori.b   #$40,d2
        cmp.b   game_score_flags-game_core_state(a5),d2
        bne     .done
        moveq   #0,d2
        move.b  game_mode-game_core_state(a5),d2
        lsr.b   #4,d2
        andi.b  #1,d2
        cmp.w   d7,d2
        bne     .done
        lea     game_play_state-game_core_state(a5),a4
        tst.b   G_LOWER_AI(a4,d7.w)
        bne     .done
        move.w  d7,d2
        eori.w  #1,d2
        tst.b   G_LOWER_AI(a4,d2.w)
        beq     .done
        moveq   #6,d1
        cmp.b   game_lower_owner-game_core_state(a5),d7
        bne     .done
        cmp.b   game_upper_owner-game_core_state(a5),d2
        bne     .done
        moveq   #7,d1
        lsl.b   #6,d2
        cmp.b   G_CONTACT(a4),d2
        bne     .done
        btst    #6,G_FLIGHT(a4)
        beq     .done
        btst    #7,G_FLIGHT(a4)
        bne     .done
        moveq   #1,d0
        moveq   #0,d1
.done:  movem.l (sp)+,d2-d7/a0-a6
        rts

; Same no-argument envelope boundary. Resolver and exact requests use original.
game_preview_dispatch:
        cmpi.b  #2,game_preview_active
        bne.s   .original
        moveq   #0,d7
        move.b  game_preview_variant,d7
        lea     game_preview_predictor_routes,a0
        tst.b   (a0,d7.w)
        beq.s   .original
        bra     game_preview_predictor_tick
.original:
        bra     game_tick_dispatch_body

; All future-affecting incoming motion/contact remains actual shared code.
; Omitted score/display/audio state is incidental only within the guarded horizon.
game_preview_predictor_tick:
        bsr     input_update
        bsr     game_play_tick
        bsr     game_scene_finish_tick
        bra     game_advance_clocks

game_preview_predictor_code_end:
