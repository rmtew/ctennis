; Temporary CT08 sound-stream ABI. Lifecycle requests named paired effects;
; the existing decoder/Paula sink consumes these records. No Z80 registers.
game_result_sound:
        move.w  #sound_stream_2-1,d0
        moveq   #$22,d1
        lea     $85(a5),a0
        bsr.s   game_arm_pair_channel
        move.w  #sound_stream_3-1,d0
        moveq   #$26,d1
        lea     $93(a5),a0
        bra.s   game_arm_pair_channel
game_start_sound:
        move.w  #sound_stream_0-1,d0
        moveq   #$4f,d1
        lea     $85(a5),a0
        bsr.s   game_arm_pair_channel
        move.w  #sound_stream_1-1,d0
        moveq   #$45,d1
        lea     $93(a5),a0
game_arm_pair_channel:
        move.b  d0,(a0)
        lsr.w   #8,d0
        move.b  d0,1(a0)
        move.b  d1,2(a0)
        clr.b   3(a0)
        move.b  #1,4(a0)
        clr.b   13(a0)
        rts
game_pair_sound_complete:
        moveq   #0,d0
        move.b  $88(a5),d1
        cmp.b   $89(a5),d1
        bne.s   .done
        move.b  $96(a5),d1
        cmp.b   $97(a5),d1
        bne.s   .done
        moveq   #1,d0
.done:
        rts

game_result_redraw:
        bra     game_scene_redraw_fields
