# Emitted first-serve mute regression

The existing `p2-first-serve-mute` case now checks emitted audio as well as Paula
volume registers. No additional case is registered. Missing protection was an
absent effect or residual sound in the output despite correct logical commands.
The independent oracle is the retained original PCM16 WAV, associated with the
all-muted PSG event at source callback 40. Both normal and fault captures preserve
original game state and ordered PSG commands.

The original establishes audible output in a 5 ms window starting 10 ms before
mute, and silence in a 20 ms window starting 10 ms afterwards. Each output channel
is inspected separately. Native float samples are rounded to the source's PCM16
precision (32768 integer steps per normalized unit), so harmless float residues
are not mistaken for sound and opposite-phase stereo cannot cancel into silence.
This is a bounded digital recording criterion, not an analogue hearing threshold
or proof of exact onset/decay timing. Debugger-stop times locate native windows;
complete retention and finite samples are required. Subsequent audible original
commands cannot fall inside the quiet comparison window.

`python scripts/run_audio_tests.py --case p2-first-serve-mute --self-test`
completed successfully with three actual native captures, normal rebuilt last:

- Normal: audible channel peak 332 PCM16 units before mute, both channels zero
  at PCM16 precision afterwards; hardware mapped volumes also zero.
- Private mute table changed from 0 to 1: post-mute channel peak 166, waveform
  comparator rejects the residual sound.
- Private four-byte waveform replaced with zeros: pre-mute signal disappears;
  waveform comparator rejects it while period, volume and DMA length controls
  remain identical to normal for every retained audio event.

The first validation attempt compared the entire custom-register dump and failed
because the zero-waveform control deliberately changes DMA-fetched AUDxDAT.
The assertion was corrected to compare period/volume/length controls, and all
three captures were rerun successfully. This was a harness assertion error,
not a product regression. No product assembly or original media changed.

Finite/truncated-window checks, opposite-phase stereo and subnormal residue
controls exercise the digital comparator. Suite policy rejects each fault as
unexpected red. Existing classifications are retained; this is an incremental
mute-case run, not a new full-suite execution. Stop equivalent first-serve mute
windows. Later effect classes, stereo balance, waveform fidelity, onset/duration,
ordinary execution and the remaining behavioural requirements remain open.
