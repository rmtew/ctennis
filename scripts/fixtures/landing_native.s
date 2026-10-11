; Test-only benchmark inserted after native input polling. It runs isolated
; intrinsic ball jobs on separate state buffers; it is not a production schedule.
        section code,code
landing_native_hook:
        move.w  sr,-(sp)
        movem.l d0-d7/a0-a6,-(sp)
        moveq   #0,d0
        move.w  landing_native_completed,d0
        cmpi.w  #LANDING_NATIVE_TOTAL,d0
        bcc     landing_native_return
        lsr.w   #3,d0
        mulu.w  #320,d0
        lea     landing_native_inputs,a0
        adda.l  d0,a0
        lea     landing_native_reference_state,a1
        lea     landing_native_query_state,a2
        move.w  #158,d3
landing_native_copy:
        move.w  (a0)+,d0
        move.w  d0,(a1)+
        move.w  d0,(a2)+
        dbra    d3,landing_native_copy
        moveq   #0,d0
        move.w  (a0),d0
        move.w  d0,landing_native_reference_steps
landing_native_before:
        lea     landing_native_reference_state,a5
        jsr     landing_reference
        lea     landing_native_query_state,a5
        jsr     landing_query
        movem.l d0-d3,landing_native_results
        addq.w  #1,landing_native_completed
landing_native_after:
landing_native_return:
        movem.l (sp)+,d0-d7/a0-a6
        move.w  (sp)+,sr
        rts

; Independently measured actual ball scan. Its finite phase count is obtained
; from an uninterrupted CPU reference before building this diagnostic fixture.
; No intermediate state is supplied. The native endpoint must match both query
; and CPU endpoint in the observer, not a counter alone.
landing_reference:
        movem.l d7/a4,-(sp)
        lea     game_play_state-game_core_state(a5),a4
        move.w  landing_native_reference_steps,d7
        subq.w  #1,d7
landing_reference_loop:
        jsr     game_ball_tick
        dbra    d7,landing_reference_loop
        movem.l (sp)+,d7/a4
        rts

        include "scripts/fixtures/guarded_landing.s"
        include "build/tests/guarded-landing-native-inputs.i"

        section landing_native_storage,bss
landing_native_completed: ds.w 1
landing_native_reference_steps: ds.w 1
landing_native_results: ds.l 4
landing_native_left_canary: ds.l 1
landing_native_reference_state: ds.b 318
landing_native_middle_canary: ds.l 1
landing_native_query_state: ds.b 318
landing_native_right_canary: ds.l 1
landing_native_storage_end:
