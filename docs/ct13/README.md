# CT13: provisional Warm Fanfare and match celebration

Six games now retain the final court and logical winner/totals instead of
automatically returning to title. After a bounded 48-tick celebration pause,
the loser/ball/shadow disappear and the winner moves to their own half's visual
centre, raises the racket and bounces upward by zero, one or two pixels. Blue/Red
identity follows logical score ownership through exchanged ends. The text is
ordinary native label data; future P1/P2 naming or sprites are separate scope.
Individual game-win feedback remains the existing short feedback.

The independent Warm Fanfare is provisional, selected by the user to proceed
with CT13 while traditional tune alternatives are prepared separately. It is
the existing audition's melody, bass and harmony, represented by authored
16-byte records in `assets/native/audio/fanfare.i`. No audition WAV/ZIP is a game
input or committed delivery workaround. The source uses direct independently
calculated Paula periods, native volume indices32/20/13 and a 7/8 release scale;
it does not use the retained melody, period index or envelope rows for this cue.
The analytic four-byte square DMA waveform remains shared with other sounds.
Superseded Sega-derived victory score-2/3 are removed from the active manifest,
includes and files; Git history preserves their provenance. Other retained
assets keep their honest Sega-derived/private-only provenance. No unsupported
rights-clearance, original parity or real-hardware quality claim is made.

Eight 4/4 bars take384 rate2 sequencer steps (768 simulation ticks), approximately
12.8165 seconds per subsequent loop. Initial queuing adds2 simulation ticks.
Final one-beat rests align all voices and create an intentional loop breath.
`AV_DONE` retains its legacy last-loaded meaning for unaffected cue waits;
`game_audio_phrase_complete` is the explicit full-duration/zero-emitted-level
contract for all three voices. Completion, not an assumed elapsed delay, sets
the first-play latch and restarts the next loop. The prompt appears only then.
Early presses are discarded, inherited holds remain blocked and all action
sources must release before fresh fire/action can return once to title.
Title return mutes/resets voices and celebration state and clears the match.
Normal pause freezes the sequencer, mutes Paula and resumes its prior levels.
The frozen winner/totals line is cached after first drawing; prompt appearance
and pause/resume copy it and draw only the prompt to stay within the unchanged
callback deadline. The initial uncached two-line redraw failed cold-ADF cadence
and was replaced; that failed receipt is not an acceptance pass.

The tune boundary is three fixed native pointers (melody/bass/harmony), not a
skin/music framework. To replace the provisional tune after selection, edit
the three authored scores, align their terminal rests and update manifest
hashes. Direct-period flag bit5 is documented in the score and is unused by the
retained records. No new channels, PCM streaming or runtime allocation are
introduced. There are59 records/944 score bytes,8 bytes of celebration state and a256-byte
static chip cache for the frozen banner;
additional code/labels must be measured with the normal post-link chip telemetry.
Target remains PAL A500/68000/OCS/512KiB chip, zero expansion, legitimate
Kickstart1.3 and pinned Copperline. Pre-Exec-pool bootstrap memory remains outside
the established telemetry scope.

## Affected finite verification

Run the following against the exact committed branch head. Build/fixture and
ordinary receipts retain actual source/tool/executable hashes; raw PCM, scanout
images, bus telemetry and reports stay under ignored `build/`, outside Git.
The draft PR reports completed results and limitations from those receipts.

```
python -m unittest discover -s tests/unit -q
python scripts/native_assets.py
python scripts/build_native_adf.py --self-test
RUST_LOG=info python scripts/run_celebration_tests.py --winner=blue --self-test
RUST_LOG=info python scripts/run_celebration_tests.py --winner=red
RUST_LOG=info python scripts/run_celebration_tests.py --winner=blue --exchanged
RUST_LOG=info python scripts/run_celebration_tests.py --winner=red --exchanged
RUST_LOG=info python scripts/run_native_contracts.py --case=audio-hit --self-test
RUST_LOG=info python scripts/run_enhanced_menu_tests.py --adf
RUST_LOG=info python scripts/run_demo_match_tests.py
RUST_LOG=info python scripts/run_demo_match_tests.py --takeover
RUST_LOG=info python scripts/run_enhanced_feedback_tests.py --mode=one
RUST_LOG=info python scripts/run_enhanced_feedback_tests.py --mode=two
RUST_LOG=info python scripts/run_ordinary_round_tests.py --mode=one --match --cadence --adf
RUST_LOG=info python scripts/run_ordinary_round_tests.py --mode=two --match --cadence
RUST_LOG=info python scripts/run_ordinary_round_tests.py --mode=one --match --early-release --audio --self-test
RUST_LOG=info python scripts/run_native_setup_tests.py --self-test
```

The four new fixtures initialise near-match state once, then use actual native
scoring, dispatcher, physical input, audio and scanout. They check both winners
and end orientations, frozen score, exact footer font pixels, winner colour /
absent loser pixels, raised pose, three bounce heights, two full plays and quiet
real-emulator loop breath, held/early input, full-play gate, pause/mute/resume,
fresh continuation, single title return and stable bounded chip allocation.
A compiled premature-completion mutant removes the duration check and must be
rejected. These fixtures are explicitly separate from uninterrupted ordinary
play. The ordinary match/cadence tests now require full-play/release/fresh-fire
milestones instead of the superseded automatic result-to-title epoch; existing
restart/input/publication guards remain. Attract replay still compares the
frozen10958-tick trajectory without regenerating it.

The cold menu joystick takeover check now observes up to12 actual native input
samples, matching its existing keyboard takeover check. The old single-sample
assumption could run before the physical event was sampled. The check still
requires actual takeover, byte-preserved world/score/audio/clocks at that sample,
and consumed input; no takeover state is injected or assertion removed.

No master merge, public release, new sprite design, music-alternative selection
or unrelated sound-effect redesign is part of this draft.
