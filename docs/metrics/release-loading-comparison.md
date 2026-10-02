# Release loading comparison

Historical symbol-rich before versus fresh stripped-release after, on the same pinned unexpanded PAL A500 configuration and cold read-only ADF at 100% disk speed. All figures are emulated seconds, not host wallclock.

| Milestone | Before (s) | After (s) | After − before (s) |
| --- | ---: | ---: | ---: |
| reset | 0.000000 | 0.000000 | 0.000000 |
| boot_script_begins | unavailable | unavailable | unavailable |
| loadseg_begin | unavailable | unavailable | unavailable |
| loadseg_complete | 24.738865 | 20.582720 | -4.156145 |
| executable_entry | 24.740379 | 20.583725 | -4.156654 |
| assets_ready | 24.752147 | 20.595379 | -4.156768 |
| first_complete_title_frame | 24.786953 | 20.636332 | -4.150621 |
| input_responsive | 24.789238 | 20.665747 | -4.123492 |

File size: **198,960 → 163,876 bytes**, saving **35,084 bytes (17.6%)**. Loaded payload remains 154,680 bytes. Runtime chip usage/free/largest block and initialized-pool cold peak have **zero measured difference**. No pre-Exec RAM claim is made.

Actual emulated CCK, not host wallclock. Historical title point was independently reprocessed under continuous title selection. After run waits for that proof before physical mode input; title/input/total comparisons include this harness timing change. Reset-to-LoadSeg is prior to input and supports the loading comparison; OS boot and loader remain combined because LoadSeg begin is unavailable. No isolated read/relocation cost or disk counts are claimed.

Before executable: `e81fe61be19e28cb585f4c0f5808ebc96aa038d77a5f6667780e14f79f30f46c`.
After executable: `ead8265319cf5a55a2a6bb1c9a1f9dfc8349f70e7e89af7be5d6bc8ac0b929e5`.
Before ADF: `ffc168c34df52d0f4294718edd61cec3b603c3136f15d447e18b817a8530ed02`.
After ADF: `6d0eccf31da8dc591b3332882783538cc2ab35906c6f268fce84281edc9ad94c`.

Exact report/receipt/config/tool hashes and CCK differences are in the adjacent JSON. The ordinary metrics generator produces the current source report; this comparison is a bounded review snapshot against the preserved historical baseline. No significance estimate or optimization beyond symbol removal is inferred.
