; Diagnostic boundary only. Import captured initial conditions once; subsequent
; source-page observations and PSG-format traces are derived from native voices.
; Nothing here feeds the sequencer or Paula. Ordinary builds exclude this file.
audio_observer_reset:
        lea     audio_observer_defaults,a1
        lea     audio_observer_idle,a2
        moveq   #17,d0
.copy:
        move.b  (a1)+,(a2)+
        dbra    d0,.copy
        rts
game_audio_import_capture:
        movem.l d0-d7/a0-a4,-(sp)
        move.b  $82(a5),game_audio_rate
        move.b  $83(a5),game_audio_wait
        move.b  $84(a5),game_audio_transpose
        lea     $85(a5),a3
        lea     game_audio_voices,a0
        lea     audio_observer_idle,a4
        moveq   #0,d7
.voice:
        move.b  (a3),(a4)
        move.b  1(a3),1(a4)
        move.b  2(a3),2(a4)
        move.b  3(a3),3(a4)
        move.b  4(a3),4(a4)
        move.b  #-1,AV_CLIP(a0)
        move.b  #1,AV_DONE(a0)
        clr.b   AV_CURSOR(a0)
        move.b  5(a3),AV_RELEASE_SCALE(a0)
        move.b  6(a3),AV_BASE(a0)
        move.b  7(a3),AV_OCTAVE(a0)
        move.b  8(a3),AV_DEFAULT_DURATION(a0)
        move.b  11(a3),AV_ENVELOPE_STEP(a0)
        move.b  12(a3),AV_DURATION(a0)
        move.b  13(a3),AV_RELEASE(a0)
        clr.b   AV_ENVELOPE(a0)
        moveq   #0,d0
        move.b  10(a3),d0
        lsl.w   #8,d0
        move.b  9(a3),d0
        beq.s   .queue
        subi.w  #$19bc,d0
        lsr.w   #3,d0
        addq.w  #1,d0
        cmpi.w  #7,d0
        bhi     audio_observer_bad_initial
        move.b  d0,AV_ENVELOPE(a0)
.queue:
        moveq   #0,d0
        move.b  1(a3),d0
        lsl.w   #8,d0
        move.b  (a3),d0
        lea     native_audio_source_scores,a1
        moveq   #0,d1
.find:
        cmp.w   (a1),d0
        beq.s   .found
        addq.l  #4,a1
        addq.w  #1,d1
        cmpi.w  #6,d1
        bne.s   .find
; An idle ring must actually be stopped; unsupported active source streams fail.
        move.b  3(a3),d0
        cmp.b   4(a3),d0
        bne     audio_observer_bad_initial
        bra.s   .next
.found:
        tst.b   3(a3)
        bne     audio_observer_bad_initial
        move.b  d1,AV_CLIP(a0)
        lsl.w   #2,d1
        lea     native_audio_scores,a1
        move.l  (a1,d1.w),a1
        move.l  a1,AV_NEXT(a0)
        cmpi.b  #1,4(a3)
        beq.s   .active
.seek:
        addq.b  #1,AV_CURSOR(a0)
        bsr     audio_observer_cursor
        adda.w  #16,a1
        move.l  a1,AV_NEXT(a0)
        cmp.b   4(a3),d0
        beq.s   .selected
        cmpi.b  #64,AV_CURSOR(a0)
        bcc     audio_observer_bad_initial
        bra.s   .seek
.selected:
        tst.b   d0
        beq.s   .next
.active:
        clr.b   AV_DONE(a0)
.next:
        adda.w  #14,a3
        adda.w  #AV_SIZE,a0
        addq.l  #6,a4
        addq.w  #1,d7
        cmpi.w  #3,d7
        bne     .voice
        movem.l (sp)+,d0-d7/a0-a4
        rts
audio_observer_bad_initial:
        illegal

game_audio_export_capture:
        movem.l d0-d7/a0-a4,-(sp)
        move.b  #$bc,$80(a5)
        move.b  #$19,$81(a5)
        move.b  game_audio_rate,$82(a5)
        move.b  game_audio_wait,$83(a5)
        move.b  game_audio_transpose,$84(a5)
        lea     $85(a5),a3
        lea     game_audio_voices,a0
        lea     audio_observer_idle,a4
        moveq   #0,d7
.voice:
        moveq   #0,d0
        move.b  AV_CLIP(a0),d0
        bmi.s   .idle
        lsl.w   #2,d0
        lea     native_audio_source_scores,a1
        move.w  (a1,d0.w),d1
        move.b  d1,(a3)
        lsr.w   #8,d1
        move.b  d1,1(a3)
        move.w  2(a1,d0.w),d1
        move.b  d1,2(a3)
        clr.b   3(a3)
        move.b  #1,4(a3)
        tst.b   AV_CURSOR(a0)
        beq.s   .fields
        bsr     audio_observer_cursor
        move.b  d0,4(a3)
        bra.s   .fields
.idle:
        move.b  (a4),(a3)
        move.b  1(a4),1(a3)
        move.b  2(a4),2(a3)
        move.b  3(a4),3(a3)
        move.b  4(a4),4(a3)
.fields:
        move.b  AV_RELEASE_SCALE(a0),5(a3)
        move.b  AV_BASE(a0),6(a3)
        move.b  AV_OCTAVE(a0),7(a3)
        move.b  AV_DEFAULT_DURATION(a0),8(a3)
        moveq   #0,d0
        move.b  AV_ENVELOPE(a0),d0
        beq.s   .envelope
        subq.w  #1,d0
        lsl.w   #3,d0
        addi.w  #$19bc,d0
.envelope:
        move.b  d0,9(a3)
        lsr.w   #8,d0
        move.b  d0,10(a3)
        move.b  AV_ENVELOPE_STEP(a0),11(a3)
        move.b  AV_DURATION(a0),12(a3)
        move.b  AV_RELEASE(a0),13(a3)
        adda.w  #14,a3
        adda.w  #AV_SIZE,a0
        addq.l  #6,a4
        addq.w  #1,d7
        cmpi.w  #3,d7
        bne     .voice
        movem.l (sp)+,d0-d7/a0-a4
        rts
; Read-only mapping of an actual native note cursor to the retained source ABI.
audio_observer_cursor:
        movem.l d1/a2,-(sp)
        moveq   #0,d1
        move.b  AV_CLIP(a0),d1
        lsl.w   #2,d1
        lea     native_audio_source_cursors,a2
        move.l  (a2,d1.w),a2
        moveq   #0,d1
        move.b  AV_CURSOR(a0),d1
        moveq   #0,d0
        move.b  (a2,d1.w),d0
        movem.l (sp)+,d1/a2
        rts
; D2 actual musical period-table offset; D7 actual voice, D0 native amplitude step.
game_audio_observe_pitch:
        movem.l d0-d4/a1-a2,-(sp)
        lea     native_audio_source_divisors,a2
        move.w  (a2,d2.w),d3
        move.w  d3,d0
        andi.w  #15,d0
        move.w  d7,d4
        lsl.w   #5,d4
        or.w    d4,d0
        ori.w   #$80,d0
        bsr.s   audio_observer_byte
        move.w  d3,d0
        lsr.w   #4,d0
        bsr.s   audio_observer_byte
        movem.l (sp)+,d0-d4/a1-a2
        rts
game_audio_observe_level:
        movem.l d0/d4/a1,-(sp)
        move.w  d7,d4
        lsl.w   #5,d4
        or.w    d4,d0
        ori.w   #$90,d0
        bsr.s   audio_observer_byte
        movem.l (sp)+,d0/d4/a1
        rts
audio_observer_byte:
        move.l  psg_ptr,a1
        move.b  d0,(a1)+
        move.l  a1,psg_ptr
        addq.b  #1,psg_count
        ifd LONG_GAME_REPLAY
        movem.l d0/d4,-(sp)
        andi.w  #255,d0
        move.w  replay_psg_hash,d4
        mulu.w  #33,d4
        add.w   d0,d4
        move.w  d4,replay_psg_hash
        addq.w  #1,replay_psg_total
        movem.l (sp)+,d0/d4
        endif
        rts
        even
; Default idle-ring diagnostics for ordinary reset inside a captured replay.
audio_observer_defaults: dc.b $af,$c0,32,0,0,0,$cf,$c0,32,0,0,0,$ef,$c0,32,0,0,0
audio_observer_idle: dcb.b 18,0
psg_count: dc.b 0
        even
psg_ptr: dc.l psg_log
psg_log: dcb.b 64,0
        ifd LONG_GAME_REPLAY
replay_psg_hash: dc.w 0
replay_psg_total: dc.w 0
        endif
        include "build/amiga/native-audio/diagnostic.i"
