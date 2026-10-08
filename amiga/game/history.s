; Fixed in-memory history of complete logical operations. No gameplay rules.
; Cursor is unsigned high/low longwords; tick bytes may wrap independently.
HISTORY_RECORD_BYTES equ 14
HISTORY_RECORDS equ 1024
HISTORY_SPACING equ 64
HISTORY_CHECKPOINTS equ 16
HISTORY_CHECKPOINT_BYTES equ 12+GAME_CORE_STATE_SIZE
HISTORY_CHECKPOINT_OFFSET equ HISTORY_RECORDS*HISTORY_RECORD_BYTES
HISTORY_ATTEMPTS equ 128
HISTORY_ATTEMPT_BYTES equ 12
HISTORY_ATTEMPT_OFFSET equ HISTORY_CHECKPOINT_OFFSET+HISTORY_CHECKPOINTS*HISTORY_CHECKPOINT_BYTES
HISTORY_LIVE_OFFSET equ HISTORY_ATTEMPT_OFFSET+HISTORY_ATTEMPTS*HISTORY_ATTEMPT_BYTES
HISTORY_BUFFER_BYTES equ HISTORY_LIVE_OFFSET+GAME_CORE_STATE_SIZE

; A0 preallocated even buffer, D0 exact size. Reject before touching core.
; Caller owns its lifetime; native/standalone reserve it as a fixed BSS hunk.
; Returning D0=0 means unavailable. The product continues without recording.
game_history_attach:
        move.l  a0,d1
        beq     .invalid
        btst    #0,d1
        bne     .invalid
        cmpa.l  #game_history_buffer,a0
        bne     .invalid
        cmpi.l  #HISTORY_BUFFER_BYTES,d0
        bne     .invalid
        movem.l d2-d7/a1-a6,-(sp)
        lea     game_history_state,a1
        move.w  #game_history_state_end-game_history_state-1,d2
.clear: clr.b   (a1)+
        dbra    d2,.clear
        move.l  a0,game_history_store
        move.b  #1,game_history_mode
        bsr     game_history_checkpoint
        movem.l (sp)+,d2-d7/a1-a6
        moveq   #1,d0
        rts
.invalid:
        clr.b   game_history_mode
        clr.l   game_history_store
        moveq   #0,d0
        rts

; Wrapper saved D0-D7/A0-A6 before this call; D6 operation ID.
game_history_before:
        cmpi.b  #1,game_history_mode
        bne.s   .done
        move.w  d6,game_history_operation
        move.l  game_history_cursor+4,d7
        andi.w  #HISTORY_RECORDS-1,d7
        mulu.w  #HISTORY_RECORD_BYTES,d7
        move.l  game_history_store,a0
        adda.l  d7,a0
        move.w  d6,(a0)+
        move.w  d0,(a0)+
        move.w  d1,(a0)+
        move.w  d2,(a0)+
        move.w  d3,(a0)+
        move.w  d4,(a0)+
        move.w  d5,(a0)+
.done:  rts

game_history_after:
        cmpi.b  #1,game_history_mode
        bne.s   .done
        addq.l  #1,game_history_cursor+4
        bcc.s   .clock_ok
        addq.l  #1,game_history_cursor
        bne.s   .clock_ok
        ; Do not alias ancient cursors if the 64-bit lifetime is exhausted.
        clr.b   game_history_mode
        rts
.clock_ok:
        tst.b   game_history_probe_active
        beq.s   .checkpoint_due
        cmpi.w  #GAME_PLAYING,game_lifecycle
        bne.s   .miss
        move.b  game_contact,d0
        andi.b  #$0d,d0
        beq.s   .checkpoint_due
.miss:
        moveq   #0,d0
        move.w  game_history_probe_index,d0
        bsr     game_history_attempt_address
        move.w  #2,8(a0)
        clr.b   game_history_probe_active
.checkpoint_due:
        move.l  game_history_cursor+4,d0
        andi.w  #HISTORY_SPACING-1,d0
        bne.s   .done
        bsr     game_history_checkpoint
.done:  rts

; Return A0 checkpoint address for slot D0.w; scratch D0.
game_history_checkpoint_address:
        mulu.w  #HISTORY_CHECKPOINT_BYTES,d0
        move.l  game_history_store,a0
        adda.l  #HISTORY_CHECKPOINT_OFFSET,a0
        adda.l  d0,a0
        rts

game_history_checkpoint:
        moveq   #0,d0
        move.w  game_history_checkpoint_next,d0
        bsr     game_history_checkpoint_address
        move.l  game_history_cursor,(a0)+
        move.l  game_history_cursor+4,(a0)+
        move.w  #GAME_CORE_SCHEMA_VERSION,(a0)+
        move.w  #GAME_CORE_SIMULATION_VERSION,(a0)+
        lea     game_core_state,a1
        bsr     game_history_copy_state
        addq.w  #1,game_history_checkpoint_next
        andi.w  #HISTORY_CHECKPOINTS-1,game_history_checkpoint_next
        cmpi.w  #HISTORY_CHECKPOINTS,game_history_checkpoint_count
        beq.s   .evict
        addq.w  #1,game_history_checkpoint_count
        rts
.evict:
        ; The overwritten origin and its dependent operations/attempts retire
        ; together. Its successor is always a complete canonical checkpoint.
        moveq   #0,d0
        move.w  game_history_checkpoint_next,d0
        bsr     game_history_checkpoint_address
        move.l  (a0),game_history_oldest
        move.l  4(a0),game_history_oldest+4
.prune:
        tst.w   game_history_attempt_count
        beq.s   .done
        moveq   #0,d0
        move.w  game_history_attempt_first,d0
        bsr     game_history_attempt_address
        move.l  (a0),d0
        cmp.l   game_history_oldest,d0
        bcs.s   .remove
        bhi.s   .done
        move.l  4(a0),d0
        cmp.l   game_history_oldest+4,d0
        bcc.s   .done
.remove:
        addq.w  #1,game_history_attempt_first
        andi.w  #HISTORY_ATTEMPTS-1,game_history_attempt_first
        subq.w  #1,game_history_attempt_count
        ; An unfinished episode whose origin retired cannot later publish.
        ; Clear active if its origin is now outside the retained interval.
        tst.b   game_history_probe_active
        beq.s   .pruned
        moveq   #0,d0
        move.w  game_history_probe_index,d0
        bsr     game_history_attempt_address
        move.l  (a0),d0
        cmp.l   game_history_oldest,d0
        bcs.s   .cancel_probe
        bhi.s   .pruned
        move.l  4(a0),d0
        cmp.l   game_history_oldest+4,d0
        bcc.s   .pruned
.cancel_probe:
        clr.b   game_history_probe_active
.pruned:
        bra.s   .prune
.done:  rts

; Copy all canonical bytes A1->A0; no normalization, including reserves.
game_history_copy_state:
        move.w  #GAME_CORE_STATE_SIZE/2-1,d7
.copy:  move.w  (a1)+,(a0)+
        dbra    d7,.copy
        rts

; Freeze complete live state once. No later samples may reach the core until
; the caller resumes it. UI/branching is deliberately absent in this increment.
game_history_freeze:
        cmpi.b  #1,game_history_mode
        bne.s   .invalid
        move.l  game_history_store,a0
        adda.l  #HISTORY_LIVE_OFFSET,a0
        lea     game_core_state,a1
        bsr     game_history_copy_state
        move.b  #2,game_history_mode
        moveq   #1,d0
        rts
.invalid:
        moveq   #0,d0
        rts

game_history_resume_latest:
        cmpi.b  #2,game_history_mode
        bne.s   .invalid
        move.l  game_history_store,a1
        adda.l  #HISTORY_LIVE_OFFSET,a1
        lea     game_core_state,a0
        bsr     game_history_copy_state
        move.b  #1,game_history_mode
        moveq   #1,d0
        rts
.invalid:
        moveq   #0,d0
        rts

; Seek D0.l high/D1.l low cursor. Frozen store never changes. D0=1 success.
; Validate envelope and every needed operation before touching canonical state.
; Replay emits the actual ordered semantic outputs; native sinks suppress their
; hardware/presentation work while mode=2. CPU adapters still observe outputs.
game_history_seek:
        cmpi.b  #2,game_history_mode
        bne     .invalid
        cmp.l   game_history_oldest,d0
        bcs     .invalid
        bhi.s   .lower_ok
        cmp.l   game_history_oldest+4,d1
        bcs     .invalid
.lower_ok:
        cmp.l   game_history_cursor,d0
        bhi     .invalid
        bcs.s   .upper_ok
        cmp.l   game_history_cursor+4,d1
        bhi     .invalid
.upper_ok:
        move.l  d0,game_history_target
        move.l  d1,game_history_target+4
        clr.l   game_history_origin
        clr.l   game_history_origin+4
        clr.l   game_history_selected
        moveq   #0,d6
.find:
        moveq   #0,d0
        move.w  d6,d0
        bsr     game_history_checkpoint_address
        move.l  (a0),d0
        cmp.l   game_history_target,d0
        bhi.s   .next
        bcs.s   .candidate
        move.l  4(a0),d0
        cmp.l   game_history_target+4,d0
        bhi.s   .next
.candidate:
        tst.l   game_history_selected
        beq.s   .select
        move.l  (a0),d0
        cmp.l   game_history_origin,d0
        bcs.s   .next
        bhi.s   .select
        move.l  4(a0),d0
        cmp.l   game_history_origin+4,d0
        bcs.s   .next
.select:
        move.l  a0,game_history_selected
        move.l  (a0),game_history_origin
        move.l  4(a0),game_history_origin+4
.next:
        addq.w  #1,d6
        cmp.w   game_history_checkpoint_count,d6
        bcs.s   .find
        tst.l   game_history_selected
        beq     .invalid
        move.l  game_history_selected,a0
        cmpi.w  #GAME_CORE_SCHEMA_VERSION,8(a0)
        bne     .invalid
        cmpi.w  #GAME_CORE_SIMULATION_VERSION,10(a0)
        bne     .invalid
        lea     12(a0),a1
        bsr     game_history_validate_state
        tst.b   d0
        beq     .invalid
        move.l  game_history_target+4,d6
        sub.l   game_history_origin+4,d6
        ; Modular low subtraction covers a low-longword carry. Origins are
        ; at most63 operations away, never an unbounded replay request.
        cmpi.l  #HISTORY_SPACING-1,d6
        bhi     .invalid
        move.w  d6,game_history_replay_count
        move.l  game_history_origin+4,game_history_replay_low
        move.w  d6,d5
        beq.s   .restore
        subq.w  #1,d5
.validate:
        bsr     game_history_record_address
        move.w  (a0),d0
        beq     .invalid
        cmpi.w  #9,d0
        bhi     .invalid
        cmpi.w  #2,d0
        bne.s   .validated
        cmpi.w  #1,6(a0)
        bhi     .invalid
.validated:
        addq.l  #1,game_history_replay_low
        dbra    d5,.validate
.restore:
        move.l  game_history_selected,a1
        adda.w  #12,a1
        lea     game_core_state,a0
        bsr     game_history_copy_state
        move.l  game_history_origin+4,game_history_replay_low
        st      game_history_replaying
.loop:
        tst.w   game_history_replay_count
        beq.s   .success
        bsr     game_history_record_address
        moveq   #0,d6
        move.w  (a0)+,d6
        subq.w  #1,d6
        lsl.w   #2,d6
        lea     game_history_operations,a1
        move.l  (a1,d6.w),a1
        move.w  (a0)+,d0
        move.w  (a0)+,d1
        move.w  (a0)+,d2
        move.w  (a0)+,d3
        move.w  (a0)+,d4
        move.w  (a0)+,d5
        jsr     (a1)
        addq.l  #1,game_history_replay_low
        subq.w  #1,game_history_replay_count
        bra.s   .loop
.success:
        clr.b   game_history_replaying
        moveq   #1,d0
        rts
.invalid:
        moveq   #0,d0
        rts

; Validate canonical table IDs/offsets before any restoration. Records are
; internal to this exact executable; persistent cross-build files are absent.
game_history_validate_state:
        cmpi.b  #1,game_entropy_policy-game_core_state(a1)
        bhi     .invalid
        lea     game_audio_voices-game_core_state(a1),a2
        moveq   #2,d6
.voice:
        move.l  AV_NEXT(a2),d0
        bne.s   .clip
        cmpi.b  #$ff,AV_CLIP(a2)
        beq.s   .next
        moveq   #0,d1
        moveq   #7,d2
        move.l  a2,a3
.zero:  or.l    (a3)+,d1
        dbra    d2,.zero
        tst.l   d1
        beq.s   .next
.clip:
        moveq   #0,d1
        move.b  AV_CLIP(a2),d1
        cmpi.w  #7,d1
        bcc.s   .invalid
        lsl.w   #3,d1
        lea     game_history_clip_bounds,a3
        adda.w  d1,a3
        cmp.l   (a3),d0
        bcs.s   .invalid
        cmp.l   4(a3),d0
        bhi.s   .invalid
        bne.s   .alignment
        tst.b   AV_DONE(a2)
        beq.s   .invalid
.alignment:
        sub.l   (a3),d0
        andi.w  #15,d0
        bne.s   .invalid
.next:
        adda.w  #AV_SIZE,a2
        dbra    d6,.voice
        moveq   #1,d0
        rts
.invalid:
        moveq   #0,d0
        rts

game_history_clip_bounds:
        dc.l native_audio_score_0-native_audio_scores,native_audio_score_1-native_audio_scores
        dc.l native_audio_score_1-native_audio_scores,native_audio_score_4-native_audio_scores
        dc.l native_victory_melody-native_audio_scores,native_victory_bass-native_audio_scores
        dc.l native_victory_bass-native_audio_scores,native_victory_arpeggio-native_audio_scores
        dc.l native_audio_score_4-native_audio_scores,native_audio_score_5-native_audio_scores
        dc.l native_audio_score_5-native_audio_scores,native_audio_periods-native_audio_scores
        dc.l native_victory_arpeggio-native_audio_scores,native_victory_periods-native_audio_scores
game_history_clip_bounds_end:

game_history_record_address:
        move.l  game_history_replay_low,d0
        andi.w  #HISTORY_RECORDS-1,d0
        mulu.w  #HISTORY_RECORD_BYTES,d0
        move.l  game_history_store,a0
        adda.l  d0,a0
        rts

game_history_operations:
        dc.l game_core_init,game_core_select,game_core_sample_pads
        dc.l game_core_sample_result,game_core_clear_inputs,game_core_return_title
        dc.l game_round_poll,game_tick_dispatch,game_core_latch_actions

 ; Contact episode starts only after the actual receiver/contact mask gates.
; Repeated geometry probes share one index. A successful return upgrades that
; episode to kind1; point/lifecycle termination upgrades it to kind2 (miss).
; Kind0 is still incoming; not a completed shot/attempt for future navigation.
game_history_contact_begin:
        move.w  sr,-(sp)
        movem.l d0-d7/a0-a6,-(sp)
        cmpi.b  #1,game_history_mode
        bne.s   .done
        cmpi.w  #8,game_history_operation
        bne.s   .done
        tst.b   G_LOWER_AI(a4,d7.w)
        bne.s   .done
        tst.b   game_history_probe_active
        bne.s   .done
        move.w  d7,d5
        moveq   #0,d6
        move.w  game_history_attempt_next,game_history_probe_index
        bsr     game_history_add_index
        st      game_history_probe_active
.done:
        movem.l (sp)+,d0-d7/a0-a6
        move.w  (sp)+,sr
        rts

game_history_contact:
        move.w  sr,-(sp)
        movem.l d0-d7/a0-a6,-(sp)
        cmpi.b  #1,game_history_mode
        bne.s   .done
        tst.b   G_LOWER_AI(a4,d7.w)
        bne.s   .done
        tst.b   game_history_probe_active
        beq.s   .done
        moveq   #0,d0
        move.w  game_history_probe_index,d0
        bsr     game_history_attempt_address
        move.w  #1,8(a0)
        clr.b   game_history_probe_active
.done:
        movem.l (sp)+,d0-d7/a0-a6
        move.w  (sp)+,sr
        rts

; Actual completed human serve launch, kind3. Preserve the rules' registers.
game_history_serve:
        move.w  sr,-(sp)
        movem.l d0-d7/a0-a6,-(sp)
        cmpi.b  #1,game_history_mode
        bne.s   .done
        tst.b   G_LOWER_AI(a4,d7.w)
        bne.s   .done
        move.w  d7,d5
        moveq   #3,d6
        bsr     game_history_add_index
.done:
        movem.l (sp)+,d0-d7/a0-a6
        move.w  (sp)+,sr
        rts

game_history_add_index:
        moveq   #0,d0
        move.w  game_history_attempt_next,d0
        bsr     game_history_attempt_address
        move.l  game_history_cursor,(a0)+
        move.l  game_history_cursor+4,(a0)+
        move.w  d6,(a0)+
        move.w  d5,(a0)+
        addq.w  #1,game_history_attempt_next
        andi.w  #HISTORY_ATTEMPTS-1,game_history_attempt_next
        cmpi.w  #HISTORY_ATTEMPTS,game_history_attempt_count
        beq.s   .full
        addq.w  #1,game_history_attempt_count
        rts
.full:
        move.w  game_history_attempt_next,game_history_attempt_first
        rts

game_history_attempt_address:
        mulu.w  #HISTORY_ATTEMPT_BYTES,d0
        move.l  game_history_store,a0
        adda.l  #HISTORY_ATTEMPT_OFFSET,a0
        adda.l  d0,a0
        rts

        even
game_history_state:
game_history_store: dc.l 0
game_history_mode: dc.b 0
        even
game_history_operation: dc.w 0
game_history_cursor: dc.l 0,0
game_history_oldest: dc.l 0,0
game_history_checkpoint_next: dc.w 0
game_history_checkpoint_count: dc.w 0
game_history_attempt_next: dc.w 0
game_history_attempt_first: dc.w 0
game_history_attempt_count: dc.w 0
game_history_target: dc.l 0,0
game_history_origin: dc.l 0,0
game_history_selected: dc.l 0
game_history_replay_low: dc.l 0
game_history_replay_count: dc.w 0
game_history_probe_index: dc.w 0
game_history_probe_active: dc.b 0
game_history_replaying: dc.b 0
        even
game_history_state_end:
