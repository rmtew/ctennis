        section code,code
SCORE_COPPER_PROBE equ 1

start:
        lea     pointer_sources(pc),a0
        lea     pointer_targets(pc),a1
        moveq   #11,d7
patch_display_pointers:
        move.l  (a0)+,d0
        move.l  (a1)+,a2
        move.l  d0,d1
        swap    d1
        move.w  d1,(a2)
        move.w  d0,4(a2)
        dbra    d7,patch_display_pointers

        bsr     patch_score_pointers
        lea     $dff000,a6
        move.w  #$7fff,$09a(a6)
        move.w  #$7fff,$096(a6)
        move.l  #copperlist,$080(a6)
        move.w  #0,$088(a6)
        move.w  #$83a0,$096(a6)

wait_frame:
        move.w  $006(a6),d0
        andi.w  #$ff00,d0
        cmpi.w  #$f000,d0
        bne.s   wait_frame
        moveq   #0,d0
        move.b  $bfe001,d1
        btst    #7,d1
        bne.s   state_ready
        moveq   #1,d0
state_ready:
        cmp.b   selected_state,d0
        beq.s   wait_frame_end
        move.b  d0,selected_state
        tst.b   d0
        beq.s   choose_original
        lea     alternate_fields(pc),a0
        bra.s   copy_field_values
choose_original:
        lea     original_fields(pc),a0
copy_field_values:
        lea     field_values(pc),a1
        moveq   #5,d7
copy_next_field:
        move.b  (a0)+,(a1)+
        dbra    d7,copy_next_field
        bsr     patch_score_pointers
wait_frame_end:
        move.w  $006(a6),d0
        andi.w  #$ff00,d0
        cmpi.w  #$f000,d0
        beq.s   wait_frame_end
        bra.s   wait_frame

; Each descriptor holds two Copper value-word addresses, a table of native
; bitplane-bank addresses, and the game field selecting that table entry.
patch_score_pointers:
        lea     score_patch_descriptors(pc),a0
        lea     field_values(pc),a4
        move.w  #SCORE_PATCH_COUNT-1,d7
patch_next_score_pointer:
        move.l  (a0)+,a1
        move.l  (a0)+,a2
        move.l  (a0)+,a3
        move.w  (a0)+,d1
        cmpi.w  #$ffff,d1
        beq.s   use_fixed_pointer
        moveq   #0,d2
        move.b  0(a4,d1.w),d2
        lsl.w   #2,d2
        move.l  0(a3,d2.w),d0
        bra.s   write_score_pointer
use_fixed_pointer:
        move.l  (a3),d0
write_score_pointer:
        move.l  d0,d1
        swap    d1
        move.w  d1,(a1)
        move.w  d0,(a2)
        dbra    d7,patch_next_score_pointer
        rts

        even
selected_state:  dc.b 0
field_values:    dc.b 0,0,0,0,0,1
original_fields: dc.b 0,0,0,0,0,1
alternate_fields: dc.b 1,2,1,2,1,2
        even
pointer_sources:
        dc.l plane0,plane1,plane2,plane3
        dc.l sprite0,sprite1,sprite2,sprite3,sprite4,sprite5,sprite6,sprite7
pointer_targets:
        dc.l cop_bpl0h+2,cop_bpl1h+2,cop_bpl2h+2,cop_bpl3h+2
        dc.l cop_spr0h+2,cop_spr1h+2,cop_spr2h+2,cop_spr3h+2
        dc.l cop_spr4h+2,cop_spr5h+2,cop_spr6h+2,cop_spr7h+2
        include "build/amiga/score-copper-probe/score-patch-tables.i"

        include "amiga/sprite_probe_display.i"
        even
        include "build/amiga/score-copper-probe/score-bank-data.i"
