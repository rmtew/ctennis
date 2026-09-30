# Independent original audio and native Paula comparison

The source audio captures run the actual cartridge twice from reset under each
existing frozen R1/R2 input policy. Every callback recording retains its accepted
parent hash. The read-only observer records actual PSG writes and frame-label
timestamps as integer seconds plus attoseconds. WAV generation uses explicit
48 kHz, zero-dB output and the headless sound backend. No CPU/game state is written.

R1 retains 11,808,001 mono PCM16 sample frames (246 seconds plus one sample),
4,240 timed writes and 3,353 writes exactly associated with the raw callback
recording; 3,352 belong to the retained parent timeline. R2 retains 22,752,001
sample frames (474 seconds plus one sample), 6,299 timed writes and 5,423 exact
raw associations; 5,422 belong to its parent. Complete WAV bytes, PCM, event
timestamps, frame timestamps and callback recordings repeat identically.
The raw recorder can include a final event beyond the fixture's retained stop;
that distinction is preserved rather than silently merging the two extents.

`capture_source_audio_reference.py`, `source_audio_reference.py` and
`freeze_audio_reference.py` provide explicit capture, validation and private
retention under `tests/reference/audio/`. Eighteen named WAV intervals cover
both serve ends, both instrumented return paths, point awards, initial round
tail/resume, match award/result sound and restarted gameplay across the parents.
They retain complete intervals and the first audible-command/all-muted times;
a silence between phrases does not truncate a result sequence. These command
times are distinct from measured waveform response. Source mono/stereo output,
filter/phase, onset and level measurements remain explicit P2 work.

The pinned MAME [SC-3000 configuration](https://github.com/mamedev/mame/blob/mame0289/src/mame/sega/sg1000.cpp)
selects SN76489A at 10.738635 MHz / 3, or 3,579,545 Hz. Its
[PSG implementation](https://github.com/mamedev/mame/blob/mame0289/src/devices/sound/sn76496.cpp)
defines register latching, the non-Sega zero-divisor case (1024), and the
2 dB attenuation steps with level 15 muted. It is BSD-3-Clause and credited to
Nicola Salmoria and contributors listed in that file. The test-only decoder
summarizes recorded hardware commands; it generates no expected waveform or
gameplay. The elapsed-time API follows [MAME's Lua reference](https://docs.mamedev.org/luascript/ref-core.html).

Only a noise-volume mute (`FF`) is observed as a noise-related latch write.
Noise stays muted during both retained gameplay recordings. Non-Sega reset
state before the cartridge's initialization is separate; its WAV output must
not be mislabeled as a game noise effect. No active gameplay noise case is
invented to justify a new implementation requirement.

## First actual native audio case

`python scripts/run_audio_tests.py --case p2-first-serve-pitch --self-test`
runs the actual native application with the existing recorded-entropy seam and
physical fire input. It stops after the Paula event application, verifies the
ordered PSG bytes against the source callback, reads actual custom registers,
and captures the emitted WAV. The native WAV is stereo IEEE float32 at 44.1 kHz,
which Python's standard wave reader does not support; `audio_wave.py` reads its
RIFF subtype explicitly. It also accepts the source PCM16 format. No resampled
or synthesized waveform becomes an oracle.

The first serve uses source tone 2, divisor 213, at 525.167987 Hz. Its mapped
Paula channel 3 uses a four-sample waveform and stock PAL clock 3,546,895 Hz.
The nearest integral period is 1688; actual AUD3PER is 1687. The current code
approximates the conversion ratio as 507/64 = 7.921875, versus the exact clock
ratio 3,546,895 * 8 / 3,579,545 = 7.927029832. The case records the first failure
at callback 17, `paula-events-applied`, expected 1688/actual 1687. No product
correction is made. The native waveform's rising-crossing estimate is about
525.622 Hz, consistent with the actual period, but is diagnostic evidence;
no unmeasured waveform tolerance is inferred. Attenuation, stereo, filter,
onset/duration and later effect classes remain separate comparisons.

The self-test mutates the private assembled `MULU.W #507,D3` instruction to
`#508`. Actual native period changes to 1691, with a different executable hash.
The normal executable is rebuilt and recaptured last; no mutation remains in
the authoritative report/output. A changed frozen timestamp file was rejected
by integrity validation and restored. Suite known-failure policy also rejects
changed signatures and unexpected passes. This case adds one P2 comparison;
the full objective remains incomplete.
