; Continuous replay: RAM is initialized once and carried across all callbacks.
        section code,code
        include "build/translation/player-frame-symbols.i"
        include "amiga/translated_z80_macros.i"
start:
        lea     virtual_memory,a6
        lea     virtual_memory+$c000,a5
        lea     initial_ram,a0
        move.l  a5,a1
        move.w  #255,d7
copy_initial:
        move.b  (a0)+,(a1)+
        dbra    d7,copy_initial
        clr.w   update_index
        bsr     run_tail
        move.l  a5,a0
        move.w  #256,d0
        bsr     emit_hex
        lea     psg_log,a0
        moveq   #0,d0
        move.b  psg_count,d0
        bsr     emit_hex
next_update:
        moveq   #0,d0
        move.w  update_index,d0
        lea     inputs,a0
        move.b  (a0,d0.w),case_game_bits
        clr.b   write_count
        move.l  #write_log,write_ptr
        bsr     scoreboard_update
        bsr     input_update
        bsr     score_gate
        bsr     lower_player_state
        bsr     upper_player_state
        bsr     ball_flight_update
        bsr     player_movement_and_sprites
        move.l  a5,a0
        move.w  #256,d0
        bsr     emit_hex
        bsr     run_tail
        move.l  a5,a0
        move.w  #256,d0
        bsr     emit_hex
        lea     psg_log,a0
        moveq   #0,d0
        move.b  psg_count,d0
        bsr     emit_hex
        addq.w  #1,update_index
        cmpi.w  #200,update_index
        bne     next_update
        moveq   #0,d0
        rts
run_tail:
        bsr     irq_counter_prefix
        clr.b   psg_count
        move.l  #psg_log,psg_ptr
        bsr     audio_tick_adapter
        clr.b   vdp_count
        move.l  #vdp_log,vdp_ptr
        bsr     irq_vdp_tail
        rts
; Copperline debug call emits one bounded hexadecimal record, including empty PSG.
emit_hex:
        movem.l d0-d7/a0-a6,-(sp)
        lea     output_text+4,a1
        lea     hex_digits,a2
        move.w  d0,d7
        beq.s   emit_done
        subq.w  #1,d7
emit_byte:
        moveq   #0,d1
        move.b  (a0)+,d1
        move.w  d1,d2
        lsr.w   #4,d2
        move.b  (a2,d2.w),(a1)+
        andi.w  #15,d1
        move.b  (a2,d1.w),(a1)+
        dbra    d7,emit_byte
emit_done:
        clr.b   (a1)
        move.l  #output_text,-(sp)
        move.l  #86,-(sp)
        jsr     $f0ff60
        addq.l  #8,sp
        movem.l (sp)+,d0-d7/a0-a6
        rts
        include "amiga/tests/probe_io.i"
        include "amiga/translated_audio_tick.s"
        ifd REGRESSION_MUTATION
        include "build/tests/mutated-routines.s"
        else
        include "build/translation/player-frame-routines.s"
        endif
        even
update_index: dc.w 0
case_game_bits: dc.b 0
case_keyboard_bits: dc.b 0
write_count: dc.b 0
vdp_count: dc.b 0
        even
write_ptr: dc.l 0
vdp_ptr: dc.l 0
write_log: dcb.b 192,0
vdp_log: dcb.b 4,0
hex_digits: dc.b "0123456789ABCDEF"
output_text: dc.b "REG "
        dcb.b 513,0
        even
virtual_memory:
        incbin "build/translation/player-frame-memory.bin"
initial_ram:
        incbin "build/tests/initial-ram.bin"
inputs:
        incbin "build/tests/inputs.bin"
