# Committed PR19 integration comparison

Historical pre-PR19 release versus current merged product. Both executables omit symbol records. Font, sprite, music and cache changes are included; this is not an isolated stripping experiment.

| Bytes | Before | Current | Delta |
| --- | ---: | ---: | ---: |
| executable bytes | 198,960 | 248,480 | +49,520 |
| code bytes | 40,140 | 49,564 | +9,424 |
| data bytes | 114,540 | 152,540 | +38,000 |
| bss bytes | 0 | 0 | +0 |
| loaded payload bytes | 154,680 | 202,104 | +47,424 |
| release executable bytes | 163,876 | 211,920 | +48,044 |

| Cold milestone (emulated seconds) | Before | Current | Delta |
| --- | ---: | ---: | ---: |
| reset | 0.000000 | 0.000000 | 0.000000 |
| boot_script_begins | unavailable | unavailable | unavailable |
| loadseg_begin | unavailable | unavailable | unavailable |
| loadseg_complete | 20.582720 | 24.786221 | 4.203501 |
| executable_entry | 20.583725 | 24.787227 | 4.203502 |
| assets_ready | 20.595379 | 24.799342 | 4.203963 |
| first_complete_title_frame | 20.636332 | 24.841747 | 4.205415 |
| input_responsive | 20.665747 | 24.869748 | 4.204002 |

Actual emulated time. Added Mac font/classic robot/Battle Hymn/UI caches change the product; these differences are not isolated symbol-stripping savings. OS boot/loader remain combined; read/relocation subphases, disk counters and host launch time remain unavailable.

Not subtracted: integration adopts complete-longword allocation observation; historical peak boundary is not equivalent. Current peak is measured independently.
Not subtracted across old result/celebration split. Both bound reports retain their actual extents; current celebration is newly measured.

Runtime cold chip usage changes by +47,424 B. Current per-profile update/render p95/max and deadline headroom, including celebration, are in current.md. Exact report/product/ADF hashes and CCK differences are in the companion JSON.
