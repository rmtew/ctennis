# Native physical input regression baseline

The retained original calibration now drives actual Amiga joystick lines and
live input routines. Thirteen independent control windows share one continuous
native capture: both pads' four directions and two buttons, plus simultaneous
pad-1 Right and pad-2 Left. Three cases are green; ten expose exact existing
sampler omissions. These are local input comparisons, not full P3 acceptance.

## Independent source and declared connector mapping

`tests/reference/input-map.json` is the earlier twice-identical original MAME
calibration documented in [the source input map](two-player-input-map.md).
No source recapture was necessary. Raw capture SHA256 is
`e6fa3b7fb4b5862eb7b4dac70e0a1b74a297764fcc840b2882b6eb58bffbb3da`;
frozen fixture SHA256 is
`3ff7a462b3178d42abbbc5c171337a727e0ab231e4ef556a5d45abef36d4b636`.
The public physical-input policy pins these hashes and the cartridge hash.

Source pad 1 maps to Amiga connector 2, source pad 2 to connector 1. Both are
configured as joysticks. Source Button 1 maps to red/fire; Button 2 to blue/second
fire. In this source calibration the court-side bit is clear: pad 1 is lower,
pad 2 upper. This does not establish player ownership after a side exchange.

`physical_input_reference.py` cross-checks all 1,124 recorded source reader
returns against their timeline events and physical control states. It verifies
562 consecutive source callbacks, both readers per callback, two-player mode
and the declared side mapping. Expected normalized directions/actions come
from actual captured source RAM, not a Python game implementation. The original
combined control fields also agree with the recorded reader values throughout.

Each case retains one neutral sample, 24 consecutive held samples and 16
released samples: 41 comparisons. Recipe validation rejects missing neutral or
first-press samples, shortened holds/releases and intervals outside the frozen
capture. All 13 source windows validated; 26 shifted/shortened recipes were
rejected in negative checks.

## Actual native execution

The adapter builds the existing application and replaces only its initial RAM
include with the original calibration callback0 post-tail state. This sets a
reachable two-player start without claiming that the absent native menu accepted
the selection. Product source is unchanged. The normal executable uses the
existing joystick sampler, translated input update, game loop, CIA cadence and
native display/audio paths. No expected intermediate RAM is injected.

Physical events are retimed to actual native callback sampling boundaries using
the source reader event timeline. Both pad states are applied before the live
sampler. The actual calls to each input reader are observed through their real
stack return addresses, recording the returned byte. Normalized directions and
actions are read after input update and before score/game processing. This
compares actual native I/O and consumption, not supplied core-replay input bytes.

The complete capture observes 561 successive native callbacks after its one
source initialization. Diagnostic counter checks reject skipped/repeated
callbacks and require the final callback to complete. Source/global callback
IDs, native beam/time stops, physical state changes, reader returns, normalization
and executable/source/emulator/bridge/ROM hashes remain in private captures.
Host debugger pauses do not establish real-time input latency or deadline
acceptance; those require ordinary uninterrupted runs.

## Measured case results

| Case | First held source callback/frame | Expected reader value | Actual value | Result |
|---|---|---:|---:|---|
| Pad 1 Up | 21 / 1320 | 2 | 0 | Known red |
| Pad 1 Down | 61 / 1360 | 8 | 0 | Known red |
| Pad 1 Left | 101 / 1400 | 4 | 4 | Green |
| Pad 1 Right | 141 / 1440 | 1 | 1 | Green |
| Pad 1 Button 1 | 181 / 1480 | 16 | 16 | Green |
| Pad 1 Button 2 | 221 / 1520 | 32 | 0 | Known red |
| Pad 2 Up | 261 / 1560 | 2 | 0 | Known red |
| Pad 2 Down | 301 / 1600 | 8 | 0 | Known red |
| Pad 2 Left | 341 / 1640 | 4 | 0 | Known red |
| Pad 2 Right | 381 / 1680 | 1 | 0 | Known red |
| Pad 2 Button 1 | 421 / 1720 | 16 | 0 | Known red |
| Pad 2 Button 2 | 461 / 1760 | 32 | 0 | Known red |
| Simultaneous Right / Left | 521 / 1820 | group1: 4 | 0 | Known red |

Every window compares both readers and both normalized fields, including its
neutral and release samples. The three green cases pass all 41 samples.
The simultaneous interval retains pad1's correct Right value while exposing
the absent pad2 Left value. Exact signatures include callback/frame, reader
boundary, group and wanted/observed value; baseline classification rejects
changed failures and unexpected passes. Ten red cases are not ten independent
product defects: the live code lacks vertical and second-button handling, and
its second input routine clears the result instead of reading the other pad.

## Sensitivity, batching and architecture freedom

`--self-test` assembles a separate temporary executable that toggles the sampled
pad1 Right bit immediately before the sampler returns. It introduces actual
wrong/cross-player controls. All 13 case windows reject this changed executable;
each also detects it at a neutral boundary which passes in the normal capture.
Normal and mutated captures remain separate and hashed. Product code and the
frozen original oracle are unchanged.

Run `python scripts/run_physical_input_tests.py --all --self-test`, or use
`--case <p3-input-case>` for one report. The aggregate executes the entire batch
once and classifies all thirteen reports separately, rather than repeating the
same 561 callbacks thirteen times. It deletes old reports first and rejects a
failed/incomplete batch as tool errors rather than interpreting stale reports
as product failures.

These byte observations are temporary diagnostics of the translated starting
point. Final native controls may use different flags, structures and routines;
replace this adapter with named native input intents/acceptance while retaining
the physical cases, original evidence and observable behaviour. There is no
requirement to retain SG device readers in the production port.

Stop equivalent initial-side single-control windows. P3 still requires actual
player/action response and side exchange, sampling-edge/real-time latency,
ordinary cadence through tail/result regimes and complete-match display/audio
deadlines. P1/P2 and remaining focused gameplay coverage also remain open.

Full aggregate baseline/self-test completed 77 cases: 42 green, 35 exact known
red, no unexplained failures or tool errors. Four missing groups still fail the
suite. Normal/mutated captures both complete 561 callbacks; normal per-sample
counters are exactly0..560. All thirteen report capture hashes and mutation
capture hashes verified after completion. Product code remains unchanged.
