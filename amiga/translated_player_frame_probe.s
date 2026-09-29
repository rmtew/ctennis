        section code,code
point_outcome_flags equ $c039
mode_status_flags equ $c03d
lower_player_y equ $c049
upper_player_y equ $c045
irq_tick_counter equ $c06b
input_direction_a equ $c053
lower_movement_bounds equ $144d
upper_movement_bounds equ $147c
animation_records equ $14fa
player_sprite_descriptors equ $115a

start:
        lea     virtual_memory,a6
        lea     virtual_memory+$c000,a5
        lea     cases,a4
        clr.w   case_index
next_case:
        move.l  a5,a1
        move.w  #255,d7
copy_ram:
        move.b  (a4)+,d0
        move.b  d0,(a1)+
        dbra    d7,copy_ram
        bsr     lower_player_motion_update
        bsr     upper_player_movement
        bsr     animate_lower_player
        bsr     animate_upper_player
        bsr     build_player_sprites
        move.l  a5,a1
        move.w  #255,d7
compare_ram:
        move.b  (a4)+,d0
        cmp.b   (a1)+,d0
        bne.s   failed
        dbra    d7,compare_ram
        addq.w  #1,case_index
        cmpi.w  #40,case_index
        bne.s   next_case
        moveq   #0,d0
        rts
failed:
        move.w  case_index,d0
        addq.w  #1,d0
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

        include "build/translation/player-frame-routines.s"
        even
case_index:
        dc.w    0
virtual_memory:
        incbin  "build/translation/player-frame-memory.bin"
cases:
        incbin  "build/translation/player-frame-cases.bin"