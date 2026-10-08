; Fixture-only synchronous observation. No instructions emitted without CORE_TRACE.
        ifd CORE_TRACE
core_trace_sink macro
        move.w  sr,-(sp)
        move.w  d7,core_trace_arguments
        move.w  d0,core_trace_arguments+2
        move.w  #\1,core_trace_marker
        move.w  (sp)+,sr
        endm
        else
core_trace_sink macro
        endm
        endif
