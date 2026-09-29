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
        bne.s   failed
        dbra    d7,compare_ram
        moveq   #0,d7
        move.b  (a4)+,d7
        cmp.b   write_count,d7
        bne.s   failed
        tst.w   d7
        beq.s   writes_done
        subq.w  #1,d7
        lea     write_log,a1
compare_writes:
        move.b  (a4)+,d0
        cmp.b   (a1)+,d0
        bne.s   failed
        move.b  (a4)+,d0
        cmp.b   (a1)+,d0
        bne.s   failed
        move.b  (a4)+,d0
        cmp.b   (a1)+,d0
        bne.s   failed
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
        addq.w  #1,case_index
        cmpi.w  #240,case_index
        bne     next_case
        moveq   #0,d0
        rts
failed:
        move.w  case_index,d0
        addq.w  #1,d0
        rts
read_game_input:
        move.b  case_game_bits,d0
        rts
sample_second_input_group:
        move.b  case_keyboard_bits,d0
        rts
upload_sprite_attributes:
        rts
GET_ADDRESS: MACRO
        lea     virtual_memory+\1,\2
        ENDM
LOAD_HL: MACRO
        move.w  #\1,d6
        move.b  #(\1)>>8,d5
        ENDM
LOAD_DE: MACRO
        move.w  #\1,d4
        move.b  #(\1)>>8,d3
        ENDM
LOAD_BC: MACRO
        move.w  #\1,d2
        move.b  #(\1)>>8,d1
        ENDM
MOVE_W_TO_REG: MACRO
        moveq   #0,d7
        move.b  1(\1),d7
        lsl.w   #8,d7
        move.b  (\1),d7
        move.w  d7,\2
        ENDM
MOVE_W_FROM_REG: MACRO
        move.b  \1,(\2)
        move.w  \1,d7
        lsr.w   #8,d7
        move.b  d7,1(\2)
        ENDM
MAKE_HL_NO_AR: MACRO
        moveq   #0,d7
        move.b  d5,d7
        lsl.w   #8,d7
        move.b  d6,d7
        move.w  d7,d6
        ENDM
MAKE_H: MACRO
        move.w  d6,d7
        lsr.w   #8,d7
        move.b  d7,d5
        andi.w  #$00ff,d6
        ENDM
MAKE_BC_NO_AR: MACRO
        moveq   #0,d7
        move.b  d1,d7
        lsl.w   #8,d7
        move.b  d2,d7
        move.w  d7,d2
        ENDM
MAKE_B: MACRO
        move.w  d2,d7
        lsr.w   #8,d7
        move.b  d7,d1
        andi.w  #$00ff,d2
        ENDM
MAKE_DE_NO_AR: MACRO
        moveq   #0,d7
        move.b  d3,d7
        lsl.w   #8,d7
        move.b  d4,d7
        move.w  d7,d4
        ENDM
MAKE_D: MACRO
        move.w  d4,d7
        lsr.w   #8,d7
        move.b  d7,d3
        andi.w  #$00ff,d4
        ENDM
MAKE_AR_FROM_HL: MACRO
        MAKE_HL_NO_AR
        lea     virtual_memory,\1
        moveq   #0,d7
        move.w  d6,d7
        adda.l  d7,\1
        ENDM
MAKE_AR_FROM_DE: MACRO
        MAKE_DE_NO_AR
        lea     virtual_memory,\1
        moveq   #0,d7
        move.w  d4,d7
        adda.l  d7,\1
        ENDM
MAKE_HL: MACRO
        MAKE_HL_NO_AR
        lea     virtual_memory,\1
        moveq   #0,d7
        move.w  d6,d7
        adda.l  d7,\1
        ENDM
MAKE_DE: MACRO
        MAKE_DE_NO_AR
        lea     virtual_memory,\1
        moveq   #0,d7
        move.w  d4,d7
        adda.l  d7,\1
        ENDM
PUSH_SR: MACRO
        move.w  sr,-(sp)
        ENDM
POP_SR: MACRO
        move.w  (sp)+,ccr
        ENDM
READ_Z80_REFRESH: MACRO
        clr.b   d0
        ENDM
CLR_XC_FLAGS: MACRO
        andi.b  #$ee,ccr
        ENDM
SET_XC_FLAGS: MACRO
        ori.b   #$11,ccr
        ENDM
INVERT_XC_FLAGS: MACRO
        eori.b  #$01,ccr
        SET_X_FROM_C
        ENDM
SET_X_FROM_C: MACRO
        move.w  sr,-(sp)
        move.w  (sp),d7
        bset    #4,d7
        btst    #0,d7
        bne.s   carry_set\@
        bclr    #4,d7
carry_set\@:
        move.w  d7,(sp)
        move.w  (sp)+,ccr
        ENDM

copy_cpu_bytes_to_vram_b_count:
        MAKE_HL_NO_AR
        MAKE_DE_NO_AR
        tst.b   d1
        beq.s   copy_vram_done
copy_vram_byte:
        lea     virtual_memory,a0
        moveq   #0,d0
        move.w  d6,d0
        adda.l  d0,a0
        move.b  (a0),d0
        bsr     log_vram_write
        addq.w  #1,d6
        addq.w  #1,d4
        subq.b  #1,d1
        bne.s   copy_vram_byte
copy_vram_done:
        MAKE_H
        MAKE_D
        clr.b   d0
        rts
l_0008:
        movem.l d4/d6-d7,-(sp)
        MAKE_HL_NO_AR
        move.w  d6,d4
        bsr     log_vram_write
        movem.l (sp)+,d4/d6-d7
        rts
log_vram_write:
        move.l  write_ptr,a1
        move.w  d4,d7
        lsr.w   #8,d7
        move.b  d7,(a1)+
        move.b  d4,(a1)+
        move.b  d0,(a1)+
        move.l  a1,write_ptr
        addq.b  #1,write_count
        rts
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
virtual_memory:
        incbin  "build/translation/player-frame-memory.bin"
cases:
        incbin  "build/translation/player-frame-cases.bin"
