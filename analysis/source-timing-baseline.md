# Source gameplay timing baseline

`python scripts/source_timing_baseline.py` runs two identical MAME captures, checks their event order and values, and writes `build/reference/source-timing/report.json`. The raw TSV files and report are local generated evidence and are ignored by Git. `--verify-only` checks existing captures. The capture uses [capture_source_timing.lua](../scripts/capture_source_timing.lua); no private cartridge bytes are embedded in either script.

The machine is MAME 0.289 `sc3000`, with its reported display refresh of 59.922738 Hz (16.688156 ms per video interval). The executable SHA-256 is `af6966108d9b52c22465c6d50f4e5d50cc371b50f2d27dc443935f287aad37a3`; the 8 KB G-1009 cartridge SHA-256 is `19bb6647f14ef50f976e8d0a06d389f06b2e700d54a54fb1734d3140f9745ad1`. The runner checks that the MAME cartridge archive contains exactly the configured cartridge. It uses `-noreadconfig`, `-video none`, `-sound none`, `-nothrottle`, and a 23-second emulated run.

The SC-3000 Del/Ins key selects one-player mode after frame callback 120 and is released after callback 420. Controller left is requested after frame callback 1300 and released after callback 1320. The Lua frame callback labels the **following emulation interval**; thus interval 1300 already sees left held, and interval 1320 sees it released. The checked interval labels are 1280–1339, after the callback pointer at `$C000-$C001` has become `$0699`.

Each of those 60 consecutive video intervals contains exactly one gameplay checkpoint at the write to `$C06B` (post-write PC `$06B5`), giving 60 gameplay updates in 60 intervals: **59.922738 updates/s in this bounded run**. The checkpoint occurs after gameplay and movement but before the remaining counter/audio/VDP tail. Its 1 KB RAM snapshot is taken by the tap before the `$C06B` write; the event separately records the new counter value. It is not a final end-of-interrupt state.

Each interval reads port `$DC` 12 times at `$093A` before normalized input writes at `$084E/$0858`, then movement, then the checkpoint. During held left, the first six reads are `$FB` and the next six `$FF`; otherwise all 12 are `$FF`. In interval 1299, lower X is `$C0` and normalized input `$C053` is zero. In interval 1300, `$C053` is `$04` and lower X has moved to `$BE`. The source movement step is `1 + ($C06B & 1)` before the tail writes `$C06B`, so the held input alternates two- and one-pixel moves: `$BE`, `$BD`, `$BB`, and so on, reaching `$A2` after 20 held updates. At interval 1320, `$C053` returns to zero and X remains `$A2`. This demonstrates same-interval input acceptance and movement for this schedule; `$A2` is not a boundary stop.

The two full 166,001-byte captures are byte-identical, SHA-256 `ce446ae46756d19a915311e27189132dcb4dcdb7fe67a5369643bd701ef04fd9`. The verifier checks the 60 checkpoints, 720 port reads, 120 normalized input writes, 20 movement writes, callback pointer, counter progression and observed positions. The report records selected full-RAM snapshot hashes for later comparisons.

This establishes a controlled active-play timing and input baseline on MAME's SC-3000 machine. It does not establish that every source mode updates once per frame, the SG-1000/Gearsystem clock, audio cadence, visual parity, or PAL A500 parity. The port should use these source checkpoints as one replay comparison and separately measure its own interrupt/update and presentation schedule.

`python scripts/check_translated_timing_replay.py` resumes the translated full update from source interval 1299 and matches all 256 RAM bytes for each of intervals 1300-1339, after accounting for the tap occurring before the `$C06B` write. All 40 updates take the lower `serve_wait`, upper `ai_wait` and ball-dispatch `idle` paths; changing displayed ball coordinates arise from the lower serve wait path, not active ball flight. This is translation-vs-source evidence for this one bounded state trajectory, not native Amiga equivalence.

A separate `python scripts/capture_source_serve.py` run presses button 1 after frame 1300 and captures intervals 1299-1499 twice. The 201-checkpoint files are byte-identical (SHA-256 `633f77ba928793c358ea2941321d11662615486e703de13243fede1efe1f9c83`). The translated full update matches every byte of the 256-byte pre-tail RAM snapshot for intervals 1300-1499. Serve triggers at 1300, launches at 1316, active flight later crosses a net/return and ends in the observed point state at 1432. This is a strong differential reference for evaluating a mechanical transcode, not a native-port result.

## CT09 ordinary clock contract

The retained original one/two-player audio `frame-times.tsv` files give a
constant **16688156054054544 attoseconds** per source frame. Both full source
state fixtures' `begin_frame` labels also advance exactly one frame per callback: 13,378 and 27,037
updates respectively. `ordinary_cadence.clock_contract()` checks these original
facts and saves its contract before running the maintained application.

On the pinned PAL emulator, a colour clock is 1/3546895 second and the CIA
E-clock is one tick per five colour clocks, or 709379 Hz. These are emulated
time, independent of host execution speed. CPU bus notifications include an
integer colour-clock timestamp and full physical beam position. The source
interval is **11838.227453469159 E-clock ticks**; its nearest 16.16 value is
**775830074**, split into 11838 whole ticks and a 14906/65536 remainder.
The maintained loop accumulates this remainder rather than discarding it per
update. Its initial immediately due update is preserved.

The timer start write and initial CIA counter read establish the time origin:
start colour clock + (65535 − initial count) × 5. Origin uncertainty is at
most one E-clock. Fractional deadline quantization contributes another tick;
rounding the interval contributes at most N/(2×65536) ticks after N intervals.
An update must start no earlier than that independently derived bound, and
complete before its next source deadline. A late callback is a failure, not a
reason to fit a larger tolerance. Entry and completion counters distinguish
work duration from polling delay without stopping execution.

`run_ordinary_round_tests.py --mode=one --match --cadence` (and `--mode=two`)
uses one uninterrupted execution from loaded application through complete
match, returned title, opposite selection, held-action suppression and a fresh
restarted serve. Only physical keyboard/pad commands are injected. Ordinary
native timer entropy is separate from the two recorded-entropy reference
replays. Milestone screenshots, emitted audio and actual input replies are
retained privately. The completion counter, lifecycle, inputs, score/pose and
Copper writes are observed externally; no expected state is written to RAM.
Every Copper publication must use the latest completed prepared epoch and
occur outside physical visible rows 44–235. PAL can legitimately present the
latest of multiple source updates; it must not publish an older epoch.

Memory is measured from Kickstart Exec's MemList/free chunks, cross-checking
their sum against each chip MemHeader's free count. Header/list writes are
watched continuously during the ordinary run. A changed allocation/topology
leaves peak memory unverified unless accounted for; an unchanged allocation
establishes the actual peak, including OS and allocated executable/stack.
Executable file size is not a RAM measurement. Cold ADF boot remains CT10.

Four focused `run_physical_input_tests.py --timing-edges` probes put a real
direction/action immediately before sampling or after the pre-tail checkpoint.
They check actual movement from the measured initial X, and actual serve phase,
in the same or following callback. Debugger stops make these boundary probes,
not uninterrupted cadence evidence.

The initial integer scheduler title check accumulated 1.24 ms of advance over
3,595 updates. With fractional scheduling its endpoint difference was 6.9 μs.
The first uninterrupted ordinary match still failed at callback 4,072: completion
was 59,415 colour clocks after its deadline, beyond the next interval (~59,191).
Unconditional repatching of 224 unchanged scoreboard descriptors between
callbacks delayed entry. A separate cache for each native Copper bank avoids
that redundant work while changed fields still patch their inactive list.
Final ordinary measurements and focused display checks determine acceptance;
these baseline observations alone do not certify CT09.

The cache also exposed an existing mixed-generation publication at generation
470: a newer score/status selection could alter the already prepared sprites'
Copper bank. The original 42-check score/status prefix rejected it. Preparing
the six field selections together with the sprite scene, and using that
snapshot for bank patches, restored all 42 exact comparisons. The source
fixtures and pixel expectations were retained unchanged.

At the current checkpoint, the final one-player ordinary run passes through
result, returned title, opposite selection and fresh restarted flight: 11,890
completed updates, 9,753 publications, no deadline violations or visible-line
commits, and **329,136 bytes peak chip allocation**. Four final direction/action
boundary probes pass. This is one measured native-entropy run, not CT09
completion: the two-player ordinary run and final replay/display guardrails
remain to be run. The progress command therefore keeps CT09 unverified.
