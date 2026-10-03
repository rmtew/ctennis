; Negative control: exact measurement routine from merged PR27 (16679feb).
measure_presentation_field:
        bsr     read_presentation_line
        move.w  d0,d3
.wait_wrap:
        bsr     read_presentation_line
        cmp.w   d3,d0
        bcs.s   .start_field
        move.w  d0,d3
        bra.s   .wait_wrap
.start_field:
        move.w  d0,d3
.next_line:
        bsr     read_presentation_line
        cmp.w   d3,d0
        bcs.s   .measured
        move.w  d0,d3
        bra.s   .next_line
.measured:
        move.w  d3,presentation_last_line
        subq.w  #4,d3
        move.w  d3,presentation_last_safe_line
        rts

