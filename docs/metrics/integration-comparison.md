# Frozen title and square-score integration comparison

Historical pre-title/score release versus current frozen product. Both executables omit symbol records. The selected title design and startup-generated square-score banks are included.

| Bytes | Before | Current | Delta |
| --- | ---: | ---: | ---: |
| executable bytes | 248,480 | 235,180 | -13,300 |
| code bytes | 49,564 | 49,932 | +368 |
| data bytes | 152,540 | 137,980 | -14,560 |
| bss bytes | 0 | 14,336 | +14,336 |
| loaded payload bytes | 202,104 | 202,248 | +144 |
| release executable bytes | 211,920 | 197,812 | -14,108 |

| Cold milestone (emulated seconds) | Before | Current | Delta |
| --- | ---: | ---: | ---: |
| reset | 0.000000 | 0.000000 | 0.000000 |
| boot_script_begins | unavailable | unavailable | unavailable |
| loadseg_begin | unavailable | unavailable | unavailable |
| loadseg_complete | 24.786221 | 23.392447 | -1.393773 |
| executable_entry | 24.787227 | 23.393450 | -1.393777 |
| assets_ready | 24.799342 | 23.426694 | -1.372648 |
| first_complete_title_frame | 24.841747 | 23.486006 | -1.355740 |
| input_responsive | 24.869748 | 23.513730 | -1.356018 |

Actual emulated time. Title design and startup-generated square-score banks change the product; these differences are not isolated symbol-stripping savings. OS boot/loader remain combined; read/relocation subphases, disk counters and host launch time remain unavailable.

Both snapshots use the same complete-longword allocation observer; measured initialized-pool peaks are retained independently.
Same observer definitions; current.json carries compatible per-profile deltas and the actual measured extents.

Runtime cold chip usage changes by +152 B. Current per-profile update/render p95/max and deadline headroom, including celebration, are in current.md. Exact report/product/ADF hashes and CCK differences are in the companion JSON.
