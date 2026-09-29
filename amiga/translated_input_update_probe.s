        section code,code
mode_status_flags equ $c03d
input_direction_a equ $c053
input_direction_b equ $c056

start:
        lea     cases,a4
        clr.w   case_index
next_case:
        move.b  (a4)+,mode_status_flags_ram
        move.b  (a4)+,case_game_bits
        move.b  (a4)+,case_keyboard_bits
        bsr     input_update
        move.b  (a4)+,d7
        cmp.b   input_direction_a_ram,d7
        bne.s   failed
        move.b  (a4)+,d7
        cmp.b   input_direction_b_ram,d7
        bne.s   failed
        addq.w  #1,case_index
        cmpi.w  #16896,case_index
        bne.s   next_case
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

GET_ADDRESS: MACRO
        lea     \1_ram,\2
        ENDM
CLR_XC_FLAGS: MACRO
        andi.b  #$ee,ccr
        ENDM

        include "build/translation/input-update-routine.s"
mode_status_flags_ram:
        dc.b    0
input_direction_a_ram:
        dc.b    0
input_direction_b_ram:
        dc.b    0
case_game_bits:
        dc.b    0
case_keyboard_bits:
        dc.b    0
        even
case_index:
        dc.w    0
cases:
        incbin  "build/translation/input-update-cases.bin"
