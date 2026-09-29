        section code,code
        include "build/translation/player-frame-symbols.i"

start:
        lea     virtual_memory,a6
        lea     virtual_memory+$c000,a5
        lea     cases,a4
        clr.w   case_index
next_case:
        move.b  (a4)+,case_game_bits
        move.b  (a4)+,case_keyboard_bits
        move.l  a5,a1
        move.w  #255,d7
copy_ram:
        move.b  (a4)+,d0
        move.b  d0,(a1)+
        dbra    d7,copy_ram
        clr.b   write_count
        move.l  #write_log,write_ptr
        bsr     scoreboard_update
        bsr     input_update
        bsr     score_gate
        bsr     lower_player_state
        bsr     upper_player_state
        bsr     ball_flight_update
        bsr     player_movement_and_sprites
        move.l  a5,a1
        move.w  #255,d7
compare_ram:
        move.b  (a4)+,d0
        cmp.b   (a1)+,d0
        bne     failed
        dbra    d7,compare_ram
        moveq   #0,d7
        move.b  (a4)+,d7
        cmp.b   write_count,d7
        bne     failed
        tst.w   d7
        beq.s   writes_done
        subq.w  #1,d7
        lea     write_log,a1
compare_writes:
        move.b  (a4)+,d0
        cmp.b   (a1)+,d0
        bne     failed
        move.b  (a4)+,d0
        cmp.b   (a1)+,d0
        bne     failed
        move.b  (a4)+,d0
        cmp.b   (a1)+,d0
        bne     failed
        dbra    d7,compare_writes
writes_done:
        bsr     irq_counter_prefix
        lea     $6b(a5),a1
        move.w  #6,d7
compare_irq_counters:
        move.b  (a4)+,d0
        cmp.b   (a1)+,d0
        bne     failed
        dbra    d7,compare_irq_counters
        move.b  (a4)+,d0
        cmp.b   $83(a5),d0
        bne     failed
        clr.b   psg_count
        move.l  #psg_log,psg_ptr
        bsr     audio_tick_adapter
        clr.b   vdp_count
        move.l  #vdp_log,vdp_ptr
        bsr     irq_vdp_tail
        move.l  a5,a1
        move.w  #255,d7
compare_post_audio_ram:
        move.b  (a4)+,d0
        cmp.b   (a1)+,d0
        bne     failed
        dbra    d7,compare_post_audio_ram
        moveq   #0,d7
        move.b  (a4)+,d7
        cmp.b   psg_count,d7
        bne     failed
        tst.w   d7
        beq.s   psg_done
        subq.w  #1,d7
        lea     psg_log,a1
compare_psg:
        move.b  (a4)+,d0
        cmp.b   (a1)+,d0
        bne     failed
        dbra    d7,compare_psg
psg_done:
        moveq   #0,d7
        move.b  (a4)+,d7
        cmp.b   vdp_count,d7
        bne     failed
        tst.w   d7
        beq.s   vdp_done
        subq.w  #1,d7
        lea     vdp_log,a1
compare_vdp:
        move.b  (a4)+,d0
        cmp.b   (a1)+,d0
        bne     failed
        dbra    d7,compare_vdp
vdp_done:
        addq.w  #1,case_index
        cmpi.w  #244,case_index
        bne     next_case
        moveq   #0,d0
        rts
failed:
        move.w  case_index,d0
        addq.w  #1,d0
        rts
        include "amiga/translated_z80_macros.i"
        include "amiga/tests/probe_io.i"
        include "amiga/translated_audio_tick.s"
        include "build/translation/player-frame-routines.s"
        even
case_index:
        dc.w    0
case_game_bits:
        dc.b    0
case_keyboard_bits:
        dc.b    0
write_count:
        dc.b    0
        even
write_ptr:
        dc.l    0
write_log:
        dcb.b   192,0
vdp_count:
        dc.b    0
        even
vdp_ptr:
        dc.l    0
vdp_log:
        dcb.b   4,0
virtual_memory:
        incbin  "build/translation/player-frame-memory.bin"
cases:
        incbin  "build/translation/player-frame-cases.bin"
