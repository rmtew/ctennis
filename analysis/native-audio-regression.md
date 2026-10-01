# CT08 maintained native sound

The ordinary application and maintained replay share `amiga/game/audio.s`.
`audio_state.i` names three native voices. Gameplay requests a strike; scoring
and round waits request a ready cue; result and restart request paired phrases.
Completion means the final note was loaded, not that its remaining envelope was
cut off. Queuing preserves the current note and resets its release clock; reset
mutes all three actual Paula channels. Lifecycle predicates read native queue
completion, with no source stream cursor or ROM pointer in product control.

`generate_native_audio_assets.py` deterministically converts the six identified
scores to native note records, unpacked envelope levels and nearest integral PAL
Paula periods. Conversion is offline, using the legitimate configured cartridge;
all generated notes/data remain ignored. The native runtime dispatches musical
settings, duration and envelope steps, with no SG stream opcodes, source pitch
lookup or PSG latch interpreter. `paula_output.s` writes the prepared period and
calibrated amplitude directly to channels 0,1,3. Its four-sample chip waveform is
unchanged. Unsupported active noise/stereo/filter fidelity is not added.

The maintained tail already gated its former countdown before CT08. The stale
plan statement about an unconditional maintained call was corrected. The new
native engine decrements its own countdown once per shared tick, including waits;
the generated counter prefix's audio decrement and source-stream assignment are
excluded under NATIVE_AUDIO. Remaining generated scalar clocks/virtual memory
are explicit CT09/CT10 debt, not claimed removed.

`amiga/tests/audio_observer.s` imports a captured initial audio condition once,
then serializes actual native note cursors, durations and envelopes for retained
comparisons. Source cursor annotations/divisors are separate diagnostic assets;
ordinary notes contain no such annotations. PSG-format traces are observations
of emitted native musical levels/pitches, never input to hardware playback.
The ordinary compiled product excludes the observer, old decoder and PSG sink.
Actual Paula registers and emitted WAV checks independently protect physical
pitch, level, missing waveform and stuck/unmuted output faults.

The restored independent original A/B recordings match their accepted source
parents and repeat byte-identically. The18 named original intervals group into
six phrase classes plus silence/scheduling; intervals can contain repeated or
multiple requests. One existing result/title/restart window11959–13381 exercises
all six audible classes and returned-title silence. It is a captured phase,
not eighteen ordinary recordings or whole-match waveform equivalence. Source
callback writes are associated with the same native boundary; four main-thread
reset mute writes at12281 remain separately identified as between-callbacks.
Reset output is checked through actual register/silence and ordinary title proof.
Amplitude expectations for every class are derived from the original serve WAV's
measured plateaus under unchanged2/3/4ms trims, rather than copying native levels.

The first native baseline AUD3PER at17 was1687 instead of nearest1688. Native
prepared periods use the exact clock ratio3546895*8/3579545; all audible periods
in the retained original captures fall within666–6397, so no legal-period
clamping masks an observed out-of-range pitch. Source amplitude step14 maps to3,
with all15 nonmute steps independently measured. Faults mutate the actual compiled
period table, amplitude table and waveform; the authoritative normal capture is
rebuilt last. Reference expectations remain unchanged.

The standalone status-timer phase was absent and mechanically restored with
`phase_reference.build_phase/validate_phase` from the accepted original parent.
Its captured initial state is a returned-title main-thread wait. A one-time
explicit diagnostic initialization validates that title/mode/score state and
selects GAME_TITLE_TRANSITION; it does not dispatch by callback kind, inject
intermediate state or change ordinary startup. Both declared updates must match.
The existing serve smoke mutation had a pre-existing ambiguous anchor after CT06
added a returned-title active call. It now names the unique active-play call and
still mutates/restores the actual maintained dispatcher.

Final commands, exact receipts, ordinary executable hash and known failures are
recorded in WORKLOG.md and ignored build/ct08/final-command-ledger.json,
final-index.json and final-progress.json. Audio runners use the existing freshness
transaction: incomplete/failed invocations invalidate old passes, source/WAV/
reference/tool/config/executable dependencies and actual mutant captures are
fingerprinted. Progress keeps integration, bounded working behavior and target
RAM/cadence/ADF delivery as separate dimensions. No full-game, byte-identical
waveform, filter/phase/stereo, peak RAM, ADF or independent target claim is made.
