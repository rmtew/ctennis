        include "amiga/game/audio_state.i"
; Shared maintained sequencer. Requests queue a musical phrase without cutting
; the current note; completion means its last note was loaded, as the lifecycle
; requires. AV_DONE remains last-loaded for legacy waits; full phrase completion
; is separately duration/level-aware via game_audio_phrase_complete.
game_audio_reset:
        movem.l d0-d7/a0-a3,-(sp)
        lea     game_audio_voices,a0
        moveq   #95,d0
.clear:
        clr.b   (a0)+
        dbra    d0,.clear
        move.b  #2,game_audio_rate
        move.b  #2,game_audio_wait
        clr.b   game_audio_transpose
        clr.b   game_audio_due
        lea     game_audio_voices,a0
        moveq   #0,d7
.voice:
        move.b  #-1,AV_CLIP(a0)
        move.b  #1,AV_DONE(a0)
        move.b  #2,AV_OCTAVE(a0)
        move.b  #7,AV_RELEASE_SCALE(a0)
        move.b  #16,AV_DEFAULT_DURATION(a0)
        move.b  #16,AV_ENVELOPE_STEP(a0)
        moveq   #0,d0
        bsr     game_audio_write_level
        adda.w  #AV_SIZE,a0
        addq.w  #1,d7
        cmpi.w  #3,d7
        bne.s   .voice
        movem.l (sp)+,d0-d7/a0-a3
        rts
; D0=clip, D1=voice. Preserve all registers for native gameplay/lifecycle callers.
game_audio_queue:
        movem.l d0-d2/a0-a1,-(sp)
        move.w  d1,d2
        lsl.w   #5,d2
        lea     game_audio_voices,a0
        adda.w  d2,a0
        move.b  d0,AV_CLIP(a0)
        lsl.w   #2,d0
        lea     native_audio_scores,a1
        move.l  (a1,d0.w),AV_NEXT(a0)
        clr.b   AV_CURSOR(a0)
        clr.b   AV_DONE(a0)
        clr.b   AV_RELEASE(a0)
        movem.l (sp)+,d0-d2/a0-a1
        rts
game_audio_request_cue:
        movem.l d0-d1,-(sp)
        moveq   #4,d0
        moveq   #2,d1
        bsr     game_audio_queue
        movem.l (sp)+,d0-d1
        rts
game_audio_request_hit:
        movem.l d0-d1,-(sp)
        moveq   #5,d0
        moveq   #2,d1
        bsr     game_audio_queue
        movem.l (sp)+,d0-d1
        rts
game_audio_cue_complete:
        moveq   #0,d0
        move.b  game_audio_voices+2*AV_SIZE+AV_DONE,d0
        rts
; Own countdown: one decrement per shared native tick in play AND service waits.
game_audio_tick:
        movem.l d0-d7/a0-a3,-(sp)
        clr.b   game_audio_due
        subq.b  #1,game_audio_wait
        bne     .done
        st      game_audio_due
.voices:
        moveq   #2,d7
        lea     game_audio_voices+2*AV_SIZE,a0
.voice:
        tst.b   AV_DURATION(a0)
        beq.s   .load
        subq.b  #1,AV_DURATION(a0)
        bne     .envelope
        moveq   #15,d0
        bsr     game_audio_emit_level
.load:
        tst.b   AV_DONE(a0)
        bne     .envelope
        move.l  AV_NEXT(a0),a1
        move.b  1(a1),d6
        btst    #0,d6
        beq.s   .base
        move.b  4(a1),AV_OCTAVE(a0)
.base:
        btst    #1,d6
        beq.s   .shape
        move.b  5(a1),AV_BASE(a0)
.shape:
        btst    #2,d6
        beq.s   .scale
        move.b  6(a1),AV_ENVELOPE(a0)
.scale:
        btst    #3,d6
        beq.s   .duration
        move.b  7(a1),AV_RELEASE_SCALE(a0)
.duration:
        btst    #4,d6
        beq.s   .transpose
        move.b  8(a1),AV_DEFAULT_DURATION(a0)
.transpose:
        btst    #5,d6
        beq.s   .cadence
        move.b  10(a1),game_audio_transpose
.cadence:
        btst    #6,d6
        beq.s   .advance
        move.b  11(a1),game_audio_rate
.advance:
        addq.b  #1,AV_CURSOR(a0)
        lea     16(a1),a2
        move.l  a2,AV_NEXT(a0)
        move.b  (a1),d6
        btst    #3,d6
        beq.s   .note
        move.b  #1,AV_DONE(a0)
.note:
        btst    #4,d6
        bne     .envelope
        btst    #0,d6
        bne.s   .initial_level
        move.b  2(a1),AV_KEY(a0)
        move.b  AV_OCTAVE(a0),AV_NOTE_OCTAVE(a0)
        btst    #2,d6
        beq.s   .pitch
        move.b  3(a1),AV_NOTE_OCTAVE(a0)
.pitch:
        moveq   #0,d2
        move.b  AV_NOTE_OCTAVE(a0),d2
        andi.w  #7,d2
        mulu.w  #384,d2
        moveq   #0,d0
        move.b  game_audio_transpose,d0
        mulu.w  #24,d0
        add.w   d0,d2
        moveq   #0,d0
        move.b  AV_KEY(a0),d0
        add.w   d0,d0
        add.w   d0,d2
        lea     native_audio_periods,a2
        cmpi.w  #GAME_RESULT_SOUND,game_lifecycle
        bne.s   .period_table
        lea     native_victory_periods,a2
.period_table:
        move.w  (a2,d2.w),d0
        move.w  d0,AV_PERIOD(a0)
        bsr     game_audio_write_period
.initial_level:
        moveq   #15,d0
        btst    #0,d6
        bne.s   .level
        tst.b   AV_ENVELOPE(a0)
        bne.s   .level
        move.b  AV_BASE(a0),d0
.level:
        bsr     game_audio_emit_level
        moveq   #0,d3
        move.b  AV_DEFAULT_DURATION(a0),d3
        btst    #1,d6
        beq.s   .set_duration
        move.b  9(a1),d3
.set_duration:
        move.b  d3,AV_DURATION(a0)
        moveq   #0,d0
        move.b  AV_RELEASE_SCALE(a0),d0
        mulu.w  d3,d0
        lsr.w   #3,d0
        addq.b  #1,d0
        move.b  d0,AV_RELEASE(a0)
        clr.b   AV_ENVELOPE_STEP(a0)
        btst    #0,d6
        beq.s   .envelope
        move.b  #16,AV_ENVELOPE_STEP(a0)
.envelope:
        tst.b   AV_ENVELOPE(a0)
        beq.s   .release
        cmpi.b  #16,AV_ENVELOPE_STEP(a0)
        beq.s   .next
        subq.b  #1,AV_RELEASE(a0)
        beq.s   .release_start
        cmpi.b  #8,AV_ENVELOPE_STEP(a0)
        beq.s   .next
        bra.s   .envelope_level
.release_start:
        move.b  #8,AV_ENVELOPE_STEP(a0)
.envelope_level:
        moveq   #0,d0
        move.b  AV_ENVELOPE(a0),d0
        lsl.w   #4,d0
        moveq   #0,d1
        move.b  AV_ENVELOPE_STEP(a0),d1
        add.w   d1,d0
        lea     native_audio_envelopes,a2
        move.b  (a2,d0.w),d0
        addq.b  #1,AV_ENVELOPE_STEP(a0)
        bsr     game_audio_emit_level
        bra.s   .next
.release:
        tst.b   AV_DURATION(a0)
        beq.s   .next
        subq.b  #1,AV_RELEASE(a0)
        bne.s   .next
        moveq   #15,d0
        bsr     game_audio_emit_level
.next:
        suba.w  #AV_SIZE,a0
        dbra    d7,.voice
        cmpi.w  #GAME_RESULT_SOUND,game_lifecycle
        bne.s   .rearm
        bsr     game_audio_phrase_complete
        tst.b   d0
        beq.s   .rearm
        ; Notify only after every final duration actually expires. Reload the
        ; next downbeat in THIS sequencer step, avoiding an extra empty step.
        st      game_celebration_first_play
        addq.w  #1,game_celebration_loops
        bsr     game_result_sound
        bra     .voices
.rearm:
        cmpi.w  #GAME_RESULT_SOUND,game_lifecycle
        bne.s   .ordinary_rate
        ; Game updates are ~59.923Hz, NOT the PAL50 video rate assumed by
        ; authored .04s score units. A bounded2/3-tick cadence averages2.4
        ; native ticks/unit (~40.052ms), retaining the intended125BPM pacing.
        moveq   #2,d0
        addq.b  #2,game_celebration_audio_fraction
        cmpi.b  #5,game_celebration_audio_fraction
        bcs.s   .victory_rate
        subq.b  #5,game_celebration_audio_fraction
        moveq   #3,d0
.victory_rate:
        move.b  d0,game_audio_wait
        bra.s   .done
.ordinary_rate:
        move.b  game_audio_rate,game_audio_wait
.done:
        movem.l (sp)+,d0-d7/a0-a3
        rts
; Native envelope step -> calibrated hardware amplitude. Diagnostics observe
; the emitted musical level, but never control it or feed the hardware sink.
game_audio_emit_level:
        andi.w  #15,d0
        lea     game_audio_levels,a2
        move.b  (a2,d0.w),d0
        andi.w  #255,d0
        move.b  d0,AV_LEVEL(a0)
        bra     game_audio_write_level

game_audio_levels: dc.b 64,51,40,32,25,20,16,13,10,8,6,5,4,3,3,0
; A0 voice, result D0: no final note duration or emitted level remains.
game_audio_voice_complete:
        moveq   #0,d0
        tst.b   AV_DONE(a0)
        beq.s   .done
        tst.b   AV_DURATION(a0)
        bne.s   .done
        tst.b   AV_LEVEL(a0)
        bne.s   .done
        moveq   #1,d0
.done:  rts
game_audio_phrase_complete:
        movem.l d1/a0,-(sp)
        lea     game_audio_voices,a0
        moveq   #2,d1
.voice: bsr     game_audio_voice_complete
        tst.b   d0
        beq.s   .done
        adda.w  #AV_SIZE,a0
        dbra    d1,.voice
.done:  movem.l (sp)+,d1/a0
        rts
        even
game_audio_voices: dcb.b 3*AV_SIZE,0
game_audio_rate: dc.b 2
game_audio_wait: dc.b 2
game_audio_transpose: dc.b 0
game_audio_due: dc.b 0
        even
        include "assets/native/audio/data.i"
