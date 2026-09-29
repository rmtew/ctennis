; Source-semantic port of the G-1009 three-channel PSG interpreter (17C5-19BB).
; A0 is the current RAM record; A5 is C000; A6 is the virtual Z80 address space.
; This is separate from the generated body because its indirect command jump,
; indexed Z80 stack transfers, and PSG OUTs still require translation repair.
audio_tick_adapter:
        move.b  #2,audio_channel_index
audio_next_channel:
        moveq   #0,d0
        move.b  audio_channel_index,d0
        mulu.w  #14,d0
        lea     $85(a5),a0
        adda.w  d0,a0
        tst.b   12(a0)
        beq.s   audio_fetch_setup
        subq.b  #1,12(a0)
        bne.s   audio_service_envelope
        moveq   #15,d0
        bsr     audio_emit_volume
audio_fetch_setup:
        bsr     audio_fetch_byte
        tst.b   d1
        bne.s   audio_service_envelope
        move.b  d0,d2
        bsr     audio_dispatch_command
        tst.b   d1
        beq.s   audio_fetch_setup
audio_service_envelope:
        tst.b   10(a0)
        beq.s   audio_release
        bsr     audio_step_envelope
        bra.s   audio_advance_channel
audio_release:
        tst.b   12(a0)
        beq.s   audio_advance_channel
        subq.b  #1,13(a0)
        bne.s   audio_advance_channel
        moveq   #15,d0
        bsr     audio_emit_volume
audio_advance_channel:
        subq.b  #1,audio_channel_index
        bpl     audio_next_channel
        move.b  $82(a5),$83(a5)
        rts

; Returns D0=byte, D1=stop flag. A0 and the channel index remain intact.
audio_fetch_byte:
        moveq   #0,d1
        moveq   #0,d3
        move.b  4(a0),d3
        cmp.b   3(a0),d3
        bne.s   audio_fetch_active
        move.b  3(a0),d0
        moveq   #1,d1
        rts
audio_fetch_active:
        move.w  d3,d4
        addq.b  #1,d4
        cmp.b   2(a0),d4
        bcs.s   audio_fetch_store_index
        clr.b   d4
audio_fetch_store_index:
        move.b  d4,4(a0)
        moveq   #0,d4
        move.b  1(a0),d4
        lsl.w   #8,d4
        move.b  (a0),d4
        add.w   d3,d4
        moveq   #0,d0
        move.b  0(a6,d4.w),d0
        rts

; D2 is the command. D1=1 after a note/rest, otherwise zero.
audio_dispatch_command:
        moveq   #0,d3
        move.b  d2,d3
        lsr.b   #4,d3
        andi.b  #7,d3
        moveq   #0,d4
        move.b  d2,d4
        andi.b  #15,d4
        cmpi.b  #0,d3
        bne.s   audio_command_one
        tst.b   d4
        bne.s   audio_table_note
        moveq   #1,d6
        bra     audio_volume_duration
audio_table_note:
        subq.b  #1,d4
        moveq   #0,d5
        move.b  7(a0),d5
        bsr     audio_emit_pitch
        moveq   #0,d6
        bra     audio_volume_duration
audio_command_one:
        cmpi.b  #1,d3
        bne.s   audio_command_two
        bsr     audio_fetch_byte
        move.b  d0,d2
        andi.b  #$7f,d0
        subq.b  #1,d0
        moveq   #0,d4
        move.b  d0,d4
        moveq   #0,d5
audio_reduce_octave:
        cmpi.w  #12,d4
        bcs.s   audio_emit_long_note
        subi.w  #12,d4
        addq.b  #1,d5
        bra.s   audio_reduce_octave
audio_emit_long_note:
        bsr     audio_emit_pitch
        moveq   #0,d6
        bra     audio_volume_duration
audio_command_two:
        cmpi.b  #2,d3
        bne.s   audio_command_three
        btst    #7,d2
        beq.s   audio_set_octave
        move.b  d4,$84(a5)
        bra     audio_command_continue
audio_set_octave:
        andi.b  #7,d2
        move.b  d2,7(a0)
        bra     audio_command_continue
audio_command_three:
        cmpi.b  #3,d3
        bne.s   audio_command_four
        moveq   #15,d0
        sub.b   d4,d0
        move.b  d0,6(a0)
        bra     audio_command_continue
audio_command_four:
        cmpi.b  #4,d3
        bne.s   audio_command_five
        moveq   #0,d0
        moveq   #0,d3
        move.b  d2,d3
        andi.w  #7,d3
        beq.s   audio_store_envelope
        subq.w  #1,d3
        lsl.w   #3,d3
        move.b  $81(a5),d0
        lsl.w   #8,d0
        move.b  $80(a5),d0
        add.w   d3,d0
audio_store_envelope:
        move.b  d0,9(a0)
        lsr.w   #8,d0
        move.b  d0,10(a0)
        bra     audio_command_continue
audio_command_five:
        cmpi.b  #5,d3
        bne.s   audio_command_six
        move.b  d4,5(a0)
        bra     audio_command_continue
audio_command_six:
        cmpi.b  #6,d3
        bne.s   audio_command_seven
        bsr     audio_fetch_byte
        move.b  d0,8(a0)
        bra     audio_command_continue
audio_command_seven:
        bsr     audio_fetch_byte
        move.b  d0,$82(a5)
audio_command_continue:
        moveq   #0,d1
        rts

; D4 note index, D5 shift. Emit pitch latch and data byte.
audio_emit_pitch:
        moveq   #0,d0
        move.b  $84(a5),d0
        add.b   d4,d0
        cmpi.b  #12,d0
        bcs.s   audio_pitch_index
        addq.b  #1,d5
        subi.b  #12,d0
audio_pitch_index:
        andi.w  #$ff,d0
        lsl.w   #1,d0
        addi.w  #$18da,d0
        moveq   #0,d3
        move.b  0(a6,d0.w),d3
        lsl.w   #8,d3
        addq.w  #1,d0
        move.b  0(a6,d0.w),d3
        andi.w  #7,d5
        lsr.w   d5,d3
        moveq   #0,d0
        move.b  d3,d0
        lsr.b   #4,d0
        bsr     audio_emit_tone_latch
        moveq   #0,d0
        move.w  d3,d0
        lsr.w   #8,d0
        bsr     audio_emit_psg_byte
        rts
audio_emit_tone_latch:
        andi.b  #15,d0
        moveq   #0,d4
        move.b  audio_channel_index,d4
        lsl.b   #5,d4
        or.b    d4,d0
        ori.b   #$80,d0
        bsr     audio_emit_psg_byte
        rts

; D2 command, D6 rest flag. D1=1 on return.
audio_volume_duration:
        tst.b   d6
        bne.s   audio_muted_volume
        tst.b   10(a0)
        bne.s   audio_muted_volume
        moveq   #0,d0
        move.b  6(a0),d0
        bra.s   audio_write_volume
audio_muted_volume:
        moveq   #15,d0
audio_write_volume:
        bsr     audio_emit_volume
        moveq   #0,d3
        move.b  8(a0),d3
        btst    #7,d2
        beq.s   audio_duration_ready
        bsr     audio_fetch_byte
        move.b  d0,d3
audio_duration_ready:
        move.b  d3,12(a0)
        moveq   #0,d0
        move.b  5(a0),d0
        mulu.w  d3,d0
        lsr.w   #3,d0
        addq.b  #1,d0
        move.b  d0,13(a0)
        moveq   #0,d0
        tst.b   d6
        beq.s   audio_store_step
        moveq   #16,d0
audio_store_step:
        move.b  d0,11(a0)
        moveq   #1,d1
        rts

audio_step_envelope:
        move.b  11(a0),d0
        cmpi.b  #16,d0
        beq.s   audio_envelope_done
        subq.b  #1,13(a0)
        beq.s   audio_envelope_restart
        cmpi.b  #8,d0
        beq.s   audio_envelope_done
        bra.s   audio_envelope_read
audio_envelope_restart:
        move.b  #8,11(a0)
audio_envelope_read:
        moveq   #0,d4
        move.b  11(a0),d4
        move.w  d4,d5
        lsr.w   #1,d5
        moveq   #0,d3
        move.b  10(a0),d3
        lsl.w   #8,d3
        move.b  9(a0),d3
        add.w   d5,d3
        moveq   #0,d0
        move.b  0(a6,d3.w),d0
        btst    #0,d4
        bne.s   audio_envelope_low
        lsr.b   #4,d0
audio_envelope_low:
        addq.b  #1,11(a0)
        bsr     audio_emit_volume
audio_envelope_done:
        rts

audio_emit_volume:
        andi.b  #15,d0
        moveq   #0,d4
        move.b  audio_channel_index,d4
        lsl.b   #5,d4
        or.b    d4,d0
        ori.b   #$90,d0
audio_emit_psg_byte:
        move.l  psg_ptr,a1
        move.b  d0,(a1)+
        move.l  a1,psg_ptr
        addq.b  #1,psg_count
        rts

audio_channel_index: dc.b 0
psg_count:           dc.b 0
        even
psg_ptr:             dc.l 0
psg_log:             dcb.b 64,0
