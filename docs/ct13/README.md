# CT13: sequenced Battle Hymn and match celebration

Six games retain the final court, logical winner/totals and celebration rather
than automatically returning to title. After48 celebration ticks the loser,
ball and shadow disappear; the winner centres on their own half with raised
racket and0–2 pixel bounce. Logical Blue/Red ownership stays correct through end
exchanges. Individual game feedback remains short.

The user selected the corrected Battle Hymn chorus, replacing provisional Warm
Fanfare. Asset-only source commit:9c7ede993525fdea8eee139a66ee72327fdb54db. See
[authored format/provenance](../../assets/native/audio/battle-hymn/README.md).
Melody/bass/arpeggio have34/33/65 native16-byte records:2,112 score bytes,4-byte
square waveform and independent3,072-byte period bank,5,188 runtime asset bytes.
This is three-voice sequenced chiptune, not embedded WAV music. No Hail alternative
or tune selector is included. Old Sega victory score-2/3 and placeholder fanfare
are removed from active inputs. Other retained provenance remains honest/private.
The selected square is byte-identical to the previous mathematical waveform;
the new period bank is used only during celebration. Ordinary effect pitches,
levels and envelopes remain unchanged. No new channel/runtime allocation or
unsupported public-release rights/original/hardware parity claim.

Composer timing assumes50Hz updates; the accepted game updates at~59.923Hz,
despite PAL50Hz video. Celebration alone uses a bounded2/3-tick pattern averaging
2.4 ticks/unit (~40.052ms), keeping approximately125BPM without changing gameplay
or effects. The384-unit phrase plus1-unit terminal rest takes924 simulation ticks
(~15.4205s) per subsequent loop; initial queuing adds2 ticks to the first play.
This is distinct from the software audition's nominal15.36s phrase/15.40s end.
Native timing is checked against actual emitted events.

AV_DONE retains its legacy last-loaded meaning for unaffected cue waits.
game_audio_phrase_complete requires all three actual final durations to expire
and emitted levels to reach zero. The audio tick then notifies first-play,
counts the completed cycle and reloads the next downbeat in that SAME step.
There is no extra empty requeue interval after terminal rest. Only then does
PRESS FIRE TO CONTINUE appear for human play. Unattended demo play automatically
returns to title after that same first complete phrase, then the unchanged
30-second idle starts the next attract cycle. Takeover clears demo ownership and
therefore retains the human gate. Early presses are discarded, inherited holds
blocked, and all action sources must release before fresh fire/action returns
once to title, clearing match/audio/presentation/phase. Pause freezes fractional
clock and notes, mutes Paula and resumes previous levels. A256-byte static chip
banner cache bounds prompt/resume drawing to one font line. The earlier two-line
redraw failed cold-ADF cadence and was replaced; that failure is not a pass.
Celebration state occupies8 bytes. Pre-Exec-pool bootstrap RAM remains unmeasured.

The tune boundary is three fixed pointers, not a music/skin framework. Future
replacement needs explicit selection, positive aligned terminal records, an
independently checked compatible pitch bank and updated manifest hashes.
Historical correction/provenance are attributed to the primary-source reviewer
in the asset README, not claimed as this integrator's independent inspection.

## Sprite/label integration contract

No pose/sprite mask is added. Lower pose4 frame offsets:$0180/$0880/$0900,
racket DY=-2/DX=+16. Upper pose11:$1180/$1880/$1900, DY=-2/DX=-16. Origins are
X120/Y125 lower and X120/Y52 upper, with0–2 pixels upward bounce; legs retain
Y+16 and existing native masks/offsets. Replacement sprites must cover these
explicit raised-racket indices with unchanged anchors. Winner is logical0/1;
interface_text.s holds ordinary label strings. Global A/B naming and Classic
human/robot art belong to the separate sprite branch.

Lifecycle/audio touchpoints:result.s/result_audio.s/audio.s and square declaration
in main.s. Shared UI:interface.s/interface_feedback.s/interface_input.s/
interface_pause.s/interface_render.s/interface_text.s. Manifest/data includes are
explicitly updated. Parent combines these files and independently reviews/tests
before any merge. No master merge or public release here.

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
RUST_LOG=info python scripts/run_native_contracts.py --case=match-award
RUST_LOG=info python scripts/run_enhanced_menu_tests.py --adf
RUST_LOG=info python scripts/run_demo_match_tests.py
RUST_LOG=info python scripts/run_demo_match_tests.py --takeover
RUST_LOG=info python scripts/run_attract_cycle_tests.py
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
absent loser pixels, raised pose, three bounce heights, independent authored pitch versus actual Paula registers, complete first play,
exact subsequent-cycle interval and quiet
real-emulator loop breath, held/early input, full-play gate, pause/mute/resume,
fresh continuation, single title return and stable bounded chip allocation.
A compiled premature-completion mutant removes the duration check and must be
rejected. These fixtures are explicitly separate from uninterrupted ordinary
play. The ordinary match/cadence tests now require full-play/release/fresh-fire
milestones instead of the superseded automatic result-to-title epoch; existing
restart/input/publication guards remain. Attract replay still compares the
frozen10958-tick trajectory without regenerating it.

All bottom messages use the256-pixel court viewport and centered32-cell rows.
Inversion consistently marks the selected title-menu row (including the current
player-count choice), pause option, return-confirmation option and demo option.
Static instructions and game-state messages remain normal. Cached normal pages
and cleared footer rows remove the previous inversion before each redraw.
Navigation remains edge-driven: holding a direction never repeats the selection.
The title has no star or control-hint row. Its four entries share one left edge,
with the maximum88-pixel text/highlight width centered at native x84..171;
1,536 bytes of authored normal/inverted row caches support exact half-byte
alignment without repeated font drawing. Both player-count variants enter the
width calculation. The title/court positions are unchanged.
Pause/confirmation and match celebration own both rows. Ordinary demo game-state
feedback owns row1; row2 always shows `DEMO - TAKE OVER / EXIT`, with only the
chosen option inverted and EXIT selected by default. Left chooses TAKE OVER,
right chooses EXIT, either player's action button or Enter confirms, and Escape
exits. The selected action preserves world/score/audio/AI state on takeover and
consumes the confirming event. Every carried keyboard/joystick control is masked
until its own release. Live controls never drive recorded demo gameplay.

The cold menu check compares the entire two-row scanout for pause, confirmation,
default EXIT and selected TAKE OVER, including blank background pixels. Keyboard
and joystick confirmation observe up to12 actual input samples. Frozen full-demo
replay additionally carries live left/right/up/down input across50 callbacks
apiece while still requiring the independently frozen10958-tick trajectory.
Mid-match takeover checks exact native state at the confirmation sample and
consumption of the held selector direction as well as the confirming action.
Full demo replay then observes actual COP1LC/COPJMP publications through the
complete tune, automatic return, full idle and next demo; four title scanouts
and the next demo raster check pixels as well as lifecycle counters. A separate
no-input/no-injection two-cycle run checks every title COP1LC/COPJMP publication,
retained sprite/header blank windows, absence of subsequent quiet-title bitmap
writes and eight actual title/menu scanouts until the next automatic selection.
The active celebration never enters legacy intermediate title states7/8; cue
completion returns directly once, preserving30-second idle before the next demo.

The later approved native-size A/B human/robot+racket title preview and HUMAN VS
AI/HUMAN VS HUMAN captions depend on the separate sprite branch and belong to
parent combined integration. Hooks are ui_menu_lines/ui_players_one/two in
interface_text.s, ui_player_count and remembered selection in interface_menu.s,
the derived width/row caches in native_ui_pages.py, title rows144/152/160/168
in interface_render.s, and native sprite/palette publication in main.s.
Use actual gameplay poses/masks; no custom title art is introduced here. Update
the independent menu raster contract when those captions/preview are integrated.

No master merge, public release, new sprite design, music-alternative selection
or unrelated sound-effect redesign is part of this draft.
