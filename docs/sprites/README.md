# Classic human and robot replacement

Selected direction A Classic implements A/B identity on the independent
`sprites/classic-p1-p2` branch based on `93bb640`. No master merge or CT13 lifecycle,
audio, bounce or celebration changes are included.

## Artwork and native constraints

`classic-generated-masks.png` is the built-in ImageGen source, generated from the
inspected committed native bodies and selected Classic concept. It is not an
engine atlas. Native masks are nearest-neighbour sampled to 16x32, reduced to
binary occupancy and clipped to each retained part's bounds. The one-pixel
boundary from the retained part preserves seams, wrists and feet; this fitting
is not a claim that every body pixel is newly authored. White racket masks,
pose offsets, animations, ball and shadow retain their Sega-derived provenance.
No source cartridge or original-platform assets were read or extracted.

The body uses one Blue `$55e` or Red `$e33` colour and transparent holes; the
racket remains white `$fff`. No skin tone, outline colour, extra channel or
anti-aliasing is introduced. The existing atlas's 24 used body masks are replaced
by human masks. A compact 24-mask robot extension adds 3072 bytes; the robot pose
table adds 112 bytes. Both role tables cover all 14 retained ready/serve/swing
poses with identical racket references and signed offsets. The original human
pose and animation tables are byte-identical. Physics and the frozen recorded
trajectory are unchanged on disk.

`classic-native-poses.png` shows the fitted masks, enlarged without interpolation.
`classic-court-review.png` and `court-decode-*.png` are static native-asset decodes
at court scale, visually reviewed for the human/robot distinction and A/B
court headings. They are explicitly **not emulator scanout**, target timing
evidence or native acceptance. In the court preview, earlier hardware sprite
channels are drawn over later ones; the pose sheet is a mask overview. Runtime
priority/occlusion must be reviewed in actual target captures.

## Ownership and shared integration points

`scene.s` selects role masks using logical controller mode and end ownership;
court-relative AI flags temporarily lag ownership during round pause and are
not used for appearance. Demo playback
records the human A slot against the AI robot B slot. Colours remain assigned by
the existing stable owner/end mapping. Two-player mode uses two humans. Takeover preserves the same A-human/B-robot appearance; no sprite role switch
or geometry refresh is needed when recorded input becomes live input. Coordinates, contact
points, gameplay clocks, score and entropy are untouched.

Player-facing controls, court headings, winner prompts and tallies use A/B.
A HUMAN and B AI/HUMAN role labels are centred under the letters. Demo A remains
human. Footer text/layout and the approved DEMO - TAKE OVER / EXIT selector
are owned by CT13; its final A/B footer must be used during integration.
Blue/Red remain swatches and the controls legend. Existing symbol names for tally
digits and feedback kinds remain compatible with native observations and CT13.
`YOUR SERVE` already appears only for a live human controller, so it remains.

Shared files with CT13: `amiga/game/scene.s`, `interface_input.s`,
`interface_render.s`, `interface_text.s`, `assets/native/manifest.json` and
`assets/native/scene/sprite-images.bin`. `main.s` is unchanged: its existing
atlas include loads the enlarged file. The published CT13 contract at
`9ec02488e00593f1e41e59bd95f2c463a615a665` was inspected: pose4 is the lower
winner at X120/Y125; pose11 is the upper winner at X120/Y52, with bounce heights
0/1/2. Both Classic role tables already cover these poses with retained racket
masks and offsets. No new pose or extended `<14` guard is required. Combined
CT13 runtime verification and its latest footer selector remain separate work.

## Residual logo audit

Decoded and inspected all active title/court planes, all atlas masks and the
initial eight hardware sprite masks. Title artwork has only BASELINE RALLY;
startup sprites contain actors/rackets/ball, no logo. The court retained a blue
logo fragment at native x8..38/y139..143. Clear only that audited black/Blue
rectangle. Atlas slots28..30 contained unused logo fragments; zero those three
128-byte masks. Neither pose table references them. Score banks contain status,
point/game/tally graphics or role labels, not logo fragments. The retained font's
ordinary S/E/G/A letters and honest provenance text are not a graphical logo.
Frozen court tests verify every unrelated court pixel is byte-identical to the
original base. HUMAN/AI headers replace the obsolete mode row in every variant,
including demo; their visible glyph centres lie within half a pixel of A/B.

The supplied screenshot `libfile_c028265956f881918e08414bcc6a44c4` was resolved
through Library, but two current-helper materialization attempts failed with
`library file transfer failed: download failed`. The authorized-file fallback
also failed with `file could not be authorized or resolved`. It was not locally
materialized or visually inspected; the asset audit uses actual committed native
pixels instead. This reference-access gap is reported, not silently treated as
successful screenshot inspection.

## Verification status

Passed locally: `python -m unittest discover -s tests/unit -q` (28 tests),
`python scripts/native_assets.py` (116 inputs), native UI page baking with the
retained font, Python syntax compilation and `git diff --check`.
`native-contract.json` freezes the retained racket hashes, body bounds,
pose/animation hashes, physics modules and canonical recording/trajectory from
the base. Host tests inspect all role masks and both plane variants, exact
colours/geometry and authored A/B glyphs. These tests do not certify runtime
selection or CPU timing.

Extended existing finite native demo/full replay/takeover and ordinary feedback
checks to inspect actual native scene frames, owner colours and positions in
both modes/end exchange. The full replay still checks the independently frozen
10958 input-tick trajectory; no golden was regenerated. These extended target
checks have **not run** in this environment.

Initial setup failure is resolved. The CT12 recovery procedure rebuilt vasm1.9d
from Leffmann/vasm commit685a87e5ed14285350ccdb6581c9771bc8df6c7d with the exact
locked SHA2560332feebc562e06bf245c1d60bef3fd7598c464a4be8162429be5e3e3a061e39.
The official Copperline1.0.0-rc.1 AppImage and extracted ELF match the hashes in
CT12 verification. Portable mode, pinned amitools and the existing legitimate
external Kickstart are configured under ignored .tools/config. No cartridge
extraction, substitute tools or packaged ROM is involved.

Final native verification results are recorded in verification.md; they apply
only to the exact committed head named there. Do not infer combined CT13
acceptance from sprite-branch results.
