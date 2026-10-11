; Named native phrase requests; lifecycle observes actual queue completion.
game_result_sound:
        movem.l d0-d1,-(sp)
        moveq   #2,d0
        moveq   #0,d1
        bsr     game_audio_queue
        moveq   #3,d0
        moveq   #1,d1
        bsr     game_audio_queue
        moveq   #6,d0
        moveq   #2,d1
        bsr     game_audio_queue
        movem.l (sp)+,d0-d1
        rts
game_start_sound:
        movem.l d0-d1,-(sp)
        moveq   #0,d0
        moveq   #0,d1
        bsr     game_audio_queue
        moveq   #1,d0
        moveq   #1,d1
        bsr     game_audio_queue
        movem.l (sp)+,d0-d1
        rts
game_pair_sound_complete:
        moveq   #0,d0
        tst.b   game_audio_voices+AV_DONE-game_core_state(a5)
        beq.s   .done
        tst.b   game_audio_voices+AV_SIZE+AV_DONE-game_core_state(a5)
        beq.s   .done
        moveq   #1,d0
.done:
        rts

game_result_redraw:
        bra     game_scene_redraw_fields
