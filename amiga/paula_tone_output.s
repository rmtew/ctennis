; Native Paula output for the cartridge's three PSG tone channels.
; The source emits pitch latch + data, and independent volume latch bytes.
; Each Amiga channel loops the same four-sample square wave in chip RAM.
; PSG 0 -> Paula 0, PSG 1 -> Paula 1, PSG 2 -> Paula 3.
paula_tone_init:
        movem.l d0-d2/a0,-(sp)
        lea     $dff000,a0
        move.w  #$00ff,$09e(a0)       ; no audio period/volume modulation
        move.l  #paula_square,d0
        move.l  d0,d1
        swap    d1
        move.w  d1,$0a0(a0)
        move.w  d0,$0a2(a0)
        move.w  d1,$0b0(a0)
        move.w  d0,$0b2(a0)
        move.w  d1,$0d0(a0)
        move.w  d0,$0d2(a0)
        move.w  #2,$0a4(a0)
        move.w  #2,$0b4(a0)
        move.w  #2,$0d4(a0)
        move.w  #$0400,$0a6(a0)
        move.w  #$0400,$0b6(a0)
        move.w  #$0400,$0d6(a0)
        clr.w   $0a8(a0)
        clr.w   $0b8(a0)
        clr.w   $0d8(a0)
        move.w  #$800b,$096(a0)       ; master DMA is enabled by display init
        movem.l (sp)+,d0-d2/a0
        rts

paula_apply_psg_events:
        movem.l d0-d7/a0-a2,-(sp)
        lea     psg_log(pc),a0
        moveq   #0,d7
        move.b  psg_count,d7
        beq     paula_events_done
        subq.w  #1,d7
paula_next_event:
        moveq   #0,d0
        move.b  (a0)+,d0
        ifd LONG_GAME_REPLAY
        move.w  replay_psg_hash,d6
        mulu.w  #33,d6
        add.w   d0,d6
        move.w  d6,replay_psg_hash
        addq.w  #1,replay_psg_total
        endif
        btst    #7,d0
        beq.s   paula_tone_data
        move.w  d0,d1
        lsr.w   #5,d1
        andi.w  #3,d1
        cmpi.w  #3,d1
        beq     paula_next_done       ; source game uses only tone 0-2
        move.b  d1,paula_latched_channel
        btst    #4,d0
        bne.s   paula_volume_latch
        andi.w  #15,d0
        move.w  d1,d2
        add.w   d2,d2
        lea     paula_tone_periods(pc),a1
        move.w  0(a1,d2.w),d3
        andi.w  #$03f0,d3
        or.w    d0,d3
        move.w  d3,0(a1,d2.w)
        bra.s   paula_next_done
paula_volume_latch:
        andi.w  #15,d0
        lea     paula_volume_table(pc),a1
        moveq   #0,d3
        move.b  0(a1,d0.w),d3
        lea     paula_register_offsets(pc),a1
        add.w   d1,d1
        move.w  0(a1,d1.w),d2
        lea     $dff000,a2
        move.w  d3,8(a2,d2.w)
        bra.s   paula_next_done
paula_tone_data:
        moveq   #0,d1
        move.b  paula_latched_channel,d1
        cmpi.w  #3,d1
        beq.s   paula_next_done
        andi.w  #$3f,d0
        lsl.w   #4,d0
        move.w  d1,d2
        add.w   d2,d2
        lea     paula_tone_periods(pc),a1
        move.w  0(a1,d2.w),d3
        andi.w  #15,d3
        or.w    d0,d3
        move.w  d3,0(a1,d2.w)
        bne.s   paula_nonzero_period
        move.w  #$400,d3              ; PSG zero divisor behaves as 1024
paula_nonzero_period:
        ; PAL Paula 3546895 Hz; PSG 3579545/(32*N) Hz; four PCM samples.
        ; Rounded ratio 3546895*32/(3579545*4) ~= 507/64.
        mulu.w  #507,d3
        addi.l  #32,d3
        lsr.l   #6,d3
        cmpi.w  #123,d3
        bcc.s   paula_period_ready
        move.w  #123,d3
paula_period_ready:
        lea     paula_register_offsets(pc),a1
        move.w  0(a1,d2.w),d2
        lea     $dff000,a2
        move.w  d3,6(a2,d2.w)
paula_next_done:
        dbra    d7,paula_next_event
paula_events_done:
        movem.l (sp)+,d0-d7/a0-a2
        rts

        even
paula_latched_channel: dc.b 3
paula_volume_table: dc.b 64,51,40,32,25,20,16,13,10,8,6,5,4,3,2,0
        even
paula_tone_periods: dc.w 0,0,0
paula_register_offsets: dc.w $0a0,$0b0,$0d0
        ifd LONG_GAME_REPLAY
replay_psg_hash: dc.w 0
replay_psg_total: dc.w 0
        endif
