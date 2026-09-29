        section code,code
start:
        lea     expected(pc),a4
        moveq   #0,d3
next_seed:
        move.b  d3,prng_seed
        bsr     prng_step
        cmp.b   (a4)+,d0
        bne.s   failed
        cmp.b   prng_seed,d0
        bne.s   failed
        addq.w  #1,d3
        cmpi.w  #256,d3
        bne.s   next_seed
        moveq   #0,d0
        rts
failed:
        moveq   #1,d0
        rts

        include "build/translation/prng-routine.s"
expected:
        incbin  "build/translation/prng-expected.bin"

        section game_ram,data
state_ram:
        ds.b    256
prng_seed equ state_ram+$72
