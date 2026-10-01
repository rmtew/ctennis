; Native display events. A typed scalar packet enters at the temporary game
; ABI; this code selects six native field banks, never tiles/VRAM/VDP registers.
D_FLAGS equ 0
D_TIMER equ 1
D_MODE equ 2
D_POINT_A equ 3
D_POINT_B equ 4
D_GAME_A equ 5
D_GAME_B equ 6
D_SIZE equ 8

game_scene_update_fields:
        movem.l d0-d7/a0-a4,-(sp)
        bsr     scene_collect_fields
        ifd NATIVE_SCENE_OBSERVE
        move.b  D_FLAGS(a0),score_flags_before
        move.b  D_TIMER(a0),status_timer_before
        endif
        clr.b   score_dirty
        lea     game_display_state,a0
        move.b  D_FLAGS(a0),d0
        btst    #7,d0
        beq.s   .scores
        btst    #6,d0
        beq.s   .show_status
        cmpi.b  #255,D_TIMER(a0)
        bne.s   .scores
        andi.b  #$3f,D_FLAGS(a0)
        clr.b   field_values+4
        bra.s   .status_changed
.show_status:
        bset    #6,D_FLAGS(a0)
        andi.b  #7,d0
        move.b  d0,field_values+4
.status_changed:
        move.b  #224,D_TIMER(a0)
        st      score_dirty
.scores:
        btst    #5,D_FLAGS(a0)
        beq.s   .publish
        bsr     game_scene_draw_scores
.publish:
        bsr     scene_export_display_flags
        bsr     game_scene_present_fields
        movem.l (sp)+,d0-d7/a0-a4
        rts

; Main-thread round/result requests redraw only mode/score. They do not consume
; status-expiry events even if its clock has saturated during a service wait.
game_scene_redraw_fields:
        movem.l d0-d7/a0-a4,-(sp)
        bsr     scene_collect_fields
        clr.b   score_dirty
        lea     game_display_state,a0
        bsr     game_scene_draw_scores
        bsr     scene_export_display_flags
        bsr     game_scene_present_fields
        movem.l (sp)+,d0-d7/a0-a4
        rts

game_scene_draw_scores:
        bclr    #5,D_FLAGS(a0)
        move.b  D_POINT_A(a0),field_values
        move.b  D_POINT_B(a0),field_values+1
        move.b  D_GAME_A(a0),field_values+2
        move.b  D_GAME_B(a0),field_values+3
        moveq   #0,d0
        btst    #2,D_MODE(a0)
        bne.s   .mode
        moveq   #1,d0
        btst    #7,D_MODE(a0)
        beq.s   .mode
        moveq   #2,d0
.mode:
        move.b  d0,field_values+5
        st      score_dirty
        rts

; Native Copper/title requests are explicit lifecycle hooks. The old pending
; register flag is retired and has no display consumer in the product.
game_scene_service:
        ifd NATIVE_SCENE_OBSERVE
        bclr    #7,$02(a5) ; raw diagnostic serialization only
        endif
        rts
        even
game_display_state: dcb.b D_SIZE,0
        ifd NATIVE_SCENE_OBSERVE
score_flags_before: dc.b 0
status_timer_before: dc.b 0
        even
        endif
