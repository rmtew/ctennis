; Actual native voice -> Paula register output. Prepared periods and calibrated
; amplitudes are written directly; no PSG latch or source divisor is interpreted.
paula_tone_init:
        movem.l d0-d2/a0,-(sp)
        lea     $dff000,a0
        move.w  #$00ff,$09e(a0)
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
        move.w  #$800b,$096(a0)
        movem.l (sp)+,d0-d2/a0
        rts
; D7=voice, D0=period/level. Preserve sequencer scratch registers.
game_audio_write_period:
        core_trace_sink $105
        movem.l d0/d1/a2-a3,-(sp)
        move.w  d7,d1
        add.w   d1,d1
        lea     game_audio_registers,a2
        move.w  (a2,d1.w),d1
        lea     $dff000,a3
        move.w  d0,6(a3,d1.w)
        movem.l (sp)+,d0/d1/a2-a3
        rts
game_audio_write_level:
        core_trace_sink $106
        movem.l d1/a2-a3,-(sp)
        move.w  d7,d1
        add.w   d1,d1
        lea     game_audio_registers,a2
        move.w  (a2,d1.w),d1
        lea     $dff000,a3
        move.w  d0,8(a3,d1.w)
        movem.l (sp)+,d1/a2-a3
        rts
game_audio_registers: dc.w $0a0,$0b0,$0d0
