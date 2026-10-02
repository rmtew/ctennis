# Classic human and robot replacement

Selected direction A Classic implements P1/P2 identity on the independent
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
at court scale, visually reviewed for the human/robot distinction and P1/P2
court headings. They are explicitly **not emulator scanout**, target timing
evidence or native acceptance. In the court preview, earlier hardware sprite
channels are drawn over later ones; the pose sheet is a mask overview. Runtime
priority/occlusion must be reviewed in actual target captures.

## Ownership and shared integration points

`scene.s` selects role masks using logical controller mode and end ownership;
court-relative AI flags temporarily lag ownership during round pause and are
not used for appearance. Demo playback
visually uses robots for both recorded controllers. Colours remain assigned by
the existing stable owner/end mapping. Two-player mode uses two humans. Takeover
in `interface_input.s` refreshes the scene bodies after demo ownership changes,
before the same callback prepares an inactive sprite bank. Coordinates, contact
points, gameplay clocks, score and entropy are untouched.

Player-facing controls, court headings, winner prompts and tallies now use P1/P2.
One-player P2 winners/tallies and demo winners/tallies identify AI explicitly.
Blue/Red remain swatches and the controls legend. Existing symbol names for tally
digits and feedback kinds remain compatible with native observations and CT13.
`YOUR SERVE` already appears only for a live human controller, so it remains.

Shared files with CT13: `amiga/game/scene.s`, `interface_input.s`,
`interface_render.s`, `interface_text.s`, `assets/native/manifest.json` and
`assets/native/scene/sprite-images.bin`. `main.s` is unchanged: its existing
atlas include loads the enlarged file. Raised-racket celebration integration
remains **pending**. The other worker must supply pose index(es), racket mask,
offsets, timing and whether the facing follows the winning end. Human and robot
table entries must then be added together; the current `<14` guard must be
extended only with that concrete contract. No placeholder celebration art or
state hook is presented as complete.

## Verification status

Passed locally: `python -m unittest discover -s tests/unit -q` (27 tests),
`python scripts/native_assets.py` (116 inputs), native UI page baking with the
retained font, Python syntax compilation and `git diff --check`.
`native-contract.json` freezes the retained racket hashes, body bounds,
pose/animation hashes, physics modules and canonical recording/trajectory from
the base. Host tests inspect all role masks and both plane variants, exact
colours/geometry and authored P1/P2 glyphs. These tests do not certify runtime
selection or CPU timing.

Extended existing finite native demo/full replay/takeover and ordinary feedback
checks to inspect actual native scene frames, owner colours and positions in
both modes/end exchange. The full replay still checks the independently frozen
10958 input-tick trajectory; no golden was regenerated. These extended target
checks have **not run** in this environment.

Blocked build: `python scripts/build_native_game.py` fails with
`FileNotFoundError: /workspace/ctennis/.tools/vasm/vasmm68k_mot.exe`.
Python is the pinned 3.12.14. Pinned vasm 1.9d, Copperline 1.0.0-rc.1 and local
configuration are unavailable. A legitimate uploaded Kickstart input exists;
it was not copied into the repository. No substitute assembler/emulator was
used. Native executable/ADF hashes, all-used-pose scanout, publication/cadence,
chip-memory headroom and cold ADF checks remain unverified. Do not merge until
these and combined CT13 verification pass on the configured target.
