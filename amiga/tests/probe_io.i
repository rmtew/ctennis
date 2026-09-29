; Shared source-interface test adapters; display writes are recorded only.
read_game_input:
        move.b  case_game_bits,d0
        rts
sample_second_input_group:
        move.b  case_keyboard_bits,d0
        rts
upload_sprite_attributes:
        rts
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
record_vdp_byte:
        move.l  vdp_ptr,a1
        move.b  d0,(a1)+
        move.l  a1,vdp_ptr
        addq.b  #1,vdp_count
        rts
